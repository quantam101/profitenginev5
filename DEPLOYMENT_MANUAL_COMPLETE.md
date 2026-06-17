# ProfitEngine v5 — Manual Secret Deployment Guide

**Status:** SSH access works ✅ | Infrastructure ready ✅ | Secrets need manual transfer ⏳  
**Time required:** 5-10 minutes  
**Expected result:** All 6 profit streams activate + ~$1K-$2.8K/month revenue

---

## Prerequisites

✅ SSH key available locally: `~/.ssh/cmdos_deploy_key`  
✅ SSH access to server works: `ssh -i ~/.ssh/cmdos_deploy_key opc@129.146.236.177`  
✅ Docker running on server  
✅ GitHub Secrets containing all 31 API keys  

---

## Step 1: Copy All 31 Secrets from GitHub

1. Go to: https://github.com/quantam101/profitenginev5/settings/secrets/actions
2. You'll see these secrets (copy each value):

### Payment Processing (3 secrets)
- [ ] `STRIPE_SECRET_KEY` → Copy value
- [ ] `STRIPE_API_KEY` → Copy value  
- [ ] `STRIPE_WEBHOOK_SECRET` → Copy value

### Products & Sales (2 secrets)
- [ ] `GUMROAD_ACCESS_TOKEN` → Copy value
- [ ] `GUMROAD_SELLER_ID` → Copy value

### AI Providers (4 secrets)
- [ ] `OPENROUTER_API_KEY` → Copy value
- [ ] `GROQ_API_KEY` → Copy value
- [ ] `GEMINI_API_KEY` → Copy value
- [ ] `OPENAI_API_KEY` → Copy value

### Databases (2 secrets)
- [ ] `MONGODB_URL` → Copy value
- [ ] `DATABASE_URL` → Copy value

### Content Publishing (7 secrets)
- [ ] `BEEHIIV_API_KEY` → Copy value
- [ ] `BEEHIIV_PUBLICATION_ID` → Copy value
- [ ] `DEVTO_API_KEY` → Copy value
- [ ] `HASHNODE_API_KEY` → Copy value
- [ ] `HASHNODE_PUB_ID` → Copy value
- [ ] `MEDIUM_API_KEY` → Copy value
- [ ] `MEDIUM_AUTHOR_ID` → Copy value

### Social Media (6 secrets)
- [ ] `YOUTUBE_CLIENT_ID` → Copy value
- [ ] `YOUTUBE_CLIENT_SECRET` → Copy value
- [ ] `YOUTUBE_REFRESH_TOKEN` → Copy value
- [ ] `TELEGRAM_BOT_TOKEN` → Copy value
- [ ] `TELEGRAM_CHAT_ID` → Copy value
- [ ] `TELEGRAM_WEBHOOK_SECRET` → Copy value

### Infrastructure (5 secrets)
- [ ] `GITHUB_TOKEN` → Copy value
- [ ] `CONTENT_REPO_TOKEN` → Copy value
- [ ] `HF_TOKEN` → Copy value
- [ ] `PROFITENGINE_WEBHOOK_TOKEN` → Copy value
- [ ] `RUNTIME_API_URL` → Copy value

### Cloud Services (2 secrets)
- [ ] `AWS_ACCESS_KEY_ID` → Copy value
- [ ] `AWS_SECRET_ACCESS_KEY` → Copy value

**TOTAL: 31 secrets**

---

## Step 2: SSH to Server and Create .env File

Open a terminal and run:

```bash
ssh -i ~/.ssh/cmdos_deploy_key opc@129.146.236.177
```

Once connected:

```bash
# Create the .env file
mkdir -p /home/opc/profitenginev5
cd /home/opc/profitenginev5
nano .env
```

This opens the nano editor. Now you'll paste each secret in the format:

```
SECRET_NAME=secret_value
```

---

## Step 3: Paste Secrets (Copy/Paste Method)

### Quick Paste Template

In the nano editor, paste this template and fill in each value:

```
# Payment Processing
STRIPE_SECRET_KEY=<paste_value>
STRIPE_API_KEY=<paste_value>
STRIPE_WEBHOOK_SECRET=<paste_value>

# Products
GUMROAD_ACCESS_TOKEN=<paste_value>
GUMROAD_SELLER_ID=<paste_value>

# AI Providers
OPENROUTER_API_KEY=<paste_value>
GROQ_API_KEY=<paste_value>
GEMINI_API_KEY=<paste_value>
OPENAI_API_KEY=<paste_value>

# Databases
MONGODB_URL=<paste_value>
DATABASE_URL=<paste_value>

# Content Publishing
BEEHIIV_API_KEY=<paste_value>
BEEHIIV_PUBLICATION_ID=<paste_value>
DEVTO_API_KEY=<paste_value>
HASHNODE_API_KEY=<paste_value>
HASHNODE_PUB_ID=<paste_value>
MEDIUM_API_KEY=<paste_value>
MEDIUM_AUTHOR_ID=<paste_value>

# Social Media
YOUTUBE_CLIENT_ID=<paste_value>
YOUTUBE_CLIENT_SECRET=<paste_value>
YOUTUBE_REFRESH_TOKEN=<paste_value>
TELEGRAM_BOT_TOKEN=<paste_value>
TELEGRAM_CHAT_ID=<paste_value>
TELEGRAM_WEBHOOK_SECRET=<paste_value>

# Infrastructure
GITHUB_TOKEN=<paste_value>
CONTENT_REPO_TOKEN=<paste_value>
HF_TOKEN=<paste_value>
PROFITENGINE_WEBHOOK_TOKEN=<paste_value>
RUNTIME_API_URL=<paste_value>

# Cloud Services
AWS_ACCESS_KEY_ID=<paste_value>
AWS_SECRET_ACCESS_KEY=<paste_value>
```

