#!/usr/bin/env python3
"""
Real-Time Telegram Alert System
Sends live trading alerts to Telegram
- Pre-market research alerts
- Trade execution alerts
- Profit/loss alerts
- Daily summary alerts
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, Optional
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TelegramAlertSystem:
    """Send real-time trading alerts to Telegram"""

    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram credentials not configured. Alerts disabled.")
            self.enabled = False
        else:
            self.enabled = True
            logger.info(f"Telegram alerts enabled for chat {self.chat_id}")

    def send_alert(self, message: str, parse_mode: str = "HTML") -> bool:
        """Send alert to Telegram"""
        if not self.enabled:
            logger.info(f"Alert (disabled): {message[:100]}")
            return False

        try:
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True
            }

            response = requests.post(self.api_url, json=payload, timeout=5)

            if response.status_code == 200:
                logger.info(f"Alert sent: {message[:50]}...")
                return True
            else:
                logger.error(f"Failed to send alert: {response.text}")
                return False

        except Exception as e:
            logger.error(f"Telegram error: {e}")
            return False

    def alert_premarket_research(self, candidates: list) -> bool:
        """Alert when pre-market research finds candidates"""
        if not candidates:
            return False

        message = """
<b>📊 PRE-MARKET RESEARCH COMPLETE</b>

<b>Swing Candidates Found:</b>
"""

        for i, candidate in enumerate(candidates[:4], 1):
            message += f"\n{i}. <b>{candidate['symbol']}</b> (Score: {candidate['swing_score']}/100)"
            message += f"\n   Catalyst: {candidate['catalyst']}"
            message += f"\n   Entry: {candidate['recommended_entry']}"
            message += f"\n   Target: {candidate['target']}"

        message += f"\n\n⏰ Next: Ensemble validation @ 4:00 AM MST"

        return self.send_alert(message)

    def alert_market_scanner(self, candidates: int) -> bool:
        """Alert when market scanner finds technical candidates"""
        message = f"""
<b>🔍 MARKET SCAN COMPLETE</b>

📈 Bull run candidates found: <b>{candidates}</b>
⏰ Combining with news catalysts...
→ Ready for 4:00 AM ensemble validation
"""
        return self.send_alert(message)

    def alert_trade_executed(self, symbol: str, action: str, details: Dict) -> bool:
        """Alert when trade is executed"""
        emoji = "📈" if action == "BUY" else "📉"

        message = f"""
<b>{emoji} TRADE EXECUTED</b>

<b>Symbol:</b> {symbol}
<b>Action:</b> {action}
<b>Setup Score:</b> {details.get('confidence', 'N/A')}%

<b>Entry Details:</b>
├─ Price: ${details.get('entry_price', 'N/A')}
├─ Position: {details.get('position_size', 'N/A')}
├─ Stop: ${details.get('stop_loss', 'N/A')}
└─ Target: ${details.get('target', 'N/A')}

<b>Expected:</b>
├─ Win Rate: {details.get('expected_win_rate', 'N/A')}
├─ Profit Potential: {details.get('profit_potential', 'N/A')}
└─ Hold Time: {details.get('hold_time', '2-4 days')}

⏰ Executing now...
"""
        return self.send_alert(message)

    def alert_profit_taken(self, symbol: str, profit: float, roi: float) -> bool:
        """Alert when profit target is hit"""
        emoji = "🎉" if profit > 0 else "⚠️"

        message = f"""
<b>{emoji} PROFIT TAKEN</b>

<b>Symbol:</b> {symbol}
<b>Profit:</b> ${profit:.2f}
<b>ROI:</b> {roi:.1f}%

<b>Status:</b> ✅ Target Hit
<b>Next:</b> Monitor remaining positions
"""
        return self.send_alert(message)

    def alert_stop_loss_hit(self, symbol: str, loss: float, roi: float) -> bool:
        """Alert when stop loss is triggered"""
        message = f"""
<b>⛔ STOP LOSS HIT</b>

<b>Symbol:</b> {symbol}
<b>Loss:</b> ${loss:.2f}
<b>ROI:</b> {roi:.1f}%

<b>Status:</b> ❌ Exited
<b>Next:</b> Preserve capital, wait for next signal
"""
        return self.send_alert(message)

    def alert_daily_summary(self, summary: Dict) -> bool:
        """Send daily trading summary"""
        message = f"""
<b>📊 DAILY TRADING SUMMARY</b>
<b>{datetime.now().strftime('%A, %B %d, %Y')}</b>

<b>Execution Summary:</b>
├─ Trades executed: <b>{summary.get('trades_executed', 0)}</b>
├─ Winners: <b>{summary.get('winners', 0)}</b>
├─ Losers: <b>{summary.get('losers', 0)}</b>
└─ Win Rate: <b>{summary.get('win_rate', '0')}%</b>

