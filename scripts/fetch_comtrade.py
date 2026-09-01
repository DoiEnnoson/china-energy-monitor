#!/usr/bin/env python3
"""
Fetches monthly China fossil fuel import data from UN ComTrade for 2025.
Commodities: Coal (2701), Crude Oil (2709), LNG (271111), Pipeline Gas (271121).
Fields: partner, quantity (Mt), value (bn USD), value per tonne (USD/t).
Always overwrites data/fuel-imports/comtrade_2025.csv.

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
OUT_PATH = "data/fuel-imports/comtrade_2025.csv"


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


def main():
    print(f"[{datetime.utcnow():%Y-%m-%d %H:%M} UTC] Fetching ComTrade data for {YEAR}...")

    frames = []
    for code, name in COMMODITIES.items():
        print(f"  {name} ({code})...", end=" ", flush=True)
        df = fetch(code)
        if df.empty:
            print("no data")
            continue

        df = df[df["partnerDesc"] != "World"].copy()
        df["commodity"] = name
        df["commodity_code"] = code
        df["value_usd_bn"] = (df["primaryValue"] / 1e9).round(4)
        df["qty_mt"] = (df["netWgt"] / 1e9).round(4)
        df["value_per_mt_usd"] = (
            (df["primaryValue"] / (df["netWgt"] / 1000))
            .where(df["netWgt"] > 0)
            .round(2)
        )
        frames.append(
            df[["period", "commodity", "commodity_code",
                "partnerDesc", "value_usd_bn", "qty_mt", "value_per_mt_usd"]]
            .rename(columns={"partnerDesc": "partner"})
        )
        periods_found = sorted(df["period"].unique())
        print(f"{len(df)} rows — periods: {', '.join(str(p) for p in periods_found)}")

    if not frames:
        print("No 2025 data available yet. Exiting without writing.")
        sys.exit(0)

    result = (
        pd.concat(frames, ignore_index=True)
        .sort_values(
            ["period", "commodity", "value_usd_bn"],
            ascending=[True, True, False],
        )
        .reset_index(drop=True)
    )

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    result.to_csv(OUT_PATH, index=False)
    print(f"\nWritten: {OUT_PATH} ({len(result)} rows, {result['period'].nunique()} periods)")


if __name__ == "__main__":
    main()
