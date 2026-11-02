"""Build one five-year page per company from data/history/<TICKER>.json. Never calls the AI.

Writes docs/history/<TICKER>.html and docs/history/index.html, linked by a menu. Each cell is a
line's effect on pre-tax income beyond moving in step with revenue (the
ratio effect, sign flipped so a cost that outran revenue shows as a loss).

Usage: python build_history.py
"""
import json
import math
import re
from datetime import date, timedelta
from html import escape

import header
from header import nav
from pull import ROOT

DATA = ROOT / "data" / "history"
HEADLINE = ROOT / "data" / "headline"
OUT = ROOT / "docs"


def m(dollars, sign=True):
    v = dollars / 1e6
    if abs(v) >= 1000:
        s = f"${abs(v) / 1000:,.2f}B"
    else:
        s = f"${abs(v):,.1f}M"
    if s in ("$0.0M", "$0.00B"):
        return "$0.0M"
    return ("+" if v > 0 else "-") + s if sign else ("-" + s if v < 0 else s)


def rounding_only(a, b):
    """True when two filings' figures differ only because one rounds coarser: the coarser figure (the one with more
    trailing zeros, at most $1M) equals the finer one rounded half up to its unit. PGR's 2025 10-K reports
    $62,109M where its 2023 10-K reported $62,108.5M."""
    unit = lambda v: next((u for u in (10 ** 6, 10 ** 5, 10 ** 4, 10 ** 3) if v % u == 0), 1)
    coarse, fine = (a, b) if unit(a) > unit(b) else (b, a)
    u = unit(coarse)
    return u > unit(fine) and math.floor(fine / u + 0.5) * u == coarse


def year(end):
    """A fiscal year's label from its end date, read a week early: a 52/53-week year ends up to a week past its
    nominal month (JNJ's 2020 ended 2021-01-03, HD's years end late January or early February), and the week
    keeps each company's labels on one month: 2020, not Jan 2021."""
    d = date.fromisoformat(end) - timedelta(days=7)
    return str(d.year) if d.month == 12 else d.strftime("%b %Y")


def cell(value, scale, title):
    """Tinted cell: green helped operating income, red hurt it; tint by size against the page's largest."""
    share = min(abs(value) / scale, 1) if scale else 0
    var = "--up" if value > 0 else "--down"
    tint = f"color-mix(in srgb, var({var}) {share * 70:.0f}%, transparent)"
    return f'<td style="background:{tint}" title="{escape(title)}">{m(value)}</td>'


def sections(h):
    """[(heading or None, lines)]: lines above operating income, then those below it, when the company
    reports operating income; otherwise one section."""
    if h["operating_income"] is None:
        return [(None, h["lines"])]
    return [(None, [l for l in h["lines"] if l["operating"]]),
            ("Below operating income", [l for l in h["lines"] if not l["operating"]])]


def label_html(l):
    # No income/expense tag: the filer's label says what the line is, and a negative share means it added income.
    return f'<th scope="row">{escape(l["label"])}</th>'


def ratios(h):
    """Each line as a share of revenue per year, tinted by its change from the year before."""
    ends, rev = h["period_ends"], h["revenue"]
    share = {l["concept"]: {e: -l["weight"] * (l["values"][e] or 0) / rev[e] * 100 for e in ends}
             for l in h["lines"]}
    margin = {e: h["pretax_income"][e] / rev[e] * 100 for e in ends}
    for e in ends:  # pre-tax margin = 100% minus the cost shares, exactly
        if abs(100 - sum(s[e] for s in share.values()) - margin[e]) > 1e-6:
            raise SystemExit(f"{h['ticker']} {e}: shares do not reach pre-tax margin")
    op_margin = None
    if h["operating_income"] is not None:
        op_margin = {e: h["operating_income"][e] / rev[e] * 100 for e in ends}
        for e in ends:  # operating margin = 100% minus the operating cost shares, exactly
            if abs(100 - sum(share[l["concept"]][e] for l in h["lines"] if l["operating"]) - op_margin[e]) > 1e-6:
                raise SystemExit(f"{h['ticker']} {e}: operating shares do not reach operating margin")
    scale = max(abs(s[b] - s[a]) for s in share.values() for a, b in zip(ends, ends[1:]))

    def pct(v):
        return f"{v + 0.0:.1f}%" if round(v, 1) else "0.0%"  # no "-0.0%"

    def tds(values, good_when_up):
        out = [f"<td>{pct(values[ends[0]])}</td>"]
        for a, b in zip(ends, ends[1:]):
            d = values[b] - values[a]
            effect = d if good_when_up else -d
            share_of = min(abs(d) / scale, 1) if scale else 0
            tint = f"color-mix(in srgb, var({'--up' if effect > 0 else '--down'}) {share_of * 70:.0f}%, transparent)"
            out.append(f'<td style="background:{tint}" title="{d:+.2f} points from {year(a)}">{pct(values[b])}</td>')
        return "".join(out)
    rows = [f'<tr class="strong"><th scope="row">Pre-tax margin</th>{tds(margin, True)}</tr>']
    if op_margin:
        rows.append(f'<tr><th scope="row">&nbsp;&nbsp;operating margin</th>{tds(op_margin, True)}</tr>')
    for heading, ls in sections(h):
        rows.append(f'<tr class="sep"><td colspan="99"></td></tr>' if heading is None else
                    f'<tr class="sub"><th colspan="99">{heading}</th></tr>')
        rows += [f'<tr>{label_html(l)}{tds(share[l["concept"]], False)}</tr>' for l in ls]
    return "\n".join(rows)


