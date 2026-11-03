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
from headline import FIRST
from pull import ROOT

DATA = ROOT / "data" / "history"
HEADLINE = ROOT / "data" / "headline"
OUT = ROOT / "docs"


def m(dollars, sign=True):
    v = dollars / 1e6
    if abs(v) >= 1_000_000:  # the S&P 500 page's sums
        s = f"${abs(v) / 1_000_000:,.2f}T"
    elif abs(v) >= 1000:
        s = f"${abs(v) / 1000:,.2f}B"
    else:
        s = f"${abs(v):,.1f}M"
    if s in ("$0.0M", "$0.00B"):
        return "$0.0M"
    return ("+" if v > 0 else "-") + s if sign else ("-" + s if v < 0 else s)


def footing(h):
    """The footer's footing sentence; any gap allowed as the filing's own rounding is named with both values,
    once per year and subtotal (the first filing listed is the latest, whose figures the page uses)."""
    base = "every year foots\nto reported pre-tax income, and to operating income where the company reports it"
    seen, parts = set(), []
    for g in h["footing_gaps"]:
        if (g["period_end"], g["subtotal"]) not in seen:
            seen.add((g["period_end"], g["subtotal"]))
            digits = max(0, -math.floor(math.log10(abs(g["gap"]) / 1e6)))  # in millions, fine enough to show the gap

            def mm(v):
                return f"{'-' if v < 0 else ''}${abs(v) / 1e6:,.{digits}f}M"
            parts.append((g["period_end"], f"{year(g['period_end'])} {g['subtotal']}, lines {mm(g['lines_total'])} "
                                           f"against reported {mm(g['reported'])}"))
    if not parts:
        return base + "."
    return (base + ", apart from the filing's own rounding, shown in the rows headed \"Rounding in the filing\": "
            + "; ".join(s for _, s in sorted(parts)) + ".")


def retags(h):
    """The footer's sentence for lines the company tagged differently between its two 10-Ks, shown as one row."""
    rows = [l for l in h["lines"] if l.get("retagged")]
    if not rows:
        return ""

    def span(ys):
        return year(ys[0]) if len(ys) == 1 else f"{year(ys[0])} to {year(ys[-1])}"
    return (" " + ("One line carries" if len(rows) == 1 else "These lines carry")
            + " a different XBRL tag in the two 10-Ks and " + ("is" if len(rows) == 1 else "are each") + " shown as one row: "
            + "; ".join(f"{escape(l['label'])}, tagged "
                        + ", then ".join(f"{escape(t['concept'].split('_', 1)[-1])} for {span(t['years'])}"
                                         for t in l["retagged"] if t["years"])
                        for l in rows) + ".")


def pretax_line(h):
    """The footer's sentence when pre-tax income is found by position rather than by its usual tag."""
    found = [(f, f["pretax_by_position"]) for f in h["filings"] if f.get("pretax_by_position")]
    if not found:
        return ""
    labels = sorted({p["label"] for _, p in found})
    which = ("both 10-Ks" if len(found) == 2 else f"the 10-K for {year(found[0][0]['report_date'])}")
    return (f" Pre-tax income is the line {which} label{'s' if len(found) == 1 else ''} "
            + " / ".join(f"&ldquo;{escape(l)}&rdquo;" for l in labels)
            + ": the statement subtracts income tax from it to reach net income.")


def summed(h):
    """The footer's sentence for lines the filing reports only by member (BA's cost of goods and services sold, by
    product and service), shown as the members' sum."""
    rows = [l for l in h["lines"] if l.get("summed_members")]
    if not rows:
        return ""
    parts = []
    for l in rows:
        ys = sorted(l["summed_members"])
        groups = []  # consecutive years with the same members
        for e in ys:
            if groups and groups[-1][1] == l["summed_members"][e]:
                groups[-1][0].append(e)
            else:
                groups.append(([e], l["summed_members"][e]))
        parts.append(f"{escape(l['label'])}, " + "; ".join(
            (year(es[0]) if len(es) == 1 else f"{year(es[0])} to {year(es[-1])}") + ", the sum of the parts labeled "
            + " and ".join(f"&ldquo;{escape(m.removesuffix(' [Member]'))}&rdquo;" for m in ms) for es, ms in groups))
    return (" The filing tags " + ("one line" if len(rows) == 1 else "these lines")
            + " only in parts, with no total, shown here summed: " + "; ".join(parts) + ".")


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


def adoptions():
    """{(ticker, "606" or "842"): record} from data/adoptions.json, read by hand from each company's 10-K."""
    d = json.loads((ROOT / "data" / "adoptions.json").read_text(encoding="utf-8"))
    return {(a["ticker"], a["standard"]): a for a in d["adoptions"]}


def deal_names():
    """{XBRL member: name} from data/deal_names.json, the acquired company's name read by hand from the buyer's
    10-K prose."""
    d = json.loads((ROOT / "data" / "deal_names.json").read_text(encoding="utf-8"))
    return {r["member"]: r["name"] for r in d["deals"]}


