#!/usr/bin/env python3
"""Append one completed field-service job to the field income ledger.

The daily revenue tracker reads this ledger (data/field_income.csv) so
Field Nation, WorkMarket and direct-client income shows up in the
daily revenue report.

Examples:
  python3 scripts/log_field_income.py --platform "Field Nation" \
      --client "Retail Tech" --wo 20162091 --amount 130 \
      --desc "Holiday register install, Chandler"
  python3 scripts/log_field_income.py --date 2026-10-21 --platform Direct \
      --client "Acme Clinics" --amount 2000 --status paid --desc "October retainer"
  python3 scripts/log_field_income.py --mark-paid 20162091
"""

import argparse
import csv
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

COLUMNS = ["date", "platform", "client", "work_order", "description", "amount_usd", "status"]
STATUSES = ["completed", "approved", "paid", "cancelled"]
DEFAULT_FILE = os.getenv("FIELD_INCOME_FILE", "data/field_income.csv")


def today_phoenix() -> str:
    return datetime.now(ZoneInfo("America/Phoenix")).strftime("%Y-%m-%d")


def ensure_ledger(path: str) -> None:
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(COLUMNS)


def append_row(path: str, row: dict) -> None:
    ensure_ledger(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=COLUMNS).writerow(row)


def mark_paid(path: str, work_order: str) -> int:
    ensure_ledger(path)
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    changed = 0
    for row in rows:
        if row.get("work_order", "").strip() == work_order and row.get("status") != "paid":
            row["status"] = "paid"
            changed += 1
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return changed


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--file", default=DEFAULT_FILE, help="ledger path (default: %(default)s)")
    p.add_argument("--mark-paid", metavar="WORK_ORDER", help="mark every row for this work order as paid")
    p.add_argument("--date", default=None, help="work date YYYY-MM-DD (default: today, Arizona time)")
    p.add_argument("--platform", help='e.g. "Field Nation", "WorkMarket", "Direct"')
    p.add_argument("--client", help='e.g. "Retail Tech"')
    p.add_argument("--wo", "--work-order", dest="work_order", default="", help="work order or invoice number")
    p.add_argument("--amount", type=float, help="amount earned in USD")
    p.add_argument("--desc", default="", help="short description of the job")
    p.add_argument("--status", default="completed", choices=STATUSES)
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)

    if args.mark_paid:
        n = mark_paid(args.file, args.mark_paid)
        print(f"Marked {n} row(s) paid for work order {args.mark_paid}")
        return 0 if n else 1

    missing = [name for name in ("platform", "client", "amount") if getattr(args, name) in (None, "")]
    if missing:
        print(f"Missing required option(s): {', '.join('--' + m for m in missing)}", file=sys.stderr)
        return 2
    if args.amount <= 0:
        print("--amount must be greater than 0", file=sys.stderr)
        return 2

    date = args.date or today_phoenix()
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        print("--date must be YYYY-MM-DD", file=sys.stderr)
        return 2

    row = {
        "date": date,
        "platform": args.platform.strip(),
        "client": args.client.strip(),
        "work_order": str(args.work_order).strip(),
        "description": args.desc.strip(),
        "amount_usd": f"{args.amount:.2f}",
        "status": args.status,
    }
    append_row(args.file, row)
    print(f"Logged ${row['amount_usd']} from {row['client']} ({row['platform']}) on {date} to {args.file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
