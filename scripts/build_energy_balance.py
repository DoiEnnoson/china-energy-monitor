#!/usr/bin/env python3
"""
Build energy_balance.csv: total primary energy supply in TWh.

Combines fossil fuel supply (coal, crude oil, gas; imports + domestic production)
with clean electricity generation (nuclear, hydro, wind, solar, bioenergy from Ember)
into a unified monthly energy balance.

Fossil fuels are converted to TWh using IEA/BP Statistical Review conversion factors:
  Coal:      1 Mt  →  8.14 TWh   (29.3 GJ/t, standard coal equivalent, tce)
  Crude oil: 1 Mt  → 11.63 TWh   (41.87 GJ/t, tonne of oil equivalent, toe)
  Gas:       1 BCM → 10.55 TWh   (38 GJ/1000 m³, gross calorific value)
Source: BP Statistical Review of World Energy, Annex: Conversion Factors.

Clean electricity (nuclear, hydro, wind, solar, bioenergy) is taken from Ember at
face value (TWh generated). Coal and gas power generation are EXCLUDED to avoid
double-counting with the fossil fuel supply figures.

Methodological note: Fossil fuel figures represent PRIMARY energy (heat content of
the fuel before conversion losses). Clean electricity is FINAL energy (electricity
output). Adding both gives a proxy for "total energy entering the Chinese energy
system" — commonly used in journalistic energy balance analyses.

Jan-Feb convention: fossil_supply.csv period 202601 = combined Jan+Feb.
Corresponding Ember periods (202601 + 202602) are summed accordingly.

Inputs:  data/combined/fossil_supply.csv
         data/power/ember_power.csv
Output:  data/combined/energy_balance.csv
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

REPO_DIR    = Path(__file__).resolve().parent.parent
DATA_DIR    = REPO_DIR / "data"
SUPPLY_FILE = DATA_DIR / "combined" / "fossil_supply.csv"
EMBER_FILE  = DATA_DIR / "power"    / "ember_power.csv"
OUTPUT_DIR  = DATA_DIR / "combined"
OUTPUT_FILE = OUTPUT_DIR / "energy_balance.csv"

# BP Statistical Review of World Energy — Conversion Factors
COAL_TWH_PER_MT  = 8.14   # 29.3 GJ/t (tce)
OIL_TWH_PER_MT   = 11.63  # 41.87 GJ/t (toe)
GAS_TWH_PER_BCM  = 10.55  # 38 GJ/1000 m³

# From Ember, these sources are added at face value (ex coal, gas, other_fossil)
CLEAN_SOURCES = ["nuclear", "hydro", "wind", "solar", "bioenergy"]


def prior_val(current: float, yoy_pct: float) -> float | None:
    if pd.isna(current) or pd.isna(yoy_pct):
        return None
    f = 1 + yoy_pct / 100
    return current / f if abs(f) > 1e-9 else None


def yoy_series(cur: pd.Series, pri: pd.Series) -> pd.Series:
    return ((cur - pri) / pri.abs() * 100).round(1).where(pri.notna() & (pri != 0))


def ember_sum(ember: pd.DataFrame, periods: list[str]) -> dict:
    """Sum Ember clean-source TWh for a list of periods (handles Jan-Feb merge)."""
    rows = ember[ember["period"].isin(periods)]
    if rows.empty:
        return {}
    result = {}
    for s in CLEAN_SOURCES:
        col = f"{s}_twh"
        if col in rows.columns:
            result[col] = round(float(rows[col].sum()), 1)
    result["clean_power_twh"] = round(sum(result.values()), 1)
    return result


def ember_periods_for(supply_period: str) -> list[str]:
    return ["202601", "202602"] if supply_period == "202601" else [supply_period]


def prior_ember_periods(supply_period: str) -> list[str]:
    year = str(int(supply_period[:4]) - 1)
    return [f"{year}01", f"{year}02"] if supply_period == "202601" \
           else [f"{year}{supply_period[4:]}"]


def main():
    print(f"[{datetime.now():%Y-%m-%d %H:%M}] Building energy_balance.csv\n")

    if not SUPPLY_FILE.exists():
        print(f"  ERROR: {SUPPLY_FILE} not found. Run build_supply.py first.")
        raise SystemExit(1)
    if not EMBER_FILE.exists():
        print(f"  ERROR: {EMBER_FILE} not found. Run fetch_ember_history.py first.")
        raise SystemExit(1)

    supply = pd.read_csv(SUPPLY_FILE, dtype={"period": str})
    ember  = pd.read_csv(EMBER_FILE,  dtype={"period": str})

    rows_out = []

    for _, row in supply.iterrows():
        period = str(row["period"])

        # ── Fossil supply → TWh ───────────────────────────────────────────────
        coal_imp_twh  = round(row["coal_import_mt"]       * COAL_TWH_PER_MT, 1)
        coal_prod_twh = round(row["coal_prod_mt"]         * COAL_TWH_PER_MT, 1)
        coal_twh      = round(row["coal_total_mt"]        * COAL_TWH_PER_MT, 1)

        oil_imp_twh   = round(row["crude_oil_import_mt"]  * OIL_TWH_PER_MT,  1)
        oil_prod_twh  = round(row["crude_oil_prod_mt"]    * OIL_TWH_PER_MT,  1)
        oil_twh       = round(row["crude_oil_total_mt"]   * OIL_TWH_PER_MT,  1)

        gas_imp_twh   = round(row["gas_import_bcm"]       * GAS_TWH_PER_BCM, 1)
        gas_prod_twh  = round(row["gas_prod_bcm"]         * GAS_TWH_PER_BCM, 1)
        gas_twh       = round(row["gas_total_bcm"]        * GAS_TWH_PER_BCM, 1)

        fossil_twh    = round(coal_twh + oil_twh + gas_twh, 1)

        # ── Clean power from Ember ────────────────────────────────────────────
        now_em    = ember_sum(ember, ember_periods_for(period))
        prior_em  = ember_sum(ember, prior_ember_periods(period))

        clean_twh       = now_em.get("clean_power_twh")
        clean_prior_twh = prior_em.get("clean_power_twh")

        # ── System total ──────────────────────────────────────────────────────
        total_twh = round(fossil_twh + clean_twh, 1) if clean_twh is not None else None

        # ── 2025 back-calc for fossil aggregate YoY ───────────────────────────
        coal_25   = prior_val(coal_twh,  row["coal_total_yoy_pct"])
        oil_25    = prior_val(oil_twh,   row["crude_oil_total_yoy_pct"])
        gas_25    = prior_val(gas_twh,   row["gas_total_yoy_pct"])
        fossil_25 = round(coal_25 + oil_25 + gas_25, 1) \
                    if all(x is not None for x in [coal_25, oil_25, gas_25]) else None
        total_25  = round(fossil_25 + clean_prior_twh, 1) \
                    if (fossil_25 is not None and clean_prior_twh is not None) else None

        rows_out.append({
            "period":                   period,
            "coal_import_twh":          coal_imp_twh,
            "coal_prod_twh":            coal_prod_twh,
            "coal_total_twh":           coal_twh,
            "coal_total_yoy_pct":       row["coal_total_yoy_pct"],
            "crude_oil_import_twh":     oil_imp_twh,
            "crude_oil_prod_twh":       oil_prod_twh,
            "crude_oil_total_twh":      oil_twh,
            "crude_oil_total_yoy_pct":  row["crude_oil_total_yoy_pct"],
            "gas_import_twh":           gas_imp_twh,
            "gas_prod_twh":             gas_prod_twh,
            "gas_total_twh":            gas_twh,
            "gas_total_yoy_pct":        row["gas_total_yoy_pct"],
            "fossil_total_twh":         fossil_twh,
            "_fossil_25":               fossil_25,
            "clean_power_twh":          clean_twh,
            "_clean_25":                clean_prior_twh,
            "total_twh":                total_twh,
            "_total_25":                total_25,
            **{k: v for k, v in now_em.items() if k != "clean_power_twh"},
        })

    df = pd.DataFrame(rows_out).sort_values("period").reset_index(drop=True)

    # ── Monthly YoY for aggregates ────────────────────────────────────────────
    df["fossil_total_yoy_pct"] = yoy_series(df["fossil_total_twh"], df["_fossil_25"])
    df["clean_power_yoy_pct"]  = yoy_series(df["clean_power_twh"],  df["_clean_25"])
    df["total_yoy_pct"]        = yoy_series(df["total_twh"],        df["_total_25"])

    # ── YTD cumulative ────────────────────────────────────────────────────────
    df["year"] = df["period"].astype(str).str[:4]

    ytd_map = [
        ("coal_total_twh",      "coal_ytd_twh"),
        ("crude_oil_total_twh", "crude_oil_ytd_twh"),
        ("gas_total_twh",       "gas_ytd_twh"),
        ("fossil_total_twh",    "fossil_ytd_twh"),
        ("clean_power_twh",     "clean_power_ytd_twh"),
        ("total_twh",           "total_ytd_twh"),
        ("_fossil_25",          "_fossil_ytd_25"),
        ("_clean_25",           "_clean_ytd_25"),
        ("_total_25",           "_total_ytd_25"),
    ]
    for src, dst in ytd_map:
        if src in df.columns:
            df[dst] = df.groupby("year")[src].cumsum().round(1)

    df["fossil_ytd_yoy_pct"]      = yoy_series(df["fossil_ytd_twh"],      df["_fossil_ytd_25"])
    df["clean_power_ytd_yoy_pct"] = yoy_series(df["clean_power_ytd_twh"], df["_clean_ytd_25"])
    df["total_ytd_yoy_pct"]       = yoy_series(df["total_ytd_twh"],       df["_total_ytd_25"])

    # ── Output ────────────────────────────────────────────────────────────────
    source_cols = [f"{s}_twh" for s in CLEAN_SOURCES if f"{s}_twh" in df.columns]

    out_cols = [
        "period",
        "coal_import_twh",        "coal_prod_twh",        "coal_total_twh",
        "coal_total_yoy_pct",     "coal_ytd_twh",
        "crude_oil_import_twh",   "crude_oil_prod_twh",   "crude_oil_total_twh",
        "crude_oil_total_yoy_pct","crude_oil_ytd_twh",
        "gas_import_twh",         "gas_prod_twh",         "gas_total_twh",
        "gas_total_yoy_pct",      "gas_ytd_twh",
        "fossil_total_twh",       "fossil_total_yoy_pct",
        "fossil_ytd_twh",         "fossil_ytd_yoy_pct",
    ] + source_cols + [
        "clean_power_twh",        "clean_power_yoy_pct",
        "clean_power_ytd_twh",    "clean_power_ytd_yoy_pct",
        "total_twh",              "total_yoy_pct",
        "total_ytd_twh",          "total_ytd_yoy_pct",
    ]
    out_cols = [c for c in out_cols if c in df.columns]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df[out_cols].to_csv(OUTPUT_FILE, index=False)

    print(f"  Written : {OUTPUT_FILE.relative_to(REPO_DIR)}")
    print(f"  Rows    : {len(df)}  Cols: {len(out_cols)}")
    print(f"  Periods : {df['period'].min()} – {df['period'].max()}")

    if not df.empty:
        last = df.iloc[-1]
        print(f"\n  Snapshot {last['period']}:")
        print(f"    Fossil primary energy : {last['fossil_total_twh']:>8,.1f} TWh")
        if pd.notna(last.get("clean_power_twh")):
            print(f"    Clean electricity     : {last['clean_power_twh']:>8,.1f} TWh")
        if pd.notna(last.get("total_twh")):
            print(f"    System total          : {last['total_twh']:>8,.1f} TWh")
            print(f"    YoY total             : {last['total_yoy_pct']:>+8.1f} %")

    print(f"\n[{datetime.now():%Y-%m-%d %H:%M}] Done.")


if __name__ == "__main__":
    main()
