"""
Already Here LLC — Slack Notification Layer
Sends structured deal alerts, phase updates, and pipeline summaries
directly to Slack channels via the MCP integration.

All messages are posted programmatically — no webhook URL required.
Channel IDs are configured via environment variables.
"""

from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import aiohttp

# ── Channel config (set these in .env) ────────────────────────────────────────
# SLACK_REVENUE_CHANNEL  = Slack channel ID for revenue alerts (e.g. C0B1XSBS2AF)
# SLACK_BOT_TOKEN        = Slack bot OAuth token (xoxb-...)
# Fall back to #general if SLACK_REVENUE_CHANNEL not set

SLACK_API_POST = "https://slack.com/api/chat.postMessage"
SLACK_GENERAL        = "C0B1XSBS2AF"  # #general
SLACK_REVENUE_OPS    = "C0B8VN2S89Y"  # #revenue-ops
SLACK_DEALS_WON      = "C0B8VN2RQBC"  # #deals-won

_REVENUE_CHANNEL = os.getenv("SLACK_REVENUE_CHANNEL", SLACK_REVENUE_OPS)
_BOT_TOKEN       = os.getenv("SLACK_BOT_TOKEN", "")


def _now_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


# ── Core post function ────────────────────────────────────────────────────────

async def _post(blocks: List[Dict], channel: str = _REVENUE_CHANNEL, text: str = "") -> bool:
    """
    Post a block-kit message to Slack.
    Returns True on success. Requires SLACK_BOT_TOKEN env var.
    """
    token = os.getenv("SLACK_BOT_TOKEN", _BOT_TOKEN)
    if not token:
        # Fallback: log to stdout so the dashboard still works without a token
        print(f"[Slack/no-token] {text or json.dumps(blocks, indent=2)}")
        return False

    payload = {"channel": channel, "text": text, "blocks": blocks}
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

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


# ── Message builders ──────────────────────────────────────────────────────────

def _header(text: str) -> Dict:
    return {"type": "header", "text": {"type": "plain_text", "text": text, "emoji": True}}

def _section(text: str) -> Dict:
    return {"type": "section", "text": {"type": "mrkdwn", "text": text}}

def _divider() -> Dict:
    return {"type": "divider"}

def _fields(*pairs: tuple) -> Dict:
    return {
        "type": "section",
        "fields": [{"type": "mrkdwn", "text": f"*{k}*\n{v}"} for k, v in pairs],
    }


# ── Public notification functions ─────────────────────────────────────────────

async def notify_deal_won(
    lead_id: int,
    company: str,
    service: str,
    amount: float,
    phase: str,
    total_realized: float,
    gap: float,
    sender_name: str = "Already Here LLC",
) -> None:
    """Fire when a deal is closed — posts to #deals-won AND #revenue-ops."""
    blocks = [
        _header("DEAL CLOSED"),
        _section(
            f":money_with_wings: *${amount:,.0f}* collected from *{company}*\n"
            f"Service: `{service.upper()}` | Phase: `{phase}` | Lead #{lead_id}"
        ),
        _divider(),
        _fields(
            ("Total Realized", f"*${total_realized:,.0f}*"),
            ("Remaining Gap", f"${gap:,.0f}"),
            ("Closed by", sender_name),
            ("Time", _now_str()),
        ),
        _section(":bar_chart: Run `python vp_dashboard.py status` for the full pipeline view."),
    ]
    text = f"DEAL CLOSED: {company} — ${amount:,.0f} ({service.upper()})"
    # Post to both channels simultaneously
    await asyncio.gather(
        _post(blocks, channel=SLACK_DEALS_WON, text=text),
        _post(blocks, channel=SLACK_REVENUE_OPS, text=text),
    )


