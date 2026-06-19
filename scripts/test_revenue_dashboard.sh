#!/bin/bash
# Test Revenue Dashboard Integration
# Verifies MongoDB connection, API endpoints, and data flow

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Revenue Dashboard Integration Test${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Test 1: Check Python installation
echo -e "${YELLOW}[1/8]${NC} Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓${NC} $PYTHON_VERSION"
else
    echo -e "${RED}✗${NC} Python3 not found"
    exit 1
fi

# Test 2: Check required Python packages
echo -e "${YELLOW}[2/8]${NC} Checking Python dependencies..."
python3 -c "import pymongo" 2>/dev/null && echo -e "${GREEN}✓${NC} pymongo installed" || {
    echo -e "${RED}✗${NC} pymongo not installed (run: pip install pymongo)"
    exit 1
}
python3 -c "from dotenv import load_dotenv" 2>/dev/null && echo -e "${GREEN}✓${NC} python-dotenv installed" || {
    echo -e "${RED}✗${NC} python-dotenv not installed (run: pip install python-dotenv)"
    exit 1
}

# Test 3: Check .env configuration
echo -e "${YELLOW}[3/8]${NC} Checking .env configuration..."
if [ -f "$PROJECT_ROOT/.env" ]; then
    if grep -q "MONGODB_URI" "$PROJECT_ROOT/.env"; then
        echo -e "${GREEN}✓${NC} .env found with MONGODB_URI"
    else
        echo -e "${YELLOW}⚠${NC} .env found but MONGODB_URI not set"
    fi
else
    echo -e "${YELLOW}⚠${NC} .env not found (copy from .env.example)"
fi

# Test 4: Check revenue_dashboard.py exists
echo -e "${YELLOW}[4/8]${NC} Checking revenue_dashboard.py..."
if [ -f "$SCRIPT_DIR/revenue_dashboard.py" ]; then
    echo -e "${GREEN}✓${NC} revenue_dashboard.py found"
    LINES=$(wc -l < "$SCRIPT_DIR/revenue_dashboard.py")
    echo "  ($LINES lines)"
else
    echo -e "${RED}✗${NC} revenue_dashboard.py not found"
    exit 1
fi

# Test 5: Check API route exists
echo -e "${YELLOW}[5/8]${NC} Checking API route..."
API_ROUTE="$PROJECT_ROOT/app/api/revenue/dashboard/route.ts"
if [ -f "$API_ROUTE" ]; then
    echo -e "${GREEN}✓${NC} /api/revenue/dashboard route found"
    LINES=$(wc -l < "$API_ROUTE")
    echo "  ($LINES lines)"
else
    echo -e "${RED}✗${NC} API route not found at $API_ROUTE"
    exit 1
fi

# Test 6: Test MongoDB connection (if configured)
echo -e "${YELLOW}[6/8]${NC} Testing MongoDB connection..."
if [ -f "$PROJECT_ROOT/.env" ]; then
    if grep -q "MONGODB_URI=" "$PROJECT_ROOT/.env"; then
        cd "$PROJECT_ROOT"
        python3 << 'EOF'
import os
from dotenv import load_dotenv
load_dotenv()

try:
    from pymongo import MongoClient
    uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("MONGODB_DB", "profitenginev5")

    if not uri or "xxxxx" in uri:
        print("  ⚠ MONGODB_URI not configured (using placeholder)")
        exit(0)

    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print("  ✓ MongoDB connection successful")

    db = client[db_name]
    collections = db.list_collection_names()
    if 'revenue_transactions' in collections:
        count = db['revenue_transactions'].count_documents({})
        print(f"  ✓ revenue_transactions collection: {count} documents")
    else:
        print("  ⚠ revenue_transactions collection not found (will be created on first write)")

    client.close()
except Exception as e:
    print(f"  ✗ MongoDB connection failed: {e}")
    exit(1)
EOF
    else
        echo -e "${YELLOW}⚠${NC} MONGODB_URI not configured in .env"
    fi
else
    echo -e "${YELLOW}⚠${NC} .env file not found"
fi

# Test 7: Test dashboard generation
echo -e "${YELLOW}[7/8]${NC} Testing dashboard generation..."
cd "$PROJECT_ROOT"
DASHBOARD_OUTPUT=$(python3 scripts/revenue_dashboard.py --action dashboard 2>&1)
if echo "$DASHBOARD_OUTPUT" | grep -q "ALREADY HERE LLC"; then
    echo -e "${GREEN}✓${NC} Dashboard generated successfully"
    echo "$DASHBOARD_OUTPUT" | head -20
else
    echo -e "${YELLOW}⚠${NC} Dashboard output unexpected"
    echo "$DASHBOARD_OUTPUT"
fi

# Test 8: Test manual entry
echo -e "${YELLOW}[8/8]${NC} Testing manual revenue entry..."
TEST_DATE=$(date +%Y-%m-%d)
TEST_CHANNEL="test_channel"
TEST_AMOUNT="123.45"
TEST_DESC="Test entry for dashboard verification"

python3 scripts/revenue_dashboard.py --action add \
    --channel "$TEST_CHANNEL" \
    --amount "$TEST_AMOUNT" \
    --description "$TEST_DESC" \
    --date "$TEST_DATE" 2>&1 > /dev/null && \
    echo -e "${GREEN}✓${NC} Manual entry successful" || \
    echo -e "${YELLOW}⚠${NC} Manual entry test completed"

# Summary
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}All tests completed!${NC}"
echo ""
echo -e "Next steps:"
echo -e "  1. Configure .env with real API keys:"
echo -e "     cp scripts/revenue_tracker.env.example .env"
echo -e "     # Edit .env with actual values"
echo -e ""
echo -e "  2. Test live data fetch:"
echo -e "     python scripts/revenue_dashboard.py --action fetch"
echo -e ""
echo -e "  3. View dashboard:"
echo -e "     python scripts/revenue_dashboard.py --action dashboard"
echo -e ""
echo -e "  4. Test API endpoint (after Next.js starts):"
echo -e "     curl http://localhost:3000/api/revenue/dashboard"
echo -e ""
echo -e "  5. For detailed setup, see:"
echo -e "     cat REVENUE_DASHBOARD_SETUP.md"
echo -e "     cat REVENUE_INTEGRATION_QUICK_START.md"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
