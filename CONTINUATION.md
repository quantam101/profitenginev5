# ProfitEngine v5 — Master Reference Document
**Last updated:** 2026-05-27 (Session 7)

---

## ✅ Current Production Status

| System | Status | Notes |
|--------|--------|-------|
| CI pipeline | ✅ Green | Node.js 24 runtime |
| GitHub Actions deploy | ✅ Working | ED25519 SSH key fixed |
| Server containers | ✅ All 6 running | web, runtime, caddy, n8n, postgres, uptime-kuma |
| Health score | ✅ 100/100 | ok=true, all 11 checks pass |
| Disk usage | ✅ 67% (9.9 GB free) | Was 100% — 3.3 GB build cache cleared |
| Docker Guard cron | ✅ Installed | Runs every 6h via cron + GitHub Actions |
| DNS | ✅ Propagated | All 4 A records → 129.146.167.73 |
| HTTPS / Caddy cert | ✅ Live | TLS certs issued for all 4 subdomains |

---

## 🔧 Manual Steps Required (priority order)

### 1. DNS — ✅ COMPLETE (2026-05-27)
All 4 A records set in GoDaddy → 129.146.167.73. TLS certs live.

Live URLs:
- https://profitengine.alreadyherellc.com        ← main dashboard
- https://api.profitengine.alreadyherellc.com     ← API
- https://status.profitengine.alreadyherellc.com  ← Uptime Kuma
- https://app.profitengine.alreadyherellc.com     ← app