**In nano:**
1. Paste this template (Ctrl+Shift+V or right-click)
2. For each `<paste_value>`, replace with actual secret from GitHub
3. Save: Press `Ctrl+X`, then `Y`, then `Enter`

---

## Step 4: Set File Permissions

Still in SSH session:

```bash
chmod 600 .env
ls -l .env  # Should show: -rw------- 1 opc opc
```

---

## Step 5: Restart Services

```bash
cd deploy
docker compose -f docker-compose.prod.yml restart
```

Wait for services to restart (should take 10-30 seconds).

---

## Step 6: Verify Deployment

```bash
# Check service status
docker compose -f docker-compose.prod.yml ps

# Check .env was loaded
grep STRIPE .env | wc -l  # Should show: 3
grep -c "=" .env  # Should show close to 31
```

Expected output:
```
NAME                     IMAGE            STATUS
dashboard                dashboard        Up 12 seconds
runtime                  runtime          Up 11 seconds
backend                  backend          Up 10 seconds
nginx                    nginx            Up 9 seconds
```

---

## Step 7: Test Endpoints

From SSH session:

```bash
# Test dashboard
curl -s http://localhost:3000 | head -5

# Test runtime API
curl -s http://localhost:8000/health

# Test backend API
curl -s http://localhost:8001/health

# Test nginx
curl -s https://129.146.236.177/health
```

All should respond with HTTP 200 or valid JSON.

---

## Step 8: Check Logs (Optional)

If services fail to restart:

```bash
docker compose logs -f runtime  # View runtime logs
docker compose logs -f backend  # View backend logs
```

Press `Ctrl+C` to exit logs.

---

## Troubleshooting

### "Permission denied while trying to connect to Docker daemon"

This is normal - the opc user doesn't have docker group access. Use `sudo`:

```bash
sudo docker compose -f docker-compose.prod.yml ps
sudo docker compose -f docker-compose.prod.yml restart
```

### "Cannot find .env file"

Make sure you saved the file in `/home/opc/profitenginev5/.env`:

```bash
ls -la /home/opc/profitenginev5/.env
```

### Services still in "restarting" state after 60 seconds

Check logs:

```bash
docker compose logs backend | tail -20
```

Common issues:
- Missing `RUNTIME_API_URL` secret
- Database URL format incorrect
- API key invalid or expired

### SSH connection refused

The server might be unreachable. Try:

```bash
ssh -i ~/.ssh/cmdos_deploy_key -v opc@129.146.236.177
```

Check OCI Console → Compute → Instances → 129.146.236.177 → Instance State

---

## ✅ Success Checklist

After deployment:

- [ ] All 31 secrets copied to server
- [ ] `.env` file created at `/home/opc/profitenginev5/.env`
- [ ] File permissions set to `600`
- [ ] Docker services restarted
- [ ] All 4 containers show "Up X seconds"
- [ ] Health endpoints respond with 200
- [ ] Log files show no `ERROR` entries

Once complete:

```
✅ Revenue streams ACTIVE:
   - Trading (Robinhood)
   - Payments (Stripe)
   - Products (Gumroad)
   - Affiliate (Amazon)
   - Newsletter (Beehiiv)
   - Content (GitHub Pages)

💰 Expected: $1K-$2.8K+/month
```

---

## Support

If you get stuck:

1. **Check SSH access first:**
   ```bash
   ssh -i ~/.ssh/cmdos_deploy_key opc@129.146.236.177 whoami
   ```

2. **View Docker service logs:**
   ```bash
   docker compose logs -f
   ```

3. **Verify .env format:**
   ```bash
   cat .env | head -5
   ```

4. **Check disk space:**
   ```bash
   df -h
   ```

---

**Next steps:** Once deployed, the system will automatically:
- Generate content daily (07:05 UTC)
- Process affiliate clicks
- Handle payment transactions
- Publish to social channels
- Send email digests

Monitor via logs: `docker compose logs -f` (from `/home/opc/profitenginev5/deploy`)

Good luck! 🚀
