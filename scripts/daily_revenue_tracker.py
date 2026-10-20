#!/usr/bin/env python3
"""
Daily Revenue Tracking Aggregator
Pulls metrics from all revenue sources hourly and generates daily reports.
Designed to run as a scheduled job (cron or GitHub Actions).
"""

import csv
import json
import os
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Dict, Any, Optional
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
# Field-service income (Field Nation, WorkMarket, direct clients) is the
# business's main revenue. It has no payout API, so it is logged to a CSV
# ledger with scripts/log_field_income.py and read here.
FIELD_INCOME_FILE = os.getenv("FIELD_INCOME_FILE", "data/field_income.csv")
FIELD_INCOME_COLUMNS = ["date", "platform", "client", "work_order", "description", "amount_usd", "status"]
FIELD_INCOME_EXCLUDED_STATUSES = {"cancelled", "canceled", "void"}
# Field jobs are dated by the Arizona work day (the logger uses the same
# zone), and the scheduled run (06:55 UTC = 23:55 Arizona) closes that day.
BUSINESS_TZ = ZoneInfo(os.getenv("FIELD_INCOME_TZ", "America/Phoenix"))
# YouTube has no monetization yet; channel stats are opt-in so a missing or
# expired OAuth token does not read as a revenue failure.
TRACK_YOUTUBE = os.getenv("REVENUE_TRACK_YOUTUBE", "").strip().lower() in {"1", "true", "yes"}

