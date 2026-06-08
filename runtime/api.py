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


class SocialDistributeRequest(BaseModel):
    text:       str = Field(min_length=1, max_length=500)
    full_text:  str = Field(default="", max_length=50000)
    title:      str = Field(default="", max_length=300)
    url:        str = Field(default="")
    media_path: str = Field(default="")
    platforms:  List[str] = Field(default_factory=list)


class NewsletterRequest(BaseModel):
    headline: str = Field(min_length=5, max_length=200)
    sections: List[Dict[str, str]] = Field(min_length=1, max_length=10)
    tags: List[str] = Field(default_factory=list)
    cta_url: str = Field(default="https://alreadyherellc.com")


class CitySEORequest(BaseModel):
    niches: List[str] = Field(default_factory=list)
    tiers: List[str] = Field(default_factory=list)
    limit: int = Field(default=25, ge=1, le=200)
    dry_run: bool = Field(default=False)


class ChatbotRequest(BaseModel):
    business_name: str = Field(min_length=2, max_length=200)
    contact_email: str = Field(min_length=5, max_length=200)
    website_url: str = Field(min_length=10, max_length=500)
    niche: str = Field(default="business", max_length=50)
    tier: str = Field(default="starter")
    send_email: bool = Field(default=True)


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


@app.post("/social/distribute")
async def social_distribute(payload: SocialDistributeRequest) -> Dict[str, Any]:
    """
    Distribute a post across all configured social platforms via the Python engine.
    Platforms: X/Twitter, LinkedIn, Facebook, Instagram, TikTok, YouTube, Telegram.
    Called by the Node.js pipeline after each article publish.
    """
    from .eaos.social_engine import ProductionSocialEngine, SocialPost
    engine = ProductionSocialEngine()

    requested = set(payload.platforms) if payload.platforms else {
        "twitter", "linkedin", "facebook", "instagram", "tiktok", "youtube", "telegram"
    }

    post = SocialPost(
        db_id        = None,
        platform     = "multi",
        text_content = payload.text,
        media_path   = payload.media_path or None,
        extra        = {
            "title":       payload.title,
            "url":         payload.url,
            "full_text":   payload.full_text,
            "description": payload.full_text[:500],
            "tags":        ["AI", "automation", "AlreadyHereLLC", "passiveincome"],
        },
    )

    results: Dict[str, Any] = {}
    posted = 0

    platform_map = {
        "twitter":   "_post_twitter",
        "linkedin":  "_post_linkedin",
        "facebook":  "_post_facebook",
        "instagram": "_post_instagram",
        "tiktok":    "_post_tiktok",
        "youtube":   "_post_youtube",
        "telegram":  "_post_telegram",
    }

    for platform, method_name in platform_map.items():
        if platform not in requested:
            continue
        try:
            method = getattr(engine, method_name, None)
            if method:
                # Run blocking social calls in thread pool
                import asyncio, functools
                result = await asyncio.get_event_loop().run_in_executor(
                    None, functools.partial(
                        lambda m, p: asyncio.get_event_loop().run_until_complete(m(p))
                        if asyncio.iscoroutinefunction(m) else m(p),
                        method, post
                    )
                )
                if result:
                    posted += 1
                results[platform] = "ok" if result else "skipped"
            else:
                results[platform] = "not_implemented"
        except Exception as exc:
            results[platform] = f"error: {str(exc)[:80]}"

    return {"ok": True, "posted": posted, "platforms": results}


@app.post("/newsletter/publish")
def newsletter_publish(payload: NewsletterRequest) -> Dict[str, Any]:
    """Publish a digest to Beehiiv (income stream 8 — newsletter)."""
    from .beehiiv_client import publish_digest_from_sections
    result = publish_digest_from_sections(
        headline = payload.headline,
        sections = payload.sections,
        tags     = payload.tags or ["ai", "automation", "income"],
        cta_url  = payload.cta_url,
    )
    return {
        "ok":      result.ok,
        "post_id": result.post_id,
        "web_url": result.web_url,
        "status":  result.status,
        "error":   result.error,
    }


@app.get("/newsletter/stats")
def newsletter_stats() -> Dict[str, Any]:
    """Beehiiv publication stats: subscriber count, free/paid breakdown, MRR estimate."""
    from .beehiiv_client import get_stats, get_subscribers
    stats = get_stats()
    subs  = get_subscribers()
    return {**stats, "subscribers": subs}


@app.post("/products/bootstrap")
def products_bootstrap() -> Dict[str, Any]:
    """Ensure all 5 Gumroad digital products exist (idempotent — income stream 3)."""
    from .gumroad_client import bootstrap_catalog
    results = bootstrap_catalog()
    return {"ok": True, "products": results}


