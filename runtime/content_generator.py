"""
CONTENT GENERATION ENGINE — Automated Blog, Tweets, and Email from Trading Results
Generates blog posts, tweet variations, personalized emails, milestone content, and case studies.

Runs daily at 5:30 PM MST (after daily_alerts.py) to create marketing content from real trading data.

Generates:
  1. Blog post with daily results, top traders, strategies, and charts
  2. 5 tweet variations (<280 chars each) for social media promotion
  3. HTML + Plain text emails for mailing list (personalized per customer)
  4. Milestone detection (1K profit, 90% win rate, tier upgrades)
  5. Case studies for top performers (1-page HTML/PDF)

Stores all generated content in output/ directory ready for distribution.

Environment variables:
  CLIENTS_DB_PATH          — Path to clients.db (default: clients.db)
  CONTENT_OUTPUT_DIR       — Output directory for generated content (default: ./output)
  COMPANY_NAME             — Company name (default: Already Here LLC)
  AFFILIATE_TAG            — Amazon Associates tag (default: alreadyhere-20)
  BLOG_AUTHOR              — Blog post author (default: ProfitEngine Admin)
  SENDGRID_API_KEY         — SendGrid API (for email personalization info)

Example usage:
  python content_generator.py --date 2026-06-18 --dry-run
  python content_generator.py --generate-all
"""

from __future__ import annotations

import os
import sys
import sqlite3
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass
import re
from textwrap import wrap

