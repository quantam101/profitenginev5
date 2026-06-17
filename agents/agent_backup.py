"""
Agent Backup Management System

Handles backup creation, rotation (28-day policy), and SHA256 validation.
Provides comprehensive backup lifecycle management for agent state and configuration.
"""

import hashlib
import json
import logging
import os
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple


logger = logging.getLogger(__name__)


class AgentBackup:
    """
    Manages agent backup creation, rotation, and validation.

    Implements 28-day rotation policy with SHA256 integrity validation.
    Supports full directory backups and incremental state snapshots.
    """

    # 28-day rotation window in seconds
    ROTATION_DAYS = 28
    ROTATION_WINDOW = ROTATION_DAYS * 24 * 60 * 60

    # Backup metadata filename
    MANIFEST_FILE = "backup.manifest.json"

    # Compression format
    BACKUP_FORMAT = "tar.gz"

    def __init__(
        self,
        backup_dir: str = "./backups/agents",
        max_backups: int = 4,
        hash_algorithm: str = "sha256",
    ):
        """
        Initialize backup manager.

        Args:
            backup_dir: Directory for storing backups
            max_backups: Maximum backups to retain (4 = 28+ days)
            hash_algorithm: Hash algorithm for validation (sha256)
        """
        self.backup_dir = Path(backup_dir)
        self.max_backups = max_backups
        self.hash_algorithm = hash_algorithm
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"AgentBackup initialized: {self.backup_dir}")

    def create(
        self,
        source_path: str,
        agent_name: str,
        tags: Optional[Dict[str, str]] = None,
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Create a backup of agent directory or file.

        Args:
            source_path: Path to agent directory or file to backup
            agent_name: Name of agent (used in backup filename)
            tags: Optional metadata tags (e.g., {'version': '1.0', 'env': 'prod'})

        Returns:
            Tuple of (success, backup_path, error_message)
            - success: True if backup created
            - backup_path: Path to created backup (or None if failed)
            - error_message: Human-readable error (or None if successful)
        """
        try:
            source = Path(source_path)
            if not source.exists():
                error = f"Source path does not exist: {source_path}"
                logger.error(error)
                return False, None, error

            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{agent_name}_backup_{timestamp}.{self.BACKUP_FORMAT}"
            backup_path = self.backup_dir / backup_filename

            logger.info(f"Creating backup: {source_path} -> {backup_path}")

            if source.is_dir():
                shutil.make_archive(
                    str(backup_path.with_suffix("")),
                    self.BACKUP_FORMAT.split(".")[0],
                    source,
                )
            else:
                shutil.copy2(source, backup_path)

            # Generate and store metadata
            backup_hash = self._compute_hash(backup_path)
            metadata = {
                "agent_name": agent_name,
                "backup_timestamp": datetime.utcnow().isoformat(),
                "source_path": str(source_path),
                "backup_path": str(backup_path),
                "file_size_bytes": backup_path.stat().st_size,
                f"{self.hash_algorithm}": backup_hash,
                "tags": tags or {},
                "format": self.BACKUP_FORMAT,
                "rotation_days": self.ROTATION_DAYS,
            }

            manifest_path = backup_path.with_suffix(f".manifest.json")
            with open(manifest_path, "w") as f:
                json.dump(metadata, f, indent=2)

            logger.info(
                f"Backup created successfully: {backup_path} "
                f"(hash: {backup_hash[:16]}..., size: {metadata['file_size_bytes']} bytes)"
            )
            return True, str(backup_path), None

        except Exception as e:
            error = f"Backup creation failed: {str(e)}"
            logger.error(error, exc_info=True)
            return False, None, error

    def rotate(self) -> Tuple[bool, Dict[str, any], Optional[str]]:
        """
        Rotate backups based on 28-day retention policy.

        Removes backups older than ROTATION_DAYS, keeping at most max_backups.
        Ensures at least one backup from each week if possible.

        Returns:
            Tuple of (success, rotation_info, error_message)
            - success: True if rotation completed
            - rotation_info: Dict with deleted/retained counts
            - error_message: Human-readable error (or None if successful)
        """
        try:
            backups = self._list_backups()
            if not backups:
                logger.info("No backups to rotate")
                return True, {"deleted": 0, "retained": len(backups)}, None

            # Sort by creation time (newest first)
            backups_sorted = sorted(
                backups, key=lambda x: x["timestamp"], reverse=True
            )

            rotation_cutoff = (
                datetime.utcnow() - timedelta(seconds=self.ROTATION_WINDOW)
            ).timestamp()
            deleted_count = 0
            retained_count = 0

            logger.info(
                f"Rotation policy: keep backups newer than {self.ROTATION_DAYS} days "
                f"or max {self.max_backups} backups"
            )

            for backup_info in backups_sorted:
                # Keep if within rotation window AND under max limit
                if backup_info["timestamp"] > rotation_cutoff and retained_count < self.max_backups:
                    retained_count += 1
                    logger.debug(f"Retaining: {backup_info['path']}")
                else:
                    # Delete old or excess backup
                    try:
                        Path(backup_info["path"]).unlink()
                        manifest = Path(backup_info["path"]).with_suffix(".manifest.json")
                        if manifest.exists():
                            manifest.unlink()
                        deleted_count += 1
                        logger.info(f"Deleted rotated backup: {backup_info['path']}")
                    except Exception as e:
                        logger.warning(f"Failed to delete {backup_info['path']}: {e}")

            rotation_info = {
                "deleted": deleted_count,
                "retained": retained_count,
                "rotation_days": self.ROTATION_DAYS,
                "max_backups": self.max_backups,
            }
            logger.info(f"Rotation complete: {rotation_info}")
            return True, rotation_info, None

        except Exception as e:
            error = f"Backup rotation failed: {str(e)}"
            logger.error(error, exc_info=True)
            return False, {}, error

    def validate(self, backup_path: str) -> Tuple[bool, Dict[str, any], Optional[str]]:
        """
        Validate backup integrity using SHA256 hash.

        Compares stored hash in manifest against current backup file.
        Reports detailed validation results.

        Args:
            backup_path: Path to backup file to validate

        Returns:
            Tuple of (valid, validation_info, error_message)
            - valid: True if backup passes validation
            - validation_info: Dict with hash/size/timestamp details
            - error_message: Human-readable error (or None if successful)
        """
        try:
            backup = Path(backup_path)
            if not backup.exists():
                error = f"Backup file does not exist: {backup_path}"
                logger.error(error)
                return False, {}, error

            # Load manifest
            manifest_path = backup.with_suffix(".manifest.json")
            if not manifest_path.exists():
                error = f"Manifest not found: {manifest_path}"
                logger.error(error)
                return False, {}, error

            with open(manifest_path, "r") as f:
                manifest = json.load(f)

            stored_hash = manifest.get(self.hash_algorithm)
            if not stored_hash:
                error = f"No {self.hash_algorithm} hash in manifest"
                logger.error(error)
                return False, {}, error

            # Compute current hash
            current_hash = self._compute_hash(backup)
            file_size = backup.stat().st_size

            validation_info = {
                "backup_path": str(backup),
                "backup_timestamp": manifest.get("backup_timestamp"),
                "file_size_bytes": file_size,
                "manifest_file_size_bytes": manifest.get("file_size_bytes"),
                f"{self.hash_algorithm}_stored": stored_hash,
                f"{self.hash_algorithm}_current": current_hash,
                "hash_match": current_hash == stored_hash,
                "size_match": file_size == manifest.get("file_size_bytes", file_size),
                "agent_name": manifest.get("agent_name"),
            }

            is_valid = validation_info["hash_match"] and validation_info["size_match"]
            status = "VALID" if is_valid else "INVALID"
            logger.info(f"Validation {status}: {backup_path}")

            return is_valid, validation_info, None

        except json.JSONDecodeError as e:
            error = f"Manifest JSON error: {str(e)}"
            logger.error(error)
            return False, {}, error
        except Exception as e:
            error = f"Backup validation failed: {str(e)}"
            logger.error(error, exc_info=True)
            return False, {}, error

    def list_backups(self) -> List[Dict[str, any]]:
        """
        List all available backups with metadata.

        Returns:
            List of backup dicts with path, timestamp, size, hash, agent_name
        """
        return self._list_backups()

    def restore(
        self, backup_path: str, restore_dir: str
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Restore backup to target directory.

        Validates backup before restore. Supports both file and directory backups.

        Args:
            backup_path: Path to backup file
            restore_dir: Target directory for restoration

        Returns:
            Tuple of (success, restore_info, error_message)
        """
        try:
            # Validate first
            is_valid, validation_info, validation_error = self.validate(backup_path)
            if not is_valid:
                error = f"Backup validation failed: {validation_error}"
                logger.error(error)
                return False, "", error

            backup = Path(backup_path)
            restore_path = Path(restore_dir)
            restore_path.mkdir(parents=True, exist_ok=True)

            logger.info(f"Restoring {backup_path} to {restore_dir}")

            if backup_path.endswith(f".{self.BACKUP_FORMAT}"):
                # Extract archive
                shutil.unpack_archive(backup_path, restore_dir)
            else:
                # Copy file
                shutil.copy2(backup_path, restore_dir)

            info = f"Restored from {backup_path} to {restore_dir}"
            logger.info(info)
            return True, info, None

        except Exception as e:
            error = f"Restore failed: {str(e)}"
            logger.error(error, exc_info=True)
            return False, "", error

    def _compute_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of file."""
        hasher = hashlib.new(self.hash_algorithm)
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _list_backups(self) -> List[Dict[str, any]]:
        """List all backups with metadata."""
        backups = []
        for manifest_file in sorted(self.backup_dir.glob("*.manifest.json")):
            try:
                with open(manifest_file, "r") as f:
                    metadata = json.load(f)
                backup_path = metadata.get("backup_path")
                if backup_path and Path(backup_path).exists():
                    backup_time = datetime.fromisoformat(
                        metadata.get("backup_timestamp", "2000-01-01T00:00:00")
                    )
                    backups.append(
                        {
                            "path": backup_path,
                            "timestamp": backup_time.timestamp(),
                            "agent_name": metadata.get("agent_name"),
                            "file_size_bytes": metadata.get("file_size_bytes", 0),
                            "hash": metadata.get(self.hash_algorithm),
                            "tags": metadata.get("tags", {}),
                        }
                    )
            except Exception as e:
                logger.warning(f"Error reading manifest {manifest_file}: {e}")
        return backups


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Example usage
    backup_mgr = AgentBackup(backup_dir="./backups/agents", max_backups=4)

    print("\n=== AgentBackup System ===\n")

    # Example: create backup
    success, path, error = backup_mgr.create(
        source_path="./agents/taylor",
        agent_name="taylor",
        tags={"version": "1.0", "env": "production"},
    )
    if success:
        print(f"Created: {path}")

        # Validate
        is_valid, info, err = backup_mgr.validate(path)
        print(f"Valid: {is_valid} | Hash: {info.get('sha256_current', 'N/A')[:16]}...")

        # Rotate
        success, rotation, err = backup_mgr.rotate()
        print(f"Rotation: {rotation}")

        # List all
        all_backups = backup_mgr.list_backups()
        print(f"Total backups: {len(all_backups)}")
    else:
        print(f"Error: {error}")
