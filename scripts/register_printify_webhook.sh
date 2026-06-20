#!/bin/bash
set -euo pipefail

# Register Printify API webhook for real-time POD order tracking
# Usage: ./scripts/register_printify_webhook.sh [--shop-id SHOP_ID] [--verify] [--remove WEBHOOK_ID]

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Load environment
if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
else
    echo -e "${RED}❌ .env file not found${NC}"
    exit 1
fi

# Configuration
PRINTIFY_API_TOKEN="${PRINTIFY_API_TOKEN:-}"
DOMAIN="${PUBLIC_SITE_URL:-https://profitengine.alreadyherellc.com}"
WEBHOOK_URL="${DOMAIN}/api/webhooks/printify"

# Flags
SHOP_ID="${1:-}"
VERIFY_ONLY=false
REMOVE_WEBHOOK=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --shop-id)
            SHOP_ID="$2"
            shift 2
            ;;
        --verify)
            VERIFY_ONLY=true
            shift
            ;;
        --remove)
            REMOVE_WEBHOOK="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validate API token
if [ -z "$PRINTIFY_API_TOKEN" ]; then
    echo -e "${RED}❌ Error: PRINTIFY_API_TOKEN not set${NC}"
    echo -e "${YELLOW}Set it in .env: PRINTIFY_API_TOKEN='your-token'${END}"
    exit 1
fi

# Helper function: Make API request
api_request() {
    local method=$1
    local endpoint=$2
    local data=${3:-}

    local url="https://api.printify.com/v1${endpoint}"
    local headers=(
        -H "Authorization: Bearer ${PRINTIFY_API_TOKEN}"
        -H "Content-Type: application/json"
        -H "User-Agent: ProfitEngine/5.0"
    )

    if [ -n "$data" ]; then
        curl -s -X "$method" "$url" "${headers[@]}" -d "$data"
    else
        curl -s -X "$method" "$url" "${headers[@]}"
    fi
}

# Get shops
get_shops() {
    api_request GET "/shops.json" | jq -r '.[] | "\(.id)|\(.title)"'
}

# Verify webhook endpoint
verify_endpoint() {
    echo -e "${BLUE}Testing webhook endpoint...${NC}"

    local test_payload='{
        "action": "order.created",
        "data": {
            "id": "999999",
            "status": "pending",
            "total_price": 99.99,
            "currency": "USD",
            "line_items": [{"title": "Test Product", "quantity": 1}]
        }
    }'

    local http_code=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST "$WEBHOOK_URL" \
        -H "Content-Type: application/json" \
        -d "$test_payload" \
        --connect-timeout 10)

    if [[ "$http_code" == "200" || "$http_code" == "400" ]]; then
        echo -e "   Webhook endpoint: ${GREEN}reachable${NC} (HTTP $http_code)"
        return 0
    else
        echo -e "   Webhook endpoint: ${RED}unreachable${NC} (HTTP $http_code)"
        return 1
    fi
}

# Get existing webhooks for shop
get_webhooks() {
    local shop_id=$1
    api_request GET "/shops/${shop_id}/webhooks.json" | jq -r '.[] | "\(.id)|\(.address)|\(.topic)"'
}

# Register webhook
register_webhook() {
    local shop_id=$1
    local domain=$2

    echo -e "${BLUE}Registering webhook...${NC}"

    # Check for existing webhook
    local existing=$(get_webhooks "$shop_id" | grep -F "${domain}/api/webhooks/printify" || true)
    if [ -n "$existing" ]; then
        echo -e "${YELLOW}⚠️  Webhook already registered:${NC}"
        echo "   $existing" | tr '|' '\n' | awk '{print "   " $0}'
        return 0
    fi

    # Register new webhook
    local payload='{"topic":"order:created","address":"'"${domain}/api/webhooks/printify"'"}'
    local response=$(api_request POST "/shops/${shop_id}/webhooks.json" "$payload")

    local webhook_id=$(echo "$response" | jq -r '.id // empty')
    if [ -n "$webhook_id" ]; then
        echo -e "${GREEN}✅ Webhook registered successfully!${NC}"
        echo "   ID: $webhook_id"
        echo "   URL: ${domain}/api/webhooks/printify"
        echo "   Topic: order:created"
        return 0
    else
        echo -e "${RED}❌ Failed to register webhook${NC}"
        echo "$response" | jq '.'
        return 1
    fi
}

# Remove webhook
remove_webhook() {
    local shop_id=$1
    local webhook_id=$2

    echo -e "${BLUE}Removing webhook...${NC}"

    local http_code=$(curl -s -o /dev/null -w "%{http_code}" \
        -X DELETE "https://api.printify.com/v1/shops/${shop_id}/webhooks/${webhook_id}.json" \
        -H "Authorization: Bearer ${PRINTIFY_API_TOKEN}" \
        -H "User-Agent: ProfitEngine/5.0")

    if [[ "$http_code" == "200" || "$http_code" == "204" ]]; then
        echo -e "${GREEN}✅ Webhook removed successfully!${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed to remove webhook (HTTP $http_code)${NC}"
        return 1
    fi
}

# Main execution
main() {
    echo -e "\n${BLUE}$(printf '%.0s=' {1..60})${NC}"
    echo -e "${BLUE}Printify Webhook Registration${NC}"
    echo -e "${BLUE}$(printf '%.0s=' {1..60})${NC}\n"

    echo "Domain: $DOMAIN"
    echo "Webhook URL: $WEBHOOK_URL"
    echo ""

    # Get or select shop
    echo -e "${BLUE}Fetching available shops...${NC}"
    shops=$(get_shops)

    if [ -z "$shops" ]; then
        echo -e "${RED}❌ No shops found. Create one at https://printify.com${NC}"
        exit 1
    fi

    # Select shop
    if [ -n "$SHOP_ID" ]; then
        selected_shop=$SHOP_ID
    else
        echo -e "${BLUE}Available shops:${NC}"
        declare -a shop_ids
        declare -a shop_names
        local idx=1

        while IFS='|' read -r id name; do
            shop_ids[$idx]=$id
            shop_names[$idx]=$name
            echo "  $idx. $name (ID: $id)"
            ((idx++))
        done <<< "$shops"

        if [ ${#shop_ids[@]} -eq 2 ]; then
            selected_shop=${shop_ids[1]}
            echo -e "\n${GREEN}✅ Using: ${shop_names[1]}${NC}"
        else
            read -p "$(echo -e ${BLUE}Select shop: ${NC})" choice
            selected_shop=${shop_ids[$choice]}
        fi
    fi

    # If verify-only, test endpoint and exit
    if [ "$VERIFY_ONLY" = true ]; then
        verify_endpoint
        exit $?
    fi

    # If remove, delete webhook and exit
    if [ -n "$REMOVE_WEBHOOK" ]; then
        remove_webhook "$selected_shop" "$REMOVE_WEBHOOK"
        exit $?
    fi

    # Register webhook
    if register_webhook "$selected_shop" "$DOMAIN"; then
        echo ""
        verify_endpoint
        echo ""
        echo -e "${GREEN}$(printf '%.0s=' {1..60})${NC}"
        echo -e "${GREEN}Webhook registration complete!${NC}"
        echo -e "${GREEN}$(printf '%.0s=' {1..60})${NC}\n"

        echo -e "${BLUE}Next steps:${NC}"
        echo "1. Printify will send order events to your webhook"
        echo "2. Orders logged to .runtime/revenue/transactions.jsonl"
        echo "3. View latest orders: tail -f .runtime/revenue/transactions.jsonl"
        echo ""
    else
        exit 1
    fi
}

main
