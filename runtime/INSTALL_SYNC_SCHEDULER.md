# Installing the ProfitEngine v5 Sync Scheduler

This guide covers installing and configuring the daily sync job to run automatically.

## Quick Start

Choose one method below:

1. **Linux/macOS (cron)** — Simple, widely available
2. **Linux (systemd)** — Recommended for modern systems
3. **Docker** — Container-based scheduling
4. **GitHub Actions** — Cloud-based (no server needed)

---

## Method 1: Cron (Linux/macOS)

### Installation

1. Copy the sync script to your server:

```bash
scp runtime/profitenginev5_sync_daily.py opc@129.146.167.73:/opt/profitengine/runtime/
chmod +x /opt/profitengine/runtime/profitenginev5_sync_daily.py
```

2. Open crontab editor:

```bash
crontab -e
```

3. Add this line (runs at 5 PM MST every day):

```cron
# ProfitEngine v5 Daily Sync — 5 PM MST (12 AM UTC)
0 0 * * * cd /opt/profitengine && /usr/bin/python3 runtime/profitenginev5_sync_daily.py >> /var/log/profitenginev5-sync.log 2>&1
```

4. Verify cron job was added:

```bash
crontab -l | grep profitenginev5
```

5. View logs:

```bash
tail -f /var/log/profitenginev5-sync.log
```

### Cron Time Conversions

**5 PM MST:**
- Standard Time (Nov-Mar): `0 0 * * *` (12 AM UTC next day)
- Daylight Time (Mar-Nov): `1 0 * * *` (1 AM UTC next day)

**Or use UTC directly:** `0 0 * * * *` runs at midnight UTC (= 5-6 PM previous day MST depending on DST)

If you want it to run at exactly 5 PM MST year-round, use:

```cron
# Run at 5 PM MST every day (accounts for DST automatically)
0 0 * * * cd /opt/profitengine && /usr/bin/python3 runtime/profitenginev5_sync_daily.py
```

### Log Rotation

Add to `/etc/logrotate.d/profitenginev5`:

```
/var/log/profitenginev5-sync.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 profitengine profitengine
    sharedscripts
}
```

---

## Method 2: systemd (Linux - Recommended)

### Installation

1. Copy files to server:

```bash
scp runtime/profitenginev5-sync.service opc@129.146.167.73:/etc/systemd/system/
scp runtime/profitenginev5-sync.timer opc@129.146.167.73:/etc/systemd/system/
scp runtime/profitenginev5_sync_daily.py opc@129.146.167.73:/opt/profitengine/runtime/
```

2. Create profitengine user (if not exists):

```bash
sudo useradd -r -s /bin/bash -d /opt/profitengine profitengine
```

3. Set proper permissions:

```bash
sudo chown -R profitengine:profitengine /opt/profitengine
sudo chmod +x /opt/profitengine/runtime/profitenginev5_sync_daily.py
```

4. Reload systemd and enable timer:

```bash
sudo systemctl daemon-reload
sudo systemctl enable profitenginev5-sync.timer
sudo systemctl start profitenginev5-sync.timer
```

5. Verify it's active:

```bash
sudo systemctl status profitenginev5-sync.timer
sudo systemctl list-timers profitenginev5-sync.timer
```

### Monitor Logs

```bash
# Show recent logs
journalctl -u profitenginev5-sync.service -n 50

# Follow logs in real-time
journalctl -u profitenginev5-sync.service -f

# Show all logs for today
journalctl -u profitenginev5-sync.service --since today
```

### Troubleshooting

Check if timer is running:

```bash
systemctl status profitenginev5-sync.timer
```

View when the next execution is scheduled:

```bash
systemctl list-timers profitenginev5-sync
```

Manually trigger the sync (for testing):

```bash
sudo systemctl start profitenginev5-sync.service
```

Disable the timer:

```bash
sudo systemctl stop profitenginev5-sync.timer
sudo systemctl disable profitenginev5-sync.timer
```

---

## Method 3: Docker

### Using docker-compose

Add to your `docker-compose.yml`:

