#!/bin/bash
# Already Here LLC — Full Stack Installer
# Run on OCI server: ssh ubuntu@129.146.167.73 && bash deploy/install.sh
# Installs: Docker, N8N, Taylor voice agent, PM2, all dependencies

set -e
echo "============================================================"
echo "  Already Here LLC — Production Stack Installer"
echo "  OCI Server: $(hostname -I | awk '{print $1}')"
echo "============================================================"

# ── 1. System dependencies ────────────────────────────────────────────────────
echo "[1/8] Installing system dependencies..."
sudo apt-get update -qq
sudo apt-get install -y -qq \
  docker.io docker-compose-v2 \
  python3 python3-pip python3-venv \
  nodejs npm \
  git curl wget \
  nginx certbot python3-certbot-nginx

# Enable Docker
sudo systemctl enable docker
sudo usermod -aG docker $USER

# ── 2. PM2 (process manager for Taylor and pipeline) ─────────────────────────
echo "[2/8] Installing PM2..."
sudo npm install -g pm2
pm2 startup | tail -1 | bash || true

# ── 3. Python dependencies ────────────────────────────────────────────────────
echo "[3/8] Installing Python packages..."
pip3 install --quiet \
  fastapi uvicorn aiohttp aiosqlite pydantic "pydantic-ai>=0.0.14" \
  stripe twilio \
  python-dotenv

# ── 4. Clone / pull repo ──────────────────────────────────────────────────────
echo "[4/8] Setting up project..."
mkdir -p /opt/already-here
cd /opt/already-here

if [ -d ".git" ]; then
  git pull origin main
else
  echo "  Project directory ready at /opt/already-here"
fi

# ── 5. N8N via Docker ─────────────────────────────────────────────────────────
echo "[5/8] Starting N8N automation hub..."
cd /opt/already-here

if [ ! -f "deploy/n8n/.env" ]; then
  cp deploy/n8n/.env.example deploy/n8n/.env
  echo "  IMPORTANT: Fill in deploy/n8n/.env before N8N will start fully"
fi

docker compose -f deploy/n8n/docker-compose.yml up -d postgres traefik n8n

# ── 6. Taylor voice agent via PM2 ────────────────────────────────────────────
echo "[6/8] Starting Taylor voice agent..."
cd /opt/already-here

if [ ! -f "agents/taylor/.env" ]; then
  cp agents/taylor/.env.example agents/taylor/.env
  echo "  IMPORTANT: Fill in agents/taylor/.env with Twilio + Retell + Stripe keys"
fi

# Load env and start Taylor
set -a && source agents/taylor/.env && set +a
pm2 start agents/taylor/server.py \
  --name taylor \
  --interpreter python3 \
  --watch false \
  --log /var/log/taylor.log \
  -- --host 0.0.0.0 --port 8001

# ── 7. Pipeline daemon ────────────────────────────────────────────────────────
echo "[7/8] Starting pipeline daemon..."
cd /opt/already-here

if [ -f "pipeline/.env" ]; then
  set -a && source pipeline/.env && set +a
  pm2 start pipeline/mesh_engine.py \
    --name profitengine \
    --interpreter python3 \
    --log /var/log/profitengine.log
fi

pm2 save

# ── 8. OCI firewall rules ─────────────────────────────────────────────────────
echo "[8/8] Opening required firewall ports..."
# HTTP + HTTPS for N8N and Taylor
sudo iptables -I INPUT -p tcp --dport 80  -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 8001 -j ACCEPT
# Persist iptables
sudo sh -c "iptables-save > /etc/iptables/rules.v4" || true

echo ""
echo "============================================================"
echo "  INSTALLATION COMPLETE"
echo "============================================================"
echo ""
echo "  N8N:    http://$(hostname -I | awk '{print $1}'):5678"
echo "  Taylor: http://$(hostname -I | awk '{print $1}'):8001/health"
echo ""
echo "  NEXT STEPS:"
echo "  1. Fill deploy/n8n/.env with N8N admin credentials"
echo "  2. Fill agents/taylor/.env with Twilio + Retell + Stripe keys"
echo "  3. Run: python agents/taylor/twilio_setup.py"
echo "  4. Import workflow JSONs into N8N from deploy/n8n/workflows/"
echo "  5. Create Retell AI agent at retellai.com"
echo ""
echo "  Taylor transfer chain:"
echo "    Primary:  602-882-2920"
echo "    Backup 1: 619-806-6457"
echo "    Backup 2: 619-884-9241"
echo "============================================================"
