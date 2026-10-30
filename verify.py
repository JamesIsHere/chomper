"""Check the drafted commentary against the filing and compute the flags.

Reads data/commentary.raw.json, data/mdna.json and data/bridge.json. Writes
data/commentary.draft.json (commentary plus check results and flags) and
review.md (one section per bar, for James). Exits non-zero on any hard
failure: a quote not on its cited page, an amount phrase outside its quote,
a draft number with no source, or a missing bar.

Usage: python verify.py                  check and write the draft + review
       python verify.py --approve "Name"  after review: write data/commentary.json
"""
import json
import re
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

from pull import norm

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

NUMBER = re.compile(r"(?<![\w.])\d[\d,]*(?:\.\d+)?")
AMOUNT = re.compile(r"\$\s?([\d,]+(?:\.(\d+))?)\s*(million|billion|thousand)?", re.I)
SCALE = {"billion": Decimal(1_000_000), "million": Decimal(1000), "thousand": Decimal(1), None: Decimal("0.001")}
ALWAYS_ALLOWED = {"2024", "2025"}


def numbers(text):
    return {n.replace(",", "") for n in NUMBER.findall(text)}


def parse_amount(phrase):
    """'$54.0 million' -> (value in thousands, half-unit tolerance in thousands)."""
    m = AMOUNT.search(phrase)
    if not m:
        return None
    scale = SCALE[m.group(3).lower() if m.group(3) else None]
    decimals = len(m.group(2) or "")
    value = Decimal(m.group(1).replace(",", "")) * scale
    tolerance = Decimal(5) / Decimal(10) ** (decimals + 1) * scale
    return value, tolerance


def apply_edits(raw, edits):
    """James's hand edits (edits.json) replace a bar's draft and/or add passages; checked like the model's."""
    for entry in raw["bars"]:
        edit = edits.get(entry["key"])
        if edit:
            entry["draft"] = edit.get("draft", entry["draft"])
            entry["passages"] = entry["passages"] + edit.get("add_passages", [])
            entry["edited_by"] = edit["edited_by"]
    unknown = set(edits) - {b["key"] for b in raw["bars"]}
    if unknown:
        raise SystemExit(f"edits.json names unknown bars: {sorted(unknown)}")
    return raw


def check(raw, mdna, bridge):
    pages = {p["page"]: p["text"] for p in mdna}
    bars = {b["key"]: b for b in bridge["bars"]}
    failures = []
    given = [b["key"] for b in raw["bars"]]
    if sorted(given) != sorted(bars):
        failures.append(f"bar keys mismatch: missing {sorted(set(bars) - set(given))}, "
                        f"extra or duplicate {sorted(k for k in given if given.count(k) > 1 or k not in bars)}")

    out = []
    for entry in raw["bars"]:
        bar = bars.get(entry["key"])
        if bar is None:
            continue
        passages, matched_amount = [], None
        for p in entry["passages"]:
            quote = norm(p["quote"])
            on_page = quote in pages.get(p["page"], "")
            where = [n for n, t in pages.items() if quote in t]
            result = {"page": p["page"], "quote": quote, "verbatim": on_page}
            if not on_page:
                failures.append(f"{bar['key']}: quote not on page {p['page']}"
                                f"{f' (found on {where})' if where else ' (not in MD&A)'}: {quote[:80]!r}")
            phrase = p["stated_amount_text"]
            if phrase:
                phrase = norm(phrase)
                parsed = parse_amount(phrase)
                if phrase not in quote or parsed is None:
                    failures.append(f"{bar['key']}: amount phrase {phrase!r} not a $ amount inside its quote")
                else:
                    value, tol = parsed
                    ok = abs(value - abs(bar["amount"])) <= tol
                    result["stated_amount"] = {"text": phrase, "thousands": str(value), "tolerance": str(tol),
                                               "matches_bar": ok}
                    matched_amount = ok if matched_amount is None else (matched_amount and ok)
            passages.append(result)

        allowed = ALWAYS_ALLOWED | numbers(" ".join(p["quote"] for p in passages))
        allowed |= numbers(f"{abs(bar['amount']) / 1000:,.1f} {abs(bar['amount']):,}")
        unsourced = sorted(numbers(entry["draft"]) - allowed)
        if unsourced:
            failures.append(f"{bar['key']}: draft numbers with no source: {unsourced}")

        flags = []
        if not passages:
            flags.append("not_discussed")
        elif matched_amount is None and bar["kind"] == "expense":
            flags.append("no_dollar_amount")
        if matched_amount is False:
            flags.append("amount_mismatch")
        out.append({"key": bar["key"], "label": bar["label"], "kind": bar["kind"], "amount": bar["amount"],
                    "draft": entry["draft"], "passages": passages, "flags": flags,
                    "quantified": bool(matched_amount), "edited_by": entry.get("edited_by")})

    expense = [b for b in out if b["kind"] == "expense"]
    total = sum(b["amount"] for b in expense)
    quantified = sum(b["amount"] for b in expense if b["quantified"])
    coverage = {
        "expense_change": total,
        "quantified_by_mdna": quantified,
        "unexplained": total - quantified,
        "share_quantified": str((Decimal(quantified) / Decimal(total) * 100).quantize(Decimal("0.1"))),
        "lines_quantified": f"{sum(b['quantified'] for b in expense)} of {len(expense)}",
    }
    order = [b["key"] for b in bridge["bars"]]
    out.sort(key=lambda b: order.index(b["key"]))
    return out, coverage, failures


