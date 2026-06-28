# AH-POS: Already Here Point of Sale System
## Federal Contracting Intelligence Platform

Automated system for tracking federal opportunities, past performance, and pricing intelligence. Designed for contractors pursuing GSA Schedule, IDIQ, and FFP federal contracts.

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    SAM.gov / usaspending.gov                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                   GitHub Actions (Daily @ 06:00 UTC)
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
    ┌────▼────┐      ┌──────▼──────┐      ┌────▼──────┐
    │ Capture │      │   Pricing   │      │   CPARS   │
    │ Intel   │      │   Update    │      │  Refresh  │
    └────┬────┘      └──────┬──────┘      └────┬──────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
                   PostgreSQL Database
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
    ┌────▼──────────┐   ┌────▼────────┐   ┌────▼────────────┐
    │ Proposal Gen  │   │  Analytics  │   │  Alerts & Nudge │
    │  (80% draft)  │   │  Dashboard  │   │   Notifications │
    └───────────────┘   └─────────────┘   └─────────────────┘
```

### Core Modules

#### 1. **Past Performance Database**
- Immutable audit trail of completed contracts
- Searchable by agency, NAICS, PSC, contract type
- Performance metrics: on-time %, cost variance, quality rating
- Reference contacts for CPARS verification
- Supports 10-year proposal history lookback

#### 2. **Capture Intelligence**
- **SAM.gov Scraper** — daily fetch of new solicitations
- **Incumbent Tracker** — monitor recompete windows
- **Budget Trends** — agency spending by NAICS (usaspending.gov)
- **Opportunity Scoring** — ML-ready: relevance (35%) + timeline (30%) + agency fit (25%) + incumbent risk (10%)
- **Alert System** — automatic high-priority notifications

#### 3. **Pricing & Wrap-Rate Model**
- GSA Schedule labor category rates
- DCAA indirect cost rates (negotiated & provisional)
- Overhead/G&A allocation by contract type (FFP, T&M, IDIQ)
- Annual COLA adjustments (2024-2026 tracked)
- Cost Analysis (SF 1411) export-ready

#### 4. **Proposal Generator** (Future Phase)
- Auto-populate from past performance database
- Generate 80% complete proposal drafts
- CPARS rating integration
- Risk buffer calculation
- Compliance certification (DCAA audit trail)

---

## Quick Start

### Local Development (Docker)

```bash
# Clone and navigate
git clone https://github.com/already-here-llc/ah-pos.git
cd ah-pos

# Start PostgreSQL + backend services
docker-compose up -d

# Verify database is ready
docker-compose logs postgres

# Import sample past performance
python backend/ingest_past_performance.py

# Run SAM.gov scraper
python backend/scrape_sam_gov.py
```

Check the database:
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U ah_pos_user -d ah_pos

# Query high-priority opportunities
SELECT solicitation_number, title, opportunity_score, days_to_close
FROM high_priority_opportunities
WHERE opportunity_score >= 70
ORDER BY opportunity_score DESC
LIMIT 10;
```

### Production Deployment (OCI Server)

#### Prerequisites
- PostgreSQL 14+ (managed or self-hosted on OCI)
- Python 3.11
- GitHub Actions access for daily cron jobs

#### Step 1: Set Up Database

```bash
# On OCI server or managed database
createdb ah_pos

# Initialize schema
psql -U postgres -d ah_pos < database/00_init_schema.sql

# Create application user (read-only for queries, write for ingestion)
psql -U postgres << EOF
CREATE ROLE ah_pos_app WITH LOGIN PASSWORD 'generate-strong-password';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ah_pos_app;

CREATE ROLE ah_pos_admin WITH LOGIN PASSWORD 'generate-strong-password';
GRANT ALL PRIVILEGES ON DATABASE ah_pos TO ah_pos_admin;
EOF
```

#### Step 2: Configure GitHub Actions Secrets

```bash
gh secret set AH_POS_DATABASE_URL \
  --body "postgresql://ah_pos_admin:password@your-db-host:5432/ah_pos"

gh secret set SLACK_WEBHOOK_URL \
  --body "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"  # Optional
```

#### Step 3: Push to Main Branch

```bash
git add ah-pos/
git commit -m "feat: Add AH-POS federal contracting platform"
git push origin main
```

This triggers:
- Database schema initialization
- Initial data import (if CSV provided)
- First daily sync run at 06:00 UTC

---

## Data Import

### Import Past Performance from CSV

**File format:** `ah-pos/data/past_performance.csv`

```csv
contract_id,contract_number,agency_name,naics_code,psc_code,contract_type,award_date,start_date,end_date,total_contract_value,amount_spent,on_time_percent,cost_variance_percent,quality_rating,customer_poc_name,customer_poc_email,ordering_officer_name,executive_summary
GEN2024001,GSA-2024-001,General Services Administration,541611,7030,FFP,2023-01-15,2023-02-01,2024-01-31,500000,495000,98,2,4.5,John Smith,john.smith@gsa.gov,Jane Doe,"Delivered network infrastructure refresh..."
```

**Import command:**
```bash
python backend/ingest_past_performance.py --file data/past_performance.csv
```

The importer is idempotent — running twice produces identical results. Duplicates are skipped by `contract_id`.

### Bootstrap NAICS & PSC Codes

```bash
python backend/ingest_past_performance.py --bootstrap-naics data/naics_2024.csv
```

---

## Daily Sync Operations

### Automatic Schedule

- **06:00 UTC** — SAM.gov solicitation scrape (500 opportunities/NAICS)
- **12:00 UTC** — Labor rate COLA update & pricing refresh
- **18:00 UTC** — CPARS rating refresh

### Manual Trigger

