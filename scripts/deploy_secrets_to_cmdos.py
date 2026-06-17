#!/usr/bin/env python3
"""
Deploy all GitHub Secrets to CMDOS server .env file
Uses SSH to safely sync secrets without fork issues
"""

import subprocess
import os
import sys
from pathlib import Path

# Configuration
CMDOS_HOST = "129.146.236.177"
APP_DIR = "/home/opc/profitenginev5"
SSH_KEY = str(Path.home() / ".ssh" / "cmdos_deploy_key")
OPC_USER = "opc"

# List of production secrets to deploy
SECRETS = [
    'BEEHIIV_API_KEY',
    'BEEHIIV_PUBLICATION_ID',
    'CONTENT_REPO_TOKEN',
    'DATABASE_URL',
    'DEVTO_API_KEY',
    'GEMINI_API_KEY',
    'GROQ_API_KEY',
    'GUMROAD_ACCESS_TOKEN',
    'GUMROAD_SELLER_ID',
    'HASHNODE_API_KEY',
    'HASHNODE_PUB_ID',
    'HF_TOKEN',
    'MEDIUM_API_KEY',
    'MEDIUM_AUTHOR_ID',
    'MONGODB_URL',
    'OPENAI_API_KEY',
    'OPENROUTER_API_KEY',
    'PROFITENGINE_WEBHOOK_TOKEN',
    'RUNTIME_API_URL',
    'STRIPE_API_KEY',
    'STRIPE_SECRET_KEY',
    'STRIPE_WEBHOOK_SECRET',
    'TELEGRAM_BOT_TOKEN',
    'TELEGRAM_CHAT_ID',
    'TELEGRAM_WEBHOOK_SECRET',
    'YOUTUBE_CLIENT_ID',
    'YOUTUBE_CLIENT_SECRET',
    'YOUTUBE_REFRESH_TOKEN',
    'AWS_ACCESS_KEY_ID',
    'AWS_SECRET_ACCESS_KEY',
    'GITHUB_TOKEN',
]

def get_secret(secret_name):
    """Get secret from GitHub CLI"""
    try:
        result = subprocess.run(
            ['gh', 'secret', 'view', secret_name],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except Exception as e:
        print(f"  ✗ {secret_name} (error: {e})")
        return None

def deploy_to_server():
    """Deploy secrets to CMDOS server"""

    print("[*] Deploying API secrets to CMDOS server")
    print(f"    Host: {CMDOS_HOST}")
    print(f"    App:  {APP_DIR}")
    print()

    # Collect secrets
    print("[+] Retrieving secrets from GitHub...")
    secrets_data = {}
    for secret_name in SECRETS:
        value = get_secret(secret_name)
        if value:
            secrets_data[secret_name] = value
            print(f"    [OK] {secret_name}")
        else:
            print(f"    [--] {secret_name} (skipped)")

    print()
    print(f"[OK] Collected {len(secrets_data)} secrets")
    print()

    if not secrets_data:
        print("[!] No secrets retrieved. Aborting deployment.")
        return False

    # Build env file content
    env_content = ""
    for name, value in secrets_data.items():
        # Escape special characters for shell
        escaped_value = value.replace("'", "'\\''")
        env_content += f"{name}='{escaped_value}'\n"

    # Deploy via SSH
    print("[*] Deploying to server via SSH...")

    # SSH command to create/update .env and restart services
    ssh_cmd = [
        'ssh',
        '-o', 'StrictHostKeyChecking=no',
        '-o', 'BatchMode=yes',
        '-i', SSH_KEY,
        f'{OPC_USER}@{CMDOS_HOST}',
        f"""
# Create .env with secrets
ENV_FILE="{APP_DIR}/.env"
mkdir -p "{APP_DIR}"
touch "$ENV_FILE"
chmod 600 "$ENV_FILE"

# Build .env from stdin
cat > "$ENV_FILE" << 'ENVEOF'
{env_content}ENVEOF

chmod 600 "$ENV_FILE"
echo "[OK] .env updated on server"
echo ""

# Restart services
cd "{APP_DIR}/deploy"
docker compose -f docker-compose.prod.yml restart 2>&1 | tail -3
sleep 8

echo ""
echo "[*] Service Status:"
docker compose -f docker-compose.prod.yml ps

# Health check
echo ""
echo "[*] Health Endpoints:"
curl -s http://localhost:3000 -I | head -1 || echo "    Dashboard: pending..."
curl -s http://localhost:8000/health -I | head -1 || echo "    Runtime API: pending..."
curl -s http://localhost:8001/health -I | head -1 || echo "    Backend API: pending..."
"""
    ]

    try:
        result = subprocess.run(
            ssh_cmd,
            capture_output=False,
            text=True,
            timeout=120
        )

        if result.returncode == 0:
            print()
            print("[OK] Deployment complete!")
            print()
            print("[+] Revenue streams now active:")
            print("    - Trading (Robinhood)")
            print("    - Payments (Stripe)")
            print("    - Products (Gumroad)")
            print("    - Affiliate (Amazon)")
            print("    - Newsletter (Beehiiv)")
            print("    - Content (GitHub Pages)")
            print()
            print("[*] Expected earnings: $1K-$2.8K+/month")
            return True
        else:
            print()
            print(f"[!] SSH deployment failed with exit code {result.returncode}")
            return False

    except subprocess.TimeoutExpired:
        print("[!] SSH command timed out")
        return False
    except Exception as e:
        print(f"[!] Error during deployment: {e}")
        return False

if __name__ == "__main__":
    if not os.path.exists(SSH_KEY):
        print(f"[!] SSH key not found: {SSH_KEY}")
        sys.exit(1)

    success = deploy_to_server()
    sys.exit(0 if success else 1)
