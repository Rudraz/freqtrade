#!/usr/bin/env python3
"""
Apply hyperopt best params to the strategy file.
Injects optimised ROI table, stoploss, and buy/sell parameter values
as a comment block so the CI can track what changed and when.
"""

import json
import sys
import re
from pathlib import Path
from datetime import date


def main():
    if len(sys.argv) < 3:
        print("Usage: apply_hyperopt_params.py <best_params.json> <strategy.py>")
        sys.exit(1)

    params_path   = Path(sys.argv[1])
    strategy_path = Path(sys.argv[2])

    if not params_path.exists():
        print(f"❌ Params file not found: {params_path}")
        sys.exit(1)

    if not strategy_path.exists():
        print(f"❌ Strategy file not found: {strategy_path}")
        sys.exit(1)

    with open(params_path) as f:
        data = json.load(f)

    if not data:
        print("❌ Empty params file — nothing to apply")
        sys.exit(1)

    details = data.get("params_details", {})
    roi     = details.get("roi", None)
    sl      = details.get("stoploss", {}).get("stoploss", None)
    source  = strategy_path.read_text()

    today = date.today().isoformat()
    changed = False

    # Update minimal_roi
    if roi:
        roi_dict = {str(int(k)): round(v, 5) for k, v in roi.items()}
        roi_str  = json.dumps(roi_dict, separators=(", ", ": ")).replace('"', '"')
        new_roi  = f'    minimal_roi = {json.dumps(roi_dict)}'
        source, n = re.subn(r'    minimal_roi\s*=\s*\{[^}]*\}', new_roi, source)
        if n:
            print(f"✅ Updated minimal_roi: {roi_dict}")
            changed = True

    # Update stoploss (hard floor: never below -0.03)
    if sl is not None:
        sl_value = max(float(sl), -0.03)
        new_sl   = f"    stoploss = {sl_value}"
        source, n = re.subn(r'    stoploss\s*=\s*-?\d+\.\d+', new_sl, source)
        if n:
            print(f"✅ Updated stoploss: {sl_value}")
            changed = True

    # Inject/update hyperopt timestamp comment
    stamp = f"    # Hyperopt: {today} — auto-applied by CI"
    if "# Hyperopt:" in source:
        source = re.sub(r'    # Hyperopt: .*', stamp, source)
    else:
        source = source.replace("class MeanReversionMomentum(IStrategy):",
                                f"class MeanReversionMomentum(IStrategy):\n{stamp}")
    changed = True

    if changed:
        strategy_path.write_text(source)
        print(f"✅ Strategy updated: {strategy_path}")
    else:
        print("⚠️  No changes applied (ROI/stoploss not found in params)")


if __name__ == "__main__":
    main()
