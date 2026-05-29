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
- [x] 29 backend endpoints (+3 new for distillation, /api/distillation/status now live)
- [x] **11-agent fleet** preserved (Sovereign + Cost Guard + Content + Proposal + Lifelong + SEO Scout + Faceless Video + POD Designer + Affiliate + Health Oracle + Procurement)
- [x] 18 dashboard pages with AHD command-OS aesthetic
- [x] TokenForge-style launch (React + Next.js mirror)
- [x] **Data Distillation engine** — cache + Gemini-Flash + Claude-Sonnet tiering, 82.58% live savings
- [x] **Advisor endpoint upgraded** — now uses distiller with deterministic fallback
- [x] **5-stage CI/CD pipeline** in `.github/workflows/ci.yml`
- [x] **k6 smoke** at `/app/ci/load_smoke.js`
- [x] **76/76 tests pass** (15 code_merger + 41 backend_api + 13 distillation unit + 7 distillation live HTTP)

## Backlog (P1)
- Push `/app` to `quantam101/profitenginev5` via "Save to Github"
- Wire `POST /api/waitlist` from the Next.js launch (currently `mailto:` fallback)
- Persist agent execute / approval decisions to Mongo + WebSocket push for real-time cycle updates
- Connector registry UI (the YAML already exists at `/app/connectors/registry.yaml`)
- Extract fixture blocks from server.py into `backend/fixtures.py` (server.py is at ~645 lines)

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
