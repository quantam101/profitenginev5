"""
Real-time Revenue Optimization Engine

Analyzes live revenue data and automatically:
- Reallocates budget to top-performing streams
- Recommends price adjustments
- Optimizes marketing spend
- A/B tests offer variations
- Identifies growth opportunities
"""
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
from enum import Enum


class OptimizationStrategy(Enum):
    GROWTH = "growth"  # Maximize revenue growth
    STABILITY = "stability"  # Maximize consistent revenue
    DIVERSIFICATION = "diversification"  # Balance across streams


class RevenueOptimizer:
    """Real-time revenue optimization engine"""

    def __init__(self, db=None):
        self.db = db
        self.strategy = OptimizationStrategy.GROWTH

    async def analyze_performance(self, days: int = 7) -> Dict[str, Any]:
        """Analyze stream performance over period"""

        if not self.db:
            return {"status": "offline"}

        start_date = datetime.utcnow() - timedelta(days=days)

        # Get revenue by stream
        pipeline = [
            {"$match": {"timestamp": {"$gte": start_date}}},
            {"$group": {
                "_id": "$source",
                "total_revenue": {"$sum": "$amount_usd"},
                "transaction_count": {"$sum": 1},
                "avg_transaction": {"$avg": "$amount_usd"},
                "last_transaction": {"$max": "$timestamp"}
            }},
            {"$sort": {"total_revenue": -1}}
        ]

        results = await self.db.transactions.aggregate(pipeline).to_list(None)

        analysis = {
            "period_days": days,
            "total_revenue": sum(r["total_revenue"] for r in results),
            "streams": []
        }

        for stream in results:
            analysis["streams"].append({
                "name": stream["_id"],
                "revenue": stream["total_revenue"],
                "transactions": stream["transaction_count"],
                "avg_transaction": stream["avg_transaction"],
                "last_activity": stream["last_transaction"],
                "performance_score": (stream["total_revenue"] / analysis["total_revenue"] * 100)
                if analysis["total_revenue"] > 0 else 0
            })

        return analysis

    async def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Get AI-generated optimization recommendations"""

        if not self.db:
            return []

        performance = await self.analyze_performance(days=7)

        recommendations = []

        if not performance.get("streams"):
            return recommendations

        streams = performance["streams"]
        total_revenue = performance["total_revenue"]

        # Recommendation 1: Scale top performers
        top_stream = max(streams, key=lambda x: x["revenue"])
        if top_stream["revenue"] > total_revenue * 0.3:
            recommendations.append({
                "type": "scale_top_performer",
                "stream": top_stream["name"],
                "current_revenue": top_stream["revenue"],
                "recommendation": f"Scale {top_stream['name']} - it generates {top_stream['performance_score']:.1f}% of revenue. Increase marketing spend by 25-50%.",
                "priority": "high",
                "potential_impact": f"${top_stream['revenue'] * 0.5:.2f}/week"
            })

        # Recommendation 2: Fix underperformers
        low_performers = [s for s in streams if s["performance_score"] < 5]
        if low_performers:
            for stream in low_performers:
                recommendations.append({
                    "type": "optimize_or_sunset",
                    "stream": stream["name"],
                    "current_revenue": stream["revenue"],
                    "recommendation": f"Optimize {stream['name']} or reallocate resources. Currently only {stream['performance_score']:.1f}% of revenue.",
                    "priority": "medium",
                    "options": ["A/B test new offering", "Change pricing", "Redirect marketing budget", "Sunset if no improvement in 30 days"]
                })

        # Recommendation 3: Diversification
        top_3_percent = sum(s["performance_score"] for s in streams[:3])
        if top_3_percent > 80:
            recommendations.append({
                "type": "diversify",
                "recommendation": "Top 3 streams generate 80%+ of revenue. Diversify to reduce risk.",
                "priority": "medium",
                "action": "Focus on growing 3-5 underperforming streams to 10%+ of revenue each"
            })

        # Recommendation 4: Cross-sell opportunities
        recommendations.append({
            "type": "cross_sell",
            "recommendation": "Implement cross-sell between high-traffic and high-revenue streams",
            "priority": "medium",
            "action": "Bundle Gumroad + Consulting services, POD + Affiliate traffic"
        })

        return recommendations

    async def optimize_pricing(self, stream_name: str) -> Dict[str, Any]:
        """Recommend price optimization for stream"""

        if not self.db:
            return {}

        # Get recent transactions
        transactions = await self.db.transactions.find(
            {"source": stream_name},
            sort=[("timestamp", -1)],
            limit=100
        ).to_list(None)

        if not transactions:
            return {"status": "no_data"}

        amounts = [t["amount_usd"] for t in transactions if t["amount_usd"] > 0]

        if not amounts:
            return {"status": "no_paid_transactions"}

        avg_price = sum(amounts) / len(amounts)
        min_price = min(amounts)
        max_price = max(amounts)

        # A/B test prices
        test_prices = [
            avg_price * 0.8,  # 20% discount
            avg_price,  # Current
            avg_price * 1.2,  # 20% premium
            avg_price * 1.5,  # 50% premium
        ]

        return {
            "stream": stream_name,
            "current_avg_price": avg_price,
            "price_range": {"min": min_price, "max": max_price},
            "recommended_price": avg_price * 1.15,  # 15% increase
            "test_variants": test_prices,
            "recommendation": f"Test prices between ${test_prices[0]:.2f} and ${test_prices[-1]:.2f}. Optimal likely around ${avg_price * 1.15:.2f}."
        }

    async def allocate_marketing_budget(self, total_budget_usd: float) -> Dict[str, Any]:
        """Allocate marketing budget based on performance"""

        performance = await self.analyze_performance(days=30)

        if not performance.get("streams"):
            return {"status": "no_data"}

        streams = performance["streams"]
        allocation = {
            "total_budget": total_budget_usd,
            "allocations": [],
            "rationale": "Allocate 80% to top performers, 20% to growth opportunities"
        }

        # Sort by performance
        sorted_streams = sorted(streams, key=lambda x: x["revenue"], reverse=True)

        # Allocate 50% to top stream, 30% to second, 20% to others
        for i, stream in enumerate(sorted_streams[:3]):
            if i == 0:
                percentage = 0.50
            elif i == 1:
                percentage = 0.30
            else:
                percentage = 0.20

            budget = total_budget_usd * percentage
            allocation["allocations"].append({
                "stream": stream["name"],
                "percentage": percentage * 100,
                "budget_usd": budget,
                "roi_expectation": f"${budget * 3:.2f}-${budget * 5:.2f}"  # 3-5x ROI
            })

        return allocation

    async def track_optimization_results(self) -> Dict[str, Any]:
        """Track results of optimization actions"""

        if not self.db:
            return {}

        # Get optimization history
        recent_optimizations = await self.db.optimizations.find(
            {"created_at": {"$gte": datetime.utcnow() - timedelta(days=30)}}
        ).to_list(None)

        results = {
            "total_optimizations": len(recent_optimizations),
            "successful": sum(1 for o in recent_optimizations if o.get("status") == "success"),
            "successful_rate": 0
        }

        if results["total_optimizations"] > 0:
            results["successful_rate"] = results["successful"] / results["total_optimizations"] * 100

        return results