def chart_breaks(h):
    """{end: [text]} for each year with a significant acquisition or a newly required accounting standard: the
    years numbered on the chart and listed in its key. Restatements are not marked: the chart chains same-basis
    growth, so a recast makes no spike in its lines (the table's asterisks carry them)."""
    out = {}
    for d in h["deals"]:
        if d["significant"]:
            out.setdefault(d["fiscal_year_end"], []).append(
                f"Acquired {d['name']}, {m(d['size'], False)}, {d['share_of_assets']:.0%} of total assets at the "
                f"prior year end")
    for s in h["standards"]:
        out.setdefault(s["fiscal_year_end"], []).append(
            f"{s['standard']} required this year (the company may have adopted earlier)")
    return out


def money_tick(v):
    """An axis label: $0, $500M, $2B, -$1B."""
    if v == 0:
        return "$0"
    s = f"${abs(v) / 1e9:g}B" if abs(v) >= 1e9 else f"${abs(v) / 1e6:g}M"
    return ("-" if v < 0 else "") + s


def log_ticks(lo, hi):
    """1-2-5 dollar ticks covering lo..hi, widened to the tick just below and just above."""
    all_ticks = [k * 10 ** p for p in range(5, 15) for k in (1, 2, 5)]
    below = max(v for v in all_ticks if v <= lo)
    above = min(v for v in all_ticks if v >= hi)
    return [v for v in all_ticks if below <= v <= above]


def bar_ticks(values):
    """Round dollar ticks through zero covering every bar, at most five intervals."""
    lo, hi = min(min(values), 0), max(max(values), 0)
    step = next(k * 10 ** p for p in range(5, 15) for k in (1, 2, 5) if (hi - lo) / (k * 10 ** p) <= 5)
    return [k * step for k in range(math.floor(lo / step), math.ceil(hi / step) + 1)]


def cost_gaps(h):
    """{end: dollars} for each year after the first: the pre-tax income the company would have earned at the prior
    year's pre-tax margin, minus what it earned. Both years come from the one 10-K that shows them together
    (headline.py's same-basis changes), so a recast never mixes two bases in one bar. Above zero, costs grew
    faster than revenue that year. Fails if revenue and pre-tax income took that pair from different filings."""
    rev, pre = h["changes"]["revenue"], h["changes"]["pretax_income"]
    out = {}
    for e in h["period_ends"][1:]:
        r, p = rev[e], pre[e]
        if (r["filed"], r["prior_end"]) != (p["filed"], p["prior_end"]):
            raise SystemExit(f"{h['ticker']} {e}: revenue and pre-tax income changes come from different filings")
        out[e] = r["value"] * p["prior"] / r["prior"] - p["value"]
    return out


