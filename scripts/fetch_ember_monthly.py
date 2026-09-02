#!/usr/bin/env python3
"""
Monthly Ember updater for China electricity data.

Checks whether Ember has a period newer than what is already in
data/power/ember_power.csv. If yes: re-fetches and overwrites both
ember_power.csv and ember_capacity.csv, then signals new_data=true
so the workflow can commit and disable itself until next month.
If no new data: exits cleanly with new_data=false.

Called by .github/workflows/monthly_ember_update.yml (days 17-31).
Re-enabled on the 1st of each month by monthly_ember_reenable.yml.
"""

import os
import sys
from pathlib import Path

# Reuse build functions from the history script
sys.path.insert(0, str(Path(__file__).parent))
from fetch_ember_history import (
    build_power, build_capacity,
    POWER_FILE, CAPACITY_FILE, POWER_DIR,
)

import pandas as pd
from datetime import datetime


def github_output(key: str, value: str) -> None:
    output_file = os.environ.get("GITHUB_OUTPUT")
    if output_file:
        with open(output_file, "a") as f:
            f.write(f"{key}={value}\n")
    print(f"  → {key}={value}")


def main():
    print(f"[{datetime.now():%Y-%m-%d %H:%M}] Ember monthly check — China\n")

    # Current latest period in repo
    if POWER_FILE.exists():
        old = pd.read_csv(POWER_FILE, dtype=str)
        old_latest = old["period"].max() if not old.empty else "000000"
    else:
        old_latest = "000000"

    print(f"  CSV latest period  : {old_latest}")

    # Fetch fresh data from Ember
    print("\n  Fetching from Ember API ...")
    POWER_DIR.mkdir(parents=True, exist_ok=True)

    new_power = build_power()
    new_latest = new_power["period"].max() if not new_power.empty else "000000"
    print(f"  Ember latest period: {new_latest}")

    if new_latest <= old_latest:
        print("\n  No new data. Exiting.")
        github_output("new_data", "false")
        github_output("new_period", new_latest)
        return

    # New period found — write both CSVs
    print(f"\n  New period found: {new_latest}. Updating CSVs ...")
    new_power.to_csv(POWER_FILE, index=False)
    print(f"  Written: {POWER_FILE.name} ({len(new_power)} rows)")

    new_cap = build_capacity()
    if not new_cap.empty:
        new_cap.to_csv(CAPACITY_FILE, index=False)
        print(f"  Written: {CAPACITY_FILE.name} ({len(new_cap)} rows)")

    github_output("new_data", "true")
    github_output("new_period", new_latest)
    print(f"\n[{datetime.now():%Y-%m-%d %H:%M}] Done.")


if __name__ == "__main__":
    main()
