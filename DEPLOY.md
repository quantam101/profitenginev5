# ProfitEngine v5 — Free-tier deployment runbook

Two‑service stack, $0/month forever:

| Layer | Host | Free tier | Why |
|---|---|---|---|
| **Frontend** (React) | **Vercel** | Hobby: unlimited static, 100GB bandwidth | Global CDN, zero config |
| **Backend** (FastAPI + WebSockets) | **Oracle Cloud Free** *or* **Koyeb** *or* **Render** | Permanent free VM | WebSockets supported, no cold starts on Oracle |
| **Database** (MongoDB) | **MongoDB Atlas M0** | 512MB shared, free forever | Managed, no infra |

---

## Step 1 — Database: MongoDB Atlas M0 (5 min)

1. Sign up at https://www.mongodb.com/cloud/atlas/register
2. Build a Database → **M0 (FREE)** → AWS → pick region closest to your backend host
3. **Database Access** → Add user (save password)
4. **Network Access** → Add IP: `0.0.0.0/0` (allow from anywhere; tighten later)
5. **Connect** → "Drivers" → copy the connection string:
   `mongodb+srv://USER:PASSWORD@cluster0.xxxx.mongodb.net/`
6. Append `/profitengine` to the URI. This is your `MONGO_URL`.

---

## Step 2 — Backend: pick ONE

### Option A — Oracle Cloud Always‑Free VM (recommended; most powerful)
Free forever: 4 Arm Ampere A1 cores + 24GB RAM. No credit card hold after sign-up.

```bash
# 1. Sign up: https://signup.cloud.oracle.com (Always Free tier)
# 2. Create a "Compute Instance"
#    - Shape: VM.Standard.A1.Flex (1 OCPU, 6GB — within free tier)
#    - OS: Canonical Ubuntu 22.04
#    - Networking: assign public IP, open ports 22, 80, 443, 8001
# 3. SSH in:
ssh ubuntu@<your-oracle-public-ip>

# 4. Install Docker + clone the repo:
sudo apt update && sudo apt install -y docker.io docker-compose-plugin git
sudo usermod -aG docker ubuntu && newgrp docker
git clone https://github.com/quantam101/profitenginev5.git && cd profitenginev5

# 5. Create backend/.env (paste your keys + Atlas MONGO_URL):
cat > backend/.env <<'EOF'
MONGO_URL=mongodb+srv://USER:PASS@cluster0.xxxx.mongodb.net/profitengine
DB_NAME=profitengine
GEMINI_API_KEY=AQ.Ab8RN6IS...
STRIPE_API_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
RESEND_API_KEY=re_...
DISTILLATION_CHEAP_PROVIDER=gemini
DISTILLATION_CHEAP_MODEL=gemini-2.5-flash
DISTILLATION_EXPENSIVE_PROVIDER=gemini
DISTILLATION_EXPENSIVE_MODEL=gemini-2.5-flash
DISTILLATION_CACHE_TTL_HOURS=168
COHORT_TOTAL_SEATS=100
COHORT_LABEL=Cohort 1
APP_PUBLIC_URL=https://profitengine.alreadyherellc.com
EOF

# 6. Run the backend:
docker build -t pev5-backend -f Dockerfile .
docker run -d --name pev5 --restart unless-stopped \
  -p 8001:8001 --env-file backend/.env pev5-backend

# 7. Set up an HTTPS reverse proxy with Caddy (auto SSL):
sudo apt install -y caddy
sudo tee /etc/caddy/Caddyfile <<EOF
api.YOURDOMAIN.com {
    reverse_proxy localhost:8001
}
EOF
sudo systemctl reload caddy
# point api.YOURDOMAIN.com DNS → your Oracle public IP
```

### Option B — Koyeb (one-click, sleeps after inactivity)
1. Sign up: https://app.koyeb.com (no credit card)
2. **Create App** → Docker → paste your GitHub repo URL
3. **Dockerfile path**: `Dockerfile`
4. **Port**: 8001 (HTTP)
5. **Health check**: `/api/health`
6. **Region**: `was` (Washington DC) or `fra` (Frankfurt)
7. **Instance**: Free
8. **Env vars**: copy from `koyeb.yaml` comments
9. Backend URL will be `https://<app-name>-<org>.koyeb.app`

### Option C — Render (simplest, sleeps after 15min idle)
1. Sign up: https://render.com (no credit card)
2. **New** → **Web Service** → connect GitHub → pick your repo
3. **Runtime**: Docker
4. **Health check path**: `/api/health`
5. **Plan**: Free
6. **Env**: paste the same env vars
7. Backend URL: `https://<service-name>.onrender.com`

---

## Step 3 — Frontend: Vercel (3 min)

1. Sign up: https://vercel.com (no credit card)
2. **Import Project** → GitHub → pick your repo
3. **Framework Preset**: Other
4. **Root Directory**: leave empty (the `vercel.json` at repo root handles it)
5. **Environment Variables**:
   - `REACT_APP_BACKEND_URL` = `https://api.YOURDOMAIN.com` (or your Koyeb/Render URL)
6. **Deploy**. Vercel gives you `https://profitenginev5.vercel.app`.
7. **Custom domain**: add `profitengine.yourdomain.com` → Vercel auto-issues SSL.

---

## Step 4 — Stripe webhook (production)

1. https://dashboard.stripe.com/webhooks → **Add endpoint**
2. URL: `https://api.YOURDOMAIN.com/api/webhook/stripe`
3. Events: `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`
4. Copy the **Signing secret** (`whsec_…`) → set as `STRIPE_WEBHOOK_SECRET` in your backend env
5. Restart the backend container/service to pick it up

---

## Step 5 — Verify the live stack

```bash
# Replace with your actual production URL:
BASE=https://api.YOURDOMAIN.com

curl -sS $BASE/api/health
curl -sS $BASE/api/launch/social-proof
curl -sS $BASE/api/agents | python3 -c "import sys,json;print(len(json.load(sys.stdin)),'agents')"
# Should print "20 agents"
```

Then open `https://profitengine.yourdomain.com` and click **Get early access** → checkout flow should redirect to a real Stripe checkout page on `checkout.stripe.com`.

---

## Costs at scale

| Tier | Stack | Monthly cost |
|---|---|---|
| **Free (0-1k MAU)** | Oracle + Atlas M0 + Vercel + Gemini free | $0 |
| **Growth (1-10k MAU)** | Oracle + Atlas M10 + Vercel + Gemini paid | ~$60 |
| **Scale (10-100k MAU)** | Multi-region Render Pro + Atlas M30 + Vercel Pro + GPT-4o | ~$400 |

The architecture is the same all the way up — just move from free to paid plans on each service as traffic grows.
