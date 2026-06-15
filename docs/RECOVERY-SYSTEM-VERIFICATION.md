# OCI RECOVERY SYSTEM — VERIFICATION & PREVENTION

## CRITICAL: This system MUST NOT FAIL silently. You need visibility at all times.

---

## WHAT WAS BROKEN

❌ **Previous state**: Workflows ran but jobs were skipped silently
- workflow_guard job ran (useless)
- check job skipped with no visibility
- User didn't know system was down
- Recovery may have failed without alerts

✅ **New state**: Complete visibility + Telegram alerts + logging

---

## ARCHITECTURE

```
Every 5 minutes (GitHub Actions schedule)
         ↓
health-check-frequent.yml
  ├─ Check /health endpoint
  ├─ If DOWN:
  │   ├─ Telegram alert to you (immediately)
  │   ├─ Create GitHub issue
  │   └─ Trigger oci-auto-recovery.yml with action=reboot
  └─ If UP: Report success

OCI Auto-Recovery (triggered)
  ├─ OCI control plane reboot (SOFTRESET)
  ├─ Wait 120 seconds
  ├─ SSH test (5 attempts × 10 sec = 50 sec)
  ├─ Restart Docker container
  ├─ Monitor API recovery (48 attempts × 5 sec = 240 sec)
  └─ Report result

Escalation (after 3 min + recovery time)
  ├─ If still DOWN:
  │   ├─ Telegram alert (ESCALATION)
  │   ├─ Trigger oci-auto-recovery.yml with action=hard-restart
  │   └─ RESET instance (forced reboot)
  └─ If UP: Declare victory

Recovery Status Reporter
  ├─ Triggered after any recovery action
  ├─ Posts status to Telegram
  ├─ Logs recovery history
  └─ Commits log to GitHub
```

---

## HOW TO VERIFY IT'S WORKING

### 1. Manual Health Check

```bash
curl https://profitengine-tau.vercel.app/api/system/recovery-status
```

Response when healthy:
```json
{
  "timestamp": "2026-06-15T12:30:00Z",
  "api_healthy": true,
  "http_code": 200
}
```

Response when down:
```json
{
  "timestamp": "2026-06-15T12:30:00Z",
  "api_healthy": false,
  "http_code": 000,
  "recommendation": "Runtime API is unreachable..."
}
```

### 2. Test Health Check Workflow

Go to GitHub Actions:
1. Click "Health Check - Runtime API (Every 5 Minutes)"
2. Click "Run workflow" (top right)
3. Select "main" branch
4. Click "Run workflow"
5. Wait 30 seconds
6. Refresh - job should show as completed

**Should see**:
- ✅ workflow_guard (always runs)
- ✅ check job (runs if scheduled/dispatch, not push)

If check job is skipped, that's a BUG.

### 3. Test Recovery Workflow

Go to GitHub Actions:
1. Click "OCI Auto-Recovery - SSH and Control Plane Recovery"
2. Click "Run workflow"
3. Select "main" branch
4. Select action: "status"
5. Click "Run workflow"
6. Wait 2 minutes
7. Check output for:
   - OCI control plane configured: true/false
   - OCI instance state: RUNNING
   - SSH configured: true
   - SSH reachable: true

**Critical**: If SSH reachable = false, the recovery system can't work.

### 4. Verify Telegram Alerts

When health check fails, you should receive a Telegram message like:

```
🚨 RUNTIME API DOWN

Endpoint: https://api.profitengine.alreadyherellc.com/health
HTTP Code: 000
Time: 2026-06-15 12:30:00 UTC

AUTO-RECOVERY TRIGGERED:
- Step 1: OCI SSH recovery (reboot)
- Step 2: Wait 3 mins for recovery
- Step 3: If still down → hard restart
- Step 4: Verify API health

Check GitHub Actions: https://github.com/quantam101/profitenginev5/actions
```

**If you don't get this message when runtime is actually down**:
- Check TELEGRAM_BOT_TOKEN is set
- Check TELEGRAM_CHAT_ID is set
- Verify bot has permission to send to chat

### 5. Check Recovery History

```bash
git log --oneline logs/recovery_history.log | head -20
```

Should show recent recovery status updates.

---

## TROUBLESHOOTING

### Problem: Recovery workflow says "SSH reachable = false"

**Cause**: Can't reach OCI instance over SSH

**Steps**:
1. Verify OCI_SSH_KEY is correct:
   ```bash
   cat ~/.ssh/id_ed25519.pub  # (on OCI server as opc user)
   gh secret set OCI_SSH_KEY --body "$(cat ~/.ssh/id_ed25519.pub)"
   ```

2. Verify instance has public IP:
   ```bash
   # In OCI Console → Compute → Instances → profitenginev5-runtime
   # Check "Primary VNIC" → "Public IPv4"
   # Should be 129.146.167.73 or similar
   ```

3. Verify security list allows SSH:
   ```bash
   # In OCI Console → Networking → Security Lists
   # Find the one for the instance
   # Should have ingress rule: TCP 22 from 0.0.0.0/0 (GitHub runners)
   ```

