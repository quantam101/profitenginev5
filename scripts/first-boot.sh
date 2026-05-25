#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════
#  ProfitEngine v5 — First-Boot Setup
#
#  Run this ONCE on a fresh Ubuntu 22.04 / 24.04 OCI instance to:
#    1. Install Docker + Compose
#    2. Clone the repo
#    3. Add the GitHub Actions deploy key to authorized_keys
#    4. Write all secrets to .env
#    5. Start all services
#
#  METHOD A — OCI Serial Console (no SSH key needed):
#    OCI Console → Instances → profitengine-server
#    → Console connections → Create local connection
#    → Connect (serial console or VNC)
#    → Paste this ENTIRE script when prompted, press Enter
#
#  METHOD B — OCI Cloud Shell (if instance is on public subnet):
#    Open Cloud Shell (>_ in OCI Console top bar)
#    → ssh ubuntu@129.146.167.73   (if your OCI Cloud Shell key is in authorized_keys)
#    → Paste this script
#
#  METHOD C — Any machine with any working SSH key:
#    ssh -i YOUR_KEY ubuntu@129.146.167.73
#    → Paste this script
#
#  Fill in your API keys below before running.
# ═══════════════════════════════════════════════════════════════════
set -euo pipefail

# ── YOUR KEYS (fill these in before running) ──────────────────────
# Keys are in your Bitwarden vault and in GitHub Actions secrets.
# Find them in: Downloads/COMPLETE_SETUP.sh  or  GitHub → Settings → Secrets
GROQ_API_KEY="${GROQ_API_KEY:-<your-groq-key>}"
GEMINI_API_KEY="${GEMINI_API_KEY:-<your-gemini-key>}"
GITHUB_CONTENT_TOKEN="${GITHUB_CONTENT_TOKEN:-<your-github-pat>}"
GMAIL_APP_PASSWORD="${GMAIL_APP_PASSWORD:-<your-gmail-app-password>}"
AMAZON_PARTNER_TAG="${AMAZON_PARTNER_TAG:-alreadyhere-20}"
DEVTO_API_KEY="${DEVTO_API_KEY:-}"
# ─────────────────────────────────────────────────────────────────

REPO_DIR="/home/ubuntu/profitenginev5"
DEPLOY_PUB_KEY="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIF5IOnsqRDtbUYu5WQfLaAjAQmc+zKrlK6TDafDgO0Ij profitengine-deploy@github-actions"

log()  { echo -e "\033[32m[first-boot]\033[0m $*"; }
warn() { echo -e "\033[33m[first-boot] WARN:\033[0m $*" >&2; }

# ── 1. Add GitHub Actions deploy key (enables CI/CD forever after) ─
log "Adding GitHub Actions deploy key …"
mkdir -p ~/.ssh && chmod 700 ~/.ssh
touch ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys
if ! grep -qF "profitengine-deploy@github-actions" ~/.ssh/authorized_keys; then
  echo "$DEPLOY_PUB_KEY" >> ~/.ssh/authorized_keys
  log "Deploy key added — GitHub Actions can now SSH into this server."
else
  log "Deploy key already present."
fi

# ── 2. Install Docker ───────────────────────────────────────────────
if ! command -v docker &>/dev/null; then
  log "Installing Docker …"
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -qq
  apt-get install -y -qq ca-certificates curl gnupg lsb-release git
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
    https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
    tee /etc/apt/sources.list.d/docker.list > /dev/null
  apt-get update -qq
  apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin
  usermod -aG docker ubuntu
  systemctl enable docker
  systemctl start docker
  log "Docker installed."
else
  log "Docker already installed: $(docker --version)"
fi

# ── 3. Install docker compose v2 if missing ────────────────────────
if ! docker compose version &>/dev/null; then
  log "Installing Docker Compose plugin …"
  apt-get install -y -qq docker-compose-plugin
fi

# ── 4. Clone or update repo ────────────────────────────────────────
if [[ ! -d "$REPO_DIR/.git" ]]; then
  log "Cloning profitenginev5 …"
  git clone https://github.com/quantam101/profitenginev5.git "$REPO_DIR"
else
  log "Repo already cloned — pulling latest …"
  git -C "$REPO_DIR" pull --ff-only || {
    warn "Fast-forward failed; resetting to origin/main"
    git -C "$REPO_DIR" fetch origin main
    git -C "$REPO_DIR" reset --hard origin/main
  }
fi

# ── 5. Run bootstrap with all secrets ─────────────────────────────
log "Running bootstrap-server.sh …"
cd "$REPO_DIR"

export GROQ_API_KEY GEMINI_API_KEY GITHUB_CONTENT_TOKEN GMAIL_APP_PASSWORD
export AMAZON_PARTNER_TAG DEVTO_API_KEY

bash scripts/bootstrap-server.sh

log ""
log "╔══════════════════════════════════════════════════════════════╗"
log "║  FIRST BOOT COMPLETE                                         ║"
log "╠══════════════════════════════════════════════════════════════╣"
log "║  Dashboard: http://129.146.167.73:3000                       ║"
log "║  Health:    http://129.146.167.73:3000/api/health            ║"
log "║  CI/CD:     every git push to main auto-deploys now          ║"
log "╚══════════════════════════════════════════════════════════════╝"
