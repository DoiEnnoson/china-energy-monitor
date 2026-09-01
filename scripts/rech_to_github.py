#!/usr/bin/env python3
"""
Reads the <!--machine_data ... --> YAML block from a monthly Energiebilanz RECH file,
extracts energy import and production figures, appends to the GitHub repo
data/fuel-imports/gacc_production.csv, commits and pushes.

Existing rows for the same period are replaced (idempotent — safe to run twice).

Usage (from anywhere):
    python scripts/rech_to_github.py \
        --file "11_Recherche/Berichte/260820_RECH_China_Energiebilanz_Juli2026.md"

    # absolute path also works:
    python scripts/rech_to_github.py \
        --file "/Users/hado/Documents/Arbeit/China-Archiv/11_Recherche/Berichte/..."
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
OUT_FILE = REPO_DIR / "data/fuel-imports/gacc_production.csv"

COLUMNS  = ["period", "commodity", "flow", "qty", "qty_unit", "value_usd_bn"]


def extract_yaml(text: str) -> dict:
    match = re.search(r"<!--machine_data\s+(.*?)-->", text, re.DOTALL)
    if not match:
        raise ValueError("No <!--machine_data ... --> block found.")
    return yaml.safe_load(match.group(1))


def build_rows(data: dict) -> list[dict]:
    period = str(data["period"])
    rows = []

    for commodity, vals in data.get("imports", {}).items():
        rows.append({
            "period":       period,
            "commodity":    commodity,
            "flow":         "import",
            "qty":          vals.get("qty_mt"),
            "qty_unit":     "mt",
            "value_usd_bn": vals.get("value_usd_bn"),
        })

    for key, val in data.get("production", {}).items():
        # key format: coal_mt / crude_oil_mt / gas_bcm
        commodity, unit = key.rsplit("_", 1)
        rows.append({
            "period":       period,
            "commodity":    commodity,
            "flow":         "production",
            "qty":          val,
            "qty_unit":     unit,
            "value_usd_bn": None,
        })

    return rows


def run_git(args: list[str]) -> None:
    result = subprocess.run(["git"] + args, cwd=REPO_DIR,
                            capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}:\n{result.stderr}")


def get_token() -> str:
    return subprocess.run(["gh", "auth", "token"],
                          capture_output=True, text=True).stdout.strip()


def auth_url(token: str) -> str:
    return REPO_URL.replace("https://", f"https://DoiEnnoson:{token}@")


def ensure_repo() -> None:
    token = get_token()
    if not REPO_DIR.exists():
        subprocess.run(["git", "clone", auth_url(token), str(REPO_DIR)], check=True)
    else:
        run_git(["remote", "set-url", "origin", auth_url(token)])
        run_git(["pull", "origin", "main"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True,
                        help="Path to Energiebilanz RECH markdown file "
                             "(absolute or relative to vault root)")
    args = parser.parse_args()

    rech_path = Path(args.file)
    if not rech_path.is_absolute():
        rech_path = VAULT / rech_path
    if not rech_path.exists():
        print(f"File not found: {rech_path}")
        sys.exit(1)

    data = extract_yaml(rech_path.read_text(encoding="utf-8"))
    rows = build_rows(data)
    period = str(data["period"])

    print(f"Period: {period} — {len(rows)} rows extracted")

    ensure_repo()

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    if OUT_FILE.exists():
        existing = pd.read_csv(OUT_FILE, dtype=str)
        existing = existing[existing["period"] != period]
        result = pd.concat([existing, pd.DataFrame(rows, columns=COLUMNS)],
                           ignore_index=True)
    else:
        result = pd.DataFrame(rows, columns=COLUMNS)

    result = result.sort_values(["period", "commodity", "flow"]).reset_index(drop=True)
    result.to_csv(OUT_FILE, index=False)
    print(f"Written: {OUT_FILE} ({len(result)} rows total)")

    token = get_token()
    run_git(["remote", "set-url", "origin", auth_url(token)])
    run_git(["add", "data/fuel-imports/gacc_production.csv"])

    no_changes = subprocess.run(
        ["git", "diff", "--staged", "--quiet"], cwd=REPO_DIR
    ).returncode == 0

    if no_changes:
        print("No changes — already up to date.")
    else:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        run_git(["commit", "-m", f"data: gacc_production {period} ({today})"])
        run_git(["push", "origin", "main"])
        print("Pushed to GitHub.")

    run_git(["remote", "set-url", "origin", REPO_URL])


if __name__ == "__main__":
    main()
