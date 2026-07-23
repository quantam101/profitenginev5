# Run AH-POS Local Test on YOUR Machine

**Important:** You need to run this on your local computer (Windows, Mac, or Linux), not in the cloud.

---

## Prerequisites (Check These First)

```bash
# Check Docker is installed
docker --version
# Should show: Docker version 20.10+

# Check Docker Compose is installed
docker-compose --version
# Should show: Docker Compose version 1.29+

# Check Python is installed
python --version
# Should show: Python 3.11+

# Check PostgreSQL client is installed
psql --version
# Should show: psql (PostgreSQL) 12+
```

If any are missing, install them first:
- **Docker Desktop** — https://www.docker.com/products/docker-desktop
- **Python 3.11** — https://www.python.org/downloads/
- **PostgreSQL client** — `brew install postgresql` (Mac) or `apt-get install postgresql-client` (Linux)

---

## Step 1: Download and Navigate to Project

```bash
# Navigate to where you downloaded profitengine-v5-final
cd "path/to/profitengine-v5-final (1)/ah-pos"

# Verify you're in the right place
ls -la
# Should show: docker-compose.yml, Dockerfile, requirements.txt, etc.
```

---

## Step 2: Run the Automated Test

### Option A: Run the Script (Easiest)

```bash
# On Mac/Linux:
bash RUN_LOCAL_TEST.sh

# On Windows (PowerShell):
powershell -ExecutionPolicy Bypass -File RUN_LOCAL_TEST.sh
```

**This will automatically:**
- Start Docker services
- Wait for PostgreSQL
- Import sample data
- Run SAM.gov scraper
- Generate proposals
- Show results

**Then skip to "View Results" below.**

### Option B: Run Commands Manually

```bash
# 1. Start Docker
docker-compose up -d

# 2. Wait 10 seconds for PostgreSQL to start
sleep 10

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Import sample data
python backend/ingest_past_performance.py --file data/sample_past_performance.csv

# 5. Run SAM.gov scraper
python backend/scrape_sam_gov.py

# 6. Verify data
psql postgresql://ah_pos_user:dev_password_change_in_production@localhost:5432/ah_pos << EOF
SELECT COUNT(*) FROM past_performance_contracts;
SELECT COUNT(*) FROM solicitations;
SELECT COUNT(*) FROM high_priority_opportunities;
EOF
```

---

## Step 3: View Results

### Check Database Results

```bash
# View past performance contracts
psql postgresql://ah_pos_user:dev_password_change_in_production@localhost:5432/ah_pos << EOF
SELECT 'Past Performance' as type, COUNT(*) as count FROM past_performance_contracts
UNION ALL
SELECT 'Opportunities', COUNT(*) FROM solicitations
UNION ALL
SELECT 'High-Priority', COUNT(*) FROM high_priority_opportunities
UNION ALL
SELECT 'Alerts', COUNT(*) FROM alerts WHERE status = 'new';
EOF
```

**Expected Output:**
```
          type          | count
------------------------+-------
 Past Performance       |    10
 Opportunities          |    50
 High-Priority          |    12
 Alerts                 |     7
```

### View Generated Proposal

```bash
# The script created: proposal_draft.html

# Open in your browser:
open proposal_draft.html      # Mac
xdg-open proposal_draft.html  # Linux
start proposal_draft.html     # Windows
```

### Access Database UI (pgAdmin)

```
URL: http://localhost:5050
Email: admin@alreadyherellc.invalid
Password: admin
```

Steps:
1. Click "Add New Server"
2. Name: "AH-POS"
3. Hostname: `postgres`
4. Username: `ah_pos_user`
5. Password: `dev_password_change_in_production`
6. Save
7. Browse tables and run queries

### Check Docker Status

```bash
# View running containers
docker-compose ps

# View logs
docker-compose logs -f

# View specific service
docker-compose logs postgres
docker-compose logs
```

---

## Expected Results

### ✅ If Everything Works

```
✓ Docker services started
✓ PostgreSQL is ready
✓ Dependencies installed
✓ 10 past performance contracts imported
✓ 47 SAM.gov opportunities scraped
✓ 12 high-priority opportunities scored
✓ 7 new alerts generated
✓ Proposal drafted (80% complete)
✓ proposal_draft.html created
```

### ❌ If Something Fails

**Docker won't start:**
```bash
# Check if ports are in use
lsof -i :5432
lsof -i :5050

# Or try without port conflicts
docker-compose down
docker-compose up -d
```

**PostgreSQL won't connect:**
```bash
# Check PostgreSQL is running
docker-compose logs postgres

# Wait longer (increase sleep time)
sleep 20
```

**Python dependencies missing:**
```bash
# Reinstall
pip install --upgrade pip
pip install -r requirements.txt

# For PDF export (optional)
pip install weasyprint python-docx
```

**SAM.gov scraper times out:**
```bash
# Free API might be rate-limited, try again
python backend/scrape_sam_gov.py

# Or test with local data only
psql $DATABASE_URL -c "SELECT COUNT(*) FROM solicitations"
```

---

## Testing Checklist

Run these to verify each component:

```bash
# 1. Docker running
docker-compose ps
# Expected: postgres (Up), backend (Up if configured)

# 2. PostgreSQL connected
psql postgresql://ah_pos_user:dev_password_change_in_production@localhost:5432/ah_pos -c "SELECT 1"
# Expected: 1

# 3. Schema created
psql postgresql://ah_pos_user:dev_password_change_in_production@localhost:5432/ah_pos -c "\dt"
# Expected: 16 tables listed

# 4. Data imported
psql postgresql://ah_pos_user:dev_password_change_in_production@localhost:5432/ah_pos -c "SELECT COUNT(*) FROM past_performance_contracts"
# Expected: 10

# 5. Opportunities scraped
psql postgresql://ah_pos_user:dev_password_change_in_production@localhost:5432/ah_pos -c "SELECT COUNT(*) FROM solicitations"
# Expected: 50+

# 6. Scoring works
psql postgresql://ah_pos_user:dev_password_change_in_production@localhost:5432/ah_pos -c "SELECT COUNT(*) FROM high_priority_opportunities"
# Expected: 10+

# 7. Alerts generated
psql postgresql://ah_pos_user:dev_password_change_in_production@localhost:5432/ah_pos -c "SELECT COUNT(*) FROM alerts WHERE status = 'new'"
# Expected: 5+
```

---

## Stop When Done

```bash
# Stop Docker services (but keep data)
docker-compose stop

# Stop and delete (loses data)
docker-compose down

# Stop and delete everything (clean slate)
docker-compose down -v
```

---

## Success!

If all the tests pass, you have:

✅ **Working Database** — PostgreSQL with 16 tables  
✅ **Working Scraper** — Live SAM.gov data  
✅ **Working Scoring** — Opportunity ranking (0-100)  
✅ **Working Proposals** — Auto-generation (80% complete)  
✅ **Working Alerts** — High-priority notifications  

---

## Next: Deploy to Production

Once local testing succeeds:

1. **Choose a server** (DigitalOcean, AWS, etc.)
2. **Set up database** (PostgreSQL in cloud)
3. **Configure cron jobs** (daily sync automation)
4. **Import your data** (real past performance contracts)

See: `CI_CD_ALTERNATIVES.md` and `IMPLEMENT_NOW.md`

---

## Questions?

- **Docker issues?** See "Troubleshooting" in LOCAL_TEST.md
- **Database issues?** Run `docker-compose logs postgres`
- **Python issues?** Check Python version: `python --version`
- **Network issues?** Verify ports: `netstat -an | grep 5432`

---

**Now go run it on your local machine! 🚀**