def chart_breaks(h):
    """{end: [text]} for each year with a significant acquisition or a new accounting standard: the years numbered
    on the chart and listed in its key. A standard is marked in the year the company adopted it (data/adoptions.json);
    one adopted with earlier years recast is not marked, since the series has no break there, nor is one the
    company's own 10-K says does not reach its main business (out_of_scope, e.g. PGR 606). With no adoption
    note found, it stays on the year it became required. A deal is named from data/deal_names.json. Fails if a
    company has no record for a standard or a significant deal, or an adoption year is not one of its ten."""
    out = {}
    names = deal_names()
    for d in h["deals"]:
        if d["significant"]:
            name = names.get(d["member"]) or (d["name"] if d.get("by_hand") else None)  # hand records carry it
            if name is None:
                raise SystemExit(f"{h['ticker']}: no name for {d['member']} in data/deal_names.json")
            if d.get("significant_by") == "assets":  # cheap to buy, large to absorb: the asset test marked it
                brought = (f"{m(d['assets_acquired'], False)} of assets" if d.get("assets_acquired") is not None
                           else f"at least {m(d['assets_floor'], False)} of assets")
                text = (f"Acquired {name} for {m(d['size'], False)}, bringing {brought}, {d['asset_share']:.0%} of "
                        f"total assets at the prior year end")
            else:
                text = (f"Acquired {name}, {m(d['size'], False)}, {d['share_of_assets']:.0%} of total assets at the "
                        f"prior year end")
            out.setdefault(d["fiscal_year_end"], []).append(text)
    records = adoptions()
    for s in h["standards"]:
        code = s["standard"].split()[1]  # "ASC 606 (revenue)" -> "606"
        a = records.get((h["ticker"], code))
        if a is None:
            raise SystemExit(f"{h['ticker']}: no ASC {code} record in data/adoptions.json")
        if a.get("out_of_scope"):
            continue
        if a["recast"]:
            # A full retrospective adoption recasts only the years its 10-K presents (that year and the two
            # before). A series reaching further back has a break where the recast starts: the record names that
            # year (recast_from), or the build stops.
            ends = h["period_ends"]
            first_recast = a.get("recast_from")
            if first_recast is None:
                if a["year_ending"] in ends and ends.index(a["year_ending"]) > 2:
                    raise SystemExit(f"{h['ticker']} ASC {code}: recast, but the series starts before the years the "
                                     f"adoption 10-K presents; add recast_from to data/adoptions.json")
                continue
            if first_recast not in ends:
                raise SystemExit(f"{h['ticker']} ASC {code}: recast_from {first_recast} is not one of its years")
            if ends.index(first_recast) > 0:
                out.setdefault(first_recast, []).append(
                    f"{s['standard']} adopted in {year(a['year_ending'])} with this year and after recast; earlier "
                    f"years as first reported")
            continue
        if a["year_ending"] is None:
            out.setdefault(s["fiscal_year_end"], []).append(f"{s['standard']} required this year")
            continue
        if a["year_ending"] not in h["period_ends"]:
            raise SystemExit(f"{h['ticker']} ASC {code}: adoption year {a['year_ending']} is not one of its years")
        out.setdefault(a["year_ending"], []).append(
            f"{s['standard']} adopted" + ("; earlier years not recast" if a["recast"] is False else ""))
    return out


def money_tick(v):
    """An axis label: $0, $500M, $2B, -$1B."""
    if v == 0:
        return "$0"
    s = (f"${abs(v) / 1e12:g}T" if abs(v) >= 1e12 else f"${abs(v) / 1e9:g}B" if abs(v) >= 1e9
         else f"${abs(v) / 1e6:g}M")
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
    faster than revenue that year. No bar for a year whose prior year was a loss or zero: a negative margin scaled
    by revenue is not a cost gap (Carnival, Nov 2022: -499% on 6.4x revenue gave $54.6B). Fails if revenue and
    pre-tax income took that pair from different filings."""
    rev, pre = h["changes"]["revenue"], h["changes"]["pretax_income"]
    out = {}
    for e in h["period_ends"][1:]:
        r, p = rev[e], pre[e]
        if (r["filed"], r["prior_end"]) != (p["filed"], p["prior_end"]):
            raise SystemExit(f"{h['ticker']} {e}: revenue and pre-tax income changes come from different filings")
        if p["prior"] <= 0:
            continue
        out[e] = r["value"] * p["prior"] / r["prior"] - p["value"]
    return out


# US recessions as the NBER dates them (peak month to trough month), the official US business-cycle dates:
# https://www.nber.org/research/data/us-business-cycle-expansions-and-contractions
RECESSIONS = [("2007-12-01", "2009-06-30"), ("2020-02-01", "2020-04-30")]
RECESSION_SHARE = 0.25  # a fiscal year is a recession year when it holds a quarter or more of a recession's days


def fiscal_start(ends, i):
    """The first day of fiscal year i: the day after the prior year's end (a year before the end for the first)."""
    prev = ends[i - 1] if i else str(int(ends[i][:4]) - 1) + ends[i][4:]
    return (date.fromisoformat(prev) + timedelta(days=1)).isoformat()


def recession_years(ends, recessions=RECESSIONS):
    """Fiscal years holding RECESSION_SHARE or more of a US recession's days. A share, not a fixed length, because
    the 2020 recession lasted three months: a fixed three-month test missed a fiscal year starting 3 February."""
    out = set()
    for i, e in enumerate(ends):
        a = date.fromisoformat(fiscal_start(ends, i))
        for s, t in recessions:
            s, t = date.fromisoformat(s), date.fromisoformat(t)
            lo, hi = max(a, s), min(date.fromisoformat(e), t)
            if ((hi - lo).days + 1) / ((t - s).days + 1) >= RECESSION_SHARE:
                out.add(e)
    return out


def recession_span(ends):
    """The recessions that shade a year in this table, as the note names them ("December 2007 to June 2009;
    February to April 2020"); a recession the table never reaches is left out."""
    parts = []
    for s, t in RECESSIONS:
        if recession_years(ends, [(s, t)]):
            a, b = date.fromisoformat(s), date.fromisoformat(t)
            parts.append(f"{a:%B} to {b:%B %Y}" if a.year == b.year else f"{a:%B %Y} to {b:%B %Y}")
    return "; ".join(parts)


