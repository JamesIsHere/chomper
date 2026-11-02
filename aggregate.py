"""Trial: revenue and pre-tax income summed across the S&P 500 and each GICS sector, ten calendar years.

Values come from the SEC's XBRL frames API (one tag, one calendar year, every filer; the SEC places each fiscal
year in the calendar year it most nearly covers, and keeps the most recently filed value). A company counts only
when it has revenue and pre-tax income in all ten years, so every year sums the same companies; the rest are
listed with the reason. Share classes of one company (GOOGL and GOOG) count once.

    python aggregate.py    writes data/aggregate.json and docs/aggregate.html; no AI call
"""
import json
import urllib.error
from html import escape

import build_history as B
from header import nav
from history import get_json
from pull import ROOT, user_agent

YEARS = list(range(2016, 2026))
# Revenue: every tag that names total revenue; a company's revenue in a year is the largest it reports, since the
# narrower tags (revenue from contracts with customers) are parts of the total where both appear.
REVENUE = ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax",
           "RevenueFromContractWithCustomerIncludingAssessedTax", "RevenuesNetOfInterestExpense",
           "SalesRevenueNet", "SalesRevenueGoodsNet", "SalesRevenueServicesNet"]
# Pre-tax income: the two tags history.py anchors on, in its order; the first one a company reports wins.
PRETAX = ["IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
          "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments"]
# With no total, pre-tax income is domestic plus foreign, the taxonomy's own split of it (ORCL).
PARTS = ["IncomeLossFromContinuingOperationsBeforeIncomeTaxesDomestic",
         "IncomeLossFromContinuingOperationsBeforeIncomeTaxesForeign"]
OUT = ROOT / "data" / "aggregate.json"
PAGE = ROOT / "docs" / "aggregate.html"


def frame(tag, year, ua):
    """{cik: value} for one tag in one calendar year; {} when the SEC has no frame for it (404)."""
    url = f"https://data.sec.gov/api/xbrl/frames/us-gaap/{tag}/USD/CY{year}.json"
    try:
        data = get_json(url, f"frames/{tag}-CY{year}.json", ua)
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise
        return {}
    return {r["cik"]: r["val"] for r in data["data"]}


def collect(universe, ua):
    rev = {t: {y: frame(t, y, ua) for y in YEARS} for t in REVENUE}
    pre = {t: {y: frame(t, y, ua) for y in YEARS} for t in PRETAX + PARTS}
    by_cik, used, excluded = {}, [], []
    for c in universe["companies"]:
        by_cik.setdefault(c["cik"], []).append(c)
    for cik, cs in sorted(by_cik.items(), key=lambda kv: kv[1][0]["ticker"]):
        c = cs[0]
        tickers = sorted(x["ticker"] for x in cs)
        r = {y: max((rev[t][y][cik] for t in REVENUE if cik in rev[t][y]), default=None) for y in YEARS}
        p = {y: next((pre[t][y][cik] for t in PRETAX if cik in pre[t][y]), None) for y in YEARS}
        p = {y: v if v is not None or not all(cik in pre[t][y] for t in PARTS)
             else sum(pre[t][y][cik] for t in PARTS) for y, v in p.items()}
        missing = [y for y in YEARS if r[y] is None or p[y] is None]
        row = {"tickers": tickers, "name": c["name"], "sector": c["sector"], "cik": cik}
        if len(missing) == len(YEARS) and all(r[y] is None for y in YEARS):
            excluded.append(row | {"reason": f"no revenue or pre-tax income in any year under the tags read, for its SEC identifier (CIK {cik})"})
            continue
        if missing:
            what = [k for k, s in (("revenue", r), ("pre-tax income", p)) if any(s[y] is None for y in YEARS)]
            excluded.append(row | {"reason": f"no {' or '.join(what)} for {', '.join(map(str, missing))}"})
            continue
        if any(r[y] <= 0 for y in YEARS):
            excluded.append(row | {"reason": "revenue zero or negative in a year"})
            continue
        used.append(row | {"revenue": r, "pretax_income": p})
    return used, excluded


def total(rows, name):
    return {"name": name, "companies": len(rows),
            "revenue": {y: sum(r["revenue"][y] for r in rows) for y in YEARS},
            "pretax_income": {y: sum(r["pretax_income"][y] for r in rows) for y in YEARS}}