```bash
# Trigger via GitHub CLI
gh workflow run daily-sync.yml

# Or directly via API
curl -X POST https://api.github.com/repos/already-here-llc/ah-pos/actions/workflows/daily-sync.yml/dispatches \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  -d '{"ref":"main"}'
```

### Verify Last Run

```bash
psql -U ah_pos_app -d ah_pos << 'EOF'
SELECT
  (SELECT COUNT(*) FROM solicitations) as total_opportunities,
  (SELECT COUNT(*) FROM solicitations WHERE first_seen_date >= NOW() - INTERVAL '1 day') as new_24h,
  (SELECT COUNT(*) FROM alerts WHERE status = 'new') as new_alerts,
  (SELECT MAX(last_updated) FROM solicitations) as last_sync_time;
EOF
```

---

## API Endpoints (Future)

Once a FastAPI wrapper is added:

```bash
# List high-priority opportunities
GET /api/opportunities?min_score=70&days_to_close_max=30

# Get past performance for NAICS
GET /api/past-performance?naics_code=541611

# Export cost analysis template
POST /api/cost-analysis/generate
{
  "opportunity_id": 12345,
  "labor_categories": ["PM-001", "DEV-002"],
  "contract_type": "FFP"
}

# Generate proposal draft
POST /api/proposal/generate
{
  "solicitation_id": "SAM-2024-0001"
}
```

---

## Database Schema

### Core Tables

| Table | Purpose | Key Columns |
|-------|---------|------------|
| `past_performance_contracts` | Completed contracts | contract_id, agency_id, naics_code, quality_rating, on_time_percent |
| `solicitations` | Active SAM.gov opportunities | solicitation_id, agency_id, naics_codes[], opportunity_score, response_deadline |
| `incumbent_contracts` | Current federal contracts held by others | contract_id, incumbent_contractor, expiration_date, cpars_rating |
| `labor_categories` | GSA labor rates | category_code, loaded_rate_2026, ffp_rate, tm_rate |
| `cost_analyses` | Generated cost proposals | proposal_id, total_contract_value, profit_margin_percent |
| `alerts` | High-priority notifications | alert_type, severity, solicitation_id, status |

### Views

- `high_priority_opportunities` — scored solicitations ready for proposal
- `recompete_alerts` — incumbent contracts approaching expiration

---

## Configuration

### Environment Variables

```bash
# Required
DATABASE_URL=postgresql://user:pass@host:5432/ah_pos

# Optional
NAICS_CODES=541611,541512,541330  # Which industries to monitor
SLACK_WEBHOOK_URL=https://hooks.slack.com/...  # Notifications
LOG_LEVEL=INFO
```

### SAM.gov API

- **Endpoint:** `https://api.sam.gov/prod/opportunities/v1/search`
- **Auth:** Public API (no key required)
- **Rate Limit:** 10 req/second (honored by script)
- **Data Freshness:** Updated daily

---

## Compliance & Security

### DCAA Audit Trail
- All data mutations logged with user/timestamp
- Indirect cost rates tracked with approval date
- Past performance can be exported for audit verification

### Data Protection
- PostgreSQL role-based access (read-only for proposals, write for ingestion)
- Database backups to S3 daily (immutable past performance records)
- No API keys or credentials in code (GitHub Secrets only)

### Cost Analysis
- SF 1411 (Cost Analysis) export-ready format
- Profit margin validation (prevents negative margins)
- DCAA-compliant rate component tracking (labor + burden + overhead + G&A)

---

## Troubleshooting

### "Database connection timeout"
```bash
# Check DATABASE_URL
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1"
```

### "SAM.gov API rate limited"
The scraper includes exponential backoff. If it persists:
```bash
# Check last sync status in logs
docker-compose logs backend | tail -50

# Manual retry (will skip duplicates)
python backend/scrape_sam_gov.py --retry
```

### "Query performance > 5 seconds"
```bash
# Analyze query plan
EXPLAIN (ANALYZE) SELECT * FROM high_priority_opportunities;

# Refresh materialized views
REFRESH MATERIALIZED VIEW high_priority_opportunities;
```

### "Missing past performance records"
Verify import completed:
```bash
python backend/ingest_past_performance.py --verify
# Output: "✓ 47 contracts imported, 0 duplicates skipped"
```

---

## Contributing

1. **Schema changes:** Update `database/00_init_schema.sql` + models.py
2. **New data sources:** Add scraper in `backend/` + add daily sync job to GitHub workflow
3. **Testing:** `pytest backend/tests/` before push
4. **Code format:** `black backend/`
5. **Security scan:** `bandit backend/*.py`

---

## Cost Analysis

### Infrastructure
- **Database:** PostgreSQL managed (~$15-40/month on AWS RDS or OCI Always Free tier)
- **Compute:** GitHub Actions (free tier covers this workload)
- **Storage:** S3/OCI object storage for backups (~$1/month)
- **Total:** ~$20-50/month (or free tier with OCI Always Free)

### Data Sources
- SAM.gov: Free (public API)
- usaspending.gov: Free (public API)
- CPARS: Free (public API, limited detail)

---

## Roadmap

- [ ] **Phase 2:** Proposal auto-generation (80% draft)
- [ ] **Phase 3:** Web dashboard + alert management UI
- [ ] **Phase 4:** Incumbent CPARS rating integration (full API)
- [ ] **Phase 5:** Historical bid analysis (win/loss modeling)
- [ ] **Phase 6:** Team collaboration (comments, assignments, workflow)

---

## License

Internal tool — Already Here LLC. All rights reserved.

---

## Support

For issues or questions:
1. Check GitHub Issues
2. Review logs: `docker-compose logs`
3. Contact: dispatch@alreadyherellc.com

---

**Last Updated:** 2026-06-28  
**Version:** 1.0.0  
**Status:** Production Ready
