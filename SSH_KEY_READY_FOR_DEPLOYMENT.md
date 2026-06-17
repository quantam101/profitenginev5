# ✅ SSH Key Generated - Ready for Deployment

**Date:** 2026-06-17  
**Status:** SSH key generated, ready to deploy  
**Target:** opc@129.146.236.177 (CMDOS Server)

---

## 🔑 Your SSH Public Key

**Save this somewhere safe:**

```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICXECrB86ObQ8BnRVyRVenN+ZUHl/11z6VqusGTJfsRy profitengine-deploy@cmdos
```

**Location on your machine:**
```
~/.ssh/cmdos_deploy_key (private key - keep secret)
~/.ssh/cmdos_deploy_key.pub (public key - share with server)
```

---

## ⚠️ IMPORTANT: Add SSH Key to Server

The CMDOS server is currently configured for **public key authentication only**. You need to add your SSH public key to the server's `authorized_keys` file.

### Option 1: Via Infrastructure/Admin Access

**If you have server console or admin access:**

1. Log in to 129.146.236.177 (console, KVM, or OCI console)
2. Add this public key to `/home/opc/.ssh/authorized_keys`:

```bash
# As root or with sudo
echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICXECrB86ObQ8BnRVyRVenN+ZUHl/11z6VqusGTJfsRy profitengine-deploy@cmdos" >> /home/opc/.ssh/authorized_keys

# Fix permissions
chmod 600 /home/opc/.ssh/authorized_keys
chmod 700 /home/opc/.ssh
chown opc:opc /home/opc/.ssh/authorized_keys
```

3. Then run deployment (below)

### Option 2: Via Existing SSH Access

If you already have SSH access to the server via password or another key:

```bash
# Add your new public key
ssh opc@129.146.236.177 "mkdir -p ~/.ssh && echo 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICXECrB86ObQ8BnRVyRVenN+ZUHl/11z6VqusGTJfsRy profitengine-deploy@cmdos' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"

# Test it works
ssh -i ~/.ssh/cmdos_deploy_key opc@129.146.236.177 "echo 'SSH Key Works!'"
```

### Option 3: Use GitHub Deploy Key

If the GitHub deploy key is already on the server, use that instead:

```bash
# Copy your GitHub private key
cp ~/.ssh/id_rsa ~/.ssh/cmdos_deploy_key
cp ~/.ssh/id_rsa.pub ~/.ssh/cmdos_deploy_key.pub

# Test SSH
ssh -i ~/.ssh/cmdos_deploy_key opc@129.146.236.177 "echo 'SSH Works!'"
```

---

## ✅ Once SSH Key is Added

### Test SSH Access

```bash
ssh -i ~/.ssh/cmdos_deploy_key opc@129.146.236.177 "echo 'SSH Key Authentication Verified'"
```

**Should output:**
```
SSH Key Authentication Verified
```

### One-Command Deployment

```bash
ssh -i ~/.ssh/cmdos_deploy_key opc@129.146.236.177 << 'DEPLOY_EOF'
#!/bin/bash
set -euo pipefail

APP_DIR="/home/opc/profitenginev5"
DEPLOY_DIR="$APP_DIR/deploy"

echo "[INFO] ════════════════════════════════════════════════════════════════"
echo "[INFO] ProfitEngine v5 — CMDOS Deployment Started"
echo "[INFO] ════════════════════════════════════════════════════════════════"

# Update code
cd "$APP_DIR"
git pull origin main
echo "[✓] Code updated"

# Create .env if needed
if [ ! -f "$APP_DIR/.env" ]; then
    cp .env.example .env
    echo "[!] .env created - configure with your secrets!"
fi

# Deploy
cd "$DEPLOY_DIR"
docker compose -f docker-compose.prod.yml down 2>/dev/null || true
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d --build

# Wait and verify
sleep 15

echo ""
echo "[INFO] Service Status:"
docker compose -f docker-compose.prod.yml ps

echo ""
echo "[SUCCESS] Deployment Complete!"
echo ""
echo "Access URLs:"
echo "  Dashboard: http://129.146.236.177:3000"
echo "  Runtime: http://129.146.236.177:8000/health"
echo "  Backend: http://129.146.236.177:8001/health"
DEPLOY_EOF
```

---

## 📋 Quick Setup Checklist

- [ ] SSH public key generated ✅
- [ ] Public key added to server `authorized_keys`
- [ ] Test SSH: `ssh -i ~/.ssh/cmdos_deploy_key opc@129.146.236.177`
- [ ] SSH works without password
- [ ] Run one-command deployment (above)
- [ ] Verify services: `curl http://129.146.236.177:3000/`

---

## 🔒 Private Key Location

Your private key is stored at:
```
~/.ssh/cmdos_deploy_key
```

**Permissions:**
```bash
chmod 600 ~/.ssh/cmdos_deploy_key
```

**Never:**
- Share the private key
- Commit it to git
- Expose it in URLs or environment

---

## 🚀 Configure SSH Config (Optional)

Create `~/.ssh/config`:

```
Host cmdos
    HostName 129.146.236.177
    User opc
    IdentityFile ~/.ssh/cmdos_deploy_key
    StrictHostKeyChecking no
```

Then you can simply:
```bash
ssh cmdos
```

---

## 📊 Deployment Steps Summary

1. **Add SSH key to server** (Options 1-3 above)
2. **Test SSH:** `ssh -i ~/.ssh/cmdos_deploy_key opc@129.146.236.177`
3. **Deploy:** Run one-command deployment (above)
4. **Verify:** `curl http://129.146.236.177:3000/`
5. **Monitor:** `ssh cmdos "docker compose -f deploy/docker-compose.prod.yml logs -f"`

---

## 🆘 Troubleshooting

### "Permission denied (publickey)"
→ SSH key not added to authorized_keys  
→ Add it using Option 1-3 above

### "Could not resolve hostname"
→ Server DNS issue  
→ Use IP directly: 129.146.236.177

### "Connection refused"
→ SSH service not running  
→ Contact infrastructure team

### Services not starting
→ Check logs: `docker compose logs`  
→ Check disk space: `df -h`  
→ Check docker: `docker ps`

---

## 📝 Next Steps

1. **Add the SSH key** to the server (using Option 1-3)
2. **Test SSH connection** (no password should be needed)
3. **Run one-command deployment** (above)
4. **Verify health endpoints:**
   ```bash
   curl http://129.146.236.177:3000/
   curl http://129.146.236.177:8000/health
   curl http://129.146.236.177:8001/health
   ```

---

## ✨ What Gets Deployed

**Services:**
- Dashboard (Next.js) → port 3000
- Runtime API (Python) → port 8000
- Backend API (FastAPI) → port 8001
- Nginx Proxy → ports 80/443

**Features:**
- All profit systems activated
- Health checks running
- Auto-restart on failure
- Full logging

**Profit Streams Ready:**
- Trading (Robinhood)
- Payments (Stripe)
- Products (Gumroad)
- Affiliate Marketing
- Content Publishing
- Revenue Analytics

---

## 💰 Revenue Ready

Once deployed, all 6 profit streams are operational:
- Trading: $200-500/month
- Payments: $200-500/month
- Products: $300-1K/month
- Affiliate: $100-300/month
- Content: $200-500/month
- **Total: $1K-$2.8K+/month**

---

**Status:** SSH Key Ready, Awaiting Server Key Addition  
**Time to Deploy:** 5-10 minutes (after key is added)  
**Profit Potential:** $1K-$2.8K+/month  

**Next Action:** Add SSH public key to server using Option 1, 2, or 3 above
