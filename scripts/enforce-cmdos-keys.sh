#!/bin/bash
###############################################################################
# CMDOS SSH Keys — Manual Enforcement Script
# Adds required SSH public keys to CMDOS authorized_keys
# Usage: bash scripts/enforce-cmdos-keys.sh [password-auth]
###############################################################################

set -euo pipefail

CMDOS_HOST="129.146.236.177"
CMDOS_USER="opc"

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
echo "CMDOS SSH Keys — Manual Enforcement"
echo "Target: ${CMDOS_USER}@${CMDOS_HOST}"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

# Public keys to enforce
declare -a PUBKEYS=(
  "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDWOpmhKqA1QoSoCC4fv3Ee2Ie9TpdYXuokmDaUE+I9+ez6CA0I9tFMQr8HPGYoV6nvVL5uobSq8JEaObf7iBVdDu2aZYTVVGfCYenm2s+OWEikdAyVujNJ2GGWzKETbEjziq2ag23MSJ9UC4OETQb0fxiG+n+rGmzQV/pch9PYMMlDiLemZ8c476hL5MUf8DYWbdGUxrEz2eB4gxIj292Z+Rr/YbFXY8V75M24oIzhBZZp3LMwvI/ZzC8ZYxncFivyZZHMRWuvlpRcJZMtOlNtogXFvVBJpOPnTjbyhS4cqmLV0Xtbvsfuq6ZkFEvz6M03yOPp3/r8OUVgKiU4+tY5 oci_cmdos_oci-stephen"
  "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPp2I2ngE5QRsB9HyLbZCpxBwylhntz7IaElLbcto2FU devin-deploy-profitenginev5"
  "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIF5IOnsqRDtbUYu5WQfLaAjAQmc+zKrlK6TDafDgO0Ij profitengine-deploy@github-actions"
  "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICXECrB86ObQ8BnRVyRVenN+ZUHl/11z6VqusGTJfsRy profitengine-deploy@cmdos"
)

# Check if using password auth
USE_PASSWORD=false
if [ "${1:-}" = "password-auth" ]; then
  USE_PASSWORD=true
  log_info "Using password authentication (will prompt for ${CMDOS_USER} password)"
else
  log_info "Attempting key-based authentication"
fi

echo ""

