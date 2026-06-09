#!/usr/bin/env bash
set -Eeuo pipefail

APP_NAME="${APP_NAME:-profitenginev5}"
APP_DIR="${APP_DIR:-/opt/profitenginev5}"
BRANCH="${BRANCH:-main}"
PORT="${PORT:-3000}"

log() { printf '[oci-recover] %s\n' "$*"; }
fail() { printf '[oci-recover] ERROR: %s\n' "$*" >&2; exit 1; }

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || fail "$1 is not installed on this OCI host"
}

sync_repo() {
  if [ ! -d "$APP_DIR/.git" ]; then
    fail "APP_DIR does not contain a git checkout: $APP_DIR. Set APP_DIR to the existing app path."
  fi
  log "Syncing $APP_DIR to origin/$BRANCH"
  git -C "$APP_DIR" fetch origin "$BRANCH"
  git -C "$APP_DIR" reset --hard "origin/$BRANCH"
}

restart_app() {
  cd "$APP_DIR"
  if [ -f docker-compose.yml ]; then
    require_cmd docker
    log "Restarting docker compose stack"
    docker compose up -d --build
    docker compose ps
    return
  fi
  require_cmd npm
  log "Building npm application"
  npm ci
  npm run build
  log "Starting npm application on localhost:$PORT"
  nohup npm run start -- --hostname 127.0.0.1 --port "$PORT" > "/tmp/${APP_NAME}.log" 2>&1 &
}

verify_local_routes() {
  require_cmd curl
  local healthy=false
  for path in /api/health /api/distillation/status /; do
    if curl -fsS --max-time 15 "http://127.0.0.1:${PORT}${path}" >/dev/null 2>&1; then
      log "OK http://127.0.0.1:${PORT}${path}"
      healthy=true
    else
      log "NOT_READY http://127.0.0.1:${PORT}${path}"
    fi
  done
  [ "$healthy" = "true" ] || fail "No local app route responded on port $PORT"
}

verify_edge_ports() {
  log "Local listening sockets"
  ss -ltnp || true
  log "Firewall status"
  if command -v ufw >/dev/null 2>&1; then ufw status || true; fi
  log "Nginx status"
  if command -v systemctl >/dev/null 2>&1; then systemctl --no-pager status nginx || true; fi
}

main() {
  require_cmd git
  require_cmd ss
  sync_repo
  restart_app
  verify_local_routes
  verify_edge_ports
  log "Recovery check completed. OCI security list or NSG must allow inbound TCP 22, 80, and 443 for public reachability."
}

main "$@"
