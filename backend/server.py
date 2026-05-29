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


MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]
mongo_client = AsyncIOMotorClient(MONGO_URL)
db = mongo_client[DB_NAME]


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
    {"id": "sovereign-v1", "name": "Sovereign", "type": "orchestrator", "tier": "sovereign",
     "status": "active", "mission": "Govern the command OS. Maximize net revenue toward $25k unlock at $0/mo fixed cost.",
     "last_run": "decision cached · 47m remaining", "success_rate": 0.99,
     "runs_today": 24, "run_count": 1842, "success_count": 1824, "failure_count": 18,
     "cycle_interval_min": 60, "model": "gemini/gemini-2.0-flash"},
    {"id": "scout-agent", "name": "Trend Scout", "type": "specialist", "tier": "operational",
     "status": "online", "mission": "Scan trending search queries, subreddits, TikTok signals to surface monetizable niches.",
     "last_run": "2m ago", "success_rate": 0.94, "runs_today": 18, "run_count": 612, "success_count": 575, "failure_count": 37,
     "cycle_interval_min": 60, "model": "gemini/gemini-2.0-flash"},
    {"id": "content-agent", "name": "Content Generator", "type": "specialist", "tier": "operational",
     "status": "thinking", "mission": "Produce blog posts, threads, scripts and email sequences from Scout's briefs.",
     "last_run": "running", "success_rate": 0.91, "runs_today": 42, "run_count": 1289, "success_count": 1173, "failure_count": 116,
     "cycle_interval_min": 360, "model": "anthropic/claude-sonnet-4-5"},
    {"id": "video-agent", "name": "Faceless Video Script", "type": "specialist", "tier": "operational",
     "status": "online", "mission": "Stitch Content briefs into vertical video scripts with captions, music cues and B-roll.",
     "last_run": "11m ago", "success_rate": 0.88, "runs_today": 9, "run_count": 287, "success_count": 252, "failure_count": 35,
     "cycle_interval_min": 720, "model": "anthropic/claude-sonnet-4-5"},
    {"id": "social-agent", "name": "Social Publisher", "type": "specialist", "tier": "operational",
     "status": "online", "mission": "Schedule posts, reply to comments, reroute traffic to revenue assets.",
     "last_run": "1m ago", "success_rate": 0.97, "runs_today": 64, "run_count": 2104, "success_count": 2041, "failure_count": 63,
     "cycle_interval_min": 30, "model": "openai/gpt-5.2"},
    {"id": "revenue-agent", "name": "Revenue Tracker", "type": "specialist", "tier": "operational",
     "status": "online", "mission": "Route traffic across affiliate links, digital products and ad inventory; reallocate budget.",
     "last_run": "6m ago", "success_rate": 0.92, "runs_today": 24, "run_count": 824, "success_count": 758, "failure_count": 66,
     "cycle_interval_min": 60, "model": "gemini/gemini-2.0-flash"},
    {"id": "guard-agent", "name": "Infrastructure Guardian", "type": "specialist", "tier": "operational",
     "status": "paused", "mission": "Review every outbound asset for policy, IP and brand-safety violations.",
     "last_run": "human review", "success_rate": 1.0, "runs_today": 6, "run_count": 192, "success_count": 192, "failure_count": 0,
     "cycle_interval_min": 15, "model": "openai/gpt-5.2"},
]

_APPROVALS = [
    {"id": "apr_001", "agent": "Content Generator", "action": "Publish blog post",
     "summary": "“5 sleeper niches for affiliate creators in 2026” — 2,180 words, 6 outbound links.", "risk": "low", "created_at": "4m ago"},
    {"id": "apr_002", "agent": "Revenue Tracker", "action": "Reallocate budget",
     "summary": "Move $240/day from Stream-B (Amazon) to Stream-C (Digital). Projected lift +18%.", "risk": "medium", "created_at": "12m ago"},
    {"id": "apr_003", "agent": "Social Publisher", "action": "Reply to comment thread",
     "summary": "Public reply on @already_here_llc → 412k impressions, sentiment 0.78.", "risk": "low", "created_at": "21m ago"},
    {"id": "apr_004", "agent": "Infrastructure Guardian", "action": "Block outbound asset",
     "summary": "Detected DMCA-flagged image in Video-#221 thumbnail. Requesting alternate.", "risk": "high", "created_at": "38m ago"},
    {"id": "apr_005", "agent": "Sovereign", "action": "Trigger 6-hour campaign",
     "summary": "Sovereign proposes a 6-hour multi-channel push on Scout opportunity #4017. Est. spend $0, est. yield $480.", "risk": "medium", "created_at": "1h ago"},
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
    {"id": "ev_001", "actor": "sovereign-v1", "action": "decision.approve", "target": "apr_005", "at": "now"},
    {"id": "ev_002", "actor": "operator@quantam", "action": "approval.veto", "target": "apr_004", "at": "32m ago"},
    {"id": "ev_003", "actor": "scout-agent", "action": "opportunity.create", "target": "opp_4017", "at": "1h ago"},
    {"id": "ev_004", "actor": "revenue-agent", "action": "budget.reallocate", "target": "rs_2", "at": "1h ago"},
    {"id": "ev_005", "actor": "guard-agent", "action": "asset.block", "target": "video_221", "at": "2h ago"},
    {"id": "ev_006", "actor": "content-agent", "action": "asset.publish", "target": "c2", "at": "1d ago"},
    {"id": "ev_007", "actor": "social-agent", "action": "reply.post", "target": "tweet_88121", "at": "1d ago"},
]

_PROPOSALS = [
    {"id": "prop_1", "title": "Open Studio tier waitlist publicly", "author": "sovereign-v1", "votes_for": 4, "votes_against": 1, "state": "open"},
    {"id": "prop_2", "title": "Pause video-agent until B-roll license resolved", "author": "guard-agent", "votes_for": 6, "votes_against": 0, "state": "passed"},
    {"id": "prop_3", "title": "Spin up Stream-F (Gumroad cohorts)", "author": "revenue-agent", "votes_for": 3, "votes_against": 2, "state": "open"},
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
    return {"id": "sovereign-v1", "model": "gemini/gemini-2.0-flash",
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
    return {"state": "active", "tier_routing": {"local": 0.42, "groq": 0.31, "gemini": 0.18, "claude": 0.09},
            "savings_vs_baseline_pct": 0.71, "pipeline_runs_24h": 1842}


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
    return {
        "question": q,
        "answer": (
            "Based on the last 14 days, your Stream-C (digital product) is your highest-leverage channel. "
            "Suggest pushing Scout opportunity #4017 through Content → Video → Social, gated on Guard."
        ),
        "agent": "sovereign-v1",
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
