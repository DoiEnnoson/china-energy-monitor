#!/usr/bin/env python3
"""
goatcounter_report.py
Täglich: GoatCounter-Daten holen, in traffic_log.csv schreiben, traffic_monthly.csv aktualisieren.
Montags zusätzlich: Weekly-Email mit WoW-Vergleich, MTD und MoM-Vergleich.

GitHub Secrets:
  GOATCOUNTER   — GoatCounter API token
  GMAIL_CONFIG  — user@gmail.com:app_password
"""

import csv
import os
import smtplib
import sys
from datetime import date, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import requests

SITE = "china-energy-monitor.goatcounter.com"
REPO_ROOT = Path(__file__).parent.parent
CSV_DAILY = REPO_ROOT / "data" / "traffic_log.csv"
CSV_MONTHLY = REPO_ROOT / "data" / "traffic_monthly.csv"
DAILY_HEADER = ["date", "pageviews", "unique_visitors"]
MONTHLY_HEADER = ["month", "pageviews", "unique_visitors"]

DAY_NAMES = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
MONTH_NAMES = {
    1: "Jan", 2: "Feb", 3: "Mär", 4: "Apr", 5: "Mai", 6: "Jun",
    7: "Jul", 8: "Aug", 9: "Sep", 10: "Okt", 11: "Nov", 12: "Dez",
}


# ── Secrets ──────────────────────────────────────────────────────────────────

def get_token() -> str:
    token = os.environ.get("GOATCOUNTER", "")
    if not token:
        sys.exit("GOATCOUNTER secret not set")
    return token


def get_gmail_config() -> tuple[str, str]:
    cfg = os.environ.get("GMAIL_CONFIG", "")
    if not cfg or ":" not in cfg:
        sys.exit("GMAIL_CONFIG not set or malformed (expected user@gmail.com:password)")
    user, password = cfg.split(":", 1)
    return user.strip(), password.strip()


# ── GoatCounter API ───────────────────────────────────────────────────────────

def fetch_day(day: date, token: str) -> dict:
    r = requests.get(
        f"https://{SITE}/api/v0/stats/hits",
        headers={"Authorization": f"Bearer {token}"},
        params={"start": str(day), "end": str(day), "daily": "true"},
        timeout=30,
    )
    r.raise_for_status()
    hits = r.json().get("hits", [])
    entry = hits[0] if hits else {}
    return {
        "date": str(day),
        "pageviews": entry.get("count", 0),
        "unique_visitors": entry.get("count_unique", 0),
    }


# ── CSV I/O ───────────────────────────────────────────────────────────────────

def already_logged(day: date) -> bool:
    if not CSV_DAILY.exists():
        return False
    with open(CSV_DAILY, newline="") as f:
        return any(row["date"] == str(day) for row in csv.DictReader(f))


def append_daily(row: dict):
    write_header = not CSV_DAILY.exists()
    with open(CSV_DAILY, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=DAILY_HEADER)
        if write_header:
            writer.writeheader()
        writer.writerow(row)
    print(f"Logged daily: {row}")


def read_range(start: date, end: date) -> list[dict]:
    if not CSV_DAILY.exists():
        return []
    with open(CSV_DAILY, newline="") as f:
        rows = [
            r for r in csv.DictReader(f)
            if start <= date.fromisoformat(r["date"]) <= end
        ]
    return sorted(rows, key=lambda r: r["date"])


def update_monthly_csv():
    """Recompute all monthly totals from daily CSV and overwrite traffic_monthly.csv."""
    if not CSV_DAILY.exists():
        return
    monthly: dict[str, dict] = {}
    with open(CSV_DAILY, newline="") as f:
        for row in csv.DictReader(f):
            m = row["date"][:7]
            if m not in monthly:
                monthly[m] = {"pageviews": 0, "unique_visitors": 0}
            monthly[m]["pageviews"] += int(row["pageviews"])
            monthly[m]["unique_visitors"] += int(row["unique_visitors"])
    with open(CSV_MONTHLY, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=MONTHLY_HEADER)
        writer.writeheader()
        for m in sorted(monthly):
            writer.writerow({"month": m, **monthly[m]})
    print(f"Updated monthly CSV: {len(monthly)} months")


def read_monthly() -> list[dict]:
    if not CSV_MONTHLY.exists():
        return []
    with open(CSV_MONTHLY, newline="") as f:
        return list(csv.DictReader(f))


# ── Helpers ───────────────────────────────────────────────────────────────────

def aggregate(rows: list[dict]) -> tuple[int, int]:
    pv = sum(int(r["pageviews"]) for r in rows)
    uv = sum(int(r["unique_visitors"]) for r in rows)
    return pv, uv


def pct(new_val: int, old_val: int) -> str:
    if old_val == 0:
        return "n/a"
    p = (new_val - old_val) / old_val * 100
    sign = "+" if p >= 0 else ""
    return f"{sign}{p:.0f}%"


def last_month_start(d: date) -> date:
    if d.month == 1:
        return d.replace(year=d.year - 1, month=12, day=1)
    return d.replace(month=d.month - 1, day=1)


def month_label(ym: str) -> str:
    y, m = ym.split("-")
    return f"{MONTH_NAMES[int(m)]} {y[2:]}"


# ── Email ─────────────────────────────────────────────────────────────────────

