# CI/CD Alternatives & Bypass Options

**Problem:** GitHub Actions blocked by account billing issue  
**Goal:** Get AH-POS daily sync running without depending on GitHub's account status

---

## Option 1: Fix GitHub Billing (Easiest)

**Time:** 5 minutes  
**Cost:** Depends on your account issue  
**Effort:** Minimal

### Steps
1. Go to GitHub Settings → Billing & plans
2. Check payment method
3. Update if expired/invalid
4. Workflows auto-resume

**Pros:**
- Simplest solution
- GitHub Actions is free tier (2,000 min/month)
- Already configured and committed

**Cons:**
- Requires fixing underlying billing issue
- Won't help if you want to avoid GitHub Actions permanently

---

## Option 2: Move CI/CD to OCI Server (Recommended Alternative)

**Time:** 15 minutes  
**Cost:** Free (uses existing OCI server at 129.146.236.177)  
**Effort:** Low

### How It Works
Instead of GitHub Actions, run daily sync directly on OCI server via cron job.

### Setup

```bash
# SSH to OCI server
ssh opc@129.146.236.177

# Create script: /home/opc/ah-pos-sync.sh
cat > /home/opc/ah-pos-sync.sh << 'EOF'
#!/bin/bash
set -e

# Navigate to repo
cd /home/opc/profitenginev5/ah-pos

# Load environment
export DATABASE_URL="postgresql://user:pass@localhost:5432/ah_pos"

# Run sync jobs (same as GitHub Actions)
python backend/scrape_sam_gov.py          # 06:00 UTC
python backend/pricing_update.py          # 12:00 UTC
python backend/cpars_refresh.py           # 18:00 UTC

# Log results
echo "Sync completed: $(date)" >> /var/log/ah-pos-sync.log
EOF

chmod +x /home/opc/ah-pos-sync.sh

# Add to crontab (runs at 06:00, 12:00, 18:00 UTC)
crontab -e
# Add these lines:
# 0 6 * * * /home/opc/ah-pos-sync.sh
# 0 12 * * * /home/opc/ah-pos-sync.sh
# 0 18 * * * /home/opc/ah-pos-sync.sh

# Verify cron is running
crontab -l
```

### Deployment

```bash
# 1. Copy code to OCI server
scp -r ah-pos opc@129.146.236.177:/home/opc/profitenginev5/

# 2. Install Python dependencies
ssh opc@129.146.236.177 << 'EOF'
cd /home/opc/profitenginev5/ah-pos
python -m pip install -r requirements.txt
EOF

# 3. Create PostgreSQL on OCI (local or managed)
# Run schema initialization
ssh opc@129.146.236.177 << 'EOF'
psql -U postgres -d postgres < /home/opc/profitenginev5/ah-pos/database/00_init_schema.sql
EOF

# 4. Cron will auto-run sync jobs
```

