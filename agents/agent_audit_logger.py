"""
Immutable SQLite-based audit trail for agent proposals, executions, and outcomes.

Provides complete traceability of all agent decisions and actions with
tamper-evident timestamps, JSON serialization, and append-only design patterns.
"""

import sqlite3
import json
import hashlib
import threading
from datetime import datetime, timezone
from typing import Any, Dict, Optional, List, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum


class AuditEventType(Enum):
    """Enumeration of audit event types."""
    PROPOSAL = "proposal"
    EXECUTION = "execution"
    OUTCOME = "outcome"
    ERROR = "error"
    VALIDATION = "validation"


class AuditSeverity(Enum):
    """Audit event severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEntry:
    """Represents a single audit log entry."""
    event_type: str
    timestamp: str
    agent_id: str
    agent_name: str
    session_id: str
    proposal_id: Optional[str]
    execution_id: Optional[str]
    content: Dict[str, Any]
    severity: str = "info"
    metadata: Optional[Dict[str, Any]] = None
    hash_chain: Optional[str] = None
    entry_id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert entry to dictionary, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}


class AgentAuditLogger:
    """
    Immutable SQLite audit trail for agent activities.

    Features:
    - Append-only design (INSERT only, no UPDATE/DELETE)
    - Hash-chain integrity (each entry references previous hash)
    - JSON serialization for flexible content storage
    - Thread-safe operations with connection pooling
    - Automatic schema initialization
    - Integrity verification methods

    Attributes:
        db_path: Path to SQLite database file
        agent_id: Unique identifier for this agent instance
        agent_name: Human-readable agent name
        session_id: Current session identifier
    """

    # Schema version for compatibility checking
    SCHEMA_VERSION = 1

    # Thread-local storage for connections
    _thread_local = threading.local()

    def __init__(
        self,
        db_path: str = ".audit/agent_audit.db",
        agent_id: str = "default-agent",
        agent_name: str = "DefaultAgent",
        session_id: Optional[str] = None,
    ):
        """
        Initialize the audit logger.

        Args:
            db_path: Path to SQLite database file (auto-created)
            agent_id: Unique agent identifier
            agent_name: Human-readable agent name
            session_id: Optional session ID (auto-generated if not provided)
        """
        self.db_path = Path(db_path)
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.session_id = session_id or self._generate_session_id()
        self._last_hash: Optional[str] = None
        self._entry_count = 0
        self._lock = threading.RLock()

        # Ensure database directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize schema on first use
        self._initialize_schema()
        self._load_last_hash()

    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._thread_local, "connection"):
            self._thread_local.connection = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
                timeout=30.0,
            )
            self._thread_local.connection.row_factory = sqlite3.Row
        return self._thread_local.connection

    def _initialize_schema(self) -> None:
        """Initialize SQLite schema if it doesn't exist."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Metadata table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        # Main audit log table (append-only)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                session_id TEXT NOT NULL,
                proposal_id TEXT,
                execution_id TEXT,
                content TEXT NOT NULL,
                severity TEXT DEFAULT 'info',
                metadata TEXT,
                hash_chain TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                CHECK (severity IN ('info', 'warning', 'error', 'critical')),
                CHECK (event_type IN ('proposal', 'execution', 'outcome', 'error', 'validation'))
            )
        """)

        # Index for common queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_timestamp
            ON audit_log(session_id, timestamp DESC)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent_id
            ON audit_log(agent_id, created_at DESC)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_proposal_id
            ON audit_log(proposal_id) WHERE proposal_id IS NOT NULL
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_execution_id
            ON audit_log(execution_id) WHERE execution_id IS NOT NULL
        """)

        conn.commit()

        # Check schema version
        cursor.execute("SELECT value FROM audit_metadata WHERE key = ?", ("schema_version",))
        result = cursor.fetchone()
        if not result:
            cursor.execute(
                "INSERT INTO audit_metadata (key, value, created_at) VALUES (?, ?, ?)",
                ("schema_version", str(self.SCHEMA_VERSION), self._get_timestamp())
            )
            conn.commit()

    def _load_last_hash(self) -> None:
        """Load the last hash from the database for chain integrity."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT hash_chain, entry_id FROM audit_log
                ORDER BY entry_id DESC LIMIT 1
            """)
            result = cursor.fetchone()
            if result:
                self._last_hash = result["hash_chain"]
                self._entry_count = result["entry_id"]
            else:
                self._last_hash = None
                self._entry_count = 0

    @staticmethod
    def _generate_session_id() -> str:
        """Generate a unique session identifier."""
        ts = datetime.now(timezone.utc).isoformat()
        return hashlib.sha256(ts.encode()).hexdigest()[:16]

    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp in ISO 8601 format."""
        return datetime.now(timezone.utc).isoformat()

    def _compute_hash(self, entry_data: Dict[str, Any], previous_hash: Optional[str]) -> str:
        """
        Compute hash for an entry (hash-chain integrity).

        Args:
            entry_data: Dictionary of entry data
            previous_hash: Previous entry's hash for chaining

        Returns:
            SHA-256 hash as hex string
        """
        # Serialize entry data consistently
        entry_str = json.dumps(entry_data, sort_keys=True, separators=(',', ':'))

        # Chain with previous hash
        chain_input = f"{previous_hash or '0'}{entry_str}"
        return hashlib.sha256(chain_input.encode()).hexdigest()

    def log_proposal(
        self,
        proposal_id: str,
        proposal_content: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        severity: str = "info",
    ) -> Dict[str, Any]:
        """
        Log an agent proposal (decision point).

        Args:
            proposal_id: Unique proposal identifier
            proposal_content: Proposal data (objectives, constraints, options)
            metadata: Optional metadata (user_id, context_tags, etc.)
            severity: Event severity level

        Returns:
            Audit entry record with entry_id
        """
        with self._lock:
            entry = AuditEntry(
                event_type=AuditEventType.PROPOSAL.value,
                timestamp=self._get_timestamp(),
                agent_id=self.agent_id,
                agent_name=self.agent_name,
                session_id=self.session_id,
                proposal_id=proposal_id,
                execution_id=None,
                content=proposal_content,
                severity=severity,
                metadata=metadata,
            )

            # Compute hash chain
            entry_dict = entry.to_dict()
            entry_dict.pop("entry_id", None)
            entry_dict.pop("hash_chain", None)
            hash_value = self._compute_hash(entry_dict, self._last_hash)

            return self._write_entry(entry, hash_value)

    def log_execution(
        self,
        execution_id: str,
        proposal_id: Optional[str],
        execution_content: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        severity: str = "info",
    ) -> Dict[str, Any]:
        """
        Log an agent execution (action taken).

        Args:
            execution_id: Unique execution identifier
            proposal_id: Reference to originating proposal (if applicable)
            execution_content: Execution details (action, parameters, result)
            metadata: Optional metadata (duration_ms, resource_usage, etc.)
            severity: Event severity level

        Returns:
            Audit entry record with entry_id
        """
        with self._lock:
            entry = AuditEntry(
                event_type=AuditEventType.EXECUTION.value,
                timestamp=self._get_timestamp(),
                agent_id=self.agent_id,
                agent_name=self.agent_name,
                session_id=self.session_id,
                proposal_id=proposal_id,
                execution_id=execution_id,
                content=execution_content,
                severity=severity,
                metadata=metadata,
            )

            # Compute hash chain
            entry_dict = entry.to_dict()
            entry_dict.pop("entry_id", None)
            entry_dict.pop("hash_chain", None)
            hash_value = self._compute_hash(entry_dict, self._last_hash)

            return self._write_entry(entry, hash_value)

    def log_outcome(
        self,
        execution_id: str,
        proposal_id: Optional[str],
        outcome_content: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        severity: str = "info",
    ) -> Dict[str, Any]:
        """
        Log an execution outcome (results and effects).

        Args:
            execution_id: Reference to execution that produced outcome
            proposal_id: Reference to originating proposal (if applicable)
            outcome_content: Outcome data (success, effects, error messages)
            metadata: Optional metadata (validation_score, side_effects, etc.)
            severity: Event severity level

        Returns:
            Audit entry record with entry_id
        """
        with self._lock:
            entry = AuditEntry(
                event_type=AuditEventType.OUTCOME.value,
                timestamp=self._get_timestamp(),
                agent_id=self.agent_id,
                agent_name=self.agent_name,
                session_id=self.session_id,
                proposal_id=proposal_id,
                execution_id=execution_id,
                content=outcome_content,
                severity=severity,
                metadata=metadata,
            )

            # Compute hash chain
            entry_dict = entry.to_dict()
            entry_dict.pop("entry_id", None)
            entry_dict.pop("hash_chain", None)
            hash_value = self._compute_hash(entry_dict, self._last_hash)

            return self._write_entry(entry, hash_value)

    def _write_entry(self, entry: AuditEntry, hash_value: str) -> Dict[str, Any]:
        """
        Write entry to database (atomic operation).

        Args:
            entry: AuditEntry object
            hash_value: Computed hash for integrity

        Returns:
            Entry record with assigned entry_id
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        content_json = json.dumps(entry.content)
        metadata_json = json.dumps(entry.metadata) if entry.metadata else None

        cursor.execute("""
            INSERT INTO audit_log (
                event_type, timestamp, agent_id, agent_name, session_id,
                proposal_id, execution_id, content, severity, metadata, hash_chain
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry.event_type,
            entry.timestamp,
            entry.agent_id,
            entry.agent_name,
            entry.session_id,
            entry.proposal_id,
            entry.execution_id,
            content_json,
            entry.severity,
            metadata_json,
            hash_value,
        ))

        conn.commit()
        entry_id = cursor.lastrowid
        self._last_hash = hash_value
        self._entry_count = entry_id

        # Return complete entry record
        result = entry.to_dict()
        result["entry_id"] = entry_id
        result["hash_chain"] = hash_value
        return result

    def get_session_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve audit log for current session.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of audit entries (newest first)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT entry_id, event_type, timestamp, agent_id, agent_name,
                   session_id, proposal_id, execution_id, content, severity,
                   metadata, hash_chain, created_at
            FROM audit_log
            WHERE session_id = ?
            ORDER BY entry_id DESC
            LIMIT ?
        """, (self.session_id, limit))

        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def verify_integrity(self) -> Tuple[bool, str]:
        """
        Verify hash-chain integrity of entire audit log.

        Returns:
            Tuple of (is_valid, message)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT entry_id, event_type, timestamp, agent_id, agent_name,
                   session_id, proposal_id, execution_id, content, severity,
                   metadata, hash_chain
            FROM audit_log
            ORDER BY entry_id ASC
        """)

        rows = cursor.fetchall()
        if not rows:
            return True, "No entries to verify"

        previous_hash = None
        for row in rows:
            entry_dict = self._row_to_dict(row)
            stored_hash = entry_dict.pop("hash_chain")

            # Reconstruct hash
            computed_hash = self._compute_hash(entry_dict, previous_hash)
            if computed_hash != stored_hash:
                return False, f"Hash mismatch at entry_id={row['entry_id']}"

            previous_hash = stored_hash

        return True, f"Integrity verified: {len(rows)} entries"

    def get_proposal_chain(self, proposal_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all log entries for a specific proposal.

        Args:
            proposal_id: Proposal identifier to retrieve

        Returns:
            List of entries related to this proposal (chronological order)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT entry_id, event_type, timestamp, agent_id, agent_name,
                   session_id, proposal_id, execution_id, content, severity,
                   metadata, hash_chain, created_at
            FROM audit_log
            WHERE proposal_id = ?
            ORDER BY entry_id ASC
        """, (proposal_id,))

        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_execution_chain(self, execution_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all log entries for a specific execution.

        Args:
            execution_id: Execution identifier to retrieve

        Returns:
            List of entries related to this execution (chronological order)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT entry_id, event_type, timestamp, agent_id, agent_name,
                   session_id, proposal_id, execution_id, content, severity,
                   metadata, hash_chain, created_at
            FROM audit_log
            WHERE execution_id = ?
            ORDER BY entry_id ASC
        """, (execution_id,))

        return [self._row_to_dict(row) for row in cursor.fetchall()]

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
        """Convert SQLite Row to dictionary with JSON parsing."""
        d = dict(row)
        if d.get("content"):
            d["content"] = json.loads(d["content"])
        if d.get("metadata"):
            d["metadata"] = json.loads(d["metadata"])
        return d

    def close(self) -> None:
        """Close database connection."""
        if hasattr(self._thread_local, "connection"):
            self._thread_local.connection.close()
            delattr(self._thread_local, "connection")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