def start_note(ends):
    """One line under the long-view heading when the series does not reach fiscal 2007 (headline.FIRST): the years
    before its first year have not been read for this company yet."""
    if ends[0] <= FIRST[1]:
        return ""
    return (f'<p class="note">The years before {year(ends[0])} have not yet been read for this company; the long view '
            'starts at fiscal 2007, the pre-crisis peak, once they are.</p>\n')


def trend_chart(h):
    """Revenue and pre-tax income in dollars on a log scale (the table's figures), each year with a break numbered
    at the top and explained in a key; under it, a band of bars for each year's cost gap (cost_gaps). A log scale
    has no zero or negative, so a year with zero or negative pre-tax income breaks the income line and sits on a
    loss strip under the plot, labeled with its amount. Fails if a year's revenue is zero or negative."""
    ends = h["period_ends"]
    series = [("Revenue", "--s1", h["revenue"]), ("Pre-tax income", "--s2", h["pretax_income"])]
    if min(h["revenue"][e] for e in ends) <= 0:
        raise SystemExit(f"{h['ticker']}: a year's revenue is zero or negative")
    losses = [e for e in ends if h["pretax_income"][e] <= 0]
    vals = [s[e] for _, _, s in series for e in ends if s[e] > 0]
    W, L, R, T, PLOT_H, X_H, GAP, BAND_H = 800, 60, 170, 26, 280, 26, 18, 110
    # Loss labels on the strip alternate between two lines where loss years are adjacent, so they never collide.
    lower = {}
    for e in losses:
        i = ends.index(e)
        lower[e] = int(i > 0 and ends[i - 1] in lower and not lower[ends[i - 1]])
    LOSS_H = (58 if any(lower.values()) else 46) if losses else 0
    ticks = log_ticks(min(vals), max(vals))
    lo, hi = math.log10(ticks[0]), math.log10(ticks[-1])
    step_x = (W - L - R) / len(ends)  # one slot per year, so every bar sits inside the plot
    px = lambda i: L + (i + 0.5) * step_x
    py = lambda v: T + (hi - math.log10(v)) / (hi - lo) * PLOT_H if v > 0 else T + PLOT_H + 22
    g = cost_gaps(h)
    bt = bar_ticks(list(g.values()))
    b0 = T + PLOT_H + LOSS_H + X_H + GAP
    by = lambda v: b0 + (bt[-1] - v) / (bt[-1] - bt[0]) * BAND_H
    H = b0 + BAND_H + 8

    # Recession years shaded as whole year slots, the same years the table shades: each point is a fiscal year,
    # so the shading covers the points the recession falls in.
    rec = recession_years(ends)
    out = [f'<rect x="{px(i) - step_x / 2:.1f}" y="{T}" width="{step_x:.1f}" height="{H - 8 - T}" class="rec">'
           f'<title>{escape(year(e))}: fiscal year in a US recession (NBER)</title></rect>'
           for i, e in enumerate(ends) if e in rec]
    out += [f'<line x1="{L}" x2="{W - R}" y1="{py(v):.1f}" y2="{py(v):.1f}" class="g"/>'
           f'<text x="{L - 6}" y="{py(v) + 4:.1f}" class="ax" text-anchor="end">{money_tick(v)}</text>'
           for v in ticks]
    # The axis shows the year alone ("Jan 2009" -> 2009); the table's rows carry the month.
    out += [f'<text x="{px(i):.1f}" y="{T + PLOT_H + LOSS_H + 18}" class="ax" text-anchor="middle">'
            f'{year(e).split()[-1]}</text>' for i, e in enumerate(ends)]
    if losses:
        out.append(f'<text x="{L - 6}" y="{T + PLOT_H + 26}" class="ax" text-anchor="end">Loss</text>')
        out += [f'<text x="{px(ends.index(e)):.1f}" y="{T + PLOT_H + 40 + 12 * lower[e]}" class="ax" '
                f'text-anchor="middle">{m(h["pretax_income"][e], False)}</text>' for e in losses]
    b = chart_breaks(h)
    years = [e for e in ends if e in b]
    out += [f'<line x1="{px(ends.index(e)):.1f}" x2="{px(ends.index(e)):.1f}" y1="{T - 2}" y2="{T + PLOT_H}" '
            f'class="guide"/><circle cx="{px(ends.index(e)):.1f}" cy="{T - 10}" r="9" class="mark"/>'
            f'<text x="{px(ends.index(e)):.1f}" y="{T - 6}" class="marknum" text-anchor="middle">{n}</text>'
            for n, e in enumerate(years, 1)]
    label_y = []
    for name, var, s in series:
        runs, run = [], []  # the line runs only through consecutive years above zero
        for i, e in enumerate(ends):
            if s[e] > 0:
                run.append(f"{px(i):.1f},{py(s[e]):.1f}")
            elif run:
                runs.append(run)
                run = []
        runs += [run] if run else []
        out += [f'<polyline points="{" ".join(r)}" fill="none" style="stroke:var({var})" stroke-width="2"/>'
                for r in runs if len(r) > 1]
        out += [f'<circle cx="{px(i):.1f}" cy="{py(s[e]):.1f}" r="4" style="fill:var({var})" class="dot"/>'
                for i, e in enumerate(ends)]
        label_y.append(py(s[ends[-1]]))
    a, c = label_y  # keep the two end labels from colliding
    if abs(a - c) < 14 and h["pretax_income"][ends[-1]] > 0:
        mid = (a + c) / 2
        a, c = (mid - 7, mid + 7) if a <= c else (mid + 7, mid - 7)
    out += [f'<text x="{W - R + 10}" y="{y + 4:.1f}" class="lab">{name} {m(s[ends[-1]], False)}</text>'
            for (name, _, s), y in zip(series, (a, c))]
    for i, e in enumerate(ends):
        tip = f"{year(e)}: revenue {m(h['revenue'][e], False)}, pre-tax income {m(h['pretax_income'][e], False)}"
        out.append(f'<rect x="{px(i) - step_x / 2:.1f}" y="{T}" width="{step_x:.1f}" height="{PLOT_H + LOSS_H}" '
                   f'class="hit"><title>{escape(tip)}</title></rect>')
    out += [f'<text x="{L - 6}" y="{by(v) + 4:.1f}" class="ax" text-anchor="end">{money_tick(v)}</text>'
            for v in bt]
    for i, e in enumerate(ends[1:], 1):
        if e not in g:  # prior year a loss: no cost gap (cost_gaps)
            continue
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
    if rec:
        legend += '<span><i class="sw rec-sw"></i>Fiscal year in a US recession (NBER)</span>'
    return (f'<p class="legend">{legend}</p>'
            f'<svg class="trend wide" viewBox="0 0 {W} {H}" role="img" aria-label="Revenue and pre-tax income in '
            f'dollars on a log scale{", loss years on a strip under the plot" if losses else ""}, with each year\'s '
            f'cost gap as bars below; values in the table above">'
            f'{"".join(out)}</svg>'
            + (f'<ol class="key">{key}</ol>' if key else ""))


