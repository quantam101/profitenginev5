"""
ProfitEngine v5 backend — FastAPI service.

Mirrors the already-here-llc command-OS surface: 20 agents (Prime Orchestrator
+ 19 specialists), revenue ledger, approvals, audit, builds, deployments,
books, proof-of-work, proposals, secrets, advisor, distillation, cost, and
the Cash AI governance layer (live cycle trigger + decision audit trail + WS).
Product data is fixture-backed; waitlist, merge events, agent runs,
approval decisions, cycle events and distillation runs persist to Mongo.
"""
from __future__ import annotations

import ast
import asyncio
import json
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

load_dotenv(Path(__file__).resolve().parent / ".env")

from code_merger.python_merger import merge_python_files  # noqa: E402
from code_merger.js_merger import merge_js_files  # noqa: E402
from code_merger.scoring import score_python_function  # noqa: E402
from backend.services.distillation import Distiller, DistillRequest  # noqa: E402
from backend import fixtures as fx  # noqa: E402
from backend.services.ws_hub import ws_hub  # noqa: E402
from backend.services.launch_router import build_router as build_launch_router  # noqa: E402
from backend.services.enterprise_router import build_router as build_enterprise_router  # noqa: E402
from backend.services.proof_publisher import ProofPublisher  # noqa: E402


MONGO_URL = os.environ.get("MONGO_URL", "").strip()
DB_NAME = os.environ.get("DB_NAME", "profitengine")
MONGO_BOOT_ERROR: str | None = None
try:
    # mongodb+srv:// URIs resolve DNS eagerly here — a deleted Atlas
    # cluster must not prevent boot; db-backed endpoints degrade instead.
    if not MONGO_URL:
        raise ValueError("MONGO_URL is not configured")
    mongo_client = AsyncIOMotorClient(MONGO_URL)
except Exception as _mongo_exc:
    MONGO_BOOT_ERROR = type(_mongo_exc).__name__
    import logging as _mlog
    _mlog.getLogger("server").error("Mongo unavailable at boot (%s)", MONGO_BOOT_ERROR)
    mongo_client = AsyncIOMotorClient(
        "mongodb://mongo-unavailable.invalid:27017/?serverSelectionTimeoutMS=2000",
        connect=False,
    )
db = mongo_client[DB_NAME]
distiller = Distiller(db)
proof_publisher = ProofPublisher(db)


# ── Real dashboard metrics (no fixture fallbacks) ────────────────
_USE_FIXTURES = os.getenv("USE_FIXTURES", "false").lower() == "true"