def chart(g):
    """The company pages' log chart, fed the group's sums. Each year's pair is the same companies' sums, so the
    one-basis rule the chart checks holds by construction."""
    ends = [str(y) for y in YEARS]
    rev = {str(y): g["revenue"][y] for y in YEARS}
    pre = {str(y): g["pretax_income"][y] for y in YEARS}
    changes = {k: {e: {"filed": "sum", "prior_end": p, "value": s[e], "prior": s[p]}
                   for p, e in zip(ends, ends[1:])} for k, s in (("revenue", rev), ("pretax_income", pre))}
    h = {"ticker": g["name"], "period_ends": [f"{e}-12-31" for e in ends], "deals": [], "standards": []}
    h["revenue"] = {f"{e}-12-31": v for e, v in rev.items()}
    h["pretax_income"] = {f"{e}-12-31": v for e, v in pre.items()}
    h["changes"] = {k: {f"{e}-12-31": v | {"prior_end": f"{v['prior_end']}-12-31"} for e, v in d.items()}
                    for k, d in changes.items()}
    return B.trend_chart(h)


def growth(g):
    """Annualized growth of revenue and of costs (revenue less pre-tax income), first year to last."""
    n = len(YEARS) - 1
    a, b = YEARS[0], YEARS[-1]
    cost = {y: g["revenue"][y] - g["pretax_income"][y] for y in (a, b)}
    rg = (g["revenue"][b] / g["revenue"][a]) ** (1 / n) - 1
    cg = (cost[b] / cost[a]) ** (1 / n) - 1
    return rg * 100, cg * 100


def section(g, note=""):
    rg, cg = growth(g)
    gap = cg - rg
    verdict = "costs grew slower than revenue" if gap < 0 else "costs grew faster than revenue"
    return (f'<section class="agg"><h2>{escape(g["name"])} <span class="dim">{g["companies"]} companies</span></h2>'
            f'<p class="lead-num">{YEARS[0]} to {YEARS[-1]}: revenue {rg:+.1f}% a year, costs {cg:+.1f}% a year; '
            f'{verdict} by {abs(gap):.1f} points a year.</p>{note}{chart(g)}</section>')


def main():
    ua = user_agent()
    universe = json.loads((ROOT / "data" / "sp500.json").read_text(encoding="utf-8"))
    used, excluded = collect(universe, ua)
    groups = [total(used, "S&P 500")]
    for s in sorted({r["sector"] for r in used}):
        groups.append(total([r for r in used if r["sector"] == s], s))
    for y in YEARS:  # the sectors add up to the total, every year
        for k in ("revenue", "pretax_income"):
            if sum(g[k][y] for g in groups[1:]) != groups[0][k][y]:
                raise SystemExit(f"{y} {k}: sectors do not add up to the total")
    OUT.write_text(json.dumps({"years": YEARS, "groups": groups, "companies": used, "excluded": excluded},
                              indent=1) + "\n", encoding="utf-8")
    fin = ('<p class="note">Banks and insurers report revenue differently (interest income, premiums), so this '
           "sector's revenue and costs are not comparable with the others.</p>")
    body = "\n".join(section(g, fin if g["name"] == "Financials" else "") for g in groups)
    gone = "".join(f'<li>{escape(", ".join(r["tickers"]))} ({escape(r["name"])}): {escape(r["reason"])}</li>'
                   for r in excluded)
    PAGE.write_text(PAGE_HTML.format(
        css=B.CSS, nav=nav("aggregate.html"), body=body, used=len(used), first=YEARS[0], last=YEARS[-1],
        excluded=len(excluded), gone=gone), encoding="utf-8")
    print(f"data/aggregate.json, docs/aggregate.html: {len(used)} companies summed, {len(excluded)} left out")


PAGE_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>S&amp;P 500 - Chomper</title>
<style>{css}
section.agg {{ margin: 0 0 2.5rem; }}
.lead-num {{ margin: .25rem 0 .5rem; }}
</style>
</head>
<body>
<main>
{nav}
<h1>Costs and revenue across the S&amp;P 500</h1>
<p class="lede">Revenue and pre-tax income summed across {used} of today's S&amp;P 500 companies, {first} to {last},
first for the whole index and then for each sector. Costs are revenue less pre-tax income. Sums are dominated by
the largest companies. Each company's fiscal year is placed in the calendar year it most nearly covers.</p>
{body}
<footer>
<p>Source: the SEC's XBRL frames data, the most recently filed value for each company and year. A company counts
only when it reports revenue and pre-tax income in all ten years, so every year sums the same companies; today's
members are traced back, so companies that left the index are not included. {excluded} companies are left out:</p>
<ul class="gone">{gone}</ul>
</footer>
</main>
</body>
</html>
"""

if __name__ == "__main__":
    main()
