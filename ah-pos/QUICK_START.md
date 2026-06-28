# AH-POS Quick Start

## Local Testing (5 minutes)

```bash
cd ah-pos

# Start PostgreSQL + backend
docker-compose up -d

# Wait for postgres
docker-compose logs postgres | grep "ready to accept"

# Import sample data
python backend/ingest_past_performance.py --file data/sample_past_performance.csv

# Run SAM.gov scraper
python backend/scrape_sam_gov.py

# Query results
psql postgresql://ah_pos_user:dev_password_change_in_production@localhost:5432/ah_pos << EOF
SELECT COUNT(*) FROM solicitations;
SELECT COUNT(*) FROM high_priority_opportunities;
EOF

# Stop services
docker-compose down
```

## Production Setup (30 minutes)

### Step 1: Create Database
```bash
# OCI Always Free tier (recommended)
# Or AWS RDS t3.micro
# Or self-hosted PostgreSQL on OCI Compute

# Initialize schema
psql -h your-db-host -U admin -d postgres < database/00_init_schema.sql
```

### Step 2: Configure GitHub Secrets
```bash
# Set database connection
gh secret set AH_POS_DATABASE_URL \
  --body "postgresql://user:pass@host:5432/ah_pos"

# Set Slack webhook (optional)
gh secret set SLACK_WEBHOOK_URL \
  --body "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

### Step 3: Deploy
```bash
# Commit and push
git add ah-pos/
git commit -m "feat: Add AH-POS federal contracting platform"
git push origin main

# GitHub Actions auto-runs:
# - Database initialization
# - First SAM.gov sync (daily at 06:00 UTC)
# - Pricing update (daily at 12:00 UTC)
# - CPARS refresh (daily at 18:00 UTC)
```

### Step 4: Verify
```bash
# Check workflow status
gh workflow run daily-sync.yml
gh run watch

# Query database
psql $DATABASE_URL << EOF
SELECT COUNT(*) FROM past_performance_contracts;
SELECT COUNT(*) FROM high_priority_opportunities;
EOF
```

## Daily Operations

```bash
# Morning check
psql $DATABASE_URL << EOF
SELECT COUNT(*) as new_opportunities FROM solicitations 
WHERE first_seen_date > NOW() - INTERVAL '24 hours';

SELECT COUNT(*) as high_priority FROM high_priority_opportunities 
WHERE status = 'open';
EOF

# Import your past performance
python backend/ingest_past_performance.py --file your_contracts.csv

# Generate proposal draft (future)
python -c "from proposal_generator import ProposalGenerator; ..."
```

## Database Queries

### High-Priority Opportunities
```sql
SELECT solicitation_number, title, opportunity_score, days_to_close
FROM high_priority_opportunities
WHERE status = 'open'
ORDER BY opportunity_score DESC
LIMIT 10;
```

### Past Performance by Agency
```sql
SELECT agency_name, COUNT(*) as contract_count, AVG(quality_rating) as avg_quality
FROM past_performance_contracts
WHERE end_date >= CURRENT_DATE - INTERVAL '10 years'
GROUP BY agency_name
ORDER BY contract_count DESC;
```

### Recompete Alerts
```sql
SELECT contract_number, incumbent_contractor, agency_name, days_to_expiration
FROM recompete_alerts
WHERE days_to_expiration BETWEEN 180 AND 365
ORDER BY days_to_expiration ASC;
```

### Labor Rates
```sql
SELECT category_name, loaded_rate_2026, ffp_rate, tm_rate, idiq_rate
FROM labor_categories
WHERE loaded_rate_2026 IS NOT NULL
LIMIT 20;
```

## Troubleshooting

### Docker won't start
```bash
docker-compose logs postgres
# Check for port conflicts (5432, 5050)
```

### Database connection failed
```bash
# Test connection
psql $DATABASE_URL -c "SELECT 1"

# Check DATABASE_URL format
echo $AH_POS_DATABASE_URL
```

### SAM.gov API rate limited
```bash
# Script includes backoff
# If persistent, increase delay in scrape_sam_gov.py:
# TIME_BETWEEN_REQUESTS = 0.1 → 0.2 seconds
```

### GitHub Actions failed
```bash
gh run view -R already-here-llc/ah-pos --log
# Check secrets: gh secret list
```

## Files Overview

| File | Purpose | Size |
|------|---------|------|
| `database/00_init_schema.sql` | PostgreSQL schema (16 tables, 40 indexes) | 18 KB |
| `backend/models.py` | SQLAlchemy ORM + Pydantic | 20 KB |
| `backend/ingest_past_performance.py` | CSV import (idempotent) | 11 KB |
| `backend/scrape_sam_gov.py` | SAM.gov scraper (daily) | 14 KB |
| `.github/workflows/daily-sync.yml` | GitHub Actions automation | 9 KB |
| `docker-compose.yml` | Local development | 1.2 KB |
| `Dockerfile` | Production container | 0.5 KB |
| `README.md` | Quick start (394 lines) | 9 KB |
| `DEPLOYMENT_GUIDE.md` | Production setup (500 lines) | 16 KB |
| `BUILD_COMPLETE.md` | Feature overview (511 lines) | 17 KB |

**Total: ~115 KB, ~5,500 lines of code + documentation**

## Cost Analysis

| Component | Monthly Cost |
|-----------|--------------|
| PostgreSQL (OCI Always Free) | $0 |
| GitHub Actions (free tier) | $0 |
| Object storage (backups) | $1-2 |
| **Total** | **$1-2/month** |

## Support

- **Docs:** README.md, DEPLOYMENT_GUIDE.md, BUILD_COMPLETE.md
- **Issues:** Check DEPLOYMENT_GUIDE.md § Troubleshooting
- **Help:** dispatch@alreadyherellc.com

---

✅ **Ready to deploy!**
