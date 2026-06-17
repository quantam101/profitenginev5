# Backup & Rotation System Integration Guide

## Overview

The backup & rotation system provides automated weekly backups with:
- **Timestamped archives** (BACKUP_YYYYMMDD_HHMMSS.tar.gz format)
- **SHA256 integrity validation** (automatic checksum verification)
- **Automatic rotation** (28-day retention policy)
- **Multi-location distribution** (GitHub Releases + optional S3)
- **Email verification reports** (optional SMTP)

## Architecture

### Components

1. **GitHub Actions Workflow** (`.github/workflows/backup-rotation.yml`)
   - Scheduled: Every Monday at 02:00 UTC
   - Manual trigger: Full control via workflow_dispatch inputs
   - 6-job pipeline with dependency management

2. **Python Backup Script** (`scripts/backup_and_rotate.py`)
   - Creates tar.gz archives with exclusions
   - Validates archive integrity
   - Rotates old backups based on retention days
   - Uploads to S3 if configured

3. **GitHub Releases**
   - Primary backup storage (always available)
   - Each backup = tagged release with archive + checksum

4. **S3-Compatible Storage** (optional)
   - Secondary distribution to AWS S3, Wasabi, DigitalOcean Spaces, etc.
   - Requires valid AWS credentials

## Setup Instructions

### Required Secrets (GitHub Actions)

Add these secrets to your GitHub repository (Settings → Secrets and Variables → Actions):

#### Critical (must have)
```
BACKUP_ENCRYPTION_KEY
  Description: Encryption key for backup validation
  Value: Generate with: python -c "import secrets; print(secrets.token_hex(32))"
```

#### Optional (email notifications)
```
BACKUP_NOTIFICATION_EMAIL
  Description: Email to receive backup verification reports
  Value: user@example.com

SMTP_USER
  Description: SMTP account username
  Value: your-email@gmail.com (or other provider)

SMTP_PASSWORD
  Description: SMTP password or app-specific password
  Value: [Gmail app password or SMTP token]

SMTP_HOST
  Description: SMTP server hostname (default: smtp.gmail.com)
  Value: smtp.gmail.com

SMTP_PORT
  Description: SMTP port (default: 587)
  Value: 587
```

#### Optional (S3 distribution)
```
S3_BUCKET
  Description: S3 bucket name
  Value: my-profitengine-backups

S3_ACCESS_KEY
  Description: AWS access key ID
  Value: AKIA...

S3_SECRET_KEY
  Description: AWS secret access key
  Value: [secret]

S3_ENDPOINT
  Description: S3 endpoint (default: https://s3.amazonaws.com)
  Value: https://s3.amazonaws.com
  Examples:
    - Wasabi: https://s3.wasabisys.com
    - DigitalOcean: https://[region].digitaloceanspaces.com

S3_REGION
  Description: AWS region (default: us-east-1)
  Value: us-east-1
```

### Generate Encryption Key

```bash
python -c "import secrets; print(secrets.token_hex(32))"
# Output: a1b2c3d4e5f6... (64 character hex string)
```

Copy this value into `BACKUP_ENCRYPTION_KEY` secret.

## Usage

### Automatic (Scheduled)

Backups run automatically every Monday at 02:00 UTC. No action required.

### Manual Trigger

In GitHub Actions, navigate to:
```
Actions → Weekly Backup & Rotation → Run workflow
```

**Workflow Inputs:**

| Input | Default | Options | Purpose |
|-------|---------|---------|---------|
| `retention_days` | 28 | 1-365 | How many days to keep backups |
| `verify_only` | false | true/false | Only verify existing, don't create new |
| `enable_s3_distribution` | false | true/false | Upload to S3 after creation |

### Command-line (Local Testing)

```bash
# Create backup with default settings
python scripts/backup_and_rotate.py

# Verify only (no new backup)
python scripts/backup_and_rotate.py --verify-only

# Enable S3 upload
python scripts/backup_and_rotate.py --enable-s3

# Custom retention (14 days instead of 28)
python scripts/backup_and_rotate.py --retention-days 14

# All options
python scripts/backup_and_rotate.py \
  --retention-days 21 \
  --enable-s3 \
  --backup-dir ./backups \
  --archive-prefix myapp-backup
```

## Environment Variables

### Required
```
BACKUP_ENCRYPTION_KEY  # For backup validation
```

### Optional (script configuration)
```
BACKUP_DIR             # Backup directory (default: ./backups)
ARCHIVE_PREFIX         # Archive prefix (default: profitengine-backup)
RETENTION_DAYS         # Retention days (default: 28)
VERIFY_ONLY            # Verify-only mode (default: false)
ENABLE_S3              # S3 upload (default: false)
AWS_ACCESS_KEY_ID      # AWS key
AWS_SECRET_ACCESS_KEY  # AWS secret
AWS_S3_BUCKET          # S3 bucket name
AWS_S3_ENDPOINT        # S3 endpoint
AWS_REGION             # AWS region
```

