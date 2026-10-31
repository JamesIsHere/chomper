"""Build the public page from the reviewed data. Never calls the AI.

Reads data/bridge.json, data/commentary.json (approved) and data/facts.json;
writes docs/index.html. Every number on the page is computed here from those
files; the only prose not written in this file is the approved commentary.

Usage: python build.py
"""
import json
import re
from decimal import Decimal, ROUND_HALF_UP
from html import escape
from pathlib import Path
from urllib.parse import quote as urlquote

import header
from pull import YEARS

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUT = ROOT / "docs" / "bridge" / "ODFL.html"
UP = "../" * (len(OUT.relative_to(ROOT / "docs").parts) - 1)  # header links resolve from the page's folder

AXIS_MIN, AXIS_MAX, TICK = 900_000, 1_600_000, 100_000  # USD thousands
TABLE_ROW = re.compile(r"^(.*?[A-Za-z)])\s+((?:\$\s?)?[\d,.]+\s+(?:\$\s?)?[\d,.]+(?:\s+.*)?)$")
FLAG_TEXT = {
    "not_discussed": "Not explained by management",
    "no_dollar_amount": "Management gives reasons but no dollar amount",
    "amount_mismatch": "Management's stated amount does not match the filing",
}
# Cost-behavior view: our classification, not the company's (the page says so). Statement order within a group.
GROUPS = [
    ("revenue", "Revenue", {"volume", "yield", "revenue_remainder"}),
    ("variable", "Costs that move with freight volume", {"operating_supplies", "purchased_transportation"}),
    ("mixed", "Costs that partly move with volume", {"salaries", "general_supplies", "insurance"}),
    ("fixed", "Costs that are mostly fixed", {"operating_taxes", "communications", "depreciation"}),
    ("other", "Other", {"miscellaneous"}),
]


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def m(thousands, sign=True):
    """USD thousands -> '$527.5M' with optional sign, rounded half up."""
    v = (Decimal(thousands) / 1000).quantize(Decimal("0.1"), ROUND_HALF_UP)
    s = f"${abs(v):,.1f}M"
    return (("+" if v > 0 else "-" if v < 0 else "") + s) if sign else ("-" + s if v < 0 else s)


def pct(new, old):
    return (Decimal(new - old) / Decimal(old) * 100).quantize(Decimal("0.1"), ROUND_HALF_UP)


def x(thousands):
    """Position on the bridge axis, in percent of the track width."""
    if not AXIS_MIN <= thousands <= AXIS_MAX:
        raise SystemExit(f"value {thousands} outside axis {AXIS_MIN}-{AXIS_MAX}; widen the axis")
    return float(Decimal(thousands - AXIS_MIN) / Decimal(AXIS_MAX - AXIS_MIN) * 100)


def fragment_link(doc_url, text):
    """Text-fragment link: whole text if short, else first and last five words."""
    enc = lambda s: urlquote(s, safe="").replace("-", "%2D")
    words = text.split()
    frag = enc(text) if len(words) <= 10 else enc(" ".join(words[:5])) + "," + enc(" ".join(words[-5:]))
    return f"{doc_url}#:~:text={frag}"


def table_row(q):
    """'LTL tons (in thousands) 8,177 9,000 (823 ) (9.1 )' -> (label, cells), or None for a sentence."""
    if q.rstrip().endswith((".", ":", ";")):
        return None
    row = TABLE_ROW.match(q)
    if not row:
        raise SystemExit(f"quote is neither a sentence nor a table row: {q!r}")
    label, rest = row.groups()
    return label, [c.replace(" ", "") for c in re.findall(r"\(?\$?\s?[\d,.]+\s?\)?", rest)]


def passages_html(passages, doc_url):
    """Sentences as linked quotes; consecutive table rows from one page as one small linked table."""
    out, group = [], []

    def flush():
        if not group:
            return
        width = max(len(cells) for _, _, cells in group)
        ths = "".join(f"<th>{h}</th>" for h in ["2025", "2024", "Change", "% change"][:width])
        trs = "".join(f'<tr><th scope="row"><a href="{escape(fragment_link(doc_url, label))}">{escape(label)}</a></th>'
                      + "".join(f"<td>{escape(c)}</td>" for c in cells) + "</tr>" for _, label, cells in group)
        out.append(f'<figure class="quote tablequote"><table><thead><tr><th></th>{ths}</tr></thead>'
                   f'<tbody>{trs}</tbody></table><figcaption>10-K page {group[0][0]}, operating metrics table'
                   f'</figcaption></figure>')
        group.clear()

    for p in passages:
        parsed = table_row(p["quote"])
        if parsed and (not group or group[0][0] == p["page"]):
            group.append((p["page"], *parsed))
            continue
        flush()
        if parsed:
            group.append((p["page"], *parsed))
            continue
        out.append(f'<figure class="quote"><blockquote>{escape(p["quote"])}</blockquote>'
                   f'<figcaption><a href="{escape(fragment_link(doc_url, p["quote"]))}">10-K page {p["page"]}</a>'
                   f'</figcaption></figure>')
    flush()
    return "".join(out)


