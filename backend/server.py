"""
ProfitEngine v5 backend — FastAPI service for the launchpad + command-center.

Provides marketing endpoints (waitlist, stats, demo) plus dashboard endpoints
(agents, approvals, revenue, content, cycle) that power the embedded
command-center preview ported from already-here-dashboard.

The AST code-merger engine ships as a separate ``code_merger`` package at the
repo root and is exposed here via /api/merge, /api/score and /api/demo.
"""
from __future__ import annotations

import os
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Literal

import ast
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr, Field
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

load_dotenv(Path(__file__).resolve().parent / ".env")

from code_merger.python_merger import merge_python_files  # noqa: E402
from code_merger.js_merger import merge_js_files  # noqa: E402
from code_merger.scoring import score_python_function  # noqa: E402


# ---------------------------------------------------------------------------
# Mongo wiring
# ---------------------------------------------------------------------------
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]
mongo_client = AsyncIOMotorClient(MONGO_URL)
db = mongo_client[DB_NAME]


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
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


class Agent(BaseModel):
    id: str
    name: str
    role: str
    status: Literal["online", "thinking", "paused", "offline"]
    last_run: str
    success_rate: float
    runs_today: int
    description: str


class Approval(BaseModel):
    id: str
    agent: str
    action: str
    summary: str
    risk: Literal["low", "medium", "high"]
    created_at: str


class ContentItem(BaseModel):
    id: str
    title: str
    channel: str
    status: Literal["draft", "queued", "published"]
    revenue: float
    created_at: str


class RevenuePoint(BaseModel):
    date: str
    amount: float


# ---------------------------------------------------------------------------
# Mock domain data — autonomous-agent product preview
# ---------------------------------------------------------------------------
_AGENTS = [
    {
        "id": "scout",
        "name": "Scout",
        "role": "Opportunity discovery",
        "status": "online",
        "last_run": "2m ago",
        "success_rate": 0.94,
        "runs_today": 18,
        "description": "Scans trending search queries, subreddits and TikTok signals to surface monetizable niches.",
    },
    {
        "id": "content",
        "name": "Content",
        "role": "Multi-channel writer",
        "status": "thinking",
        "last_run": "running",
        "success_rate": 0.91,
        "runs_today": 42,
        "description": "Produces blog posts, threads, scripts and email sequences from Scout's briefs.",
    },
    {
        "id": "video",
        "name": "Video",
        "role": "Short-form producer",
        "status": "online",
        "last_run": "11m ago",
        "success_rate": 0.88,
        "runs_today": 9,
        "description": "Stitches Content briefs into vertical videos with captions, music and B-roll.",
    },
    {
        "id": "social",
        "name": "Social",
        "role": "Distribution & engagement",
        "status": "online",
        "last_run": "1m ago",
        "success_rate": 0.97,
        "runs_today": 64,
        "description": "Schedules posts, replies to comments and reroutes traffic to revenue assets.",
    },
    {
        "id": "revenue",
        "name": "Revenue",
        "role": "Monetization controller",
        "status": "online",
        "last_run": "6m ago",
        "success_rate": 0.92,
        "runs_today": 24,
        "description": "Routes traffic across affiliate links, digital products and ad inventory.",
    },
    {
        "id": "guard",
        "name": "Guard",
        "role": "Compliance & risk",
        "status": "paused",
        "last_run": "human review",
        "success_rate": 1.0,
        "runs_today": 6,
        "description": "Reviews every outbound asset for policy, IP and brand-safety violations.",
    },
]

_APPROVALS = [
    {
        "id": "apr_001",
        "agent": "Content",
        "action": "Publish blog post",
        "summary": "“5 sleeper niches for affiliate creators in 2026” — 2,180 words, 6 outbound links.",
        "risk": "low",
        "created_at": "4m ago",
    },
    {
        "id": "apr_002",
        "agent": "Revenue",
        "action": "Reallocate budget",
        "summary": "Move $240/day from Stream-B (Amazon) to Stream-C (Digital). Projected lift +18%.",
        "risk": "medium",
        "created_at": "12m ago",
    },
    {
        "id": "apr_003",
        "agent": "Social",
        "action": "Reply to comment thread",
        "summary": "Public reply on @already_here_llc → 412k impressions, sentiment 0.78.",
        "risk": "low",
        "created_at": "21m ago",
    },
    {
        "id": "apr_004",
        "agent": "Guard",
        "action": "Block outbound asset",
        "summary": "Detected DMCA-flagged image in Video-#221 thumbnail. Requesting alternate.",
        "risk": "high",
        "created_at": "38m ago",
    },
]