@app.get("/products/revenue")
def products_revenue() -> Dict[str, Any]:
    """Gumroad revenue summary: month sales, MRR, product list."""
    from .gumroad_client import revenue_summary
    return revenue_summary()


@app.post("/city-seo/generate")
def city_seo_generate(payload: CitySEORequest) -> Dict[str, Any]:
    """
    Generate and commit city × niche SEO pages (income stream 10).
    Set dry_run=true to preview without committing.
    """
    from .city_seo_engine import generate_batch
    return generate_batch(
        niches  = payload.niches or None,
        tiers   = payload.tiers  or None,
        limit   = payload.limit,
        dry_run = payload.dry_run,
    )


@app.post("/chatbot/build")
def chatbot_build(payload: ChatbotRequest) -> Dict[str, Any]:
    """
    Build a white-label AI chatbot for a local business (income stream 1).
    Scrapes website, creates Chatbase bot, generates Stripe payment links,
    sends onboarding email.
    """
    from .chatbot_builder import build_chatbot
    result = build_chatbot(
        business_name = payload.business_name,
        contact_email = payload.contact_email,
        website_url   = payload.website_url,
        niche         = payload.niche,
        tier          = payload.tier,
        send_email    = payload.send_email,
    )
    return {
        "ok":              result.ok,
        "chatbot_id":      result.chatbot_id,
        "embed_code":      result.embed_code,
        "setup_url":       result.setup_url,
        "subscription_url": result.subscription_url,
        "error":           result.error,
    }


@app.get("/chatbot/revenue")
def chatbot_revenue() -> Dict[str, Any]:
    """Active chatbot retainer subscriptions and MRR from Stripe."""
    from .chatbot_builder import revenue_pipeline_summary
    return revenue_pipeline_summary()


@app.get("/income/summary")
def income_summary() -> Dict[str, Any]:
    """
    Aggregate revenue snapshot across all 10 income streams.
    Returns MRR estimates and pipeline status for each stream.
    """
    summary: Dict[str, Any] = {"ok": True, "streams": {}}

    # Stream 1: Chatbot retainers
    try:
        from .chatbot_builder import revenue_pipeline_summary
        summary["streams"]["chatbot_retainers"] = revenue_pipeline_summary()
    except Exception as exc:
        summary["streams"]["chatbot_retainers"] = {"ok": False, "error": str(exc)}

    # Stream 3: Digital products
    try:
        from .gumroad_client import revenue_summary
        summary["streams"]["digital_products"] = revenue_summary()
    except Exception as exc:
        summary["streams"]["digital_products"] = {"ok": False, "error": str(exc)}

    # Stream 8: Newsletter
    try:
        from .beehiiv_client import get_subscribers
        summary["streams"]["newsletter"] = get_subscribers()
    except Exception as exc:
        summary["streams"]["newsletter"] = {"ok": False, "error": str(exc)}

    # Stream 4: POD
    try:
        from .eaos.cluster_master import get_master
        master = get_master()
        stats  = master.queue.stats()
        summary["streams"]["pod"] = {"ok": True, "queue": stats}
    except Exception as exc:
        summary["streams"]["pod"] = {"ok": False, "error": str(exc)}

    # Stream 6: Video pipeline
    try:
        from .eaos.video_engine import get_engine
        summary["streams"]["video"] = get_engine().status()
    except Exception as exc:
        summary["streams"]["video"] = {"ok": False, "error": str(exc)}

    return summary


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


def _check_webhook_token(request: Request) -> None:
    """Shared-secret auth — mirrors the Bearer/x-profitengine-token pattern
    used by app/api/ai-gateway and app/api/skill-gateway on the Vercel side,
    so a single rotated PROFITENGINE_WEBHOOK_TOKEN secures both surfaces."""
    import os
    configured = os.environ.get("PROFITENGINE_WEBHOOK_TOKEN", "")
    if not configured:
        raise HTTPException(status_code=503, detail="PROFITENGINE_WEBHOOK_TOKEN not configured")
    auth = request.headers.get("authorization", "")
    bearer = auth[7:].strip() if auth.lower().startswith("bearer ") else ""
    header_token = request.headers.get("x-profitengine-token", "")
    if bearer != configured and header_token != configured:
        raise HTTPException(status_code=401, detail="invalid or missing token")


@app.post("/digest/run")
def run_digest(request: Request) -> Dict[str, Any]:
    """HTTP-reachable trigger for the daily digest, used by the
    'Daily Digest' GitHub Actions workflow over HTTPS (via Caddy) instead of
    SSH — port 22 to the OCI host is firewalled but HTTPS is reachable."""
    _check_webhook_token(request)
    from .agent_impls import daily_digest
    try:
        daily_digest.main()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"digest failed: {exc}") from exc
    return {"ok": True, "service": "profitengine-runtime", "ran": "daily_digest"}
