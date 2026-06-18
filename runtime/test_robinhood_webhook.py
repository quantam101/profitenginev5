"""
TEST SUITE — Robinhood Webhook Handler
======================================

Tests for webhook signature validation, idempotency, P&L calculation, and alerts.

Usage:
    python test_robinhood_webhook.py

    Or with pytest:
    pytest test_robinhood_webhook.py -v

Requirements:
    pip install pytest pytest-asyncio httpx
"""

import asyncio
import hashlib
import hmac
import json
import sqlite3
import time
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from pathlib import Path
import tempfile

import pytest
from fastapi.testclient import TestClient

from robinhood_webhook_handler import (
    app,
    DatabaseManager,
    WebhookHandler,
    WebhookPayload,
    validate_webhook_signature,
    verify_timestamp_freshness,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def test_db():
    """Create temporary test database"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    db = DatabaseManager(db_path)
    yield db

    # Cleanup
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def webhook_secret():
    """Test webhook secret"""
    return "test-webhook-secret-123"


@pytest.fixture
def client(test_db, webhook_secret, monkeypatch):
    """FastAPI test client with test database"""
    monkeypatch.setenv("ROBINHOOD_WEBHOOK_SECRET", webhook_secret)
    monkeypatch.setenv("CLIENTS_DB_PATH", test_db.db_path)

    # Patch the database manager in the app module
    from robinhood_webhook_handler import db_manager
    db_manager.db_path = test_db.db_path

    return TestClient(app)


# ============================================================================
# SIGNATURE VALIDATION TESTS
# ============================================================================

class TestSignatureValidation:
    """Tests for HMAC-SHA256 signature validation"""

    def test_valid_signature(self, webhook_secret):
        """Test valid signature passes validation"""
        timestamp = "2026-06-18T14:30:00Z"
        payload = b'{"event_type":"order_filled"}'

        signed_message = f"{timestamp}.{payload.decode()}"
        signature = hmac.new(
            webhook_secret.encode(),
            signed_message.encode(),
            hashlib.sha256
        ).hexdigest()

        assert validate_webhook_signature(payload, signature, timestamp) is True

    def test_invalid_signature(self, webhook_secret):
        """Test invalid signature fails validation"""
        timestamp = "2026-06-18T14:30:00Z"
        payload = b'{"event_type":"order_filled"}'
        invalid_signature = "invalid_signature_abc123"

        assert validate_webhook_signature(payload, invalid_signature, timestamp) is False

    def test_tampered_payload(self, webhook_secret):
        """Test signature fails if payload is tampered with"""
        timestamp = "2026-06-18T14:30:00Z"
        original_payload = b'{"event_type":"order_filled"}'
        tampered_payload = b'{"event_type":"order_rejected"}'

        # Create signature with original payload
        signed_message = f"{timestamp}.{original_payload.decode()}"
        signature = hmac.new(
            webhook_secret.encode(),
            signed_message.encode(),
            hashlib.sha256
        ).hexdigest()

        # Signature should fail with tampered payload
        assert validate_webhook_signature(tampered_payload, signature, timestamp) is False

    def test_timestamp_mismatch(self, webhook_secret):
        """Test signature fails if timestamp is changed"""
        original_timestamp = "2026-06-18T14:30:00Z"
        different_timestamp = "2026-06-18T14:31:00Z"
        payload = b'{"event_type":"order_filled"}'

        # Create signature with original timestamp
        signed_message = f"{original_timestamp}.{payload.decode()}"
        signature = hmac.new(
            webhook_secret.encode(),
            signed_message.encode(),
            hashlib.sha256
        ).hexdigest()

        # Signature should fail with different timestamp
        assert validate_webhook_signature(payload, signature, different_timestamp) is False


# ============================================================================
# TIMESTAMP VERIFICATION TESTS
# ============================================================================

class TestTimestampVerification:
    """Tests for replay attack prevention"""

    def test_fresh_timestamp(self):
        """Test recent timestamp passes verification"""
        now = datetime.now(timezone.utc)
        timestamp = now.isoformat()
        assert verify_timestamp_freshness(timestamp) is True

    def test_old_timestamp(self):
        """Test old timestamp fails verification"""
        old_time = datetime.now(timezone.utc) - timedelta(minutes=10)
        timestamp = old_time.isoformat()
        assert verify_timestamp_freshness(timestamp) is False

    def test_future_timestamp(self):
        """Test timestamp too far in future fails"""
        future_time = datetime.now(timezone.utc) + timedelta(minutes=10)
        timestamp = future_time.isoformat()
        assert verify_timestamp_freshness(timestamp) is False

    def test_clock_skew_tolerance(self):
        """Test small clock skew is tolerated"""
        # 30 second clock skew should be OK
        future_time = datetime.now(timezone.utc) + timedelta(seconds=30)
        timestamp = future_time.isoformat()
        assert verify_timestamp_freshness(timestamp) is True


# ============================================================================
# IDEMPOTENCY TESTS
# ============================================================================

class TestIdempotency:
    """Tests for idempotent event processing"""

    def test_duplicate_event_not_reprocessed(self, test_db):
        """Test duplicate events are not reprocessed"""
        event_id = "evt_123"
        event_type = "order_filled"
        account_id = "acc_xyz"
        payload = {"symbol": "AAPL"}

        # First insertion should succeed
        result1 = test_db.record_webhook_event(event_id, event_type, account_id, payload)
        assert result1 is True

        # Second insertion should fail (already exists)
        result2 = test_db.record_webhook_event(event_id, event_type, account_id, payload)
        assert result2 is False

    def test_webhook_idempotency_endpoint(self, client, webhook_secret):
        """Test webhook endpoint is idempotent"""
        timestamp = datetime.now(timezone.utc).isoformat()
        event_id = f"evt_test_{int(time.time())}"

        payload = {
            "event_type": "order_filled",
            "event_id": event_id,
            "timestamp": timestamp,
            "account_id": "acc_xyz",
            "symbol": "AAPL",
            "side": "buy",
            "quantity": 10,
            "filled_quantity": 10,
            "avg_fill_price": 150.25
        }

        payload_json = json.dumps(payload)
        signed_message = f"{timestamp}.{payload_json}"
        signature = hmac.new(
            webhook_secret.encode(),
            signed_message.encode(),
            hashlib.sha256
        ).hexdigest()

        # First request
        response1 = client.post(
            "/webhook/robinhood",
            content=payload_json,
            headers={
                "Content-Type": "application/json",
                "X-Robinhood-Signature": signature,
                "X-Robinhood-Timestamp": timestamp
            }
        )
        assert response1.status_code == 202

        # Second request (same event_id) should also succeed but not reprocess
        response2 = client.post(
            "/webhook/robinhood",
            content=payload_json,
            headers={
                "Content-Type": "application/json",
                "X-Robinhood-Signature": signature,
                "X-Robinhood-Timestamp": timestamp
            }
        )
        assert response2.status_code == 202


# ============================================================================
# DATABASE TESTS
# ============================================================================

class TestDatabase:
    """Tests for database operations"""

    def test_trade_update_with_fill(self, test_db):
        """Test updating trade with fill information"""
        # First need to insert a trade
        with sqlite3.connect(test_db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO trade_log
                (trade_id, user_id, symbol, side, quantity, entry_price,
                 entry_time, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "ord_123", 1, "AAPL", "buy", 10, 150.0,
                datetime.now(timezone.utc).isoformat(),
                "open", datetime.now(timezone.utc).isoformat(),
                datetime.now(timezone.utc).isoformat()
            ))
            conn.commit()

        # Update with fill
        result = test_db.update_trade_with_fill(
            trade_id="ord_123",
            symbol="AAPL",
            filled_qty=10,
            avg_fill_price=151.50,
            commission=1.00
        )

        assert result is not None
        assert result["status"] == "filled"
        assert result["exit_price"] == 151.50
        assert result["pnl"] == 10.50  # (10 * 151.50) - 1.00

    def test_balance_update(self, test_db):
        """Test recording balance changes"""
        result = test_db.update_user_balance(
            user_id=1,
            previous_balance=10000.0,
            current_balance=10050.0,
            available_cash=9000.0,
            margin_used=1000.0
        )
        assert result is True

        # Verify in database
        with sqlite3.connect(test_db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM balance_history WHERE user_id = 1")
            row = cursor.fetchone()
            assert row is not None
            assert row[3] == 10050.0  # current_balance

    def test_alert_recording(self, test_db):
        """Test recording alerts"""
        alert_id = test_db.record_alert(
            user_id=1,
            alert_type="daily_loss_limit",
            severity="critical",
            message="Daily loss exceeded",
            threshold=100.0,
            current_value=-105.0
        )

        assert alert_id.startswith("alert_1_")

        # Verify in database
        with sqlite3.connect(test_db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM alerts WHERE alert_id = ?", (alert_id,))
            row = cursor.fetchone()
            assert row is not None
            assert row[4] == "critical"  # severity

    def test_daily_stats_calculation(self, test_db):
        """Test calculating daily trading statistics"""
        today = datetime.now().strftime("%Y-%m-%d")

        # Insert test trades
        with sqlite3.connect(test_db.db_path) as conn:
            cursor = conn.cursor()

            # Winning trade: buy at 150, sell at 155, profit $50
            cursor.execute("""
                INSERT INTO trade_log
                (trade_id, user_id, symbol, side, quantity, entry_price, exit_price,
                 entry_time, status, pnl, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "ord_1", 1, "AAPL", "buy", 10, 150.0, 155.0,
                f"{today}T10:00:00Z", "closed", 50.0,
                f"{today}T10:00:00Z", f"{today}T10:30:00Z"
            ))

            # Losing trade: buy at 160, sell at 158, loss $20
            cursor.execute("""
                INSERT INTO trade_log
                (trade_id, user_id, symbol, side, quantity, entry_price, exit_price,
                 entry_time, status, pnl, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "ord_2", 1, "TSLA", "buy", 10, 160.0, 158.0,
                f"{today}T11:00:00Z", "closed", -20.0,
                f"{today}T11:00:00Z", f"{today}T11:30:00Z"
            ))

            conn.commit()

        # Calculate stats
        stats = test_db.get_user_daily_stats(1)

        assert stats["total_trades"] == 2
        assert stats["winning_trades"] == 1
        assert stats["losing_trades"] == 1
        assert stats["win_rate"] == 50.0
        assert stats["total_pnl"] == 30.0


# ============================================================================
# WEBHOOK HANDLER TESTS
# ============================================================================

class TestWebhookHandler:
    """Tests for webhook event processing"""

    @pytest.mark.asyncio
    async def test_handle_order_filled(self, test_db):
        """Test handling order_filled event"""
        handler = WebhookHandler(test_db)

        # Create test trade first
        with sqlite3.connect(test_db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO trade_log
                (trade_id, user_id, symbol, side, quantity, entry_price,
                 entry_time, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "ord_123", 1, "AAPL", "buy", 10, 150.0,
                datetime.now(timezone.utc).isoformat(),
                "open", datetime.now(timezone.utc).isoformat(),
                datetime.now(timezone.utc).isoformat()
            ))
            conn.commit()

        payload = WebhookPayload(
            event_type="order_filled",
            event_id="evt_123",
            timestamp=datetime.now(timezone.utc).isoformat(),
            account_id="acc_xyz",
            order_id="ord_123",
            symbol="AAPL",
            side="buy",
            quantity=10,
            filled_quantity=10,
            avg_fill_price=151.50,
            commission=1.00
        )

        success, message = await handler.process_webhook(payload)
        assert success is True

    @pytest.mark.asyncio
    async def test_margin_call_alert(self, test_db):
        """Test margin call alert triggering"""
        handler = WebhookHandler(test_db)

        payload = WebhookPayload(
            event_type="margin_call",
            event_id="evt_margin",
            timestamp=datetime.now(timezone.utc).isoformat(),
            account_id="acc_xyz",
            margin_used=5000.0,
            buying_power=0.0,
            alert_level="critical",
            alert_message="Margin call - liquidation may occur"
        )

        success, message = await handler.process_webhook(payload)
        assert success is True

        # Verify alert was recorded
        with sqlite3.connect(test_db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM alerts
                WHERE alert_type = 'margin_call' AND severity = 'critical'
            """)
            row = cursor.fetchone()
            assert row is not None


