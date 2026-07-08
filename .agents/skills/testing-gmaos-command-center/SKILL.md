---
name: testing-gmaos-command-center
description: Test the GMAOS Enterprise command center scaffold end-to-end. Use when verifying Next.js UI pages, Python EAOS runtime, or navigation after merging or updating the GMAOS scaffold.
---

# Testing GMAOS Command Center

## Prerequisites

- Node.js and npm installed
- Python 3.x with `pyyaml`, `pytest`, and `pip install -r backend/requirements.txt`
- Run `npm install` in the project root

## Shell Tests (run first, no browser needed)

### Python Runtime Smoke Test
```bash
python3 -m runtime.sovereign_core
```
Expect: exit code 0, output contains `status='ok'`

### Python Unit Tests
```bash
pytest tests/test_core.py -q
```
Expect: `20 passed`

Note: Both `pytest` and `python3 -m pytest` work. A root `conftest.py` adds the project root to sys.path.

### ESLint
```bash
npx eslint . --max-warnings=0
```
Expect: 0 errors, 0 warnings

### TypeScript
```bash
npx tsc --noEmit
```
Expect: 0 type errors

### Full Test Suite (mirrors CI)
```bash
npm run test:unit && npm run test:integration && npm run test:ai-gateway && npm run test:skill-gateway && npm run test:opportunity
```

### Security Scanner
```bash
python -c "from runtime.security_scanner import scan_repo; f=scan_repo('.'); print('PASS' if not f else f)"
```

## Middleware Testing (critical for SEO revenue)

The middleware (`middleware.ts`) controls bot access. Test via curl against the Vercel preview:

```bash
# Should get 200 (search crawlers allowed)
curl -sI -A "Mozilla/5.0 (compatible; Googlebot/2.1)" "$PREVIEW_URL/" | head -1

# Should get 200 (normal browsers)
curl -sI -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" "$PREVIEW_URL/" | head -1

# Should get 403 (scraping tools blocked)
curl -sI -A "curl/7.88.1" "$PREVIEW_URL/" | head -1
curl -sI -A "python-requests/2.31.0" "$PREVIEW_URL/" | head -1
```

Security headers to verify in responses:
- `x-content-type-options: nosniff`
- `x-frame-options: DENY`
- `permissions-policy: geolocation=(), microphone=(), camera=()`
- `referrer-policy: strict-origin-when-cross-origin`

## Vercel Preview URL Pattern

PR preview deploys follow:
```
profitenginev5-git-{branch-slug}-already-here-llc-s-projects.vercel.app
```
Check the Vercel bot comment on the PR for the exact URL.

## Browser UI Tests

### Start Dev Server (local)
```bash
npx next dev -p 3000
```
Wait for "Ready in Xms" message.

### Homepage (http://localhost:3000 or Vercel preview)
Verify:
- Tab title: "ProfitEngine v5"
- Heading: "Build proof. Sell the work. Then sell the engine."
- Profitability run panel with 6 agents (offer scout, margin guard, kdp guard, listing optimizer, traffic agent, proof ledger)
- 13 agent mesh cards visible on scroll
- Dark theme (black/green)

### Revenue APIs
- `/api/profitability` — returns JSON with `proof`, `storeLinks`, `rankedOffers`, `agents`
- `/api/kdp-revenue` — returns KDP publishing revenue data

### Command Center Pages
Pages exist at `/command-center/{slug}` (NOT at `/command-center` which returns 404):
- agents, modules, workflows, approvals, costs, security, logs, connectors, changelog

Verify:
- h1 heading matches page name
- "COMMAND CENTER" badge visible and links back to `/`
- Status badges (PASS/LOCKED/REVIEW) for each section item

## Sovereign Core Execution Test

Test that the inference cascade stub doesn't trigger the verifier:
```python
import os, sys
sys.path.insert(0, '.')
os.environ['GMAOS_AUDIT_LOG'] = '/tmp/test_audit.jsonl'
os.environ['GMAOS_APPROVAL_DB'] = '/tmp/test_approvals.json'
os.environ['GMAOS_VECTOR_CACHE'] = '/tmp/test_vector.sqlite3'
os.environ['GMAOS_EMBEDDING_DIM'] = '4'
from runtime.sovereign_core import SovereignAutomationCore
core = SovereignAutomationCore()
result = core.execute('system', 'context', 'Create a local draft', [0.1]*4)
assert result.status == 'ok'
assert result.route_tier == 'DETERMINISTIC_LOCAL'
assert 'API_KEY=' not in result.output
```

## Known Issues / Tips

- `/command-center` (index) returns 404 — only subpages with `[section]` slug work
- `/api/health` may have redirect loops on Vercel preview — this is a Vercel config issue
- The security scanner skips its own source files and `verifier.py` to avoid false positives
- The verifier blocks output containing secret-like patterns (e.g. private key headers, API key assignments, password fields) — ensure agent output doesn't contain these patterns
- When running multiple GMAOS repos simultaneously, use different ports
- Next.js may auto-modify `tsconfig.json` on first dev server start — expected, can be ignored
- `Caddyfile` and `docker-compose.yml` may reference `alreadyherellc.com` — update per project before deployment

## Devin Secrets Needed

No secrets required for basic testing. The sovereign core uses deterministic local fallback when no API keys are configured.

For full inference testing (optional):
- `GROQ_API_KEY` — Groq cloud inference
- `GEMINI_API_KEY` — Google Gemini
- `ANTHROPIC_API_KEY` — Claude