class RevenueTracker:
    def __init__(self):
        self.data = {
            "timestamp": datetime.utcnow().isoformat(),
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "metrics": {}
        }
        self.errors = []      # a configured source failed
        self.skipped = []     # a source is not configured; not a failure
        self.warnings = []    # a non-revenue metric failed
        # Arizona calendar day that field income is reported against.
        self.business_date = datetime.now(BUSINESS_TZ).strftime("%Y-%m-%d")

    def fetch_gumroad_sales(self) -> Dict[str, Any]:
        """Fetch hourly sales data from Gumroad."""
        try:
            if not GUMROAD_TOKEN:
                self.skipped.append("GUMROAD_ACCESS_TOKEN not set")
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
                self.skipped.append("STRIPE_SECRET_KEY not set")
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
                self.skipped.append("YouTube OAuth env not set")
                return {}
            tok = requests.post(
                "https://oauth2.googleapis.com/token",
                data={"client_id": YT_CLIENT_ID, "client_secret": YT_CLIENT_SECRET,
                      "refresh_token": YT_REFRESH_TOKEN, "grant_type": "refresh_token"},
                timeout=10)
            if tok.status_code != 200:
                self.warnings.append(f"YouTube token refresh failed: {tok.status_code}")
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
                self.warnings.append(f"YouTube API error: {response.status_code}")
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
            except Exception as e:
                self.warnings.append(f"YouTube views delta unavailable: {e}")
            return youtube_data

        except Exception as e:
            self.warnings.append(f"YouTube fetch error: {str(e)}")
            return {}

    def fetch_email_metrics(self) -> Dict[str, Any]:
        """Fetch newsletter metrics from Beehiiv (falls back to
        EMAIL_PLATFORM_API_KEY as the bearer if BEEHIIV_API_KEY unset)."""
        try:
            key = BEEHIIV_API_KEY or (EMAIL_PLATFORM_API or "").strip()
            if not (key and BEEHIIV_PUBLICATION_ID):
                self.skipped.append("Beehiiv creds not set")
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

    def fetch_field_income(self) -> Dict[str, Any]:
        """Field-service income from the CSV ledger (see FIELD_INCOME_FILE).

        Each row is one completed job: date (YYYY-MM-DD, the work date),
        platform, client, work_order, description, amount_usd, status.
        Rows whose status is cancelled/void are ignored.
        """
        if not os.path.exists(FIELD_INCOME_FILE):
            self.skipped.append(f"Field income ledger not found: {FIELD_INCOME_FILE}")
            return {}
        try:
            today = self.business_date
            month = today[:7]
            year = today[:4]
            last_24h = month_to_date = year_to_date = unpaid = 0.0
            jobs_mtd = 0
            by_platform: Dict[str, float] = {}
            by_client: Dict[str, float] = {}
            rows = 0
            with open(FIELD_INCOME_FILE, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                missing = [c for c in FIELD_INCOME_COLUMNS if c not in (reader.fieldnames or [])]
                if missing:
                    self.errors.append(f"Field income ledger missing columns: {', '.join(missing)}")
                    return {}
                for line_no, row in enumerate(reader, start=2):
                    status = (row.get("status") or "").strip().lower()
                    if status in FIELD_INCOME_EXCLUDED_STATUSES:
                        continue
                    date = (row.get("date") or "").strip()
                    try:
                        datetime.strptime(date, "%Y-%m-%d")
                        amount = float((row.get("amount_usd") or "").replace("$", "").replace(",", ""))
                    except ValueError:
                        self.errors.append(f"Field income ledger line {line_no}: bad date or amount")
                        continue
                    rows += 1
                    if date == today:
                        last_24h += amount
                    if date.startswith(year):
                        year_to_date += amount
                    if date.startswith(month):
                        month_to_date += amount
                        jobs_mtd += 1
                        platform = (row.get("platform") or "unknown").strip() or "unknown"
                        client = (row.get("client") or "unknown").strip() or "unknown"
                        by_platform[platform] = round(by_platform.get(platform, 0) + amount, 2)
                        by_client[client] = round(by_client.get(client, 0) + amount, 2)
                    if status != "paid":
                        unpaid += amount
            return {
                "source_file": FIELD_INCOME_FILE,
                "business_date": today,
                "total_revenue": round(last_24h, 2),
                "last_24h": {"revenue": round(last_24h, 2)},
                "month_to_date": round(month_to_date, 2),
                "year_to_date": round(year_to_date, 2),
                "jobs_month_to_date": jobs_mtd,
                "unpaid_total": round(unpaid, 2),
                "by_platform_mtd": by_platform,
                "by_client_mtd": by_client,
                "ledger_rows": rows,
            }
        except Exception as e:
            self.errors.append(f"Field income ledger read error: {str(e)}")
            return {}

    def calculate_consolidated_metrics(self) -> Dict[str, Any]:
        """Calculate consolidated daily revenue and metrics."""
        metrics = self.data.get("metrics", {})
        breakdown = {
            "field": metrics.get("field", {}).get("last_24h", {}).get("revenue", 0),
            "gumroad": metrics.get("gumroad", {}).get("last_24h", {}).get("revenue", 0),
            "stripe": metrics.get("stripe", {}).get("total_revenue", 0),
            "email": metrics.get("email", {}).get("revenue_from_email", 0),
        }
        if "youtube" in metrics:
            breakdown["youtube"] = metrics.get("youtube", {}).get("revenue_24h", 0)

        tracked = [name for name in breakdown if metrics.get(name)]
        field = metrics.get("field", {})
        return {
            "total_revenue_24h": round(sum(breakdown.values()), 2),
            "active_revenue_streams": len(tracked),
            "tracked_streams": len(breakdown),
            "revenue_breakdown": breakdown,
            "field_month_to_date": field.get("month_to_date", 0),
            "field_year_to_date": field.get("year_to_date", 0),
            "field_unpaid_total": field.get("unpaid_total", 0),
        }

    def aggregate_all_metrics(self) -> Dict[str, Any]:
        """Fetch all metrics from all sources."""
        print("Starting revenue tracking aggregation...")

        self.data["metrics"]["field"] = self.fetch_field_income()
        print("✓ Field income ledger read")

        self.data["metrics"]["gumroad"] = self.fetch_gumroad_sales()
        print("✓ Gumroad metrics fetched")

        self.data["metrics"]["stripe"] = self.fetch_stripe_payments()
        print("✓ Stripe metrics fetched")

        if TRACK_YOUTUBE:
            self.data["metrics"]["youtube"] = self.fetch_youtube_metrics()
            print("✓ YouTube metrics fetched")

        self.data["metrics"]["email"] = self.fetch_email_metrics()
        print("✓ Email metrics fetched")

        # Calculate consolidated metrics
        self.data["consolidated"] = self.calculate_consolidated_metrics()

        # Add errors to report
        if self.errors:
            self.data["errors"] = self.errors
            print(f"⚠ {len(self.errors)} errors encountered")
        if self.warnings:
            self.data["warnings"] = self.warnings
        if self.skipped:
            self.data["not_configured"] = self.skipped

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
        print(f"Active Streams: {consolidated.get('active_revenue_streams', 0)}/{consolidated.get('tracked_streams', 0)}")
        print(f"Field income MTD: ${consolidated.get('field_month_to_date', 0):.2f}  YTD: ${consolidated.get('field_year_to_date', 0):.2f}  unpaid: ${consolidated.get('field_unpaid_total', 0):.2f}")
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
        tracker.save_report()

        # Return success
        sys.exit(0)

    except Exception as e:
        print(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
