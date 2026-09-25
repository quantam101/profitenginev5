"""Quality and release gates (spec §7).

Ten ordered milestones, each independently recorded.  A gate may only be
marked passed by the Director holding a live fencing token, and the
Security/Verification gates additionally require a passing evidence
record — the Director cannot declare a failed mandatory check passed.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

from runtime.monetizeos.store import Store

RELEASE_GATES = (
    "repo_access_verified",
    "monetizable_hypothesis_documented",
    "product_contract_reviewed",
    "core_implementation_complete",
    "auth_isolation_billing_passed",
    "independent_e2e_verification_passed",
    "release_artifacts_signed",
    "deploy_rollback_verified",
    "authorized_production_deployed",
    "live_operational_checks_passed",
)

# Milestones kept distinct from the gates (spec §7): a gate being green is
# not the same as live revenue.
MILESTONES = (
    "code_complete",
    "locally_verified",
    "integration_verified",
    "deployed",
    "live_payment_verified",
    "paying_customer_acquired",
)

MANDATORY_EVIDENCE_GATES = frozenset({
    "auth_isolation_billing_passed",
    "independent_e2e_verification_passed",
    "release_artifacts_signed",
    "deploy_rollback_verified",
})


@dataclass
class GateBoard:
    store: Store
    project_id: str

    def _table(self) -> dict:
        # Gates and milestones are stored as decisions of kind 'gate'/'milestone'.
        rows = self.store._conn.execute(
            "SELECT kind, detail_json, created_at FROM decisions WHERE project_id=?"
            " AND kind IN ('gate','milestone') ORDER BY decision_id", (self.project_id,)).fetchall()
        import json
        return {json.loads(r["detail_json"])["name"]: {**json.loads(r["detail_json"]),
                                                      "at": r["created_at"]}
                for r in rows}

    def state(self) -> dict:
        recorded = self._table()
        return {
            "gates": {g: recorded.get(g, {"passed": False}) for g in RELEASE_GATES},
            "milestones": {m: recorded.get(m, {"reached": False}) for m in MILESTONES},
            "next_gate": next((g for g in RELEASE_GATES
                               if not recorded.get(g, {}).get("passed")), None),
        }

    def mark_passed(self, gate: str, fencing: int, evidence: dict | None = None) -> None:
        if gate not in RELEASE_GATES:
            raise KeyError(gate)
        # Ordered: all earlier gates must be passed first.
        recorded = self._table()
        for earlier in RELEASE_GATES[:RELEASE_GATES.index(gate)]:
            if not recorded.get(earlier, {}).get("passed"):
                raise RuntimeError(f"gate {earlier} must pass before {gate}")
        if gate in MANDATORY_EVIDENCE_GATES:
            if not (evidence or {}).get("passed"):
                raise RuntimeError(
                    f"mandatory evidence gate {gate} cannot be declared passed "
                    "without a passing evidence record"
                )
            # A bare `passed: true` is a declaration, not evidence — the record
            # must point at the artifact/run/task that produced the result.
            if not any(v for k, v in evidence.items() if k != "passed" and v):
                raise RuntimeError(
                    f"mandatory evidence gate {gate} requires a reference to the "
                    "recorded check (artifact, run id, or verified task) — "
                    "a bare passed flag is not evidence"
                )
        self.store.record_decision(self.project_id, fencing, "gate",
                                   {"name": gate, "passed": True,
                                    "evidence": evidence or {}, "at": time.time()})

    def reach_milestone(self, milestone: str, fencing: int, evidence: dict | None = None) -> None:
        if milestone not in MILESTONES:
            raise KeyError(milestone)
        if milestone == "live_payment_verified" and (evidence or {}).get("test_transaction"):
            raise RuntimeError("test transactions are not evidence of actual revenue")
        self.store.record_decision(self.project_id, fencing, "milestone",
                                   {"name": milestone, "reached": True,
                                    "evidence": evidence or {}, "at": time.time()})
