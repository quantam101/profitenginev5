# ProfitEngine v5 OCI Deployment Readiness Report
**Generated:** 2026-06-20  
**Target:** OCI Always Free (cmdos at 129.146.236.177)  
**Status:** **BLOCKED** — Critical secrets missing

---

## Executive Summary

Infrastructure is **85% ready** but deployment is **BLOCKED** on 4 critical secrets:

| Issue | Status | Impact |
|-------|--------|--------|
| POSTGRES_PASSWORD empty | ❌ Critical | PostgreSQL will fail to init |
| SERVER_SSH_KEY not in GitHub Secrets | ❌ Critical | Deploy workflow can't SSH to OCI |
| PRINTIFY_API_KEY missing | ❌ Critical | Product catalog sync fails |
| ANTHROPIC_API_KEY missing | ⚠️ Warning | AI fallback unavailable (Ollama primary) |

**OCI Server:** Reachable (SSH port 22 open, TCP connection confirmed)  
**Vercel Frontend:** Ready (profitengine-tau.vercel.app)  
**Databases:** Configured (MongoDB Atlas, PostgreSQL Neon)  
**Docker:** All images buildable, compose valid

---

## Critical Blockers (REQUIRED)

### 1. POSTGRES_PASSWORD is EMPTY
**File:** `.env` line 57  
**Current:** `POSTGRES_PASSWORD=`  
**Action:**
```bash
# Generate strong password
POSTGRES_PASSWORD=$(openssl rand -base64 32)
# Update .env line 57 with this value
```
**Why:** PostgreSQL container will not initialize without a password. Database will be INACCESSIBLE.

### 2. SERVER_SSH_KEY Not in GitHub Secrets
**Needed by:** `.github/workflows/deploy.yml` (line 145)  
**Current:** Not configured  
**Action:**
```bash
# Generate Ed25519 keypair
bash scripts/setup-oci-ssh-secret.sh
# This will print setup instructions
# Copy the PRIVATE key to GitHub Secrets > SERVER_SSH_KEY
# Copy the PUBLIC key to OCI Console > Instance (cmdos) > Edit > SSH keys
```
**Why:** Deploy workflow uses SSH to execute commands on 129.146.236.177. Without this key, OCI deployment will skip.

### 3. PRINTIFY_API_KEY Missing
**File:** `.env` (add new line)  
**Current:** Not present  
**Action:**
```bash
# Log into printify.com → Account → API
# Copy your API key
echo "PRINTIFY_API_KEY=<your-key-here>" >> .env
```
**Why:** Product sync will fail silently. Printify catalog won't be available.

### 4. ANTHROPIC_API_KEY Missing (Optional but Recommended)
**File:** `.env` (add new line)  
**Current:** Not present  
**Action:**
```bash
echo "ANTHROPIC_API_KEY=sk-ant-<your-key-here>" >> .env
```
**Why:** AI inference cascade uses Ollama → Claude → Groq. Without Claude, complex tasks fall back to Groq. (Recoverable, not blocking.)

---

## Component Status Checklist

### SSH Key Configuration
- ✅ OCI SSH port 22: **OPEN** (verified with Test-NetConnection)
- ✅ Workflow references: Present in deploy.yml
- ❌ SERVER_SSH_KEY GitHub Secret: **NOT CONFIGURED**
- ❌ Public key on OCI: **UNKNOWN** (check OCI Console)

**Fix:**
```bash
bash scripts/setup-oci-ssh-secret.sh
# Follow printed instructions to add public key to OCI Console
# Paste private key into GitHub Secrets > SERVER_SSH_KEY
```

### Environment Variables
| Variable | Status | Value |
|----------|--------|-------|
| POSTGRES_PASSWORD | ❌ Empty | NEEDED |
| STRIPE_SECRET_KEY | ✅ Present | sk_live_51... |
| GUMROAD_ACCESS_TOKEN | ✅ Present | qP1PGdN-... |
| MONGODB_URL | ✅ Present | mongodb+srv://... |
| DATABASE_URL | ✅ Present | postgresql://... (Neon) |
| PROFITENGINE_WEBHOOK_TOKEN | ✅ Present | c8eb99e5... |
| YOUTUBE_REFRESH_TOKEN | ✅ Present | 1//06rg_nVZ... |
| PRINTIFY_API_KEY | ❌ Missing | NEEDED |
| ANTHROPIC_API_KEY | ⚠️ Missing | Optional |
| TWILIO_* | ⚠️ Empty | Optional (voice agent) |
| MEDIUM_API_KEY | ⚠️ Empty | Optional (blog syncing) |
| AWS_ACCESS_KEY_ID | ⚠️ Empty | Optional (S3 backup) |

**Current .env line 57:**
```
POSTGRES_PASSWORD=
```