def review(bars, coverage, failures, raw):
    m = lambda k: f"{k / 1000:+,.1f}"
    lines = [
        "# Commentary review",
        "",
        f"Drafted {raw['generated']} by {raw['model']}. Amounts in $ millions, as each item affects operating income.",
        "",
        f"Hard failures: {len(failures)}",
        *[f"- {f}" for f in failures],
        "",
        f"MD&A puts dollars on {coverage['lines_quantified']} expense lines: "
        f"{m(coverage['quantified_by_mdna'])} of the {m(coverage['expense_change'])} expense change "
        f"({coverage['share_quantified']}%); unexplained {m(coverage['unexplained'])}.",
        "",
    ]
    for b in bars:
        lines += [f"## {b['label']}  {m(b['amount'])}", "",
                  f"Flags: {', '.join(b['flags']) or 'none'}"
                  + (f"; draft edited by {b['edited_by']}" if b["edited_by"] else ""), "", b["draft"], ""]
        for p in b["passages"]:
            amt = p.get("stated_amount")
            tag = f"  [amount {amt['text']}: {'matches' if amt['matches_bar'] else 'MISMATCH'}]" if amt else ""
            lines.append(f"> p.{p['page']}{'' if p['verbatim'] else ' NOT VERBATIM'}: {p['quote']}{tag}")
            lines.append("")
    return "\n".join(lines) + "\n"


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--approve":
        draft = json.loads((DATA / "commentary.draft.json").read_text(encoding="utf-8"))
        if draft["failures"]:
            raise SystemExit(f"cannot approve: {len(draft['failures'])} hard failures")
        draft["reviewed_by"], draft["reviewed_on"] = sys.argv[2], date.today().isoformat()
        (DATA / "commentary.json").write_text(json.dumps(draft, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"commentary.json: approved by {sys.argv[2]}")
        return

    raw = json.loads((DATA / "commentary.raw.json").read_text(encoding="utf-8"))
    mdna = json.loads((DATA / "mdna.json").read_text(encoding="utf-8"))
    bridge = json.loads((DATA / "bridge.json").read_text(encoding="utf-8"))
    edits_file = ROOT / "edits.json"
    if edits_file.exists():
        raw = apply_edits(raw, json.loads(edits_file.read_text(encoding="utf-8")))
    bars, coverage, failures = check(raw, mdna, bridge)
    draft = {"generated": raw["generated"], "model": raw["model"], "coverage": coverage,
             "failures": failures, "bars": bars}
    (DATA / "commentary.draft.json").write_text(json.dumps(draft, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (ROOT / "review.md").write_text(review(bars, coverage, failures, raw), encoding="utf-8")
    for b in bars:
        print(f"  {b['label']:<36} {b['amount']:>+10,}  passages {len(b['passages'])}  flags {','.join(b['flags']) or '-'}")
    print(f"coverage: {coverage['lines_quantified']} lines, {coverage['share_quantified']}% of expense change, "
          f"unexplained {coverage['unexplained']:,}")
    print(f"hard failures: {len(failures)}")
    for f in failures:
        print(f"  {f}")
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
