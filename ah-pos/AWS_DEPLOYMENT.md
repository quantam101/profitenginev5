# AWS Deployment — Complete Setup Guide

**Goal:** Deploy AH-POS to AWS with automatic daily syncs  
**Cost:** Free tier eligible ($0-10/month with light usage)  
**Time:** 30-45 minutes  

---

## Prerequisites

1. **AWS Account** (free tier) — https://aws.amazon.com/free/
2. **AWS CLI installed** — `pip install awscli` or download from AWS
3. **SSH key pair** — Generate in AWS Console or use existing

---

## Step 1: Create RDS PostgreSQL Database (5 minutes)

### Via AWS Console:

1. Go to **RDS** → **Create database**
2. **Engine:** PostgreSQL (14+)
3. **Templates:** Free tier
4. **DB instance identifier:** `ah-pos-db`
5. **Master username:** `postgres`
6. **Master password:** Generate strong password
7. **DB instance class:** `db.t3.micro` (free tier)
8. **Storage:** `20 GB gp2`
9. **Public accessibility:** Yes
10. **Database name:** `ah_pos`
11. **Create database**

**Wait 5-10 minutes for creation to complete.**

### Get Connection Details:

```bash
# From RDS Console, copy:
# - Endpoint (e.g., ah-pos-db.xxxxx.us-east-1.rds.amazonaws.com:5432)
# - Username: postgres
# - Password: (what you set)
# - Database: ah_pos

export DB_HOST="ah-pos-db.xxxxx.us-east-1.rds.amazonaws.com"
export DB_PORT="5432"
export DB_NAME="ah_pos"
export DB_USER="postgres"
export DB_PASSWORD="your-password"
```

---

## Step 2: Create EC2 Instance (5 minutes)

### Via AWS Console:

1. Go to **EC2** → **Launch instances**
2. **Name:** `ah-pos-server`
3. **AMI:** Ubuntu 22.04 LTS (free tier eligible)
4. **Instance type:** `t3.micro` (free tier)
5. **Key pair:** Create new or select existing
6. **Security group:** 
   - SSH (port 22): From your IP
   - HTTP (port 80): Open
   - HTTPS (port 443): Open
7. **Storage:** 30 GB gp2 (free tier)
8. **Launch instance**

**Wait 2-3 minutes for instance to start.**

### Get Instance Details:

```bash
# From EC2 Console, copy:
# - Public IP (e.g., 3.14.159.265)
# - Key pair file (downloaded)

export EC2_IP="3.14.159.265"
export KEY_FILE="your-key.pem"

# Make key readable
chmod 600 $KEY_FILE
```

---

## Step 3: Configure RDS Security Group (2 minutes)

1. Go to **RDS** → **Databases** → `ah-pos-db`
2. Click **VPC security groups**
3. Edit inbound rules
4. Add rule:
   - Type: PostgreSQL
   - Source: EC2 security group (or EC2 IP)
5. Save

---

## Step 4: Deploy Code to EC2 (10 minutes)

```bash
# SSH to EC2
ssh -i $KEY_FILE ubuntu@$EC2_IP

# Update system
sudo apt-get update
sudo apt-get install -y python3.11 python3-pip git postgresql-client

# Clone repository
cd /home/ubuntu
git clone https://github.com/quantam101/profitenginev5.git
cd profitenginev5/ah-pos

# Install Python dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://postgres:$DB_PASSWORD@$DB_HOST:5432/$DB_NAME"
export PYTHONUNBUFFERED=1
```

---

## Step 5: Initialize Database Schema (2 minutes)

```bash
# From EC2, run:
psql "postgresql://postgres:$DB_PASSWORD@$DB_HOST:5432/ah_pos" < database/00_init_schema.sql

# Verify
psql "postgresql://postgres:$DB_PASSWORD@$DB_HOST:5432/ah_pos" -c "\dt"
# Should show 16 tables
```

---

## Step 6: Import Sample Data (2 minutes)

```bash
# From EC2
cd /home/ubuntu/profitenginev5/ah-pos

# Import contracts
python backend/ingest_past_performance.py --file data/sample_past_performance.csv

# Verify
psql "postgresql://postgres:$DB_PASSWORD@$DB_HOST:5432/ah_pos" -c "SELECT COUNT(*) FROM past_performance_contracts"
# Should show: 10
```

---

## Step 7: Run SAM.gov Scraper (3 minutes)

```bash
# From EC2
python backend/scrape_sam_gov.py

# Verify
psql "postgresql://postgres:$DB_PASSWORD@$DB_HOST:5432/ah_pos" -c "SELECT COUNT(*) FROM solicitations"
# Should show: 50+
```

---

## Step 8: Set Up Daily Cron Jobs (5 minutes)

```bash
# SSH to EC2
ssh -i $KEY_FILE ubuntu@$EC2_IP

# Create sync script
cat > /home/ubuntu/run-ah-pos-sync.sh << EOF
#!/bin/bash
set -e

export DATABASE_URL="postgresql://postgres:${DB_PASSWORD}@${DB_HOST}:5432/ah_pos"
cd /home/ubuntu/profitenginev5/ah-pos

# Run scraper
python backend/scrape_sam_gov.py >> /var/log/ah-pos-sync.log 2>&1

# Log completion
echo "Sync completed: $(date)" >> /var/log/ah-pos-sync.log
EOF

chmod +x /home/ubuntu/run-ah-pos-sync.sh

# Create log file
sudo mkdir -p /var/log
sudo touch /var/log/ah-pos-sync.log
sudo chown ubuntu:ubuntu /var/log/ah-pos-sync.log

# Add to crontab (runs 06:00, 12:00, 18:00 UTC)
(crontab -l 2>/dev/null || true; echo "0 6,12,18 * * * /home/ubuntu/run-ah-pos-sync.sh") | crontab -

# Verify crontab
crontab -l
```

