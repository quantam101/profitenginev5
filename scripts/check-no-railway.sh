#!/usr/bin/env bash
# Railway Disabled Policy Enforcement
#
# This script runs in CI/CD and in git pre-commit hooks.
# It blocks any attempt to re-add Railway configuration.
#
# Exit codes:
#   0 = No Railway files found (pass)
#   1 = Railway files found (fail)
#
# Usage:
#   bash scripts/check-no-railway.sh          # check working tree
#   bash scripts/check-no-railway.sh --staged # check git staging area

set -euo pipefail

STAGED=${1:-}
FORBIDDEN_FILES=(
  'railway.json'
  'railway.toml'
  'deploy/railway.json'
  'docs/RAILWAY_SETUP_GUIDE.md'
  'docs/ARCHITECTURE_HA_FAILOVER.md'
)

FORBIDDEN_PATTERNS=(
  'railway\.app'
  'RAILWAY_API_KEY'
  'RAILWAY_TOKEN'
  'railwayapp'
)

check_files() {
  local found=0
  for file in "${FORBIDDEN_FILES[@]}"; do
    if [[ $STAGED == '--staged' ]]; then
      if git diff --cached --name-only | grep -q "^$file$"; then
        echo "❌ BLOCKED: Attempting to add forbidden file: $file"
        found=1
      fi
    else
      if [[ -f "$file" ]]; then
        echo "❌ BLOCKED: Forbidden file exists: $file"
        found=1
      fi
    fi
  done
  return $found
}

check_patterns() {
  local found=0

  for pattern in "${FORBIDDEN_PATTERNS[@]}"; do
    if [[ $STAGED == '--staged' ]]; then
      # Check staged changes, excluding metadata files
      if git diff --cached -i -- \
        ':!scripts/check-no-railway.sh' \
        ':!scripts/verify-no-railway.sh' \
        ':!CLAUDE.md' 2>/dev/null | grep -v "^Binary" | grep -qi "$pattern"; then
        echo "❌ BLOCKED: Found forbidden pattern: $pattern"
        found=1
      fi
    else
      # Check working tree with git grep, excluding metadata files
      if git grep -i "$pattern" \
        -- \
        ':!scripts/check-no-railway.sh' \
        ':!scripts/verify-no-railway.sh' \
        ':!CLAUDE.md' 2>/dev/null | grep -q .; then
        echo "❌ BLOCKED: Found forbidden pattern: $pattern"
        found=1
      fi
    fi
  done
  return $found
}

echo "🚫 Railway Disabled Policy Check"
echo ""

if check_files && check_patterns; then
  echo "✅ PASS: No Railway references found"
  exit 0
else
  echo ""
  echo "Railway deployment is permanently disabled."
  echo "See CLAUDE.md → RAILWAY PERMANENTLY DISABLED for details."
  exit 1
fi
