#!/usr/bin/env python3
"""
Scans the vault for all Energiebilanz RECH files that contain a <!--machine_data-->
block and writes three wide-format CSVs to the GitHub repo:
  data/production/nbs_production.csv   — one row per period, NBS domestic output
  data/fuel-imports/gacc_imports.csv   — one row per period, GACC import qty + value
  data/power/capacity_additions.csv    — one row per period, CREA capacity additions

Run once after annotating existing RECH files with machine_data blocks.

Usage:
    python scripts/backfill_to_github.py
"""

import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml
import pandas as pd

VAULT     = Path("/Users/hado/Documents/Arbeit/China-Archiv")
RECH_DIRS = [VAULT / "11_Recherche" / "Berichte"]
REPO_URL  = "https://github.com/DoiEnnoson/china-energy-monitor.git"
REPO_DIR  = Path("/tmp/china-energy-monitor")

NBS_FILE      = REPO_DIR / "data/production/nbs_production.csv"
GACC_FILE     = REPO_DIR / "data/fuel-imports/gacc_imports.csv"
CAPACITY_FILE = REPO_DIR / "data/power/capacity_additions.csv"

NBS_COLS      = ["period", "coal_mt", "coal_mt_yoy_pct", "crude_oil_mt", "crude_oil_mt_yoy_pct", "gas_bcm", "gas_bcm_yoy_pct"]
CAPACITY_COLS = ["period", "crea_period", "coal_gw", "gas_gw", "nuclear_gw", "hydro_gw", "wind_gw", "solar_gw", "total_gw"]
GACC_COLS = [
    "period",
    "coal_mt",        "coal_usd_bn",       "coal_usd_per_mt",
    "crude_oil_mt",   "crude_oil_usd_bn",  "crude_oil_usd_per_mt",
    "gas_mt",         "gas_usd_bn",        "gas_usd_per_mt",
]

ENERGIEBILANZ_RE = re.compile(r"energiebilanz|energy.bilanz|china.energie", re.IGNORECASE)


def find_rech_files() -> list[Path]:
    files = []
    for d in RECH_DIRS:
        for f in sorted(d.glob("*.md")):
            if ENERGIEBILANZ_RE.search(f.name):
                files.append(f)
    return files


def extract_yaml(text: str) -> dict | None:
    m = re.search(r"<!--machine_data\s+(.*?)-->", text, re.DOTALL)
    return yaml.safe_load(m.group(1)) if m else None


def vpu(qty, val):
    """Value per unit in USD/t. None if either input is None/zero."""
    if qty and val:
        return round(val * 1000 / qty, 1)
    return None


def to_nbs_row(data: dict) -> dict:
    p = data.get("production", {})
    return {
        "period":               str(data["period"]),
        "coal_mt":              p.get("coal_mt"),
        "coal_mt_yoy_pct":      p.get("coal_mt_yoy_pct"),
        "crude_oil_mt":         p.get("crude_oil_mt"),
        "crude_oil_mt_yoy_pct": p.get("crude_oil_mt_yoy_pct"),
        "gas_bcm":              p.get("gas_bcm"),
        "gas_bcm_yoy_pct":      p.get("gas_bcm_yoy_pct"),
    }


def to_gacc_row(data: dict) -> dict:
    imp = data.get("imports", {})
    coal = imp.get("coal", {})
    oil  = imp.get("crude_oil", {})
    gas  = imp.get("gas", {})

    cq, cv = coal.get("qty_mt"), coal.get("value_usd_bn")
    oq, ov = oil.get("qty_mt"),  oil.get("value_usd_bn")
    gq, gv = gas.get("qty_mt"),  gas.get("value_usd_bn")

    return {
        "period":              str(data["period"]),
        "coal_mt":             cq,
        "coal_usd_bn":         cv,
        "coal_usd_per_mt":     vpu(cq, cv),
        "crude_oil_mt":        oq,
        "crude_oil_usd_bn":    ov,
        "crude_oil_usd_per_mt": vpu(oq, ov),
        "gas_mt":              gq,
        "gas_usd_bn":          gv,
        "gas_usd_per_mt":      vpu(gq, gv),
    }


def to_capacity_row(data: dict) -> dict | None:
    cap = data.get("capacity_additions")
    if not cap:
        return None
    return {
        "period":      str(data["period"]),
        "crea_period": str(cap.get("crea_period", "")),
        "coal_gw":     cap.get("coal_gw"),
        "gas_gw":      cap.get("gas_gw"),
        "nuclear_gw":  cap.get("nuclear_gw"),
        "hydro_gw":    cap.get("hydro_gw"),
        "wind_gw":     cap.get("wind_gw"),
        "solar_gw":    cap.get("solar_gw"),
        "total_gw":    cap.get("total_gw"),
    }


def run_git(args: list[str]) -> None:
    r = subprocess.run(["git"] + args, cwd=REPO_DIR, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}:\n{r.stderr}")


def get_token() -> str:
    return subprocess.run(["gh", "auth", "token"],
                          capture_output=True, text=True).stdout.strip()


def ensure_repo() -> None:
    token = get_token()
    url = REPO_URL.replace("https://", f"https://DoiEnnoson:{token}@")
    if not REPO_DIR.exists():
        subprocess.run(["git", "clone", url, str(REPO_DIR)], check=True)
    else:
        run_git(["remote", "set-url", "origin", url])
        run_git(["pull", "origin", "main"])


def main():
    print(f"[{datetime.now():%Y-%m-%d %H:%M}] Scanning vault for Energiebilanz RECH files...")

    nbs_rows, gacc_rows, capacity_rows, periods = [], [], [], []

    for f in find_rech_files():
        data = extract_yaml(f.read_text(encoding="utf-8"))
        if data is None:
            print(f"  [SKIP] {f.name}")
            continue
        nbs_rows.append(to_nbs_row(data))
        gacc_rows.append(to_gacc_row(data))
        cap_row = to_capacity_row(data)
        if cap_row is not None:
            capacity_rows.append(cap_row)
        periods.append(str(data["period"]))
        print(f"  [OK]   {f.name} — {data['period']}"
              + (" [+CREA]" if cap_row else ""))

    if not nbs_rows:
        print("No annotated RECH files found.")
        sys.exit(0)

    ensure_repo()

    targets = [
        (NBS_FILE,  nbs_rows,  NBS_COLS),
        (GACC_FILE, gacc_rows, GACC_COLS),
    ]
    if capacity_rows:
        targets.append((CAPACITY_FILE, capacity_rows, CAPACITY_COLS))

    for path, rows, cols in targets:
        path.parent.mkdir(parents=True, exist_ok=True)
        df = pd.DataFrame(rows, columns=cols).sort_values("period").reset_index(drop=True)
        df.to_csv(path, index=False)
        print(f"Written: {path.name} ({len(df)} rows)")

    token = get_token()
    run_git(["remote", "set-url", "origin",
             REPO_URL.replace("https://", f"https://DoiEnnoson:{token}@")])
    run_git(["add", "data/production/", "data/fuel-imports/", "data/power/capacity_additions.csv"])

    no_change = subprocess.run(
        ["git", "diff", "--staged", "--quiet"], cwd=REPO_DIR
    ).returncode == 0

    if no_change:
        print("No changes to commit.")
    else:
        p = sorted(periods)
        run_git(["commit", "-m",
                 f"data: nbs_production + gacc_imports {p[0]}–{p[-1]} ({datetime.now():%Y-%m-%d})"])
        run_git(["push", "origin", "main"])
        print("Pushed.")

    run_git(["remote", "set-url", "origin", REPO_URL])


if __name__ == "__main__":
    main()