def trend_chart(h):
    """Revenue and pre-tax income in dollars on a log scale (the table's figures), each year with a break numbered
    at the top and explained in a key; under it, a band of bars for each year's cost gap (cost_gaps)."""
    ends = h["period_ends"]
    series = [("Revenue", "--s1", h["revenue"]), ("Pre-tax income", "--s2", h["pretax_income"])]
    vals = [s[e] for _, _, s in series for e in ends]
    if min(vals) <= 0:
        return ('<p class="note">Chart omitted: a year\'s pre-tax income is zero or negative, so it cannot go on a '
                'log scale.</p>')
    W, L, R, T, PLOT_H, X_H, GAP, BAND_H = 800, 60, 170, 26, 280, 26, 18, 110
    ticks = log_ticks(min(vals), max(vals))
    lo, hi = math.log10(ticks[0]), math.log10(ticks[-1])
    step_x = (W - L - R) / len(ends)  # one slot per year, so every bar sits inside the plot
    px = lambda i: L + (i + 0.5) * step_x
    py = lambda v: T + (hi - math.log10(v)) / (hi - lo) * PLOT_H
    g = cost_gaps(h)
    bt = bar_ticks(list(g.values()))
    b0 = T + PLOT_H + X_H + GAP
    by = lambda v: b0 + (bt[-1] - v) / (bt[-1] - bt[0]) * BAND_H
    H = b0 + BAND_H + 8

    out = [f'<line x1="{L}" x2="{W - R}" y1="{py(v):.1f}" y2="{py(v):.1f}" class="g"/>'
           f'<text x="{L - 6}" y="{py(v) + 4:.1f}" class="ax" text-anchor="end">{money_tick(v)}</text>'
           for v in ticks]
    out += [f'<text x="{px(i):.1f}" y="{T + PLOT_H + 18}" class="ax" text-anchor="middle">{year(e)}</text>'
            for i, e in enumerate(ends)]
    b = chart_breaks(h)
    years = [e for e in ends if e in b]
    out += [f'<line x1="{px(ends.index(e)):.1f}" x2="{px(ends.index(e)):.1f}" y1="{T - 2}" y2="{T + PLOT_H}" '
            f'class="guide"/><circle cx="{px(ends.index(e)):.1f}" cy="{T - 10}" r="9" class="mark"/>'
            f'<text x="{px(ends.index(e)):.1f}" y="{T - 6}" class="marknum" text-anchor="middle">{n}</text>'
            for n, e in enumerate(years, 1)]
    label_y = []
    for name, var, s in series:
        pts = " ".join(f"{px(i):.1f},{py(s[e]):.1f}" for i, e in enumerate(ends))
        out.append(f'<polyline points="{pts}" fill="none" style="stroke:var({var})" stroke-width="2"/>')
        out += [f'<circle cx="{px(i):.1f}" cy="{py(s[e]):.1f}" r="4" style="fill:var({var})" class="dot"/>'
                for i, e in enumerate(ends)]
        label_y.append(py(s[ends[-1]]))
    a, c = label_y  # keep the two end labels from colliding
    if abs(a - c) < 14:
        mid = (a + c) / 2
        a, c = (mid - 7, mid + 7) if a <= c else (mid + 7, mid - 7)
    out += [f'<text x="{W - R + 10}" y="{y + 4:.1f}" class="lab">{name} {m(s[ends[-1]], False)}</text>'
            for (name, _, s), y in zip(series, (a, c))]
    for i, e in enumerate(ends):
        tip = f"{year(e)}: revenue {m(h['revenue'][e], False)}, pre-tax income {m(h['pretax_income'][e], False)}"
        out.append(f'<rect x="{px(i) - step_x / 2:.1f}" y="{T}" width="{step_x:.1f}" height="{PLOT_H}" '
                   f'class="hit"><title>{escape(tip)}</title></rect>')
    out += [f'<text x="{L - 6}" y="{by(v) + 4:.1f}" class="ax" text-anchor="end">{money_tick(v)}</text>'
            for v in bt]
    for i, e in enumerate(ends[1:], 1):
        v = g[e]
        top, bot = sorted((by(v), by(0)))
        out.append(f'<rect x="{px(i) - step_x / 4:.1f}" y="{top:.1f}" width="{step_x / 2:.1f}" '
                   f'height="{max(bot - top, 0.5):.1f}" class="{"bar-down" if v > 0 else "bar-up"}"><title>'
                   f'{escape(year(e))}: {escape(m(abs(v), False))} '
                   f'{"costs ran ahead of revenue" if v > 0 else "revenue ran ahead of costs"}</title></rect>')
    out.append(f'<line x1="{L}" x2="{W - R}" y1="{by(0):.1f}" y2="{by(0):.1f}" class="zero"/>')
    key = "".join(f'<li><span class="num">{n}</span><b>{year(e)}</b>: '
                  + "; ".join(escape(d) for d in b[e]) + "</li>" for n, e in enumerate(years, 1))
    legend = "".join(f'<span><i style="background:var({var})"></i>{name}</span>' for name, var, _ in series)
    legend += ('<span><i class="sw bar-down-sw"></i>Costs ran ahead of revenue</span>'
               '<span><i class="sw bar-up-sw"></i>Revenue ran ahead of costs</span>')
    return (f'<p class="legend">{legend}</p>'
            f'<svg class="trend wide" viewBox="0 0 {W} {H}" role="img" aria-label="Revenue and pre-tax income in '
            f'dollars on a log scale, with each year\'s cost gap as bars below; values in the table above">'
            f'{"".join(out)}</svg>'
            + (f'<ol class="key">{key}</ol>' if key else ""))


def dollar_row(l, changes, scale):
    cells = []
    for ch in changes:
        r = next(r for r in ch["lines"] if r["concept"] == l["concept"])
        note = " (line not reported that year)" if r["absent"] else ""
        cells.append(cell(-r["ratio"], scale, f"Line changed {m(r['actual'])}; in step with revenue it would "
                                              f"have changed {m(r['flex'])}{note}"))
    return f'<tr>{label_html(l)}{"".join(cells)}</tr>'




DECISION = re.compile(r"^## (\d{4}-\d{2}-\d{2}) \| (.+)$")
# Decision groups, in page order, with the question each answers.
DECISION_GROUPS = [("Scope", "What gets analyzed"), ("Method", "How the numbers are computed"),
                   ("Presentation", "How the pages show it"), ("Evidence and review", "Why a reader can trust it"),
                   ("Build and process", "How it gets made and changed")]
FIELDS = {"Group", "Decision", "Why", "Status"}


def decisions():
    """[{date, title, group, decision, why, status}] from decisions.md, in file order; fails on any malformed entry."""
    text = (ROOT / "decisions.md").read_text(encoding="utf-8")
    groups = {g for g, _ in DECISION_GROUPS}
    out = []
    for block in re.split(r"\n(?=## )", text)[1:]:
        lines = [l for l in block.strip().splitlines() if l.strip()]
        head = DECISION.match(lines[0])
        fields = dict(l.split(": ", 1) for l in lines[1:] if ": " in l)
        if not head or set(fields) != FIELDS or len(lines) != len(FIELDS) + 1:
            raise SystemExit(f"decisions.md: malformed entry starting {lines[0]!r}")
        if fields["Group"] not in groups:
            raise SystemExit(f"decisions.md: {lines[0]!r} has unknown group {fields['Group']!r}; use one of {sorted(groups)}")
        out.append({"date": head.group(1), "title": head.group(2), "group": fields["Group"],
                    "decision": fields["Decision"], "why": fields["Why"], "status": fields["Status"]})
    return out


# Consideration themes, in page order, with the question each answers.
THEMES = [("Accounting basis", "Is every year measured the same way"), ("Acquisitions", "Is it the same business"),
          ("Presentation", "Does the page read right"), ("Coverage", "Does it hold across companies and browsers"),
          ("Evidence", "Is every claim checked"), ("Path forward", "What comes next")]
