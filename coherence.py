"""Cross-page check: every figure or fact that appears on more than one built page, or in the README, is read
from each place and compared. Prints one line per check and exits 1 on any disagreement. No network, no AI.

    python coherence.py

Pages are read from docs/ as built; the data behind them from data/. A check that cannot find what it looks for
fails loud (it is not skipped), so a template change that moves a sentence shows up here.
"""
import json
import re
import sys
from html import unescape
from pathlib import Path

import build_history as B
from pull import ROOT

DOCS = ROOT / "docs"
SITE_PAGES = {"index.html", "aggregate.html", "decisions.html", "considerations.html", "membership.html", "readme.html"}
WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine",
         10: "ten", 11: "eleven", 12: "twelve", 13: "thirteen", 14: "fourteen", 15: "fifteen", 16: "sixteen",
         17: "seventeen", 18: "eighteen", 19: "nineteen", 20: "twenty"}
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]
results = []


def page(name):
    return (DOCS / name).read_text(encoding="utf-8")


def text(html):
    return unescape(re.sub(r"<[^>]+>", "", html))


def one(pattern, s, where, flags=0):
    """The single match of a pattern, or a failed check naming where it was expected."""
    found = re.findall(pattern, s, flags)
    if len(found) != 1:
        raise LookupError(f"{where}: expected one match of {pattern!r}, found {len(found)}")
    return found[0]


def check(name, *values):
    """All values equal -> pass; each value is (source, value)."""
    vals = [v for _, v in values]
    ok = all(v == vals[0] for v in vals)
    results.append((ok, name, values))


