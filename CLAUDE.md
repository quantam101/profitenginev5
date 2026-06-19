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

## RAILWAY PERMANENTLY DISABLED

**Railway deployment is forbidden and cannot be re-enabled.**

### Why
- Railway's free tier is outdated and unmaintained
- Single-platform vendor lock-in defeats the multi-cloud strategy
- OCI Always Free VM + Vercel provides zero-cost HA without external dependency

### Enforcement
- ✅ All Railway config files deleted (`railway.json`, `railway.toml`, `deploy/railway.json`)
- ✅ All Railway documentation deleted (`RAILWAY_SETUP_GUIDE.md`, `ARCHITECTURE_HA_FAILOVER.md`)
- ✅ Vercel build trigger regex purged of `railway.toml` checks
- ✅ Zero Railway environment variables
- ✅ Zero Railway API keys in GitHub Secrets

### If You See Railway References
They are **only in git history**. Do NOT:
- Re-add Railway config files
- Create `railway.toml` or `railway.json`
- Use Railway as a failover target
- Set `RAILWAY_API_KEY` or similar secrets

**Action:** Delete the file immediately. File a GitHub issue if found in active code.

---

## Architecture

- **Frontend**: Next.js 15 on Vercel → `profitengine-tau.vercel.app`
- **Backend**: Go + SQLite on OCI Always Free (`cmdos` at `129.146.236.177`)
- **Content**: GitHub Pages → `quantam101.github.io/content`
- **CI/CD**: GitHub Actions → auto-deploy on push to `main`
- **Failover**: OCI is primary; Vercel handles frontend-only if backend unreachable

## Key Constraints
- `max_cost_usd: 0` — no paid LLM calls allowed
- `paid_adapters_enabled: false` — enforced by health check
- Security scan must pass (`npm run security:scan`) before every commit
- All tests must pass (`npm test`)
- No secrets in repo — keys live in server `.env` and GitHub Secrets only

## Content & Monetization
- Amazon Associates tag: `alreadyhere-20` (hardcoded default)
- GitHub content owner: `quantam101`, repo: `content`
- FTC disclosure auto-injected in every published post
- Affiliate links injected via `AFFILIATE_LINKS` env var (JSON map)

## Server Access
- OCI server: `opc@129.146.236.177` — `cmdos` (Always Free E2.1.Micro, Oracle Linux)
- Deploy key (public): `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIF5IOnsqRDtbUYu5WQfLaAjAQmc+zKrlK6TDafDgO0Ij profitengine-deploy@github-actions`
- Add via OCI Console → Instance (`cmdos`) → Edit → SSH keys → Add public key

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
