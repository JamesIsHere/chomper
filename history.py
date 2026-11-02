"""Five years of any company's income statement, split into demand and ratio effects.

Anchored on pre-tax income, which every industry reports; operating income is kept as a
subtotal where the company reports one.

For a ticker, finds its latest 10-K and the 10-K two years earlier (three years
each, overlapping on one year), reads the face income statement from each
filing's own XBRL (presentation for order and labels, calculation for how lines
roll up to operating income), and writes data/history/<TICKER>.json. Each line's
year-over-year change is split exactly into:

  flex   = last year's (line / revenue) x this year's revenue change
  ratio  = actual change - flex

Every year must foot: revenue minus the cost lines equals operating income.
Raw downloads are cached in data/raw/<cik>/. Every check fails loud.

Usage: python history.py TICKER
"""
import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import date

from pull import ROOT, RAW, fetch, user_agent

OUT = ROOT / "data" / "history"
X = "{http://www.xbrl.org/2003/instance}"
LINK = "{http://www.xbrl.org/2003/linkbase}"
XLINK = "{http://www.w3.org/1999/xlink}"
OPERATING_INCOME = "us-gaap_OperatingIncomeLoss"
# Anchor: pre-tax income, reported by every industry. Preferred tag first; the second is used by filers
# that show equity-method income below the pre-tax line.
PRETAX = ["us-gaap_IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
          "us-gaap_IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments"]
REVENUE = re.compile(r"^us-gaap_(Revenues|RevenuesNetOfInterestExpense|RevenueFromContractWithCustomer\w*"
                     r"|SalesRevenue\w*)$")
WHOLE = re.compile(r"-?\d+(\.0+)?")  # some filers write 349000000.0
STATEMENT = re.compile(r"operations|income|earnings", re.I)
NOT_STATEMENT = re.compile(r"parenthetical|comprehensive", re.I)


def get(url, name, ua):
    (RAW / name).parent.mkdir(parents=True, exist_ok=True)
    return fetch(url, name, ua)


def get_json(url, name, ua):
    return json.loads(get(url, name, ua).read_text(encoding="utf-8"))


def cik_for(ticker, ua):
    for row in get_json("https://www.sec.gov/files/company_tickers.json", "company_tickers.json", ua).values():
        if row["ticker"] == ticker:
            return row["cik_str"], row["title"]
    raise SystemExit(f"ticker {ticker} not in SEC company_tickers.json")


def all_ten_ks(cik, ua):
    """Every original 10-K, newest first."""
    sub = get_json(f"https://data.sec.gov/submissions/CIK{cik:010d}.json", f"{cik}/submissions.json", ua)
    pages = [sub["filings"]["recent"]]  # heavy filers spill older filings into extra pages
    for extra in sub["filings"].get("files", []):
        pages.append(get_json(f"https://data.sec.gov/submissions/{extra['name']}", f"{cik}/{extra['name']}", ua))
    filings = sorted(({"accession": a, "report_date": d, "document": p}
                      for r in pages
                      for f, a, d, p in zip(r["form"], r["accessionNumber"], r["reportDate"], r["primaryDocument"])
                      if f == "10-K"), key=lambda f: f["report_date"], reverse=True)
    if not filings:
        raise SystemExit(f"CIK {cik}: no 10-K filings")
    return filings


def ten_ks(cik, ua):
    """Latest original 10-K and the one whose period ends two years earlier."""
    filings = all_ten_ks(cik, ua)
    latest = filings[0]
    # Two fiscal years back; 52/53-week years drift a few days, so match by distance, not calendar year.
    target = date.fromisoformat(latest["report_date"]).toordinal() - 730
    older = [f for f in filings if abs(date.fromisoformat(f["report_date"]).toordinal() - target) <= 21]
    if len(older) != 1:
        raise SystemExit(f"CIK {cik}: expected one 10-K about two years before {latest['report_date']}, "
                         f"found {[f['report_date'] for f in older]}")
    return latest, older[0]


