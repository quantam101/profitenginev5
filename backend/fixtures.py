"""Domain fixtures for ProfitEngine v5 — extracted from server.py.

These are the AHD-shaped seed datasets used by the dashboard preview. They
remain fixture-backed by design; real persistence (Mongo writes + WS) is
layered on top in server.py for agent runs, approval decisions and cycle
events.
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone


AGENTS = [
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

APPROVALS = [
    {"id": "apr_001", "agent": "Content Generation Agent", "action": "Publish blog post",
     "summary": "\u201c5 sleeper niches for affiliate creators in 2026\u201d \u2014 2,180 words, 6 outbound links.",
     "risk": "low", "created_at": "4m ago", "confidence": 0.88, "state": "open"},
    {"id": "apr_002", "agent": "Affiliate Link Agent", "action": "Reallocate budget",
     "summary": "Move $240/day from Stream-B (Amazon) to Stream-C (Digital). Projected lift +18%.",
     "risk": "medium", "created_at": "12m ago", "confidence": 0.79, "state": "open"},
    {"id": "apr_003", "agent": "SEO Scout Agent", "action": "Queue new topic batch",
     "summary": "Queue 12 new keyword clusters from AHREFS pull \u2014 est. 38k monthly searches.",
     "risk": "low", "created_at": "21m ago", "confidence": 0.92, "state": "open"},
    {"id": "apr_004", "agent": "Cost Guard Agent", "action": "Block paid action",
     "summary": "Faceless Video Agent attempted $4.00 ElevenLabs call \u2014 blocked, fallback to local TTS.",
     "risk": "high", "created_at": "38m ago", "confidence": 0.97, "state": "open"},
    {"id": "apr_005", "agent": "Sovereign Orchestrator", "action": "Trigger 6-hour campaign",
     "summary": "Sovereign proposes a 6-hour multi-channel push on SEO Scout opportunity #4017. Est. spend $0, est. yield $480.",
     "risk": "medium", "created_at": "1h ago", "confidence": 0.94, "state": "open"},
]

CONTENT = [
    {"id": "c1", "title": "5 sleeper niches for affiliate creators in 2026", "channel": "Blog", "status": "queued", "revenue": 0.0, "created_at": "today", "word_count": 2180},
    {"id": "c2", "title": "How we automated a $14k/mo content stack", "channel": "Newsletter", "status": "published", "revenue": 1280.40, "created_at": "yesterday", "word_count": 1870},
    {"id": "c3", "title": "Why your funnel needs Guard before Revenue", "channel": "X / Twitter", "status": "published", "revenue": 412.10, "created_at": "2d", "word_count": 280},
    {"id": "c4", "title": "Scout vs human researchers \u2014 a 30-day test", "channel": "YouTube short", "status": "draft", "revenue": 0.0, "created_at": "3d", "word_count": 95},
    {"id": "c5", "title": "Edge-case: when Guard overrides Revenue", "channel": "Blog", "status": "published", "revenue": 884.50, "created_at": "4d", "word_count": 2410},
    {"id": "c6", "title": "Sovereign Decision Log \u2014 Week 17", "channel": "Newsletter", "status": "published", "revenue": 1102.20, "created_at": "5d", "word_count": 1610},
    {"id": "c7", "title": "Three free signals Scout missed last sprint", "channel": "Blog", "status": "draft", "revenue": 0.0, "created_at": "6d", "word_count": 0},
]

REVENUE_STREAMS = [
    {"id": "rs_1", "name": "Amazon Affiliates", "kind": "affiliate", "active": True, "mrr": 2340.00, "ctr": 0.041, "health": 0.92},
    {"id": "rs_2", "name": "Digital Product \u2014 Operator Playbook", "kind": "product", "active": True, "mrr": 6120.00, "ctr": 0.087, "health": 0.98},
    {"id": "rs_3", "name": "Display Ads (Mediavine)", "kind": "ads", "active": True, "mrr": 1890.00, "ctr": 0.014, "health": 0.81},
    {"id": "rs_4", "name": "Sponsored Slots", "kind": "sponsorship", "active": True, "mrr": 3800.00, "ctr": 0.0, "health": 0.95},
    {"id": "rs_5", "name": "Affiliate \u2014 Skool Cohort", "kind": "affiliate", "active": False, "mrr": 0.0, "ctr": 0.0, "health": 0.0},
]

DEPLOYMENTS = [
    {"id": "dep_1", "service": "engine-runtime", "env": "production", "version": "v5.0.7", "status": "active", "url": "engine.profitengine.dev", "deployed_at": "12m ago"},
    {"id": "dep_2", "service": "blog-publisher", "env": "production", "version": "v5.0.6", "status": "active", "url": "blog.profitengine.dev", "deployed_at": "2h ago"},
    {"id": "dep_3", "service": "approvals-worker", "env": "production", "version": "v5.0.7", "status": "rolling", "url": "\u2014", "deployed_at": "now"},
    {"id": "dep_4", "service": "dashboard", "env": "production", "version": "v5.0.7", "status": "active", "url": "app.profitengine.dev", "deployed_at": "12m ago"},
    {"id": "dep_5", "service": "video-rendering", "env": "staging", "version": "v5.1.0-rc.2", "status": "active", "url": "\u2014", "deployed_at": "1d ago"},
]

BUILDS = [
    {"id": "b_4017", "branch": "main", "commit": "a3f9c12", "title": "feat: sovereign decision cache", "status": "success", "duration_s": 142, "started_at": "12m ago"},
    {"id": "b_4016", "branch": "feat/scout-v2", "commit": "9e1ab44", "title": "scout: tiktok signal source", "status": "success", "duration_s": 188, "started_at": "1h ago"},
    {"id": "b_4015", "branch": "main", "commit": "55c0f8e", "title": "merge from already-here-dashboard", "status": "success", "duration_s": 96, "started_at": "3h ago"},
    {"id": "b_4014", "branch": "fix/guard-regex", "commit": "12db77a", "title": "guard: tighten DMCA regex", "status": "failed", "duration_s": 204, "started_at": "5h ago"},
    {"id": "b_4013", "branch": "main", "commit": "780e231", "title": "revenue: amazon connector retry", "status": "success", "duration_s": 132, "started_at": "8h ago"},
]

AUDIT = [
    {"id": "ev_001", "actor": "sovereign-orchestrator", "action": "decision.approve", "target": "apr_005", "at": "now"},
    {"id": "ev_002", "actor": "operator@quantam", "action": "approval.veto", "target": "apr_004", "at": "32m ago"},
    {"id": "ev_003", "actor": "seo-scout", "action": "opportunity.create", "target": "opp_4017", "at": "1h ago"},
    {"id": "ev_004", "actor": "affiliate-link", "action": "budget.reallocate", "target": "rs_2", "at": "1h ago"},
    {"id": "ev_005", "actor": "cost-guard", "action": "paid_action.block", "target": "elevenlabs_call_88", "at": "2h ago"},
    {"id": "ev_006", "actor": "content-generation", "action": "asset.publish", "target": "c2", "at": "1d ago"},
    {"id": "ev_007", "actor": "lifelong-catch-correct", "action": "fix.applied", "target": "guard_regex_v3", "at": "1d ago"},
]

PROPOSALS = [
    {"id": "prop_1", "title": "Open Studio tier waitlist publicly", "author": "sovereign-orchestrator", "votes_for": 4, "votes_against": 1, "state": "open"},
    {"id": "prop_2", "title": "Pause Faceless Video until B-roll license resolved", "author": "cost-guard", "votes_for": 6, "votes_against": 0, "state": "passed"},
    {"id": "prop_3", "title": "Spin up Stream-F (POD Designer \u2192 Etsy)", "author": "pod-designer", "votes_for": 3, "votes_against": 2, "state": "open"},
]

BOOKS = [
    {"id": "bk_1", "title": "Operator's Playbook v2", "author": "Sovereign", "channel": "Gumroad", "price": 49, "sold": 312, "revenue": 15288.0},
    {"id": "bk_2", "title": "Free-Tier Stack Field Guide", "author": "Already Here LLC", "channel": "Direct", "price": 0, "sold": 1820, "revenue": 0},
    {"id": "bk_3", "title": "Content Agent Recipes", "author": "Quantam", "channel": "Lemon Squeezy", "price": 19, "sold": 92, "revenue": 1748.0},
]

SECRETS = [
    {"id": "s_anthropic", "name": "ANTHROPIC_API_KEY", "set": True, "last_rotated": "12d ago"},
    {"id": "s_openai", "name": "OPENAI_API_KEY", "set": True, "last_rotated": "12d ago"},
    {"id": "s_gemini", "name": "GEMINI_API_KEY", "set": True, "last_rotated": "30d ago"},
    {"id": "s_stripe", "name": "STRIPE_SECRET_KEY", "set": True, "last_rotated": "60d ago"},
    {"id": "s_devto", "name": "DEVTO_API_KEY", "set": False, "last_rotated": "\u2014"},
    {"id": "s_hashnode", "name": "HASHNODE_API_KEY", "set": False, "last_rotated": "\u2014"},
]

SOVEREIGN_DECISIONS = [
    {"id": "sd_4017", "summary": "Approve 6-hour Scout opportunity #4017 push", "verdict": "approve",
     "rationale": "ROI 14.6x, $0 marginal cost, Guard clean. Within safety budget.", "at": "now", "confidence": 0.91,
     "risk": "low", "tags": ["sovereign-orchestrator", "seo-scout", "affiliate-link"]},
    {"id": "sd_4016", "summary": "Reallocate $240/day from Stream-B \u2192 Stream-C", "verdict": "approve",
     "rationale": "Stream-C CTR 6.2x Stream-B; price elasticity tested.", "at": "1h ago", "confidence": 0.88,
     "risk": "medium", "tags": ["affiliate-link"]},
    {"id": "sd_4015", "summary": "Hold Video-Agent until B-roll license resolved", "verdict": "hold",
     "rationale": "Guard flagged DMCA risk on three sources. Wait on operator.", "at": "2h ago", "confidence": 0.97,
     "risk": "high", "tags": ["faceless-video", "cost-guard"]},
    {"id": "sd_4014", "summary": "Auto-merge code from already-here-dashboard@a3f9c12", "verdict": "approve",
     "rationale": "AST merger reports +2 upgrades, +32 additions, 0 regressions in CI.", "at": "3h ago", "confidence": 0.99,
     "risk": "low", "tags": ["sovereign-orchestrator", "lifelong-catch-correct"]},
]

SCOUT_OPPS = [
    {"id": "opp_4017", "title": "AI invoice tools for solo creators", "source": "Reddit", "velocity": 4.6, "score": 0.87, "estimated_yield_usd": 480, "captured_at": "12m ago"},
    {"id": "opp_4016", "title": "Niche newsletters around AST tooling", "source": "HN", "velocity": 3.1, "score": 0.78, "estimated_yield_usd": 320, "captured_at": "1h ago"},
    {"id": "opp_4015", "title": "Stripe alternatives in the EU", "source": "TikTok", "velocity": 2.8, "score": 0.71, "estimated_yield_usd": 210, "captured_at": "3h ago"},
    {"id": "opp_4014", "title": "Faceless YouTube finance channels", "source": "Google Trends", "velocity": 5.2, "score": 0.92, "estimated_yield_usd": 610, "captured_at": "5h ago"},
]

COST = [
    {"category": "LLM \u2014 Anthropic", "today_usd": 0.04, "month_usd": 1.18, "limit_usd": 5.0},
    {"category": "LLM \u2014 OpenAI", "today_usd": 0.02, "month_usd": 0.47, "limit_usd": 5.0},
    {"category": "LLM \u2014 Gemini", "today_usd": 0.0, "month_usd": 0.0, "limit_usd": 1.0},
    {"category": "Cloud \u2014 OCI", "today_usd": 0.0, "month_usd": 0.0, "limit_usd": 0.0},
    {"category": "Cloud \u2014 Vercel", "today_usd": 0.0, "month_usd": 0.0, "limit_usd": 0.0},
]


def revenue_series(days: int = 30) -> list[dict]:
    """Deterministic seeded RNG for mock chart data \u2014 not a security context."""
    rng = random.Random(42)  # noqa: S311
    base = 280.0
    today = datetime.now(timezone.utc).date()
    out = []
    for i in range(days, -1, -1):
        d = today - timedelta(days=i)
        base *= 1 + (rng.uniform(-0.05, 0.09))
        out.append({"date": d.isoformat(), "amount": round(max(0, base), 2)})
    return out
