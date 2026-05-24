#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# ProfitEngine v5 — One-command deploy / update script
#
# Usage:
#   ./scripts/deploy.sh              # deploy from current repo checkout
#   ./scripts/deploy.sh --pull       # git-pull latest commits first
#   ./scripts/deploy.sh --fresh      # rebuild images without cache
#
# Requirements (on the target server):
#   docker >= 24, docker compose >= 2.20, git
#
# Environment:
#   Copy .env.example → .env and fill in every required value BEFORE running.
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# ── flags ──────────────────────────────────────────────────────────────────
DO_PULL=false
FRESH_BUILD=false
for arg in "$@"; do
  case $arg in
    --pull)  DO_PULL=true ;;
    --fresh) FRESH_BUILD=true ;;
    *)       echo "Unknown flag: $arg"; exit 1 ;;
  esac
done

# ── helpers ────────────────────────────────────────────────────────────────
log()  { echo "[deploy] $*"; }
warn() { echo "[deploy] WARN: $*" >&2; }
die()  { echo "[deploy] ERROR: $*" >&2; exit 1; }

require_cmd() { command -v "$1" &>/dev/null || die "'$1' not found — install it first."; }

# ── pre-flight checks ──────────────────────────────────────────────────────
require_cmd docker
require_cmd git

log "ProfitEngine v5 deploy starting …"
log "Project root: $PROJECT_ROOT"

[[ -f .env ]] || die ".env not found. Copy .env.example → .env and fill in all values."

# Verify required env vars are set
required_vars=(POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD N8N_BASIC_AUTH_USER N8N_BASIC_AUTH_PASSWORD SITE_DOMAIN)
missing=()
for var in "${required_vars[@]}"; do
  val="$(grep -E "^${var}=" .env | cut -d= -f2-)"
  [[ -n "$val" ]] || missing+=("$var")
done
if [[ ${#missing[@]} -gt 0 ]]; then
  die "Missing required .env values: ${missing[*]}"
fi

# ── git pull ───────────────────────────────────────────────────────────────
if $DO_PULL; then
  log "Pulling latest commits …"
  git pull --ff-only
fi

# ── build flags ────────────────────────────────────────────────────────────
BUILD_ARGS=()
$FRESH_BUILD && BUILD_ARGS+=(--no-cache)

# ── bring up services ──────────────────────────────────────────────────────
log "Building images …"
docker compose build "${BUILD_ARGS[@]}" web runtime

log "Starting all services …"
docker compose up -d --remove-orphans

# ── wait for runtime health ────────────────────────────────────────────────
log "Waiting for runtime to become healthy …"
max_wait=60
elapsed=0
until docker compose exec -T runtime curl -sf http://localhost:8080/health > /dev/null 2>&1; do
  sleep 2
  elapsed=$((elapsed + 2))
  if [[ $elapsed -ge $max_wait ]]; then
    warn "Runtime did not become healthy within ${max_wait}s — check logs:"
    docker compose logs --tail=30 runtime
    exit 1
  fi
done
log "Runtime is healthy."

# ── wait for web health ────────────────────────────────────────────────────
log "Waiting for web (Next.js) to become healthy …"
elapsed=0
until docker compose exec -T web curl -sf http://localhost:3000/api/health > /dev/null 2>&1; do
  sleep 2
  elapsed=$((elapsed + 2))
  if [[ $elapsed -ge $max_wait ]]; then
    warn "Web did not become healthy within ${max_wait}s — check logs:"
    docker compose logs --tail=30 web
    break  # non-fatal; caddy will retry
  fi
done

# ── Ollama model pull (first deploy only) ──────────────────────────────────
MODEL="${GMAOS_LOCAL_MODEL_NAME:-llama3.1:8b}"
if ! docker compose exec -T ollama ollama list 2>/dev/null | grep -q "${MODEL%%:*}"; then
  log "Pulling Ollama model: $MODEL (this may take a few minutes the first time) …"
  docker compose exec -T ollama ollama pull "$MODEL" || warn "Model pull failed — run manually: docker compose exec ollama ollama pull $MODEL"
else
  log "Ollama model $MODEL already present."
fi

# ── summary ────────────────────────────────────────────────────────────────
DOMAIN="$(grep -E "^SITE_DOMAIN=" .env | cut -d= -f2-)"
log ""
log "╔══════════════════════════════════════════════════════════╗"
log "║  ProfitEngine v5 deployed successfully!                  ║"
log "╠══════════════════════════════════════════════════════════╣"
log "║  Site:           https://$DOMAIN"
log "║  Command center: https://app.$DOMAIN"
log "║  Runtime API:    https://api.$DOMAIN"
log "║  Status page:    https://status.$DOMAIN"
log "║  Runtime health: docker compose exec runtime curl http://localhost:8080/health"
log "║  Logs:           docker compose logs -f"
log "╚══════════════════════════════════════════════════════════╝"
