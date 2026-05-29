"""
ProfitEngine v5 backend — FastAPI service.

Mirrors the already-here-llc command-OS surface: 7 agents (Sovereign + 6
specialists), revenue ledger, approvals, audit, builds, deployments, books,
proof-of-work, proposals, secrets, advisor, distillation, cost tracking.
All product data is fixture-backed for the preview; waitlist + merge events
persist to Mongo.
"""
from __future__ import annotations

import ast
import json
import os
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
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


# ── Domain fixtures (matches AHD shapes) ───────────────────────
_AGENTS = [
    {"id": "sovereign-orchestrator", "name": "Sovereign Orchestrator", "type": "orchestrator", "tier": "sovereign",
     "status": "active", "category": "orchestrator",
     "mission": "Coordinate multi-agent workflows and enforce governance policies.",
     "last_run": "decision cached · 47m remaining",
     "run_count": 152, "success_rate": 0.97, "success_count": 147, "failure_count": 5, "recent_fails": 4, "runs_today": 18,
     "cycle_interval_min": 60, "model": "gemini/gemini-2.0-flash"},
    {"id": "cost-guard", "name": "Cost Guard Agent", "type": "security", "tier": "operational",
     "status": "active", "category": "security",
     "mission": "Enforce zero-spend policy and block unauthorized paid actions.",
     "last_run": "11m ago",
     "run_count": 488, "success_rate": 1.0, "success_count": 488, "failure_count": 0, "recent_fails": 0, "runs_today": 22,
     "cycle_interval_min": 5, "model": "openai/gpt-5.2"},
    {"id": "content-generation", "name": "Content Generation Agent", "type": "content", "tier": "operational",
     "status": "active", "category": "content",
     "mission": "Generate revenue-focused content using AI for blogs, social, and proposals.",
     "last_run": "running",
     "run_count": 234, "success_rate": 0.94, "success_count": 220, "failure_count": 14, "recent_fails": 13, "runs_today": 12,
     "cycle_interval_min": 60, "model": "anthropic/claude-sonnet-4-5"},
    {"id": "proposal-engine", "name": "Proposal Engine Agent", "type": "revenue", "tier": "operational",
     "status": "active", "category": "revenue",
     "mission": "Generate federal proposals and capability statements using H&M proof data.",
     "last_run": "3h ago",
     "run_count": 81, "success_rate": 0.94, "success_count": 76, "failure_count": 5, "recent_fails": 5, "runs_today": 2,
     "cycle_interval_min": 720, "model": "anthropic/claude-sonnet-4-5"},
    {"id": "lifelong-catch-correct", "name": "Lifelong Catch and Correct", "type": "learning", "tier": "operational",
     "status": "active", "category": "learning",
     "mission": "Track failures, generate fixes, and prevent repeated mistakes.",
     "last_run": "27m ago",
     "run_count": 124, "success_rate": 0.98, "success_count": 121, "failure_count": 3, "recent_fails": 3, "runs_today": 6,
     "cycle_interval_min": 120, "model": "openai/gpt-5.2"},
    {"id": "seo-scout", "name": "SEO Scout Agent", "type": "content", "tier": "operational",
     "status": "active", "category": "content",
     "mission": "Discover trending niches, run keyword research, and queue topics.",
     "last_run": "2m ago",
     "run_count": 312, "success_rate": 0.98, "success_count": 305, "failure_count": 7, "recent_fails": 7, "runs_today": 18,
     "cycle_interval_min": 60, "model": "gemini/gemini-2.0-flash"},
    {"id": "faceless-video", "name": "Faceless Video Agent", "type": "content", "tier": "operational",
     "status": "active", "category": "content",
     "mission": "Assemble faceless videos from AI script + free stock footage + TTS.",
     "last_run": "11m ago",
     "run_count": 96, "success_rate": 0.95, "success_count": 91, "failure_count": 5, "recent_fails": 5, "runs_today": 4,
     "cycle_interval_min": 360, "model": "anthropic/claude-sonnet-4-5"},
    {"id": "pod-designer", "name": "POD Designer Agent", "type": "revenue", "tier": "operational",
     "status": "active", "category": "revenue",
     "mission": "Generate print-on-demand designs and push to RedBubble / Printify / Etsy.",
     "last_run": "44m ago",
     "run_count": 178, "success_rate": 0.95, "success_count": 169, "failure_count": 9, "recent_fails": 9, "runs_today": 9,
     "cycle_interval_min": 240, "model": "gemini/gemini-2.0-flash"},
    {"id": "affiliate-link", "name": "Affiliate Link Agent", "type": "revenue", "tier": "operational",
     "status": "active", "category": "revenue",
     "mission": "Manage affiliate link injection across content and track conversions.",
     "last_run": "1m ago",
     "run_count": 421, "success_rate": 1.0, "success_count": 419, "failure_count": 2, "recent_fails": 2, "runs_today": 32,
     "cycle_interval_min": 30, "model": "openai/gpt-5.2"},
    {"id": "health-oracle", "name": "Health Oracle Agent", "type": "security", "tier": "operational",
     "status": "active", "category": "security",
     "mission": "Continuous health checks, circuit-breakers, and self-improve hooks.",
     "last_run": "16s ago",
     "run_count": 1043, "success_rate": 1.0, "success_count": 1041, "failure_count": 2, "recent_fails": 2, "runs_today": 144,
     "cycle_interval_min": 1, "model": "openai/gpt-5.2"},
    {"id": "procurement-scout", "name": "Procurement Scout Agent", "type": "revenue", "tier": "operational",
     "status": "active", "category": "revenue",
     "mission": "Scan SAM.gov + Grants.gov for matching opportunities, queue proposals.",
     "last_run": "1h ago",
     "run_count": 62, "success_rate": 0.94, "success_count": 58, "failure_count": 4, "recent_fails": 4, "runs_today": 4,
     "cycle_interval_min": 360, "model": "gemini/gemini-2.0-flash"},
]

