#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════════════
# ETSY/PRINTIFY AUTOMATION — API EXAMPLES
# ═══════════════════════════════════════════════════════════════════════════════
#
# Complete curl examples for all API endpoints.
# Requires: AUTOMATION_API_TOKEN set in environment
#
# Usage:
#   export BASE_URL="http://localhost:3000"
#   export AUTH_TOKEN="your-secret-token"
#   source examples/etsy-api-examples.sh
#

BASE_URL="${BASE_URL:-http://localhost:3000}"
AUTH_TOKEN="${AUTH_TOKEN:-test-token}"

echo "═══════════════════════════════════════════════════════════════════════════════"
echo "ETSY/PRINTIFY AUTOMATION API EXAMPLES"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""
echo "Base URL: $BASE_URL"
echo "Auth Token: ${AUTH_TOKEN:0:10}..."
echo ""

# ═══════════════════════════════════════════════════════════════════════════════
# 1. HEALTH CHECK
# ═══════════════════════════════════════════════════════════════════════════════

health_check() {
  echo "📋 Health Check"
  echo "───────────────────────────────────────────────────────────────────────────"
  curl -X GET "$BASE_URL/api/automation/etsy" \
    -H "Authorization: Bearer $AUTH_TOKEN" \
    -H "Content-Type: application/json" \
    -s | jq .
  echo ""
}

# ═══════════════════════════════════════════════════════════════════════════════
# 2. CREATE SINGLE PRODUCT
# ═══════════════════════════════════════════════════════════════════════════════

create_single_product() {
  echo "🎨 Create Single Product"
  echo "───────────────────────────────────────────────────────────────────────────"
  curl -X POST "$BASE_URL/api/automation/etsy" \
    -H "Authorization: Bearer $AUTH_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "action": "create",
      "templates": [
        {
          "name": "Classic Trading T-Shirt",
          "description": "Premium 100% organic cotton t-shirt with trading graphics",
          "category": "apparel",
          "printifyProductId": "16",
          "basePrice": 24.99,
          "designs": [
            {
              "id": "design-black",
              "name": "Black Shirt",
              "colors": ["black"],
              "sizes": ["XS", "S", "M", "L", "XL", "2XL"],
              "imageUrl": "https://via.placeholder.com/500x500?text=Trading+Logo",
              "sku": "tshirt-black"
            }
          ],
          "tags": ["t-shirt", "trading", "apparel"],
          "materials": ["100% organic cotton"]
        }
      ]
    }' \
    -s | jq .
  echo ""
}

# ═══════════════════════════════════════════════════════════════════════════════
# 3. CREATE MULTIPLE PRODUCTS (BULK)
# ═══════════════════════════════════════════════════════════════════════════════

create_bulk_products() {
  echo "📦 Create Multiple Products"
  echo "───────────────────────────────────────────────────────────────────────────"
  curl -X POST "$BASE_URL/api/automation/etsy" \
    -H "Authorization: Bearer $AUTH_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "action": "create",
      "templates": [
        {
          "name": "Trading T-Shirt",
          "description": "Premium t-shirt with trading graphics",
          "category": "apparel",
          "printifyProductId": "16",
          "basePrice": 24.99,
          "designs": [
            {
              "id": "tshirt-1",
              "name": "Black",
              "colors": ["black"],
              "sizes": ["S", "M", "L", "XL"],
              "imageUrl": "https://via.placeholder.com/500x500?text=Trading",
              "sku": "tshirt-black"
            }
          ],
          "tags": ["t-shirt", "trading"]
        },
        {
          "name": "Profit Engine Hoodie",
          "description": "Comfortable hoodie for traders",
          "category": "apparel",
          "printifyProductId": "22",
          "basePrice": 49.99,
          "designs": [
            {
              "id": "hoodie-1",
              "name": "Black",
              "colors": ["black"],
              "sizes": ["S", "M", "L", "XL"],
              "imageUrl": "https://via.placeholder.com/500x500?text=Hoodie",
              "sku": "hoodie-black"
            }
          ],
          "tags": ["hoodie", "apparel"]
        }
      ]
    }' \
    -s | jq .
  echo ""
}

