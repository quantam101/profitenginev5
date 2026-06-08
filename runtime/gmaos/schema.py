"""
G-MAOS Schema — canonical data contracts for the mesh.
All dataclasses are frozen (immutable after creation).
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TaskPriority(int, Enum):
    CRITICAL   = 0   # pre-empts everything; reserved for health probes
    HIGH       = 1   # revenue-impacting agents
    NORMAL     = 2   # content, social, POD (default)
    LOW        = 3   # housekeeping, analytics
    BACKGROUND = 4   # long-running distillation jobs


class TaskStatus(str, Enum):
    PENDING           = "PENDING"
    QUEUED            = "QUEUED"
    RUNNING           = "RUNNING"
    COMPLETED         = "COMPLETED"
    COMPLETED_LOCAL   = "COMPLETED_LOCAL"    # served from offline cache
    COMPLETED_DISTILL = "COMPLETED_DISTILL"  # served from distilled snapshot
    RETRYING          = "RETRYING"
    DLQ               = "DLQ"               # dead-letter queue
    FAILED            = "FAILED"


class AgentStatus(str, Enum):
    HEALTHY   = "HEALTHY"
    DEGRADED  = "DEGRADED"   # circuit half-open
    OFFLINE   = "OFFLINE"    # circuit open
    UNKNOWN   = "UNKNOWN"


@dataclass(frozen=True)
class Task:
    """One unit of work submitted to the mesh."""
    agent: str                                # maps to runtime.agent_impls.<agent>
    payload: dict[str, Any]                   # free-form task input
    id: str            = field(default_factory=lambda: str(uuid.uuid4()))
    priority: TaskPriority = TaskPriority.NORMAL
    max_retries: int   = 3
    timeout_sec: float = 120.0
    trace_id: str      = field(default_factory=lambda: uuid.uuid4().hex[:12])
    submitted_at: float = field(default_factory=time.time)
    # If set, bypass the inference cascade and return a canned response (testing)
    _stub_response: str | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True)
class MeshResult:
    """Outcome of a single Task execution."""
    task_id:      str
    agent:        str
    status:       TaskStatus
    output:       str
    tier:         str          # which inference tier was used (or "cache", "dlq", etc.)
    duration_ms:  int
    retry_count:  int
    cached:       bool
    trace_id:     str
    error:        str = ""
    tokens_in:    int = 0
    tokens_out:   int = 0
    distilled:    bool = False