def source_html(bar, facts_by_tag, filing):
    acc = escape(filing["accession"])
    src = bar["source"]
    if "tag" in src:
        f = facts_by_tag[src["tag"]]
        return (f'<dl class="source"><dt>XBRL tag</dt><dd><code>{escape(src["tag"])}</code></dd>'
                f'<dt>FY2024</dt><dd>{f["fy2024"] * 1000:,} USD ({YEARS["fy2024"][0]} to {YEARS["fy2024"][1]})</dd>'
                f'<dt>FY2025</dt><dd>{f["fy2025"] * 1000:,} USD ({YEARS["fy2025"][0]} to {YEARS["fy2025"][1]})</dd>'
                f'<dt>Calculation</dt><dd>{escape(bar["basis"])}, rounded to $0.1M</dd>'
                f'<dt>Filing</dt><dd>10-K, accession {acc}</dd></dl>')
    rows = "".join(f"<li>{escape(r)}</li>" for r in src["rows"])
    return (f'<dl class="source"><dt>Calculation</dt><dd>{escape(bar["basis"])}</dd>'
            f'<dt>Inputs</dt><dd>10-K page {src["page"]}, operating metrics table:<ul>{rows}</ul></dd>'
            f'<dt>Filing</dt><dd>10-K, accession {acc}</dd></dl>')


def total_source_html(tag, amount, year, filing):
    return (f'<dl class="source"><dt>XBRL tag</dt><dd><code>{escape(tag)}</code></dd>'
            f'<dt>{year.upper()}</dt><dd>{amount * 1000:,} USD ({YEARS[year][0]} to {YEARS[year][1]})</dd>'
            f'<dt>Filing</dt><dd>10-K, accession {escape(filing["accession"])}</dd></dl>')


def track(lo, hi, cls, prev=None, title=""):
    grid = "".join(f'<span class="grid" style="left:{x(t):.3f}%"></span>'
                   for t in range(AXIS_MIN + TICK, AXIS_MAX, TICK))
    link = f'<span class="link" style="left:{x(prev):.3f}%"></span>' if prev is not None else ""
    width = max(x(hi) - x(lo), 0.3)
    return (f'<span class="track" aria-hidden="true">{grid}{link}'
            f'<span class="bar {cls}" style="left:{x(lo):.3f}%;width:{width:.3f}%" title="{escape(title)}"></span></span>')


def layout(bars, start):
    """Running-total geometry for bars in the given order: key -> (left, width, link, title)."""
    out, running = {}, start
    for bar in bars:
        prev, running = running, running + bar["amount"]
        lo, hi = sorted((prev, running))
        out[bar["key"]] = (round(x(lo), 3), round(max(x(hi) - x(lo), 0.3), 3), round(x(prev), 3),
                           f"{m(bar['amount'])}; running total {m(running, False)}")
    return out


def views(bars, start):
    """Item order and bar geometry for each ordering the page offers."""
    keys = [b["key"] for b in bars]
    grouped = [k for _, _, ks in GROUPS for k in ks]
    if sorted(grouped) != sorted(keys):
        raise SystemExit(f"GROUPS does not cover the bridge bars exactly: {sorted(set(keys) ^ set(grouped))}")
    by_key = {b["key"]: b for b in bars}
    orders = {
        "statement": [(None, keys)],
        "behavior": [(g, [k for k in keys if k in ks]) for g, _, ks in GROUPS],
        "size": [(None, [b["key"] for b in sorted(bars, key=lambda b: -abs(b["amount"]))])],
    }
    out = {}
    for name, sections in orders.items():
        geo = layout([by_key[k] for _, ks in sections for k in ks], start)
        items = []
        for group, ks in sections:
            if group:
                items.append({"key": f"group-{group}"})
            items += [{"key": k, "bar": geo[k][:3], "title": geo[k][3]} for k in ks]
        out[name] = items
    return out


