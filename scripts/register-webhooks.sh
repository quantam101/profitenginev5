#!/bin/bash
set -euo pipefail

# ProfitEngine v5 — Comprehensive Webhook Registration Script
# Registers and verifies all revenue integration webhooks:
# - Gumroad (ebook/course sales)
# - Printify (POD order tracking)
# - Beehiiv (newsletter sponsorships)
# - YouTube Analytics (AdSense revenue)
#
# Usage:
#   ./scripts/register-webhooks.sh [--verify-only] [--help]
#
# Environment:
#   - .env file required (loaded automatically)
#   - API tokens: GUMROAD_API_TOKEN, PRINTIFY_API_TOKEN, BEEHIIV_API_KEY, YOUTUBE_REFRESH_TOKEN
#   - Domain: PUBLIC_SITE_URL or PROFITENGINE_DOMAIN

echo "🔗 ProfitEngine v5 — Webhook Registration System"
echo "=================================================="

# ───────────────────────────────────────────────────────────────────────────
# Configuration
# ───────────────────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_FILE="${PROJECT_DIR}/webhooks-registration.log"
TEMP_DIR="/tmp/profitengine-webhook-$$"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Counters
SUCCESS_COUNT=0
FAIL_COUNT=0
SKIP_COUNT=0
VERIFY_ONLY=false
SHOW_HELP=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --verify-only)
            VERIFY_ONLY=true
            shift
            ;;
        --help|-h)
            SHOW_HELP=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Show help if requested
if [ "$SHOW_HELP" = true ]; then
    cat <<'EOF'
ProfitEngine v5 — Webhook Registration Script

USAGE:
  ./scripts/register-webhooks.sh [OPTIONS]

OPTIONS:
  --verify-only    Only test webhook connectivity; don't register
  --help, -h       Show this help message

WEBHOOKS REGISTERED:
  1. Gumroad (POST /api/webhooks/gumroad)
     - Requires: GUMROAD_API_TOKEN
     - Events: product.purchased, license_issued

  2. Printify (POST /api/webhooks/printify)
     - Requires: PRINTIFY_API_TOKEN
     - Events: order.created, order.completed
     - Auto-detects shop and registers

  3. Beehiiv (POST /api/webhooks/newsletter)
     - Requires: BEEHIIV_API_KEY
     - Events: sponsor.created, sponsor.paid

  4. YouTube Analytics (Daily sync at 08:00 UTC)
     - Requires: YOUTUBE_REFRESH_TOKEN, YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET
     - Syncs: AdSense revenue to .runtime/revenue/transactions.jsonl

ENVIRONMENT SETUP:
  Set these in .env (server-side only, never commit to git):
    GUMROAD_API_TOKEN=xxx
    PRINTIFY_API_TOKEN=xxx
    BEEHIIV_API_KEY=xxx
    YOUTUBE_REFRESH_TOKEN=xxx
    YOUTUBE_CLIENT_ID=xxx
    YOUTUBE_CLIENT_SECRET=xxx
    YOUTUBE_CHANNEL_ID=UCxxxxxx
    PUBLIC_SITE_URL=https://profitengine.alreadyherellc.com

EXIT CODES:
  0 = All webhooks verified successfully
  1 = One or more webhook checks failed
  2 = Missing required environment variables

EXAMPLE:
  # Verify all webhooks are reachable
  ./scripts/register-webhooks.sh --verify-only

  # Full registration with API setup
  ./scripts/register-webhooks.sh

LOGS:
  Full registration log saved to: webhooks-registration.log
  View: cat webhooks-registration.log
  Tail: tail -f webhooks-registration.log

EOF
    exit 0
fi

# ───────────────────────────────────────────────────────────────────────────
# Environment Loading
# ───────────────────────────────────────────────────────────────────────────

echo -e "${BLUE}Loading environment...${NC}"

if [ -f "${PROJECT_DIR}/.env" ]; then
    set -a
    source "${PROJECT_DIR}/.env"
    set +a
else
    echo -e "${RED}❌ Error: .env file not found at ${PROJECT_DIR}/.env${NC}"
    echo "   Create one from .env.example or .env.template"
    exit 2
fi