def send_weekly_email(week_start: date, week_end: date, today: date, user: str, password: str):
    week_rows = read_range(week_start, week_end)
    prev_week_rows = read_range(week_start - timedelta(days=7), week_end - timedelta(days=7))
    monthly_rows = read_monthly()

    w_pv, w_uv = aggregate(week_rows)
    pw_pv, pw_uv = aggregate(prev_week_rows)

    # MTD: 1. des Monats bis gestern
    month_start = today.replace(day=1)
    mtd_rows = read_range(month_start, week_end)
    mtd_pv, mtd_uv = aggregate(mtd_rows)

    # Gleiches Zeitfenster im Vormonat
    lm_start = last_month_start(today)
    lm_same_end = lm_start.replace(day=today.day - 1) if today.day > 1 else lm_start
    lm_rows = read_range(lm_start, lm_same_end)
    lm_pv, lm_uv = aggregate(lm_rows)

    subject = f"CEM Traffic {week_start.strftime('%d.%m.')}–{week_end.strftime('%d.%m.%Y')}"

    # Wochentabelle
    week_table = ""
    for r in week_rows:
        d = date.fromisoformat(r["date"])
        week_table += (
            f"<tr><td>{DAY_NAMES[d.weekday()]}, {d.strftime('%d.%m.')}</td>"
            f"<td align='right'>{r['pageviews']}</td>"
            f"<td align='right'>{r['unique_visitors']}</td></tr>\n"
        )

    wow_pv = pct(w_pv, pw_pv)
    wow_uv = pct(w_uv, pw_uv)

    # MTD-Zeile
    mtd_label = f"{MONTH_NAMES[today.month]} {today.year} (1.–{week_end.day}.)"
    lm_label = f"{MONTH_NAMES[lm_start.month]} (1.–{lm_same_end.day}.)"
    mom_pv = pct(mtd_pv, lm_pv)
    mom_uv = pct(mtd_uv, lm_uv)

    # Monatstabelle
    month_table = ""
    for r in monthly_rows:
        label = month_label(r["month"])
        is_current = r["month"] == today.strftime("%Y-%m")
        marker = " *" if is_current else ""
        month_table += (
            f"<tr><td>{label}{marker}</td>"
            f"<td align='right'>{r['pageviews']}</td>"
            f"<td align='right'>{r['unique_visitors']}</td></tr>\n"
        )

    html = f"""<html><body style="font-family:monospace;font-size:14px;color:#222;line-height:1.5">
<h3 style="margin-bottom:2px">China Energy Monitor</h3>
<p style="margin-top:0;color:#666;font-size:12px">{week_start.strftime('%d.%m.%Y')} – {week_end.strftime('%d.%m.%Y')}</p>

<h4 style="margin-bottom:4px">Woche</h4>
<table cellpadding="5" cellspacing="0" border="0">
<tr style="border-bottom:1px solid #ccc">
  <th align="left">Tag</th><th align="right">Pageviews</th><th align="right">Unique</th>
</tr>
{week_table}<tr style="border-top:2px solid #333;font-weight:bold">
  <td>Gesamt</td><td align="right">{w_pv}</td><td align="right">{w_uv}</td>
</tr>
<tr style="color:#666;font-size:12px">
  <td>vs. Vorwoche</td><td align="right">{wow_pv}</td><td align="right">{wow_uv}</td>
</tr>
</table>

<h4 style="margin-bottom:4px;margin-top:20px">Monat bisher</h4>
<table cellpadding="5" cellspacing="0" border="0">
<tr style="border-bottom:1px solid #ccc">
  <th align="left">Zeitraum</th><th align="right">Pageviews</th><th align="right">Unique</th>
</tr>
<tr><td>{mtd_label}</td><td align="right">{mtd_pv}</td><td align="right">{mtd_uv}</td></tr>
<tr><td>{lm_label}</td><td align="right">{lm_pv}</td><td align="right">{lm_uv}</td></tr>
<tr style="color:#666;font-size:12px">
  <td>Veränderung</td><td align="right">{mom_pv}</td><td align="right">{mom_uv}</td>
</tr>
</table>

<h4 style="margin-bottom:4px;margin-top:20px">Monatsverlauf</h4>
<table cellpadding="5" cellspacing="0" border="0">
<tr style="border-bottom:1px solid #ccc">
  <th align="left">Monat</th><th align="right">Pageviews</th><th align="right">Unique</th>
</tr>
{month_table}</table>
<p style="font-size:11px;color:#999;margin-top:4px">* laufender Monat</p>

<p style="margin-top:20px;font-size:11px;color:#bbb">GoatCounter · china-energy-monitor.com</p>
</body></html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = user
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.starttls()
        smtp.login(user, password)
        smtp.sendmail(user, user, msg.as_string())
    print(f"Email sent: {subject}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    token = get_token()
    gmail_user, gmail_password = get_gmail_config()

    today = date.today()
    yesterday = today - timedelta(days=1)

    if already_logged(yesterday):
        print(f"{yesterday} already in CSV, skipping fetch.")
    else:
        row = fetch_day(yesterday, token)
        append_daily(row)

    update_monthly_csv()

    if today.weekday() == 0:  # Montag
        week_end = yesterday
        week_start = week_end - timedelta(days=6)
        send_weekly_email(week_start, week_end, today, gmail_user, gmail_password)


if __name__ == "__main__":
    main()
