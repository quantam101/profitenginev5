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

# Default repo dir: opc on Oracle Linux (OCI default), ubuntu on Ubuntu
_DEFAULT_HOME="$(getent passwd opc 2>/dev/null | cut -d: -f6 || echo /home/ubuntu)"
REPO_DIR="${REPO_DIR:-${_DEFAULT_HOME}/profitenginev5}"
ENV_FILE="$REPO_DIR/.env"

log()  { echo -e "\033[32m[bootstrap]\033[0m $*"; }
warn() { echo -e "\033[33m[bootstrap] WARN:\033[0m $*" >&2; }
die()  { echo -e "\033[31m[bootstrap] ERROR:\033[0m $*" >&2; exit 1; }

# ── install Docker if missing ───────────────────────────────────────────────
if ! command -v docker &>/dev/null; then
  log "Docker not found — installing …"
  if command -v dnf &>/dev/null; then
    # Oracle Linux / RHEL / CentOS
    sudo dnf config-manager --add-repo \
      https://download.docker.com/linux/centos/docker-ce.repo 2>/dev/null || true
    sudo dnf install -y docker-ce docker-ce-cli containerd.io \
      docker-buildx-plugin docker-compose-plugin
    sudo systemctl enable --now docker
    sudo usermod -aG docker "$USER" && warn "Re-login or run: newgrp docker"
  elif command -v apt-get &>/dev/null; then
    # Ubuntu / Debian
    sudo apt-get update -qq
    curl -fsSL https://get.docker.com | sudo bash
    sudo usermod -aG docker "$USER"
    sudo systemctl enable --now docker
  else
    die "Cannot install Docker — unsupported OS (no dnf or apt-get)"
  fi
  # Re-exec with newgrp so docker group takes effect immediately
  exec sg docker "$0" "$@" 2>/dev/null || true
fi

# Ensure docker compose (plugin) is available
if ! docker compose version &>/dev/null; then
  die "docker compose plugin not found — check your Docker installation"
fi

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

Pass them as env vars or source ~/.profitengine-secrets first.
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
upsert_env BACKEND_API_URL   "${BACKEND_API_URL:-http://backend:8001}"
PG_PASS="$(grep -E "^POSTGRES_PASSWORD=" "$ENV_FILE" | cut -d= -f2-)"
if [[ -z "$PG_PASS" ]]; then
  upsert_env POSTGRES_PASSWORD "$(openssl rand -hex 24)"
  log "Generated new Postgres password."
fi

upsert_env GMAOS_LOCAL_MODEL_ENABLED  "true"
upsert_env GMAOS_LOCAL_MODEL_ENDPOINT "http://ollama:11434"
upsert_env GMAOS_LOCAL_MODEL_NAME     "llama3.1:8b"
upsert_env GMAOS_LOCAL_MODEL_TIMEOUT  "120"
upsert_env GMAOS_GROQ_MODEL           "llama-3.3-70b-versatile"
upsert_env GMAOS_GROQ_TIMEOUT         "60"
upsert_env GMAOS_GEMINI_MODEL         "gemini-1.5-flash"
upsert_env GMAOS_GEMINI_TIMEOUT       "60"
upsert_env SITE_DOMAIN                "${SITE_DOMAIN:-profitengine.alreadyherellc.com}"
upsert_env ACME_EMAIL                 "${ACME_EMAIL:-ops@alreadyherellc.com}"

# ── backend (FastAPI / MongoDB) optional keys ──────────────────────────────
# Set these GitHub secrets to activate the v5 backend service:
#   MONGO_URL, STRIPE_API_KEY, STRIPE_WEBHOOK_SECRET,
#   OPENAI_API_KEY, OPENROUTER_API_KEY, DEEPSEEK_API_KEY, RESEND_API_KEY
[[ -n "${MONGO_URL:-}"              ]] && upsert_env MONGO_URL              "${MONGO_URL}"
[[ -n "${STRIPE_API_KEY:-}"         ]] && upsert_env STRIPE_API_KEY         "${STRIPE_API_KEY}"
[[ -n "${STRIPE_WEBHOOK_SECRET:-}"  ]] && upsert_env STRIPE_WEBHOOK_SECRET  "${STRIPE_WEBHOOK_SECRET}"
[[ -n "${OPENAI_API_KEY:-}"         ]] && upsert_env OPENAI_API_KEY         "${OPENAI_API_KEY}"
[[ -n "${OPENROUTER_API_KEY:-}"     ]] && upsert_env OPENROUTER_API_KEY     "${OPENROUTER_API_KEY}"
[[ -n "${DEEPSEEK_API_KEY:-}"       ]] && upsert_env DEEPSEEK_API_KEY       "${DEEPSEEK_API_KEY}"
[[ -n "${RESEND_API_KEY:-}"         ]] && upsert_env RESEND_API_KEY         "${RESEND_API_KEY}"

