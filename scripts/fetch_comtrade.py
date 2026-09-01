#!/usr/bin/env python3
"""
Monthly GitHub Actions script: fetches China fossil fuel import data for 2025
from UN ComTrade and upserts into the commodity CSVs:
  data/fuel-imports/comtrade_coal.csv
  data/fuel-imports/comtrade_crude_oil.csv
  data/fuel-imports/comtrade_lng.csv
  data/fuel-imports/comtrade_pipeline_gas.csv

Each file: period, partner, value_usd_bn, qty_mt, value_per_mt_usd
2025 rows are replaced in full on each run (idempotent).

Usage:
    export COMTRADE_PRIMARY_KEY=<key>
    python scripts/fetch_comtrade.py
"""

import os
import sys
import comtradeapicall as ct
import pandas as pd
from datetime import datetime

KEY = os.environ["COMTRADE_PRIMARY_KEY"]

COMMODITIES = {
    "2701":   "coal",
    "2709":   "crude_oil",
    "271111": "lng",
    "271121": "pipeline_gas",
}

YEAR = "2025"
PERIODS = ",".join(f"{YEAR}{m:02d}" for m in range(1, 13))
OUT_DIR = "data/fuel-imports"


def fetch(cmd_code: str) -> pd.DataFrame:
    df = ct.getFinalData(
        subscription_key=KEY,
        typeCode="C",
        freqCode="M",
        clCode="HS",
        period=PERIODS,
        reporterCode="156",
        cmdCode=cmd_code,
        flowCode="M",
        partnerCode=None,
        partner2Code="0",
        customsCode="C00",
        motCode="0",
        maxRecords=5000,
        includeDesc=True,
    )
    return df if df is not None and not df.empty else pd.DataFrame()


def upsert_year(path: str, new_rows: pd.DataFrame, year: str) -> pd.DataFrame:
    if os.path.exists(path):
        existing = pd.read_csv(path, dtype={"period": str})
        existing = existing[~existing["period"].str.startswith(year)]
    else:
        existing = pd.DataFrame(columns=new_rows.columns)
    return (
        pd.concat([existing, new_rows], ignore_index=True)
        .sort_values(["period", "value_usd_bn"], ascending=[True, False])
        .reset_index(drop=True)
    )


def main():
    print(f"[{datetime.utcnow():%Y-%m-%d %H:%M} UTC] Fetching ComTrade data for {YEAR}...")

    any_data = False
    os.makedirs(OUT_DIR, exist_ok=True)

    for code, name in COMMODITIES.items():
        print(f"  {name} ({code})...", end=" ", flush=True)
        df = fetch(code)
        if df.empty:
            print("no data")
            continue

        df = df[df["partnerDesc"] != "World"].copy()
        df["value_usd_bn"] = (df["primaryValue"] / 1e9).round(4)
        df["qty_mt"] = (df["netWgt"] / 1e9).round(4)
        df["value_per_mt_usd"] = (
            (df["primaryValue"] / (df["netWgt"] / 1000))
            .where(df["netWgt"] > 0)
            .round(2)
        )
        new_rows = (
            df[["period", "partnerDesc", "value_usd_bn", "qty_mt", "value_per_mt_usd"]]
            .rename(columns={"partnerDesc": "partner"})
        )
        periods_found = sorted(df["period"].unique())
        print(f"{len(df)} rows — periods: {', '.join(str(p) for p in periods_found)}")

        path = f"{OUT_DIR}/comtrade_{name}.csv"
        result = upsert_year(path, new_rows, YEAR)
        result.to_csv(path, index=False)
        any_data = True

    if not any_data:
        print("No 2025 data available yet. Exiting without writing.")
        sys.exit(0)


if __name__ == "__main__":
    main()
