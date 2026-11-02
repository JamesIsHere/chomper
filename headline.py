"""Ten years of revenue, operating income (where the company reports it), pre-tax income and margin, with
every break marked.

The long window of the time-windows rule: headline numbers only. Values come from SEC companyfacts
(the facts in every 10-K the company filed). For each year the latest 10-K that reports it wins (a value
only rounded more coarsely is not a restatement; the precise one is kept); every other value a 10-K
reported for that year is kept as a restatement. Tags change over a decade (ASC 606 renamed revenue, the
2019+ taxonomy renamed pre-tax income), so a tag joins the series only where it matches the series in a
year both cover. The series is anchored on the five-year page: in the years of its latest filing, revenue
and pre-tax income must equal data/history/<TICKER>.json exactly, and in all five of its years the page's
values are used, so the two pages never show different numbers.

Breaks, read from each year's 10-K XBRL instance:
  acquisitions  every business combination tagged with its consideration on the BusinessAcquisitionAxis;
                marked significant under SEC Regulation S-X Rule 1-02(w)(1)(i), the investment test:
                consideration >= 10% of the buyer's total assets at the prior fiscal year end. A year whose
                cash paid for businesses or goodwill acquired reaches that size with no significant deal
                tagged fails the run.
  restatements  every disagreement between 10-Ks about the same year; years before a restated stretch are
                on the old basis.

Changes year over year are on one accounting basis: each comes from the latest 10-K that shows both years, so
a recast (restatement, retrospective change in principle, reclassification, discontinued operations) never
shows up as growth. Modified retrospective adoptions recast nothing and stay a marked break.
  ASC 606/842   the fiscal year each became required, from the company's fiscal year start. Early adoption
                is not read (the XBRL tagging of adoption is inconsistent across filers); a fully
                retrospective early adoption shows up as a restatement instead.

Usage: python headline.py TICKER   (run history.py TICKER first)
"""
import html
import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import date

from history import OUT as HISTORY, X, all_ten_ks, get, get_json, labels
from pull import ROOT, user_agent

OUT = ROOT / "data" / "headline"
HAND = ROOT / "data" / "by_hand" / "acquisitions.json"
# The long window starts at fiscal 2007, the pre-crisis peak (James, 2026-11-02): the fiscal year ending between
# 1 July 2007 and 30 June 2008, the one that most nearly covers calendar 2007.
FIRST = ("2007-07-01", "2008-06-30")
SIGNIFICANT = 0.10  # S-X Rule 1-02(w)(1)(i), investment test
FORMS = ("10-K", "10-K/A")
REVENUE = re.compile(r"^(Revenues|RevenuesNetOfInterestExpense|RevenueFromContractWithCustomer\w*|SalesRevenue\w*)$")
OPERATING = ["OperatingIncomeLoss"]
PRETAX = ["IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
          "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments"]
# Deal size, best evidence first: consideration; net assets acquired including goodwill (equal to consideration
# under ASC 805 absent a bargain purchase; JNJ tags Actelion only this way); cash paid for that one business.
SIZE = [("consideration", {"BusinessCombinationConsiderationTransferred1", "BusinessCombinationConsiderationTransferred",
                           "BusinessAcquisitionCostOfAcquiredEntityPurchasePrice"}),
        ("net assets acquired", {"BusinessCombinationRecognizedIdentifiableAssetsAcquiredGoodwillAndLiabilitiesAssumedNet"}),
        ("cash paid", {"PaymentsToAcquireBusinessesGross"}),
        ("cash paid net of cash acquired", {"PaymentsToAcquireBusinessesNetOfCashAcquired"})]
SPEND = ["PaymentsToAcquireBusinessesNetOfCashAcquired", "PaymentsToAcquireBusinessesGross",
         "GoodwillAcquiredDuringPeriod"]
AXIS = "us-gaap:BusinessAcquisitionAxis"
XDI = "{http://xbrl.org/2006/xbrldi}"


