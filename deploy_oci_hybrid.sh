#!/bin/bash
# OCI Hybrid System - Complete Automated Setup
# Run this on your OCI server: bash deploy_oci_hybrid.sh

set -e

echo "=========================================="
echo "🚀 OCI HYBRID SYSTEM - AUTOMATED SETUP"
echo "=========================================="
echo ""

# Step 1: Clone/update repo
echo "[1/8] Setting up repository..."
cd /home/ubuntu
if [ ! -d profitenginev5 ]; then
  echo "  Cloning repository..."
  git clone https://github.com/quantam101/profitenginev5.git
else
  echo "  Updating repository..."
  cd profitenginev5
  git pull origin main
  cd /home/ubuntu
fi
cd profitenginev5

# Step 2: Install system dependencies
echo "[2/8] Installing system dependencies..."
sudo apt-get update -qq
sudo apt-get install -y --quiet ffmpeg python3-pip python3-venv git

# Step 3: Setup Python environment
echo "[3/8] Setting up Python environment..."
python3 -m venv venv --quiet 2>/dev/null || python3 -m venv venv
source venv/bin/activate
pip install --quiet --upgrade pip setuptools wheel
pip install --quiet httpx pillow

# Step 4: Configure credentials
echo "[4/8] Configuring credentials..."
cat > /home/ubuntu/profitenginev5/.env.production << 'EOF'
# ===== VIDEO GENERATION =====
EAOS_VIDEO_ROOT=/home/ubuntu/profitenginev5/datacenter/video_pipeline
EAOS_GPU_ENABLED=false
PYTHONUTF8=1

# ===== TIKTOK =====
TIKTOK_CLIENT_KEY=aw585wlt3458r9dh
TIKTOK_CLIENT_SECRET=NjeOcOBE65Tx92OqoVjPlwUigoBeWSs5
TIKTOK_ACCESS_TOKEN=v1_YOUR_TIKTOK_ACCESS_TOKEN_HERE

# ===== TWITTER/X =====
TWITTER_API_KEY=W6JnmO0diTw30duXOF1PJkB2g
TWITTER_API_SECRET=1pKfNfaBb3oCLavp0iZVTs6tkfnWcv1O82Lg8bESTEpGHbm092
TWITTER_ACCESS_TOKEN=1971705917587820544-S3KBdRzah9Y2jz0YXc9ZUv43mcS2Ws
TWITTER_ACCESS_SECRET=rHxy1ZfQxHoRktLnzGkd8bjfTWHVbg0Yrv9KFenKWzoJl

# ===== LINKEDIN =====
LINKEDIN_ACCESS_TOKEN=YOUR_LINKEDIN_TOKEN
LINKEDIN_PERSON_URN=YOUR_LINKEDIN_URN

# ===== INSTAGRAM =====
IG_USER_ID=1077849398753613
IG_PAGE_ACCESS_TOKEN=1693351238518696|AZ0-uERN5vIFm7oytGSCug6Zlx8

# ===== FACEBOOK =====
FB_PAGE_ID=61590010037059
FB_PAGE_ACCESS_TOKEN=1693351238518696|AZ0-uERN5vIFm7oytGSCug6Zlx8

# ===== YOUTUBE =====
YOUTUBE_CLIENT_ID=YOUR_YT_CLIENT_ID
YOUTUBE_CLIENT_SECRET=YOUR_YT_CLIENT_SECRET
YOUTUBE_REFRESH_TOKEN=YOUR_YT_REFRESH_TOKEN

# ===== TELEGRAM =====
TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_TOKEN
TELEGRAM_CHAT_ID=YOUR_TELEGRAM_CHAT_ID

# ===== ARTICLE CONFIG =====
CANONICAL_URL=https://quantam101.github.io/content
ARTICLE_TOPIC=Best AI Tools for Passive Income in 2026
EOF

# Copy to active .env (used by scripts)
cp /home/ubuntu/profitenginev5/.env.production /home/ubuntu/profitenginev5/.env
chmod 600 /home/ubuntu/profitenginev5/.env
echo "  ✅ Credentials configured"

# Step 5: Create execution script
echo "[5/8] Creating video generation script..."
cat > /home/ubuntu/profitenginev5/run_video_generation.sh << 'EOF'
#!/bin/bash
# OCI Video Generation Runner
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"
source venv/bin/activate
source .env

# Run video generation
python3 scripts/oci_generate_and_post.py

# Log timestamp
echo "[$(date -u +'%Y-%m-%d %H:%M:%S UTC')] Video generation cycle completed" >> /home/ubuntu/video_generation.log
EOF

chmod +x /home/ubuntu/profitenginev5/run_video_generation.sh
echo "  ✅ Execution script ready"

# Step 6: Setup directories
echo "[6/8] Setting up directories..."
mkdir -p /home/ubuntu/profitenginev5/datacenter/video_pipeline/{raw_clips,audio_tracks,subtitles,distribution_masters}
echo "  ✅ Video directories created"

# Step 7: Configure cron job
echo "[7/8] Configuring automated schedule..."
CRON_CMD="/home/ubuntu/profitenginev5/run_video_generation.sh >> /home/ubuntu/video_generation.log 2>&1"

# Remove existing entry if present
(crontab -l 2>/dev/null | grep -v "run_video_generation" || true) | crontab -

# Add new cron jobs - run every 10 minutes
(crontab -l 2>/dev/null || echo "") | {
  cat
  echo ""
  echo "# ProfitEngine Video Generation - Every 10 minutes"
  echo "*/10 * * * * $CRON_CMD"
  echo ""
  echo "# Alternative: Run twice daily at 07:15 and 19:15 UTC"
  echo "# 15 7,19 * * * $CRON_CMD"
} | crontab -

echo "  ✅ Cron job scheduled (every 10 minutes)"

# Step 8: Initialize logging
echo "[8/8] Initializing logging..."
touch /home/ubuntu/video_generation.log
chmod 644 /home/ubuntu/video_generation.log
echo "[$(date -u +'%Y-%m-%d %H:%M:%S UTC')] ===== OCI HYBRID SYSTEM INITIALIZED =====" >> /home/ubuntu/video_generation.log
echo "  ✅ Logging initialized"

echo ""
echo "=========================================="
echo "✅ SETUP COMPLETE!"
echo "=========================================="
echo ""
echo "📊 System Status:"
echo "   Repo: /home/ubuntu/profitenginev5"
echo "   Config: .env (production credentials)"
echo "   Execution: run_video_generation.sh"
echo "   Schedule: Every 10 minutes (cron)"
echo "   Logs: /home/ubuntu/video_generation.log"
echo ""
echo "🚀 Next Steps:"
echo "   1. Edit .env with your actual tokens"
echo "      nano /home/ubuntu/profitenginev5/.env"
echo ""
echo "   2. Test video generation (manual run):"
echo "      cd /home/ubuntu/profitenginev5"
echo "      source venv/bin/activate"
echo "      source .env"
echo "      python3 scripts/oci_generate_and_post.py"
echo ""
echo "   3. Monitor logs:"
echo "      tail -f /home/ubuntu/video_generation.log"
echo ""
echo "📅 Daily Workflow:"
echo "   07:05 UTC: GitHub Actions publishes article"
echo "   07:15 UTC: OCI cron generates video & posts"
echo "   (repeats every 10 min)"
echo ""
echo "=========================================="
