#!/usr/bin/env bash
set -euo pipefail
DEST="${1:-./backups/profitengine-backup-$(date +%Y%m%d-%H%M%S).tgz}"
mkdir -p "$(dirname "$DEST")"
paths=(
  agents
  app
  approvals
  caddy
  connectors
  docs
  public
  runtime
  scripts
  security
  tests
  .env.example
  docker-compose.yml
  Dockerfile.runtime
  Dockerfile.web
  eaos.config.yaml
  next.config.ts
  package-lock.json
  package.json
  README.md
  tsconfig.json
  vercel.json
)
existing=()
for path in "${paths[@]}"; do
  if [[ -e "$path" ]]; then
    existing+=("$path")
  fi
done
tar -czf "$DEST" "${existing[@]}"
printf 'backup created: %s\n' "$DEST"
