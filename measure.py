"""The cost measure: how far a company's profit fell when its revenue fell, one row per fall year.

    python measure.py

A fall year is a fiscal year whose revenue is down FALL (5%) or more on the prior fiscal year. Its decremental
margin is the change in profit over the change in revenue: 0.30 means profit fell by 30 cents of each dollar of
revenue lost, so costs fell by the other 70. The verdict comes from pre-tax income for every company (James,
2026-11-03, decisions.md "The cost measure's verdict comes from pre-tax income"); where the company reports an
operating income subtotal the same ratio on operating income sits beside it, and a row is flagged when the two land
in different bands: below zero (profit rose or the line moved against revenue), zero to one, above one (profit fell
by more than revenue). The bands are structural boundaries, not a tolerance.

Reads every ten-year series the bulk run passed (data/bulk/headline/, not tracked) and writes data/measure.json
(tracked), which the pages read. No network, no AI. waterfall.py takes its fall-year counts from the same function,
so one definition of a fall year serves both.
"""
import glob
import json
from pathlib import Path

from pull import ROOT

BULK = ROOT / "data" / "bulk"
OUT = ROOT / "data" / "measure.json"
FALL = 0.05  # a fall year: revenue down by this share or more against the prior fiscal year


def band(m):
    return "below zero" if m < 0 else "zero to one" if m <= 1 else "above one"


def fall_years(d):
    """Every fall year in one headline file, oldest first: revenue and its change, the pre-tax decremental margin,
    the operating one where both years report operating income, and whether the two bands differ."""
    ends = sorted(d["period_ends"])
    rev, pre, oi = d["revenue"], d["pretax_income"], d.get("operating_income") or {}
    rows = []
    for a, b in zip(ends, ends[1:]):
        if rev.get(a) is None or rev.get(b) is None or rev[a] <= 0:
            continue
        change = rev[b] - rev[a]
        if change / rev[a] > -FALL:
            continue
        if pre.get(a) is None or pre.get(b) is None:
            raise SystemExit(f"{d['ticker']}: fall year ending {b} has revenue but no pre-tax income in both years")
        dm_pre = (pre[b] - pre[a]) / change
        dm_oi = (oi[b] - oi[a]) / change if oi.get(a) is not None and oi.get(b) is not None else None
        rows.append({
            "ticker": d["ticker"], "company": d["company"], "prior_end": a, "period_end": b,
            "revenue_prior": rev[a], "revenue": rev[b], "revenue_change": change / rev[a],
            "pretax_prior": pre[a], "pretax": pre[b], "decremental_pretax": dm_pre, "band": band(dm_pre),
            "operating_prior": oi.get(a), "operating": oi.get(b), "decremental_operating": dm_oi,
            "bands_differ": dm_oi is not None and band(dm_oi) != band(dm_pre),
        })
    return rows


def main():
    files = sorted(glob.glob(str(BULK / "headline" / "*.json")))
    if not files:
        raise SystemExit(f"{BULK / 'headline'} is empty: the bulk run's series are needed")
    rows = [r for f in files for r in fall_years(json.loads(Path(f).read_text(encoding="utf-8")))]
    out = {"fall": FALL, "companies_read": len(files), "fall_years": rows}
    OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    both = [r for r in rows if r["decremental_operating"] is not None]
    print(f"data/measure.json: {len(files)} series, {len(rows)} fall years in {len({r['ticker'] for r in rows})} companies; "
          f"{len(both)} with both lines, {sum(r['bands_differ'] for r in both)} where the bands differ")


if __name__ == "__main__":
    main()
