"""
Already Here LLC — Slack Daily Update Templates
Production-ready copy-paste templates for:
  - 8 AM Morning Briefing
  - 6 PM Evening Metrics
  - Sunday Weekly Summary
  - Monthly Completion Report

All fields are exact and named explicitly for direct integration with dashboard data.
Post via: python -c "from slack_daily_templates import *; import asyncio; asyncio.run(send_morning_briefing(...))"
"""

from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Optional

import aiohttp

SLACK_API_POST = "https://slack.com/api/chat.postMessage"
SLACK_REVENUE_OPS = os.getenv("SLACK_REVENUE_CHANNEL", "C0B8VN2S89Y")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")


async def _post_blocks(blocks: list[dict], channel: str = SLACK_REVENUE_OPS) -> bool:
    """Post block-kit message to Slack. Returns True on success."""
    if not SLACK_BOT_TOKEN:
        print(f"[Slack/no-token] Channel {channel}:\n{json.dumps(blocks, indent=2)}")
        return False

    payload = {
        "channel": channel,
        "blocks": blocks,
    }
    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                SLACK_API_POST,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=8),
            ) as resp:
                body = await resp.json()
                if not body.get("ok"):
                    print(f"[Slack error] {body.get('error', body)}")
                    return False
                return True
    except Exception as exc:
        print(f"[Slack post failed] {exc}")
        return False


def _header(text: str, emoji: bool = True) -> dict:
    """Block: large text header."""
    return {
        "type": "header",
        "text": {"type": "plain_text", "text": text, "emoji": emoji}
    }


def _section(text: str, mrkdwn: bool = True) -> dict:
    """Block: single text section (markdown or plain)."""
    return {
        "type": "section",
        "text": {
            "type": "mrkdwn" if mrkdwn else "plain_text",
            "text": text
        }
    }


def _fields(*pairs: tuple[str, str]) -> dict:
    """Block: 2-column field layout."""
    return {
        "type": "section",
        "fields": [
            {"type": "mrkdwn", "text": f"*{label}*\n{value}"}
            for label, value in pairs
        ]
    }


def _divider() -> dict:
    """Block: horizontal divider."""
    return {"type": "divider"}


def _context(text: str) -> dict:
    """Block: small gray context text."""
    return {
        "type": "context",
        "elements": [{"type": "mrkdwn", "text": text}]
    }


# ═══════════════════════════════════════════════════════════════════════════════
# TEMPLATE 1: 8 AM MORNING BRIEFING
# ═══════════════════════════════════════════════════════════════════════════════

async def send_morning_briefing(
    date_str: str,
    opens_24h: int,
    clicks_24h: int,
    sales_24h: int,
    revenue_24h_usd: float,
    ytd_revenue_usd: float,
    ytd_target_usd: float,
    active_leads: int,
    pipeline_value_usd: float,
    status: str = "ON_TRACK",
    channel: str = SLACK_REVENUE_OPS,
) -> bool:
    """
    8 AM Morning Briefing — Post daily kickoff metrics and targets.

    Args:
        date_str: Date (e.g. "2026-06-25")
        opens_24h: Unique email opens in last 24h
        clicks_24h: Email clicks in last 24h
        sales_24h: Number of sales closed in last 24h
        revenue_24h_usd: Revenue collected yesterday (USD)
        ytd_revenue_usd: Year-to-date revenue (USD)
        ytd_target_usd: Annual revenue target (USD)
        active_leads: Active pipeline leads
        pipeline_value_usd: Total pipeline value (USD)
        status: One of: ON_TRACK, BEHIND, ALERT, CRITICAL
        channel: Slack channel ID (defaults to #revenue-ops)

    Returns:
        True if posted successfully
    """

    pct_ytd = round(100 * ytd_revenue_usd / ytd_target_usd, 1) if ytd_target_usd > 0 else 0
    status_emoji = {
        "ON_TRACK": ":green_circle:",
        "BEHIND": ":yellow_circle:",
        "ALERT": ":orange_circle:",
        "CRITICAL": ":red_circle:",
    }.get(status, ":grey_circle:")

    now_utc = datetime.now(timezone.utc).strftime("%H:%M UTC")

    blocks = [
        _header(f"{status_emoji} DAILY BRIEFING — {date_str}"),
        _section(f"Good morning. *{now_utc}* — daily metrics and targets below."),
        _divider(),

        # ─ ENGAGEMENT METRICS (top row) ─
        _section("*📊 ENGAGEMENT (24h)*"),
        _fields(
            ("Opens", str(opens_24h)),
            ("Clicks", str(clicks_24h)),
            ("Sales", str(sales_24h)),
            ("Revenue Collected", f"${revenue_24h_usd:,.2f}"),
        ),
        _divider(),

        # ─ YTD PROGRESS (second row) ─
        _section("*📈 YTD PROGRESS*"),
        _fields(
            ("YTD Revenue", f"${ytd_revenue_usd:,.2f}"),
            ("YTD Target", f"${ytd_target_usd:,.2f}"),
            ("Achievement %", f"{pct_ytd}%"),
            ("Remaining Gap", f"${max(0, ytd_target_usd - ytd_revenue_usd):,.2f}"),
        ),
        _divider(),

        # ─ PIPELINE STATUS (third row) ─
        _section("*:chart_with_upwards_trend: PIPELINE*"),
        _fields(
            ("Active Leads", str(active_leads)),
            ("Total Pipeline Value", f"${pipeline_value_usd:,.2f}"),
        ),

        # ─ FOOTER ─
        _context(f"Status: {status} | Next update: 6 PM"),
    ]

    return await _post_blocks(blocks, channel=channel)


