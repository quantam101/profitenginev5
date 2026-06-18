#!/bin/bash

# Trading Dashboard API Test Commands
# Test the dashboard endpoints with curl

# Configuration
DOMAIN="${DOMAIN:-http://localhost:3000}"
RUNTIME_DOMAIN="${RUNTIME_DOMAIN:-http://localhost:8080}"
API_KEY="${API_KEY:-default-dev-key}"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Trading Dashboard API Tests ===${NC}\n"

# Test 1: Dashboard Aggregation Endpoint
echo -e "${YELLOW}Test 1: Dashboard Aggregation API${NC}"
echo "GET ${DOMAIN}/api/command/trading-dashboard"
curl -X GET "${DOMAIN}/api/command/trading-dashboard" \
  -H "Cache-Control: no-store" \
  -H "Accept: application/json" \
  -w "\nHTTP Status: %{http_code}\n" \
  -s | jq '.' 2>/dev/null || echo "jq not available, raw response:"
curl -X GET "${DOMAIN}/api/command/trading-dashboard" -H "Cache-Control: no-store" -s

echo -e "\n${YELLOW}Test 2: Runtime - Client Stats Endpoint${NC}"
echo "GET ${RUNTIME_DOMAIN}/api/clients/stats"
curl -X GET "${RUNTIME_DOMAIN}/api/clients/stats" \
  -H "Authorization: Bearer ${API_KEY}" \
  -w "\nHTTP Status: %{http_code}\n" \
  -s | jq '.' 2>/dev/null || echo "jq not available, raw response:"
curl -X GET "${RUNTIME_DOMAIN}/api/clients/stats" \
  -H "Authorization: Bearer ${API_KEY}" \
  -s

echo -e "\n${YELLOW}Test 3: Runtime - Leaderboard (Win Rate)${NC}"
echo "GET ${RUNTIME_DOMAIN}/api/clients/leaderboard?metric=win_rate&limit=5&days=30"
curl -X GET "${RUNTIME_DOMAIN}/api/clients/leaderboard?metric=win_rate&limit=5&days=30" \
  -H "Authorization: Bearer ${API_KEY}" \
  -w "\nHTTP Status: %{http_code}\n" \
  -s | jq '.' 2>/dev/null || echo "jq not available, raw response:"
curl -X GET "${RUNTIME_DOMAIN}/api/clients/leaderboard?metric=win_rate&limit=5&days=30" \
  -H "Authorization: Bearer ${API_KEY}" \
  -s

echo -e "\n${YELLOW}Test 4: Runtime - Leaderboard (P&L)${NC}"
echo "GET ${RUNTIME_DOMAIN}/api/clients/leaderboard?metric=pnl&limit=5&days=30"
curl -X GET "${RUNTIME_DOMAIN}/api/clients/leaderboard?metric=pnl&limit=5&days=30" \
  -H "Authorization: Bearer ${API_KEY}" \
  -w "\nHTTP Status: %{http_code}\n" \
  -s | jq '.' 2>/dev/null || echo "jq not available, raw response:"
curl -X GET "${RUNTIME_DOMAIN}/api/clients/leaderboard?metric=pnl&limit=5&days=30" \
  -H "Authorization: Bearer ${API_KEY}" \
  -s

echo -e "\n${YELLOW}Test 5: Runtime - Upsell Candidates${NC}"
echo "GET ${RUNTIME_DOMAIN}/api/clients/upsell-candidates?days=30"
curl -X GET "${RUNTIME_DOMAIN}/api/clients/upsell-candidates?days=30" \
  -H "Authorization: Bearer ${API_KEY}" \
  -w "\nHTTP Status: %{http_code}\n" \
  -s | jq '.' 2>/dev/null || echo "jq not available, raw response:"
curl -X GET "${RUNTIME_DOMAIN}/api/clients/upsell-candidates?days=30" \
  -H "Authorization: Bearer ${API_KEY}" \
  -s

# Test with custom parameters
echo -e "\n${YELLOW}Test 6: Dashboard with Custom Days Parameter${NC}"
echo "GET ${DOMAIN}/api/command/trading-dashboard?days=7"
curl -X GET "${DOMAIN}/api/command/trading-dashboard?days=7" \
  -H "Cache-Control: no-store" \
  -w "\nHTTP Status: %{http_code}\n" \
  -s | jq '.summary' 2>/dev/null || curl -X GET "${DOMAIN}/api/command/trading-dashboard?days=7" -s

echo -e "\n${GREEN}=== Tests Complete ===${NC}\n"

# Usage instructions
echo -e "${YELLOW}Usage:${NC}"
echo "  source dashboard-test-commands.sh              # Run with defaults"
echo "  DOMAIN=https://example.com ./dashboard-test-commands.sh  # Custom domain"
echo "  RUNTIME_DOMAIN=http://runtime:8080 DOMAIN=... ./dashboard-test-commands.sh"
echo "  API_KEY=your-key-here DOMAIN=... ./dashboard-test-commands.sh"
echo ""
echo -e "${YELLOW}Dashboard URLs:${NC}"
echo "  http://localhost:3000/command-center/trading"
echo "  http://localhost:3000/command-center?view=trading"
echo ""