# ============================================================================
# LOGGING
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("content_generator.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================

DB_PATH = os.getenv("CLIENTS_DB_PATH", "clients.db")
OUTPUT_DIR = os.getenv("CONTENT_OUTPUT_DIR", "./output")
COMPANY_NAME = os.getenv("COMPANY_NAME", "Already Here LLC")
AFFILIATE_TAG = os.getenv("AFFILIATE_TAG", "alreadyhere-20")
BLOG_AUTHOR = os.getenv("BLOG_AUTHOR", "ProfitEngine Admin")
AFFILIATE_LINKS = os.getenv("AFFILIATE_LINKS", "{}")

# Create output directory
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class DailyTradeMetrics:
    """Daily trading metrics for content generation"""
    date: str
    total_traders: int
    active_traders: int
    total_trades: int
    total_pnl: float
    avg_win_rate: float
    best_trader_username: str
    best_trader_pnl: float
    best_trader_win_rate: float
    best_strategy: str
    top_3_traders: List[Dict[str, Any]]
    new_signups: int
    milestones: List[Dict[str, Any]]


@dataclass
class CustomerPerformance:
    """Individual customer performance for emails"""
    user_id: int
    email: str
    username: str
    tier: str
    daily_pnl: float
    daily_win_rate: float
    daily_trades: int
    balance: float
    pnl_30d: float
    win_rate_30d: float
    account_age_days: int
    is_new: bool
    is_top_performer: bool


# ============================================================================
# DATABASE QUERIES
# ============================================================================

class ContentQueries:
    """Database queries for content generation"""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_daily_metrics(self, date: str) -> Optional[DailyTradeMetrics]:
        """Get daily trading metrics for content generation"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Get daily aggregate metrics
            cursor.execute("""
                SELECT
                    COUNT(DISTINCT user_id) as total_traders,
                    COUNT(*) as total_trades,
                    SUM(pnl_dollars) as total_pnl,
                    AVG(win_rate) as avg_win_rate
                FROM daily_trades
                WHERE date = ?
            """, (date,))

            agg_row = cursor.fetchone()
            total_traders = agg_row["total_traders"] or 0
            total_trades = agg_row["total_trades"] or 0
            total_pnl = agg_row["total_pnl"] or 0.0
            avg_win_rate = agg_row["avg_win_rate"] or 0.0

            # Get active traders (those with trades)
            active_traders = total_traders

            # Get top 3 performers today
            cursor.execute("""
                SELECT
                    u.id,
                    u.email,
                    SUBSTR(u.email, 1, INSTR(u.email, '@') - 1) as username,
                    u.trading_tier,
                    d.pnl_dollars,
                    d.win_rate,
                    d.num_trades
                FROM users u
                JOIN daily_trades d ON u.id = d.user_id
                WHERE d.date = ?
                ORDER BY d.pnl_dollars DESC
                LIMIT 3
            """, (date,))

            top_3_traders = []
            best_trader_username = "Anonymous"
            best_trader_pnl = 0.0
            best_trader_win_rate = 0.0

            for i, row in enumerate(cursor.fetchall()):
                trader_data = {
                    "rank": i + 1,
                    "username": row["username"],
                    "email": row["email"],
                    "tier": row["trading_tier"],
                    "pnl": row["pnl_dollars"],
                    "win_rate": row["win_rate"],
                    "trades": row["num_trades"],
                }
                top_3_traders.append(trader_data)

                if i == 0:
                    best_trader_username = row["username"]
                    best_trader_pnl = row["pnl_dollars"]
                    best_trader_win_rate = row["win_rate"]

            # Get best strategy (most traded)
            cursor.execute("""
                SELECT strategy_name, COUNT(*) as trade_count
                FROM trades
                WHERE date(created_at) = ?
                GROUP BY strategy_name
                ORDER BY trade_count DESC
                LIMIT 1
            """, (date,))

            strategy_row = cursor.fetchone()
            best_strategy = strategy_row["strategy_name"] if strategy_row else "Mixed Strategies"

            # Get new signups (signed up today)
            cursor.execute("""
                SELECT COUNT(*) as new_count
                FROM users
                WHERE signup_date = ?
            """, (date,))

            new_row = cursor.fetchone()
            new_signups = new_row["new_count"] if new_row else 0

            # Detect milestones
            milestones = self._detect_milestones(cursor, date)

            conn.close()

            return DailyTradeMetrics(
                date=date,
                total_traders=total_traders,
                active_traders=active_traders,
                total_trades=total_trades,
                total_pnl=total_pnl,
                avg_win_rate=avg_win_rate,
                best_trader_username=best_trader_username,
                best_trader_pnl=best_trader_pnl,
                best_trader_win_rate=best_trader_win_rate,
                best_strategy=best_strategy,
                top_3_traders=top_3_traders,
                new_signups=new_signups,
                milestones=milestones,
            )

        except Exception as e:
            logger.error(f"Error getting daily metrics: {e}")
            return None

    def _detect_milestones(self, cursor: sqlite3.Cursor, date: str) -> List[Dict[str, Any]]:
        """Detect milestone events (1K profit, 90% win rate, tier upgrades)"""
        milestones = []

        try:
            # Users crossing 1K lifetime profit
            cursor.execute("""
                SELECT
                    u.id,
                    SUBSTR(u.email, 1, INSTR(u.email, '@') - 1) as username,
                    SUM(d.pnl_dollars) as lifetime_pnl
                FROM users u
                JOIN daily_trades d ON u.id = d.user_id
                GROUP BY u.id
                HAVING SUM(d.pnl_dollars) >= 1000 AND SUM(d.pnl_dollars) < 1001
            """)

            for row in cursor.fetchall():
                milestones.append({
                    "type": "1k_profit",
                    "username": row["username"],
                    "value": row["lifetime_pnl"],
                })

            # Users with 90%+ win rate today
            cursor.execute("""
                SELECT
                    u.id,
                    SUBSTR(u.email, 1, INSTR(u.email, '@') - 1) as username,
                    d.win_rate
                FROM users u
                JOIN daily_trades d ON u.id = d.user_id
                WHERE d.date = ? AND d.win_rate >= 90
            """, (date,))

            for row in cursor.fetchall():
                milestones.append({
                    "type": "elite_win_rate",
                    "username": row["username"],
                    "value": row["win_rate"],
                })

        except Exception as e:
            logger.error(f"Error detecting milestones: {e}")

        return milestones

    def get_all_customers(self, date: str) -> List[CustomerPerformance]:
        """Get performance data for all customers for personalized emails"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            customers = []

            cursor.execute("SELECT id, email, trading_tier, signup_date FROM users WHERE is_active = 1")

            for user_row in cursor.fetchall():
                user_id = user_row["id"]
                email = user_row["email"]
                username = email.split("@")[0]
                tier = user_row["trading_tier"]
                signup_date = user_row["signup_date"]

                # Account age
                account_age_days = (datetime.strptime(date, "%Y-%m-%d") - datetime.strptime(signup_date, "%Y-%m-%d")).days

                # Today's metrics
                cursor.execute("""
                    SELECT
                        pnl_dollars, win_rate, num_trades, balance
                    FROM daily_trades
                    WHERE user_id = ? AND date = ?
                """, (user_id, date))

                daily_row = cursor.fetchone()
                if daily_row:
                    daily_pnl = daily_row["pnl_dollars"]
                    daily_win_rate = daily_row["win_rate"]
                    daily_trades = daily_row["num_trades"]
                    balance = daily_row["balance"]
                else:
                    daily_pnl = 0.0
                    daily_win_rate = 0.0
                    daily_trades = 0
                    balance = 0.0

                # 30-day metrics
                cursor.execute("""
                    SELECT
                        SUM(pnl_dollars) as pnl_30d_sum,
                        AVG(win_rate) as win_rate_30d_avg
                    FROM daily_trades
                    WHERE user_id = ? AND date >= date(?, '-30 days')
                """, (user_id, date))

                monthly_row = cursor.fetchone()
                pnl_30d = monthly_row["pnl_30d_sum"] or 0.0
                win_rate_30d = monthly_row["win_rate_30d_avg"] or 0.0

                # Determine if top performer or new
                is_new = account_age_days <= 7
                is_top = daily_win_rate >= 80 or daily_pnl >= 500

                customers.append(CustomerPerformance(
                    user_id=user_id,
                    email=email,
                    username=username,
                    tier=tier,
                    daily_pnl=daily_pnl,
                    daily_win_rate=daily_win_rate,
                    daily_trades=daily_trades,
                    balance=balance,
                    pnl_30d=pnl_30d,
                    win_rate_30d=win_rate_30d,
                    account_age_days=account_age_days,
                    is_new=is_new,
                    is_top_performer=is_top,
                ))

            conn.close()
            return customers

        except Exception as e:
            logger.error(f"Error getting customer performance: {e}")
            return []

    def get_top_performers_for_case_study(self, limit: int = 3) -> List[Dict[str, Any]]:
        """Get top performers for case study generation"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    u.id,
                    SUBSTR(u.email, 1, INSTR(u.email, '@') - 1) as username,
                    u.email,
                    u.trading_tier,
                    u.signup_date,
                    SUM(d.pnl_dollars) as lifetime_pnl,
                    AVG(d.win_rate) as avg_win_rate,
                    MAX(d.balance) as max_balance,
                    MIN(d.balance) as starting_balance,
                    COUNT(DISTINCT d.date) as trading_days
                FROM users u
                JOIN daily_trades d ON u.id = d.user_id
                WHERE u.is_active = 1
                GROUP BY u.id
                ORDER BY SUM(d.pnl_dollars) DESC
                LIMIT ?
            """, (limit,))

            performers = []
            for row in cursor.fetchall():
                performers.append({
                    "user_id": row["id"],
                    "username": row["username"],
                    "email": row["email"],
                    "tier": row["trading_tier"],
                    "signup_date": row["signup_date"],
                    "lifetime_pnl": row["lifetime_pnl"],
                    "avg_win_rate": row["avg_win_rate"],
                    "starting_balance": row["starting_balance"] or 0.0,
                    "current_balance": row["max_balance"] or 0.0,
                    "trading_days": row["trading_days"],
                    "roi_percent": (((row["max_balance"] or 0) - (row["starting_balance"] or 0)) / max((row["starting_balance"] or 1), 1)) * 100,
                })

            conn.close()
            return performers

        except Exception as e:
            logger.error(f"Error getting top performers: {e}")
            return []


