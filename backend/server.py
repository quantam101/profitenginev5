"""
ProfitEngine v5 backend — FastAPI service.

Mirrors the already-here-llc command-OS surface: 11 agents (Sovereign + 10
specialists), revenue ledger, approvals, audit, builds, deployments, books,
proof-of-work, proposals, secrets, advisor, distillation, cost, and the
Cash AI governance layer (live cycle trigger + decision audit trail + WS).
Product data is fixture-backed; waitlist, merge events, agent runs,
approval decisions, cycle events and distillation runs persist to Mongo.
"""
from __future__ import annotations

import ast
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


MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]
mongo_client = AsyncIOMotorClient(MONGO_URL)
db = mongo_client[DB_NAME]
distiller = Distiller(db)


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
_AGENTS = fx.AGENTS
_APPROVALS = fx.APPROVALS
_CONTENT = fx.CONTENT
_REVENUE_STREAMS = fx.REVENUE_STREAMS
_DEPLOYMENTS = fx.DEPLOYMENTS
_BUILDS = fx.BUILDS
_AUDIT = fx.AUDIT
_PROPOSALS = fx.PROPOSALS
_BOOKS = fx.BOOKS
_SECRETS = fx.SECRETS
_SOVEREIGN_DECISIONS = fx.SOVEREIGN_DECISIONS
_SCOUT_OPPS = fx.SCOUT_OPPS
_COST = fx.COST
_revenue_series = fx.revenue_series


