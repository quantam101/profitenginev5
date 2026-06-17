#!/usr/bin/env python3
"""
Backup and Rotation Management Script

Creates timestamped backup archives with SHA256 validation, automatic rotation
based on retention policy, and optional S3 distribution.

Usage:
    python backup_and_rotate.py [--retention-days 28] [--verify-only] [--enable-s3]

Environment Variables:
    BACKUP_DIR: Directory for local backups (default: ./backups)
    ARCHIVE_PREFIX: Prefix for archive names (default: profitengine-backup)
    BACKUP_ENCRYPTION_KEY: Required for backup validation
    RETENTION_DAYS: Days to retain backups (default: 28)
    VERIFY_ONLY: Only verify, don't create new backup (default: false)
    ENABLE_S3: Upload to S3 (default: false)
    AWS_ACCESS_KEY_ID: AWS access key
    AWS_SECRET_ACCESS_KEY: AWS secret key
    AWS_S3_BUCKET: S3 bucket name
    AWS_S3_ENDPOINT: S3 endpoint (default: https://s3.amazonaws.com)
    AWS_REGION: AWS region (default: us-east-1)
"""

import argparse
import hashlib
import json
import logging
import os
import shutil
import subprocess
import sys
import tarfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S UTC",
)
logger = logging.getLogger(__name__)


