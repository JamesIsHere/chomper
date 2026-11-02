"""Trial: four ways to tie the ten-year breaks to the ten-year chart, side by side on one page.

Not part of the site build. Writes docs/trials/<TICKER>-breaks.html for James to compare; the chosen parts go
into build_history.py and this file is archived.

  1. Numbered markers on the chart, with a key under it
  2. Shaded year bands behind the lines
  3. Labels on the chart, with lines to the year they explain
  4. Swim lanes under the chart, one per kind of break, sized by magnitude

Acquisitions and accounting standards are drawn in all four. Recasts are drawn only in the swim lanes: the
chart chains same-basis growth, so a recast makes no spike in its lines (the table's asterisks carry them).

Usage: python trial_breaks.py TICKER
"""
import sys
from html import escape

from build_history import CSS, OUT, axis, headline, m, multiples, times, year
from header import nav

W, L, R = 640, 40, 170
PLOT_H = 180  # height of the lines' plot area


def short(name):
    """A label short enough for a chart: the first party of the deal, two words, lowercase words capitalized."""
    first = name.split(" and ")[0].split(",")[0]
    return " ".join(w[:1].upper() + w[1:] if w.islower() else w for w in first.split()[:2])


def breaks(t):
    """{end: [(kind, label, detail, share)]} for each year with a break; share is the deal's share of assets."""
    out = {}
    for d in t["deals"]:
        if d["significant"]:
            out.setdefault(d["fiscal_year_end"], []).append(
                ("acquisition", short(d["name"]), f"Acquired {d['name']}, {m(d['size'], False)}, "
                 f"{d['share_of_assets']:.0%} of total assets at the prior year end", d["share_of_assets"]))
    for s in t["standards"]:
        code = s["standard"].split(" (")[0]
        out.setdefault(s["fiscal_year_end"], []).append(
            ("standard", code, f"{s['standard']} required this year (the company may have adopted earlier)", None))
    return out


def recasts(t):
    """{end: [(item, pct)]}: the figure as later recast against the figure as first reported."""
    first = {}
    for d in t["disagreements"]:
        k = (d["period_end"], d["item"])
        if k not in first or d["other_filed"] < first[k]["other_filed"]:
            first[k] = d
    out = {}
    for (e, item), d in sorted(first.items()):
        out.setdefault(e, []).append((item, (d["value"] - d["other_value"]) / abs(d["other_value"]) * 100))
    return out


def chart(t, top=12, bottom=26, under="", over="", extra_h=0):
    """The ten-year chart (revenue and pre-tax income as multiples of the first year, chained same-basis growth)
    with room above (top) and below (extra_h) for overlays. under: SVG drawn behind the lines; over: drawn on
    top. Returns the svg."""
    ends = t["period_ends"]
    names = [("Revenue", "--s1"), ("Pre-tax income", "--s2")]
    idx = multiples(t)
    ticks, lo, hi = axis([v for vs in idx.values() for v in vs])
    y0, y1 = top, top + PLOT_H
    px = lambda i: L + i * (W - L - R) / (len(ends) - 1)
    py = lambda v: y0 + (hi - v) / (hi - lo) * (y1 - y0)
    H = y1 + bottom + extra_h
    grid = "".join(f'<line x1="{L}" x2="{W - R}" y1="{py(v):.1f}" y2="{py(v):.1f}" class="g"/>'
                   f'<text x="{L - 6}" y="{py(v) + 4:.1f}" class="ax" text-anchor="end">{times(v)}</text>'
                   for v in ticks)
    xs = "".join(f'<text x="{px(i):.1f}" y="{y1 + 18}" class="ax" text-anchor="middle">{year(e)}</text>'
                 for i, e in enumerate(ends))
    lines = []
    for name, var in names:
        pts = " ".join(f"{px(i):.1f},{py(v):.1f}" for i, v in enumerate(idx[name]))
        lines.append(f'<polyline points="{pts}" fill="none" style="stroke:var({var})" stroke-width="2"/>')
        lines += [f'<circle cx="{px(i):.1f}" cy="{py(v):.1f}" r="4" style="fill:var({var})" class="dot"/>'
                  for i, v in enumerate(idx[name])]
        lines.append(f'<text x="{px(len(ends) - 1) + 10:.1f}" y="{py(idx[name][-1]) + 4:.1f}" class="lab">'
                     f'{name} {times(idx[name][-1])}</text>')
    u = under(px, py, y0, y1) if callable(under) else under
    o = over(px, py, y0, y1, idx) if callable(over) else over
    svg = (f'<svg class="trend" viewBox="0 0 {W} {H}" role="img" aria-label="Revenue and pre-tax income with '
           f'breaks">{u}{grid}{xs}{"".join(lines)}{o}</svg>')
    return svg


