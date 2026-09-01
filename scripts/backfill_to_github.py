#!/usr/bin/env python3
"""
Scans the vault for all Energiebilanz RECH files that contain a <!--machine_data-->
block, extracts import and production figures from each, and writes all periods
to data/fuel-imports/gacc_production.csv in the GitHub repo. One commit total.

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

VAULT      = Path("/Users/hado/Documents/Arbeit/China-Archiv")
RECH_DIRS  = [
    VAULT / "11_Recherche" / "Berichte",
]
REPO_URL   = "https://github.com/DoiEnnoson/china-energy-monitor.git"
REPO_DIR   = Path("/tmp/china-energy-monitor")
OUT_FILE   = REPO_DIR / "data/fuel-imports/gacc_production.csv"
COLUMNS    = ["period", "commodity", "flow", "qty", "qty_unit", "value_usd_bn"]

ENERGIEBILANZ_PATTERN = re.compile(
    r"energiebilanz|energiebilanz|energy.bilanz|china.energie", re.IGNORECASE
)


def find_rech_files() -> list[Path]:
    files = []
    for d in RECH_DIRS:
        for f in d.glob("*.md"):
            if ENERGIEBILANZ_PATTERN.search(f.name):
                files.append(f)
    return sorted(files)


def extract_yaml(text: str) -> dict | None:
    match = re.search(r"<!--machine_data\s+(.*?)-->", text, re.DOTALL)
    if not match:
        return None
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
    print(f"[{datetime.utcnow():%Y-%m-%d %H:%M} UTC] Scanning vault for Energiebilanz RECH files...")

    rech_files = find_rech_files()
    print(f"Found {len(rech_files)} candidates:")
    for f in rech_files:
        print(f"  {f.name}")

    all_rows = []
    processed = []

    for f in rech_files:
        text = f.read_text(encoding="utf-8")
        data = extract_yaml(text)
        if data is None:
            print(f"  [SKIP] {f.name} — no machine_data block")
            continue
        rows = build_rows(data)
        all_rows.extend(rows)
        processed.append((str(data["period"]), f.name, len(rows)))
        print(f"  [OK]   {f.name} — period {data['period']}, {len(rows)} rows")

    if not all_rows:
        print("\nNo data extracted. Annotate RECH files with <!--machine_data--> blocks first.")
        sys.exit(0)

    ensure_repo()

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    result = (
        pd.DataFrame(all_rows, columns=COLUMNS)
        .sort_values(["period", "commodity", "flow"])
        .reset_index(drop=True)
    )

    result.to_csv(OUT_FILE, index=False)
    print(f"\nWritten: {OUT_FILE} ({len(result)} rows, {result['period'].nunique()} periods)")

    token = get_token()
    run_git(["remote", "set-url", "origin", auth_url(token)])
    run_git(["add", "data/fuel-imports/gacc_production.csv"])

    no_changes = subprocess.run(
        ["git", "diff", "--staged", "--quiet"], cwd=REPO_DIR
    ).returncode == 0

    if no_changes:
        print("No changes to commit — already up to date.")
    else:
        periods = sorted({p for p, _, _ in processed})
        today = datetime.utcnow().strftime("%Y-%m-%d")
        run_git(["commit", "-m",
                 f"data: backfill gacc_production {periods[0]}–{periods[-1]} ({today})"])
        run_git(["push", "origin", "main"])
        print("Pushed to GitHub.")

    run_git(["remote", "set-url", "origin", REPO_URL])


if __name__ == "__main__":
    main()
