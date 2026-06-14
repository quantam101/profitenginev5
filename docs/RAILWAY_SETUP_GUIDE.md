# Railway Failover Deployment — Step-by-Step

## Overview

Deploy a standby runtime to Railway that automatically takes over when OCI fails. Transparent failover via Route 53 health checks.

**Time: 2-3 hours**  
**Cost: $5/month**  
**Benefit: Zero downtime when OCI fails**

---

## Prerequisites

- [ ] GitHub account (already have)
- [ ] AWS account with Route 53 (create if needed — free tier covers this)
- [ ] Railway account (free, linked to GitHub)

---

## Part 1: Deploy to Railway (45 min)

### 1.1 Create Railway Account
1. Go to **railway.app**
2. Click **Sign up**
3. Choose **Continue with GitHub**
4. Authorize and login

### 1.2 Create New Project
1. Click **New Project** (or **+**)
2. Select **Deploy from GitHub**
3. Choose repository: **profitenginev5**
4. Click **Import**

Railway automatically detects it's a Next.js + Python project.

### 1.3 Configure Environment Variables

Railway needs the same env vars as OCI. Go to **Project Settings → Variables**

Add these (copy from your OCI server):

```
# Runtime API
RUNTIME_API_URL=https://api.profitengine.alreadyherellc.com

# Database
POSTGRES_DB=profitengine
POSTGRES_USER=profitengine
POSTGRES_PASSWORD=<your-password>
POSTGRES_HOST=<your-postgres-host>

# AI/LLM
ANTHROPIC_API_KEY=<key>
GROQ_API_KEY=<key>
GEMINI_API_KEY=<key>

# Authentication
NEXTAUTH_SECRET=<secret>
NEXTAUTH_URL=https://api.profitengine.alreadyherellc.com

# Content publishing
GITHUB_CONTENT_TOKEN=<token>

# Webhooks
PROFITENGINE_WEBHOOK_TOKEN=<token>

# Telegram
TELEGRAM_BOT_TOKEN=<token>
TELEGRAM_CHAT_ID=<id>
TELEGRAM_WEBHOOK_SECRET=<secret>

# Email
GMAIL_APP_PASSWORD=<password>

# Meta
FB_PAGE_ID=<id>
FB_PAGE_ACCESS_TOKEN=<token>
IG_USER_ID=<id>
```

⚠️ **Where to get these:**
- Most are in your GitHub Secrets (Settings → Secrets and variables)
- Some are in OCI server `.env` (SSH and read file)
- Database password from your current setup

### 1.4 Monitor Deployment
1. Click on your project
2. Watch the **Services** tab
3. When green ✅ — deployment successful

Expected build time: 5-10 minutes

### 1.5 Get Railway Public URL
1. Go to your project
2. Click on the **web** service
3. Find **Public URL** section
4. Copy the URL (should be `https://runtime-prod.railway.app` or similar)

### 1.6 Test Railway Deployment
```bash
# Test the health endpoint
curl https://<your-railway-url>/health

# Should return: HTTP 200
# {"status": "ok"}
```

