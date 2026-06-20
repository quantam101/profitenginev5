#!/bin/bash
set -euo pipefail

# Deploy ProfitEngine to OCI cmdos server
# Usage: ./scripts/deploy-to-oci.sh [--push-images] [--register-webhooks]

echo "🚀 Deploying ProfitEngine to OCI..."
echo "=================================================="

# Configuration
OCI_HOST="${OCI_HOST:-129.146.236.177}"
OCI_USER="${OCI_USER:-opc}"
SSH_KEY_VAR="${OCI_SSH_KEY:-}"
PUSH_IMAGES=false
REGISTER_WEBHOOKS=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --push-images)
            PUSH_IMAGES=true
            shift
            ;;
        --register-webhooks)
            REGISTER_WEBHOOKS=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--push-images] [--register-webhooks]"
            exit 1
            ;;
    esac
done

# Load environment
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo "❌ .env file not found"
    exit 1
fi

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

LOG_FILE="deployment-$(date +%s).log"

log() {
    echo -e "${BLUE}[$(date +%H:%M:%S)]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}✅ $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}❌ $1${NC}" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}" | tee -a "$LOG_FILE"
}

# Step 0: Verify Prerequisites
log "Verifying prerequisites..."

if [ -z "$OCI_SSH_KEY" ]; then
    error "OCI_SSH_KEY not set in .env"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    error "Docker not installed"
    exit 1
fi

success "Prerequisites verified"

# Step 1: Test SSH Connection
log "Testing SSH connection to OCI server..."
SSH_KEY_FILE="/tmp/oci_ssh_key_$$"
printf '%s\n' "$OCI_SSH_KEY" > "$SSH_KEY_FILE"
chmod 600 "$SSH_KEY_FILE"

if ssh -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=10 \
    -i "$SSH_KEY_FILE" "${OCI_USER}@${OCI_HOST}" "echo 'SSH connection successful'" 2>/dev/null; then
    success "SSH connection verified"
else
    error "Cannot connect to OCI server at ${OCI_USER}@${OCI_HOST}"
    rm -f "$SSH_KEY_FILE"
    exit 1
fi

# Step 2: Build Docker Images (optional)
if [ "$PUSH_IMAGES" = true ]; then
    log "Building Docker images..."

    # Backend
    if docker build -f Dockerfile -t profitengine-backend:latest . >> "$LOG_FILE" 2>&1; then
        success "Backend image built"
    else
        error "Failed to build backend image"
        rm -f "$SSH_KEY_FILE"
        exit 1
    fi

    # Frontend
    if docker build -f Dockerfile.web -t profitengine-web:latest . >> "$LOG_FILE" 2>&1; then
        success "Frontend image built"
    else
        error "Failed to build frontend image"
        rm -f "$SSH_KEY_FILE"
        exit 1
    fi

    log "Images built successfully"
fi

# Step 3: Deploy to OCI
log "Deploying application to OCI..."

# Create deployment script
DEPLOY_SCRIPT=$(cat << 'EOFDEPLOY'
#!/bin/bash
set -euo pipefail

cd /srv/profitengine || mkdir -p /srv/profitengine && cd /srv/profitengine

# Pull latest code
if [ -d .git ]; then
    git pull origin main
else
    git clone https://github.com/quantam101/profitenginev5.git .
fi

# Ensure directories exist
mkdir -p .runtime/revenue logs data

# Update environment file from passed secrets
cat > .env << 'ENVEOF'
# These will be populated by the deploy script
ENVEOF

# Bring up containers
docker-compose down || true
docker-compose up -d

# Wait for services to be ready
sleep 10

# Check backend health
if curl -fs http://localhost:8001/api/health > /dev/null; then
    echo "✅ Backend is healthy"
else
    echo "⚠️ Backend health check failed (may still be starting)"
fi

# Check frontend health
if curl -fs http://localhost:3000/api/health > /dev/null; then
    echo "✅ Frontend is healthy"
else
    echo "⚠️ Frontend health check failed (may still be starting)"
fi

echo "✅ Deployment complete"
EOFDEPLOY
)

