"""Pull Old Dominion's FY2025 10-K data from SEC EDGAR and extract it to JSON.

Writes data/facts.json (income statement lines, both years, integer thousands),
data/stats.json (LTL tons and revenue per hundredweight from the MD&A) and
data/mdna.json (Item 7 text by printed page, quote-matching form).
Raw downloads are cached in data/raw/. Every check fails loud.

Usage: python pull.py   (needs SEC_USER_AGENT in .env, e.g. "Name email")
"""
import html
import json
import re
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"

CIK = 878927
ACCESSION = "0001193125-26-067161"
DOCUMENT = "odfl-20251231.htm"
INSTANCE = "odfl-20251231_htm.xml"
FILING_DIR = f"https://www.sec.gov/Archives/edgar/data/{CIK}/{ACCESSION.replace('-', '')}"
COMPANYFACTS = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{CIK:010d}.json"
YEARS = {"fy2024": ("2024-01-01", "2024-12-31"), "fy2025": ("2025-01-01", "2025-12-31")}

# Face income statement, in statement order. Labels as printed in the MD&A
# percent-of-revenue table, which is also used to audit the tag mapping.
REVENUE = ("revenue", "Revenue from operations", "us-gaap:RevenueFromContractWithCustomerIncludingAssessedTax")
EXPENSES = [
    ("salaries", "Salaries, wages and benefits", "us-gaap:LaborAndRelatedExpense"),
    ("operating_supplies", "Operating supplies and expenses", "us-gaap:OperatingCostsAndExpenses"),
    ("general_supplies", "General supplies and expenses", "odfl:OtherSellingAndGeneralExpense"),
    ("operating_taxes", "Operating taxes and licenses", "us-gaap:DirectTaxesAndLicensesCosts"),
    ("insurance", "Insurance and claims", "us-gaap:OperatingInsuranceAndClaimsCostsProduction"),
    ("communications", "Communications and utilities", "us-gaap:DirectCommunicationsAndUtilitiesCosts"),
    ("depreciation", "Depreciation and amortization", "us-gaap:DepreciationAndAmortization"),
    ("purchased_transportation", "Purchased transportation", "odfl:PurchasedTransportation"),
    ("miscellaneous", "Miscellaneous expenses, net", "us-gaap:OtherCostAndExpenseOperating"),
]
TOTAL_EXPENSES = ("total_expenses", "Total operating expenses", "us-gaap:CostsAndExpenses")
OPERATING_INCOME = ("operating_income", "Operating income", "us-gaap:OperatingIncomeLoss")

X = "{http://www.xbrl.org/2003/instance}"
NS = {"us-gaap": "{http://fasb.org/us-gaap/2025}", "odfl": "{http://odfl.com/20251231}"}


def user_agent():
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        key, _, value = line.partition("=")
        if key.strip() == "SEC_USER_AGENT":
            return value.strip().strip('"')
    raise SystemExit("SEC_USER_AGENT missing from .env")


def fetch(url, name, ua):
    dest = RAW / name
    if not dest.exists():
        req = urllib.request.Request(url, headers={"User-Agent": ua})
        with urllib.request.urlopen(req) as r:
            dest.write_bytes(r.read())
        time.sleep(0.2)  # SEC limit is 10 requests/second
    return dest


# --- XBRL facts -------------------------------------------------------------

def instance_facts(path):
    """{qualified tag: {year key: dollars}} for undimensioned full-year facts."""
    root = ET.parse(path).getroot()
    periods = {}
    for c in root.iter(X + "context"):
        if c.find(f"{X}entity/{X}segment") is not None:
            continue
        p = c.find(X + "period")
        span = (p.findtext(X + "startDate"), p.findtext(X + "endDate"))
        for key, years in YEARS.items():
            if span == years:
                periods[c.get("id")] = key
    out = {}
    for _, _, tag in [REVENUE, *EXPENSES, TOTAL_EXPENSES, OPERATING_INCOME]:
        prefix, local = tag.split(":")
        values = {}
        for e in root.iter(NS[prefix] + local):
            key = periods.get(e.get("contextRef"))
            if key is None:
                continue
            v = int(e.text)
            if values.setdefault(key, v) != v:
                raise SystemExit(f"{tag} {key}: conflicting values {values[key]} and {v}")
        if set(values) != set(YEARS):
            raise SystemExit(f"{tag}: missing years in instance, found {sorted(values)}")
        out[tag] = values
    return out