---

## Step 9: Verify Everything Works (2 minutes)

```bash
# From EC2
ssh -i $KEY_FILE ubuntu@$EC2_IP

# Check logs
tail -f /var/log/ah-pos-sync.log

# Check database
psql "postgresql://postgres:${DB_PASSWORD}@${DB_HOST}:5432/ah_pos" << EOF
SELECT 'Contracts' as item, COUNT(*) FROM past_performance_contracts
UNION ALL
SELECT 'Opportunities', COUNT(*) FROM solicitations
UNION ALL
SELECT 'High-Priority', COUNT(*) FROM high_priority_opportunities;
EOF

# Expected output:
#          item          | count
# -----------------------+-------
#  Contracts             |    10
#  High-Priority         |    10+
#  Opportunities         |    50+
```

---

## Complete AWS Setup Script (Automated)

Save this as `deploy-to-aws.sh` and run it:

```bash
#!/bin/bash
set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║           AH-POS AWS DEPLOYMENT — AUTOMATED                   ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Prompt for AWS details
read -p "Enter RDS endpoint (ah-pos-db.xxxxx.rds.amazonaws.com): " DB_HOST
read -p "Enter RDS password: " DB_PASSWORD
read -p "Enter EC2 public IP: " EC2_IP
read -p "Enter path to SSH key (.pem file): " KEY_FILE

echo ""
echo "Deploying to EC2 at $EC2_IP..."
echo ""

# SSH and run setup
ssh -i "$KEY_FILE" ubuntu@"$EC2_IP" << SSHEOF
#!/bin/bash
set -e

echo "Setting up AH-POS on EC2..."

# Update system
sudo apt-get update
sudo apt-get install -y python3.11 python3-pip git postgresql-client

# Clone repo
cd /home/ubuntu
[ -d profitenginev5 ] || git clone https://github.com/quantam101/profitenginev5.git
cd profitenginev5/ah-pos

# Install dependencies
pip install -q -r requirements.txt

# Initialize database
export DATABASE_URL="postgresql://postgres:$DB_PASSWORD@$DB_HOST:5432/ah_pos"
psql \$DATABASE_URL < database/00_init_schema.sql

# Import data
python backend/ingest_past_performance.py --file data/sample_past_performance.csv

# Run scraper
python backend/scrape_sam_gov.py

# Set up cron
cat > /home/ubuntu/run-ah-pos-sync.sh << 'CRONEOF'
#!/bin/bash
export DATABASE_URL="postgresql://postgres:$DB_PASSWORD@$DB_HOST:5432/ah_pos"
cd /home/ubuntu/profitenginev5/ah-pos
python backend/scrape_sam_gov.py >> /var/log/ah-pos-sync.log 2>&1
CRONEOF

chmod +x /home/ubuntu/run-ah-pos-sync.sh
sudo touch /var/log/ah-pos-sync.log
sudo chown ubuntu:ubuntu /var/log/ah-pos-sync.log

(crontab -l 2>/dev/null || true; echo "0 6,12,18 * * * /home/ubuntu/run-ah-pos-sync.sh") | crontab -

echo "✓ Deployment complete!"
SSHEOF

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  ✅ AWS DEPLOYMENT COMPLETE                                    ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Your system is live at:"
echo "  EC2 IP: $EC2_IP"
echo "  Database: $DB_HOST"
echo ""
echo "Daily sync runs at: 06:00, 12:00, 18:00 UTC"
echo ""
echo "Monitor logs:"
echo "  ssh -i $KEY_FILE ubuntu@$EC2_IP"
echo "  tail -f /var/log/ah-pos-sync.log"
echo ""
```

---

## Cost Estimate

| Service | Free Tier | Cost |
|---------|-----------|------|
| **EC2 t3.micro** | 750 hours/month | $0 |
| **RDS db.t3.micro** | 750 hours/month | $0 |
| **Storage** | 20 GB | $0-2 |
| **Data transfer** | 100 GB/month | $0-10 |
| **Total** | — | **$0-12/month** |

---

## Monitoring

### Check Cron Execution
```bash
ssh -i $KEY_FILE ubuntu@$EC2_IP
tail -f /var/log/ah-pos-sync.log
```

### Query Database
```bash
psql "postgresql://postgres:${DB_PASSWORD}@${DB_HOST}:5432/ah_pos" << EOF
SELECT COUNT(*) FROM solicitations WHERE last_updated > NOW() - INTERVAL '1 hour';
EOF
```

### View EC2 CloudWatch Metrics
1. Go to **CloudWatch** → **Dashboards**
2. Monitor CPU, network, disk usage
3. Set up alarms if needed

---

## Troubleshooting

### RDS Connection Failed
```bash
# Check security group allows EC2 IP
# Check password is correct
psql -h $DB_HOST -U postgres -d ah_pos
```

### Cron Not Running
```bash
# Check crontab
crontab -l

# Check logs
grep CRON /var/log/syslog | tail -20

# Run manually to test
/home/ubuntu/run-ah-pos-sync.sh
```

### Scraper Timeout
```bash
# SAM.gov API might be slow
# Check internet connection
curl -I https://api.sam.gov

# Increase timeout in scrape_sam_gov.py
```

---

## Next Steps

1. ✅ Run AWS setup
2. ✅ Verify daily sync runs
3. ✅ Import your real past performance data
4. ✅ Customize NAICS codes
5. ✅ Set up email/Slack alerts

---

**AWS deployment is live and running 24/7!** 🚀
