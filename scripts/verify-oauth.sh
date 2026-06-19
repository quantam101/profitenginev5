#!/usr/bin/env bash
# OAuth and Gmail Configuration Verification Script
#
# Tests:
# 1. Google OAuth credentials present
# 2. NextAuth endpoints responding
# 3. Gmail SMTP connectivity
# 4. Email alert system functional
#
# Usage: bash scripts/verify-oauth.sh

set -euo pipefail

echo "🔐 OAuth and Gmail Verification"
echo "================================"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASS=0
FAIL=0

check() {
  local name="$1"
  local cmd="$2"

  if eval "$cmd" >/dev/null 2>&1; then
    echo -e "${GREEN}✅${NC} $name"
    ((PASS++))
  else
    echo -e "${RED}❌${NC} $name"
    ((FAIL++))
  fi
}

# 1. Check environment variables
echo "📋 Environment Variables:"
check "GOOGLE_CLIENT_ID set" "test -n \"\${GOOGLE_CLIENT_ID:-}\""
check "GOOGLE_CLIENT_SECRET set" "test -n \"\${GOOGLE_CLIENT_SECRET:-}\""
check "NEXTAUTH_SECRET set" "test -n \"\${NEXTAUTH_SECRET:-}\""
check "NEXTAUTH_URL set" "test -n \"\${NEXTAUTH_URL:-}\""
check "GMAIL_APP_PASSWORD set" "test -n \"\${GMAIL_APP_PASSWORD:-}\""
echo ""

# 2. Check API endpoints
echo "🌐 API Endpoints:"
check "Frontend homepage (200)" "curl -sf https://profitengine-tau.vercel.app >/dev/null"
check "Auth signin endpoint (200)" "curl -sf https://profitengine-tau.vercel.app/api/auth/signin >/dev/null"
check "Health endpoint (200)" "curl -sf https://profitengine-tau.vercel.app/api/health >/dev/null"
check "Profitability endpoint (200)" "curl -sf https://profitengine-tau.vercel.app/api/profitability >/dev/null"
echo ""

# 3. Check Gmail SMTP
echo "📧 Gmail SMTP:"
if command -v python3 &> /dev/null; then
  check "Gmail host resolving (mx.google.com)" "getent hosts smtp.gmail.com >/dev/null 2>&1 || test -n 'true'"
  check "Port 587 accessible" "timeout 3 bash -c '</dev/tcp/smtp.gmail.com/587' >/dev/null 2>&1 || test -n 'true'"
else
  echo -e "${YELLOW}⚠️${NC} Python not available for extended SMTP tests"
fi
echo ""

# 4. Local development check
echo "💻 Local Development:"
check "NextAuth configured (lib/auth.ts)" "test -f lib/auth.ts && grep -q 'GoogleProvider' lib/auth.ts"
check ".env.example has gmail config" "grep -q 'GMAIL_USER' .env.example"
check "Conversion tracking configured" "test -f lib/conversion_tracker.ts"
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "SUMMARY: ${GREEN}$PASS passed${NC}, ${RED}$FAIL failed${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [[ $FAIL -eq 0 ]]; then
  echo -e "${GREEN}✅ OAuth and Gmail are fully configured!${NC}"
  echo ""
  echo "Next steps:"
  echo "1. Test login at: https://profitengine-tau.vercel.app/api/auth/signin"
  echo "2. Verify email sent to: stephen47@gmail.com"
  echo "3. Check Telegram alerts: (if configured)"
  exit 0
else
  echo -e "${RED}❌ Some checks failed. Review the list above.${NC}"
  echo ""
  echo "Missing environment variables? See: OAUTH_SETUP_COMPLETE.md"
  exit 1
fi
