#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# ProfitEngine v5 — n8n workflow setup
#
# Imports the daily content-pipeline workflow into n8n and activates it.
# Run this ON THE SERVER after bootstrap-server.sh has completed.
#
# Requirements: curl, jq (or python3 for JSON parsing)
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

N8N_URL="${N8N_URL:-http://localhost:5678}"
N8N_USER="${N8N_BASIC_AUTH_USER:-admin}"
N8N_PASS="${N8N_BASIC_AUTH_PASSWORD:-ProfitEngine2026}"
WORKFLOWS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../n8n/workflows" && pwd)"

log()  { echo "[n8n-setup] $*"; }
warn() { echo "[n8n-setup] WARN: $*" >&2; }

log "Connecting to n8n at $N8N_URL …"

# Wait for n8n to be ready
for i in $(seq 1 30); do
  if curl -sf "$N8N_URL/healthz" > /dev/null 2>&1; then
    log "n8n is reachable."
    break
  fi
  sleep 2
  [[ $i -eq 30 ]] && { log "n8n not reachable after 60s. Is it running?"; exit 1; }
done

# Helper: call n8n API
n8n_api() {
  local method="$1" path="$2"
  shift 2
  curl -sf -X "$method" \
    -u "${N8N_USER}:${N8N_PASS}" \
    -H "Content-Type: application/json" \
    "${N8N_URL}${path}" \
    "$@"
}

# Import each workflow file
for wf_file in "$WORKFLOWS_DIR"/*.json; do
  wf_name="$(basename "$wf_file" .json)"
  log "Importing workflow: $wf_name …"

  # Check if workflow already exists
  existing_id=$(n8n_api GET "/api/v1/workflows" | \
    python3 -c "import sys,json; wfs=json.load(sys.stdin).get('data',[]); print(next((w['id'] for w in wfs if w['name']==open('$wf_file').read().split('\"name\": \"')[1].split('\"')[0]),'' ))" 2>/dev/null || echo "")

  if [[ -n "$existing_id" ]]; then
    log "Workflow already exists (id=$existing_id) — updating …"
    n8n_api PATCH "/api/v1/workflows/$existing_id" --data "@$wf_file" > /dev/null
  else
    log "Creating new workflow …"
    response=$(n8n_api POST "/api/v1/workflows" --data "@$wf_file")
    existing_id=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))" 2>/dev/null || echo "")
  fi

  # Activate the workflow
  if [[ -n "$existing_id" ]]; then
    n8n_api PATCH "/api/v1/workflows/$existing_id" \
      --data '{"active":true}' > /dev/null
    log "Workflow activated (id=$existing_id)."
  else
    warn "Could not get workflow ID — activate manually in n8n UI."
  fi
done

log ""
log "n8n workflows imported and activated."
log "Access n8n UI: http://$(hostname -I | awk '{print $1}'):5678"
log "Credentials: $N8N_USER / $N8N_PASS"
