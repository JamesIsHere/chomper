"""Who was in the S&P 500 each month, 2016 to 2025, from Wikipedia's own page history.

For each month, the version of "List of S&P 500 companies" that was current on the 1st holds that month's
constituents table. Companies are matched across months by SEC identifier (CIK), so a ticker change (FB to META)
is one company, not an exit and an entry; so is a new CIK that keeps the ticker the next month; a blank CIK is taken from the SEC's ticker file. Fails unless every month lists 495 to 510 rows with a CIK.

    python membership.py    writes data/membership.json and docs/membership.html; no AI call
"""
import json
import re
import time
import urllib.parse
import urllib.request
from html import escape, unescape

from header import CSS, nav
from pull import RAW, ROOT

UA = {"User-Agent": "chomper research jamesphilipmccoy@yahoo.com"}
API = "https://en.wikipedia.org/w/api.php"
TITLE = "List of S&P 500 companies"
MONTHS = [f"{y}-{m:02d}" for y in range(2016, 2026) for m in range(1, 13)]
CACHE = RAW / "sp500" / "revisions"
OUT = ROOT / "data" / "membership.json"
PAGE = ROOT / "docs" / "membership.html"


def revision(month):
    """(revid, timestamp) of the page version current at 00:00 UTC on the 1st of the month."""
    q = urllib.parse.urlencode({"action": "query", "prop": "revisions", "titles": TITLE, "rvlimit": 1,
                                "rvstart": f"{month}-01T00:00:00Z", "rvdir": "older", "rvprop": "ids|timestamp",
                                "format": "json"})
    with urllib.request.urlopen(urllib.request.Request(f"{API}?{q}", headers=UA)) as r:
        (page,) = json.load(r)["query"]["pages"].values()
    rev = page["revisions"][0]
    return rev["revid"], rev["timestamp"]


def fetch(month):
    path = CACHE / f"{month}.html"
    meta = CACHE / f"{month}.json"
    if not path.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        revid, ts = revision(month)
        url = f"https://en.wikipedia.org/w/index.php?oldid={revid}"
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA)) as r:
            path.write_bytes(r.read())
        meta.write_text(json.dumps({"revid": revid, "timestamp": ts}), encoding="utf-8")
        time.sleep(1)
    return path.read_text(encoding="utf-8"), json.loads(meta.read_text(encoding="utf-8"))


def text(cell):
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", "", cell))).strip()


