# ProfitEngine v5 — PRD

## Original problem statement
> Compare already-here-llc-dashboard to profitenginev5. Use AST-based merging
> to auto-pull the best functions from AHD into pev5. Then **mirror AHD's
> dashboard functionality, visual style and code into pev5** (or enhance it).
> Ship it with a TokenForge-style market launch.

## Vision
ProfitEngine v5 is the **open-core Command OS** of an autonomous content
business. Seven AI agents — one Sovereign orchestrator + six specialists —
find niches, produce assets, distribute, monetize and stay compliant. Each
release the engine self-upgrades by AST-merging the best functions from the
production already-here-dashboard codebase.

## Personas
- Indie operator running a $5–25k/mo content business solo
- Agency lead managing 3–10 client brands
- Holding studio with white-label, SSO and Guard policy DSL

## Architecture
- **/app/code_merger/** — Python AST merger CLI (`python -m code_merger ...`)
  - 15/15 pytest, AHD ↔ PEV5 demo merge committed under `demo_output/`
- **/app/backend/server.py** — FastAPI · 27 endpoints
  - Marketing: `/api/health`, `/api/stats`, `/api/waitlist`, `/api/demo`
  - Command: `/api/agents`, `/api/agents/{id}/execute`, `/api/sovereign/status`, `/api/sovereign/decisions`, `/api/approvals`, `/api/approvals/{id}/decide`, `/api/advisor/ask`, `/api/cycle/status`
  - Ops: `/api/scout/opportunities`, `/api/content/recent`, `/api/revenue/series`, `/api/revenue/streams`, `/api/revenue/stats`, `/api/ledger/progress`, `/api/books`
  - Infra/Governance: `/api/deployments`, `/api/builds`, `/api/audit`, `/api/proposals`, `/api/proof-of-work`, `/api/distillation/status`, `/api/analytics`, `/api/cost`, `/api/secrets`
  - Engine: `/api/merge`, `/api/score`
- **/app/frontend/** — React + React Router v6
  - `/` — TokenForge-style launchpad: hero, problem, agents showcase (7 cards), dashboard preview, engine playground, pricing, roadmap, FAQ, waitlist
  - `/dashboard` and 17 nested routes:
    - **Command**: Overview · Sovereign · Agents · Approvals · Advisor
    - **Operations**: Scout · Content · Revenue · Books
    - **Infrastructure**: Deployments · Builds · Audit Log · Proposals
    - **Governance**: Proof of Work · Analytics · Distillation · Cost · Secrets
- **/app/app/page.tsx** — Next.js mirror of the launch page for production deploy
- **MongoDB** — `waitlist`, `merge_events` collections

## Visual system (mirrors AHD Command OS v2.0)
- Dark blue-gray base `#0a0e1a` with diagonal gradient
- Glass-blur `.ent-card` panels (24px backdrop-filter) + `.sov-card` indigo-glow tier for Sovereign elements
- Green primary `#22c55e` (operational), indigo Sovereign accent `#6366f1`, amber warnings, pink danger
- Space Grotesk display + Inter body + JetBrains Mono code
- Status pill grammar: `status-badge-{active|online|paused|failed|...}`
- 18-link grouped sidebar (Command / Operations / Infrastructure / Governance)
- Live cycle pill in topbar + Sovereign mini-status in sidebar footer

## What's implemented (Jan 2026)
- [x] AST merger CLI · 15/15 pytest pass
- [x] AHD ↔ PEV5 merge applied — 4 files paired · 2 upgrades · 32 new defs pulled into `/app/backend/services/` + `/app/runtime/` (originals `.bak`)
- [x] 28 backend endpoints (added `/api/agents/fleet-stats`)
- [x] **11-agent fleet** preserved exactly as in pev5's original: Sovereign Orchestrator · Cost Guard · Content Generation · Proposal Engine · Lifelong Catch and Correct · SEO Scout · Faceless Video · POD Designer · Affiliate Link · Health Oracle · Procurement Scout. Total runs 3,191 · fleet success 98%.
- [x] 18 dashboard pages with AHD command-OS aesthetic merged on top — Agent Command Center matches user's spec pixel-for-pixel (title, subtitle, 4 KPIs, 11 cards, status/category badges, Execute button, Runs / Success rate / Recent fails columns)
- [x] React launch site with 11-AGENT FLEET hero, AHD-derived sections (problem, dashboard preview, AST engine playground, pricing, roadmap, FAQ, waitlist)
- [x] Next.js mirror at `/app/app/page.tsx` for production deploy
- [x] **56/56 tests pass · `retest_needed: false`** (testing agent iteration_3)

## Backlog (P1)
- Push `/app` to `quantam101/profitenginev5` (the user's live repo)
- Wire `POST /api/waitlist` from the Next.js launch (currently `mailto:` fallback)
- Persist agent execute / approval decisions to Mongo + WebSocket push for real-time cycle updates
- Connector registry UI (the YAML already exists at `/app/connectors/registry.yaml`)

## Backlog (P2)
- GitHub Action that runs `code_merger repo` on every PR + posts an "Engine Self-Upgrade" diff comment
- Stripe checkout for Studio tier
- Telegram/Pushover mobile approvals
- LLM-judge layer for ambiguous AST merges (Claude Sonnet 4.5)
- SSO + audit log streaming to S3 (Holding tier)

## Next tasks
1. **Push to GitHub** — `quantam101/profitenginev5` gets the new launch + 18 dashboard pages + merged backend
2. Schedule the `code_merger repo` Action to run weekly so v5 keeps pulling from AHD
3. Land PR-bot mode behind a feature flag (P2 → P1 after first cohort)

## Test ownership
- CLI: `cd /app && python -m pytest code_merger/tests/ -v` (15 tests)
- Backend: `cd /app && python -m pytest backend/tests/test_backend_api.py -v` (41 tests)
- Last green run: `/app/test_reports/iteration_3.json`
