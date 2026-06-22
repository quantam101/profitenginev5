"""
Zero-cost Affiliate Tracking

Tracks:
- Amazon Associates clicks
- Internal product clicks
- Conversion funnels
- Revenue attribution
"""
from datetime import datetime
from typing import Optional
import hashlib
import uuid

class AffiliateTracker:
    """Track affiliate revenue and attribution."""

    def __init__(self, db):
        self.db = db
        self.collection = db.affiliate_clicks if db else None

    async def track_click(
        self,
        source: str,  # blog, email, video, social
        affiliate_program: str,  # amazon, gumroad, etsy
        product_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> str:
        """Log affiliate click and return tracking ID."""

        tracking_id = str(uuid.uuid4())

        click_record = {
            "tracking_id": tracking_id,
            "source": source,
            "program": affiliate_program,
            "product_id": product_id,
            "user_id": user_id,
            "timestamp": datetime.utcnow(),
            "session_id": hashlib.sha256(f"{user_id}{datetime.utcnow()}".encode()).hexdigest(),
            "status": "pending"  # Will be updated when conversion happens
        }

        await self.collection.insert_one(click_record)
        return tracking_id

    async def log_conversion(
        self,
        tracking_id: str,
        amount_usd: float,
        commission_rate: float
    ) -> dict:
        """Log conversion and calculate commission."""

        commission = amount_usd * commission_rate

        await self.collection.update_one(
            {"tracking_id": tracking_id},
            {
                "$set": {
                    "status": "converted",
                    "amount_usd": amount_usd,
                    "commission_rate": commission_rate,
                    "commission_usd": commission,
                    "converted_at": datetime.utcnow()
                }
            }
        )

        return {
            "tracking_id": tracking_id,
            "amount": amount_usd,
            "commission": commission,
            "status": "logged"
        }

    async def get_stats(self, days: int = 30) -> dict:
        """Get affiliate stats for period."""
        from datetime import timedelta

        start_date = datetime.utcnow() - timedelta(days=days)

        clicks = await self.collection.count_documents(
            {"timestamp": {"$gte": start_date}}
        )

        conversions = await self.collection.aggregate([
            {"$match": {"timestamp": {"$gte": start_date}, "status": "converted"}},
            {"$group": {
                "_id": None,
                "total_revenue": {"$sum": "$amount_usd"},
                "total_commission": {"$sum": "$commission_usd"},
                "conversion_count": {"$sum": 1}
            }}
        ]).to_list(None)

        return {
            "clicks": clicks,
            "conversions": conversions[0] if conversions else {"total_revenue": 0, "total_commission": 0, "conversion_count": 0},
            "period_days": days
        }