# ═══════════════════════════════════════════════════════════════════════════════
# TEMPLATE 2: 6 PM EVENING METRICS
# ═══════════════════════════════════════════════════════════════════════════════

async def send_evening_metrics(
    date_str: str,
    opens_24h: int,
    clicks_24h: int,
    click_rate_pct: float,
    sales_24h: int,
    sales_target_24h: int,
    revenue_24h_usd: float,
    revenue_target_24h_usd: float,
    deals_closed_detail: list[dict],  # [{"company": "...", "amount": 1000}, ...]
    leads_added: int,
    active_leads: int,
    status: str = "ON_TRACK",
    channel: str = SLACK_REVENUE_OPS,
) -> bool:
    """
    6 PM Evening Metrics — Daily close-out summary with deal details.

    Args:
        date_str: Date (e.g. "2026-06-25")
        opens_24h: Total email opens today
        clicks_24h: Total email clicks today
        click_rate_pct: Click-to-open rate %
        sales_24h: Number of sales closed today
        sales_target_24h: Daily sales target
        revenue_24h_usd: Revenue collected today (USD)
        revenue_target_24h_usd: Daily revenue target (USD)
        deals_closed_detail: List of deal dicts with 'company', 'amount', optional 'service'
        leads_added: New leads added today
        active_leads: Total active pipeline leads
        status: ON_TRACK, BEHIND, ALERT, CRITICAL
        channel: Slack channel ID

    Returns:
        True if posted successfully
    """

    status_emoji = {
        "ON_TRACK": ":green_circle:",
        "BEHIND": ":yellow_circle:",
        "ALERT": ":orange_circle:",
        "CRITICAL": ":red_circle:",
    }.get(status, ":grey_circle:")

    sales_pct = round(100 * sales_24h / sales_target_24h, 1) if sales_target_24h > 0 else 0
    revenue_pct = round(100 * revenue_24h_usd / revenue_target_24h_usd, 1) if revenue_target_24h_usd > 0 else 0

    now_utc = datetime.now(timezone.utc).strftime("%H:%M UTC")

    blocks = [
        _header(f"{status_emoji} DAILY CLOSE-OUT — {date_str}"),
        _section(f"*{now_utc}* — end-of-day summary. Status: *{status}*"),
        _divider(),

        # ─ ENGAGEMENT SNAPSHOT ─
        _section("*📧 ENGAGEMENT*"),
        _fields(
            ("Opens", str(opens_24h)),
            ("Clicks", str(clicks_24h)),
            ("Click-to-Open Rate", f"{click_rate_pct}%"),
        ),
        _divider(),

        # ─ SALES & REVENUE ─
        _section("*💰 SALES & REVENUE*"),
        _fields(
            ("Sales Closed", f"{sales_24h} / {sales_target_24h} ({sales_pct}%)"),
            ("Revenue", f"${revenue_24h_usd:,.2f} / ${revenue_target_24h_usd:,.2f} ({revenue_pct}%)"),
        ),

        # ─ DEALS DETAIL (if any closed) ─
        *([
            _divider(),
            _section("*:money_with_wings: DEALS CLOSED TODAY*"),
            _section("\n".join(
                f"  • *{d['company']}* — ${d['amount']:,.2f}" +
                (f" ({d.get('service', 'general')})" if 'service' in d else "")
                for d in deals_closed_detail
            )),
        ] if deals_closed_detail else []),

        _divider(),

        # ─ PIPELINE STATUS ─
        _section("*:chart_with_upwards_trend: PIPELINE*"),
        _fields(
            ("New Leads Today", str(leads_added)),
            ("Active Pipeline Leads", str(active_leads)),
        ),

        _context(f"Status: {status} | Next update: 8 AM tomorrow"),
    ]

    return await _post_blocks(blocks, channel=channel)


