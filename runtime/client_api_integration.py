"""
CLIENT API INTEGRATION GUIDE & EXAMPLES
Usage examples for profitengine-tau, content repo, and other services
"""

import asyncio
import hashlib
import os
from typing import Dict, Any, Optional
import httpx
import json


# ============================================================================
# CONFIGURATION
# ============================================================================

# Your API key (hash stored in CLIENT_API_KEY_HASH env var)
API_KEY = os.environ.get("PROFITENGINE_CLIENT_API_KEY", "dev-key-change-in-production")

# Client API endpoint
BASE_URL = os.environ.get("PROFITENGINE_CLIENT_API_URL", "http://localhost:8001")

# Generate auth header
def get_auth_header(api_key: str) -> str:
    """Create Bearer token authorization header"""
    return f"Bearer {api_key}"


# ============================================================================
# CLIENT WRAPPER
# ============================================================================

class ClientAPIClient:
    """Async HTTP client for ProfitEngine Client API"""

    def __init__(self, api_key: str, base_url: str = BASE_URL, timeout: int = 30):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.headers = {
            "Authorization": get_auth_header(api_key),
            "Content-Type": "application/json",
        }

    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to API"""
        url = f"{self.base_url}{endpoint}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.request(method, url, headers=self.headers, **kwargs)
            response.raise_for_status()
            return response.json()

    async def health_check(self) -> Dict[str, Any]:
        """Check API health (no auth required)"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/api/health")
            response.raise_for_status()
            return response.json()

    async def get_aggregate_stats(self, days: int = 30) -> Dict[str, Any]:
        """
        GET /api/clients/stats
        Returns: total traders, active traders, avg win rate, total P&L
        """
        return await self._request("GET", "/api/clients/stats", params={"days": days})

    async def get_leaderboard(
        self,
        metric: str = "win_rate",
        limit: int = 10,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        GET /api/clients/leaderboard
        Metrics: win_rate, pnl, days_active, total_trades
        Returns: ranked list of top traders
        """
        params = {
            "metric": metric,
            "limit": limit,
            "days": days,
        }
        return await self._request("GET", "/api/clients/leaderboard", params=params)

    async def get_upsell_candidates(self, days: int = 30) -> Dict[str, Any]:
        """
        GET /api/clients/upsell-candidates
        Returns: list of clients ready for premium upgrade
        """
        return await self._request(
            "GET", "/api/clients/upsell-candidates", params={"days": days}
        )

    async def get_trader_performance(
        self,
        user_id: str,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        GET /api/clients/{user_id}
        Returns: individual trader performance metrics
        """
        return await self._request(
            "GET", f"/api/clients/{user_id}", params={"days": days}
        )

    async def get_daily_summary(self, limit: int = 50) -> Dict[str, Any]:
        """
        GET /api/clients/daily-summary
        Returns: today's trading activity summary
        """
        return await self._request(
            "GET", "/api/clients/daily-summary", params={"limit": limit}
        )


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

async def example_aggregate_stats():
    """Example: Get aggregate stats for dashboard"""
    client = ClientAPIClient(API_KEY)

    try:
        stats = await client.get_aggregate_stats(days=30)
        print("\n=== AGGREGATE STATS ===")
        print(f"Total Traders: {stats['total_traders']}")
        print(f"Active Traders: {stats['active_traders']}")
        print(f"Avg Win Rate: {stats['avg_win_rate']}%")
        print(f"Total P&L: ${stats['total_pnl']}")
        print(f"Total Trades: {stats['total_trades']}")
        print(f"Avg Trades/Trader: {stats['avg_trades_per_trader']}")
    except httpx.HTTPStatusError as e:
        print(f"Error: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        print(f"Error: {e}")


async def example_leaderboard():
    """Example: Get top traders by win rate"""
    client = ClientAPIClient(API_KEY)

    try:
        leaderboard = await client.get_leaderboard(metric="win_rate", limit=5)
        print("\n=== LEADERBOARD: WIN RATE ===")
        for entry in leaderboard["entries"]:
            print(
                f"#{entry['rank']} {entry['user_id']}: "
                f"{entry['metric_value']}% win rate, ${entry['secondary_value']} P&L"
            )
    except Exception as e:
        print(f"Error: {e}")


async def example_upsell_candidates():
    """Example: Find clients ready for premium upgrade"""
    client = ClientAPIClient(API_KEY)

    try:
        response = await client.get_upsell_candidates()
        print(f"\n=== UPSELL CANDIDATES ({response['count']}) ===")
        for candidate in response["candidates"]:
            print(
                f"[{candidate['urgency'].upper()}] {candidate['user_id']}: "
                f"{candidate['total_trades']} trades, "
                f"{candidate['win_rate']}% win rate, "
                f"Potential Value: ${candidate['potential_value']}"
            )
    except Exception as e:
        print(f"Error: {e}")


async def example_trader_performance():
    """Example: Get individual trader details"""
    client = ClientAPIClient(API_KEY)

    try:
        # Replace with real user_id
        performance = await client.get_trader_performance("user_123")
        print("\n=== TRADER PERFORMANCE ===")
        print(f"User: {performance['user_id']}")
        print(f"Total Trades: {performance['total_trades']}")
        print(f"Win Rate: {performance['win_rate']}%")
        print(f"Total P&L: ${performance['total_pnl']}")
        print(f"Avg Win: ${performance['avg_win']} | Avg Loss: ${performance['avg_loss']}")
        print(f"Current Streak: {performance['current_streak']} ({performance['consecutive_wins']}W/{performance['consecutive_losses']}L)")
        print(f"Account Created: {performance['account_created']}")
        print(f"Days Active: {performance['days_active']}")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            print("Trader not found")
        else:
            print(f"Error: {e.response.status_code}")
    except Exception as e:
        print(f"Error: {e}")


async def example_daily_summary():
    """Example: Get today's trading summary"""
    client = ClientAPIClient(API_KEY)

    try:
        summary = await client.get_daily_summary()
        print("\n=== DAILY SUMMARY ===")
        print(f"Date: {summary['date']}")
        print(f"Total Trades: {summary['total_trades']}")
        print(f"Total P&L: ${summary['total_pnl']}")
        print(f"Win Rate: {summary['win_rate']}%")
        print(f"Active Users: {summary['active_users']}")
        print(f"Top Symbol: {summary['top_symbol']}")
        print("\nTop Trades:")
        for trade in summary["recent_trades"][:5]:
            print(
                f"  {trade['symbol']} ({trade['side']}): "
                f"${trade['pnl']} ({trade['pnl_percent']}%) @ {trade['entry_time']}"
            )
    except Exception as e:
        print(f"Error: {e}")


async def example_health_check():
    """Example: Check API health"""
    client = ClientAPIClient(API_KEY)

    try:
        health = await client.health_check()
        print("\n=== API HEALTH ===")
        print(f"Status: {'OK' if health['ok'] else 'ERROR'}")
        print(f"Service: {health['service']}")
        print(f"Version: {health['version']}")
        print(f"DB Ready: {health['db_ready']}")
    except Exception as e:
        print(f"Error: {e}")


# ============================================================================
# INTEGRATION PATTERNS
# ============================================================================

async def integrate_with_frontend(context: Dict[str, Any]):
    """
    Pattern: Use in profitengine-tau frontend for real-time dashboard
    Call periodically to refresh stats on client-facing pages
    """
    client = ClientAPIClient(API_KEY)

    # Get stats for header/footer
    stats = await client.get_aggregate_stats(days=30)
    context["site_stats"] = {
        "total_traders": stats["total_traders"],
        "total_pnl": f"${stats['total_pnl']:,.0f}",
        "avg_win_rate": f"{stats['avg_win_rate']}%",
    }

    # Get leaderboard for showcase
    leaderboard = await client.get_leaderboard(metric="pnl", limit=3)
    context["top_traders"] = [
        {
            "rank": e["rank"],
            "user_id": e["user_id"],
            "pnl": f"${e['metric_value']:,.0f}",
        }
        for e in leaderboard["entries"]
    ]

    return context


async def integrate_with_content_blog():
    """
    Pattern: Use in content repo to generate trading stats blog post
    Fetch real data to seed blog posts about trading performance
    """
    client = ClientAPIClient(API_KEY)

    summary = await client.get_daily_summary()
    stats = await client.get_aggregate_stats()

    post_content = f"""
# Daily Trading Report — {summary['date']}

**Today's Activity:**
- Trades Executed: {summary['total_trades']}
- Traders Active: {summary['active_users']}
- Total P&L: ${summary['total_pnl']:,.2f}
- Win Rate: {summary['win_rate']}%
- Top Symbol: {summary['top_symbol']}

**Community Stats (30 days):**
- Total Traders: {stats['total_traders']}
- Aggregate P&L: ${stats['total_pnl']:,.0f}
- Average Win Rate: {stats['avg_win_rate']}%
- Total Trades: {stats['total_trades']}

---

*Auto-generated trading summary. Data updates hourly.*
"""

    return post_content


async def integrate_with_sales_engine():
    """
    Pattern: Use in sales/marketing to identify upsell opportunities
    Find high-performing traders ready for premium features
    """
    client = ClientAPIClient(API_KEY)

    candidates = await client.get_upsell_candidates()

    # Segment by urgency
    high_urgency = [c for c in candidates["candidates"] if c["urgency"] == "high"]

    email_list = []
    for candidate in high_urgency:
        email_list.append(
            {
                "user_id": candidate["user_id"],
                "reason": (
                    f"{candidate['total_trades']} winning trades "
                    f"with {candidate['win_rate']}% win rate"
                ),
                "potential_revenue": candidate["potential_value"],
            }
        )

    return email_list


# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Run all examples"""
    print("ProfitEngine Client API Examples")
    print("=" * 50)

    # Health check first
    await example_health_check()

    # Run examples
    await example_aggregate_stats()
    await example_leaderboard()
    await example_upsell_candidates()
    await example_trader_performance()
    await example_daily_summary()

    print("\n" + "=" * 50)
    print("Examples complete!")


if __name__ == "__main__":
    asyncio.run(main())
