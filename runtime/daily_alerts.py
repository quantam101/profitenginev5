"""
DAILY ALERTS ENGINE — Market Close Alert System (5 PM MST)
Runs daily at 5 PM MST (market close) to send email/Telegram summaries.

Generates:
  1. Top 5 performers (by win rate and P&L)
  2. New customer signups (count and details)
  3. System health status (trading activity, database integrity)
  4. Upsell opportunities (clients ready for premium tiers)
  5. Daily P&L aggregate

Sends via:
  - Email (Gmail SMTP, SendGrid, or AWS SES)
  - Telegram (optional, for critical updates)
  - Slack (optional, for team notifications)

Environment variables required:
  EMAIL_PROVIDER         — 'gmail', 'sendgrid', or 'aws_ses' (default: gmail)
  GMAIL_USER             — Gmail address (if using Gmail)
  GMAIL_APP_PASSWORD     — Gmail app password (if using Gmail)
  SENDGRID_API_KEY       — SendGrid API key (if using SendGrid)
  AWS_ACCESS_KEY_ID      — AWS credentials (if using SES)
  AWS_SECRET_ACCESS_KEY  — AWS credentials (if using SES)
  AWS_SES_REGION         — AWS region for SES (default: us-east-1)
  ALERT_EMAIL            — Recipient email (default: dispatch@alreadyherellc.com)
  TELEGRAM_BOT_TOKEN     — Bot token for Telegram alerts (optional)
  TELEGRAM_CHAT_ID       — Chat ID for Telegram alerts (optional)
  SLACK_WEBHOOK_URL      — Webhook URL for Slack alerts (optional)
  CLIENTS_DB_PATH        — Path to clients.db (default: clients.db)
"""

from __future__ import annotations

import os
import sys
import sqlite3
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal
from dataclasses import dataclass, asdict
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

# Try to import optional dependencies
try:
    import sendgrid
    from sendgrid.helpers.mail import Mail, Email, To, Content
except ImportError:
    sendgrid = None

try:
    import boto3
except ImportError:
    boto3 = None

try:
    import requests
except ImportError:
    requests = None


# ============================================================================
# LOGGING
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("daily_alerts.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================

EMAIL_PROVIDER = os.getenv("EMAIL_PROVIDER", "gmail").lower()
ALERT_EMAIL = os.getenv("ALERT_EMAIL", "dispatch@alreadyherellc.com")
DB_PATH = os.getenv("CLIENTS_DB_PATH", "clients.db")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "").strip()

# Email provider configs
GMAIL_USER = os.getenv("GMAIL_USER", "").strip()
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "").strip()
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "").strip()
AWS_REGION = os.getenv("AWS_SES_REGION", "us-east-1")


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class ClientPerformance:
    """Client trading performance snapshot"""
    client_id: str
    username: str
    email: Optional[str]
    account_balance: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    daily_pnl: float
    daily_trades: int
    subscription_tier: str
    days_since_signup: int
    last_trade_time: Optional[datetime]

    @property
    def win_rate(self) -> float:
        """Calculate win rate percentage"""
        if self.total_trades == 0:
            return 0.0
        return (self.winning_trades / self.total_trades) * 100

    @property
    def avg_win(self) -> float:
        """Average win per winning trade"""
        if self.winning_trades == 0:
            return 0.0
        return self.daily_pnl / self.winning_trades if self.daily_pnl > 0 else 0.0


@dataclass
class DailyAlertData:
    """Complete daily alert summary"""
    date: datetime
    total_clients: int
    active_clients_today: int
    total_daily_trades: int
    total_daily_pnl: float
    system_health_status: str

    top_performers: List[ClientPerformance]
    new_signups: List[ClientPerformance]
    upsell_candidates: List[Dict[str, Any]]

    timestamp: datetime


# ============================================================================
# DATABASE QUERIES
# ============================================================================

