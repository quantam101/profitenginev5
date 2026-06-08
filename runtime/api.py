from __future__ import annotations

import hashlib
import time
from dataclasses import asdict
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from .cycle_log import CycleLog
from .registry import RegistryError, RuntimeRegistry
from .sovereign_core import SovereignAutomationCore
from .telegram_gateway import format_runtime_reply, parse_update, send_telegram_message, stable_embedding, verify_secret

app = FastAPI(title="ProfitEngine Runtime API", version="0.1.0")
registry = RuntimeRegistry()


class ExecuteRequest(BaseModel):
    objective: str = Field(min_length=1, max_length=2000)
    system_declaration: str = Field(default="Registry-governed local execution.", max_length=4000)
    dynamic_context: str = Field(default="", max_length=8000)
    embedding_vector: List[float] = Field(default_factory=lambda: [0.001] * 384, min_length=1)
    namespace: str = Field(default="api", min_length=1, max_length=128)
    agent_id: str = Field(default="local-research", min_length=1, max_length=128)
    actor: str = Field(default="runtime-api", min_length=1, max_length=128)


class ConsensusRequest(BaseModel):
    objective: str = Field(min_length=1, max_length=2000)
    context: str = Field(default="", max_length=8000)
    agents: List[str] = Field(default_factory=list, max_length=10)
    timeout_sec: float = Field(default=60.0, ge=5.0, le=300.0)
    threshold: float = Field(default=0.67, ge=0.5, le=1.0)


class VideoRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=20, max_length=20000)
    canonical_url: str = Field(default="")


class EnqueueRequest(BaseModel):
    agent_type: str = Field(min_length=1, max_length=32)
    payload: Dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=1, ge=1, le=10)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or hashlib.sha256(f"{time.time_ns()}:{request.url.path}".encode()).hexdigest()[:16]
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    return response


@app.get("/health")
def health() -> Dict[str, Any]:
    core = SovereignAutomationCore()
    return {
        "ok": True,
        "service": "profitengine-runtime",
        "mode": core.cost_guard.status()["mode"],
        "registry": registry.status(),
    }


@app.get("/agents")
def agents() -> Dict[str, Any]:
    return {"agents": [asdict(agent) for agent in registry.agents.values()]}


@app.get("/connectors")
def connectors() -> Dict[str, Any]:
    return {"connectors": [asdict(connector) for connector in registry.connectors.values()]}


@app.get("/cycles")
def cycles(limit: int = 50) -> Dict[str, Any]:
    """Return the most-recent execution records (proof-of-work ledger)."""
    limit = max(1, min(limit, 500))
    log = CycleLog()
    records = log.tail(limit)
    return {"cycles": [asdict(r) for r in records], "count": len(records)}


@app.get("/metrics")
def metrics() -> Dict[str, Any]:
    """Return aggregate execution statistics."""
    log = CycleLog()
    return log.metrics()


@app.get("/telegram/health")
def telegram_health() -> Dict[str, Any]:
    import os

    return {
        "ok": True,
        "service": "profitengine-telegram-gateway",
        "bot_token_configured": bool(os.getenv("TELEGRAM_BOT_TOKEN", "").strip()),
        "webhook_secret_configured": bool(os.getenv("TELEGRAM_WEBHOOK_SECRET", "").strip()),
    }


@app.post("/telegram/webhook")
async def telegram_webhook(request: Request) -> Dict[str, Any]:
    if not verify_secret(request.headers.get("x-telegram-bot-api-secret-token")):
        raise HTTPException(status_code=403, detail="Invalid Telegram webhook secret")

    update = await request.json()
    command = parse_update(update)
    if command is None:
        return {"ok": True, "ignored": True}

    if not command.should_execute:
        sent = send_telegram_message(command.chat_id, command.objective)
        return {"ok": True, "executed": False, "reply_sent": sent, "agent_id": command.agent_id}

    payload = ExecuteRequest(
        objective=command.objective,
        system_declaration="Telegram command routed through ProfitEngine policy, cost guard, memory, and verifier.",
        dynamic_context=f"Telegram command: {command.text}",
        embedding_vector=stable_embedding(f"{command.agent_id}:{command.objective}"),
        namespace="telegram",
        agent_id=command.agent_id,
        actor=command.actor,
    )
    result = execute(payload)
    sent = send_telegram_message(command.chat_id, format_runtime_reply(result))
    return {
        "ok": True,
        "executed": True,
        "reply_sent": sent,
        "agent_id": command.agent_id,
        "status": result.get("status"),
        "route_tier": result.get("route_tier"),
    }


@app.post("/consensus")
async def consensus(payload: ConsensusRequest) -> Dict[str, Any]:
    """
    Run the same objective through N agents in parallel and return the
    supermajority-voted result (2-of-3 by default).

    Body fields
    -----------
    objective   : The task or question for all agents to execute.
    context     : Optional additional context injected into each agent prompt.
    agents      : Optional list of agent IDs (defaults to sovereign-orchestrator,
                  local-research, free-tier-cost-guard).
    timeout_sec : Per-agent timeout in seconds (5–300, default 60).
    threshold   : Quorum fraction required (0.5–1.0, default 0.67 = 2-of-3).
    """
    from .enterprise_mesh import ASIMeshEngine
    engine = ASIMeshEngine(
        agents=payload.agents or None,
        threshold=payload.threshold,
    )
    return await engine.dispatch_consensus(
        objective=payload.objective,
        context=payload.context,
        timeout_sec=payload.timeout_sec,
    )


@app.post("/video")
async def video(payload: VideoRequest) -> Dict[str, Any]:
    """
    Render a faceless vertical video from an article.
    Tier routing: GPU Wan → HF TTS slideshow → pure FFmpeg slideshow.

    Body: { title, body, canonical_url? }
    Returns: { ok, output_path, status }
    """
    from .eaos.video_engine import get_engine
    engine = get_engine()
    output = await engine.produce_article_video(
        title         = payload.title,
        body          = payload.body,
        canonical_url = payload.canonical_url,
    )
    return {
        "ok":          output is not None,
        "output_path": output,
        "status":      engine.status(),
    }


@app.post("/eaos/enqueue")
def eaos_enqueue(payload: EnqueueRequest) -> Dict[str, Any]:
    """Enqueue a task into the EAOS cluster (VIDEO / SOCIAL / POD / MESH)."""
    from .eaos.cluster_master import get_master
    master  = get_master()
    task_id = master.queue.enqueue(payload.agent_type, payload.payload, payload.priority)
    return {"ok": True, "task_id": task_id, "agent_type": payload.agent_type}


@app.get("/eaos/health")
def eaos_health() -> Dict[str, Any]:
    """EAOS cluster health: queue stats, metrics, video engine status."""
    from .eaos.cluster_master import get_master
    from .eaos.video_engine   import get_engine
    master = get_master()
    engine = get_engine()
    return {**master.health(), "video_engine": engine.status()}


@app.post("/execute")
def execute(payload: ExecuteRequest) -> Dict[str, Any]:
    try:
        core = SovereignAutomationCore()
        result = core.execute(
            payload.system_declaration,
            payload.dynamic_context,
            payload.objective,
            payload.embedding_vector,
            namespace=payload.namespace,
            actor=payload.actor,
            agent_id=payload.agent_id,
        )
    except RegistryError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return asdict(result)
