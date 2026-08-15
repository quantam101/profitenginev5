"""
ProfitEngine v5 — Async Edge-Mesh Payment Engine
Dual-Track Velocity Model:
  Track Alpha (Immediate Cash-Flow): IT audits, drone data surveys
  Track Beta  ($25k Scaler):        Structured cabling, logistics brokerage

Architecture: CLOSED/OPEN/HALF-OPEN circuit breaker, WAL SQLite, parallel Ollama inference,
idempotent Stripe Checkout, exponential-backoff retry, dead-letter queue, daemon loop.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import random
import signal
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
import aiosqlite
from pydantic import BaseModel, Field, field_validator
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel

from token_distiller import distill_payload, estimate_tokens
from revenue_matrix import RevenueMatrix

# ── Environment validation (fail-fast — no placeholders ever) ─────────────────

_REQUIRED_ENV: Tuple[str, ...] = (
    "STRIPE_SECRET_KEY",
    "MESH_SYSTEM_WEBHOOK",
    "STRIPE_SUCCESS_URL",
    "STRIPE_CANCEL_URL",
)


def _load_config() -> Dict[str, str]:
    missing = [k for k in _REQUIRED_ENV if not os.getenv(k)]
    if missing:
        sys.exit(
            f"[FATAL] Missing required env vars: {', '.join(missing)}\n"
            "Export them before starting the engine. No defaults are provided."
        )
    return {k: os.environ[k] for k in _REQUIRED_ENV}


# ── Structured JSON logging ───────────────────────────────────────────────────

class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return json.dumps(
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "level": record.levelname,
                "node": "MESH_CORE",
                "msg": record.getMessage(),
                "exc": self.formatException(record.exc_info) if record.exc_info else None,
            },
            default=str,
        )


def _build_logger() -> logging.Logger:
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(_JsonFormatter())
    log = logging.getLogger("MeshEngine")
    log.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
    log.addHandler(h)
    log.propagate = False
    return log


logger = _build_logger()


# ── Data schemas (Pydantic v2) ────────────────────────────────────────────────

class StripeProductSchema(BaseModel):
    product_name: str = Field(..., min_length=1, max_length=250)
    price_in_cents: int = Field(..., ge=50, le=99_999_999)  # Stripe floor: $0.50
    currency: str = Field(default="usd", pattern=r"^[a-z]{3}$")
    stripe_payment_behavior: str = Field(default="payment")

    @field_validator("stripe_payment_behavior")
    @classmethod
    def _valid_mode(cls, v: str) -> str:
        allowed = {"payment", "subscription", "setup"}
        if v not in allowed:
            raise ValueError(f"stripe_payment_behavior must be one of {allowed}")
        return v


class ContentPayload(BaseModel):
    headline: str = Field(..., min_length=5, max_length=300)
    copy_body: str = Field(..., min_length=50)
    affiliate_cta: str = Field(..., min_length=5)
    monetization_structure: StripeProductSchema


# ── Circuit Breaker (CLOSED → OPEN → HALF-OPEN → CLOSED) ─────────────────────

class _CBState(Enum):
    CLOSED = auto()
    OPEN = auto()
    HALF_OPEN = auto()


@dataclass
class CircuitBreaker:
    failure_threshold: int = 3
    success_threshold: int = 2   # consecutive successes in HALF_OPEN to close
    recovery_timeout: float = 60.0

    _state: _CBState = field(default=_CBState.CLOSED, init=False, repr=False)
    _failures: int = field(default=0, init=False, repr=False)
    _half_open_successes: int = field(default=0, init=False, repr=False)
    _opened_at: float = field(default=0.0, init=False, repr=False)

    @property
    def state(self) -> _CBState:
        if self._state is _CBState.OPEN:
            if time.monotonic() - self._opened_at >= self.recovery_timeout:
                self._state = _CBState.HALF_OPEN
                self._half_open_successes = 0
                logger.info("Circuit → HALF_OPEN: probing upstream")
        return self._state

    @property
    def allows_traffic(self) -> bool:
        return self.state in (_CBState.CLOSED, _CBState.HALF_OPEN)

    def record_success(self) -> None:
        s = self.state
        if s is _CBState.HALF_OPEN:
            self._half_open_successes += 1
            if self._half_open_successes >= self.success_threshold:
                self._state = _CBState.CLOSED
                self._failures = 0
                logger.info("Circuit → CLOSED: upstream healthy")
        elif s is _CBState.CLOSED:
            self._failures = max(0, self._failures - 1)  # decay

    def record_failure(self) -> None:
        self._failures += 1
        if self.state in (_CBState.CLOSED, _CBState.HALF_OPEN):
            if self._failures >= self.failure_threshold:
                self._state = _CBState.OPEN
                self._opened_at = time.monotonic()
                logger.warning(f"Circuit → OPEN: {self._failures} consecutive failures")


# ── Exponential backoff with jitter ──────────────────────────────────────────

async def _with_backoff(
    fn,
    *args: Any,
    retries: int = 4,
    base: float = 1.0,
    cap: float = 30.0,
    **kwargs: Any,
) -> Any:
    for attempt in range(retries):
        try:
            return await fn(*args, **kwargs)
        except Exception as exc:
            if attempt == retries - 1:
                raise
            delay = min(base * 2 ** attempt + random.uniform(0, 0.5), cap)
            logger.warning(f"Attempt {attempt + 1}/{retries} failed ({exc!r}); retry in {delay:.1f}s")
            await asyncio.sleep(delay)


# ── WAL SQLite persistence (fully async via aiosqlite) ───────────────────────

_DB_PATH = os.getenv("MESH_DB_PATH", "production_mesh_edge.db")

_PRAGMA = (
    "PRAGMA journal_mode=WAL;"
    "PRAGMA synchronous=NORMAL;"
    "PRAGMA foreign_keys=ON;"
    "PRAGMA cache_size=-32000;"   # 32 MB page cache
    "PRAGMA temp_store=MEMORY;"
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS asset_pipeline (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword             TEXT    UNIQUE NOT NULL,
    niche               TEXT    NOT NULL,
    headline            TEXT,
    copy_body           TEXT,
    affiliate_cta       TEXT,
    stripe_product_name TEXT,
    stripe_price_cents  INTEGER,
    stripe_currency     TEXT    DEFAULT 'usd',
    stripe_behavior     TEXT    DEFAULT 'payment',
    stripe_session_id   TEXT,           -- idempotency anchor
    stripe_checkout_url TEXT,
    processing_state    TEXT    DEFAULT 'QUEUED',   -- QUEUED | COMPILED | FAILED
    sync_state          TEXT    DEFAULT 'UNSYNCED', -- UNSYNCED | SYNCED | DEAD
    retry_count         INTEGER DEFAULT 0,
    inserted_at         TEXT    NOT NULL,
    compiled_at         TEXT,
    synchronized_at     TEXT,
    error_msg           TEXT
);

CREATE TABLE IF NOT EXISTS dead_letter (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    pipeline_id INTEGER NOT NULL,
    reason      TEXT,
    payload     TEXT,
    created_at  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_processing_state ON asset_pipeline(processing_state);
CREATE INDEX IF NOT EXISTS idx_sync_state       ON asset_pipeline(sync_state);
"""

