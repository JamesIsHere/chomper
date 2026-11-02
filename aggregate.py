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


def figures(ua):
    """{cik: ({year: revenue}, {year: pre-tax income})} for every filer in the frames, read as collect() reads them."""
    rev = {t: {y: frame(t, y, ua) for y in YEARS} for t in REVENUE}
    pre = {t: {y: frame(t, y, ua) for y in YEARS} for t in PRETAX + PARTS}
    ciks = {c for d in list(rev.values()) + list(pre.values()) for f in d.values() for c in f}
    out = {}
    for cik in ciks:
        r = {y: max((rev[t][y][cik] for t in REVENUE if cik in rev[t][y]), default=None) for y in YEARS}
        p = {y: next((pre[t][y][cik] for t in PRETAX if cik in pre[t][y]), None) for y in YEARS}
        p = {y: v if v is not None or not all(cik in pre[t][y] for t in PARTS)
             else sum(pre[t][y][cik] for t in PARTS) for y, v in p.items()}
        out[cik] = (r, p)
    return out


def chained(name, members, figs):
    """Revenue and pre-tax income for a membership that may change every year, chain-linked: each year's change
    is measured only on companies that were members on 1 January of that year and report both years, each company
    against itself, so joiners and leavers never show as jumps. members: {year: [[cik, ...] per company]}.
    The first year's level is the sum over its members. Costs are revenue less pre-tax income."""
    def pick(ciks, y):
        for c in ciks:
            r, p = figs.get(c, ({}, {}))
            if r.get(y) is not None and p.get(y) is not None and r[y] > 0:
                return r[y], p[y]
        return None
    y0 = YEARS[0]
    base = [v for v in (pick(m, y0) for m in members[y0]) if v]
    R, C = {y0: sum(r for r, _ in base)}, {y0: sum(r - p for r, p in base)}
    cover = {y0: (len(base), len(members[y0]))}
    for a, b in zip(YEARS, YEARS[1:]):
        both = [(pa, pb) for pa, pb in ((pick(m, a), pick(m, b)) for m in members[b]) if pa and pb]
        ra, rb = sum(x[0] for x, _ in both), sum(y[0] for _, y in both)
        ca, cb = sum(x[0] - x[1] for x, _ in both), sum(y[0] - y[1] for _, y in both)
        R[b], C[b] = R[a] * rb / ra, C[a] * cb / ca
        cover[b] = (len(both), len(members[b]))
    return {"name": name, "companies": max(n for n, _ in cover.values()),
            "revenue": R, "pretax_income": {y: R[y] - C[y] for y in YEARS}, "coverage": cover}


