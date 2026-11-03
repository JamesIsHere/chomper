"""The population waterfall: who could be read, who was, who is published, and who the cost measure would see.
Every count is taken from the file that defines that level and written to data/waterfall.json, which
build_history.py renders as the Waterfall page. No network, no AI.

    python waterfall.py

Levels and their sources:
  membership      data/membership.json      every company in the S&P 500 in any month the file covers
  today's list    data/sp500.json           the list the readers run on (tickers; a company may list two classes)
  five-year read  data/census.json          history.py's verdict on every ticker of today's list
  ten-year read   data/bulk/results.json    headline.py run over every readable ticker (the bulk run)
  published       data/history/, docs/      company pages finished by hand; bridges
  cost measure    data/bulk/headline/       fall years (revenue down 5% or more) and which profit lines they carry
  S&P 500 page    data/aggregate.json       a separate path: companyfacts figures for today's members
A ten-year pass reaches fiscal 2007 or stops short where the tags end without a gap (a short series, 2026-11-03);
the ten-year row counts both and says how many reach the peak, and the cost-measure rows count every pass.
The bulk folders are not in the repository; this script needs them and stops if they are missing. The json it
writes is tracked, so the page rebuilds anywhere.
"""
import glob
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path

from headline import FIRST
from pull import ROOT

BULK = ROOT / "data" / "bulk"
OUT = ROOT / "data" / "waterfall.json"
FALL = 0.05  # a fall year: revenue down by this share or more against the prior fiscal year

# headline.py's stop messages, in a reader's words; every stop must match one or this script stops
STOP_CLASSES = [
    ("Series starts after fiscal 2007 under the tags read; the early years need a hand record",
     r"starts \d{4}-\d{2}-\d{2}, not fiscal 2007"),
    ("A 10-K before XBRL: its acquisitions must be read by hand", r"predates XBRL; read its acquisitions"),
    ("A deal's assets acquired are not tagged: read them from the 10-K by hand",
     r"deal\(s\) need total assets acquired read from the 10-K"),
    ("A gap in the series no tag fills", r"has a gap \d{4}-\d{2}-\d{2} to \d{4}-\d{2}-\d{2}"),
    ("Series too short under the tags read", r"only \d+ years .*no other tag reaches further back"),
    ("No companyfacts tag matches the five-year page", r"no companyfacts tag matches the five-year page"),
    ("Acquisition spend the tagged deals leave unexplained is itself significant",
     r"(PaymentsToAcquireBusinesses|GoodwillAcquiredDuringPeriod).* leaves "),
    ("A year's 10-K not found", r"expected one 10-K, found \[\]"),
    ("Fiscal years not consecutive", r"are not consecutive"),
    ("Conflicting values in one filing", r"reports different values under the tags used"),
    ("No 10-K shows two consecutive years", r"no 10-K reports both"),
    ("A deal tagged at two values more than 1% apart",
     r"(consideration|net assets acquired|cash paid net of cash acquired|identifiable assets acquired) [\d,]+ and [\d,]+ in one filing"),
    ("A year's 10-K has no XBRL instance", r"expected one XBRL instance, found \[\]"),
]


def classify(message):
    for name, pat in STOP_CLASSES:
        if re.search(pat, message):
            return name
    raise SystemExit(f"headline stop not classified: {message[:120]}")