def shown(ch, r):
    """The amount a five-year dollar cell shows: the line's effect beyond revenue, or, in a column that starts
    from a loss year (ch["loss_base"]), its whole change, since scaling a loss by revenue means nothing."""
    return -r["actual"] if ch["loss_base"] else -r["ratio"]


def dollar_row(l, changes, scale):
    cells = []
    for ch in changes:
        r = next(r for r in ch["lines"] if r["concept"] == l["concept"])
        note = " (line not reported that year)" if r["absent"] else ""
        title = (f"Line changed {m(r['actual'])}; no split in step with revenue, since {year(ch['from'])} was a loss"
                 if ch["loss_base"] else
                 f"Line changed {m(r['actual'])}; in step with revenue it would have changed {m(r['flex'])}")
        cells.append(cell(shown(ch, r), scale, title + note))
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


def waterfall_page():
    """The population waterfall from data/waterfall.json (written by waterfall.py): one table per path, each row a
    level with its count, the share of the level above it, and what fell out and why."""
    w = json.loads((ROOT / "data" / "waterfall.json").read_text(encoding="utf-8"))
    mem, today, five, ten, pub, ms, agg = (w[k] for k in ("membership", "today", "five_year", "ten_year", "published",
                                                           "measure", "aggregate"))

    def month(m):
        return f'{["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"][int(m[5:]) - 1]} {m[:4]}'

    def table(rows):
        """rows: (label, count, base, note, link); the bar is count / the first row's count."""
        top = rows[0][1]
        out = ['<table class="fall"><thead><tr><th>Level</th><th class="n">Companies</th><th class="n">Of the level above</th>'
               '<th>What falls out, and why</th></tr></thead><tbody>']
        for label, count, base, note, link in rows:
            share = "" if base is None else f"{100 * count / base:.0f}%"
            width = 100 * count / top
            out.append(f'<tr><th scope="row">{label}</th><td class="n">{count:,}</td><td class="n">{share}</td>'
                       f'<td class="text"><div class="bar"><i style="width:{width:.1f}%"></i></div><p>{note}'
                       + (f' <a href="{link[0]}">{link[1]}</a>.' if link else "") + '</p></td></tr>')
        out.append("</tbody></table>")
        return "".join(out)

    def classes(d):
        """'51 series too short under the tags read; 20 acquisition spend ...': the count first, the cause lower-cased."""
        return "; ".join(f"{v} {escape(k[0].lower() + k[1:])}" for k, v in d.items())

    not_read = {k: NOT_READABLE[k] for k in five["classes"]}
    sections = []
    # 1. who could be read
    sections.append("<h2>Who could be read</h2>" + table([
        (f"In the S&amp;P 500 in any month, {month(mem['first'])} to {month(mem['last'])}", mem["companies"], None,
         f"Every company the index held at any point in those ten years, matched across months by SEC identifier. "
         f"Membership before {month(mem['first'])} has not been read, so a fifteen- or twenty-year population does not "
         f"exist here yet.", ("membership.html", "Who was in the S&amp;P 500")),
        (f"Still in the index in {month(mem['last'])}", mem["in_last_month"], mem["companies"],
         f"{mem['left_before_last']} left the index before then: acquired, delisted or dropped. The readers below run on "
         f"today's list only, so those {mem['left_before_last']} are not read anywhere yet.", None),
        (f"On today's list ({today['retrieved']})", today["companies"], None,  # not a subset of the row above: no share
         f"{today['tickers']} tickers for {today['companies']} companies, since {len(today['two_class'])} companies list two "
         f"share classes ({', '.join(' and '.join(p) for p in today['two_class'])}). {len(today['not_in_membership'])} of the "
         f"{today['companies']} are not in the membership file: they joined after {month(mem['last'])} or now file under a "
         f"new identifier ({', '.join(today['not_in_membership'])}).", None),
    ]))
    # 2. the readers
    sections.append("<h2>Read from the filings</h2>" + table([
        ("Tickers on today's list", today["tickers"], None, "The population every reader runs on.", ("index.html", "Chomper")),
        ("Two 10-Ks read, every year footing to pre-tax income", five["readable"], today["tickers"],
         f"{five['not_readable']} cannot be read yet, by cause: " + "; ".join(
             f"{v} where {escape(not_read[k][0].lower() + not_read[k][1:].rstrip('.'))}" for k, v in five["classes"].items())
         + ". Each row on the Chomper page says which", ("index.html", "Chomper")),
        (f"Read back to the first year the SEC holds (bulk run of {ten['run']})", ten["passed"], five["readable"],
         f"{ten['stopped']} stopped, by cause: {classes(ten['classes'])}. A stop is not a verdict on the company: the long "
         f"view must reach fiscal 2007, and the SEC's structured data begins in 2009, so nearly every company waits on a "
         f"hand record for its first years, the step each published page went through.", None),
        ("Finished by hand and published", len(pub["pages"]), ten["passed"],
         f"{', '.join(pub['pages'])}. One-year bridge: {', '.join(pub['bridges'])}.", ("index.html", "Chomper")),
    ]))
    # 3. the cost measure
    sections.append("<h2>What the cost measure would see (version 2, not built)</h2>" + table([
        ("Ten-year series under the earlier rules", ms["companies"], None,
         "Counted on the bulk run made before the fiscal-2007 rule (2026-11-02, 17:15), when a series could start "
         "after 2007 and acquisitions before XBRL were not required; the only ten-year sample wide enough to show what "
         "the measure would see. Not the same population as the row above.", None),
        (f"With at least one fall year (revenue down {ms['fall'] * 100:.0f}% or more on the prior fiscal year)",
         ms["fall_companies"], ms["companies"], f"{ms['fall_years']} fall years in all; most companies have one or none, and 2020 "
         f"holds many of them.", None),
        ("Fall years carrying both operating and pre-tax income", ms["both_companies"], ms["fall_companies"],
         f"{ms['both_years']} fall years. The other {ms['pre_only_years']} fall years, in {ms['pre_only_companies']} companies, "
         f"have pre-tax income only (banks and insurers above all).", None),
    ]))
    # 4. the S&P 500 page
    sections.append("<h2>The S&amp;P 500 page, a separate path</h2>" + table([
        ("Companies on today's list", today["companies"], None,
         "This page reads each company's own filed figures (the SEC's companyfacts), one value per fiscal year, placed by the year it most nearly covers.", ("aggregate.html", "S&amp;P 500")),
        ("Summed", agg["summed"], today["companies"],
         f"{agg['excluded']} left out, by cause: {classes(agg['reasons'])}. The page names each one", ("aggregate.html", "S&amp;P 500")),
    ]))
    return WATERFALL.format(sections="\n".join(sections), nav=nav("waterfall.html"), css=CSS)