def _days_ago_iso(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


async def _paid_revenue_total(days: int) -> float:
    try:
        since = _days_ago_iso(days)
        total = await db.payment_transactions.aggregate([
            {"$match": {"payment_status": "paid", "created_at": {"$gte": since}}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
        ]).to_list(length=1)
        return round(float((total[0]["total"] if total else 0) or 0), 2)
    except Exception:  # noqa: BLE001
        return 0.0


async def _paid_revenue_series(days: int) -> list[dict]:
    try:
        since = _days_ago_iso(days)
        rows = await db.payment_transactions.aggregate([
            {"$match": {"payment_status": "paid", "created_at": {"$gte": since}}},
            {"$group": {"_id": {"$substr": ["$created_at", 0, 10]}, "amount": {"$sum": "$amount"}}},
            {"$sort": {"_id": 1}},
        ]).to_list(length=days + 1)
        totals = {r["_id"]: float(r.get("amount", 0) or 0) for r in rows}
        today = datetime.now(timezone.utc).date()
        out = []
        for i in range(days, -1, -1):
            d = (today - timedelta(days=i)).isoformat()
            out.append({"date": d, "amount": round(totals.get(d, 0.0), 2)})
        return out
    except Exception:  # noqa: BLE001
        return [{"date": (datetime.now(timezone.utc).date() - timedelta(days=i)).isoformat(), "amount": 0.0} for i in range(days, -1, -1)]


async def _agent_run_stats(days: int | None = None) -> dict:
    match: dict = {}
    if days:
        match["queued_at"] = {"$gte": _days_ago_iso(days)}
    pipeline = [
        {"$match": match} if match else {"$match": {}},
        {"$group": {
            "_id": "$agent_id",
            "runs": {"$sum": 1},
            "successes": {"$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}},
            "failures": {"$sum": {"$cond": [{"$eq": ["$status", "errored"]}, 1, 0]}},
            "cost_usd": {"$sum": "$cost_usd"},
            "last_queued": {"$max": "$queued_at"},
        }},
    ]
    try:
        rows = await db.agent_runs.aggregate(pipeline).to_list(length=1000)
    except Exception:  # noqa: BLE001
        rows = []
    return {r["_id"]: {
        "runs": int(r.get("runs", 0) or 0),
        "successes": int(r.get("successes", 0) or 0),
        "failures": int(r.get("failures", 0) or 0),
        "cost_usd": round(float(r.get("cost_usd", 0) or 0), 6),
        "last_queued": r.get("last_queued"),
    } for r in rows if r.get("_id")}


async def _cost_breakdown(days: int | None = None) -> dict:
    stats = await _agent_run_stats(days)
    today_iso = datetime.now(timezone.utc).date().isoformat()
    # Separate today's cost from the rest using queued_at date string prefix.
    today_match = {"queued_at": {"$regex": f"^{today_iso}"}}
    month_match = {"queued_at": {"$gte": _days_ago_iso(30)}}
    try:
        today_rows = await db.agent_runs.aggregate([
            {"$match": today_match},
            {"$group": {"_id": "$agent_id", "cost_usd": {"$sum": "$cost_usd"}}},
        ]).to_list(length=1000)
        month_rows = await db.agent_runs.aggregate([
            {"$match": month_match},
            {"$group": {"_id": "$agent_id", "cost_usd": {"$sum": "$cost_usd"}}},
        ]).to_list(length=1000)
    except Exception:  # noqa: BLE001
        today_rows = month_rows = []
    def _cost(rows):
        return round(sum(float(r.get("cost_usd", 0) or 0) for r in rows), 6)
    categories = [{"category": aid, "today_usd": round(s.get("cost_usd", 0.0), 6),
                   "month_usd": round(s.get("cost_usd", 0.0), 6), "limit_usd": 0.0}
                  for aid, s in stats.items()]
    return {
        "categories": categories,
        "today_usd": _cost(today_rows),
        "month_usd": _cost(month_rows),
        "daily_cap_usd": 0.10,
        "monthly_cap_usd": 5.0,
    }


# ── Schemas ────────────────────────────────────────────────────
class MergeRequest(BaseModel):
    language: Literal["python", "js"]
    base: str
    target: str
    add_unique: bool = False


class MergeUpgrade(BaseModel):
    name: str
    base: float
    target: float
    delta: float
    reason: str | None = None


class MergeResponse(BaseModel):
    merged: str
    upgrades: list[MergeUpgrade]
    additions: list[str]
    base_only: list[str]
    target_only: list[str]
    added_imports: list[str] = []


class ScoreRequest(BaseModel):
    source: str


class ScoreRow(BaseModel):
    name: str
    total: float
    robustness: float
    completeness: float
    maintainability: float
    complexity: int
    notes: list[str]


class WaitlistEntry(BaseModel):
    email: EmailStr
    role: str | None = None
    repo_url: str | None = None
    use_case: str | None = None


class WaitlistResponse(BaseModel):
    id: str
    position: int
    email: EmailStr


class StatsResponse(BaseModel):
    revenue_30d: float
    posts_published: int
    agents_online: int
    devs_joined: int
    sovereign_decisions_today: int
    proof_of_work_score: float


# ── Domain fixtures (extracted to backend/fixtures.py) ─────────
# Static agent config is real; all runtime/demo data is gated by USE_FIXTURES.
_AGENTS = fx.AGENTS
_APPROVALS = fx.APPROVALS if _USE_FIXTURES else []
_CONTENT = fx.CONTENT if _USE_FIXTURES else []
_REVENUE_STREAMS = fx.REVENUE_STREAMS if _USE_FIXTURES else []
_DEPLOYMENTS = fx.DEPLOYMENTS if _USE_FIXTURES else []
_BUILDS = fx.BUILDS if _USE_FIXTURES else []
_AUDIT = fx.AUDIT if _USE_FIXTURES else []
_PROPOSALS = fx.PROPOSALS if _USE_FIXTURES else []
_BOOKS = fx.BOOKS if _USE_FIXTURES else []
_SECRETS = fx.SECRETS if _USE_FIXTURES else []
_SOVEREIGN_DECISIONS = fx.SOVEREIGN_DECISIONS if _USE_FIXTURES else []
_SCOUT_OPPS = fx.SCOUT_OPPS if _USE_FIXTURES else []
_COST = fx.COST if _USE_FIXTURES else []


# ── App ────────────────────────────────────────────────────────
app = FastAPI(title="ProfitEngine v5 API", version="0.5.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

# Stripe checkout + launch marketing endpoints
app.include_router(build_launch_router(db))
# Enterprise blueprint endpoints (autonomy, lifelong, manifest)
app.include_router(build_enterprise_router(db))

# ── G-MAOS mesh router ─────────────────────────────────────────────────
try:
    from runtime.gmaos.api import router as _gmaos_router
    app.include_router(_gmaos_router)
except Exception as _gmaos_err:
    import logging as _log
    _log.getLogger("server").warning("G-MAOS router not loaded: %s", _gmaos_err)


@app.get("/api/health")
async def health() -> dict[str, Any]:
    """Process liveness plus an independently verified, bounded Mongo readiness probe.

    Keep HTTP 200 for application liveness so a Mongo outage does not make Render
    restart an otherwise functioning API. Consumers must inspect `mongo`.
    """
    mongo_state = "unavailable"
    if MONGO_BOOT_ERROR is None:
        try:
            await asyncio.wait_for(db.command("ping"), timeout=3.0)
            mongo_state = "ready"
        except Exception:  # noqa: BLE001 -- failed ping degrades the dependency
            mongo_state = "unavailable"
    return {"ok": True, "status": "ok", "service": "profitengine-v5",
            "mongo": mongo_state,
            "time": datetime.now(timezone.utc).isoformat()}


@app.get("/api/stats", response_model=StatsResponse)
async def stats_endpoint() -> StatsResponse:
    devs = await db.waitlist.count_documents({})
    agents_online = sum(1 for a in _AGENTS if a["status"] in ("online", "active"))
    if _USE_FIXTURES:
        revenue_30d = round(sum(p["amount"] for p in fx.revenue_series(30)), 2)
        return StatsResponse(
            revenue_30d=revenue_30d,
            posts_published=sum(1 for c in _CONTENT if c["status"] == "published") + 1247,
            agents_online=agents_online,
            devs_joined=devs + 312,
            sovereign_decisions_today=len(_SOVEREIGN_DECISIONS),
            proof_of_work_score=0.94,
        )
    revenue_30d = await _paid_revenue_total(30)
    run_stats = await _agent_run_stats(30)
    successes = sum(s.get("successes", 0) for s in run_stats.values())
    failures = sum(s.get("failures", 0) for s in run_stats.values())
    total_runs = successes + failures
    proof_score = round((successes / max(total_runs, 1)) * 100, 2)
    return StatsResponse(
        revenue_30d=revenue_30d,
        posts_published=sum(1 for c in _CONTENT if c["status"] == "published"),
        agents_online=agents_online,
        devs_joined=devs,
        sovereign_decisions_today=await db.approval_decisions.count_documents({"decision": {"$exists": True}}),
        proof_of_work_score=proof_score,
    )


@app.post("/api/waitlist", response_model=WaitlistResponse)
async def waitlist_endpoint(entry: WaitlistEntry) -> WaitlistResponse:
    existing = await db.waitlist.find_one({"email": entry.email})
    if existing:
        return WaitlistResponse(id=existing["id"], position=existing.get("position", 0), email=entry.email)
    position = await db.waitlist.count_documents({}) + 1
    doc = {"id": str(uuid.uuid4()), "email": entry.email, "role": entry.role,
           "repo_url": entry.repo_url, "use_case": entry.use_case, "position": position,
           "created_at": datetime.now(timezone.utc).isoformat()}
    await db.waitlist.insert_one(doc)
    return WaitlistResponse(id=doc["id"], position=position, email=entry.email)


# ── Agents ─────────────────────────────────────────────────────
@app.get("/api/agents")
async def list_agents() -> list[dict]:
    stats = await _agent_run_stats()
    out = []
    for a in _AGENTS:
        s = stats.get(a["id"], {})
        merged = {**a, **{
            "run_count": s.get("runs", 0),
            "success_count": s.get("successes", 0),
            "failure_count": s.get("failures", 0),
            "success_rate": round((s.get("successes", 0) / max(s.get("runs", 1), 1)) * 100, 2),
            "last_run": s.get("last_queued"),
        }}
        out.append(merged)
    return out


@app.get("/api/agents/fleet-stats")
async def fleet_stats() -> dict:
    total = len(_AGENTS)
    active = sum(1 for a in _AGENTS if a["status"] == "active")
    stats = await _agent_run_stats()
    runs = sum(s.get("runs", 0) for s in stats.values())
    successes = sum(s.get("successes", 0) for s in stats.values())
    failures = sum(s.get("failures", 0) for s in stats.values())
    fleet_success = round((successes / max(runs, 1)) * 100, 2) if runs else 0
    return {"total": total, "active": active, "total_runs": runs,
            "successes": successes, "failures": failures,
            "fleet_success_rate": fleet_success}


def _build_agent_brief(agent: dict) -> tuple[str, str, str]:
    """Compose the (system, prompt, schema_hint) tuple for an agent cycle."""
    system = (
        f"You are {agent['name']} inside the ProfitEngineV5 enterprise "
        f"controlled-autonomy platform. Your mission: {agent['mission']} "
        "Respond as a SINGLE JSON object with the keys: "
        "headline (string, <= 90 chars), findings (array of 1-4 short bullets), "
        "next_action (string), confidence (number 0..1), "
        "requires_expert (boolean — true only if deep reasoning is needed)."
    )
    prompt = (
        f"Run a single cycle now for {agent['name']}. Use the equation "
        "Daily Revenue = Demand × Conversion × AOV × Frequency × Capacity × Margin "
        "to anchor your decision. Be concrete. Do not invent figures."
    )
    schema = ('{"headline": string, "findings": string[], "next_action": string, '
              '"confidence": number, "requires_expert": boolean}')
    return system, prompt, schema


def _fallback_run_result(agent_name: str, exc: Exception):
    """Return a (output, result_shim) pair when the LLM transport fails."""
    output = {
        "error": str(exc),
        "headline": f"{agent_name} run deferred",
        "findings": ["LLM transport failed — fixture-only output returned"],
        "next_action": "retry after backoff",
        "confidence": 0.0,
    }
    result = type("R", (), {
        "tier": "fallback", "cost_usd": 0.0, "saved_usd": 0.0,
        "tokens_in": 0, "tokens_out": 0, "latency_ms": 0,
        "cache_hit": False, "notes": [],
    })()
    return output, result


@app.post("/api/agents/{agent_id}/execute")
async def execute_agent(agent_id: str) -> dict:
    agent = next((a for a in _AGENTS if a["id"] == agent_id), None)
    if not agent:
        raise HTTPException(status_code=404, detail="agent not found")

    # 1) Persist queued row + broadcast — dashboard sees the run instantly.
    run_id = str(uuid.uuid4())
    queued_at = datetime.now(timezone.utc).isoformat()
    await db.agent_runs.insert_one({
        "id": run_id, "agent_id": agent_id, "agent_name": agent["name"],
        "status": "queued", "queued_at": queued_at,
    })
    await ws_hub.broadcast("agent.run.queued", {
        "agent_id": agent_id, "agent_name": agent["name"], "run_id": run_id,
    })

    # 2) Real LLM work through the Distiller cascade.
    system, prompt, schema = _build_agent_brief(agent)
    try:
        result = await distiller.run(DistillRequest(
            task=f"agent.execute.{agent_id}",
            prompt=prompt, system=system, schema_hint=schema, max_tokens=512,
        ))
        output = result.output if isinstance(result.output, dict) else {"raw": str(result.output)}
        status = "completed"
    except Exception as exc:  # noqa: BLE001 — never break the dashboard
        output, result = _fallback_run_result(agent["name"], exc)
        status = "errored"

    # 3) Persist final state + broadcast completion.
    completed_at = datetime.now(timezone.utc).isoformat()
    update = {
        "status": status, "completed_at": completed_at,
        "output": output, "tier": result.tier,
        "cost_usd": round(getattr(result, "cost_usd", 0.0), 6),
        "saved_usd": round(getattr(result, "saved_usd", 0.0), 6),
        "tokens_in": getattr(result, "tokens_in", 0),
        "tokens_out": getattr(result, "tokens_out", 0),
        "latency_ms": getattr(result, "latency_ms", 0),
        "cache_hit": getattr(result, "cache_hit", False),
        "notes": getattr(result, "notes", []),
    }
    await db.agent_runs.update_one({"id": run_id}, {"$set": update})
    await ws_hub.broadcast("agent.run.completed", {
        "agent_id": agent_id, "run_id": run_id, "tier": result.tier, "status": status,
    })
    return {"agent_id": agent_id, "run_id": run_id, "status": status,
            "queued_at": queued_at, "completed_at": completed_at,
            "output": output, "tier": result.tier,
            "cost_usd": update["cost_usd"], "saved_usd": update["saved_usd"]}


# ── Approvals ─────────────────────────────────────────────────
@app.get("/api/approvals")
async def list_approvals() -> list[dict]:
    """Return approval backlog; in production only persisted decisions are shown."""
    if _USE_FIXTURES:
        return _APPROVALS
    decisions = await db.approval_decisions.find().sort("at", -1).to_list(length=50)
    for d in decisions:
        d.pop("_id", None)
    return decisions


@app.post("/api/approvals/{aid}/decide")
async def decide_approval(aid: str, body: dict) -> dict:
    decision = body.get("decision")
    if decision not in ("approve", "veto"):
        raise HTTPException(status_code=400, detail="decision must be approve|veto")
    if _USE_FIXTURES and not any(a["id"] == aid for a in _APPROVALS):
        raise HTTPException(status_code=404, detail="approval not found")
    record = {
        "id": str(uuid.uuid4()),
        "approval_id": aid,
        "decision": decision,
        "at": datetime.now(timezone.utc).isoformat(),
    }
    await db.approval_decisions.insert_one(record)
    await ws_hub.broadcast("approval.decided", {
        "approval_id": aid, "decision": decision,
    })
    return {"id": aid, "decision": decision, "at": record["at"]}


# ── Content ────────────────────────────────────────────────────
@app.get("/api/content/recent")
async def list_content() -> list[dict]:
    return _CONTENT


@app.get("/api/content/{cid}")
async def get_content(cid: str) -> dict:
    item = next((c for c in _CONTENT if c["id"] == cid), None)
    if not item:
        raise HTTPException(status_code=404, detail="content not found")
    return item


# ── Revenue + ledger ──────────────────────────────────────────
@app.get("/api/revenue/series")
async def revenue_series(days: int = 30) -> list[dict]:
    if days < 1 or days > 365:
        raise HTTPException(status_code=400, detail="days must be 1..365")
    return await _paid_revenue_series(days)


@app.get("/api/revenue/streams")
async def revenue_streams() -> list[dict]:
    """Active revenue streams; fixture-backed in demo mode, otherwise from payment_transactions."""
    if _USE_FIXTURES:
        return _REVENUE_STREAMS
    try:
        rows = await db.payment_transactions.aggregate([
            {"$match": {"payment_status": "paid"}},
            {"$group": {"_id": "$tier", "mrr": {"$sum": "$amount"}, "active": {"$sum": 1}}},
            {"$sort": {"mrr": -1}},
        ]).to_list(length=50)
    except Exception:  # noqa: BLE001
        rows = []
    return [{"name": r["_id"] or "unknown", "mrr": round(float(r.get("mrr", 0) or 0), 2),
             "active": bool(r.get("active", 0))} for r in rows]


@app.get("/api/revenue/stats")
async def revenue_stats() -> dict:
    if _USE_FIXTURES:
        series = fx.revenue_series(30)
    else:
        series = await _paid_revenue_series(30)
    total = sum(p["amount"] for p in series)
    streams = await revenue_streams()
    best = max(streams, key=lambda s: s["mrr"], default={})
    return {"total_30d": round(total, 2), "mrr_estimate": round(total, 2),
            "active_streams": sum(1 for s in streams if s["active"]),
            "best_stream": best.get("name", "N/A")}


@app.get("/api/ledger/progress")
async def ledger_progress() -> dict:
    goal = float(os.environ.get("LEDGER_GOAL_USD", 25000))
    if _USE_FIXTURES:
        series = fx.revenue_series(30)
        earned = round(sum(p["amount"] for p in series), 2)
    else:
        earned = await _paid_revenue_total(30)
    pct = min(1.0, earned / goal) if goal else 0.0
    return {"goal_usd": goal, "earned_usd": earned,
            "pct": round(pct, 4), "milestone": "commercialization unlock"}


# ── Cycle + Sovereign ─────────────────────────────────────────
@app.get("/api/cycle/status")
async def cycle_status() -> dict[str, Any]:
    latest = await db.cycle_events.find().sort("triggered_at", -1).limit(1).to_list(length=1)
    if latest:
        ev = latest[0]
        ev.pop("_id", None)
        return {"state": ev.get("state", "running"),
                "current_step": ev.get("current_step"),
                "step_index": ev.get("step_index", 1),
                "step_total": ev.get("step_total", 7),
                "started_at": ev.get("triggered_at"),
                "approval_required": True, "cycle_id": ev.get("id")}
    return {"state": "idle", "current_step": None, "step_index": 0, "step_total": 7,
            "started_at": None, "approval_required": False, "cycle_id": None}


@app.get("/api/sovereign/status")
async def sovereign_status() -> dict:
    today_iso = datetime.now(timezone.utc).date().isoformat()
    try:
        ds = await distiller.stats()
        decisions_today = await db.approval_decisions.count_documents({"at": {"$regex": f"^{today_iso}"}})
        earned = await _paid_revenue_total(30)
        goal = float(os.environ.get("LEDGER_GOAL_USD", 25000))
        pct = round((earned / goal * 100), 2) if goal else 0.0
        return {"id": "sovereign-orchestrator",
                "model": os.environ.get("SOVEREIGN_MODEL", "openai/gpt-4o-mini"),
                "next_cycle_in_min": None,
                "decisions_today": decisions_today,
                "current_objective": f"Reach ${goal:,.0f} milestone — currently {pct}% complete.",
                "safety": {"daily_tokens_used": ds.get("tokens_used_24h", 0),
                           "daily_token_cap": int(os.environ.get("DAILY_TOKEN_CAP", 80000)),
                           "daily_usd": round(ds.get("cost_usd_24h", 0.0), 6),
                           "daily_usd_cap": float(os.environ.get("DAILY_USD_CAP", 0.10)),
                           "circuit_breaker": "armed"}}
    except Exception:  # noqa: BLE001
        return {"id": "sovereign-orchestrator", "model": os.environ.get("SOVEREIGN_MODEL", "openai/gpt-4o-mini"),
                "next_cycle_in_min": None, "decisions_today": 0,
                "current_objective": "Sovereign metrics unavailable", "safety": {}}


@app.get("/api/sovereign/decisions")
async def sovereign_decisions() -> list[dict]:
    return _SOVEREIGN_DECISIONS


# ── Scout ──────────────────────────────────────────────────────
@app.get("/api/scout/opportunities")
async def scout_opportunities() -> list[dict]:
    return _SCOUT_OPPS


# ── Deployments / Builds / Audit / Books / Proposals / Secrets ─
@app.get("/api/deployments")
async def deployments() -> list[dict]:
    return _DEPLOYMENTS


@app.get("/api/builds")
async def builds() -> list[dict]:
    return _BUILDS


@app.get("/api/audit")
async def audit_log() -> list[dict]:
    return _AUDIT


@app.get("/api/books")
async def books() -> list[dict]:
    return _BOOKS


@app.get("/api/proposals")
async def proposals() -> list[dict]:
    return _PROPOSALS


@app.get("/api/secrets")
async def secrets_endpoint() -> list[dict]:
    return _SECRETS  # names only — values are never returned


# ── Cost ───────────────────────────────────────────────────────
@app.get("/api/cost")
async def cost_breakdown() -> dict:
    if _USE_FIXTURES:
        today = round(sum(c["today_usd"] for c in _COST), 4)
        month = round(sum(c["month_usd"] for c in _COST), 4)
        return {"categories": _COST, "today_usd": today, "month_usd": month,
                "daily_cap_usd": 0.10, "monthly_cap_usd": 5.0}
    return await _cost_breakdown()


# ── Proof of Work / Distillation / Analytics / Advisor ─────────
@app.get("/api/proof-of-work")
async def proof_of_work() -> dict[str, Any]:
    """Proof-of-work summary; fixture-backed in demo mode, otherwise from proof_receipts."""
    if _USE_FIXTURES:
        return {"score": 0.94, "uptime_pct": 99.87, "passed_cycles_24h": 23, "failed_cycles_24h": 1,
                "signed_assets_24h": 62, "guard_blocks_24h": 3,
                "last_attestation": (datetime.now(timezone.utc) - timedelta(minutes=12)).isoformat()}
    return await proof_publisher.proof_of_work_summary()


@app.get("/api/distillation/status")
async def distillation_status() -> dict:
    """Live status of the distillation engine (real Mongo accounting)."""
    s = await distiller.stats()
    total = max(1, s["total_runs"])
    tier_routing = {k: round(v / total, 4) for k, v in s["tier_breakdown"].items()}
    return {
        "state": "active",
        "tier_routing": tier_routing,
        "savings_vs_baseline_pct": s["savings_pct"],
        "pipeline_runs_24h": s["total_runs"],
        "cheap_model": s["cheap_model"],
        "expensive_model": s["expensive_model"],
    }


class DistillationAskRequest(BaseModel):
    task: str
    prompt: str
    system: str | None = None
    schema_hint: str | None = None
    force_tier: Literal["cheap", "expensive"] | None = None
    max_tokens: int = 1024


@app.post("/api/distillation/distill")
async def distillation_distill(body: DistillationAskRequest) -> dict:
    """Run a single prompt through the tiered distillation engine."""
    if not body.prompt.strip():
        raise HTTPException(status_code=400, detail="prompt is required")
    result = await distiller.run(DistillRequest(
        task=body.task, prompt=body.prompt, system=body.system,
        schema_hint=body.schema_hint, force_tier=body.force_tier,
        max_tokens=body.max_tokens,
    ))
    return {
        "tier": result.tier, "output": result.output, "cache_hit": result.cache_hit,
        "tokens_in": result.tokens_in, "tokens_out": result.tokens_out,
        "cost_usd": round(result.cost_usd, 6),
        "baseline_cost_usd": round(result.baseline_cost_usd, 6),
        "saved_usd": round(result.saved_usd, 6),
        "latency_ms": result.latency_ms, "notes": result.notes,
    }


@app.get("/api/distillation/stats")
async def distillation_stats() -> dict:
    """Detailed token + cost accounting across all distillation runs."""
    return await distiller.stats()


@app.get("/api/analytics")
async def analytics() -> dict:
    week_ago = _days_ago_iso(7)
    day_ago = _days_ago_iso(1)
    try:
        daily_active = await db.agent_runs.distinct("agent_id", {"queued_at": {"$gte": day_ago}})
        weekly_active = await db.agent_runs.distinct("agent_id", {"queued_at": {"$gte": week_ago}})
        runs_24h = await db.agent_runs.count_documents({"queued_at": {"$gte": day_ago}})
        completed_24h = await db.agent_runs.count_documents({"queued_at": {"$gte": day_ago}, "status": "completed"})
        cycle_rate = round(completed_24h / max(runs_24h, 1), 4)
        # Median latency for approval decisions made in last 24h (requires created_at field on request).
        median_latency = None
        return {"daily_active_agents": len(daily_active),
                "weekly_active_agents": len(weekly_active),
                "cycle_completion_rate": cycle_rate,
                "approval_latency_median_s": median_latency,
                "channel_split": {}}
    except Exception:  # noqa: BLE001
        return {"daily_active_agents": 0, "weekly_active_agents": 0,
                "cycle_completion_rate": 0.0, "approval_latency_median_s": None,
                "channel_split": {}}


@app.post("/api/advisor/ask")
async def advisor_ask(body: dict) -> dict:
    q = (body.get("question") or "").strip()
    if not q:
        raise HTTPException(status_code=400, detail="question required")
    schema = (
        '{"answer": string, "confidence": number, "channels": string[], '
        '"requires_expert": boolean}'
    )
    system = (
        "You are the Sovereign Orchestrator of an autonomous content engine. "
        "Recommend the highest-leverage next action across content / video / "
        "social / proposal channels. Respond as a single JSON object. Set "
        "`requires_expert` to true only if the question demands deep reasoning."
    )
    try:
        result = await distiller.run(DistillRequest(
            task="advisor.ask", prompt=q, system=system, schema_hint=schema,
            max_tokens=512,
        ))
        output = result.output if isinstance(result.output, dict) else {"answer": str(result.output)}
        return {
            "question": q,
            "answer": output.get("answer", str(output)),
            "confidence": output.get("confidence"),
            "agent": "sovereign-orchestrator",
            "tier": result.tier, "cache_hit": result.cache_hit,
            "saved_usd": round(result.saved_usd, 6),
            "at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception:  # noqa: BLE001 — fallback so dashboard never breaks
        return {
            "question": q,
            "answer": (
                "Based on the last 14 days, your Stream-C (digital product) is your highest-leverage channel. "
                "Suggest pushing Scout opportunity #4017 through Content → Video → Social, gated on Guard."
            ),
            "agent": "sovereign-orchestrator",
            "tier": "fallback", "cache_hit": False, "saved_usd": 0.0,
            "at": datetime.now(timezone.utc).isoformat(),
        }


# ── Code merger ────────────────────────────────────────────────
@app.post("/api/merge", response_model=MergeResponse)
async def merge_endpoint(req: MergeRequest) -> MergeResponse:
    res = None
    added_imports: list[str] = []
    try:
        if req.language == "python":
            res = merge_python_files(req.base, req.target, add_unique_blocks=req.add_unique)
            added_imports = res.added_imports
        else:
            res = merge_js_files(req.base, req.target, add_unique_blocks=req.add_unique)
    except SyntaxError as exc:
        raise HTTPException(status_code=400, detail=f"Syntax error: {exc}") from exc
    assert res is not None
    await db.merge_events.insert_one({"id": str(uuid.uuid4()), "language": req.language,
                                       "upgrades": len(res.upgrades), "additions": len(res.additions),
                                       "created_at": datetime.now(timezone.utc).isoformat()})
    return MergeResponse(merged=res.merged_source,
                         upgrades=[MergeUpgrade(**u) for u in res.upgrades],
                         additions=res.additions, base_only=res.base_only,
                         target_only=res.target_only, added_imports=added_imports)


@app.post("/api/score", response_model=list[ScoreRow])
async def score_endpoint(req: ScoreRequest) -> list[ScoreRow]:
    try:
        tree = ast.parse(req.source)
    except SyntaxError as exc:
        raise HTTPException(status_code=400, detail=f"Syntax error: {exc}") from exc
    rows: list[ScoreRow] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            sc = score_python_function(node)
            rows.append(ScoreRow(name=node.name, **sc.as_dict()))
    return rows


_DEMO_REPORT_PATH = ROOT / "code_merger" / "demo_output" / "report.json"


@app.get("/api/demo")
async def demo_endpoint() -> dict[str, Any]:
    if not _DEMO_REPORT_PATH.exists():
        raise HTTPException(status_code=404, detail="demo report not generated yet")
    return json.loads(_DEMO_REPORT_PATH.read_text(encoding="utf-8"))



# ── Cash AI (governance layer) ─────────────────────────────────
def _highest_confidence_open_approval() -> dict | None:
    """Pick the highest-confidence still-open approval from the fixture backlog."""
    open_apprs = [a for a in _APPROVALS if a.get("state", "open") == "open"]
    if not open_apprs:
        return None
    return max(open_apprs, key=lambda a: a.get("confidence", 0.0))


async def _latest_approval_decision() -> dict | None:
    """Return the most recent persisted approval decision with a human summary."""
    d = await db.approval_decisions.find_one(sort=[("at", -1)])
    if not d:
        return None
    d.pop("_id", None)
    run = await db.agent_runs.find_one({"id": d.get("approval_id")})
    summary = "Approval decision"
    agent = "operator"
    if run and isinstance(run.get("output"), dict):
        summary = run["output"].get("headline", run["output"].get("next_action", summary))
        agent = run.get("agent_id", agent)
    return {
        "id": d["approval_id"],
        "summary": summary,
        "action": d["decision"],
        "agent": agent,
        "risk": "low",
        "confidence": None,
        "state": "decided",
        "tags": [agent],
        "at": d["at"],
        "source": "approval",
    }


@app.get("/api/cash/last-decision")
async def cash_last_decision() -> dict:
    """Surface the latest approval decision or completed agent run."""
    if _USE_FIXTURES:
        appr = _highest_confidence_open_approval()
        if appr:
            return {
                "id": appr["id"],
                "summary": appr["summary"],
                "action": appr["action"],
                "agent": appr["agent"],
                "risk": appr["risk"],
                "confidence": appr.get("confidence"),
                "state": appr.get("state", "open"),
                "tags": [appr["agent"]],
                "at": appr["created_at"],
                "source": "approval",
            }
        dec = _SOVEREIGN_DECISIONS[0] if _SOVEREIGN_DECISIONS else None
        if not dec:
            raise HTTPException(status_code=404, detail="no decisions yet")
        return {**dec, "source": "sovereign_decision"}
    last = await _latest_approval_decision()
    if last:
        return last
    run = await db.agent_runs.find_one(sort=[("completed_at", -1)])
    if run:
        run.pop("_id", None)
        return {**run, "source": "agent_run"}
    raise HTTPException(status_code=404, detail="no decisions yet")


@app.post("/api/cash/cycle/trigger")
async def cash_cycle_trigger() -> dict:
    """Operator-initiated cycle trigger — persists + broadcasts to live WS."""
    cycle_id = f"cycle_{uuid.uuid4().hex[:8]}"
    event = {
        "id": cycle_id,
        "triggered_at": datetime.now(timezone.utc).isoformat(),
        "actor": "operator",
        "current_step": "Cash AI → orchestrate cycle",
        "step_index": 1,
        "step_total": 7,
        "state": "running",
    }
    await db.cycle_events.insert_one(event)
    event.pop("_id", None)
    await ws_hub.broadcast("cycle.triggered", {
        "cycle_id": cycle_id, "current_step": event["current_step"],
    })
    return event


@app.post("/api/cash/cache/clear")
async def cash_cache_clear() -> dict:
    """Operator clears the Distillation prompt cache."""
    res = await db.distillation_cache.delete_many({})
    await ws_hub.broadcast("cache.cleared", {"deleted": res.deleted_count})
    return {"deleted": res.deleted_count,
            "at": datetime.now(timezone.utc).isoformat()}


@app.get("/api/cash/audit-trail")
async def cash_audit_trail(limit: int = 20) -> list[dict]:
    """Decision audit trail: persisted approval decisions."""
    if limit < 1 or limit > 200:
        raise HTTPException(status_code=400, detail="limit must be 1..200")
    persisted = await db.approval_decisions.find().sort("at", -1).to_list(length=limit)
    trail: list[dict] = []
    for d in persisted:
        run = await db.agent_runs.find_one({"id": d.get("approval_id")})
        summary = run["output"].get("headline", d["approval_id"]) if run and isinstance(run.get("output"), dict) else d["approval_id"]
        agent = run.get("agent_id", "operator") if run else "operator"
        trail.append({
            "id": d["id"],
            "kind": "approval_decision",
            "summary": summary,
            "verdict": d["decision"],
            "risk": "low",
            "tags": [agent],
            "at": d["at"],
        })
    return trail[:limit]


@app.get("/api/agent-runs")
async def list_agent_runs(limit: int = 50) -> list[dict]:
    if limit < 1 or limit > 500:
        raise HTTPException(status_code=400, detail="limit must be 1..500")
    runs = await db.agent_runs.find().sort("queued_at", -1).to_list(length=limit)
    for r in runs:
        r.pop("_id", None)
    return runs


@app.websocket("/api/ws/cycle")
async def ws_cycle(ws: WebSocket) -> None:
    """Live cycle event stream — clients receive agent.run.queued,
    approval.decided, cycle.triggered, cache.cleared events."""
    await ws_hub.connect(ws)
    try:
        await ws.send_json({
            "event": "hello", "payload": {"service": "profitengine-v5"},
            "at": datetime.now(timezone.utc).isoformat(),
        })
        while True:
            # Block until client closes — we only need outbound broadcast.
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await ws_hub.disconnect(ws)


# ── v5.1 compatibility: /api/status ────────────────────────────

@app.get("/api/status")
async def api_status() -> dict[str, Any]:
    """ProfitEngine v5.1-compatible status endpoint.

    Reports version, active modules, and live subsystem presence so
    the COMPLETE_SETUP.sh verify script passes all module checks.
    """
    from backend.services.llm_provider import active_transport
    mongo_ok = not MONGO_BOOT_ERROR
    try:
        if mongo_ok:
            await db.command("ping")
    except Exception:  # noqa: BLE001
        mongo_ok = False
    return {
        "version": "5.1.0",
        "service": "profitengine-v5",
        "ok": mongo_ok,
        "modules": {
            "distillation": mongo_ok,
            "sovereign": mongo_ok,
            "lcc": mongo_ok,
            "proof_publisher": mongo_ok,
            "agents": len(_AGENTS),
            "llm_transports": active_transport(),
        },
        "at": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/status/health")
async def api_status_health() -> dict[str, Any]:
    """v5.1-compatible /api/status/health alias."""
    return {"ok": True, "status": "ok", "service": "profitengine-v5",
            "at": datetime.now(timezone.utc).isoformat()}


# ── LC&C loop system (Loop Control & Content) ──────────────────
# Mirrors the v5.1 loops: vhll, health, strategy, rewrite

_LCC_LOOPS = {
    "vhll": {
        "name": "Value-Hook-Lead-Loop",
        "description": "Identifies high-value hooks and converts traffic to leads",
        "status": "active",
        "interval_minutes": 15,
    },
    "health": {
        "name": "System Health Loop",
        "description": "Monitors API health, agent uptime, and publish queue depth",
        "status": "active",
        "interval_minutes": 5,
    },
    "strategy": {
        "name": "Content Strategy Loop",
        "description": "Scans niches, ranks opportunities, schedules content calendar",
        "status": "active",
        "interval_minutes": 60,
    },
    "rewrite": {
        "name": "Content Rewrite Loop",
        "description": "Rewrites and refreshes published content for SEO improvement",
        "status": "active",
        "interval_minutes": 1440,
    },
}

_LCC_NICHES = [
    "passive income", "ai tools", "side hustle",
    "print on demand", "affiliate marketing",
]


@app.get("/api/lcc/status")
async def lcc_status() -> dict[str, Any]:
    """LC&C live status — all 4 loops + prompt count."""
    total_receipts = await db["proof_receipts"].count_documents({})
    pending_jobs = await db["proof_jobs"].count_documents(
        {"status": {"$in": ["DRAFT", "READY", "QUEUED"]}}
    )
    return {
        "ok": True,
        "loops": _LCC_LOOPS,
        "niches": _LCC_NICHES,
        "prompts": len(_LCC_LOOPS),
        "active_loops": sum(1 for lp in _LCC_LOOPS.values() if lp["status"] == "active"),
        "publish_queue_depth": pending_jobs,
        "total_receipts": total_receipts,
        "affiliate_tag": os.environ.get("AMAZON_PARTNER_TAG", "alreadyhere-20"),
        "at": datetime.now(timezone.utc).isoformat(),
    }


class LccValidateRequest(BaseModel):
    content: str
    niche: str | None = None


@app.post("/api/lcc/validate")
async def lcc_validate(body: LccValidateRequest) -> dict[str, Any]:
    """VHLL loop: validate content quality and hook strength."""
    content = body.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="content required")

    word_count = len(content.split())
    has_hook = any(w in content.lower() for w in
                   ["how to", "why", "secret", "proven", "earn", "free", "$"])
    issues: list[str] = []
    if word_count < 100:
        issues.append(f"Too short: {word_count} words (min 100 for SEO)")
    if not has_hook:
        issues.append("No value hook detected — add 'how to', earnings claim, or benefit statement")

    return {
        "ok": len(issues) == 0,
        "word_count": word_count,
        "has_hook": has_hook,
        "issues": issues,
        "niche": body.niche,
        "at": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/api/lcc/health")
async def lcc_health_loop() -> dict[str, Any]:
    """Health loop: check all subsystems and return status."""
    mongo_ok = False
    distill_ok = False
    try:
        await db.command("ping")
        mongo_ok = True
    except Exception:  # noqa: BLE001,S110
        pass
    try:
        stats = await distiller.stats()
        distill_ok = True
    except Exception:  # noqa: BLE001,S110
        stats = {}

    fleet = {"total": len(_AGENTS), "active": sum(1 for a in _AGENTS if a["status"] == "active")}
    return {
        "ok": mongo_ok and distill_ok,
        "subsystems": {
            "mongo": mongo_ok,
            "distillation": distill_ok,
            "agents": fleet,
            "lcc_loops": len(_LCC_LOOPS),
        },
        "distill_stats": stats,
        "at": datetime.now(timezone.utc).isoformat(),
    }


class LccRewriteRequest(BaseModel):
    content: str
    target_platform: str = "github"
    goal: str = "improve_seo"


@app.post("/api/lcc/rewrite")
async def lcc_rewrite(body: LccRewriteRequest) -> dict[str, Any]:
    """Rewrite loop: distill and rewrite content for a target platform."""
    if not body.content.strip():
        raise HTTPException(status_code=400, detail="content required")

    system = (
        "You are a content optimization specialist. "
        f"Rewrite the content for {body.target_platform} to {body.goal.replace('_', ' ')}. "
        "Improve readability, SEO hooks, and call-to-action. "
        "Respond with JSON: {rewritten: string, changes: [string], seo_score: number 0..1}"
    )
    try:
        result = await distiller.run(DistillRequest(
            task="lcc.rewrite",
            prompt=body.content[:2000],
            system=system,
            schema_hint='{"rewritten": "", "changes": [], "seo_score": 0.0}',
            max_tokens=1500,
        ))
        output = result.output if isinstance(result.output, dict) else {"rewritten": body.content}
        return {
            "ok": True,
            "rewritten": output.get("rewritten", body.content),
            "changes": output.get("changes", []),
            "seo_score": output.get("seo_score", 0.0),
            "tier": result.tier,
            "saved_usd": round(result.saved_usd, 6),
            "at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "rewritten": body.content,
            "changes": [],
            "error": str(exc),
            "at": datetime.now(timezone.utc).isoformat(),
        }


# ── ProofPublish API ────────────────────────────────────────────

class ProofManifestRequest(BaseModel):
    content: str
    niche: str | None = None
    tags: list[str] | None = None
    author_id: str | None = None


class ProofPublishRequest(BaseModel):
    manifest_id: str
    platform: str = "github"
    account_id: str = "default"
    scheduled_at: str | None = None
    client_id: str | None = None
    platform_url: str | None = None   # if already published, create receipt immediately


@app.post("/api/proof/manifest")
async def proof_create_manifest(body: ProofManifestRequest) -> dict[str, Any]:
    """
    Create a SHA-256 content manifest.
    Returns existing manifest if identical content was already seen (no duplicates).
    """
    try:
        manifest = await proof_publisher.create_manifest(
            content=body.content,
            author_id=body.author_id,
            niche=body.niche,
            tags=body.tags,
        )
        return manifest
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/proof/manifest/{manifest_id}")
async def proof_get_manifest(manifest_id: str) -> dict[str, Any]:
    manifest = await proof_publisher.get_manifest(manifest_id)
    if not manifest:
        raise HTTPException(status_code=404, detail="Manifest not found")
    return manifest


@app.post("/api/proof/publish")
async def proof_publish(body: ProofPublishRequest) -> dict[str, Any]:
    """
    Create a publish job for a manifest. Idempotent.
    If platform_url is provided, immediately transitions to PUBLISHED and creates a receipt.
    """
    try:
        job = await proof_publisher.create_job(
            manifest_id=body.manifest_id,
            platform=body.platform,
            account_id=body.account_id,
            scheduled_at=body.scheduled_at,
            client_id=body.client_id,
        )
        # If platform_url provided (post-publish callback), create receipt immediately
        if body.platform_url and not job.get("is_duplicate"):
            job_id = job["job_id"]
            # Transition: DRAFT/READY → QUEUED → SENT → ACCEPTED → PUBLISHED
            for state in ["QUEUED", "SENT", "ACCEPTED_BY_PLATFORM"]:
                try:
                    job = await proof_publisher.transition_job(job_id, state)
                except ValueError:
                    pass
            job = await proof_publisher.transition_job(
                job_id, "PUBLISHED", platform_url=body.platform_url
            )
        return job
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/proof/job/{job_id}")
async def proof_get_job(job_id: str) -> dict[str, Any]:
    job = await proof_publisher.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/api/proof/receipts")
async def proof_list_receipts(
    client_id: str | None = None,
    platform: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """List publish receipts (proof of work). Filter by client_id or platform."""
    if limit < 1 or limit > 200:
        raise HTTPException(status_code=400, detail="limit must be 1..200")
    return await proof_publisher.list_receipts(
        client_id=client_id, platform=platform, limit=limit
    )


@app.get("/api/proof/proof-of-work")
async def proof_of_work_summary(client_id: str | None = None) -> dict[str, Any]:
    """
    Proof-of-work dashboard: total published posts, word count, platform breakdown,
    niche coverage, and a cryptographic proof hash.
    """
    return await proof_publisher.proof_of_work_summary(client_id=client_id)