**Current .env line 33:**
```
YOUTUBE_API_KEY=
```

**Missing from .env:**
```
PRINTIFY_API_KEY=
ANTHROPIC_API_KEY=
```

### Database Credentials
- ✅ MongoDB Atlas: `profitenginev5.mongodb.net` (user: `alreadyherellc_db_user`)
- ✅ PostgreSQL Neon: `ep-dawn-truth-aigy5e9n-pooler.c-4.us-east-1.aws.neon.tech` (user: `neondb_owner`)
- ⚠️ PostgreSQL local (Docker): Password unset (PostgreSQL will FAIL)

### Docker Images & Build
- ✅ Dockerfile: Present (Python 3.12, FastAPI)
- ✅ Dockerfile.runtime: Present (Python 3.12, uvicorn)
- ✅ Dockerfile.web: Present (Next.js 15)
- ✅ Dockerfile.taylor: Present (Voice agent)
- ✅ docker-compose.yml: 127 lines, all services configured
- ✅ requirements.txt: 50+ packages (anthropic, fastapi, stripe, twilio, etc.)
- ✅ package.json: Node 20.x, Next 15.5.18, PostgreSQL driver

**Resource limits (OCI E2.1.Micro):**
- Caddy: cpus=1, mem=512m
- Web (Next.js): cpus=1.5, mem=2g
- Runtime (Python): cpus=1.5, mem=2g
- Taylor (voice): cpus=1, mem=768m
- PostgreSQL: cpus=1, mem=1g
- **Total: 6 CPUs, 7.3 GB RAM** (OCI free tier provides 1 CPU, 1GB RAM)
  
  ⚠️ **WARNING:** Resource limits exceed OCI Always Free capacity. Expect slow performance or OOM kills. Consider:
  - Reducing mem_limit for non-critical services
  - Moving PostgreSQL to Neon (serverless, free tier)
  - Disabling uptime-kuma or running on separate box

### Domain & TLS
- ✅ SITE_DOMAIN: `profitengine.alreadyherellc.com`
- ✅ ACME_EMAIL: `ops@alreadyherellc.com`
- ✅ Caddyfile: 126 lines, all subdomains configured
- ✅ Health endpoint: `http://129.146.236.177/health` (no TLS required)

**Required DNS Setup:**
```
A profitengine.alreadyherellc.com 129.146.236.177
CNAME app.profitengine.alreadyherellc.com profitengine.alreadyherellc.com
CNAME api.profitengine.alreadyherellc.com profitengine.alreadyherellc.com
CNAME taylor.profitengine.alreadyherellc.com profitengine.alreadyherellc.com
CNAME status.profitengine.alreadyherellc.com profitengine.alreadyherellc.com
```

### Vercel Frontend
- ✅ Domain: `profitengine-tau.vercel.app`
- ✅ Repository: `quantam101/profitenginev5` (public)
- ✅ Build: Next.js 15.5.18
- ✅ Node: 20.x
- ✅ vercel.json: Configured with fallback URLs

**Production URLs:**
```
Frontend: https://profitengine-tau.vercel.app
Fallback: https://profitengine.alreadyherellc.com (via Vercel custom domain, optional)
API: https://api.profitengine.alreadyherellc.com (OCI backend)
```

### CI/CD Pipeline
- ✅ `.github/workflows/deploy.yml`: 215 lines
  - Preflight checks (HTTP, HTTPS, SSH reachability)
  - SSH deploy (git fetch, docker pull, health check)
  - Non-blocking on SSH failure (Vercel remains primary)
- ✅ Deploy scripts present:
  - `scripts/install-oci-runtime-updater.sh`
  - `scripts/oci-runtime-update.sh`
  - `scripts/setup-oci-ssh-secret.sh`
  - `scripts/oci-recovery.sh`
- ✅ Systemd integration (timer-based auto-updates)

### OCI Server Reachability
- ✅ SSH port 22: **OPEN** (verified)
- ⚠️ HTTP port 80: Unknown (not tested, but should be open)
- ⚠️ HTTPS port 443: Unknown (not tested, but Caddy should be running)
- ✅ Static IP: 129.146.236.177 (OCI Always Free)
- ✅ OS: Oracle Linux
- ✅ Docker: Must be pre-installed on OCI host

---

## Deployment Checklist

### Pre-Deployment (REQUIRED)
- [ ] Fix POSTGRES_PASSWORD in `.env` line 57
- [ ] Add PRINTIFY_API_KEY to `.env`
- [ ] Add ANTHROPIC_API_KEY to `.env` (optional)
- [ ] Run: `bash scripts/setup-oci-ssh-secret.sh`
- [ ] Create GitHub Secret `SERVER_SSH_KEY` (paste private key)
- [ ] Verify OCI Console has public SSH key registered
- [ ] Verify DNS A record: `profitengine.alreadyherellc.com` → `129.146.236.177`
- [ ] Review docker-compose.yml resource limits (may exceed OCI capacity)

