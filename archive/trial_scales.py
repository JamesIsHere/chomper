"""Trial: the ten-year chart in dollars on a log scale, with bars for each year's cost gap, two ways.

Not part of the site build. Writes docs/trials/scales.html: for each company named, the log chart with the bars
in their own band under the lines, then the same chart with the bars behind the lines on a second axis.

The bar for a year is the pre-tax income the company would have earned at the prior year's pre-tax margin,
minus what it earned: revenue x prior margin - pre-tax income. Above zero (red), costs ran ahead of revenue that
year; below zero (green), revenue ran ahead of costs. Dollars are the table's figures.

Usage: python trial_scales.py TICKER [TICKER ...]
"""
import math
import sys
from html import escape

from build_history import CSS, OUT, headline, m, year
from header import nav

W, L, R = 800, 60, 210
PLOT_H, T, X_H = 280, 12, 26  # line plot height, top margin, room for the year labels
BAND_H, BAND_GAP = 110, 18    # bar band height and its gap below the year labels (option 1)


def money(v):
    """A tick label: $0, $500M, $2B, -$1B."""
    if v == 0:
        return "$0"
    s = f"${abs(v) / 1e9:g}B" if abs(v) >= 1e9 else f"${abs(v) / 1e6:g}M"
    return ("-" if v < 0 else "") + s


def log_ticks(lo, hi):
    """1-2-5 ticks covering the values, widened to the tick just below and just above."""
    all_ticks = [k * 10 ** p for p in range(6, 14) for k in (1, 2, 5)]
    return [v for v in all_ticks if max(t for t in all_ticks if t <= lo) <= v <= min(t for t in all_ticks if t >= hi)]


def bar_ticks(values):
    """Round ticks through zero covering every bar, at most five intervals."""
    lo, hi = min(min(values), 0), max(max(values), 0)
    step = next(k * 10 ** p for p in range(5, 14) for k in (1, 2, 5) if (hi - lo) / (k * 10 ** p) <= 5)
    return [k * step for k in range(math.floor(lo / step), math.ceil(hi / step) + 1)]


def gaps(t):
    """{end: dollars} for each year after the first: revenue x prior-year pre-tax margin - pre-tax income."""
    ends, rev, pre = t["period_ends"], t["revenue"], t["pretax_income"]
    return {e: rev[e] * pre[p] / rev[p] - pre[e] for p, e in zip(ends, ends[1:])}


