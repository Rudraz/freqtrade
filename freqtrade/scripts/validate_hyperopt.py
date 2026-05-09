#!/usr/bin/env python3
"""
Validate that hyperopt best params are a meaningful improvement.
Reads best_params.json and checks Sharpe/profit vs minimum thresholds.
Exits 0 if improvement is real, 1 if not worth applying.
"""

import json
import sys
from pathlib import Path

MIN_SHARPE   = 0.8    # higher bar than backtest validation (0.5)
MIN_PROFIT   = 0.01   # at least 1% total profit in hyperopt period


def main():
    if len(sys.argv) < 2:
        print("Usage: validate_hyperopt.py <best_params.json> [strategy.py]")
        sys.exit(1)

    params_path = Path(sys.argv[1])
    if not params_path.exists():
        print(f"❌ Best params file not found: {params_path}")
        sys.exit(1)

    with open(params_path) as f:
        content = f.read().strip()

    if not content or content == "null":
        print("❌ No best params found — hyperopt may have produced no results")
        sys.exit(1)

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"❌ Could not parse best_params.json: {e}")
        sys.exit(1)

    # freqtrade hyperopt-show --print-json wraps under 'results_metrics'
    metrics = data.get("results_metrics", data)
    sharpe  = metrics.get("sharpe", None)
    profit  = metrics.get("profit_total", metrics.get("profit_total_pct", None))

    print("\n" + "="*50)
    print("  HYPEROPT VALIDATION REPORT")
    print("="*50)

    passed = True

    if sharpe is not None:
        ok = sharpe >= MIN_SHARPE
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"  {status}  Sharpe: {sharpe:.4f} (min {MIN_SHARPE})")
        if not ok:
            passed = False
    else:
        print("  ⚠️  SKIP  Sharpe: not available")

    if profit is not None:
        profit_pct = profit * 100 if abs(profit) < 10 else profit
        ok = profit_pct >= MIN_PROFIT * 100
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"  {status}  Total profit: {profit_pct:.2f}% (min {MIN_PROFIT*100:.0f}%)")
        if not ok:
            passed = False
    else:
        print("  ⚠️  SKIP  Profit: not available")

    if "params_details" in data:
        print("\n  Best parameters found:")
        for space, params in data["params_details"].items():
            for key, val in params.items():
                print(f"    {space}.{key} = {val}")

    print("="*50)
    if passed:
        print("  🟢 VERDICT: Params are an improvement — apply and open PR ✅\n")
        sys.exit(0)
    else:
        print("  🔴 VERDICT: No significant improvement — keeping current params ❌\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