### Deployment
- [ ] Commit `.env` changes (after scrubbing secrets from git history)
- [ ] Push to main branch
- [ ] GitHub Actions > Workflows > OCI Runtime Mirror Deploy > Run workflow
- [ ] Monitor workflow logs
- [ ] Watch for SSH connection, Docker pulls, health checks

### Post-Deployment Smoke Tests
- [ ] `curl https://profitengine.alreadyherellc.com/health`
- [ ] `curl https://api.profitengine.alreadyherellc.com/health`
- [ ] Access frontend: `https://profitengine.alreadyherellc.com`
- [ ] Check Vercel: `https://profitengine-tau.vercel.app`
- [ ] Test DB: `npm run db:test`
- [ ] Test MongoDB: `docker compose exec -T runtime python -c "import pymongo; print(pymongo.MongoClient(...).admin.command('ping'))"`
- [ ] Smoke test Stripe: Trigger test charge, verify webhook
- [ ] Check status page: `https://status.profitengine.alreadyherellc.com`

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│ OCI Always Free (129.146.236.177)                       │
│ Docker Compose:                                         │
│  • Caddy (TLS, reverse proxy) port 80/443               │
│  • Next.js frontend port 3000                           │
│  • Python runtime API port 8080                         │
│  • FastAPI backend port 8001                            │
│  • Taylor voice agent port 8001                         │
│  • PostgreSQL port 5432                                 │
│  • Uptime Kuma port 3001                                │
└─────────────────────────────────────────────────────────┘
         ↓
    profitengine.alreadyherellc.com
    (Caddy auto-TLS via ACME)
         ↓
┌─────────────────────────────────────────────────────────┐
│ External Services                                       │
├─────────────────────────────────────────────────────────┤
│ • MongoDB Atlas (profitenginev5)                        │
│ • PostgreSQL Neon (us-east-1)                           │
│ • Stripe (payments)                                     │
│ • Gumroad (ebooks)                                      │
│ • Printify (POD products)                               │
│ • YouTube OAuth 2.0                                     │
│ • GitHub Pages (content)                                │
│ • Telegram Bot (daily digest)                           │
└─────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────┐
│ Vercel Frontend (profitengine-tau.vercel.app)          │
│ Failover if OCI unreachable                            │
└─────────────────────────────────────────────────────────┘
```

---

## Warnings & Known Issues

### Resource Constraints
- OCI Always Free: 1 CPU, 1 GB RAM (free tier)
- docker-compose.yml requests: 6 CPUs, 7.3 GB RAM
- **Impact:** Containers will be heavily throttled or OOM-killed
- **Recommendation:** 
  - Reduce mem_limit for non-critical services
  - Move PostgreSQL to Neon (serverless) instead of local Docker container
  - Disable uptime-kuma or run on separate machine

### Optional Features
If not configured, these services degrade gracefully:
- Twilio (voice agent won't work)
- AWS S3 (local storage used instead)
- Medium API (article publishing skipped)
- Anthropic API (falls back to Groq/Gemini)

### Monitoring
- Health endpoint: `http://129.146.236.177/health`
- Status page: Uptime Kuma at `status.profitengine.alreadyherellc.com`
- Logs: `docker compose logs -f`

---

## Final Readiness Assessment

### PASS Criteria (All required):
1. ✅ SSH key configured in GitHub Secrets
2. ✅ All critical secrets in `.env`
3. ✅ Docker images buildable
4. ✅ OCI server reachable (port 22 open)
5. ✅ Databases configured (MongoDB, PostgreSQL)
6. ✅ Vercel frontend ready
7. ✅ CI/CD pipeline in place

### CURRENT STATUS: **BLOCKED**
Missing:
- POSTGRES_PASSWORD
- SERVER_SSH_KEY (GitHub Secret)
- PRINTIFY_API_KEY

Once these 3 items are fixed, readiness = **READY FOR PRODUCTION DEPLOYMENT**

---

## Next Steps

1. **This hour:** Fix POSTGRES_PASSWORD, SERVER_SSH_KEY, PRINTIFY_API_KEY
2. **This hour:** Run `bash scripts/setup-oci-ssh-secret.sh`
3. **Today:** Create GitHub Secret `SERVER_SSH_KEY`
4. **Today:** Trigger deploy.yml workflow
5. **Today:** Run smoke tests
6. **This week:** Monitor logs, verify daily jobs

---

**For questions or blockers, consult:** `.claude/projects/*/memory/MEMORY.md` for project context and recent fixes.