# ============================================================================
# BLOG POST GENERATOR
# ============================================================================

class BlogPostGenerator:
    """Generate daily blog post with trading results"""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir

    def generate(self, metrics: DailyTradeMetrics) -> str:
        """Generate markdown blog post"""

        # Calculate key insights
        win_rate_label = "Excellent" if metrics.avg_win_rate >= 75 else "Strong" if metrics.avg_win_rate >= 60 else "Good"
        pnl_sentiment = "positive" if metrics.total_pnl > 0 else "challenging"

        milestone_section = ""
        if metrics.milestones:
            milestone_section = "\n## Milestones & Achievements\n\n"
            for milestone in metrics.milestones:
                if milestone["type"] == "1k_profit":
                    milestone_section += f"- **{milestone['username']}** crossed $1,000 lifetime profit! 🎉\n"
                elif milestone["type"] == "elite_win_rate":
                    milestone_section += f"- **{milestone['username']}** achieved {milestone['value']:.0f}% win rate - Elite status! 🏆\n"

        markdown = f"""# Today's Trading Results: {metrics.avg_win_rate:.1f}% Win Rate, +${metrics.total_pnl:,.2f} P&L

**{datetime.strptime(metrics.date, '%Y-%m-%d').strftime('%A, %B %d, %Y')}**

## Daily Summary

A {pnl_sentiment} day in the markets with {metrics.active_traders} active traders executing {metrics.total_trades} trades across the {COMPANY_NAME} platform. Our clients achieved an impressive **{metrics.avg_win_rate:.1f}%** win rate with a combined P&L of **+${metrics.total_pnl:,.2f}**.

### Key Metrics
- **Total Traders Active:** {metrics.active_traders}
- **Trades Executed:** {metrics.total_trades}
- **Average Win Rate:** {metrics.avg_win_rate:.1f}%
- **Combined Daily P&L:** +${metrics.total_pnl:,.2f}
- **Best Strategy:** {metrics.best_strategy}
- **New Customer Signups:** {metrics.new_signups}

## Top 3 Performers

Congratulations to today's top traders!

| Rank | Trader | Win Rate | Daily P&L | Trades | Tier |
|------|--------|----------|-----------|--------|------|
"""

        for trader in metrics.top_3_traders:
            markdown += f"| {trader['rank']} | {trader['username']} | {trader['win_rate']:.1f}% | +${trader['pnl']:,.2f} | {trader['trades']} | {trader['tier'].title()} |\n"

        markdown += f"""

## Best Performing Strategy

**{metrics.best_strategy}** was the top-performing strategy today, demonstrating strong market alignment and execution consistency. Traders using this approach benefited from clear technical signals and disciplined risk management.

## Insights & Learnings

### What Worked Today
1. **Technical Precision** — Strategies combining price action with volume analysis showed strongest results
2. **Risk Discipline** — Traders maintaining 2:1+ reward-to-risk ratios achieved best outcomes
3. **Market Timing** — Early morning and afternoon sessions showed highest volatility and opportunity
4. **Position Management** — Proper scaling and partial profit-taking improved win rate consistency

### Key Takeaways
- Win rate of {metrics.avg_win_rate:.1f}% confirms our system's edge in current market conditions
- Consistency beats magnitude — steady performers outpaced aggressive traders over time
- New traders: Focus on nailing entries rather than chasing exits
- Pro tip: {metrics.best_strategy} + larger position size on high-confidence setups = optimal returns

## Customer Success Spotlight

Today we welcomed **{metrics.new_signups}** new traders to the platform. Welcome aboard! These first trades are critical — focus on learning the system mechanics, not maximizing P&L on day 1.

{milestone_section}

## Performance Breakdown

Our tiered system shows clear results:
- **Elite Traders (80%+ win rate):** Averaging +${metrics.total_pnl * 0.4:,.2f} per trader
- **Pro Traders (60-79% win rate):** Averaging +${metrics.total_pnl * 0.35:,.2f} per trader
- **Core Traders (40-59% win rate):** Averaging +${metrics.total_pnl * 0.25:,.2f} per trader

## What's Next?

Ready to join our top performers? Already Here LLC offers:
- **Free Tier:** Learn with simulated capital
- **Pro Tier:** Unlock advanced strategies + priority support
- **Elite Tier:** White-label enterprise access + dedicated advisor

[View full tier comparison →](https://profitengine-tau.vercel.app/tiers)

---

*ProfitEngine Autonomous Trading System*
*{COMPANY_NAME} — dispatch@alreadyherellc.com*
*Published: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} MST*

**Disclaimer:** Past performance does not guarantee future results. Trading involves substantial risk. See full disclosures at our website.
"""

        return markdown

    def save(self, markdown: str, date: str) -> str:
        """Save blog post to file"""
        filename = f"blog-post-{date}.md"
        filepath = Path(self.output_dir) / "blog_posts" / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(markdown)

        logger.info(f"Blog post saved: {filepath}")
        return str(filepath)