def main():
    idx = page("index.html")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    universe = json.loads((ROOT / "data" / "sp500.json").read_text(encoding="utf-8"))["companies"]
    history = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted((ROOT / "data" / "history").glob("*.json"))}
    headline = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted((ROOT / "data" / "headline").glob("*.json"))}
    company_pages = sorted(p.stem for p in DOCS.glob("*.html") if p.name not in SITE_PAGES)
    bridges = sorted(p.stem for p in (DOCS / "bridge").glob("*.html"))

    # 1. The All page's opening counts against the universe, the pages on disk, the sector summaries, the rows
    lede = text(one(r'<p class="lede">(The S&amp;P 500 by sector.*?)</p>', idx, "All page lede", re.S))
    total, analyzed = map(int, one(r"(\d+) companies, (\d+) analyzed so far", lede, "All page lede"))
    readable, unreadable = map(int, one(r"Of the rest, (\d+) have[\s\S]*?and (\d+) cannot be read yet", lede, "All page lede"))
    sectors = re.findall(r'<details class="sector"><summary>[^<]*<span class="dim">(\d+) compan(?:y|ies)(?:, (\d+) analyzed)?',
                         idx)
    check("All page: companies in the S&P 500 list", ("lede", total), ("data/sp500.json", len(universe)),
          ("sector summaries", sum(int(n) for n, _ in sectors)))
    check("All page: companies analyzed", ("lede", analyzed), ("company pages in docs/", len(company_pages)),
          ("data/history/", len(history)), ("data/headline/", len(headline)),
          ("sector summaries", sum(int(a or 0) for _, a in sectors)),
          ("linked tickers in the table", len(re.findall(r'<th scope="row"><a href="[A-Z.]+\.html">', idx))),
          ("'Built so far' links", len(re.findall(r'company pages for (.*?)\.</p>', idx, re.S) and
                                       re.findall(r'<a href="[A-Z.]+\.html">', re.search(r'company pages for (.*?)\.</p>', idx, re.S).group(1)))),
          ("README", readme.count(f"({WORDS[analyzed]} so far)") and analyzed),
          ("README status", readme.count(f"{WORDS[analyzed]} company pages") and analyzed))
    check("All page: readable + unreadable + analyzed = total", ("lede", total), ("sum", readable + unreadable + analyzed))
    check("All page: readable rows", ("lede", readable), ("rows saying Readable", idx.count('class="why">Readable:')))
    check("All page: not-readable rows", ("lede", unreadable), ("rows saying Not readable", idx.count('class="why">Not readable:')))

    # 2. Each company page against its row on the All page and against the data
    short = []
    for t in company_pages:
        p, h = page(f"{t}.html"), history[t]
        ends = sorted(h["period_ends"])
        row = one(rf'<th scope="row"><a href="{t}\.html">{t}</a></th><td class="name">[^<]*</td>'
                  r'<td>([^<]*)</td><td>([^<]*)</td><td>([^<]*)</td><td>([^<]*)</td><td>([^<]*)</td>', idx, f"All page row {t}")
        five = one(r"<h2>Five years: which costs moved with revenue, ([^<]*)</h2>", p, f"{t} five-year heading")
        check(f"{t}: five-year window", ("All page row", row[0]), ("company page heading", five))
        rev, pre = h["revenue"], h["pretax_income"]
        check(f"{t}: latest revenue", ("All page row", row[1]), ("data/history", B.m(rev[ends[-1]], sign=False)))
        check(f"{t}: revenue change", ("All page row", row[2]), ("data/history", f"{100 * (rev[ends[-1]] / rev[ends[0]] - 1):+.1f}%"))
        check(f"{t}: first and last margin", ("All page row", (row[3], row[4])),
              ("data/history", (f"{100 * pre[ends[0]] / rev[ends[0]]:.1f}%", f"{100 * pre[ends[-1]] / rev[ends[-1]]:.1f}%")))
        long_h2 = one(r"<h2>((?:[A-Z][a-z]{2} )?\d{4} to (?:[A-Z][a-z]{2} )?\d{4})</h2>", p, f"{t} long-view heading")
        hl_ends = sorted(headline[t]["period_ends"])
        tip = one(rf"<title>{re.escape(B.year(ends[-1]))}: revenue (\$[\d.,]+[MBT]), pre-tax income", p, f"{t} latest-year chart tooltip")
        check(f"{t}: latest revenue on its own page", ("All page row", row[1]), ("company page chart", tip))
        check(f"{t}: long view years", ("company page heading", long_h2),
              ("data/headline", f"{B.year(hl_ends[0])} to {B.year(hl_ends[-1])}"))
        if B.year(hl_ends[0]).endswith("2016"):
            short.append(t)
        has_cross = 'class="crossref"><a href="bridge/' in p
        check(f"{t}: bridge link only where a bridge exists", ("company page", has_cross), ("docs/bridge/", t in bridges))
    check("README: pages that stop at fiscal 2016", ("README", bool(re.search(rf"{WORDS[len(short)].capitalize()} company pages stop at fiscal 2016", readme)) and len(short)),
          ("company pages whose long view starts 2016", len(short)))

    # 3. The bridge against the All page sentence, the ODFL page, the README
    bridge = json.loads((ROOT / "data" / "bridge.json").read_text(encoding="utf-8"))
    bp = page("bridge/ODFL.html")
    fy0, fy1 = (one(r"FY(\d{4}) operating income", bridge[k]["label"], f"bridge.json {k}") for k in ("start", "end"))
    change = bridge["end"]["amount"] - bridge["start"]["amount"]
    import build as A
    h1 = text(one(r"<h1>(.*?)</h1>", bp, "bridge h1"))
    check("Bridge: the change in the heading", ("bridge page h1", one(r"(\$[\d.,]+M)", h1, "bridge h1 amount")),
          ("bridge.json", A.m(abs(change), sign=False)), ("README screenshot caption", one(r"fell (\$[\d.,]+M) in", readme, "README alt")))
    check("Bridge: fell or rose", ("bridge page h1", "fell" in h1), ("bridge.json", change < 0))
    check("Bridge: years", ("All page sentence", one(r"operating income from fiscal (\d{4} to \d{4})", idx, "All page built line")),
          ("bridge.json", f"{fy0} to {fy1}"), ("README", one(r"walks operating income from\s+fiscal (\d{4} to \d{4})", readme, "README bridge")),
          ("bridge page h1 year", f"{int(one(r'in (\d{4})$', h1, 'bridge h1 year')) - 1} to {one(r'in (\d{4})$', h1, 'bridge h1 year')}"))
    check("Bridge: company page link back", ("bridge page", 'href="../ODFL.html"' in bp), ("expected", True))

    # 4. The two ledgers against their source files
    dec = page("decisions.html")
    active, count = map(int, one(r"(\d+) active of (\d+)\.", text(dec), "decisions lede"))
    md = (ROOT / "decisions.md").read_text(encoding="utf-8")
    check("Decisioning: entries", ("page", count), ("decisions.md", len(re.findall(r"^## \d{4}-\d{2}-\d{2} \| ", md, re.M))))
    check("Decisioning: active", ("page", active), ("decisions.md", len(re.findall(r"^Status: active\s*$", md, re.M))))
    con = page("considerations.html")
    open_, ccount = map(int, one(r"(\d+) open of (\d+)\.", text(con), "considerations lede"))
    cmd = (ROOT / "considerations.md").read_text(encoding="utf-8")
    check("Considerations: entries", ("page", ccount), ("considerations.md", len(re.findall(r"^## \d{4}-\d{2}-\d{2} \| ", cmd, re.M))))
    check("Considerations: open", ("page", open_), ("considerations.md", len(re.findall(r"^Status: open\s*$", cmd, re.M))))

    # 5. The S&P 500 page against the membership data and page
    agg, mem_page = page("aggregate.html"), page("membership.html")
    mem = json.loads((ROOT / "data" / "membership.json").read_text(encoding="utf-8"))
    cov = dict(re.findall(r"(\d{4}) \d+ of (\d+)", one(r"Companies counted in each year&rsquo;s change, out of that year&rsquo;s members: ([^.]*)\.", agg, "aggregate coverage")))
    jan = {y: sum(f"{y}-01" in c["months"] for c in mem["companies"]) for y in cov}
    check("S&P 500 page: members each 1 January", ("aggregate coverage denominators", {y: int(n) for y, n in cov.items()}),
          ("data/membership.json, companies in that January", jan))
    months = sorted(mem["months"])
    check("S&P 500 page: years", ("aggregate", one(r"members as they were, (\d{4} to \d{4})", text(agg), "aggregate years") if re.search(r"members as they were, \d{4} to \d{4}", text(agg)) else one(r"(\d{4} to \d{4})", one(r'<a href="membership.html">([^<]*)</a>', agg, "aggregate membership link"), "aggregate link years")),
          ("membership.json", f"{months[0][:4]} to {months[-1][:4]}"))
    n_mem = int(one(r"(\d+) in all", text(mem_page), "membership lede"))
    check("Membership page: companies", ("lede", n_mem), ("table rows", mem_page.count('<tr><td>')),
          ("chart rows", mem_page.count("<g><title>")), ("membership.json", len(mem["companies"])),
          ("heading of the table", int(one(r"The same (\d+) companies", mem_page, "membership table heading"))))
    check("Membership page: span", ("lede", one(r"from ([A-Z][a-z]+ \d{4} to [A-Z][a-z]+ \d{4})", text(mem_page), "membership span")),
          ("membership.json", f"{MONTHS[int(months[0][5:]) - 1]} {months[0][:4]} to {MONTHS[int(months[-1][5:]) - 1]} {months[-1][:4]}"))

    # 6. The Readme page carries every paragraph of README.md
    rp = text(page("readme.html"))
    paras = [re.sub(r"\s+", " ", b).strip() for b in re.split(r"\n\s*\n", readme.strip())
             if not b.startswith(("#", "![", "    ", "- "))]
    plain = re.sub(r"\s+", " ", rp)
    check("Readme page: every README paragraph present", ("README.md paragraphs", len(paras)),
          ("found on the page", sum(re.sub(r"`", "", p_) in plain for p_ in paras)))

    # 7. The same menu on every page
    navs = {}
    for f in sorted(DOCS.glob("*.html")) + sorted((DOCS / "bridge").glob("*.html")):
        nav = one(r'(<nav class="menu">.*?</nav>)', f.read_text(encoding="utf-8"), f"{f.name} menu")
        navs[f.name] = re.sub(r' aria-current="page"', "", nav.replace('href="../', 'href="'))
    check("Menu identical on every page", *((n, v) for n, v in navs.items()))

    width = max(len(n) for _, n, _ in results)
    bad = 0
    for ok, name, values in results:
        shown = "; ".join(f"{src} = {val}" for src, val in values) if not ok else f"{values[0][1]}"
        print(f"{'ok  ' if ok else 'FAIL'} {name:<{width}}  {shown}")
        bad += not ok
    print(f"\n{len(results) - bad} agree, {bad} disagree")
    return 1 if bad else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except LookupError as e:
        raise SystemExit(f"FAIL {e}")