_MAX_SYNC_RETRIES = int(os.getenv("MESH_MAX_SYNC_RETRIES", "5"))


class EdgeStorageManager:
    def __init__(self, db_path: str = _DB_PATH) -> None:
        self._path = db_path

    async def init(self) -> None:
        async with aiosqlite.connect(self._path) as db:
            await db.executescript(_PRAGMA)
            await db.executescript(_SCHEMA)
            await db.commit()
        logger.info(f"WAL database ready: {self._path}")

    async def seed(self, records: List[Tuple[str, str]]) -> None:
        ts = _now()
        async with aiosqlite.connect(self._path) as db:
            await db.executemany(
                "INSERT OR IGNORE INTO asset_pipeline (keyword, niche, inserted_at) VALUES (?,?,?)",
                [(kw, niche, ts) for kw, niche in records],
            )
            await db.commit()

    async def pending(self, limit: int = 20) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self._path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "SELECT id, keyword, niche FROM asset_pipeline WHERE processing_state='QUEUED' LIMIT ?",
                (limit,),
            )
            return [dict(r) for r in await cur.fetchall()]

    async def save_asset(self, node_id: int, payload: ContentPayload) -> None:
        m = payload.monetization_structure
        async with aiosqlite.connect(self._path) as db:
            await db.execute(
                """UPDATE asset_pipeline
                   SET headline=?, copy_body=?, affiliate_cta=?,
                       stripe_product_name=?, stripe_price_cents=?,
                       stripe_currency=?, stripe_behavior=?,
                       processing_state='COMPILED', compiled_at=?
                   WHERE id=?""",
                (
                    payload.headline, payload.copy_body, payload.affiliate_cta,
                    m.product_name, m.price_in_cents, m.currency,
                    m.stripe_payment_behavior, _now(), node_id,
                ),
            )
            await db.commit()

    async def mark_generation_failed(self, node_id: int, error: str) -> None:
        async with aiosqlite.connect(self._path) as db:
            await db.execute(
                """UPDATE asset_pipeline
                   SET processing_state='FAILED', retry_count=retry_count+1, error_msg=?
                   WHERE id=?""",
                (error[:500], node_id),
            )
            await db.commit()

    async def unsynced(self, limit: int = 25) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self._path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                """SELECT id, keyword, headline, copy_body, affiliate_cta,
                          stripe_product_name, stripe_price_cents, stripe_currency,
                          stripe_behavior, stripe_session_id, retry_count
                   FROM asset_pipeline
                   WHERE processing_state='COMPILED'
                     AND sync_state='UNSYNCED'
                     AND retry_count < ?
                   LIMIT ?""",
                (_MAX_SYNC_RETRIES, limit),
            )
            return [dict(r) for r in await cur.fetchall()]

    async def mark_synced(self, node_id: int, session_id: str, checkout_url: str) -> None:
        async with aiosqlite.connect(self._path) as db:
            await db.execute(
                """UPDATE asset_pipeline
                   SET sync_state='SYNCED', synchronized_at=?,
                       stripe_session_id=?, stripe_checkout_url=?
                   WHERE id=?""",
                (_now(), session_id, checkout_url, node_id),
            )
            await db.commit()

    async def increment_sync_retry(self, node_id: int, error: str) -> None:
        async with aiosqlite.connect(self._path) as db:
            await db.execute(
                "UPDATE asset_pipeline SET retry_count=retry_count+1, error_msg=? WHERE id=?",
                (error[:500], node_id),
            )
            await db.commit()

    async def dead_letter(self, node_id: int, reason: str, payload: Dict[str, Any]) -> None:
        async with aiosqlite.connect(self._path) as db:
            await db.execute(
                "INSERT INTO dead_letter (pipeline_id, reason, payload, created_at) VALUES (?,?,?,?)",
                (node_id, reason, json.dumps(payload, default=str), _now()),
            )
            await db.execute(
                "UPDATE asset_pipeline SET sync_state='DEAD', error_msg=? WHERE id=?",
                (reason[:500], node_id),
            )
            await db.commit()
        logger.error(f"Node {node_id} moved to dead-letter: {reason}")


