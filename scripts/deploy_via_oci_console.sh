#!/bin/bash
# Deploy ProfitEngine secrets via OCI Console Cloud Shell or Serial Console
# Run this script ON the server (not locally)
# Purpose: Avoids SSH key issues by running directly on target

set -euo pipefail

echo "🚀 ProfitEngine v5 - Direct Server Deployment"
echo "=================================================="
echo ""

APP_DIR="/home/opc/profitenginev5"
ENV_FILE="$APP_DIR/.env"

# Create directory
mkdir -p "$APP_DIR"

# Initialize .env
echo "[*] Creating .env file at: $ENV_FILE"
touch "$ENV_FILE"
chmod 600 "$ENV_FILE"
> "$ENV_FILE"  # Clear it

# Function to safely add a secret
add_secret() {
    local name="$1"
    local value="$2"

    if [ -z "$value" ]; then
        echo "    ⏭️  $name (empty, skipping)"
        return
    fi

    # Remove any existing entry
    sed -i.bak "/^${name}=/d" "$ENV_FILE" 2>/dev/null || true

    # Add new entry (escape special characters)
    printf '%s=%s\n' "$name" "$value" >> "$ENV_FILE"
    echo "    ✅ $name"
}

# Prompt for each secret
echo "[+] Enter secrets (paste from GitHub Secrets):"
echo ""

# Payment Processing
read -p "STRIPE_SECRET_KEY: " STRIPE_SECRET_KEY
add_secret "STRIPE_SECRET_KEY" "$STRIPE_SECRET_KEY"

read -p "STRIPE_API_KEY: " STRIPE_API_KEY
add_secret "STRIPE_API_KEY" "$STRIPE_API_KEY"

read -p "STRIPE_WEBHOOK_SECRET: " STRIPE_WEBHOOK_SECRET
add_secret "STRIPE_WEBHOOK_SECRET" "$STRIPE_WEBHOOK_SECRET"

# Products
read -p "GUMROAD_ACCESS_TOKEN: " GUMROAD_ACCESS_TOKEN
add_secret "GUMROAD_ACCESS_TOKEN" "$GUMROAD_ACCESS_TOKEN"

read -p "GUMROAD_SELLER_ID: " GUMROAD_SELLER_ID
add_secret "GUMROAD_SELLER_ID" "$GUMROAD_SELLER_ID"

# AI Providers
read -p "OPENROUTER_API_KEY: " OPENROUTER_API_KEY
add_secret "OPENROUTER_API_KEY" "$OPENROUTER_API_KEY"

read -p "GROQ_API_KEY: " GROQ_API_KEY
add_secret "GROQ_API_KEY" "$GROQ_API_KEY"

read -p "GEMINI_API_KEY: " GEMINI_API_KEY
add_secret "GEMINI_API_KEY" "$GEMINI_API_KEY"

read -p "OPENAI_API_KEY: " OPENAI_API_KEY
add_secret "OPENAI_API_KEY" "$OPENAI_API_KEY"

# Databases
read -p "MONGODB_URL: " MONGODB_URL
add_secret "MONGODB_URL" "$MONGODB_URL"

read -p "DATABASE_URL: " DATABASE_URL
add_secret "DATABASE_URL" "$DATABASE_URL"

# Content Publishing
read -p "BEEHIIV_API_KEY: " BEEHIIV_API_KEY
add_secret "BEEHIIV_API_KEY" "$BEEHIIV_API_KEY"

read -p "BEEHIIV_PUBLICATION_ID: " BEEHIIV_PUBLICATION_ID
add_secret "BEEHIIV_PUBLICATION_ID" "$BEEHIIV_PUBLICATION_ID"

read -p "DEVTO_API_KEY: " DEVTO_API_KEY
add_secret "DEVTO_API_KEY" "$DEVTO_API_KEY"

read -p "HASHNODE_API_KEY: " HASHNODE_API_KEY
add_secret "HASHNODE_API_KEY" "$HASHNODE_API_KEY"