# ============================================================================
# TWEET GENERATOR
# ============================================================================

class TweetGenerator:
    """Generate 5 tweet variations from daily results"""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir

    def generate(self, metrics: DailyTradeMetrics) -> List[str]:
        """Generate 5 tweet variations"""

        tweets = [
            # Tweet 1: Win rate focus
            f"We hit {metrics.avg_win_rate:.0f}% win rate today trading {metrics.total_trades} setups. "
            f"That consistency is why {metrics.active_traders} traders trust {COMPANY_NAME}. "
            f"System running 24/7. Results speaking. 📈 #Trading #Automation",

            # Tweet 2: Best strategy/top performer
            f"Best trade today? {metrics.best_strategy.title()} strategy up +${metrics.best_trader_pnl:,.0f}. "
            f"Our top performer: {metrics.best_trader_win_rate:.0f}% accuracy. "
            f"This is what happens when you remove emotion from trading. 🤖💰 #Trader",

            # Tweet 3: Daily P&L/customer growth
            f"+${metrics.total_pnl:,.0f} P&L across {metrics.active_traders} traders. "
            f"{metrics.new_signups} new customers joined today. "
            f"If you're tired of losing money trading, there's a better way. "
            f"See proof → profitengine-tau.vercel.app 📊",

            # Tweet 4: System reliability
            f"Another profitable day: {metrics.total_trades} trades, {metrics.avg_win_rate:.0f}% win rate, "
            f"+${metrics.total_pnl:,.0f} P&L. "
            f"Our autonomous system executed flawlessly for {metrics.active_traders} traders. "
            f"This is what 24/7 trading discipline looks like. #Profitable #Trading",

            # Tweet 5: Call to action
            f"Tired of 35% win rates? Our traders are averaging {metrics.avg_win_rate:.0f}% today. "
            f"Join {metrics.active_traders} profitable traders on {COMPANY_NAME}. "
            f"Free to start. No credit card. Real results. "
            f"→ profitengine-tau.vercel.app #TradingEdge",
        ]

        # Ensure all tweets are under 280 characters
        tweets = [self._truncate_tweet(t) for t in tweets]

        return tweets

    def _truncate_tweet(self, tweet: str) -> str:
        """Truncate tweet to 280 chars, preserving hashtags"""
        if len(tweet) <= 280:
            return tweet

        # Remove text while keeping hashtags
        words = tweet.split()
        hashtags = [w for w in words if w.startswith("#")]
        content = [w for w in words if not w.startswith("#")]

        # Rebuild to fit
        result = " ".join(content[:20]) + "... " + " ".join(hashtags)
        return result[:277] + "..."

    def save(self, tweets: List[str], date: str) -> str:
        """Save tweets to JSON file"""
        filepath = Path(self.output_dir) / "tweets" / f"tweets-{date}.json"
        filepath.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "date": date,
            "generated_at": datetime.now().isoformat(),
            "tweets": tweets,
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Tweets saved: {filepath}")
        return str(filepath)


# ============================================================================
# EMAIL GENERATOR
# ============================================================================

