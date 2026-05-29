# ProfitEngine v5 — PRD

## Original problem statement
> Review and compare already-here-llc-dashboard to profitenginev5. Compare the
> two codebases and auto-merge the "best" parts into profitenginev5 using
> AST-based code merging (Automated Program Repair). Score on robustness,
> completeness, complexity. Then enhance profitenginev5 with the dashboard from
> already-here-dashboard and ship a TokenForge-style market launch.

## Vision
ProfitEngine v5 is an open-core, six-agent autonomous content business engine
(Scout / Content / Video / Social / Revenue / Guard) targeting senior indie
operators, agencies and fund-backed content studios. Each release, the engine
self-upgrades by AST-merging the best functions from the production
already-here-dashboard codebase back into v5.

## Personas
| Persona | Goal |
| --- | --- |
| Indie operator | Run a $5–25k/mo content business solo, unattended |
| Agency lead | Multi-workspace control plane for 3–10 client brands |
| Holding studio | White-label brand mode, SSO, custom Guard policy DSL |

## Architecture
- **/app/code_merger/** — Python AST merger CLI (`python -m code_merger ...`)
  - `scoring.py` — robustness / completeness / maintainability scoring
  - `python_merger.py` — full AST swap + import pull-in
  - `js_merger.py` — brace-balanced JS/TS tokenizer & merge
  - `repo_merger.py` — walks two repos, pairs by basename, writes upgraded output
  - `cli.py` — `merge` / `score` / `repo` subcommands
  - `tests/` — 15 pytest tests (all pass)
- **/app/backend/server.py** — FastAPI on port 8001
  - Marketing: `/api/health`, `/api/stats`, `/api/waitlist`, `/api/demo`
  - Dashboard: `/api/agents`, `/api/approvals`, `/api/content/recent`, `/api/revenue/series`, `/api/cycle/status`
  - Engine: `/api/merge`, `/api/score`
- **/app/frontend/** — React (CRA) on port 3000, React Router v6
  - `/` — TokenForge-style launchpad
  - `/dashboard`, `/dashboard/agents`, `/dashboard/approvals`, `/dashboard/revenue`, `/dashboard/content`
- **/app/app/page.tsx** — Next.js mirror of the launch page for the actual production deploy (uses inline neon CSS, no Tailwind)
- **MongoDB** — `waitlist`, `merge_events` collections

## What's implemented (2026-01)
- [x] AST merger CLI (Python + JS/TS, 15/15 pytest)
- [x] Real-world merge run: PEV5 ⇄ AHD → 4 files paired, 2 upgrades, 32 new blocks pulled in. Output committed under `/app/code_merger/demo_output/` and applied to `/app/backend/services/` + `/app/runtime/` (originals backed up as `.bak`)
- [x] Backend API (10 endpoints) wired to Mongo
- [x] React launch site: nav, hero w/ live cycle panel, stats, problem cards, agents showcase (6 cards from API), dashboard preview, engine playground, pricing (3 tiers), roadmap (5 quarters), FAQ, waitlist, footer
- [x] Dashboard preview pages: Overview (KPIs + Recharts area chart + approvals queue + agent grid), Agents, Approvals (approve/veto interactions), Revenue (range selector + chart), Content (table)
- [x] Next.js mirror at `/app/app/page.tsx` for production deploy
- [x] 30/30 backend + CLI tests, 100% functional frontend (testing agent iteration_2)

## Backlog (P1)
- Wire `POST /api/waitlist` from the Next.js launch (currently `mailto:` fallback in production page)
- Persist approve/veto decisions to Mongo and resync dashboard from API
- Connector registry UI (already exists in pev5 backend — `connectors/registry.yaml`)

## Backlog (P2)
- Pull-request bot mode: run the AST merger automatically on PRs and post a diff comment
- LLM-judge layer (Claude Sonnet 4.5 via Emergent Universal Key) as opt-in for blocks the AST merger flags as "ambiguous"
- Stripe checkout for Studio tier
- Audit log + SSO for Holding tier
- Mobile push approvals (Telegram or Pushover)

## Next tasks
1. (P1) Push `/app` to `quantam101/profitenginev5` so the new launch + dashboard land in production
2. (P1) Re-run `code_merger repo` weekly via GitHub Action to keep v5 in sync with already-here-dashboard
3. (P2) Land the PR-bot mode behind a feature flag

## Test ownership
- CLI: `cd /app && python -m pytest code_merger/tests/ -v` (15 tests)
- Backend: `cd /app && python -m pytest backend/tests/test_backend_api.py -v`
- E2E: `/app/test_reports/iteration_2.json` (last green run)
