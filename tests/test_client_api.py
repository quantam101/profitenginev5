"""
Tests for Client API endpoints
Validates stats, leaderboards, upsell candidates, performance, and daily summary
"""

import pytest
import asyncio
import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from runtime.client_api import (
    ClientDB, app, API_KEY_HASH, verify_api_key, verify_webhook_signature,
    RateLimiter, decode_pnl
)
from fastapi.testclient import TestClient


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def temp_db():
    """Create temporary SQLite database for testing"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    # Patch the database path
    with patch("runtime.client_api.DB_PATH", db_path):
        db = ClientDB(db_path)
        yield db
        # Cleanup
        import os
        if os.path.exists(db_path):
            os.remove(db_path)


@pytest.fixture
def sample_data(temp_db):
    """Populate database with sample trading data"""
    with temp_db.get_connection() as conn:
        cursor = conn.cursor()

        # Insert clients
        clients = [
            ("user_1", "trader_alice", "alice@example.com", "active", "free"),
            ("user_2", "trader_bob", "bob@example.com", "active", "standard"),
            ("user_3", "trader_charlie", "charlie@example.com", "active", "free"),
        ]
        for user_id, username, email, status, tier in clients:
            account_created = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
            cursor.execute(
                "INSERT INTO clients (user_id, username, email, account_created, account_status, tier) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, username, email, account_created, status, tier),
            )

        # Insert trades for user_1
        for i in range(20):
            entry_time = (datetime.now(timezone.utc) - timedelta(days=20, hours=i)).isoformat()
            exit_time = (datetime.now(timezone.utc) - timedelta(days=20, hours=i, minutes=30)).isoformat()
            pnl = 100.0 if i % 3 == 0 else -50.0
            cursor.execute(
                "INSERT INTO trades "
                "(trade_id, user_id, symbol, side, entry_price, exit_price, shares, pnl, pnl_percent, entry_time, exit_time, status) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    f"trade_user1_{i}",
                    "user_1",
                    "AAPL",
                    "BUY",
                    150.0,
                    151.5 if pnl > 0 else 149.5,
                    10,
                    pnl,
                    (pnl / (150.0 * 10)) * 100,
                    entry_time,
                    exit_time,
                    "closed",
                ),
            )

        # Insert trades for user_2
        for i in range(30):
            entry_time = (datetime.now(timezone.utc) - timedelta(days=15, hours=i)).isoformat()
            exit_time = (datetime.now(timezone.utc) - timedelta(days=15, hours=i, minutes=45)).isoformat()
            pnl = 150.0 if i % 2 == 0 else -75.0
            cursor.execute(
                "INSERT INTO trades "
                "(trade_id, user_id, symbol, side, entry_price, exit_price, shares, pnl, pnl_percent, entry_time, exit_time, status) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    f"trade_user2_{i}",
                    "user_2",
                    "MSFT",
                    "SELL",
                    300.0,
                    298.5 if pnl > 0 else 301.5,
                    5,
                    pnl,
                    (pnl / (300.0 * 5)) * 100,
                    entry_time,
                    exit_time,
                    "closed",
                ),
            )

        # Insert trades for today
        today = datetime.now(timezone.utc)
        for i in range(10):
            entry_time = (today - timedelta(hours=i)).isoformat()
            exit_time = (today - timedelta(hours=i, minutes=15)).isoformat()
            pnl = 200.0 if i % 2 == 0 else -100.0
            cursor.execute(
                "INSERT INTO trades "
                "(trade_id, user_id, symbol, side, entry_price, exit_price, shares, pnl, pnl_percent, entry_time, exit_time, status) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    f"trade_today_{i}",
                    "user_1" if i % 2 == 0 else "user_2",
                    "GOOGL",
                    "BUY",
                    2800.0,
                    2808.0 if pnl > 0 else 2792.0,
                    1,
                    pnl,
                    (pnl / 2800.0) * 100,
                    entry_time,
                    exit_time,
                    "closed",
                ),
            )

        conn.commit()

    return temp_db


@pytest.fixture
def client_api(sample_data):
    """Create FastAPI test client"""
    with patch("runtime.client_api.client_db", sample_data):
        return TestClient(app)


@pytest.fixture
def valid_auth_header():
    """Generate valid authorization header for testing"""
    # Default dev key used in tests
    import hashlib
    api_key = "dev-key-change-in-production"
    return f"Bearer {api_key}"


# ============================================================================
# UNIT TESTS
# ============================================================================

class TestAuthentication:
    """Test API authentication"""

    def test_verify_api_key_valid(self):
        """Test valid API key verification"""
        api_key = "dev-key-change-in-production"
        assert verify_api_key(api_key) is True

    def test_verify_api_key_invalid(self):
        """Test invalid API key verification"""
        assert verify_api_key("wrong-key") is False

    def test_verify_webhook_signature_valid(self):
        """Test valid webhook signature"""
        import hmac
        import hashlib
        secret = "test-secret"
        body = b"test body"
        signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        with patch("runtime.client_api.WEBHOOK_SECRET", secret):
            assert verify_webhook_signature(body, signature) is True

    def test_verify_webhook_signature_invalid(self):
        """Test invalid webhook signature"""
        with patch("runtime.client_api.WEBHOOK_SECRET", "test-secret"):
            assert verify_webhook_signature(b"test body", "wrong-signature") is False


class TestRateLimiter:
    """Test rate limiting"""

    def test_rate_limiter_allows_within_limit(self):
        """Test that requests within limit are allowed"""
        limiter = RateLimiter(requests=5, window=10)
        for _ in range(5):
            assert limiter.is_allowed("test_id") is True

    def test_rate_limiter_blocks_over_limit(self):
        """Test that requests over limit are blocked"""
        limiter = RateLimiter(requests=3, window=10)
        for _ in range(3):
            limiter.is_allowed("test_id")
        assert limiter.is_allowed("test_id") is False

    def test_rate_limiter_resets_after_window(self):
        """Test that rate limiter resets after window expires"""
        limiter = RateLimiter(requests=2, window=1)
        assert limiter.is_allowed("test_id") is True
        assert limiter.is_allowed("test_id") is True
        assert limiter.is_allowed("test_id") is False

        # Wait for window to expire
        import time
        time.sleep(1.1)
        assert limiter.is_allowed("test_id") is True


class TestHelpers:
    """Test helper functions"""

    def test_decode_pnl_float(self):
        """Test decoding float PnL"""
        assert decode_pnl(123.45) == 123.45

    def test_decode_pnl_string(self):
        """Test decoding string PnL"""
        assert decode_pnl("123.45") == 123.45

    def test_decode_pnl_none(self):
        """Test decoding None PnL"""
        assert decode_pnl(None) == 0.0

    def test_decode_pnl_zero(self):
        """Test decoding zero PnL"""
        assert decode_pnl(0) == 0.0


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_check_no_auth(self, client_api):
        """Health check should work without authentication"""
        response = client_api.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["service"] == "client-api"
        assert data["version"] == "1.0.0"
        assert "timestamp" in data


class TestStatsEndpoint:
    """Test aggregate stats endpoint"""

    def test_stats_missing_auth(self, client_api):
        """Should reject requests without auth header"""
        response = client_api.get("/api/clients/stats")
        assert response.status_code == 401

    def test_stats_invalid_auth(self, client_api):
        """Should reject invalid API key"""
        response = client_api.get(
            "/api/clients/stats",
            headers={"Authorization": "Bearer invalid-key"},
        )
        assert response.status_code == 403

    def test_stats_valid_request(self, client_api, valid_auth_header):
        """Should return stats with valid auth"""
        response = client_api.get(
            "/api/clients/stats",
            headers={"Authorization": valid_auth_header},
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_traders" in data
        assert "active_traders" in data
        assert "avg_win_rate" in data
        assert "total_pnl" in data
        assert "total_trades" in data
        assert "timestamp" in data

    def test_stats_values(self, client_api, valid_auth_header):
        """Validate stat values"""
        response = client_api.get(
            "/api/clients/stats?days=30",
            headers={"Authorization": valid_auth_header},
        )
        data = response.json()
        assert data["total_traders"] == 3
        assert data["active_traders"] >= 2  # At least users with trades
        assert data["total_trades"] > 0
        assert isinstance(data["avg_win_rate"], float)


class TestLeaderboardEndpoint:
    """Test leaderboard endpoint"""

    def test_leaderboard_missing_auth(self, client_api):
        """Should reject requests without auth"""
        response = client_api.get("/api/clients/leaderboard")
        assert response.status_code == 401

    def test_leaderboard_valid_request(self, client_api, valid_auth_header):
        """Should return leaderboard with valid auth"""
        response = client_api.get(
            "/api/clients/leaderboard",
            headers={"Authorization": valid_auth_header},
        )
        assert response.status_code == 200
        data = response.json()
        assert "metric" in data
        assert "entries" in data
        assert "timestamp" in data

    def test_leaderboard_metrics(self, client_api, valid_auth_header):
        """Test all leaderboard metrics"""
        for metric in ["win_rate", "pnl", "days_active", "total_trades"]:
            response = client_api.get(
                f"/api/clients/leaderboard?metric={metric}",
                headers={"Authorization": valid_auth_header},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["metric"] == metric

    def test_leaderboard_limit(self, client_api, valid_auth_header):
        """Test limit parameter"""
        response = client_api.get(
            "/api/clients/leaderboard?limit=2",
            headers={"Authorization": valid_auth_header},
        )
        data = response.json()
        assert len(data["entries"]) <= 2


class TestUpsellCandidatesEndpoint:
    """Test upsell candidates endpoint"""

    def test_upsell_candidates_valid_request(self, client_api, valid_auth_header):
        """Should return upsell candidates"""
        response = client_api.get(
            "/api/clients/upsell-candidates",
            headers={"Authorization": valid_auth_header},
        )
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert "candidates" in data
        assert "timestamp" in data

    def test_upsell_candidates_structure(self, client_api, valid_auth_header):
        """Validate candidate structure"""
        response = client_api.get(
            "/api/clients/upsell-candidates",
            headers={"Authorization": valid_auth_header},
        )
        data = response.json()
        if data["count"] > 0:
            candidate = data["candidates"][0]
            assert "user_id" in candidate
            assert "current_pnl" in candidate
            assert "win_rate" in candidate
            assert "urgency" in candidate
            assert candidate["urgency"] in ["low", "medium", "high"]


class TestTraderPerformanceEndpoint:
    """Test individual trader performance endpoint"""

    def test_trader_performance_not_found(self, client_api, valid_auth_header):
        """Should return 404 for non-existent trader"""
        response = client_api.get(
            "/api/clients/nonexistent",
            headers={"Authorization": valid_auth_header},
        )
        assert response.status_code == 404

    def test_trader_performance_valid(self, client_api, valid_auth_header):
        """Should return performance for valid trader"""
        response = client_api.get(
            "/api/clients/user_1",
            headers={"Authorization": valid_auth_header},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "user_1"
        assert "total_trades" in data
        assert "win_rate" in data
        assert "total_pnl" in data
        assert "consecutive_wins" in data
        assert "consecutive_losses" in data

    def test_trader_performance_calculations(self, client_api, valid_auth_header):
        """Validate performance calculations"""
        response = client_api.get(
            "/api/clients/user_1",
            headers={"Authorization": valid_auth_header},
        )
        data = response.json()
        assert data["total_trades"] == (data["winning_trades"] + data["losing_trades"])
        assert data["win_rate"] <= 100.0
        assert data["win_rate"] >= 0.0


class TestDailySummaryEndpoint:
    """Test daily summary endpoint"""

    def test_daily_summary_valid_request(self, client_api, valid_auth_header):
        """Should return daily summary"""
        response = client_api.get(
            "/api/clients/daily-summary",
            headers={"Authorization": valid_auth_header},
        )
        assert response.status_code == 200
        data = response.json()
        assert "date" in data
        assert "total_trades" in data
        assert "total_pnl" in data
        assert "win_rate" in data
        assert "active_users" in data
        assert "timestamp" in data

    def test_daily_summary_structure(self, client_api, valid_auth_header):
        """Validate daily summary structure"""
        response = client_api.get(
            "/api/clients/daily-summary",
            headers={"Authorization": valid_auth_header},
        )
        data = response.json()
        assert isinstance(data["trades_by_user"], dict)
        assert isinstance(data["pnl_by_user"], dict)
        assert isinstance(data["recent_trades"], list)


class TestErrorHandling:
    """Test error handling"""

    def test_invalid_metric_parameter(self, client_api, valid_auth_header):
        """Should reject invalid metric"""
        response = client_api.get(
            "/api/clients/leaderboard?metric=invalid",
            headers={"Authorization": valid_auth_header},
        )
        assert response.status_code == 422  # Validation error

    def test_invalid_limit_parameter(self, client_api, valid_auth_header):
        """Should reject limit < 1"""
        response = client_api.get(
            "/api/clients/leaderboard?limit=0",
            headers={"Authorization": valid_auth_header},
        )
        assert response.status_code == 422

    def test_invalid_days_parameter(self, client_api, valid_auth_header):
        """Should reject days > 365"""
        response = client_api.get(
            "/api/clients/stats?days=400",
            headers={"Authorization": valid_auth_header},
        )
        assert response.status_code == 422


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestPerformance:
    """Test API performance"""

    def test_stats_response_time(self, client_api, valid_auth_header):
        """Stats endpoint should respond within reasonable time"""
        import time
        start = time.time()
        response = client_api.get(
            "/api/clients/stats",
            headers={"Authorization": valid_auth_header},
        )
        elapsed = time.time() - start
        assert elapsed < 1.0  # Should respond in under 1 second
        assert response.status_code == 200

    def test_leaderboard_response_time(self, client_api, valid_auth_header):
        """Leaderboard should respond within reasonable time"""
        import time
        start = time.time()
        response = client_api.get(
            "/api/clients/leaderboard",
            headers={"Authorization": valid_auth_header},
        )
        elapsed = time.time() - start
        assert elapsed < 1.0
        assert response.status_code == 200


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
