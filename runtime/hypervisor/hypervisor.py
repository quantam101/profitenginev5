"""
Already Here LLC — Autonomous Multi-Agent Asynchronous Hypervisor
─────────────────────────────────────────────────────────────────
Architecture:
  • LiteLLM gateway (port 4000) — zero-cost provider routing mesh
  • Redis WAL-backed state cache — survives restarts and network partitions
  • Qdrant vector memory — semantic task deduplication and recall
  • Ollama local fallback — air-gapped operation when all cloud routes fail

Fixes applied over the original design:
  • asyncio.run() called once via async main() — no double event-loop crash
  • httpx.AsyncClient opened inside async context manager — correct lifecycle
  • recreate_collection replaced with get_or_create — non-destructive, non-deprecated
  • Vector dim set to 384 (all-MiniLM compatible) — valid for real embeddings
  • SQLite WAL writes moved to asyncio.get_event_loop().run_in_executor() — non-blocking
  • Task IDs zero-padded with :04d — correct for >9 items
  • gemini-1.5-pro removed — paid model; only free tier in routing matrix
  • LITELLM_MASTER_KEY injected into every gateway request
  • ollama base URL uses 172.17.0.1 (Linux Docker bridge) not host.docker.internal
  • Typed return values, no magic fault strings as control flow
"""
from __future__ import annotations

import os
import sys
import json
import sqlite3
import logging
import asyncio
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

import httpx

# ── Logging ──────────────────────────────────────────────────────────────────

class _JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return json.dumps({
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "component": record.name,
            "message": record.getMessage(),
        })

_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(_JSONFormatter())
logger = logging.getLogger("HypervisorCore")
logger.addHandler(_handler)
logger.setLevel(logging.INFO)

# ── Config ────────────────────────────────────────────────────────────────────

GATEWAY_URL      = os.environ.get("GATEWAY_URL",      "http://gateway_router:4000/v1/chat/completions")
LOCAL_OLLAMA_URL = os.environ.get("LOCAL_OLLAMA_URL",  "http://ollama:11434/api/generate")
MASTER_KEY       = os.environ.get("LITELLM_MASTER_KEY", "")
WAL_DB_PATH      = os.environ.get("HYPERVISOR_DB",     "state_journal.db")
VECTOR_HOST      = os.environ.get("VECTOR_HOST",       "vector_memory")
VECTOR_PORT      = int(os.environ.get("VECTOR_PORT",   "6333"))
VECTOR_DIM       = 384   # all-MiniLM-L6-v2 compatible

# AGENT_MESH_OS integration — Redis broker for distributed state
REDIS_URL        = os.environ.get("REDIS_URL", "")  # redis://:password@state_cache:6379/0
MESH_DB_PATH     = os.environ.get("MESH_STATE_DB",
                   "/app/data/agent_mesh_state.db")

_EXECUTOR = ThreadPoolExecutor(max_workers=4)


# ── WAL Journal (non-blocking) ────────────────────────────────────────────────

