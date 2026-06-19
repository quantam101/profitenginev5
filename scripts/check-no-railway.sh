#!/usr/bin/env bash
# Railway Disabled Policy Enforcement
#
# CI policy: block active Railway deployment/configuration from re-entering
# the production path without failing on historical notes, docs, or this
# enforcement script itself.
#
# Exit codes:
#   0 = no active Railway deployment configuration found
#   1 = active Railway configuration found
#
# Usage:
#   bash scripts/check-no-railway.sh
#   bash scripts/check-no-railway.sh --staged

set -euo pipefail

STAGED=${1:-}

FORBIDDEN_FILES=(
  'railway.json'
  'railway.toml'
  'deploy/railway.json'
  '.github/workflows/railway.yml'
  '.github/workflows/railway.yaml'
)

# Only scan active deployment/runtime surfaces. Do not scan docs, reports,
# markdown roadmaps, or the policy script; those create false CI failures.
ACTIVE_SCAN_PATHS=(
  '.github/workflows'
  'deploy'
  'scripts'
  'backend'
  'app'
  'lib'
  'package.json'
  'package-lock.json'
  'requirements.txt'
  'backend/requirements.txt'
  'Dockerfile'
  'docker-compose.yml'
)

EXCLUDED_SCAN_PATHS=(
  ':!scripts/check-no-railway.sh'
  ':!scripts/verify-no-railway.sh'
  ':!CLAUDE.md'
  ':!docs/**'
  ':!**/*.md'
  ':!**/*.txt'
  ':!runtime/test_execution_output.txt'
  ':!COMPLETE_ROADMAP.md'
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
        echo "BLOCKED: attempting to add forbidden Railway file: $file"
        found=1
      fi
    else
      if [[ -f "$file" ]]; then
        echo "BLOCKED: forbidden Railway file exists: $file"
        found=1
      fi
    fi
  done

  return "$found"
}

check_patterns() {
  local found=0
  local pattern

  for pattern in "${FORBIDDEN_PATTERNS[@]}"; do
    if [[ $STAGED == '--staged' ]]; then
      if git diff --cached -i -- "${EXCLUDED_SCAN_PATHS[@]}" 2>/dev/null \
        | grep -v '^Binary' \
        | grep -qi "$pattern"; then
        echo "BLOCKED: staged active Railway reference matched pattern: $pattern"
        found=1
      fi
    else
      if git grep -i "$pattern" -- "${ACTIVE_SCAN_PATHS[@]}" "${EXCLUDED_SCAN_PATHS[@]}" 2>/dev/null | grep -q .; then
        echo "BLOCKED: active Railway reference matched pattern: $pattern"
        found=1
      fi
    fi
  done

  return "$found"
}

echo "Railway disabled policy check"
echo ""

if check_files && check_patterns; then
  echo "PASS: no active Railway deployment configuration found"
  exit 0
fi

echo ""
echo "Railway deployment is disabled for the production path."
echo "Remove active Railway config or route it outside CI before continuing."
exit 1
