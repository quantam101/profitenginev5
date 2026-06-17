#!/bin/bash
set -euo pipefail

###############################################################################
# ProfitEngine v5 — SSH Key Deployment Script
# Adds SSH public key to server and deploys services
###############################################################################

CMDOS_HOST="129.146.236.177"
CMDOS_USER="opc"
SSH_KEY="~/.ssh/cmdos_deploy_key"
SSH_PUBKEY="~/.ssh/cmdos_deploy_key.pub"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[!]${NC} $1"; }

###############################################################################
echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo "ProfitEngine v5 — SSH Key Deployment"
echo "Target: $CMDOS_USER@$CMDOS_HOST"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

# Expand tilde
SSH_KEY="${SSH_KEY/#\~/$HOME}"
SSH_PUBKEY="${SSH_PUBKEY/#\~/$HOME}"

# Verify key files exist
log_info "Verifying SSH key files..."
if [ ! -f "$SSH_KEY" ]; then
    log_error "Private key not found: $SSH_KEY"
    exit 1
fi
log_success "Private key found: $SSH_KEY"

if [ ! -f "$SSH_PUBKEY" ]; then
    log_error "Public key not found: $SSH_PUBKEY"
    exit 1
fi
log_success "Public key found: $SSH_PUBKEY"

echo ""
log_info "SSH Public Key:"
cat "$SSH_PUBKEY"
echo ""

###############################################################################
echo ""
log_info "STEP 1: Attempting to add SSH key to server..."
echo ""

# Try ssh-copy-id first
if command -v ssh-copy-id &> /dev/null; then
    log_info "Using ssh-copy-id to add public key to server..."
    echo "Note: You may be prompted for password for $CMDOS_USER@$CMDOS_HOST"
    echo ""

    if ssh-copy-id -i "$SSH_PUBKEY" "$CMDOS_USER@$CMDOS_HOST" 2>/dev/null; then
        log_success "SSH public key added successfully!"
    else
        log_warn "ssh-copy-id failed. Trying manual method..."

        # Manual method
        echo ""
        log_info "Adding key manually via SSH..."
        echo "You will be prompted for the password one more time..."
        echo ""

        ssh "$CMDOS_USER@$CMDOS_HOST" << 'MANUAL_ADD_KEY_EOF'
mkdir -p ~/.ssh
cat >> ~/.ssh/authorized_keys << 'PUBKEY_EOF'
MANUAL_ADD_KEY_EOF

        cat "$SSH_PUBKEY" | ssh "$CMDOS_USER@$CMDOS_HOST" "cat >> ~/.ssh/authorized_keys"

        ssh "$CMDOS_USER@$CMDOS_HOST" "chmod 600 ~/.ssh/authorized_keys && chmod 700 ~/.ssh"
        log_success "SSH public key added manually"
    fi
else
    log_warn "ssh-copy-id not found, using manual method..."

    ssh "$CMDOS_USER@$CMDOS_HOST" << 'MANUAL_METHOD_EOF'
mkdir -p ~/.ssh
chmod 700 ~/.ssh
MANUAL_METHOD_EOF

    cat "$SSH_PUBKEY" | ssh "$CMDOS_USER@$CMDOS_HOST" "cat >> ~/.ssh/authorized_keys"

    ssh "$CMDOS_USER@$CMDOS_HOST" "chmod 600 ~/.ssh/authorized_keys"
    log_success "SSH public key added"
fi

echo ""
log_info "Verifying SSH key authentication..."

# Test SSH connection with key
if timeout 10 ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$CMDOS_USER@$CMDOS_HOST" "echo 'SSH Key Authentication Verified'" 2>/dev/null; then
    log_success "SSH key authentication working!"
else
    log_error "SSH key authentication failed"
    log_warn "You may need to manually add the key to the server"
    exit 1
fi

###############################################################################
echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
log_info "STEP 2: Deploying services to CMDOS..."
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

# Deploy via SSH
ssh -i "$SSH_KEY" "$CMDOS_USER@$CMDOS_HOST" << 'DEPLOY_SCRIPT_EOF'
#!/bin/bash
set -euo pipefail

APP_DIR="/home/opc/profitenginev5"
DEPLOY_DIR="$APP_DIR/deploy"

echo "[INFO] ═══════════════════════════════════════════════════════════════"
echo "[INFO] ProfitEngine v5 — CMDOS Deployment Started"
echo "[INFO] ═══════════════════════════════════════════════════════════════"
echo ""

# Phase 1: Pre-flight checks
echo "[INFO] PHASE 1: Pre-flight Checks"
if [ ! -d "$APP_DIR" ]; then
    echo "[ERROR] Application directory not found: $APP_DIR"
    exit 1
fi
echo "[✓] Application directory verified"