def row(label, amount_text, track_html, body, cls="", flag="", key=""):
    flag_html = f'<span class="flag">{escape(flag)}</span>' if flag else ""
    return (f'<details class="row {cls}" data-key="{escape(key)}"><summary><span class="label">{escape(label)}{flag_html}</span>'
            f'{track_html}<span class="amount">{amount_text}</span></summary>'
            f'<div class="body">{body}</div></details>')


def findings(bars, commentary, facts, bridge):
    by_key = {b["key"]: b for b in bars}
    cov = commentary["coverage"]
    silent = sorted((b for b in commentary["bars"] if b["kind"] == "expense" and "not_discussed" in b["flags"]),
                    key=lambda b: -abs(b["amount"]))
    top = silent[0]
    tf = {f["key"]: f for f in facts["lines"]}[top["key"]]
    sal = {f["key"]: f for f in facts["lines"]}["salaries"]
    tons = by_key["volume"]["source"]["rows"]
    t24, t25 = 9000, 8177
    if f"{t25:,} {t24:,}" not in tons[0]:
        raise SystemExit(f"tons changed in bridge.json; update findings: {tons[0]}")
    per24 = Decimal(sal["fy2024"]) / t24
    per25 = Decimal(sal["fy2025"]) / t25
    per_ton = lambda v: f"${v.quantize(Decimal('0.01'), ROUND_HALF_UP):,.2f}"
    rise = ((per25 / per24 - 1) * 100).quantize(Decimal("0.1"), ROUND_HALF_UP)
    items = [
        (f"Management puts a dollar figure on {cov['lines_quantified'].replace(' of ', ' of the ')} cost lines.",
         f"Those three account for {m(cov['quantified_by_mdna'], False)} of the {m(cov['expense_change'], False)} "
         f"net cost reduction ({cov['share_quantified']}%). The other {m(cov['unexplained'], False)} is not "
         f"explained in the MD&amp;A."),
        (f"The largest unexplained line is {escape(top['label'].lower())}.",
         f"It fell {m(tf['fy2024'] - tf['fy2025'], False)}, from {m(tf['fy2024'], False)} to "
         f"{m(tf['fy2025'], False)} ({pct(tf['fy2025'], tf['fy2024'])}%), with no discussion."),
        (f"Labor cost per ton of freight rose {rise}%.",
         f"Salaries, wages and benefits fell {abs(pct(sal['fy2025'], sal['fy2024']))}% while LTL tons fell "
         f"{abs(pct(t25, t24))}%, so labor cost per ton went from {per_ton(per24)} to {per_ton(per25)}. "
         f"Headcount came down, but more slowly than freight. (All salaries, wages and benefits divided by "
         f"LTL tons; this is an analyst's calculation, not a figure management reports.)"),
    ]
    return "".join(f"<li><strong>{h}</strong> {b}</li>" for h, b in items)