# ═══════════════════════════════════════════════════════════════════════════════
# TEMPLATE 3: SUNDAY WEEKLY SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════

async def send_weekly_summary(
    week_end_date: str,  # e.g. "2026-06-28"
    week_opens: int,
    week_clicks: int,
    week_sales: int,
    week_revenue_usd: float,
    week_target_usd: float,
    daily_avg_revenue: float,
    leads_added_week: int,
    deals_detail: list[dict],  # [{"company": "...", "amount": 1000, "date": "2026-06-26"}, ...]
    active_leads: int,
    pipeline_value_usd: float,
    top_performer: Optional[str] = None,
    notes: str = "",
    channel: str = SLACK_REVENUE_OPS,
) -> bool:
    """
    Sunday Weekly Summary — 7-day aggregate metrics and wins.

    Args:
        week_end_date: Week ending date (e.g. "2026-06-28")
        week_opens: Total email opens this week
        week_clicks: Total email clicks this week
        week_sales: Total sales closed this week
        week_revenue_usd: Total revenue collected (USD)
        week_target_usd: Weekly revenue target (USD)
        daily_avg_revenue: Average daily revenue this week (USD)
        leads_added_week: New leads added this week
        deals_detail: List of deals with company, amount, date
        active_leads: Total active leads
        pipeline_value_usd: Total pipeline value (USD)
        top_performer: Name of top performer (optional)
        notes: Additional notes or observations
        channel: Slack channel ID

    Returns:
        True if posted successfully
    """

    week_pct = round(100 * week_revenue_usd / week_target_usd, 1) if week_target_usd > 0 else 0

    blocks = [
        _header(f":chart_with_upwards_trend: WEEKLY SUMMARY — Week Ending {week_end_date}"),
        _section(f"Complete 7-day performance review and next-week outlook."),
        _divider(),

        # ─ ENGAGEMENT METRICS ─
        _section("*📊 ENGAGEMENT (7 days)*"),
        _fields(
            ("Opens", str(week_opens)),
            ("Clicks", str(week_clicks)),
            ("Sales Closed", str(week_sales)),
        ),
        _divider(),

        # ─ REVENUE PERFORMANCE ─
        _section("*💰 REVENUE PERFORMANCE*"),
        _fields(
            ("Weekly Revenue", f"${week_revenue_usd:,.2f}"),
            ("Weekly Target", f"${week_target_usd:,.2f}"),
            ("Achievement", f"{week_pct}%"),
            ("Daily Average", f"${daily_avg_revenue:,.2f}"),
        ),
        _divider(),

        # ─ DEALS CLOSED ─
        *([
            _section("*:money_with_wings: DEALS CLOSED THIS WEEK*"),
            _section("\n".join(
                f"  • {d['date']} — *{d['company']}* — ${d['amount']:,.2f}"
                for d in sorted(deals_detail, key=lambda x: x['date'])
            )),
            _divider(),
        ] if deals_detail else [_divider()]),

        # ─ PIPELINE ─
        _section("*:chart_with_upwards_trend: PIPELINE STATUS*"),
        _fields(
            ("New Leads (week)", str(leads_added_week)),
            ("Active Pipeline Leads", str(active_leads)),
            ("Total Pipeline Value", f"${pipeline_value_usd:,.2f}"),
        ),

        # ─ TOP PERFORMER ─
        *([
            _divider(),
            _section(f"*:star: TOP PERFORMER*\n{top_performer}"),
        ] if top_performer else []),

        # ─ NOTES ─
        *([
            _divider(),
            _section(f"*📝 NOTES*\n{notes}"),
        ] if notes else []),

        _context("Week ending " + week_end_date),
    ]

    return await _post_blocks(blocks, channel=channel)


