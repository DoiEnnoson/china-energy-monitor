#!/usr/bin/env python3
"""
One-time script: fetches complete Ember China electricity history and writes CSVs.

Outputs:
  data/power/ember_power.csv     — demand, generation by source (TWh + share),
                                   fossil/clean/renewables aggregates, carbon intensity
  data/power/ember_capacity.csv  — installed renewable capacity (solar, wind)

Coverage notes:
  Generation (monthly) : Coal, Gas, Nuclear, Hydro, Wind, Solar, Bioenergy,
                         Other fossil, Net imports — from 2015-01
  Capacity (monthly)   : Onshore wind, Offshore wind, Solar ONLY.
                         Ember does not provide monthly capacity for Coal, Gas,
                         Nuclear or Hydro via the installed-capacity endpoint.
  Emissions (monthly)  : NaN for recent months in the API — skipped here.
                         Use carbon_intensity_gco2_kwh as proxy instead.

Run via GitHub Actions (fetch_ember_history.yml) or locally:
    export EMBER_KEY=<key>
    python scripts/fetch_ember_history.py
"""

import os
import sys
import requests
import pandas as pd
from datetime import datetime
from pathlib import Path

API_KEY  = os.environ["EMBER_KEY"]
BASE_URL = "https://api.ember-energy.org/v1"
CHINA    = "CHN"

REPO_DIR      = Path(__file__).resolve().parent.parent
POWER_DIR     = REPO_DIR / "data" / "power"
POWER_FILE    = POWER_DIR / "ember_power.csv"
CAPACITY_FILE = POWER_DIR / "ember_capacity.csv"

SESSION = requests.Session()
SESSION.headers.update({"Accept": "application/json"})


def fetch(endpoint: str, resolution: str, **extra) -> pd.DataFrame:
    params = {"entity_code": CHINA, "limit": 5000, "api_key": API_KEY, **extra}
    r = SESSION.get(f"{BASE_URL}/{endpoint}/{resolution}", params=params, timeout=30)
    r.raise_for_status()
    data = r.json().get("data", [])
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)


def to_period(date_str: str) -> str:
    return str(date_str)[:7].replace("-", "")


SERIES_SLUG = {
    "Bioenergy":    "bioenergy",
    "Coal":         "coal",
    "Gas":          "gas",
    "Hydro":        "hydro",
    "Net imports":  "net_imports",
    "Nuclear":      "nuclear",
    "Other fossil": "other_fossil",
    "Solar":        "solar",
    "Wind":         "wind",
}

CAPACITY_SLUG = {
    "Offshore wind": "offshore_wind",
    "Onshore wind":  "onshore_wind",
    "Solar":         "solar",
}

FOSSIL_SOURCES    = ["coal", "gas", "other_fossil"]
RENEWABLE_SOURCES = ["hydro", "wind", "solar", "bioenergy"]
CLEAN_SOURCES     = RENEWABLE_SOURCES + ["nuclear"]


def safe_sum(df: pd.DataFrame, cols: list[str]) -> pd.Series:
    present = [c for c in cols if c in df.columns]
    if not present:
        return pd.Series([None] * len(df), index=df.index)
    return (
        df[present]
        .sum(axis=1, skipna=True)
        .where(df[present].notna().any(axis=1))
        .round(2)
    )