## Workflow Jobs

### 1. Validate (2 min timeout)
- Checks `BACKUP_ENCRYPTION_KEY` secret
- Verifies email config (if SMTP credentials set)
- Checks S3 config (if S3 distribution requested)

### 2. Backup (30 min timeout)
- Creates timestamped tar.gz archive
- Excludes: .git, node_modules, .env, logs, __pycache__
- Calculates SHA256 checksum
- Validates archive integrity
- Uploads to GitHub Releases as tagged release
- Optionally uploads to S3
- Cleans up local backup directory

### 3. Rotate (10 min timeout)
- Lists all backup releases
- Deletes releases older than retention days
- Optionally rotates old S3 objects
- Reports deleted/retained counts

### 4. Verify (5 min timeout)
- Checks latest backup is accessible
- Counts total retained backups
- Outputs verification status

### 5. Notify (5 min timeout)
- Sends email report via SMTP (if configured)
- Includes archive name, size, SHA256
- Shows rotation summary (deleted/retained)
- Provides link to releases page

### 6. Summary
- Generates GitHub Actions summary report
- Shows all metrics in markdown table format

## Archive Contents

Each backup includes:

```
.github/              # Workflow definitions
scripts/              # All scripts
src/                  # Source code
datacenter/           # Data center configs
deploy/               # Deployment configs
runtime/              # Runtime configs
agents/               # Agent definitions
docs/                 # Documentation
package.json          # Node dependencies
pyproject.toml        # Python metadata
docker-compose.yml    # Container definitions
README.md             # Documentation
.gitignore            # Git ignore rules
```

Excluded from backups:

```
.git/                 # Git history (too large)
node_modules/         # Dependencies (can reinstall)
__pycache__/          # Python cache
*.log                 # Log files
.pytest_cache/        # Test cache
*.pyc                 # Compiled Python
.env                  # Secrets (never backup!)
backups/              # Previous backups
```

## Verification

### Download and Verify Backup

```bash
# List all backup releases
gh release list --repo quantam101/profitengine-v5-final

# Download latest backup
gh release download backup-YYYYMMDD_HHMMSS \
  --repo quantam101/profitengine-v5-final

# Verify checksum
sha256sum -c profitengine-backup-YYYYMMDD_HHMMSS.tar.gz.sha256

# List archive contents
tar -tzf profitengine-backup-YYYYMMDD_HHMMSS.tar.gz | head -20

# Extract backup
tar -xzf profitengine-backup-YYYYMMDD_HHMMSS.tar.gz
```

## S3 Configuration Examples

### AWS S3
```
S3_ENDPOINT=https://s3.amazonaws.com
S3_REGION=us-east-1
S3_BUCKET=my-profitengine-backups
```

### Wasabi
```
S3_ENDPOINT=https://s3.wasabisys.com
S3_REGION=us-east-1
S3_BUCKET=my-profitengine-backups
```

### DigitalOcean Spaces
```
S3_ENDPOINT=https://nyc3.digitaloceanspaces.com
S3_REGION=nyc3
S3_BUCKET=my-profitengine-backups
```

### MinIO (local)
```
S3_ENDPOINT=http://localhost:9000
S3_REGION=local
S3_BUCKET=profitengine-backups
```

## Troubleshooting

### Missing BACKUP_ENCRYPTION_KEY

**Error:** `❌ BLOCKING: Missing critical secrets: BACKUP_ENCRYPTION_KEY`

**Solution:**
```bash
# Generate key
python -c "import secrets; print(secrets.token_hex(32))"

# Add to GitHub Secrets
# Settings → Secrets and variables → Actions → New repository secret
# Name: BACKUP_ENCRYPTION_KEY
# Value: [paste generated key]
```

### S3 Upload Fails

**Check:**
1. S3 bucket exists and you have write access
2. AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are correct
3. S3_BUCKET name is correct
4. For custom endpoints, verify S3_ENDPOINT and S3_REGION

**Debug:**
```bash
# Test S3 access locally
export AWS_ACCESS_KEY_ID=AKIA...
export AWS_SECRET_ACCESS_KEY=...
export AWS_S3_BUCKET=my-bucket

python scripts/backup_and_rotate.py --enable-s3
```

### Email Notification Fails

**Check:**
1. BACKUP_NOTIFICATION_EMAIL is valid
2. SMTP_USER and SMTP_PASSWORD are correct
3. For Gmail: use app-specific password, not regular password
4. SMTP_HOST and SMTP_PORT match email provider

**Gmail Setup:**
1. Enable 2-factor authentication
2. Generate app-specific password: https://myaccount.google.com/apppasswords
3. Use app password in SMTP_PASSWORD secret

### Backup Archive is Corrupted

**Check integrity:**
```bash
tar -tzf profitengine-backup-YYYYMMDD_HHMMSS.tar.gz > /dev/null
echo $?  # 0 = OK, non-zero = corrupted
```