If it fails:
- Check logs in Railway console (there's a logs tab)
- Verify env vars are correct
- Check database connectivity
- Verify API keys are valid

---

## Part 2: AWS Route 53 Health Checks & Failover (1 hour)

### 2.1 Create AWS Account (if needed)
1. Go to **aws.amazon.com**
2. Sign up for free tier
3. Create IAM user with Route 53 permissions
4. Save access key ID + secret

### 2.2 Create Health Check for OCI
1. Go to **AWS Console → Route 53**
2. Click **Health Checks** (left sidebar)
3. Click **Create health check**
4. Configure:
   - **Health checker region:** US East (N. Virginia)
   - **Protocol:** HTTPS
   - **IP/Domain name:** `api.profitengine.alreadyherellc.com`
   - **Port:** 443
   - **Path:** `/health`
   - **Interval:** 30 seconds
   - **Failure threshold:** 2 (fail after 2 consecutive failures = 60 seconds)
   - **Enable SNI:** Yes
5. Click **Create health check**

### 2.3 Create Health Check for Railway
1. Click **Create health check** again
2. Configure:
   - **Health checker region:** US East (N. Virginia)
   - **Protocol:** HTTPS
   - **IP/Domain name:** `<your-railway-url>` (e.g., `runtime-prod.railway.app`)
   - **Port:** 443
   - **Path:** `/health`
   - **Interval:** 30 seconds
   - **Failure threshold:** 2
   - **Enable SNI:** Yes
3. Click **Create health check**

### 2.4 Setup Route 53 Weighted Routing
1. Go to **Route 53 → Hosted Zones**
2. Click **alreadyherellc.com**
3. Look for `api.profitengine` record
   - If it doesn't exist, create it first
   - Type: A (or AAAA for IPv6)
   - Value: OCI IP (129.146.167.73)

4. **Modify existing record** OR **Create new weighted records**:

   **Record 1 — OCI Primary:**
   - **Record name:** `api.profitengine.alreadyherellc.com`
   - **Type:** A
   - **Value:** ALIAS to your OCI domain
   - **Routing policy:** Weighted
   - **Set ID:** `OCI-Primary`
   - **Weight:** 100
   - **Health check:** Select OCI health check from #2.2
   - **Save**

   **Record 2 — Railway Failover:**
   - **Record name:** `api.profitengine.alreadyherellc.com`
   - **Type:** A
   - **Value:** ALIAS to your Railway domain
   - **Routing policy:** Weighted
   - **Set ID:** `Railway-Failover`
   - **Weight:** 0 (inactive until OCI fails)
   - **Health check:** Select Railway health check from #2.3
   - **Save**

### 2.5 Test DNS Resolution
```bash
# Should resolve to OCI initially
dig api.profitengine.alreadyherellc.com

# Should return OCI IP (129.146.167.73)
```

---

## Part 3: Test Failover (30 min)

### 3.1 Manual Failover Test
1. **Stop OCI instance** (or simulate failure by stopping the runtime service)
2. **Wait 60-90 seconds** (2 health check failures + DNS propagation)
3. **Run DNS check:**
   ```bash
   dig api.profitengine.alreadyherellc.com
   ```
   Should now resolve to Railway IP

4. **Test API still works:**
   ```bash
   curl https://api.profitengine.alreadyherellc.com/health
   # Should return 200 OK (from Railway)
   ```

5. **Restart OCI instance**
6. **Wait 60 seconds**
7. **Run DNS check again:**
   ```bash
   dig api.profitengine.alreadyherellc.com
   # Should be back to OCI IP
   ```

### 3.2 Production Simulation (Optional)
Send actual requests during failover:
```bash
# Terminal 1: Continuous health check
while true; do
  curl -s https://api.profitengine.alreadyherellc.com/health
  sleep 5
done

# Terminal 2: Stop OCI (simulate crash)
# You should see uninterrupted responses despite OCI being down
```

---

## Part 4: Monitoring & Alerts (15 min)

### 4.1 Setup CloudWatch Alarms (Optional)
In AWS:
1. CloudWatch → Alarms
2. Create alarm for Route 53 health checks
3. Trigger: "Health check unhealthy"
4. Action: SNS notification to your email

### 4.2 Monitor Railway Deployment
1. Setup GitHub → Railway auto-deployments:
   - Railway auto-redeploys on commits to `main`
   - Or use Railway deploy hooks in GitHub Actions

2. Setup monitoring:
   - Railway dashboard shows CPU, memory, logs
   - Check daily that Railway is running

---

## Part 5: Cleanup & Documentation (15 min)

### 5.1 Update DNS Records
Verify final setup:
```bash
dig api.profitengine.alreadyherellc.com +short
# Should show both IPs (weighted)

nslookup api.profitengine.alreadyherellc.com
# Should show Route 53 name servers
```

### 5.2 Document in CLAUDE.md
Update your project instructions:
```markdown
## Runtime Failover Setup

- Primary: OCI Instance (129.146.167.73)
- Failover: Railway (runtime-prod.railway.app)
- Routing: Route 53 weighted failover
- Health check interval: 30 seconds
- Failover time: ~60 seconds (2 failures + DNS)

Manual failover test:
1. Stop OCI instance
2. Wait 90 seconds
3. Verify: curl https://api.profitengine.alreadyherellc.com/health
4. Should resolve to Railway and return 200
```

### 5.3 Update ops-monitor.yml
Add Railway to health checks:
```yaml
check "Railway Standby" "https://runtime-prod.railway.app/health"
```

---

## Troubleshooting

### Health Check Shows "Unhealthy"
- Verify `/health` endpoint is working on that instance
- Check security groups (Route 53 IP ranges must be allowed)
- Verify domain/IP is correct

### DNS Not Switching to Failover
- Check health check status in Route 53 console (should show red ❌ for failed)
- Wait 60 seconds (2 failures × 30s interval)
- Verify weight is 0 for failover (becomes 100 when active)

### Railway Deployment Failing
- Check logs in Railway console
- Verify all env vars are set
- Check database connectivity from Railway
- Verify API keys are valid

### High Latency During Failover
- Route 53 failover is typically < 100ms
- DNS propagation can take 10-30 seconds
- This is normal, expected behavior

---

## Cost Verification

```
Route 53:
  - Health checks: 3 × $0.50/month = $1.50
  - DNS queries: ~100k/month = $0.50
  Subtotal: ~$2/month

Railway:
  - Runtime service: $5/month (eco)
  - PostgreSQL (if hosted): varies
  Subtotal: ~$5-15/month

Total: ~$7-17/month
  (vs $500+ cost of 1 hour downtime)
```

---

## Success Criteria

✅ Railway deployment is green in console  
✅ Health check returns 200 from Railway  
✅ Route 53 health checks show healthy  
✅ DNS test shows both OCI and Railway in weighted set  
✅ Manual failover test: OCI down → traffic routes to Railway  
✅ Manual failover test: OCI up → traffic routes back to OCI  
✅ Failover completes in < 90 seconds  
✅ No data loss during failover  
✅ Services resume without manual intervention  

---

## Next Steps

After this setup:
1. ✅ Monitor for 1 week
2. ✅ Schedule quarterly failover tests
3. ✅ Consider upgrading to Lambda (true serverless)
4. ✅ Document in runbooks

---

**Timeline:** 2-3 hours  
**Cost:** $7-17/month  
**MTTR before:** 24+ hours  
**MTTR after:** ~1 minute  
**Worth it:** Absolutely ✅

Start with Part 1 (Railway deployment) — that's the biggest win.
