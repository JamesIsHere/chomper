"""Rebuild every page in docs/ from the committed data. No network, no AI call.

    python rebuild.py

Runs build.py (the ODFL one-year bridge, from the approved commentary), build_history.py (the company pages,
the All page, Decisioning and Considerations), then coherence.py (every figure that appears on more than one
page, or in the README, compared across them). Stops at the first failure. The S&P 500 and Membership pages
come from aggregate.py and membership.py, which read the SEC and Wikipedia, and are rebuilt only when run by hand.
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

for script in ("build.py", "build_history.py", "coherence.py"):
    print(f"-- {script}", flush=True)
    if subprocess.run([sys.executable, str(HERE / script)], cwd=HERE).returncode:
        raise SystemExit(f"{script} failed" + ("; docs/ may be half rebuilt" if script != "coherence.py" else ""))