def filing_files(cik, filing, ua):
    """Local paths to the instance, presentation, calculation and label files plus FilingSummary."""
    acc = filing["accession"].replace("-", "")
    base = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc}"
    names = [i["name"] for i in get_json(f"{base}/index.json", f"{cik}/{acc}/index.json", ua)["directory"]["item"]]
    # Linkbases ship as separate files, or (newer filings) embedded in the .xsd schema.
    want = {"instance": "_htm.xml", "pre": "_pre.xml", "cal": "_cal.xml", "lab": "_lab.xml"}
    out = {}
    for key, suffix in want.items():
        hits = [n for n in names if n.endswith(suffix)]
        if not hits and key != "instance":
            hits = [n for n in names if n.endswith(".xsd")]
        if len(hits) != 1:
            raise SystemExit(f"{filing['accession']}: expected one *{suffix} or .xsd, found {hits}")
        out[key] = get(f"{base}/{hits[0]}", f"{cik}/{acc}/{hits[0]}", ua)
    out["summary"] = get(f"{base}/FilingSummary.xml", f"{cik}/{acc}/FilingSummary.xml", ua)
    filing["document_url"] = f"{base}/{filing['document']}"
    filing["index_url"] = f"{base}/{filing['accession']}-index.html"
    return out


def statement_role(summary_path):
    """Role URI of the income statement, from the filing's own report list."""
    reports = ET.parse(summary_path).getroot().iter("Report")
    statements = [(r.findtext("ShortName"), r.findtext("Role")) for r in reports
                  if r.findtext("MenuCategory") == "Statements"]
    hits = [s for s in statements if STATEMENT.search(s[0]) and not NOT_STATEMENT.search(s[0])]
    if not hits:  # some filers present income and OCI as one statement
        hits = [s for s in statements if STATEMENT.search(s[0]) and "parenthetical" not in s[0].lower()]
    if len(hits) != 1:
        raise SystemExit(f"income statement not unique among statements: {[s[0] for s in statements]}")
    return hits[0]


def concept(href):
    return href.split("#", 1)[1]


def arcs(path, role, arc_tag):
    """[(parent, child, attrs)] for one extended link role, in document order."""
    for link in ET.parse(path).getroot().iter(LINK + arc_tag.replace("Arc", "Link")):
        if link.get(XLINK + "role") != role:
            continue
        locs = {l.get(XLINK + "label"): concept(l.get(XLINK + "href")) for l in link.iter(LINK + "loc")}
        return [(locs[a.get(XLINK + "from")], locs[a.get(XLINK + "to")], a.attrib) for a in link.iter(LINK + arc_tag)]
    raise SystemExit(f"role {role} not in {path.name}")


def presentation_order(path, role):
    """[(concept, preferred label role)] depth-first in printed order."""
    children, parents = {}, set()
    for p, c, a in arcs(path, role, "presentationArc"):
        children.setdefault(p, []).append((float(a.get("order", 0)), c, a.get("preferredLabel")))
        parents.add(c)
    roots = [p for p in children if p not in parents]
    out = []

    def walk(node, pref):
        out.append((node, pref))
        for _, c, pl in sorted(children.get(node, [])):
            walk(c, pl)
    for r in roots:
        walk(r, None)
    return out


def labels(path):
    """{concept: {label role: text}}."""
    root = ET.parse(path).getroot()
    out = {}
    for link in root.iter(LINK + "labelLink"):
        locs = {l.get(XLINK + "label"): concept(l.get(XLINK + "href")) for l in link.iter(LINK + "loc")}
        text = {}
        for lab in link.iter(LINK + "label"):
            text.setdefault(lab.get(XLINK + "label"), {})[lab.get(XLINK + "role")] = lab.text
        for arc in link.iter(LINK + "labelArc"):
            for role, t in text.get(arc.get(XLINK + "to"), {}).items():
                out.setdefault(locs[arc.get(XLINK + "from")], {})[role] = t
    return out


def stitch(kids, anchor, vals):
    """Children for an anchor the filer left unconnected: the set of other calculation roots whose values sum
    exactly to the anchor in every year (HD's FY2023 10-K splits operating income, non-operating items and
    pre-tax income into separate trees). None if no unique set exists."""
    from itertools import combinations
    children = {c for cs in kids.values() for c, _ in cs}
    roots = [r for r in kids if r not in children and r != anchor and r in vals]
    ends = sorted(vals.get(anchor, {}))
    found = [combo for n in (2, 3) for combo in combinations(roots, n)
             if all(all(e in vals[r] for r in combo) and sum(vals[r][e] for r in combo) == vals[anchor][e]
                    for e in ends)]
    return [(r, 1.0) for r in found[0]] if len(found) == 1 else None


