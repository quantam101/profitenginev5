# Profit-Generating Repos: Verification & Roadmap

**Date**: 2026-06-19  
**Status**: APScheduler build in profitenginev5 COMPLETE + deploying

---

## Repos Overview (Audited 2026-06-12)

| Repo | Purpose | Status | Priority | Action |
|------|---------|--------|----------|--------|
| **profitenginev5** | Main trading/content system | ✅ READY | P0 | Deploy + Verify |
| **already-here-llc** | Marketing/site repo | 🟢 GREEN | P1 | Verify + APScheduler |
| **content** | GitHub Pages (Jekyll) | 🟢 PUBLISHES | P0 | Verify daily publish |
| **already-here-dashboard** | Field Network OS | ⚠️ DRIFTING | P1 | Fix lockfile |
| **Token** | Tokenforge frontend | ⚠️ DEPLOY ISSUES | P2 | Fix SSH deploy |
| **tradegate2** | Trading gate | 🟢 GREEN | P2 | Verify + optimize |
| **ai-profit-suite** | Automation scripts | 🟢 GREEN | P2 | Verify + optimize |
| **alreadyhere-site** | Static site | 🟢 GREEN | P3 | Light verify |

---

## Current Deployment Status

### profitenginev5 (THIS BUILD)
**Status**: Deploy in progress  
**Last Commit**: feat: replace n8n with native APScheduler  
**GitHub Actions**: CI, Quality Pipeline, Runtime Image all running

**Next Steps**:
1. ⏳ Wait for GitHub Actions to complete (10-15 min)
2. 🔍 Verify `/health` endpoint responds with scheduler status
3. 🔍 Verify `/scheduler/jobs` shows daily content pipeline job
4. ⏰ Wait for 7am UTC tomorrow to verify content publishes
5. ✅ Declare production-ready

---

## Known Issues & Blockers (from 2026-06-12 audit)

### BLOCKING: SSH Port 22 Closed on OCI
**Impact**: Prevents automatic deploys to OCI  
**Root Cause**: Ingress rule removed from VCN security list  
**Remedy**: Use OCI Console to re-add tcp/22 or use Cloud Shell

**Status**: UNRESOLVED — User needs OCI Console access

```bash
# Manual workaround via OCI Cloud Shell:
cd /home/opc/profitenginev5
git fetch origin main && git reset --hard origin/main
sudo APP_DIR=/home/opc/profitenginev5 bash scripts/install-oci-runtime-updater.sh
APP_DIR=/home/opc/profitenginev5 bash scripts/oci-runtime-update.sh
```

### Issue: Beehiiv Newsletter Down (Income Stream 8)
**Impact**: Newsletter publishing failing  
**Root Cause**: Runtime mirror deploy stuck on old image, Beehiiv endpoint hangs  
**Status**: WAITING ON SSH FIX above

**Resolution Chain**:
1. Fix SSH port 22 (needs OCI Console)
2. Redeploy runtime with current code
3. Test `/newsletter/publish` endpoint
4. If Beehiiv API issue, update credentials in .env

### Issue: already-here-dashboard lockfile drift
**Impact**: Backend Sync Gate cron failing  
**Root Cause**: npm lockfile regeneration incomplete  
**Status**: Fixed 2026-06-12, needs verification

---

## Phase 1: Verify profitenginev5 is Live & Working

### Checklist
- [ ] GitHub Actions deploy completes (CI, Quality Pipeline, Runtime Image)
- [ ] APScheduler starts successfully in runtime logs
- [ ] `/health` endpoint returns `scheduler.running: true`
- [ ] `/scheduler/jobs` shows daily content pipeline scheduled for 7am UTC
- [ ] Tomorrow at 7am UTC: new blog post publishes via content pipeline
- [ ] Social distribution triggers automatically
- [ ] Affiliate links injected in article
- [ ] Revenue metrics show content activity
- [ ] No errors in runtime logs
- [ ] Newsletter publishing recovers (after OCI SSH fix)

### Verification Script
```bash
# SSH to OCI when available
ssh opc@129.146.167.73

# Check runtime health
curl http://localhost:8080/health | jq .scheduler

# Check scheduler jobs
curl http://localhost:8080/scheduler/jobs | jq .

# View logs
docker compose logs -f runtime | grep -E "scheduler|content-pipeline"

# Check for tomorrow's scheduled run
date -u +%Y-%m-%d' '%H:%M:%S
curl http://localhost:8080/scheduler/jobs | jq '.jobs[0].next_run'
```

---

## Phase 2: Verify All Repos End-to-End