def constituents(html):
    """[{ticker, name, cik, sector}] from the first wikitable: the constituents table."""
    table = re.search(r'<table[^>]*class="[^"]*wikitable[^"]*"[^>]*>(.*?)</table>', html, re.S).group(1)
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", table, re.S)
    head = [text(c).lower() for c in re.findall(r"<th[^>]*>(.*?)</th>", rows[0], re.S)]
    col = lambda *names: next(i for i, h in enumerate(head) if any(n in h for n in names))
    i_t, i_n, i_c, i_s = col("symbol", "ticker"), col("security", "company"), col("cik"), col("sector")
    out = []
    for r in rows[1:]:
        cells = [text(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", r, re.S)]
        if len(cells) < len(head):
            continue
        cik = re.sub(r"\D", "", cells[i_c])
        out.append({"ticker": cells[i_t], "name": cells[i_n], "cik": int(cik) if cik else None,
                    "sector": cells[i_s]})
    return out


def main():
    sec = {r["ticker"]: r["cik_str"] for r in json.loads((RAW / "company_tickers.json").read_text(
        encoding="utf-8")).values()}
    months = {}
    for mo in MONTHS:
        html, meta = fetch(mo)
        rows = constituents(html)
        for r in rows:  # a blank CIK on Wikipedia (SOLS, a new spin-off) is looked up in the SEC's ticker file
            if r["cik"] is None and r["ticker"] in sec:
                r["cik"] = sec[r["ticker"]]
        no_cik = [r["ticker"] for r in rows if r["cik"] is None]
        if not 495 <= len(rows) <= 510 or no_cik:
            raise SystemExit(f"{mo} (revision {meta['revid']}): {len(rows)} rows, no CIK for {no_cik[:10]}")
        months[mo] = {"revision": meta, "rows": rows}
    # One row per company: a CIK, plus any new CIK that takes over the same ticker the very next month (a new
    # holding company or a corrected CIK: Disney, BlackRock), since the company never left the index.
    row_of, prev = {}, {}
    for mo in MONTHS:
        now = {r["cik"]: r["ticker"] for r in months[mo]["rows"]}
        for cik, t in now.items():
            if cik in row_of:
                continue
            gone = [c for c, pt in prev.items() if pt == t and c not in now]
            row_of[cik] = row_of[gone[0]] if gone else cik
        prev = now
    companies = {}  # row -> {ciks, tickers, name, sector, months}
    for mo in MONTHS:
        for r in months[mo]["rows"]:
            c = companies.setdefault(row_of[r["cik"]], {"ciks": [], "tickers": [], "months": []})
            if r["cik"] not in c["ciks"]:
                c["ciks"].append(r["cik"])
            c.update(name=r["name"], sector=r["sector"])  # latest month's name and sector win
            if r["ticker"] not in c["tickers"]:
                c["tickers"].append(r["ticker"])
            if mo not in c["months"]:
                c["months"].append(mo)
    OUT.write_text(json.dumps({"months": {m: v["revision"] | {"count": len(v["rows"])} for m, v in months.items()},
                               "companies": list(companies.values())}, indent=1) + "\n", encoding="utf-8")
    PAGE.write_text(page(companies, months), encoding="utf-8")
    first, last = MONTHS[0], MONTHS[-1]
    start = [c for c in companies.values() if first in c["months"]]
    print(f"data/membership.json, docs/membership.html: {len(companies)} companies over {len(MONTHS)} months; "
          f"{len(start)} at {first}, {sum(last in c['months'] for c in companies.values())} at {last}, "
          f"{sum(last not in c['months'] for c in start)} of {first}'s gone by {last}")


def page(companies, months):
    """One row per company, one column per month; a filled cell is a month in the index."""
    idx = {m: i for i, m in enumerate(MONTHS)}
    rows = sorted(companies.values(), key=lambda c: (idx[c["months"][0]], -idx[c["months"][-1]], c["tickers"][-1]))
    CW, RH, LW, TOP = 5, 1.6, 22, 14
    W, H = LW + CW * len(MONTHS) + 4, round(TOP + RH * len(rows) + 4)
    out = []
    for y in range(2016, 2026):  # year lines and labels
        x = LW + CW * idx[f"{y}-01"]
        out.append(f'<line x1="{x}" x2="{x}" y1="{TOP - 4}" y2="{H}" class="yr"/>'
                   f'<text x="{x + 2}" y="{TOP - 5}" class="yl">{y}</text>')
    for n, c in enumerate(rows):
        y = round(TOP + n * RH, 1)
        tip = (f'{" / ".join(c["tickers"])} {c["name"]} ({c["sector"]}): '
               f'{c["months"][0]} to {c["months"][-1]}, {len(c["months"])} months')
        cells, run = [], None  # draw each unbroken run of months as one bar
        for i, m in enumerate(MONTHS + [None]):
            on = m is not None and m in c["months"]
            if on and run is None:
                run = i
            elif not on and run is not None:
                cells.append(f'<rect x="{LW + CW * run}" y="{y + .2:.1f}" width="{CW * (i - run)}" height="{RH - .4:.1f}"/>')
                run = None
        out.append(f'<g><title>{escape(tip)}</title><text x="{LW - 2}" y="{y + RH - .3:.1f}" class="tk" '
                   f'text-anchor="end">{escape(c["tickers"][-1])}</text>{"".join(cells)}</g>')
    svg = (f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="S&amp;P 500 membership by month, '
           f'2016 to 2025, one row per company">{"".join(out)}</svg>')
    return PAGE_HTML.format(css=CSS, nav=nav(), svg=svg, n=len(rows), table=table(rows))


def month_name(m):
    """'2016-01' -> 'Jan 2016'."""
    y, mo = m.split("-")
    return f'{["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][int(mo) - 1]} {y}'


def table(rows):
    """The chart's rows as text, same order: every ticker the company used, name, sector, first and last month,
    months in the index (fewer than the span when a company left and came back)."""
    out = ['<table class="list"><thead><tr><th>Ticker</th><th>Company</th><th class="sec">Sector</th><th class="d">From</th><th class="d">To</th>'
           '<th class="n">Months</th></tr></thead><tbody>']
    for c in rows:
        out.append(f'<tr><td>{escape(" / ".join(c["tickers"]))}</td><td>{escape(c["name"])}</td>'
                   f'<td class="sec">{escape(c["sector"])}</td><td class="d">{month_name(c["months"][0])}</td>'
                   f'<td class="d">{month_name(c["months"][-1])}</td><td class="n">{len(c["months"])}</td></tr>')
    out.append("</tbody></table>")
    return "".join(out)


PAGE_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Membership - Chomper</title>
<style>
{css}
:root {{ --on: #2f6fd1; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --on: #6ea0f0; }} }}
:root[data-theme="dark"] {{ --on: #6ea0f0; }}
h1 {{ font-size: 1.5rem; line-height: 1.25; margin: 0 0 .5rem; }}
.wrap {{ overflow-x: auto; }}
svg rect {{ fill: var(--on); }}
svg .yr {{ stroke: var(--rule); }}
svg .yl {{ font-size: 6px; fill: var(--ink-2); }}
svg .tk {{ font-size: 1.5px; fill: var(--ink-2); }}
p {{ max-width: 46rem; color: var(--ink-2); }}
h2 {{ font-size: 1.1rem; margin: 2rem 0 .5rem; }}
.list {{ border-collapse: collapse; width: 100%; font-size: .85rem; }}
.list th, .list td {{ text-align: left; vertical-align: top; padding: .25rem .5rem .25rem 0; border-bottom: 1px solid var(--rule); }}
.list th {{ color: var(--ink-2); font-weight: 600; }}
.list .n {{ text-align: right; padding-right: 0; }}
.list .d {{ white-space: nowrap; }}
@media (max-width: 600px) {{ .list {{ font-size: .8rem; }} .list .sec {{ display: none; }} }}
</style>
</head>
<body>
<main>
{nav}
<h1>Who was in the S&amp;P 500</h1>
<p>Every company in the index at any point from January 2016 to December 2025, {n} in all, one row each; a bar
marks the months it was a member. Members at the start come first, longest-staying at the top; companies that
joined later follow in order of joining. Hover a row for its name and dates, or read the same rows in the
table below the chart.</p>
<div class="wrap">{svg}</div>
<h2>The same {n} companies, in the chart's order</h2>
<p>Every ticker the company used in the index, its name and sector in its last month, its first and last month as
a member, and the number of months it was one (fewer than the span when it left and came back). On a narrow
screen the sector column is left out.</p>
{table}
<p>Source: the version of Wikipedia's "List of S&amp;P 500 companies" current on the first of each month; companies
are matched across months by SEC identifier, so a ticker change is one row, as is a new identifier that keeps
the ticker from one month to the next (a new holding company, or a corrected identifier).</p>
</main>
</body>
</html>
"""


if __name__ == "__main__":
    main()