# ============================================================================
# API ENDPOINT TESTS
# ============================================================================

class TestAPIEndpoints:
    """Tests for FastAPI endpoints"""

    def test_webhook_status(self, client):
        """Test GET /webhook/status endpoint"""
        response = client.get("/webhook/status")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "webhook_events" in data
        assert "trades" in data
        assert "alerts" in data

    def test_webhook_missing_signature(self, client):
        """Test webhook fails without signature"""
        payload = {"event_type": "order_filled"}

        response = client.post(
            "/webhook/robinhood",
            json=payload,
            headers={
                "X-Robinhood-Timestamp": datetime.now(timezone.utc).isoformat()
                # Missing X-Robinhood-Signature
            }
        )

        assert response.status_code == 400

    def test_webhook_invalid_signature(self, client):
        """Test webhook fails with invalid signature"""
        timestamp = datetime.now(timezone.utc).isoformat()
        payload = json.dumps({"event_type": "order_filled"})

        response = client.post(
            "/webhook/robinhood",
            content=payload,
            headers={
                "Content-Type": "application/json",
                "X-Robinhood-Signature": "invalid_signature",
                "X-Robinhood-Timestamp": timestamp
            }
        )

        assert response.status_code == 401

    def test_webhook_stale_timestamp(self, client, webhook_secret):
        """Test webhook fails with stale timestamp"""
        old_timestamp = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
        payload = json.dumps({"event_type": "order_filled"})

        signed_message = f"{old_timestamp}.{payload}"
        signature = hmac.new(
            webhook_secret.encode(),
            signed_message.encode(),
            hashlib.sha256
        ).hexdigest()

        response = client.post(
            "/webhook/robinhood",
            content=payload,
            headers={
                "Content-Type": "application/json",
                "X-Robinhood-Signature": signature,
                "X-Robinhood-Timestamp": old_timestamp
            }
        )

        assert response.status_code == 400

    def test_webhook_success(self, client, webhook_secret):
        """Test successful webhook processing"""
        timestamp = datetime.now(timezone.utc).isoformat()
        event_id = f"evt_test_{int(time.time())}"

        payload = {
            "event_type": "order_filled",
            "event_id": event_id,
            "timestamp": timestamp,
            "account_id": "acc_xyz",
            "symbol": "AAPL",
            "side": "buy",
            "quantity": 10,
            "filled_quantity": 10,
            "avg_fill_price": 150.25
        }

        payload_json = json.dumps(payload)
        signed_message = f"{timestamp}.{payload_json}"
        signature = hmac.new(
            webhook_secret.encode(),
            signed_message.encode(),
            hashlib.sha256
        ).hexdigest()

        response = client.post(
            "/webhook/robinhood",
            content=payload_json,
            headers={
                "Content-Type": "application/json",
                "X-Robinhood-Signature": signature,
                "X-Robinhood-Timestamp": timestamp
            }
        )

        assert response.status_code == 202
        data = response.json()
        assert data["success"] is True
        assert data["event_id"] == event_id


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """End-to-end integration tests"""

    def test_full_trade_workflow(self, client, webhook_secret, test_db):
        """Test complete trade workflow: order -> fill -> close"""
        timestamp = datetime.now(timezone.utc).isoformat()
        trade_id = f"ord_{int(time.time())}"

        # 1. Order filled event
        fill_event = {
            "event_type": "order_filled",
            "event_id": f"evt_fill_{trade_id}",
            "timestamp": timestamp,
            "account_id": "acc_xyz",
            "order_id": trade_id,
            "symbol": "AAPL",
            "side": "buy",
            "quantity": 10,
            "filled_quantity": 10,
            "avg_fill_price": 150.0,
            "commission": 1.00
        }

        # Insert test trade
        with sqlite3.connect(test_db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO trade_log
                (trade_id, user_id, symbol, side, quantity, entry_price,
                 entry_time, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trade_id, 1, "AAPL", "buy", 10, 150.0,
                timestamp, "open", timestamp, timestamp
            ))
            conn.commit()

        # Send fill event
        payload_json = json.dumps(fill_event)
        signed_message = f"{timestamp}.{payload_json}"
        signature = hmac.new(
            webhook_secret.encode(),
            signed_message.encode(),
            hashlib.sha256
        ).hexdigest()

        response = client.post(
            "/webhook/robinhood",
            content=payload_json,
            headers={
                "Content-Type": "application/json",
                "X-Robinhood-Signature": signature,
                "X-Robinhood-Timestamp": timestamp
            }
        )

        assert response.status_code == 202

        # 2. Check trade status
        response = client.get(f"/trades/daily/1")
        assert response.status_code == 200
        data = response.json()
        assert data["statistics"]["total_trades"] >= 1


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