_APPROVALS = [
    {"id": "apr_001", "agent": "Content Generation Agent", "action": "Publish blog post",
     "summary": "“5 sleeper niches for affiliate creators in 2026” — 2,180 words, 6 outbound links.", "risk": "low", "created_at": "4m ago"},
    {"id": "apr_002", "agent": "Affiliate Link Agent", "action": "Reallocate budget",
     "summary": "Move $240/day from Stream-B (Amazon) to Stream-C (Digital). Projected lift +18%.", "risk": "medium", "created_at": "12m ago"},
    {"id": "apr_003", "agent": "SEO Scout Agent", "action": "Queue new topic batch",
     "summary": "Queue 12 new keyword clusters from AHREFS pull — est. 38k monthly searches.", "risk": "low", "created_at": "21m ago"},
    {"id": "apr_004", "agent": "Cost Guard Agent", "action": "Block paid action",
     "summary": "Faceless Video Agent attempted $4.00 ElevenLabs call — blocked, fallback to local TTS.", "risk": "high", "created_at": "38m ago"},
    {"id": "apr_005", "agent": "Sovereign Orchestrator", "action": "Trigger 6-hour campaign",
     "summary": "Sovereign proposes a 6-hour multi-channel push on SEO Scout opportunity #4017. Est. spend $0, est. yield $480.", "risk": "medium", "created_at": "1h ago"},
]

_CONTENT = [
    {"id": "c1", "title": "5 sleeper niches for affiliate creators in 2026", "channel": "Blog", "status": "queued", "revenue": 0.0, "created_at": "today", "word_count": 2180},
    {"id": "c2", "title": "How we automated a $14k/mo content stack", "channel": "Newsletter", "status": "published", "revenue": 1280.40, "created_at": "yesterday", "word_count": 1870},
    {"id": "c3", "title": "Why your funnel needs Guard before Revenue", "channel": "X / Twitter", "status": "published", "revenue": 412.10, "created_at": "2d", "word_count": 280},
    {"id": "c4", "title": "Scout vs human researchers — a 30-day test", "channel": "YouTube short", "status": "draft", "revenue": 0.0, "created_at": "3d", "word_count": 95},
    {"id": "c5", "title": "Edge-case: when Guard overrides Revenue", "channel": "Blog", "status": "published", "revenue": 884.50, "created_at": "4d", "word_count": 2410},
    {"id": "c6", "title": "Sovereign Decision Log — Week 17", "channel": "Newsletter", "status": "published", "revenue": 1102.20, "created_at": "5d", "word_count": 1610},
    {"id": "c7", "title": "Three free signals Scout missed last sprint", "channel": "Blog", "status": "draft", "revenue": 0.0, "created_at": "6d", "word_count": 0},
]

