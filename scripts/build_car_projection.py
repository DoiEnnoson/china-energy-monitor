#!/usr/bin/env python3
"""
Fits a logistic S-curve to China BEV market share data and projects to 2040.

Input:  data/transport/china_car_sales_retail.csv
Output: data/transport/china_car_sales_projection.csv

Methodology:
  BEV share follows a logistic (sigmoid) function:
    f(t) = L / (1 + exp(-k * (t - t0)))
  where:
    L  = 0.85  — saturation ceiling (model assumption; Chinese government
                  targets BEVs to "dominate" new car sales by 2035, no explicit
                  percentage published)
    k  = fitted from historical CPCA retail data
    t0 = fitted inflection point (month of maximum growth rate)

  ICE and PHEV+EREV projections are derived from the BEV curve:
    PHEV+EREV share is modelled as plateauing at its trailing 12-month average
    then declining linearly to 0.08 by 2040 (PHEVs become redundant as BEV
    range and charging infrastructure improve).
    ICE = 1 - BEV - PHEV_EREV (floored at 0.01).

  Data source: CPCA via @leRaffl (https://x.com/leRaffl)
"""

import sys
from io import StringIO

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

RETAIL_PATH     = "data/transport/china_car_sales_retail.csv"
PROJECTION_PATH = "data/transport/china_car_sales_projection.csv"

L_BEV          = 0.85   # saturation ceiling
PHEV_EREV_FLOOR = 0.08  # long-run PHEV+EREV floor by 2040
PROJ_END_YEAR  = 2040


def logistic(t, k, t0):
    return L_BEV / (1 + np.exp(-k * (t - t0)))


def period_to_t(period: str, ref_year: int = 2010) -> int:
    """Convert 'YYYY-MM' to months-since-ref_year-Jan (1-indexed)."""
    y, m = int(period[:4]), int(period[5:7])
    return (y - ref_year) * 12 + m


def t_to_period(t: int, ref_year: int = 2010) -> str:
    y = ref_year + (t - 1) // 12
    m = (t - 1) % 12 + 1
    return f"{y}-{m:02d}"


def main():
    df = pd.read_csv(RETAIL_PATH)

    # Keep only monthly rows with valid totals
    monthly = df[
        (df["time_interval"] == "monthly") & (df["TOTAL"] > 0)
    ].copy()

    if monthly.empty:
        # Fall back to all rows if time_interval labelling differs
        monthly = df[df["TOTAL"] > 0].copy()

    monthly["t"] = monthly["period"].apply(period_to_t)
    monthly["bev_share"] = monthly["BEV"] / monthly["TOTAL"]

    # Drop rows where BEV share is zero (pre-adoption noise)
    fit_data = monthly[monthly["bev_share"] > 0.001].copy()

    # Fit logistic — initial guess: k=0.07, t0=~month 180 (mid-2024)
    popt, _ = curve_fit(
        logistic,
        fit_data["t"].values,
        fit_data["bev_share"].values,
        p0=[0.07, 180],
        bounds=([0.01, 80], [0.5, 320]),
        maxfev=20_000,
    )
    k_fit, t0_fit = popt
    print(f"Fitted: k={k_fit:.4f}, t0={t0_fit:.1f} "
          f"({t_to_period(int(round(t0_fit)))})")

    # Generate projection 2010-01 through 2040-12
    t_end = period_to_t(f"{PROJ_END_YEAR}-12")
    t_all = np.arange(1, t_end + 1)

    bev_proj = np.clip(logistic(t_all, k_fit, t0_fit), 0, L_BEV)

    # PHEV+EREV: trailing 12-month observed average, then linear decline to floor
    recent_phev_erev = (
        (monthly["PHEV"] + monthly["EREV"]) / monthly["TOTAL"]
    ).tail(12).mean()

    last_hist_t = monthly["t"].max()
    phev_erev_proj = np.where(
        t_all <= last_hist_t,
        np.nan,   # filled from actual data below
        recent_phev_erev + (PHEV_EREV_FLOOR - recent_phev_erev)
        * (t_all - last_hist_t) / (t_end - last_hist_t),
    )

    ice_proj = np.clip(1 - bev_proj - np.where(
        np.isnan(phev_erev_proj), recent_phev_erev, phev_erev_proj
    ), 0.01, 1)

    periods = [t_to_period(int(t)) for t in t_all]

    out = pd.DataFrame({
        "period":       periods,
        "bev_proj":     bev_proj.round(4),
        "phev_erev_proj": np.where(np.isnan(phev_erev_proj),
                                    np.nan, phev_erev_proj).round(4),
        "ice_proj":     ice_proj.round(4),
    })

    out.to_csv(PROJECTION_PATH, index=False)
    print(f"Written: {PROJECTION_PATH} ({len(out)} rows, 2010-01 → {PROJ_END_YEAR}-12)")
    print(f"BEV projection 2035-12: {logistic(period_to_t('2035-12'), k_fit, t0_fit):.1%}")
    print(f"BEV projection 2040-12: {logistic(period_to_t('2040-12'), k_fit, t0_fit):.1%}")


if __name__ == "__main__":
    main()
