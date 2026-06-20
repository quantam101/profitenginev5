#!/bin/bash

# E2E Revenue System Verification Script
# Tests all 5 revenue channels and dashboard

set -e

BASE_URL="https://profitengine.alreadyherellc.com"
VERIFY_ENDPOINT="http://localhost:3000"  # For local dev testing
PROD_ENDPOINT="$BASE_URL"

echo "=========================================="
echo "PROFITENGINE REVENUE SYSTEM VERIFICATION"
echo "=========================================="
echo "Test Date: $(date)"
echo ""

# Test results
TESTS_PASSED=0
TESTS_FAILED=0

# Helper function to make API calls
api_call() {
    local method=$1
    local endpoint=$2
    local data=$3
    local url="${PROD_ENDPOINT}${endpoint}"
    
    echo "  → $method $url"
    
    if [ -z "$data" ]; then
        curl -s -X "$method" "$url" -H "Content-Type: application/json"
    else
        curl -s -X "$method" "$url" -H "Content-Type: application/json" -d "$data"
    fi
}

test_result() {
    local name=$1
    local status=$2
    
    if [ "$status" = "pass" ]; then
        echo "✅ $name"
        ((TESTS_PASSED++))
    else
        echo "❌ $name"
        ((TESTS_FAILED++))
    fi
}

# TEST 1: GUMROAD WEBHOOK
echo ""
echo "TEST 1: GUMROAD WEBHOOK"
echo "------------------------"
GUMROAD_PAYLOAD='{
  "product_id": "test_product_001",
  "product_name": "Test eBook",
  "price": "19.99",
  "purchase_email": "buyer@example.com",
  "license_key": "license_12345",
  "timestamp": '$(date +%s)',
  "variant_title": "PDF Edition"
}'

echo "Sending test payload..."
GUMROAD_RESP=$(api_call POST "/api/webhooks/gumroad" "$GUMROAD_PAYLOAD")
echo "$GUMROAD_RESP" | grep -q '"ok":true' && test_result "Gumroad webhook accepted" "pass" || test_result "Gumroad webhook accepted" "fail"

# Verify transaction was logged
echo "Verifying transaction logged..."
if grep -q "gumroad" ".runtime/revenue/transactions.jsonl" 2>/dev/null; then
    test_result "Gumroad transaction persisted" "pass"
else
    test_result "Gumroad transaction persisted" "fail"
fi

# TEST 2: PRINTIFY WEBHOOK
echo ""
echo "TEST 2: PRINTIFY WEBHOOK"
echo "------------------------"
PRINTIFY_PAYLOAD='{
  "action": "order.created",
  "data": {
    "id": "order_12345",
    "status": "pending",
    "total_price": 49.99,
    "currency": "usd",
    "cost": 30.00,
    "line_items": [
      {
        "title": "Premium T-Shirt",
        "quantity": 2,
        "sku": "tshirt-001"
      }
    ],
    "shipping_address": {
      "first_name": "John",
      "last_name": "Doe"
    }
  }
}'

echo "Sending test payload..."
PRINTIFY_RESP=$(api_call POST "/api/webhooks/printify" "$PRINTIFY_PAYLOAD")
echo "$PRINTIFY_RESP" | grep -q '"ok":true' && test_result "Printify webhook accepted" "pass" || test_result "Printify webhook accepted" "fail"

# Verify profit calculation
if echo "$PRINTIFY_RESP" | grep -q '"profit"'; then
    test_result "Printify profit calculated" "pass"
else
    test_result "Printify profit calculated" "fail"
fi

# TEST 3: REVENUE DASHBOARD
echo ""
echo "TEST 3: REVENUE DASHBOARD"
echo "------------------------"
DASHBOARD_RESP=$(api_call GET "/api/revenue/dashboard" "")

echo "Checking dashboard structure..."
echo "$DASHBOARD_RESP" | grep -q '"month_revenue"' && test_result "Dashboard returns month_revenue" "pass" || test_result "Dashboard returns month_revenue" "fail"
echo "$DASHBOARD_RESP" | grep -q '"monthly_target"' && test_result "Dashboard returns monthly_target" "pass" || test_result "Dashboard returns monthly_target" "fail"
echo "$DASHBOARD_RESP" | grep -q '"by_channel"' && test_result "Dashboard returns by_channel" "pass" || test_result "Dashboard returns by_channel" "fail"