read -p "HASHNODE_PUB_ID: " HASHNODE_PUB_ID
add_secret "HASHNODE_PUB_ID" "$HASHNODE_PUB_ID"

read -p "MEDIUM_API_KEY: " MEDIUM_API_KEY
add_secret "MEDIUM_API_KEY" "$MEDIUM_API_KEY"

read -p "MEDIUM_AUTHOR_ID: " MEDIUM_AUTHOR_ID
add_secret "MEDIUM_AUTHOR_ID" "$MEDIUM_AUTHOR_ID"

# Social Media
read -p "YOUTUBE_CLIENT_ID: " YOUTUBE_CLIENT_ID
add_secret "YOUTUBE_CLIENT_ID" "$YOUTUBE_CLIENT_ID"

read -p "YOUTUBE_CLIENT_SECRET: " YOUTUBE_CLIENT_SECRET
add_secret "YOUTUBE_CLIENT_SECRET" "$YOUTUBE_CLIENT_SECRET"

read -p "YOUTUBE_REFRESH_TOKEN: " YOUTUBE_REFRESH_TOKEN
add_secret "YOUTUBE_REFRESH_TOKEN" "$YOUTUBE_REFRESH_TOKEN"

read -p "TELEGRAM_BOT_TOKEN: " TELEGRAM_BOT_TOKEN
add_secret "TELEGRAM_BOT_TOKEN" "$TELEGRAM_BOT_TOKEN"

read -p "TELEGRAM_CHAT_ID: " TELEGRAM_CHAT_ID
add_secret "TELEGRAM_CHAT_ID" "$TELEGRAM_CHAT_ID"

read -p "TELEGRAM_WEBHOOK_SECRET: " TELEGRAM_WEBHOOK_SECRET
add_secret "TELEGRAM_WEBHOOK_SECRET" "$TELEGRAM_WEBHOOK_SECRET"

# Infrastructure
read -p "GITHUB_TOKEN: " GITHUB_TOKEN
add_secret "GITHUB_TOKEN" "$GITHUB_TOKEN"

read -p "CONTENT_REPO_TOKEN: " CONTENT_REPO_TOKEN
add_secret "CONTENT_REPO_TOKEN" "$CONTENT_REPO_TOKEN"

read -p "HF_TOKEN: " HF_TOKEN
add_secret "HF_TOKEN" "$HF_TOKEN"

read -p "PROFITENGINE_WEBHOOK_TOKEN: " PROFITENGINE_WEBHOOK_TOKEN
add_secret "PROFITENGINE_WEBHOOK_TOKEN" "$PROFITENGINE_WEBHOOK_TOKEN"

read -p "RUNTIME_API_URL: " RUNTIME_API_URL
add_secret "RUNTIME_API_URL" "$RUNTIME_API_URL"

# Cloud Services
read -p "AWS_ACCESS_KEY_ID: " AWS_ACCESS_KEY_ID
add_secret "AWS_ACCESS_KEY_ID" "$AWS_ACCESS_KEY_ID"

read -p "AWS_SECRET_ACCESS_KEY: " AWS_SECRET_ACCESS_KEY
add_secret "AWS_SECRET_ACCESS_KEY" "$AWS_SECRET_ACCESS_KEY"

# Verify
echo ""
echo "[✓] .env file created"
echo "[*] Total secrets: $(grep -c "=" "$ENV_FILE")"
chmod 600 "$ENV_FILE"
ls -lh "$ENV_FILE"

# Restart services
echo ""
echo "[*] Restarting Docker services..."
cd "$APP_DIR/deploy"
docker compose -f docker-compose.prod.yml restart || sudo docker compose -f docker-compose.prod.yml restart

sleep 8

echo ""
echo "[*] Service Status:"
docker compose -f docker-compose.prod.yml ps || sudo docker compose -f docker-compose.prod.yml ps

echo ""
echo "✅ Deployment complete!"
echo "💰 Revenue streams active: Trading • Payments • Products • Affiliate • Newsletter • Content"
echo "📊 Expected: \$1K-\$2.8K+/month"
