# Backup & Rotation - Quick Start

## 60-Second Setup

### 1. Generate Encryption Key
```bash
python -c "import secrets; print(secrets.token_hex(32))"
# Copy the output (64-char hex string)
```

### 2. Add to GitHub Secrets
Go to: **Settings → Secrets and variables → Actions → New repository secret**

| Secret Name | Value |
|-------------|-------|
| BACKUP_ENCRYPTION_KEY | [paste from step 1] |

### 3. Test It
**GitHub Actions → Weekly Backup & Rotation → Run workflow → Run workflow**

Monitor: Actions tab → latest run

**That's it!** Backups now run automatically every Monday at 02:00 UTC.

---

## Command Line (Local)

```bash
# Create backup
python scripts/backup_and_rotate.py

# Verify only (don't create new)
python scripts/backup_and_rotate.py --verify-only

# With S3 upload
ENABLE_S3=true python scripts/backup_and_rotate.py
```

---

## View Backups

```bash
# List all backups
gh release list --repo quantam101/profitengine-v5-final --limit 10

# Download specific backup
gh release download backup-YYYYMMDD_HHMMSS \
  --repo quantam101/profitengine-v5-final

# Verify integrity
sha256sum -c profitengine-backup-YYYYMMDD_HHMMSS.tar.gz.sha256

# Extract
tar -xzf profitengine-backup-YYYYMMDD_HHMMSS.tar.gz
```

---

## Optional: Email Notifications

Add these secrets for backup reports:

```
BACKUP_NOTIFICATION_EMAIL     = user@example.com
SMTP_USER                     = noreply@gmail.com
SMTP_PASSWORD                 = [Gmail app password]
```

[Gmail: Generate app password](https://myaccount.google.com/apppasswords)

---

## Optional: S3 Backup Distribution

Add these secrets for S3 upload:

```
S3_BUCKET         = my-backups
S3_ACCESS_KEY     = AKIA...
S3_SECRET_KEY     = [secret]
S3_ENDPOINT       = https://s3.amazonaws.com  (or your provider)
S3_REGION         = us-east-1
```

Then enable when running:
```bash
# Via GitHub Actions: Run workflow → enable_s3_distribution: true
# Via command line:
ENABLE_S3=true AWS_S3_BUCKET=... python scripts/backup_and_rotate.py
```

---

## Files

- **Workflow**: `.github/workflows/backup-rotation.yml` (658 lines)
- **Script**: `scripts/backup_and_rotate.py` (450+ lines)
- **Full Docs**: `docs/BACKUP-ROTATION-INTEGRATION.md`

---

## What Gets Backed Up

✅ Included:
- .github/ scripts/ src/ datacenter/ deploy/ runtime/ agents/ docs/
- package.json, docker-compose.yml, README.md, etc.

❌ Excluded:
- .git/, node_modules/, .env, __pycache__/, *.log

Archive size: ~50-100 MB (compressed)

---

## Retention Policy

Default: **28 days** (keeps ~4 weekly backups)

Change:
- Via GitHub Actions input: `retention_days` parameter
- Via command line: `--retention-days 14` (or any number)

---

## Troubleshooting

**Workflow fails**: Check `BACKUP_ENCRYPTION_KEY` is set in Secrets

**Email not working**: Verify SMTP_PASSWORD is a Gmail app password, not your regular password

**S3 upload fails**: Confirm bucket exists, access key is valid, region matches

See `docs/BACKUP-ROTATION-INTEGRATION.md` for detailed troubleshooting.

---

## Schedule

**Automatic**: Every Monday at 02:00 UTC

**Manual**: Anytime via GitHub Actions workflow_dispatch

---

## Status

✅ Workflow ready to deploy
✅ Python script tested
✅ All validations passing
✅ GitHub Releases integration ready

Start using: Add `BACKUP_ENCRYPTION_KEY` secret + run workflow!