_CONTENT = [
    {"id": "c1", "title": "5 sleeper niches for affiliate creators in 2026", "channel": "Blog", "status": "queued", "revenue": 0.0, "created_at": "today"},
    {"id": "c2", "title": "How we automated a $14k/mo content stack", "channel": "Newsletter", "status": "published", "revenue": 1280.40, "created_at": "yesterday"},
    {"id": "c3", "title": "Why your funnel needs Guard before Revenue", "channel": "X / Twitter", "status": "published", "revenue": 412.10, "created_at": "2d"},
    {"id": "c4", "title": "Scout vs human researchers — a 30-day test", "channel": "YouTube short", "status": "draft", "revenue": 0.0, "created_at": "3d"},
    {"id": "c5", "title": "Edge-case: when Guard overrides Revenue", "channel": "Blog", "status": "published", "revenue": 884.50, "created_at": "4d"},
]


def _revenue_series(days: int = 30) -> list[dict]:
    rng = random.Random(42)
    base = 280.0
    today = datetime.now(timezone.utc).date()
    out = []
    for i in range(days, -1, -1):
        d = today - timedelta(days=i)
        base *= 1 + (rng.uniform(-0.05, 0.09))
        out.append({"date": d.isoformat(), "amount": round(max(0, base), 2)})
    return out


# ---------------------------------------------------------------------------
# App + middleware
# ---------------------------------------------------------------------------
app = FastAPI(title="ProfitEngine v5 API", version="0.5.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Health + marketing
# ---------------------------------------------------------------------------
@app.get("/api/health")
async def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "profitengine-v5",
        "time": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/stats", response_model=StatsResponse)
async def stats_endpoint() -> StatsResponse:
    devs = await db.waitlist.count_documents({})
    return StatsResponse(
        revenue_30d=sum(p["amount"] for p in _revenue_series(30)),
        posts_published=sum(1 for c in _CONTENT if c["status"] == "published") + 1247,
        agents_online=sum(1 for a in _AGENTS if a["status"] == "online"),
        devs_joined=devs + 312,
    )


@app.post("/api/waitlist", response_model=WaitlistResponse)
async def waitlist_endpoint(entry: WaitlistEntry) -> WaitlistResponse:
    existing = await db.waitlist.find_one({"email": entry.email})
    if existing:
        return WaitlistResponse(
            id=existing["id"], position=existing.get("position", 0), email=entry.email
        )
    position = await db.waitlist.count_documents({}) + 1
    doc = {
        "id": str(uuid.uuid4()),
        "email": entry.email,
        "role": entry.role,
        "repo_url": entry.repo_url,
        "use_case": entry.use_case,
        "position": position,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.waitlist.insert_one(doc)
    return WaitlistResponse(id=doc["id"], position=position, email=entry.email)


# ---------------------------------------------------------------------------
# Dashboard — command-center preview endpoints
# ---------------------------------------------------------------------------
@app.get("/api/agents", response_model=list[Agent])
async def list_agents() -> list[Agent]:
    return [Agent(**a) for a in _AGENTS]


@app.get("/api/approvals", response_model=list[Approval])
async def list_approvals() -> list[Approval]:
    return [Approval(**a) for a in _APPROVALS]


@app.get("/api/content/recent", response_model=list[ContentItem])
async def list_content() -> list[ContentItem]:
    return [ContentItem(**c) for c in _CONTENT]


@app.get("/api/revenue/series", response_model=list[RevenuePoint])
async def revenue_series(days: int = 30) -> list[RevenuePoint]:
    if days < 1 or days > 365:
        raise HTTPException(status_code=400, detail="days must be 1..365")
    return [RevenuePoint(**p) for p in _revenue_series(days)]


@app.get("/api/cycle/status")
async def cycle_status() -> dict[str, Any]:
    return {
        "state": "running",
        "current_step": "Content -> Video pipeline",
        "step_index": 3,
        "step_total": 7,
        "started_at": (datetime.now(timezone.utc) - timedelta(minutes=8)).isoformat(),
        "approval_required": True,
    }


# ---------------------------------------------------------------------------
# Code merger endpoints (powers the in-launch playground)
# ---------------------------------------------------------------------------
@app.post("/api/merge", response_model=MergeResponse)
async def merge_endpoint(req: MergeRequest) -> MergeResponse:
    try:
        if req.language == "python":
            res = merge_python_files(req.base, req.target, add_unique_blocks=req.add_unique)
            added_imports = res.added_imports
        else:
            res = merge_js_files(req.base, req.target, add_unique_blocks=req.add_unique)
            added_imports = []
    except SyntaxError as exc:
        raise HTTPException(status_code=400, detail=f"Syntax error: {exc}") from exc
    await db.merge_events.insert_one({
        "id": str(uuid.uuid4()),
        "language": req.language,
        "upgrades": len(res.upgrades),
        "additions": len(res.additions),
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return MergeResponse(
        merged=res.merged_source,
        upgrades=[MergeUpgrade(**u) for u in res.upgrades],
        additions=res.additions,
        base_only=res.base_only,
        target_only=res.target_only,
        added_imports=added_imports,
    )


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