# Verify target ($2,500)
DASHBOARD_TARGET=$(echo "$DASHBOARD_RESP" | grep -o '"monthly_target":[0-9]*' | cut -d: -f2)
if [ "$DASHBOARD_TARGET" = "2500" ]; then
    test_result "Monthly target is $2,500" "pass"
else
    test_result "Monthly target is $2,500" "fail"
fi

# TEST 4: SPONSOR PAYMENT (Stripe)
echo ""
echo "TEST 4: SPONSOR PAYMENT (STRIPE)"
echo "--------------------------------"
SPONSOR_PAYLOAD='{
  "sponsor_name": "TechCorp Inc",
  "sponsorship_amount": 250,
  "return_url": "https://profitengine.alreadyherellc.com/success",
  "duration": "1 month",
  "email": "sponsor@techcorp.com"
}'

echo "Creating Stripe checkout session..."
SPONSOR_RESP=$(api_call POST "/api/payments/sponsor" "$SPONSOR_PAYLOAD")
echo "$SPONSOR_RESP" | grep -q '"ok":true' && test_result "Stripe session created" "pass" || test_result "Stripe session created" "fail"
echo "$SPONSOR_RESP" | grep -q '"session_url"' && test_result "Checkout URL generated" "pass" || test_result "Checkout URL generated" "fail"

# Extract session ID for verification
SESSION_ID=$(echo "$SPONSOR_RESP" | grep -o '"session_id":"[^"]*' | cut -d: -f2 | tr -d '"')
if [ -n "$SESSION_ID" ]; then
    echo "Session ID: $SESSION_ID"
    test_result "Session ID extracted" "pass"
    
    # Verify session status
    echo "Verifying session status..."
    STATUS_RESP=$(api_call GET "/api/payments/sponsor?session_id=$SESSION_ID" "")
    echo "$STATUS_RESP" | grep -q '"status"' && test_result "Session status retrievable" "pass" || test_result "Session status retrievable" "fail"
else
    test_result "Session ID extracted" "fail"
fi

# TEST 5: WEBHOOK HEALTH CHECKS
echo ""
echo "TEST 5: WEBHOOK HEALTH CHECKS"
echo "------------------------------"
GUMROAD_HEALTH=$(api_call GET "/api/webhooks/gumroad" "")
echo "$GUMROAD_HEALTH" | grep -q '"ok":true' && test_result "Gumroad endpoint healthy" "pass" || test_result "Gumroad endpoint healthy" "fail"

PRINTIFY_HEALTH=$(api_call GET "/api/webhooks/printify" "")
echo "$PRINTIFY_HEALTH" | grep -q '"ok":true' && test_result "Printify endpoint healthy" "pass" || test_result "Printify endpoint healthy" "fail"

# TEST 6: TRANSACTION FILE VERIFICATION
echo ""
echo "TEST 6: TRANSACTION LOG VERIFICATION"
echo "-------------------------------------"
TRANSACTION_COUNT=$(grep -c . ".runtime/revenue/transactions.jsonl" 2>/dev/null || echo "0")
echo "Total transactions logged: $TRANSACTION_COUNT"

if [ "$TRANSACTION_COUNT" -gt 0 ]; then
    test_result "Transaction log populated" "pass"
    echo "Sample transaction:"
    head -1 ".runtime/revenue/transactions.jsonl" | jq . 2>/dev/null || head -1 ".runtime/revenue/transactions.jsonl"
else
    test_result "Transaction log populated" "fail"
fi

# SUMMARY
echo ""
echo "=========================================="
echo "TEST SUMMARY"
echo "=========================================="
echo "Passed: $TESTS_PASSED"
echo "Failed: $TESTS_FAILED"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo "✅ ALL TESTS PASSED - SYSTEM READY FOR LIVE TRAFFIC"
    exit 0
else
    echo "⚠️  SOME TESTS FAILED - REVIEW ABOVE FOR DETAILS"
    exit 1
fi
