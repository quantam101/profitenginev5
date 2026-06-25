"""
Already Here LLC — Slack Daily Templates Integration Example
Shows how to wire dashboard data to Slack update templates.

This example demonstrates:
1. Querying production_mesh_edge.db for metrics
2. Calculating derived metrics (click rates, achievement %, etc.)
3. Posting to Slack via slack_daily_templates functions

Run:
    python pipeline/slack_integration_example.py [template] [--dry-run]

Examples:
    python pipeline/slack_integration_example.py morning
    python pipeline/slack_integration_example.py evening
    python pipeline/slack_integration_example.py weekly
    python pipeline/slack_integration_example.py monthly
    python pipeline/slack_integration_example.py all --dry-run
"""

from __future__ import annotations

import asyncio
import os
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Import template functions
from slack_daily_templates import (
    send_morning_briefing,
    send_evening_metrics,
    send_weekly_summary,
    send_monthly_report,
)

DB_PATH = os.getenv("MESH_DB_PATH", "production_mesh_edge.db")
SLACK_CHANNEL = os.getenv("SLACK_REVENUE_CHANNEL", "C0B8VN2S89Y")


def get_db() -> sqlite3.Connection:
    """Open database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn


# ═════════════════════════════════════════════════════════════════════════════
# 8 AM MORNING BRIEFING DATA
# ═════════════════════════════════════════════════════════════════════════════

def get_morning_briefing_data() -> dict:
    """
    Fetch 8 AM morning briefing metrics from database.
    Returns dictionary with all required fields.
    """
    conn = get_db()
    cur = conn.cursor()

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    year_start = datetime.now(timezone.utc).strftime("%Y-01-01")

    # ─ 24h engagement (last 24 hours) ─
    cur.execute("""
        SELECT
            COUNT(DISTINCT email_open_id) as opens_24h,
            COUNT(DISTINCT email_click_id) as clicks_24h
        FROM analytics_events
        WHERE event_type IN ('open', 'click')
          AND created_at >= datetime('now', '-1 day')
    """)
    row = cur.fetchone()
    opens_24h = row[0] if row else 0
    clicks_24h = row[1] if row else 0

    # ─ 24h sales and revenue ─
    cur.execute("""
        SELECT
            COUNT(*) as sales_24h,
            COALESCE(SUM(amount_usd), 0) as revenue_24h_usd
        FROM deals
        WHERE status = 'CLOSED'
          AND closed_at >= datetime('now', '-1 day')
    """)
    row = cur.fetchone()
    sales_24h = row[0] if row else 0
    revenue_24h_usd = float(row[1]) if row else 0.0

    # ─ YTD revenue ─
    cur.execute("""
        SELECT COALESCE(SUM(amount_usd), 0) as ytd_revenue
        FROM deals
        WHERE status = 'CLOSED'
          AND closed_at >= ?
    """, (year_start,))
    ytd_revenue_usd = float(cur.fetchone()[0]) if cur.fetchone() else 0.0

    # ─ YTD target (hardcoded or from config) ─
    ytd_target_usd = 100000.00  # Replace with dynamic config if available

    # ─ Pipeline ─
    cur.execute("""
        SELECT
            COUNT(*) as active_leads,
            COALESCE(SUM(estimated_value_usd), 0) as pipeline_value
        FROM leads
        WHERE status IN ('ACTIVE', 'QUALIFIED')
    """)
    row = cur.fetchone()
    active_leads = row[0] if row else 0
    pipeline_value_usd = float(row[1]) if row else 0.0

    conn.close()

    # ─ Determine status ─
    ytd_pct = (ytd_revenue_usd / ytd_target_usd * 100) if ytd_target_usd > 0 else 0
    if ytd_pct >= 100:
        status = "ON_TRACK"
    elif ytd_pct >= 85:
        status = "BEHIND"
    elif ytd_pct >= 70:
        status = "ALERT"
    else:
        status = "CRITICAL"

    return {
        "date_str": today,
        "opens_24h": opens_24h,
        "clicks_24h": clicks_24h,
        "sales_24h": sales_24h,
        "revenue_24h_usd": revenue_24h_usd,
        "ytd_revenue_usd": ytd_revenue_usd,
        "ytd_target_usd": ytd_target_usd,
        "active_leads": active_leads,
        "pipeline_value_usd": pipeline_value_usd,
        "status": status,
        "channel": SLACK_CHANNEL,
    }


# ═════════════════════════════════════════════════════════════════════════════
# 6 PM EVENING METRICS DATA
# ═════════════════════════════════════════════════════════════════════════════

def get_evening_metrics_data() -> dict:
    """
    Fetch 6 PM evening metrics from database.
    Returns dictionary with all required fields.
    """
    conn = get_db()
    cur = conn.cursor()

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # ─ 24h engagement ─
    cur.execute("""
        SELECT
            COUNT(DISTINCT email_open_id) as opens_24h,
            COUNT(DISTINCT email_click_id) as clicks_24h
        FROM analytics_events
        WHERE event_type IN ('open', 'click')
          AND created_at >= datetime('now', '-1 day')
    """)
    row = cur.fetchone()
    opens_24h = row[0] if row else 0
    clicks_24h = row[1] if row else 0

    # ─ Click-to-open rate ─
    click_rate_pct = 0.0
    if opens_24h > 0:
        click_rate_pct = round(clicks_24h / opens_24h * 100, 1)

    # ─ Sales and revenue ─
    cur.execute("""
        SELECT
            COUNT(*) as sales_24h,
            COALESCE(SUM(amount_usd), 0) as revenue_24h_usd
        FROM deals
        WHERE status = 'CLOSED'
          AND closed_at >= datetime('now', '-1 day')
    """)
    row = cur.fetchone()
    sales_24h = row[0] if row else 0
    revenue_24h_usd = float(row[1]) if row else 0.0

    # ─ Targets (hardcoded or from config) ─
    sales_target_24h = 2
    revenue_target_24h_usd = 3500.00

    # ─ Deal details ─
    cur.execute("""
        SELECT
            company_name,
            amount_usd,
            service_type
        FROM deals
        WHERE status = 'CLOSED'
          AND closed_at >= datetime('now', '-1 day')
        ORDER BY closed_at DESC
    """)
    deals_closed_detail = [
        {
            "company": row[0],
            "amount": float(row[1]),
            "service": row[2] if row[2] else "general",
        }
        for row in cur.fetchall()
    ]

    # ─ Leads added today ─
    cur.execute("""
        SELECT COUNT(*) as leads_added
        FROM leads
        WHERE created_at >= datetime('now', 'start of day')
          AND created_at < datetime('now', '+1 day', 'start of day')
    """)
    leads_added = cur.fetchone()[0] if cur.fetchone() else 0

    # ─ Active leads ─
    cur.execute("""
        SELECT COUNT(*) as active_leads
        FROM leads
        WHERE status IN ('ACTIVE', 'QUALIFIED')
    """)
    active_leads = cur.fetchone()[0] if cur.fetchone() else 0

    conn.close()

    # ─ Determine status ─
    sales_pct = (sales_24h / sales_target_24h * 100) if sales_target_24h > 0 else 0
    revenue_pct = (revenue_24h_usd / revenue_target_24h_usd * 100) if revenue_target_24h_usd > 0 else 0
    avg_pct = (sales_pct + revenue_pct) / 2

    if avg_pct >= 100:
        status = "ON_TRACK"
    elif avg_pct >= 85:
        status = "BEHIND"
    elif avg_pct >= 70:
        status = "ALERT"
    else:
        status = "CRITICAL"

    return {
        "date_str": today,
        "opens_24h": opens_24h,
        "clicks_24h": clicks_24h,
        "click_rate_pct": click_rate_pct,
        "sales_24h": sales_24h,
        "sales_target_24h": sales_target_24h,
        "revenue_24h_usd": revenue_24h_usd,
        "revenue_target_24h_usd": revenue_target_24h_usd,
        "deals_closed_detail": deals_closed_detail,
        "leads_added": leads_added,
        "active_leads": active_leads,
        "status": status,
        "channel": SLACK_CHANNEL,
    }


# ═════════════════════════════════════════════════════════════════════════════
# SUNDAY WEEKLY SUMMARY DATA
# ═════════════════════════════════════════════════════════════════════════════

def get_weekly_summary_data() -> dict:
    """
    Fetch Sunday weekly summary metrics from database.
    Returns dictionary with all required fields.
    """
    conn = get_db()
    cur = conn.cursor()

    # ─ Week ending date (last Sunday) ─
    today = datetime.now(timezone.utc)
    days_since_sunday = today.weekday() + 1 if today.weekday() != 6 else 0
    week_end = today - timedelta(days=days_since_sunday)
    week_end_date = week_end.strftime("%Y-%m-%d")
    week_start = (week_end - timedelta(days=6)).strftime("%Y-%m-%d")

    # ─ 7-day engagement ─
    cur.execute("""
        SELECT
            COUNT(DISTINCT email_open_id) as week_opens,
            COUNT(DISTINCT email_click_id) as week_clicks
        FROM analytics_events
        WHERE event_type IN ('open', 'click')
          AND created_at >= datetime('now', '-7 days')
    """)
    row = cur.fetchone()
    week_opens = row[0] if row else 0
    week_clicks = row[1] if row else 0

    # ─ 7-day sales and revenue ─
    cur.execute("""
        SELECT
            COUNT(*) as week_sales,
            COALESCE(SUM(amount_usd), 0) as week_revenue_usd
        FROM deals
        WHERE status = 'CLOSED'
          AND closed_at >= datetime('now', '-7 days')
    """)
    row = cur.fetchone()
    week_sales = row[0] if row else 0
    week_revenue_usd = float(row[1]) if row else 0.0

    # ─ Weekly target (hardcoded or from config) ─
    week_target_usd = 20000.00

    # ─ Daily average ─
    daily_avg_revenue = week_revenue_usd / 7 if week_sales > 0 else 0.0

    # ─ Leads added this week ─
    cur.execute("""
        SELECT COUNT(*) as leads_added_week
        FROM leads
        WHERE created_at >= datetime('now', '-7 days')
    """)
    leads_added_week = cur.fetchone()[0] if cur.fetchone() else 0

    # ─ All deals this week (with dates) ─
    cur.execute("""
        SELECT
            company_name,
            amount_usd,
            DATE(closed_at) as closed_date
        FROM deals
        WHERE status = 'CLOSED'
          AND closed_at >= datetime('now', '-7 days')
        ORDER BY closed_at DESC
    """)
    deals_detail = [
        {
            "company": row[0],
            "amount": float(row[1]),
            "date": row[2],
        }
        for row in cur.fetchall()
    ]

    # ─ Pipeline ─
    cur.execute("""
        SELECT
            COUNT(*) as active_leads,
            COALESCE(SUM(estimated_value_usd), 0) as pipeline_value
        FROM leads
        WHERE status IN ('ACTIVE', 'QUALIFIED')
    """)
    row = cur.fetchone()
    active_leads = row[0] if row else 0
    pipeline_value_usd = float(row[1]) if row else 0.0

    # ─ Top performer this week ─
    cur.execute("""
        SELECT
            closer_name,
            COUNT(*) as deals_closed_count
        FROM deals
        WHERE status = 'CLOSED'
          AND closed_at >= datetime('now', '-7 days')
        GROUP BY closer_name
        ORDER BY deals_closed_count DESC
        LIMIT 1
    """)
    top_performer = None
    row = cur.fetchone()
    if row:
        top_performer = f"{row[0]} ({row[1]} deals)"

    conn.close()

    week_pct = (week_revenue_usd / week_target_usd * 100) if week_target_usd > 0 else 0
    if week_pct >= 100:
        status = "ON_TRACK"
    elif week_pct >= 85:
        status = "BEHIND"
    else:
        status = "ALERT"

    return {
        "week_end_date": week_end_date,
        "week_opens": week_opens,
        "week_clicks": week_clicks,
        "week_sales": week_sales,
        "week_revenue_usd": week_revenue_usd,
        "week_target_usd": week_target_usd,
        "daily_avg_revenue": daily_avg_revenue,
        "leads_added_week": leads_added_week,
        "deals_detail": deals_detail,
        "active_leads": active_leads,
        "pipeline_value_usd": pipeline_value_usd,
        "top_performer": top_performer,
        "notes": "Run `python pipeline/vp_dashboard.py status` for full pipeline details.",
        "channel": SLACK_CHANNEL,
    }


# ═════════════════════════════════════════════════════════════════════════════
# MONTHLY COMPLETION REPORT DATA
# ═════════════════════════════════════════════════════════════════════════════

def get_monthly_report_data() -> dict:
    """
    Fetch monthly completion report metrics from database.
    Returns dictionary with all required fields.
    """
    conn = get_db()
    cur = conn.cursor()

    now = datetime.now(timezone.utc)
    month_year = now.strftime("%B %Y")
    month_start = datetime(now.year, now.month, 1).strftime("%Y-%m-%d")

    # ─ Monthly engagement ─
    cur.execute("""
        SELECT
            COUNT(DISTINCT email_open_id) as month_opens,
            COUNT(DISTINCT email_click_id) as month_clicks
        FROM analytics_events
        WHERE event_type IN ('open', 'click')
          AND created_at >= ?
    """, (month_start,))
    row = cur.fetchone()
    month_opens = row[0] if row else 0
    month_clicks = row[1] if row else 0

    # ─ Monthly sales and revenue ─
    cur.execute("""
        SELECT
            COUNT(*) as month_sales,
            COALESCE(SUM(amount_usd), 0) as month_revenue_usd
        FROM deals
        WHERE status = 'CLOSED'
          AND closed_at >= ?
    """, (month_start,))
    row = cur.fetchone()
    month_sales = row[0] if row else 0
    month_revenue_usd = float(row[1]) if row else 0.0

    # ─ Monthly target ─
    month_target_usd = 100000.00

    # ─ Monthly spend (from expenses table) ─
    cur.execute("""
        SELECT COALESCE(SUM(amount_usd), 0)
        FROM expenses
        WHERE created_at >= ?
    """, (month_start,))
    month_spend_usd = float(cur.fetchone()[0]) if cur.fetchone() else 0.0

    month_net_profit_usd = month_revenue_usd - month_spend_usd

    # ─ Leads added this month ─
    cur.execute("""
        SELECT COUNT(*) as total_leads_added
        FROM leads
        WHERE created_at >= ?
    """, (month_start,))
    total_leads_added = cur.fetchone()[0] if cur.fetchone() else 0

    # ─ Deals closed this month (with details) ─
    cur.execute("""
        SELECT
            company_name,
            amount_usd,
            DATE(closed_at) as closed_date
        FROM deals
        WHERE status = 'CLOSED'
          AND closed_at >= ?
        ORDER BY amount_usd DESC
    """, (month_start,))
    deals_detail = [
        {
            "company": row[0],
            "amount": float(row[1]),
            "date": row[2],
        }
        for row in cur.fetchall()
    ]
    deals_closed_count = len(deals_detail)

    # ─ Average deal size ─
    avg_deal_size_usd = month_revenue_usd / deals_closed_count if deals_closed_count > 0 else 0.0

    # ─ Pipeline ─
    cur.execute("""
        SELECT
            COUNT(*) as active_leads,
            COALESCE(SUM(estimated_value_usd), 0) as pipeline_value
        FROM leads
        WHERE status IN ('ACTIVE', 'QUALIFIED')
    """)
    row = cur.fetchone()
    active_leads = row[0] if row else 0
    pipeline_value_usd = float(row[1]) if row else 0.0

    conn.close()

    month_pct = (month_revenue_usd / month_target_usd * 100) if month_target_usd > 0 else 0
    key_wins = [
        f"${month_revenue_usd:,.0f} revenue collected",
        f"{deals_closed_count} deals closed",
        f"{total_leads_added} new leads added",
    ]

    next_month_focus = f"Build on this month's momentum. Next month target: ${month_target_usd:,.0f}"

    return {
        "month_year": month_year,
        "month_opens": month_opens,
        "month_clicks": month_clicks,
        "month_sales": month_sales,
        "month_revenue_usd": month_revenue_usd,
        "month_target_usd": month_target_usd,
        "month_spend_usd": month_spend_usd,
        "month_net_profit_usd": month_net_profit_usd,
        "total_leads_added": total_leads_added,
        "deals_closed_count": deals_closed_count,
        "deals_detail": deals_detail,
        "avg_deal_size_usd": avg_deal_size_usd,
        "pipeline_value_usd": pipeline_value_usd,
        "active_leads": active_leads,
        "key_wins": key_wins,
        "challenges": ["(Add actual challenges from operations review)"],
        "next_month_focus": next_month_focus,
        "channel": SLACK_CHANNEL,
    }


# ═════════════════════════════════════════════════════════════════════════════
# MAIN DISPATCH
# ═════════════════════════════════════════════════════════════════════════════

async def main(template: str = "all", dry_run: bool = False):
    """
    Post daily update templates to Slack.

    Args:
        template: "morning", "evening", "weekly", "monthly", or "all"
        dry_run: If True, print to stdout instead of posting to Slack
    """
    if dry_run:
        # Clear SLACK_BOT_TOKEN to trigger stdout mode
        os.environ["SLACK_BOT_TOKEN"] = ""

    if template in ("morning", "all"):
        print("[8 AM] Fetching morning briefing data...")
        data = get_morning_briefing_data()
        print(f"[8 AM] Posting to Slack... (dry_run={dry_run})")
        await send_morning_briefing(**data)

    if template in ("evening", "all"):
        print("[6 PM] Fetching evening metrics data...")
        data = get_evening_metrics_data()
        print(f"[6 PM] Posting to Slack... (dry_run={dry_run})")
        await send_evening_metrics(**data)

    if template in ("weekly", "all"):
        print("[Sunday] Fetching weekly summary data...")
        data = get_weekly_summary_data()
        print(f"[Sunday] Posting to Slack... (dry_run={dry_run})")
        await send_weekly_summary(**data)

    if template in ("monthly", "all"):
        print("[Monthly] Fetching monthly report data...")
        data = get_monthly_report_data()
        print(f"[Monthly] Posting to Slack... (dry_run={dry_run})")
        await send_monthly_report(**data)

    print("[Done] All updates processed.")


if __name__ == "__main__":
    template = sys.argv[1] if len(sys.argv) > 1 else "all"
    dry_run = "--dry-run" in sys.argv

    if template not in ("morning", "evening", "weekly", "monthly", "all"):
        print(f"Invalid template: {template}")
        print("Usage: python slack_integration_example.py [morning|evening|weekly|monthly|all] [--dry-run]")
        sys.exit(1)

    asyncio.run(main(template=template, dry_run=dry_run))