# ═══════════════════════════════════════════════════════════════════════════════
# TEMPLATE 4: MONTHLY COMPLETION REPORT
# ═══════════════════════════════════════════════════════════════════════════════

async def send_monthly_report(
    month_year: str,  # e.g. "June 2026"
    month_opens: int,
    month_clicks: int,
    month_sales: int,
    month_revenue_usd: float,
    month_target_usd: float,
    month_spend_usd: float,
    month_net_profit_usd: float,
    total_leads_added: int,
    deals_closed_count: int,
    deals_detail: list[dict],  # [{"company": "...", "amount": 1000, "date": "2026-06-15"}, ...]
    avg_deal_size_usd: float,
    pipeline_value_usd: float,
    active_leads: int,
    key_wins: list[str] = None,  # ["Win 1", "Win 2"]
    challenges: list[str] = None,  # ["Challenge 1", "Challenge 2"]
    next_month_focus: str = "",
    channel: str = SLACK_REVENUE_OPS,
) -> bool:
    """
    Monthly Completion Report — Full month aggregate, P&L, and strategic outlook.

    Args:
        month_year: Month and year (e.g. "June 2026")
        month_opens: Total email opens this month
        month_clicks: Total email clicks this month
        month_sales: Total sales closed this month
        month_revenue_usd: Total revenue collected (USD)
        month_target_usd: Monthly revenue target (USD)
        month_spend_usd: Total spend this month (USD)
        month_net_profit_usd: Net profit (revenue - spend)
        total_leads_added: Total leads added this month
        deals_closed_count: Number of deals closed
        deals_detail: List of all deals with company, amount, date
        avg_deal_size_usd: Average deal size (USD)
        pipeline_value_usd: Total pipeline value (USD)
        active_leads: Active pipeline leads for next month
        key_wins: List of major wins or milestones
        challenges: List of challenges faced
        next_month_focus: Strategic focus for next month
        channel: Slack channel ID

    Returns:
        True if posted successfully
    """

    key_wins = key_wins or []
    challenges = challenges or []

    month_pct = round(100 * month_revenue_usd / month_target_usd, 1) if month_target_usd > 0 else 0
    month_roi = round(100 * month_net_profit_usd / month_spend_usd, 1) if month_spend_usd > 0 else 0

    blocks = [
        _header(f":calendar: MONTHLY REPORT — {month_year}"),
        _section(f"Complete monthly performance review, P&L analysis, and next-month strategy."),
        _divider(),

        # ─ EXECUTIVE SUMMARY ─
        _section("*📊 EXECUTIVE SUMMARY*"),
        _fields(
            ("Revenue", f"${month_revenue_usd:,.2f}"),
            ("Target", f"${month_target_usd:,.2f}"),
            ("Achievement", f"{month_pct}%"),
            ("Status", ":green_circle: ON TARGET" if month_pct >= 100 else ":yellow_circle: BEHIND TARGET"),
        ),
        _divider(),

        # ─ ENGAGEMENT ─
        _section("*📧 ENGAGEMENT METRICS*"),
        _fields(
            ("Opens", str(month_opens)),
            ("Clicks", str(month_clicks)),
            ("Sales Closed", str(month_sales)),
        ),
        _divider(),

        # ─ FINANCIAL SUMMARY ─
        _section("*💰 FINANCIAL SUMMARY*"),
        _fields(
            ("Revenue", f"${month_revenue_usd:,.2f}"),
            ("Spend", f"${month_spend_usd:,.2f}"),
            ("Net Profit", f"${month_net_profit_usd:,.2f}"),
            ("ROI", f"{month_roi}%"),
        ),
        _divider(),

        # ─ DEAL METRICS ─
        _section("*:money_with_wings: DEAL METRICS*"),
        _fields(
            ("Deals Closed", str(deals_closed_count)),
            ("Avg Deal Size", f"${avg_deal_size_usd:,.2f}"),
            ("New Leads", str(total_leads_added)),
        ),
        _divider(),

        # ─ TOP DEALS ─
        *([
            _section("*:chart_with_upwards_trend: BIGGEST DEALS*"),
            _section("\n".join(
                f"  • *{d['company']}* — ${d['amount']:,.2f} ({d['date']})"
                for d in sorted(deals_detail, key=lambda x: x['amount'], reverse=True)[:5]
            )),
            _divider(),
        ] if deals_detail else [_divider()]),

        # ─ PIPELINE ─
        _section("*:chart_with_upwards_trend: PIPELINE OUTLOOK*"),
        _fields(
            ("Active Leads", str(active_leads)),
            ("Total Pipeline Value", f"${pipeline_value_usd:,.2f}"),
        ),
        _divider(),

        # ─ KEY WINS ─
        *([
            _section("*:star: KEY WINS*"),
            _section("\n".join(f"  • {win}" for win in key_wins)),
            _divider(),
        ] if key_wins else []),

        # ─ CHALLENGES ─
        *([
            _section("*:warning: CHALLENGES*"),
            _section("\n".join(f"  • {ch}" for ch in challenges)),
            _divider(),
        ] if challenges else []),

        # ─ NEXT MONTH FOCUS ─
        *([
            _section("*:rocket: NEXT MONTH FOCUS*"),
            _section(next_month_focus),
        ] if next_month_focus else []),

        _context(f"Report period: {month_year}"),
    ]

    return await _post_blocks(blocks, channel=channel)