def main():
    bridge, commentary, facts = load("bridge.json"), load("commentary.json"), load("facts.json")
    if commentary.get("reviewed_by") is None or commentary["failures"]:
        raise SystemExit("commentary.json is not an approved, failure-free review")
    filing = bridge["filing"]
    doc_url = filing["document_url"]
    facts_by_tag = {f["tag"]: f for f in facts["lines"]}
    notes = {b["key"]: b for b in commentary["bars"]}
    if [b["key"] for b in bridge["bars"]] != [b["key"] for b in commentary["bars"]]:
        raise SystemExit("bridge.json and commentary.json bars differ; rerun verify.py and re-approve")

    start, end = bridge["start"]["amount"], bridge["end"]["amount"]
    rows, running = [], start
    rows.append(row(bridge["start"]["label"], m(start, False),
                     track(AXIS_MIN, start, "total", title=f"{m(start, False)}"),
                     total_source_html(bridge["start"]["tag"], start, "fy2024", filing), cls="totalrow"))
    for bar in bridge["bars"]:
        note = notes[bar["key"]]
        prev, running = running, running + bar["amount"]
        lo, hi = sorted((prev, running))
        cls = "up" if bar["amount"] > 0 else "down"
        flag = FLAG_TEXT[note["flags"][0]] if note["flags"] else ""
        quotes = passages_html(note["passages"], doc_url)
        body = (f'<p class="draft">{escape(note["draft"])}</p>{quotes}'
                f'{source_html(bar, facts_by_tag, filing)}')
        rows.append(row(bar["label"], m(bar["amount"]),
                        track(lo, hi, cls, prev, f"{m(bar['amount'])}; running total {m(running, False)}"),
                        body, flag=flag, key=bar["key"]))
    if running != end:
        raise SystemExit(f"bars do not reach FY2025 operating income: {running} vs {end}")
    rows += [f'<div class="group" data-key="group-{g}" hidden>{escape(label)}</div>' for g, label, _ in GROUPS]
    rows.append(row(bridge["end"]["label"], m(end, False),
                    track(AXIS_MIN, end, "total", running, f"{m(end, False)}"),
                    total_source_html(bridge["end"]["tag"], end, "fy2025", filing), cls="totalrow", key="end"))

    cost = sum(b["amount"] for b in bridge["bars"] if b["kind"] == "expense")
    by_key = {b["key"]: b["amount"] for b in bridge["bars"]}
    ticks = "".join(f'<span style="left:{x(t):.3f}%">{m(t, False).replace(".0M", "M")}</span>'
                    for t in range(AXIS_MIN + TICK, AXIS_MAX, TICK))
    page = TEMPLATE.format(
        company=escape(filing["company"]),
        change=m(start - end, False), change_pct=pct(end, start),
        start=m(start, False), end=m(end, False),
        volume=m(-by_key["volume"], False), yield_=m(by_key["yield"], False), cost=m(cost, False),
        ticks=ticks, rows="\n".join(rows), findings=findings(bridge["bars"], commentary, facts, bridge),
        doc_url=escape(doc_url), index_url=escape(filing["index_url"]), accession=escape(filing["accession"]),
        reviewer=escape(commentary["reviewed_by"]),
        reviewed_on=escape(commentary["reviewed_on"]), axis_min=m(AXIS_MIN, False).replace(".0M", "M"),
        views=json.dumps(views(bridge["bars"], start)).replace("</", "<\\/"), script=SCRIPT,
        nav=header.nav(prefix=UP), menu_css=header.CSS, up=UP,
    )
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(page, encoding="utf-8")
    print(f"{OUT.relative_to(ROOT)}: {len(rows)} rows, {start:,} -> {end:,} (USD thousands)")


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ODFL bridge, FY2025 - chomper</title>
<meta name="description" content="Why {company}'s operating income fell from FY2024 to FY2025, bar by bar, with management's explanations quoted and linked to the 10-K.">
<style>
:root {{
  color-scheme: light;
  --bg: #fcfcfb; --panel: #f4f3f0; --ink: #0b0b0b; --ink-2: #52514e; --ink-3: #75746f;
  --rule: #e2e1dc; --grid: #ecebe7; --up: #1f8a4c; --down: #d03b3b; --total: #8b8a85;
  --flag-bg: #fdf1e7; --flag-ink: #8a3d0f; --link: #1c5cab;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    color-scheme: dark;
    --bg: #1a1a19; --panel: #232322; --ink: #f0efec; --ink-2: #c3c2b7; --ink-3: #9a9992;
    --rule: #383835; --grid: #2a2a28; --up: #3fb36b; --down: #e05252; --total: #8b8a85;
    --flag-bg: #3a2a1e; --flag-ink: #f2b48c; --link: #86b6ef;
  }}
}}
:root[data-theme="dark"] {{
  color-scheme: dark;
  --bg: #1a1a19; --panel: #232322; --ink: #f0efec; --ink-2: #c3c2b7; --ink-3: #9a9992;
  --rule: #383835; --grid: #2a2a28; --up: #3fb36b; --down: #e05252; --total: #8b8a85;
  --flag-bg: #3a2a1e; --flag-ink: #f2b48c; --link: #86b6ef;
}}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: var(--bg); color: var(--ink);
  font: 16px/1.5 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }}
main {{ max-width: 60rem; margin: 0 auto; padding: 2rem 1rem 4rem; }}
h1 {{ font-size: 1.6rem; line-height: 1.25; margin: 0 0 .5rem; }}
h2 {{ font-size: 1.1rem; margin: 2.5rem 0 .75rem; }}
.lede {{ font-size: 1.1rem; color: var(--ink-2); margin: 0 0 1.5rem; max-width: 46rem; }}
.lede b {{ color: var(--ink); font-weight: 600; }}
a {{ color: var(--link); }}
.chart {{ border-top: 1px solid var(--rule); }}
.head, summary {{ display: grid; grid-template-columns: minmax(8rem, 15rem) 1fr 5.5rem; gap: 0 .75rem;
  align-items: center; }}