def main():
    mem = json.loads((ROOT / "data" / "membership.json").read_text(encoding="utf-8"))
    months = sorted(mem["months"])
    cos = mem["companies"]
    last = months[-1]
    uni = json.loads((ROOT / "data" / "sp500.json").read_text(encoding="utf-8"))
    tickers = uni["companies"]
    ciks = Counter(c["cik"] for c in tickers)
    two_class = sorted([c["ticker"] for c in tickers if c["cik"] == k] for k, n in ciks.items() if n > 1)
    mem_ciks = {k for c in cos for k in c["ciks"]}
    new_today = sorted(c["ticker"] for c in tickers if c["cik"] not in mem_ciks)
    census = json.loads((ROOT / "data" / "census.json").read_text(encoding="utf-8"))
    if set(census) != {c["ticker"] for c in tickers}:
        raise SystemExit("data/census.json does not cover exactly today's list")
    fails = Counter(r["class"] for r in census.values() if r["status"] != "pass")
    passes = sorted(t for t, r in census.items() if r["status"] == "pass")

    results_path = BULK / "results.json"
    if not results_path.is_file():
        raise SystemExit(f"{results_path} missing: the bulk run's results are needed")
    res = json.loads(results_path.read_text(encoding="utf-8"))
    if set(res) != set(passes):
        raise SystemExit("data/bulk/results.json does not cover exactly the census passes")
    ten_pass = sorted(t for t, r in res.items() if r["status"] == "pass")
    crashes = sorted(t for t, r in res.items() if r["status"] == "crash")
    if crashes:
        raise SystemExit(f"{len(crashes)} companies crashed in the bulk run (rerun them first): {crashes[:8]}")
    stops = Counter(classify(r["message"]) for r in res.values() if r["status"] == "stop")
    run_date = date.fromtimestamp(results_path.stat().st_mtime).isoformat()

    built = sorted(p.stem for p in (ROOT / "data" / "history").glob("*.json"))
    bridges = sorted(p.stem for p in (ROOT / "docs" / "bridge").glob("*.html"))

    files = sorted(glob.glob(str(BULK / "headline" / "*.json")))
    if sorted(Path(f).stem for f in files) != ten_pass:
        raise SystemExit("data/bulk/headline/ does not hold exactly the ten-year passes")
    # A pass reaches fiscal 2007 or is a short series (James, 2026-11-03): the page says how many reach the peak.
    to_2007 = sum(min(json.loads(Path(f).read_text(encoding="utf-8"))["period_ends"]) <= FIRST[1] for f in files)
    fall_years, both_years, pre_only_years = [], [], []
    for f in files:
        d = json.loads(Path(f).read_text(encoding="utf-8"))
        ends = sorted(d["period_ends"])
        rev, pre, oi = d["revenue"], d["pretax_income"], d.get("operating_income") or {}
        for a, b in zip(ends, ends[1:]):
            if rev.get(a) is None or rev.get(b) is None or rev[a] <= 0 or (rev[b] - rev[a]) / rev[a] > -FALL:
                continue
            has_pre = pre.get(a) is not None and pre.get(b) is not None
            has_oi = oi.get(a) is not None and oi.get(b) is not None
            fall_years.append(d["ticker"])
            (both_years if has_pre and has_oi else pre_only_years if has_pre else []).append(d["ticker"])
    agg = json.loads((ROOT / "data" / "aggregate.json").read_text(encoding="utf-8"))
    excl = Counter(re.sub(r" in any year.*| for .*", "", e["reason"]) for e in agg["excluded"])
    out = {
        "membership": {"first": months[0], "last": last, "companies": len(cos),
                       "left_before_last": sum(last not in c["months"] for c in cos),
                       "in_last_month": sum(last in c["months"] for c in cos)},
        "today": {"retrieved": uni["retrieved"], "tickers": len(tickers), "companies": len(ciks), "two_class": two_class,
                  "not_in_membership": new_today},
        "five_year": {"readable": len(passes), "not_readable": sum(fails.values()), "classes": dict(fails.most_common())},
        "ten_year": {"run": run_date, "passed": len(ten_pass), "to_2007": to_2007, "stopped": sum(stops.values()),
                     "classes": dict(stops.most_common())},
        "published": {"pages": built, "bridges": bridges},
        "measure": {"fall": FALL, "run": run_date, "companies": len(files),
                    "fall_years": len(fall_years), "fall_companies": len(set(fall_years)),
                    "both_years": len(both_years), "both_companies": len(set(both_years)),
                    "pre_only_years": len(pre_only_years), "pre_only_companies": len(set(pre_only_years))},
        "aggregate": {"summed": len(agg["companies"]),
                      "excluded": len(agg["excluded"]), "reasons": dict(excl.most_common())},
    }
    OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(f"data/waterfall.json: {out['membership']['companies']} ever members -> {out['today']['tickers']} tickers today -> "
          f"{out['five_year']['readable']} readable -> {out['ten_year']['passed']} read to the first year under the current rules -> "
          f"{len(built)} published; the {len(files)} passes show {out['measure']['fall_years']} fall years "
          f"in {out['measure']['fall_companies']} companies")


if __name__ == "__main__":
    main()
