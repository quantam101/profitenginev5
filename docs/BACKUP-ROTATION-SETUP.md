# Backup Rotation Workflow Setup Guide

## Overview

The **Weekly Backup & Rotation** workflow (`.github/workflows/backup-rotation.yml`) automates:

- **Weekly timestamped backups** (every Monday at 02:00 UTC)
- **SHA256 integrity validation** (archive checksums)
- **28-day retention rotation** (automatic cleanup of old backups)
- **Multi-location distribution** (GitHub Releases + optional S3)
- **Email verification** (summary reports with details)

## Required Secrets

Add these to GitHub repository **Settings → Secrets and variables → Actions**:

| Secret | Purpose | Example | Required |
|--------|---------|---------|----------|
| `BACKUP_ENCRYPTION_KEY` | Encryption key for backups | `your-secure-key-32-char-min` | ✅ Yes |
| `BACKUP_NOTIFICATION_EMAIL` | Email for verification reports | `ops@alreadyherellc.com` | ⚠️ Optional* |
| `SMTP_USER` | SMTP sender email | `noreply@gmail.com` | ⚠️ Optional* |
| `SMTP_PASSWORD` | SMTP auth token/password | `app-specific-password` | ⚠️ Optional* |
| `SMTP_HOST` | SMTP server | `smtp.gmail.com` | ⚠️ Optional* |
| `SMTP_PORT` | SMTP port | `587` | ⚠️ Optional* |
| `S3_BUCKET` | S3 bucket name | `profitengine-backups` | ❌ No |
| `S3_ACCESS_KEY` | AWS access key ID | (from AWS IAM) | ❌ No |
| `S3_SECRET_KEY` | AWS secret key | (from AWS IAM) | ❌ No |
| `S3_ENDPOINT` | S3-compatible endpoint | `https://s3.amazonaws.com` | ❌ No |
| `S3_REGION` | AWS region | `us-east-1` | ❌ No |

*\*Email notification is optional. If both `BACKUP_NOTIFICATION_EMAIL` and `SMTP_PASSWORD` are configured, emails will be sent.*

## Quick Start

### 1. Configure Minimal Setup (GitHub Releases only)

```bash
# Step 1: Generate encryption key
openssl rand -base64 32

# Step 2: Add to GitHub Secrets
# BACKUP_ENCRYPTION_KEY = <output from step 1>
```

### 2. Enable Email Notifications (Optional)

For Gmail with 2FA enabled:

1. Generate app-specific password: https://myaccount.google.com/apppasswords
2. Add GitHub Secrets:
   - `BACKUP_NOTIFICATION_EMAIL`: `your-email@gmail.com`
   - `SMTP_USER`: `your-email@gmail.com`
   - `SMTP_PASSWORD`: `<16-char app password>`
   - `SMTP_HOST`: `smtp.gmail.com`
   - `SMTP_PORT`: `587`

### 3. Enable S3 Replication (Optional)

For AWS S3 backup distribution:

1. Create IAM user with S3 access
2. Generate access key pair
3. Create S3 bucket: `profitengine-backups`
4. Add GitHub Secrets:
   - `S3_BUCKET`: `profitengine-backups`
   - `S3_ACCESS_KEY`: `AKIA...`
   - `S3_SECRET_KEY`: `<secret key>`
   - `S3_REGION`: `us-east-1` (or your region)

## Usage

### Automatic Scheduled Run

Runs every **Monday at 02:00 UTC**. Monitor in **Actions → Weekly Backup & Rotation**.

### Manual Trigger

**GitHub UI:**
- Go to **Actions → Weekly Backup & Rotation**
- Click **Run workflow**
- Configure options:
  - **Retention Days**: Keep last N days (default: 28)
  - **Verify Only**: Check existing backups without creating new one
  - **Enable S3 Distribution**: Upload to S3 (requires secrets)

**GitHub CLI:**

```bash
# Run with defaults
gh workflow run backup-rotation.yml

# Run verification only
gh workflow run backup-rotation.yml \
  -f verify_only=true

# Run with custom retention
gh workflow run backup-rotation.yml \
  -f retention_days=60

# Run with S3 distribution
gh workflow run backup-rotation.yml \
  -f enable_s3_distribution=true
```

## Workflow Structure

### Jobs

| Job | Purpose | Duration |
|-----|---------|----------|
| **validate** | Check secrets and configuration | ~1-2 min |
| **backup** | Create timestamped archive with checksums | ~20-30 min |
| **rotate** | Delete backups older than retention period | ~5-10 min |
| **verify** | Confirm backup accessibility | ~2-5 min |
| **notify** | Send verification email | ~2 min |
| **summary** | Generate GitHub Actions summary report | ~1 min |

### Backup Contents

The archive (`profitengine-backup-YYYYMMDD_HHMMSS.tar.gz`) includes:

```
✅ Backed up:
  .github/           (workflows, CI/CD config)
  scripts/           (automation scripts)
  src/               (source code)
  datacenter/        (content pipeline)
  deploy/            (deployment configs)
  runtime/           (API/service configs)
  agents/            (agent definitions)
  docs/              (documentation)
  *.json, *.toml     (package configs)
  docker-compose.yml (infrastructure)

❌ Excluded:
  .git/              (too large, redundant with GitHub)
  node_modules/      (reinstallable dependencies)
  .env               (sensitive - not backed up)
  *.log              (temporary files)
  __pycache__/       (compiled Python cache)
```

## Verification

### Access Backups

All backups are stored in **GitHub Releases** with tags like `backup-20260616_020000`.

**GitHub UI:**
- Repository → **Releases** → Filter "backup-"
- Click release to download archive + checksum

**GitHub CLI:**