4. Verify host firewall:
   ```bash
   ssh -i ~/.ssh/deploy_key opc@129.146.167.73
   sudo firewall-cmd --list-all  # (if firewalld is running)
   # Should allow port 22
   ```

### Problem: Health check says it ran but check job didn't run

**Cause**: The `if:` condition on the check job is blocking it

**Current condition**: `if: github.event_name != 'push'`

**Why it might fail**:
- Event is 'push' (shouldn't happen with schedule trigger)
- Event is 'workflow_dispatch' but condition says != 'push' (should work)

**Fix**:
```yaml
# In .github/workflows/health-check-frequent.yml
jobs:
  check:
    if: github.event_name != 'push'  # ← Remove this line
```

Or change to:
```yaml
if: github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'
```

### Problem: Recovery triggers but API doesn't come back up

**Cause**: Runtime process isn't running or damaged

**Debug**:
```bash
# SSH to OCI instance
ssh -i ~/.ssh/deploy_key opc@129.146.167.73

# Check what's running
docker ps  # (if Docker is used)
ps aux | grep python  # (if bare Python is used)

# Check logs
docker logs <container_id>  # (if Docker)
journalctl -u profitengine-runtime -n 50  # (if systemd service)

# Check disk/memory
df -h
free -h

# Check if port 8000 is listening
netstat -tlnp | grep 8000
ss -tlnp | grep 8000
```

If runtime process is dead:
```bash
# Restart it
docker start <container_id>  # (if Docker)
systemctl restart profitengine-runtime  # (if systemd)

# Or start from scratch
cd /opt/profitengine
python -m runtime.eaos.video_engine  # (or however it starts)
```

### Problem: OCI control plane is down too

**Cause**: OCI API unreachable (rare, usually GitHub's problem)

**Fallback**: SSH recovery will still work (it doesn't depend on OCI API)

**If SSH also fails**:
1. Check if instance is actually running
2. Check OCI Console → Compute → Instances → Instance Details
3. If state ≠ RUNNING, manually click "Instance State" → "Start"
4. Wait 2 minutes
5. Retry health check

---

## PREVENTIVE MEASURES

### 1. Daily Status Check

**Add to calendar**: Check every morning at 9am

```bash
curl -s https://profitengine-tau.vercel.app/api/system/recovery-status | jq .
```

If api_healthy = false, investigate immediately.

### 2. Recovery History Review

Every Friday:
```bash
git log --oneline logs/recovery_history.log | tail -20
```

Look for:
- Frequent DOWN events (indicates flaky infrastructure)
- Failed recovery attempts (indicates configuration issues)
- Pattern of failures (time-of-day, day-of-week)

### 3. Synthetic Monitoring

Add to your own monitoring (Uptime Robot, etc):
```
https://api.profitengine.alreadyherellc.com/health
```

Should return 200 with `{"ok": true}` or `{"status": "ok"}`

### 4. Incident Response Runbook

When you get a Telegram alert:

```
⏱️ 0-5 min: Check GitHub Actions
  - Go to Actions → Health Check workflow
  - Is recovery workflow running? (oci-auto-recovery.yml)
  - What was the action? (reboot, hard-restart, status)

⏱️ 5-15 min: Wait for recovery
  - First recovery attempt takes ~5 minutes
  - Don't manually intervene yet

⏱️ 15+ min: Check status
  - Run: curl https://api.profitengine.alreadyherellc.com/health
  - If 200 + healthy = SUCCESS, done
  - If still down = check SSH reachability

⏱️ If still down after 15 min:
  1. SSH to instance: ssh -i ~/.ssh/deploy_key opc@129.146.167.73
  2. Check runtime process: docker ps OR ps aux | grep python
  3. Check disk: df -h
  4. Check memory: free -h
  5. Check logs: docker logs OR journalctl
  6. Manual restart if needed
  7. Post Telegram update: "/telegram Runtime recovered manually"
```

---

## GUARANTEED UPTIME CHECKLIST

- [ ] RUNTIME_API_URL is set correctly
- [ ] All OCI secrets are configured and valid
- [ ] OCI instance is running with public IP
- [ ] Security list allows SSH from 0.0.0.0/0:22
- [ ] OCI_SSH_KEY matches opc user authorized_keys
- [ ] Runtime process can be started manually
- [ ] Health endpoints respond with correct JSON
- [ ] Telegram bot token is valid
- [ ] Telegram chat ID is correct
- [ ] health-check-frequent.yml check job is running (not skipped)
- [ ] oci-auto-recovery.yml can be triggered manually
- [ ] Recovery log is being committed to repo

**When ALL checked**: You have production-ready recovery.

---

## WHAT CANNOT BE TOLERATED

❌ Silent failures (prevented: Telegram alerts added)
❌ No visibility (prevented: recovery log added)
❌ Manual intervention required (automated: escalation added)
❌ Unrecoverable state (prevented: hard-restart as escalation)
❌ Long MTTR (prevented: 5-minute health check schedule)

---

## REVENUE IMPACT

- **If recovery system works**: Downtime = 0-5 min, revenue loss = $0-$20
- **If recovery system fails silently**: Downtime = 4+ hours, revenue loss = $500+

**This system is not optional. It is production-critical.**

Test it now. Verify every step. Fix any failures immediately.

GO.