def days(a, b):
    return (date.fromisoformat(b) - date.fromisoformat(a)).days


def zeros(v):
    """Trailing zeros of a whole-dollar value, capped at millions: its reporting precision."""
    n = 0
    while n < 6 and v and v % 10 ** (n + 1) == 0:
        n += 1
    return n


def annual(g, tag):
    """{period end: [(filed, value, accession)]} for one-year USD facts from 10-K filings."""
    out = {}
    for r in g.get(tag, {}).get("units", {}).get("USD", []):
        if r.get("form") in FORMS and "start" in r and 350 <= days(r["start"], r["end"]) <= 380:
            out.setdefault(r["end"], []).append((r["filed"], r["val"], r["accn"]))
    return out


def same(a, b):
    """True if two values agree at the coarser one's precision (round half away from zero, as filers do)."""
    q = 10 ** max(zeros(a), zeros(b))

    def r(v):
        return (abs(v) + q // 2) // q * q * (1 if v >= 0 else -1)
    return r(a) == r(b)


def series(g, candidates, reference, page, what):
    """({end: value}, [tags used], [disagreements]) back to fiscal 2007 (FIRST), ending at the reference's last year.
    reference: the five-year page's latest-filing years, which a tag must match to anchor the series.
    page: all five years of the five-year page; in those years its value is used, so the pages agree."""
    have = {t: f for t in candidates if (f := annual(g, t))}

    def latest(f, e):
        return max(f[e])[1]
    accepted = [t for t, f in have.items() if all(e in f and latest(f, e) == v for e, v in reference.items())]
    if not accepted:
        raise SystemExit(f"{what}: no companyfacts tag matches the five-year page in {sorted(reference)}")
    last = max(reference)

    def winner(e):
        rows = [(filed, v, a, t) for t in accepted for filed, v, a in have[t].get(e, [])]
        top = max(r[0] for r in rows)
        values = {r[1] for r in rows if r[0] == top}
        if len(values) != 1:
            raise SystemExit(f"{what} {e}: the latest filing reports different values under the tags used "
                             f"{sorted((r[3], r[1]) for r in rows if r[0] == top)}")
        value = values.pop()
        if e in page and any(r[1] == page[e] for r in rows):
            return page[e], rows
        # A filer that moves to coarser rounding (PGR: tenths of millions, then millions) has not restated:
        # keep the most precise value that agrees with the latest one, as history.py does within one filing.
        return min((r[1] for r in rows if same(r[1], value)), key=zeros), rows

    while True:
        ends = sorted(e for e in {e for t in accepted for e in have[t]} if FIRST[0] <= e <= last)
        if ends and ends[0] <= FIRST[1]:
            break
        joiners = [t for t, f in have.items() if t not in accepted and any(e < ends[0] for e in f)
                   and any(e in f and latest(f, e) == winner(e)[0] for e in ends)]
        if not joiners:
            raise SystemExit(f"{what}: starts {ends[0] if ends else 'nowhere'}, not fiscal 2007; no other tag "
                             f"reaches further back and matches the series in a shared year")
        accepted += joiners
    out, disagreements = {}, []
    for e in ends:
        value, rows = winner(e)
        out[e] = value
        seen = set()
        for filed, v, a, t in sorted(rows, reverse=True):
            if not same(v, value) and (v, a) not in seen:
                seen.add((v, a))
                disagreements.append({"item": what, "period_end": e, "value": value, "other_value": v,
                                      "other_accession": a, "other_filed": filed, "tag": t})
    for a, b in zip(ends, ends[1:]):
        if not 350 <= days(a, b) <= 380:
            raise SystemExit(f"{what}: fiscal years {a} and {b} are not consecutive")
    return out, [t for t in accepted if any(e in have[t] for e in ends)], disagreements


def pairs(g, tags, levels, what):
    """{end: comparison} for each year after the first, on one accounting basis: the latest 10-K that reports
    both the year and the one before it (every 10-K presents its comparative year on its own basis). basis_changed:
    that 10-K's figures differ from the levels shown, because a later filing recast one of the two years, so the
    change is not the ratio of the levels."""
    by = {}  # accession: (filed, {end: {values}})
    for t in tags:
        for e, rows in annual(g, t).items():
            for filed, v, a in rows:
                by.setdefault(a, (filed, {}))[1].setdefault(e, set()).add(v)
    ends, out = list(levels), {}
    for prev, e in zip(ends, ends[1:]):
        both = [(filed, a) for a, (filed, vals) in by.items() if prev in vals and e in vals]
        if not both:
            raise SystemExit(f"{what} {e}: no 10-K reports both {prev} and {e}")
        filed, a = max(both)
        vals = by[a][1]

        def one(end):
            best = min(vals[end], key=zeros)  # the most precise of the values this filing gives the year
            if any(not same(v, best) for v in vals[end]):
                raise SystemExit(f"{what} {end}: 10-K {a} reports {sorted(vals[end])} under {tags}")
            return best
        p, v = one(prev), one(e)
        out[e] = {"prior_end": prev, "prior": p, "value": v, "accession": a, "filed": filed,
                  "basis_changed": not (same(p, levels[prev]) and same(v, levels[e]))}
    return out


def instant(g, tag, near):
    """Latest-filed 10-K value of an instant fact dated within three weeks of `near`."""
    rows = [(r["filed"], r["end"], r["val"]) for r in g.get(tag, {}).get("units", {}).get("USD", [])
            if r.get("form") in FORMS and "start" not in r and abs(days(near, r["end"])) <= 21]
    if not rows:
        raise SystemExit(f"{tag}: no 10-K value near {near}")
    return max(rows)[2]


def instance_names(cik, filing, ua):
    """Candidate XBRL instance files in a 10-K (inline filings: *_htm.xml; older: plain .xml); [] before XBRL."""
    acc = filing["accession"].replace("-", "")
    base = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc}"
    names = [i["name"] for i in get_json(f"{base}/index.json", f"{cik}/{acc}/index.json", ua)["directory"]["item"]]
    return [n for n in names if n.endswith("_htm.xml")] or [
        n for n in names if n.endswith(".xml") and n != "FilingSummary.xml"
        and not re.search(r"(_(cal|def|lab|pre)|^R\d+|^defnref)\.xml$", n)]  # early filings: rendering files


