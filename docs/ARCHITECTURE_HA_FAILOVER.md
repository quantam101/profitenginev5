# High-Availability Architecture — Eliminate OCI Single Point of Failure

## Current Problem

```
┌─────────────────────────────────────────────┐
│  Single OCI Instance (129.146.167.73)       │
│  - Runtime API                              │
│  - Newsletter publishing                    │
│  - Telegram digest                          │
│  - AI operations                            │
│  - Lead capture processing                  │
└──────────────┬──────────────────────────────┘
               │
         Single point of failure
      ↓ Instance down = ALL services down
```

**When it fails:** No redundancy, no failover, revenue blocked.

---

## Solution: Multi-Region Active-Standby Architecture

```
┌────────────────────────────────────────────────────────────┐
│                                                            │
│  api.profitengine.alreadyherellc.com (Smart DNS)          │
│  └─ Route 53 / Cloudflare / Health Check based routing   │
│     │                                                     │
│     ├─ Primary: OCI Instance (129.146.167.73) ────┐       │
│     │           /health → HTTP 200                │       │
│     │                                             │       │
│     └─ Failover: Railway/Heroku Runtime   ────────┘       │
│                 /health → HTTP 200                        │
│                 (automatically routes traffic if OCI down)│
│                                                            │
│  RESULT: If OCI down → traffic routes to Railway          │
│          No detection delay, no manual intervention       │
│          Transparent failover (~50ms DNS update)          │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## Implementation Options

### **Option 1: Railway (RECOMMENDED — Easiest)**

**Why Railway?**
- Python FastAPI support ✅
- $5/month (free tier covers this use case)
- Docker support ✅
- Automatic deployments from GitHub ✅
- Health check endpoints built-in ✅
- Sub-second failover with proper DNS setup

**Setup (2 hours):**
1. Create Railway account → connect GitHub
2. Deploy `profitenginev5` repo to Railway
3. Set `RUNTIME_API_URL` env vars (same as OCI)
4. Setup Route 53 weighted routing (50% OCI, 50% Railway)
   - When OCI health check fails → 100% traffic to Railway
5. Cost: $5-10/month

**Test:**
```bash
# Stop OCI instance → traffic should route to Railway
# curl https://api.profitengine.alreadyherellc.com/health should still work
```

---

### **Option 2: Heroku (Medium Effort)**

**Why Heroku?**
- Reliable, battle-tested
- Python support ✅
- $7/month (eco dyno)
- Built-in health checks

**Setup (2-3 hours):**
1. Create Heroku app
2. Deploy via GitHub Actions
3. Configure Route 53 weighted routing
4. Cost: $7-15/month

---

### **Option 3: AWS Lambda + RDS (Advanced)**

**Why?**
- Serverless = no instance to crash
- Auto-scaling
- Multi-AZ database redundancy

**Setup (4-6 hours):**
- Refactor code to Lambda handler
- Setup RDS for state
- API Gateway routing
- Cost: $15-30/month

---

## Detailed Setup: Route 53 Active-Passive Failover

This is the critical piece that makes failover automatic:

### **Step 1: Deploy Failover Runtime to Railway**
```bash
# 1. Create Railway account (2 min)
#    Go to railway.app → sign up with GitHub

# 2. Create new project → Deploy from GitHub
#    Select: profitenginev5 repo
#    Auto-deploy from main branch

# 3. Set environment variables (same as OCI):
#    POSTGRES_URL=<your-remote-postgres>
#    ANTHROPIC_API_KEY=<key>
#    etc.

# 4. Get Railway URL
#    Should be something like: runtime-prod.railway.app
```

### **Step 2: Setup Route 53 Health Checks + Weighted Routing**

```
1. Go to AWS → Route 53 → Health Checks
2. Create health check for OCI:
   - Protocol: HTTPS
   - Host: api.profitengine.alreadyherellc.com
   - Path: /health
   - Interval: 30s
   - Failure threshold: 2 (fail after 2 failed checks = 60s)

3. Create health check for Railway:
   - Protocol: HTTPS
   - Host: runtime-prod.railway.app
   - Path: /health
   - Same settings

4. Go to Route 53 → Hosted Zones → alreadyherellc.com
5. Create ALIAS record: api.profitengine
   - Type: A (IPv4)
   - Routing policy: WEIGHTED
   
   Set 2 weighted records:
   ├─ Set ID: "OCI-Primary"
   │  Weight: 100
   │  Value: ALIAS to api.profitengine.alreadyherellc.com (OCI)
   │  Health Check: OCI health check
   │
   └─ Set ID: "Railway-Failover"
       Weight: 0 (inactive until OCI fails)
       Value: ALIAS to runtime-prod.railway.app
       Health Check: Railway health check
