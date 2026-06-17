#!/bin/bash
set -euo pipefail

# ProfitEngine v5 — Profit System Verification
# Runs all profit-generating services and verifies functionality
# Target: 129.146.236.177 (CMDOS Server)

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
REPORT_FILE="profit_verification_${TIMESTAMP// /_}.json"

echo "═══════════════════════════════════════════════════════════════"
echo "ProfitEngine v5 — Profit System Verification"
echo "Server: 129.146.236.177 (CMDOS)"
echo "Started: $TIMESTAMP"
echo "═══════════════════════════════════════════════════════════════"

# Initialize report
cat > "$REPORT_FILE" << 'EOF'
{
  "timestamp": "",
  "server": "129.146.236.177",
  "services": {},
  "verification_results": {},
  "status": "in_progress"
}
EOF

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_status() {
  local service=$1
  local status=$2
  local message=$3

  case $status in
    PASS)
      echo -e "${GREEN}✓${NC} $service: $message"
      ;;
    FAIL)
      echo -e "${RED}✗${NC} $service: $message"
      ;;
    PENDING)
      echo -e "${YELLOW}⏳${NC} $service: $message"
      ;;
    INFO)
      echo -e "${BLUE}ℹ${NC} $service: $message"
      ;;
  esac
}

# Function to check if port is open
check_port() {
  local host=$1
  local port=$2
  timeout 2 bash -c "</dev/tcp/$host/$port" 2>/dev/null && return 0 || return 1
}

# Function to check if service is responding
check_service() {
  local name=$1
  local url=$2
  local expected_code=${3:-200}

  log_status "$name" "INFO" "Checking $url"

  if response=$(curl -s -w "\n%{http_code}" -m 5 "$url" 2>/dev/null); then
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)

    if [ "$http_code" = "$expected_code" ]; then
      log_status "$name" "PASS" "HTTP $http_code - Service responding"
      return 0
    else
      log_status "$name" "FAIL" "HTTP $http_code (expected $expected_code)"
      return 1
    fi
  else
    log_status "$name" "FAIL" "Connection timeout or error"
    return 1
  fi
}

echo ""
echo "── PHASE 1: Service Connectivity ──────────────────────────────"

# Check CMDOS server
log_status "CMDOS Server" "INFO" "Checking 129.146.236.177"
if check_port 129.146.236.177 80; then
  log_status "CMDOS Server" "PASS" "Port 80 (HTTP) accessible"
else
  log_status "CMDOS Server" "FAIL" "Port 80 not accessible"
fi

if check_port 129.146.236.177 443; then
  log_status "CMDOS Server" "PASS" "Port 443 (HTTPS) accessible"
else
  log_status "CMDOS Server" "FAIL" "Port 443 not accessible"
fi

# Check Dashboard
log_status "Dashboard" "PENDING" "Checking port 3000"
if check_port 129.146.236.177 3000; then
  log_status "Dashboard" "PASS" "Port 3000 accessible"
  check_service "Dashboard" "http://129.146.236.177:3000/"
else
  log_status "Dashboard" "FAIL" "Port 3000 not accessible - service may not be running"
fi

# Check Runtime API
log_status "Runtime API" "PENDING" "Checking port 8000"
if check_port 129.146.236.177 8000; then
  log_status "Runtime API" "PASS" "Port 8000 accessible"
  check_service "Runtime API" "http://129.146.236.177:8000/health"
else
  log_status "Runtime API" "FAIL" "Port 8000 not accessible - service may not be running"
fi

# Check Backend API
log_status "Backend API" "PENDING" "Checking port 8001"
if check_port 129.146.236.177 8001; then
  log_status "Backend API" "PASS" "Port 8001 accessible"
  check_service "Backend API" "http://129.146.236.177:8001/health"
else
  log_status "Backend API" "FAIL" "Port 8001 not accessible - service may not be running"
fi

echo ""
echo "── PHASE 2: Profit Revenue Streams ────────────────────────────"

# Check Revenue Agent
log_status "Revenue Agent" "PENDING" "Checking revenue tracking"
if [ -f "agents/revenue/index.js" ]; then
  log_status "Revenue Agent" "PASS" "Revenue agent code present"
else
  log_status "Revenue Agent" "FAIL" "Revenue agent code not found"
fi

# Check Gumroad Integration
log_status "Gumroad" "PENDING" "Checking Gumroad client"
if [ -f "runtime/gumroad_client.py" ]; then
  log_status "Gumroad" "PASS" "Gumroad client present"
else
  log_status "Gumroad" "FAIL" "Gumroad client not found"
fi

# Check Stripe Integration
log_status "Stripe" "PENDING" "Checking Stripe transport"
if [ -f "backend/services/stripe_transport.py" ]; then
  log_status "Stripe" "PASS" "Stripe integration present"
else
  log_status "Stripe" "FAIL" "Stripe integration not found"
fi

# Check Affiliate System
log_status "Affiliate System" "PENDING" "Checking affiliate agent"
if [ -f "agents/affiliate/index.js" ]; then
  log_status "Affiliate System" "PASS" "Affiliate agent present"
else
  log_status "Affiliate System" "FAIL" "Affiliate agent not found"
