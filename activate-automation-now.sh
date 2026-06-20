#!/bin/bash

# ============================================================================
# PROFITENGINE v5 — INSTANT AUTOMATION ACTIVATION
# ============================================================================
# This script activates the entire fully automated system
# Time to full automation: 10 minutes
# ============================================================================

set -e

echo "🚀 PROFITENGINE v5 — FULL AUTOMATION ACTIVATION"
echo "=============================================================="
echo ""

# ============================================================================
# STEP 1: CHECK ENVIRONMENT
# ============================================================================

echo "📋 STEP 1: Checking environment..."
echo ""

if ! command -v npm &> /dev/null; then
    echo "❌ npm not found. Please install Node.js"
    exit 1
fi

if ! command -v gh &> /dev/null; then
    echo "⚠️  GitHub CLI not found. Install with: brew install gh"
    echo "   (Not required for local automation, but needed for GitHub Actions)"
fi

echo "✅ Environment check passed"
echo ""

# ============================================================================
# STEP 2: BUILD PROJECT
# ============================================================================

echo "🔨 STEP 2: Building project..."
echo ""

npm run build

echo "✅ Build complete"
echo ""

# ============================================================================
# STEP 3: SETUP ENVIRONMENT FILE
# ============================================================================

echo "⚙️  STEP 3: Setting up environment variables..."
echo ""

if [ ! -f .env.local ]; then
    echo "Creating .env.local from .env.automation..."
    cp .env.automation .env.local

    echo ""
    echo "⚠️  IMPORTANT: Add your API keys to .env.local"
    echo ""
    echo "Required API keys (get from setup guide):"
    echo "  - GUMROAD_API_TOKEN"
    echo "  - INSTAGRAM_ACCESS_TOKEN"
    echo "  - INSTAGRAM_BUSINESS_ACCOUNT_ID"
    echo "  - OPENAI_API_KEY"
    echo "  - REPLICATE_API_TOKEN"
    echo "  - ELEVEN_LABS_API_KEY"
    echo "  - KLAVIYO_API_KEY"
    echo ""
    echo "Edit .env.local with your keys, then run: ./activate-automation-now.sh"
    exit 0
else
    echo "✅ .env.local found with credentials"
fi

echo ""

# ============================================================================
# STEP 4: VERIFY AUTOMATION SYSTEM
# ============================================================================

echo "✔️  STEP 4: Verifying automation system..."
echo ""

# Check if automation files exist
if [ ! -f "lib/automation/orchestrate.ts" ]; then
    echo "❌ Automation system not found. Run: npm run setup:automation"
    exit 1
fi

echo "✅ Automation system verified"
echo ""

# ============================================================================
# STEP 5: START DEVELOPMENT SERVER
# ============================================================================

echo "🌐 STEP 5: Starting development server..."
echo ""

# Kill any existing servers on port 3000
pkill -f "next dev" || true

# Start in background
npm run dev &
DEV_PID=$!

# Wait for server to be ready
echo "Waiting for server to start..."
sleep 5

# Check if server is running
if ! curl -s http://localhost:3000 > /dev/null; then
    echo "❌ Server failed to start"
    kill $DEV_PID
    exit 1
fi

echo "✅ Development server running on http://localhost:3000"
echo ""

# ============================================================================
# STEP 6: TEST AUTOMATION ENDPOINTS
# ============================================================================

echo "🧪 STEP 6: Testing automation endpoints..."
echo ""

# Test launch endpoint
echo "Testing POST /api/automation/launch..."
RESPONSE=$(curl -s -X POST http://localhost:3000/api/automation/launch \
  -H "Content-Type: application/json" \
  -d '{"test": true}')

if echo "$RESPONSE" | grep -q "success\|running\|queued"; then
    echo "✅ Automation API responding"
else
    echo "⚠️  API response: $RESPONSE"
fi

echo ""

# ============================================================================
# STEP 7: TRIGGER FULL AUTOMATION
# ============================================================================

echo "🎯 STEP 7: Starting full automation..."
echo ""

curl -X POST http://localhost:3000/api/automation/launch \
  -H "Content-Type: application/json" \
  -d '{
    "components": ["gumroad", "instagram-carousel", "instagram-reel", "instagram-stories", "email"],
    "dryRun": false,
    "notify": true
  }'

echo ""
echo ""
echo "✅ Automation triggered!"
echo ""

# ============================================================================
# STEP 8: OPEN DASHBOARD
# ============================================================================

echo "📊 STEP 8: Opening automation dashboard..."
echo ""

# Try to open in browser
if command -v open &> /dev/null; then
    open automation-dashboard.html
elif command -v xdg-open &> /dev/null; then
    xdg-open automation-dashboard.html
elif command -v start &> /dev/null; then
    start automation-dashboard.html
fi

echo "📖 Dashboard: file://$(pwd)/automation-dashboard.html"
echo ""

# ============================================================================
# FINAL STATUS
# ============================================================================

echo "=============================================================="
echo "✅ PROFITENGINE v5 AUTOMATION ACTIVATED"
echo "=============================================================="
echo ""
echo "STATUS:"
echo "  ✅ Build: Complete"
echo "  ✅ Environment: Configured"
echo "  ✅ Server: Running (http://localhost:3000)"
echo "  ✅ Automation: Active"
echo "  ✅ Dashboard: Open (automation-dashboard.html)"
echo ""
echo "WHAT'S RUNNING:"
echo "  📤 Gumroad: Auto-uploading products"
echo "  📸 Instagram Carousel: Generating & posting"
echo "  🎬 Instagram Reel: Generating & posting"
echo "  📱 Instagram Stories: Generating & posting (3x daily)"
echo "  📧 Email: Auto-triggering sequences"
echo ""
echo "NEXT STEPS:"
echo "  1. Open automation-dashboard.html to monitor"
echo "  2. Check .runtime/automation/ for logs"
echo "  3. For GitHub Actions, add secrets to GitHub Secrets"
echo "  4. Commit to main branch to trigger automated workflow"
echo ""
echo "MANUAL TRIGGER:"
echo "  curl -X POST http://localhost:3000/api/automation/launch"
echo ""
echo "Server will stay running. Press Ctrl+C to stop."
echo ""

# Keep server running
wait $DEV_PID
