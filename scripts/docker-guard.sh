#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# docker-guard.sh — ProfitEngine v5 Docker/Ollama Health Guardian
#
# Monitors disk usage, container health, and Ollama model inventory.
# Prunes resources automatically based on configurable thresholds.
# Output is DATA-DISTILLED: compact key=value pairs — no prose filler.
# Designed to be piped into the docker-guard Python agent for AI analysis.
#
# Install as server cron (runs every 6 h):
#   echo "0 */6 * * * opc /home/opc/profitenginev5/scripts/docker-guard.sh \
#         >> /var/log/docker-guard.log 2>&1" | sudo tee /etc/cron.d/docker-guard
#
# Also triggered by .github/workflows/docker-guard.yml via SSH.
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

REPO_DIR="${REPO_DIR:-/home/opc/profitenginev5}"
TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# Disk thresholds (KB)
THRESHOLD_WARN_KB=5242880    # 5 GB  → prune exec.cachemount layers
THRESHOLD_AGG_KB=3145728     # 3 GB  → prune ALL build cache
THRESHOLD_CRIT_KB=2097152    # 2 GB  → prune ALL unused images + volumes

# Ollama: only these models are kept; others are removed (distillation: prefer small quant)
OLLAMA_KEEP=("llama3.1:8b" "qwen2.5:7b" "phi3.5:3.8b" "llama3.2:3b")

# ── Distilled output helpers ──────────────────────────────────────────────────
# Every output line is a compact record: ts=<iso> key1=val1 key2=val2 ...
emit() {
  local level="${1:-info}"; shift
  echo "ts=${TS} level=${level} $*"
}

# ── 1. Disk snapshot ──────────────────────────────────────────────────────────
AVAIL_KB=$(df / | awk 'NR==2{print $4}')
USED_PCT=$(df / | awk 'NR==2{print $5}' | tr -d '%')
TOTAL_KB=$(df / | awk 'NR==2{print $2}')
AVAIL_GB=$(awk "BEGIN{printf \"%.1f\", ${AVAIL_KB}/1048576}")
USED_GB=$(awk "BEGIN{printf \"%.1f\", (${TOTAL_KB}-${AVAIL_KB})/1048576}")
TOTAL_GB=$(awk "BEGIN{printf \"%.1f\", ${TOTAL_KB}/1048576}")
emit info "event=disk_snapshot avail_gb=${AVAIL_GB} used_gb=${USED_GB} total_gb=${TOTAL_GB} used_pct=${USED_PCT}"

# ── 2. Container health summary ───────────────────────────────────────────────
COMPOSE_FILE="$REPO_DIR/docker-compose.yml"
if [[ -f "$COMPOSE_FILE" ]]; then
  # Parse docker compose ps output — distilled: count + service names only
  RUNNING_SERVICES=""
  UNHEALTHY_SERVICES=""
  EXIT_SERVICES=""
  while IFS= read -r svc_json; do
    [[ -z "$svc_json" ]] && continue
    svc=$(echo "$svc_json"   | python3 -c "import sys,json; d=json.loads(sys.stdin.read()); print(d.get('Service','?'))" 2>/dev/null || echo "?")
    state=$(echo "$svc_json" | python3 -c "import sys,json; d=json.loads(sys.stdin.read()); print(d.get('State','?').lower())" 2>/dev/null || echo "?")
    health=$(echo "$svc_json"| python3 -c "import sys,json; d=json.loads(sys.stdin.read()); print(d.get('Health','').lower())" 2>/dev/null || echo "")
    case "$state" in
      running)  RUNNING_SERVICES="${RUNNING_SERVICES},${svc}" ;;
      exited)   EXIT_SERVICES="${EXIT_SERVICES},${svc}" ;;
    esac
    [[ "$health" == "unhealthy" ]] && UNHEALTHY_SERVICES="${UNHEALTHY_SERVICES},${svc}"
  done < <(docker compose -f "$COMPOSE_FILE" ps --format json 2>/dev/null || true)

  RUNNING_SERVICES="${RUNNING_SERVICES#,}"
  UNHEALTHY_SERVICES="${UNHEALTHY_SERVICES#,}"
  EXIT_SERVICES="${EXIT_SERVICES#,}"
  RUNNING_COUNT=$(echo "$RUNNING_SERVICES" | tr ',' '\n' | grep -c . || echo 0)
  UNHEALTHY_COUNT=$(echo "$UNHEALTHY_SERVICES" | tr ',' '\n' | grep -c . || echo 0)

  emit info "event=container_status running=${RUNNING_COUNT} services=${RUNNING_SERVICES:-none} unhealthy=${UNHEALTHY_SERVICES:-none} exited=${EXIT_SERVICES:-none}"
  [[ "${UNHEALTHY_COUNT:-0}" -gt 0 ]] && \
    emit warn "event=unhealthy_containers count=${UNHEALTHY_COUNT} names=${UNHEALTHY_SERVICES}"
else
  emit warn "event=compose_missing path=${COMPOSE_FILE}"
fi

# ── 3. Prune stopped containers (older than 24 h) ─────────────────────────────
CTPRUNE=$(docker container prune -f --filter "until=24h" 2>&1 | tr '\n' ' ' | cut -c1-120)
emit info "event=container_prune result=$(echo "$CTPRUNE" | tr -s ' ')"

