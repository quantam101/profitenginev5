"""Explicit task contracts and completion reports (MonetizeOS spec §3).

Every delegated task carries a TaskContract; every completion carries a
CompletionReport.  An agent's declaration of success is not evidence —
the store only accepts a report whose declared tests actually ran.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any

# Credential-shaped values must never be embedded in contracts, reports or
# decisions (spec §6: keep production secrets out of prompts and context).
_SECRET_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),                                   # AWS access key
    re.compile(r"(?:sk|pk|rk|ghp|gho|ghu|ghs|ghr|glpat|xox[baprs])[_-][A-Za-z0-9_-]{8,}"),
    re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{5,}"),  # JWT
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[^-]*-----END [A-Z ]*PRIVATE KEY-----", re.S),
    re.compile(r"(?i)(bearer|token|api[_-]?key|secret|password|passwd)"
               r"(\s*[:=]\s*|\s+)(['\"]?)[^\s'\"]{8,}\3"),
]


def contains_secret(text: str) -> bool:
    return any(p.search(text) for p in _SECRET_PATTERNS)


def redact_text(text: str) -> str:
    """Replace credential-shaped substrings with a fixed marker."""
    for pat in _SECRET_PATTERNS:
        text = pat.sub("[REDACTED]", text)
    return text


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
        if self.budget_usd != 0:
            # Repository policy is max_cost_usd: 0 — a contract that
            # budgets spend violates the mandatory zero-cost boundary.
            errors.append("budget_usd must be 0 (zero-spend policy)")
        if self.retry_limit < 0:
            errors.append("retry_limit must be >= 0")
        if contains_secret(json.dumps(asdict(self))):
            # Fail closed rather than silently redact: a contract carrying a
            # credential is a policy violation the delegator must fix.
            errors.append("contract contains credential-shaped values; "
                          "secrets must never be embedded in task contracts")
        return errors

    def fingerprint(self) -> str:
        """Stable hash of the ENTIRE contract — every field that defines the
        work (scope, budgets, tools, permissions) participates, so a changed
        contract can never silently reuse the old task or its artifacts."""
        return hashlib.sha256(
            json.dumps(asdict(self), sort_keys=True).encode()).hexdigest()


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
        if self.status == "completed" and not all(
                t.get("name") and t.get("command") for t in self.tests_run):
            errors.append("each recorded test must include the command that produced it")
        if self.status == "completed" and not all(
                t.get("output") or t.get("evidence") for t in self.tests_run):
            errors.append("each recorded test must carry captured output/evidence — "
                          "a bare 'passed' label is not verification evidence")
        if self.cost_usd < 0 or self.tokens_used < 0:
            errors.append("resource consumption cannot be negative")
        return errors

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True)
