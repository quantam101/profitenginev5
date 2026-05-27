# ProfitEngine v5 — Master Reference Document
**Last updated:** 2026-05-27 (Session 5)

---

## 🚨 URGENT: Server SSH Access Broken (deploy pipeline down)

**Status:** CI/CD tests pass ✅ — Deploy fails ❌ (server `authorized_keys` lost the deploy key)

### Fix — Option A: OCI Console → Edit SSH Keys (easiest, web UI)

1. Go to https://cloud.oracle.com → Compute → Instances → **profitengine-server**
2. Click **Edit** (top right)
3. Scroll to **SSH keys** section → **Add SSH public key**
4. Paste the key below and save:

```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJujLyE+xXWJn4cJ9bVTeLmWb2qzUWfTLjnd10GdNGKt profitengine-deploy@github-actions
```

5. After saving, trigger a deploy (see "Re-trigger deploy" below)

### Fix — Option B: OCI Run Command (Cloud Shell)

Paste this into OCI Cloud Shell (https://cloud.oracle.com → Cloud Shell icon):

```bash
COMP_ID="ocid1.tenancy.oc1..aaaaaaaay5qjgld6vs42ttb7lcdiof4tg767u4fojkqjidlglbvdzy4yiqaa"
INST_ID="ocid1.instance.oc1.phx.anyhqljsmvp52oyc4e4u537ie7faz2spvhfzciy2uyx53zmj3azzueccp7aq"

cat > /tmp/add_key.sh << 'SCRIPT'
#!/bin/bash
mkdir -p /home/opc/.ssh && chmod 700 /home/opc/.ssh
touch /home/opc/.ssh/authorized_keys && chmod 600 /home/opc/.ssh/authorized_keys
PUBKEY="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJujLyE+xXWJn4cJ9bVTeLmWb2qzUWfTLjnd10GdNGKt profitengine-deploy@github-actions"
grep -qF "AAAAC3NzaC1lZDI1NTE5AAAAIJujLyE" /home/opc/.ssh/authorized_keys || \
  echo "$PUBKEY" >> /home/opc/.ssh/authorized_keys
chown -R opc:opc /home/opc/.ssh
echo "DONE: $(cat /home/opc/.ssh/authorized_keys | tail -1)"
SCRIPT

B64=$(base64 -w0 /tmp/add_key.sh)
oci instance-agent command create \
  --compartment-id "$COMP_ID" \
  --instance-id   "$INST_ID" \
  --os-type LINUX \
  --execution-time-out-in-seconds 60 \
  --content "{\"source\":{\"sourceType\":\"TEXT\",\"text\":\"$B64\"}}"
```

### Re-trigger deploy (after key is added)

```powershell
# PowerShell
$env:GH_TOKEN = "gho_..."   # from your password manager
& "C:\Program Files\GitHub CLI\gh.exe" workflow run deploy.yml --repo quantam101/profitenginev5
& "C:\Program Files\GitHub CLI\gh.exe" run watch --repo quantam101/profitenginev5
```

Or via curl:
```bash
curl -s -X POST \
  -H "Authorization: token $GH_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/quantam101/profitenginev5/actions/workflows/deploy.yml/dispatches \
  -d '{"ref":"main"}'
```

### Update SERVER_SSH_KEY secret (if needed)

The `set-secret-ed25519.mjs` script is ready at `C:\Users\alrea\set-secret-ed25519.mjs`.

```powershell
cd "C:\Users\alrea\profitenginev5"
npm install tweetsodium --no-save
$env:GH_TOKEN = "gho_..."
node "C:\Users\alrea\set-secret-ed25519.mjs"
# Should print: Status: 204   SUCCESS — SERVER_SSH_KEY updated
```

### If the key breaks again (generate new one)

```powershell
# 1. Generate new ED25519 key in WSL
wsl bash -c "ssh-keygen -t ed25519 -C 'profitengine-deploy@github-actions' -f /tmp/new_deploy -N '' && cp /tmp/new_deploy /mnt/c/Users/alrea/profitengine-ed25519 && cp /tmp/new_deploy.pub /mnt/c/Users/alrea/profitengine-ed25519.pub"
# 2. Update GitHub secret
cd C:\Users\alrea\profitenginev5
npm install tweetsodium --no-save
$env:GH_TOKEN = "gho_..."
node "C:\Users\alrea\set-secret-ed25519.mjs"
```

---

## Project Overview

**ProfitEngine v5** — Autonomous AI content monetization platform.

| Component | Technology | Location |
|-----------|-----------|---------|
| Dashboard / Frontend | Next.js 14 + Tailwind | Vercel (quantam101/profitenginev5) |
| AI Runtime / API | Python FastAPI | OCI server :8080 |
| Orchestration | n8n workflows | Docker container :5678 |
| Database | PostgreSQL 15 | Docker container :5432 |
| Local LLM | Ollama (llama3.1:8b) | Docker container :11434 |
| Proxy / TLS | Caddy v2 | Docker container :80/:443 |
| Cycle store | Upstash Redis | External (free tier) |

**Inference cascade (cheapest-first):**
1. Ollama local — free, on-device, llama3.1:8b
2. Groq Cloud — free tier, 700+ tok/s, llama-3.3-70b-versatile
3. Gemini Flash — free tier, 1M context
4. Claude API — paid fallback (key-gated)
5. Deterministic stub — never returns None

**Cost constraint:** `max_cost_usd: 0`, `paid_adapters_enabled: false` — enforced in health check.

---

## SSH Access

```bash
# Direct SSH (when authorized_keys is healthy)
ssh -i C:\Users\alrea\profitengine-ed25519 opc@129.146.167.73

# Deploy key fingerprint
SHA256:lEzI1h1lTjWqNqjJmtO2WQQ8l/D09oAqFzOyeVPAhLM

# Deploy public key
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJujLyE+xXWJn4cJ9bVTeLmWb2qzUWfTLjnd10GdNGKt profitengine-deploy@github-actions
```

**Private key files:**
- `C:\Users\alrea\profitengine-ed25519` (private)
- `C:\Users\alrea\profitengine-ed25519.pub` (public)

---

## Live Infrastructure

```
OCI Server:        129.146.167.73  (opc@, Oracle Linux 9.7, us-phoenix-1)
Dashboard:         http://129.146.167.73:3000
Runtime API:       http://129.146.167.73:8080/health

Docker containers:
  profitenginev5-web-1       Next.js    :3000
  profitenginev5-runtime-1   FastAPI    :8080 (healthy)
  profitenginev5-caddy-1     Caddy      :80/:443
  profitenginev5-n8n-1       n8n        :5678 (Docker-internal only)
  profitenginev5-ollama-1    Ollama     :11434
  profitenginev5-postgres-1  Postgres   :5432
```

---

## n8n Workflows

```
URL:       http://172.18.0.3:5678  (Docker-internal — expose via Caddy if needed)
Login:     admin@alreadyherellc.com / ProfitEngine2026!

Active workflows:
  ProfitEngine — Daily Content Pipeline
    ID: 6f8691a2-0688-4dae-80bd-8cac8c2a61f5   active: true
  ProfitEngine — Blog Cross-post Webhook
    ID: 409ed6db-db7d-4778-b009-5895ef332def   active: true
```

---

## GitHub CI/CD

```
Repo:     quantam101/profitenginev5
Branch:   main
Token:    stored in password manager (GH_TOKEN env var)
CLI:      C:\Program Files\GitHub CLI\gh.exe

Workflows:
  ci.yml            — runs on every push; pytest (68 tests)
  deploy.yml        — push to main or workflow_dispatch; SSH deploy to OCI
  daily-content.yml — cron daily content generation
  cycle.yml         — cron every 6h; sovereign-orchestrator → Upstash Redis
  self-improve.yml  — cron daily 03:00 UTC; lifelong-catch-correct agent
  release.yml       — manual release tagging
```

---

## GitHub Secrets Status

| Secret | Status | How to get it |
|--------|--------|--------------|
| GROQ_API_KEY | ✅ Set | console.groq.com |
| GEMINI_API_KEY | ✅ Set | aistudio.google.com |
| GMAIL_APP_PASSWORD | ✅ Set | Google Account → App passwords |
| CONTENT_REPO_TOKEN | ✅ Set | github.com/settings/tokens |
| SERVER_SSH_KEY | ✅ Set (base64 ED25519) | See "Update SERVER_SSH_KEY" above |
| DEVTO_API_KEY | ❌ Missing | dev.to/settings/extensions |
| HASHNODE_API_KEY | ❌ Missing | hashnode.com/settings/developer |
| HASHNODE_PUB_ID | ❌ Missing | Your Hashnode publication ID |
| MEDIUM_API_KEY | ❌ Missing | medium.com/me/settings → Integration Tokens |
| MEDIUM_AUTHOR_ID | ❌ Missing | `curl -H "Authorization: Bearer TOKEN" https://api.medium.com/v1/me` |
| AFFILIATE_LINKS | ❌ Missing | JSON object of affiliate links |
| AMAZON_PARTNER_TAG | ❌ Missing | Amazon Associates tag |
| UPSTASH_REDIS_REST_URL | ❌ Missing | console.upstash.com (free) — needed by cycle.yml |
| UPSTASH_REDIS_REST_TOKEN | ❌ Missing | console.upstash.com (free) — needed by cycle.yml |

**Set a secret:**
```powershell
& "C:\Program Files\GitHub CLI\gh.exe" secret set SECRET_NAME --repo quantam101/profitenginev5
# (pastes from clipboard or prompts for value)
```

---

## Remaining Manual Steps (priority order)

### 1 — Fix server SSH + re-deploy (BLOCKING)
See "URGENT" section at top.

### 2 — Upstash Redis (5 min, free)
1. Go to https://console.upstash.com → Create database → Region: us-east-1 → Free tier
2. Copy **REST URL** and **REST Token**
3. Set GitHub secrets:
   ```powershell
   gh secret set UPSTASH_REDIS_REST_URL --repo quantam101/profitenginev5
   gh secret set UPSTASH_REDIS_REST_TOKEN --repo quantam101/profitenginev5
   ```
4. Set Vercel env vars (for dashboard cycle display):
   - Go to https://vercel.com/already-here-llc-s-projects/profitengine/settings/environment-variables
   - Add `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN`

### 3 — Vercel Webhook Token (5 min)
1. Go to https://vercel.com/already-here-llc-s-projects/profitengine/settings/environment-variables
2. Add:
   - Key: `PROFITENGINE_WEBHOOK_TOKEN`
   - Value: `29d6accb030f7d60f1d0503197f9017e74962e18fdee514ea85c0635124f2700`
   - All environments (Production, Preview, Development)
3. Redeploy on Vercel after saving

### 4 — DNS A Records (5 min)
1. Go to https://dcc.godaddy.com/control/portfolio/alreadyherellc.com/settings/dns
2. Add A records → IP: `129.146.167.73`, TTL: 600:
   - `profitengine`
   - `api.profitengine`
   - `status.profitengine`

### 5 — Blog Platform API Keys
```powershell
# Dev.to (free, 2 min) — https://dev.to/settings/extensions
gh secret set DEVTO_API_KEY --repo quantam101/profitenginev5

# Hashnode (free, 3 min) — https://hashnode.com/settings/developer
gh secret set HASHNODE_API_KEY --repo quantam101/profitenginev5
gh secret set HASHNODE_PUB_ID --repo quantam101/profitenginev5

# Medium (free, 5 min) — https://medium.com/me/settings → Integration Tokens
gh secret set MEDIUM_API_KEY --repo quantam101/profitenginev5
gh secret set MEDIUM_AUTHOR_ID --repo quantam101/profitenginev5
```

### 6 — Affiliate Programs
- Amazon Associates: https://affiliate-program.amazon.com (takes days to approve)
- After approval:
  ```powershell
  gh secret set AMAZON_PARTNER_TAG --repo quantam101/profitenginev5
  gh secret set AFFILIATE_LINKS --repo quantam101/profitenginev5
  ```

### 7 — n8n External Access (optional)
n8n is currently Docker-internal only. To expose via Caddy:
1. Add DNS A record `n8n.profitengine` → `129.146.167.73`
2. Uncomment the n8n block in `caddy/Caddyfile`
3. Push to trigger a redeploy

---

## Completed Work (all sessions)

### Session 1 (2026-05-24)
- Project scaffolding: Next.js 14, FastAPI runtime, Docker Compose stack
- Free-tier cost guard (max_cost_usd=0, paid_adapters_enabled=false)
- GitHub Actions CI workflow
- Vercel deployment configuration
- GROQ_API_KEY, GEMINI_API_KEY, GMAIL_APP_PASSWORD, CONTENT_REPO_TOKEN set

### Session 2 (2026-05-26)
- OCI GitHub Actions CI/CD pipeline — fully working end-to-end
- Last successful run: https://github.com/quantam101/profitenginev5/actions/runs/26436815984
- SSH keepalives + extended timeout for Docker build
- `bootstrap-server.sh` — idempotent server setup script

### Session 3 (2026-05-27)
- n8n owner account: `admin@alreadyherellc.com` / `ProfitEngine2026!`
- Workflows imported + activated via `n8n import:workflow` CLI:
  - `ProfitEngine — Daily Content Pipeline`
  - `ProfitEngine — Blog Cross-post Webhook`
- `scripts/setup-n8n.sh` rewritten to use CLI (avoids REST API cookie issue over HTTP)

### Session 4 (2026-05-27) — Data Distillation + File Restore
- **Data Distillation pipeline** — 4-stage, zero LLM cost, 40-75% token reduction:
  - `runtime/distillation.py` — noise_strip, dedup_sentences, keyword_focus, budget_truncate
  - `runtime/token_budget.py` — per-tier input/output budgets
  - `runtime/structured_output.py` — shared JSON/list extraction, OUTPUT_CONSTRAINT constants
  - `runtime/vector_cache.py` — TTL columns, prune_expired(), output deduplication
  - `runtime/complexity_scorer.py` — token_est field, risk_terms list, token_len component
  - `runtime/inference_cascade.py` — lambda fix for monkeypatching, distill=True support, infer_with_report()
  - `tests/test_distillation.py` — 34 new tests (all 68 total passing)
- **Missing workflows restored** from canonical zip:
  - `.github/workflows/cycle.yml` — sovereign-orchestrator every 6h → Upstash Redis
  - `.github/workflows/self-improve.yml` — lifelong-catch-correct daily 03:00 UTC
  - `scripts/push_cycles_to_redis.py` — pushes cycle JSONL to Upstash REST API
  - `lib/cycleStore.ts` — TypeScript Upstash client for Vercel dashboard
  - `config/distillation.yaml` — distillation config
- **SSH key rotation**: new ED25519 key generated (old RSA key rejected by server)
- **`scripts/bootstrap-server.sh`** — updated with new deploy pub key + fingerprint-based check

---

## Test Suite

```powershell
# Run all tests
cd "C:\Users\alrea\profitenginev5"
python -m pytest tests/ -v

# Run specific modules
python -m pytest tests/test_core.py -v          # 34 tests — sovereign orchestrator, inference cascade
python -m pytest tests/test_distillation.py -v  # 34 tests — distillation, token budget, structured output
python -m pytest tests/test_publishing.py -v    # blog publisher tests
```

**Current test status:** 68/68 passing ✅

---

## Key Infrastructure Details

```
OCI Server:
  IP: 129.146.167.73 / user: opc / OS: Oracle Linux 9.7 / region: us-phoenix-1
  Instance OCID: ocid1.instance.oc1.phx.anyhqljsmvp52oyc4e4u537ie7faz2spvhfzciy2uyx53zmj3azzueccp7aq
  Compartment/Tenancy OCID: ocid1.tenancy.oc1..aaaaaaaay5qjgld6vs42ttb7lcdiof4tg767u4fojkqjidlglbvdzy4yiqaa
  Bastion OCID: ocid1.bastion.oc1.phx.amaaaaaamvp52oyafrslzyr3dbajlctmptq6lfdprpmplwy3kdgqa5wcrvpq
  Repo dir: /home/opc/profitenginev5
  WEBHOOK_SECRET: 29d6accb030f7d60f1d0503197f9017e74962e18fdee514ea85c0635124f2700

n8n:
  Owner: admin@alreadyherellc.com / ProfitEngine2026!
  Workflow IDs:
    content-pipeline-daily:  6f8691a2-0688-4dae-80bd-8cac8c2a61f5
    blog-crosspost-webhook:   409ed6db-db7d-4778-b009-5895ef332def

GitHub:
  Repo: quantam101/profitenginev5
  Token: stored in your password manager (GH_TOKEN env var)
  CLI: C:\Program Files\GitHub CLI\gh.exe

Local Paths:
  Repo: C:\Users\alrea\profitenginev5\
  Deploy key (private): C:\Users\alrea\profitengine-ed25519
  Deploy key (public):  C:\Users\alrea\profitengine-ed25519.pub
  Secret-set script:    C:\Users\alrea\set-secret-ed25519.mjs
  Deploy workflow:      .github\workflows\deploy.yml
  Bootstrap script:     scripts\bootstrap-server.sh
  n8n setup:            scripts\setup-n8n.sh

OCI CLI:
  Config: C:\Users\alrea\.oci\config / Profile: PROFITENGINE
```

---

## Key Runtime Files

```
runtime/
  inference_cascade.py    — infer() + infer_with_report(); 4-tier cascade with distillation
  distillation.py         — noise_strip, dedup_sentences, keyword_focus, budget_truncate
  token_budget.py         — TierBudget, budget_for(), clamp_max_tokens(), apply_input_budget()
  structured_output.py    — extract_json(), extract_list(), OUTPUT_CONSTRAINT_JSON
  vector_cache.py         — SQLite cache with TTL, output dedup, prune_expired()
  complexity_scorer.py    — ComplexityResult with token_est + risk_terms
  sovereign_core.py       — main orchestration loop
  agents.py               — agent registry
  cost_guard.py           — free-tier enforcement
  agent_impls/
    sovereign_orchestrator.py
    content_pipeline.py
    blog_publisher.py
    trend_scanner.py
    content_gen.py
    local_research.py
    lifelong_catch_correct.py
    free_tier_cost_guard.py

scripts/
  bootstrap-server.sh         — idempotent OCI server setup
  setup-n8n.sh                — n8n workflow import via CLI
  push_cycles_to_redis.py     — push cycle JSONL to Upstash REST API

lib/
  cycleStore.ts               — TypeScript Upstash client for Next.js dashboard

config/
  distillation.yaml           — distillation pipeline config

.github/workflows/
  ci.yml                      — pytest on every push
  deploy.yml                  — SSH deploy to OCI on push to main
  daily-content.yml           — cron: daily AI content generation
  cycle.yml                   — cron: every 6h sovereign-orchestrator
  self-improve.yml            — cron: daily 03:00 UTC lifelong-catch-correct
  release.yml                 — manual release tagging
```

---

## Disk Space Warning

OCI root disk was at 95% after first Docker build. If you hit space issues:
```bash
# Free space
ssh -i C:\Users\alrea\profitengine-ed25519 opc@129.146.167.73 'docker buildx prune -af'
```

Or expand boot volume to 50 GB:
Compute → Instances → profitengine-server → Boot Volume → Resize → 50 GB

---

## Session History

| Session | Date | Key Work |
|---------|------|---------|
| 1 | 2026-05-24 | Scaffolding, free-tier guards, CI, Vercel deploy |
| 2 | 2026-05-26 | OCI CI/CD pipeline end-to-end |
| 3 | 2026-05-27 | n8n workflows import + activation |
| 4 | 2026-05-27 | Data distillation, file restore from zip, SSH key rotation |
| 5 | 2026-05-27 | Master document |
