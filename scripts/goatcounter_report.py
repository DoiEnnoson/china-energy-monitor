#!/usr/bin/env python3
"""
goatcounter_report.py
Pulls yesterday's GoatCounter data, appends to data/traffic_log.csv.
On Mondays: sends weekly summary email via Gmail SMTP.

GitHub Secrets required:
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
CSV_PATH = Path(__file__).parent.parent / "data" / "traffic_log.csv"
CSV_HEADER = ["date", "pageviews", "unique_visitors"]


def get_token():
    token = os.environ.get("GOATCOUNTER", "")
    if not token:
        sys.exit("GOATCOUNTER secret not set")
    return token


def get_gmail_config():
    cfg = os.environ.get("GMAIL_CONFIG", "")
    if not cfg or ":" not in cfg:
        sys.exit("GMAIL_CONFIG secret not set or malformed (expected user@gmail.com:password)")
    user, password = cfg.split(":", 1)
    return user.strip(), password.strip()


def fetch_day(day: date, token: str) -> dict:
    url = f"https://{SITE}/api/v0/stats/hits"
    r = requests.get(
        url,
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


def already_logged(day: date) -> bool:
    if not CSV_PATH.exists():
        return False
    with open(CSV_PATH, newline="") as f:
        return any(row["date"] == str(day) for row in csv.DictReader(f))


def append_to_csv(row: dict):
    write_header = not CSV_PATH.exists()
    with open(CSV_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
        if write_header:
            writer.writeheader()
        writer.writerow(row)
    print(f"Logged: {row}")


def read_week(start: date, end: date) -> list:
    if not CSV_PATH.exists():
        return []
    with open(CSV_PATH, newline="") as f:
        rows = [
            r for r in csv.DictReader(f)
            if start <= date.fromisoformat(r["date"]) <= end
        ]
    return sorted(rows, key=lambda r: r["date"])


def send_weekly_email(week_start: date, week_end: date, rows: list, user: str, password: str):
    total_pv = sum(int(r["pageviews"]) for r in rows)
    total_uv = sum(int(r["unique_visitors"]) for r in rows)
    subject = f"CEM Traffic {week_start.strftime('%d.%m.')}–{week_end.strftime('%d.%m.%Y')}"

    day_names = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
    table_rows = ""
    for r in rows:
        d = date.fromisoformat(r["date"])
        table_rows += (
            f"<tr><td>{day_names[d.weekday()]}, {d.strftime('%d.%m.')}</td>"
            f"<td align='right'>{r['pageviews']}</td>"
            f"<td align='right'>{r['unique_visitors']}</td></tr>\n"
        )

    html = f"""<html><body style="font-family:monospace;font-size:14px;color:#222">
<h3 style="margin-bottom:4px">China Energy Monitor</h3>
<p style="margin-top:0;color:#666">{week_start.strftime('%d.%m.%Y')} – {week_end.strftime('%d.%m.%Y')}</p>
<table cellpadding="6" cellspacing="0" border="0">
<tr style="border-bottom:1px solid #ccc">
  <th align="left">Tag</th><th align="right">Pageviews</th><th align="right">Unique Visitors</th>
</tr>
{table_rows}<tr style="border-top:2px solid #333;font-weight:bold">
  <td>Gesamt</td><td align="right">{total_pv}</td><td align="right">{total_uv}</td>
</tr>
</table>
<p style="margin-top:16px;font-size:11px;color:#999">GoatCounter · china-energy-monitor.com</p>
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


def main():
    token = get_token()
    gmail_user, gmail_password = get_gmail_config()

    today = date.today()
    yesterday = today - timedelta(days=1)

    if already_logged(yesterday):
        print(f"{yesterday} already in CSV, skipping fetch.")
    else:
        row = fetch_day(yesterday, token)
        append_to_csv(row)

    if today.weekday() == 0:  # Monday
        week_end = yesterday           # Sunday
        week_start = week_end - timedelta(days=6)  # Monday
        rows = read_week(week_start, week_end)
        if rows:
            send_weekly_email(week_start, week_end, rows, gmail_user, gmail_password)
        else:
            print(f"No data for {week_start}–{week_end}, skipping email.")


if __name__ == "__main__":
    main()