class DatabaseQueries:
    """All database query logic for daily alerts"""

    def __init__(self, db_path: str):
        """Initialize with database path"""
        self.db_path = db_path

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_daily_pnl_summary(self) -> Tuple[float, int, int]:
        """
        Get today's aggregate P&L, trade count, and active traders.
        Returns: (total_pnl, trade_count, active_traders_count)
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            today = datetime.now(timezone.utc).date()

            # Get today's trades from daily_trades table
            cursor.execute("""
                SELECT
                    SUM(num_trades) as trade_count,
                    SUM(win_count) as winning_trades,
                    SUM(COALESCE(pnl_dollars, 0)) as total_pnl
                FROM daily_trades
                WHERE DATE(date) = ?
            """, (today.isoformat(),))

            row = cursor.fetchone()
            trade_count = row["trade_count"] or 0
            total_pnl = row["total_pnl"] or 0.0

            # Get active traders today
            cursor.execute("""
                SELECT COUNT(DISTINCT user_id) as active_count
                FROM daily_trades
                WHERE DATE(date) = ?
            """, (today.isoformat(),))

            active_row = cursor.fetchone()
            active_count = active_row["active_count"] or 0

            conn.close()
            return total_pnl, trade_count, active_count

        except Exception as e:
            logger.error(f"Error querying daily P&L: {e}")
            return 0.0, 0, 0

    def get_top_performers(self, limit: int = 5) -> List[ClientPerformance]:
        """
        Get top performers for today by P&L and win rate.
        Returns top N clients active today.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            today = datetime.now(timezone.utc).date()

            cursor.execute("""
                SELECT
                    ts.user_id,
                    c.username,
                    c.email,
                    ts.total_pnl as account_balance,
                    ts.total_trades,
                    ts.winning_trades,
                    ts.losing_trades,
                    c.tier as subscription_tier,
                    c.account_created as created_at,
                    COALESCE(dt.pnl_dollars, 0) as daily_pnl,
                    COALESCE(dt.num_trades, 0) as daily_trades
                FROM trader_stats ts
                LEFT JOIN clients c ON ts.user_id = c.user_id
                LEFT JOIN daily_trades dt ON ts.user_id = dt.user_id AND DATE(dt.date) = ?
                WHERE ts.total_trades > 0
                ORDER BY daily_pnl DESC, ts.win_rate DESC
                LIMIT ?
            """, (today.isoformat(), limit))

            performers = []
            now = datetime.now(timezone.utc)

            for row in cursor.fetchall():
                created = datetime.fromisoformat(row["created_at"]) if row["created_at"] else now
                days_since = (now - created).days if isinstance(created, datetime) else 0

                perf = ClientPerformance(
                    client_id=row["user_id"],
                    username=row["username"] or "Unknown",
                    email=row["email"],
                    account_balance=float(row["account_balance"] or 0),
                    total_trades=row["total_trades"] or 0,
                    winning_trades=row["winning_trades"] or 0,
                    losing_trades=row["losing_trades"] or 0,
                    daily_pnl=float(row["daily_pnl"] or 0),
                    daily_trades=row["daily_trades"] or 0,
                    subscription_tier=row["subscription_tier"] or "Free",
                    days_since_signup=days_since,
                    last_trade_time=None,
                )
                performers.append(perf)

            conn.close()
            return performers

        except Exception as e:
            logger.error(f"Error querying top performers: {e}")
            return []

    def get_new_signups(self, days: int = 1) -> List[ClientPerformance]:
        """
        Get clients who signed up in the last N days.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

            cursor.execute("""
                SELECT
                    c.user_id,
                    c.username,
                    c.email,
                    c.tier as subscription_tier,
                    c.account_created as created_at,
                    ts.total_trades,
                    ts.winning_trades,
                    ts.losing_trades,
                    ts.total_pnl as account_balance
                FROM clients c
                LEFT JOIN trader_stats ts ON c.user_id = ts.user_id
                WHERE c.account_created > ?
                ORDER BY c.account_created DESC
            """, (cutoff_date.isoformat(),))

            signups = []
            now = datetime.now(timezone.utc)
            today = now.date()

            for row in cursor.fetchall():
                created = datetime.fromisoformat(row["created_at"]) if row["created_at"] else now
                days_since = (now - created).days if isinstance(created, datetime) else 0

                # Get today's stats for this new client
                cursor.execute("""
                    SELECT
                        COALESCE(pnl_dollars, 0) as daily_pnl,
                        COALESCE(num_trades, 0) as daily_trades
                    FROM daily_trades
                    WHERE user_id = ? AND DATE(date) = ?
                """, (row["user_id"], today.isoformat()))

                trade_row = cursor.fetchone()
                daily_pnl = float(trade_row["daily_pnl"] if trade_row else 0.0)
                daily_trades = int(trade_row["daily_trades"] if trade_row else 0)

                perf = ClientPerformance(
                    client_id=row["user_id"],
                    username=row["username"] or "Unknown",
                    email=row["email"],
                    account_balance=float(row["account_balance"] or 0),
                    total_trades=row["total_trades"] or 0,
                    winning_trades=row["winning_trades"] or 0,
                    losing_trades=row["losing_trades"] or 0,
                    daily_pnl=daily_pnl,
                    daily_trades=daily_trades,
                    subscription_tier=row["subscription_tier"] or "Free",
                    days_since_signup=days_since,
                    last_trade_time=None,
                )
                signups.append(perf)

            conn.close()
            return signups

        except Exception as e:
            logger.error(f"Error querying new signups: {e}")
            return []

    def get_total_clients(self) -> int:
        """Get total number of registered clients"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(DISTINCT user_id) as count FROM clients")
            result = cursor.fetchone()
            conn.close()
            return result["count"] if result else 0
        except Exception as e:
            logger.error(f"Error counting clients: {e}")
            return 0

    def check_database_health(self) -> str:
        """
        Check database integrity and return status.
        Returns: status string ('healthy', 'degraded', 'error')
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Check table integrity
            cursor.execute("SELECT COUNT(*) as count FROM clients")
            clients = cursor.fetchone()["count"]

            cursor.execute("SELECT COUNT(*) as count FROM trades")
            trades = cursor.fetchone()["count"]

            conn.close()

            if clients == 0 or trades == 0:
                return "degraded"

            return "healthy"

        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return "error"

    def get_upsell_candidates(self) -> List[Dict[str, Any]]:
        """
        Get clients ready for upsell based on performance metrics.
        Candidates: win_rate >= 70%, OR daily_pnl > threshold, OR 5+ winning streak
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            today = datetime.now(timezone.utc).date()

            cursor.execute("""
                SELECT
                    ts.user_id,
                    c.username,
                    c.email,
                    ts.total_pnl as account_balance,
                    ts.total_trades,
                    ts.winning_trades,
                    ts.losing_trades,
                    ts.win_rate,
                    c.tier as subscription_tier,
                    COALESCE(dt.pnl_dollars, 0) as daily_pnl
                FROM trader_stats ts
                LEFT JOIN clients c ON ts.user_id = c.user_id
                LEFT JOIN daily_trades dt ON ts.user_id = dt.user_id AND DATE(dt.date) = ?
                WHERE ts.total_trades >= 20
                    AND (ts.win_rate >= 0.70 OR COALESCE(dt.pnl_dollars, 0) > 500 OR ts.winning_trades >= 10)
                ORDER BY ts.win_rate DESC
                LIMIT 10
            """, (today.isoformat(),))

            candidates = []
            for row in cursor.fetchall():
                win_rate = float(row["win_rate"] or 0) * 100

                # Determine tier recommendation
                if win_rate >= 85:
                    tier = "White-Label / Enterprise"
                    message = "Proven high-performance trader. Enterprise features recommended."
                elif win_rate >= 70:
                    tier = "Hybrid Tier"
                    message = "Consistent performer. Upgrade to Hybrid for premium support."
                else:
                    tier = "Premium Features"
                    message = "Active trader with growth potential."

                candidates.append({
                    "client_id": row["user_id"],
                    "username": row["username"] or "Unknown",
                    "email": row["email"],
                    "win_rate": round(win_rate, 1),
                    "total_trades": row["total_trades"] or 0,
                    "daily_pnl": round(float(row["daily_pnl"] or 0), 2),
                    "account_balance": round(float(row["account_balance"] or 0), 2),
                    "current_tier": row["subscription_tier"] or "Free",
                    "recommended_tier": tier,
                    "sales_message": message,
                    "priority": "high" if win_rate >= 85 else "medium",
                })

            conn.close()
            return candidates

        except Exception as e:
            logger.error(f"Error querying upsell candidates: {e}")
            return []


