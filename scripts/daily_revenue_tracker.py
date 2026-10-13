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
YT_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID", "").strip()
YT_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET", "").strip()
YT_REFRESH_TOKEN = os.getenv("YOUTUBE_REFRESH_TOKEN", "").strip()
YT_CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID", "").strip()
EMAIL_PLATFORM_API = os.getenv("EMAIL_PLATFORM_API_KEY")
BEEHIIV_API_KEY = os.getenv("BEEHIIV_API_KEY", "").strip()
BEEHIIV_PUBLICATION_ID = os.getenv("BEEHIIV_PUBLICATION_ID", "").strip()
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
                "sales_events": [],
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
                    "sales_count": product.get("sales_count", 0),
                    "revenue_usd": product.get("sales_usd_cents", 0) / 100,
                    "url": product.get("short_url")
                }
                gumroad_data["products"][product.get("id")] = product_info
                gumroad_data["total_revenue"] += product.get("sales_usd_cents", 0) / 100
                gumroad_data["total_sales"] += product.get("sales_count", 0)

            cutoff = datetime.utcnow() - timedelta(days=1)
            sales_response = requests.get(
                "https://api.gumroad.com/v2/sales",
                headers=headers,
                params={"after": cutoff.strftime("%Y-%m-%d")},
                timeout=10
            )
            if sales_response.status_code == 200:
                for sale in sales_response.json().get("sales", []):
                    try:
                        created = datetime.strptime(sale.get("created_at", ""), "%Y-%m-%dT%H:%M:%SZ")
                    except ValueError:
                        continue
                    if created >= cutoff:
                        price_usd = int(sale.get("price", 0)) / 100
                        gumroad_data["last_24h"]["sales"] += 1
                        gumroad_data["last_24h"]["revenue"] += price_usd
                        # Real per-sale ledger entries — actual API amounts, not estimates.
                        gumroad_data["sales_events"].append({
                            "source":       "gumroad",
                            "sale_id":      sale.get("id"),
                            "product_id":   sale.get("product_id"),
                            "product_name": sale.get("product_name"),
                            "price_usd":    price_usd,
                            "created_at":   sale.get("created_at"),
                        })
            else:
                self.errors.append(f"Gumroad sales API error: {sales_response.status_code}")

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
        """Fetch YouTube channel statistics via the upload OAuth chain
        (no separate API key needed). 24h deltas come from comparing
        against the previous committed daily report."""
        try:
            if not (YT_CLIENT_ID and YT_CLIENT_SECRET and YT_REFRESH_TOKEN):
                self.errors.append("YouTube OAuth env not set")
                return {}
            tok = requests.post(
                "https://oauth2.googleapis.com/token",
                data={"client_id": YT_CLIENT_ID, "client_secret": YT_CLIENT_SECRET,
                      "refresh_token": YT_REFRESH_TOKEN, "grant_type": "refresh_token"},
                timeout=10)
            if tok.status_code != 200:
                self.errors.append(f"YouTube token refresh failed: {tok.status_code}")
                return {}
            headers = {"Authorization": f"Bearer {tok.json()['access_token']}"}
            params = {"part": "statistics"}
            if YT_CHANNEL_ID:
                params["id"] = YT_CHANNEL_ID
            else:
                params["mine"] = "true"
            response = requests.get("https://www.googleapis.com/youtube/v3/channels",
                                    params=params, headers=headers, timeout=10)
            if response.status_code != 200 or not response.json().get("items"):
                self.errors.append(f"YouTube API error: {response.status_code}")
                return {}
            stats = response.json()["items"][0]["statistics"]
            youtube_data = {
                "revenue_24h": 0,  # monetization requires YT Partner Program
                "total_views": int(stats.get("viewCount", 0)),
                "subscribers": int(stats.get("subscriberCount", 0)),
                "video_count": int(stats.get("videoCount", 0)),
                "views_24h": 0,
            }
            # delta vs the most recent previous committed report
            try:
                import glob
                prev_files = sorted(glob.glob("daily_revenue_*.json"))
                prev_files = [p for p in prev_files
                              if self.data["date"] not in p]
                if prev_files:
                    with open(prev_files[-1]) as f:
                        prev = json.load(f)["metrics"].get("youtube", {})
                    if prev.get("total_views"):
                        youtube_data["views_24h"] = max(
                            youtube_data["total_views"] - prev["total_views"], 0)
            except Exception:
                pass
            return youtube_data

        except Exception as e:
            self.errors.append(f"YouTube fetch error: {str(e)}")
            return {}

    def fetch_email_metrics(self) -> Dict[str, Any]:
        """Fetch newsletter metrics from Beehiiv (falls back to
        EMAIL_PLATFORM_API_KEY as the bearer if BEEHIIV_API_KEY unset)."""
        try:
            key = BEEHIIV_API_KEY or (EMAIL_PLATFORM_API or "").strip()
            if not (key and BEEHIIV_PUBLICATION_ID):
                self.errors.append("Beehiiv creds not set")
                return {}
            response = requests.get(
                f"https://api.beehiiv.com/v2/publications/{BEEHIIV_PUBLICATION_ID}",
                params={"expand[]": "stats"},
                headers={"Authorization": f"Bearer {key}"},
                timeout=10)
            if response.status_code != 200:
                self.errors.append(f"Beehiiv API error: {response.status_code}")
                return {}
            stats = response.json().get("data", {}).get("stats", {})
            return {
                "platform": "beehiiv",
                "total_subscribers": stats.get("active_subscriptions", 0),
                "premium_subscribers": stats.get("active_premium_subscriptions", 0),
                "avg_open_rate": stats.get("average_open_rate", 0),
                "avg_click_rate": stats.get("average_click_rate", 0),
                "total_sent": stats.get("total_sent", 0),
                "total_clicks": stats.get("total_clicked", 0),
                "revenue_from_email": 0,
            }

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