# ── 4. Prune dangling images ──────────────────────────────────────────────────
IMGPRUNE=$(docker image prune -f 2>&1 | tr '\n' ' ' | cut -c1-120)
emit info "event=dangling_image_prune result=$(echo "$IMGPRUNE" | tr -s ' ')"

# ── 5. Prune exec.cachemount build cache (safe — does not affect image layers) ─
docker buildx prune -f --filter type=exec.cachemount 2>/dev/null || true
emit info "event=buildcache_prune type=exec.cachemount"

# ── 6. Threshold-based aggressive pruning ─────────────────────────────────────
if [[ "${AVAIL_KB:-0}" -lt "${THRESHOLD_WARN_KB}" ]]; then
  emit warn "event=disk_warn avail_gb=${AVAIL_GB} action=full_buildcache_prune"
  docker buildx prune -af 2>/dev/null || true
fi

if [[ "${AVAIL_KB:-0}" -lt "${THRESHOLD_AGG_KB}" ]]; then
  emit warn "event=disk_agg avail_gb=${AVAIL_GB} action=all_buildcache_prune"
  docker buildx prune -af 2>/dev/null || true
fi

if [[ "${AVAIL_KB:-0}" -lt "${THRESHOLD_CRIT_KB}" ]]; then
  emit warn "event=disk_critical avail_gb=${AVAIL_GB} action=prune_unused_images_volumes"
  docker image prune -af 2>/dev/null || true
  docker volume prune -f --filter "label!=keep=true" 2>/dev/null || true
fi

# ── 7. Ollama model inventory & distillation enforcement ──────────────────────
# Distillation principle: keep only small quantized models, remove large ones.
if [[ -f "$COMPOSE_FILE" ]] && docker compose -f "$COMPOSE_FILE" ps ollama 2>/dev/null | grep -q "running"; then
  MODEL_LIST=$(docker compose -f "$COMPOSE_FILE" exec -T ollama \
    ollama list 2>/dev/null | tail -n +2 | awk '{print $1, $3, $4}' || echo "")
  MODEL_COUNT=$(echo "$MODEL_LIST" | grep -c . 2>/dev/null || echo 0)

  # Distilled model inventory: name:size pairs only
  MODEL_SUMMARY=$(echo "$MODEL_LIST" | awk '{printf "%s:%s%s,", $1,$2,$3}' | sed 's/,$//')
  emit info "event=ollama_inventory count=${MODEL_COUNT} models=${MODEL_SUMMARY:-none}"

  # Remove models NOT in the keep list (enforces distillation / disk discipline)
  while IFS= read -r model_line; do
    model_name=$(echo "$model_line" | awk '{print $1}')
    [[ -z "$model_name" ]] && continue
    is_kept=false
    for keep_model in "${OLLAMA_KEEP[@]}"; do
      [[ "$model_name" == "$keep_model" ]] && is_kept=true && break
    done
    if [[ "$is_kept" == false ]]; then
      emit warn "event=ollama_remove_unlisted model=${model_name}"
      docker compose -f "$COMPOSE_FILE" exec -T ollama \
        ollama rm "$model_name" 2>/dev/null || true
    fi
  done <<< "$MODEL_LIST"
else
  emit info "event=ollama_status state=offline reason=profile_local-llm_not_active"
fi

# ── 8. Docker system disk usage (distilled: df breakdown) ─────────────────────
DOCKER_DF=$(docker system df --format "{{.Type}}:{{.Size}}:{{.Reclaimable}}" 2>/dev/null \
  | tr '\n' '|' | sed 's/|$//')
emit info "event=docker_df breakdown=${DOCKER_DF:-unavailable}"

# ── 9. Re-check disk after pruning ───────────────────────────────────────────
AVAIL_KB_AFTER=$(df / | awk 'NR==2{print $4}')
AVAIL_GB_AFTER=$(awk "BEGIN{printf \"%.1f\", ${AVAIL_KB_AFTER}/1048576}")
FREED_KB=$(( AVAIL_KB_AFTER - AVAIL_KB ))
FREED_MB=$(awk "BEGIN{printf \"%.0f\", ${FREED_KB}/1024}")
emit info "event=disk_after avail_gb=${AVAIL_GB_AFTER} freed_mb=${FREED_MB}"

# ── 10. Install as cron if not already present ────────────────────────────────
CRON_MARKER="docker-guard.sh"
if ! crontab -l 2>/dev/null | grep -q "$CRON_MARKER"; then
  # Add to user crontab: every 6 hours
  (crontab -l 2>/dev/null || true; echo "0 */6 * * * ${REPO_DIR}/scripts/docker-guard.sh >> /var/log/docker-guard.log 2>&1") \
    | crontab -
  emit info "event=cron_installed schedule=0_*/6_*_*_*"
else
  emit info "event=cron_already_present"
fi

# ── Exit codes ────────────────────────────────────────────────────────────────
if [[ "${AVAIL_KB_AFTER:-0}" -lt "${THRESHOLD_CRIT_KB}" ]]; then
  emit warn "event=disk_still_critical avail_gb=${AVAIL_GB_AFTER} action_required=manual_expansion"
  exit 2
fi

emit info "event=guard_complete status=ok"