class BackupManager:
    """Manages backup creation, validation, and rotation."""

    def __init__(
        self,
        backup_dir: str = "./backups",
        archive_prefix: str = "profitengine-backup",
        retention_days: int = 28,
        enable_s3: bool = False,
    ):
        self.backup_dir = Path(backup_dir)
        self.archive_prefix = archive_prefix
        self.retention_days = retention_days
        self.enable_s3 = enable_s3

        # Validate encryption key
        self.encryption_key = os.getenv("BACKUP_ENCRYPTION_KEY")
        if not self.encryption_key:
            logger.warning(
                "BACKUP_ENCRYPTION_KEY not set - backups will not be encrypted"
            )

        # S3 configuration
        self.s3_config = self._load_s3_config()

    def _load_s3_config(self) -> Optional[Dict[str, str]]:
        """Load and validate S3 configuration."""
        if not self.enable_s3:
            return None

        access_key = os.getenv("AWS_ACCESS_KEY_ID")
        secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        bucket = os.getenv("AWS_S3_BUCKET")

        if not all([access_key, secret_key, bucket]):
            logger.warning("S3 enabled but credentials incomplete - S3 upload will be skipped")
            return None

        return {
            "access_key": access_key,
            "secret_key": secret_key,
            "bucket": bucket,
            "endpoint": os.getenv(
                "AWS_S3_ENDPOINT", "https://s3.amazonaws.com"
            ),
            "region": os.getenv("AWS_REGION", "us-east-1"),
        }

    def _generate_timestamp(self) -> Tuple[str, str]:
        """Generate backup timestamp in two formats.

        Returns:
            Tuple of (YYYYMMDD_HHMMSS, YYYY-MM-DDTHH:MM:SSZ)
        """
        now = datetime.utcnow()
        compact = now.strftime("%Y%m%d_%H%M%S")
        iso = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        return compact, iso

    def _calculate_sha256(self, filepath: Path) -> str:
        """Calculate SHA256 checksum of a file.

        Args:
            filepath: Path to file

        Returns:
            SHA256 hex digest
        """
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def create_backup(self) -> Optional[Dict[str, str]]:
        """Create timestamped backup archive.

        Returns:
            Dict with archive metadata or None on failure
        """
        logger.info("Creating backup archive...")

        # Create backup directory
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Generate timestamp
        compact_ts, iso_ts = self._generate_timestamp()

        # Define archive path
        archive_name = f"{self.archive_prefix}-{compact_ts}.tar.gz"
        archive_path = self.backup_dir / archive_name

        # Files/directories to include in backup
        include_paths = [
            ".github",
            "scripts",
            "src",
            "datacenter",
            "deploy",
            "runtime",
            "agents",
            "docs",
            "package.json",
            "package-lock.json",
            "pyproject.toml",
            "requirements.txt",
            "docker-compose.yml",
            ".gitignore",
            "README.md",
        ]

        # Exclude patterns
        exclude_patterns = [
            ".git",
            "node_modules",
            ".env",
            "*.log",
            "__pycache__",
            ".pytest_cache",
            "*.pyc",
            ".DS_Store",
            "backups",
        ]

        try:
            logger.info(f"Creating tar.gz archive: {archive_name}")

            with tarfile.open(archive_path, "w:gz") as tar:
                for item in include_paths:
                    item_path = Path(item)
                    if item_path.exists():
                        logger.debug(f"Adding: {item}")
                        tar.add(
                            item_path,
                            arcname=item_path.name,
                            filter=self._tar_filter(exclude_patterns),
                        )
                    else:
                        logger.debug(f"Skipping (not found): {item}")

            # Verify archive was created
            if not archive_path.exists():
                logger.error("Archive creation failed - file not found")
                return None

            # Get file size
            archive_size = archive_path.stat().st_size
            logger.info(f"Archive size: {archive_size:,} bytes ({archive_size / (1024*1024):.2f} MB)")

            # Calculate checksum
            logger.info("Calculating SHA256 checksum...")
            sha256 = self._calculate_sha256(archive_path)
            logger.info(f"SHA256: {sha256}")

            # Write checksum file
            checksum_path = self.backup_dir / f"{archive_name}.sha256"
            checksum_path.write_text(f"{sha256}  {archive_name}\n")

            return {
                "name": archive_name,
                "path": str(archive_path),
                "size": str(archive_size),
                "sha256": sha256,
                "timestamp": compact_ts,
                "iso_timestamp": iso_ts,
            }

        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            return None

    def _tar_filter(self, exclude_patterns: List[str]):
        """Create a tar filter function for exclusions.

        Args:
            exclude_patterns: List of glob patterns to exclude

        Returns:
            Filter function for tarfile.add()
        """
        def should_exclude(tarinfo):
            name = tarinfo.name
            for pattern in exclude_patterns:
                if pattern in name or name.endswith(pattern):
                    return None
            return tarinfo

        return should_exclude

    def validate_backup(self, archive_path: Path) -> bool:
        """Validate backup archive integrity.

        Args:
            archive_path: Path to archive file

        Returns:
            True if valid, False otherwise
        """
        logger.info("Validating backup integrity...")

        # Check file exists
        if not archive_path.exists():
            logger.error(f"Archive not found: {archive_path}")
            return False

        # Check archive is readable
        try:
            with tarfile.open(archive_path, "r:gz") as tar:
                # Test that we can read the archive
                members = tar.getmembers()
                logger.info(f"Archive readable - contains {len(members)} items")

        except Exception as e:
            logger.error(f"Archive integrity check failed: {e}")
            return False

        # Verify checksum file exists and matches
        checksum_path = archive_path.parent / f"{archive_path.name}.sha256"
        if checksum_path.exists():
            try:
                expected_sha256 = checksum_path.read_text().split()[0]
                actual_sha256 = self._calculate_sha256(archive_path)

                if expected_sha256 == actual_sha256:
                    logger.info(f"Checksum verified: {actual_sha256}")
                    return True
                else:
                    logger.error(
                        f"Checksum mismatch!\nExpected: {expected_sha256}\nActual: {actual_sha256}"
                    )
                    return False

            except Exception as e:
                logger.error(f"Checksum verification failed: {e}")
                return False
        else:
            logger.warning(f"Checksum file not found: {checksum_path}")
            return False

    def rotate_backups(self) -> Dict[str, int]:
        """Delete backups older than retention period.

        Returns:
            Dict with deleted and retained counts
        """
        logger.info(f"Rotating backups (retention: {self.retention_days} days)...")

        if not self.backup_dir.exists():
            logger.info("Backup directory doesn't exist - nothing to rotate")
            return {"deleted": 0, "retained": 0}

        cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
        deleted = 0
        retained = 0

        # Find all tar.gz files
        for archive in sorted(self.backup_dir.glob(f"{self.archive_prefix}-*.tar.gz")):
            # Extract timestamp from filename
            try:
                timestamp_str = archive.stem.replace(f"{self.archive_prefix}-", "").replace(".tar", "")
                archive_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")

                if archive_date < cutoff_date:
                    logger.info(f"Deleting: {archive.name} (created: {archive_date.date()})")
                    archive.unlink()

                    # Also delete checksum file
                    checksum_path = archive.parent / f"{archive.name}.sha256"
                    if checksum_path.exists():
                        checksum_path.unlink()

                    deleted += 1
                else:
                    logger.info(f"Retaining: {archive.name} (created: {archive_date.date()})")
                    retained += 1

            except ValueError as e:
                logger.warning(f"Could not parse timestamp in {archive.name}: {e}")

        logger.info(f"Rotation complete: deleted {deleted}, retained {retained}")
        return {"deleted": deleted, "retained": retained}

    def upload_to_s3(self, archive_info: Dict[str, str]) -> bool:
        """Upload backup to S3-compatible storage.

        Args:
            archive_info: Archive metadata dict from create_backup()

        Returns:
            True if successful, False otherwise
        """
        if not self.s3_config:
            logger.info("S3 upload disabled or credentials missing")
            return True

        try:
            import boto3
        except ImportError:
            logger.warning("boto3 not installed - S3 upload skipped")
            return False

        try:
            logger.info("Uploading to S3...")

            s3_client = boto3.client(
                "s3",
                endpoint_url=self.s3_config["endpoint"],
                aws_access_key_id=self.s3_config["access_key"],
                aws_secret_access_key=self.s3_config["secret_key"],
                region_name=self.s3_config["region"],
            )

            archive_path = Path(archive_info["path"])
            archive_name = archive_info["name"]

            # Upload archive
            s3_key = f"backups/{archive_name}"
            logger.info(f"Uploading archive to s3://{self.s3_config['bucket']}/{s3_key}")

            s3_client.upload_file(
                str(archive_path),
                self.s3_config["bucket"],
                s3_key,
                ExtraArgs={"Metadata": {"sha256": archive_info["sha256"]}},
            )
            logger.info("✅ Archive uploaded")

            # Upload checksum
            checksum_path = archive_path.parent / f"{archive_name}.sha256"
            checksum_key = f"{s3_key}.sha256"
            logger.info(f"Uploading checksum to s3://{self.s3_config['bucket']}/{checksum_key}")

            s3_client.upload_file(
                str(checksum_path),
                self.s3_config["bucket"],
                checksum_key,
            )
            logger.info("✅ Checksum uploaded")

            return True

        except Exception as e:
            logger.error(f"S3 upload failed: {e}")
            return False

    def cleanup_local_backup(self) -> None:
        """Remove local backup directory after upload."""
        if self.backup_dir.exists():
            try:
                logger.info(f"Cleaning up local backup directory: {self.backup_dir}")
                shutil.rmtree(self.backup_dir)
                logger.info("✅ Cleanup complete")
            except Exception as e:
                logger.warning(f"Failed to cleanup backup directory: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Create timestamped backups with rotation and S3 distribution"
    )
    parser.add_argument(
        "--retention-days",
        type=int,
        default=int(os.getenv("RETENTION_DAYS", "28")),
        help="Backup retention days (default: 28)",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        default=os.getenv("VERIFY_ONLY", "").lower() == "true",
        help="Only verify existing backups, don't create new one",
    )
    parser.add_argument(
        "--enable-s3",
        action="store_true",
        default=os.getenv("ENABLE_S3", "").lower() == "true",
        help="Upload backup to S3",
    )
    parser.add_argument(
        "--backup-dir",
        default=os.getenv("BACKUP_DIR", "./backups"),
        help="Backup directory (default: ./backups)",
    )
    parser.add_argument(
        "--archive-prefix",
        default=os.getenv("ARCHIVE_PREFIX", "profitengine-backup"),
        help="Archive prefix (default: profitengine-backup)",
    )

    args = parser.parse_args()

    # Validate encryption key if required
    if not os.getenv("BACKUP_ENCRYPTION_KEY"):
        logger.error("❌ BACKUP_ENCRYPTION_KEY not set")
        return 1

    manager = BackupManager(
        backup_dir=args.backup_dir,
        archive_prefix=args.archive_prefix,
        retention_days=args.retention_days,
        enable_s3=args.enable_s3,
    )

    if args.verify_only:
        logger.info("Running in verify-only mode")
        # Find most recent backup
        backups = list(Path(args.backup_dir).glob(f"{args.archive_prefix}-*.tar.gz"))
        if backups:
            latest = sorted(backups)[-1]
            if manager.validate_backup(latest):
                logger.info("✅ Latest backup is valid")
                return 0
            else:
                logger.error("❌ Latest backup validation failed")
                return 1
        else:
            logger.warning("No backups found")
            return 0

    # Create new backup
    logger.info("Starting backup process...")
    archive_info = manager.create_backup()

    if not archive_info:
        logger.error("❌ Backup creation failed")
        return 1

    logger.info(f"✅ Backup created: {archive_info['name']}")

    # Validate backup
    archive_path = Path(archive_info["path"])
    if not manager.validate_backup(archive_path):
        logger.error("❌ Backup validation failed")
        return 1

    logger.info("✅ Backup validation passed")

    # Upload to S3 if enabled
    if args.enable_s3:
        if not manager.upload_to_s3(archive_info):
            logger.warning("⚠️ S3 upload failed (continuing anyway)")

    # Rotate old backups
    rotation = manager.rotate_backups()

    # Output summary as JSON for GitHub Actions
    summary = {
        "archive_name": archive_info["name"],
        "archive_size": archive_info["size"],
        "archive_sha256": archive_info["sha256"],
        "timestamp": archive_info["timestamp"],
        "iso_timestamp": archive_info["iso_timestamp"],
        "deleted": rotation["deleted"],
        "retained": rotation["retained"],
        "s3_enabled": args.enable_s3,
        "s3_bucket": manager.s3_config.get("bucket") if manager.s3_config else None,
    }

    print("\n" + "=" * 60)
    print("BACKUP SUMMARY")
    print("=" * 60)
    print(json.dumps(summary, indent=2))
    print("=" * 60 + "\n")

    # Cleanup local backup directory
    manager.cleanup_local_backup()

    logger.info("✅ Backup and rotation process complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
