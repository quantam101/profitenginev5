---
name: testing-profitengine-v5
description: End-to-end testing checklist for the ProfitEngine v5 Vercel preview, including dashboard, command-center, runtime API routes, and Vercel env verification.
---

# Testing ProfitEngine v5 Previews

## Devin Secrets Needed

- `VERCEL_TOKEN` – to inspect project environment variables and preview deployments.
- `RENDER_API_KEY` – to verify the live Render runtime service exists and is reachable.
- `GITHUB_TOKEN` – optional, for verifying the `quantam101/content` `_posts` feed.

## What to check

1. **Landing page (`/`)**
   - HTTP 200, `<title>` contains `ProfitEngine v5`.
   - Hero text: `Build proof. Sell the work. Then sell the engine.`
   - 13-agent mesh visible below the fold.

2. **Dashboard (`/dashboard`)**
   - Page must return HTTP 200 and render the Operations/Revenue/Streams tabs.
   - Live indicator (`● LIVE` or `◌ DEMO`) visible in the header.
   - Data comes from `/api/data` on the client; the page itself is pre-rendered.

3. **Command center**
   - `/command-center` should redirect to `/command-center/agents` (or another default slug).
   - `/command-center/agents` (or any valid slug) returns HTTP 200 and shows the `COMMAND CENTER` badge.

4. **API endpoints**
   - `/api/health` → 200, `ok: true`, `healthScore: 100`.
   - `/api/data` → 200, `_source` can be `oracle_live` or `github_only` depending on runtime availability.
   - `/api/dashboard` → 200 with live data, or a sensible `502 runtime_unreachable` if the Render runtime is cold/unreachable.
   - `/api/command` (POST `{"command":"Run Cycle"}`) → 200 and should not reference `runtime:8080` or `localhost`.

5. **Vercel bot filter**
   - Non-browser UAs (`curl/7.88.1`, `python-requests/2.31.0`) get `403`.
   - Browser UA (`Mozilla/5.0 ... Chrome/...`) gets `200`.

## Common blockers

- **Stale `RUNTIME_API_URL` / `PROFITENGINE_URL`**: Vercel environment variables override the new Render fallback defaults. If `/api/dashboard` or `/api/run-cycle` time out with `runtime_unreachable` or `fetch failed`, inspect the Preview environment variables with `npx vercel env ls` and update them for the Preview target only.
- **Command center root 404**: if `/command-center` returns 404, add `app/command-center/page.tsx` with a `redirect('/command-center/agents')` or update landing/footer links to the slug route.
- **Runtime cold start**: Render web services can take 5–15 s to wake. `/api/dashboard` has a 5 s timeout, so expect `502` on cold starts. `/api/data` falls back to GitHub stats and still returns 200.

## Quick verification script

```bash
PREVIEW="https://profitenginev5-git-<branch>-already-here-llc-s-projects.vercel.app"
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

curl -s -A "$UA" "$PREVIEW/api/health" | jq .
curl -s -A "$UA" "$PREVIEW/api/data" | jq .
curl -s -X POST -A "$UA" -H 'Content-Type: application/json' -d '{"command":"Run Cycle"}' "$PREVIEW/api/command"
curl -sI -A "curl/7.88.1" "$PREVIEW/" | head -1
```

## Notes

- Vercel preview deployments are immutable. Updating environment variables does **not** affect an already-deployed preview; redeploy the branch to apply env changes.
- The `Run Cycle` button in `/dashboard` posts to `/api/command`, which in turn calls `/api/run-cycle`. Both routes must point to the live Render URL, not to `http://runtime:8080`/`localhost`.
