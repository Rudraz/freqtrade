#!/usr/bin/env python3
"""
Freqtrade Backtest Validation Script
=====================================
Reads freqtrade backtest results JSON and enforces minimum
performance thresholds before allowing deploy to Pi.

Thresholds (edit these to adjust your standards):
  - MIN_MONTHLY_PROFIT_PCT : Minimum average monthly profit %
  - MAX_DRAWDOWN_PCT        : Maximum allowed drawdown %
  - MIN_TRADES              : Minimum number of trades in period
  - MIN_SHARPE              : Minimum Sharpe ratio
  - MIN_WIN_RATE            : Minimum win rate %
"""

import json
import sys
import os
from pathlib import Path

# ── Thresholds ────────────────────────────────────────────────
MIN_MONTHLY_PROFIT_PCT = 3.0   # %  — must profit at least 3%/month
MAX_DRAWDOWN_PCT       = 20.0  # %  — drawdown cannot exceed 20%
MIN_TRADES             = 10    # count — need enough trades to be meaningful
MIN_SHARPE             = 0.5   # ratio — basic risk-adjusted return
MIN_WIN_RATE           = 40.0  # %  — at least 40% of trades profitable
# ──────────────────────────────────────────────────────────────


def load_backtest_results(filepath: str) -> dict:
    """Load and parse freqtrade backtest JSON results."""
    path = Path(filepath)
    if not path.exists():
        print(f"❌ ERROR: Backtest results file not found: {filepath}")
        print("   Make sure the backtest step ran successfully before validation.")
        sys.exit(1)

    with open(path) as f:
        data = json.load(f)

    # freqtrade wraps results under 'strategy' key
    if "strategy" in data:
        strategies = data["strategy"]
        strategy_name = list(strategies.keys())[0]
        print(f"📊 Validating strategy: {strategy_name}")
        return strategies[strategy_name]
    else:
        # older format — results at top level
        return data


def validate(results: dict) -> bool:
    """
    Run all threshold checks. Returns True if all pass, False otherwise.
    Prints a detailed report regardless.
    """
    passed = True
    checks = []

    # ── Extract key metrics ──────────────────────────────────
    total_profit_pct = results.get("profit_total_pct", 0) * 100
    max_drawdown_pct = abs(results.get("max_drawdown_account", 0) * 100)
    total_trades     = results.get("total_trades", 0)
    wins             = results.get("wins", 0)
    win_rate         = (wins / total_trades * 100) if total_trades > 0 else 0

    # Sharpe ratio
    sharpe = results.get("sharpe", None)

    # Calculate monthly profit from total profit and duration
    backtest_days = results.get("backtest_days", 60)
    months        = max(backtest_days / 30, 1)
    monthly_profit = total_profit_pct / months

    # ── Print summary ────────────────────────────────────────
    print("\n" + "="*55)
    print("  BACKTEST VALIDATION REPORT")
    print("="*55)
    print(f"  Period:          {backtest_days} days ({months:.1f} months)")
    print(f"  Total profit:    {total_profit_pct:.2f}%")
    print(f"  Monthly profit:  {monthly_profit:.2f}%")
    print(f"  Max drawdown:    {max_drawdown_pct:.2f}%")
    print(f"  Total trades:    {total_trades}")
    print(f"  Win rate:        {win_rate:.1f}%")
    print(f"  Sharpe ratio:    {sharpe if sharpe is not None else 'N/A'}")
    print("="*55)
    print("  THRESHOLD CHECKS")
    print("-"*55)

    # ── Check 1: Monthly profit ──────────────────────────────
    ok = monthly_profit >= MIN_MONTHLY_PROFIT_PCT
    status = "✅ PASS" if ok else "❌ FAIL"
    checks.append(ok)
    print(f"  {status}  Monthly profit: {monthly_profit:.2f}% "
          f"(min {MIN_MONTHLY_PROFIT_PCT}%)")
    if not ok:
        passed = False

    # ── Check 2: Max drawdown ────────────────────────────────
    ok = max_drawdown_pct <= MAX_DRAWDOWN_PCT
    status = "✅ PASS" if ok else "❌ FAIL"
    checks.append(ok)
    print(f"  {status}  Max drawdown:   {max_drawdown_pct:.2f}% "
          f"(max {MAX_DRAWDOWN_PCT}%)")
    if not ok:
        passed = False

    # ── Check 3: Trade count ─────────────────────────────────
    ok = total_trades >= MIN_TRADES
    status = "✅ PASS" if ok else "❌ FAIL"
    checks.append(ok)
    print(f"  {status}  Total trades:   {total_trades} "
          f"(min {MIN_TRADES})")
    if not ok:
        passed = False

    # ── Check 4: Win rate ────────────────────────────────────
    ok = win_rate >= MIN_WIN_RATE
    status = "✅ PASS" if ok else "❌ FAIL"
    checks.append(ok)
    print(f"  {status}  Win rate:       {win_rate:.1f}% "
          f"(min {MIN_WIN_RATE}%)")
    if not ok:
        passed = False

    # ── Check 5: Sharpe ratio (optional if available) ────────
    if sharpe is not None:
        ok = sharpe >= MIN_SHARPE
        status = "✅ PASS" if ok else "❌ FAIL"
        checks.append(ok)
        print(f"  {status}  Sharpe ratio:   {sharpe:.2f} "
              f"(min {MIN_SHARPE})")
        if not ok:
            passed = False
    else:
        print(f"  ⚠️  SKIP  Sharpe ratio:   not available in results")

    print("-"*55)

    # ── Final verdict ────────────────────────────────────────
    if passed:
        print("  🟢 VERDICT: ALL CHECKS PASSED — Deploy approved ✅")
    else:
        failed_count = sum(1 for c in checks if not c)
        print(f"  🔴 VERDICT: {failed_count} CHECK(S) FAILED — Deploy BLOCKED ❌")
        print()
        print("  Strategy does not meet minimum requirements.")
        print("  Review the results above and adjust the strategy before pushing again.")

    print("="*55 + "\n")
    return passed


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_backtest.py <path-to-backtest-results.json>")
        sys.exit(1)

    filepath = sys.argv[1]
    print(f"\n🔍 Loading backtest results from: {filepath}")

    results = load_backtest_results(filepath)
    passed  = validate(results)

    # Exit code 0 = pass (CI continues), 1 = fail (CI blocks deploy)
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
