# SSH Public Key Setup for CMDOS Deployment

**Purpose:** Enable passwordless SSH authentication for automated deployment  
**Target:** opc@129.146.236.177  
**Date:** 2026-06-17

---

## Option 1: Generate New SSH Key Pair (Recommended)

### Step 1: Generate SSH Key

```bash
# Generate new SSH key pair (Ed25519 - modern & secure)
ssh-keygen -t ed25519 -C "profitengine-deploy@cmdos" -f ~/.ssh/cmdos_deploy_key -N ""
```

This creates:
- Private key: `~/.ssh/cmdos_deploy_key` (keep secret)
- Public key: `~/.ssh/cmdos_deploy_key.pub` (share with server)

### Step 2: Display Public Key

```bash
cat ~/.ssh/cmdos_deploy_key.pub
```

**Output will look like:**
```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI... profitengine-deploy@cmdos
```

### Step 3: Copy Public Key to Server

**Option A: Using ssh-copy-id (easiest)**
```bash
ssh-copy-id -i ~/.ssh/cmdos_deploy_key.pub opc@129.146.236.177
```

**Option B: Manual setup (if ssh-copy-id not available)**
```bash
# Copy the public key
cat ~/.ssh/cmdos_deploy_key.pub

# Then SSH to server and add it:
ssh opc@129.146.236.177
mkdir -p ~/.ssh
cat >> ~/.ssh/authorized_keys << 'EOF'
# Paste the public key content here
EOF
chmod 600 ~/.ssh/authorized_keys
exit
```

### Step 4: Test SSH Connection

```bash
# Test with new key
ssh -i ~/.ssh/cmdos_deploy_key opc@129.146.236.177

# Should connect without password prompt
# If successful, type: exit
```

### Step 5: Configure SSH Config (Optional but Recommended)

Create/edit `~/.ssh/config`:

```bash
nano ~/.ssh/config
```

Add this configuration:

```
Host cmdos
    HostName 129.146.236.177
    User opc
    IdentityFile ~/.ssh/cmdos_deploy_key
    StrictHostKeyChecking no
    UserKnownHostsFile=/dev/null
    LogLevel=error
```

Now you can simply use:
```bash
ssh cmdos
```

---

## Option 2: Use Existing SSH Key

### If you already have an SSH key:

```bash
# Copy existing public key
cat ~/.ssh/id_rsa.pub

# Add to server
ssh opc@129.146.236.177
mkdir -p ~/.ssh
cat >> ~/.ssh/authorized_keys << 'EOF'
# Paste your existing public key here
EOF
```

---

## Option 3: GitHub Deploy Key Method

If you have a GitHub account with deploy keys:

```bash
# Get your GitHub SSH key
curl -u YOUR_GITHUB_USERNAME https://api.github.com/user/keys

# Or manually copy from:
# https://github.com/settings/keys

# Add to cmdos server authorized_keys
ssh opc@129.146.236.177
cat ~/.ssh/authorized_keys
# Verify your key is there
```

---

## ✅ Verification

Once setup is complete, verify:

```bash
# Should work without password
ssh opc@129.146.236.177 "echo 'SSH Access Verified!'"

# If it prompts for password, SSH key setup failed
# If it prints 'SSH Access Verified!', you're good!
```

---

## 🚀 Now Deploy

Once SSH works, run deployment:

```bash
# Direct SSH deployment
ssh opc@129.146.236.177 << 'DEPLOY_EOF'
#!/bin/bash
set -euo pipefail

APP_DIR="/home/opc/profitenginev5"
DEPLOY_DIR="$APP_DIR/deploy"

echo "[INFO] Starting deployment..."

# Update code
cd "$APP_DIR"
git pull origin main

# Create .env if needed
if [ ! -f "$APP_DIR/.env" ]; then
    cp .env.example .env
    echo "[WARNING] .env created - please configure secrets"
fi

# Deploy
cd "$DEPLOY_DIR"
docker compose -f docker-compose.prod.yml down 2>/dev/null || true
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d --build

sleep 15

echo "[INFO] Service status:"
docker compose -f docker-compose.prod.yml ps

echo ""
echo "[SUCCESS] Deployment Complete!"
echo "Dashboard: http://129.146.236.177:3000"
echo "Runtime: http://129.146.236.177:8000/health"
echo "Backend: http://129.146.236.177:8001/health"
DEPLOY_EOF
```

---

## 🔒 Security Notes

### Keep Private Key Secure
```bash
# Set correct permissions
chmod 600 ~/.ssh/cmdos_deploy_key

# Never commit to git
echo "~/.ssh/cmdos_deploy_key" >> .gitignore

# Never share the private key
# Only share the .pub file
```

### Server-Side Security
```bash
# On the server, verify authorized_keys permissions:
ssh opc@129.146.236.177 "chmod 600 ~/.ssh/authorized_keys && chmod 700 ~/.ssh"
```

### Key Rotation (Optional)
```bash
# Generate new key when needed
ssh-keygen -t ed25519 -C "profitengine-deploy-v2@cmdos" -f ~/.ssh/cmdos_deploy_key_v2 -N ""

# Add to server, then remove old key
```

---

## 🆘 Troubleshooting

### "Permission denied (publickey)"
- ✓ Verify public key is on server: `ssh cmdos "cat ~/.ssh/authorized_keys"`
- ✓ Check file permissions: `ssh cmdos "ls -la ~/.ssh"`
- ✓ Verify SSH service: `ssh cmdos "sudo systemctl status ssh"`

### "Could not open a connection"
- ✓ Check server is online: `ping 129.146.236.177`
- ✓ Check port 22: `curl -v ssh://129.146.236.177`
- ✓ Verify firewall allows SSH

### "Too many authentication failures"
- ✓ Clear SSH cache: `ssh-keygen -R 129.146.236.177`
- ✓ Retry with specific key: `ssh -i ~/.ssh/cmdos_deploy_key opc@129.146.236.177`

### Still having issues?
1. Verify key exists: `ls -la ~/.ssh/cmdos_deploy_key*`
2. Verify permissions: `chmod 600 ~/.ssh/cmdos_deploy_key`
3. Test manually: `ssh -vvv -i ~/.ssh/cmdos_deploy_key opc@129.146.236.177`
4. Check server logs: `ssh cmdos "sudo tail -20 /var/log/auth.log"`

---

## 📋 Quick Checklist

- [ ] SSH key generated (`ssh-keygen`)
- [ ] Public key copied to server
- [ ] SSH connection tested (no password prompt)
- [ ] SSH config created (optional)
- [ ] Private key permissions set to 600
- [ ] Ready for deployment

---

## 🚀 Next: Deploy Services

Once SSH is working:

```bash
ssh cmdos << 'EOF'
cd /home/opc/profitenginev5
git pull origin main
cp .env.example .env
nano .env  # Configure secrets
cd deploy
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml ps
EOF
```

---

**Status:** Ready for SSH Key Setup  
**Time Required:** 5-10 minutes  
**Difficulty:** Easy  
**Automation:** High (once key is set up)