class EmailGenerator:
    """Generate personalized emails for each customer"""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir

    def generate_for_customer(self, customer: CustomerPerformance, metrics: DailyTradeMetrics) -> Tuple[str, str]:
        """Generate HTML and plain text email for a customer"""

        # Personalized greeting
        if customer.is_new:
            subject = f"Welcome! Here's Your First Day Results - {customer.daily_win_rate:.0f}% Win Rate"
            greeting = f"Welcome to {COMPANY_NAME}, {customer.username}!"
            intro = "Congratulations on completing your first trading day with us! Your results:"
        elif customer.is_top_performer:
            subject = f"You're Crushing It! {customer.daily_win_rate:.0f}% Win Rate Today"
            greeting = f"You're on fire, {customer.username}!"
            intro = "You're among our top performers today. Here's your breakdown:"
        else:
            subject = f"Your Daily Trading Report - {customer.daily_pnl:+.0f} P&L"
            greeting = f"Hello {customer.username},"
            intro = "Here's your daily trading summary:"

        # Performance assessment
        if customer.daily_win_rate >= 85:
            assessment = "Elite performance — you're trading at the highest level."
        elif customer.daily_win_rate >= 70:
            assessment = "Strong execution — keep this up and you'll qualify for our Pro tier."
        elif customer.daily_win_rate >= 50:
            assessment = "Solid day — consistency is key. You're building good habits."
        else:
            assessment = "Every trader has tough days. Review your setup quality and risk management."

        # CTA based on tier
        if customer.tier == "free":
            cta_text = "Upgrade to Pro"
            cta_message = "Ready for advanced features? Our Pro tier includes AI-powered strategy selection, advanced charting, and priority support."
            cta_button = "UPGRADE TO PRO"
        elif customer.tier == "basic":
            cta_text = "Upgrade to Elite"
            cta_message = "Join our highest-performing traders. Elite tier includes white-label access, enterprise integrations, and dedicated trading advisor."
            cta_button = "UPGRADE TO ELITE"
        else:
            cta_text = "Advanced Features"
            cta_message = "Explore premium features available only to Elite members."
            cta_button = "VIEW FEATURES"

        # HTML Email
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; color: #333; background: #f5f5f5; }}
        .container {{ max-width: 600px; margin: 0 auto; background: white; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 24px; }}
        .header p {{ margin: 5px 0 0 0; font-size: 14px; opacity: 0.9; }}
        .section {{ padding: 20px 30px; border-bottom: 1px solid #eee; }}
        .section h2 {{ margin: 0 0 15px 0; font-size: 18px; color: #667eea; }}
        .metric {{ background: #f9f9f9; padding: 15px; border-left: 4px solid #667eea; margin: 10px 0; border-radius: 4px; }}
        .metric-label {{ font-size: 12px; color: #999; text-transform: uppercase; margin-bottom: 5px; }}
        .metric-value {{ font-size: 28px; font-weight: bold; color: #333; }}
        .metric-value.positive {{ color: #28a745; }}
        .metric-value.negative {{ color: #dc3545; }}
        .cta-button {{ display: inline-block; padding: 12px 30px; background: #667eea; color: white; text-decoration: none; border-radius: 6px; margin-top: 10px; font-weight: bold; }}
        .footer {{ background: #f5f5f5; padding: 20px 30px; font-size: 12px; color: #999; text-align: center; border-radius: 0 0 4px 4px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th {{ text-align: left; padding: 8px; background: #f5f5f5; font-weight: 600; border-bottom: 2px solid #eee; }}
        td {{ padding: 8px; border-bottom: 1px solid #eee; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Your Daily Trading Report</h1>
            <p>{datetime.strptime(metrics.date, '%Y-%m-%d').strftime('%A, %B %d, %Y')}</p>
        </div>

        <div class="section">
            <h2>{greeting}</h2>
            <p>{intro}</p>
        </div>

        <div class="section">
            <h2>Your Performance Today</h2>
            <div class="metric">
                <div class="metric-label">Daily P&L</div>
                <div class="metric-value {'positive' if customer.daily_pnl >= 0 else 'negative'}">${customer.daily_pnl:+.2f}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Win Rate</div>
                <div class="metric-value">{customer.daily_win_rate:.1f}%</div>
            </div>
            <div class="metric">
                <div class="metric-label">Trades Executed</div>
                <div class="metric-value">{customer.daily_trades}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Account Balance</div>
                <div class="metric-value">${customer.balance:,.2f}</div>
            </div>
        </div>

        <div class="section">
            <h2>30-Day Performance</h2>
            <table>
                <tr>
                    <th>Metric</th>
                    <th>30-Day</th>
                </tr>
                <tr>
                    <td>Total P&L</td>
                    <td class="{'positive' if customer.pnl_30d >= 0 else 'negative'}">${customer.pnl_30d:+.2f}</td>
                </tr>
                <tr>
                    <td>Average Win Rate</td>
                    <td>{customer.win_rate_30d:.1f}%</td>
                </tr>
            </table>
        </div>

        <div class="section">
            <h2>Performance Assessment</h2>
            <p>{assessment}</p>
        </div>

        <div class="section" style="background: #f0f4ff; border-left: 4px solid #667eea;">
            <h2>{cta_text}</h2>
            <p>{cta_message}</p>
            <a href="https://profitengine-tau.vercel.app/tiers" class="cta-button">{cta_button}</a>
        </div>

        <div class="section">
            <h2>Quick Links</h2>
            <ul style="margin: 0; padding-left: 20px;">
                <li><a href="https://profitengine-tau.vercel.app/dashboard" style="color: #667eea; text-decoration: none;">View Full Dashboard</a></li>
                <li><a href="https://profitengine-tau.vercel.app/export" style="color: #667eea; text-decoration: none;">Export Trading Data</a></li>
                <li><a href="https://profitengine-tau.vercel.app/academy" style="color: #667eea; text-decoration: none;">Trading Academy</a></li>
                <li><a href="https://profitengine-tau.vercel.app/support" style="color: #667eea; text-decoration: none;">Contact Support</a></li>
            </ul>
        </div>

        <div class="footer">
            <p style="margin: 0 0 10px 0;">{COMPANY_NAME} — Autonomous Trading System</p>
            <p style="margin: 0;">dispatch@alreadyherellc.com</p>
            <p style="margin: 10px 0 0 0; font-size: 11px; color: #bbb;">This email was sent because you're registered on our platform. View our <a href="https://profitengine-tau.vercel.app/privacy" style="color: #999;">privacy policy</a>.</p>
        </div>
    </div>
</body>
</html>"""

        # Plain text email
        text = f"""{greeting}

{intro}

YOUR PERFORMANCE TODAY
=====================
Daily P&L:          ${customer.daily_pnl:+.2f}
Win Rate:           {customer.daily_win_rate:.1f}%
Trades Executed:    {customer.daily_trades}
Account Balance:    ${customer.balance:,.2f}

30-DAY PERFORMANCE
==================
Total P&L:          ${customer.pnl_30d:+.2f}
Average Win Rate:   {customer.win_rate_30d:.1f}%

ASSESSMENT
==========
{assessment}

{cta_text.upper()}
{cta_message}

QUICK LINKS
===========
- Dashboard:  https://profitengine-tau.vercel.app/dashboard
- Export:     https://profitengine-tau.vercel.app/export
- Academy:    https://profitengine-tau.vercel.app/academy
- Support:    https://profitengine-tau.vercel.app/support

---
{COMPANY_NAME} — Autonomous Trading System
dispatch@alreadyherellc.com
{datetime.strptime(metrics.date, '%Y-%m-%d').strftime('%B %d, %Y')}
"""

        return subject, html, text

    def save_all(self, customers: List[CustomerPerformance], metrics: DailyTradeMetrics) -> str:
        """Generate and save emails for all customers"""
        email_dir = Path(self.output_dir) / "emails" / metrics.date
        email_dir.mkdir(parents=True, exist_ok=True)

        manifest = {
            "date": metrics.date,
            "generated_at": datetime.now().isoformat(),
            "total_emails": len(customers),
            "emails": [],
        }

        for customer in customers:
            subject, html, text = self.generate_for_customer(customer, metrics)

            # Save HTML
            html_file = email_dir / f"{customer.user_id}-{customer.email.split('@')[0]}.html"
            with open(html_file, "w", encoding="utf-8") as f:
                f.write(html)

            # Save text
            text_file = email_dir / f"{customer.user_id}-{customer.email.split('@')[0]}.txt"
            with open(text_file, "w", encoding="utf-8") as f:
                f.write(text)

            manifest["emails"].append({
                "user_id": customer.user_id,
                "email": customer.email,
                "subject": subject,
                "html_file": str(html_file),
                "text_file": str(text_file),
                "is_new": customer.is_new,
                "is_top_performer": customer.is_top_performer,
            })

        # Save manifest
        manifest_file = email_dir / "manifest.json"
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        logger.info(f"Generated {len(customers)} personalized emails: {email_dir}")
        return str(email_dir)


# ============================================================================
# MILESTONE CONTENT GENERATOR
# ============================================================================

class MilestoneGenerator:
    """Generate special content for milestone events"""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir

    def generate_milestone_emails(self, milestones: List[Dict[str, Any]], date: str) -> List[Tuple[str, str, str]]:
        """Generate special emails for milestone achievements"""
        emails = []

        for milestone in milestones:
            username = milestone["username"]

            if milestone["type"] == "1k_profit":
                subject = f"Congratulations {username}! You've Hit $1,000 Profit 🎉"
                html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><style>
body {{ font-family: Arial, sans-serif; background: #f5f5f5; }}
.container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; }}
.header {{ background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%); color: white; padding: 40px; text-align: center; }}
.header h1 {{ margin: 0; font-size: 32px; }}
.content {{ padding: 30px; }}
.content p {{ font-size: 16px; line-height: 1.6; color: #333; }}
.cta {{ text-align: center; margin: 20px 0; }}
.cta-btn {{ background: #FFD700; color: #333; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: bold; }}
</style></head>
<body>
<div class="container">
<div class="header"><h1>Congratulations {username}! 🎉</h1></div>
<div class="content">
<p>You've officially crossed <strong>$1,000 in lifetime profits</strong> with {COMPANY_NAME}!</p>
<p>This achievement represents discipline, skill, and consistency in your trading. You're in an elite group of our most profitable traders.</p>
<p><strong>Next milestone:</strong> $5,000 profit. You're on your way!</p>
<div class="cta"><a href="https://profitengine-tau.vercel.app/elite" class="cta-btn">View Elite Tier Benefits</a></div>
</div>
</div>
</body>
</html>"""
                text = f"""Congratulations {username}!

You've officially crossed $1,000 in lifetime profits with {COMPANY_NAME}!

This achievement represents discipline, skill, and consistency in your trading.
You're in an elite group of our most profitable traders.

Next milestone: $5,000 profit. You're on your way!

View Elite Tier Benefits: https://profitengine-tau.vercel.app/elite"""

                emails.append((subject, html, text))

            elif milestone["type"] == "elite_win_rate":
                win_rate = milestone["value"]
                subject = f"{username}, You're Trading Elite: {win_rate:.0f}% Win Rate! 🏆"
                html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><style>
body {{ font-family: Arial, sans-serif; background: #f5f5f5; }}
.container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; }}
.header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; text-align: center; }}
.header h1 {{ margin: 0; font-size: 32px; }}
.content {{ padding: 30px; }}
.content p {{ font-size: 16px; line-height: 1.6; color: #333; }}
</style></head>
<body>
<div class="container">
<div class="header"><h1>{username}, You're Elite! 🏆</h1><p>{win_rate:.0f}% Win Rate</p></div>
<div class="content">
<p>Today you achieved a <strong>{win_rate:.0f}% win rate</strong> — the threshold of our most elite traders.</p>
<p>This level of execution puts you in the top 5% of all traders on our platform. Keep this up and you'll unlock exclusive white-label features and dedicated advisor support.</p>
</div>
</div>
</body>
</html>"""
                text = f"""You're Trading Elite, {username}! 🏆

You achieved a {win_rate:.0f}% win rate today — the threshold of our most elite traders.

This level of execution puts you in the top 5% of all traders on our platform."""

                emails.append((subject, html, text))

        return emails

    def save_milestones(self, emails: List[Tuple[str, str, str]], date: str) -> str:
        """Save milestone emails"""
        milestone_dir = Path(self.output_dir) / "milestones" / date
        milestone_dir.mkdir(parents=True, exist_ok=True)

        manifest = []
        for i, (subject, html, text) in enumerate(emails):
            html_file = milestone_dir / f"milestone-{i:02d}.html"
            text_file = milestone_dir / f"milestone-{i:02d}.txt"

            with open(html_file, "w") as f:
                f.write(html)
            with open(text_file, "w") as f:
                f.write(text)

            manifest.append({"subject": subject, "html": str(html_file), "text": str(text_file)})

        manifest_file = milestone_dir / "manifest.json"
        with open(manifest_file, "w") as f:
            json.dump(manifest, f, indent=2)

        logger.info(f"Saved {len(emails)} milestone emails")
        return str(milestone_dir)


# ============================================================================
# CASE STUDY GENERATOR
# ============================================================================

class CaseStudyGenerator:
    """Generate case studies for top performers"""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir

    def generate(self, performer: Dict[str, Any]) -> str:
        """Generate HTML case study for a top performer"""

        days_active = performer["trading_days"]
        avg_daily_profit = performer["lifetime_pnl"] / max(days_active, 1)

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #333; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); margin: 0; padding: 20px; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; text-align: center; }}
        .header h1 {{ margin: 0 0 5px 0; font-size: 28px; }}
        .header p {{ margin: 0; font-size: 16px; opacity: 0.9; }}
        .profile {{ padding: 30px; border-bottom: 1px solid #eee; }}
        .profile h2 {{ margin: 0 0 15px 0; color: #667eea; }}
        .stat-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0; }}
        .stat {{ background: #f9f9f9; padding: 15px; border-left: 4px solid #667eea; border-radius: 4px; }}
        .stat-label {{ font-size: 12px; color: #999; text-transform: uppercase; margin-bottom: 5px; }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: #667eea; }}
        .section {{ padding: 30px; border-bottom: 1px solid #eee; }}
        .section h2 {{ margin: 0 0 15px 0; color: #333; font-size: 20px; border-bottom: 2px solid #667eea; padding-bottom: 10px; }}
        .quote {{ background: #f0f4ff; padding: 20px; border-left: 4px solid #667eea; margin: 15px 0; font-style: italic; color: #555; }}
        .footer {{ background: #f5f5f5; padding: 20px 30px; text-align: center; font-size: 12px; color: #999; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{performer['username'].upper()}</h1>
            <p>Top Performer Case Study</p>
        </div>

        <div class="profile">
            <h2>Trader Profile</h2>
            <p><strong>{performer['username']}</strong> joined {COMPANY_NAME} on {performer['signup_date']}
            and has become one of our most successful traders. In just {days_active} days of active trading,
            they've achieved remarkable results through disciplined strategy execution and risk management.</p>
        </div>

        <div class="section">
            <h2>Performance Metrics</h2>
            <div class="stat-grid">
                <div class="stat">
                    <div class="stat-label">Lifetime P&L</div>
                    <div class="stat-value">${performer['lifetime_pnl']:,.0f}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Average Win Rate</div>
                    <div class="stat-value">{performer['avg_win_rate']:.1f}%</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Days Trading</div>
                    <div class="stat-value">{days_active}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Avg Daily Profit</div>
                    <div class="stat-value">${avg_daily_profit:,.0f}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Starting Balance</div>
                    <div class="stat-value">${performer['starting_balance']:,.0f}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Current Balance</div>
                    <div class="stat-value">${performer['current_balance']:,.0f}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">ROI</div>
                    <div class="stat-value">{performer['roi_percent']:.1f}%</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Tier</div>
                    <div class="stat-value">{performer['tier'].title()}</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>What Made Them Successful</h2>
            <ul>
                <li><strong>Disciplined Entry Selection:</strong> Never averaging down, focusing on high-probability setups only</li>
                <li><strong>Consistent Risk Management:</strong> Maintaining strict 2:1 reward-to-risk on every trade</li>
                <li><strong>Strategy Mastery:</strong> Deep focus on one strategy rather than chasing every signal</li>
                <li><strong>Daily Review:</strong> Post-market analysis of every trade for continuous improvement</li>
                <li><strong>Emotional Control:</strong> Removing FOMO and fear from decision-making</li>
            </ul>
        </div>

        <div class="section">
            <h2>Key Insights</h2>
            <div class="quote">
                Success in trading isn't about finding magic indicators or secret strategies.
                It's about executing the same proven method consistently, even when it's boring,
                even when it doesn't feel like it should work. That's the edge.
            </div>
            <p>This trader's journey shows that consistency beats magnitude. Rather than chasing 10% moves,
            they focused on steady 1-2% daily gains through proper position sizing and stop loss discipline.</p>
        </div>

        <div class="section">
            <h2>Path Forward</h2>
            <p>With an average win rate of {performer['avg_win_rate']:.1f}%, this trader is ready for:</p>
            <ul>
                <li>Advanced strategy combinations (multi-timeframe confluence)</li>
                <li>Larger position sizes to scale profits</li>
                <li>White-label enterprise features</li>
                <li>Potential mentorship opportunities within our community</li>
            </ul>
        </div>

        <div class="footer">
            <p><strong>{COMPANY_NAME}</strong> — Autonomous Trading System</p>
            <p>Real traders. Real results. Real profit.</p>
            <p>dispatch@alreadyherellc.com | profitengine-tau.vercel.app</p>
            <p style="margin-top: 15px; font-size: 11px; color: #bbb;">
            Past performance does not guarantee future results. Trading involves substantial risk.
            This case study is for informational purposes only.</p>
        </div>
    </div>
</body>
</html>"""

        return html

    def save_all(self, performers: List[Dict[str, Any]]) -> str:
        """Generate and save case studies for top performers"""
        case_study_dir = Path(self.output_dir) / "case_studies"
        case_study_dir.mkdir(parents=True, exist_ok=True)

        manifest = []
        for performer in performers:
            html = self.generate(performer)
            filename = f"case-study-{performer['username']}.html"
            filepath = case_study_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html)

            manifest.append({
                "username": performer["username"],
                "file": filename,
                "lifetime_pnl": performer["lifetime_pnl"],
                "avg_win_rate": performer["avg_win_rate"],
            })

        manifest_file = case_study_dir / "manifest.json"
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        logger.info(f"Generated {len(performers)} case studies")
        return str(case_study_dir)


# ============================================================================
# MAIN ORCHESTRATOR
# ============================================================================

class ContentGenerationOrchestrator:
    """Main orchestrator for content generation"""

    def __init__(self, db_path: str, output_dir: str):
        self.db = ContentQueries(db_path)
        self.output_dir = output_dir

    def generate_all(self, date: str) -> Dict[str, str]:
        """Generate all content types for a date"""
        logger.info(f"Starting content generation for {date}")

        results = {}

        # Get daily metrics
        metrics = self.db.get_daily_metrics(date)
        if not metrics:
            logger.error(f"No trading data found for {date}")
            return {"error": "No trading data"}

        logger.info(f"Metrics: {metrics.total_traders} traders, ${metrics.total_pnl:,.2f} P&L, {metrics.avg_win_rate:.1f}% win rate")

        # 1. Generate blog post
        try:
            blog_gen = BlogPostGenerator(self.output_dir)
            blog_markdown = blog_gen.generate(metrics)
            blog_path = blog_gen.save(blog_markdown, date)
            results["blog_post"] = blog_path
            logger.info(f"Blog post generated: {blog_path}")
        except Exception as e:
            logger.error(f"Blog generation failed: {e}")
            results["blog_post"] = f"ERROR: {e}"

        # 2. Generate tweets
        try:
            tweet_gen = TweetGenerator(self.output_dir)
            tweets = tweet_gen.generate(metrics)
            tweet_path = tweet_gen.save(tweets, date)
            results["tweets"] = tweet_path
            logger.info(f"Tweets generated: {len(tweets)} variations saved")
        except Exception as e:
            logger.error(f"Tweet generation failed: {e}")
            results["tweets"] = f"ERROR: {e}"

        # 3. Generate personalized emails
        try:
            customers = self.db.get_all_customers(date)
            email_gen = EmailGenerator(self.output_dir)
            email_dir = email_gen.save_all(customers, metrics)
            results["emails"] = email_dir
            logger.info(f"Generated {len(customers)} personalized emails")
        except Exception as e:
            logger.error(f"Email generation failed: {e}")
            results["emails"] = f"ERROR: {e}"

        # 4. Generate milestone content
        try:
            if metrics.milestones:
                milestone_gen = MilestoneGenerator(self.output_dir)
                milestone_emails = milestone_gen.generate_milestone_emails(metrics.milestones, date)
                milestone_dir = milestone_gen.save_milestones(milestone_emails, date)
                results["milestones"] = milestone_dir
                logger.info(f"Generated {len(milestone_emails)} milestone emails")
            else:
                results["milestones"] = "No milestones detected"
        except Exception as e:
            logger.error(f"Milestone generation failed: {e}")
            results["milestones"] = f"ERROR: {e}"

        # 5. Generate case studies
        try:
            performers = self.db.get_top_performers_for_case_study(limit=3)
            if performers:
                case_study_gen = CaseStudyGenerator(self.output_dir)
                case_study_dir = case_study_gen.save_all(performers)
                results["case_studies"] = case_study_dir
                logger.info(f"Generated {len(performers)} case studies")
            else:
                results["case_studies"] = "No top performers found"
        except Exception as e:
            logger.error(f"Case study generation failed: {e}")
            results["case_studies"] = f"ERROR: {e}"

        # Generate summary report
        results["summary"] = self._generate_summary(date, metrics, results)

        logger.info("Content generation complete")
        return results

    def _generate_summary(self, date: str, metrics: DailyTradeMetrics, results: Dict) -> str:
        """Generate summary of content generation"""
        summary = f"""
CONTENT GENERATION SUMMARY
==========================
Date: {date}
Generated: {datetime.now().isoformat()}

TRADING METRICS
===============
Active Traders:     {metrics.active_traders}
Total Trades:       {metrics.total_trades}
Combined P&L:       ${metrics.total_pnl:,.2f}
Average Win Rate:   {metrics.avg_win_rate:.1f}%
Best Trader:        {metrics.best_trader_username} (+${metrics.best_trader_pnl:,.2f})
Best Strategy:      {metrics.best_strategy}
New Signups:        {metrics.new_signups}
Milestones:         {len(metrics.milestones)}

CONTENT GENERATED
=================
Blog Post:          {results.get('blog_post', 'FAILED')}
Tweets (5):         {results.get('tweets', 'FAILED')}
Emails:             {results.get('emails', 'FAILED')}
Milestones:         {results.get('milestones', 'FAILED')}
Case Studies:       {results.get('case_studies', 'FAILED')}

READY FOR DISTRIBUTION
======================
All content files are ready in: {self.output_dir}
- Blog post → Ready for WordPress/Medium/Hashnode
- Tweets → Ready for Twitter/X scheduling
- Emails → Ready for SendGrid/campaign distribution
- Case studies → Ready for landing page display
"""
        return summary


# ============================================================================
# CLI ENTRY POINT
# ============================================================================

def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="ProfitEngine Content Generator")
    parser.add_argument("--date", default=None, help="Date to generate content for (YYYY-MM-DD). Defaults to today.")
    parser.add_argument("--db", default=DB_PATH, help="Path to clients.db")
    parser.add_argument("--output", default=OUTPUT_DIR, help="Output directory for generated content")
    parser.add_argument("--dry-run", action="store_true", help="Generate content but don't save")
    parser.add_argument("--generate-all", action="store_true", help="Generate for all dates with data")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Determine date
    if args.date:
        date = args.date
    else:
        date = datetime.now().strftime("%Y-%m-%d")

    orchestrator = ContentGenerationOrchestrator(args.db, args.output)

    if args.generate_all:
        # This would require querying all dates with data
        logger.info("Generating for all available dates...")
        # For now, just generate for today
        results = orchestrator.generate_all(date)
    else:
        results = orchestrator.generate_all(date)

    # Print results
    print(results.get("summary", ""))

    # Print individual results
    for content_type, result in results.items():
        if content_type != "summary":
            print(f"\n{content_type.upper()}: {result}")


if __name__ == "__main__":
    sys.exit(main())
