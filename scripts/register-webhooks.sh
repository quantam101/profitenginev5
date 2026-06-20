#!/bin/bash
set -euo pipefail

# Register all webhooks for ProfitEngine revenue integrations
# Usage: ./scripts/register-webhooks.sh

echo "🔗 Registering ProfitEngine Webhooks..."
echo "=================================================="

# Load environment
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo "❌ .env file not found"
    exit 1
fi

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

DOMAIN="${PUBLIC_SITE_URL:-https://profitengine.alreadyherellc.com}"
LOG_FILE="webhooks-registration.log"
SUCCESS_COUNT=0
FAIL_COUNT=0

# Timestamp log
{
    echo "=========================================="
    echo "Webhook Registration - $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "=========================================="
    echo ""
} | tee -a "$LOG_FILE"

# Function to test webhook endpoint
test_webhook() {
    local name=$1
    local endpoint=$2
    local test_payload=$3

    echo -n "Testing $name... "
    if curl -s -X POST "$DOMAIN$endpoint" \
        -H "Content-Type: application/json" \
        -d "$test_payload" \
        -o /dev/null -w "%{http_code}" --connect-timeout 5 | grep -q "200\|400"; then
        echo -e "${GREEN}✅ OK${NC}"
        echo "✅ $name endpoint is reachable" >> "$LOG_FILE"
        ((SUCCESS_COUNT++))
        return 0
    else
        echo -e "${RED}❌ FAILED${NC}"
        echo "❌ $name endpoint failed connectivity check" >> "$LOG_FILE"
        ((FAIL_COUNT++))
        return 1
    fi
}

# Test 1: Gumroad Webhook
echo ""
echo "1️⃣  Gumroad Integration"
echo "   Webhook URL: $DOMAIN/api/webhooks/gumroad"
GUMROAD_PAYLOAD='{"product_id":"test","product_name":"Test Product","price":99.99,"purchaser":{"email":"test@example.com"}}'
test_webhook "Gumroad" "/api/webhooks/gumroad" "$GUMROAD_PAYLOAD"

echo "   ℹ️  Manual setup in Gumroad:"
echo "   https://app.gumroad.com/settings/webhooks"
echo "   Add webhook URL: $DOMAIN/api/webhooks/gumroad"
echo "   Events: product_purchased"
echo ""

# Test 2: Printify Webhook
echo "2️⃣  Printify Integration"
echo "   Webhook URL: $DOMAIN/api/webhooks/printify"
PRINTIFY_PAYLOAD='{"action":"order.created","data":{"id":"123456","status":"pending","total_price":89.99,"currency":"USD","line_items":[{"title":"Test T-Shirt","quantity":1}]}}'
test_webhook "Printify" "/api/webhooks/printify" "$PRINTIFY_PAYLOAD"

echo "   ℹ️  Manual setup in Printify:"
echo "   https://printify.com/integrations"
echo "   Add webhook URL: $DOMAIN/api/webhooks/printify"
echo "   Events: order.created, order.completed"
echo ""

# Test 3: Newsletter Webhook
echo "3️⃣  Newsletter (Beehiiv) Integration"
echo "   Webhook URL: $DOMAIN/api/webhooks/newsletter"
NEWSLETTER_PAYLOAD='{"event":"sponsor.created","data":{"sponsor_name":"Acme Corp","sponsorship_amount":500,"sponsorship_duration":"1 month","currency":"USD"}}'
test_webhook "Newsletter" "/api/webhooks/newsletter" "$NEWSLETTER_PAYLOAD"

echo "   ℹ️  Manual setup in Beehiiv:"
echo "   https://dashboard.beehiiv.com/settings/webhooks"
echo "   Add webhook URL: $DOMAIN/api/webhooks/newsletter"
echo "   Events: sponsor.paid, sponsor.created"
echo ""

# Test 4: Revenue Dashboard
echo "4️⃣  Revenue Dashboard Health Check"
echo "   Endpoint: $DOMAIN/api/revenue/dashboard"
if curl -s -X GET "$DOMAIN/api/revenue/dashboard" \
    -H "Content-Type: application/json" \
    -o /dev/null -w "%{http_code}" --connect-timeout 5 | grep -q "200"; then
    echo -e "${GREEN}✅ Dashboard API is healthy${NC}"
    echo "✅ Revenue dashboard API responding" >> "$LOG_FILE"
    ((SUCCESS_COUNT++))
else
    echo -e "${RED}❌ Dashboard API unreachable${NC}"
    echo "⚠️  Revenue dashboard API not responding - backend may not be running" >> "$LOG_FILE"
    ((FAIL_COUNT++))
fi
echo ""

# Summary
echo "=================================================="
{
    echo ""
    echo "Summary:"
    echo "  ✅ Successful: $SUCCESS_COUNT"
    echo "  ❌ Failed: $FAIL_COUNT"
    echo ""
    echo "Manual Configuration Required:"
    echo "1. Gumroad: https://app.gumroad.com/settings/webhooks"
    echo "2. Printify: https://printify.com/integrations"
    echo "3. Beehiiv: https://dashboard.beehiiv.com/settings/webhooks"
    echo "4. YouTube Analytics: Set YOUTUBE_REFRESH_TOKEN in .env"
    echo ""
    echo "Webhook URLs to use:"
    echo "  - Gumroad:    $DOMAIN/api/webhooks/gumroad"
    echo "  - Printify:   $DOMAIN/api/webhooks/printify"
    echo "  - Newsletter: $DOMAIN/api/webhooks/newsletter"
    echo ""
} | tee -a "$LOG_FILE"

echo -e "${GREEN}📋 Full log saved to: $LOG_FILE${NC}"

if [ "$FAIL_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Some checks failed. Backend may not be running yet.${NC}"
    echo -e "${YELLOW}   Run after OCI deployment: docker-compose up -d${NC}"
    exit 1
else
    echo -e "${GREEN}✅ All webhook endpoints verified!${NC}"
    exit 0
fi