def margin_chart(lines):
    """Pre-tax margin by year, one line per population: the gap between them is the survivorship bias."""
    W, L, R, T, H = 800, 60, 170, 14, 180
    ms = {n: {y: g["pretax_income"][y] / g["revenue"][y] * 100 for y in YEARS} for n, g in lines}
    lo = min(min(v.values()) for v in ms.values()) // 2 * 2
    hi = -(-max(max(v.values()) for v in ms.values()) // 2) * 2
    px = lambda i: L + (i + 0.5) * (W - L - R) / len(YEARS)
    py = lambda v: T + (hi - v) / (hi - lo) * H
    out = [f'<line x1="{L}" x2="{W - R}" y1="{py(v):.1f}" y2="{py(v):.1f}" class="g"/>'
           f'<text x="{L - 6}" y="{py(v) + 4:.1f}" class="ax" text-anchor="end">{v:.0f}%</text>'
           for v in range(int(lo), int(hi) + 1, 2)]
    out += [f'<text x="{px(i):.1f}" y="{T + H + 18}" class="ax" text-anchor="middle">{y}</text>'
            for i, y in enumerate(YEARS)]
    for (n, _), var in zip(lines, ("--s1", "--s2")):
        pts = " ".join(f"{px(i):.1f},{py(ms[n][y]):.1f}" for i, y in enumerate(YEARS))
        out.append(f'<polyline points="{pts}" fill="none" style="stroke:var({var})" stroke-width="2"/>')
        out += [f'<circle cx="{px(i):.1f}" cy="{py(ms[n][y]):.1f}" r="3.5" style="fill:var({var})" class="dot">'
                f'<title>{y}: {escape(n)}, pre-tax margin {ms[n][y]:.1f}%</title></circle>'
                for i, y in enumerate(YEARS)]
        out.append(f'<text x="{W - R + 10}" y="{py(ms[n][YEARS[-1]]) + 4:.1f}" class="lab">{escape(n)} '
                   f'{ms[n][YEARS[-1]]:.1f}%</text>')
    legend = "".join(f'<span><i style="background:var({v})"></i>{escape(n)}</span>'
                     for (n, _), v in zip(lines, ("--s1", "--s2")))
    return (f'<p class="legend">{legend}</p><svg class="trend wide" viewBox="0 0 {W} {T + H + 26}" role="img" '
            f'aria-label="Pre-tax margin by year for the two populations">{"".join(out)}</svg>')


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
    mem = json.loads((ROOT / "data" / "membership.json").read_text(encoding="utf-8"))
    figs = figures(ua)
    at = {y: [c["ciks"] for c in mem["companies"] if f"{y}-01" in c["months"]] for y in YEARS}
    today = [c["ciks"] for c in mem["companies"] if f"{YEARS[-1]}-12" in c["months"]]
    was = chained("As it was", at, figs)
    now = chained("Today's members", {y: today for y in YEARS}, figs)
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
    rg_w, cg_w = growth(was)
    rg_n, cg_n = growth(now)
    cov = "; ".join(f"{y} {n} of {t}" for y, (n, t) in was["coverage"].items())
    bias = (f'<section class="agg"><h2>The S&amp;P 500 as it was, against today&rsquo;s members</h2>'
            f'<p class="lead-num">As it was (the members on 1 January of each year): revenue {rg_w:+.1f}% a year, '
            f'costs {cg_w:+.1f}% a year. Today&rsquo;s members traced back: revenue {rg_n:+.1f}% a year, costs '
            f'{cg_n:+.1f}% a year. The chart shows each one&rsquo;s pre-tax margin (pre-tax income as a share of '
            f'revenue).</p>{margin_chart([(was["name"], was), (now["name"], now)])}'
            f'<p class="note">Both lines link each year to the next using only companies that report both years, '
            f'each against itself, so a company joining or leaving never shows as a jump; they differ only in who '
            f'counts. Companies counted in each year&rsquo;s change, out of that year&rsquo;s members: {cov}. '
            f'Who was a member each month: <a href="membership.html">membership, 2016 to 2025</a>.</p>'
            f'</section>')
    sector = lambda c: "Communication Services" if c["sector"].startswith("Telecommunication") else c["sector"]
    parts = ['<h2 class="part">By sector: as it was, against today&rsquo;s members</h2>'
             '<p class="note">Each company sits in its last sector while a member (the old Telecommunication Services '
             'is Communication Services). Where few members are counted, the line is less sure.</p>']
    for sname in sorted({sector(c) for c in mem["companies"]}):
        at_s = {y: [c["ciks"] for c in mem["companies"] if sector(c) == sname and f"{y}-01" in c["months"]]
                for y in YEARS}
        now_s = [c["ciks"] for c in mem["companies"] if sector(c) == sname and f"{YEARS[-1]}-12" in c["months"]]
        w = chained("As it was", at_s, figs)
        n = chained("Today's members", {y: now_s for y in YEARS}, figs)
        mg = lambda g, y: g["pretax_income"][y] / g["revenue"][y] * 100
        dw, dn = mg(w, YEARS[-1]) - mg(w, YEARS[0]), mg(n, YEARS[-1]) - mg(n, YEARS[0])
        (c0, t0), (c1, t1) = w["coverage"][YEARS[0]], w["coverage"][YEARS[-1]]
        parts.append(f'<section class="agg"><h3>{escape(sname)}</h3><p class="lead-num">Pre-tax margin, {YEARS[0]} '
                     f'to {YEARS[-1]}: as it was {dw:+.1f} points, today&rsquo;s members {dn:+.1f} points. Counted: '
                     f'{c0} of {t0} members in {YEARS[0]}, {c1} of {t1} in {YEARS[-1]}.</p>'
                     f'{margin_chart([(w["name"], w), (n["name"], n)])}</section>')
    parts.append('<h2 class="part">Today&rsquo;s members with ten years of filings, in dollars</h2>')
    body = bias + "\n" + "\n".join(parts) + "\n" + "\n".join(section(g, fin if g["name"] == "Financials" else "") for g in groups)
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
