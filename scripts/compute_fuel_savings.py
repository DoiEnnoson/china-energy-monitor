#!/usr/bin/env python3
"""
Fuel savings model for China's BEV/PHEV/EREV passenger car fleet.

Computes monthly crude oil displacement and primary energy balance
using a Weibull fleet survival model with China-specific parameters.

Output: data/transport/fuel_savings.csv

Sources / calibration:
  IEA GEO 2026: China 1.0 mb/d crude oil displacement for full-year 2025
  JEC WTW v5 COG1: WTT factor 1.24 for petrol
  Zheng et al. 2019 / Liu et al. 2025: Weibull k=2.5, λ=14.9 yr
  IEA GEO 2026 (China): 11,000 km/yr ICE; MDPI empirical: 12,500 km/yr BEV
"""

import math
import calendar
from pathlib import Path
import pandas as pd

# ── Model parameters ────────────────────────────────────────────────────────

LHV_B     = 8.92     # kWh/L  lower heating value, petrol
WTT_B     = 1.24     # well-to-tank factor, petrol (JEC WTW v5 COG1)
Y_B       = 0.43     # refinery yield: litres petrol per litre crude processed
KM_ICE    = 11_000   # annual km, displaced ICE (IEA GEO 2026, China)
KM_BEV    = 12_500   # annual km, electric vehicle (MDPI empirical, China)
ETA       = 0.95     # vehicle availability factor
F_ICE     = 6.2      # L/100 km, ICE fuel consumption
E_BEV     = 16.0     # kWh/100 km, EV electricity consumption
DELTA     = 0.90     # displacement coefficient (share of BEV replacing an ICE)
UF_PHEV   = 0.50     # PHEV electric utility factor
UF_EREV   = 0.65     # EREV electric utility factor
WEIBULL_K = 2.5      # Weibull shape
WEIBULL_L = 14.9     # Weibull scale, years (median scrappage ~12.9 yr)

LITRES_PER_BARREL = 158.99

# China grid primary energy factor — declining as coal share falls
GF = {2020: 2.10, 2025: 1.80, 2030: 1.50, 2035: 1.30, 2040: 1.15, 2060: 1.03}

PROJ_END = '2030-12'   # project through end of 2030


# ── Helpers ─────────────────────────────────────────────────────────────────

def weibull_survival(age_years: float) -> float:
    return math.exp(-((age_years / WEIBULL_L) ** WEIBULL_K))


def grid_factor(year: int) -> float:
    keys = sorted(GF)
    if year <= keys[0]:
        return GF[keys[0]]
    if year >= keys[-1]:
        return GF[keys[-1]]
    for i in range(len(keys) - 1):
        y0, y1 = keys[i], keys[i + 1]
        if y0 <= year <= y1:
            t = (year - y0) / (y1 - y0)
            return GF[y0] + t * (GF[y1] - GF[y0])
    return GF[keys[-1]]


def period_idx(period: str) -> int:
    return int(period[:4]) * 12 + int(period[5:7])


# ── Core model ───────────────────────────────────────────────────────────────

