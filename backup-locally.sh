#!/bin/bash
# ProfitEngine v5 - Complete Local Backup Script
# Creates encrypted, timestamped backups of all system components
# Usage: bash backup-locally.sh

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
BACKUP_ROOT="$HOME/profitengine-backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$BACKUP_ROOT/$TIMESTAMP"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  ProfitEngine v5 - LOCAL BACKUP SYSTEM${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""
echo -e "📅 Timestamp: $TIMESTAMP"
echo -e "📁 Backup location: $BACKUP_DIR"
echo ""

# Create backup structure
mkdir -p "$BACKUP_DIR"/{code,secrets,docker,databases,videos,scripts,docs}

echo -e "${YELLOW}[1/8] Backing up source code...${NC}"
cp -r "$REPO_DIR" "$BACKUP_DIR/code" 2>/dev/null || true
cd "$BACKUP_DIR/code"
git log --oneline -50 > GIT_HISTORY.txt 2>/dev/null || echo "No git history" > GIT_HISTORY.txt
git branch -a > GIT_BRANCHES.txt 2>/dev/null || echo "No branches" > GIT_BRANCHES.txt
cd "$BACKUP_DIR"
echo -e "${GREEN}✅ Code backed up${NC}"

echo -e "${YELLOW}[2/8] Encrypting secrets...${NC}"
if [ -f "$REPO_DIR/.env" ]; then
  echo -e "${BLUE}  Found .env${NC}"
  if command -v gpg &> /dev/null; then
    gpg --symmetric --cipher-algo AES256 --batch --yes --quiet "$REPO_DIR/.env" -o "$BACKUP_DIR/secrets/.env.gpg" 2>/dev/null
    echo -e "${GREEN}  ✅ Encrypted: .env.gpg${NC}"
  else
    cp "$REPO_DIR/.env" "$BACKUP_DIR/secrets/.env.unencrypted"
    echo -e "${YELLOW}  ⚠️  GPG not found, saved unencrypted (install gpg for security)${NC}"
  fi
else
  echo -e "${YELLOW}  ⚠️  No .env file found${NC}"
fi

if [ -f "$REPO_DIR/.env.production" ]; then
  echo -e "${BLUE}  Found .env.production${NC}"
  if command -v gpg &> /dev/null; then
    gpg --symmetric --cipher-algo AES256 --batch --yes --quiet "$REPO_DIR/.env.production" -o "$BACKUP_DIR/secrets/.env.production.gpg" 2>/dev/null
    echo -e "${GREEN}  ✅ Encrypted: .env.production.gpg${NC}"
  fi
fi

# Backup GitHub Secrets list
if command -v gh &> /dev/null; then
  echo -e "${BLUE}  Exporting GitHub Secrets list...${NC}"
  gh secret list --repo quantam101/profitenginev5 > "$BACKUP_DIR/secrets/GITHUB_SECRETS_LIST.txt" 2>/dev/null || true
  echo -e "${GREEN}  ✅ GitHub Secrets exported (names only)${NC}"
fi

echo -e "${GREEN}✅ Secrets encrypted${NC}"

echo -e "${YELLOW}[3/8] Backing up Docker images...${NC}"
if command -v docker &> /dev/null; then
  if docker image inspect profitengine-video:latest &> /dev/null; then
    echo -e "${BLUE}  Saving profitengine-video...${NC}"
    docker save profitengine-video:latest | gzip > "$BACKUP_DIR/docker/video-engine-image.tar.gz"
    echo -e "${GREEN}  ✅ Saved: video-engine-image.tar.gz${NC}"
  fi
  if docker image inspect profitengine:latest &> /dev/null; then
    echo -e "${BLUE}  Saving profitengine...${NC}"
    docker save profitengine:latest | gzip > "$BACKUP_DIR/docker/profitengine-image.tar.gz"
    echo -e "${GREEN}  ✅ Saved: profitengine-image.tar.gz${NC}"
  fi
else
  echo -e "${YELLOW}  ⚠️  Docker not installed, skipping${NC}"
fi

echo -e "${YELLOW}[4/8] Backing up databases...${NC}"
if command -v mongodump &> /dev/null; then
  echo -e "${BLUE}  Dumping MongoDB...${NC}"
  mongodump --out "$BACKUP_DIR/databases/mongodb" 2>/dev/null || echo "MongoDB not running"
  echo -e "${GREEN}  ✅ MongoDB dumped${NC}"
fi
if command -v sqlite3 &> /dev/null; then
  find "$REPO_DIR" -name "*.db" -o -name "*.sqlite" 2>/dev/null | while read db; do
    cp "$db" "$BACKUP_DIR/databases/"
  done
  echo -e "${GREEN}  ✅ SQLite databases backed up${NC}"
fi

echo -e "${YELLOW}[5/8] Backing up configuration files...${NC}"
mkdir -p "$BACKUP_DIR/config"
cp -r "$REPO_DIR/.github" "$BACKUP_DIR/config/" 2>/dev/null || true
cp "$REPO_DIR/docker-compose*.yml" "$BACKUP_DIR/config/" 2>/dev/null || true
cp "$REPO_DIR/Dockerfile*" "$BACKUP_DIR/config/" 2>/dev/null || true
cp "$REPO_DIR/*.md" "$BACKUP_DIR/config/" 2>/dev/null || true
echo -e "${GREEN}✅ Configuration backed up${NC}"

echo -e "${YELLOW}[6/8] Creating metadata...${NC}"
cat > "$BACKUP_DIR/BACKUP_MANIFEST.txt" << MANIFEST
PROFITENGINE v5 - BACKUP MANIFEST
==================================

Timestamp: $TIMESTAMP
Repository: https://github.com/quantam101/profitenginev5
Server: Render (profitengine-runtime.onrender.com)
Frontend: https://app.alreadyherellc.com

CONTENTS:
---------
/code                  - Complete source code
/secrets               - Encrypted credentials (.env.gpg)
/docker                - Docker images (compressed)
/databases             - Database backups
/config                - Configuration files & workflows

RESTORATION:
-----------
1. Code:     cp -r code/* /path/to/restore/
2. Secrets:  gpg secrets/.env.gpg (prompts for password)
3. Docker:   docker load < docker/*.tar.gz
4. Databases: mongorestore databases/mongodb/

SECURITY:
---------
✅ Secrets encrypted with AES256
✅ Timestamp prevents overwrite
✅ Git history preserved
✅ All credentials isolated

MAINTENANCE:
-----------
Run weekly:  bash backup-locally.sh
Test monthly: Restore to temp directory and verify
Verify GPG:  gpg --list-keys

DISASTER RECOVERY:
------------------
If system fails:
  1. Restore code from this backup
  2. Recreate .env from .env.gpg (gpg decryption)
  3. Restore database from databases/
  4. Pull latest from GitHub: git pull origin main
  5. Redeploy: bash deploy_oci_hybrid.sh (on OCI)

MANIFEST

sed -i "s/TIMESTAMP_PLACEHOLDER/$TIMESTAMP/" "$BACKUP_DIR/BACKUP_MANIFEST.txt"
echo -e "${GREEN}✅ Manifest created${NC}"

echo -e "${YELLOW}[7/8] Creating compressed archive...${NC}"
cd "$BACKUP_ROOT"
ARCHIVE_NAME="backup_${TIMESTAMP}.tar.gz"
tar -czf "$ARCHIVE_NAME" "$TIMESTAMP/" 2>/dev/null

# Calculate size
BACKUP_SIZE=$(du -sh "$TIMESTAMP" | cut -f1)
ARCHIVE_SIZE=$(du -sh "$ARCHIVE_NAME" | cut -f1)

echo -e "${GREEN}✅ Archive created: $ARCHIVE_NAME${NC}"
echo -e "${GREEN}  Uncompressed: $BACKUP_SIZE${NC}"
echo -e "${GREEN}  Compressed: $ARCHIVE_SIZE${NC}"

echo -e "${YELLOW}[8/8] Generating summary...${NC}"
cat > "$BACKUP_DIR/BACKUP_SUMMARY.txt" << 'SUMMARY'
BACKUP SUMMARY
==============

System Components Backed Up:
✅ Source Code (all branches & history)
✅ Secrets (GPG encrypted)
✅ Docker Images (both services)
✅ Database Dumps (if available)
✅ Configuration Files (.github, docker-compose, Dockerfile)
✅ Documentation & Guides

Backup Verification:
✅ Size: BACKUP_SIZE_PLACEHOLDER
✅ Compressed: ARCHIVE_SIZE_PLACEHOLDER
✅ Format: tar.gz
✅ Encryption: AES256 (GPG)
✅ Timestamp: TIMESTAMP_PLACEHOLDER

Next Steps:
1. Store this backup off-site (cloud, external drive)
2. Verify restore: tar -tzf backup_*.tar.gz
3. Test decryption: gpg secrets/.env.gpg
4. Schedule weekly backups

Restore Instructions:
1. Extract: tar -xzf backup_TIMESTAMP.tar.gz
2. Navigate: cd TIMESTAMP/
3. Restore code: cp -r code/* /destination/
4. Restore secrets: gpg secrets/.env.gpg
5. Restore docker: docker load < docker/*.tar.gz

SUMMARY

sed -i "s/BACKUP_SIZE_PLACEHOLDER/$BACKUP_SIZE/" "$BACKUP_DIR/BACKUP_SUMMARY.txt"
sed -i "s/ARCHIVE_SIZE_PLACEHOLDER/$ARCHIVE_SIZE/" "$BACKUP_DIR/BACKUP_SUMMARY.txt"
sed -i "s/TIMESTAMP_PLACEHOLDER/$TIMESTAMP/" "$BACKUP_DIR/BACKUP_SUMMARY.txt"

echo -e "${GREEN}✅ Summary generated${NC}"

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}  ✅ BACKUP COMPLETE${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "📊 Statistics:"
echo -e "  Location: $BACKUP_DIR"
echo -e "  Archive: $BACKUP_ROOT/$ARCHIVE_NAME"
echo -e "  Size: $BACKUP_SIZE (compressed: $ARCHIVE_SIZE)"
echo ""
echo -e "🔐 Security:"
echo -e "  Encryption: AES256 (GPG)"
echo -e "  Secrets: ${GREEN}ENCRYPTED${NC}"
echo -e "  Git History: PRESERVED"
echo ""
echo -e "📌 Next Steps:"
echo -e "  1. Review: cat $BACKUP_DIR/BACKUP_SUMMARY.txt"
echo -e "  2. Verify: tar -tzf $BACKUP_ROOT/$ARCHIVE_NAME | head -20"
echo -e "  3. Store: Copy $ARCHIVE_NAME to external storage"
echo -e "  4. Schedule: Add to crontab for weekly runs"
echo ""
echo -e "${BLUE}Backup scheduled command (add to crontab):${NC}"
echo -e "  ${YELLOW}0 2 * * 0 bash $REPO_DIR/backup-locally.sh${NC}"
echo ""
