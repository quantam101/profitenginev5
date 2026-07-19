# ProfitEngine v5 — Project Rules

## NO-PLACEHOLDER RULE (PRODUCTION-BLOCKING)

**Placeholders are forbidden everywhere, permanently.**

Before marking ANY task complete, audit and fix every instance of:
- `your-profitengine-domain.com`, `YOUR_*`, `<replace-me>`, `<token>`, `<generated-token>`
- `<runtime-url>`, `example.com`, `localhost` in production config
- `TODO: set later`, `mock`, `dummy`, `sample`, `test-token`
- Fake domains, fake API keys, fake webhook secrets, preview URLs used as production URLs

### Audit Checklist (required before completion)
1. Full text search both `profitenginev5` and `already-here-llc` repos
2. Vercel Production env vars for both projects
3. Vercel Production domains and deployment URLs
4. GitHub Actions / workflow files
5. README / docs / handoff notes
6. Smoke-test commands and scripts
7. Deployment config and runtime config

### Acceptance Criteria
- No placeholder values in production code or config
- `PROFITENGINE_URL` → real deployed production URL
- `PROFITENGINE_WEBHOOK_TOKEN` → real rotated token, matches both projects
- `RUNTIME_API_URL` → real runtime service URL
- Production smoke tests run with real values only

### Final Status Must Be
```
PASS — all real production values configured and live tests passed.
BLOCKED — real value missing or production verification failed.
```
No partial "looks good" status is acceptable.

---

## Architecture

- **Frontend/API**: Next.js 14 on Vercel → production URL `app.alreadyherellc.com` (Vercel project `profitenginev5`; note: non-browser user agents get a 403 from the bot filter — use a browser UA when smoke-testing)
- **Runtime**: hosted on Render (OCI box `129.146.236.177` is DEAD — decommissioned 2026-07-12; never target it)
- **Content**: GitHub Pages (`quantam101/content` repo, Jekyll) → served at `www.alreadyherellc.com/content/*`; posts live in `_posts/` (NOT `posts/` — files outside `_posts` don't appear in the feed or blog index)
- **CI/CD**: GitHub Actions → auto-deploy on push to `main`
- **Content pipeline**: GitHub Actions cron `07:05 UTC` daily (`daily-content.yml`; publishes at most one post per day — `FORCE_PUBLISH=true` overrides)

## Key Constraints
- `max_cost_usd: 0` — no paid LLM calls allowed
- `paid_adapters_enabled: false` — enforced by health check
- Security scan must pass (`npm run security:scan`) before every commit
- All 34 tests must pass (`npm test`)
- No secrets in repo — keys live in server `.env` and GitHub Secrets only

## Content & Monetization
- Amazon Associates tag: `alreadyhere-20` (hardcoded default)
- GitHub content owner: `quantam101`, repo: `content`
- FTC disclosure auto-injected in every published post
- Affiliate links injected via `AFFILIATE_LINKS` env var (JSON map)

## Server Access
- The OCI server (`opc@129.146.236.177`) is permanently dead as of 2026-07-12 — do not SSH, deploy, or health-check against it. Customer-facing services run on Vercel + Render.

## Context Mesh Engine — Token Optimization Rules

### Symbol Extraction (90% token reduction)
When analyzing code, use the `dispatch_parallel_context` MCP tool instead of reading full files.
```
Tool: dispatch_parallel_context
Args: { repoPath: "<path>", symbolIdentifier: "<function/class name>", lang: "auto" }
```

### Search Tools (use in order)
| Task | Tool |
|------|------|
| Find symbol across repo | `dispatch_parallel_context` |
| High-volume code grep | `rg --smart-case` |
| File structure mapping | `fd --type f` |
| JSON filtering | `jq -c -r` |

### Context Rules
- Small files (<50 lines): read directly — no overhead
- Large files (>200 lines): use `dispatch_parallel_context` to extract the specific symbol
- Config/YAML/JSON files: read directly — AST not applicable
- Full file reads allowed for: package.json, pyproject.toml, docker-compose.yml, .env.example
