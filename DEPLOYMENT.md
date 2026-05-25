# ProfitEngine v5 — Deployment & Global Packaging Guide

> **Zero-spend principle.** The system runs entirely on free infrastructure.
> Ollama handles all AI inference locally. Claude API is only invoked as an
> optional key-gated fallback. No paid adapters are enabled by default.

---

## Table of contents

1. [Prerequisites](#1-prerequisites)
2. [Quick start (OCI Always Free — recommended)](#2-quick-start-oci-always-free--recommended)
3. [Environment variables reference](#3-environment-variables-reference)
4. [First-run Ollama model setup](#4-first-run-ollama-model-setup)
5. [DNS & HTTPS with Caddy](#5-dns--https-with-caddy)
6. [Verifying the system is working (proof of work)](#6-verifying-proof-of-work)
7. [Going global — packaging for distribution](#7-going-global--packaging-for-distribution)
8. [Scaling beyond one server](#8-scaling-beyond-one-server)
9. [Upgrading](#9-upgrading)
10. [Security checklist](#10-security-checklist)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. Prerequisites

| Requirement | Minimum | Recommended |
|---|---|---|
| OS | Ubuntu 22.04 LTS | Ubuntu 24.04 LTS |
| RAM | 8 GB | 24 GB (OCI A1 ARM) |
| CPU | 2 cores | 4 OCPUs (ARM Ampere A1) |
| Storage | 50 GB | 100 GB block volume |
| Docker | 24+ | latest |
| Docker Compose | 2.20+ | latest |
| Open ports | 22, 80, 443 | same |
| Domain | Required for HTTPS | any registrar |

**Install Docker on Ubuntu:**
```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
```

---

## 2. Quick start (OCI Always Free — recommended)

OCI Always Free gives you 4 ARM OCPUs + 24 GB RAM + 200 GB storage at **$0/month**.
This is the reference deployment target.

```bash
# 1. Clone the repo
git clone https://github.com/quantam101/profitenginev5.git
cd profitenginev5

# 2. Configure environment
cp .env.example .env
nano .env          # fill in SITE_DOMAIN, POSTGRES_*, N8N_*, etc.

# 3. Set your Anthropic key on the server (optional — system works without it)
echo "ANTHROPIC_API_KEY=sk-ant-..." >> .env   # never commit this file

# 4. Deploy (builds images, starts all services, pulls Ollama model)
bash scripts/deploy.sh

# 5. Verify everything is healthy
curl -s http://localhost:8080/health | python3 -m json.tool
curl -s http://localhost:8080/metrics | python3 -m json.tool
```

**Expected output after first run:**
```json
{ "ok": true, "service": "profitengine-runtime", "mode": "strict_zero_spend" }
```

---

## 3. Environment variables reference

Copy `.env.example` to `.env` and fill in the values below.
**Never commit `.env` to git** — it is in `.gitignore`.

| Variable | Required | Default | Description |
|---|---|---|---|
| `SITE_DOMAIN` | ✅ | — | Root domain, e.g. `profitengine.alreadyherellc.com` |
| `ACME_EMAIL` | ✅ | — | Email for Let's Encrypt certificates |
| `POSTGRES_DB` | ✅ | — | Database name |
| `POSTGRES_USER` | ✅ | — | Database user |
| `POSTGRES_PASSWORD` | ✅ | — | Database password (use a strong random value) |
| `N8N_BASIC_AUTH_USER` | ✅ | — | n8n admin username |
| `N8N_BASIC_AUTH_PASSWORD` | ✅ | — | n8n admin password |
| `ANTHROPIC_API_KEY` | ⬜ | — | Optional Claude API key (set on server only) |
| `GMAOS_LOCAL_MODEL_ENABLED` | ⬜ | `true` | Enable Ollama local inference |
| `GMAOS_LOCAL_MODEL_NAME` | ⬜ | `llama3.1:8b` | Ollama model to use |
| `GMAOS_LOCAL_MODEL_ENDPOINT` | ⬜ | `http://ollama:11434` | Ollama service URL |
| `GMAOS_LOCAL_MODEL_TIMEOUT` | ⬜ | `120` | Ollama request timeout (seconds) |
| `GMAOS_THRESH_DETERMINISTIC` | ⬜ | `0.25` | Complexity score below which tasks are deterministic |
| `GMAOS_THRESH_LOCAL_MODEL` | ⬜ | `0.70` | Below this → Ollama; above → Claude/human |
| `GMAOS_THRESH_CLAUDE` | ⬜ | `0.90` | Below this (if key set) → Claude; above → human queue |
| `GMAOS_CYCLE_LOG` | ⬜ | `./data/logs/cycles.jsonl` | Execution ledger path |

---

## 4. First-run Ollama model setup

The Ollama service starts automatically but the model must be pulled once:

```bash
# Default — best all-round (4.7 GB, ~15-30 tok/s on OCI A1 ARM)
docker compose exec ollama ollama pull llama3.1:8b

# Alternatives by use-case:
docker compose exec ollama ollama pull qwen2.5:7b    # SEO / multilingual content
docker compose exec ollama ollama pull phi3.5:3.8b   # fastest for short structured tasks

# Check what's downloaded
docker compose exec ollama ollama list
```

After the pull the inference cascade activates automatically on the next execution.

---

## 5. DNS & HTTPS with Caddy

Point your DNS records to your server IP **before** running the deploy script.
Caddy handles TLS automatically via Let's Encrypt.

Required DNS records — A records pointing to `129.146.167.73`:

| Subdomain | Points to | Purpose |
|---|---|---|
| `profitengine.alreadyherellc.com` | `129.146.167.73` | Marketing site |
| `app.profitengine.alreadyherellc.com` | `129.146.167.73` | Command center (Next.js) |
| `api.profitengine.alreadyherellc.com` | `129.146.167.73` | Runtime API (FastAPI) |
| `status.profitengine.alreadyherellc.com` | `129.146.167.73` | Uptime Kuma monitoring |

n8n is NOT publicly exposed by default (security policy). Enable it in the Caddyfile
only after verifying `N8N_BASIC_AUTH_ACTIVE=true` is set.

---

## 6. Verifying proof of work

### Check the execution ledger

Every time an agent runs it writes a record to the cycle log:

```bash
# Recent executions
curl -s http://localhost:8080/cycles?limit=10 | python3 -m json.tool

# Aggregate stats
curl -s http://localhost:8080/metrics | python3 -m json.tool
```

Example metrics response:
```json
{
  "total_cycles": 47,
  "successful_cycles": 45,
  "success_rate_pct": 95.7,
  "avg_duration_ms": 3420,
  "tier_distribution": {
    "DETERMINISTIC_LOCAL": 12,
    "LOCAL_MODEL": 28,
    "CLAUDE_API": 5
  },
  "agent_distribution": {
    "sovereign-orchestrator": 30,
    "local-research": 12,
    "lifelong-catch-correct": 5
  },
  "last_cycle_iso": "2026-01-15T08:23:11Z"
}
```

### Trigger a test run

```bash
curl -s -X POST http://localhost:8080/execute \
  -H "Content-Type: application/json" \
  -d '{
    "objective": "Run a local profit cycle health check",
    "agent_id": "sovereign-orchestrator"
  }' | python3 -m json.tool
```

### Check the dashboard

Visit `https://app.<your-domain>` — the dashboard now shows live data from
the execution ledger: total cycles, success rate, tier distribution, and an
activity feed of recent runs.

### Audit log

All actions are also recorded in the full audit log:
```bash
docker compose exec runtime tail -f /data/audit.jsonl
```

---

## 7. Going global — packaging for distribution

### Option A: Docker images from GHCR (easiest for others)

When you push a version tag, the release workflow automatically builds
multi-arch images (amd64 + arm64) and publishes them to GHCR:

```bash
git tag v0.2.0
git push --tags
```

Recipients can then run the full stack with just Docker:

```bash
# They only need docker-compose.yml + .env
curl -O https://raw.githubusercontent.com/<org>/profitenginev5/main/docker-compose.yml
curl -O https://raw.githubusercontent.com/<org>/profitenginev5/main/.env.example
cp .env.example .env
# edit .env, then:
docker compose pull   # pulls published images from GHCR
docker compose up -d
```

Add this to `docker-compose.yml` for image-based deployment (production):
```yaml
# Replace 'build: ...' blocks with pre-built image references:
web:
  image: ghcr.io/<org>/profitenginev5-web:latest
runtime:
  image: ghcr.io/<org>/profitenginev5-runtime:latest
```

### Option B: Fork and deploy anywhere

Any VPS with 8+ GB RAM and Docker works:
- **DigitalOcean**: $48/mo (8 GB Droplet)
- **Hetzner**: €8/mo (8 GB CX31) — best price/performance in EU
- **Linode/Akamai**: $48/mo
- **AWS EC2 t4g.xlarge (ARM)**: ~$100/mo
- **OCI Always Free**: $0/mo ← what this repo runs on

All that changes is the server IP in your DNS records.

### Option C: Kubernetes (at scale)

The Docker images are multi-arch and stateless (state is in volumes).
A `helm/` chart is a natural next step when you need >1 replica.
See `docs/AGENT_ROADMAP.md` for the future agents roadmap.

---

## 8. Scaling beyond one server

The current architecture is intentionally single-node to stay on OCI Free.
When you're ready to scale:

| Component | Scale strategy |
|---|---|
| Next.js web | Vercel or multiple replicas behind a load balancer |
| FastAPI runtime | Add replicas; put Postgres behind PgBouncer |
| Ollama | Each node gets its own Ollama — no shared GPU needed on ARM CPU |
| n8n | n8n Enterprise or self-hosted queue mode |
| Postgres | Managed Postgres (Supabase, Neon, RDS) when DB load grows |

---

## 9. Upgrading

```bash
# Pull latest code
git pull --ff-only

# Rebuild and restart with zero-downtime (compose handles rolling restarts)
bash scripts/deploy.sh --pull

# Or with a full image rebuild (after Dockerfile changes):
bash scripts/deploy.sh --pull --fresh
```

Data volumes (`postgres_data`, `gmaos_data`, `n8n_data`, `ollama_data`) are
preserved across upgrades.

---

## 10. Security checklist

Before going live, verify each item:

- [ ] `.env` is **not** committed to git (`git status` should not show it)
- [ ] `ANTHROPIC_API_KEY` is set only in server `.env`, never in source
- [ ] `POSTGRES_PASSWORD` is a random 32+ character string
- [ ] `N8N_BASIC_AUTH_PASSWORD` is a random 32+ character string
- [ ] Only ports 22, 80, 443 are open in your firewall / OCI Security List
- [ ] n8n is NOT publicly exposed (Caddy n8n block is commented out)
- [ ] `npm run ci:all` passes (includes `npm run security:scan`)
- [ ] `node scripts/agent-healthcheck.mjs` returns `ok: true`
- [ ] Caddy is serving HTTPS (green lock in browser)
- [ ] Health endpoint returns `ok: true`: `curl -s https://api.<domain>/health`

---

## 11. Troubleshooting

**Runtime won't start:**
```bash
docker compose logs runtime
```
Common causes: missing `.env` values, Python dependency error, port conflict.

**Ollama inference is slow:**
This is expected on CPU — llama3.1:8b generates ~15-30 tok/s on OCI A1 ARM.
For short structured tasks, switch to phi3.5:3.8b (~45-60 tok/s).

**Health score below 100%:**
```bash
node scripts/agent-healthcheck.mjs
```
The output will name the failing check. Common fixes:
- `config`: check `eaos.config.yaml` `mode: strict_zero_spend` and `max_cost_usd: 0`
- `security`: check for accidentally committed secrets
- `docker`: `Dockerfile.web` must use `node:20-alpine`

**n8n workflows not triggering:**
n8n is on the internal Docker network. Trigger workflows from inside the
runtime container or via the n8n UI at `https://n8n.<domain>` (after enabling
the Caddy block and confirming auth is set).

**Postgres connection refused:**
```bash
docker compose ps postgres
docker compose logs postgres
```
Ensure `POSTGRES_PASSWORD` is set and non-empty in `.env`.

---

*Built on OCI Always Free ARM · Zero-spend AI runtime · Runs globally on any VPS*