# ============================================================================
# EMAIL TEMPLATES
# ============================================================================

class EmailTemplates:
    """HTML email template generation"""

    @staticmethod
    def daily_alert_html(
        alert_data: DailyAlertData,
        top_performers: List[ClientPerformance],
        new_signups: List[ClientPerformance],
        upsell_candidates: List[Dict[str, Any]],
        system_health: str,
    ) -> str:
        """
        Generate professional HTML email for daily alert.
        """
        pnl_color = "#28a745" if alert_data.total_daily_pnl >= 0 else "#dc3545"
        health_color = "#28a745" if system_health == "healthy" else "#ffc107" if system_health == "degraded" else "#dc3545"

        top_performers_html = ""
        for i, perf in enumerate(top_performers, 1):
            top_performers_html += f"""
            <tr>
                <td style='padding:10px;border-bottom:1px solid #eee'>{i}</td>
                <td style='padding:10px;border-bottom:1px solid #eee'><strong>{perf.username}</strong></td>
                <td style='padding:10px;border-bottom:1px solid #eee;text-align:right'>{perf.win_rate:.1f}%</td>
                <td style='padding:10px;border-bottom:1px solid #eee;text-align:right'>${perf.daily_pnl:,.2f}</td>
                <td style='padding:10px;border-bottom:1px solid #eee;text-align:center'>{perf.daily_trades}</td>
                <td style='padding:10px;border-bottom:1px solid #eee;font-size:12px'>{perf.subscription_tier}</td>
            </tr>
            """

        new_signups_html = ""
        if new_signups:
            for signup in new_signups:
                new_signups_html += f"""
                <li style='margin-bottom:8px'>
                    <strong>{signup.username}</strong> ({signup.email or 'no-email'})
                    — Free tier • {signup.daily_trades} trades today (${signup.daily_pnl:,.2f})
                </li>
                """
        else:
            new_signups_html = "<li style='color:#999'>No new signups today</li>"

        upsell_html = ""
        for candidate in upsell_candidates[:3]:  # Top 3 only
            upsell_html += f"""
            <div style='background:#f9f9f9;padding:12px;margin-bottom:10px;border-left:4px solid #ffc107;border-radius:4px'>
                <strong>{candidate['username']}</strong> — Win Rate: {candidate['win_rate']:.1f}%
                <br><small style='color:#666'>{candidate['sales_message']}</small>
                <br><small style='color:#999'>Recommended: {candidate['recommended_tier']}</small>
            </div>
            """

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset='utf-8'>
            <meta name='viewport' content='width=device-width, initial-scale=1.0'>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; color: #333; }}
                .container {{ max-width: 700px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                .header h1 {{ margin: 0; font-size: 28px; }}
                .header p {{ margin: 5px 0 0 0; font-size: 14px; opacity: 0.9; }}
                .section {{ background: white; padding: 20px; border-bottom: 1px solid #eee; }}
                .section h2 {{ margin: 0 0 15px 0; font-size: 18px; color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; }}
                .stat-box {{ display: inline-block; padding: 15px 20px; margin-right: 15px; margin-bottom: 10px; background: #f5f5f5; border-radius: 6px; }}
                .stat-value {{ font-size: 24px; font-weight: bold; color: {pnl_color}; }}
                .stat-label {{ font-size: 12px; color: #666; margin-top: 5px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                th {{ text-align: left; padding: 10px; background: #f5f5f5; font-weight: 600; border-bottom: 2px solid #ddd; }}
                td {{ padding: 10px; border-bottom: 1px solid #eee; }}
                .footer {{ background: #f9f9f9; padding: 15px; font-size: 12px; color: #999; text-align: center; border-radius: 0 0 8px 8px; }}
                .health-badge {{ display: inline-block; padding: 5px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; color: white; background: {health_color}; }}
            </style>
        </head>
        <body>
            <div class='container'>
                <div class='header'>
                    <h1>ProfitEngine Daily Alert</h1>
                    <p>{alert_data.date.strftime('%A, %B %d, %Y')} • 5 PM MST Market Close</p>
                </div>

                <!-- DAILY SUMMARY -->
                <div class='section'>
                    <h2>Daily Summary</h2>
                    <div class='stat-box'>
                        <div class='stat-value' style='color: {pnl_color}'>${alert_data.total_daily_pnl:,.2f}</div>
                        <div class='stat-label'>Total Daily P&L</div>
                    </div>
                    <div class='stat-box'>
                        <div class='stat-value'>{alert_data.total_daily_trades}</div>
                        <div class='stat-label'>Trades Executed</div>
                    </div>
                    <div class='stat-box'>
                        <div class='stat-value'>{alert_data.active_clients_today}</div>
                        <div class='stat-label'>Active Traders</div>
                    </div>
                    <div class='stat-box'>
                        <div class='stat-value'>{alert_data.total_clients}</div>
                        <div class='stat-label'>Total Customers</div>
                    </div>
                    <div style='clear:both;margin-top:15px'>
                        <span class='health-badge'>{system_health.upper()}</span>
                    </div>
                </div>

                <!-- TOP PERFORMERS -->
                <div class='section'>
                    <h2>Top 5 Performers Today</h2>
                    {
                        f"""
                    <table>
                        <thead>
                            <tr>
                                <th style='width:5%'>#</th>
                                <th style='width:25%'>Trader</th>
                                <th style='width:15%'>Win Rate</th>
                                <th style='width:20%'>Today P&L</th>
                                <th style='width:15%'>Trades</th>
                                <th style='width:20%'>Tier</th>
                            </tr>
                        </thead>
                        <tbody>
                            {top_performers_html or '<tr><td colspan="6" style="text-align:center;color:#999;padding:20px">No trades today</td></tr>'}
                        </tbody>
                    </table>
                    """ if top_performers else "<p style='color:#999'>No trading activity today</p>"
                    }
                </div>

                <!-- NEW SIGNUPS -->
                <div class='section'>
                    <h2>New Customers ({len(new_signups)})</h2>
                    <ul style='margin:0;padding-left:20px'>
                        {new_signups_html}
                    </ul>
                </div>

                <!-- UPSELL OPPORTUNITIES -->
                <div class='section'>
                    <h2>Upsell Opportunities</h2>
                    {upsell_html if upsell_html else "<p style='color:#999'>No upsell candidates at this time</p>"}
                </div>

                <!-- FOOTER -->
                <div class='footer'>
                    <p style='margin:0'>ProfitEngine Autonomous Trading System<br>
                    Already Here LLC • dispatch@alreadyherellc.com<br>
                    This alert runs automatically at 5 PM MST daily</p>
                </div>
            </div>
        </body>
        </html>
        """

        return html

    @staticmethod
    def daily_alert_text(
        alert_data: DailyAlertData,
        top_performers: List[ClientPerformance],
        new_signups: List[ClientPerformance],
        upsell_candidates: List[Dict[str, Any]],
    ) -> str:
        """
        Generate plain text version of daily alert.
        """
        lines = [
            "ProfitEngine Daily Alert",
            f"{alert_data.date.strftime('%A, %B %d, %Y')} • 5 PM MST Market Close",
            "",
            "═" * 60,
            "DAILY SUMMARY",
            "═" * 60,
            f"Total Daily P&L:      ${alert_data.total_daily_pnl:>12,.2f}",
            f"Trades Executed:      {alert_data.total_daily_trades:>12}",
            f"Active Traders:       {alert_data.active_clients_today:>12}",
            f"Total Customers:      {alert_data.total_clients:>12}",
            f"System Health:        {alert_data.system_health_status.upper():>12}",
            "",
            "═" * 60,
            "TOP 5 PERFORMERS",
            "═" * 60,
        ]

        if top_performers:
            lines.append(f"{'#':<3} {'Trader':<15} {'Win Rate':<12} {'Today P&L':<15} {'Trades':<8} {'Tier':<15}")
            lines.append("-" * 68)
            for i, perf in enumerate(top_performers, 1):
                lines.append(
                    f"{i:<3} {perf.username:<15} {perf.win_rate:>10.1f}% ${perf.daily_pnl:>12,.2f} {perf.daily_trades:>8} {perf.subscription_tier:<15}"
                )
        else:
            lines.append("No trading activity today")

        lines.extend([
            "",
            "═" * 60,
            f"NEW CUSTOMERS ({len(new_signups)})",
            "═" * 60,
        ])

        if new_signups:
            for signup in new_signups:
                lines.append(
                    f"• {signup.username} ({signup.email or 'no-email'}) - {signup.daily_trades} trades, ${signup.daily_pnl:,.2f}"
                )
        else:
            lines.append("No new signups today")

        lines.extend([
            "",
            "═" * 60,
            "UPSELL OPPORTUNITIES",
            "═" * 60,
        ])

        if upsell_candidates:
            for candidate in upsell_candidates[:3]:
                lines.append(f"\n{candidate['username']}")
                lines.append(f"  Win Rate: {candidate['win_rate']:.1f}%")
                lines.append(f"  Recommended: {candidate['recommended_tier']}")
                lines.append(f"  Message: {candidate['sales_message']}")
        else:
            lines.append("No upsell candidates at this time")

        lines.extend([
            "",
            "═" * 60,
            "ProfitEngine Autonomous Trading System",
            "Already Here LLC • dispatch@alreadyherellc.com",
            "═" * 60,
        ])

        return "\n".join(lines)


# ============================================================================
# EMAIL SENDERS
# ============================================================================

class EmailSender:
    """Abstract email sender interface"""

    def send(
        self,
        to: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
    ) -> bool:
        """Send email. Returns True on success."""
        raise NotImplementedError


class GmailSender(EmailSender):
    """Send via Gmail SMTP"""

    def __init__(self, gmail_user: str, app_password: str):
        self.gmail_user = gmail_user
        self.app_password = app_password

    def send(
        self,
        to: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
    ) -> bool:
        """Send email via Gmail SMTP"""
        if not self.gmail_user or not self.app_password:
            logger.error("Gmail credentials not configured")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"ProfitEngine <{self.gmail_user}>"
            msg["To"] = to

            if body_text:
                msg.attach(MIMEText(body_text, "plain"))
            msg.attach(MIMEText(body_html, "html"))

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(self.gmail_user, self.app_password)
                server.sendmail(self.gmail_user, to, msg.as_string())

            logger.info(f"Email sent successfully to {to} via Gmail")
            return True

        except Exception as e:
            logger.error(f"Failed to send email via Gmail: {e}")
            return False


class SendGridSender(EmailSender):
    """Send via SendGrid API"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        if sendgrid is None:
            logger.error("sendgrid package not installed")

    def send(
        self,
        to: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
    ) -> bool:
        """Send email via SendGrid"""
        if sendgrid is None or not self.api_key:
            logger.error("SendGrid not available or not configured")
            return False

        try:
            from_email = Email(GMAIL_USER or "noreply@profitengine.com")
            to_email = To(to)
            content = Content("text/html", body_html)

            mail = Mail(from_email, to_email, subject, content)

            if body_text:
                mail.add_content(body_text, "text/plain", 0)

            sg = sendgrid.SendGridAPIClient(self.api_key)
            response = sg.send(mail)

            logger.info(f"Email sent successfully to {to} via SendGrid")
            return True

        except Exception as e:
            logger.error(f"Failed to send email via SendGrid: {e}")
            return False


class AmazonSESSender(EmailSender):
    """Send via AWS SES"""

    def __init__(self, region: str = "us-east-1"):
        self.region = region
        if boto3 is None:
            logger.error("boto3 package not installed")
            self.client = None
        else:
            try:
                self.client = boto3.client("ses", region_name=region)
            except Exception as e:
                logger.error(f"Failed to initialize SES: {e}")
                self.client = None

    def send(
        self,
        to: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
    ) -> bool:
        """Send email via AWS SES"""
        if not self.client:
            logger.error("AWS SES not available or not configured")
            return False

        try:
            self.client.send_email(
                Source=GMAIL_USER or "noreply@profitengine.com",
                Destination={"ToAddresses": [to]},
                Message={
                    "Subject": {"Data": subject, "Charset": "UTF-8"},
                    "Body": {
                        "Html": {"Data": body_html, "Charset": "UTF-8"},
                        **({"Text": {"Data": body_text, "Charset": "UTF-8"}} if body_text else {}),
                    },
                },
            )

            logger.info(f"Email sent successfully to {to} via AWS SES")
            return True

        except Exception as e:
            logger.error(f"Failed to send email via AWS SES: {e}")
            return False


# ============================================================================
# NOTIFICATION CHANNELS
# ============================================================================

def send_telegram_alert(chat_id: str, message: str) -> bool:
    """Send alert to Telegram chat"""
    if not TELEGRAM_BOT_TOKEN:
        logger.warning("Telegram not configured (TELEGRAM_BOT_TOKEN not set)")
        return False

    if requests is None:
        logger.error("requests package not installed")
        return False

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message[:3900],
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }

        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            logger.info(f"Telegram alert sent to chat {chat_id}")
            return True
        else:
            logger.error(f"Telegram API error: {response.status_code}")
            return False

    except Exception as e:
        logger.error(f"Failed to send Telegram alert: {e}")
        return False


def send_slack_alert(webhook_url: str, message: str, pnl: float) -> bool:
    """Send alert to Slack webhook"""
    if not webhook_url or requests is None:
        logger.warning("Slack not configured")
        return False

    try:
        color = "good" if pnl >= 0 else "danger"
        payload = {
            "attachments": [
                {
                    "color": color,
                    "title": "ProfitEngine Daily Alert",
                    "text": message[:2000],
                    "footer": "ProfitEngine Autonomous Trading",
                    "ts": int(datetime.now().timestamp()),
                }
            ]
        }

        response = requests.post(webhook_url, json=payload, timeout=10)
        if response.status_code == 200:
            logger.info("Slack alert sent")
            return True
        else:
            logger.error(f"Slack webhook error: {response.status_code}")
            return False

    except Exception as e:
        logger.error(f"Failed to send Slack alert: {e}")
        return False


# ============================================================================
# MAIN ALERT ORCHESTRATOR
# ============================================================================

class DailyAlertOrchestrator:
    """Main orchestrator for daily alerts"""

    def __init__(self, db_path: str):
        self.db = DatabaseQueries(db_path)
        self.email_sender = self._init_email_sender()

    def _init_email_sender(self) -> Optional[EmailSender]:
        """Initialize appropriate email sender based on configuration"""
        provider = EMAIL_PROVIDER.lower()

        if provider == "sendgrid" and SENDGRID_API_KEY:
            logger.info("Using SendGrid email provider")
            return SendGridSender(SENDGRID_API_KEY)

        elif provider == "aws_ses":
            logger.info("Using AWS SES email provider")
            return AmazonSESSender(AWS_REGION)

        else:  # Default to Gmail
            if GMAIL_USER and GMAIL_APP_PASSWORD:
                logger.info("Using Gmail email provider")
                return GmailSender(GMAIL_USER, GMAIL_APP_PASSWORD)
            else:
                logger.warning("No email provider fully configured")
                return None

    def generate_alert(self) -> DailyAlertData:
        """Generate complete daily alert data"""
        logger.info("Generating daily alert...")

        # Query all metrics
        total_pnl, total_trades, active_clients = self.db.get_daily_pnl_summary()
        top_performers = self.db.get_top_performers(limit=5)
        new_signups = self.db.get_new_signups(days=1)
        upsell_candidates = self.db.get_upsell_candidates()
        total_clients = self.db.get_total_clients()
        health = self.db.check_database_health()

        alert_data = DailyAlertData(
            date=datetime.now(timezone.utc),
            total_clients=total_clients,
            active_clients_today=active_clients,
            total_daily_trades=total_trades,
            total_daily_pnl=total_pnl,
            system_health_status=health,
            top_performers=top_performers,
            new_signups=new_signups,
            upsell_candidates=upsell_candidates,
            timestamp=datetime.now(timezone.utc),
        )

        return alert_data

    def send_alerts(self, alert_data: DailyAlertData) -> bool:
        """Send all configured alerts"""
        logger.info("Sending alerts...")
        success = False

        # Generate templates
        email_html = EmailTemplates.daily_alert_html(
            alert_data,
            alert_data.top_performers,
            alert_data.new_signups,
            alert_data.upsell_candidates,
            alert_data.system_health_status,
        )

        email_text = EmailTemplates.daily_alert_text(
            alert_data,
            alert_data.top_performers,
            alert_data.new_signups,
            alert_data.upsell_candidates,
        )

        # Send email
        if self.email_sender:
            email_success = self.email_sender.send(
                to=ALERT_EMAIL,
                subject=f"ProfitEngine Daily Alert — {alert_data.date.strftime('%B %d, %Y')} • ${alert_data.total_daily_pnl:,.2f} P&L",
                body_html=email_html,
                body_text=email_text,
            )
            success = email_success

            # Log email
            if email_success:
                with open("daily_alerts.log", "a") as f:
                    f.write(
                        f"\n[{datetime.now().isoformat()}] Email sent to {ALERT_EMAIL} "
                        f"• P&L: ${alert_data.total_daily_pnl:,.2f} • Trades: {alert_data.total_daily_trades}\n"
                    )
        else:
            logger.warning("No email sender configured")

        # Send Telegram alert
        if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            telegram_msg = f"""
            <b>ProfitEngine Daily Alert</b>

            <b>P&L:</b> ${alert_data.total_daily_pnl:,.2f}
            <b>Trades:</b> {alert_data.total_daily_trades}
            <b>Active Traders:</b> {alert_data.active_clients_today}
            <b>New Customers:</b> {len(alert_data.new_signups)}
            <b>Upsell Candidates:</b> {len(alert_data.upsell_candidates)}
            """
            send_telegram_alert(TELEGRAM_CHAT_ID, telegram_msg)

        # Send Slack alert
        if SLACK_WEBHOOK_URL:
            slack_summary = f"Daily P&L: ${alert_data.total_daily_pnl:,.2f} | {alert_data.total_daily_trades} trades | {alert_data.active_clients_today} active traders"
            send_slack_alert(SLACK_WEBHOOK_URL, slack_summary, alert_data.total_daily_pnl)

        return success

    def run(self) -> bool:
        """Generate and send all daily alerts"""
        try:
            alert_data = self.generate_alert()
            return self.send_alerts(alert_data)
        except Exception as e:
            logger.error(f"Alert failed: {e}")
            return False


# ============================================================================
# CLI ENTRY POINT
# ============================================================================

def main():
    """CLI entry point for running daily alerts"""
    import argparse

    parser = argparse.ArgumentParser(description="ProfitEngine Daily Alert System")
    parser.add_argument("--db", default=DB_PATH, help="Path to clients.db")
    parser.add_argument("--email", default=ALERT_EMAIL, help="Email recipient")
    parser.add_argument("--dry-run", action="store_true", help="Generate alert without sending")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    orchestrator = DailyAlertOrchestrator(args.db)
    alert_data = orchestrator.generate_alert()

    # Print summary
    print("\n" + "=" * 60)
    print("DAILY ALERT SUMMARY")
    print("=" * 60)
    print(f"Date: {alert_data.date.strftime('%A, %B %d, %Y')}")
    print(f"Total Daily P&L: ${alert_data.total_daily_pnl:,.2f}")
    print(f"Trades Executed: {alert_data.total_daily_trades}")
    print(f"Active Traders: {alert_data.active_clients_today}")
    print(f"Total Customers: {alert_data.total_clients}")
    print(f"System Health: {alert_data.system_health_status.upper()}")
    print(f"Top Performers: {len(alert_data.top_performers)}")
    print(f"New Signups: {len(alert_data.new_signups)}")
    print(f"Upsell Candidates: {len(alert_data.upsell_candidates)}")
    print("=" * 60 + "\n")

    if not args.dry_run:
        success = orchestrator.send_alerts(alert_data)
        if success:
            print(f"Alert sent successfully to {args.email}")
        else:
            print("Alert failed to send (check logs)")
        return 0 if success else 1
    else:
        print("DRY RUN — Alert not sent")
        return 0


if __name__ == "__main__":
    sys.exit(main())
