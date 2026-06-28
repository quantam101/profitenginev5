# AH-POS Deployment Guide

Complete step-by-step instructions for deploying AH-POS to production on OCI or AWS.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Database Setup](#database-setup)
3. [GitHub Actions Configuration](#github-actions-configuration)
4. [Initial Data Import](#initial-data-import)
5. [Verification & Smoke Tests](#verification--smoke-tests)
6. [Monitoring & Operations](#monitoring--operations)

---

## Prerequisites

### Required
- [ ] PostgreSQL 14+ access (managed service or self-hosted on OCI)
- [ ] GitHub repository access with Actions enabled
- [ ] Python 3.11 runtime (for local testing)
- [ ] SSH access to OCI server (optional, if self-hosting)

### Recommended
- [ ] Slack workspace for notifications
- [ ] Email configured for alerts
- [ ] CloudWatch or equivalent monitoring

---

## Database Setup

### Step 1: Create PostgreSQL Database

#### Option A: OCI Always Free Tier (Recommended)
```bash
# If using OCI Database MySQL HeatWave (best free option):
# Use OCI Console → MySQL HeatWave → Create DB System

# Or use self-hosted PostgreSQL on OCI Compute:
ssh opc@129.146.236.177

# Install PostgreSQL
sudo yum install -y postgresql-server
sudo /usr/pgsql-14/bin/postgresql-14-setup initdb
sudo systemctl start postgresql-14
sudo systemctl enable postgresql-14

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE ah_pos WITH ENCODING 'UTF8';
CREATE ROLE ah_pos_app WITH LOGIN PASSWORD 'GENERATE-STRONG-PASSWORD-HERE';
CREATE ROLE ah_pos_admin WITH LOGIN PASSWORD 'GENERATE-ANOTHER-PASSWORD-HERE';

-- Grant permissions to read-only app role
GRANT CONNECT ON DATABASE ah_pos TO ah_pos_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO ah_pos_app;

-- Grant admin permissions
GRANT ALL PRIVILEGES ON DATABASE ah_pos TO ah_pos_admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ah_pos_admin;
EOF
```

#### Option B: AWS RDS PostgreSQL
```bash
# Via AWS Console:
# 1. RDS → Create Database
# 2. Engine: PostgreSQL 14
# 3. DB instance class: db.t3.micro (free tier eligible)
# 4. Storage: 20GB gp2
# 5. Publicly accessible: Yes (restrict via security group)
# 6. Initial database name: ah_pos
```

### Step 2: Initialize Schema

```bash
# Download schema file
curl -L https://raw.githubusercontent.com/already-here-llc/ah-pos/main/database/00_init_schema.sql -o schema.sql

# Apply schema
psql -h your-db-host -U ah_pos_admin -d ah_pos < schema.sql

# Verify schema created
psql -h your-db-host -U ah_pos_app -d ah_pos << EOF
\dt
-- Should list tables: agencies, solicitations, past_performance_contracts, etc.
EOF
```

### Step 3: Configure Network Access

#### On OCI:
```bash
# Edit security list to allow PostgreSQL from GitHub Actions
ssh opc@129.146.236.177
sudo firewall-cmd --permanent --add-service=postgresql
sudo firewall-cmd --reload
```

#### On AWS:
1. Go to RDS → Databases → ah_pos
2. Under "Connectivity & security" → "VPC security groups"
3. Edit security group: Inbound Rules
4. Add: Type=PostgreSQL, Source=Anywhere (or restrict to GitHub Actions IP range)

---

## GitHub Actions Configuration

### Step 1: Create GitHub Secrets

```bash
# Set database connection URL
gh secret set AH_POS_DATABASE_URL \
  --repo already-here-llc/ah-pos \
  --body "postgresql://ah_pos_admin:PASSWORD@your-db-host:5432/ah_pos"

# Set Slack webhook for notifications (optional)
gh secret set SLACK_WEBHOOK_URL \
  --repo already-here-llc/ah-pos \
  --body "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# Verify secrets are set
gh secret list --repo already-here-llc/ah-pos
```

### Step 2: Enable GitHub Actions

```bash
# Ensure Actions are enabled in repository
gh repo view already-here-llc/ah-pos --json defaultBranchRef

# Check workflow file is accessible
gh workflow list --repo already-here-llc/ah-pos
# Should show: daily-sync.yml    active    schedule
```

### Step 3: Test Workflow Manually

```bash
# Trigger daily sync workflow
gh workflow run daily-sync.yml --repo already-here-llc/ah-pos

# Monitor run in real-time
gh run list --repo already-here-llc/ah-pos --workflow=daily-sync.yml

# View logs of last run
gh run view -R already-here-llc/ah-pos --log
```

---

## Initial Data Import

### Step 1: Prepare Past Performance CSV

**Create** `ah-pos/data/past_performance.csv` with your completed contracts:

```csv
contract_id,contract_number,agency_name,naics_code,psc_code,contract_type,award_date,start_date,end_date,total_contract_value,amount_spent,on_time_percent,cost_variance_percent,quality_rating,customer_poc_name,customer_poc_email,ordering_officer_name,executive_summary
YOUR-2024-001,GSA-XXXX,General Services Administration,541611,7030,FFP,2023-01-15,2023-02-01,2024-01-31,500000,495000,98,2,4.5,John Smith,john@gsa.gov,Jane Doe,"Your executive summary here..."
```

### Step 2: Commit and Push

```bash
# From project root
cd ah-pos
git add data/past_performance.csv
git commit -m "data: Initialize past performance database"
git push origin main
```

This automatically triggers:
- GitHub Actions: database initialization
- Initial data import
- First SAM.gov sync

### Step 3: Verify Import

```bash
# Query imported contracts
psql -h your-db-host -U ah_pos_app -d ah_pos << EOF
SELECT COUNT(*) as total_contracts FROM past_performance_contracts;
-- Should show: 10+ (from sample data)
EOF
```

---

## Verification & Smoke Tests

### Test 1: Database Connectivity

```bash
psql -h your-db-host -U ah_pos_app -d ah_pos -c \
  "SELECT version();"
# Should return PostgreSQL version string
```

### Test 2: Daily Sync Execution

```bash
# Manually trigger workflow
gh workflow run daily-sync.yml --repo already-here-llc/ah-pos

# Wait ~2-3 minutes, then verify data was imported
psql -h your-db-host -U ah_pos_app -d ah_pos << EOF
SELECT COUNT(*) as new_solicitations 
FROM solicitations 
WHERE first_seen_date > NOW() - INTERVAL '1 hour';
-- Should show: > 0
EOF
```

### Test 3: Opportunity Scoring

```bash
psql -h your-db-host -U ah_pos_app -d ah_pos << EOF
SELECT 
  solicitation_number,
  title,
  opportunity_score,
  days_to_close
FROM high_priority_opportunities
WHERE opportunity_score >= 70
LIMIT 5;
EOF
```

### Test 4: Alert Generation

```bash
psql -h your-db-host -U ah_pos_app -d ah_pos << EOF
SELECT 
  alert_type,
  severity,
  title,
  created_at
FROM alerts
WHERE status = 'new'
LIMIT 10;
EOF
```

---

## Monitoring & Operations

### Daily Checklist

Run this each morning to verify overnight sync:

```bash
#!/bin/bash
# Save as: ah-pos/scripts/daily_checklist.sh

DB_URL="postgresql://ah_pos_app:PASSWORD@your-db-host:5432/ah_pos"

echo "=== AH-POS Daily Operations Check ==="
echo ""

# 1. Solicitation count
echo "1. Solicitation count:"
psql $DB_URL -c \
  "SELECT COUNT(*) as total FROM solicitations; \
   SELECT COUNT(*) as updated_24h FROM solicitations \
   WHERE last_updated > NOW() - INTERVAL '24 hours';"

# 2. High-priority opportunities
echo ""
echo "2. High-priority opportunities (score >= 75):"
psql $DB_URL -c \
  "SELECT COUNT(*) FROM solicitations \
   WHERE status = 'open' \
   AND relevance_score * 0.35 + timeline_score * 0.30 + agency_fit_score * 0.25 >= 75;"

# 3. New alerts
echo ""
echo "3. New alerts (unacknowledged):"
psql $DB_URL -c \
  "SELECT alert_type, COUNT(*) as count FROM alerts \
   WHERE status = 'new' GROUP BY alert_type;"

# 4. Past performance records
echo ""
echo "4. Past performance database:"
psql $DB_URL -c \
  "SELECT COUNT(*) as contracts, \
          COUNT(DISTINCT agency_id) as agencies, \
          COUNT(DISTINCT naics_code) as naics_coverage \
   FROM past_performance_contracts;"

# 5. Labor categories (for pricing)
echo ""
echo "5. Labor categories with 2026 rates:"
psql $DB_URL -c \
  "SELECT COUNT(*) as categories FROM labor_categories \
   WHERE loaded_rate_2026 IS NOT NULL;"

# 6. Database health
echo ""
echo "6. Database health:"
psql $DB_URL -c \
  "SELECT pg_size_pretty(pg_database_size('ah_pos')) as database_size;"

echo ""
echo "=== All systems nominal ==="
```

Run:
```bash
bash ah-pos/scripts/daily_checklist.sh
```

### Alert Management

#### Acknowledge an alert
```bash
psql -h your-db-host -U ah_pos_admin -d ah_pos << EOF
UPDATE alerts 
SET status = 'acknowledged', acknowledged_at = NOW(), acknowledged_by = 'ops-team'
WHERE id = 123;
EOF
```

#### Dismiss low-priority alerts
```bash
psql -h your-db-host -U ah_pos_admin -d ah_pos << EOF
UPDATE alerts 
SET status = 'dismissed'
WHERE severity = 'low' AND created_at < NOW() - INTERVAL '7 days';
EOF
```

### Performance Tuning

#### Check for slow queries
```bash
psql -h your-db-host -U ah_pos_admin -d ah_pos << EOF
-- Enable slow query logging
ALTER SYSTEM SET log_min_duration_statement = 5000;  -- 5 seconds
SELECT pg_reload_conf();

-- View slow logs after running sync
SELECT query, mean_exec_time FROM pg_stat_statements 
WHERE mean_exec_time > 5000 
ORDER BY mean_exec_time DESC;
EOF
```

#### Analyze and reindex
```bash
psql -h your-db-host -U ah_pos_admin -d ah_pos << EOF
ANALYZE;
REINDEX DATABASE ah_pos;
VACUUM FULL;
EOF
```

### Backup & Recovery

#### Daily backup to S3
```bash
# Add to cron (OCI server):
0 23 * * * pg_dump -Fc postgresql://ah_pos_admin@localhost/ah_pos \
  | aws s3 cp - s3://your-backup-bucket/ah-pos/$(date +\%Y\%m\%d).backup

# Test restore:
pg_restore -d ah_pos_test /path/to/backup.sql
```

#### Emergency recovery
```bash
# If database corrupted, restore from backup
pg_restore -Fc -c -d ah_pos /path/to/latest.backup

# Verify past performance integrity (immutable records)
SELECT COUNT(*) FROM past_performance_contracts;
```

---

## Troubleshooting

### GitHub Actions Workflow Fails

**Symptom:** Workflow shows red X in GitHub

**Steps:**
1. View workflow run: `gh run view -R already-here-llc/ah-pos --log`
2. Check secrets are set: `gh secret list --repo already-here-llc/ah-pos`
3. Verify DATABASE_URL is correct:
   ```bash
   psql $AH_POS_DATABASE_URL -c "SELECT 1;"
   ```
4. Check GitHub Actions logs for error details

### SAM.gov API Rate Limiting

**Symptom:** Workflow timeout or "429 Too Many Requests"

**Solution:** Script includes backoff. If persistent:
```bash
# Increase rate limit delay in scrape_sam_gov.py
# Change: TIME_BETWEEN_REQUESTS = 0.1 → 0.2 (seconds)
```

### Database Connection Pooling

**Symptom:** "too many connections" error

**Solution:**
```bash
# Increase connection limit in PostgreSQL
psql -U postgres -d postgres << EOF
ALTER SYSTEM SET max_connections = 200;
SELECT pg_reload_conf();
EOF
```

### Out of Disk Space

**Symptom:** Database write fails, logs fill up

**Steps:**
```bash
# Check disk usage
df -h /var/lib/postgresql

# Vacuum and analyze
psql -U ah_pos_admin -d ah_pos -c "VACUUM FULL; ANALYZE;"

# Rotate old logs (keep 30 days)
find /var/lib/postgresql/pg_log -name "*.log" -mtime +30 -delete
```

---

## Cutover Checklist

Before going live with daily automated syncs:

- [ ] Database schema initialized and verified
- [ ] Past performance records imported and tested
- [ ] GitHub Actions secrets configured
- [ ] Daily sync workflow tested manually (no errors)
- [ ] Slack webhook notifications tested (optional)
- [ ] Database backups configured and tested
- [ ] Monitoring/alerts configured
- [ ] Team trained on alert acknowledgment process
- [ ] Documentation shared with stakeholders

---

## Post-Launch Monitoring

### Week 1: Daily Oversight
- [ ] Monitor workflow execution every morning
- [ ] Verify data quality (no NULL contract values, etc.)
- [ ] Test alert workflow (manually create test opportunity)
- [ ] Validate scoring algorithm (do high-score opp match past performance?)

### Week 2-4: Operational Handoff
- [ ] Assign alert ownership (who responds to which agencies?)
- [ ] Document any data issues found
- [ ] Fine-tune NAICS codes being monitored
- [ ] Review past performance quality (fill in missing narratives)

### Month 2+: Continuous Improvement
- [ ] Analyze which alerts led to proposals
- [ ] Refine scoring weights based on win/loss data
- [ ] Add new NAICS codes as business expands
- [ ] Archive old solicitations (status = closed/awarded)

---

## Support

**Issue:** Database won't start  
**Solution:** Check logs: `sudo journalctl -u postgresql-14`

**Issue:** GitHub Actions throttled  
**Solution:** Increase rate limits in workflow, or contact GitHub Support

**Issue:** Need to rollback changes  
**Solution:** Restore database from backup, rollback GitHub commit

---

**Deployment Date:** [YYYY-MM-DD]  
**Deployed By:** [Name]  
**Database Host:** [host:port]  
**GitHub Repository:** already-here-llc/ah-pos  
**Production URL:** [If API exposed]

---

For questions: dispatch@alreadyherellc.com
