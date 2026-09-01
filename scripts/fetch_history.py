#!/usr/bin/env python3
"""
One-time script: fetches monthly China fossil fuel import data 2020-2024
from UN ComTrade. Writes one CSV per commodity:
  data/fuel-imports/comtrade_coal.csv
  data/fuel-imports/comtrade_crude_oil.csv
  data/fuel-imports/comtrade_lng.csv
  data/fuel-imports/comtrade_pipeline_gas.csv

Each file: period, partner, value_usd_bn, qty_mt, value_per_mt_usd

Usage:
    export COMTRADE_PRIMARY_KEY=<key>
    python scripts/fetch_history.py
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

YEARS = ["2020", "2021", "2022", "2023", "2024"]
OUT_DIR = "data/fuel-imports"


def periods_for_year(year: str) -> str:
    return ",".join(f"{year}{m:02d}" for m in range(1, 13))


def fetch(cmd_code: str, year: str) -> pd.DataFrame:
    df = ct.getFinalData(
        subscription_key=KEY,
        typeCode="C",
        freqCode="M",
        clCode="HS",
        period=periods_for_year(year),
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


def main():
    print(f"[{datetime.utcnow():%Y-%m-%d %H:%M} UTC] Fetching ComTrade history 2020-2024...")

    frames = {name: [] for name in COMMODITIES.values()}

    for year in YEARS:
        print(f"\n  {year}:")
        for code, name in COMMODITIES.items():
            print(f"    {name} ({code})...", end=" ", flush=True)
            df = fetch(code, year)
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
            frames[name].append(
                df[["period", "partnerDesc", "value_usd_bn", "qty_mt", "value_per_mt_usd"]]
                .rename(columns={"partnerDesc": "partner"})
            )
            print(f"{len(df)} rows")

    os.makedirs(OUT_DIR, exist_ok=True)
    for name, parts in frames.items():
        if not parts:
            print(f"\n  {name}: no data — skipping")
            continue
        out = (
            pd.concat(parts, ignore_index=True)
            .sort_values(["period", "value_usd_bn"], ascending=[True, False])
            .reset_index(drop=True)
        )
        path = f"{OUT_DIR}/comtrade_{name}.csv"
        out.to_csv(path, index=False)
        print(f"\nWritten: {path} ({len(out)} rows)")


if __name__ == "__main__":
    main()