def chart(t, mode):
    """mode "band": bars in their own band under the lines; "overlay": bars behind the lines, second axis."""
    ends, rev, pre = t["period_ends"], t["revenue"], t["pretax_income"]
    series = [("Revenue", "--s1", rev), ("Pre-tax income", "--s2", pre)]
    vals = [s[e] for _, _, s in series for e in ends]
    if min(vals) <= 0:
        raise SystemExit(f"{t['ticker']}: a year is zero or negative, so it cannot go on a log scale")
    g = gaps(t)
    ticks = log_ticks(min(vals), max(vals))
    lo, hi = math.log10(ticks[0]), math.log10(ticks[-1])
    step_x = (W - L - R) / len(ends)  # one slot per year, so every bar sits inside the plot
    px = lambda i: L + (i + 0.5) * step_x
    py = lambda v: T + (hi - math.log10(v)) / (hi - lo) * PLOT_H
    y_axis = T + PLOT_H + X_H

    bt = bar_ticks(list(g.values()))
    if mode == "band":
        b0, b1 = y_axis + BAND_GAP, y_axis + BAND_GAP + BAND_H
        H = b1 + 8
    else:
        b0, b1 = T, T + PLOT_H
        H = y_axis
    by = lambda v: b0 + (bt[-1] - v) / (bt[-1] - bt[0]) * (b1 - b0)

    out = []
    if mode == "overlay":  # bars first, behind everything
        out += [f'<text x="{W - R + 8}" y="{by(v) + 4:.1f}" class="ax">{money(v)}</text>' for v in bt]
    out += [f'<line x1="{L}" x2="{W - R}" y1="{py(v):.1f}" y2="{py(v):.1f}" class="g"/>'
            f'<text x="{L - 6}" y="{py(v) + 4:.1f}" class="ax" text-anchor="end">{money(v)}</text>' for v in ticks]
    bar_w = step_x * 0.5
    for i, e in enumerate(ends[1:], 1):
        v = g[e]
        y_top, y_bot = sorted((by(v), by(0)))
        cls = "bar-down" if v > 0 else "bar-up"
        tip = (f"{year(e)}: at {year(ends[i - 1])}'s pre-tax margin, pre-tax income would have been "
               f"{m(rev[e] * pre[ends[i - 1]] / rev[ends[i - 1]], False)}; it was {m(pre[e], False)}")
        out.append(f'<rect x="{px(i) - bar_w / 2:.1f}" y="{y_top:.1f}" width="{bar_w:.1f}" '
                   f'height="{max(y_bot - y_top, 0.5):.1f}" class="{cls}"><title>{escape(tip)}</title></rect>')
    out.append(f'<line x1="{L}" x2="{W - R}" y1="{by(0):.1f}" y2="{by(0):.1f}" class="zero"/>')
    if mode == "band":
        out += [f'<text x="{L - 6}" y="{by(v) + 4:.1f}" class="ax" text-anchor="end">{money(v)}</text>'
                for v in bt]
    out += [f'<text x="{px(i):.1f}" y="{T + PLOT_H + 18}" class="ax" text-anchor="middle">{year(e)}</text>'
            for i, e in enumerate(ends)]
    label_y = []
    for name, var, s in series:
        pts = " ".join(f"{px(i):.1f},{py(s[e]):.1f}" for i, e in enumerate(ends))
        out.append(f'<polyline points="{pts}" fill="none" style="stroke:var({var})" stroke-width="2"/>')
        out += [f'<circle cx="{px(i):.1f}" cy="{py(s[e]):.1f}" r="4" style="fill:var({var})" class="dot"/>'
                for i, e in enumerate(ends)]
        label_y.append(py(s[ends[-1]]))
    a, b = label_y
    if abs(a - b) < 14:
        mid = (a + b) / 2
        a, b = (mid - 7, mid + 7) if a <= b else (mid + 7, mid - 7)
    lab_x = W - R + (62 if mode == "overlay" else 10)
    out += [f'<text x="{lab_x}" y="{y + 4:.1f}" class="lab">{name} {m(s[ends[-1]], False)}</text>'
            for (name, _, s), y in zip(series, (a, b))]
    return (f'<svg class="trend wide" viewBox="0 0 {W} {H}" role="img" aria-label="Revenue and pre-tax income in '
            f'dollars on a log scale, with each year\'s cost gap as bars">{"".join(out)}</svg>')


LEGEND = ('<p class="legend"><span><i style="background:var(--s1)"></i>Revenue</span><span><i style="background:'
          'var(--s2)"></i>Pre-tax income</span><span><i class="sw bar-down-sw"></i>Costs ran ahead of revenue'
          '</span><span><i class="sw bar-up-sw"></i>Revenue ran ahead of costs</span></p>')


def main():
    if len(sys.argv) < 2:
        raise SystemExit("usage: python trial_scales.py TICKER [TICKER ...]")
    body = []
    for ticker in (a.upper() for a in sys.argv[1:]):
        t = headline(ticker)
        body.append(f'<h1>{escape(t["company"])}</h1>'
                    f'<section class="trial">{LEGEND}{chart(t, "band")}</section>')
    note = ('<p class="dim">Lines: dollars on a log scale, so equal distances up the axis are equal percentage '
            'changes. Bars: the pre-tax income the company would have earned at the prior year\'s pre-tax margin, '
            'minus what it earned. A bar above zero means costs grew faster than revenue that year, by that many '
            'dollars.</p>')
    css = CSS + """
.trial { border-top: 1px solid var(--rule); padding-top: .5rem; margin-top: 1.5rem; }
.trend.wide { max-width: 50rem; }
.trend .zero { stroke: var(--ink-3); stroke-width: 1; }
.trend .bar-down { fill: var(--down); fill-opacity: .55; }
.trend .bar-up { fill: var(--up); fill-opacity: .55; }
.legend .sw { width: .8rem; height: .8rem; }
.bar-down-sw { background: var(--down); opacity: .55; }
.bar-up-sw { background: var(--up); opacity: .55; }
"""
    html = (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" '
            f'content="width=device-width, initial-scale=1"><title>Chart scales trial - Chomper</title>'
            f'<style>{css}</style></head><body><main>{nav(prefix="../")}<p class="lede">Trial page, not linked '
            f'from the site. The ten-year chart in dollars on a log scale, with the cost gap as bars under it.</p>'
            f'{note}{"".join(body)}</main></body></html>')
    out = OUT / "trials" / "scales.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"{out.relative_to(OUT.parent)}: {len(body)} companies")


if __name__ == "__main__":
    main()
