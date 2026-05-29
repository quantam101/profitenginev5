# ProfitEngine v5 — PRD

## Original problem statement
> Compare already-here-llc-dashboard to profitenginev5. Use AST-based merging
> to auto-pull the best functions from AHD into pev5. Then **mirror AHD's
> dashboard functionality, visual style and code into pev5** (or enhance it).
> Ship it with a TokenForge-style market launch.
>
> **(Feb 2026)** Add a mature CI/CD pipeline (GitHub Actions: pre-merge,
> integration, e2e, performance/k6) and a "Data Distillation" engine that
> minimizes LLM token costs via tiered processing, semantic compression and
> aggressive caching. Most optimal, efficient, no-cost-long-term.

## Vision
ProfitEngine v5 is the **open-core Command OS** of an autonomous content
business. 11 AI agents — one Sovereign orchestrator + ten specialists —
find niches, produce assets, distribute, monetize and stay compliant. The
engine self-upgrades by AST-merging the best functions from the production
already-here-dashboard codebase, and every LLM call routes through a tiered
distillation cascade (cache → Gemini 3 Flash → Claude Sonnet 4.6) that holds
steady-state cost near $0.

## Personas
- Indie operator running a $5–25k/mo content business solo
- Agency lead managing 3–10 client brands
- Holding studio with white-label, SSO and Guard policy DSL

## Architecture
- **/app/code_merger/** — Python AST merger CLI (15/15 pytest)
- **/app/backend/server.py** — FastAPI · 29 endpoints
- **/app/backend/services/distillation.py** — Token-efficient LLM router
  - SHA-256 prompt cache (Mongo `distillation_cache`, 7d TTL)
  - Semantic compression (stopword drop outside code fences, dedupe lines)
  - Tier router: cache → Gemini 3 Flash → Claude Sonnet 4.6
  - Strict-JSON outputs · self-escalation via `requires_expert` flag
  - Full token/cost accounting (Mongo `distillation_runs`)
- **/app/frontend/** — React + React Router v6 (18 dashboard pages, AHD aesthetic)
- **/app/app/page.tsx** — Next.js mirror of the launch page
- **/app/.github/workflows/ci.yml** — 5-stage pipeline
  - Stage 1 pre-merge (ruff, ESLint, unit tests)
  - Stage 2 integration (FastAPI + Mongo service, contract pytest)
  - Stage 3 e2e (Playwright headless)
  - Stage 4 performance (k6 smoke @ p95<500ms, err<1%)
  - Stage 5 readiness gate
- **/app/ci/load_smoke.js** — k6 smoke test (10s→5VU, 20s→20VU, 10s→0)
- **MongoDB** — `waitlist`, `merge_events`, `distillation_cache`, `distillation_runs`

## Distillation tiers + live metrics
| Tier | Model | Used for | Cost / 1k tokens |
|------|-------|----------|------------------|
| `cache` | SHA-256 prompt cache | Repeat queries | $0 |
| `cheap` | gemini/gemini-3-flash-preview | Classify, summarize, JSON extract | ~$0.000075 |
| `expensive` | anthropic/claude-sonnet-4-6 | Cheap-tier escalation only | ~$0.009 |

Live verified: **82.58% savings vs all-Claude baseline** over 10 runs.

## Endpoints (29)
- Marketing: `/api/health`, `/api/stats`, `/api/waitlist`, `/api/demo`
- Command: `/api/agents`, `/api/agents/fleet-stats`, `/api/agents/{id}/execute`, `/api/sovereign/status`, `/api/sovereign/decisions`, `/api/approvals`, `/api/approvals/{id}/decide`, `/api/advisor/ask`, `/api/cycle/status`
- Ops: `/api/scout/opportunities`, `/api/content/recent`, `/api/revenue/series`, `/api/revenue/streams`, `/api/revenue/stats`, `/api/ledger/progress`, `/api/books`
- Infra/Gov: `/api/deployments`, `/api/builds`, `/api/audit`, `/api/proposals`, `/api/proof-of-work`, `/api/analytics`, `/api/cost`, `/api/secrets`
- **Distillation (new)**: `/api/distillation/status`, `/api/distillation/stats`, `POST /api/distillation/distill`
- Engine: `/api/merge`, `/api/score`