def readme_page():
    """README.md as a page: the same words, the same order. The README's small Markdown (headings, paragraphs,
    bullet lists, one indented code block, an image, inline code, bare links) is converted here; anything else in
    the file is a hard stop, so the page never silently drops a line."""
    src = (ROOT / "README.md").read_text(encoding="utf-8")

    def inline(s):
        s = escape(s)
        if "**" in s or "](" in s and "![" not in s:
            raise SystemExit(f"README.md: construct not rendered: {s[:60]}")
        s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
        return re.sub(r"(https?://[^\s<]+?)([.,;)]?)(?=\s|$)", r'<a href="\1">\1</a>\2', s)

    out = []
    for block in re.split(r"\n\s*\n", src.strip()):
        lines = block.split("\n")
        if block.startswith("# "):
            out.append(f"<h1>{inline(block[2:])}</h1>")
        elif block.startswith("## "):
            out.append(f"<h2>{inline(block[3:])}</h2>")
        elif block.startswith("!["):
            alt, path = re.fullmatch(r"!\[(.*?)\]\((.*?)\)", block.strip()).groups()
            if not path.startswith("docs/"):
                raise SystemExit(f"README.md: image outside docs/: {path}")
            out.append(f'<figure><img src="{escape(path[5:])}" alt="{escape(alt)}"><figcaption>{inline(alt)}</figcaption></figure>')
        elif all(l.startswith("    ") for l in lines):
            out.append("<pre>" + escape("\n".join(l[4:] for l in lines)) + "</pre>")
        elif block.startswith("- "):
            items, cur = [], None
            for l in lines:
                if l.startswith("- "):
                    cur = [l[2:]]
                    items.append(cur)
                elif l.startswith("  ") and cur is not None:
                    cur.append(l.strip())
                else:
                    raise SystemExit(f"README.md: list line not understood: {l!r}")
            out.append("<ul>" + "".join(f"<li>{inline(' '.join(i))}</li>" for i in items) + "</ul>")
        else:
            out.append(f"<p>{inline(' '.join(l.strip() for l in lines))}</p>")
    return README.format(body="\n".join(out), nav=nav("readme.html"), css=CSS)


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
    # A column that starts from a loss year gets no split in step with revenue (a loss scaled by revenue means
    # nothing); its lines show their whole change, which sums to revenue change less pre-tax income change.
    changes = [ch | {"loss_base": h["pretax_income"][ch["from"]] <= 0} for ch in h["changes"]]
    for ch in changes:  # beyond-revenue effects sum exactly to the pre-tax leverage
        total = -sum(r["ratio"] for r in ch["lines"])
        if abs(total - ch["leverage"]) > 1:
            raise SystemExit(f"{h['ticker']} {ch['to']}: line effects {total:,.0f} != leverage {ch['leverage']:,.0f}")
        whole = -sum(r["actual"] for r in ch["lines"])
        if abs(whole - (ch["pretax_change"] - ch["revenue_change"])) > 1:
            raise SystemExit(f"{h['ticker']} {ch['to']}: line changes {whole:,.0f} != pre-tax less revenue change")
    scale = max(abs(shown(ch, r)) for ch in changes for r in ch["lines"])
    heads = "".join(f"<th>{year(ch['from'])} to {year(ch['to'])}</th>" for ch in changes)

    def plain(label, key, cls="", split=False):
        return (f'<tr class="{cls}"><th scope="row">{label}</th>'
                + "".join("<td></td>" if split and ch["loss_base"] else f"<td>{m(ch[key])}</td>" for ch in changes)
                + "</tr>")
    top = (plain("Revenue change", "revenue_change")
           + plain("Pre-tax income change", "pretax_change", "strong")
           + plain("&nbsp;&nbsp;if every cost moved in step with revenue", "pretax_flex", split=True)
           + plain("&nbsp;&nbsp;beyond revenue (sum of lines below)", "leverage", split=True))
    from_loss = [ch for ch in changes if ch["loss_base"]]
    loss_note = ("" if not from_loss else
                 '\n<p class="note">'
                 + ("The column" if len(from_loss) == 1 else "The columns")
                 + " starting from a loss year ("
                 + ", ".join(f"{year(ch['from'])} to {year(ch['to'])}" for ch in from_loss)
                 + ") show each line's whole change, and leave the split in step with revenue blank: scaling a "
                 "loss by revenue does not mean anything.</p>")
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
                           rows="\n".join(rows), years=years, filings=filings, cik=f"{int(h['cik']):010d}",
                           disagreements=disagreements, footing=footing(h) + retags(h) + summed(h) + pretax_line(h), loss_note=loss_note,
                           ratio_rows=ratio_rows, first=year(h["period_ends"][0]),
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
        # "Earlier", not "first": for a year before XBRL, the earliest value in the SEC's data is a later 10-K's.
        a, b = m(d["value"], False), m(d["other_value"], False)
        pct = (d["value"] - d["other_value"]) / abs(d["other_value"]) * 100
        if a == b:  # a recast smaller than the page's rounding: show millions so the two figures differ
            a, b = f"${d['value'] / 1e6:,.0f}M", f"${d['other_value'] / 1e6:,.0f}M"
        notes.append((e, f"{escape(item[0].upper() + item[1:])} {a} as later recast; earlier reported as {b} "
                         f"({pct:+.{2 if abs(pct) < 0.05 else 1}f}%) in the 10-K filed {d['other_filed']}."))
    items = "".join(f"<li><b>{year(e)}</b>: {text}</li>" for e, text in sorted(notes, key=lambda n: n[0]))
    if not items:
        return ""
    return ('<h2>Note 1 - Recast Figures</h2>\n'
            f'<ul class="breaks">{items}</ul>\n'
            '<p class="note">A later 10-K changed these figures. The table and the chart\'s lines above '
            'already use the later figures; nothing here needs to be added back.</p>\n')