**Pros:**
- 100% free (uses existing OCI server)
- No GitHub dependency
- Direct control over scheduling
- More reliable (runs on your server, not GitHub's)
- Can send notifications via email/Slack

**Cons:**
- Requires SSH access to OCI server
- Manual setup (no GitHub UI)
- Need to manage logs manually

### Monitoring

```bash
# Check cron logs
tail -f /var/log/ah-pos-sync.log

# Check database activity
psql $DATABASE_URL -c "SELECT COUNT(*) FROM solicitations WHERE last_updated > NOW() - INTERVAL '1 hour';"

# Check cron execution
grep CRON /var/log/syslog | tail -20
```

---

## Option 3: Use GitLab CI (Free & Generous)

**Time:** 20 minutes  
**Cost:** Free (10,000 free minutes/month)  
**Effort:** Medium

### Why GitLab?
- 10,000 free CI/CD minutes/month (vs GitHub's 2,000)
- No billing account required for free tier
- Same YAML syntax as GitHub

### Setup

```bash
# 1. Create GitLab account (free)
# 2. Create new project: ah-pos
# 3. Add SSH key for push

# 4. Add .gitlab-ci.yml (similar to GitHub Actions)
cat > ah-pos/.gitlab-ci.yml << 'EOF'
stages:
  - sync
  - report

sam_gov_sync:
  stage: sync
  image: python:3.11
  script:
    - pip install -r requirements.txt
    - python backend/scrape_sam_gov.py
  only:
    - schedules  # Scheduled pipeline

pricing_update:
  stage: sync
  image: python:3.11
  script:
    - pip install -r requirements.txt
    - python backend/pricing_update.py
  only:
    - schedules

daily_report:
  stage: report
  image: python:3.11
  script:
    - pip install -r requirements.txt
    - python backend/generate_report.py
  only:
    - schedules
EOF

# 5. Push to GitLab
git remote add gitlab https://gitlab.com/your-username/ah-pos.git
git push gitlab main

# 6. Set pipeline schedule in GitLab UI
# GitLab → CI/CD → Schedules → New Schedule
# Set time: 06:00 UTC, 12:00 UTC, 18:00 UTC
```

**Pros:**
- Free tier is very generous
- No billing concerns
- Better uptime than GitHub (historically)
- Built-in CI/CD minutes pool

**Cons:**
- Requires learning GitLab
- Need to migrate repo or maintain mirror
- Less commonly used (but fully capable)

---

## Option 4: Use CircleCI (Free for Public Repos)

**Time:** 15 minutes  
**Cost:** Free for public repos  
**Effort:** Low

### Setup

```bash
# 1. Create CircleCI account (free)
# 2. Connect GitHub repo (or mirror)
# 3. Add .circleci/config.yml

cat > ah-pos/.circleci/config.yml << 'EOF'
version: 2.1

jobs:
  daily_sync:
    docker:
      - image: python:3.11
      - image: postgres:16
        environment:
          POSTGRES_DB: ah_pos
    steps:
      - checkout
      - run:
          name: Install dependencies
          command: pip install -r ah-pos/requirements.txt
      - run:
          name: Run SAM.gov scraper
          command: python ah-pos/backend/scrape_sam_gov.py

workflows:
  scheduled_sync:
    triggers:
      - schedule:
          cron: "0 6,12,18 * * *"
          filters:
            branches:
              only: main
    jobs:
      - daily_sync
EOF
```

**Pros:**
- Free for public repos
- No account/billing restrictions
- Large free tier (performance plan)
- Good reliability

**Cons:**
- Requires public GitHub repo
- Slightly more complex setup
- Less integration with GitHub than Actions

---

## Option 5: Disable Workflows, Run Locally (Interim)

**Time:** 2 minutes  
**Cost:** Free  
**Effort:** Minimal (temporary solution)

### For Immediate Testing

```bash
# Keep code, disable GitHub Actions
mv ah-pos/.github/workflows/daily-sync.yml ah-pos/.github/workflows/daily-sync.yml.disabled

# Test locally
cd ah-pos
docker-compose up -d
python backend/ingest_past_performance.py
python backend/scrape_sam_gov.py
python backend/proposal_generator.py

# Re-enable when GitHub billing fixed
mv ah-pos/.github/workflows/daily-sync.yml.disabled ah-pos/.github/workflows/daily-sync.yml
```

**Pros:**
- Instant solution (no wait)
- Code not affected
- Can test everything locally

**Cons:**
- No automation
- Not production-grade
- Only temporary fix

---

## Option 6: Use AWS Lambda (Minimal Cost)

**Time:** 30 minutes  
**Cost:** ~$1/month (free tier covers it)  
**Effort:** Medium-High

### How It Works
AWS Lambda runs Python code on schedule without servers.

```python
# lambda_handler.py
import json
from backend.scrape_sam_gov import SolicitationScraper
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def lambda_handler(event, context):
    # Initialize
    database_url = os.environ['DATABASE_URL']
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Run sync
    scraper = SolicitationScraper(database_url)
    result = scraper.run_daily_sync(['541611', '541512', '541330'])
    
    return {
        'statusCode': 200,
        'body': json.dumps(f'Synced {result} opportunities')
    }
```

**Pros:**
- Pay only for execution time (~$1/month)
- No server to manage
- AWS handles scaling/reliability
- CloudWatch for monitoring

**Cons:**
- Requires AWS account & knowledge
- More complex setup
- Package dependencies can be tricky

---

## Option 7: Docker Swarm or Kubernetes (Overkill)

**Time:** 1+ hours  
**Cost:** Depends on infrastructure  
**Effort:** High

Only if you need multi-region failover or advanced orchestration.

---

## Recommendation Matrix

| Option | Cost | Time | Reliability | Effort |
|--------|------|------|-------------|--------|
| 1. Fix GitHub | $0 | 5 min | ⭐⭐⭐⭐⭐ | ⭐ |
| 2. OCI Cron | $0 | 15 min | ⭐⭐⭐⭐ | ⭐⭐ |
| 3. GitLab CI | $0 | 20 min | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 4. CircleCI | $0 | 15 min | ⭐⭐⭐⭐ | ⭐⭐ |
| 5. Local Only | $0 | 2 min | ⭐⭐ | ⭐ |
| 6. AWS Lambda | $1 | 30 min | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

---

## My Recommendation

### Short-term (This Week)
**Option 2: OCI Cron Job**
- Zero cost (already have server at 129.146.236.177)
- 15 minutes to set up
- More reliable than GitHub Actions
- Full control over scheduling

### Long-term (Best Practice)
**Option 1: Fix GitHub Billing** (Primary)
**+ Option 2: OCI Cron** (Backup)
- GitHub Actions for immediate CI/CD
- OCI Cron as fallback if GitHub has issues
- Best of both worlds

### If You Never Want GitHub Dependency
**Option 3: GitLab CI**
- More generous free tier
- Same code (just different CI/CD)
- No billing concerns
- More reliable historically

---

## Implementation: OCI Cron (Quick Start)

### 1-Minute Setup
```bash
# SSH to OCI
ssh opc@129.146.236.177

# Create daily sync script
cat > /home/opc/run-ah-pos-sync.sh << 'EOF'
#!/bin/bash
cd /home/opc/profitenginev5/ah-pos
export DATABASE_URL="postgresql://user:pass@db-host:5432/ah_pos"
python backend/scrape_sam_gov.py >> /var/log/ah-pos.log 2>&1
EOF

chmod +x /home/opc/run-ah-pos-sync.sh

# Add to crontab
echo "0 6,12,18 * * * /home/opc/run-ah-pos-sync.sh" | crontab -
```

Done. Runs daily at 06:00, 12:00, 18:00 UTC forever.

---

## Summary

| Scenario | Best Option |
|----------|-------------|
| Just fix the issue | Option 1 (GitHub Billing) |
| Never want GitHub dependency | Option 2 (OCI Cron) + Option 3 (GitLab CI) |
| Quick fallback | Option 2 (OCI Cron) |
| Already on AWS | Option 6 (Lambda) |
| Testing only | Option 5 (Local) |

---

**Choose one and let me know. I'll implement it for you.**