# Backend config (safe defaults — no secrets)
upsert_env DB_NAME                        "profitengine"
upsert_env DISTILLATION_CHEAP_PROVIDER   "${DISTILLATION_CHEAP_PROVIDER:-gemini}"
upsert_env DISTILLATION_CHEAP_MODEL      "${DISTILLATION_CHEAP_MODEL:-gemini-2.5-flash}"
upsert_env DISTILLATION_EXPENSIVE_PROVIDER "${DISTILLATION_EXPENSIVE_PROVIDER:-gemini}"
upsert_env DISTILLATION_EXPENSIVE_MODEL  "${DISTILLATION_EXPENSIVE_MODEL:-gemini-2.5-flash}"
upsert_env DISTILLATION_CACHE_TTL_HOURS  "${DISTILLATION_CACHE_TTL_HOURS:-168}"
upsert_env COHORT_TOTAL_SEATS            "${COHORT_TOTAL_SEATS:-100}"
upsert_env COHORT_LABEL                  "${COHORT_LABEL:-Cohort 1}"
upsert_env APP_PUBLIC_URL                "${APP_PUBLIC_URL:-https://profitengine.alreadyherellc.com}"

# Optional keys — injected when available, skipped otherwise
[[ -n "${ANTHROPIC_API_KEY:-}" ]] && upsert_env ANTHROPIC_API_KEY      "${ANTHROPIC_API_KEY}"
[[ -n "${DEVTO_API_KEY:-}"        ]] && upsert_env DEVTO_API_KEY         "${DEVTO_API_KEY}"
[[ -n "${AFFILIATE_LINKS:-}"      ]] && upsert_env AFFILIATE_LINKS        "${AFFILIATE_LINKS}"
[[ -n "${AMAZON_PARTNER_TAG:-}"   ]] && upsert_env AMAZON_PARTNER_TAG     "${AMAZON_PARTNER_TAG}"
[[ -n "${HASHNODE_API_KEY:-}"     ]] && upsert_env HASHNODE_API_KEY        "${HASHNODE_API_KEY}"
[[ -n "${HASHNODE_PUB_ID:-}"      ]] && upsert_env HASHNODE_PUBLICATION_ID "${HASHNODE_PUB_ID}"
[[ -n "${MEDIUM_API_KEY:-}"       ]] && upsert_env MEDIUM_API_KEY          "${MEDIUM_API_KEY}"
[[ -n "${MEDIUM_AUTHOR_ID:-}"     ]] && upsert_env MEDIUM_AUTHOR_ID        "${MEDIUM_AUTHOR_ID}"
[[ -n "${TELEGRAM_BOT_TOKEN:-}"   ]] && upsert_env TELEGRAM_BOT_TOKEN      "${TELEGRAM_BOT_TOKEN}"
[[ -n "${TELEGRAM_CHAT_ID:-}"     ]] && upsert_env TELEGRAM_CHAT_ID        "${TELEGRAM_CHAT_ID}"

# Auto-generate WEBHOOK_SECRET if not set
if ! grep -qE "^WEBHOOK_SECRET=.+" "$ENV_FILE"; then
  upsert_env WEBHOOK_SECRET "$(openssl rand -hex 32)"
  log "Generated new WEBHOOK_SECRET."
fi

log ".env updated."

