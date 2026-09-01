#!/usr/bin/env python3
"""
Reads the <!--machine_data ... --> YAML block from a monthly Energiebilanz RECH file,
updates two wide-format CSVs in the GitHub repo, commits and pushes.
  data/production/nbs_production.csv   — NBS domestic output
  data/fuel-imports/gacc_imports.csv   — GACC import qty + value + value per unit

Existing rows for the same period are replaced (idempotent).

Usage:
    python scripts/rech_to_github.py \
        --file "11_Recherche/Berichte/260820_RECH_China_Energiebilanz_Juli2026.md"
"""

import argparse
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml
import pandas as pd

VAULT    = Path("/Users/hado/Documents/Arbeit/China-Archiv")
REPO_URL = "https://github.com/DoiEnnoson/china-energy-monitor.git"
REPO_DIR = Path("/tmp/china-energy-monitor")

NBS_FILE  = REPO_DIR / "data/production/nbs_production.csv"
GACC_FILE = REPO_DIR / "data/fuel-imports/gacc_imports.csv"

NBS_COLS  = ["period", "coal_mt", "crude_oil_mt", "gas_bcm"]
GACC_COLS = [
    "period",
    "coal_mt",        "coal_usd_bn",       "coal_usd_per_mt",
    "crude_oil_mt",   "crude_oil_usd_bn",  "crude_oil_usd_per_mt",
    "gas_mt",         "gas_usd_bn",        "gas_usd_per_mt",
]


def extract_yaml(text: str) -> dict:
    m = re.search(r"<!--machine_data\s+(.*?)-->", text, re.DOTALL)
    if not m:
        raise ValueError("No <!--machine_data ... --> block found.")
    return yaml.safe_load(m.group(1))


def vpu(qty, val):
    if qty and val:
        return round(val * 1000 / qty, 1)
    return None


def to_nbs_row(data: dict) -> dict:
    p = data.get("production", {})
    return {
        "period":       str(data["period"]),
        "coal_mt":      p.get("coal_mt"),
        "crude_oil_mt": p.get("crude_oil_mt"),
        "gas_bcm":      p.get("gas_bcm"),
    }


def to_gacc_row(data: dict) -> dict:
    imp  = data.get("imports", {})
    coal = imp.get("coal", {})
    oil  = imp.get("crude_oil", {})
    gas  = imp.get("gas", {})
    cq, cv = coal.get("qty_mt"), coal.get("value_usd_bn")
    oq, ov = oil.get("qty_mt"),  oil.get("value_usd_bn")
    gq, gv = gas.get("qty_mt"),  gas.get("value_usd_bn")
    return {
        "period":               str(data["period"]),
        "coal_mt":              cq,
        "coal_usd_bn":          cv,
        "coal_usd_per_mt":      vpu(cq, cv),
        "crude_oil_mt":         oq,
        "crude_oil_usd_bn":     ov,
        "crude_oil_usd_per_mt": vpu(oq, ov),
        "gas_mt":               gq,
        "gas_usd_bn":           gv,
        "gas_usd_per_mt":       vpu(gq, gv),
    }


def upsert(path: Path, new_row: dict, cols: list[str]) -> pd.DataFrame:
    period = new_row["period"]
    if path.exists():
        df = pd.read_csv(path, dtype=str)
        df = df[df["period"] != period]
    else:
        df = pd.DataFrame(columns=cols)
    return (
        pd.concat([df, pd.DataFrame([new_row], columns=cols)], ignore_index=True)
        .sort_values("period")
        .reset_index(drop=True)
    )


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
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True,
                        help="Path to RECH file (absolute or relative to vault root)")
    args = parser.parse_args()

    rech_path = Path(args.file)
    if not rech_path.is_absolute():
        rech_path = VAULT / rech_path
    if not rech_path.exists():
        print(f"File not found: {rech_path}")
        sys.exit(1)

    data    = extract_yaml(rech_path.read_text(encoding="utf-8"))
    period  = str(data["period"])
    nbs_row = to_nbs_row(data)
    gacc_row = to_gacc_row(data)
    print(f"Period: {period}")

    ensure_repo()

    for path, row, cols in [
        (NBS_FILE,  nbs_row,  NBS_COLS),
        (GACC_FILE, gacc_row, GACC_COLS),
    ]:
        path.parent.mkdir(parents=True, exist_ok=True)
        df = upsert(path, row, cols)
        df.to_csv(path, index=False)
        print(f"Written: {path.name} ({len(df)} rows)")

    token = get_token()
    run_git(["remote", "set-url", "origin",
             REPO_URL.replace("https://", f"https://DoiEnnoson:{token}@")])
    run_git(["add", "data/production/", "data/fuel-imports/"])

    no_change = subprocess.run(
        ["git", "diff", "--staged", "--quiet"], cwd=REPO_DIR
    ).returncode == 0

    if no_change:
        print("No changes — already up to date.")
    else:
        run_git(["commit", "-m",
                 f"data: nbs_production + gacc_imports {period} ({datetime.now():%Y-%m-%d})"])
        run_git(["push", "origin", "main"])
        print("Pushed.")

    run_git(["remote", "set-url", "origin", REPO_URL])


if __name__ == "__main__":
    main()
