"""YouTube Analytics API integration for AdSense revenue tracking."""
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# Google API imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.service_account import Credentials
    from google.auth.oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
except ImportError:
    # Optional dependency - graceful degradation
    pass


class YouTubeRevenueAnalytics:
    """Fetch AdSense revenue from YouTube Analytics API."""

    def __init__(self):
        """Initialize YouTube Analytics client."""
        self.client_id = os.environ.get("YOUTUBE_CLIENT_ID", "")
        self.client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET", "")
        self.refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN", "")
        self.channel_id = "UCRx7YOYr0bpOD7V3b1P8T3A"  # Set to actual channel if available

    def get_credentials(self):
        """Get valid credentials for YouTube Analytics API."""
        if not self.refresh_token or not self.client_id or not self.client_secret:
            return None

        try:
            from google.oauth2.credentials import Credentials

            creds = Credentials(
                token=None,
                refresh_token=self.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret,
            )
            return creds
        except Exception as e:
            print(f"⚠️ Failed to create YouTube credentials: {e}")
            return None

    def fetch_monthly_revenue(self, year: int, month: int) -> Optional[float]:
        """Fetch AdSense revenue for a specific month."""
        creds = self.get_credentials()
        if not creds:
            print("⚠️ YouTube credentials not configured")
            return None

        try:
            service = build("youtubeAnalytics", "v2", credentials=creds)

            # Date range for the month
            start_date = f"{year:04d}-{month:02d}-01"
            end_date = (
                datetime(year, month, 1) + timedelta(days=32)
            ).replace(day=1) - timedelta(days=1)
            end_date = end_date.strftime("%Y-%m-%d")

            # Query for revenue metrics
            request = service.reports().query(
                ids="channel==MINE",
                start_date=start_date,
                end_date=end_date,
                metrics="estimatedMinutesWatched,views,likes,comments,shares",
                dimensions="day",
            )

            response = request.execute()
            print(f"✅ YouTube Analytics fetched for {year}-{month:02d}")
            print(f"   Data: {response}")

            # Parse revenue from response (YouTube API structure varies)
            # This is a placeholder - actual revenue is in separate AdSense API
            return None

        except Exception as e:
            print(f"❌ Failed to fetch YouTube revenue: {e}")
            return None

    def fetch_adsense_revenue(self) -> Optional[dict]:
        """Fetch AdSense revenue for current month."""
        # AdSense revenue requires separate Google AdSense API credentials
        # This is a placeholder for the integration
        print("📊 AdSense revenue sync would go here")
        print(f"   Client ID: {self.client_id[:20]}..." if self.client_id else "   Client ID: Not configured")
        return None

    def log_revenue(self, amount_usd: float, timestamp: Optional[str] = None):
        """Log YouTube revenue to transaction file."""
        if not timestamp:
            timestamp = datetime.utcnow().isoformat() + "+00:00"

        transaction = {
            "channel": "youtube",
            "amount_usd": amount_usd,
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "source_id": f"youtube_adsense_{datetime.utcnow().timestamp()}",
            "description": "YouTube AdSense monthly revenue",
            "content_id": None,
            "metadata": {"revenue_type": "adsense", "channel_id": self.channel_id},
            "created_at": timestamp,
        }

        runtime_dir = Path(__file__).parent.parent.parent / ".runtime" / "revenue"
        runtime_dir.mkdir(parents=True, exist_ok=True)

        transaction_path = runtime_dir / "transactions.jsonl"
        with open(transaction_path, "a") as f:
            f.write(json.dumps(transaction) + "\n")

        print(f"✅ YouTube revenue logged: ${amount_usd:.2f}")
        return transaction

    def sync_monthly_revenue(self):
        """Sync revenue for current month."""
        now = datetime.utcnow()
        print(f"📊 Syncing YouTube revenue for {now.year}-{now.month:02d}...")

        # Try to fetch from AdSense API
        revenue = self.fetch_adsense_revenue()

        if revenue and isinstance(revenue, dict):
            amount = revenue.get("earnings_usd", 0)
            if amount > 0:
                self.log_revenue(amount)
                return amount
        else:
            print("⚠️ AdSense revenue not available via API")

        return None


def main():
    """Standalone script to sync YouTube revenue."""
    analytics = YouTubeRevenueAnalytics()

    # Sync this month's revenue
    amount = analytics.sync_monthly_revenue()

    if amount:
        print(f"✅ Synced ${amount:.2f} from YouTube AdSense")
    else:
        print("⚠️ No revenue data available yet (new channel or API not fully configured)")

    return 0 if amount else 1


if __name__ == "__main__":
    sys.exit(main())
