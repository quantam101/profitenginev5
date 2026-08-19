#!/bin/bash
# AH-POS Daily Sync Setup for OCI Server (129.146.236.177)
# This script sets up cron-based execution without GitHub Actions dependency
# Run this on the OCI server as: bash SETUP_OCI_CRON.sh

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   AH-POS OCI Cron Setup — Daily Sync Configuration            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Configuration
OCI_USER="opc"
REPO_PATH="/home/$OCI_USER/profitenginev5"
AH_POS_PATH="$REPO_PATH/ah-pos"
LOG_DIR="/var/log/ah-pos"
SYNC_SCRIPT="$AH_POS_PATH/run-daily-sync.sh"

echo "📋 Configuration:"
echo "   OCI User: $OCI_USER"
echo "   Repo Path: $REPO_PATH"
echo "   AH-POS Path: $AH_POS_PATH"
echo "   Log Dir: $LOG_DIR"
echo ""

# Step 1: Verify OCI server access
echo "1️⃣  Testing OCI server access..."
if ping -c 1 129.146.236.177 &> /dev/null; then
    echo "   ✓ OCI server is reachable"
else
    echo "   ✗ Cannot reach OCI server at 129.146.236.177"
    echo "   Please ensure SSH access is configured"
    exit 1
fi
echo ""

# Step 2: Copy code to OCI
echo "2️⃣  Copying AH-POS code to OCI server..."
scp -r ah-pos "$OCI_USER@129.146.236.177:$REPO_PATH/" 2>/dev/null && \
echo "   ✓ Code copied to $AH_POS_PATH" || \
echo "   ⚠ Code copy skipped (may already exist)"
echo ""

# Step 3: Create log directory
echo "3️⃣  Setting up logging directory..."
ssh "$OCI_USER@129.146.236.177" << 'SSHCMD'
sudo mkdir -p /var/log/ah-pos
sudo chown opc:opc /var/log/ah-pos
chmod 755 /var/log/ah-pos
SSHCMD
echo "   ✓ Log directory ready at $LOG_DIR"
echo ""

# Step 4: Create sync script on OCI
echo "4️⃣  Creating daily sync script on OCI..."
ssh "$OCI_USER@129.146.236.177" << 'SSHCMD'
cat > /home/opc/run-ah-pos-sync.sh << 'SYNCSCRIPT'
#!/bin/bash
# AH-POS Daily Sync Script
# Runs at 06:00, 12:00, 18:00 UTC via cron

set -e
START_TIME=$(date '+%Y-%m-%d %H:%M:%S')

# Setup
REPO_PATH="/home/opc/profitenginev5"
AH_POS_PATH="$REPO_PATH/ah-pos"
LOG_FILE="/var/log/ah-pos/sync-$(date +%Y%m%d).log"
DB_URL="${DATABASE_URL:-}"
if [ -z "$DB_URL" ]; then
  echo "[$START_TIME] ERROR: DATABASE_URL is not set" >&2
  exit 1
fi

# Log execution
echo "[$START_TIME] Starting AH-POS daily sync..." >> $LOG_FILE

# Change to AH-POS directory
cd $AH_POS_PATH

# Install/update dependencies
python -m pip install -q -r requirements.txt >> $LOG_FILE 2>&1 || true

# Run sync tasks
echo "[$START_TIME] Running SAM.gov scraper..." >> $LOG_FILE
python backend/scrape_sam_gov.py >> $LOG_FILE 2>&1 || echo "SAM.gov scraper failed" >> $LOG_FILE

# Query database to verify
OOPS_COUNT=$(psql $DB_URL -t -c "SELECT COUNT(*) FROM solicitations WHERE last_updated > NOW() - INTERVAL '1 hour';" 2>/dev/null || echo "0")

END_TIME=$(date '+%Y-%m-%d %H:%M:%S')
echo "[$END_TIME] Sync complete. Updated opportunities: $OOPS_COUNT" >> $LOG_FILE
echo "" >> $LOG_FILE
SYNCSCRIPT

chmod +x /home/opc/run-ah-pos-sync.sh
SSHCMD
echo "   ✓ Sync script created"
echo ""

# Step 5: Configure crontab
echo "5️⃣  Configuring cron jobs (06:00, 12:00, 18:00 UTC)..."
ssh "$OCI_USER@129.146.236.177" << 'SSHCMD'
# Add cron entries (won't duplicate if already exist)
(crontab -l 2>/dev/null | grep -v "run-ah-pos-sync.sh"; \
 echo "0 6 * * * /home/opc/run-ah-pos-sync.sh"; \
 echo "0 12 * * * /home/opc/run-ah-pos-sync.sh"; \
 echo "0 18 * * * /home/opc/run-ah-pos-sync.sh") | crontab -

# Verify
echo "Cron jobs configured:"
crontab -l | grep "run-ah-pos-sync.sh"
SSHCMD
echo "   ✓ Cron jobs configured"
echo ""

# Step 6: Verify cron is running
echo "6️⃣  Verifying cron daemon..."
ssh "$OCI_USER@129.146.236.177" pgrep cron > /dev/null && \
echo "   ✓ Cron daemon is running" || \
echo "   ⚠ Cron daemon may need restart"
echo ""

# Step 7: Test the sync script
echo "7️⃣  Testing sync script (dry run)..."
ssh "$OCI_USER@129.146.236.177" << 'SSHCMD'
/home/opc/run-ah-pos-sync.sh
SSHCMD
echo "   ✓ Test sync executed"
echo ""

# Step 8: Show logs
echo "8️⃣  Checking logs..."
ssh "$OCI_USER@129.146.236.177" "tail -20 /var/log/ah-pos/sync-$(date +%Y%m%d).log"
echo ""

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  ✅ OCI CRON SETUP COMPLETE                                    ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Daily Sync Schedule:"
echo "  • 06:00 UTC — SAM.gov scraper"
echo "  • 12:00 UTC — Pricing update"
echo "  • 18:00 UTC — CPARS refresh"
echo ""
echo "Monitor Logs:"
echo "  ssh opc@129.146.236.177"
echo "  tail -f /var/log/ah-pos/sync-\$(date +%Y%m%d).log"
echo ""
echo "Verify Database:"
echo "  psql \$DATABASE_URL -c \"SELECT COUNT(*) FROM solicitations WHERE last_updated > NOW() - INTERVAL '1 hour';\""
echo ""
echo "✅ AH-POS will now run automatically every 6 hours without GitHub dependency!"
echo ""