def weights(path, role, vals):
    """(anchor, {leaf: weight toward pre-tax income}, {leaf: True if it rolls up through operating income},
    stitched roots or None)."""
    kids = {}
    for p, c, a in arcs(path, role, "calculationArc"):
        kids.setdefault(p, []).append((c, float(a["weight"])))
    present = [t for t in PRETAX if t in vals]
    anchors = [t for t in present if t in kids]
    stitched = None
    if not anchors and present:
        stitched = stitch(kids, present[0], vals)
        if stitched:
            kids[present[0]] = stitched
            anchors = [present[0]]
    if not anchors:
        raise SystemExit(f"no calculation for a pre-tax income tag {PRETAX} in the income statement role")
    out, operating = {}, {}

    def expand(node, w, above_oi):
        above_oi = above_oi or node == OPERATING_INCOME
        if node in kids and not REVENUE.match(node):
            for c, cw in kids[node]:
                expand(c, w * cw, above_oi)
        else:
            out[node] = out.get(node, 0) + w
            operating[node] = above_oi
    expand(anchors[0], 1.0, False)
    return anchors[0], out, operating, [r for r, _ in stitched] if stitched else None


def annual_values(path):
    """{concept: {period end: dollars}} for undimensioned facts spanning about a year."""
    root = ET.parse(path).getroot()
    ns = {}
    for _, (prefix, uri) in ET.iterparse(path, events=["start-ns"]):
        ns.setdefault(uri, prefix)
    periods, dimensioned = {}, set()
    for c in root.iter(X + "context"):
        p = c.find(X + "period")
        s, e = p.findtext(X + "startDate"), p.findtext(X + "endDate")
        if s and e and 350 <= (date.fromisoformat(e) - date.fromisoformat(s)).days <= 380:
            periods[c.get("id")] = e
            if c.find(f"{X}entity/{X}segment") is not None:
                dimensioned.add(c.get("id"))
    precise, dims = {}, {}
    for el in root:
        end = periods.get(el.get("contextRef"))
        if end is None or el.text is None or not el.tag.startswith("{"):
            continue
        if el.get("contextRef") in dimensioned:
            text = el.text.strip()
            if WHOLE.fullmatch(text):
                uri, local = el.tag[1:].split("}")
                d = el.get("decimals")
                d = 0 if d in (None, "INF") else min(int(d), 0)
                dims.setdefault(f"{ns[uri]}_{local}", {}).setdefault(end, set()).add((int(float(text)), d))
            continue
        text = el.text.strip()
        if not WHOLE.fullmatch(text):
            continue  # per-share amounts and text blocks; dollar lines are whole numbers
        uri, local = el.tag[1:].split("}")
        name = f"{ns[uri]}_{local}"
        v, dec = int(float(text)), el.get("decimals")
        dec = 0 if dec in (None, "INF") else min(int(dec), 0)
        have = precise.setdefault(name, {}).get(end)
        if have is None or dec > have[1]:
            new, old = (v, dec), have
        else:
            new, old = have, (v, dec)
        if old is not None and round(new[0], old[1]) != old[0]:  # a rounded duplicate must round to the precise one
            raise SystemExit(f"{name} {end}: conflicting values {new[0]} and {old[0]} (decimals {old[1]})")
        precise[name][end] = new
    return ({n: {e: v for e, (v, _) in d.items()} for n, d in precise.items()},
            {n: {e: k for e, (_, k) in d.items()} for n, d in precise.items()}, dims)