def crosscheck_companyfacts(path, facts):
    """us-gaap tags must match companyfacts exactly; extension tags are absent there."""
    cf = json.loads(path.read_text(encoding="utf-8"))["facts"]["us-gaap"]
    ends = {end: key for key, (_, end) in YEARS.items()}
    result = {}
    for tag, values in facts.items():
        prefix, local = tag.split(":")
        if prefix != "us-gaap":
            result[tag] = "extension tag, not in companyfacts"
            continue
        found = {}
        for f in cf[local]["units"]["USD"]:
            if f["accn"] != ACCESSION or "start" not in f or f["end"] not in ends:
                continue
            days = (date.fromisoformat(f["end"]) - date.fromisoformat(f["start"])).days
            if 350 <= days <= 380:
                found[ends[f["end"]]] = f["val"]
        if found != values:
            raise SystemExit(f"{tag}: instance {values} != companyfacts {found}")
        result[tag] = "matches companyfacts"
    return result


def thousands(dollars):
    if dollars % 1000:
        raise SystemExit(f"{dollars} is not a whole number of thousands")
    return dollars // 1000


# --- 10-K text ---------------------------------------------------------------

def pages(path):
    """[(printed page number or None, flattened text)] split on page breaks."""
    raw = path.read_text(encoding="utf-8")
    out = []
    for chunk in re.split(r"<hr[^>]*page-break-after:always[^>]*>", raw):
        text = re.sub(r"<[^>]+>", " ", chunk)
        text = re.sub(r"\s+", " ", html.unescape(text).replace("\xa0", " ")).strip()
        footer = re.search(r"(\d{1,3})$", text)
        out.append((int(footer.group(1)) if footer else None, text))
    return out


