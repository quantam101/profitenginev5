#!/bin/bash
# Setup OCI SSH Secret in GitHub
# This script safely adds the SSH key to GitHub Secrets

KEY_PATH="${1:-/c/Users/alrea/profitengine-key}"

echo "🔐 OCI SSH Secret Setup"
echo ""

# Verify key exists
if [ ! -f "$KEY_PATH" ]; then
    echo "❌ SSH key not found at: $KEY_PATH"
    exit 1
fi

echo "✅ SSH key found: $KEY_PATH"
echo ""

# Check GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI not found. Install from: https://cli.github.com"
    exit 1
fi

echo "✅ GitHub CLI is available"
echo ""

echo "Setting up GitHub Secret OCI_SSH_KEY..."
cat "$KEY_PATH" | gh secret set OCI_SSH_KEY --repo quantam101/profitengine-v5

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Secret added successfully!"
    echo ""
    echo "Testing SSH connection to OCI instance..."

    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no -o ConnectTimeout=10 opc@129.146.167.73 "uptime" 2>/dev/null

    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ SSH authentication verified!"
        echo ""
        echo "Next: Run the recovery workflow to test"
        echo "  gh workflow run oci-auto-recovery.yml -f action=status"
    else
        echo ""
        echo "⚠️ SSH connection test failed."
        echo "Check that the public key is authorized on the OCI instance."
        echo "Manual: OCI Console → Instance → Edit → SSH Keys → Add profitengine-key.pub"
    fi
else
    echo "❌ Failed to set secret. Verify GitHub CLI auth:"
    echo "  gh auth login"
    exit 1
fi
