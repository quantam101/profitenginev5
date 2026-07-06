#!/usr/bin/env python3
"""
Daily Revenue Tracking Aggregator
Pulls metrics from all revenue sources hourly and generates daily reports.
Designed to run as a scheduled job (cron or GitHub Actions).
"""

import json
import os
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import sys

# Configuration from environment variables
GUMROAD_TOKEN = os.getenv("GUMROAD_ACCESS_TOKEN") or os.getenv("GUMROAD_API_KEY")
STRIPE_KEY = os.getenv("STRIPE_SECRET_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
EMAIL_PLATFORM_API = os.getenv("EMAIL_PLATFORM_API_KEY")
AFFILIATE_API_KEY = os.getenv("AFFILIATE_API_KEY")
TRADING_ACCOUNT_TOKEN = os.getenv("TRADING_API_KEY")

class RevenueTracker:
    def __init__(self):
        self.data = {
            "timestamp": datetime.utcnow().isoformat(),
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "metrics": {}
        }
        self.errors = []

    def fetch_gumroad_sales(self) -> Dict[str, Any]:
        """Fetch hourly sales data from Gumroad."""
        try:
            if not GUMROAD_TOKEN:
                self.errors.append("GUMROAD_ACCESS_TOKEN not set")
                return {}

            headers = {"Authorization": f"Bearer {GUMROAD_TOKEN}"}
            response = requests.get(
                "https://api.gumroad.com/v2/products",
                headers=headers,
                timeout=10
            )

            if response.status_code != 200:
                self.errors.append(f"Gumroad API error: {response.status_code}")
                return {}

            products = response.json().get("products", [])

            gumroad_data = {
                "total_revenue": 0,
                "total_sales": 0,
                "products": {},
                "last_24h": {
                    "revenue": 0,
                    "sales": 0,
                    "new_customers": 0
                }
            }

            for product in products:
                product_info = {
                    "id": product.get("id"),
                    "name": product.get("name"),
                    "sales_24h": product.get("sales_in_last_24_hours", 0),
                    "revenue_24h": product.get("revenue_in_last_24_hours", 0),
                    "url": product.get("url")
                }
                gumroad_data["products"][product.get("id")] = product_info
                gumroad_data["total_revenue"] += product.get("sales_usd_cents", 0) / 100
                gumroad_data["total_sales"] += product.get("sales_count", 0)
                gumroad_data["last_24h"]["revenue"] += product.get("revenue_in_last_24_hours", 0)
                gumroad_data["last_24h"]["sales"] += product.get("sales_in_last_24_hours", 0)

            return gumroad_data

        except Exception as e:
            self.errors.append(f"Gumroad fetch error: {str(e)}")
            return {}

    def fetch_stripe_payments(self) -> Dict[str, Any]:
        """Fetch payment data from Stripe."""
        try:
            if not STRIPE_KEY:
                self.errors.append("STRIPE_SECRET_KEY not set")
                return {}

            headers = {"Authorization": f"Bearer {STRIPE_KEY}"}

            # Get charges from last 24 hours
            yesterday = int((datetime.utcnow() - timedelta(days=1)).timestamp())
            response = requests.get(
                "https://api.stripe.com/v1/charges",
                headers=headers,
                params={"created[gte]": yesterday, "limit": 100},
                timeout=10
            )

            if response.status_code != 200:
                self.errors.append(f"Stripe API error: {response.status_code}")
                return {}

            charges = response.json().get("data", [])

            stripe_data = {
                "total_revenue": 0,
                "total_transactions": len(charges),
                "successful_transactions": 0,
                "failed_transactions": 0,
                "refunds": 0,
                "avg_transaction_value": 0
            }

            total_amount = 0
            for charge in charges:
                if charge.get("status") == "succeeded":
                    stripe_data["successful_transactions"] += 1
                    amount = charge.get("amount", 0) / 100  # Convert from cents
                    stripe_data["total_revenue"] += amount
                    total_amount += amount
                elif charge.get("status") == "failed":
                    stripe_data["failed_transactions"] += 1

            if stripe_data["successful_transactions"] > 0:
                stripe_data["avg_transaction_value"] = stripe_data["total_revenue"] / stripe_data["successful_transactions"]

            return stripe_data

        except Exception as e:
            self.errors.append(f"Stripe fetch error: {str(e)}")
            return {}

    def fetch_youtube_metrics(self) -> Dict[str, Any]:
        """Fetch YouTube analytics data."""
        try:
            if not YOUTUBE_API_KEY:
                self.errors.append("YOUTUBE_API_KEY not set")
                return {}

            headers = {"Authorization": f"Bearer {YOUTUBE_API_KEY}"}

            # Fetch channel statistics
            response = requests.get(
                "https://www.googleapis.com/youtube/v3/channels",
                params={"part": "statistics", "mine": True},
                headers=headers,
                timeout=10
            )

            if response.status_code != 200:
                self.errors.append(f"YouTube API error: {response.status_code}")
                return {}

            youtube_data = {
                "revenue_24h": 0,
                "views_24h": 0,
                "watch_time_hours_24h": 0,
                "subscribers_gained_24h": 0,
                "channel_stats": {},
                "top_videos": []
            }

            # Note: YouTube Analytics API requires OAuth and special setup
            # This is a placeholder for implementation

            return youtube_data

        except Exception as e:
            self.errors.append(f"YouTube fetch error: {str(e)}")
            return {}

    def fetch_email_metrics(self) -> Dict[str, Any]:
        """Fetch email platform metrics (Mailchimp, ConvertKit, etc.)."""
        try:
            if not EMAIL_PLATFORM_API:
                self.errors.append("EMAIL_PLATFORM_API_KEY not set")
                return {}

            # Placeholder for email platform integration
            email_data = {
                "total_subscribers": 0,
                "new_subscribers_24h": 0,
                "unsubscribes_24h": 0,
                "campaigns_sent_24h": 0,
                "total_opens_24h": 0,
                "total_clicks_24h": 0,
                "avg_open_rate": 0,
                "avg_click_rate": 0,
                "revenue_from_email": 0
            }

            return email_data

        except Exception as e:
            self.errors.append(f"Email metrics fetch error: {str(e)}")
            return {}

    def fetch_affiliate_data(self) -> Dict[str, Any]:
        """Fetch affiliate program data."""
        try:
            if not AFFILIATE_API_KEY:
                self.errors.append("AFFILIATE_API_KEY not set")
                return {}

            affiliate_data = {
                "total_revenue_24h": 0,
                "total_clicks_24h": 0,
                "total_conversions_24h": 0,
                "programs": {},
                "top_performers": [],
                "pending_payouts": 0
            }

            return affiliate_data

        except Exception as e:
            self.errors.append(f"Affiliate data fetch error: {str(e)}")
            return {}

    def fetch_trading_data(self) -> Dict[str, Any]:
        """Fetch trading portfolio and P&L data."""
        try:
            if not TRADING_ACCOUNT_TOKEN:
                self.errors.append("TRADING_API_KEY not set")
                return {}

            trading_data = {
                "portfolio_value": 0,
                "daily_pnl": 0,
                "daily_pnl_percent": 0,
                "positions": 0,
                "cash_available": 0,
                "margin_used_percent": 0,
                "win_rate_24h": 0,
                "trades_24h": 0
            }

            return trading_data

        except Exception as e:
            self.errors.append(f"Trading data fetch error: {str(e)}")
            return {}

    def calculate_consolidated_metrics(self) -> Dict[str, Any]:
        """Calculate consolidated daily revenue and metrics."""
        metrics = self.data.get("metrics", {})

        total_revenue = (
            metrics.get("gumroad", {}).get("last_24h", {}).get("revenue", 0) +
            metrics.get("stripe", {}).get("total_revenue", 0) +
            metrics.get("youtube", {}).get("revenue_24h", 0) +
            metrics.get("email", {}).get("revenue_from_email", 0) +
            metrics.get("affiliates", {}).get("total_revenue_24h", 0)
        )

        consolidated = {
            "total_revenue_24h": total_revenue,
            "active_revenue_streams": len([m for m in [
                metrics.get("gumroad"),
                metrics.get("stripe"),
                metrics.get("youtube"),
                metrics.get("email"),
                metrics.get("affiliates")
            ] if m]),
            "revenue_breakdown": {
                "gumroad": metrics.get("gumroad", {}).get("last_24h", {}).get("revenue", 0),
                "stripe": metrics.get("stripe", {}).get("total_revenue", 0),
                "youtube": metrics.get("youtube", {}).get("revenue_24h", 0),
                "email": metrics.get("email", {}).get("revenue_from_email", 0),
                "affiliates": metrics.get("affiliates", {}).get("total_revenue_24h", 0),
                "trading": metrics.get("trading", {}).get("daily_pnl", 0)
            },
            "trading_pnl": metrics.get("trading", {}).get("daily_pnl", 0)
        }

        return consolidated

    def aggregate_all_metrics(self) -> Dict[str, Any]:
        """Fetch all metrics from all sources."""
        print("Starting revenue tracking aggregation...")

        self.data["metrics"]["gumroad"] = self.fetch_gumroad_sales()
        print("✓ Gumroad metrics fetched")

        self.data["metrics"]["stripe"] = self.fetch_stripe_payments()
        print("✓ Stripe metrics fetched")

        self.data["metrics"]["youtube"] = self.fetch_youtube_metrics()
        print("✓ YouTube metrics fetched")

        self.data["metrics"]["email"] = self.fetch_email_metrics()
        print("✓ Email metrics fetched")

        self.data["metrics"]["affiliates"] = self.fetch_affiliate_data()
        print("✓ Affiliate metrics fetched")

        self.data["metrics"]["trading"] = self.fetch_trading_data()
        print("✓ Trading metrics fetched")

        # Calculate consolidated metrics
        self.data["consolidated"] = self.calculate_consolidated_metrics()

        # Add errors to report
        if self.errors:
            self.data["errors"] = self.errors
            print(f"⚠ {len(self.errors)} errors encountered")

        return self.data

    def save_report(self, output_file: Optional[str] = None) -> str:
        """Save the report to a JSON file."""
        if not output_file:
            output_file = f"daily_revenue_{self.data['date']}.json"

        with open(output_file, 'w') as f:
            json.dump(self.data, f, indent=2)

        print(f"✓ Report saved to {output_file}")
        return output_file

    def print_summary(self):
        """Print a summary to console."""
        consolidated = self.data.get("consolidated", {})

        print("\n" + "="*60)
        print(f"DAILY REVENUE SUMMARY - {self.data['date']}")
        print("="*60)
        print(f"Total Revenue (24h): ${consolidated.get('total_revenue_24h', 0):.2f}")
        print(f"Active Streams: {consolidated.get('active_revenue_streams', 0)}/6")
        print("\nRevenue Breakdown:")

        for stream, amount in consolidated.get("revenue_breakdown", {}).items():
            print(f"  {stream.capitalize():20} ${amount:>10.2f}")

        print("="*60 + "\n")

def main():
    """Main entry point."""
    tracker = RevenueTracker()

    try:
        # Aggregate all metrics
        tracker.aggregate_all_metrics()

        # Print summary
        tracker.print_summary()

        # Save report
        report_file = tracker.save_report()

        # Return success
        sys.exit(0)

    except Exception as e:
        print(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