### Revenue Stream Verification

| Stream | Repo | Endpoint | Expected | Status |
|--------|------|----------|----------|--------|
| 1. Content | profitenginev5 + content | Daily publish | ✅ Working | Verify |
| 2. Social | profitenginev5 | Distribution | ✅ Working | Verify |
| 3. Digital Products | profitenginev5 | `/products/revenue` | 🟢 Gumroad OK | Verify |
| 4. POD | profitenginev5 | `/eaos/health` | ✅ Queue running | Verify |
| 5. Trading | tradegate2 + profitenginev5 | Live orders | ✅ Robinhood API | Verify |
| 6. Video | profitenginev5 | Video engine | ✅ FFmpeg | Verify |
| 7. Chatbots | ai-profit-suite | Bot builders | ✅ Active | Verify |
| 8. Newsletter | profitenginev5 | `/newsletter/publish` | ⚠️ Beehiiv down | Fix OCI SSH |

### Cross-Repo Verification
```bash
# From any runner with network access

# 1. Frontend
curl -L https://profitengine-tau.vercel.app/ | head -20

# 2. Content publishing
curl -L https://quantam101.github.io/content/ | grep -i "profit"

# 3. Runtime API
curl https://api.profitengine.alreadyherellc.com/health | jq .

# 4. Dashboard (if online)
curl https://alreadyherellc.com/dashboard | head -5

# 5. Trading system
curl https://api.profitengine.alreadyherellc.com/eaos/health | jq '.trading'

# 6. Newsletter (after OCI SSH fix)
curl https://api.profitengine.alreadyherellc.com/newsletter/stats | jq .
```

---

## Phase 3: Apply Workflow Pattern to Remaining Repos

After profitenginev5 verified working, apply same build pattern to:

### Batch 1 (High Priority)
- **already-here-llc** — Next scheduled for APScheduler + optimization
- **tradegate2** — Trading system, needs APScheduler for market hours checks
- **ai-profit-suite** — Automation, needs scheduling

### Batch 2 (Medium Priority)
- **Token** — Fix SSH deploy issue, then optimize
- **already-here-dashboard** — Fix lockfile, verify sync gate
- **content** — GitHub Pages, add workflow scheduling

### Batch 3 (Low Priority)
- **alreadyhere-site** — Light optimization
- Archived repos (keep for reference, no changes)

---

## Execution Plan: Next 7 Days

### Day 1 (Today)
- [x] APScheduler build complete in profitenginev5
- [ ] GitHub Actions deploy finishes (10-15 min)
- [ ] Verify scheduler running
- [ ] Check `/health` and `/scheduler/jobs` endpoints

### Day 2
- [ ] Wait for 7am UTC content pipeline (if applicable)
- [ ] Verify daily content publishes
- [ ] Verify social distribution
- [ ] All logs clean (no errors)

### Day 3-4
- [ ] OCI SSH port 22 fix (user via OCI Console)
- [ ] Redeploy runtime (newsletter recovery)
- [ ] Verify Beehiiv newsletter publishes

### Day 5-7
- [ ] Apply Workflow pattern to already-here-llc
- [ ] Apply Workflow pattern to tradegate2
- [ ] Apply Workflow pattern to ai-profit-suite
- [ ] Comprehensive cross-repo testing

---

## Critical Success Factors

✅ **Must Have**:
- Scheduler executes daily at 7am UTC
- Content publishes automatically
- Social distribution follows
- No silent failures (all errors logged)
- OCI SSH port 22 restored

⚠️ **Important**:
- Newsletter service recovery (Beehiiv)
- Dashboard lockfile stability
- Token deploy SSH working
- All revenue streams online

🎯 **Nice to Have**:
- Performance optimization across repos
- Unified monitoring dashboard
- Automated recovery patterns

---

## Notes

- **Token Status**: Deploy blocked by SSH key authorization. Needs on-box verification: `cat ~/.ssh/authorized_keys | grep profitengine-deploy`
- **Memory Status**: 6 GB used, headroom available for additional containers
- **Disk Status**: 70% guard active (OCI A1 30GB boot vol), n8n removal frees ~150MB
- **Next Audit**: After all repos deployed, schedule weekly health checks

---

## Summary

**Current Phase**: Deploying APScheduler build to profitenginev5  
**Blocker**: OCI SSH port 22 (manual fix needed)  
**ETA to All Repos Live**: 7-10 days  
**Revenue Streams**: 7/8 online (newsletter pending SSH fix)  

Ready to proceed with Phase 2 verification after GitHub Actions completes.