if [ ! -f "$DEPLOY_DIR/docker-compose.prod.yml" ]; then
    echo "[ERROR] Docker Compose file not found"
    exit 1
fi
echo "[✓] Docker Compose configuration found"

if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker is not installed"
    exit 1
fi
echo "[✓] Docker is available"

# Phase 2: Update code
echo ""
echo "[INFO] PHASE 2: Update Code"
cd "$APP_DIR"
git pull origin main
echo "[✓] Code updated"

# Phase 3: Create .env if needed
echo ""
echo "[INFO] PHASE 3: Environment Configuration"
if [ ! -f "$APP_DIR/.env" ]; then
    echo "[INFO] Creating .env from .env.example"
    cp .env.example .env
    echo "[WARNING] .env file created with defaults"
    echo "[WARNING] IMPORTANT: Configure your secrets in .env:"
    echo "  - POSTGRES_PASSWORD"
    echo "  - MONGO_URL"
    echo "  - API keys (Stripe, Anthropic, etc.)"
    echo ""
    echo "[INFO] Edit .env:"
    echo "  ssh opc@129.146.236.177"
    echo "  nano /home/opc/profitenginev5/.env"
else
    echo "[✓] .env file exists"
fi

# Phase 4: Stop old services
echo ""
echo "[INFO] PHASE 4: Stop Previous Services"
cd "$DEPLOY_DIR"
docker compose -f docker-compose.prod.yml down 2>/dev/null || true
echo "[✓] Previous services stopped"

# Phase 5: Pull images
echo ""
echo "[INFO] PHASE 5: Pull Docker Images"
docker compose -f docker-compose.prod.yml pull
echo "[✓] Docker images ready"

# Phase 6: Start services
echo ""
echo "[INFO] PHASE 6: Start Services"
docker compose -f docker-compose.prod.yml up -d --build
echo "[✓] Services starting..."

# Phase 7: Wait and verify
echo ""
echo "[INFO] PHASE 7: Service Verification"
sleep 15

echo ""
echo "[INFO] Service Status:"
docker compose -f docker-compose.prod.yml ps

echo ""
echo "[INFO] Health Checks:"
for i in {1..5}; do
    if curl -s http://localhost/health > /dev/null 2>&1; then
        echo "[✓] System health check passed"
        break
    fi
    if [ $i -lt 5 ]; then
        echo "[⏳] Waiting for services... ($i/5)"
        sleep 3
    else
        echo "[⚠] Health check still pending (services may take longer to initialize)"
    fi
done

# Phase 8: Final summary
echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo "[✓] DEPLOYMENT COMPLETE"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "Access URLs:"
echo "  Dashboard:  http://129.146.236.177:3000"
echo "  Runtime:    http://129.146.236.177:8000/health"
echo "  Backend:    http://129.146.236.177:8001/health"
echo "  System:     http://129.146.236.177/health"
echo ""
echo "Next Steps:"
echo "  1. Check services are running:"
echo "     docker compose -f deploy/docker-compose.prod.yml ps"
echo ""
echo "  2. Configure secrets in .env:"
echo "     nano /home/opc/profitenginev5/.env"
echo ""
echo "  3. Restart services after .env changes:"
echo "     cd /home/opc/profitenginev5/deploy"
echo "     docker compose -f docker-compose.prod.yml restart"
echo ""
echo "  4. Monitor logs:"
echo "     docker compose -f docker-compose.prod.yml logs -f"
echo ""
DEPLOY_SCRIPT_EOF

# Deployment succeeded
DEPLOY_EXIT=$?

###############################################################################
echo ""
echo "═══════════════════════════════════════════════════════════════════════════"

if [ $DEPLOY_EXIT -eq 0 ]; then
    log_success "DEPLOYMENT COMPLETE!"
    echo ""
    echo "✅ Services deployed to 129.146.236.177"
    echo ""
    echo "Verify Deployment:"
    echo "  curl http://129.146.236.177:3000/"
    echo "  curl http://129.146.236.177:8000/health"
    echo "  curl http://129.146.236.177:8001/health"
    echo ""
    echo "SSH Access:"
    echo "  ssh -i ~/.ssh/cmdos_deploy_key opc@129.146.236.177"
    echo ""
    echo "Or simply:"
    echo "  ssh opc@129.146.236.177"
    echo ""
else
    log_error "DEPLOYMENT FAILED (exit code: $DEPLOY_EXIT)"
    echo ""
    echo "For troubleshooting:"
    echo "  1. SSH to server: ssh -i ~/.ssh/cmdos_deploy_key opc@129.146.236.177"
    echo "  2. Check logs: docker compose -f deploy/docker-compose.prod.yml logs"
    echo "  3. Verify Docker: docker ps"
    exit 1
fi

echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
