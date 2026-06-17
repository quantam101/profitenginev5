#!/bin/bash
# Diagnose ProfitEngine v5 Docker services on CMDOS
# Run: ssh opc@129.146.236.177 "bash /home/opc/profitenginev5/scripts/diagnose-services.sh"

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     ProfitEngine v5 Service Diagnostic Tool               ║"
echo "║     CMDOS Server: 129.146.236.177                         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# 1. Check Docker daemon
echo "[1/6] Checking Docker daemon..."
if sudo docker info &>/dev/null; then
    echo "      ✅ Docker daemon running"
else
    echo "      ❌ Docker daemon NOT running"
    exit 1
fi

# 2. Check running containers
echo "[2/6] Checking running containers..."
if containers=$(sudo docker ps --format "{{.Names}}" 2>/dev/null); then
    if [ -z "$containers" ]; then
        echo "      ⚠️  No containers running"
        echo "      Run: cd /home/opc/profitenginev5/deploy && sudo docker compose up -d"
    else
        echo "      ✅ Running containers: $containers"
    fi
else
    echo "      ❌ Cannot query Docker containers"
fi

# 3. Check port 8001 (backend)
echo "[3/6] Testing backend service (port 8001)..."
if timeout 3 curl -s http://localhost:8001/api/health &>/dev/null; then
    echo "      ✅ Backend responding"
else
    echo "      ❌ Backend not responding"
    echo "         Try: curl -v http://localhost:8001/api/health"
fi

# 4. Check port 8000 (runtime)
echo "[4/6] Testing runtime service (port 8000)..."
if timeout 3 curl -s http://localhost:8000/health &>/dev/null; then
    echo "      ✅ Runtime responding"
else
    echo "      ❌ Runtime not responding"
    echo "         Try: curl -v http://localhost:8000/health"
fi

# 5. Check .env file
echo "[5/6] Checking environment configuration..."
if [ -f /home/opc/profitenginev5/.env ]; then
    count=$(grep -c "=" /home/opc/profitenginev5/.env || echo "0")
    echo "      ✅ .env file exists with $count variables"

    # Check for key variables
    if grep -q "GUMROAD_ACCESS_TOKEN=" /home/opc/profitenginev5/.env; then
        echo "         ✅ Gumroad credentials found"
    else
        echo "         ❌ Gumroad credentials missing"
    fi

    if grep -q "STRIPE_API_KEY=" /home/opc/profitenginev5/.env; then
        echo "         ✅ Stripe credentials found"
    else
        echo "         ❌ Stripe credentials missing"
    fi
else
    echo "      ❌ .env file not found at /home/opc/profitenginev5/.env"
fi

# 6. Check compose file
echo "[6/6] Checking Docker Compose configuration..."
if [ -f /home/opc/profitenginev5/deploy/docker-compose.prod.yml ]; then
    echo "      ✅ docker-compose.prod.yml exists"
    services=$(grep "^  [a-z]:" /home/opc/profitenginev5/deploy/docker-compose.prod.yml | awk '{print $1}' | tr '\n' ' ')
    echo "         Services: $services"
else
    echo "      ❌ docker-compose.prod.yml not found"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                    Recommendations                         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

if ! timeout 3 curl -s http://localhost:8001/api/health &>/dev/null; then
    echo "⚠️  Backend service not responding. Try:"
    echo ""
    echo "  1. Check logs:"
    echo "     cd /home/opc/profitenginev5/deploy"
    echo "     sudo docker compose logs -f backend"
    echo ""
    echo "  2. Restart services:"
    echo "     sudo docker compose down"
    echo "     sudo docker compose up -d"
    echo ""
    echo "  3. Rebuild (if needed):"
    echo "     sudo docker compose build --no-cache backend runtime"
    echo "     sudo docker compose up -d"
fi

echo ""
echo "✅ For store activation, once services are running:"
echo ""
echo "   curl -X POST http://localhost:8000/products/bootstrap \\"
echo "     -H 'Content-Type: application/json' -d '{}'"
echo ""
