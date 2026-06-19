# Deploying ProfitEngine v5 outside [removed]

This codebase is **fully portable**. The integrations layer auto-detects
your credentials and picks the right transport — no code changes needed
to go from [removed] preview → production hosting.

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

| Concern | Local | Production |
|---------|-------|-----------|
| LLM     | `ANTHROPIC_API_KEY` + `GEMINI_API_KEY` | Same (use production keys) |
| Stripe  | `STRIPE_API_KEY=sk_test_...` | `STRIPE_API_KEY=sk_live_...` |
| Mongo   | Docker Compose (local) | MongoDB Atlas / Neon |
| Hosting | localhost | Vercel (frontend) + OCI (backend) |

The Distiller (`backend/services/llm_provider.py`) and Stripe transport
(`backend/services/stripe_transport.py`) detect which set of keys you
have and route accordingly. **Same code, both worlds.**

## Hosting options

### Vercel + OCI (production-ready)
- **Frontend** → Vercel: import the GitHub repo, auto-deploys on `main` push
- **Backend** → OCI Always Free E2.1.Micro: Go + SQLite + Caddy via Docker Compose
- **Database** → SQLite (local) + Litestream backup, or MongoDB Atlas for scale
- **DNS:** point apex/`www` to Vercel, point `api.yourdomain.com` to OCI (129.146.236.177)

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

Vercel: one-click rollback via dashboard. OCI: Litestream snapshots for database rollback.

## What doesn't work off-[removed]

- The `[removed] universal key only works inside the [removed] pod
  → replace with `ANTHROPIC_API_KEY` + `GEMINI_API_KEY` (already supported
  by the abstraction; just provide the keys).
- The `*.preview.[removed] URL — you'll point your own domain instead.
- [removed]'s secret injection — use your hosting provider's secret manager.

Everything else (FastAPI + React + MongoDB + the 20-agent fleet + Cash AI
+ Distillation + Stripe Checkout + Launch kit) is platform-agnostic.