# ── add deploy public key to authorized_keys ───────────────────────────────
# This key fingerprint: SHA256:lEzI1h1lTjWqNqjJmtO2WQQ8l/D09oAqFzOyeVPAhLM
DEPLOY_PUB_KEY="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJujLyE+xXWJn4cJ9bVTeLmWb2qzUWfTLjnd10GdNGKt profitengine-deploy@github-actions"
AUTH_KEYS="$HOME/.ssh/authorized_keys"
mkdir -p "$HOME/.ssh" && chmod 700 "$HOME/.ssh"
touch "$AUTH_KEYS" && chmod 600 "$AUTH_KEYS"
# Use fingerprint-based check so key rotation doesn't leave orphaned entries
if grep -qF "AAAAC3NzaC1lZDI1NTE5AAAAIJujLyE+xXWJn4cJ9bVTeLmWb2qzUWfTLjnd10GdNGKt" "$AUTH_KEYS" 2>/dev/null; then
  log "Deploy key already present in $AUTH_KEYS — skipping."
else
  # Remove any stale deploy keys with the same comment, add the current one
  sed -i '/profitengine-deploy@github-actions/d' "$AUTH_KEYS" 2>/dev/null || true
  echo "$DEPLOY_PUB_KEY" >> "$AUTH_KEYS"
  log "Added GitHub Actions deploy key to $AUTH_KEYS"
fi

# ── pull latest code ───────────────────────────────────────────────────────
log "Pulling latest code …"
git pull --ff-only || {
  warn "Fast-forward pull failed; fetching + resetting …"
  git fetch origin main
  git reset --hard origin/main
}

# ── open OS-level firewall (OCI Oracle Linux ships with firewalld blocking everything) ──
log "Opening ports 80 and 443 in OS firewall …"
if command -v firewall-cmd &>/dev/null; then
  sudo firewall-cmd --permanent --add-service=http  --add-service=https 2>/dev/null || true
  sudo firewall-cmd --reload 2>/dev/null || true
  log "firewalld: http + https allowed"
elif command -v ufw &>/dev/null; then
  sudo ufw allow http  2>/dev/null || true
  sudo ufw allow https 2>/dev/null || true
  log "ufw: http + https allowed"
else
  # Raw iptables fallback
  sudo iptables -I INPUT -p tcp --dport 80  -j ACCEPT 2>/dev/null || true
  sudo iptables -I INPUT -p tcp --dport 443 -j ACCEPT 2>/dev/null || true
  log "iptables: ports 80/443 inserted"
fi

# ── free build cache before rebuilding (prevents disk-full failures) ──────
log "Pruning Docker build cache …"
docker buildx prune -af --filter type=exec.cachemount 2>/dev/null || true
# Keep at least 4 GB free; if less, prune all build + dangling images
AVAIL_KB=$(df / | awk 'NR==2{print $4}')
if [[ "${AVAIL_KB:-0}" -lt 4194304 ]]; then
  warn "Disk below 4 GB free (${AVAIL_KB} KB) — running full prune …"
  docker buildx prune -af 2>/dev/null || true
  docker image prune -af 2>/dev/null || true
fi

# ── rebuild and restart containers ────────────────────────────────────────
log "Rebuilding Docker images …"
docker compose build web runtime backend

log "Restarting services (ollama is opt-in; use --profile local-llm to enable) …"
docker compose up -d --remove-orphans

# ── wait for services ─────────────────────────────────────────────────────
log "Waiting for runtime API …"
for i in $(seq 1 30); do
  # runtime has curl; web (Alpine Next.js) does not
  docker compose exec -T runtime python3 -c \
    "import urllib.request,sys; r=urllib.request.urlopen('http://localhost:8080/health',timeout=3); sys.exit(0 if r.status==200 else 1)" \
    > /dev/null 2>&1 && { log "Runtime healthy."; break; } || sleep 2
done

log "Waiting for web (Next.js) …"
for i in $(seq 1 30); do
  docker compose exec -T runtime python3 -c \
    "import urllib.request,sys; r=urllib.request.urlopen('http://web:3000/api/health',timeout=3); sys.exit(0 if r.status==200 else 1)" \
    > /dev/null 2>&1 && { log "Web healthy."; break; } || sleep 2
done

log "Waiting for FastAPI backend …"
for i in $(seq 1 30); do
  docker compose exec -T backend python3 -c \
    "import urllib.request,sys; r=urllib.request.urlopen('http://localhost:8001/api/health',timeout=3); sys.exit(0 if r.status==200 else 1)" \
    > /dev/null 2>&1 && { log "Backend healthy."; break; } || sleep 2
done

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