CONSIDERATION_FIELDS = ["Theme", "Item", "Why", "Companies", "Due", "Status"]


def considerations():
    """[{date, title, theme, item, why, companies, due, status}] from considerations.md, in file order; fails on any
    malformed entry."""
    text = (ROOT / "considerations.md").read_text(encoding="utf-8")
    themes = {t for t, _ in THEMES}
    out = []
    for block in re.split(r"\n(?=## )", text)[1:]:
        lines = [l for l in block.strip().splitlines() if l.strip()]
        head = DECISION.match(lines[0])
        fields = dict(l.split(": ", 1) for l in lines[1:] if ": " in l)
        if not head or list(fields) != CONSIDERATION_FIELDS or len(lines) != len(CONSIDERATION_FIELDS) + 1:
            raise SystemExit(f"considerations.md: malformed entry starting {lines[0]!r}")
        if fields["Theme"] not in themes:
            raise SystemExit(f"considerations.md: {lines[0]!r} has unknown theme {fields['Theme']!r}; "
                             f"use one of {sorted(themes)}")
        if not (fields["Status"] == "open" or fields["Status"].startswith("closed ")):
            raise SystemExit(f"considerations.md: {lines[0]!r} status must be open or closed YYYY-MM-DD, how")
        out.append({"date": head.group(1), "title": head.group(2)} | {k.lower(): v for k, v in fields.items()})
    return out


def considerations_page():
    items = considerations()
    sections = []
    for theme, question in THEMES:
        members = [i for i in items if i["theme"] == theme]
        members.sort(key=lambda i: i["date"], reverse=True)
        members.sort(key=lambda i: i["status"] != "open")  # open first, newest first within each
        rows = []
        for i in members:
            closed = i["status"] != "open"
            cls = ' class="superseded"' if closed else ""
            rows.append(f'<tr{cls}><th scope="row">{escape(i["title"])}'
                        f'<span class="dim"><br>{i["date"]}</span></th>'
                        f'<td class="text"><p>{escape(i["item"])}</p><p class="why">{escape(i["why"])}</p>'
                        f'<p class="why">Companies: {escape(i["companies"])}</p>'
                        f'<p class="due">Due: {escape(i["due"])}</p>'
                        + (f'<p class="status">{escape(i["status"])}</p>' if closed else "") + '</td></tr>')
        n_open = sum(i["status"] == "open" for i in members)
        sections.append(f'<details class="sector"><summary>{theme} <span class="dim">{question}; {n_open} open of '
                        f'{len(members)}</span></summary><div class="wrap"><table class="decisions"><tbody>'
                        f'{"".join(rows)}</tbody></table></div></details>')
    n_open = sum(i["status"] == "open" for i in items)
    return CONSIDERATIONS.format(sections="\n".join(sections), count=len(items), open=n_open,
                                 nav=nav("considerations.html"), css=CSS)


def plural(n, noun):
    return f"{n} {noun}" if n == 1 else f"{n} {noun}s"


def decisions_page():
    items = decisions()
    sections = []
    for group, question in DECISION_GROUPS:
        members = [i for i in items if i["group"] == group]
        # newest first: later dates first, and within a date the later entry in the file first
        members = sorted(reversed(members), key=lambda i: i["date"], reverse=True)
        by_date = {}
        for i in members:
            by_date.setdefault(i["date"], []).append(i)
        dates = []
        for d, ds in by_date.items():  # second level: one caret per date
            rows = []
            for i in ds:
                cls = "" if i["status"] == "active" else ' class="superseded"'
                note = "" if i["status"] == "active" else f'<p class="status">{escape(i["status"])}</p>'
                rows.append(f'<tr{cls}><th scope="row">{escape(i["title"])}</th>'
                            f'<td class="text"><p>{escape(i["decision"])}</p><p class="why">{escape(i["why"])}</p>'
                            f'{note}</td></tr>')
            dates.append(f'<details class="sub"><summary>{d} <span class="dim">{plural(len(ds), "decision")}'
                         f'</span></summary><div class="wrap"><table class="decisions"><tbody>{"".join(rows)}'
                         f'</tbody></table></div></details>')
        sections.append(f'<details class="sector"><summary>{group} <span class="dim">{question}; '
                        f'{plural(len(members), "decision")}</span></summary>{"".join(dates)}</details>')
    active = sum(i["status"] == "active" for i in items)
    return DECISIONS.format(sections="\n".join(sections), count=len(items), active=active,
                            nav=nav("decisions.html"), css=CSS)


LEGAL_SUFFIX = re.compile(r",? (?:& Company|& Co\.|Inc\.?|Incorporated|Corporation|Corp\.?|Company|Co\.|plc|PLC|"
                          r"Ltd\.?|Limited|LLC|N\.V\.|S\.A\.|SE|AG)$")


def display_name(name):
    """The S&P 500 list's name (data/sp500.json, the only source) as the page shows it: a trailing legal suffix
    dropped ("Apple Inc." -> "Apple"), except a bare "Company" that would leave one word ("Southern Company"
    stays); words that are part of the name stay (Group, Holdings, Trust, Bancorp). Where the list files
    "Home Depot (The)" and nothing was dropped, "The" moves to the front."""
    the = name.endswith(" (The)")
    base = name[:-6] if the else name
    match = LEGAL_SUFFIX.search(base)
    if match and not (match.group(0) == " Company" and len(base[:match.start()].split()) == 1):
        return base[:match.start()]
    return "The " + base if the else base