# ── AI inference agent (local Ollama) ─────────────────────────────────────────

_OLLAMA_BASE  = (os.getenv("OLLAMA_BASE_URL") or "").strip()
_OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")  # llama3.2 confirmed installed

_SYSTEM_PROMPT = (
    "You are a precision affiliate-content compiler running in a production payment pipeline. "
    "For each request output ONLY a valid JSON object that conforms exactly to the ContentPayload schema. "
    "Rules: price_in_cents ≥ 50 (integer); currency is lowercase ISO-4217 (e.g. 'usd'); "
    "stripe_payment_behavior is one of 'payment', 'subscription', or 'setup'. "
    "headline ≤ 300 chars; copy_body ≥ 50 chars. No prose outside the JSON object."
)


def _build_agent() -> Agent | None:
    if not _OLLAMA_BASE:
        logger.warning("OLLAMA_BASE_URL is not configured — mesh AI generation disabled.")
        return None
    model = OpenAIChatModel(
        model_name=_OLLAMA_MODEL,
        base_url=_OLLAMA_BASE,
        api_key="ollama",  # Ollama ignores auth; SDK requires a non-empty value
    )
    return Agent(model=model, result_type=ContentPayload, system_prompt=_SYSTEM_PROMPT)


# ── Network connectivity probes ───────────────────────────────────────────────