def by_hand(ticker, end, cik, filing, ua):
    """The hand record for one pre-XBRL year: {deals, spend, prior_total_assets, sources}. Every source quote must
    appear verbatim (whitespace collapsed) in the named document of a filing, and the spend and prior total assets
    must each appear, in millions as the filing prints them, in one of the quotes."""
    records = json.loads(HAND.read_text(encoding="utf-8")) if HAND.exists() else {}
    rec = records.get(ticker, {}).get(end)
    if rec is None:
        raise SystemExit(f"{end}: 10-K {filing['accession']} predates XBRL; read its acquisitions and the prior "
                         f"year's total assets and record them in {HAND.relative_to(ROOT)} under {ticker} {end}")
    quotes = []
    for s in rec["sources"]:
        acc = s["accession"].replace("-", "")
        page = get(f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{s['document']}",
                   f"{cik}/{acc}/{s['document']}", ua).read_text(encoding="utf-8", errors="replace")
        text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", page)))
        if s["quote"] not in text:
            raise SystemExit(f"{ticker} {end}: quote not found verbatim in {s['accession']} {s['document']}: "
                             f"{s['quote']!r}")
        quotes.append(s["quote"])
    for what in ("spend", "prior_total_assets"):
        v = rec[what]
        if v % 1_000_000 or not any(f"{v // 1_000_000:,}" in q for q in quotes):
            raise SystemExit(f"{ticker} {end}: {what} {v:,} does not appear in millions in any quote")
    for d in rec["deals"]:
        if not any(f"{d['size'] // 1_000_000:,}" in q for q in quotes):
            raise SystemExit(f"{ticker} {end}: deal {d['name']} size {d['size']:,} does not appear in any quote")
    return rec


