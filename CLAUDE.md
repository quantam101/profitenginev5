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

- **Frontend/API**: Next.js 14 on Vercel → `profitengine-tau.vercel.app`
- **Runtime**: Python FastAPI (Docker) on OCI `129.146.167.73`
- **Content**: GitHub Pages → `quantam101.github.io/content`
- **CI/CD**: GitHub Actions → auto-deploy on push to `main`
- **Content pipeline**: GitHub Actions cron `07:05 UTC` daily

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
- OCI server: `ubuntu@129.146.167.73`
- Deploy key (public): `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIF5IOnsqRDtbUYu5WQfLaAjAQmc+zKrlK6TDafDgO0Ij profitengine-deploy@github-actions`
- Add via OCI Console → Instance → Edit → SSH keys
