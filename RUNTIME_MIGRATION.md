# Runtime Migration: OCI → Render

The OCI server (129.146.236.177) is unreachable and the Oracle account is inaccessible.
This repo now ships a `render.yaml` blueprint that redeploys the Python runtime
(`Dockerfile.runtime`, `runtime/api.py`) on Render's free tier with auto-deploy on push to `main`.

## One-time setup (~5 minutes)

1. Go to https://render.com and sign up / log in with the `quantam101` GitHub account.
2. Click **New → Blueprint**, select the `quantam101/profitenginev5` repo, branch `main`.
   Render reads `render.yaml` and creates the `profitengine-runtime` web service.
3. In the service's **Environment** tab, fill in the secret env vars (same values as the
   GitHub Actions secrets): `MONGO_URL`, `GUMROAD_ACCESS_TOKEN`, `PRINTIFY_API_TOKEN`,
   `PRINTIFY_SHOP_ID`, `STRIPE_SECRET_KEY`, `PROFITENGINE_WEBHOOK_TOKEN`,
   `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `GROQ_API_KEY`, `GEMINI_API_KEY`,
   `ANTHROPIC_API_KEY`. Skip any you don't use — endpoints degrade gracefully.
4. Deploy. The service URL will look like `https://profitengine-runtime.onrender.com`.
   Verify: `curl https://profitengine-runtime.onrender.com/health`

## Repoint everything at the new runtime

1. **Vercel** (profitenginev5 project → Settings → Environment Variables, Production):
   set `RUNTIME_API_URL=https://profitengine-runtime.onrender.com`, then redeploy.
2. **DNS** (registrar for alreadyherellc.com): change `api.alreadyherellc.com` from the
   A record `129.146.236.177` to a CNAME → `profitengine-runtime.onrender.com`
   (add the custom domain in Render → Settings → Custom Domains first).
   `app.alreadyherellc.com` should point at the Vercel frontend instead of OCI.
3. **GitHub Actions**: workflows that call `http://129.146.236.177/...`
   (`daily-ops.yml`, `docker-guard.yml`, `eaos-pod-render.yml`) use the new
   base URL via the `RUNTIME_BASE`/hardcoded values — update after the Render URL exists.

## Notes / limits

- Render free tier spins down after 15 min idle; first request after idle takes ~30-60s.
  The scheduled GitHub Actions pings keep it warm during active hours.
- Cycle history (`CycleLog`) on OCI was stored on the instance volume and is lost;
  the new service starts with a fresh log.
- Heavy local-LLM (Ollama) and video-rendering jobs are NOT part of this service —
  they need a GPU/large VM and stay degraded until a replacement VM exists.
