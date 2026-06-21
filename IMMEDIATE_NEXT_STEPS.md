# IMMEDIATE: Configure Caddy SSL (10 minutes)

## Step-by-Step Instructions

### 1. SSH to OCI Backend
```bash
ssh opc@129.146.236.177
```

### 2. Copy & Paste This Complete Setup
```bash
# Set error handling
set -e

echo "========================================"
echo "Caddy SSL Setup for ProfitEngine"
echo "Domain: api.profitengine.alreadyherellc.com"
echo "Backend: localhost:8001"
echo "========================================"
echo ""

# Find Caddyfile
echo "[STEP 1] Locating Caddyfile..."
CADDY_FILE=$(sudo find / -name "Caddyfile" -type f 2>/dev/null | head -1)
if [ -z "$CADDY_FILE" ]; then
    CADDY_FILE="/etc/caddy/Caddyfile"
    sudo mkdir -p /etc/caddy
    sudo touch "$CADDY_FILE"
fi
echo "[OK] Caddyfile: $CADDY_FILE"

# Backup
echo "[STEP 2] Backing up configuration..."
sudo cp "$CADDY_FILE" "${CADDY_FILE}.backup.$(date +%s)"
echo "[OK] Backup created"

# Add configuration
echo "[STEP 3] Adding Caddy configuration..."
if ! sudo grep -q "api.profitengine.alreadyherellc.com" "$CADDY_FILE"; then
    sudo tee -a "$CADDY_FILE" > /dev/null << 'CADDY_CONFIG'

# ProfitEngine API Gateway (2026-06-21)
api.profitengine.alreadyherellc.com:443 {
    reverse_proxy localhost:8001
    encode gzip
    header -Server
    header X-Real-IP {http.request.remote.host}
    header X-Forwarded-For {http.request.header.X-Forwarded-For}
    header X-Forwarded-Proto "https"
    header Strict-Transport-Security "max-age=31536000; includeSubDomains"
    header X-Content-Type-Options "nosniff"
    header X-Frame-Options "DENY"
}

api.profitengine.alreadyherellc.com:80 {
    redir https://{host}{uri} permanent
}
CADDY_CONFIG
    echo "[OK] Configuration added"
fi

# Validate
echo "[STEP 4] Validating Caddyfile..."
if sudo caddy validate --config "$CADDY_FILE"; then
    echo "[OK] Syntax valid"
else
    echo "[ERROR] Invalid syntax - fix errors above"
    exit 1
fi

# Reload
echo "[STEP 5] Reloading Caddy..."
sudo systemctl reload caddy && echo "[OK] Reloaded" || {
    echo "[WARN] Reload failed, restarting..."
    sudo systemctl restart caddy
    sleep 2
}

# Status
echo "[STEP 6] Checking status..."
sudo systemctl status caddy --no-pager | head -10

# Certificate
echo ""
echo "[STEP 7] Waiting for SSL certificate (30 sec)..."
for i in {1..6}; do
    sleep 5
    if sudo caddy list-certs 2>/dev/null | grep -q "api.profitengine"; then
        echo "[OK] Certificate ready!"
        break
    fi
    echo "[WAIT] Still waiting... ($i/6)"
done

echo ""
echo "========================================"
echo "✅ Caddy configuration complete!"
echo "========================================"
echo ""
echo "Test from your local machine:"
echo "  curl -I https://api.profitengine.alreadyherellc.com/"
echo ""
```

### 3. Expected Output
The script should complete with:
```
[OK] Caddyfile: /etc/caddy/Caddyfile
[OK] Backup created
[OK] Configuration added
[OK] Syntax valid
[OK] Reloaded
[OK] Certificate ready!
✅ Caddy configuration complete!
```

### 4. Verify from Your Local Machine (After Caddy finishes)
```bash
# Test HTTPS endpoint
curl -I https://api.profitengine.alreadyherellc.com/
# Expected: HTTP/2 200 (or any 2xx status)

# Test with verbose output
curl -v https://api.profitengine.alreadyherellc.com/

# Check certificate
echo | openssl s_client -servername api.profitengine.alreadyherellc.com -connect 129.146.236.177:443 2>/dev/null | grep -E "subject=|issuer=|Verify"
# Expected:
#   subject=CN = api.profitengine.alreadyherellc.com
#   issuer=C = US, O = Let's Encrypt, CN = R3
#   Verify return code: 0 (ok)
```

### 5. Troubleshoot if Needed

**Caddy reload failed?**
```bash
ssh opc@129.146.236.177
sudo systemctl restart caddy
sudo journalctl -u caddy -n 30  # Check logs
```

**Certificate not issued?**
```bash
# Check if DNS is resolving inside OCI server
nslookup api.profitengine.alreadyherellc.com
# Must show 129.146.236.177

# Wait another minute and check again
sudo caddy list-certs | grep api.profitengine
```

**Backend API not responding?**
```bash
# Check if :8001 is listening
sudo ss -tlnp | grep 8001
# or
curl http://localhost:8001/
```

---

## Current Status

| Component | Status | Notes |
|-----------|--------|-------|
| DNS | ✅ UPDATED | 129.146.236.177 globally propagated |
| Caddy Config | ⏳ PENDING | Run script on OCI server |
| SSL Certificate | ⏳ PENDING | Auto-issued after Caddy reloads |
| API Gateway | ⏳ PENDING | Works after Caddy setup |
| Vercel Frontend | ✅ READY | Already has correct RUNTIME_API_URL |

---

## Timeline

```
NOW:     SSH to OCI + Run Caddy setup script (5-10 min)
         ↓
+2 min:  SSL certificate issued by Let's Encrypt (automatic)
         ↓
+2 min:  Test from local machine (2 min)
         ↓
+5 min:  Vercel automatically redeploys
         ↓
+3 min:  TokenForge conversions LIVE ✅
```

**Total Time: 15 minutes to production**

---

## After Caddy is Ready

Once you see "✅ Caddy configuration complete!", immediately run:

```bash
# From your local machine (NOT on OCI)
curl -I https://api.profitengine.alreadyherellc.com/

# Should return something like:
# HTTP/2 200 OK
# or
# HTTP/2 404 (if endpoint doesn't exist - that's OK, means Caddy is working)
```

Report back with the response and we'll verify everything is working!