def build_power() -> pd.DataFrame:
    print("  generation/monthly ...", end=" ", flush=True)
    gen_raw = fetch("electricity-generation", "monthly", is_aggregate_series="false")
    print(f"{len(gen_raw)} rows")

    print("  demand/monthly       ...", end=" ", flush=True)
    dem_raw = fetch("electricity-demand", "monthly")
    print(f"{len(dem_raw)} rows")

    print("  carbon-intensity/monthly ...", end=" ", flush=True)
    ci_raw = fetch("carbon-intensity", "monthly")
    print(f"{len(ci_raw)} rows")

    # ── Generation: long → wide ───────────────────────────────────────────────
    gen = gen_raw.copy()
    gen["period"] = gen["date"].astype(str).apply(to_period)
    gen["slug"]   = gen["series"].map(SERIES_SLUG)
    gen = gen.dropna(subset=["slug"])

    twh   = gen.pivot(index="period", columns="slug", values="generation_twh")
    share = gen.pivot(index="period", columns="slug", values="share_of_generation_pct")
    twh.columns   = [f"{c}_twh"       for c in twh.columns]
    share.columns = [f"{c}_share_pct" for c in share.columns]
    wide = pd.concat([twh, share], axis=1).reset_index()

    # ── Demand ────────────────────────────────────────────────────────────────
    if not dem_raw.empty:
        dem = dem_raw.copy()
        dem["period"] = dem["date"].astype(str).apply(to_period)
        dem = dem[["period", "demand_twh"]].drop_duplicates("period")
        wide = wide.merge(dem, on="period", how="left")

    # ── Carbon intensity ──────────────────────────────────────────────────────
    if not ci_raw.empty:
        ci = ci_raw.copy()
        ci["period"] = ci["date"].astype(str).apply(to_period)
        ci = ci[["period", "emissions_intensity_gco2_per_kwh"]].drop_duplicates("period")
        ci = ci.rename(columns={"emissions_intensity_gco2_per_kwh": "carbon_intensity_gco2_kwh"})
        wide = wide.merge(ci, on="period", how="left")

    # ── Aggregates ────────────────────────────────────────────────────────────
    wide["fossil_twh"]           = safe_sum(wide, [f"{s}_twh"       for s in FOSSIL_SOURCES])
    wide["fossil_share_pct"]     = safe_sum(wide, [f"{s}_share_pct" for s in FOSSIL_SOURCES])
    wide["clean_twh"]            = safe_sum(wide, [f"{s}_twh"       for s in CLEAN_SOURCES])
    wide["clean_share_pct"]      = safe_sum(wide, [f"{s}_share_pct" for s in CLEAN_SOURCES])
    wide["renewables_twh"]       = safe_sum(wide, [f"{s}_twh"       for s in RENEWABLE_SOURCES])
    wide["renewables_share_pct"] = safe_sum(wide, [f"{s}_share_pct" for s in RENEWABLE_SOURCES])

    # ── Column order ──────────────────────────────────────────────────────────
    src_order = ["coal", "gas", "nuclear", "hydro", "wind", "solar",
                 "bioenergy", "other_fossil", "net_imports"]
    src_cols  = []
    for s in src_order:
        for sfx in ["_twh", "_share_pct"]:
            c = f"{s}{sfx}"
            if c in wide.columns:
                src_cols.append(c)

    agg_cols = ["fossil_twh", "fossil_share_pct",
                "clean_twh",  "clean_share_pct",
                "renewables_twh", "renewables_share_pct"]
    tail_cols = ["carbon_intensity_gco2_kwh"]

    final = (["period", "demand_twh"] + src_cols + agg_cols +
             [c for c in tail_cols if c in wide.columns])

    return wide[final].sort_values("period").reset_index(drop=True)


def build_capacity() -> pd.DataFrame:
    print("  installed-capacity/monthly ...", end=" ", flush=True)
    cap_raw = fetch("installed-capacity", "monthly", is_aggregate_series="false")
    print(f"{len(cap_raw)} rows")

    if cap_raw.empty:
        return pd.DataFrame()

    cap = cap_raw.copy()
    cap["period"] = cap["date"].astype(str).apply(to_period)
    cap["slug"]   = cap["series"].map(CAPACITY_SLUG)
    cap = cap.dropna(subset=["slug"])

    wide = cap.pivot(index="period", columns="slug", values="capacity_gw").reset_index()
    wide.columns.name = None

    if "onshore_wind" in wide.columns and "offshore_wind" in wide.columns:
        wide["wind_gw"] = (wide["onshore_wind"].fillna(0) +
                           wide["offshore_wind"].fillna(0)).round(2)

    rename = {s: f"{s}_gw" for s in ["onshore_wind", "offshore_wind", "solar"]
              if s in wide.columns}
    wide = wide.rename(columns=rename)

    ordered = ["period", "onshore_wind_gw", "offshore_wind_gw", "wind_gw", "solar_gw"]
    ordered = [c for c in ordered if c in wide.columns]

    return wide[ordered].sort_values("period").reset_index(drop=True)


def main():
    print(f"[{datetime.now():%Y-%m-%d %H:%M}] Ember history — China (CHN)\n")
    POWER_DIR.mkdir(parents=True, exist_ok=True)

    print("── ember_power.csv ──────────────────────────────────────────")
    power = build_power()
    power.to_csv(POWER_FILE, index=False)
    print(f"  → {POWER_FILE.name}: {len(power)} rows × {len(power.columns)} cols")
    print(f"    period range: {power['period'].min()} – {power['period'].max()}")

    print("\n── ember_capacity.csv ───────────────────────────────────────")
    print("  NOTE: Ember API provides capacity only for Solar, Onshore Wind,")
    print("        Offshore Wind. Coal/Gas/Nuclear/Hydro not available here.")
    cap = build_capacity()
    if not cap.empty:
        cap.to_csv(CAPACITY_FILE, index=False)
        print(f"  → {CAPACITY_FILE.name}: {len(cap)} rows × {len(cap.columns)} cols")
        print(f"    period range: {cap['period'].min()} – {cap['period'].max()}")
    else:
        print("  No data returned.")

    print(f"\n[{datetime.now():%Y-%m-%d %H:%M}] Done.")


if __name__ == "__main__":
    main()
