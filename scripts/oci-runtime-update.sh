#!/usr/bin/env bash
# Optimized OCI runtime updater for ProfitEngine v5.
# Runs on the OCI host only. It pulls the prebuilt GHCR runtime image,
# swaps the docker compose runtime service without on-box builds, verifies
# health, rolls back on failure, and prunes safely.

set -Eeuo pipefail

APP_DIR="${APP_DIR:-/home/opc/profitenginev5}"
IMAGE="${IMAGE:-ghcr.io/quantam101/profitenginev5-runtime:latest}"
LOCAL_IMAGE="${LOCAL_IMAGE:-profitenginev5-runtime:latest}"
SERVICE="${SERVICE:-runtime}"
HEALTH_URL="${HEALTH_URL:-https://api.profitengine.alreadyherellc.com/health}"
LOCK_FILE="${LOCK_FILE:-/tmp/profitengine-runtime-update.lock}"
STATE_DIR="${STATE_DIR:-/var/lib/profitengine-runtime-update}"
MAX_HEALTH_TRIES="${MAX_HEALTH_TRIES:-24}"
HEALTH_SLEEP_SEC="${HEALTH_SLEEP_SEC:-5}"
PRUNE_AFTER_SUCCESS="${PRUNE_AFTER_SUCCESS:-true}"

log() {
  printf 'ts=%s level=%s event=%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$1" "$2" "${3:-}"
}

fail() {
  log error "$1" "${2:-}"
  exit "${3:-1}"
}

need() {
  command -v "$1" >/dev/null 2>&1 || fail missing_dependency "name=$1"
}

health_ok() {
  curl -fsS --connect-timeout 5 --max-time 15 "$HEALTH_URL" \
    | python3 -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if d.get('ok') is True or d.get('status') == 'ok' else 1)" \
    >/dev/null 2>&1
}

wait_for_health() {
  local i
  for i in $(seq 1 "$MAX_HEALTH_TRIES"); do
    if health_ok; then
      log info health_ok "attempt=$i url=$HEALTH_URL"
      return 0
    fi
    sleep "$HEALTH_SLEEP_SEC"
  done
  return 1
}

rollback() {
  local previous_id="${1:-}"
  if [ -z "$previous_id" ]; then
    log warn rollback_skipped "reason=no_previous_image"
    return 1
  fi

  log warn rollback_start "previous_image_id=$previous_id service=$SERVICE"
  docker tag "$previous_id" "$LOCAL_IMAGE"
  docker compose -f "$APP_DIR/docker-compose.yml" up -d --no-deps --no-build "$SERVICE"
  if wait_for_health; then
    log warn rollback_complete "status=healthy"
    return 0
  fi
  log error rollback_failed "status=unhealthy"
  return 1
}

main() {
  need docker
  need curl
  need python3
  need flock

  [ -d "$APP_DIR" ] || fail app_dir_missing "path=$APP_DIR"
  [ -f "$APP_DIR/docker-compose.yml" ] || fail compose_missing "path=$APP_DIR/docker-compose.yml"

  mkdir -p "$STATE_DIR"

  exec 9>"$LOCK_FILE"
  if ! flock -n 9; then
    log warn already_running "lock=$LOCK_FILE"
    exit 0
  fi

  log info update_start "app_dir=$APP_DIR image=$IMAGE service=$SERVICE"

  local previous_id=""
  previous_id="$(docker image inspect "$LOCAL_IMAGE" --format '{{.Id}}' 2>/dev/null || true)"
  if [ -n "$previous_id" ]; then
    echo "$previous_id" > "$STATE_DIR/previous-image-id"
    log info previous_image "id=$previous_id"
  else
    log warn previous_image_missing "local_image=$LOCAL_IMAGE"
  fi

  local before_digest=""
  before_digest="$(docker image inspect "$IMAGE" --format '{{index .RepoDigests 0}}' 2>/dev/null || true)"

  log info pull_start "image=$IMAGE"
  docker pull "$IMAGE"
  docker tag "$IMAGE" "$LOCAL_IMAGE"

  local after_digest=""
  after_digest="$(docker image inspect "$IMAGE" --format '{{index .RepoDigests 0}}' 2>/dev/null || true)"
  echo "$after_digest" > "$STATE_DIR/current-repo-digest"
  log info pull_complete "before=${before_digest:-none} after=${after_digest:-unknown}"

  log info compose_swap_start "service=$SERVICE local_image=$LOCAL_IMAGE"
  docker compose -f "$APP_DIR/docker-compose.yml" up -d --no-deps --no-build "$SERVICE"

  if wait_for_health; then
    log info update_complete "status=healthy digest=${after_digest:-unknown}"
    if [ "$PRUNE_AFTER_SUCCESS" = "true" ]; then
      docker image prune -f >/dev/null 2>&1 || true
      docker builder prune -f >/dev/null 2>&1 || true
      log info prune_complete "mode=safe"
    fi
    exit 0
  fi

  log error health_failed "action=rollback"
  rollback "$previous_id" || true
  fail update_failed "status=unhealthy_after_swap" 2
}

main "$@"
