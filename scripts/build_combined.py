#!/usr/bin/env python3
"""
Build combined partner-level fuel import CSVs from ComTrade and GACC.

ComTrade takes priority: for any (period, partner) pair present in ComTrade,
the ComTrade values are used. GACC fills all periods not covered by ComTrade
(i.e. 2025 onwards until ComTrade catches up).

Output: data/combined/combined_{coal,crude_oil,lng,pipeline_gas}.csv
Schema: period, partner, value_usd_bn, qty_mt, value_per_mt_usd, source

Run locally:
    python scripts/build_combined.py

Triggered automatically by build_combined.yml on push to data/fuel-imports/.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

REPO_DIR  = Path(__file__).resolve().parent.parent
FUEL_DIR  = REPO_DIR / "data" / "fuel-imports"
OUT_DIR   = REPO_DIR / "data" / "combined"

COMMODITIES = ["coal", "crude_oil", "lng", "pipeline_gas"]


def load(path: Path, source: str) -> pd.DataFrame:
    df = pd.read_csv(path, dtype={"period": str})
    df["source"] = source
    for col in ["qty_mt", "value_per_mt_usd"]:
        if col not in df.columns:
            df[col] = None
    return df[["period", "partner", "value_usd_bn", "qty_mt", "value_per_mt_usd", "source"]]


def build(commodity: str) -> pd.DataFrame:
    ct_path   = FUEL_DIR / f"comtrade_{commodity}.csv"
    gacc_path = FUEL_DIR / f"gacc_{commodity}.csv"

    ct   = load(ct_path,   "comtrade") if ct_path.exists()   else pd.DataFrame()
    gacc = load(gacc_path, "gacc")     if gacc_path.exists() else pd.DataFrame()

    if ct.empty and gacc.empty:
        return pd.DataFrame()

    if ct.empty:
        return gacc.sort_values(["period", "value_usd_bn"], ascending=[True, False]).reset_index(drop=True)

    if gacc.empty:
        return ct.sort_values(["period", "value_usd_bn"], ascending=[True, False]).reset_index(drop=True)

    # ComTrade takes priority: drop GACC rows for periods already in ComTrade
    ct_periods  = set(ct["period"].unique())
    gacc_fill   = gacc[~gacc["period"].isin(ct_periods)]

    combined = (
        pd.concat([ct, gacc_fill], ignore_index=True)
        .sort_values(["period", "value_usd_bn"], ascending=[True, False])
        .reset_index(drop=True)
    )
    return combined


def main():
    print(f"[{datetime.now():%Y-%m-%d %H:%M}] Building combined fuel import CSVs\n")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for commodity in COMMODITIES:
        df = build(commodity)
        if df.empty:
            print(f"  {commodity}: no source data found — skipped")
            continue
        out = OUT_DIR / f"combined_{commodity}.csv"
        df.to_csv(out, index=False)
        periods = sorted(df["period"].unique())
        ct_rows   = len(df[df["source"] == "comtrade"])
        gacc_rows = len(df[df["source"] == "gacc"])
        print(f"  {commodity}: {len(df)} rows — {periods[0]}–{periods[-1]} "
              f"(comtrade: {ct_rows}, gacc: {gacc_rows})")

    print(f"\n[{datetime.now():%Y-%m-%d %H:%M}] Done.")


if __name__ == "__main__":
    main()