LEGEND = ('<p class="legend"><span><i style="background:var(--s1)"></i>Revenue</span><span><i style="background:'
          'var(--s2)"></i>Pre-tax income</span><span class="dim">Times {first}: 1x = the {first} figure; '
          'growth on one accounting basis</span></p>')


def option1(t, b):
    """Numbered markers at the top of the plot, one per year with a break; the key lists every item."""
    ends = t["period_ends"]
    years = [e for e in ends if e in b]

    def over(px, py, y0, y1, idx):
        out = []
        for n, e in enumerate(years, 1):
            x = px(ends.index(e))
            out.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{y0 - 2}" y2="{y1}" class="guide"/>'
                       f'<circle cx="{x:.1f}" cy="{y0 - 10}" r="9" class="mark"/>'
                       f'<text x="{x:.1f}" y="{y0 - 6}" class="marknum" text-anchor="middle">{n}</text>')
        return "".join(out)
    svg = chart(t, top=26, over=over)
    key = "".join(f'<li><span class="num">{n}</span><b>{year(e)}</b>: '
                  + "; ".join(escape(d) for _, _, d, _ in b[e]) + "</li>" for n, e in enumerate(years, 1))
    return svg + f'<ol class="key">{key}</ol>'


def option2(t, b):
    """A shaded band behind each break year: darker for a larger acquisition, light grey for a standard."""
    ends = t["period_ends"]

    def under(px, py, y0, y1):
        half = (px(1) - px(0)) / 2
        out = []
        for e, items in b.items():
            x = px(ends.index(e))
            deals = [s for k, _, _, s in items if k == "acquisition"]
            if deals:
                share = sum(deals)
                out.append(f'<rect x="{x - half:.1f}" y="{y0}" width="{2 * half:.1f}" height="{y1 - y0}" '
                           f'class="band-acq" style="fill-opacity:{min(.12 + share, .55):.2f}"/>'
                           f'<text x="{x:.1f}" y="{y0 - 4}" class="bandlab" text-anchor="middle">'
                           f'{share:.0%}</text>')
            else:
                out.append(f'<rect x="{x - half:.1f}" y="{y0}" width="{2 * half:.1f}" height="{y1 - y0}" '
                           f'class="band-std"/>')
            codes = " ".join(lab for k, lab, _, _ in items if k == "standard")
            if codes:  # above the band, above the acquisition's percentage when the year has both
                out.append(f'<text x="{x:.1f}" y="{y0 - 4 - (14 if deals else 0)}" class="bandlab" '
                           f'text-anchor="middle">{codes}</text>')
        return "".join(out)
    svg = chart(t, top=32, under=under)
    legend = ('<p class="legend"><span><i class="sw band-acq-sw"></i>Acquisition year (darker = larger share of '
              'assets, % above)</span><span><i class="sw band-std-sw"></i>Accounting standard required</span></p>')
    return svg + legend


def option3(t, b):
    """Each break labeled on the chart, with a line from the label down to the revenue point of its year."""
    ends = t["period_ends"]
    rows = 3

    def over(px, py, y0, y1, idx):
        out, n = [], 0
        for e in ends:
            for kind, lab, _, share in b.get(e, []):
                i = ends.index(e)
                x, yp = px(i), py(idx["Revenue"][i])
                ly = 14 + (n % rows) * 16
                text = f"{lab} {share:.0%}" if kind == "acquisition" else f"{lab} required"
                cls = "lab-acq" if kind == "acquisition" else "lab-std"
                out.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{ly + 3}" y2="{yp - 5:.1f}" class="leader"/>'
                           f'<text x="{x + 3:.1f}" y="{ly}" class="{cls}">{escape(text)}</text>')
                n += 1
        return "".join(out)
    return chart(t, top=14 + rows * 16 + 6, over=over)