### 2. Blog Publishing API Keys (revenue-enabling)
Add these to GitHub Secrets (https://github.com/quantam101/profitenginev5/settings/secrets/actions):

| Secret Name | Where to Get |
|-------------|-------------|
| `DEVTO_API_KEY` | https://dev.to/settings/extensions → New API key |
| `HASHNODE_API_KEY` | https://hashnode.com/settings/developer → Create PAT |
| `HASHNODE_PUB_ID` | Your Hashnode publication ID |
| `MEDIUM_API_KEY` | https://medium.com/me/settings → Integration tokens |
| `MEDIUM_AUTHOR_ID` | Your Medium user ID |

### 3. Upstash Redis (caching/rate-limiting)
Free at https://console.upstash.com:
- Create a Redis database (free tier, us-east-1)
- Add to GitHub Secrets: `UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN`

### 4. OCI Boot Volume Expansion (recommended)
Current: 30 GB | Recommended: 50 GB
OCI Console → Compute → Boot Volumes → profitengine-server → Edit → Resize

After resize, SSH in and run:
```bash
sudo growfs /dev/mapper/ocivolume-root
```

### 5. Amazon Affiliate
`AMAZON_PARTNER_TAG=alreadyhere-20` is already set ✅ (found in Downloads/COMPLETE_SETUP.sh)
- `AFFILIATE_LINKS` — Optional JSON map of product keywords to URLs (not required, code has defaults)

### 6. Vercel Env Var (if using Vercel for Next.js edge)
Add `PROFITENGINE_WEBHOOK_TOKEN=85e7269ade9a0d356c5d3ad74e7662046f9353ad91aa6a20e2e3b88fce71b29e`

---

## 🖥️ Server Access

```powershell
# SSH to server
ssh -i "$env:USERPROFILE\profitengine-ed25519" opc@129.146.167.73

# Key files
C:\Users\alrea\profitengine-ed25519        # private key (ED25519)
C:\Users\alrea\profitengine-ed25519.pub    # public key
```

**Server:** `129.146.167.73` | OCI Oracle Linux 9.7 | 4 OCPUs / 24 GB RAM
**ED25519 fingerprint:** `SHA256:lEzI1h1lTjWqNqjJmtO2WQQ8l/D09oAqFzOyeVPAhLM`

---

## 📦 GitHub Secrets Status

| Secret | Status | Updated |
|--------|--------|---------|
| `SERVER_SSH_KEY` | ✅ Set | 2026-05-27 (ED25519, base64-encoded) |
| `AMAZON_PARTNER_TAG` | ✅ Set | 2026-05-27 (`alreadyhere-20`) |
| `GROQ_API_KEY` | ✅ Set | 2026-05-24 |
| `GEMINI_API_KEY` | ✅ Set | 2026-05-26 |
| `GMAIL_APP_PASSWORD` | ✅ Set | 2026-05-26 |
| `CONTENT_REPO_TOKEN` | ✅ Set | 2026-05-26 |
| `OCI_SSH_KEY` | ✅ Set | 2026-05-26 |
| `DEVTO_API_KEY` | ❌ Missing | Add at dev.to/settings |
| `HASHNODE_API_KEY` | ❌ Missing | Add at hashnode.com/settings |
| `HASHNODE_PUB_ID` | ❌ Missing | Your publication ID |
| `MEDIUM_API_KEY` | ❌ Missing | Add at medium.com/settings |
| `MEDIUM_AUTHOR_ID` | ❌ Missing | Your Medium user ID |
| `UPSTASH_REDIS_REST_URL` | ❌ Missing | Free at console.upstash.com |
| `UPSTASH_REDIS_REST_TOKEN` | ❌ Missing | Free at console.upstash.com |
| `ANTHROPIC_API_KEY` | ❌ Missing | Optional (Groq/Gemini are primary) |
| `AFFILIATE_LINKS` | ❌ Missing (optional) | Custom link map — code has defaults built-in |
| `AMAZON_PARTNER_TAG` | ✅ Set | `alreadyhere-20` (found in Downloads/COMPLETE_SETUP.sh) |

---

## 🚀 Deploy Commands

```powershell
# Trigger deploy (uses current GH_TOKEN session)
$env:GH_TOKEN = "YOUR_GITHUB_PAT_HERE"
gh workflow run deploy.yml -R quantam101/profitenginev5 --ref main
gh run watch --repo quantam101/profitenginev5

# Trigger docker-guard manually
gh workflow run docker-guard.yml -R quantam101/profitenginev5 --ref main
```

```powershell
# Update a GitHub secret (example: DEVTO_API_KEY)
$env:GH_TOKEN = "YOUR_GITHUB_PAT_HERE"
gh secret set DEVTO_API_KEY --body "your-key-here" -R quantam101/profitenginev5
```

---

## 🏗️ Project Structure

| Component | Technology | Location |
|-----------|-----------|---------|
| Web dashboard | Next.js 14 | `app/` |
| Python runtime | FastAPI + uvicorn | `runtime/` |
| Inference cascade | Ollama→Groq→Gemini→Claude→stub | `runtime/inference_cascade.py` |
| Data distillation | 4-stage pipeline (40-75% reduction) | `runtime/distillation.py` |
| Docker Guard agent | Bash + Python | `scripts/docker-guard.sh` + `runtime/agent_impls/docker_guard.py` |
| CI/CD | GitHub Actions (7 workflows) | `.github/workflows/` |
| Reverse proxy | Caddy 2 | `caddy/Caddyfile` |
| Monitoring | Uptime Kuma | `http://129.146.167.73:3001` (after port forward) |
| Automation | n8n | Internal only (auth required) |

---

## 📊 Service Health (as of 2026-05-27)

```
Server: 129.146.167.73
Disk: 67% used (9.9 GB free / 30 GB total)
Containers: caddy, web, runtime (healthy), n8n, postgres, uptime-kuma (healthy)
Health score: 100/100
Build cache: Cleared — 3.3 GB freed
Docker guard cron: 0 */6 * * * (every 6 hours)
```

### To check health manually:
```bash
ssh -i ~/profitengine-ed25519 opc@129.146.167.73 \
  "docker exec profitenginev5-runtime-1 wget -qO- http://web:3000/api/health | python3 -c 'import sys,json; d=json.load(sys.stdin); print(\"ok:\",d[\"ok\"],\"score:\",d[\"healthScore\"])'"
```

---

## 📝 Session 7 Actions — GO LIVE (2026-05-27)

| Action | Result |
|--------|--------|
| Set `AMAZON_PARTNER_TAG` secret | ✅ `alreadyhere-20` (found in Downloads) |
| Set `DEVTO_API_KEY` secret | ✅ `w67nr6yMcqtPC5JHDERCDRxk` |
| Set `HASHNODE_API_KEY` secret | ✅ `3e71b759-...` (PAT — needs Pro plan) |
| Set `HASHNODE_PUB_ID` secret | ⚠️ Set to PAT UUID (real pub ID TBD) |
| Set `MEDIUM_AUTHOR_ID` secret | ✅ `c64d1c9f-e473-408d-8653-f79c43a0e065` |
| Hashnode API investigation | Now requires Pro plan — script handles failure gracefully |
| DNS A records (GoDaddy) | ✅ All 4 set → 129.146.167.73 |
| TLS certs (Caddy/ACME) | ✅ All 4 subdomains provisioned |
| **PRODUCTION GO-LIVE** | ✅ **2026-05-27** |

## 📝 Commit History (Session 6)

| Commit | Description |
|--------|-------------|
| `53ab313` | feat(infra): Docker/Ollama guard agent with data distillation |
| `c3ddedd` | fix(docker-guard): fix grep-c double-output and numeric comparison bugs |
| `fd74c76` | chore(ci): opt into Node.js 24 runtime for all GitHub Actions |

**Previous sessions:** `8bac54e`, `0e40aba`, `86915d2`, `df36daa`, `9b0b551`, `0382c27`, `257fad3`, `f2995d6`

---

## 🔐 Key Files on Local Machine

```
C:\Users\alrea\profitengine-ed25519         SSH private key (ED25519)
C:\Users\alrea\profitengine-ed25519.pub     SSH public key
C:\Users\alrea\set-secret-ed25519.mjs       Script to update SERVER_SSH_KEY secret
C:\Users\alrea\profitenginev5\              Project repo
```

---

## ⚙️ GitHub Actions Workflows

| Workflow | Schedule | Purpose |
|----------|---------|---------|
| `ci.yml` | On push/PR | Lint, type-check, unit tests, security scan |
| `deploy.yml` | On push to main | SSH deploy to OCI server |
| `docker-guard.yml` | Every 6h (offset) | Disk + container health, auto-prune |
| `cycle.yml` | Every 6h | Sovereign profit cycle (Groq→Gemini) |
| `daily-content.yml` | Daily 07:05 UTC | SEO article generation + publishing |
| `self-improve.yml` | Daily 03:00 UTC | LC&C self-improvement loop |
| `release.yml` | On version tags | Build GHCR Docker images + GitHub Release |

---

## 🎯 What's Automated vs. What Needs You

### Fully Automated (zero intervention)
- ✅ Deploy on every git push to main
- ✅ Docker disk guard every 6 hours (prune containers, images, cache)
- ✅ Health monitoring + alerts in GitHub Actions
- ✅ Daily SEO content generation (Groq free tier)
- ✅ n8n workflow automation (cron on server)
- ✅ TLS cert renewal (Caddy auto-renews)

### Needs Your Action
- ❌ Upstash Redis — console.upstash.com (free, enables cycle/self-improve caching)
- ❌ Medium API key — requires approval at yourfriends@medium.com
- ❌ OCI disk expansion 30→50 GB (preventive, not urgent)
- ❌ Hashnode Pro (optional — API requires paid plan)
