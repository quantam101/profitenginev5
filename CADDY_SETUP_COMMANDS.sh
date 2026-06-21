#!/bin/bash
# Caddy SSL Configuration for api.profitengine.alreadyherellc.com
# Run these commands on OCI server: ssh opc@129.146.236.177

set -e

echo "========================================"
echo "Caddy SSL Setup for ProfitEngine"
echo "Domain: api.profitengine.alreadyherellc.com"
echo "Backend: localhost:8001"
echo "========================================"
echo ""

# Step 1: Find Caddyfile
echo "[STEP 1] Locating Caddyfile..."
CADDY_FILE=$(sudo find / -name "Caddyfile" -type f 2>/dev/null | head -1)
if [ -z "$CADDY_FILE" ]; then
    echo "[ERROR] Caddyfile not found. Creating one..."
    CADDY_FILE="/etc/caddy/Caddyfile"
    sudo mkdir -p /etc/caddy
    sudo touch "$CADDY_FILE"
fi
echo "[OK] Caddyfile location: $CADDY_FILE"
echo ""

# Step 2: Backup current config
echo "[STEP 2] Backing up current configuration..."
sudo cp "$CADDY_FILE" "${CADDY_FILE}.backup.$(date +%s)"
echo "[OK] Backup created"
echo ""

# Step 3: Check if config already has api.profitengine
echo "[STEP 3] Checking for existing configuration..."
if sudo grep -q "api.profitengine.alreadyherellc.com" "$CADDY_FILE"; then
    echo "[WARN] api.profitengine.alreadyherellc.com already in config, skipping append"
else
    echo "[OK] Adding new configuration..."
    sudo tee -a "$CADDY_FILE" > /dev/null << 'EOF'

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
EOF
    echo "[OK] Configuration added to Caddyfile"
fi
echo ""

# Step 4: Validate Caddyfile
echo "[STEP 4] Validating Caddyfile syntax..."
if sudo caddy validate --config "$CADDY_FILE"; then
    echo "[OK] Caddyfile is valid"
else
    echo "[ERROR] Caddyfile validation failed. Check the error above."
    exit 1
fi
echo ""

# Step 5: Reload Caddy
echo "[STEP 5] Reloading Caddy..."
if sudo systemctl reload caddy; then
    echo "[OK] Caddy reloaded successfully"
else
    echo "[WARN] Reload failed, attempting restart..."
    sudo systemctl restart caddy
    sleep 2
fi
echo ""

# Step 6: Check Caddy status
echo "[STEP 6] Checking Caddy status..."
if sudo systemctl status caddy | grep -q "active (running)"; then
    echo "[OK] Caddy is running"
else
    echo "[ERROR] Caddy is not running. Check logs:"
    sudo journalctl -u caddy -n 20
    exit 1
fi
echo ""

# Step 7: Wait for certificate
echo "[STEP 7] Waiting for SSL certificate (up to 30 seconds)..."
for i in {1..6}; do
    sleep 5
    if sudo caddy list-certs | grep -q "api.profitengine.alreadyherellc.com"; then
        echo "[OK] Certificate issued for api.profitengine.alreadyherellc.com"
        break
    else
        echo "[WAIT] Attempt $i/6 - Still waiting for certificate..."
    fi
done
echo ""

# Step 8: Show certificate details
echo "[STEP 8] Certificate details:"
sudo caddy list-certs 2>/dev/null | grep -A 5 "api.profitengine" || echo "[INFO] Certificate details not yet available"
echo ""

# Step 9: Test local connectivity
echo "[STEP 9] Testing local connectivity..."
if curl -s http://localhost:8001/ > /dev/null 2>&1; then
    echo "[OK] Backend API (localhost:8001) is responding"
else
    echo "[WARN] Backend API not responding. Is it running?"
    echo "      Check with: curl http://localhost:8001/"
fi
echo ""

# Step 10: Final verification
echo "[STEP 10] Final verification..."
echo ""
echo "========================================"
echo "✅ Caddy Configuration Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Run from your local machine:"
echo "   curl -I https://api.profitengine.alreadyherellc.com/"
echo "   Expected: HTTP/2 200 or similar"
echo ""
echo "2. Check certificate validity:"
echo "   echo | openssl s_client -servername api.profitengine.alreadyherellc.com -connect 129.146.236.177:443"
echo ""
echo "3. Verify from anywhere:"
echo "   curl -v https://api.profitengine.alreadyherellc.com/api/health"
echo ""
echo "========================================"
