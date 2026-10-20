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
  python3 scripts/log_field_income.py --mark-paid 20162091 --push

The scheduled report reads the ledger from the repository, so a job only
counts once the ledger is committed and pushed. --push does that for you
(git add, commit and push of the ledger file only).
"""

import argparse
import csv
import os
import subprocess
import sys
import tempfile
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
    with open(path, newline="", encoding="utf-8") as f:
        header = next(csv.reader(f), COLUMNS)
    with open(path, "a", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=header, extrasaction="ignore", restval="").writerow(row)


def mark_paid(path: str, work_order: str) -> int:
    """Set status=paid on every row for this work order.

    Keeps the file's own header (including any extra columns) and writes a
    temporary file first, replacing the ledger only once the write succeeds.
    """
    ensure_ledger(path)
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        header = list(reader.fieldnames or COLUMNS)
        rows = list(reader)
    changed = 0
    for row in rows:
        if (row.get("work_order") or "").strip() == work_order and row.get("status") != "paid":
            row["status"] = "paid"
            changed += 1
    if not changed:
        return 0
    directory = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".field_income.", suffix=".csv", dir=directory)
    try:
        with os.fdopen(fd, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=header, restval="")
            writer.writeheader()
            writer.writerows(rows)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    return changed


def push_ledger(path: str, message: str) -> bool:
    """Commit and push only the ledger file. Returns True on success."""
    directory = os.path.dirname(os.path.abspath(path)) or "."

    def git(*args):
        return subprocess.run(["git", *args], cwd=directory, capture_output=True, text=True)

    steps = [
        ("add", git("add", os.path.abspath(path))),
    ]
    if steps[-1][1].returncode == 0:
        steps.append(("commit", git("commit", "--only", os.path.abspath(path), "-m", message)))
    if steps[-1][1].returncode == 0:
        steps.append(("push", git("push")))
    name, result = steps[-1]
    if result.returncode != 0:
        print(f"git {name} failed: {(result.stderr or result.stdout).strip()}", file=sys.stderr)
        return False
    print("Ledger committed and pushed; the next scheduled report will include it.")
    return True


def sync_reminder(path: str) -> None:
    print(f"Not yet synced: commit and push {path} (or rerun with --push) so the scheduled report sees it.")


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
    p.add_argument("--push", action="store_true", help="commit and push the ledger after the change")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)

    if args.mark_paid:
        n = mark_paid(args.file, args.mark_paid)
        print(f"Marked {n} row(s) paid for work order {args.mark_paid}")
        if not n:
            return 1
        if args.push:
            return 0 if push_ledger(args.file, f"field income: mark {args.mark_paid} paid") else 3
        sync_reminder(args.file)
        return 0

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
    if args.push:
        message = f"field income: {row['client']} {row['work_order'] or ''} ${row['amount_usd']} on {date}".replace("  ", " ")
        return 0 if push_ledger(args.file, message) else 3
    sync_reminder(args.file)
    return 0


if __name__ == "__main__":
    sys.exit(main())