def read_filing(cik, filing, ua):
    files = filing_files(cik, filing, ua)
    name, role = statement_role(files["summary"])
    vals, decs, dims = annual_values(files["instance"])
    anchor, w, operating, stitched = weights(files["cal"], role, vals)
    order = presentation_order(files["pre"], role)
    labs = labels(files["lab"])
    revenue = [c for c in w if REVENUE.match(c)]
    if len(revenue) != 1 or w[revenue[0]] != 1.0:
        raise SystemExit(f"{filing['accession']}: expected one revenue concept with weight +1, got "
                         f"{[(c, w[c]) for c in revenue]}")
    ends = sorted({e for e in vals.get(anchor, {})})
    if len(ends) != 3:
        raise SystemExit(f"{filing['accession']}: expected 3 years of pre-tax income, found {ends}")
    rank = {c: i for i, (c, _) in enumerate(order)}
    prefs = dict(order)

    def label(c):
        std = "http://www.xbrl.org/2003/role/label"
        return labs.get(c, {}).get(prefs.get(c) or std) or labs.get(c, {}).get(std) or c
    lines = []
    for c in sorted((c for c in w if c != revenue[0]), key=lambda c: rank.get(c, 1e9)):
        values, from_dims, units = {}, [], {}
        for e in ends:
            values[e] = vals.get(c, {}).get(e)
            units[e] = 10 ** -decs.get(c, {}).get(e, 0)
            only = dims.get(c, {}).get(e, set())
            if values[e] is None and len(only) == 1:  # face line tagged with one dimension member (CAT)
                values[e], d = next(iter(only))
                units[e] = 10 ** -d
                from_dims.append(e)
        lines.append({"concept": c, "label": label(c), "weight": w[c], "values": values,
                      "operating": operating[c], "dimensioned_years": from_dims, "_units": units})
    rev = {e: vals[revenue[0]][e] for e in ends}
    pretax = {e: vals[anchor][e] for e in ends}

    def unit(c, e):
        return 10 ** -decs.get(c, {}).get(e, 0)

    def slack(e, subtotal, rows):
        """Half a rounding unit (the fact's own XBRL decimals) for each summed figure and the subtotal itself:
        the most the reported figures can miss by when every true amount rounds to its reported one."""
        return 0.5 * (unit(revenue[0], e) + unit(subtotal, e)
                      + sum(l["_units"][e] for l in rows if l["values"][e] is not None))
    gaps = []
    rounding = {}
    for e in ends:  # foot: revenue + sum(weight x line) == pre-tax income, within the filing's own rounding
        total = rev[e] + sum(l["weight"] * (l["values"][e] or 0) for l in lines)
        gap, allowed = pretax[e] - total, slack(e, anchor, lines)
        if abs(gap) > allowed:
            raise SystemExit(f"{filing['accession']} {e}: lines foot to {total:,.0f}, pre-tax income {pretax[e]:,}"
                             f" (gap {gap:,.0f}, rounding allows {allowed:,.0f})")
        rounding[e] = int(gap)
        if gap:
            gaps.append({"accession": filing["accession"], "period_end": e, "subtotal": "pre-tax income",
                         "lines_total": int(total), "reported": pretax[e], "gap": int(gap), "allowed": allowed})
    # Operating income is a subtotal, kept only where the company reports it inside the same statement math.
    oi = None
    rounding_op = {e: 0 for e in ends}
    if any(operating.values()):
        oi = {e: vals[OPERATING_INCOME][e] for e in ends}
        for e in ends:
            rows = [l for l in lines if l["operating"]]
            total = rev[e] + sum(l["weight"] * (l["values"][e] or 0) for l in rows)
            gap, allowed = oi[e] - total, slack(e, OPERATING_INCOME, rows)
            if abs(gap) > allowed:
                raise SystemExit(f"{filing['accession']} {e}: operating lines foot to {total:,.0f}, "
                                 f"operating income {oi[e]:,} (gap {gap:,.0f}, rounding allows {allowed:,.0f})")
            rounding_op[e] = int(gap)
            if gap:
                gaps.append({"accession": filing["accession"], "period_end": e, "subtotal": "operating income",
                             "lines_total": int(total), "reported": oi[e], "gap": int(gap), "allowed": allowed})
    for l in lines:
        del l["_units"]
    return {"statement": name, "role": role, "revenue_concept": revenue[0], "pretax_concept": anchor,
            "stitched_from": stitched,
            "revenue_label": label(revenue[0]),
            "ends": ends, "revenue": rev, "pretax_income": pretax, "operating_income": oi, "lines": lines,
            "rounding": rounding, "rounding_operating": rounding_op, "footing_gaps": gaps}


