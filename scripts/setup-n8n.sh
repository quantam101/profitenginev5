#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# ProfitEngine v5 — n8n workflow setup
#
# Imports the daily content-pipeline workflow into n8n and activates it.
# Run this ON THE SERVER after bootstrap-server.sh has completed.
#
# Uses n8n CLI (docker compose exec) to avoid Secure-cookie issues with
# the REST API over plain HTTP.
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

REPO_DIR="${REPO_DIR:-/home/opc/profitenginev5}"
WORKFLOWS_DIR="$REPO_DIR/n8n/workflows"
COMPOSE="docker compose -f $REPO_DIR/docker-compose.yml"

log()  { echo "[n8n-setup] $*"; }
warn() { echo "[n8n-setup] WARN: $*" >&2; }

log "Waiting for n8n to be ready..."

# Get n8n container IP on the compose network
N8N_IP=$(docker inspect profitenginev5-n8n-1 \
  --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' 2>/dev/null | head -1)

if [[ -z "$N8N_IP" ]]; then
  warn "Could not find n8n container IP. Is profitenginev5-n8n-1 running?"
  exit 1
fi

log "n8n IP: $N8N_IP"

for i in $(seq 1 30); do
  if curl -sf "http://$N8N_IP:5678/healthz" > /dev/null 2>&1; then
    log "n8n is reachable."
    break
  fi
  sleep 2
  [[ $i -eq 30 ]] && { log "n8n not reachable after 60s. Is it running?"; exit 1; }
done

# Import each workflow file using n8n CLI (avoids REST auth complexity)
for wf_file in "$WORKFLOWS_DIR"/*.json; do
  wf_name="$(basename "$wf_file" .json)"
  log "Processing workflow: $wf_name ..."

  # Create cleaned copy (strip string tags, add UUID id) in /tmp
  tmp_file="/tmp/${wf_name}.json"
  python3 - "$wf_file" "$tmp_file" << 'PYEOF'
import sys, json, uuid
src, dst = sys.argv[1], sys.argv[2]
d = json.load(open(src))
d.pop("tags", None)
if not d.get("id") or not isinstance(d["id"], str) or len(d["id"]) < 30:
    d["id"] = str(uuid.uuid4())
json.dump(d, open(dst, "w"))
print(f"  Prepared: {dst} (id={d['id']})")
PYEOF

  # Copy into container
  docker cp "$tmp_file" "profitenginev5-n8n-1:/tmp/${wf_name}.json"

  # Import via n8n CLI
  $COMPOSE exec -T n8n n8n import:workflow --input="/tmp/${wf_name}.json"
  log "Imported: $wf_name"
done

# List workflow IDs then activate each
log "Activating workflows..."
$COMPOSE exec -T n8n n8n list:workflow 2>/dev/null | while IFS='|' read -r wf_id wf_name; do
  [[ -z "$wf_id" ]] && continue
  log "  Activating: $wf_name ($wf_id)"
  $COMPOSE exec -T n8n n8n update:workflow --id="$wf_id" --active=true 2>/dev/null || true
done

# Restart n8n so activation takes effect
log "Restarting n8n to apply activation..."
$COMPOSE restart n8n
sleep 5

log ""
log "n8n workflows imported and activated."
log "  n8n UI: http://$N8N_IP:5678"
log "  Owner:  admin@alreadyherellc.com / ProfitEngine2026!"