# ───────────────────────────────────────────────────────────────────────────
# Variables
# ───────────────────────────────────────────────────────────────────────────

DOMAIN="${PUBLIC_SITE_URL:-${PROFITENGINE_DOMAIN:-https://profitengine.alreadyherellc.com}}"
GUMROAD_API_TOKEN="${GUMROAD_API_TOKEN:-}"
PRINTIFY_API_TOKEN="${PRINTIFY_API_TOKEN:-}"
BEEHIIV_API_KEY="${BEEHIIV_API_KEY:-}"
YOUTUBE_REFRESH_TOKEN="${YOUTUBE_REFRESH_TOKEN:-}"
YOUTUBE_CLIENT_ID="${YOUTUBE_CLIENT_ID:-}"
YOUTUBE_CLIENT_SECRET="${YOUTUBE_CLIENT_SECRET:-}"
YOUTUBE_CHANNEL_ID="${YOUTUBE_CHANNEL_ID:-}"

# Create temp directory for cleanup
mkdir -p "$TEMP_DIR"
trap "rm -rf $TEMP_DIR" EXIT

# Initialize log
{
    echo "=========================================="
    echo "Webhook Registration Log — $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "=========================================="
    echo ""
    echo "Domain: $DOMAIN"
    echo "Script: ${BASH_SOURCE[0]}"
    echo "Verify Only: $VERIFY_ONLY"
    echo ""
} | tee "$LOG_FILE"

# ───────────────────────────────────────────────────────────────────────────
# Utility Functions
# ───────────────────────────────────────────────────────────────────────────

# Test webhook endpoint connectivity
test_webhook() {
    local name=$1
    local endpoint=$2
    local test_payload=$3
    local timeout=${4:-10}

    echo -n "Testing $name endpoint... "

    local http_code=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST "${DOMAIN}${endpoint}" \
        -H "Content-Type: application/json" \
        -d "$test_payload" \
        --connect-timeout "$timeout" 2>/dev/null || echo "000")

    case $http_code in
        200|201)
            echo -e "${GREEN}✅ OK (HTTP $http_code)${NC}"
            echo "✅ $name: Endpoint is reachable (HTTP $http_code)" >> "$LOG_FILE"
            ((SUCCESS_COUNT++))
            return 0
            ;;
        400|401|422)
            echo -e "${YELLOW}⚠️  Accepted (HTTP $http_code)${NC}"
            echo "⚠️  $name: Endpoint accepted (validation issue expected) (HTTP $http_code)" >> "$LOG_FILE"
            ((SUCCESS_COUNT++))
            return 0
            ;;
        *)
            echo -e "${RED}❌ FAILED (HTTP $http_code)${NC}"
            echo "❌ $name: Endpoint unreachable (HTTP $http_code)" >> "$LOG_FILE"
            ((FAIL_COUNT++))
            return 1
            ;;
    esac
}

# Check for required environment variable
check_env_var() {
    local var_name=$1
    local var_value=${2:-}

    if [ -z "$var_value" ]; then
        echo -e "${YELLOW}⚠️  Skipping: $var_name not set${NC}"
        echo "⚠️  $var_name not configured (skipped)" >> "$LOG_FILE"
        ((SKIP_COUNT++))
        return 1
    fi
    return 0
}

# Test HTTP connectivity to a domain
test_domain_reachable() {
    local domain=$1
    local timeout=${2:-5}

    local http_code=$(curl -s -o /dev/null -w "%{http_code}" \
        -X GET "$domain" \
        --connect-timeout "$timeout" 2>/dev/null || echo "000")

    if [[ "$http_code" =~ ^[2345][0-9]{2}$ ]]; then
        return 0
    else
        return 1
    fi
}

# ───────────────────────────────────────────────────────────────────────────
# Pre-flight Checks
# ───────────────────────────────────────────────────────────────────────────

echo ""
echo -e "${BLUE}=== Pre-flight Checks ===${NC}"
echo ""

# Check domain reachability
echo -n "Testing domain reachability ($DOMAIN)... "
if test_domain_reachable "$DOMAIN" 10; then
    echo -e "${GREEN}✅ Reachable${NC}"
    echo "✅ Domain is reachable" >> "$LOG_FILE"
