#!/bin/bash
# Gumroad Webhook Testing & Integration Commands
# Save as GUMROAD_COMMANDS.sh and source it: source GUMROAD_COMMANDS.sh

# =============================================================================
# WEBHOOK HEALTH CHECK
# =============================================================================

# Test webhook health on production
gumroad-health-prod() {
  curl -s https://profitengine.alreadyherellc.com/api/webhooks/gumroad | jq .
}

# Test webhook health on localhost
gumroad-health-local() {
  curl -s http://localhost:3000/api/webhooks/gumroad | jq .
}

# =============================================================================
# SEND TEST WEBHOOK PAYLOADS
# =============================================================================

# Send test sale to production
gumroad-test-prod() {
  curl -X POST https://profitengine.alreadyherellc.com/api/webhooks/gumroad \
    -H "Content-Type: application/json" \
    -d '{
      "product_id": "prod_test_'"$(date +%s)"'",
      "product_name": "Test Ebook: Trading 2026",
      "price": "29.99",
      "purchase_email": "test@example.com",
      "license_key": "LICENSE_test_'"$(date +%s%N | cut -b1-13)"'",
      "variant_title": "PDF Bundle",
      "timestamp": "'"$(date +%s)"'",
      "currency": "usd"
    }' | jq .
}

# Send test sale to localhost
gumroad-test-local() {
  curl -X POST http://localhost:3000/api/webhooks/gumroad \
    -H "Content-Type: application/json" \
    -d '{
      "product_id": "prod_test_'"$(date +%s)"'",
      "product_name": "Test Ebook: Investing Guide",
      "price": "19.99",
      "purchase_email": "local-test@example.com",
      "license_key": "LICENSE_test_local_'"$(date +%s%N | cut -b1-13)"'",
      "timestamp": "'"$(date +%s)"'"
    }' | jq .
}

# Send high-value test sale
gumroad-test-high-value() {
  curl -X POST https://profitengine.alreadyherellc.com/api/webhooks/gumroad \
    -H "Content-Type: application/json" \
    -d '{
      "product_id": "prod_premium_bundle",
      "product_name": "Premium Trading Bundle: Everything",
      "price": "99.99",
      "purchase_email": "premium-buyer@example.com",
      "license_key": "LICENSE_premium_'"$(date +%s%N | cut -b1-13)"'",
      "variant_title": "12-Month License",
      "timestamp": "'"$(date +%s)"'"
    }' | jq .
}

# Send sale without license key
gumroad-test-no-license() {
  curl -X POST https://profitengine.alreadyherellc.com/api/webhooks/gumroad \
    -H "Content-Type: application/json" \
    -d '{
      "product_id": "prod_basic",
      "product_name": "Basic Ebook",
      "price": "9.99",
      "purchase_email": "basic@example.com",
      "timestamp": "'"$(date +%s)"'"
    }' | jq .
}

# Send batch of test sales
gumroad-test-batch() {
  for i in {1..5}; do
    echo "Sending test $i/5..."
    curl -X POST https://profitengine.alreadyherellc.com/api/webhooks/gumroad \
      -H "Content-Type: application/json" \
      -d '{
        "product_id": "prod_batch_'"$i"'",
        "product_name": "Batch Test Ebook #'"$i"'",
        "price": "'$((10 + i * 5))'.99",
        "purchase_email": "batch-user-'"$i"'@example.com",
        "timestamp": "'"$(date +%s)"'"
      }' > /dev/null
    sleep 1
  done
  echo "Batch complete. Check .runtime/revenue/transactions.jsonl"
}

# =============================================================================
# REVENUE LEDGER QUERIES
# =============================================================================

# View all Gumroad transactions
gumroad-ledger-all() {
  cat .runtime/revenue/transactions.jsonl | jq 'select(.channel == "gumroad")'
}

# View today's Gumroad sales
gumroad-ledger-today() {
  TODAY=$(date +%Y-%m-%d)
  cat .runtime/revenue/transactions.jsonl | jq 'select(.channel == "gumroad" and .timestamp | startswith("'"$TODAY"'"))'
}

# View this week's Gumroad sales
gumroad-ledger-week() {
  WEEK_AGO=$(date -d "7 days ago" +%Y-%m-%d)
  cat .runtime/revenue/transactions.jsonl | jq 'select(.channel == "gumroad" and .timestamp >= "'"$WEEK_AGO"'")'
}

# View this month's Gumroad sales
gumroad-ledger-month() {
  MONTH=$(date +%Y-%m)
  cat .runtime/revenue/transactions.jsonl | jq 'select(.channel == "gumroad" and .timestamp | startswith("'"$MONTH"'"))'
}

# Calculate total Gumroad revenue (today)
gumroad-revenue-today() {
  TODAY=$(date +%Y-%m-%d)
  TOTAL=$(cat .runtime/revenue/transactions.jsonl | jq 'select(.channel == "gumroad" and .timestamp | startswith("'"$TODAY"'")) | .amount_usd' | awk '{sum+=$1} END {print sum}')
  echo "Gumroad Revenue (Today): \$$TOTAL"
}

# Calculate total Gumroad revenue (all time)
gumroad-revenue-total() {
  TOTAL=$(cat .runtime/revenue/transactions.jsonl | jq 'select(.channel == "gumroad") | .amount_usd' | awk '{sum+=$1} END {print sum}')
  echo "Gumroad Revenue (All Time): \$$TOTAL"
}

# Count Gumroad transactions
gumroad-count() {
  COUNT=$(cat .runtime/revenue/transactions.jsonl | jq 'select(.channel == "gumroad")' | wc -l)
  echo "Total Gumroad Transactions: $COUNT"
}