def instance(cik, filing, ua):
    """Local path to a 10-K's XBRL instance."""
    acc = filing["accession"].replace("-", "")
    base = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc}"
    hits = instance_names(cik, filing, ua)
    if len(hits) != 1:
        raise SystemExit(f"{filing['accession']}: expected one XBRL instance, found {hits}")
    return get(f"{base}/{hits[0]}", f"{cik}/{acc}/{hits[0]}", ua)


def member_name(cik, accession, member, ua):
    """The deal's name as the filing labels it (msft:ActivisionBlizzardIncMember -> Activision Blizzard, Inc.)."""
    acc = accession.replace("-", "")
    base = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc}"
    names = [i["name"] for i in get_json(f"{base}/index.json", f"{cik}/{acc}/index.json", ua)["directory"]["item"]]
    hits = [n for n in names if n.endswith("_lab.xml")] or [n for n in names if n.endswith(".xsd")]
    if len(hits) != 1:
        raise SystemExit(f"{accession}: expected one label file, found {hits}")
    text = labels(get(f"{base}/{hits[0]}", f"{cik}/{acc}/{hits[0]}", ua)).get(member.replace(":", "_"), {})
    # The standard label is often generated from the tag name ("Linked In Corporation"); the documentation
    # label is the name the filer wrote ("LinkedIn Corporation.").
    role = "http://www.xbrl.org/2003/role/"
    label = text.get(role + "documentation") or text.get(role + "terseLabel") or text.get(role + "label")
    if not label:
        raise SystemExit(f"{accession}: no label for {member}")
    return label.strip().removesuffix(".").removesuffix("[Member]").strip()


def standards(ends):
    """The fiscal year each standard became required: the first that begins after the effective date."""
    out = []
    for name, after in (("ASC 606 (revenue)", "2017-12-15"), ("ASC 842 (leases)", "2018-12-15")):
        for prev, e in zip(ends, ends[1:]):
            if prev >= after:  # the year starting the day after `prev` begins after the effective date
                out.append({"standard": name, "fiscal_year_end": e, "required_for_years_beginning_after": after})
                break
        else:
            raise SystemExit(f"{name}: no fiscal year in {ends[0]}..{ends[-1]} begins after {after}")
    return out