def compute_fuel_savings() -> pd.DataFrame:
    root = Path(__file__).parent.parent

    # Actual monthly sales
    retail = pd.read_csv(root / 'data/transport/china_car_sales_retail.csv', dtype=str)
    retail = retail[
        (retail['time_interval'] == 'monthly') &
        (retail['period'] >= '2016-11')
    ].sort_values('period').reset_index(drop=True)

    latest_actual = retail['period'].max()

    # S-curve projection
    proj = pd.read_csv(root / 'data/transport/china_car_sales_projection.csv', dtype=str)
    proj = proj[proj['period'] <= PROJ_END].sort_values('period').reset_index(drop=True)

    # ── Build sales lookup ────────────────────────────────────────────────

    # PHEV/EREV split for projected months: use trailing 6-month ratio
    last6 = retail.tail(6)
    phev6 = last6['PHEV'].astype(float).sum()
    erev6 = last6['EREV'].astype(float).sum()
    pe_total6 = phev6 + erev6
    phev_frac = phev6 / pe_total6 if pe_total6 > 0 else 0.55
    erev_frac = 1.0 - phev_frac

    # Market size base for projected months: trailing 12-month average
    base_volume = retail.tail(12)['TOTAL'].astype(float).mean()

    sales_bev  = {}
    sales_phev = {}
    sales_erev = {}

    for _, r in retail.iterrows():
        idx = period_idx(r['period'])
        sales_bev[idx]  = float(r['BEV'])
        sales_phev[idx] = float(r['PHEV'])
        sales_erev[idx] = float(r['EREV'])

    proj_lookup = proj.set_index('period').to_dict('index')
    for p, pr in proj_lookup.items():
        if p <= latest_actual:
            continue
        idx = period_idx(p)
        bev_share      = float(pr['bev_proj']) if pr['bev_proj'] else 0.0
        phev_erev_sh   = float(pr['phev_erev_proj']) if pr['phev_erev_proj'] else 0.0
        sales_bev[idx]  = base_volume * bev_share
        sales_phev[idx] = base_volume * phev_erev_sh * phev_frac
        sales_erev[idx] = base_volume * phev_erev_sh * erev_frac

    # ── Output periods ────────────────────────────────────────────────────

    actual_periods = set(retail['period'].tolist())
    out_periods = sorted(
        actual_periods |
        set(proj[proj['period'] <= PROJ_END]['period'].tolist())
    )
    out_periods = [p for p in out_periods if p >= '2016-11']

    start_idx = period_idx('2016-11')

    # ── Fleet model ───────────────────────────────────────────────────────

    rows = []
    for period_t in out_periods:
        t_idx   = period_idx(period_t)
        year_t  = int(period_t[:4])
        month_t = int(period_t[5:7])
        days    = calendar.monthrange(year_t, month_t)[1]
        is_proj = period_t not in actual_periods

        fleet_bev = fleet_phev = fleet_erev = 0.0

        for x in range(start_idx, t_idx + 1):
            age_yr   = (t_idx - x) / 12.0
            survival = weibull_survival(age_yr)
            fleet_bev  += sales_bev.get(x, 0.0)  * survival
            fleet_phev += sales_phev.get(x, 0.0) * survival
            fleet_erev += sales_erev.get(x, 0.0) * survival

        f_elec_total = fleet_bev + fleet_phev * UF_PHEV + fleet_erev * UF_EREV
        f_displaced  = f_elec_total * DELTA

        # Fuel saved
        fuel_L = f_displaced * (KM_ICE / 12) * ETA * (F_ICE / 100)

        # Crude oil displacement
        crude_L        = fuel_L / Y_B
        crude_mb_month = (crude_L / LITRES_PER_BARREL) / 1e6   # million barrels
        crude_mb_d     = crude_mb_month / days                  # mb/d

        # Primary energy saved
        pe_saved_twh = (fuel_L * LHV_B * WTT_B) / 1e9

        # Primary energy added (electricity)
        elec_kwh    = f_elec_total * (KM_BEV / 12) * ETA * (E_BEV / 100)
        pe_added_twh = (elec_kwh * grid_factor(year_t)) / 1e9

        pe_net_twh = pe_saved_twh - pe_added_twh

        rows.append({
            'period':              period_t,
            'type':                'projected' if is_proj else 'historical',
            'crude_disp_mb_d':     round(crude_mb_d, 4),
            'crude_disp_mb_month': round(crude_mb_month, 3),
            'pe_saved_twh':        round(pe_saved_twh, 2),
            'pe_added_twh':        round(pe_added_twh, 2),
            'pe_net_twh':          round(pe_net_twh, 2),
        })

    return pd.DataFrame(rows)


def main():
    print("Computing fuel savings model ...")
    df = compute_fuel_savings()

    root = Path(__file__).parent.parent
    out  = root / 'data/transport/fuel_savings.csv'
    df.to_csv(out, index=False)

    # ── Diagnostics ───────────────────────────────────────────────────────
    hist    = df[df['type'] == 'historical']
    latest  = hist.iloc[-1] if not hist.empty else None
    aug26   = df[df['period'] == '2026-08']
    y2026   = df[df['period'].str.startswith('2026')]

    print(f"  Rows: {len(df)} ({len(hist)} historical, {len(df) - len(hist)} projected)")
    if latest is not None:
        print(f"  Latest historical : {latest['period']} — {latest['crude_disp_mb_d']:.3f} mb/d")
    if not aug26.empty:
        r = aug26.iloc[0]
        print(f"  Aug 2026 (target ~0.96 mb/d): {r['crude_disp_mb_d']:.3f} mb/d")
    if not y2026.empty:
        total_mb  = y2026['crude_disp_mb_month'].sum()
        total_twh = y2026['pe_net_twh'].sum()
        print(f"  2026 total crude displaced : {total_mb:.0f} million barrels")
        print(f"  2026 net PE savings        : {total_twh:.0f} TWh")
    print(f"  Written: {out}")


if __name__ == "__main__":
    main()
