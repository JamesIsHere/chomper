"""Failure census for the five-year step: run history.py's own steps on every S&P 500 company, write no pages and
no data/history files, and record why each company stops.

Each company passes or fails. A failure keeps the exact stop message, sorted into a class; a pass also records
signals the checks do not stop on (split rows, loss years, rounding gaps). Records are saved after every company,
so a rerun resumes; companies that failed on a download are tried again.

Writes data/census.json (every record) and census.md (counts by class, signals, every company).

Usage: python census.py            (all companies; the 11 with pages first, as a control)
       python census.py --report   (rewrite census.md from data/census.json, no downloads)
       python census.py --fresh    (rerun every company, e.g. after a fix; cached downloads are reused)
"""
import json
import re
import socket
import sys
import time
import traceback
import urllib.error
from collections import Counter

from history import RAW, cik_for, merge, read_filing, split, ten_ks
from pull import ROOT, user_agent

socket.setdefaulttimeout(60)  # urlopen in pull.fetch has no timeout of its own; a stalled request must not hang the run
OUT = ROOT / "data" / "census.json"
REPORT = ROOT / "census.md"
CONTROL = ["AAPL", "CAT", "CCL", "HD", "JNJ", "JPM", "MSFT", "ODFL", "PGR", "PLD", "UNH"]

# (class, pattern on the stop message), first match wins; every hard stop in history.py and pull.py is covered.
CLASSES = [
    ("Not found", r"not in SEC company_tickers|no 10-K filings|expected one 10-K about two years before"),
    ("Filing layout", r"expected one \*_"),
    ("Statement", r"income statement not unique|^role .* not in"),
    ("Anchor", r"no calculation for a pre-tax income tag|expected 3 years of pre-tax income"),
    ("Revenue", r"expected one revenue concept"),
    ("Footing", r"lines foot to"),
    ("Values", r"conflicting values"),
    ("Member slice", r"reported by member in"),
    ("Structure", r"changes sign between the two filings|expected five fiscal years|bridge does not reach"),
]


def classify(message):
    for name, pattern in CLASSES:
        if re.search(pattern, message):
            return name
    return "Unclassified stop"


def signals(ends, pretax, lines, gaps):
    """What a passing company shows that the checks do not stop on."""
    by_label = {}
    for l in lines:
        by_label.setdefault(l["label"], []).append(l)
    split_rows = []
    for label, ls in by_label.items():  # same label, years that never overlap: one line under two tags
        if len(ls) > 1:
            years = [{e for e, v in l["values"].items() if v is not None} for l in ls]
            if all(not (a & b) for i, a in enumerate(years) for b in years[i + 1:]):
                split_rows.append({"label": label, "concepts": [l["concept"] for l in ls]})
    return {"split_rows": split_rows,
            "loss_years": [e for e in ends if pretax[e] <= 0],
            "rounding_gaps": [{k: g[k] for k in ("period_end", "subtotal", "gap", "allowed")} for g in gaps]}


def run_one(ticker, ua):
    """One company through history.py's steps, nothing written. Returns its record."""
    t0 = time.time()
    rec = {"ticker": ticker}
    try:
        cik, company = cik_for(ticker, ua)
        rec |= {"cik": cik, "company": company}
        (RAW / str(cik)).mkdir(parents=True, exist_ok=True)
        latest_f, older_f = ten_ks(cik, ua)
        rec["filings"] = [latest_f["accession"], older_f["accession"]]
        latest, older = read_filing(cik, latest_f, ua), read_filing(cik, older_f, ua)
        ends, revenue, pretax, oi, lines, disagreements = merge(latest, older)
        if len(ends) != 5:
            raise SystemExit(f"expected five fiscal years, found {ends}")
        split(ends, revenue, pretax, lines)
        gaps = [g for f in (latest, older) for g in f["footing_gaps"] if g["period_end"] in ends]
        rec |= {"status": "pass", "lines": len(lines), "disagreements": len(disagreements),
                "signals": signals(ends, pretax, lines, gaps)}
    except SystemExit as stop:  # a hard stop: the thing being counted
        rec |= {"status": "fail", "class": classify(str(stop)), "message": str(stop)}
    except (urllib.error.URLError, TimeoutError, ConnectionError) as err:
        rec |= {"status": "download", "class": "Download", "message": f"{type(err).__name__}: {err}"}
    except Exception as err:  # a bug in our code, not a property of the filing
        rec |= {"status": "crash", "class": "Crash", "message": f"{type(err).__name__}: {err}",
                "traceback": traceback.format_exc(limit=-3)}
    rec["seconds"] = round(time.time() - t0, 1)
    return rec