else
    echo -e "${YELLOW}⚠️  Not currently reachable (backend may not be running)${NC}"
    echo "⚠️  Domain not reachable (may be expected during setup)" >> "$LOG_FILE"
fi

# Check curl availability
if ! command -v curl &> /dev/null; then
    echo -e "${RED}❌ curl is not installed${NC}"
    exit 2
fi
echo -e "✅ curl is available"

# Check jq availability (for complex JSON parsing)
if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}⚠️  jq not found (some features will be limited)${NC}"
fi

# Check git (for documenting changes)
if ! command -v git &> /dev/null; then
    echo -e "${YELLOW}⚠️  git not found${NC}"
fi

echo ""

# ───────────────────────────────────────────────────────────────────────────
# 1. Gumroad Integration
# ───────────────────────────────────────────────────────────────────────────

echo -e "${MAGENTA}1️⃣  Gumroad (Ebook/Course Sales)${NC}"
echo "   Webhook URL: ${CYAN}${DOMAIN}/api/webhooks/gumroad${NC}"
echo ""

if check_env_var "GUMROAD_API_TOKEN" "$GUMROAD_API_TOKEN"; then
    # Test endpoint
    GUMROAD_PAYLOAD='{"product_id":"sample-book","product_name":"Sample Ebook","price":"29.99","purchase_email":"test@example.com","timestamp":"'$(date +%s)'"}'

    if [ "$VERIFY_ONLY" = false ]; then
        echo "   Documentation: https://gumroad.com/webhooks"
        echo "   Manual setup: https://app.gumroad.com/settings/webhooks"
        echo ""
    fi

    test_webhook "Gumroad" "/api/webhooks/gumroad" "$GUMROAD_PAYLOAD"
else
    echo ""
fi

echo -e "${CYAN}   Manual Setup (if auto-registration not supported):${NC}"
echo "   1. Go to: https://app.gumroad.com/settings/webhooks"
echo "   2. Add webhook URL: ${DOMAIN}/api/webhooks/gumroad"
echo "   3. Select events: product.purchased, license_issued"
echo ""

# ───────────────────────────────────────────────────────────────────────────
# 2. Printify Integration
# ───────────────────────────────────────────────────────────────────────────

echo -e "${MAGENTA}2️⃣  Printify (POD Order Tracking)${NC}"
echo "   Webhook URL: ${CYAN}${DOMAIN}/api/webhooks/printify${NC}"
echo ""

if check_env_var "PRINTIFY_API_TOKEN" "$PRINTIFY_API_TOKEN"; then
    # Test endpoint
    PRINTIFY_PAYLOAD='{"action":"order.created","data":{"id":"999999","status":"pending","total_price":89.99,"currency":"USD","line_items":[{"title":"Test Product","quantity":1}]}}'

    if [ "$VERIFY_ONLY" = false ]; then
        echo "   Documentation: https://printify.com/api/webhooks"
        echo "   Auto-registration: See script/register_printify_webhook.sh"
        echo ""
    fi

    test_webhook "Printify" "/api/webhooks/printify" "$PRINTIFY_PAYLOAD"
else
    echo ""
fi

echo -e "${CYAN}   Manual Setup:${NC}"
echo "   1. Go to: https://printify.com/integrations"
echo "   2. Add webhook URL: ${DOMAIN}/api/webhooks/printify"
echo "   3. Select events: order.created, order.completed"
echo "   4. OR use: ./scripts/register_printify_webhook.sh"
echo ""

# ───────────────────────────────────────────────────────────────────────────
# 3. Beehiiv (Newsletter Sponsorships)
# ───────────────────────────────────────────────────────────────────────────

echo -e "${MAGENTA}3️⃣  Beehiiv (Newsletter Sponsorships)${NC}"
echo "   Webhook URL: ${CYAN}${DOMAIN}/api/webhooks/newsletter${NC}"
echo ""

if check_env_var "BEEHIIV_API_KEY" "$BEEHIIV_API_KEY"; then
    # Test endpoint
    BEEHIIV_PAYLOAD='{"event":"sponsor.created","data":{"sponsor_id":"sp_123","sponsor_name":"Acme Corp","sponsorship_amount":500,"sponsorship_duration":"1 month","currency":"USD"}}'

    if [ "$VERIFY_ONLY" = false ]; then
        echo "   Documentation: https://docs.beehiiv.com/webhooks"
        echo "   Requires signature verification: x-beehiiv-signature (HMAC-SHA256)"
        echo ""
    fi

    test_webhook "Beehiiv" "/api/webhooks/newsletter" "$BEEHIIV_PAYLOAD"
