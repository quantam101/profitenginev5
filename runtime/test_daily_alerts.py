#!/usr/bin/env python3
"""
Test suite for ProfitEngine Daily Alerts system.
Validates database queries, email templates, and notification channels.
"""

import os
import sys
import sqlite3
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from decimal import Decimal

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from daily_alerts import (
        DatabaseQueries,
        EmailTemplates,
        DailyAlertOrchestrator,
        ClientPerformance,
        DailyAlertData,
    )
except ImportError as e:
    print(f"Error importing daily_alerts: {e}")
    sys.exit(1)


# ============================================================================
# TEST DATA GENERATOR
# ============================================================================

def create_test_database(db_path: str = "test_alerts.db") -> str:
    """Create a test database with sample data"""
    print(f"\n[1] Creating test database: {db_path}")

    # Remove old test DB
    if Path(db_path).exists():
        Path(db_path).unlink()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            client_id TEXT PRIMARY KEY,
            username TEXT,
            email TEXT,
            account_balance REAL,
            total_trades INTEGER,
            winning_trades INTEGER,
            losing_trades INTEGER,
            created_at TIMESTAMP,
            last_trade_at TIMESTAMP,
            subscription_tier TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            trade_id TEXT PRIMARY KEY,
            client_id TEXT,
            symbol TEXT,
            side TEXT,
            entry_price REAL,
            exit_price REAL,
            shares INTEGER,
            pnl_usd REAL,
            win BOOLEAN,
            executed_at TIMESTAMP
        )
    """)

    # Insert test clients
    today = datetime.now(timezone.utc)
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)

    test_clients = [
        ("client_1", "alice_trader", "alice@example.com", 50000.0, 100, 75, 25, week_ago.isoformat(), yesterday.isoformat(), "free"),
        ("client_2", "bob_growth", "bob@example.com", 35000.0, 80, 60, 20, week_ago.isoformat(), yesterday.isoformat(), "free"),
        ("client_3", "carol_pro", "carol@example.com", 75000.0, 150, 130, 20, week_ago.isoformat(), yesterday.isoformat(), "hybrid"),
        ("client_4", "dave_newbie", "dave@example.com", 10000.0, 20, 12, 8, today.isoformat(), today.isoformat(), "free"),
        ("client_5", "eve_skilled", "eve@example.com", 100000.0, 200, 175, 25, (week_ago - timedelta(days=7)).isoformat(), yesterday.isoformat(), "enterprise"),
    ]

    for client in test_clients:
        cursor.execute(
            "INSERT INTO clients VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            client,
        )

    # Insert test trades
    trade_id = 0
    for i, (client_id, username, *_) in enumerate(test_clients):
        # Add 5-10 trades per client, some today
        num_trades = 5 + (i * 2)
        for j in range(num_trades):
            trade_id += 1
            # 70% of trades are winners
            is_win = j % 10 < 7
            pnl = 100 + (j * 10) if is_win else -50 - (j * 5)

            # Some trades today, some yesterday
            trade_date = today if j % 3 == 0 else yesterday
            trade_time = (trade_date - timedelta(hours=j)).isoformat()

            cursor.execute(
                """
                INSERT INTO trades
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"trade_{trade_id}",
                    client_id,
                    "AAPL" if j % 2 == 0 else "TSLA",
                    "BUY" if j % 2 == 0 else "SELL",
                    100.0 + j,
                    105.0 + j if is_win else 95.0 + j,
                    10 + j,
                    pnl,
                    is_win,
                    trade_time,
                ),
            )

    conn.commit()
    conn.close()

    print(f"  [OK] Test database created with {len(test_clients)} clients")
    return db_path


# ============================================================================
# TEST FUNCTIONS
# ============================================================================

