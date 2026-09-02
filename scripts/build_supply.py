#!/usr/bin/env python3
"""
Build fossil_supply.csv: combines GACC fuel imports with NBS domestic production.

Per commodity (coal, crude oil, gas) and month:
  - import, production, combined total
  - YoY% for each component and the combined total (back-calculated from individual YoY figures)
  - cumulative YTD total and YTD YoY%

Gas unit convention:
  All gas figures are in BCM throughout.
  GACC imports (Mt) are converted via 1 Mt ≈ 1.36 BCM (GIIGNL standard for LNG;
  applied uniformly across LNG + pipeline since GACC combines both in mass units).
  The original gas_import_mt column is preserved for reference.

Jan-Feb convention: period 202601 = combined two-month value (NBS/GACC convention).
  The YTD cumulative correctly counts this as 2 months of data.

Output: data/combined/fossil_supply.csv

Triggered automatically by build_supply.yml when either source CSV changes.
Can also be run locally:
    python scripts/build_supply.py
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

REPO_DIR     = Path(__file__).resolve().parent.parent
DATA_DIR     = REPO_DIR / "data"
IMPORTS_FILE = DATA_DIR / "fuel-imports" / "gacc_imports.csv"
PROD_FILE    = DATA_DIR / "production"   / "nbs_production.csv"
OUTPUT_DIR   = DATA_DIR / "combined"
OUTPUT_FILE  = OUTPUT_DIR / "fossil_supply.csv"

# GIIGNL standard: 1 Mt LNG ≈ 1.36 BCM natural gas
MT_TO_BCM = 1.36


def yoy(current: pd.Series, prior: pd.Series) -> pd.Series:
    return ((current - prior) / prior.abs() * 100).round(1).where(prior.notna() & (prior != 0))


def prior_year(current: pd.Series, yoy_pct: pd.Series) -> pd.Series:
    factor = 1 + yoy_pct / 100
    return (current / factor).where(factor.abs() > 1e-9).round(4)


def main():
    print(f"[{datetime.now():%Y-%m-%d %H:%M}] Building fossil_supply.csv\n")

    imp  = pd.read_csv(IMPORTS_FILE)
    prod = pd.read_csv(PROD_FILE)

    # ── Rename to avoid collision after merge ─────────────────────────────────
    imp = imp[["period",
               "coal_mt",        "coal_mt_yoy_pct",
               "crude_oil_mt",   "crude_oil_mt_yoy_pct",
               "gas_mt",         "gas_mt_yoy_pct"]].rename(columns={
        "coal_mt":               "coal_import_mt",
        "coal_mt_yoy_pct":       "coal_import_yoy_pct",
        "crude_oil_mt":          "crude_oil_import_mt",
        "crude_oil_mt_yoy_pct":  "crude_oil_import_yoy_pct",
        "gas_mt":                "gas_import_mt",
        "gas_mt_yoy_pct":        "gas_import_yoy_pct",
    })

    prod = prod[["period",
                 "coal_mt",       "coal_mt_yoy_pct",
                 "crude_oil_mt",  "crude_oil_mt_yoy_pct",
                 "gas_bcm",       "gas_bcm_yoy_pct"]].rename(columns={
        "coal_mt":              "coal_prod_mt",
        "coal_mt_yoy_pct":      "coal_prod_yoy_pct",
        "crude_oil_mt":         "crude_oil_prod_mt",
        "crude_oil_mt_yoy_pct": "crude_oil_prod_yoy_pct",
        "gas_bcm":              "gas_prod_bcm",
        "gas_bcm_yoy_pct":      "gas_prod_yoy_pct",
    })

    df = imp.merge(prod, on="period").sort_values("period").reset_index(drop=True)

    # ── Gas: convert imports Mt → BCM ─────────────────────────────────────────
    df["gas_import_bcm"] = (df["gas_import_mt"] * MT_TO_BCM).round(2)

    # ── Monthly totals ────────────────────────────────────────────────────────
    df["coal_total_mt"]      = (df["coal_import_mt"]      + df["coal_prod_mt"]).round(2)
    df["crude_oil_total_mt"] = (df["crude_oil_import_mt"] + df["crude_oil_prod_mt"]).round(2)
    df["gas_total_bcm"]      = (df["gas_import_bcm"]      + df["gas_prod_bcm"]).round(2)

    # ── Back-calculate 2025 values ────────────────────────────────────────────
    coal_imp_25   = prior_year(df["coal_import_mt"],      df["coal_import_yoy_pct"])
    coal_prod_25  = prior_year(df["coal_prod_mt"],        df["coal_prod_yoy_pct"])
    coal_total_25 = (coal_imp_25 + coal_prod_25).round(2)

    oil_imp_25    = prior_year(df["crude_oil_import_mt"], df["crude_oil_import_yoy_pct"])
    oil_prod_25   = prior_year(df["crude_oil_prod_mt"],   df["crude_oil_prod_yoy_pct"])
    oil_total_25  = (oil_imp_25 + oil_prod_25).round(2)

    gas_imp_25_mt  = prior_year(df["gas_import_mt"],      df["gas_import_yoy_pct"])
    gas_imp_25_bcm = (gas_imp_25_mt * MT_TO_BCM).round(2)
    gas_prod_25    = prior_year(df["gas_prod_bcm"],        df["gas_prod_yoy_pct"])
    gas_total_25   = (gas_imp_25_bcm + gas_prod_25).round(2)

    # ── Monthly YoY for combined totals ───────────────────────────────────────
    df["coal_total_yoy_pct"]      = yoy(df["coal_total_mt"],      coal_total_25)
    df["crude_oil_total_yoy_pct"] = yoy(df["crude_oil_total_mt"], oil_total_25)
    df["gas_total_yoy_pct"]       = yoy(df["gas_total_bcm"],      gas_total_25)

    # ── YTD cumulative within calendar year ───────────────────────────────────
    df["year"] = df["period"].astype(str).str[:4]

    # Store 2025 back-calc totals as temp columns for grouped cumsum
    df["_coal_total_25"]  = coal_total_25
    df["_oil_total_25"]   = oil_total_25
    df["_gas_total_25"]   = gas_total_25

    df["coal_ytd_mt"]      = df.groupby("year")["coal_total_mt"].cumsum().round(2)
    df["crude_oil_ytd_mt"] = df.groupby("year")["crude_oil_total_mt"].cumsum().round(2)
    df["gas_ytd_bcm"]      = df.groupby("year")["gas_total_bcm"].cumsum().round(2)

    coal_ytd_25  = df.groupby("year")["_coal_total_25"].cumsum().round(2)
    oil_ytd_25   = df.groupby("year")["_oil_total_25"].cumsum().round(2)
    gas_ytd_25   = df.groupby("year")["_gas_total_25"].cumsum().round(2)

    df["coal_ytd_yoy_pct"]      = yoy(df["coal_ytd_mt"],      coal_ytd_25)
    df["crude_oil_ytd_yoy_pct"] = yoy(df["crude_oil_ytd_mt"], oil_ytd_25)
    df["gas_ytd_yoy_pct"]       = yoy(df["gas_ytd_bcm"],      gas_ytd_25)

    # ── Column order ──────────────────────────────────────────────────────────
    out_cols = [
        "period",
        "coal_import_mt",        "coal_prod_mt",        "coal_total_mt",
        "coal_import_yoy_pct",   "coal_prod_yoy_pct",   "coal_total_yoy_pct",
        "coal_ytd_mt",           "coal_ytd_yoy_pct",
        "crude_oil_import_mt",        "crude_oil_prod_mt",        "crude_oil_total_mt",
        "crude_oil_import_yoy_pct",   "crude_oil_prod_yoy_pct",   "crude_oil_total_yoy_pct",
        "crude_oil_ytd_mt",           "crude_oil_ytd_yoy_pct",
        "gas_import_mt",    "gas_import_bcm",   "gas_prod_bcm",   "gas_total_bcm",
        "gas_import_yoy_pct",   "gas_prod_yoy_pct",   "gas_total_yoy_pct",
        "gas_ytd_bcm",          "gas_ytd_yoy_pct",
    ]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df[out_cols].to_csv(OUTPUT_FILE, index=False)

    print(f"  Written : {OUTPUT_FILE.relative_to(REPO_DIR)}")
    print(f"  Rows    : {len(df)}  Cols: {len(out_cols)}")
    print(f"  Periods : {df['period'].min()} – {df['period'].max()}")
    print(f"\n[{datetime.now():%Y-%m-%d %H:%M}] Done.")


if __name__ == "__main__":
    main()