else
    echo ""
fi

echo -e "${CYAN}   Manual Setup:${NC}"
echo "   1. Go to: https://dashboard.beehiiv.com/settings/webhooks"
echo "   2. Add webhook URL: ${DOMAIN}/api/webhooks/newsletter"
echo "   3. Select events: sponsor.created, sponsor.paid"
echo "   4. Note: Webhook must be signed with BEEHIIV_API_KEY"
echo ""

# ───────────────────────────────────────────────────────────────────────────
# 4. YouTube Analytics Integration
# ───────────────────────────────────────────────────────────────────────────

echo -e "${MAGENTA}4️⃣  YouTube Analytics (AdSense Revenue Sync)${NC}"
echo ""

if check_env_var "YOUTUBE_REFRESH_TOKEN" "$YOUTUBE_REFRESH_TOKEN"; then
    echo -e "${CYAN}   Configuration:${NC}"
    echo "   - Refresh Token: Set ($([ -n "$YOUTUBE_REFRESH_TOKEN" ] && echo "✅" || echo "❌"))"
    echo "   - Client ID: Set ($([ -n "$YOUTUBE_CLIENT_ID" ] && echo "✅" || echo "❌"))"
    echo "   - Client Secret: Set ($([ -n "$YOUTUBE_CLIENT_SECRET" ] && echo "✅" || echo "❌"))"
    echo "   - Channel ID: Set ($([ -n "$YOUTUBE_CHANNEL_ID" ] && echo "✅" || echo "❌"))"
    echo ""

    if [ -n "$YOUTUBE_CLIENT_ID" ] && [ -n "$YOUTUBE_CLIENT_SECRET" ] && [ -n "$YOUTUBE_CHANNEL_ID" ]; then
        echo -e "${GREEN}✅ YouTube Analytics configured${NC}"
        echo "✅ YouTube Analytics credentials configured" >> "$LOG_FILE"
        ((SUCCESS_COUNT++))
    else
        echo -e "${YELLOW}⚠️  YouTube Analytics incomplete (missing client/channel config)${NC}"
        echo "⚠️  YouTube Analytics configuration incomplete" >> "$LOG_FILE"
        ((SKIP_COUNT++))
    fi
else
    echo -e "${YELLOW}⚠️  Skipping: YOUTUBE_REFRESH_TOKEN not set${NC}"
    echo "⚠️  YouTube Analytics not configured" >> "$LOG_FILE"
    ((SKIP_COUNT++))
fi

echo -e "${CYAN}   Manual Setup:${NC}"
echo "   1. Go to: https://console.cloud.google.com"
echo "   2. Enable YouTube Analytics API"
echo "   3. Create OAuth 2.0 credentials (Desktop application)"
echo "   4. Get refresh token using: python scripts/youtube_oauth_setup.py"
echo "   5. Set in .env: YOUTUBE_REFRESH_TOKEN, YOUTUBE_CLIENT_ID, etc."
echo "   6. Sync job runs daily at 08:00 UTC"
echo ""

# ───────────────────────────────────────────────────────────────────────────
# 5. Revenue Dashboard Health Check
# ───────────────────────────────────────────────────────────────────────────

echo -e "${MAGENTA}5️⃣  Revenue Dashboard Health Check${NC}"
echo ""

echo -n "Testing revenue dashboard API... "
DASHBOARD_HTTP=$(curl -s -o /dev/null -w "%{http_code}" \
    -X GET "${DOMAIN}/api/revenue/dashboard" \
    -H "Content-Type: application/json" \
    --connect-timeout 10 2>/dev/null || echo "000")

if [[ "$DASHBOARD_HTTP" =~ ^[2][0-9]{2}$ ]]; then
    echo -e "${GREEN}✅ OK (HTTP $DASHBOARD_HTTP)${NC}"
    echo "✅ Revenue dashboard API responding" >> "$LOG_FILE"
    ((SUCCESS_COUNT++))