def save(records):
    tmp = OUT.with_suffix(".tmp")
    tmp.write_text(json.dumps(records, indent=1) + "\n", encoding="utf-8")
    tmp.replace(OUT)


def table(head, rows):
    """Markdown table with every column padded so the pipes line up."""
    widths = [max(len(str(r[i])) for r in [head] + rows) for i in range(len(head))]
    fmt = lambda r: "| " + " | ".join(str(c).ljust(w) for c, w in zip(r, widths)) + " |"
    return "\n".join([fmt(head), "| " + " | ".join("-" * w for w in widths) + " |"] + [fmt(r) for r in rows])


def report(records, universe):
    sector = {c["ticker"]: c["sector"] for c in universe}
    recs = list(records.values())
    counts = Counter("Pass" if r["status"] == "pass" else r["class"] for r in recs)
    passed = [r for r in recs if r["status"] == "pass"]
    split_n = sum(bool(r["signals"]["split_rows"]) for r in passed)
    loss_n = sum(bool(r["signals"]["loss_years"]) for r in passed)
    round_n = sum(bool(r["signals"]["rounding_gaps"]) for r in passed)
    out = ["# Census: the five-year step on the S&P 500", "",
           f"{len(recs)} of {len(universe)} companies run; {len(passed)} pass. Generated by census.py from "
           "data/census.json; no pages or data/history files written.", "",
           "## Outcome by class", "",
           table(["Outcome", "Companies"], [[k, v] for k, v in counts.most_common()]), "",
           "## Signals on companies that pass", "",
           table(["Signal", "Companies"],
                 [["Split rows (one line under two tags)", split_n], ["Loss year in the five", loss_n],
                  ["Rounding row", round_n]]), "",
           "## Every company", ""]
    rows = []
    for r in sorted(recs, key=lambda r: ("Pass" if r["status"] == "pass" else r["class"], r["ticker"])):
        if r["status"] == "pass":
            s = r["signals"]
            note = "; ".join(x for x in (
                f"split rows: {', '.join(x['label'] for x in s['split_rows'])}" if s["split_rows"] else "",
                f"loss years: {', '.join(s['loss_years'])}" if s["loss_years"] else "",
                f"rounding: {len(s['rounding_gaps'])}" if s["rounding_gaps"] else "") if x)
            rows.append([r["ticker"], sector.get(r["ticker"], ""), "Pass", note.replace("|", "/")])
        else:
            rows.append([r["ticker"], sector.get(r["ticker"], ""), r["class"],
                         r["message"].replace("|", "/").replace("\n", " ")[:160]])
    out.append(table(["Ticker", "Sector", "Outcome", "Detail"], rows))
    REPORT.write_text("\n".join(out) + "\n", encoding="utf-8")


def main():
    universe = json.loads((ROOT / "data" / "sp500.json").read_text(encoding="utf-8"))["companies"]
    records = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    if sys.argv[1:] == ["--report"]:
        report(records, universe)
        return
    ua = user_agent()
    tickers = CONTROL + sorted(c["ticker"] for c in universe if c["ticker"] not in CONTROL)
    fresh = sys.argv[1:] == ["--fresh"]  # rerun every company after a fix; downloads stay cached
    todo = [t for t in tickers if fresh or t not in records or records[t]["status"] == "download"]
    start = time.time()
    for i, t in enumerate(todo, 1):
        records[t] = run_one(t, ua)
        save(records)
        r = records[t]
        print(f"[{i}/{len(todo)}] {t}: {r['status'] if r['status'] == 'pass' else r['class']} "
              f"({r['seconds']}s, {(time.time() - start) / 60:.1f} min elapsed)", flush=True)
    report(records, universe)
    print(f"census.md written: {sum(r['status'] == 'pass' for r in records.values())} of {len(records)} pass")


if __name__ == "__main__":
    main()