def retag(lines, older, ends, disagreements):
    """One line the company tagged differently in its two 10-Ks (CCL's interest expense: InterestExpense through
    2022, InterestExpenseNonoperating from 2023) arrives as two rows, each jumping to or from nothing. Rows become
    one only when the filing's label is identical, every tag carries figures, the years never overlap, and weight and
    section agree; the row
    keeps the latest tag and records every tag with its years. Anything short of that stays as two rows."""
    groups = {}
    for l in lines:
        groups.setdefault(l["label"], []).append(l)
    out = []
    for l in lines:
        group = groups[l["label"]]
        if len(group) == 1:
            out.append(l)
            continue
        if l is not group[0]:
            continue
        years = [{e for e in ends if g["values"][e] is not None} for g in group]
        if (not all(years) or any(a & b for i, a in enumerate(years) for b in years[i + 1:])
                or len({(g["weight"], g["operating"]) for g in group}) != 1):
            out += group
            continue
        row = dict(group[0], values={e: next((g["values"][e] for g in group if g["values"][e] is not None), None)
                                     for e in ends},
                   dimensioned_years=sorted(e for g in group for e in g["dimensioned_years"]),
                   retagged=sorted(({"concept": g["concept"], "years": sorted(y)} for g, y in zip(group, years)),
                                   key=lambda t: t["years"][0] if t["years"] else ""))
        # The year both 10-Ks show, compared across the tag change as merge() compares a line under one tag.
        old = {o["concept"]: o for o in older["lines"]}
        for e in sorted(set(older["ends"]) & set(ends)):
            later = row["values"][e]
            for g in group:
                o = old.get(g["concept"])
                if o and o["concept"] != row["concept"] and o["values"].get(e) is not None and later is not None \
                        and o["values"][e] != later:
                    disagreements.append({"item": row["label"], "period_end": e,
                                          "latest_filing": later, "earlier_filing": o["values"][e]})
        out.append(row)
    return out


def merge(latest, older):
    """Five years; overlap year taken from the latest filing, disagreements recorded."""
    ends = sorted(set(older["ends"]) | set(latest["ends"]))
    overlap = sorted(set(older["ends"]) & set(latest["ends"]))
    src = {e: (latest if e in latest["ends"] else older) for e in ends}
    disagreements = []
    for e in overlap:
        for what, a, b in (("revenue", latest["revenue"][e], older["revenue"][e]),
                           ("pre-tax income", latest["pretax_income"][e], older["pretax_income"][e])):
            if a != b:
                disagreements.append({"item": what, "period_end": e, "latest_filing": a, "earlier_filing": b})
        old = {l["concept"]: l for l in older["lines"]}
        for l in latest["lines"]:
            o = old.get(l["concept"])
            if o and o["values"][e] is not None and o["values"][e] != l["values"][e]:
                disagreements.append({"item": l["label"], "period_end": e,
                                      "latest_filing": l["values"][e], "earlier_filing": o["values"][e]})
    by = {}
    for f in (latest, older):  # latest first, so its label and weight win
        for l in f["lines"]:
            row = by.setdefault(l["concept"], {"concept": l["concept"], "label": l["label"], "weight": l["weight"],
                                               "operating": l["operating"], "values": {}, "dimensioned_years": []})
            for e in f["ends"]:
                if src[e] is f:
                    row["values"][e] = l["values"][e]
                    if e in l["dimensioned_years"]:
                        row["dimensioned_years"].append(e)
    lines = list(by.values())
    for l in lines:
        for e in ends:
            l["values"].setdefault(e, None)
    if any(l["weight"] != by[l["concept"]]["weight"] for f in (latest, older) for l in f["lines"]):
        raise SystemExit("a line changes sign between the two filings")
    lines = retag(lines, older, ends, disagreements)
    # The filing's own rounding, as its own rows, so every later check stays exact: one inside operating income,
    # one for the rest of the gap to pre-tax income.
    above = {e: src[e]["rounding_operating"][e] for e in ends}
    below = {e: src[e]["rounding"][e] - above[e] for e in ends}
    for concept, label, op, values in (("rounding_operating", "Rounding in the filing, within operating income",
                                        True, above),
                                       ("rounding", "Rounding in the filing", False, below)):
        if any(values.values()):
            lines.append({"concept": concept, "label": label, "weight": 1.0, "operating": op, "values": values,
                          "dimensioned_years": []})
    revenue = {e: src[e]["revenue"][e] for e in ends}
    pretax = {e: src[e]["pretax_income"][e] for e in ends}
    has_oi = latest["operating_income"] is not None and older["operating_income"] is not None
    oi = {e: src[e]["operating_income"][e] for e in ends} if has_oi else None
    if not has_oi:  # a filing without the subtotal: no line can be called operating across all five years
        for l in lines:
            l["operating"] = False
    return ends, revenue, pretax, oi, lines, disagreements