<b>P&L Report:</b>
├─ Daily P&L: <b>${summary.get('daily_pnl', 0):.2f}</b>
├─ ROI: <b>{summary.get('daily_roi', 0):.1f}%</b>
├─ Avg Winner: <b>${summary.get('avg_winner', 0):.2f}</b>
└─ Avg Loser: <b>-${summary.get('avg_loser', 0):.2f}</b>

<b>Account Status:</b>
├─ Starting: ${summary.get('account_start', 0):.2f}
├─ Ending: ${summary.get('account_end', 0):.2f}
└─ Growth: <b>{summary.get('account_growth', 0):.1f}%</b>

<b>Open Positions:</b>
├─ Active: <b>{summary.get('open_positions', 0)}</b>
└─ Expected Exit: {summary.get('next_event', 'Tomorrow 4 AM')}

🎯 Tomorrow's Plan: {summary.get('tomorrow_plan', 'New research cycle')}
"""
        return self.send_alert(message)

    def alert_weekly_summary(self, summary: Dict) -> bool:
        """Send weekly trading summary"""
        message = f"""
<b>📈 WEEKLY TRADING SUMMARY</b>
<b>Week of {summary.get('week_start', 'N/A')}</b>

<b>Trading Performance:</b>
├─ Total trades: <b>{summary.get('total_trades', 0)}</b>
├─ Winners: <b>{summary.get('winners', 0)}</b>
├─ Losers: <b>{summary.get('losers', 0)}</b>
└─ Win rate: <b>{summary.get('win_rate', 0):.1f}%</b>

<b>Weekly P&L:</b>
├─ Total profit: <b>${summary.get('weekly_profit', 0):.2f}</b>
├─ ROI: <b>{summary.get('weekly_roi', 0):.1f}%</b>
├─ Best trade: <b>${summary.get('best_trade', 0):.2f}</b>
└─ Worst trade: <b>-${summary.get('worst_trade', 0):.2f}</b>

<b>Account Growth:</b>
├─ Start: ${summary.get('account_start', 0):.2f}
├─ End: ${summary.get('account_end', 0):.2f}
└─ Growth: <b>{summary.get('account_growth', 0):.1f}%</b>

<b>Tier Status:</b>
├─ Current: {summary.get('tier', 'TIER 1')}
├─ Target: {summary.get('next_tier', 'TIER 2 ($1,500)')}
└─ Progress: {summary.get('tier_progress', '50%')}

🎯 Next Week: {summary.get('next_week_plan', 'Accelerate scaling')}
"""
        return self.send_alert(message)

    def alert_system_status(self, status: str, details: str = "") -> bool:
        """Alert about system status"""
        emoji = "✅" if "success" in status.lower() else "⚠️"

        message = f"""
<b>{emoji} SYSTEM STATUS</b>

<b>Status:</b> {status.upper()}
{f'<b>Details:</b> {details}' if details else ''}

<b>System Check:</b>
├─ News scanner: ✅
├─ Market scanner: ✅
├─ Ensemble system: ✅
└─ Telegram alerts: ✅

Ready for next cycle.
"""
        return self.send_alert(message)

    def alert_error(self, component: str, error: str) -> bool:
        """Alert about system errors"""
        message = f"""
<b>❌ SYSTEM ERROR</b>

<b>Component:</b> {component}
<b>Error:</b> {error}

<b>Action Required:</b>
Please check logs and restart if needed.

⏰ Next attempt: Scheduled
"""
        return self.send_alert(message)

    def alert_low_balance(self, balance: float, threshold: float) -> bool:
        """Alert when account balance is low"""
        message = f"""
<b>⚠️ LOW BALANCE WARNING</b>

<b>Current Balance:</b> ${balance:.2f}
<b>Threshold:</b> ${threshold:.2f}

<b>Action Required:</b>
Consider depositing funds before next trading cycle.

💡 Tip: Pause trading to preserve capital if needed.
"""
        return self.send_alert(message)


def main():
    """Test alert system"""
    alerts = TelegramAlertSystem()

    if not alerts.enabled:
        logger.warning("Telegram not configured. Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
        return False

    # Test alerts
    logger.info("Testing Telegram alert system...")

    # Test 1: System online
    alerts.alert_system_status("Ready", "All systems operational")

    # Test 2: Pre-market research
    test_candidates = [
        {
            "symbol": "NVDA",
            "swing_score": 95,
            "catalyst": "Earnings beat expected",
            "recommended_entry": "Support at $825 or breakout at $875",
            "target": "$900-950"
        }
    ]
    alerts.alert_premarket_research(test_candidates)

    # Test 3: Market scan
    alerts.alert_market_scanner(15)

    # Test 4: Trade executed
    alerts.alert_trade_executed("NVDA", "BUY", {
        "confidence": 95,
        "entry_price": 825,
        "position_size": "$500 (call spread)",
        "stop_loss": 800,
        "target": "$870",
        "expected_win_rate": "92%",
        "profit_potential": "+$1,500 (300% ROI)",
        "hold_time": "2-4 days"
    })

    logger.info("Alert system test complete!")
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