_REVENUE_STREAMS = [
    {"id": "rs_1", "name": "Amazon Affiliates", "kind": "affiliate", "active": True, "mrr": 2340.00, "ctr": 0.041, "health": 0.92},
    {"id": "rs_2", "name": "Digital Product — Operator Playbook", "kind": "product", "active": True, "mrr": 6120.00, "ctr": 0.087, "health": 0.98},
    {"id": "rs_3", "name": "Display Ads (Mediavine)", "kind": "ads", "active": True, "mrr": 1890.00, "ctr": 0.014, "health": 0.81},
    {"id": "rs_4", "name": "Sponsored Slots", "kind": "sponsorship", "active": True, "mrr": 3800.00, "ctr": 0.0, "health": 0.95},
    {"id": "rs_5", "name": "Affiliate — Skool Cohort", "kind": "affiliate", "active": False, "mrr": 0.0, "ctr": 0.0, "health": 0.0},
]

_DEPLOYMENTS = [
    {"id": "dep_1", "service": "engine-runtime", "env": "production", "version": "v5.0.7", "status": "active", "url": "engine.profitengine.dev", "deployed_at": "12m ago"},
    {"id": "dep_2", "service": "blog-publisher", "env": "production", "version": "v5.0.6", "status": "active", "url": "blog.profitengine.dev", "deployed_at": "2h ago"},
    {"id": "dep_3", "service": "approvals-worker", "env": "production", "version": "v5.0.7", "status": "rolling", "url": "—", "deployed_at": "now"},
    {"id": "dep_4", "service": "dashboard", "env": "production", "version": "v5.0.7", "status": "active", "url": "app.profitengine.dev", "deployed_at": "12m ago"},
    {"id": "dep_5", "service": "video-rendering", "env": "staging", "version": "v5.1.0-rc.2", "status": "active", "url": "—", "deployed_at": "1d ago"},
]

_BUILDS = [
    {"id": "b_4017", "branch": "main", "commit": "a3f9c12", "title": "feat: sovereign decision cache", "status": "success", "duration_s": 142, "started_at": "12m ago"},
    {"id": "b_4016", "branch": "feat/scout-v2", "commit": "9e1ab44", "title": "scout: tiktok signal source", "status": "success", "duration_s": 188, "started_at": "1h ago"},
    {"id": "b_4015", "branch": "main", "commit": "55c0f8e", "title": "merge from already-here-dashboard", "status": "success", "duration_s": 96, "started_at": "3h ago"},
    {"id": "b_4014", "branch": "fix/guard-regex", "commit": "12db77a", "title": "guard: tighten DMCA regex", "status": "failed", "duration_s": 204, "started_at": "5h ago"},
    {"id": "b_4013", "branch": "main", "commit": "780e231", "title": "revenue: amazon connector retry", "status": "success", "duration_s": 132, "started_at": "8h ago"},
]

_AUDIT = [
    {"id": "ev_001", "actor": "sovereign-orchestrator", "action": "decision.approve", "target": "apr_005", "at": "now"},
    {"id": "ev_002", "actor": "operator@quantam", "action": "approval.veto", "target": "apr_004", "at": "32m ago"},
    {"id": "ev_003", "actor": "seo-scout", "action": "opportunity.create", "target": "opp_4017", "at": "1h ago"},
    {"id": "ev_004", "actor": "affiliate-link", "action": "budget.reallocate", "target": "rs_2", "at": "1h ago"},
    {"id": "ev_005", "actor": "cost-guard", "action": "paid_action.block", "target": "elevenlabs_call_88", "at": "2h ago"},
    {"id": "ev_006", "actor": "content-generation", "action": "asset.publish", "target": "c2", "at": "1d ago"},
    {"id": "ev_007", "actor": "lifelong-catch-correct", "action": "fix.applied", "target": "guard_regex_v3", "at": "1d ago"},
]

_PROPOSALS = [
    {"id": "prop_1", "title": "Open Studio tier waitlist publicly", "author": "sovereign-orchestrator", "votes_for": 4, "votes_against": 1, "state": "open"},
    {"id": "prop_2", "title": "Pause Faceless Video until B-roll license resolved", "author": "cost-guard", "votes_for": 6, "votes_against": 0, "state": "passed"},
    {"id": "prop_3", "title": "Spin up Stream-F (POD Designer → Etsy)", "author": "pod-designer", "votes_for": 3, "votes_against": 2, "state": "open"},
]

_BOOKS = [
    {"id": "bk_1", "title": "Operator's Playbook v2", "author": "Sovereign", "channel": "Gumroad", "price": 49, "sold": 312, "revenue": 15288.0},
    {"id": "bk_2", "title": "Free-Tier Stack Field Guide", "author": "Already Here LLC", "channel": "Direct", "price": 0, "sold": 1820, "revenue": 0},
    {"id": "bk_3", "title": "Content Agent Recipes", "author": "Quantam", "channel": "Lemon Squeezy", "price": 19, "sold": 92, "revenue": 1748.0},
]

