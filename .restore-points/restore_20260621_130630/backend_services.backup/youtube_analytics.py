"""YouTube Analytics API integration for AdSense revenue tracking.

Fetches AdSense earnings from the YouTube Analytics API and logs to JSONL.
Supports both OAuth 2.0 and service account credentials.
"""
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials as OAuthCredentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False
    logger.warning("Google API client libraries not installed. YouTube Analytics will be unavailable.")

GOOGLE_OAUTH_TOKEN_URI = "https://oauth2.googleapis.com/token"


class YouTubeRevenueAnalytics:
    """Fetch AdSense revenue from YouTube Analytics API.

    Supports OAuth 2.0 refresh token flow for channel owners.
    Logs all transactions to .runtime/revenue/transactions.jsonl
    """

    # YouTube Analytics API metrics for AdSense revenue
    REVENUE_METRICS = "estimatedMinutesWatched,views,likes,comments,shares,earnings,adsense_revenue"

    def __init__(self, channel_id: Optional[str] = None):
        """Initialize YouTube Analytics client.

        Args:
            channel_id: Optional YouTube channel ID. If not provided, uses YOUTUBE_CHANNEL_ID env var.
        """
        self.client_id = os.environ.get("YOUTUBE_CLIENT_ID", "")
        self.client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET", "")
        self.refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN", "")
        self.channel_id = channel_id or os.environ.get("YOUTUBE_CHANNEL_ID", "")
        self.google_api_available = GOOGLE_API_AVAILABLE

        # Runtime directory for storing transactions
        self.runtime_dir = Path(__file__).parent.parent.parent / ".runtime" / "revenue"
        self.runtime_dir.mkdir(parents=True, exist_ok=True)

    def get_oauth_credentials(self) -> Optional[OAuthCredentials]:
        """Get valid OAuth 2.0 credentials using refresh token.

        Returns:
            OAuth2 credentials object or None if not configured.
        """
        if not self.refresh_token or not self.client_id or not self.client_secret:
            logger.warning("YouTube OAuth credentials not fully configured (client_id, client_secret, refresh_token)")
            return None

        if not self.google_api_available:
            logger.error("Google API libraries not available")
            return None

        try:
            creds = OAuthCredentials(
                token=None,
                refresh_token=self.refresh_token,
                token_uri=GOOGLE_OAUTH_TOKEN_URI,
                client_id=self.client_id,
                client_secret=self.client_secret,
            )

            # Refresh the token to get a valid access token
            request = Request()
            creds.refresh(request)

            logger.info("✅ YouTube OAuth credentials refreshed successfully")
            return creds
        except Exception as e:
            logger.error(f"❌ Failed to create/refresh YouTube credentials: {e}")
            return None

    def fetch_analytics_data(self, start_date: str, end_date: str) -> Optional[Dict[str, Any]]:
        """Fetch analytics data from YouTube Analytics API.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            Raw response from YouTube Analytics API or None on error.
        """
        creds = self.get_oauth_credentials()
        if not creds:
            logger.warning("Skipping YouTube Analytics fetch: credentials unavailable")
            return None

        try:
            service = build("youtubeAnalytics", "v2", credentials=creds)

            logger.info(f"Querying YouTube Analytics from {start_date} to {end_date}")

            request = service.reports().query(
                ids="channel==MINE",
                start_date=start_date,
                end_date=end_date,
                metrics=self.REVENUE_METRICS,
                dimensions="day",
            )

            response = request.execute()
            logger.info("✅ YouTube Analytics API response received")
            return response

        except HttpError as e:
            logger.error(f"YouTube Analytics API error: {e.resp.status} - {e.content}")
            return None
        except Exception as e:
            logger.error(f"❌ Failed to fetch YouTube Analytics: {e}")
            return None

    def fetch_adsense_revenue(self, year: int, month: int) -> Optional[float]:
        """Fetch AdSense revenue for a specific month via YouTube Analytics API.

        Note: YouTube Analytics API exposes AdSense revenue under the 'estimatedRevenue'
        or 'earnings' metric. The exact metric name depends on API version and account setup.

        Args:
            year: Year (YYYY)
            month: Month (1-12)

        Returns:
            Total AdSense revenue in USD or None if unavailable.
        """
        # Calculate date range for the month
        start_date = f"{year:04d}-{month:02d}-01"

        # Last day of month: add 32 days to 1st, then subtract to get last day
        month_end = datetime(year, month, 1) + timedelta(days=32)
        month_end = month_end.replace(day=1) - timedelta(days=1)
        end_date = month_end.strftime("%Y-%m-%d")

        response = self.fetch_analytics_data(start_date, end_date)
        if not response:
            logger.warning(f"No analytics data for {year}-{month:02d}")
            return None

        # Parse revenue from response
        # YouTube Analytics API returns rows with metrics in this structure:
        # {
        #   "columnHeaders": [{"name": "day"}, {"name": "earnings"}, ...],
        #   "rows": [["2026-06-01", "45.67", ...], ...]
        # }
        try:
            total_revenue = 0.0
            column_headers = response.get("columnHeaders", [])
            rows = response.get("rows", [])

            if not rows:
                logger.warning(f"No analytics rows for {year}-{month:02d}")
                return 0.0

            # Find the index of earnings/estimatedRevenue column
            earnings_index = None
            for i, header in enumerate(column_headers):
                col_name = header.get("name", "").lower()
                if col_name in ["earnings", "estimatedrevenue", "adsense_revenue"]:
                    earnings_index = i
                    break

            if earnings_index is None:
                logger.warning("No earnings column found in YouTube Analytics response")
                logger.debug(f"Available columns: {[h.get('name') for h in column_headers]}")
                return None

            # Sum earnings across all days in the month
            for row in rows:
                try:
                    if earnings_index < len(row):
                        earnings_str = str(row[earnings_index])
                        # Handle both "45.67" and "45,67" formats
                        earnings_value = float(earnings_str.replace(",", "."))
                        total_revenue += earnings_value
                except (ValueError, IndexError) as e:
                    logger.debug(f"Could not parse earnings value from row: {e}")
                    continue

            logger.info(f"Calculated total AdSense revenue for {year}-{month:02d}: ${total_revenue:.2f}")
            return total_revenue if total_revenue > 0 else None

        except Exception as e:
            logger.error(f"Error parsing YouTube Analytics response: {e}")
            return None

    def log_revenue(self, amount_usd: float, year: int, month: int,
                    timestamp: Optional[str] = None) -> Dict[str, Any]:
        """Log YouTube AdSense revenue to transaction ledger.

        Args:
            amount_usd: Revenue amount in USD
            year: Year of the revenue
            month: Month of the revenue
            timestamp: Optional ISO 8601 timestamp. Defaults to current UTC time.

        Returns:
            Transaction record as dict.
        """
        if not timestamp:
            timestamp = datetime.utcnow().isoformat() + "+00:00"

        transaction = {
            "channel": "youtube",
            "amount_usd": float(amount_usd),
            "date": f"{year:04d}-{month:02d}-01",
            "source_id": f"youtube_adsense_{year}_{month:02d}_{int(datetime.utcnow().timestamp())}",
            "description": f"YouTube AdSense revenue - {year}-{month:02d}",
            "content_id": None,
            "metadata": {
                "revenue_type": "adsense",
                "channel_id": self.channel_id or "unknown",
                "year": year,
                "month": month,
            },
            "created_at": timestamp,
        }

        transaction_path = self.runtime_dir / "transactions.jsonl"
        try:
            with open(transaction_path, "a") as f:
                f.write(json.dumps(transaction) + "\n")
            logger.info(f"✅ YouTube revenue logged: ${amount_usd:.2f} for {year}-{month:02d}")
        except IOError as e:
            logger.error(f"Failed to write transaction log: {e}")
            return None

        return transaction

    def sync_current_month_revenue(self) -> Optional[float]:
        """Sync AdSense revenue for the current month.

        Returns:
            Amount synced in USD or None if no new data.
        """
        now = datetime.utcnow()
        return self.sync_revenue(now.year, now.month)

    def sync_revenue(self, year: int, month: int) -> Optional[float]:
        """Sync AdSense revenue for a specific month.

        Args:
            year: Year (YYYY)
            month: Month (1-12)

        Returns:
            Amount synced in USD or None if no revenue found.
        """
        logger.info(f"📊 Syncing YouTube AdSense revenue for {year}-{month:02d}...")

        # Fetch revenue from YouTube Analytics API
        amount = self.fetch_adsense_revenue(year, month)

        if amount and amount > 0:
            self.log_revenue(amount, year, month)
            logger.info(f"✅ Synced ${amount:.2f} from YouTube AdSense for {year}-{month:02d}")
            return amount
        else:
            logger.warning(f"⚠️ No AdSense revenue data available for {year}-{month:02d}")
            return None

    def get_all_transactions(self) -> list:
        """Read all YouTube transactions from ledger.

        Returns:
            List of transaction dicts logged to this service.
        """
        transaction_path = self.runtime_dir / "transactions.jsonl"
        transactions = []

        if not transaction_path.exists():
            return transactions

        try:
            with open(transaction_path, "r") as f:
                for line in f:
                    if line.strip():
                        tx = json.loads(line)
                        if tx.get("channel") == "youtube":
                            transactions.append(tx)
        except IOError as e:
            logger.error(f"Failed to read transaction log: {e}")

        return transactions


def main():
    """Standalone script to sync YouTube AdSense revenue.

    Usage:
        python -m backend.services.youtube_analytics          # Current month
        python backend/services/youtube_analytics.py 2026 6   # Specific month
    """
    import argparse

    parser = argparse.ArgumentParser(description="YouTube AdSense revenue sync")
    parser.add_argument("year", nargs="?", type=int, help="Year (YYYY)")
    parser.add_argument("month", nargs="?", type=int, help="Month (1-12)")
    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    analytics = YouTubeRevenueAnalytics()

    if args.year and args.month:
        # Sync specific month
        amount = analytics.sync_revenue(args.year, args.month)
    else:
        # Sync current month
        amount = analytics.sync_current_month_revenue()

    if amount:
        print(f"✅ Synced ${amount:.2f} from YouTube AdSense")
        return 0
    else:
        print("⚠️ No revenue data available (check API credentials and channel setup)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