# Show top products by revenue
gumroad-top-products() {
  echo "=== Top Gumroad Products by Revenue ==="
  cat .runtime/revenue/transactions.jsonl | jq 'select(.channel == "gumroad") | {product: .metadata.product_name, amount: .amount_usd}' | jq -s 'group_by(.product) | map({product: .[0].product, total: (map(.amount) | add), count: length}) | sort_by(.total) | reverse' | jq '.[] | "\(.product): \($(.total)) (\(.count) sales)"'
}

# Show customer analysis
gumroad-customer-analysis() {
  echo "=== Gumroad Customer Analysis ==="
  cat .runtime/revenue/transactions.jsonl | jq 'select(.channel == "gumroad") | .metadata.purchaser_email' | sort | uniq -c | sort -rn
}

# =============================================================================
# PYTHON INTEGRATION
# =============================================================================

# Fetch all Gumroad products
gumroad-fetch-products() {
  python3 << 'EOF'
import asyncio
from backend.services.gumroad_service import get_gumroad_service

async def main():
    service = get_gumroad_service()
    products = await service.fetch_products()
    for product in products:
        print(f"  {product.name}: ${product.price}")
    print(f"\nTotal products: {len(products)}")

asyncio.run(main())
EOF
}

# Fetch all Gumroad sales
gumroad-fetch-sales() {
  python3 << 'EOF'
import asyncio
from backend.services.gumroad_service import get_gumroad_service

async def main():
    service = get_gumroad_service()
    sales = await service.fetch_sales()
    for sale in sales:
        print(f"  {sale.product_name}: ${sale.amount_usd} from {sale.purchaser_email}")
    print(f"\nTotal sales: {len(sales)}")

asyncio.run(main())
EOF
}

# Verify a license key
gumroad-verify-license() {
  PRODUCT_ID="${1:-prod_test}"
  LICENSE_KEY="${2:-LICENSE_test}"

  python3 << EOF
import asyncio
from backend.services.gumroad_service import get_gumroad_service

async def main():
    service = get_gumroad_service()
    is_valid = await service.verify_license("$PRODUCT_ID", "$LICENSE_KEY")
    print(f"License valid: {is_valid}")

asyncio.run(main())
EOF
}

# =============================================================================
# DEVELOPMENT COMMANDS
# =============================================================================

# Start Next.js dev server
gumroad-dev() {
  npm run dev
}

# Run integration tests
gumroad-test() {
  npm test -- test_gumroad_webhook.ts
}

# Watch logs in real time (requires 'tail' with -f)
gumroad-watch-logs() {
  tail -f .runtime/revenue/transactions.jsonl | jq 'select(.channel == "gumroad")'
}

# Pretty print last transaction
gumroad-last-transaction() {
  tail -1 .runtime/revenue/transactions.jsonl | jq .
}

# Validate JSONL format
gumroad-validate-jsonl() {
  echo "Validating .runtime/revenue/transactions.jsonl..."
  python3 << 'EOF'
import json
with open('.runtime/revenue/transactions.jsonl') as f:
    for i, line in enumerate(f, 1):
        try:
            json.loads(line)
        except json.JSONDecodeError as e:
            print(f"Error on line {i}: {e}")
            exit(1)
    print(f"✅ All {i} lines are valid JSON")
EOF
}

# =============================================================================
# DOCUMENTATION
# =============================================================================

gumroad-help() {
  cat << 'EOF'
╔════════════════════════════════════════════════════════════════════════════╗
║                    GUMROAD WEBHOOK COMMANDS                               ║
╚════════════════════════════════════════════════════════════════════════════╝

HEALTH CHECK:
  gumroad-health-prod         Test webhook on production
  gumroad-health-local        Test webhook locally

SEND TEST WEBHOOKS:
  gumroad-test-prod           Send test sale to production
  gumroad-test-local          Send test sale to localhost
  gumroad-test-high-value     Send $99.99 test sale
  gumroad-test-no-license     Send test without license key
  gumroad-test-batch          Send 5 test sales in batch

REVENUE LEDGER:
  gumroad-ledger-all          View all Gumroad transactions
  gumroad-ledger-today        View today's sales
  gumroad-ledger-week         View this week's sales
  gumroad-ledger-month        View this month's sales
  gumroad-revenue-today       Calculate today's revenue
  gumroad-revenue-total       Calculate all-time revenue
  gumroad-count               Count total transactions
  gumroad-top-products        Show top products by revenue
  gumroad-customer-analysis   Show customer distribution

PYTHON/BACKEND:
  gumroad-fetch-products      Fetch all products from Gumroad API
  gumroad-fetch-sales         Fetch all sales from Gumroad API
  gumroad-verify-license      Verify a license key (args: product_id license_key)

DEVELOPMENT:
  gumroad-dev                 Start Next.js dev server
  gumroad-test                Run integration tests
  gumroad-watch-logs          Tail transaction log in real-time
  gumroad-last-transaction    Show last transaction
  gumroad-validate-jsonl      Validate JSONL format

HELP:
  gumroad-help                Show this help message

EXAMPLES:
  gumroad-test-prod                              # Send test to prod
  gumroad-revenue-today                          # Check today's revenue
  gumroad-ledger-month | jq '.amount_usd'        # Sum monthly revenue
  gumroad-verify-license prod_123 LICENSE_abc    # Verify license

EOF
}

# Show help on script load
echo "Gumroad commands loaded. Type 'gumroad-help' for available commands."
