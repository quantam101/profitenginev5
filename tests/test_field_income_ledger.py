"""Field income ledger: tracker reads it, logger writes it, non-errors stay out of errors."""

import csv
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _ledger(tmp_path, rows):
    path = tmp_path / "field_income.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date", "platform", "client", "work_order", "description", "amount_usd", "status"])
        w.writerows(rows)
    return path


def _tracker(monkeypatch, path, today="2026-10-21"):
    monkeypatch.setenv("FIELD_INCOME_FILE", str(path))
    mod = _load("daily_revenue_tracker_under_test", "scripts/daily_revenue_tracker.py")
    t = mod.RevenueTracker()
    t.data["date"] = today
    return t


def test_field_income_totals(tmp_path, monkeypatch):
    path = _ledger(tmp_path, [
        ["2026-10-21", "Field Nation", "Retail Tech", "20162091", "register install", "130.00", "completed"],
        ["2026-10-21", "Direct", "Acme Clinics", "INV-1", "retainer", "2000", "paid"],
        ["2026-10-05", "Field Nation", "ITI", "19999999", "TV swap", "$1,050.50", "approved"],
        ["2026-09-30", "WorkMarket", "Velocity", "WM-1", "printer", "240", "paid"],
        ["2026-10-20", "Field Nation", "ITI", "X", "cancelled job", "500", "cancelled"],
    ])
    t = _tracker(monkeypatch, path)
    field = t.fetch_field_income()
    assert field["last_24h"]["revenue"] == 2130.0
    assert field["total_revenue"] == 2130.0
    assert field["month_to_date"] == 3180.5
    assert field["year_to_date"] == 3420.5
    assert field["jobs_month_to_date"] == 3
    assert field["unpaid_total"] == 1180.5
    assert field["by_platform_mtd"] == {"Field Nation": 1180.5, "Direct": 2000.0}
    assert field["ledger_rows"] == 4
    assert t.errors == []


def test_bad_rows_are_reported_not_counted(tmp_path, monkeypatch):
    path = _ledger(tmp_path, [
        ["2026-10-21", "Field Nation", "Retail Tech", "1", "ok", "100", "completed"],
        ["21/10/2026", "Field Nation", "Retail Tech", "2", "bad date", "100", "completed"],
        ["2026-10-21", "Field Nation", "Retail Tech", "3", "bad amount", "lots", "completed"],
    ])
    t = _tracker(monkeypatch, path)
    field = t.fetch_field_income()
    assert field["last_24h"]["revenue"] == 100.0
    assert len(t.errors) == 2


def test_missing_ledger_is_not_an_error(tmp_path, monkeypatch):
    t = _tracker(monkeypatch, tmp_path / "nope.csv")
    assert t.fetch_field_income() == {}
    assert t.errors == []
    assert any("not found" in s for s in t.skipped)


def test_unconfigured_sources_are_skipped_not_errors(tmp_path, monkeypatch):
    for var in ["GUMROAD_ACCESS_TOKEN", "GUMROAD_API_KEY", "STRIPE_SECRET_KEY", "BEEHIIV_API_KEY",
                "EMAIL_PLATFORM_API_KEY", "BEEHIIV_PUBLICATION_ID", "REVENUE_TRACK_YOUTUBE"]:
        monkeypatch.delenv(var, raising=False)
    path = _ledger(tmp_path, [["2026-10-21", "Field Nation", "Retail Tech", "1", "", "130", "completed"]])
    t = _tracker(monkeypatch, path)
    data = t.aggregate_all_metrics()
    assert "errors" not in data
    assert "youtube" not in data["metrics"]
    assert "affiliates" not in data["metrics"] and "trading" not in data["metrics"]
    assert data["consolidated"]["revenue_breakdown"]["field"] == 130.0
    assert data["consolidated"]["total_revenue_24h"] == 130.0
    assert data["consolidated"]["active_revenue_streams"] == 1
    assert len(data["not_configured"]) >= 3


def test_logger_appends_and_marks_paid(tmp_path):
    log = _load("log_field_income_under_test", "scripts/log_field_income.py")
    path = tmp_path / "ledger" / "field_income.csv"
    assert log.main(["--file", str(path), "--date", "2026-10-21", "--platform", "Field Nation",
                     "--client", "Retail Tech", "--wo", "20162091", "--amount", "130",
                     "--desc", "register install"]) == 0
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    assert rows == [{"date": "2026-10-21", "platform": "Field Nation", "client": "Retail Tech",
                     "work_order": "20162091", "description": "register install",
                     "amount_usd": "130.00", "status": "completed"}]
    assert log.main(["--file", str(path), "--mark-paid", "20162091"]) == 0
    assert list(csv.DictReader(open(path, encoding="utf-8")))[0]["status"] == "paid"
    assert log.main(["--file", str(path), "--mark-paid", "nope"]) == 1


def test_logger_rejects_bad_input(tmp_path):
    log = _load("log_field_income_under_test2", "scripts/log_field_income.py")
    path = tmp_path / "f.csv"
    assert log.main(["--file", str(path), "--platform", "FN", "--client", "X"]) == 2
    assert log.main(["--file", str(path), "--platform", "FN", "--client", "X", "--amount", "0"]) == 2
    assert log.main(["--file", str(path), "--platform", "FN", "--client", "X", "--amount", "5",
                     "--date", "10/21/2026"]) == 2
    assert not path.exists() or len(list(csv.reader(open(path)))) <= 1


if __name__ == "__main__":
    sys.exit(__import__("pytest").main([__file__, "-q"]))
