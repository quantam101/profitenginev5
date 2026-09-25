"""Specialist process registry (MonetizeOS spec §2).

One accountable specialist role per process.  Roles are activated on
demand — nothing runs continuously.  Each role carries a permission set
(minimum required tools / external actions) enforced by the Director
when scheduling work.

A role is an accountability boundary, not a separate model; handlers are
callables registered per role.  The Director may mark a role
"not_applicable" with a reason instead of forcing work into it.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Any, Protocol

from runtime.monetizeos.contracts import CompletionReport, TaskContract


class SpecialistHandler(Protocol):
    def __call__(self, contract: TaskContract, ctx: dict[str, Any]) -> CompletionReport: ...


@dataclass(frozen=True)
class SpecialistRole:
    name: str
    process: str
    required_output: str
    allowed_tools: tuple[str, ...] = ()
    external_actions: tuple[str, ...] = ()


SPECIALIST_ROLES: dict[str, SpecialistRole] = {
    r.name: r for r in (
        SpecialistRole("repository_auditor", "Repo structure, dependencies, capabilities, licenses",
                       "Evidence-linked asset inventory", ("read", "search")),
        SpecialistRole("commercial_analyst", "Buyer demand, competing offers, pricing, unit economics",
                       "Ranked opportunities and pricing hypotheses", ("read", "search", "web")),
        SpecialistRole("product_architect", "Product boundaries, API contracts, data model",
                       "Implementable product specification", ("read", "search", "write")),
        SpecialistRole("core_product_engineer", "Monetizable repository functionality",
                       "Working product logic and focused tests", ("read", "write", "exec")),
        SpecialistRole("api_identity_engineer", "APIs, tenant isolation, auth, quotas",
                       "Secure API and access controls", ("read", "write", "exec")),
        SpecialistRole("billing_engineer", "Checkout, subscriptions, metering, entitlements",
                       "Verified payment and usage flows", ("read", "write", "exec")),
        SpecialistRole("data_product_engineer", "Permitted ingestion, provenance, paid feeds",
                       "Verified data pipeline when justified", ("read", "write", "exec")),
        SpecialistRole("release_licensing_engineer", "Packaging, signatures, licensing, fulfillment",
                       "Verifiable release artifacts", ("read", "write", "exec")),
        SpecialistRole("experience_engineer", "Customer interface, onboarding, accessibility",
                       "Working customer journeys", ("read", "write", "exec")),
        SpecialistRole("infrastructure_engineer", "Runtime, CI/CD, secrets, migrations, rollback",
                       "Deployable and recoverable infrastructure", ("read", "write", "exec")),
        SpecialistRole("security_reviewer", "Threats, permissions, abuse cases, dependency exposure",
                       "Findings and verified remediation", ("read", "search", "exec")),
        SpecialistRole("verification_engineer", "Independent functional/integration/failure testing",
                       "Reproducible acceptance evidence", ("read", "exec")),
        SpecialistRole("growth_engineer", "Positioning, SEO, analytics, acquisition",
                       "Accurate commercial assets and measurement", ("read", "write", "web")),
        SpecialistRole("operations_engineer", "Monitoring, support, reconciliation, recovery",
                       "Operating runbook and actionable alerts", ("read", "write", "exec")),
        SpecialistRole("improvement_engineer", "Failure analysis, regression prevention, optimization",
                       "Evidence-backed improvement proposals", ("read", "search", "exec")),
    )
}

ROLE_PERMISSIONS = {name: role.allowed_tools + role.external_actions
                    for name, role in SPECIALIST_ROLES.items()}


def check_permissions(contract: TaskContract) -> list[str]:
    """Return unauthorized tool/action requests (fail-closed)."""
    role = SPECIALIST_ROLES.get(contract.process_owner)
    if role is None:
        return [f"unknown process owner {contract.process_owner!r}"]
    granted = set(role.allowed_tools) | set(role.external_actions) | {"read"}
    return [t for t in contract.allowed_tools + contract.external_actions if t not in granted]


# ----- built-in handlers (deterministic; AI judgment layered on top) -----

def repository_audit_handler(contract: TaskContract, ctx: dict[str, Any]) -> CompletionReport:
    """Evidence-linked asset inventory of the repository checkout."""
    import json as _json
    import os
    root = ctx["repo_root"]
    inventory: dict[str, Any] = {"files": 0, "python_files": 0, "ts_files": 0,
                                 "test_files": 0, "loc_estimate": 0, "manifests": []}
    manifests = {"package.json", "pyproject.toml", "requirements.txt", "Cargo.toml", "go.mod"}
    for dirpath, _dirs, files in os.walk(root):
        if ".git" in dirpath or "node_modules" in dirpath:
            continue
        for f in files:
            inventory["files"] += 1
            if f.endswith(".py"):
                inventory["python_files"] += 1
            if f.endswith((".ts", ".tsx")):
                inventory["ts_files"] += 1
            if f.startswith("test_") or f.endswith(".test.ts"):
                inventory["test_files"] += 1
            if f in manifests:
                inventory["manifests"].append(f)
    artifact_dir = ctx.get("artifact_dir")
    refs: list[str] = []
    if artifact_dir:
        os.makedirs(artifact_dir, exist_ok=True)
        ref = f"{artifact_dir}/inventory.json"
        with open(ref, "w") as fh:
            _json.dump(inventory, fh, indent=2)
        refs.append(ref)
    refs.append(f"files={inventory['files']} tests={inventory['test_files']}")
    return CompletionReport(
        task_id=contract.task_id, status="completed",
        artifact_refs=refs,
        tests_run=[{"name": "audit", "command": "walk repo_root", "result": "passed"}],
        limitations=["static scan only; no license attestation"],
    )


def command_check_handler(command: list[str]) -> SpecialistHandler:
    """Wrap a shell check (pytest, security-scan) as a specialist handler."""
    def _handler(contract: TaskContract, ctx: dict[str, Any]) -> CompletionReport:
        try:
            proc = subprocess.run(command, cwd=ctx["repo_root"], capture_output=True,
                                  text=True, timeout=int(contract.budget_seconds))
        except subprocess.TimeoutExpired:
            return CompletionReport(task_id=contract.task_id, status="failed",
                                    tests_run=[{"name": command[0], "command": " ".join(command),
                                                "result": "failed"}],
                                    limitations=["timeout"])
        result = "passed" if proc.returncode == 0 else "failed"
        tail = (proc.stdout + proc.stderr).strip().splitlines()[-3:]
        return CompletionReport(
            task_id=contract.task_id,
            status="completed" if result == "passed" else "failed",
            tests_run=[{"name": command[0], "command": " ".join(command), "result": result}],
            artifact_refs=tail,
            limitations=[f"exit code {proc.returncode}"],
        )
    return _handler


DEFAULT_HANDLERS: dict[str, SpecialistHandler] = {
    "repository_auditor": repository_audit_handler,
}
