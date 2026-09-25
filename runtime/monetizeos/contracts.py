"""Explicit task contracts and completion reports (MonetizeOS spec §3).

Every delegated task carries a TaskContract; every completion carries a
CompletionReport.  An agent's declaration of success is not evidence —
the store only accepts a report whose declared tests actually ran.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class TaskContract:
    task_id: str
    process_owner: str            # one of SPECIALIST_ROLES
    objective: str
    business_purpose: str
    input_artifacts: list[str] = field(default_factory=list)   # "path@version" refs
    dependencies: list[str] = field(default_factory=list)      # task_ids
    allowed_files: list[str] = field(default_factory=list)     # glob-ish prefixes
    allowed_tools: list[str] = field(default_factory=list)
    external_actions: list[str] = field(default_factory=list)
    required_outputs: list[str] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)
    verification_method: str = ""
    budget_seconds: float = 3600.0
    budget_tokens: int = 0                                     # 0 = unbounded (local)
    budget_usd: float = 0.0                                    # zero-spend default
    retry_limit: int = 2
    escalation: str = "director"                               # who to escalate to
    idempotency_key: str = ""

    def validate(self) -> list[str]:
        errors: list[str] = []
        for attr in ("task_id", "process_owner", "objective", "verification_method"):
            if not getattr(self, attr):
                errors.append(f"{attr} is required")
        if self.budget_seconds <= 0:
            errors.append("budget_seconds must be positive")
        if self.retry_limit < 0:
            errors.append("retry_limit must be >= 0")
        return errors

    def fingerprint(self) -> str:
        """Stable hash of the execution-relevant contract fields.  When the
        contract changes, artifacts produced under the old fingerprint are stale."""
        payload = {
            k: getattr(self, k)
            for k in (
                "process_owner", "objective", "input_artifacts", "dependencies",
                "required_outputs", "acceptance_criteria", "verification_method",
            )
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


@dataclass
class CompletionReport:
    task_id: str
    status: str                              # completed | failed | blocked
    artifact_refs: list[str] = field(default_factory=list)
    files_changed: list[str] = field(default_factory=list)
    tests_run: list[dict[str, Any]] = field(default_factory=list)  # {name, command, result}
    assumptions: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    remaining_risks: list[str] = field(default_factory=list)
    tokens_used: int = 0
    cost_usd: float = 0.0
    duration_seconds: float = 0.0

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.status not in ("completed", "failed", "blocked"):
            errors.append(f"invalid status {self.status!r}")
        if self.status == "completed" and not self.tests_run:
            errors.append("a completed report must list the tests that actually ran")
        if self.status == "completed" and not all(t.get("result") == "passed" for t in self.tests_run):
            errors.append("completed status requires every recorded test to have passed")
        if self.cost_usd < 0 or self.tokens_used < 0:
            errors.append("resource consumption cannot be negative")
        return errors

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True)