```yaml
profitenginev5-sync:
  image: python:3.11-slim
  working_dir: /app
  volumes:
    - ./:/app
    - /tmp/profitenginev5:/tmp/profitenginev5
  environment:
    - PROFITENGINEV5_REPO_URL=https://github.com/quantam101/profitenginev5.git
    - PROFITENGINEV5_LOCAL_PATH=/tmp/profitenginev5
    - GITHUB_PROFITENGINEV5_TOKEN=${GITHUB_PROFITENGINEV5_TOKEN}
    - GITHUB_PROFITENGINEV5_USER=profitengine-sync
    - GITHUB_PROFITENGINEV5_EMAIL=sync@profitengine.local
  command: |
    sh -c "
    pip install httpx &&
    python runtime/profitenginev5_sync_daily.py
    "
  restart: "no"
```

Then schedule it with a separate scheduler container or your host's cron:

```bash
# Run via cron
0 0 * * * docker compose -f /path/to/docker-compose.yml run --rm profitenginev5-sync
```

### Using docker run directly

```bash
docker run --rm \
  -v "$(pwd):/app" \
  -v "/tmp/profitenginev5:/tmp/profitenginev5" \
  -e "GITHUB_PROFITENGINEV5_TOKEN=$GITHUB_PROFITENGINEV5_TOKEN" \
  -e "PROFITENGINEV5_REPO_URL=https://github.com/quantam101/profitenginev5.git" \
  python:3.11-slim \
  bash -c "pip install httpx && python /app/runtime/profitenginev5_sync_daily.py"
```

---

## Method 4: GitHub Actions (Cloud-Based - No Server Needed)

Create `.github/workflows/profitenginev5-sync.yml`:

```yaml
name: ProfitEngine v5 Daily Sync

on:
  schedule:
    # Run daily at 5 PM MST (12 AM UTC)
    - cron: '0 0 * * *'
  workflow_dispatch:  # Allow manual trigger

jobs:
  sync:
    runs-on: ubuntu-latest
    name: Sync trading data to profitenginev5

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install httpx

      - name: Get daily metrics
        id: metrics
        run: |
          # TODO: Replace with actual metrics fetch
          echo "pnl_dollars=0" >> $GITHUB_OUTPUT
          echo "win_rate=0" >> $GITHUB_OUTPUT
          echo "trades_count=0" >> $GITHUB_OUTPUT
          echo "customer_count=0" >> $GITHUB_OUTPUT
          echo "revenue_dollars=0" >> $GITHUB_OUTPUT

      - name: Run sync
        env:
          PROFITENGINEV5_REPO_URL: https://github.com/quantam101/profitenginev5.git
          GITHUB_PROFITENGINEV5_TOKEN: ${{ secrets.GITHUB_PROFITENGINEV5_TOKEN }}
          GITHUB_PROFITENGINEV5_USER: github-actions[bot]
          GITHUB_PROFITENGINEV5_EMAIL: 41898282+github-actions[bot]@users.noreply.github.com
        run: |
          python runtime/profitenginev5_sync_daily.py

      - name: Notify on failure
        if: failure()
        uses: actions/github-script@v6
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '❌ ProfitEngine v5 sync failed. Check workflow logs.'
            })
```

Then add `GITHUB_PROFITENGINEV5_TOKEN` to repository secrets:

1. Go to Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `GITHUB_PROFITENGINEV5_TOKEN`
4. Value: Your GitHub PAT
5. Click "Add secret"

**Pros:** No server needed, free tier available
**Cons:** Less control, GitHub rate limits apply

---

## Configuration Files

### Environment Variables

Create `/opt/profitengine/.env.sync` (or add to `.env`):

```bash
# Git & GitHub
PROFITENGINEV5_REPO_URL=https://github.com/quantam101/profitenginev5.git
PROFITENGINEV5_LOCAL_PATH=/tmp/profitenginev5
PROFITENGINEV5_BRANCH=main

# GitHub authentication
GITHUB_PROFITENGINEV5_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
GITHUB_PROFITENGINEV5_USER=profitengine-sync
GITHUB_PROFITENGINEV5_EMAIL=sync@profitengine.local

# Logging
PROFITENGINEV5_SYNC_LOG_FILE=/var/log/profitenginev5-sync.log
```

### Service User Setup

