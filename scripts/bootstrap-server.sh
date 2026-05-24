#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# ProfitEngine v5 — Server Bootstrap
#
# Idempotent: safe to run multiple times.
#
# Usage (two options):
#
#   Option A — pass secrets as env vars inline:
#     GROQ_API_KEY=gsk_xxx GEMINI_API_KEY=AIza_xxx \
#     GITHUB_CONTENT_TOKEN=ghp_xxx GMAIL_APP_PASSWORD=xxx \
#     bash scripts/bootstrap-server.sh
#
#   Option B — source a local secrets file first:
#     source /home/ubuntu/.profitengine-secrets   # fill in and chmod 600
#     bash scripts/bootstrap-server.sh
#
# The script will refuse to run if required secrets are missing.
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

REPO_DIR="${REPO_DIR:-/home/ubuntu/profitenginev5}"
ENV_FILE="$REPO_DIR/.env"

log()  { echo -e "\033[32m[bootstrap]\033[0m $*"; }
warn() { echo -e "\033[33m[bootstrap] WARN:\033[0m $*" >&2; }
die()  { echo -e "\033[31m[bootstrap] ERROR:\033[0m $*" >&2; exit 1; }

# Accept CONTENT_REPO_TOKEN as alias for GITHUB_CONTENT_TOKEN (GitHub blocks GITHUB_ prefix in secrets)
GITHUB_CONTENT_TOKEN="${GITHUB_CONTENT_TOKEN:-${CONTENT_REPO_TOKEN:-}}"

# ── validate required secrets ───────────────────────────────────────────────
required_secrets=(GROQ_API_KEY GEMINI_API_KEY GITHUB_CONTENT_TOKEN GMAIL_APP_PASSWORD)
missing_secrets=()
for s in "${required_secrets[@]}"; do
  [[ -z "${!s:-}" ]] && missing_secrets+=("$s")
