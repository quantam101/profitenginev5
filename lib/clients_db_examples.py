"""
Real-world integration examples for ProfitEngine client tracking database

These examples show how to integrate the clients_db module into:
- API routes
- Background jobs
- Analytics pipelines
- Reporting systems

Copy and adapt these patterns for your specific use case.
"""

from datetime import datetime, timedelta
from lib.clients_db import ClientsDB
from typing import Dict, List, Any


# ===== USER REGISTRATION & ONBOARDING =====

def register_new_user(email: str, signup_tier: str = "free") -> Dict[str, Any]:
    """
    Register a new user in the trading system.

    Typically called from signup endpoint:
      POST /api/auth/signup
      Body: { email: "user@example.com", tier: "free" }
    """
    db = ClientsDB()

    try:
        # Check if user already exists
        existing = db.get_user_by_email(email)
        if existing:
            return {
                "success": False,
                "error": "User already exists",
                "user_id": existing.id
            }

        # Create new user
        user = db.create_user(email, signup_tier)

        # Create upsell tracking record
        db.create_upsell_tracking(user.id)

        return {
            "success": True,
            "user_id": user.id,
            "email": user.email,
            "tier": user.trading_tier
        }
    finally:
        pass  # In production, ensure db connection cleanup


# ===== DAILY TRADE LOGGING =====