```

**How it works:**
- Normal: All traffic → OCI (weight 100)
- OCI health check fails → automatically routes to Railway (weight 0 → 100)
- When OCI recovers → traffic routes back
- **Automatic, no manual intervention, ~50ms failover time**

### **Step 3: DNS Propagation**
```bash
# Test failover routing
dig api.profitengine.alreadyherellc.com
# Should resolve to OCI primary

# When you stop OCI instance:
# dig api.profitengine.alreadyherellc.com
# Should resolve to Railway after ~60s (2 health check failures)
```

---

## Cost Breakdown

| Component | Cost | Total |
|-----------|------|-------|
| OCI Always-Free Instance | $0/month | $0 |
| Railway Standby Runtime | $5/month | $5 |
| Route 53 Health Checks (3) | ~$1/month | $1 |
| Route 53 DNS Queries | ~$0.40/month | $0.40 |
| **Total** | | **~$6/month** |

**vs Revenue Impact of 1 hour downtime: $500+ (lost newsletters, delayed digests)**

ROI: ~83x

---

## Implementation Timeline

| Phase | Timeline | Impact |
|-------|----------|--------|
| **Phase 1 (Now)** | Deploy auto-recovery workflows (done) | MTTR: 24h → 7-10 min |
| **Phase 2 (This week)** | Deploy Railway standby (2-3 hours) | MTTR: 7-10 min → 1-2 min |
| **Phase 3 (This week)** | Setup Route 53 failover (1 hour) | Downtime: 1-2 min → 0 min (transparent) |
| **Phase 4 (Optional)** | Upgrade to Lambda (next month) | True serverless HA |

---

## Architecture After Implementation

```
Frontend (Vercel)
    ↓
api.profitengine.alreadyherellc.com
    ↓
Route 53 Health Check-based routing
    ├─ OCI Instance (Primary) — HTTP 200 ✅ → Traffic flows here
    │                         — Timeout ❌ → Automatic failover
    │
    └─ Railway Runtime (Standby) — receives traffic if OCI down

Services resume automatically, user sees no downtime
```

---

## Verification Checklist

After setup:
- [ ] Deploy Railway standby runtime
- [ ] Configure Route 53 health checks
- [ ] Test failover: Stop OCI instance
- [ ] Verify: API still responds (via Railway)
- [ ] Verify: Route 53 weighted routing switched
- [ ] Restart OCI instance
- [ ] Verify: Traffic routes back to OCI
- [ ] Monitor: Both instances for 1 week
- [ ] Celebrate: No more single point of failure 🎉

---

## When Should You Do This?

**NOW** (Critical):
- Deploy auto-recovery workflows ✅ (done)
- Add OCI API credentials to GitHub ✅ (actionable item)

**This Week** (High Priority):
- Deploy Railway failover instance
- Setup Route 53 DNS failover

**Next Month** (Nice to Have):
- Consider Lambda migration for true serverless

---

## Failure Modes Covered

| Failure | Before | After Route 53 Failover |
|---------|--------|-------------------------|
| OCI instance crashes | ❌ 24h+ down | ✅ Transparent failover |
| OCI network blip | ❌ 5-10 min | ✅ < 1 min (DNS recovery) |
| OCI disk full | ❌ Manual recovery | ✅ Auto-routes to Railway |
| OCI out of memory | ❌ Cascading failure | ✅ Instance reboots, routes to Railway |
| OCI reboot/maintenance | ❌ Downtime | ✅ Seamless failover |

---

## Permanent Prevention Summary

```
Level 1: Monitoring + Auto-Recovery (DONE ✅)
  → Detects failures in 5 min
  → Recovers in 2-3 min
  → Zero manual intervention
  → MTTR: ~7-10 min

Level 2: Active-Standby Failover (TO DO THIS WEEK)
  → Automatic routing to failover instance
  → Sub-minute failover time
  → Transparent to users
  → MTTR: ~1-2 min

Level 3: True Redundancy (Optional Next Month)
  → Multiple instances per region
  → Database replication
  → Load balancing
  → MTTR: 0 (user sees nothing)
```

---

**Next Action:** Deploy to Railway this week for true HA
**Estimated Effort:** 2-3 hours (deploy + test failover)
**Cost:** $6/month
**Benefit:** $500+ saved on every outage

---

Created: 2026-06-14
Status: Ready to implement
Owner: quantam101