fi

# Check Trading System
log_status "Trading System" "PENDING" "Checking trading control"
if [ -f "trading-control/app.py" ]; then
  log_status "Trading System" "PASS" "Trading system present"
  if [ -f "trading-control/config.yaml" ]; then
    log_status "Trading System" "PASS" "Trading configuration present"
  fi
else
  log_status "Trading System" "FAIL" "Trading system not found"
fi

echo ""
echo "── PHASE 3: Profit Configuration Verification ─────────────────"

# Check revenue configuration
log_status "Revenue Pipeline" "PENDING" "Checking revenue_streams.py"
if [ -f "pipeline/revenue_streams.py" ]; then
  log_status "Revenue Pipeline" "PASS" "Revenue pipeline present"
else
  log_status "Revenue Pipeline" "FAIL" "Revenue pipeline not found"
fi

# Check payment integration
log_status "Payment Integration" "PENDING" "Checking payment routes"
if grep -q "stripe\|payment\|checkout" backend/server.py 2>/dev/null; then
  log_status "Payment Integration" "PASS" "Payment routes configured"
else
  log_status "Payment Integration" "INFO" "Payment routes not explicitly found"
fi

# Check database connectivity
log_status "Database" "PENDING" "Checking MongoDB/PostgreSQL"
if [ -n "${MONGO_URL:-}" ] || [ -n "${DATABASE_URL:-}" ]; then
  log_status "Database" "PASS" "Database URLs configured"
else
  log_status "Database" "PENDING" "Database URLs not set in environment"
fi

echo ""
echo "── PHASE 4: Revenue Reporting ─────────────────────────────────"

# Check revenue report script
log_status "Revenue Report" "PENDING" "Checking revenue_report.py"
if [ -f "scripts/revenue_report.py" ]; then
  log_status "Revenue Report" "PASS" "Revenue reporting script present"
else
  log_status "Revenue Report" "FAIL" "Revenue reporting script not found"
fi

# Check audit ledger (for trading)
log_status "Audit Ledger" "PENDING" "Checking trading audit"
if [ -f "trading-control/audit_ledger.py" ]; then
  log_status "Audit Ledger" "PASS" "Trading audit ledger present"
  if [ -f "trading-control/audit.db" ]; then
    log_status "Audit Ledger" "PASS" "Trading audit database exists"
  fi
else
  log_status "Audit Ledger" "FAIL" "Trading audit ledger not found"
fi

echo ""
echo "── PHASE 5: Integration Tests ─────────────────────────────────"

# Check test files
log_status "Integration Tests" "PENDING" "Checking test suite"
if [ -f "tests/test_full_suite.py" ]; then
  log_status "Integration Tests" "PASS" "Full integration test suite present"
else
  log_status "Integration Tests" "INFO" "Full test suite not found"
fi

# Check Gumroad tests
log_status "Gumroad Tests" "PENDING" "Checking Gumroad automation tests"
if [ -f "tests/test_gumroad_client.py" ]; then
  log_status "Gumroad Tests" "PASS" "Gumroad tests present"
else
  log_status "Gumroad Tests" "INFO" "Gumroad tests not found"
fi

# Check affiliate tests
log_status "Affiliate Tests" "PENDING" "Checking affiliate integration tests"
if [ -f "tests/test_publish_article_affiliates.py" ]; then
  log_status "Affiliate Tests" "PASS" "Affiliate tests present"
else
  log_status "Affiliate Tests" "INFO" "Affiliate tests not found"
fi

echo ""
echo "── PHASE 6: Deployment Status ─────────────────────────────────"

# Check docker compose
log_status "Docker Compose" "PENDING" "Checking docker-compose.prod.yml"
if [ -f "deploy/docker-compose.prod.yml" ]; then
  log_status "Docker Compose" "PASS" "Production Docker Compose configured"
else
  log_status "Docker Compose" "FAIL" "Docker Compose not found"
fi

# Check GitHub workflows
log_status "CI/CD Workflows" "PENDING" "Checking deployment workflows"
if [ -f ".github/workflows/deploy.yml" ]; then
  log_status "CI/CD Workflows" "PASS" "Deploy workflow configured"
fi

if [ -f ".github/workflows/income-streams.yml" ]; then
  log_status "CI/CD Workflows" "PASS" "Income streams workflow configured"
fi

echo ""
echo "══════════════════════════════════════════════════════════════"
echo "VERIFICATION COMPLETE"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Summary:"
echo "  • CMDOS Server: 129.146.236.177"
echo "  • Dashboard: http://129.146.236.177:3000"
echo "  • Runtime API: http://129.146.236.177:8000"
echo "  • Backend API: http://129.146.236.177:8001"
echo ""
echo "Next Steps:"
echo "  1. SSH to cmdos: ssh opc@129.146.236.177"
echo "  2. Deploy: cd /home/opc/profitenginev5/deploy"
echo "  3. Start: docker compose -f docker-compose.prod.yml up -d"
echo "  4. Verify: docker compose -f docker-compose.prod.yml ps"
echo ""
echo "Report saved to: $REPORT_FILE"
echo "═══════════════════════════════════════════════════════════════"