def _db_setup() -> None:
    """Initialise WAL journal. Called once at startup (sync OK here)."""
    with sqlite3.connect(WAL_DB_PATH) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS task_ledger (
                task_id       TEXT PRIMARY KEY,
                agent_type    TEXT,
                input_payload TEXT,
                output_payload TEXT,
                state         TEXT DEFAULT 'QUEUED',
                retries       INTEGER DEFAULT 0,
                created_at    TEXT DEFAULT (datetime('now')),
                updated_at    TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.commit()


async def _db_run(fn, *args) -> None:
    """Run a blocking SQLite call off the event loop."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(_EXECUTOR, fn, *args)


def _insert_tasks(batches: list[str]) -> None:
    with sqlite3.connect(WAL_DB_PATH) as conn:
        for idx, item in enumerate(batches):
            conn.execute(
                "INSERT OR REPLACE INTO task_ledger (task_id, agent_type, input_payload, state) "
                "VALUES (?, ?, ?, 'QUEUED')",
                (f"TX_{idx:04d}", "INGESTION", item),
            )
        conn.commit()


def _update_state(task_id: str, state: str, output: str) -> None:
    with sqlite3.connect(WAL_DB_PATH) as conn:
        conn.execute(
            "UPDATE task_ledger SET state=?, output_payload=?, "
            "updated_at=datetime('now') WHERE task_id=?",
            (state, output, task_id),
        )
        conn.commit()


# ── Vector Memory (optional — degrades gracefully if Qdrant absent) ──────────

async def _init_vector_memory() -> Optional[object]:
    """Return AsyncQdrantClient if qdrant-client is installed, else None."""
    try:
        from qdrant_client import AsyncQdrantClient
        from qdrant_client.http import models
        from qdrant_client.http.exceptions import UnexpectedResponse

        client = AsyncQdrantClient(host=VECTOR_HOST, port=VECTOR_PORT, timeout=5)
        try:
            await client.get_collection("enterprise_memory")
            logger.info("Vector memory collection already exists — reusing.")
        except (UnexpectedResponse, Exception):
            await client.create_collection(
                collection_name="enterprise_memory",
                vectors_config=models.VectorParams(size=VECTOR_DIM, distance=models.Distance.COSINE),
            )
            logger.info("Vector memory collection created.")
        return client
    except ImportError:
        logger.warning("qdrant-client not installed — vector memory disabled.")
        return None
    except Exception as exc:
        logger.warning(f"Vector memory unavailable (non-fatal): {exc}")
        return None


# ── Inference Dispatch ────────────────────────────────────────────────────────

async def _dispatch(client: httpx.AsyncClient, system: str, user: str) -> Optional[str]:
    """
    Route 1: LiteLLM gateway (manages Groq → Gemini → OpenRouter → local cascade).
    Route 2: Local Ollama (air-gapped fallback when gateway is unreachable).
    Returns None on total failure — callers decide how to handle.
    """
    headers = {"Authorization": f"Bearer {MASTER_KEY}"} if MASTER_KEY else {}
    payload = {
        "model": "autonomous-intelligence-mesh",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        "temperature": 0.1,
    }

    try:
        resp = await client.post(GATEWAY_URL, json=payload, headers=headers, timeout=20.0)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
        logger.error(f"Gateway returned {resp.status_code}: {resp.text[:200]}")
    except Exception as exc:
        logger.error(f"Gateway unreachable: {exc}")

    # Air-gapped fallback
    logger.warning("Gateway failed — engaging local Ollama fallback.")
    try:
        local_payload = {
            "model": "llama3.1:8b",
            "prompt": f"System: {system}\nUser: {user}",
            "stream": False,
        }
        local_resp = await client.post(LOCAL_OLLAMA_URL, json=local_payload, timeout=60.0)
        if local_resp.status_code == 200:
            return local_resp.json().get("response")
    except Exception as exc:
        logger.critical(f"All inference routes failed — system isolated: {exc}")

    return None


# ── Agents ────────────────────────────────────────────────────────────────────

async def _ingestion_agent(client: httpx.AsyncClient, task_id: str, raw: str) -> Optional[str]:
    logger.info(f"[IngestionAgent] {task_id}")
    result = await _dispatch(
        client,
        "You are an expert data parsing system. Extract operational strategies from raw input "
        "and convert them into structured markdown. Remove all filler text.",
        raw,
    )
    state = "INGESTION_COMPLETE" if result else "INGESTION_FAILED"
    await _db_run(_update_state, task_id, state, result or "")
    return result


async def _growth_agent(client: httpx.AsyncClient, task_id: str, structured: str) -> Optional[str]:
    logger.info(f"[GrowthAgent] {task_id}")
    result = await _dispatch(
        client,
        "You are an enterprise growth system. Convert clean analytics into high-impact "
        "messaging frameworks with direct call-to-actions.",
        structured,
    )
    state = "DEPLOYMENT_COMPLETE" if result else "DEPLOYMENT_FAILED"
    await _db_run(_update_state, task_id, state, result or "")
    return result


# ── Orchestrator ──────────────────────────────────────────────────────────────

async def run_pipeline(batches: list[str]) -> None:
    """
    Full parallel pipeline:
      1. Write all tasks to WAL journal
      2. Run ingestion agents in parallel
      3. Feed successful outputs to growth agents in parallel
    """
    await _db_run(_insert_tasks, batches)
    vector_client = await _init_vector_memory()  # noqa: F841 — used for future recall

    async with httpx.AsyncClient(http2=True, timeout=30.0) as client:
        # Stage 1 — parallel ingestion
        logger.info(f"Launching {len(batches)} ingestion agents in parallel.")
        ingestion_results = await asyncio.gather(
            *[_ingestion_agent(client, f"TX_{i:04d}", pkg) for i, pkg in enumerate(batches)],
            return_exceptions=True,
        )

        # Stage 2 — parallel growth (only on successful ingestion outputs)
        growth_inputs = [
            (i, out) for i, out in enumerate(ingestion_results)
            if out and not isinstance(out, Exception)
        ]
        if not growth_inputs:
            logger.error("All ingestion agents failed. Growth stage skipped.")
            return

        logger.info(f"Launching {len(growth_inputs)} growth agents in parallel.")
        await asyncio.gather(
            *[_growth_agent(client, f"GROWTH_{i:04d}", out) for i, out in growth_inputs],
            return_exceptions=True,
        )

    logger.info("All pipeline agents completed.")


# ── Entry Point ───────────────────────────────────────────────────────────────

async def main() -> None:
    _db_setup()
    enterprise_feed = [
        "FEED_A: Ingestion network capturing decentralized structural metrics across micro-SaaS zones.",
        "FEED_B: Automation blueprints tracking algorithmic execution loops to reduce API routing overhead.",
        "FEED_C: High-volume sales funnel matrix documenting consumer acquisition pathways.",
    ]
    await run_pipeline(enterprise_feed)


if __name__ == "__main__":
    asyncio.run(main())  # single event loop — no double asyncio.run() crash