```bash
# List all backups
gh release list --repo quantam101/profitengine-v5 \
  --json name,createdAt | jq '.[] | select(.name | startswith("Backup"))'

# Download latest backup
gh release download backup-20260616_020000 \
  --repo quantam101/profitengine-v5 \
  --pattern "*.tar.gz*"

# Verify checksum
sha256sum -c profitengine-backup-*.tar.gz.sha256

# List archive contents
tar -tzf profitengine-backup-*.tar.gz | head -20

# Extract archive
tar -xzf profitengine-backup-*.tar.gz
```

### S3 Backups

If S3 distribution is enabled, backups are also available at:

```
s3://profitengine-backups/backups/profitengine-backup-YYYYMMDD_HHMMSS.tar.gz
s3://profitengine-backups/backups/profitengine-backup-YYYYMMDD_HHMMSS.tar.gz.sha256
```

Access via AWS CLI:

```bash
# List S3 backups
aws s3 ls s3://profitengine-backups/backups/ --recursive

# Download from S3
aws s3 cp s3://profitengine-backups/backups/profitengine-backup-*.tar.gz .

# Verify S3 metadata
aws s3api head-object \
  --bucket profitengine-backups \
  --key backups/profitengine-backup-YYYYMMDD_HHMMSS.tar.gz
```

## Email Notification Format

When email is enabled, you receive a report like:

```
From: noreply@github.com
To: ops@alreadyherellc.com
Subject: ✅ Backup Verification Report - 2026-06-16 02:00:00 UTC

BACKUP DETAILS
==============
Archive Name: profitengine-backup-20260616_020000.tar.gz
Size: 125432100 bytes
SHA256: a1b2c3d4e5f6...

ROTATION SUMMARY
================
Deleted (>28 days): 1
Retained (<=28 days): 4

VERIFICATION STATUS
===================
Status: success
Backup Count: 4
```

## Troubleshooting

### Backup Creation Fails

**Error**: "Archive is corrupted or unreadable"

**Solution**:
- Check disk space on runner (`df -h`)
- Verify file permissions in repository
- Review excluded patterns in the archive step

### Rotation Not Working

**Error**: Old backups not being deleted

**Solution**:
- Verify GitHub token has `contents: write` permission
- Check `RETENTION_DAYS` is correctly set (min: 1)
- Manually delete via: `gh release delete backup-YYYYMMDD_HHMMSS`

### Email Not Sending

**Error**: "Failed to send email"

**Solution**:
- Verify SMTP credentials are correct
- For Gmail: Use app-specific password, not account password
- Check firewall isn't blocking SMTP port 587
- Review GitHub Actions log for SMTP error details

### S3 Upload Fails

**Error**: "S3 upload failed: InvalidAccessKeyId"

**Solution**:
- Verify `S3_ACCESS_KEY` and `S3_SECRET_KEY` are correct
- Confirm IAM user has `s3:PutObject`, `s3:DeleteObject` permissions
- Check S3 bucket name matches `S3_BUCKET` secret
- Verify S3 endpoint is accessible (e.g., `https://s3.amazonaws.com`)

## Retention Policy

- **Default**: Keep 4 weeks (28 days) of backups
- **Customizable**: Set `retention_days` in manual workflow trigger
- **Rotation**: Runs weekly, deletes backups older than cutoff
- **Example**:
  - Today: 2026-06-16
  - Cutoff: 2026-05-19 (28 days ago)
  - Action: Delete all backups with dates < 2026-05-19

## Security Notes

1. **Encryption Key**: Store securely; don't commit to repository
2. **SMTP Passwords**: Use app-specific passwords for email services
3. **AWS Credentials**: Rotate regularly; use IAM policies for least privilege
4. **GitHub Token**: Automatically injected; has access to this repo only
5. **Backup Contents**: `.env` files and secrets are **explicitly excluded**

## Monitoring

Check workflow status:

```bash
# Watch latest run
gh run watch --repo quantam101/profitengine-v5 \
  $(gh run list --repo quantam101/profitengine-v5 \
    --workflow=backup-rotation.yml \
    --json databaseId \
    --jq '.[0].databaseId')

# View logs
gh run view <RUN_ID> --repo quantam101/profitengine-v5 --log

# List recent runs
gh run list --repo quantam101/profitengine-v5 \
  --workflow=backup-rotation.yml \
  --limit 10
```

## Integration Examples

### Restore from Backup

```bash
#!/bin/bash
# Download and extract latest backup

REPO="quantam101/profitengine-v5"
RELEASE=$(gh release list --repo $REPO \
  --json name --jq '.[] | select(.name | startswith("Backup")) | .name' \
  | head -1)

if [ -z "$RELEASE" ]; then
  echo "No backups found"
  exit 1
fi

echo "Restoring from: $RELEASE"
gh release download "$RELEASE" --repo $REPO

# Verify checksum
ARCHIVE=$(ls profitengine-backup-*.tar.gz | head -1)
if ! sha256sum -c "$ARCHIVE.sha256"; then
  echo "Checksum verification failed!"
  exit 1
fi

# Extract
tar -xzf "$ARCHIVE"
echo "✅ Restore complete"
```

### CI/CD Integration

Add to other workflows to ensure backups before major changes:

```yaml
jobs:
  pre-deployment:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger backup before deployment
        run: |
          gh workflow run backup-rotation.yml \
            --repo ${{ github.repository }} \
            -f verify_only=false
```

## Support

For issues or questions:

1. Check GitHub Actions logs: **Actions → Weekly Backup & Rotation → Run details**
2. Review this guide's troubleshooting section
3. Verify all required secrets are configured
4. Test with `verify_only=true` mode first