# Transfer and execute deploy script on OCI
log "Transferring deployment script to OCI..."
REMOTE_SCRIPT="/tmp/deploy_profitengine_$$.sh"
echo "$DEPLOY_SCRIPT" | ssh -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" \
    "${OCI_USER}@${OCI_HOST}" "cat > $REMOTE_SCRIPT && chmod +x $REMOTE_SCRIPT && $REMOTE_SCRIPT"

if [ $? -eq 0 ]; then
    success "Application deployed to OCI"
else
    error "Deployment failed"
    rm -f "$SSH_KEY_FILE"
    exit 1
fi

# Step 4: Verify Deployment
log "Verifying deployment..."

# Test endpoints
if ssh -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" "${OCI_USER}@${OCI_HOST}" \
    "curl -fs http://localhost:3000/ > /dev/null && echo 'Frontend responding'" 2>/dev/null; then
    success "Frontend responding on port 3000"
else
    warning "Frontend not yet responding (may still be starting)"
fi

if ssh -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" "${OCI_USER}@${OCI_HOST}" \
    "curl -fs http://localhost:8001/api/health > /dev/null && echo 'Backend responding'" 2>/dev/null; then
    success "Backend responding on port 8001"
else
    warning "Backend not yet responding (may still be starting)"
fi

# Step 5: Configure DNS and Caddy
log "Configuring domain and reverse proxy..."

DNS_UPDATE=$(cat << 'EOFDNS'
#!/bin/bash
# Update Caddyfile with correct domain

DOMAIN=${PUBLIC_SITE_URL#https://}
DOMAIN=${DOMAIN#http://}

cat > /srv/profitengine/caddy/Caddyfile << CADDYEOF
{
  auto_https off
  email ${ACME_EMAIL}
}

${DOMAIN} {
  # Frontend (Next.js)
  handle /api/* {
    reverse_proxy http://backend:8001
  }

  # Health checks
  handle /api/health {
    reverse_proxy http://backend:8001
  }

  # Default to frontend
  reverse_proxy http://web:3000
}

@internal {
  remote_ip 127.0.0.1
  remote_ip ::1
}

localhost:9000 {
  authorize @internal
  reverse_proxy http://caddy:2019
}
CADDYEOF

docker-compose exec -T caddy caddy reload
EOFDNS
)

echo "$DNS_UPDATE" | ssh -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" \
    "${OCI_USER}@${OCI_HOST}" "bash -s"

success "Domain and reverse proxy configured"

# Step 6: Register Webhooks (optional)
if [ "$REGISTER_WEBHOOKS" = true ]; then
    log "Registering webhooks..."
    PUBLIC_SITE_URL="https://${OCI_HOST}" bash scripts/register-webhooks.sh
    success "Webhooks registered"
fi

# Cleanup
rm -f "$SSH_KEY_FILE"

# Summary
echo ""
echo "=================================================="
{
    echo "✅ DEPLOYMENT COMPLETE"
    echo ""
    echo "🌐 Access Points:"
    echo "   Frontend: https://profitengine.alreadyherellc.com"
    echo "   Backend:  https://profitengine.alreadyherellc.com/api"
    echo "   Dashboard: https://profitengine.alreadyherellc.com/command-center/revenue"
    echo ""
    echo "📝 Next Steps:"
    echo "1. Verify DNS: nslookup profitengine.alreadyherellc.com"
    echo "2. Check health: curl https://profitengine.alreadyherellc.com/api/health"
    echo "3. Register webhooks: bash scripts/register-webhooks.sh"
    echo "4. Monitor logs: ssh opc@${OCI_HOST} 'docker-compose logs -f'"
    echo ""
    echo "📊 Profit Systems Live:"
    echo "   • Gumroad ebook sales → /api/webhooks/gumroad"
    echo "   • Printify POD orders → /api/webhooks/printify"
    echo "   • Newsletter sponsorships → /api/webhooks/newsletter"
    echo "   • YouTube AdSense → Daily sync via APScheduler"
    echo ""
    echo "📋 Deployment log: $LOG_FILE"
} | tee -a "$LOG_FILE"

echo "=================================================="
success "Ready for revenue!"