_SECRETS = [
    {"id": "s_anthropic", "name": "ANTHROPIC_API_KEY", "set": True, "last_rotated": "12d ago"},
    {"id": "s_openai", "name": "OPENAI_API_KEY", "set": True, "last_rotated": "12d ago"},
    {"id": "s_gemini", "name": "GEMINI_API_KEY", "set": True, "last_rotated": "30d ago"},
    {"id": "s_stripe", "name": "STRIPE_SECRET_KEY", "set": True, "last_rotated": "60d ago"},
    {"id": "s_devto", "name": "DEVTO_API_KEY", "set": False, "last_rotated": "—"},
    {"id": "s_hashnode", "name": "HASHNODE_API_KEY", "set": False, "last_rotated": "—"},
]

_SOVEREIGN_DECISIONS = [
    {"id": "sd_4017", "summary": "Approve 6-hour Scout opportunity #4017 push", "verdict": "approve",
     "rationale": "ROI 14.6x, $0 marginal cost, Guard clean. Within safety budget.", "at": "now", "confidence": 0.91},
    {"id": "sd_4016", "summary": "Reallocate $240/day from Stream-B → Stream-C", "verdict": "approve",
     "rationale": "Stream-C CTR 6.2x Stream-B; price elasticity tested.", "at": "1h ago", "confidence": 0.88},
    {"id": "sd_4015", "summary": "Hold Video-Agent until B-roll license resolved", "verdict": "hold",
     "rationale": "Guard flagged DMCA risk on three sources. Wait on operator.", "at": "2h ago", "confidence": 0.97},
    {"id": "sd_4014", "summary": "Auto-merge code from already-here-dashboard@a3f9c12", "verdict": "approve",
     "rationale": "AST merger reports +2 upgrades, +32 additions, 0 regressions in CI.", "at": "3h ago", "confidence": 0.99},
]

_SCOUT_OPPS = [
    {"id": "opp_4017", "title": "AI invoice tools for solo creators", "source": "Reddit", "velocity": 4.6, "score": 0.87, "estimated_yield_usd": 480, "captured_at": "12m ago"},
    {"id": "opp_4016", "title": "Niche newsletters around AST tooling", "source": "HN", "velocity": 3.1, "score": 0.78, "estimated_yield_usd": 320, "captured_at": "1h ago"},
    {"id": "opp_4015", "title": "Stripe alternatives in the EU", "source": "TikTok", "velocity": 2.8, "score": 0.71, "estimated_yield_usd": 210, "captured_at": "3h ago"},
    {"id": "opp_4014", "title": "Faceless YouTube finance channels", "source": "Google Trends", "velocity": 5.2, "score": 0.92, "estimated_yield_usd": 610, "captured_at": "5h ago"},
]

_COST = [
    {"category": "LLM — Anthropic", "today_usd": 0.04, "month_usd": 1.18, "limit_usd": 5.0},
    {"category": "LLM — OpenAI", "today_usd": 0.02, "month_usd": 0.47, "limit_usd": 5.0},
    {"category": "LLM — Gemini", "today_usd": 0.0, "month_usd": 0.0, "limit_usd": 1.0},
    {"category": "Cloud — OCI", "today_usd": 0.0, "month_usd": 0.0, "limit_usd": 0.0},
    {"category": "Cloud — Vercel", "today_usd": 0.0, "month_usd": 0.0, "limit_usd": 0.0},
]


def _revenue_series(days: int = 30) -> list[dict]:
    # Deterministic seeded RNG for mock chart data — NOT a security context.
    rng = random.Random(42)  # noqa: S311
    base = 280.0
    today = datetime.now(timezone.utc).date()
    out = []
    for i in range(days, -1, -1):
        d = today - timedelta(days=i)
        base *= 1 + (rng.uniform(-0.05, 0.09))
        out.append({"date": d.isoformat(), "amount": round(max(0, base), 2)})
    return out


# ── App ────────────────────────────────────────────────────────
app = FastAPI(title="ProfitEngine v5 API", version="0.5.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])


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
    return {"agent_id": agent_id, "run_id": str(uuid.uuid4()), "status": "queued",
            "queued_at": datetime.now(timezone.utc).isoformat(),
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
    return {"id": aid, "decision": decision, "at": datetime.now(timezone.utc).isoformat()}


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
