# 🚨 Runtime API Recovery Runbook

## Critical Facts
- **Primary backend**: OCI instance `cmdos` at `129.146.236.177` (Go + SQLite)
- **Detection**: Health check runs every 5 minutes (GitHub Actions)
- **Impact when down**: Lead intake, RFQ dispatch, affiliate attribution blocked
- **Typical MTTR**: 1-2 minutes (container restart) to 5 minutes (full reboot)

---

## ⚡ Emergency Recovery (< 5 min)

### Step 1: Check OCI Console Status
1. Log into **console.oracle.com**
2. Navigate to **Compute → Instances**
3. Find **cmdos** (Always Free E2.1.Micro)
4. Check the **State** column:
   - 🟢 **RUNNING** → Go to Step 2 (Reboot)
   - 🔴 **STOPPED** → Go to Step 3 (Start Instance)

### Step 2: Soft Reboot (if Instance is RUNNING but Unresponsive)
```
Instance Details → ⋮ (More Actions) → Reboot Instance
```
**Expected:** 
- Rebooting (1-2 min)
- Running (30 seconds to respond)
- Total: ~2-3 min back online

**Verify:**
```bash
curl https://api.profitengine.alreadyherellc.com/health
# Expected: HTTP 200 OK
```

### Step 3: Start Instance (if Instance is STOPPED)
```
Instance Details → ⋮ (More Actions) → Start
```
**Expected:**
- Provisioning (10-30 seconds)
- Running (2 min to boot and start services)
- Total: ~3-5 min back online

**Verify after 2 minutes:**
```bash
curl https://api.profitengine.alreadyherellc.com/health
# Expected: HTTP 200 OK
```

### Step 4: If Still Down (Hard Reboot)
```
1. Click ⋮ → Stop
2. Wait for STOPPED state
3. Click ⋮ → Start
```

---

## 🔍 Advanced Troubleshooting

### If Instance is RUNNING but Still Unreachable

**Option A: Serial Console**
1. Instance Details → **Troubleshoot** → **Serial Console**
2. This opens a terminal into the instance
3. Check if system is responsive: `ps aux`
4. Check Docker: `docker ps`

**Option B: SSH via Cloud Shell**
```bash
# From OCI Console, open Cloud Shell
ssh opc@129.146.236.177

# Check Docker containers
docker ps

# Check backend logs
docker logs -f alreadyhere-backend --tail 50

# Restart containers if needed
docker compose -f /opt/alreadyhere-backend/docker-compose.yml restart
```

### If Network is the Issue
1. Check **Network → Virtual Cloud Networks → (your VCN)**
2. Check **Security Lists** — verify:
   - SSH (port 22): 0.0.0.0/0 ingress allowed
   - HTTPS (port 443): 0.0.0.0/0 ingress allowed
   - HTTP (port 80): 0.0.0.0/0 ingress allowed (for redirect)

---

## 📊 Expected Endpoints

| Endpoint | Method | Expected Response |
|----------|--------|-------------------|
| `https://api.profitengine.alreadyherellc.com/health` | GET | HTTP 200, `{"status": "ok"}` |
| `http://129.146.236.177/health` | GET | HTTP 200 (internal check) |
| `https://profitengine-tau.vercel.app` | GET | HTTP 200 (frontend, Vercel) |

---

## 🤖 Automated Recovery (Hands-Off)

GitHub Actions health check runs every 5 minutes. When Runtime API is down:

1. ✅ Creates GitHub Issue with `runtime-critical` label
2. ✅ Triggers `oci-runtime-mirror-deploy.yml` workflow
3. ⚠️ If that fails (SSH timeout), manual intervention required

**To manually trigger redeploy:**
```bash
gh workflow run oci-runtime-mirror-deploy.yml --ref main
```

---

## 🛡️ Prevention

### Instance Resilience
- [ ] Enable automatic restart on crash (OCI Console → Instance Options)
- [ ] Set up Litestream backup for SQLite database
- [ ] Monitor disk usage (70% guard as per project rules)

### Monitoring Improvements
- [ ] Add PagerDuty/Slack alerts to GitHub Actions
- [ ] Add 3-minute threshold alert (if 2+ health checks fail in a row)
- [ ] Weekly "healthy week" report

### OCI Instance Resilience
- [ ] Enable automatic restart on crash (OCI Console → Instance Options)
- [ ] Increase OCI always-free budget if hitting limits
- [ ] Document all critical services running on the instance

---

## 📞 Escalation Path

| Symptom | First Action | Second Action | Escalation |
|---------|--------------|---------------|------------|
| Runtime API timeout (< 3 min) | Reboot instance | Check OCI Console | SSH via Serial Console |
| OCI instance down (> 5 min) | Start instance | Check billing/resource limits | OCI Support |
| Persistent network issues | Check Security Lists | Check VCN routing | ISP/Network support |
| GitHub Actions workflow failing | Manually trigger redeploy | Check deploy key SSH | Re-add SSH key to OCI |

---

## ✅ Verification Checklist

After recovery, verify all systems:

```bash
# 1. Runtime API health
curl -v https://api.profitengine.alreadyherellc.com/health

# 2. Docker containers running
ssh opc@129.146.236.177 'docker ps'

# 3. Frontend still works
curl https://profitengine-tau.vercel.app

# 4. Services resuming
# - Newsletter publishing should resume next scheduled time
# - Telegram digest should run at next scheduled time (07:05 UTC)
# - AI operations should process queued requests
```

---

**Last Updated:** 2026-06-14
**Maintained By:** quantam101
**Severity:** 🔴 CRITICAL (P0 — blocks all revenue)