# ═══════════════════════════════════════════════════════════════════════════════
# 4. SYNC INVENTORY
# ═══════════════════════════════════════════════════════════════════════════════

sync_inventory() {
  echo "📊 Sync Inventory"
  echo "───────────────────────────────────────────────────────────────────────────"
  echo "Note: Replace printifyId, etsyId, and variantId with your actual values"
  echo ""
  curl -X POST "$BASE_URL/api/automation/etsy" \
    -H "Authorization: Bearer $AUTH_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "action": "sync-inventory",
      "productMappings": [
        {
          "printifyId": "YOUR_PRINTIFY_PRODUCT_ID",
          "etsyId": 123456789,
          "variantMapping": {
            "tshirt-black": {
              "printifyId": "YOUR_VARIANT_ID",
              "etsyPropertyId": 200
            }
          }
        }
      ],
      "saveReport": true
    }' \
    -s | jq .
  echo ""
}

# ═══════════════════════════════════════════════════════════════════════════════
# 5. UPDATE PRICES
# ═══════════════════════════════════════════════════════════════════════════════

update_prices() {
  echo "💰 Update Prices"
  echo "───────────────────────────────────────────────────────────────────────────"
  echo "Note: Replace etsyId and variantId with your actual values"
  echo ""
  curl -X POST "$BASE_URL/api/automation/etsy" \
    -H "Authorization: Bearer $AUTH_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "action": "update-prices",
      "etsyListingId": 123456789,
      "printifyVariants": [
        {
          "id": "variant-1",
          "title": "Black/S",
          "sku": "tshirt-black-s",
          "price": 8.99,
          "quantity": 100,
          "options": [
            { "name": "color", "value": "black" },
            { "name": "size", "value": "S" }
          ],
          "status": "active"
        },
        {
          "id": "variant-2",
          "title": "Black/M",
          "sku": "tshirt-black-m",
          "price": 8.99,
          "quantity": 100,
          "options": [
            { "name": "color", "value": "black" },
            { "name": "size", "value": "M" }
          ],
          "status": "active"
        }
      ],
      "markupPercent": 0.4,
      "saveReport": true
    }' \
    -s | jq .
  echo ""
}

# ═══════════════════════════════════════════════════════════════════════════════
# 6. TRACK ORDERS
# ═══════════════════════════════════════════════════════════════════════════════

track_orders() {
  echo "📦 Track Orders"
  echo "───────────────────────────────────────────────────────────────────────────"
  echo "Note: Replace order IDs with your actual order IDs"
  echo ""
  curl -X POST "$BASE_URL/api/automation/etsy" \
    -H "Authorization: Bearer $AUTH_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "action": "track-orders",
      "orderIds": [
        "order-123",
        "order-456",
        "order-789"
      ]
    }' \
    -s | jq .
  echo ""
}

# ═══════════════════════════════════════════════════════════════════════════════
# MENU
# ═══════════════════════════════════════════════════════════════════════════════

show_menu() {
  echo "Available Examples:"
  echo "  1. health_check         - Check API status"
  echo "  2. create_single_product - Create one product"
  echo "  3. create_bulk_products - Create multiple products"
  echo "  4. sync_inventory       - Sync Printify → Etsy"
  echo "  5. update_prices        - Update prices with margin"
  echo "  6. track_orders         - Get order status"
  echo "  7. all                  - Run all examples"
  echo ""
  echo "Usage: health_check"
  echo "Or call a function directly"
  echo ""
}

# Run all examples
run_all() {
  health_check
  create_single_product
  create_bulk_products
  sync_inventory
  update_prices
  track_orders
}

# Show menu if no arguments
if [ $# -eq 0 ]; then
  show_menu
else
  case "$1" in
    1|health) health_check ;;
    2|create) create_single_product ;;
    3|bulk) create_bulk_products ;;
    4|sync) sync_inventory ;;
    5|price) update_prices ;;
    6|track) track_orders ;;
    7|all) run_all ;;
    *) echo "Unknown command: $1"; show_menu ;;
  esac
fi