def page(h, name):
    """One company page; name is the S&P 500 list's (the index page uses the same), not the SEC filer name."""
    changes = h["changes"]
    for ch in changes:  # beyond-revenue effects sum exactly to the pre-tax leverage
        total = -sum(r["ratio"] for r in ch["lines"])
        if abs(total - ch["leverage"]) > 1:
            raise SystemExit(f"{h['ticker']} {ch['to']}: line effects {total:,.0f} != leverage {ch['leverage']:,.0f}")
    scale = max(abs(r["ratio"]) for ch in changes for r in ch["lines"])
    heads = "".join(f"<th>{year(ch['from'])} to {year(ch['to'])}</th>" for ch in changes)

    def plain(label, key, cls=""):
        return (f'<tr class="{cls}"><th scope="row">{label}</th>'
                + "".join(f"<td>{m(ch[key])}</td>" for ch in changes) + "</tr>")
    top = (plain("Revenue change", "revenue_change")
           + plain("Pre-tax income change", "pretax_change", "strong")
           + plain("&nbsp;&nbsp;if every cost moved in step with revenue", "pretax_flex")
           + plain("&nbsp;&nbsp;beyond revenue (sum of lines below)", "leverage"))
    rows = []
    for heading, ls in sections(h):
        rows.append('<tr class="sep"><td colspan="99"></td></tr>' if heading is None else
                    f'<tr class="sub"><th colspan="99">{heading}</th></tr>')
        rows += [dollar_row(l, changes, scale) for l in ls]
    ratio_rows = ratios(h)
    years = "".join(f"<th>{year(e)}</th>" for e in h["period_ends"])
    filings = "; ".join(f'<a href="{escape(f["document_url"])}">10-K for {year(f["report_date"])}</a> '
                        f'(accession {escape(f["accession"])})' for f in h["filings"])
    real = [d for d in h["disagreements"] if not rounding_only(d["latest_filing"], d["earlier_filing"])]
    rounded = len(h["disagreements"]) - len(real)
    shared = year(min(f["report_date"] for f in h["filings"]))  # the earlier 10-K's latest year, in both
    disagreements = (f"The two 10-Ks agree on every figure for {shared}, the year both show"
                     + (", apart from rounding." if rounded else ".")
                     if not real else
                     f"The two 10-Ks differ on these figures for {shared}, the year both show (the later 10-K is "
                     f"used): "
                     + "; ".join(f"{escape(d['item'])} {m(d['latest_filing'], False)} vs "
                                 f"{m(d['earlier_filing'], False)}" for d in real)
                     + (f"; {plural(rounded, 'other figure')} {'differs' if rounded == 1 else 'differ'} only by "
                        f"rounding." if rounded else "."))
    return TEMPLATE.format(company=escape(name), ticker=escape(h["ticker"]), heads=heads, top=top,
                           rows="\n".join(rows), years=years, filings=filings,
                           disagreements=disagreements, ratio_rows=ratio_rows, first=year(h["period_ends"][0]),
                           last=year(h["period_ends"][-1]), nav=nav(), bridge_link=bridge_link(h["ticker"]),
                           ten_years=ten_years(h["ticker"]), ten_breaks=ten_breaks(h["ticker"]), css=CSS)


def headline(ticker):
    """data/headline/<TICKER>.json; fails if headline.py has not run for this company (run it first)."""
    path = HEADLINE / f"{ticker}.json"
    if not path.is_file():
        raise SystemExit(f"{path} missing: run python headline.py {ticker} first")
    return json.loads(path.read_text(encoding="utf-8"))


def ten_breaks(ticker):
    """Recast figures, one line each, at the bottom of the page: every figure a later 10-K changed. Acquisitions
    and accounting standards are not listed here; the chart's numbered key carries them."""
    t = headline(ticker)
    notes = []
    first = {}
    for d in t["disagreements"]:  # the earliest-filed other value is the figure as first reported
        k = (d["period_end"], d["item"])
        if k not in first or d["other_filed"] < first[k]["other_filed"]:
            first[k] = d
    for (e, item), d in sorted(first.items()):
        notes.append((e, f"{escape(item[0].upper() + item[1:])} {m(d['value'], False)} as later recast; first "
                         f"reported as {m(d['other_value'], False)} "
                         f"({(d['value'] - d['other_value']) / abs(d['other_value']) * 100:+.1f}%) in the 10-K "
                         f"filed {d['other_filed']}."))
    items = "".join(f"<li><b>{year(e)}</b>: {text}</li>" for e, text in sorted(notes, key=lambda n: n[0]))
    if not items:
        return ""
    return ('<h2>Note 1 - Recast Figures</h2>\n'
            f'<ul class="breaks">{items}</ul>\n'
            '<p class="note">A later 10-K changed these figures. The table and the chart\'s lines above '
            'already use the later figures; nothing here needs to be added back.</p>\n')


