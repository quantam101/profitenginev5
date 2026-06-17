# ProfitEngine v5 — Docker Restart Guide

**Status:** ⚠️ Services need restart with sudo access

---

## What We Found

✅ **Completed:**
- Killed old uvicorn process (PID 625041) that was blocking port 8001
- All 59 secrets deployed to server
- Docker daemon and docker-proxy processes running
- Docker compose file ready

❌ **Blocked:**
- Need `sudo` password to restart Docker containers
- Non-interactive SSH can't prompt for sudo password

---

## How to Complete This

You have two options:

### Option 1: Restart via Interactive SSH (Easiest)

Open your terminal and run:

```bash
ssh -i ~/.ssh/cmdos_recovery_key opc@129.146.236.177
```

You'll be logged into the server. Then run:

```bash
cd /home/opc/profitenginev5/deploy

# This will ask for your sudo password
sudo docker compose restart runtime backend

# Wait 10 seconds for containers to start
sleep 10

# Test if backend is responding
curl http://localhost:8001/api/health
```

**Expected response after restart:**
```json
{"ok": true, "status": "ok", "service": "profitengine-v5", "time": "2026-06-17T20:15:00Z"}
```

If you get that response, continue to "Activate Stores" section below.

---

### Option 2: Contact Root/Admin

If you don't have sudo password access, ask the server administrator to run:

```bash
cd /home/opc/profitenginev5/deploy
docker compose restart runtime backend
docker compose logs -f
```

Then wait for them to confirm services are running.

---

## Once Services Are Responding

### 1. Test Backend
```bash
curl http://localhost:8001/api/health
```

Should return: `{"ok": true, ...}`

### 2. Test Runtime  
```bash
curl http://localhost:8000/health
```

Should return: `{"ok": true, ...}`

### 3. Activate Gumroad Store
```bash
curl -X POST http://localhost:8000/products/bootstrap \
  -H "Content-Type: application/json" \
  -H "x-profitengine-signature: Bearer c8eb99e5c57b061cdb1cf48f3c0489c79c0f2b1badc936b3c3d20a104de33589" \
  -d '{}'
```

**Expected response:**
```json
{
  "ok": true,
  "products": [
    {"name": "AI Business Prompt Pack", "price": 2700, "status": "created"},
    {"name": "Real Estate Copywriting Kit", "price": 1900, "status": "created"},
    {"name": "Social Media Content Engine", "price": 1700, "status": "created"},
    {"name": "POD Design Prompt Bundle", "price": 2200, "status": "created"},
    {"name": "Programmatic SEO Starter Kit", "price": 2900, "status": "created"}
  ]
}
```

### 4. Check Social Platforms
```bash
curl http://localhost:8000/social/platforms
```

Will show connected platforms:
- ✅ Telegram (configured)
- ✅ YouTube (configured)
- ✅ GitHub (configured)
- ⏳ Twitter (needs token - can add TWITTER_TOKEN to .env)
- ⏳ LinkedIn (needs token - can add LINKEDIN_TOKEN to .env)
- ⏳ Facebook (needs token - can add FACEBOOK_TOKEN to .env)
- ⏳ Instagram (needs token - can add INSTAGRAM_TOKEN to .env)

### 5. Check Etsy Status
```bash
curl http://localhost:8000/etsy/status
```

Will show: `{"status": "ready_for_configuration"}`

To activate Etsy, add these to .env and restart:
```env
ETSY_API_KEY=your_key
ETSY_SHOP_ID=your_shop_id
ETSY_API_TOKEN=your_token
```

---

## Troubleshooting

**If restart doesn't work:**

```bash
# Check Docker compose status
sudo docker compose ps

# View service logs
sudo docker compose logs -f runtime backend

# Try full restart (down and up)
sudo docker compose down
sudo docker compose up -d

# Check if containers are running
sudo docker ps
```

**If you see "Connection refused" after restart:**
- Wait 30 seconds (containers take time to start)
- Check logs: `sudo docker compose logs backend`
- May need to rebuild: `sudo docker compose build --no-cache`

---

## Summary

| Step | Status | Action |
|------|--------|--------|
| 1. SSH to server | ✅ Done | `ssh -i ~/.ssh/cmdos_recovery_key opc@129.146.236.177` |
| 2. Kill old process | ✅ Done | Process PID 625041 killed |
| 3. Restart Docker | ⏳ Pending | Need sudo password |
| 4. Test backend | ⏳ Pending | `curl http://localhost:8001/api/health` |
| 5. Activate Gumroad | ⏳ Pending | `curl -X POST http://localhost:8000/products/bootstrap` |
| 6. Verify social | ⏳ Pending | `curl http://localhost:8000/social/platforms` |
| 7. Check Etsy | ⏳ Pending | `curl http://localhost:8000/etsy/status` |

---

**Next Step:** SSH to server with interactive terminal and run the sudo docker compose restart command with your password.