# ── App ────────────────────────────────────────────────────────
app = FastAPI(title="ProfitEngine v5 API", version="0.5.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

# Stripe checkout + launch marketing endpoints
app.include_router(build_launch_router(db))
# Enterprise blueprint endpoints (autonomy, lifelong, manifest)
app.include_router(build_enterprise_router(db))


@app.get("/api/health")
async def health() -> dict[str, Any]:
    return {"status": "ok", "service": "profitengine-v5",
            "time": datetime.now(timezone.utc).isoformat()}


@app.get("/api/stats", response_model=StatsResponse)
async def stats_endpoint() -> StatsResponse:
    devs = await db.waitlist.count_documents({})
    return StatsResponse(
        revenue_30d=sum(p["amount"] for p in _revenue_series(30)),
        posts_published=sum(1 for c in _CONTENT if c["status"] == "published") + 1247,
        agents_online=sum(1 for a in _AGENTS if a["status"] in ("online", "active")),
        devs_joined=devs + 312,
        sovereign_decisions_today=len(_SOVEREIGN_DECISIONS),
        proof_of_work_score=0.94,
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
    return _AGENTS


@app.get("/api/agents/fleet-stats")
async def fleet_stats() -> dict:
    total = len(_AGENTS)
    active = sum(1 for a in _AGENTS if a["status"] == "active")
    runs = sum(a["run_count"] for a in _AGENTS)
    successes = sum(a["success_count"] for a in _AGENTS)
    fleet_success = round((successes / runs) * 100) if runs else 0
    return {"total": total, "active": active, "total_runs": runs,
            "fleet_success_rate": fleet_success}


@app.post("/api/agents/{agent_id}/execute")
async def execute_agent(agent_id: str) -> dict:
    agent = next((a for a in _AGENTS if a["id"] == agent_id), None)
    if not agent:
        raise HTTPException(status_code=404, detail="agent not found")
    run = {
        "id": str(uuid.uuid4()),
        "agent_id": agent_id,
        "agent_name": agent["name"],
        "status": "queued",
        "queued_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.agent_runs.insert_one(run)
    await ws_hub.broadcast("agent.run.queued", {
        "agent_id": agent_id, "agent_name": agent["name"], "run_id": run["id"],
    })
    return {"agent_id": agent_id, "run_id": run["id"], "status": "queued",
            "queued_at": run["queued_at"],
            "message": f"{agent['name']} run queued."}


# ── Approvals ─────────────────────────────────────────────────
@app.get("/api/approvals")
async def list_approvals() -> list[dict]:
    return _APPROVALS


@app.post("/api/approvals/{aid}/decide")
async def decide_approval(aid: str, body: dict) -> dict:
    decision = body.get("decision")
    if decision not in ("approve", "veto"):
        raise HTTPException(status_code=400, detail="decision must be approve|veto")
    if not any(a["id"] == aid for a in _APPROVALS):
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
    return _revenue_series(days)


@app.get("/api/revenue/streams")
async def revenue_streams() -> list[dict]:
    return _REVENUE_STREAMS


@app.get("/api/revenue/stats")
async def revenue_stats() -> dict:
    series = _revenue_series(30)
    total = sum(p["amount"] for p in series)
    return {"total_30d": round(total, 2), "mrr_estimate": round(total, 2),
            "active_streams": sum(1 for s in _REVENUE_STREAMS if s["active"]),
            "best_stream": max(_REVENUE_STREAMS, key=lambda s: s["mrr"])["name"]}


@app.get("/api/ledger/progress")
async def ledger_progress() -> dict:
    series = _revenue_series(30)
    earned = round(sum(p["amount"] for p in series), 2)
    return {"goal_usd": 25000, "earned_usd": earned,
            "pct": min(1.0, earned / 25000), "milestone": "commercialization unlock"}


# ── Cycle + Sovereign ─────────────────────────────────────────
@app.get("/api/cycle/status")
async def cycle_status() -> dict[str, Any]:
    return {"state": "running", "current_step": "Content → Video pipeline",
            "step_index": 3, "step_total": 7,
            "started_at": (datetime.now(timezone.utc) - timedelta(minutes=8)).isoformat(),
            "approval_required": True, "cycle_id": "cycle_4017"}


@app.get("/api/sovereign/status")
async def sovereign_status() -> dict:
    return {"id": "sovereign-orchestrator", "model": "gemini/gemini-2.0-flash",
            "next_cycle_in_min": 47, "decisions_today": len(_SOVEREIGN_DECISIONS),
            "current_objective": "Reach $25k milestone — currently 22.4% complete.",
            "safety": {"daily_tokens_used": 18420, "daily_token_cap": 80000,
                       "daily_usd": 0.06, "daily_usd_cap": 0.10, "circuit_breaker": "armed"}}


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
    today = round(sum(c["today_usd"] for c in _COST), 4)
    month = round(sum(c["month_usd"] for c in _COST), 4)
    return {"categories": _COST, "today_usd": today, "month_usd": month,
            "daily_cap_usd": 0.10, "monthly_cap_usd": 5.0}


# ── Proof of Work / Distillation / Analytics / Advisor ─────────
@app.get("/api/proof-of-work")
async def proof_of_work() -> dict:
    return {"score": 0.94, "uptime_pct": 99.87, "passed_cycles_24h": 23, "failed_cycles_24h": 1,
            "signed_assets_24h": 62, "guard_blocks_24h": 3,
            "last_attestation": (datetime.now(timezone.utc) - timedelta(minutes=12)).isoformat()}


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
    return {"daily_active_agents": 7, "weekly_active_agents": 7,
            "cycle_completion_rate": 0.96, "approval_latency_median_s": 38,
            "channel_split": {"Blog": 0.42, "Newsletter": 0.18, "X / Twitter": 0.21,
                              "YouTube short": 0.11, "Other": 0.08}}


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
    """Pick the highest-confidence still-open approval (user choice b)."""
    open_apprs = [a for a in _APPROVALS if a.get("state", "open") == "open"]
    if not open_apprs:
        return None
    return max(open_apprs, key=lambda a: a.get("confidence", 0.0))


@app.get("/api/cash/last-decision")
async def cash_last_decision() -> dict:
    """Surface the highest-confidence open approval as the Last Cash Decision.

    Falls back to the most recent sovereign decision if no approval is open.
    """
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
    """Decision audit trail: sovereign decisions + persisted approval decisions."""
    if limit < 1 or limit > 200:
        raise HTTPException(status_code=400, detail="limit must be 1..200")
    persisted = await db.approval_decisions.find().sort("at", -1).to_list(length=limit)
    appr_map = {a["id"]: a for a in _APPROVALS}
    trail: list[dict] = []
    for d in persisted:
        appr = appr_map.get(d["approval_id"]) or {}
        trail.append({
            "id": d["id"],
            "kind": "approval_decision",
            "summary": appr.get("summary", d["approval_id"]),
            "verdict": d["decision"],
            "risk": appr.get("risk", "low"),
            "tags": [appr.get("agent", "operator")],
            "at": d["at"],
        })
    for d in _SOVEREIGN_DECISIONS:
        trail.append({**d, "kind": "sovereign_decision"})
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