def norm(text):
    """Canonical form for quote matching: straight quotes, single spaces."""
    for a, b in (("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"'), ("\xa0", " ")):
        text = text.replace(a, b)
    return re.sub(r"\s+", " ", text).strip()


def mdna(page_list):
    """[{page, text}] for Item 7, from its heading up to Item 7A."""
    start = [i for i, (_, t) in enumerate(page_list) if "ITEM 7. MANAGEMENT" in t]
    end = [i for i, (_, t) in enumerate(page_list) if "ITEM 7A. QUANTITATIVE" in t]
    if len(start) != 1 or len(end) != 1:
        raise SystemExit(f"Item 7 bounds not unique: start {start}, end {end}")
    out = []
    for i in range(start[0], end[0] + 1):
        page, text = page_list[i]
        if i == start[0]:
            text = text[text.index("ITEM 7. MANAGEMENT"):]
        if i == end[0]:
            text = text[:text.index("ITEM 7A. QUANTITATIVE")]
        if page is not None:
            text = re.sub(rf"\s*{page}$", "", text)  # drop the page footer
        out.append({"page": page, "text": norm(text)})
    return out


def find_page(page_list, marker):
    hits = [(n, t) for n, t in page_list if marker in t]
    if len(hits) != 1:
        raise SystemExit(f"expected one page containing {marker!r}, found {len(hits)}")
    return hits[0]


def match(pattern, text, what):
    m = re.search(pattern, text)
    if not m:
        raise SystemExit(f"{what}: no match for {pattern!r}")
    return m


def stats(page_list):
    page, text = find_page(page_list, "Key financial and operating metrics for 2025 and 2024")
    match(r"2025 2024 Change % Change", text, "stats table column order")
    tons = match(r"LTL tons \(in thousands\) ([\d,]+) ([\d,]+) ", text, "LTL tons")
    cwt = match(r"LTL revenue per hundredweight \$ ([\d.]+) \$ ([\d.]+) ", text, "LTL revenue per hundredweight")
    return {
        "ltl_tons_thousands": {
            "fy2025": int(tons.group(1).replace(",", "")),
            "fy2024": int(tons.group(2).replace(",", "")),
            "page": page,
            "row_text": tons.group(0).strip(),
        },
        "ltl_revenue_per_hundredweight": {
            "fy2025": cwt.group(1),
            "fy2024": cwt.group(2),
            "page": page,
            "row_text": cwt.group(0).strip(),
        },
    }


def audit_percent_table(page_list, facts):
    """Each line's share of revenue must round to the MD&A percent table.

    Proves the tag-to-label mapping is structural, not just plausible. The
    company rounds the printed column so it foots to its printed total, so a
    0.1-point difference is recorded as a disagreement (both values kept);
    anything larger, or a printed column that does not foot, fails.
    """
    page, text = find_page(page_list, "expenses and other items as a percentage of revenue")
    rev = facts[REVENUE[2]]
    disagreements = []
    printed_cols = {"fy2025": {}, "fy2024": {}}
    for _, label, tag in [*EXPENSES, TOTAL_EXPENSES, OPERATING_INCOME]:
        m = match(re.escape(label) + r"\s+([\d.]+)\s*%?\s+([\d.]+)", text, f"percent table row {label}")
        for key, printed in (("fy2025", m.group(1)), ("fy2024", m.group(2))):
            printed_cols[key][tag] = Decimal(printed)
            exact = Decimal(facts[tag][key]) * 100 / Decimal(rev[key])
            share = exact.quantize(Decimal("0.1"), ROUND_HALF_UP)
            if abs(share - Decimal(printed)) > Decimal("0.1"):
                raise SystemExit(f"{label} {key}: computed {share}% vs MD&A {printed}% (page {page})")
            if share != Decimal(printed):
                disagreements.append({"label": label, "year": key, "page": page,
                                      "printed_pct": printed, "computed_pct": str(exact.quantize(Decimal("0.001")))})
    for key, col in printed_cols.items():
        if sum(col[t] for _, _, t in EXPENSES) != col[TOTAL_EXPENSES[2]]:
            raise SystemExit(f"{key}: printed percent column does not foot to its total (page {page})")
    return page, disagreements


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    ua = user_agent()
    inst = fetch(f"{FILING_DIR}/{INSTANCE}", INSTANCE, ua)
    doc = fetch(f"{FILING_DIR}/{DOCUMENT}", DOCUMENT, ua)
    cf = fetch(COMPANYFACTS, f"companyfacts-CIK{CIK:010d}.json", ua)

    facts = instance_facts(inst)
    checks = crosscheck_companyfacts(cf, facts)

    for key in YEARS:
        lines = sum(facts[t][key] for _, _, t in EXPENSES)
        total = facts[TOTAL_EXPENSES[2]][key]
        if lines != total:
            raise SystemExit(f"{key}: expense lines {lines} != {TOTAL_EXPENSES[2]} {total}")
        oi = facts[REVENUE[2]][key] - total
        if oi != facts[OPERATING_INCOME[2]][key]:
            raise SystemExit(f"{key}: revenue - expenses {oi} != {OPERATING_INCOME[2]}")

    page_list = pages(doc)
    pct_page, disagreements = audit_percent_table(page_list, facts)

    out = {
        "filing": {
            "company": "Old Dominion Freight Line, Inc.",
            "cik": CIK,
            "accession": ACCESSION,
            "document_url": f"{FILING_DIR}/{DOCUMENT}",
            "index_url": f"{FILING_DIR}/{ACCESSION}-index.html",
            "percent_table_page": pct_page,
        },
        "percent_table_disagreements": disagreements,
        "unit": "USD thousands",
        "lines": [
            {
                "key": key,
                "label": label,
                "tag": tag,
                "fy2024": thousands(facts[tag]["fy2024"]),
                "fy2025": thousands(facts[tag]["fy2025"]),
                "source": "instance " + INSTANCE,
                "crosscheck": checks[tag],
            }
            for key, label, tag in [REVENUE, *EXPENSES, TOTAL_EXPENSES, OPERATING_INCOME]
        ],
    }
    (ROOT / "data" / "facts.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    (ROOT / "data" / "stats.json").write_text(json.dumps(stats(page_list), indent=2) + "\n", encoding="utf-8")
    md = mdna(page_list)
    (ROOT / "data" / "mdna.json").write_text(json.dumps(md, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"mdna.json: Item 7, pages {md[0]['page']}-{md[-1]['page']}, {sum(len(p['text'].split()) for p in md):,} words")
    print(f"facts.json: {len(out['lines'])} lines, footed both years; percent table audit passed (page {pct_page}), "
          f"{len(disagreements)} rounding disagreement(s) recorded")
    for d in disagreements:
        print(f"  {d['label']} {d['year']}: printed {d['printed_pct']}%, computed {d['computed_pct']}%")
    print("stats.json: written")


if __name__ == "__main__":
    main()