def log_daily_trades(user_id: int, trading_metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Log daily trading results for a user.

    Called after market close to record daily metrics:
      POST /api/trading/daily-log
      Body: {
        user_id: 1,
        date: "2026-06-18",
        num_trades: 12,
        win_count: 9,
        loss_count: 3,
        pnl_dollars: 625.50,
        pnl_percent: 6.25,
        balance: 10625.50
      }
    """
    db = ClientsDB()

    try:
        # Validate user exists
        user = db.get_user(user_id)
        if not user:
            return {"success": False, "error": "User not found"}

        # Record daily metrics
        trade = db.record_daily_trades(
            user_id=user_id,
            date=trading_metrics['date'],
            num_trades=trading_metrics['num_trades'],
            win_count=trading_metrics['win_count'],
            loss_count=trading_metrics['loss_count'],
            pnl_dollars=trading_metrics['pnl_dollars'],
            pnl_percent=trading_metrics['pnl_percent'],
            balance=trading_metrics['balance']
        )

        # Update user activity timestamp
        db.update_user_activity(user_id)

        return {
            "success": True,
            "date": trade.date,
            "trades_logged": trade.num_trades,
            "win_rate": trade.win_rate
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


# ===== USER PERFORMANCE DASHBOARD =====

def get_user_dashboard(user_id: int) -> Dict[str, Any]:
    """
    Get comprehensive user performance dashboard.

    Used for user profile/dashboard page:
      GET /api/users/{user_id}/dashboard
    """
    db = ClientsDB()

    try:
        user = db.get_user(user_id)
        if not user:
            return {"success": False, "error": "User not found"}

        # Get 7-day stats
        stats_7d = db.get_user_stats(user_id, days=7)

        # Get 30-day stats
        stats_30d = db.get_user_stats(user_id, days=30)

        # Get recent trades
        recent = db.get_user_trading_history(user_id, days=7)

        # Get upsell tracking
        upsell = db.get_upsell_tracking(user_id)

        return {
            "success": True,
            "user": {
                "id": user.id,
                "email": user.email,
                "tier": user.trading_tier,
                "signup_date": user.signup_date,
                "first_trade_date": user.first_trade_date,
                "is_active": user.is_active == 1
            },
            "stats": {
                "last_7_days": stats_7d,
                "last_30_days": stats_30d
            },
            "recent_trades": [
                {
                    "date": t.date,
                    "num_trades": t.num_trades,
                    "win_count": t.win_count,
                    "loss_count": t.loss_count,
                    "pnl_dollars": t.pnl_dollars,
                    "pnl_percent": t.pnl_percent,
                    "balance": t.balance,
                    "win_rate": t.win_rate
                }
                for t in recent[:14]  # Last 2 weeks
            ],
            "upsell": {
                "current_tier": user.trading_tier,
                "revenue_tier": upsell.revenue_tier if upsell else None,
                "lifetime_revenue": upsell.lifetime_revenue if upsell else 0.0
            }
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


# ===== LEADERBOARD & RANKINGS =====

def get_leaderboard(
    period_days: int = 7,
    limit: int = 10,
    min_trades: int = 0
) -> Dict[str, Any]:
    """
    Get top-performing users for leaderboard display.

    Used for competitive leaderboard page:
      GET /api/leaderboard?period=7&limit=10
    """
    db = ClientsDB()

    try:
        top_performers = db.get_top_performers(days=period_days, limit=limit)

        # Filter by minimum trades if specified
        if min_trades > 0:
            top_performers = [
                p for p in top_performers
                if p['trade_days'] >= min_trades
            ]

        return {
            "success": True,
            "period_days": period_days,
            "timestamp": datetime.now().isoformat(),
            "leaderboard": [
                {
                    "rank": idx + 1,
                    "user_id": p['user_id'],
                    "email": p['email'],
                    "tier": p['tier'],
                    "total_pnl": p['total_pnl'],
                    "avg_win_rate": round(p['avg_win_rate'], 1),
                    "trade_days": p['trade_days']
                }
                for idx, p in enumerate(top_performers)
            ]
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


# ===== UPSELL TARGETING =====

def identify_upsell_targets(
    min_pnl: float = 500.0,
    max_offers: int = 5,
    limit: int = 20
) -> Dict[str, Any]:
    """
    Identify high-performing free users for upselling.

    Used in background job to find upsell prospects:
      python scripts/upsell_targeting.py
    """
    db = ClientsDB()

    try:
        candidates = db.get_upsell_candidates(limit=limit)

        # Filter by minimum P&L and offer count
        qualified = [
            c for c in candidates
            if c['total_pnl_30d'] >= min_pnl
        ]

        # Get upsell history to avoid over-targeting
        for candidate in qualified:
            upsell = db.get_upsell_tracking(candidate['user_id'])
            candidate['upsell_history'] = {
                'offers_made': upsell.upsell_count if upsell else 0,
                'conversions': upsell.conversion_count if upsell else 0,
                'lifetime_revenue': upsell.lifetime_revenue if upsell else 0.0
            }

        # Filter by offer frequency
        targets = [
            c for c in qualified
            if c['upsell_history']['offers_made'] < max_offers
        ]

        return {
            "success": True,
            "total_candidates": len(candidates),
            "qualified": len(qualified),
            "targets": len(targets),
            "prospects": [
                {
                    "user_id": t['user_id'],
                    "email": t['email'],
                    "current_tier": t['tier'],
                    "pnl_30d": t['total_pnl_30d'],
                    "win_rate": round(t['avg_win_rate'], 1),
                    "trade_days": t['trade_days_30d'],
                    "offers_made": t['upsell_history']['offers_made'],
                    "conversions": t['upsell_history']['conversions'],
                    "recommended_tier": "pro"  # Based on performance
                }
                for t in targets[:limit]
            ]
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


# ===== RECORD UPSELL ACTION =====

def send_upsell_offer(user_id: int, tier: str) -> Dict[str, Any]:
    """
    Record that an upsell offer was sent to a user.

    Called when upsell email is sent:
      POST /api/upsell/send
      Body: { user_id: 1, tier: "pro" }
    """
    db = ClientsDB()

    try:
        user = db.get_user(user_id)
        if not user:
            return {"success": False, "error": "User not found"}

        # Record the upsell offer (not yet converted)
        tracking = db.record_upsell_offer(
            user_id=user_id,
            tier=tier,
            conversion=False
        )

        return {
            "success": True,
            "user_id": user_id,
            "offered_tier": tier,
            "total_offers": tracking.upsell_count,
            "conversions": tracking.conversion_count
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def process_tier_upgrade(user_id: int, new_tier: str, amount: float) -> Dict[str, Any]:
    """
    Process a user upgrading to a paid tier.

    Called after payment is confirmed:
      POST /api/billing/upgrade
      Body: { user_id: 1, tier: "pro", amount: 49.99 }
    """
    db = ClientsDB()

    try:
        # Update user tier
        user = db.update_user_tier(user_id, new_tier)

        # Update upsell tracking with conversion
        tracking = db.record_upsell_offer(
            user_id=user_id,
            tier=new_tier,
            conversion=True  # Mark as successful conversion
        )

        # Update revenue tier
        revenue_tier_map = {
            "free": "none",
            "basic": "paid-basic",
            "pro": "paid-pro",
            "elite": "paid-elite"
        }

        tracking = db.update_revenue_tier(
            user_id=user_id,
            revenue_tier=revenue_tier_map.get(new_tier, "none"),
            amount=amount
        )

        return {
            "success": True,
            "user_id": user_id,
            "new_tier": new_tier,
            "amount_paid": amount,
            "lifetime_revenue": tracking.lifetime_revenue,
            "conversion_count": tracking.conversion_count
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


# ===== REVENUE ANALYTICS =====

def get_revenue_report() -> Dict[str, Any]:
    """
    Generate comprehensive revenue report.

    Used in admin/analytics dashboard:
      GET /api/admin/revenue-report
    """
    db = ClientsDB()

    try:
        summary = db.get_revenue_summary()
        all_users = db.list_users(active_only=False, limit=10000)

        total_users = len(all_users)
        active_users = len([u for u in all_users if u.is_active])
        paid_users = sum(s['user_count'] for k, s in summary.items() if k != 'none')
        total_revenue = sum(s['total_revenue'] for s in summary.values())

        # Calculate MRR (Monthly Recurring Revenue) estimate
        mrr_estimate = total_revenue / 12 if total_revenue > 0 else 0

        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_users": total_users,
                "active_users": active_users,
                "paid_users": paid_users,
                "free_users": total_users - paid_users,
                "paid_conversion_rate": (paid_users / total_users * 100) if total_users > 0 else 0
            },
            "revenue": {
                "total_lifetime": round(total_revenue, 2),
                "estimated_mrr": round(mrr_estimate, 2)
            },
            "breakdown": {
                tier: {
                    "user_count": data['user_count'],
                    "total_revenue": round(data['total_revenue'], 2),
                    "avg_revenue_per_user": round(
                        data['total_revenue'] / data['user_count'], 2
                    ) if data['user_count'] > 0 else 0
                }
                for tier, data in summary.items()
            }
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


# ===== RETENTION & CHURN ANALYSIS =====

def get_user_retention_cohort(signup_year: int, signup_month: int) -> Dict[str, Any]:
    """
    Analyze retention for users who signed up in a specific month.

    Used in cohort analysis:
      GET /api/admin/cohorts?year=2026&month=6
    """
    db = ClientsDB()

    try:
        cohort_month = f"{signup_year}-{signup_month:02d}"

        # Get users who signed up in this month
        all_users = db.list_users(active_only=False, limit=10000)
        cohort = [
            u for u in all_users
            if u.signup_date.startswith(cohort_month)
        ]

        # Analyze activity
        active_count = sum(1 for u in cohort if u.is_active)
        trading_count = sum(1 for u in cohort if u.first_trade_date)

        return {
            "success": True,
            "cohort": cohort_month,
            "size": len(cohort),
            "active": active_count,
            "trading": trading_count,
            "retention_rate": (active_count / len(cohort) * 100) if cohort else 0,
            "trading_rate": (trading_count / len(cohort) * 100) if cohort else 0,
            "tier_distribution": {}  # Add tier breakdown
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


# ===== ADMIN UTILITIES =====

def bulk_tier_migration(tier_changes: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Update multiple users' tiers (admin function).

    Example:
      tier_changes = [
        {"user_id": 1, "new_tier": "pro"},
        {"user_id": 2, "new_tier": "elite"},
      ]
    """
    db = ClientsDB()

    results = {
        "success": 0,
        "failed": 0,
        "errors": []
    }

    try:
        for change in tier_changes:
            try:
                db.update_user_tier(change['user_id'], change['new_tier'])
                results["success"] += 1
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "user_id": change['user_id'],
                    "error": str(e)
                })

        return {
            "total": len(tier_changes),
            **results
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


# ===== EXPORT & REPORTING =====

def export_user_data_csv(user_id: int) -> Dict[str, Any]:
    """
    Export all user data to CSV format (GDPR data access request).

    User can request their data:
      GET /api/users/{user_id}/export-data
    """
    db = ClientsDB()

    try:
        user = db.get_user(user_id)
        if not user:
            return {"success": False, "error": "User not found"}

        history = db.get_user_trading_history(user_id, days=365)

        import csv
        import io

        # Generate CSV
        output = io.StringIO()
        writer = csv.writer(output)

        # Write user info
        writer.writerow(['User Data Export'])
        writer.writerow(['Email', user.email])
        writer.writerow(['Tier', user.trading_tier])
        writer.writerow(['Signup Date', user.signup_date])
        writer.writerow([])

        # Write trading history
        writer.writerow(['Trading History (Last 365 Days)'])
        writer.writerow([
            'Date', 'Trades', 'Wins', 'Losses',
            'P&L ($)', 'P&L (%)', 'Win Rate (%)', 'Balance'
        ])

        for trade in history:
            writer.writerow([
                trade.date,
                trade.num_trades,
                trade.win_count,
                trade.loss_count,
                round(trade.pnl_dollars, 2),
                round(trade.pnl_percent, 2),
                round(trade.win_rate, 1),
                round(trade.balance, 2)
            ])

        csv_content = output.getvalue()

        return {
            "success": True,
            "filename": f"profitengine_user_{user_id}_export.csv",
            "content": csv_content
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    # Example usage
    print("=== ProfitEngine Client DB Examples ===\n")

    # Register a user
    print("[1] Register new user")
    result = register_new_user("example@trading.com", "free")
    print(f"    Result: {result}\n")

    # Log trades
    print("[2] Log daily trades")
    if result['success']:
        result = log_daily_trades(
            result['user_id'],
            {
                'date': '2026-06-18',
                'num_trades': 10,
                'win_count': 7,
                'loss_count': 3,
                'pnl_dollars': 350.00,
                'pnl_percent': 3.5,
                'balance': 10350.00
            }
        )
        print(f"    Result: {result}\n")

    # Get dashboard
    print("[3] Get user dashboard")
    result = get_user_dashboard(1)
    if result['success']:
        print(f"    User: {result['user']['email']}")
        print(f"    7-day P&L: ${result['stats']['last_7_days']['total_pnl_dollars']}\n")

    # Get leaderboard
    print("[4] Get leaderboard")
    result = get_leaderboard(period_days=30, limit=5)
    if result['success']:
        print(f"    Top performers in last 30 days:")
        for entry in result['leaderboard'][:3]:
            print(f"      #{entry['rank']}: {entry['email']} - ${entry['total_pnl']}\n")

    print("[+] Examples complete!")