def hand_note(t):
    """One line under the long table for each year read by hand from a 10-K (headline.py hand_years): which
    10-K, and the years of it that match the SEC's data. Empty when every year comes from that data."""
    out = ""
    for e, r in sorted(t.get("hand_years", {}).items()):
        url = (f"https://www.sec.gov/Archives/edgar/data/{t['cik']}/{r['accession'].replace('-', '')}/"
               f"{r['document']}")
        first = year(min(x for x in t["period_ends"] if x not in t["hand_years"]))
        match = " and ".join(year(x) for x in r["matches_xbrl"])
        out += (f'<p class="note">{year(e)} is read from the income statement in the <a href="{escape(url)}">10-K '
                f'filed {r["filed"]}</a> (accession {escape(r["accession"])}). The SEC\'s machine-readable (XBRL) '
                f'data for this company starts with {first}, and that 10-K\'s {match} figures match it exactly.</p>\n')
    return out


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
            if c["prior"] <= 0:  # no percent change on a base at or below zero
                cells.append("<td></td>")
                continue
            r = round((c["value"] - c["prior"]) / abs(c["prior"]) * 100, 1)
            pct = f"{r:+.1f}%"
            cls = ' class="up"' if r > 0 else ' class="down"' if r < 0 else ""
            if c["basis_changed"]:
                star_note(label, s, e, c, pct)
                cells.append(f'<td{cls}>{pct}*</td>')
            else:
                cells.append(f"<td{cls}>{pct}</td>")
        return cells
    lines = [(label, s, t["changes"][key]) for label, s, key in
             (("Revenue", rev, "revenue"), ("Operating income", op, "operating_income"),
              ("Pre-tax income", pre, "pretax_income")) if s is not None]
    # Years run down the rows, so the table keeps its width however long the window is.
    cols = [([f'<td class="strong">{m(s[e], False)}</td>' for e in ends], growth(label, s, ch))
            for label, s, ch in lines]
    rec = recession_years(ends)
    breaks = chart_breaks(t)  # the chart's numbered markers, numbered the same way (trend_chart)
    num = {e: n for n, e in enumerate((e for e in ends if e in breaks), 1)}
    rows = "\n".join(f'<tr{" class=\"rec\"" if e in rec else ""}><th scope="row">{year(e)}'
                     + (f'<span class="num">{num[e]}</span>' if e in num else "") + '</th>'
                     + "".join(v[i] + c[i] for v, c in cols)
                     + f"<td>{pre[e] / rev[e] * 100:.1f}%</td></tr>" for i, e in enumerate(ends))
    head = "".join(f'<th>{label}</th><th class="dim">change</th>' for label, _, _ in lines)
    return (f'<h2>{year(ends[0])} to {year(ends[-1])}</h2>\n' + start_note(ends)
            + '<div class="wrap"><table class="ten long">\n'
            f'<thead><tr><th></th>{head}<th>Pre-tax margin</th></tr></thead>\n<tbody>\n{rows}\n</tbody></table></div>\n'
            + ('<p class="note">* See Note 1.</p>\n' if notes else "")
            + (f'<p class="note">Shaded: fiscal years holding a quarter or more of a US recession as the NBER dates it '
               f'({recession_span(ends)}).</p>\n' if rec else "")
            + hand_note(t)
            + trend_chart(t) + '\n')


