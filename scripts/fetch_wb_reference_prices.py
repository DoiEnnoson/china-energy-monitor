#!/usr/bin/env python3
"""
fetch_wb_reference_prices.py

Scrapes the World Bank Pink Sheet (CMO-Historical-Data-Monthly.xlsx) and
writes monthly benchmark prices to data/reference/wb_reference_prices.csv.

Columns written:
  period            — YYYYMM
  brent_usd_bbl     — Crude oil, Brent ($/bbl)
  dubai_usd_bbl     — Crude oil, Dubai ($/bbl)
  coal_au_usd_mt    — Coal, Australian ($/mt)
  lng_japan_usd_mmbtu — Liquefied natural gas, Japan ($/mmbtu)

Only rows from START_PERIOD (env var, default 202601) onwards are kept.
Existing CSV is merged: new data replaces rows for matching periods,
older rows outside the scrape range are preserved.

Usage:
    python scripts/fetch_reference_prices.py
    START_PERIOD=202501 python scripts/fetch_reference_prices.py
"""

import os
import re
import sys
import requests
import openpyxl
import pandas as pd
from io import BytesIO
from pathlib import Path

WB_PAGE_URL  = "https://www.worldbank.org/en/research/commodity-markets"
OUTPUT_CSV   = Path("data/reference/wb_reference_prices.csv")
START_PERIOD = int(os.environ.get("START_PERIOD", "202601"))

# Pink Sheet column name → output column name
COL_MAP = {
    "Crude oil, Brent":                "brent_usd_bbl",
    "Crude oil, Dubai":                "dubai_usd_bbl",
    "Coal, Australian":                "coal_au_usd_mt",
    "Liquefied natural gas, Japan":    "lng_japan_usd_mmbtu",
}


def get_pink_sheet_url() -> str:
    resp = requests.get(WB_PAGE_URL, timeout=30)
    resp.raise_for_status()
    matches = re.findall(
        r'https?://[^\s"\'<>]*CMO-Historical-Data-Monthly[^\s"\'<>]*\.xlsx',
        resp.text
    )
    if not matches:
        raise RuntimeError("Pink Sheet URL not found on World Bank page")
    return matches[0]


def parse_pink_sheet(url: str) -> pd.DataFrame:
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()

    wb = openpyxl.load_workbook(BytesIO(resp.content), read_only=True, data_only=True)
    ws = wb["Monthly Prices"]

    rows = list(ws.iter_rows(values_only=True))

    # Find header row: contains "Crude oil, Brent"
    header_idx = None
    for i, row in enumerate(rows):
        if any(isinstance(v, str) and "Crude oil, Brent" in v for v in row):
            header_idx = i
            break
    if header_idx is None:
        raise RuntimeError("Header row not found in Monthly Prices sheet")

    headers = rows[header_idx]
    data_start = header_idx + 2  # skip unit row

    # Map header positions to output column names
    col_indices = {}
    for j, h in enumerate(headers):
        if h in COL_MAP:
            col_indices[COL_MAP[h]] = j

    missing = set(COL_MAP.values()) - set(col_indices.keys())
    if missing:
        available = [h for h in headers if isinstance(h, str)]
        print(f"WARNING: columns not found: {missing}", file=sys.stderr)
        print(f"Available headers: {available[:20]}", file=sys.stderr)

    records = []
    for row in rows[data_start:]:
        date_val = row[0]
        if not isinstance(date_val, str) or not re.match(r"\d{4}M\d{2}", date_val):
            continue
        # "2026M01" → 202601
        period = int(date_val.replace("M", ""))
        if period < START_PERIOD:
            continue

        rec = {"period": period}
        for out_col, idx in col_indices.items():
            v = row[idx]
            # Pink Sheet uses "…" for missing data
            rec[out_col] = round(float(v), 2) if isinstance(v, (int, float)) else None
        records.append(rec)

    return pd.DataFrame(records, columns=["period"] + list(COL_MAP.values()))


def merge_and_write(new_df: pd.DataFrame) -> None:
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    if OUTPUT_CSV.exists():
        old_df = pd.read_csv(OUTPUT_CSV)
        # Drop old rows that are covered by new data
        old_df = old_df[~old_df["period"].isin(new_df["period"])]
        combined = pd.concat([old_df, new_df], ignore_index=True)
    else:
        combined = new_df

    combined = combined.sort_values("period").reset_index(drop=True)
    combined.to_csv(OUTPUT_CSV, index=False)
    print(f"Written {len(combined)} rows to {OUTPUT_CSV}")
    print(combined.tail(6).to_string(index=False))


def main():
    print("Fetching Pink Sheet URL...")
    url = get_pink_sheet_url()
    print(f"URL: {url}")

    print("Downloading and parsing...")
    df = parse_pink_sheet(url)
    print(f"Parsed {len(df)} rows (period >= {START_PERIOD})")

    merge_and_write(df)


if __name__ == "__main__":
    main()