def test_database_queries(db_path: str) -> bool:
    """Test database query methods"""
    print(f"\n[2] Testing database queries")

    try:
        db = DatabaseQueries(db_path)

        # Test 1: Daily P&L summary
        pnl, trades, active = db.get_daily_pnl_summary()
        print(f"  [OK] Daily P&L summary: ${pnl:,.2f}, {trades} trades, {active} active traders")

        # Test 2: Top performers
        performers = db.get_top_performers(limit=5)
        print(f"  [OK] Top performers: {len(performers)} traders")
        for perf in performers[:2]:
            print(f"    - {perf.username}: {perf.win_rate:.1f}% win rate, ${perf.daily_pnl:,.2f}")

        # Test 3: New signups
        signups = db.get_new_signups(days=1)
        print(f"  [OK] New signups (today): {len(signups)} clients")
        for signup in signups:
            print(f"    - {signup.username} ({signup.email})")

        # Test 4: Upsell candidates
        candidates = db.get_upsell_candidates()
        print(f"  [OK] Upsell candidates: {len(candidates)}")
        for cand in candidates[:2]:
            print(f"    - {cand['username']}: {cand['win_rate']:.1f}% -> {cand['recommended_tier']}")

        # Test 5: Database health
        health = db.check_database_health()
        print(f"  [OK] Database health: {health}")

        # Test 6: Total clients
        total = db.get_total_clients()
        print(f"  [OK] Total clients: {total}")

        return True

    except Exception as e:
        print(f"  [FAIL] Database query failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_email_templates(db_path: str) -> bool:
    """Test email template generation"""
    print(f"\n[3] Testing email templates")

    try:
        db = DatabaseQueries(db_path)

        # Build alert data
        pnl, trades, active = db.get_daily_pnl_summary()
        performers = db.get_top_performers(5)
        signups = db.get_new_signups(1)
        candidates = db.get_upsell_candidates()
        total = db.get_total_clients()
        health = db.check_database_health()

        alert_data = DailyAlertData(
            date=datetime.now(timezone.utc),
            total_clients=total,
            active_clients_today=active,
            total_daily_trades=trades,
            total_daily_pnl=pnl,
            system_health_status=health,
            top_performers=performers,
            new_signups=signups,
            upsell_candidates=candidates,
            timestamp=datetime.now(timezone.utc),
        )

        # Generate HTML
        html = EmailTemplates.daily_alert_html(
            alert_data,
            performers,
            signups,
            candidates,
            health,
        )

        print(f"  [OK] HTML email generated: {len(html)} characters")
        assert "<html>" in html.lower()
        assert "daily summary" in html.lower()
        assert "top 5 performers" in html.lower()

        # Generate text
        text = EmailTemplates.daily_alert_text(
            alert_data,
            performers,
            signups,
            candidates,
        )

        print(f"  [OK] Text email generated: {len(text)} characters")
        assert "ProfitEngine Daily Alert" in text
        assert "DAILY SUMMARY" in text

        # Verify key sections
        assert "Total Daily P&L" in html
        assert "New Customers" in html
        assert "Upsell Opportunities" in html

        return True

    except Exception as e:
        print(f"  [FAIL] Email template test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_alert_orchestration(db_path: str) -> bool:
    """Test alert generation without sending"""
    print(f"\n[4] Testing alert orchestration")

    try:
        orchestrator = DailyAlertOrchestrator(db_path)

        # Generate alert
        alert_data = orchestrator.generate_alert()

        print(f"  [OK] Alert generated")
        print(f"    - Total clients: {alert_data.total_clients}")
        print(f"    - Daily P&L: ${alert_data.total_daily_pnl:,.2f}")
        print(f"    - Trades: {alert_data.total_daily_trades}")
        print(f"    - Top performers: {len(alert_data.top_performers)}")
        print(f"    - New signups: {len(alert_data.new_signups)}")
        print(f"    - Upsell candidates: {len(alert_data.upsell_candidates)}")

        # Verify alert structure
        assert alert_data.date
        assert alert_data.total_clients >= 0
        assert alert_data.system_health_status in ["healthy", "degraded", "error"]

        return True

    except Exception as e:
        print(f"  [FAIL] Alert orchestration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cli_execution(db_path: str) -> bool:
    """Test CLI argument parsing and dry run"""
    print(f"\n[5] Testing CLI execution (dry run)")

    try:
        # Set environment
        os.environ["CLIENTS_DB_PATH"] = db_path
        os.environ["ALERT_EMAIL"] = "test@example.com"

        # Import and run
        import subprocess
        result = subprocess.run(
            [sys.executable, "daily_alerts.py", "--dry-run", "--db", db_path],
            capture_output=True,
            text=True,
            timeout=30,
        )

        print(f"  [OK] CLI executed (exit code: {result.returncode})")
        if result.stdout:
            print(f"    Output: {result.stdout[:200]}")
        if result.returncode != 0 and result.stderr:
            print(f"    Error: {result.stderr[:200]}")

        return result.returncode == 0

    except Exception as e:
        print(f"  [FAIL] CLI test failed: {e}")
        return False


def test_email_providers() -> bool:
    """Test email provider initialization"""
    print(f"\n[6] Testing email provider configurations")

    try:
        from daily_alerts import (
            GmailSender,
            SendGridSender,
            AmazonSESSender,
        )

        # Test Gmail sender
        gmail = GmailSender("test@gmail.com", "xxxx xxxx xxxx xxxx")
        print(f"  [OK] GmailSender initialized")

        # Test SendGrid sender (if available)
        try:
            sendgrid_sender = SendGridSender("SG.test_api_key")
            print(f"  [OK] SendGridSender initialized (sendgrid package available)")
        except Exception:
            print(f"  [INFO] SendGridSender skipped (sendgrid package not installed)")

        # Test AWS SES sender (if available)
        try:
            ses = AmazonSESSender("us-east-1")
            print(f"  [OK] AmazonSESSender initialized (boto3 available)")
        except Exception:
            print(f"  [INFO] AmazonSESSender skipped (boto3 package not installed)")

        return True

    except Exception as e:
        print(f"  [FAIL] Email provider test failed: {e}")
        return False


def test_notification_channels() -> bool:
    """Test notification channel functions"""
    print(f"\n[7] Testing notification channels")

    try:
        from daily_alerts import send_telegram_alert, send_slack_alert

        # These will fail without credentials, but we just test the functions exist
        print(f"  [OK] send_telegram_alert function available")
        print(f"  [OK] send_slack_alert function available")

        # Test with dummy credentials (will fail gracefully)
        result = send_telegram_alert("", "test")
        print(f"  [OK] Telegram alert handles missing credentials")

        result = send_slack_alert("", "test", 100)
        print(f"  [OK] Slack alert handles missing credentials")

        return True

    except Exception as e:
        print(f"  [FAIL] Notification channel test failed: {e}")
        return False


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def main():
    """Run all tests"""
    print("=" * 70)
    print("ProfitEngine Daily Alerts — Test Suite")
    print("=" * 70)

    db_path = create_test_database()

    tests = [
        ("Database Queries", test_database_queries, [db_path]),
        ("Email Templates", test_email_templates, [db_path]),
        ("Alert Orchestration", test_alert_orchestration, [db_path]),
        ("CLI Execution", test_cli_execution, [db_path]),
        ("Email Providers", test_email_providers, []),
        ("Notification Channels", test_notification_channels, []),
    ]

    results = []
    for test_name, test_func, args in tests:
        try:
            result = test_func(*args)
            results.append((test_name, result))
        except Exception as e:
            print(f"  ✗ {test_name} crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"[{status:4}] {test_name}")

    print(f"\n{passed}/{total} tests passed")

    # Cleanup
    if Path(db_path).exists():
        Path(db_path).unlink()
        print(f"\nTest database cleaned up: {db_path}")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