###############################################################################
# Try key-based auth first
###############################################################################
if ! $USE_PASSWORD; then
  log_info "Checking SSH key-based authentication..."

  # Find available keys
  AVAILABLE_KEYS=()
  for keyfile in ~/.ssh/*_key ~/.ssh/id_* ~/.ssh/oci_* ~/.ssh/server_*; do
    if [ -f "$keyfile" ] && ! [[ "$keyfile" =~ ".pub" ]]; then
      AVAILABLE_KEYS+=("$keyfile")
    fi
  done

  if [ ${#AVAILABLE_KEYS[@]} -eq 0 ]; then
    log_warn "No SSH keys found in ~/.ssh/"
    USE_PASSWORD=true
  else
    log_success "Found ${#AVAILABLE_KEYS[@]} potential SSH key(s)"

    # Try each key
    for key in "${AVAILABLE_KEYS[@]}"; do
      if timeout 5 ssh -o StrictHostKeyChecking=no -o BatchMode=yes -i "$key" \
           "${CMDOS_USER}@${CMDOS_HOST}" "echo FOUND" 2>/dev/null; then
        log_success "SSH key authentication successful: $key"
        SSH_KEY="$key"
        USE_PASSWORD=false
        break
      fi
    done

    if [ -z "${SSH_KEY:-}" ]; then
      log_warn "No SSH key worked, falling back to password auth"
      USE_PASSWORD=true
    fi
  fi
fi

###############################################################################
# Enforce keys via SSH
###############################################################################
echo ""
log_info "Enforcing authorized_keys on ${CMDOS_HOST}..."
echo ""

if [ -n "${SSH_KEY:-}" ]; then
  # Using key-based auth
  ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "${CMDOS_USER}@${CMDOS_HOST}" 'bash -s' << 'ENFORCE_EOF'
mkdir -p ~/.ssh
chmod 700 ~/.ssh
touch ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Keys to enforce
declare -a KEYS=(
  "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDWOpmhKqA1QoSoCC4fv3Ee2Ie9TpdYXuokmDaUE+I9+ez6CA0I9tFMQr8HPGYoV6nvVL5uobSq8JEaObf7iBVdDu2aZYTVVGfCYenm2s+OWEikdAyVujNJ2GGWzKETbEjziq2ag23MSJ9UC4OETQb0fxiG+n+rGmzQV/pch9PYMMlDiLemZ8c476hL5MUf8DYWbdGUxrEz2eB4gxIj292Z+Rr/YbFXY8V75M24oIzhBZZp3LMwvI/ZzC8ZYxncFivyZZHMRWuvlpRcJZMtOlNtogXFvVBJpOPnTjbyhS4cqmLV0Xtbvsfuq6ZkFEvz6M03yOPp3/r8OUVgKiU4+tY5 oci_cmdos_oci-stephen"
  "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPp2I2ngE5QRsB9HyLbZCpxBwylhntz7IaElLbcto2FU devin-deploy-profitenginev5"
  "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIF5IOnsqRDtbUYu5WQfLaAjAQmc+zKrlK6TDafDgO0Ij profitengine-deploy@github-actions"
  "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICXECrB86ObQ8BnRVyRVenN+ZUHl/11z6VqusGTJfsRy profitengine-deploy@cmdos"
)

added=0
for key in "${KEYS[@]}"; do
  if ! grep -qF "$key" ~/.ssh/authorized_keys 2>/dev/null; then
    echo "$key" >> ~/.ssh/authorized_keys
    key_label="${key##* }"
    echo "  [+] Added: $key_label"
    ((added++))
  fi
done

sort -u ~/.ssh/authorized_keys -o ~/.ssh/authorized_keys
total=$(wc -l < ~/.ssh/authorized_keys)
echo ""
echo "✓ authorized_keys enforced"
echo "  Added: $added keys"
echo "  Total: $total keys"
ENFORCE_EOF

else
  # Using password auth
  ssh -o StrictHostKeyChecking=no "${CMDOS_USER}@${CMDOS_HOST}" 'bash -s' << 'ENFORCE_EOF'
mkdir -p ~/.ssh
chmod 700 ~/.ssh
touch ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

declare -a KEYS=(
  "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDWOpmhKqA1QoSoCC4fv3Ee2Ie9TpdYXuokmDaUE+I9+ez6CA0I9tFMQr8HPGYoV6nvVL5uobSq8JEaObf7iBVdDu2aZYTVVGfCYenm2s+OWEikdAyVujNJ2GGWzKETbEjziq2ag23MSJ9UC4OETQb0fxiG+n+rGmzQV/pch9PYMMlDiLemZ8c476hL5MUf8DYWbdGUxrEz2eB4gxIj292Z+Rr/YbFXY8V75M24oIzhBZZp3LMwvI/ZzC8ZYxncFivyZZHMRWuvlpRcJZMtOlNtogXFvVBJpOPnTjbyhS4cqmLV0Xtbvsfuq6ZkFEvz6M03yOPp3/r8OUVgKiU4+tY5 oci_cmdos_oci-stephen"
  "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPp2I2ngE5QRsB9HyLbZCpxBwylhntz7IaElLbcto2FU devin-deploy-profitenginev5"
  "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIF5IOnsqRDtbUYu5WQfLaAjAQmc+zKrlK6TDafDgO0Ij profitengine-deploy@github-actions"
  "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICXECrB86ObQ8BnRVyRVenN+ZUHl/11z6VqusGTJfsRy profitengine-deploy@cmdos"
)

added=0
for key in "${KEYS[@]}"; do
  if ! grep -qF "$key" ~/.ssh/authorized_keys 2>/dev/null; then
    echo "$key" >> ~/.ssh/authorized_keys
    key_label="${key##* }"
    echo "  [+] Added: $key_label"
    ((added++))
  fi
done

sort -u ~/.ssh/authorized_keys -o ~/.ssh/authorized_keys
total=$(wc -l < ~/.ssh/authorized_keys)
echo ""
echo "✓ authorized_keys enforced"
echo "  Added: $added keys"
echo "  Total: $total keys"
ENFORCE_EOF

fi

EXIT_CODE=$?

###############################################################################
# Summary
###############################################################################
echo ""
echo "═══════════════════════════════════════════════════════════════════════════"

if [ $EXIT_CODE -eq 0 ]; then
  log_success "SSH keys enforced successfully!"
  echo ""
  echo "Test SSH access:"
  echo "  ssh -i ~/.ssh/cmdos_deploy_key ${CMDOS_USER}@${CMDOS_HOST} 'echo OK'"
  echo ""
else
  log_error "Failed to enforce SSH keys (exit code: $EXIT_CODE)"
  echo ""
  echo "If SSH access is still blocked, use OCI Console:"
  echo "  Instance → Instance Details → Serial Console"
  echo "  Then run: bash scripts/ensure-authorized-keys.sh"
  echo ""
fi

echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

exit $EXIT_CODE
