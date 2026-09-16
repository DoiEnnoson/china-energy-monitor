#!/usr/bin/env python3
"""
Monthly updater: pulls China passenger-car sales data from LeRaffl Gallery
and appends new rows to the local CSVs.

Sources (LeRaffl / CPCA):
  https://raw.githubusercontent.com/LeRaffl/LeRaffl-Gallery/master/data/China.csv
  https://raw.githubusercontent.com/LeRaffl/LeRaffl-Gallery/master/data/China_Wholesale.csv

Targets:
  data/transport/china_car_sales_retail.csv
  data/transport/china_car_sales_wholesale.csv

Logic:
  - Download remote CSV
  - Compare latest period to local latest period
  - If remote has newer rows: append and save
  - If already up to date: exit without changes (no git diff, no commit)

Run via GitHub Actions: daily from the 8th of each month.
"""

import os
import sys
from io import StringIO

import pandas as pd
import requests

SOURCES = {
    "retail": {
        "url": "https://raw.githubusercontent.com/LeRaffl/LeRaffl-Gallery/master/data/China.csv",
        "local": "data/transport/china_car_sales_retail.csv",
    },
    "wholesale": {
        "url": "https://raw.githubusercontent.com/LeRaffl/LeRaffl-Gallery/master/data/China_Wholesale.csv",
        "local": "data/transport/china_car_sales_wholesale.csv",
    },
}


def fetch_remote(url: str) -> pd.DataFrame:
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return pd.read_csv(StringIO(resp.text))


def update(name: str, url: str, local_path: str) -> bool:
    print(f"\n[{name}]")

    remote = fetch_remote(url)
    remote_latest = remote["period"].max()
    print(f"  Remote latest: {remote_latest}  ({len(remote)} rows)")

    local = pd.read_csv(local_path)
    local_latest = local["period"].max()
    print(f"  Local latest:  {local_latest}  ({len(local)} rows)")

    if remote_latest <= local_latest:
        print("  No new data — skipping.")
        return False

    new_rows = remote[remote["period"] > local_latest].copy()
    print(f"  New rows: {len(new_rows)}  (through {remote_latest})")

    updated = pd.concat([local, new_rows], ignore_index=True)
    updated.to_csv(local_path, index=False)
    print(f"  Written: {local_path}")
    return True


def main():
    any_updated = False
    for name, cfg in SOURCES.items():
        try:
            updated = update(name, cfg["url"], cfg["local"])
            if updated:
                any_updated = True
        except Exception as exc:
            print(f"  ERROR ({name}): {exc}", file=sys.stderr)
            sys.exit(1)

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"updated={'true' if any_updated else 'false'}\n")

    if any_updated:
        print("\nDone: new data written.")
    else:
        print("\nDone: already up to date.")


if __name__ == "__main__":
    main()
