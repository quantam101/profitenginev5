#!/usr/bin/env bash
# Vercel ignored-build command.
# Exit 0 = skip/ignore deployment.
# Exit 1 = continue Vercel build.

set -Eeuo pipefail

if ! git rev-parse --verify HEAD^ >/dev/null 2>&1; then
  echo "No previous commit available; continue Vercel build."
  exit 1
fi

changed_files="$(git diff --name-only HEAD^ HEAD || true)"

if [ -z "$changed_files" ]; then
  echo "No changed files detected; skip Vercel build."
  exit 0
fi

# Only these paths affect the public Next.js/Vercel app surface.
# Ops-only, docs-only, and runtime-worker-only changes should not
# consume Vercel deployment quota.
#
# Deployment-control files are included intentionally. Changes that remove or
# harden competing platform config, especially Railway config, must be allowed
# to produce a clean Vercel deployment instead of being silently skipped.
build_regex='^(app|pages|components|lib|public|styles|src)/|^(package.json|package-lock.json|next\.config\.(js|mjs|ts)|tsconfig\.json|postcss\.config\.(js|mjs|cjs)|tailwind\.config\.(js|mjs|ts)|middleware\.(js|ts)|instrumentation\.(js|ts)|vercel\.json|Dockerfile|railway\.toml|nixpacks\.toml|Procfile|scripts/vercel-ignore\.sh)$|^\.github/workflows/'

while IFS= read -r file; do
  [ -z "$file" ] && continue
  if [[ "$file" =~ $build_regex ]]; then
    echo "Vercel build required because web-surface or deployment-control file changed: $file"
    exit 1
  fi
done <<< "$changed_files"

echo "Skipping Vercel build; changed files do not affect public web app:"
echo "$changed_files"
exit 0