def deals(path):
    """{member: (rank, date, value, measure)} for USD facts on the BusinessAcquisitionAxis alone, sized by the
    best-ranked SIZE measure the filing tags for that deal, at its earliest date. One deal tagged under two
    members (PLD's Liberty) has the same date and amount: kept once."""
    root = ET.parse(path).getroot()
    usd = {u.get("id") for u in root.iter(X + "unit") if (u.findtext(X + "measure") or "").strip() == "iso4217:USD"}
    ctx = {}
    for c in root.iter(X + "context"):
        dims = {m.get("dimension"): m.text.strip() for m in c.iter(XDI + "explicitMember")}
        if list(dims) == [AXIS]:
            p = c.find(X + "period")
            ctx[c.get("id")] = (dims[AXIS], p.findtext(X + "endDate") or p.findtext(X + "instant"))
    rank = {tag: (i, measure) for i, (measure, tags) in enumerate(SIZE) for tag in tags}
    best = {}
    for el in root:
        key, local = ctx.get(el.get("contextRef")), el.tag.split("}")[-1]
        if key is None or el.text is None or local not in rank or el.get("unitRef") not in usd:
            continue
        (member, when), (r, measure) = key, rank[local]
        v = int(float(el.text.strip()))
        have = best.get(member)
        if have is None or (r, when) < have[:2]:
            best[member] = (r, when, v, measure)
        elif (r, when) == have[:2]:
            if abs(have[2] - v) > 0.01 * max(have[2], v):
                raise SystemExit(f"{path.name} {member} {when}: {measure} {have[2]:,} and {v:,} in one filing")
            best[member] = (r, when, max(have[2], v), measure)
    kept = {}
    for member, d in sorted(best.items()):
        kept.setdefault((d[1], d[2]), (member, d))
    return dict(kept.values())


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: python headline.py TICKER")
    ticker = sys.argv[1].upper()
    h = json.loads((HISTORY / f"{ticker}.json").read_text(encoding="utf-8"))
    cik, ua = h["cik"], user_agent()
    g = get_json(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json",
                 f"companyfacts-CIK{cik:010d}.json", ua)["facts"]["us-gaap"]
    anchor_years = h["filings"][0]["years"]  # the five-year page's latest filing
    revenue, rev_tags, d1 = series(g, [t for t in g if REVENUE.match(t)],
                                   {e: h["revenue"][e] for e in anchor_years}, h["revenue"], "revenue")
    pretax, pre_tags, d2 = series(g, PRETAX, {e: h["pretax_income"][e] for e in anchor_years},
                                  h["pretax_income"], "pre-tax income")
    if list(revenue) != list(pretax):
        raise SystemExit(f"revenue years {list(revenue)} != pre-tax income years {list(pretax)}")
    operating, op_tags, d3 = None, [], []
    if h["operating_income"] is not None:  # only where the five-year page has it (banks and insurers report none)
        operating, op_tags, d3 = series(g, OPERATING, {e: h["operating_income"][e] for e in anchor_years},
                                        h["operating_income"], "operating income")
        if list(operating) != list(revenue):
            raise SystemExit(f"operating income years {list(operating)} != revenue years {list(revenue)}")
    ends = list(revenue)
    off_page = [(e, what) for e in h["period_ends"] if e in revenue
                for what, a, b in (("revenue", revenue[e], h["revenue"][e]),
                                   ("pre-tax income", pretax[e], h["pretax_income"][e]))
                + ((("operating income", operating[e], h["operating_income"][e]),) if operating else ())
                if a != b]

    # One 10-K per year; deals of a fiscal year appear in that year's 10-K and the next.
    filings = {}
    tens = all_ten_ks(cik, ua)
    for e in ends:
        hits = [f for f in tens if abs(days(f["report_date"], e)) <= 21]
        if len(hits) != 1:
            raise SystemExit(f"{e}: expected one 10-K, found {[f['accession'] for f in hits]}")
        filings[e] = hits[0]
    # A 10-K filed before the company's first XBRL filing has no instance: that year's acquisitions come from a
    # record written by hand from the filing (data/by_hand/acquisitions.json), its quotes checked verbatim.
    hand = {e: by_hand(ticker, e, cik, filings[e], ua) for e in ends if not instance_names(cik, filings[e], ua)}
    found = {}
    for e in ends:  # oldest first: for the same deal, measure and date, the later filing's value wins
        if e in hand:
            continue
        for member, (r, when, v, measure) in deals(instance(cik, filings[e], ua)).items():
            have = found.get(member)
            if have is None or (r, when) <= have[:2]:
                found[member] = (r, when, v, measure, filings[e]["accession"])
    # A fiscal year runs from the day after the prior year's end through its own end.
    prior_end = dict(zip(ends[1:], ends[:-1])) | {ends[0]: str(int(ends[0][:4]) - 1) + ends[0][4:]}
    def prior_assets(e):
        if e in hand:
            return hand[e]["prior_total_assets"]
        return instant(g, "Assets", date.fromordinal(date.fromisoformat(e).toordinal() - 365).isoformat())
    out_deals = []
    for member, (_, when, v, measure, acc) in sorted(found.items(), key=lambda kv: kv[1][1]):
        year = next((e for e in ends if prior_end[e] < when <= e), None)
        if year is None:
            continue  # outside the window
        if year in hand:  # a later filing tags a deal of a hand-recorded year: the record must hold it, same size
            rec = {d["member"]: d for d in hand[year]["deals"]}
            if member not in rec or not same(rec[member]["size"], v):
                raise SystemExit(f"{member} {when}: tagged in {acc} at {v:,} but the hand record for {year} "
                                 f"{'has ' + format(rec[member]['size'], ',') if member in rec else 'lacks it'}")
            continue
        assets = prior_assets(year)
        out_deals.append({"name": member_name(cik, acc, member, ua), "member": member, "date": when, "fiscal_year_end": year,
                          "size": v, "measure": measure, "prior_total_assets": assets, "share_of_assets": v / assets,
                          "significant": v / assets >= SIGNIFICANT, "accession": acc})
    for e, rec in hand.items():
        a = rec["prior_total_assets"]
        out_deals += [d | {"fiscal_year_end": e, "prior_total_assets": a, "share_of_assets": d["size"] / a,
                           "significant": d["size"] / a >= SIGNIFICANT, "accession": filings[e]["accession"],
                           "by_hand": True} for d in rec["deals"]]
    out_deals.sort(key=lambda d: d["date"])
    for e in ends:  # spend the tagged deals leave unexplained, large enough to be a significant deal of its own
        assets = prior_assets(e)
        tagged = sum(d["size"] for d in out_deals if d["fiscal_year_end"] == e)
        spends = ([("spend recorded by hand", hand[e]["spend"])] if e in hand else
                  [(t, max(f[e])[1] if e in (f := annual(g, t)) else 0) for t in SPEND])
        for tag, spend in spends:
            if (spend - tagged) / assets >= SIGNIFICANT:
                raise SystemExit(f"{e}: {tag} {spend:,} leaves {spend - tagged:,} ({(spend - tagged) / assets:.0%} "
                                 f"of prior total assets) not explained by the deals tagged that year")

    out = {"ticker": ticker, "company": h["company"], "cik": cik, "unit": "USD", "period_ends": ends,
           "revenue": revenue, "operating_income": operating, "pretax_income": pretax, "revenue_tags": rev_tags,
           "operating_tags": op_tags, "pretax_tags": pre_tags,
           "changes": {"revenue": pairs(g, rev_tags, revenue, "revenue"),
                       "operating_income": pairs(g, op_tags, operating, "operating income") if operating else None,
                       "pretax_income": pairs(g, pre_tags, pretax, "pre-tax income")},
           "disagreements": d1 + d2 + d3, "differs_from_five_year_page": off_page, "deals": out_deals,
           "standards": standards(ends),
           "significance_test": "SEC Regulation S-X Rule 1-02(w)(1)(i): consideration >= 10% of total assets "
                                "at the prior fiscal year end",
           "filings": {e: {k: f[k] for k in ("accession", "report_date")} for e, f in filings.items()}}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{ticker}.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    sig = [d for d in out_deals if d["significant"]]
    print(f"data/headline/{ticker}.json: {ends[0]} to {ends[-1]}; revenue tags {rev_tags}; operating tags "
          f"{op_tags or 'none (not reported)'}; pre-tax tags {[t[:60] for t in pre_tags]}; "
          f"{len(d1 + d2 + d3)} restated value(s); {len(out_deals)} deal(s), "
          f"{len(sig)} significant: " + ", ".join(f"{d['name']} {d['date']} {d['share_of_assets']:.0%} "
                                                  f"({d['measure']})" for d in sig))
    for e, what in off_page:
        print(f"  [!] {what} {e} differs from the five-year page")
    for what, ch in out["changes"].items():
        for e, c in (ch or {}).items():
            if c["basis_changed"]:
                print(f"  basis changed: {what} {c['prior_end']} -> {e} measured in {c['accession']}: "
                      f"{c['prior']:,} -> {c['value']:,} ({(c['value'] - c['prior']) / abs(c['prior']):+.1%})")


if __name__ == "__main__":
    main()