def ten_years(ticker):
    """The long window at the top of the page: revenue, operating income (where reported), pre-tax income and
    margin for ten years, then the chart (trend_chart)."""
    t = headline(ticker)
    ends, rev, op, pre = t["period_ends"], t["revenue"], t["operating_income"], t["pretax_income"]

    notes = []

    def star_note(label, s, e, c, pct):
        """One line under the table for a starred change, naming its line, its years and the figures it compares.
        Fails if neither year in the table differs from the one-filing figures (the star would explain nothing)."""
        y0, y1 = year(c["prior_end"]), year(e)
        recast = [(y, m(s[end], False)) for y, end, v in ((y0, c["prior_end"], c["prior"]), (y1, e, c["value"]))
                  if s[end] != v]
        if not recast:
            raise SystemExit(f"{ticker} {label} {y1}: starred change, but both years match the table")
        figs = recast[0][1] if len(recast) == 1 and recast[0][0] == y1 else " and ".join(f"{y} {f}" for y, f in recast)
        verb, pron = ("is", "it") if len(recast) == 1 else ("are", "them")
        notes.append(f"* {label}, {y1}: the {figs} above {verb} from a later 10-K that recast {pron}. The 10-K filed "
                     f"{c['filed']} reports {y0} and {y1} the same way, {m(c['prior'], False)} and "
                     f"{m(c['value'], False)}; the {pct} compares those two.")

    def growth(label, s, changes):
        """Each year's change from the 10-K that shows both years; starred, with a line under the table, where a
        later 10-K recast one of them. Green when the line grew, red when it shrank (every line here is better
        higher), by the sign as shown."""
        cells = ["<td></td>"]
        for e in ends[1:]:
            c = changes[e]
            r = round((c["value"] - c["prior"]) / abs(c["prior"]) * 100, 1)
            pct = f"{r:+.1f}%"
            cls = ' class="up"' if r > 0 else ' class="down"' if r < 0 else ""
            if c["basis_changed"]:
                star_note(label, s, e, c, pct)
                cells.append(f'<td{cls}>{pct}*</td>')
            else:
                cells.append(f"<td{cls}>{pct}</td>")
        return "".join(cells)
    lines = [(label, s, t["changes"][key]) for label, s, key in
             (("Revenue", rev, "revenue"), ("Operating income", op, "operating_income"),
              ("Pre-tax income", pre, "pretax_income")) if s is not None]
    rows = "".join(f'<tr class="strong"><th scope="row">{label}</th>'
                   + "".join(f"<td>{m(s[e], False)}</td>" for e in ends)
                   + f'</tr><tr><th scope="row">&nbsp;&nbsp;change</th>{growth(label, s, ch)}</tr>'
                   for label, s, ch in lines)
    rows += ('<tr><th scope="row">Pre-tax margin</th>'
             + "".join(f"<td>{pre[e] / rev[e] * 100:.1f}%</td>" for e in ends) + "</tr>")
    return (f'<h2>Ten years</h2>\n<div class="wrap"><table class="ten">\n<thead><tr><th></th>'
            + "".join(f"<th>{year(e)}</th>" for e in ends)
            + f'</tr></thead>\n<tbody>\n{rows}\n</tbody></table></div>\n'
            + ('<p class="note">* See Note 1.</p>\n' if notes else "")
            + trend_chart(t) + '\n')


def bridge_link(ticker):
    """Link to the company's one-year bridge, only if build_bridge has written one (run it first)."""
    if not (OUT / "bridge" / f"{ticker}.html").is_file():
        return ""
    return (f'<p class="crossref"><a href="bridge/{escape(ticker)}.html">One-year bridge</a>: the latest year\'s '
            f'operating income, bar by bar, with management\'s explanations quoted from the 10-K.</p>')


def index_row(c, h):
    """One S&P 500 company: ticker and name; analyzed ones link to their page and carry headline numbers."""
    if h is None:
        return (f'<tr class="pending"><th scope="row">{escape(c["ticker"])}</th>'
                f'<td class="name">{escape(display_name(c["name"]))}</td><td colspan="5"></td></tr>')
    ends = h["period_ends"]
    margin = lambda e: h["pretax_income"][e] / h["revenue"][e] * 100
    rev_growth = (h["revenue"][ends[-1]] / h["revenue"][ends[0]] - 1) * 100
    return (f'<tr><th scope="row"><a href="{escape(h["ticker"])}.html">{escape(h["ticker"])}</a></th>'
            f'<td class="name">{escape(display_name(c["name"]))}</td><td>{year(ends[0])} to {year(ends[-1])}</td>'
            f'<td>{m(h["revenue"][ends[-1]], False)}</td><td>{rev_growth:+.1f}%</td>'
            f'<td>{margin(ends[0]):.1f}%</td><td>{margin(ends[-1]):.1f}%</td></tr>')


def counts(cs, built):
    done = sum(c["ticker"] in built for c in cs)
    noun = "company" if len(cs) == 1 else "companies"
    return f'<span class="dim">{len(cs)} {noun}{f", {done} analyzed" if done else ""}</span>'


