#!/usr/bin/env bash
# Restores all required authorized_keys on the OCI server.
# Run this from OCI serial console or any working shell to recover SSH access.
# Keys are baked in — no secrets needed at runtime.
set -euo pipefail

AUTHORIZED_KEYS_FILE="${HOME}/.ssh/authorized_keys"

log() { printf '[keywarden] %s\n' "$*"; }

install_keys() {
  mkdir -p ~/.ssh
  chmod 700 ~/.ssh

  # Declare required keys
  declare -a REQUIRED_KEYS=(
    "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDWOpmhKqA1QoSoCC4fv3Ee2Ie9TpdYXuokmDaUE+I9+ez6CA0I9tFMQr8HPGYoV6nvVL5uobSq8JEaObf7iBVdDu2aZYTVVGfCYenm2s+OWEikdAyVujNJ2GGWzKETbEjziq2ag23MSJ9UC4OETQb0fxiG+n+rGmzQV/pch9PYMMlDiLemZ8c476hL5MUf8DYWbdGUxrEz2eB4gxIj292Z+Rr/YbFXY8V75M24oIzhBZZp3LMwvI/ZzC8ZYxncFivyZZHMRWuvlpRcJZMtOlNtogXFvVBJpOPnTjbyhS4cqmLV0Xtbvsfuq6ZkFEvz6M03yOPp3/r8OUVgKiU4+tY5 oci_cmdos_oci-stephen"
    "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPp2I2ngE5QRsB9HyLbZCpxBwylhntz7IaElLbcto2FU devin-deploy-profitenginev5"
    "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIF5IOnsqRDtbUYu5WQfLaAjAQmc+zKrlK6TDafDgO0Ij profitengine-deploy@github-actions"
  )

  touch "$AUTHORIZED_KEYS_FILE"
  chmod 600 "$AUTHORIZED_KEYS_FILE"

  local added=0
  for key in "${REQUIRED_KEYS[@]}"; do
    if ! grep -qF "$key" "$AUTHORIZED_KEYS_FILE" 2>/dev/null; then
      echo "$key" >> "$AUTHORIZED_KEYS_FILE"
      log "Added: ${key##* }"
      ((added++))
    else
      log "Present: ${key##* }"
    fi
  done

  # Remove blank lines and deduplicate
  sort -u "$AUTHORIZED_KEYS_FILE" -o "$AUTHORIZED_KEYS_FILE"
  log "authorized_keys now has $(wc -l < "$AUTHORIZED_KEYS_FILE") entries (added $added new)"
}

install_keys
log "Done. Test with: ssh -i ~/.ssh/oci_cmdos_oci ubuntu@129.146.167.73 echo ok"