def built_line(built, universe):
    """One sentence on the All page naming what is built: every one-year bridge in docs/bridge/ (its company and
    years read from data/bridge.json, which must be that company's) and every company page, each linked."""
    cik = {c["ticker"]: c["cik"] for c in universe["companies"]}
    parts = []
    for path in sorted((OUT / "bridge").glob("*.html")):
        ticker = path.stem
        b = json.loads((ROOT / "data" / "bridge.json").read_text(encoding="utf-8"))
        if b["filing"]["cik"] != cik.get(ticker):
            raise SystemExit(f"docs/bridge/{ticker}.html exists but data/bridge.json is for CIK {b['filing']['cik']}")
        years = [re.fullmatch(r"FY(\d{4}) operating income", b[k]["label"]) for k in ("start", "end")]
        if not all(years):
            raise SystemExit(f"bridge.json start/end labels not of the form 'FYxxxx operating income'")
        parts.append(f'{escape(display_name(b["filing"]["company"]))}\'s <a href="bridge/{escape(ticker)}.html">one-year '
                     f'bridge</a>, which walks operating income from fiscal {years[0].group(1)} to '
                     f'{years[1].group(1)} in the 10-K\'s own words')
    tickers = [f'<a href="{escape(t)}.html">{escape(t)}</a>' for t in sorted(built)]
    if tickers:
        parts.append("company pages for " + (", ".join(tickers[:-1]) + " and " + tickers[-1] if len(tickers) > 1
                                              else tickers[0]))
    if not parts:
        return ""
    return f'<p class="lede">Built so far: {", and ".join(parts)}.</p>'


def bridge_link(ticker):
    """Link to the company's one-year bridge, only if build_bridge has written one (run it first)."""
    if not (OUT / "bridge" / f"{ticker}.html").is_file():
        return ""
    return (f'<p class="crossref"><a href="bridge/{escape(ticker)}.html">One-year bridge</a>: the latest year\'s '
            f'operating income, bar by bar, with management\'s explanations quoted from the 10-K.</p>')


# Why a company's filings cannot be read yet, in a reader's words, by census class (census.py).
NOT_READABLE = {
    "Not found": "Its two 10-Ks two years apart could not be found on SEC EDGAR.",
    "Filing layout": "Its 10-K's XBRL files are not laid out in a way the reader handles.",
    "Statement": "Its income statement could not be told apart from its other statements.",
    "Anchor": "Pre-tax income could not be found in its income statement's arithmetic.",
    "Revenue": "Its revenue is not tagged as a single line in the income statement's arithmetic.",
    "Footing": "Its income statement lines do not add up to its reported pre-tax income.",
    "Member slice": "A line is reported in parts in one 10-K and as a single total in the other.",
    "Values": "Its 10-K reports the same figure twice with values that do not agree.",
    "Structure": "Its two 10-Ks do not line up into five years.",
}


def status(t, census):
    """A company without a page: readable (passes every check) or why not."""
    r = census.get(t)
    if r is None:
        return "Not yet checked."
    if r["status"] == "pass":
        return "Readable: its filings pass every check; page not built yet."
    why = NOT_READABLE.get(r.get("class"), "The reader stopped on an error in its filings.")
    return "Not readable: " + why[0].lower() + why[1:]


def index_row(c, h, census):
    """One S&P 500 company: ticker and name; analyzed ones link to their page and carry headline numbers, the rest
    say whether their filings can be read."""
    if h is None:
        return (f'<tr class="pending"><th scope="row">{escape(c["ticker"])}</th>'
                f'<td class="name">{escape(display_name(c["name"]))}</td>'
                f'<td colspan="5" class="why">{escape(status(c["ticker"], census))}</td></tr>')
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


def index_body(universe, built, census):
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
            rows = "\n".join(index_row(c, built.get(c["ticker"]), census) for c in cs)
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
    census = json.loads((ROOT / "data" / "census.json").read_text(encoding="utf-8"))
    rest = [c["ticker"] for c in universe["companies"] if c["ticker"] not in built]
    readable = sum(census.get(t, {}).get("status") == "pass" for t in rest)
    (OUT / "index.html").write_text(INDEX.format(body=index_body(universe, built, census),
                                                 built_line=built_line(built, universe),
                                                 total=len(universe["companies"]),
                                                 analyzed=len(built), readable=readable,
                                                 unreadable=len(rest) - readable, source=escape(universe["source"]),
                                                 retrieved=escape(universe["retrieved"]), nav=nav("index.html"), css=CSS),
                                    encoding="utf-8")
    (OUT / "decisions.html").write_text(decisions_page(), encoding="utf-8")
    (OUT / "readme.html").write_text(readme_page(), encoding="utf-8")
    (OUT / "waterfall.html").write_text(waterfall_page(), encoding="utf-8")
    (OUT / "considerations.html").write_text(considerations_page(), encoding="utf-8")
    print(f"docs/: {len(companies)} company pages, index.html, readme.html, waterfall.html, decisions.html and considerations.html "
          f"({len(universe['companies'])} S&P 500 companies listed)")


