"""Ask a language model to cite and draft commentary for each bridge bar.

Reads data/bridge.json, data/stats.json and data/mdna.json; sends one prompt
through `claude -p` (plan tokens, no tools, structured output); writes the
model's raw answer to data/commentary.raw.json. It decides nothing: quotes,
amounts and flags are checked by verify.py.

Usage: python draft.py   (needs the claude CLI on PATH)
"""
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

SYSTEM = (
    "You are a careful financial analyst's assistant. You locate evidence in an "
    "SEC filing and draft plain-English commentary. You never invent numbers."
)

INSTRUCTIONS = """\
Below is the MD&A (Item 7) of Old Dominion Freight Line's FY2025 10-K, split by
printed page, and a bridge of operating income from FY2024 to FY2025 in 12 bars.
Each bar amount is its effect on operating income: for expense lines, positive
means the cost fell.

For EACH bar, return:
- passages: every MD&A passage that explains why THIS line changed between 2024
  and 2025. Copy each quote EXACTLY, character for character, as one contiguous
  sentence or clause from a single page, at most about 300 characters. Give the
  printed page number. Do not cite passages that only define a metric, describe
  an accounting policy, or discuss a different line. If nothing in the MD&A
  explains this line's change, return an empty list.
- stated_amount_text: inside a passage, the exact dollar phrase (for example
  "$54.0 million") ONLY if it states the change in this bar's whole line.
  Component amounts (part of the line) and percentages do not count; use null.
- draft: one or two plain-English sentences for a non-technical finance
  executive explaining what moved and why, according to management. Express
  money in $ millions with one decimal. Use only numbers that appear in this
  bar's amount or in your quoted passages. If there is no passage, say plainly
  that management's discussion does not address this line, and state the
  amount.

Return one entry per bar, using the bar keys given.
"""


def schema(keys):
    passage = {
        "type": "object",
        "properties": {
            "page": {"type": "integer"},
            "quote": {"type": "string"},
            "stated_amount_text": {"type": ["string", "null"]},
        },
        "required": ["page", "quote", "stated_amount_text"],
        "additionalProperties": False,
    }
    bar = {
        "type": "object",
        "properties": {
            "key": {"type": "string", "enum": keys},
            "passages": {"type": "array", "items": passage},
            "draft": {"type": "string"},
        },
        "required": ["key", "passages", "draft"],
        "additionalProperties": False,
    }
    return {
        "type": "object",
        "properties": {"bars": {"type": "array", "items": bar}},
        "required": ["bars"],
        "additionalProperties": False,
    }


def prompt(bridge, stats, mdna):
    bars = "\n".join(
        f"- key={b['key']} | {b['label']} | {b['amount'] / 1000:+,.1f} $M | basis: {b['basis']}"
        for b in bridge["bars"]
    )
    t, c = stats["ltl_tons_thousands"], stats["ltl_revenue_per_hundredweight"]
    context = (
        f"FY2024 operating income {bridge['start']['amount'] / 1000:,.1f} $M; "
        f"FY2025 {bridge['end']['amount'] / 1000:,.1f} $M. "
        f"LTL tons (thousands) {t['fy2024']:,} -> {t['fy2025']:,}; "
        f"LTL revenue per hundredweight ${c['fy2024']} -> ${c['fy2025']}."
    )
    pages = "\n\n".join(f"[page {p['page']}]\n{p['text']}" for p in mdna)
    return f"{INSTRUCTIONS}\n## Bridge\n{context}\n{bars}\n\n## MD&A\n{pages}\n"


def main():
    bridge = json.loads((DATA / "bridge.json").read_text(encoding="utf-8"))
    stats = json.loads((DATA / "stats.json").read_text(encoding="utf-8"))
    mdna = json.loads((DATA / "mdna.json").read_text(encoding="utf-8"))
    keys = [b["key"] for b in bridge["bars"]]

    cmd = [
        "claude", "-p",
        "--output-format", "json",
        "--no-session-persistence",
        "--tools", "",
        "--system-prompt", SYSTEM,
        "--json-schema", json.dumps(schema(keys)),
    ]
    run = subprocess.run(cmd, input=prompt(bridge, stats, mdna), capture_output=True,
                         text=True, encoding="utf-8", shell=False)
    if run.returncode != 0:
        raise SystemExit(f"claude -p failed ({run.returncode}): {run.stderr[:500]}")
    reply = json.loads(run.stdout)
    if reply.get("is_error") or not reply.get("structured_output"):
        raise SystemExit(f"no structured output: {run.stdout[:500]}")

    out = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": next(iter(reply.get("modelUsage", {"unknown": None}))),
        "bars": reply["structured_output"]["bars"],
    }
    (DATA / "commentary.raw.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"commentary.raw.json: {len(out['bars'])} bars from {out['model']}")


if __name__ == "__main__":
    main()
