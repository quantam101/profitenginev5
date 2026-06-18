#!/bin/bash
# ProfitEngine OCI FastAPI recovery script
# Run this on the OCI server at 129.146.167.73

set -euo pipefail

echo "=== ProfitEngine OCI Recovery ==="
echo "Step 1: System check"
hostname && whoami && pwd
echo ""

echo "Step 2: Check for running processes"
ps aux | grep -E 'uvicorn|fastapi|python' | grep -v grep || echo "No processes found (expected if down)"
echo ""

echo "Step 3: Check open ports"
sudo ss -tulpn | grep -E '8001|80|443' || echo "Ports not bound"
echo ""

echo "Step 4: Check for existing systemd service"
sudo systemctl status profitengine --no-pager 2>/dev/null || echo "No profitengine service found"
echo ""

echo "Step 5: Find app directory"
APP_DIR=""
for path in /opt/profitenginev5 /home/opc/profitenginev5 /srv/profitenginev5; do
  if [ -d "$path" ] && [ -f "$path/backend/server.py" ]; then
    APP_DIR="$path"
    echo "Found app at: $APP_DIR"
    break
  fi
done

if [ -z "$APP_DIR" ]; then
  echo "ERROR: Could not find app directory. Checked: /opt, /home/opc, /srv"
  exit 1
fi
echo ""

echo "Step 6: Pull latest code"
cd "$APP_DIR"
git status
git pull origin main || echo "Warning: git pull failed, continuing with current code"
echo ""

echo "Step 7: Setup Python environment"
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install -r backend/requirements.txt --quiet
echo ""

echo "Step 8: Test run on port 8001 (60-second timeout)"
timeout 60 uvicorn backend.server:app --host 0.0.0.0 --port 8001 &
UVICORN_PID=$!
sleep 5

# Test health endpoint
echo "Testing http://localhost:8001/api/health..."
if curl -sS http://localhost:8001/api/health | python3 -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if (d.get('ok')==True or d.get('status')=='ok') else 1)" 2>/dev/null; then
  echo "✓ Health check passed"
else
  echo "✗ Health check failed"
  kill $UVICORN_PID 2>/dev/null || true
  exit 1
fi

kill $UVICORN_PID 2>/dev/null || true
echo ""

echo "Step 9: Create systemd service"
sudo tee /etc/systemd/system/profitengine.service > /dev/null << SVCEOF
[Unit]
Description=ProfitEngine FastAPI Runtime
After=network.target

[Service]
User=opc
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/.venv/bin/uvicorn backend.server:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SVCEOF

sudo systemctl daemon-reload
sudo systemctl enable profitengine
sudo systemctl restart profitengine
echo ""

echo "Step 10: Verify service is running"
sudo systemctl status profitengine --no-pager
echo ""

echo "Step 11: Check recent logs"
sudo journalctl -u profitengine -n 20 --no-pager
echo ""

echo "Step 12: Configure Nginx reverse proxy"
sudo tee /etc/nginx/sites-available/profitengine > /dev/null << NGXEOF
server {
    listen 80;
    server_name backend.alreadyherellc.com;

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 60s;
        proxy_connect_timeout 10s;
    }
}
NGXEOF

sudo ln -sf /etc/nginx/sites-available/profitengine /etc/nginx/sites-enabled/profitengine
sudo nginx -t && sudo systemctl reload nginx
echo ""

echo "=== Recovery complete ==="
echo "Run from your LOCAL machine to verify:"
echo "  curl -sS https://backend.alreadyherellc.com/api/health"