CSS = header.CSS + """
:root { --s1: #2a78d6; --s2: #eb6834; --up-text: #17703d; --down-text: #b42828; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --s1: #3987e5; --s2: #d95926;
  --up-text: #3fb36b; --down-text: #e05252; } }
:root[data-theme="dark"] { --s1: #3987e5; --s2: #d95926; --up-text: #3fb36b; --down-text: #e05252; }
h1 { font-size: 1.5rem; line-height: 1.25; margin: 0 0 .5rem; }
h2 { font-size: 1.05rem; margin: 2rem 0 .5rem; }
.lede { color: var(--ink-2); max-width: 46rem; margin: 0 0 1.25rem; }
.wrap { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font-variant-numeric: tabular-nums; font-size: .9rem; }
th, td { padding: .4rem .6rem; border-bottom: 1px solid var(--rule); text-align: right; white-space: nowrap; }
thead th { font-weight: 600; color: var(--ink-3); font-size: .8rem; }
tbody th { text-align: left; font-weight: normal; white-space: normal; min-width: 12rem; }
table.ten tbody th { min-width: 9rem; } /* ten columns of figures must fit the page width */
table.ten th, table.ten td { padding: .4rem .5rem; }
table.long tbody th { min-width: 0; } /* years down the rows: the row label is just the year */
tr.strong th, tr.strong td, td.strong { font-weight: 600; }
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
.trend .rec { fill: var(--ink-3); fill-opacity: .14; }
.rec-sw { background: var(--ink-3); opacity: .3; }
tr.rec th, tr.rec td { background: color-mix(in srgb, var(--ink-3) 10%, transparent); }
.trend .guide { stroke: var(--ink-3); stroke-dasharray: 2 3; stroke-width: 1; }
.trend .mark { fill: var(--ink); }
.trend .marknum { fill: var(--bg); font-size: 11px; font-weight: 700; }
ol.key { list-style: none; padding: 0; margin: .5rem 0 1rem; font-size: .85rem; color: var(--ink-2); max-width: 46rem; }
ol.key li { margin: 0 0 .3rem; }
ol.key .num, table.long .num { display: inline-block; width: 1.3rem; height: 1.3rem; line-height: 1.3rem; border-radius: 50%;
  background: var(--ink); color: var(--bg); text-align: center; font-size: .75rem; font-weight: 700;
  margin-right: .5rem; }
table.long .num { width: 1.15rem; height: 1.15rem; line-height: 1.15rem; font-size: .7rem; margin: 0 0 0 .4rem; }
tr.sub th { text-align: left; font-size: .8rem; font-weight: 600; color: var(--ink-3); padding-top: .9rem; }
td.name { text-align: left; white-space: normal; }
table.index tbody th { min-width: 4rem; width: 4rem; }
table.index td.name { width: 16rem; }
tr.pending th, tr.pending td { color: var(--ink-3); }
td.why { text-align: left; white-space: normal; }
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
"""

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
</tbody></table></div>{loss_note}
</details>

{ten_breaks}
<footer>
<p>Source: {filings}. Lines, labels and order come from each filing's income statement; {footing} {disagreements}</p>
<p>The table and chart at the top come from the SEC's companyfacts data and each year's 10-K; every 10-K is in the
company's <a href="https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&amp;CIK={cik}&amp;type=10-K">SEC filing
list</a>.</p>
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
Linked tickers open five years of cost lines from the company's own 10-K filings. Of the rest, {readable} have
filings that pass every check and {unreadable} cannot be read yet; each row says which, and why.</p>
{built_line}
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


WATERFALL = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Waterfall - Chomper</title>
<style>{css}
table.fall th, table.fall td {{ white-space: normal; vertical-align: top; }}
table.fall tbody th {{ min-width: 14rem; }}
table.fall td.text {{ text-align: left; }}
table.fall td.text p {{ margin: .3rem 0 0; font-size: .85rem; color: var(--ink-2); max-width: 46rem; }}
table.fall .bar {{ height: .5rem; background: var(--rule); border-radius: 2px; max-width: 46rem; }}
table.fall .bar i {{ display: block; height: 100%; background: var(--up); border-radius: 2px; }}
</style>
</head>
<body>
<main>
{nav}
<h1>Waterfall</h1>
<p class="lede">Where every count on this site comes from: the population at the top of each path, and what falls
out at each step, with the cause. Companies, not tickers, unless the row says tickers.</p>
{sections}
<footer>
<p>Source: data/waterfall.json, written by waterfall.py from the membership file, today's list, the five-year
census, the bulk ten-year run, the published pages and the S&amp;P 500 page's data. Rerun it after any of
those change, then rebuild.</p>
</footer>
</main>
</body>
</html>
"""


README = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Readme - Chomper</title>
<style>{css}
.readme p, .readme li {{ max-width: 46rem; }}
.readme li {{ margin-bottom: .4rem; }}
.readme figure {{ margin: 1.5rem 0; }}
.readme img {{ max-width: 100%; height: auto; border: 1px solid var(--rule); }}
.readme figcaption {{ font-size: .85rem; color: var(--ink-2); margin-top: .4rem; }}
.readme pre {{ background: var(--rule); padding: .6rem .8rem; border-radius: 4px; font-size: .9rem; overflow-x: auto; }}
.readme code {{ font-size: .9em; }}
</style>
</head>
<body>
<main class="readme">
{nav}
{body}
<footer>
<p>Source: README.md in the repository, rendered as this page by the build.</p>
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