# ═══════════════════════════════════════════════════════════════════════════════
# CLI EXAMPLES (run these directly for testing)
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    async def demo():
        """Demo all templates with sample data."""

        print("[Demo] 8 AM Morning Briefing...")
        await send_morning_briefing(
            date_str="2026-06-25",
            opens_24h=42,
            clicks_24h=18,
            sales_24h=2,
            revenue_24h_usd=3500.00,
            ytd_revenue_usd=45000.00,
            ytd_target_usd=100000.00,
            active_leads=8,
            pipeline_value_usd=22500.00,
            status="ON_TRACK",
        )

        print("[Demo] 6 PM Evening Metrics...")
        await send_evening_metrics(
            date_str="2026-06-25",
            opens_24h=42,
            clicks_24h=18,
            click_rate_pct=42.9,
            sales_24h=2,
            sales_target_24h=2,
            revenue_24h_usd=3500.00,
            revenue_target_24h_usd=3500.00,
            deals_closed_detail=[
                {"company": "CompanyA", "amount": 1500.00, "service": "audit"},
                {"company": "CompanyB", "amount": 2000.00, "service": "drone"},
            ],
            leads_added=1,
            active_leads=8,
            status="ON_TRACK",
        )

        print("[Demo] Sunday Weekly Summary...")
        await send_weekly_summary(
            week_end_date="2026-06-28",
            week_opens=280,
            week_clicks=95,
            week_sales=12,
            week_revenue_usd=21000.00,
            week_target_usd=20000.00,
            daily_avg_revenue=3000.00,
            leads_added_week=5,
            deals_detail=[
                {"company": "CompanyA", "amount": 1500.00, "date": "2026-06-24"},
                {"company": "CompanyB", "amount": 2000.00, "date": "2026-06-25"},
                {"company": "CompanyC", "amount": 1800.00, "date": "2026-06-26"},
            ],
            active_leads=12,
            pipeline_value_usd=35000.00,
            top_performer="Alice Smith",
            notes="Strong week driven by drone service adoption. One logistics deal pending.",
        )

        print("[Demo] Monthly Completion Report...")
        await send_monthly_report(
            month_year="June 2026",
            month_opens=1200,
            month_clicks=380,
            month_sales=42,
            month_revenue_usd=87500.00,
            month_target_usd=100000.00,
            month_spend_usd=12000.00,
            month_net_profit_usd=75500.00,
            total_leads_added=28,
            deals_closed_count=42,
            deals_detail=[
                {"company": "BigCorp", "amount": 5000.00, "date": "2026-06-15"},
                {"company": "TechCo", "amount": 3500.00, "date": "2026-06-18"},
                {"company": "LocalBiz", "amount": 2200.00, "date": "2026-06-22"},
            ],
            avg_deal_size_usd=2083.33,
            pipeline_value_usd=45000.00,
            active_leads=15,
            key_wins=[
                "Drone service launched — 12 jobs completed",
                "Established cabling partnership with regional contractor",
                "Logistics brokerage revenue exceeded 2x target",
            ],
            challenges=[
                "Lead scoring algorithm needs refinement — false positives in finance sector",
                "Email open rates declined mid-month (platform algorithm change)",
            ],
            next_month_focus="Scale audit services to 5-state region; test YouTube content strategy.",
        )

        print("[Demo] All templates posted successfully!")

    asyncio.run(demo())
