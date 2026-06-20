"""Tests for YouTube Analytics revenue sync integration.

Tests cover:
- Credential handling (OAuth, refresh token)
- API response parsing
- Transaction logging
- Revenue calculation
- Error handling
"""
import json
import os
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest

from backend.services.youtube_analytics import YouTubeRevenueAnalytics, GOOGLE_API_AVAILABLE


class TestYouTubeRevenueAnalytics:
    """Test YouTube Analytics integration."""

    def test_init_with_env_vars(self):
        """Test initialization with environment variables."""
        with patch.dict(os.environ, {
            "YOUTUBE_CLIENT_ID": "test-client-id",
            "YOUTUBE_CLIENT_SECRET": "test-secret",
            "YOUTUBE_REFRESH_TOKEN": "test-refresh-token",
            "YOUTUBE_CHANNEL_ID": "UCxxxxx",
        }):
            analytics = YouTubeRevenueAnalytics()

            assert analytics.client_id == "test-client-id"
            assert analytics.client_secret == "test-secret"
            assert analytics.refresh_token == "test-refresh-token"
            assert analytics.channel_id == "UCxxxxx"

    def test_init_without_credentials(self):
        """Test initialization without credentials."""
        with patch.dict(os.environ, {
            "YOUTUBE_CLIENT_ID": "",
            "YOUTUBE_CLIENT_SECRET": "",
            "YOUTUBE_REFRESH_TOKEN": "",
        }, clear=False):
            analytics = YouTubeRevenueAnalytics()

            assert analytics.client_id == ""
            assert analytics.client_secret == ""
            assert analytics.refresh_token == ""

    def test_init_with_channel_id_arg(self):
        """Test initialization with explicit channel ID."""
        analytics = YouTubeRevenueAnalytics(channel_id="UCManualChannel")
        assert analytics.channel_id == "UCManualChannel"

    @patch('backend.services.youtube_analytics.OAuthCredentials')
    @patch('backend.services.youtube_analytics.Request')
    def test_get_oauth_credentials_success(self, mock_request, mock_creds_class):
        """Test successful OAuth credential creation."""
        with patch.dict(os.environ, {
            "YOUTUBE_CLIENT_ID": "test-id",
            "YOUTUBE_CLIENT_SECRET": "test-secret",
            "YOUTUBE_REFRESH_TOKEN": "test-token",
        }):
            mock_creds = MagicMock()
            mock_creds_class.return_value = mock_creds

            analytics = YouTubeRevenueAnalytics()
            creds = analytics.get_oauth_credentials()

            assert creds is not None
            mock_creds.refresh.assert_called_once()

    @patch('backend.services.youtube_analytics.GOOGLE_API_AVAILABLE', False)
    def test_get_oauth_credentials_missing_deps(self):
        """Test OAuth credentials when Google libraries unavailable."""
        with patch.dict(os.environ, {
            "YOUTUBE_CLIENT_ID": "test-id",
            "YOUTUBE_CLIENT_SECRET": "test-secret",
            "YOUTUBE_REFRESH_TOKEN": "test-token",
        }):
            analytics = YouTubeRevenueAnalytics()
            creds = analytics.get_oauth_credentials()

            assert creds is None

    def test_fetch_analytics_data_no_credentials(self):
        """Test fetch_analytics_data with missing credentials."""
        with patch.dict(os.environ, {
            "YOUTUBE_CLIENT_ID": "",
            "YOUTUBE_CLIENT_SECRET": "",
            "YOUTUBE_REFRESH_TOKEN": "",
        }, clear=False):
            analytics = YouTubeRevenueAnalytics()
            response = analytics.fetch_analytics_data("2026-06-01", "2026-06-30")

            assert response is None

    @patch('backend.services.youtube_analytics.build')
    @patch('backend.services.youtube_analytics.OAuthCredentials')
    @patch('backend.services.youtube_analytics.Request')
    def test_fetch_analytics_data_success(self, mock_request, mock_creds_class, mock_build):
        """Test successful analytics data fetch."""
        with patch.dict(os.environ, {
            "YOUTUBE_CLIENT_ID": "test-id",
            "YOUTUBE_CLIENT_SECRET": "test-secret",
            "YOUTUBE_REFRESH_TOKEN": "test-token",
        }):
            # Mock the API response
            mock_creds = MagicMock()
            mock_creds_class.return_value = mock_creds

            mock_service = MagicMock()
            mock_build.return_value = mock_service

            mock_response = {
                "columnHeaders": [
                    {"name": "day"},
                    {"name": "earnings"},
                ],
                "rows": [
                    ["2026-06-01", "45.67"],
                    ["2026-06-02", "38.23"],
                ]
            }
            mock_service.reports().query().execute.return_value = mock_response

            analytics = YouTubeRevenueAnalytics()
            response = analytics.fetch_analytics_data("2026-06-01", "2026-06-30")

            assert response == mock_response

    @patch('backend.services.youtube_analytics.build')
    @patch('backend.services.youtube_analytics.OAuthCredentials')
    @patch('backend.services.youtube_analytics.Request')
    def test_fetch_adsense_revenue_parsing(self, mock_request, mock_creds_class, mock_build):
        """Test AdSense revenue parsing from API response."""
        with patch.dict(os.environ, {
            "YOUTUBE_CLIENT_ID": "test-id",
            "YOUTUBE_CLIENT_SECRET": "test-secret",
            "YOUTUBE_REFRESH_TOKEN": "test-token",
        }):
            mock_creds = MagicMock()
            mock_creds_class.return_value = mock_creds

            mock_service = MagicMock()
            mock_build.return_value = mock_service

            # Mock API response with earnings column
            mock_response = {
                "columnHeaders": [
                    {"name": "day"},
                    {"name": "earnings"},
                    {"name": "views"},
                ],
                "rows": [
                    ["2026-06-01", "45.67", "1000"],
                    ["2026-06-02", "38.23", "800"],
                    ["2026-06-03", "52.10", "1200"],
                ]
            }
            mock_service.reports().query().execute.return_value = mock_response

            analytics = YouTubeRevenueAnalytics()
            revenue = analytics.fetch_adsense_revenue(2026, 6)

            # Should sum all earnings: 45.67 + 38.23 + 52.10 = 136.0
            assert revenue is not None
            assert abs(revenue - 136.0) < 0.01

    def test_log_revenue(self, tmp_path, monkeypatch):
        """Test revenue logging to JSONL file."""
        monkeypatch.setenv("YOUTUBE_CHANNEL_ID", "UCTestChannel")
        analytics = YouTubeRevenueAnalytics(channel_id="UCTestChannel")
        analytics.runtime_dir = tmp_path

        transaction = analytics.log_revenue(
            amount_usd=145.50,
            year=2026,
            month=6,
            timestamp="2026-06-19T08:00:00+00:00"
        )

        assert transaction is not None
        assert transaction["channel"] == "youtube"
        assert transaction["amount_usd"] == 145.50
        assert transaction["date"] == "2026-06-01"
        assert transaction["source_id"].startswith("youtube_adsense_")
        assert transaction["metadata"]["channel_id"] == "UCTestChannel"
        assert transaction["metadata"]["year"] == 2026
        assert transaction["metadata"]["month"] == 6

        # Check file was written
        transaction_file = tmp_path / "transactions.jsonl"
        assert transaction_file.exists()

        with open(transaction_file) as f:
            logged = json.loads(f.readline())
            assert logged["channel"] == "youtube"
            assert logged["amount_usd"] == 145.50

    def test_log_revenue_with_empty_amount(self, tmp_path):
        """Test that zero revenue is logged."""
        analytics = YouTubeRevenueAnalytics()
        analytics.runtime_dir = tmp_path

        # Even zero revenue should be logged (for audit trail)
        transaction = analytics.log_revenue(0.0, 2026, 6)

        assert transaction is not None
        assert transaction["amount_usd"] == 0.0

    def test_get_all_transactions(self, tmp_path):
        """Test reading YouTube transactions from ledger."""
        analytics = YouTubeRevenueAnalytics()
        analytics.runtime_dir = tmp_path

        # Log some transactions
        analytics.log_revenue(100.0, 2026, 6)
        analytics.log_revenue(150.0, 2026, 7)

        transactions = analytics.get_all_transactions()

        assert len(transactions) == 2
        assert all(tx["channel"] == "youtube" for tx in transactions)
        assert transactions[0]["amount_usd"] == 100.0
        assert transactions[1]["amount_usd"] == 150.0

    @patch.object(YouTubeRevenueAnalytics, 'fetch_adsense_revenue')
    def test_sync_revenue_with_data(self, mock_fetch, tmp_path):
        """Test sync_revenue when data is available."""
        mock_fetch.return_value = 245.75

        analytics = YouTubeRevenueAnalytics()
        analytics.runtime_dir = tmp_path
        amount = analytics.sync_revenue(2026, 6)

        assert amount == 245.75
        mock_fetch.assert_called_once_with(2026, 6)

        # Verify it was logged
        transactions = analytics.get_all_transactions()
        assert len(transactions) == 1
        assert transactions[0]["amount_usd"] == 245.75

    @patch.object(YouTubeRevenueAnalytics, 'fetch_adsense_revenue')
    def test_sync_revenue_no_data(self, mock_fetch, tmp_path):
        """Test sync_revenue when no data available."""
        mock_fetch.return_value = None

        analytics = YouTubeRevenueAnalytics()
        analytics.runtime_dir = tmp_path
        amount = analytics.sync_revenue(2026, 6)

        assert amount is None

        # Verify nothing was logged
        transactions = analytics.get_all_transactions()
        assert len(transactions) == 0

    @patch.object(YouTubeRevenueAnalytics, 'sync_revenue')
    def test_sync_current_month(self, mock_sync):
        """Test sync_current_month_revenue."""
        mock_sync.return_value = 300.0

        analytics = YouTubeRevenueAnalytics()
        amount = analytics.sync_current_month_revenue()

        assert amount == 300.0
        mock_sync.assert_called_once()

        # Verify year/month passed to sync
        call_args = mock_sync.call_args
        assert call_args[0][0] == datetime.utcnow().year
        assert call_args[0][1] == datetime.utcnow().month


