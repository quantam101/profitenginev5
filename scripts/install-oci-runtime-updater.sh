#!/usr/bin/env bash
# Installs the optimized ProfitEngine OCI runtime updater on the OCI host.
# Run from the checked-out repository on the OCI instance.

set -Eeuo pipefail

APP_DIR="${APP_DIR:-/home/opc/profitenginev5}"
SERVICE_SRC="$APP_DIR/ops/systemd/profitengine-runtime-update.service"
TIMER_SRC="$APP_DIR/ops/systemd/profitengine-runtime-update.timer"
SERVICE_DST="/etc/systemd/system/profitengine-runtime-update.service"
TIMER_DST="/etc/systemd/system/profitengine-runtime-update.timer"
SCRIPT="$APP_DIR/scripts/oci-runtime-update.sh"

log() {
  printf 'ts=%s level=%s event=%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$1" "$2" "${3:-}"
}

fail() {
  log error "$1" "${2:-}"
  exit "${3:-1}"
}

[ -d "$APP_DIR" ] || fail app_dir_missing "path=$APP_DIR"
[ -f "$SCRIPT" ] || fail updater_missing "path=$SCRIPT"
[ -f "$SERVICE_SRC" ] || fail service_template_missing "path=$SERVICE_SRC"
[ -f "$TIMER_SRC" ] || fail timer_template_missing "path=$TIMER_SRC"
command -v systemctl >/dev/null 2>&1 || fail systemctl_missing
command -v docker >/dev/null 2>&1 || fail docker_missing

chmod +x "$SCRIPT"
sudo install -m 0644 "$SERVICE_SRC" "$SERVICE_DST"
sudo install -m 0644 "$TIMER_SRC" "$TIMER_DST"
sudo systemctl daemon-reload
sudo systemctl enable --now profitengine-runtime-update.timer

log info installed "service=$SERVICE_DST timer=$TIMER_DST"
systemctl list-timers --all profitengine-runtime-update.timer --no-pager || true
