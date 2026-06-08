"""
Taylor — Multi-Carrier Redundancy & Failover Engine
Monitors primary Twilio/Retell stack and switches to Telnyx/Vapi on failure.
Runs as a background health probe alongside the main server.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

import aiohttp

logger = logging.getLogger("Taylor.Failover")

# ── State ─────────────────────────────────────────────────────────────────────

class RouteState(Enum):
    PRIMARY   = auto()   # Twilio + Retell
    SECONDARY = auto()   # Telnyx + Vapi
    LOCAL     = auto()   # Pre-recorded TTS + cell transfer

@dataclass
class FailoverState:
    route:            RouteState = RouteState.PRIMARY
    consecutive_fails: int = 0
    last_failure:     float = 0.0
    recovery_timeout: float = 120.0   # seconds before re-trying primary
    fail_threshold:   int = 2

    def record_failure(self) -> RouteState:
        self.consecutive_fails += 1
        self.last_failure = time.monotonic()
        if self.consecutive_fails >= self.fail_threshold:
            if self.route is RouteState.PRIMARY:
                self.route = RouteState.SECONDARY
                logger.warning("Failover: PRIMARY → SECONDARY (Telnyx + Vapi)")
            elif self.route is RouteState.SECONDARY:
                self.route = RouteState.LOCAL
                logger.warning("Failover: SECONDARY → LOCAL (cell transfer)")
        return self.route

    def record_success(self) -> None:
        self.consecutive_fails = 0
        if self.route is not RouteState.PRIMARY:
            elapsed = time.monotonic() - self.last_failure
            if elapsed >= self.recovery_timeout:
                self.route = RouteState.PRIMARY
                logger.info("Failover: Recovered → PRIMARY")

    @property
    def voice_platform_url(self) -> str:
        if self.route is RouteState.PRIMARY:
            return os.getenv("RETELL_WEBHOOK_URL", "https://api.retellai.com")
        return os.getenv("VAPI_WEBHOOK_URL", "https://api.vapi.ai")

    @property
    def telephony_provider(self) -> str:
        return "twilio" if self.route is RouteState.PRIMARY else "telnyx"

_state = FailoverState()

# ── Health probes ─────────────────────────────────────────────────────────────

async def _probe_retell() -> bool:
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(
                "https://api.retellai.com",
                timeout=aiohttp.ClientTimeout(total=2),
            ) as r:
                return r.status < 500
    except Exception:
        return False

async def _probe_twilio() -> bool:
    sid = os.getenv("TWILIO_ACCOUNT_SID", "")
    tok = os.getenv("TWILIO_AUTH_TOKEN", "")
    if not sid or not tok:
        return True  # not configured — assume ok
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(
                f"https://api.twilio.com/2010-04-01/Accounts/{sid}.json",
                auth=aiohttp.BasicAuth(sid, tok),
                timeout=aiohttp.ClientTimeout(total=3),
            ) as r:
                return r.status == 200
    except Exception:
        return False

async def run_health_monitor(interval: float = 30.0) -> None:
    """Background task — probes both voice and telephony layers every `interval` seconds."""
    logger.info(f"Failover monitor started (interval={interval}s)")
    while True:
        retell_ok = await _probe_retell()
        twilio_ok = await _probe_twilio()
        if retell_ok and twilio_ok:
            _state.record_success()
            logger.debug(f"Health OK — route={_state.route.name}")
        else:
            new_route = _state.record_failure()
            logger.warning(
                f"Health FAIL retell={retell_ok} twilio={twilio_ok} → route={new_route.name}"
            )
        await asyncio.sleep(interval)

def get_active_route() -> RouteState:
    return _state.route

def get_failover_state() -> FailoverState:
    return _state
