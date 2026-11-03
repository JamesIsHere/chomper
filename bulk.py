"""The bulk ten-year run: headline.py over every company the two-filing reader passed, into data/bulk/.

    python bulk.py              every ticker in data/bulk/history/ (a stop is recorded, not fatal)
    python bulk.py GOOGL NVDA   just these

Reads data/bulk/history/TICKER.json (history.py's output for the census passes), writes data/bulk/headline/TICKER.json
on a pass, and data/bulk/results.json: {ticker: {status: pass | stop | crash, step, message, seconds}}. A stop is
headline.py's own hard stop (a property of the filings under the current rules); a crash is a bug. Downloads are
cached under data/raw/, so a rerun after a rule change is mostly offline. The folder is not tracked; the Waterfall
page reads the results through waterfall.py.
"""
import json
import sys
import time
import traceback
from pathlib import Path

import headline
from pull import ROOT

BULK = ROOT / "data" / "bulk"
RESULTS = BULK / "results.json"


def main():
    headline.HISTORY = BULK / "history"  # read the census passes, write beside them
    headline.OUT = BULK / "headline"
    tickers = sys.argv[1:] or sorted(p.stem for p in headline.HISTORY.glob("*.json"))
    results = json.loads(RESULTS.read_text(encoding="utf-8")) if RESULTS.is_file() else {}
    t_start = time.time()
    for i, t in enumerate(tickers, 1):
        t0 = time.time()
        sys.argv = ["headline.py", t]
        rec = {"ticker": t}
        try:
            headline.main()
            rec["status"] = "pass"
        except SystemExit as stop:
            rec |= {"status": "stop", "step": "headline", "message": str(stop)}
        except Exception as err:
            rec |= {"status": "crash", "step": "headline", "message": f"{type(err).__name__}: {err}",
                    "traceback": traceback.format_exc(limit=-3)}
        rec["seconds"] = round(time.time() - t0, 1)
        results[t] = rec
        RESULTS.write_text(json.dumps(results, indent=1) + "\n", encoding="utf-8")
        print(f"[{i}/{len(tickers)} {time.time() - t_start:,.0f}s] {t}: {rec['status']}"
              + (f" -- {rec['message'][:110]}" if rec["status"] != "pass" else ""), flush=True)
    done = [results[t] for t in tickers]
    print(f"\n{sum(r['status'] == 'pass' for r in done)} pass, {sum(r['status'] == 'stop' for r in done)} stop, "
          f"{sum(r['status'] == 'crash' for r in done)} crash of {len(done)}")


if __name__ == "__main__":
    main()