_PROBE_TARGETS = [
    "https://1.1.1.1",           # Cloudflare DNS — fast, reliable
    "https://8.8.8.8",           # Google DNS — fallback
    "https://api.stripe.com/v1", # Validates Stripe path specifically
]


async def _probe_connectivity(session: aiohttp.ClientSession) -> bool:
    for target in _PROBE_TARGETS:
        try:
            async with session.get(target, timeout=aiohttp.ClientTimeout(total=3)) as r:
                if r.status < 500:
                    return True
        except Exception:
            continue
    return False


# ── Stripe Checkout (idempotent) ──────────────────────────────────────────────

async def _stripe_create_session(
    session: aiohttp.ClientSession,
    api_key: str,
    success_url: str,
    cancel_url: str,
    row: Dict[str, Any],
    idempotency_key: str,
) -> Tuple[str, str]:
    """Returns (session_id, checkout_url). Raises RuntimeError on Stripe rejection."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/x-www-form-urlencoded",
        "Idempotency-Key": idempotency_key,
        "Stripe-Version": "2024-06-20",
    }
    form = {
        "success_url": success_url,
        "cancel_url": cancel_url,
        "mode": row["stripe_behavior"],
        "line_items[0][price_data][currency]": row["stripe_currency"],
        "line_items[0][price_data][unit_amount]": str(row["stripe_price_cents"]),
        "line_items[0][price_data][product_data][name]": row["stripe_product_name"],
        "line_items[0][quantity]": "1",
    }
    async with session.post(
        "https://api.stripe.com/v1/checkout/sessions",
        headers=headers,
        data=form,
        timeout=aiohttp.ClientTimeout(total=10),
    ) as resp:
        body = await resp.json(content_type=None)
        if resp.status != 200:
            msg = body.get("error", {}).get("message", str(body))
            raise RuntimeError(f"Stripe {resp.status}: {msg}")
        return body["id"], body["url"]


# ── Parallel generation pool ──────────────────────────────────────────────────

async def run_generation_pool(
    storage: EdgeStorageManager,
    agent: Agent,
    concurrency: int = 4,
) -> None:
    tasks = await storage.pending(limit=concurrency * 5)
    if not tasks:
        logger.info("Generation queue empty — standby")
        return

    sem = asyncio.Semaphore(concurrency)

    async def _run_one(task: Dict[str, Any]) -> None:
        async with sem:
            prompt = f"Niche context: '{task['niche']}'. Target keyword: '{task['keyword']}'."
            try:
                result = await _with_backoff(agent.run, prompt, retries=3, base=2.0)
                await storage.save_asset(task["id"], result.data)
                logger.info(f"Compiled: [{task['keyword']}]")
            except Exception as exc:
                logger.error(f"Generation failed node {task['id']}: {exc}")
                await storage.mark_generation_failed(task["id"], str(exc))

    await asyncio.gather(*(_run_one(t) for t in tasks))


# ── Edge sync + Stripe settlement pipeline ────────────────────────────────────

async def run_sync_pipeline(
    storage: EdgeStorageManager,
    cb: CircuitBreaker,
    stripe_key: str,
    webhook_url: str,
    success_url: str,
    cancel_url: str,
) -> None:
    batch = await storage.unsynced(limit=25)
    if not batch:
        logger.info("Sync buffer balanced — nothing pending")
        return

    if not cb.allows_traffic:
        logger.warning(f"Circuit {cb.state.name}: sync deferred until recovery_timeout expires")
        return

    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as http:

        if not await _probe_connectivity(http):
            cb.record_failure()
            logger.warning(f"Connectivity lost — CB state={cb.state.name}, failures={cb._failures}")
            return

        for row in batch:
            node_id: int = row["id"]
            # Stable idempotency key: survives restarts, safe to replay
            idempotency_key = f"mesh-node-{node_id}-{row['keyword'][:40]}"

            try:
                # Resume: if Stripe session already created, skip to webhook dispatch
                session_id: str = row.get("stripe_session_id") or ""
                checkout_url = ""

                if not session_id:
                    session_id, checkout_url = await _with_backoff(
                        _stripe_create_session,
                        http, stripe_key, success_url, cancel_url, row, idempotency_key,
                        retries=3,
                    )
                    logger.info(f"Stripe session created: {session_id} for node {node_id}")

                packet = {
                    "node_id": node_id,
                    "keyword": row["keyword"],
                    "headline": row["headline"],
                    "copy_body": row["copy_body"],
                    "affiliate_cta": row["affiliate_cta"],
                    "stripe_session_id": session_id,
                    "stripe_checkout_url": checkout_url,
                }

                async with http.post(
                    webhook_url,
                    json=packet,
                    timeout=aiohttp.ClientTimeout(total=8),
                ) as resp:
                    if resp.status == 200:
                        await storage.mark_synced(node_id, session_id, checkout_url)
                        cb.record_success()
                        logger.info(f"Node {node_id} synced and settled")
                    else:
                        body = await resp.text()
                        raise RuntimeError(f"Webhook {resp.status}: {body[:200]}")

            except Exception as exc:
                cb.record_failure()
                await storage.increment_sync_retry(node_id, str(exc))
                logger.error(f"Sync failed node {node_id} (retry_count={row['retry_count']+1}): {exc}")

                # Exhaust retries → dead-letter to protect the queue
                if row["retry_count"] + 1 >= _MAX_SYNC_RETRIES:
                    await storage.dead_letter(node_id, str(exc), row)


# ── Graceful shutdown ─────────────────────────────────────────────────────────

_STOP: asyncio.Event = asyncio.Event()


def _on_signal(sig: int, _frame: Any) -> None:
    logger.info(f"Signal {sig} received — draining current cycle then exiting")
    _STOP.set()


# ── Daemon loop ───────────────────────────────────────────────────────────────

async def _daemon(
    storage: EdgeStorageManager,
    agent: Agent,
    cb: CircuitBreaker,
    config: Dict[str, str],
    concurrency: int,
    interval: float,
    matrix: Optional[RevenueMatrix] = None,
) -> None:
    logger.info(f"Mesh daemon started (cycle={interval}s, concurrency={concurrency})")
    cycle = 0
    while not _STOP.is_set():
        cycle += 1
        t0 = time.monotonic()
        logger.info(f"--- Cycle {cycle} begin ---")
        try:
            tasks = [
                run_generation_pool(storage, agent, concurrency=concurrency),
                run_sync_pipeline(
                    storage, cb,
                    stripe_key=config["STRIPE_SECRET_KEY"],
                    webhook_url=config["MESH_SYSTEM_WEBHOOK"],
                    success_url=config["STRIPE_SUCCESS_URL"],
                    cancel_url=config["STRIPE_CANCEL_URL"],
                ),
            ]
            # Dual-track revenue heartbeat every cycle
            if matrix is not None:
                tasks += [_alpha_track_tick(matrix), _beta_track_tick(matrix)]

            await asyncio.gather(*tasks)
        except Exception as exc:
            logger.error(f"Daemon cycle {cycle} unhandled exception: {exc}", exc_info=True)

        elapsed = time.monotonic() - t0
        sleep_for = max(0.0, interval - elapsed)
        logger.info(f"Cycle {cycle} done in {elapsed:.2f}s — next in {sleep_for:.0f}s")

        try:
            await asyncio.wait_for(_STOP.wait(), timeout=sleep_for)
        except asyncio.TimeoutError:
            pass  # normal — sleep elapsed, loop again

    logger.info("Daemon loop exited cleanly")


# ── Entry point ───────────────────────────────────────────────────────────────

async def _alpha_track_tick(matrix: RevenueMatrix) -> None:
    """Track Alpha heartbeat: log current cash-flow posture each daemon cycle."""
    dashboard = await matrix.dashboard()
    alpha_pct = (
        dashboard["alpha_realized_usd"] /
        max(sum(p["target_usd"] for p in dashboard["phases"] if p["track"] == "alpha"), 1)
        * 100
    )
    logger.info(
        f"[Track Alpha] realized=${dashboard['alpha_realized_usd']:,.0f} "
        f"({alpha_pct:.0f}% of Alpha target) | leads won={dashboard['lead_won']}"
    )


async def _beta_track_tick(matrix: RevenueMatrix) -> None:
    """Track Beta heartbeat: log $25k scaler posture each daemon cycle."""
    dashboard = await matrix.dashboard()
    logger.info(
        f"[Track Beta] realized=${dashboard['beta_realized_usd']:,.0f} "
        f"| total gap=${dashboard['gap_usd']:,.0f} | {dashboard['completion_pct']}% complete"
    )


async def main() -> None:
    config = _load_config()  # exits if any required env var is missing

    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, _on_signal)

    storage = EdgeStorageManager()
    await storage.init()

    # Revenue matrix — dual-track
    matrix = RevenueMatrix(db_path=_DB_PATH)
    await matrix.init()

    # Seed initial keyword matrix (idempotent via INSERT OR IGNORE)
    seed_raw = os.getenv("MESH_SEED_JSON", "")
    if seed_raw:
        try:
            pairs = [(r["keyword"], r["niche"]) for r in json.loads(seed_raw)]
            await storage.seed(pairs)
            logger.info(f"Seeded {len(pairs)} keyword targets from MESH_SEED_JSON")
        except Exception as exc:
            logger.warning(f"MESH_SEED_JSON parse error — skipping seed: {exc}")

    agent = _build_agent()
    if agent is None:
        logger.error("Mesh engine cannot start without OLLAMA_BASE_URL")
        sys.exit(1)

    cb = CircuitBreaker(
        failure_threshold=int(os.getenv("CB_FAILURE_THRESHOLD", "3")),
        success_threshold=int(os.getenv("CB_SUCCESS_THRESHOLD", "2")),
        recovery_timeout=float(os.getenv("CB_RECOVERY_TIMEOUT_S", "60")),
    )

    concurrency = int(os.getenv("MESH_CONCURRENCY", "4"))
    interval    = float(os.getenv("MESH_CYCLE_INTERVAL_S", "30"))

    # Log initial distiller stats on startup
    sample_prompt = "Target niche: enterprise-software-affiliate. Keyword: cloud arbitrage."
    dr = distill_payload(sample_prompt, max_tokens=50, model=_OLLAMA_MODEL)
    logger.info(f"Token distiller online: {dr.original_tokens}→{dr.final_tokens} tokens on sample")

    # Activate the first phase of each track automatically
    await matrix.activate_phase("ALPHA_I")
    await matrix.activate_phase("BETA_I")

    await _daemon(storage, agent, cb, config, concurrency, interval, matrix=matrix)
    logger.info("Mesh engine shutdown complete")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    asyncio.run(main())