Create a dedicated user with minimal permissions:

```bash
# Create user
sudo useradd -r -s /bin/bash -d /opt/profitengine profitengine

# Add to sudoers for systemd (optional)
echo "profitengine ALL=(ALL) NOPASSWD: /usr/bin/systemctl" | sudo tee -a /etc/sudoers.d/profitengine

# Set up SSH key for GitHub (if using SSH instead of HTTPS)
sudo -u profitengine ssh-keygen -t ed25519 -f /opt/profitengine/.ssh/id_ed25519 -N ""
```

---

## Testing

### Test the sync manually:

```bash
# Using Python directly
python3 /opt/profitengine/runtime/profitenginev5_sync_daily.py

# Using systemd
sudo systemctl start profitenginev5-sync.service

# Check status
sudo systemctl status profitenginev5-sync.service

# View output
journalctl -u profitenginev5-sync.service -n 100
```

### Expected output:

```
2026-06-18 17:00:00 [INFO] ======================================================================
2026-06-18 17:00:00 [INFO] ProfitEngine v5 Daily Sync Started
2026-06-18 17:00:00 [INFO] ======================================================================
2026-06-18 17:00:00 [INFO] Sync engine initialized successfully
2026-06-18 17:00:00 [INFO] Fetching daily metrics from trading system...
2026-06-18 17:00:01 [INFO] Synced daily metrics
2026-06-18 17:00:02 [INFO] Total items synced: 1
2026-06-18 17:00:03 [INFO] Daily sync completed successfully in 3.2s
2026-06-18 17:00:03 [INFO] ======================================================================
```

---

## Verification

After setup, verify the sync is working:

1. **Check timer status** (systemd only):

```bash
systemctl list-timers profitenginev5-sync
```

2. **Wait for next scheduled run and check logs:**

```bash
journalctl -u profitenginev5-sync.service --since "1 hour ago"
```

3. **Verify commits in profitenginev5 repo:**

```bash
git -C /tmp/profitenginev5 log --oneline -5
```

4. **Check GitHub repo directly:**

```bash
curl -s https://api.github.com/repos/quantam101/profitenginev5/commits?per_page=3 \
  | jq '.[] | {message: .commit.message, author: .commit.author.name}'
```

---

## Maintenance

### Monitor Sync Health

Create a health check script `/opt/profitengine/health_check_sync.sh`:

```bash
#!/bin/bash
# Check if sync ran in the last 25 hours

LAST_SYNC=$(find /tmp/profitenginev5 -type f -name ".git" -newer /proc -printf '%TY-%Tm-%Td %TH:%TM' 2>/dev/null)

if [ -z "$LAST_SYNC" ]; then
    echo "ERROR: No sync found in /tmp/profitenginev5"
    exit 1
fi

echo "Last sync: $LAST_SYNC"
exit 0
```

Run daily:

```bash
0 1 * * * /opt/profitengine/health_check_sync.sh >> /var/log/profitenginev5-health.log 2>&1
```

### Update PAT

Token expires every 90 days. Update in:

1. Server `.env` → `GITHUB_PROFITENGINEV5_TOKEN`
2. GitHub Actions secrets → `GITHUB_PROFITENGINEV5_TOKEN`
3. systemd service environment (reload and restart)

### Troubleshoot Common Issues

**"Git command not found"**
```bash
sudo apt-get install -y git  # Ubuntu/Debian
sudo yum install -y git      # CentOS/RHEL
```

**"Permission denied" on /tmp/profitenginev5**
```bash
sudo chown -R profitengine:profitengine /tmp/profitenginev5
sudo chmod 755 /tmp/profitenginev5
```

**"GitHub token invalid"**
- Regenerate PAT at https://github.com/settings/tokens
- Verify token has `repo` scope
- Update server secret and restart service

---

## Next Steps

1. Choose installation method (cron or systemd recommended)
2. Copy files to server
3. Set environment variables
4. Test manually: `python3 profitenginev5_sync_daily.py`
5. Enable scheduler
6. Monitor logs for first few runs
7. Set up log rotation
8. Configure monitoring/alerting

For questions, see `PROFITENGINEV5_SYNC_README.md`.