.head {{ font-size: .8rem; color: var(--ink-3); padding: .5rem 0 .25rem; border-bottom: 1px solid var(--rule); }}
.head .axis {{ position: relative; height: 1.2em; }}
.head .axis span {{ position: absolute; transform: translateX(-50%); white-space: nowrap; }}
.head .amount {{ text-align: right; }}
.legend {{ display: flex; flex-wrap: wrap; gap: .25rem 1.25rem; font-size: .85rem; color: var(--ink-2);
  margin: 0 0 .5rem; }}
.legend i {{ display: inline-block; width: .8rem; height: .8rem; border-radius: 2px; margin-right: .35rem;
  vertical-align: -1px; }}
details.row {{ border-bottom: 1px solid var(--rule); }}
summary {{ list-style: none; cursor: pointer; padding: .45rem 0; min-height: 2.75rem; }}
summary::-webkit-details-marker {{ display: none; }}
summary:hover {{ background: var(--panel); }}
summary:focus-visible {{ outline: 2px solid var(--link); outline-offset: -2px; }}
.label {{ font-size: .95rem; padding-left: 1.1rem; position: relative; }}
.label::before {{ content: ""; position: absolute; left: .2rem; top: .45em; border: .3em solid transparent;
  border-left-color: var(--ink-3); transition: transform .15s; transform-origin: 25% 50%; }}
details[open] .label::before {{ transform: rotate(90deg); }}
.head .label::before {{ display: none; }}
.totalrow .label {{ font-weight: 600; }}
.flag {{ display: block; width: fit-content; font-size: .75rem; line-height: 1.3; color: var(--flag-ink);
  background: var(--flag-bg); border-radius: 3px; padding: .1rem .4rem; margin-top: .2rem; }}
.track {{ position: relative; height: 1.4rem; }}
.grid, .link {{ position: absolute; top: -.45rem; bottom: -.45rem; width: 0; }}
.grid {{ border-left: 1px solid var(--grid); }}
.link {{ top: -.95rem; border-left: 1px dashed var(--ink-3); opacity: .6; }}
.bar {{ position: absolute; top: .2rem; bottom: .2rem; min-width: 2px; border-radius: 2px; }}
.bar.up {{ background: var(--up); }}
.bar.down {{ background: var(--down); }}
.bar.total {{ background: var(--total); border-radius: 0 3px 3px 0; }}
.amount {{ text-align: right; font-variant-numeric: tabular-nums; font-size: .95rem; }}
.totalrow .amount {{ font-weight: 600; }}
.body {{ padding: .25rem 0 1.25rem 1.1rem; max-width: 46rem; }}
.draft {{ margin: .25rem 0 1rem; }}
.quote {{ margin: 0 0 .9rem; padding-left: .9rem; border-left: 3px solid var(--rule); }}
.quote blockquote {{ margin: 0; color: var(--ink-2); }}
.quote figcaption {{ font-size: .8rem; margin-top: .2rem; }}
.tablequote table {{ border-collapse: collapse; font-size: .85rem; font-variant-numeric: tabular-nums;
  color: var(--ink-2); }}
.tablequote th, .tablequote td {{ padding: .1rem .6rem .1rem 0; text-align: right; font-weight: normal; }}
.tablequote thead th {{ color: var(--ink-3); font-size: .75rem; }}
.tablequote tbody th {{ text-align: left; }}
.source {{ display: grid; grid-template-columns: max-content 1fr; gap: .15rem .9rem; font-size: .8rem;
  color: var(--ink-3); margin: 1rem 0 0; padding-top: .6rem; border-top: 1px dashed var(--rule); }}
.source dt {{ color: var(--ink-2); }}
.source dd {{ margin: 0; overflow-wrap: anywhere; }}
.source ul {{ margin: .1rem 0 0; padding-left: 1.1rem; }}
.note {{ font-size: .8rem; color: var(--ink-3); margin: .5rem 0 0; }}
.order {{ border: 0; margin: 0 0 .75rem; padding: 0; display: flex; flex-wrap: wrap; gap: .25rem 1rem;
  font-size: .85rem; color: var(--ink-2); }}
.order legend {{ float: left; padding: 0; margin-right: .25rem; color: var(--ink-3); }}
.order label {{ cursor: pointer; white-space: nowrap; }}
.order input {{ accent-color: var(--link); margin: 0 .3rem 0 0; vertical-align: -1px; }}
.group {{ font-size: .8rem; font-weight: 600; color: var(--ink-3); padding: .9rem 0 .2rem 1.1rem;
  border-bottom: 1px solid var(--rule); }}