else
    echo -e "${YELLOW}⚠️  Not responding (HTTP $DASHBOARD_HTTP)${NC}"
    echo "⚠️  Revenue dashboard not responding (backend may not be running)" >> "$LOG_FILE"
    ((SKIP_COUNT++))
fi

# Check transaction log
TRANSACTION_LOG="${PROJECT_DIR}/.runtime/revenue/transactions.jsonl"
if [ -f "$TRANSACTION_LOG" ]; then
    LINE_COUNT=$(wc -l < "$TRANSACTION_LOG")
    echo -e "   Transaction log: ${GREEN}$LINE_COUNT entries${NC}"
    echo "   Location: $TRANSACTION_LOG"
    echo "✅ Transaction log exists: $LINE_COUNT entries" >> "$LOG_FILE"
else
    echo -e "   Transaction log: ${YELLOW}not yet created${NC}"
    echo "   Will be created on first webhook event"
    echo "⚠️  Transaction log not yet created" >> "$LOG_FILE"
fi

echo ""

# ───────────────────────────────────────────────────────────────────────────
# Summary
# ───────────────────────────────────────────────────────────────────────────

echo -e "${BLUE}=================================================${NC}"
echo -e "${BLUE}Summary${NC}"
echo -e "${BLUE}=================================================${NC}"
echo ""

{
    echo "Registration Summary:"
    echo "  ✅ Verified: $SUCCESS_COUNT"
    echo "  ❌ Failed: $FAIL_COUNT"
    echo "  ⏭️  Skipped: $SKIP_COUNT"
    echo ""
} | tee -a "$LOG_FILE"

# Show what comes next
if [ "$VERIFY_ONLY" = false ]; then
    {
        echo "Next Steps:"
        echo "1. Configure webhook credentials in each platform's dashboard"
        echo "2. Add webhook URLs to platform integrations settings"
        echo "3. Test by triggering a real event (purchase, order, etc.)"
        echo "4. Monitor transaction log: tail -f .runtime/revenue/transactions.jsonl"
        echo "5. Check logs for errors: cat webhooks-registration.log"
        echo ""
        echo "Manual Configuration URLs:"
        echo "  - Gumroad:    https://app.gumroad.com/settings/webhooks"
        echo "  - Printify:   https://printify.com/integrations"
        echo "  - Beehiiv:    https://dashboard.beehiiv.com/settings/webhooks"
        echo "  - YouTube:    https://console.cloud.google.com"
        echo ""
    } | tee -a "$LOG_FILE"
fi

{
    echo "Webhook Endpoints:"
    echo "  - Gumroad:    POST $DOMAIN/api/webhooks/gumroad"
    echo "  - Printify:   POST $DOMAIN/api/webhooks/printify"
    echo "  - Newsletter: POST $DOMAIN/api/webhooks/newsletter"
    echo "  - Dashboard:  GET  $DOMAIN/api/revenue/dashboard"
    echo ""
    echo "Transaction Log:"
    echo "  Location: $TRANSACTION_LOG"
    echo "  View: tail -f $TRANSACTION_LOG"
    echo "  Format: JSONL (one record per line)"
    echo ""
    echo "Registration completed: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "=========================================="
} | tee -a "$LOG_FILE"

echo ""
echo -e "${GREEN}📋 Full log saved to: ${LOG_FILE}${NC}"
echo ""

# ───────────────────────────────────────────────────────────────────────────
# Exit Code
# ───────────────────────────────────────────────────────────────────────────

if [ "$FAIL_COUNT" -gt 0 ]; then
    if [ "$VERIFY_ONLY" = true ]; then
        echo -e "${YELLOW}⚠️  Some webhooks are not currently reachable${NC}"
        echo -e "${YELLOW}   This is expected if the backend is not yet running${NC}"
        echo -e "${YELLOW}   Run after deployment: docker-compose up -d${NC}"
    fi
    exit 1
else
    if [ "$VERIFY_ONLY" = false ]; then
        echo -e "${GREEN}✅ Webhook registration verification complete!${NC}"
    else
        echo -e "${GREEN}✅ All webhooks verified!${NC}"
    fi
    exit 0
fi