def index_body(universe, built):
    """Sector, then sub-industry, then companies; every level collapses behind a caret."""
    head = ('<thead><tr><th></th><th></th><th>Years</th><th>Revenue, latest</th><th>Revenue change</th>'
            '<th>Pre-tax margin, first year</th><th>Pre-tax margin, last year</th></tr></thead>')
    by_sector = {}
    for c in universe["companies"]:
        by_sector.setdefault(c["sector"], {}).setdefault(c["sub_industry"], []).append(c)
    out = []
    for sector in sorted(by_sector):
        subs = by_sector[sector]
        inner = []
        for sub in sorted(subs):
            cs = sorted(subs[sub], key=lambda c: c["ticker"])
            rows = "\n".join(index_row(c, built.get(c["ticker"])) for c in cs)
            inner.append(f'<details class="sub"><summary>{escape(sub)} {counts(cs, built)}</summary>'
                         f'<div class="wrap"><table class="index">{head}<tbody>{rows}</tbody></table></div></details>')
        all_cs = [c for cs in subs.values() for c in cs]
        out.append(f'<details class="sector"><summary>{escape(sector)} {counts(all_cs, built)}</summary>'
                   f'{"".join(inner)}</details>')
    return "\n".join(out)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    companies = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(DATA.glob("*.json"))]
    universe = json.loads((ROOT / "data" / "sp500.json").read_text(encoding="utf-8"))
    built = {h["ticker"]: h for h in companies}
    outside = sorted(set(built) - {c["ticker"] for c in universe["companies"]})
    if outside:
        raise SystemExit(f"analyzed companies missing from data/sp500.json: {outside}")
    names = {c["ticker"]: c["name"] for c in universe["companies"]}
    for h in companies:
        (OUT / f"{h['ticker']}.html").write_text(page(h, display_name(names[h["ticker"]])), encoding="utf-8")
    (OUT / "index.html").write_text(INDEX.format(body=index_body(universe, built), total=len(universe["companies"]),
                                                 analyzed=len(built), source=escape(universe["source"]),
                                                 retrieved=escape(universe["retrieved"]), nav=nav("index.html"), css=CSS),
                                    encoding="utf-8")
    (OUT / "decisions.html").write_text(decisions_page(), encoding="utf-8")
    (OUT / "considerations.html").write_text(considerations_page(), encoding="utf-8")
    print(f"docs/: {len(companies)} company pages, index.html, decisions.html and considerations.html "
          f"({len(universe['companies'])} S&P 500 companies listed)")


CSS = """
:root { color-scheme: light; --s1: #2a78d6; --s2: #eb6834; --bg: #ffffff; --ink: #0b0b0b; --ink-2: #52514e; --ink-3: #75746f;
  --rule: #e2e1dc; --up: #1f8a4c; --down: #d03b3b; --up-text: #17703d; --down-text: #b42828; --link: #1c5cab; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { color-scheme: dark; --s1: #3987e5; --s2: #d95926;
  --bg: #1a1a19; --ink: #f0efec; --ink-2: #c3c2b7; --ink-3: #9a9992; --rule: #383835;
  --up: #3fb36b; --down: #e05252; --up-text: #3fb36b; --down-text: #e05252; --link: #86b6ef; } }
:root[data-theme="dark"] { color-scheme: dark; --s1: #3987e5; --s2: #d95926; --bg: #1a1a19; --ink: #f0efec; --ink-2: #c3c2b7;
  --ink-3: #9a9992; --rule: #383835; --up: #3fb36b; --down: #e05252; --up-text: #3fb36b; --down-text: #e05252;
  --link: #86b6ef; }
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink);
  font: 16px/1.5 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
main { max-width: 60rem; margin: 0 auto; padding: 2rem 1rem 4rem; }
h1 { font-size: 1.5rem; line-height: 1.25; margin: 0 0 .5rem; }
h2 { font-size: 1.05rem; margin: 2rem 0 .5rem; }
.lede { color: var(--ink-2); max-width: 46rem; margin: 0 0 1.25rem; }
a { color: var(--link); }
.wrap { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font-variant-numeric: tabular-nums; font-size: .9rem; }
th, td { padding: .4rem .6rem; border-bottom: 1px solid var(--rule); text-align: right; white-space: nowrap; }
thead th { font-weight: 600; color: var(--ink-3); font-size: .8rem; }
tbody th { text-align: left; font-weight: normal; white-space: normal; min-width: 12rem; }
table.ten tbody th { min-width: 9rem; } /* ten columns of figures must fit the page width */
table.ten th, table.ten td { padding: .4rem .5rem; }
tr.strong th, tr.strong td { font-weight: 600; }
tr.sep th, tr.sep td { border-bottom: 2px solid var(--rule); }
.dim { color: var(--ink-3); font-size: .8rem; }
.legend { display: flex; flex-wrap: wrap; gap: .25rem 1.25rem; font-size: .85rem; color: var(--ink-2);
  margin: .5rem 0 .25rem; align-items: center; }
.legend i { display: inline-block; width: .8rem; height: .2rem; border-radius: 1px; margin-right: .4rem;
  vertical-align: middle; }
.trend { display: block; width: 100%; max-width: 40rem; height: auto; margin-bottom: 1rem; }
.trend .g { stroke: var(--rule); stroke-width: 1; }
.trend .ax { fill: var(--ink-3); font-size: 11px; }
.trend .lab { fill: var(--ink-2); font-size: 12px; }
.trend .dot { stroke: var(--bg); stroke-width: 2; }
.trend .hit { fill: transparent; }
.trend .hit:hover { fill: var(--rule); fill-opacity: .35; }
.trend.wide { max-width: 50rem; }
.trend .zero { stroke: var(--ink-3); stroke-width: 1; }
.trend .bar-down { fill: var(--down); fill-opacity: .55; }
.trend .bar-up { fill: var(--up); fill-opacity: .55; }
.legend .sw { width: .8rem; height: .8rem; }
.bar-down-sw { background: var(--down); opacity: .55; }
.bar-up-sw { background: var(--up); opacity: .55; }
.trend .guide { stroke: var(--ink-3); stroke-dasharray: 2 3; stroke-width: 1; }
.trend .mark { fill: var(--ink); }
.trend .marknum { fill: var(--bg); font-size: 11px; font-weight: 700; }
ol.key { list-style: none; padding: 0; margin: .5rem 0 1rem; font-size: .85rem; color: var(--ink-2); max-width: 46rem; }
ol.key li { margin: 0 0 .3rem; }
ol.key .num { display: inline-block; width: 1.3rem; height: 1.3rem; line-height: 1.3rem; border-radius: 50%;
  background: var(--ink); color: var(--bg); text-align: center; font-size: .75rem; font-weight: 700;
  margin-right: .5rem; }
tr.sub th { text-align: left; font-size: .8rem; font-weight: 600; color: var(--ink-3); padding-top: .9rem; }
td.name { text-align: left; white-space: normal; }
table.index tbody th { min-width: 4rem; width: 4rem; }
table.index td.name { width: 16rem; }
tr.pending th, tr.pending td { color: var(--ink-3); }
details.sector { border-bottom: 1px solid var(--rule); }
details.sector > summary { font-weight: 600; font-size: 1.05rem; }
details.sub { margin-left: 1.25rem; }
details.sub > summary { font-size: .95rem; }
details > summary { cursor: pointer; padding: .45rem 0; }
details > summary .dim { margin-left: .5rem; font-weight: normal; }
details.sub[open] { margin-bottom: .75rem; }
h2 .dim { font-weight: normal; margin-left: .4rem; }
table.decisions td, table.decisions th { vertical-align: top; text-align: left; white-space: normal; }
table.decisions td.date { white-space: nowrap; color: var(--ink-3); width: 6.5rem; }
table.decisions tbody th { font-weight: 600; width: 13rem; min-width: 9rem; }
table.decisions td.text p { margin: 0 0 .3rem; }
table.decisions .why { color: var(--ink-2); font-size: .85rem; }
table.decisions .status { color: var(--down-text); font-size: .8rem; }
table.decisions .due { font-size: .85rem; font-weight: 600; }
td.up { color: var(--up-text); }  /* text shades: darker than the cell shading, readable at regular weight */
td.down { color: var(--down-text); }
tr.superseded th, tr.superseded td.text p:not(.status) { color: var(--ink-3); text-decoration: line-through; }
table.index thead th { white-space: normal; vertical-align: bottom; }
ul.breaks { font-size: .85rem; color: var(--ink-2); max-width: 46rem; padding-left: 1.1rem; margin: .75rem 0; }
ul.breaks li { margin-bottom: .2rem; }
.note, footer { font-size: .85rem; color: var(--ink-2); max-width: 46rem; }
footer { margin-top: 2.5rem; border-top: 1px solid var(--rule); padding-top: 1rem; }
""" + header.CSS

TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{ticker} - Chomper</title>
<style>{css}</style>
</head>
<body>
<main>
{nav}
<h1>{company}</h1>
{bridge_link}
{ten_years}
<h2>Five years: which costs moved with revenue, {first} to {last}</h2>

<details class="sector"><summary>Costs as a share of revenue</summary>
<div class="wrap"><table>
<thead><tr><th></th>{years}</tr></thead>
<tbody>
{ratio_rows}
</tbody></table></div>
</details>

<details class="sector"><summary>In dollars</summary>
<div class="wrap"><table>
<thead><tr><th></th>{heads}</tr></thead>
<tbody>
{top}
{rows}
</tbody></table></div>
</details>

{ten_breaks}
<footer>
<p>Source: {filings}. Lines, labels and order come from each filing's income statement; every year foots
to reported pre-tax income, and to operating income where the company reports it. {disagreements}</p>
</footer>
</main>
</body>
</html>
"""

INDEX = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Chomper</title>
<style>{css}</style>
</head>
<body>
<main>
{nav}
<h1>Which costs moved with revenue</h1>
<p class="lede">The S&amp;P 500 by sector and sub-industry: {total} companies, {analyzed} analyzed so far.
Linked tickers open five years of cost lines from the company's own 10-K filings.</p>
{body}
<footer>
<p>Sectors and sub-industries are GICS, a taxonomy owned by S&amp;P and MSCI, taken from Wikipedia's
<a href="{source}">list of S&amp;P 500 companies</a> (retrieved {retrieved}); an unofficial copy. Every company's
SEC identifier was checked against the SEC's own ticker file.</p>
</footer>
</main>
</body>
</html>
"""


DECISIONS = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Decisions - Chomper</title>
<style>{css}</style>
</head>
<body>
<main>
{nav}
<h1>Decisions</h1>
<p class="lede">Every decision behind these pages, grouped by the question it answers, newest first within
each group: {active} active of {count}.</p>
{sections}
<footer>
<p>Source: decisions.md in the project folder. To change a decision, add a new entry there and mark the old
one superseded, then rebuild.</p>
</footer>
</main>
</body>
</html>
"""


CONSIDERATIONS = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Considerations - Chomper</title>
<style>{css}</style>
</head>
<body>
<main>
{nav}
<h1>Considerations</h1>
<p class="lede">What these pages do not yet do right, or what comes next, grouped by the question it touches,
each with the condition that makes it due: {open} open of {count}.</p>
{sections}
<footer>
<p>Source: considerations.md in the project folder. To close an item, change its status there, then rebuild.</p>
</footer>
</main>
</body>
</html>
"""


if __name__ == "__main__":
    main()
