"""Compute the FY2024 -> FY2025 operating income bridge from data/facts.json and data/stats.json.

Writes data/bridge.json in integer USD thousands. Bars are signed by their
effect on operating income. The bars must sum exactly to the change.

Usage: python bridge.py
"""
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
CWT_PER_TON = 20  # hundredweight per (short) ton


def main():
    facts = json.loads((DATA / "facts.json").read_text(encoding="utf-8"))
    stats = json.loads((DATA / "stats.json").read_text(encoding="utf-8"))
    lines = {line["key"]: line for line in facts["lines"]}
    expense_keys = [k for k in lines if k not in ("revenue", "total_expenses", "operating_income")]

    tons, cwt = stats["ltl_tons_thousands"], stats["ltl_revenue_per_hundredweight"]
    t24, t25 = Decimal(tons["fy2024"]), Decimal(tons["fy2025"])
    r24, r25 = Decimal(cwt["fy2024"]), Decimal(cwt["fy2025"])

    def whole(x):
        return int(x.quantize(Decimal("1"), ROUND_HALF_UP))

    # tons are in thousands and rev/cwt in dollars, so products are in $ thousands
    volume = whole((t25 - t24) * CWT_PER_TON * r24)
    yield_ = whole(t25 * CWT_PER_TON * (r25 - r24))
    revenue_change = lines["revenue"]["fy2025"] - lines["revenue"]["fy2024"]
    remainder = revenue_change - volume - yield_

    stat_source = {"page": tons["page"], "rows": [tons["row_text"], cwt["row_text"]]}
    bars = [
        {"key": "volume", "label": "Volume (LTL tons)", "kind": "revenue", "amount": volume,
         "basis": "(FY2025 tons - FY2024 tons) x 20 cwt/ton x FY2024 revenue per cwt", "source": stat_source},
        {"key": "yield", "label": "Yield (revenue per hundredweight)", "kind": "revenue", "amount": yield_,
         "basis": "FY2025 tons x 20 cwt/ton x (FY2025 - FY2024 revenue per cwt)", "source": stat_source},
        {"key": "revenue_remainder", "label": "Other revenue and remainder", "kind": "revenue", "amount": remainder,
         "basis": "reported revenue change - volume - yield",
         "source": {"tag": lines["revenue"]["tag"]}},
    ]
    for k in expense_keys:
        line = lines[k]
        bars.append({
            "key": k, "label": line["label"], "kind": "expense",
            "amount": -(line["fy2025"] - line["fy2024"]),  # lower cost raises operating income
            "basis": "-(FY2025 - FY2024)",
            "source": {"tag": line["tag"], "fy2024": line["fy2024"], "fy2025": line["fy2025"]},
        })

    start = lines["operating_income"]["fy2024"]
    end = lines["operating_income"]["fy2025"]
    if start + sum(b["amount"] for b in bars) != end:
        raise SystemExit(f"bridge does not foot: {start} + {sum(b['amount'] for b in bars)} != {end}")

    out = {
        "unit": facts["unit"],
        "filing": facts["filing"],
        "start": {"label": "FY2024 operating income", "amount": start, "tag": lines["operating_income"]["tag"]},
        "bars": bars,
        "end": {"label": "FY2025 operating income", "amount": end, "tag": lines["operating_income"]["tag"]},
    }
    (DATA / "bridge.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"bridge.json: {start:,} + {len(bars)} bars ({end - start:+,}) = {end:,}, foots")
    for b in bars:
        print(f"  {b['label']:<36} {b['amount']:>+10,}")


if __name__ == "__main__":
    main()
