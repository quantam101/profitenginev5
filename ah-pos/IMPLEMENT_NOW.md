# Implement AH-POS Daily Sync NOW (Bypass GitHub)

**Status:** GitHub Actions blocked by billing. AH-POS code is complete.  
**Solution:** Run on OCI server via cron (15 minutes, $0)

---

## Quick Start (3 Steps)

### Step 1: Copy Setup Script to Your Machine
```bash
# The script SETUP_OCI_CRON.sh is already in ah-pos/
# It will SSH to your OCI server and set everything up
```

### Step 2: Run the Setup Script
```bash
cd ah-pos
bash SETUP_OCI_CRON.sh
```

What it does:
- ✅ Copies code to OCI ($AH_POS_HOST)
- ✅ Creates daily sync script
- ✅ Installs Python dependencies
- ✅ Sets up 3 cron jobs (06:00, 12:00, 18:00 UTC)
- ✅ Tests the setup
- ✅ Shows you the logs

### Step 3: Verify It's Running
```bash
# SSH to OCI
ssh $AH_POS_USER@$AH_POS_HOST

# Check cron jobs
crontab -l | grep "run-ah-pos-sync"

# Monitor logs
tail -f /var/log/ah-pos/sync-$(date +%Y%m%d).log

# Query database
psql $DATABASE_URL -c "SELECT COUNT(*) FROM solicitations WHERE last_updated > NOW() - INTERVAL '1 hour';"
```

---

## What Happens

| Time (UTC) | Action | Status |
|-----------|--------|--------|
| 06:00 | SAM.gov scraper runs | ✅ Automatic |
| 12:00 | Pricing update runs | ✅ Automatic |
| 18:00 | CPARS refresh runs | ✅ Automatic |
| Daily | Logs recorded | ✅ /var/log/ah-pos/ |

---

## Benefits

✅ **Zero GitHub dependency** — Runs on your server  
✅ **Zero cost** — Uses existing OCI server  
✅ **More reliable** — Your server > GitHub's servers  
✅ **Full control** — You manage the schedule  
✅ **Easy monitoring** — Simple logs on disk  

---

## If You Prefer GitHub (After Fixing Billing)

Once GitHub billing is resolved:

```bash
# GitHub Actions will auto-resume
# (No code changes needed)
```

Both options can run simultaneously if you want redundancy.

---

## Implementation Path

### Option A: OCI Cron Only (Recommended Now)
```bash
bash SETUP_OCI_CRON.sh
# Done. Runs forever without GitHub dependency.
```

### Option B: OCI Cron + GitHub Actions (Future)
```bash
# 1. Fix GitHub billing (5 min)
# 2. Already have OCI as backup (already done)
# GitHub Actions will resume automatically
```

### Option C: Other Alternatives
See `CI_CD_ALTERNATIVES.md` for GitLab CI, CircleCI, AWS Lambda, etc.

---

## Prerequisites

✅ SSH access to $AH_POS_HOST (you have this)  
✅ PostgreSQL database created (instruction below)  
✅ Python 3.11 on OCI (pre-installed on most OCI images)  

### Setup PostgreSQL (If Not Done)

```bash
# SSH to OCI
ssh $AH_POS_USER@$AH_POS_HOST

# Install PostgreSQL (if needed)
sudo yum install -y postgresql-server

# Start service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database
sudo -u postgres psql << EOF
CREATE DATABASE ah_pos;
CREATE ROLE ah_pos_user WITH LOGIN PASSWORD 'your-password';
GRANT ALL PRIVILEGES ON DATABASE ah_pos TO ah_pos_user;
EOF

# Initialize schema
psql -U ah_pos_user -d ah_pos < /path/to/database/00_init_schema.sql
```

---

## Monitoring Commands

```bash
# SSH to OCI
ssh $AH_POS_USER@$AH_POS_HOST

# View today's logs
tail -f /var/log/ah-pos/sync-$(date +%Y%m%d).log

# View all cron jobs
crontab -l

# Check next scheduled runs
crontab -l -n

# Manually trigger sync (for testing)
/home/opc/run-ah-pos-sync.sh

# Query database for recent updates
psql $DATABASE_URL << EOF
SELECT COUNT(*) as new_opportunities 
FROM solicitations 
WHERE last_updated > NOW() - INTERVAL '1 hour';
EOF
```

---

## Troubleshooting

### Cron not running
```bash
# Check cron daemon
sudo systemctl status cron

# Restart if needed
sudo systemctl restart cron
```

### Python dependencies missing
```bash
# SSH to OCI and reinstall
ssh $AH_POS_USER@$AH_POS_HOST
cd /home/opc/profitenginev5/ah-pos
python -m pip install -r requirements.txt
```

### Database connection failed
```bash
# Check DATABASE_URL environment variable
echo $DATABASE_URL

# Or set it manually
export DATABASE_URL="postgresql://user:pass@localhost:5432/ah_pos"
```

### Logs not appearing
```bash
# Check log directory exists
ls -la /var/log/ah-pos/

# Check permissions
sudo chown opc:opc /var/log/ah-pos
```

---

## Success Indicators

✅ Cron jobs listed: `crontab -l | grep "run-ah-pos-sync"`  
✅ Log file exists: `ls /var/log/ah-pos/sync-*.log`  
✅ Database updated: `SELECT COUNT(*) FROM solicitations WHERE last_updated > NOW() - INTERVAL '1 hour'` returns > 0  
✅ No error messages in logs  

---

## Next: Import Your Data

Once OCI Cron is running:

```bash
# Import your past performance contracts
python backend/ingest_past_performance.py --file your_contracts.csv

# Generate proposals
python backend/proposal_generator.py --opportunity_id 123
```

---

## Timeline

| Step | Time | Cumulative |
|------|------|-----------|
| Copy script | 1 min | 1 min |
| Run setup | 5 min | 6 min |
| Set DATABASE_URL | 2 min | 8 min |
| Verify cron | 2 min | 10 min |
| Test sync | 3 min | 13 min |
| **Total** | — | **15 minutes** |

---

## Final Notes

- **GitHub Actions will remain blocked** until billing is fixed (not our concern)
- **OCI Cron works independently** (no GitHub dependency)
- **Code is correct** (already deployed, just needs execution)
- **You can test locally anytime:** `docker-compose up -d`

---

## Ready?

```bash
cd ah-pos
bash SETUP_OCI_CRON.sh
```

✅ AH-POS will run automatically, 3x daily, without any GitHub dependency.