**Verify checksum:**
```bash
sha256sum -c profitengine-backup-YYYYMMDD_HHMMSS.tar.gz.sha256
# Should output: profitengine-backup-YYYYMMDD_HHMMSS.tar.gz: OK
```

## Monitoring

### GitHub Actions Dashboard
- Navigate to: Actions → Weekly Backup & Rotation
- View real-time logs for each job
- Check run duration, success/failure status

### Email Reports
- Receive automated verification emails if SMTP configured
- Each report includes:
  - Archive name, size, SHA256
  - Deleted/retained backup counts
  - Total backup count
  - Link to releases page

### GitHub Releases
- Navigate to: Releases
- Filter by "backup-" prefix
- Download any historical backup
- View release notes with archive metadata

## Cost Considerations

### GitHub Releases (Free)
- Unlimited backup storage in GitHub
- No transfer costs

### S3-Compatible Storage (Optional)
- **AWS S3**: ~$0.023/GB/month storage + transfer costs
- **Wasabi**: $5.99/month unlimited storage
- **DigitalOcean Spaces**: $5/month (250GB) + transfer costs

### Email Notifications (Free)
- Gmail SMTP: Free up to 500 emails/day
- SendGrid: Free tier available
- Other providers vary

## Retention Policies

### Default (28 days)
- Keeps 4 weeks of backups
- One per week = ~4 backups at any time
- Good for most use cases

### Recommended Alternatives

| Duration | Backups | Use Case |
|----------|---------|----------|
| 7 days | 1 | Minimal history |
| 14 days | 2 | Quick recovery only |
| 28 days | 4 | Standard (default) |
| 60 days | 8-9 | Long-term recovery |
| 90 days | 13 | Compliance required |
| 365 days | 52 | Legal/archive |

To change retention: Edit workflow or pass `--retention-days N` to script.

## Security Best Practices

1. **Encrypt backups** (in transit and at rest)
   - GitHub Releases: HTTPS encryption in transit
   - S3: Enable server-side encryption via S3 bucket policy
   - Local: Use encrypted storage

2. **Rotate credentials regularly**
   - Update SMTP_PASSWORD every 90 days
   - Rotate S3/AWS credentials quarterly
   - Use IAM roles for S3 access when possible

3. **Never commit secrets**
   - Keep all secrets in GitHub Actions Secrets
   - Use .env.example for required variables
   - `.env` is in .gitignore for local testing

4. **Limit access**
   - GitHub: Restrict who can manage secrets
   - S3: Use IAM policies limiting bucket access
   - SMTP: Use app-specific passwords (Gmail)

5. **Audit backups**
   - Review backup logs in GitHub Actions
   - Monitor S3 access logs
   - Verify email notifications arrive

## Disaster Recovery

### Restore from GitHub Release

```bash
# List backups
gh release list --repo quantam101/profitengine-v5-final --limit 10

# Download specific backup
gh release download backup-20260616_020000 \
  --repo quantam101/profitengine-v5-final

# Verify
sha256sum -c profitengine-backup-20260616_020000.tar.gz.sha256

# Extract
tar -xzf profitengine-backup-20260616_020000.tar.gz

# Review extracted files
ls -la
```

### Restore from S3

```bash
# Configure AWS credentials
export AWS_ACCESS_KEY_ID=AKIA...
export AWS_SECRET_ACCESS_KEY=...

# Download from S3
aws s3 cp s3://my-bucket/backups/profitengine-backup-20260616_020000.tar.gz .

# Verify and extract
sha256sum -c profitengine-backup-20260616_020000.tar.gz.sha256
tar -xzf profitengine-backup-20260616_020000.tar.gz
```

## Performance Notes

- **Backup duration**: 5-10 minutes (depending on repo size)
- **Archive size**: ~50-100 MB (excludes node_modules, .git)
- **Rotation**: <1 minute
- **S3 upload**: 1-2 minutes
- **Total workflow**: 15-20 minutes

## Files

### Workflow
- `.github/workflows/backup-rotation.yml` (658 lines)
  - 6 jobs with concurrency control
  - Full GitHub Actions integration
  - Email notifications
  - S3 distribution

### Script
- `scripts/backup_and_rotate.py` (450+ lines)
  - Object-oriented BackupManager class
  - Comprehensive logging
  - Error handling
  - JSON output for integration

### Documentation
- `docs/BACKUP-ROTATION-INTEGRATION.md` (this file)
- `.github/workflows/BACKUP-ROTATION-README.md` (setup quick-start)
- `docs/BACKUP-ROTATION-SETUP.md` (detailed setup)

## Support

For issues or questions:
1. Check GitHub Actions logs: Actions → Weekly Backup & Rotation → latest run
2. Review workflow output in GitHub Actions UI
3. Check email notifications for error details
4. Verify secrets are configured: Settings → Secrets and variables → Actions
