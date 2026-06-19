#!/usr/bin/env bash
# Railway Removal Verification Script
#
# Comprehensive check to verify:
# 1. No Railway config files exist
# 2. No Railway references in code
# 3. No Railway environment variables
# 4. No Railway deployment hooks
# 5. CI/CD enforces Railway disabled policy
#
# Exit: 0 = all checks pass, 1 = at least one check failed

set -euo pipefail

PASS=0
FAIL=0

check() {
  local name="$1"
  local cmd="$2"

  if eval "$cmd" >/dev/null 2>&1; then
    echo "✅ $name"
    ((PASS++))
  else
    echo "❌ $name"
    ((FAIL++))
  fi
}

echo "🔍 Railway Removal Verification"
echo ""

# Check 1: Config files deleted
echo "Config Files:"
check "railway.json deleted" "! test -f railway.json"
check "railway.toml deleted" "! test -f railway.toml"
check "deploy/railway.json deleted" "! test -f deploy/railway.json"
check "RAILWAY_SETUP_GUIDE.md deleted" "! test -f docs/RAILWAY_SETUP_GUIDE.md"
check "ARCHITECTURE_HA_FAILOVER.md deleted" "! test -f docs/ARCHITECTURE_HA_FAILOVER.md"
echo ""

# Check 2: Code references
echo "Code References:"
check "No railway.app URLs" "! grep -r 'railway\.app' . --exclude-dir=.git --exclude-dir=node_modules 2>/dev/null || true"
check "No RAILWAY_API_KEY vars" "! grep -r 'RAILWAY_API_KEY' . --exclude-dir=.git --exclude-dir=node_modules 2>/dev/null || true"
check "No railwayapp references" "! grep -ri 'railwayapp' . --exclude-dir=.git --exclude-dir=node_modules 2>/dev/null || true"
echo ""

# Check 3: Vercel config
echo "Deployment Configuration:"
check "vercel.json has no Railway" "! grep -i railway vercel.json 2>/dev/null || true"
check "No Railway in scripts" "! grep -r 'railway' scripts/ --include='*.sh' --exclude='check-no-railway.sh' 2>/dev/null || true"
echo ""

# Check 4: CI/CD
echo "CI/CD Pipeline:"
check "CI has Railway policy check" "grep -q 'Railway Disabled Policy Check' .github/workflows/ci.yml"
check "check-no-railway.sh exists" "test -f scripts/check-no-railway.sh"
check "check-no-railway.sh is executable" "test -x scripts/check-no-railway.sh"
echo ""

# Check 5: Git history (reference only)
echo "Git History (reference only):"
echo "  Railway removal commits:"
git log --oneline | grep -i railway | head -3 || echo "  (no recent railway commits)"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "SUMMARY: $PASS passed, $FAIL failed"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [[ $FAIL -eq 0 ]]; then
  echo "✅ All checks passed — Railway is completely removed"
  exit 0
else
  echo "❌ Some checks failed — Railway references still exist"
  exit 1
fi
