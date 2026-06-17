# Weekly Backup & Rotation Workflow

**File**: `.github/workflows/backup-rotation.yml` (562 lines)  
**Schedule**: Every Monday at 02:00 UTC  
**Status**: Production-ready

## Quick Reference

### Required Secret
```bash
BACKUP_ENCRYPTION_KEY  # openssl rand -base64 32
```

### Manual Trigger
```bash
# Basic backup
gh workflow run backup-rotation.yml

# Verify existing backups only
gh workflow run backup-rotation.yml -f verify_only=true

# Custom retention (e.g., 60 days instead of 28)
gh workflow run backup-rotation.yml -f retention_days=60

# Include S3 distribution
gh workflow run backup-rotation.yml -f enable_s3_distribution=true
```

### Access Backups
```bash
# List backups
gh release list --repo quantam101/profitengine-v5

# Download latest
gh release download $(gh release list --repo quantam101/profitengine-v5 \
  --json name --jq '.[0].name' | grep backup) \
  --repo quantam101/profitengine-v5

# Verify integrity
sha256sum -c profitengine-backup-*.tar.gz.sha256

# Extract
tar -xzf profitengine-backup-*.tar.gz
```

## Workflow Jobs

| Job | Duration | Purpose |
|-----|----------|---------|
| **validate** | 2 min | Verify secrets & config |
| **backup** | 20-30 min | Create timestamped archive |
| **rotate** | 5-10 min | Delete backups older than 28 days |
| **verify** | 2-5 min | Confirm accessibility |
| **notify** | 2 min | Send verification email |
| **summary** | 1 min | GitHub summary report |

**Total**: ~35-50 minutes

## Features

- ✅ **Weekly automated backups** - Every Monday at 02:00 UTC
- ✅ **Timestamped archives** - `profitengine-backup-YYYYMMDD_HHMMSS.tar.gz`
- ✅ **SHA256 validation** - Auto-checksum with integrity checks
- ✅ **28-day rotation** - Keeps last 4 weeks, deletes older
- ✅ **GitHub Releases** - All backups stored with release metadata
- ✅ **S3 optional** - AWS S3 or compatible storage replication
- ✅ **Email reports** - HTML + text verification summaries
- ✅ **Multi-location** - GitHub + S3 for redundancy

## Optional Secrets (for features)

**Email Notifications:**
```
BACKUP_NOTIFICATION_EMAIL = ops@alreadyherellc.com
SMTP_USER = noreply@gmail.com
SMTP_PASSWORD = <app-specific-password>
SMTP_HOST = smtp.gmail.com
SMTP_PORT = 587
```

**S3 Distribution:**
```
S3_BUCKET = profitengine-backups
S3_ACCESS_KEY = AKIA...
S3_SECRET_KEY = <secret>
S3_ENDPOINT = https://s3.amazonaws.com
S3_REGION = us-east-1
```

## Backup Contents

**Included:**
- `.github/` - Workflows & CI config
- `scripts/` - Automation scripts
- `src/`, `datacenter/`, `deploy/` - Code & config
- `docs/` - Documentation
- `package.json`, `docker-compose.yml` - Configs

**Excluded:**
- `.git/` - Git repository (too large)
- `node_modules/` - Reinstallable dependencies
- `.env` - Secrets (explicitly excluded for security)
- `*.log` - Temporary files
- `__pycache__/` - Compiled cache

## Initial Setup

1. Generate encryption key:
   ```bash
   openssl rand -base64 32
   ```

2. Add to GitHub Secrets:
   - Go to **Settings → Secrets and variables → Actions**
   - Add `BACKUP_ENCRYPTION_KEY` with the key from step 1

3. Test the workflow:
   ```bash
   gh workflow run backup-rotation.yml
   ```

4. Monitor in GitHub Actions or check releases

For detailed setup, see: `docs/BACKUP-ROTATION-SETUP.md`

## Monitoring

```bash
# Watch latest run
gh run watch --repo quantam101/profitengine-v5 \
  $(gh run list --repo quantam101/profitengine-v5 \
    --workflow=backup-rotation.yml --json databaseId \
    --jq '.[0].databaseId')

# View logs
gh run view <RUN_ID> --log

# Check status
gh workflow view backup-rotation.yml --repo quantam101/profitengine-v5
```

## Troubleshooting

**Backup creation fails:**
- Check disk space on runner
- Verify file permissions
- Review archive exclusion patterns

**Email not sending:**
- Verify SMTP credentials (use app-specific passwords for Gmail)
- Check firewall isn't blocking SMTP port 587

**S3 upload fails:**
- Verify IAM credentials have S3 permissions
- Confirm bucket exists and is accessible

**Old backups not rotating:**
- Verify GitHub token has `contents: write` permission
- Check `RETENTION_DAYS` is set correctly

See `docs/BACKUP-ROTATION-SETUP.md` for full troubleshooting guide.

## Integration Example

Add to your deployment workflow to ensure backup before major changes:

```yaml
jobs:
  pre-deploy-backup:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger backup
        run: |
          gh workflow run backup-rotation.yml \
            --repo ${{ github.repository }}
```

## Email Notification Sample

```
From: noreply@github.com
Subject: ✅ Backup Verification Report - 2026-06-16 02:00:00 UTC

BACKUP DETAILS
Archive: profitengine-backup-20260616_020000.tar.gz
Size: 125432100 bytes
SHA256: a1b2c3d4e5f6...

ROTATION SUMMARY
Deleted: 1 (older than 28 days)
Retained: 4 (within 28 days)

VERIFICATION STATUS
Status: success
Total Backups: 4
```

## Links

- **Setup Guide**: `docs/BACKUP-ROTATION-SETUP.md`
- **Workflow File**: `.github/workflows/backup-rotation.yml`
- **GitHub Releases**: `https://github.com/quantam101/profitengine-v5/releases`

---

**Questions?** Check the full setup guide at `docs/BACKUP-ROTATION-SETUP.md`
