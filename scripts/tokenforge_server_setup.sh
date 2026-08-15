#!/bin/bash
# TokenForge server full setup — run via OCI Run Command or serial console
# Server: 129.146.236.177
set -e

echo "=== TokenForge Server Setup ==="
echo "Started: $(date)"

# ── 1. Fix host firewall ──────────────────────────────────────────────────────
echo ""
echo "── Firewall ──"
if command -v ufw &>/dev/null; then
  ufw allow 22/tcp
  ufw allow 80/tcp
  ufw allow 443/tcp
  ufw allow 8000/tcp
  ufw --force enable
  ufw status
fi

# ── 2. Find TokenForge install ────────────────────────────────────────────────
echo ""
echo "── Finding TokenForge ──"
TF_DIR=""
for d in /opt/tokenforge /home/ubuntu/tokenforge /opt/token /srv/tokenforge; do
  if [ -d "$d" ]; then TF_DIR="$d"; break; fi
done
echo "TokenForge dir: ${TF_DIR:-NOT FOUND}"

if [ -z "$TF_DIR" ]; then
  echo "ERROR: TokenForge not found. Checking running processes..."
  ps aux | grep -E "python|uvicorn|gunicorn|server.py" | grep -v grep
  ss -tlnp | grep -E "8000|8001"
  exit 1
fi

# ── 3. Update .env ────────────────────────────────────────────────────────────
echo ""
echo "── Updating .env ──"
ENV_FILE="$TF_DIR/.env"

# Add/update Google OAuth
grep -q "GOOGLE_CLIENT_ID" "$ENV_FILE" 2>/dev/null \
  || echo "GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID:?Set GOOGLE_CLIENT_ID env var}" >> "$ENV_FILE"

grep -q "GOOGLE_CLIENT_SECRET" "$ENV_FILE" 2>/dev/null \
  || echo "GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET:?Set GOOGLE_CLIENT_SECRET env var}" >> "$ENV_FILE"

grep -q "FRONTEND_ORIGIN" "$ENV_FILE" 2>/dev/null \
  && sed -i 's|^FRONTEND_ORIGIN=.*|FRONTEND_ORIGIN=https://forge.alreadyherellc.com|' "$ENV_FILE" \
  || echo "FRONTEND_ORIGIN=https://forge.alreadyherellc.com" >> "$ENV_FILE"

grep -q "GOOGLE_REDIRECT_URI" "$ENV_FILE" 2>/dev/null \
  && sed -i 's|^GOOGLE_REDIRECT_URI=.*|GOOGLE_REDIRECT_URI=https://api.alreadyherellc.com/api/auth/google/callback|' "$ENV_FILE" \
  || echo "GOOGLE_REDIRECT_URI=https://api.alreadyherellc.com/api/auth/google/callback" >> "$ENV_FILE"

grep -q "GITHUB_REPO" "$ENV_FILE" 2>/dev/null \
  || echo "GITHUB_REPO=quantam101/profitenginev5" >> "$ENV_FILE"

echo ".env updated at $ENV_FILE"

# ── 4. Run SSL setup if script exists ─────────────────────────────────────────
echo ""
echo "── SSL Setup ──"
SSL_SCRIPT="$TF_DIR/deploy/oci_setup.sh"
if [ -f "$SSL_SCRIPT" ]; then
  bash "$SSL_SCRIPT" api.alreadyherellc.com
else
  echo "oci_setup.sh not found at $SSL_SCRIPT"
  echo "Checking for Caddy/nginx..."
  systemctl status caddy 2>/dev/null | head -5 || true
  systemctl status nginx 2>/dev/null | head -5 || true
fi

# ── 5. Install/update dependencies ───────────────────────────────────────────
echo ""
echo "── Dependencies ──"
if [ -f "$TF_DIR/requirements.txt" ]; then
  pip3 install -r "$TF_DIR/requirements.txt" --quiet 2>&1 | tail -3
fi

# ── 6. Restart backend ───────────────────────────────────────────────────────
echo ""
echo "── Restart Service ──"
if systemctl list-units --type=service | grep -q tokenforge; then
  systemctl restart tokenforge-backend
  sleep 3
  systemctl status tokenforge-backend | head -15
else
  echo "tokenforge-backend service not found. Checking for alternatives..."
  systemctl list-units --type=service | grep -iE "token|forge|python|uvicorn" | head -10
fi

# ── 7. Health check ──────────────────────────────────────────────────────────
echo ""
echo "── Health Check ──"
sleep 2
curl -s --max-time 10 http://127.0.0.1:8000/api/health | python3 -c "import json,sys; d=json.load(sys.stdin); print('LOCAL HEALTH:', d)" 2>/dev/null || echo "local health check failed"
curl -s --max-time 10 https://api.alreadyherellc.com/api/health | python3 -c "import json,sys; d=json.load(sys.stdin); print('PUBLIC HEALTH:', d)" 2>/dev/null || echo "public health check failed"

echo ""
echo "=== Setup complete: $(date) ==="