class TestYouTubeAnalyticsIntegration:
    """Integration tests with real file I/O."""

    def test_end_to_end_sync_flow(self, tmp_path):
        """Test complete sync flow from fetch to log."""
        with patch.dict(os.environ, {
            "YOUTUBE_CLIENT_ID": "test-id",
            "YOUTUBE_CLIENT_SECRET": "test-secret",
            "YOUTUBE_REFRESH_TOKEN": "test-token",
        }):
            with patch('backend.services.youtube_analytics.build') as mock_build:
                with patch('backend.services.youtube_analytics.OAuthCredentials'):
                    with patch('backend.services.youtube_analytics.Request'):
                        # Setup mock API response
                        mock_service = MagicMock()
                        mock_build.return_value = mock_service

                        mock_response = {
                            "columnHeaders": [
                                {"name": "day"},
                                {"name": "earnings"},
                            ],
                            "rows": [
                                ["2026-06-01", "50.00"],
                                ["2026-06-02", "75.50"],
                            ]
                        }
                        mock_service.reports().query().execute.return_value = mock_response

                        analytics = YouTubeRevenueAnalytics()
                        analytics.runtime_dir = tmp_path
                        amount = analytics.sync_revenue(2026, 6)

                        assert amount == 125.50

                        # Verify transaction was logged
                        transactions = analytics.get_all_transactions()
                        assert len(transactions) == 1
                        assert transactions[0]["amount_usd"] == 125.50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