def split(ends, revenue, pretax, lines):
    """Per year-over-year change: each line's actual, flex and ratio effect on pre-tax income."""
    changes = []
    for prev, cur in zip(ends, ends[1:]):
        d_rev = revenue[cur] - revenue[prev]
        rows = []
        r0 = 0  # the filing's own rounding last year: not a cost, so it does not scale with revenue
        for l in lines:
            # cost = amount that reduces pre-tax income; income items come out negative
            c0, c1 = (-l["weight"] * (l["values"][e] or 0) for e in (prev, cur))
            rounding = l["concept"].startswith("rounding")
            flex = 0.0 if rounding else c0 / revenue[prev] * d_rev
            r0 += -c0 if rounding else 0
            rows.append({"concept": l["concept"], "actual": c1 - c0, "flex": flex, "ratio": c1 - c0 - flex,
                         "absent": [e for e in (prev, cur) if l["values"][e] is None]})
        p_flex = (pretax[prev] - r0) / revenue[prev] * d_rev  # from the figures that foot, as the lines' flex is
        d_p = pretax[cur] - pretax[prev]
        if round(d_rev - sum(r["actual"] for r in rows)) != d_p:
            raise SystemExit(f"{prev}->{cur}: bridge does not reach pre-tax income change {d_p:,}")
        changes.append({"from": prev, "to": cur, "revenue_change": d_rev, "pretax_change": d_p,
                        "pretax_flex": p_flex, "leverage": d_p - p_flex, "lines": rows})
    return changes


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: python history.py TICKER")
    ticker = sys.argv[1].upper()
    ua = user_agent()
    cik, company = cik_for(ticker, ua)
    (RAW / str(cik)).mkdir(parents=True, exist_ok=True)
    latest_f, older_f = ten_ks(cik, ua)
    latest, older = read_filing(cik, latest_f, ua), read_filing(cik, older_f, ua)
    ends, revenue, pretax, oi, lines, disagreements = merge(latest, older)
    if len(ends) != 5:
        raise SystemExit(f"expected five fiscal years, found {ends}")
    out = {
        "ticker": ticker, "company": company, "cik": cik, "unit": "USD",
        "filings": [{k: f[k] for k in ("accession", "report_date", "document_url", "index_url")} | {
            "statement": r["statement"], "years": r["ends"], "stitched_from": r["stitched_from"]}
            for f, r in ((latest_f, latest), (older_f, older))],
        "revenue_label": latest["revenue_label"],
        "period_ends": ends, "revenue": revenue, "pretax_income": pretax, "operating_income": oi,
        "lines": lines, "disagreements": disagreements,
        "footing_gaps": [g for f in (latest, older) for g in f["footing_gaps"] if g["period_end"] in ends],
        "changes": split(ends, revenue, pretax, lines),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{ticker}.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"data/history/{ticker}.json: {company}, {ends[0]} to {ends[-1]}, {len(lines)} lines, "
          f"{len(disagreements)} overlap disagreement(s); every year foots to pre-tax income"
          + ("" if oi is None else " and operating income"))
    for d in disagreements:
        print(f"  {d['item']} {d['period_end']}: latest {d['latest_filing']:,} vs earlier {d['earlier_filing']:,}")


if __name__ == "__main__":
    main()