.group[hidden], .order[hidden] {{ display: none; }}
.findings {{ padding-left: 1.2rem; max-width: 46rem; }}
.findings li {{ margin-bottom: .75rem; }}
.findings strong {{ font-weight: 600; }}
footer {{ margin-top: 3rem; font-size: .85rem; color: var(--ink-2); max-width: 46rem;
  border-top: 1px solid var(--rule); padding-top: 1rem; }}
@media (max-width: 40rem) {{
  .head, summary {{ grid-template-columns: minmax(0, 1fr) 4.9rem; }}
  .head .axis, .head .label {{ display: none; }}
  .track {{ grid-column: 1 / -1; grid-row: 2; height: 1rem; margin-top: .3rem; }}
  .bar {{ top: .1rem; bottom: .1rem; }}
  .link {{ display: none; }}
  .label {{ font-size: .9rem; }}
  .body {{ padding-left: 0; }}
}}
@media (forced-colors: active) {{
  .bar {{ border: 1px solid CanvasText; }}
}}
{menu_css}
</style>
</head>
<body>
<main>
{nav}
<h1>Why Old Dominion's operating income fell {change} in 2025</h1>
<p class="lede">Operating income went from <b>{start}</b> in 2024 to <b>{end}</b> in 2025 ({change_pct}%).
Shipping less freight cost <b>{volume}</b>; higher prices made back <b>{yield_}</b>; costs fell, adding <b>{cost}</b>.
Open any row for management's explanation, quoted from the 10-K and linked to the page it came from.</p>
<p class="crossref"><a href="{up}ODFL.html">Company page</a>: five years of Old Dominion's cost lines as a share of revenue.</p>

<p class="legend"><span><i style="background:var(--up)"></i>Raised operating income</span>
<span><i style="background:var(--down)"></i>Lowered operating income</span>
<span><i style="background:var(--total)"></i>Operating income</span></p>
<fieldset class="order" hidden><legend>Order bars by</legend>
<label><input type="radio" name="order" value="statement" checked>10-K line order</label>
<label><input type="radio" name="order" value="behavior">Cost behavior</label>
<label><input type="radio" name="order" value="size">Size of change</label></fieldset>
<div class="chart">
<div class="head" aria-hidden="true"><span class="label">Change, 2024 to 2025</span><span class="axis">{ticks}</span><span class="amount">$ millions</span></div>
{rows}
</div>
<p class="note">The scale starts at {axis_min}, not zero, so the changes are visible.
Cost lines show their effect on operating income: a cost that fell appears as a gain.</p>
<p class="note" id="behavior-note" hidden>The cost groups are our own judgment of how each line behaves as
freight volume changes; the 10-K does not classify costs this way.</p>
<script type="application/json" id="views">{views}</script>
<script>{script}</script>

<h2>What the numbers show</h2>
<ul class="findings">
{findings}
</ul>

<footer>
<p>Source: {company} annual report on Form 10-K for 2025 (<a href="{doc_url}">document</a>,
<a href="{index_url}">filing index</a>, accession {accession}). Both years come from that filing.
Dollar amounts come from its XBRL financial data; freight volume and price come from its operating metrics table.</p>
<p>How the commentary was made: an AI model found the passages and drafted each explanation.
Code then checked every quote word for word against the filing, checked every number against the data,
and computed every flag and figure in "What the numbers show". {reviewer} reviewed and approved the commentary on {reviewed_on}.</p>
</footer>
</main>
</body>
</html>
"""


SCRIPT = """
(function () {
  var views = JSON.parse(document.getElementById("views").textContent);
  var chart = document.querySelector(".chart"), end = chart.querySelector('[data-key="end"]');
  var note = document.getElementById("behavior-note"), picker = document.querySelector(".order");
  function show(name) {
    chart.querySelectorAll(".group").forEach(function (g) { g.hidden = true; });
    views[name].forEach(function (it) {
      var el = chart.querySelector('[data-key="' + it.key + '"]');
      chart.insertBefore(el, end);
      if (!it.bar) { el.hidden = false; return; }
      var bar = el.querySelector(".bar");
      bar.style.left = it.bar[0] + "%"; bar.style.width = it.bar[1] + "%"; bar.title = it.title;
      el.querySelector(".link").style.left = it.bar[2] + "%";
    });
    note.hidden = name !== "behavior";
  }
  picker.addEventListener("change", function (e) { show(e.target.value); });
  picker.hidden = false;
})();
"""


if __name__ == "__main__":
    main()
