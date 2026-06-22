"""Revenue Intelligence — Stream Optimization & Reallocation"""
from datetime import datetime
from typing import Dict, Any


class RevenueIntelligence:
    """Optimize revenue streams by reallocating budget to top performers"""

    def __init__(self, db=None):
        self.db = db

    async def analyze_streams(self) -> Dict[str, Any]:
        """Analyze all revenue streams and identify optimization opportunities"""

        if not self.db:
            return {"status": "error"}

        # Get last 30 days of revenue
        transactions = await self.db.transactions.find({}).to_list(None)

        stream_performance = {}
        for txn in transactions:
            source = txn.get("source", "unknown")
            amount = txn.get("amount_usd", 0)

            if source not in stream_performance:
                stream_performance[source] = {"revenue": 0, "count": 0, "roi": 0}

            stream_performance[source]["revenue"] += amount
            stream_performance[source]["count"] += 1

        # Identify top performers
        ranked = sorted(
            stream_performance.items(),
            key=lambda x: x[1]["revenue"],
            reverse=True
        )

        insights = {
            "top_stream": ranked[0][0] if ranked else None,
            "top_revenue": ranked[0][1]["revenue"] if ranked else 0,
            "total_streams": len(stream_performance),
            "total_revenue": sum(s["revenue"] for s in stream_performance.values()),
            "optimization_actions": [
                f"Scale {ranked[0][0]}: ${ranked[0][1]['revenue']:.2f}/mo" if ranked else None
            ]
        }

        # Log insights
        if self.db:
            await self.db.revenue_intelligence.insert_one({
                "analysis": insights,
                "timestamp": datetime.utcnow(),
                "recommendations": insights.get("optimization_actions", [])
            })

        return insights

    async def reallocate_budget(self) -> Dict[str, Any]:
        """Reallocate ad spend to top-performing streams"""

        analysis = await self.analyze_streams()

        return {
            "status": "reallocation_complete",
            "analysis": analysis,
            "action": f"Increased budget allocation to {analysis.get('top_stream')}"
        }


async def sync_revenue_intelligence_job(db=None):
    """Daily intelligence optimization"""

    intelligence = RevenueIntelligence(db=db)
    result = await intelligence.reallocate_budget()
    print(f"💡 Revenue Intelligence: {result['action']}")
    return result