def option4(t, b, rc):
    """Three lanes under the chart on the same years: acquisitions (circle area = share of assets), recasts
    (the larger change that year, in percent), standards (a tick)."""
    ends = t["period_ends"]
    lane, gap = 30, 10
    lanes = ["Acquisitions", "Recasts", "Standards"]

    def under(px, py, y0, y1):
        top = y1 + 26 + gap
        out = []
        for j, name in enumerate(lanes):
            y = top + j * lane + lane / 2
            out.append(f'<line x1="{L}" x2="{W - R}" y1="{y:.1f}" y2="{y:.1f}" class="lane"/>'
                       f'<text x="{W - R + 10}" y="{y + 4:.1f}" class="lab">{name}</text>')
        for e in ends:
            x = px(ends.index(e))
            for kind, lab, _, share in b.get(e, []):
                if kind == "acquisition":
                    y = top + lane / 2
                    r = 3 + 22 * share ** .5
                    out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{min(r, 14):.1f}" class="lane-acq"/>'
                               f'<text x="{x:.1f}" y="{y + 4:.1f}" class="lanenum" text-anchor="middle">'
                               f'{share:.0%}</text>')
                else:
                    y = top + 2 * lane + lane / 2
                    out.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{y - 8:.1f}" y2="{y + 8:.1f}" class="tick"/>'
                               f'<text x="{x + 4:.1f}" y="{y - 6:.1f}" class="ax">{lab}</text>')
            if e in rc:
                y = top + lane + lane / 2
                item, pct = max(rc[e], key=lambda r: abs(r[1]))
                out.append(f'<rect x="{x - 4:.1f}" y="{y - 4:.1f}" width="8" height="8" class="lane-rc"/>'
                           f'<text x="{x + 7:.1f}" y="{y + 4:.1f}" class="ax">{pct:+.0f}%</text>')
        return "".join(out)
    svg = chart(t, under=under, extra_h=gap + 3 * lane)
    names = {e: ", ".join(lab for k, lab, _, _ in b.get(e, []) if k == "acquisition") for e in ends}
    deals = "; ".join(f"{year(e)} {escape(n)}" for e, n in names.items() if n)
    return svg + f'<p class="note">Acquisitions: {deals}. Recasts show the largest change to a line that year.</p>'


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: python trial_breaks.py TICKER")
    ticker = sys.argv[1].upper()
    t = headline(ticker)
    b, rc = breaks(t), recasts(t)
    legend = LEGEND.format(first=year(t["period_ends"][0]))
    parts = [("1. Numbered markers, with a key", option1(t, b)),
             ("2. Shaded year bands", option2(t, b)),
             ("3. Labels on the chart, with lines to the year", option3(t, b)),
             ("4. Swim lanes under the chart", option4(t, b, rc))]
    body = "".join(f'<section class="trial" id="o{n}"><h2>{h}</h2>{legend}{svg}</section>'
                   for n, (h, svg) in enumerate(parts, 1))
    css = CSS + TRIAL_CSS
    html = (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" '
            f'content="width=device-width, initial-scale=1"><title>{ticker} breaks trial - Chomper</title>'
            f'<style>{css}</style></head><body><main>{nav(prefix="../")}<h1>{escape(t["company"])}: four ways to '
            f'show the breaks</h1><p class="lede">Trial page, not linked from the site. The same ten-year chart '
            f'four times; each version ties the acquisitions and accounting standards to the years they '
            f'affect.</p>{body}</main></body></html>')
    out = OUT / "trials" / f"{ticker}-breaks.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"{out.relative_to(OUT.parent)}: {sum(len(v) for v in b.values())} breaks in {len(b)} years, "
          f"recasts in {len(rc)} years")


TRIAL_CSS = """
.trial { border-top: 1px solid var(--rule); padding-top: .5rem; margin-top: 2rem; }
.trend .guide { stroke: var(--ink-3); stroke-dasharray: 2 3; stroke-width: 1; }
.trend .mark { fill: var(--ink); }
.trend .marknum { fill: var(--bg); font-size: 11px; font-weight: 700; }
ol.key { list-style: none; padding: 0; margin: .5rem 0 0; font-size: .85rem; color: var(--ink-2); max-width: 46rem; }
ol.key li { margin: 0 0 .3rem; }
ol.key .num { display: inline-block; width: 1.3rem; height: 1.3rem; line-height: 1.3rem; border-radius: 50%;
  background: var(--ink); color: var(--bg); text-align: center; font-size: .75rem; font-weight: 700;
  margin-right: .5rem; }
.trend .band-acq { fill: var(--ink); }
.trend .band-std { fill: var(--ink-3); fill-opacity: .1; }
.trend .bandlab { fill: var(--ink-2); font-size: 11px; font-weight: 600; }
.legend .sw { width: .8rem; height: .8rem; }
.band-acq-sw { background: var(--ink); opacity: .4; }
.band-std-sw { background: var(--ink-3); opacity: .25; }
.trend .leader { stroke: var(--ink-3); stroke-width: 1; }
.trend .lab-acq { fill: var(--ink); font-size: 11px; font-weight: 600; }
.trend .lab-std { fill: var(--ink-3); font-size: 11px; }
.trend .lane { stroke: var(--rule); stroke-width: 1; }
.trend .lane-acq { fill: var(--ink); fill-opacity: .8; }
.trend .lanenum { fill: var(--bg); font-size: 9px; font-weight: 700; }
.trend .lane-rc { fill: none; stroke: var(--ink-2); stroke-width: 1.5; }
.trend .tick { stroke: var(--ink-2); stroke-width: 2; }
"""


if __name__ == "__main__":
    main()