done
if [[ ${#missing_secrets[@]} -gt 0 ]]; then
  die "Missing secrets: ${missing_secrets[*]}

Pass them as env vars or source /home/ubuntu/.profitengine-secrets first.
Example:
  GROQ_API_KEY=gsk_xxx GEMINI_API_KEY=AIza_xxx \\
  GITHUB_CONTENT_TOKEN=ghp_xxx GMAIL_APP_PASSWORD=xxx \\
  bash scripts/bootstrap-server.sh"
fi

# ── ensure repo dir exists ──────────────────────────────────────────────────
if [[ ! -d "$REPO_DIR" ]]; then
  log "Cloning repository into $REPO_DIR …"
  git clone https://github.com/quantam101/profitenginev5.git "$REPO_DIR"
fi
cd "$REPO_DIR"

# ── seed .env from example if not present ──────────────────────────────────
if [[ ! -f "$ENV_FILE" ]]; then
  cp .env.example "$ENV_FILE"
  log "Created $ENV_FILE from .env.example"
fi

# ── helper: upsert a key=value line in .env ────────────────────────────────
upsert_env() {
  local key="$1" val="$2"
  if grep -qE "^${key}=" "$ENV_FILE"; then
    sed -i "s|^${key}=.*|${key}=${val}|" "$ENV_FILE"
  else
    echo "${key}=${val}" >> "$ENV_FILE"
  fi
}

# ── write all API keys and configuration ───────────────────────────────────
log "Writing API keys to .env …"

upsert_env GROQ_API_KEY           "${GROQ_API_KEY}"
upsert_env GEMINI_API_KEY         "${GEMINI_API_KEY}"
upsert_env GITHUB_CONTENT_TOKEN   "${GITHUB_CONTENT_TOKEN}"
upsert_env GITHUB_CONTENT_OWNER   "${GITHUB_CONTENT_OWNER:-quantam101}"
upsert_env GITHUB_CONTENT_REPO    "${GITHUB_CONTENT_REPO:-content}"
upsert_env GITHUB_CONTENT_BRANCH  "${GITHUB_CONTENT_BRANCH:-main}"
upsert_env GITHUB_CONTENT_DIR     "${GITHUB_CONTENT_DIR:-posts}"
upsert_env GMAIL_USER             "${GMAIL_USER:-alreadyherellc@gmail.com}"
upsert_env GMAIL_APP_PASSWORD     "${GMAIL_APP_PASSWORD}"
upsert_env ALERT_EMAIL            "${ALERT_EMAIL:-stephen47@gmail.com}"
upsert_env N8N_BASIC_AUTH_ACTIVE  "true"
upsert_env N8N_BASIC_AUTH_USER    "${N8N_BASIC_AUTH_USER:-admin}"
upsert_env N8N_BASIC_AUTH_PASSWORD "${N8N_BASIC_AUTH_PASSWORD:-ProfitEngine2026}"

# Required non-secret config
upsert_env POSTGRES_DB       "profitengine"
upsert_env POSTGRES_USER     "profitengine"
PG_PASS="$(grep -E "^POSTGRES_PASSWORD=" "$ENV_FILE" | cut -d= -f2-)"
if [[ -z "$PG_PASS" ]]; then
  upsert_env POSTGRES_PASSWORD "$(openssl rand -hex 24)"
  log "Generated new Postgres password."
fi

upsert_env GMAOS_LOCAL_MODEL_ENABLED  "true"
upsert_env GMAOS_LOCAL_MODEL_ENDPOINT "http://ollama:11434"
upsert_env GMAOS_LOCAL_MODEL_NAME     "llama3.1:8b"
upsert_env GMAOS_LOCAL_MODEL_TIMEOUT  "120"
upsert_env GMAOS_GROQ_MODEL           "llama-3.1-70b-versatile"
upsert_env GMAOS_GROQ_TIMEOUT         "60"
upsert_env GMAOS_GEMINI_MODEL         "gemini-1.5-flash"
upsert_env GMAOS_GEMINI_TIMEOUT       "60"
upsert_env SITE_DOMAIN                "profitengine.alreadyherellc.com"
upsert_env ACME_EMAIL                 "ops@alreadyherellc.com"

log ".env updated."

# ── add deploy public key to authorized_keys ───────────────────────────────
DEPLOY_PUB_KEY="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIF5IOnsqRDtbUYu5WQfLaAjAQmc+zKrlK6TDafDgO0Ij profitengine-deploy@github-actions"
AUTH_KEYS="$HOME/.ssh/authorized_keys"
mkdir -p "$HOME/.ssh" && chmod 700 "$HOME/.ssh"
if ! grep -qF "profitengine-deploy@github-actions" "$AUTH_KEYS" 2>/dev/null; then
  echo "$DEPLOY_PUB_KEY" >> "$AUTH_KEYS"
  chmod 600 "$AUTH_KEYS"
  log "Added GitHub Actions deploy key to $AUTH_KEYS"
else
  log "Deploy key already present in authorized_keys — skipping."
fi

# ── pull latest code ───────────────────────────────────────────────────────
log "Pulling latest code …"
git pull --ff-only || {
  warn "Fast-forward pull failed; fetching + resetting …"
  git fetch origin main
  git reset --hard origin/main
}

# ── rebuild and restart containers ────────────────────────────────────────
log "Rebuilding Docker images …"
docker compose build web runtime

log "Restarting services …"
docker compose up -d --remove-orphans

# ── wait for services ─────────────────────────────────────────────────────
log "Waiting for runtime API …"
for i in $(seq 1 30); do
  docker compose exec -T runtime curl -sf http://localhost:8080/health > /dev/null 2>&1 && \
    { log "Runtime healthy."; break; } || sleep 2
done

log "Waiting for web (Next.js) …"
for i in $(seq 1 30); do
  docker compose exec -T web curl -sf http://localhost:3000/api/health > /dev/null 2>&1 && \
    { log "Web healthy."; break; } || sleep 2
done

# ── pull Ollama model if missing ───────────────────────────────────────────
MODEL="${GMAOS_LOCAL_MODEL_NAME:-llama3.1:8b}"
if ! docker compose exec -T ollama ollama list 2>/dev/null | grep -q "${MODEL%%:*}"; then
  log "Pulling Ollama model $MODEL in background …"
  docker compose exec -d ollama ollama pull "$MODEL" || warn "Model pull failed — run manually later."
fi

log ""
log "╔═══════════════════════════════════════════════════════════╗"
log "║  ProfitEngine v5 bootstrap COMPLETE                       ║"
log "╠═══════════════════════════════════════════════════════════╣"
log "║  Dashboard:      http://$(hostname -I | awk '{print $1}'):3000             ║"
log "║  Runtime API:    http://$(hostname -I | awk '{print $1}'):8080/health      ║"
log "║  Content site:   https://quantam101.github.io/content/    ║"
log "║                                                           ║"
log "║  Next steps:                                              ║"
log "║  1. Add DEVTO_API_KEY to .env (get free at dev.to)        ║"
log "║  2. Add SERVER_SSH_KEY to GitHub repo secrets for CI/CD   ║"
log "║  3. Set up n8n cron: bash scripts/setup-n8n.sh            ║"
log "╚═══════════════════════════════════════════════════════════╝"