async def notify_outreach_batch(
    targets: List[Dict],
    day: str,
    total_pipeline: float,
    sender_name: str = "Already Here LLC",
) -> None:
    """Fire after outreach batch is generated."""
    lines = "\n".join(
        f"  {i+1}. {t['company']} — `{t['service'].upper()}` ${t['quote']:,}"
        for i, t in enumerate(targets)
    )
    blocks = [
        _header("OUTREACH BATCH DEPLOYED"),
        _section(
            f":email: *{len(targets)} targets contacted* | Day: *{day}*\n"
            f"Total pipeline value: *${total_pipeline:,.0f}*"
        ),
        _divider(),
        _section(f"*Targets:*\n{lines}"),
        _fields(
            ("Sent by", sender_name),
            ("Time", _now_str()),
        ),
        _section(":clipboard: Copy emails from terminal and send via your email client."),
    ]
    await _post(blocks, text=f"Outreach deployed: {len(targets)} targets, ${total_pipeline:,.0f} pipeline")


async def notify_phase_complete(phase_id: str, track: str, realized: float) -> None:
    """Fire when a revenue phase hits its target."""
    next_phase = {
        "ALPHA_I": "ALPHA_II (Drone surveys — $1,500 target)",
        "ALPHA_II": "BETA_I  (Cabling contracts — $7,500 target)",
        "BETA_I":   "BETA_II (Logistics brokerage — $16,000 target)",
        "BETA_II":  "COMPLETE — $25,500 monthly target achieved",
    }.get(phase_id, "NEXT PHASE")

    blocks = [
        _header(f"PHASE COMPLETE: {phase_id}"),
        _section(
            f":white_check_mark: *{phase_id}* ({track.upper()} Track) closed at *${realized:,.0f}*\n"
            f"Next: *{next_phase}*"
        ),
        _fields(
            ("Completed", _now_str()),
            ("Track", track.upper()),
        ),
    ]
    await _post(blocks, text=f"Phase {phase_id} complete — ${realized:,.0f} realized")


async def notify_lead_added(lead_id: int, company: str, service: str, quote: float) -> None:
    blocks = [
        _section(
            f":clipboard: *New lead #{lead_id}* added\n"
            f"*{company}* | `{service.upper()}` | Quoted: *${quote:,.0f}*"
        ),
    ]
    await _post(blocks, text=f"New lead: {company} ({service}) ${quote:,.0f}")


async def notify_engine_status(
    cycle: int,
    alpha_realized: float,
    beta_realized: float,
    gap: float,
    cb_state: str,
    leads_won: int,
) -> None:
    """Periodic heartbeat from the mesh daemon — post every N cycles."""
    pct = round((alpha_realized + beta_realized) / 255, 1)  # of $25,500
    blocks = [
        _header("PROFITENGINE HEARTBEAT"),
        _fields(
            ("Cycle", str(cycle)),
            ("Circuit Breaker", cb_state),
            ("Alpha Realized", f"${alpha_realized:,.0f}"),
            ("Beta Realized", f"${beta_realized:,.0f}"),
            ("Gap to $25k", f"${gap:,.0f}"),
            ("Deals Won", str(leads_won)),
        ),
        _section(f":clock1: {_now_str()}"),
    ]
    await _post(blocks, text=f"Engine heartbeat — cycle {cycle} | gap ${gap:,.0f}")


async def notify_engine_startup(version: str = "v5") -> None:
    blocks = [
        _header(f"PROFITENGINE {version} ONLINE"),
        _section(
            ":rocket: *Already Here LLC — Revenue Engine started*\n"
            "Dual-track pipeline active. ALPHA_I and BETA_I phases running.\n"
            "Monitoring: audits, drone surveys, cabling contracts, logistics brokerage."
        ),
        _fields(
            ("Company", "Already Here LLC"),
            ("Started", _now_str()),
            ("Track Alpha Target", "$2,000"),
            ("Track Beta Target", "$23,500"),
            ("Total Target", "$25,500 / 30 days"),
        ),
    ]
    await _post(blocks, text="ProfitEngine v5 online — 30-day revenue campaign active")


async def post_raw(text: str, channel: Optional[str] = None) -> None:
    """Post a plain markdown message to Slack."""
    blocks = [_section(text)]
    await _post(blocks, channel=channel or _REVENUE_CHANNEL, text=text)