## What's implemented
- [x] AST merger CLI · 15/15 pytest pass
- [x] AHD ↔ PEV5 merge applied · 32 new defs pulled in
- [x] **Real agent execution** — `POST /api/agents/{id}/execute` runs synchronous LLM via Distiller cascade, returns structured output (`headline`, `findings`, `next_action`, `confidence`), persists `completed`/`errored` status (never `queued` placeholder). Typical first-call cost ~$0.000015, repeats free via cache.
- [x] **No placeholders in counters** — `/api/launch/social-proof` returns only real Mongo counts (no anchored baselines)
- [x] **Branded OG share image** at `/og.png` (1200×630, 47KB, Pillow-rendered) + `og:image` / `twitter:image` meta tags
- [x] **44 backend endpoints** (33 + 8 launch + 3 enterprise)
- [x] **20-agent enterprise fleet** — 11 original + 9 enterprise MVP; Sovereign renamed to **Prime Orchestrator**
- [x] **Autonomy Levels L0–L5** — default L3 Bounded Autonomy
- [x] **Lifelong Catch & Correct panel** with the 8-field issue schema
- [x] **Enterprise manifest** at `/api/enterprise/manifest`
- [x] **Safer enterprise phrasing** throughout — no banned phrases
- [x] **Cash AI page**, persistence + WS, distillation engine (82.58% savings)
- [x] Command Center status strip · Quickstart modal · viral launch kit · Stripe Checkout · referral system · 6-stage CI/CD with deployment gate
- [x] **85/85 tests pass** (iteration_8)
- [x] **Autonomy levels L0–L5** — default **L3 Bounded Autonomy** · persisted to Mongo · GET/PUT endpoints · status-strip pill
- [x] **Lifelong Catch & Correct panel** at `/dashboard/lifelong` with the exact 8-field issue schema
- [x] **Enterprise manifest** at `/api/enterprise/manifest` (system, objectives, revenue equation, loop)
- [x] **Safer enterprise phrasing** — Hero/landing/Pricing avoid "true ASI / military grade / 100% autonomous / guaranteed revenue", use "controlled autonomy / zero-trust hardened / revenue-capacity optimization"
- [x] 20 dashboard pages, AHD-taxonomy sidebar (Operations · Revenue · System)
- [x] **Cash AI page** (highest-confidence open approval) + live WS pill
- [x] **Persistence + WebSocket** — agent runs, approval decisions, cycle events to Mongo, broadcast via `WS /api/ws/cycle`
- [x] **Distillation engine** — 82.58% live LLM cost savings
- [x] **Command Center status strip** — Systems Operational · $0/mo · $25k unlock · Autonomy L3 · Re-open Quickstart
- [x] **Quickstart 5-step modal** — auto-opens first visit, re-openable
- [x] **Stripe Checkout (test mode)** — Studio $149/mo · Annual $1490 · Holding $2500 + idempotent subscriptions + webhook
- [x] **Viral launch kit** — Share Kit / Social Proof Rail / Cohort Bar / referral system / OG meta tags
- [x] **Deployment gate** — `yarn verify` (lint + env:check + test + build) blocks deploy if missing vars or server secrets leak to client bundle
- [x] **6-stage CI/CD pipeline** + k6 smoke + frontend verify
- [x] **85/85 tests pass** (iteration_7)

## Enterprise doctrine
- North-star target: **$1M/day revenue capacity** (capacity, not guarantee)
- **Daily Revenue = Qualified Demand × Conversion Rate × AOV × Purchase Frequency × Fulfillment Capacity × Profit Margin** — every agent must improve at least one variable
- Failure = diagnose → learn → correct → rebuild → retest → distill → execute with higher efficiency
- Approval required for: spending money, bulk outreach, contracts, payment changes, production deploys, sensitive data access, security changes, private-data training

## Backlog (P1)
- **Save to Github** → push `/app` to `quantam101/profitenginev5`
- **Stripe live mode** + production webhook endpoint registration
- **Real agent runtime** for the 9 enterprise MVP agents (currently fixture-shaped)
- **Operator referral dashboard** `/dashboard/referrals` with click + commission ledger
- **OG share image** at `/app/frontend/public/og.png`
- **Stripe Customer Portal** for self-serve subscription management
- **Email magnet** (free playbook PDF) for top-of-funnel capture

## Backlog (P2 — enterprise blueprint stretch)
- **LangGraph or custom parallel orchestrator** runtime (replace fixture agent simulation)
- **Postgres + pgvector** migration (currently MongoDB)
- **Clerk / Auth0** auth swap with RBAC (currently no auth)
- **Sentry + OpenTelemetry** wiring for production observability
- **Connector registry UI** (YAML already exists at `/app/connectors/registry.yaml`)
- **Full 18-agent dashboards** — one dedicated UI per agent
- **Mobile PWA** + React Native shell
- **A11y suite** (axe + Playwright a11y), Lighthouse perf checks in CI
- **k6 thresholds enforced** at p95<500ms, error<1%
- **Backup/restore runbook** + Mongo daily snapshots
- **API contract tests** via Zod schemas shared with frontend
- **GitHub Action**: weekly `code_merger repo` PR with auto comment

## Backlog (P2)
- GitHub Action that runs `code_merger repo` on every PR + posts diff comment
- Stripe checkout for Studio tier
- Telegram/Pushover mobile approvals
- LLM-judge layer for ambiguous AST merges (Claude Sonnet 4.5)
- SSO + audit log streaming to S3 (Holding tier)
- Vector-embedding-based semantic dedup in distiller (currently lexical)

## Test ownership
- Full suite: `cd /app && python -m pytest -v` → 69 local + 7 live HTTP = 76 tests
- Last green run: `/app/test_reports/iteration_4.json`
