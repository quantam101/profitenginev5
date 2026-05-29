# Deploying ProfitEngine v5 outside Emergent

This codebase is **fully portable**. The integrations layer auto-detects
your credentials and picks the right transport — no code changes needed
to go from Emergent preview → production hosting.

## Quick start (Docker, anywhere)

```bash
git clone https://github.com/quantam101/profitenginev5.git
cd profitenginev5
cp .env.pev5.example backend/.env
# Edit backend/.env with your real keys (Stripe, Anthropic, Gemini)
docker compose -f docker-compose.pev5.yml up -d
```

The stack comes up at:
- Frontend → http://localhost:3000
- Backend  → http://localhost:8001
- MongoDB  → mongodb://localhost:27017

## Provider migration matrix

| Concern | On-Emergent | Off-Emergent |
|---------|-------------|--------------|
| LLM     | `EMERGENT_LLM_KEY` | `ANTHROPIC_API_KEY` + `GEMINI_API_KEY` |
| Stripe  | `STRIPE_API_KEY=sk_test_emergent` | `STRIPE_API_KEY=sk_live_...` |
| Mongo   | Pod-local | Mongo Atlas / Railway plugin / RDS |
| Hosting | `*.preview.emergentagent.com` | Your domain |

The Distiller (`backend/services/llm_provider.py`) and Stripe transport
(`backend/services/stripe_transport.py`) detect which set of keys you
have and route accordingly. **Same code, both worlds.**

## Hosting options

### Railway (easiest — full stack on one platform)
1. New project → **Deploy from GitHub** → pick `quantam101/profitenginev5`
2. Add the **MongoDB plugin** → copy the `MONGO_URL` into the service env
3. Set the env vars from `.env.example` (Stripe + Anthropic + Gemini)
4. Healthcheck path is `/api/health` (already configured in `railway.toml`)
5. Repeat for `Dockerfile.frontend` as a second service

### Vercel + Railway (recommended for production)
- **Frontend** → Vercel: import the GitHub repo, set root dir to `frontend`, `REACT_APP_BACKEND_URL` = your Railway backend URL
- **Backend**  → Railway: deploys via `Dockerfile`, add Mongo plugin
- DNS: point apex/`www` to Vercel, point `api.yourdomain.com` to Railway

### AWS / GCP (enterprise scale)
- Backend: ECS Fargate / Cloud Run (FastAPI Docker image)
- Frontend: S3 + CloudFront / Cloud Storage + CDN
- Mongo: DocumentDB / Atlas on the same VPC
- Secrets: AWS Secrets Manager / GCP Secret Manager → injected as env vars

## Stripe live-mode checklist

1. Get keys from https://dashboard.stripe.com/apikeys
   - **Secret key** (`sk_live_...`) → backend env `STRIPE_API_KEY`
   - Publishable key (`pk_live_...`) → only needed if you add Stripe Elements
2. Add webhook endpoint at https://dashboard.stripe.com/webhooks
   - URL: `https://yourdomain.com/api/webhook/stripe`
   - Events: `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`
   - Copy the signing secret → backend env `STRIPE_WEBHOOK_SECRET`
3. Test a $0.50 live purchase → verify `subscriptions` collection grows

## Deployment gate

Before every production deploy, run:

```bash
cd frontend && yarn verify    # lint + env-check + test + build
cd .. && python -m pytest     # 100+ backend tests
```

CI (`.github/workflows/ci.yml`) runs the same gate on every PR.

## Rolling back

Each deploy is immutable in Railway/Vercel — one-click rollback to any
previous build. Mongo: take a snapshot before schema changes (`mongodump`).

## What doesn't work off-Emergent

- The `EMERGENT_LLM_KEY` universal key only works inside the Emergent pod
  → replace with `ANTHROPIC_API_KEY` + `GEMINI_API_KEY` (already supported
  by the abstraction; just provide the keys).
- The `*.preview.emergentagent.com` URL — you'll point your own domain instead.
- Emergent's secret injection — use your hosting provider's secret manager.

Everything else (FastAPI + React + MongoDB + the 20-agent fleet + Cash AI
+ Distillation + Stripe Checkout + Launch kit) is platform-agnostic.
