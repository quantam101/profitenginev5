"""ApprovalGate decision path + resumable gated executions."""

import pytest

from runtime.approval_gate import (
    ApprovalGate,
    ApprovalNotFound,
    ApprovalRequired,
)


@pytest.fixture
def gate(tmp_path):
    return ApprovalGate(path=str(tmp_path / "approvals.json"))


def _pending_id(gate):
    with pytest.raises(ApprovalRequired) as excinfo:
        gate.require("sensitive_action", "needs human sign-off", {"k": "v"})
    # approval id is embedded in the raised message
    return str(excinfo.value).split("Approval required: ")[1].split(" ")[0]


class TestDecisionPath:
    def test_require_then_approve(self, gate):
        aid = _pending_id(gate)
        assert not gate.is_approved(aid)
        result = gate.decide(aid, "approve", actor="owner")
        assert result["status"] == "approved"
        assert result["decided_by"] == "owner"
        assert gate.is_approved(aid)

    def test_veto(self, gate):
        aid = _pending_id(gate)
        gate.decide(aid, "veto")
        assert not gate.is_approved(aid)
        assert gate.get(aid)["status"] == "vetoed"

    def test_unknown_id_raises(self, gate):
        with pytest.raises(ApprovalNotFound):
            gate.decide("approval-nope", "approve")

    def test_double_decision_rejected(self, gate):
        aid = _pending_id(gate)
        gate.decide(aid, "approve")
        with pytest.raises(ValueError):
            gate.decide(aid, "veto")

    def test_invalid_decision_rejected(self, gate):
        aid = _pending_id(gate)
        with pytest.raises(ValueError):
            gate.decide(aid, "maybe")

    def test_pending_lists_undecided_only(self, gate):
        aid1 = _pending_id(gate)
        _pending_id(gate)
        gate.decide(aid1, "approve")
        pending = gate.pending()
        assert len(pending) == 1
        assert pending[0]["status"] == "pending"


class TestResumableExecution:
    """sovereign_core must resume gated work after approval, not re-queue."""

    def _core(self, tmp_path, monkeypatch):
        monkeypatch.setenv("GMAOS_AUDIT_LOG", str(tmp_path / "audit.jsonl"))
        monkeypatch.setenv("GMAOS_APPROVAL_DB", str(tmp_path / "approvals.json"))
        monkeypatch.setenv("GMAOS_VECTOR_CACHE", str(tmp_path / "vector.sqlite3"))
        monkeypatch.setenv("GMAOS_EMBEDDING_DIM", "4")
        from runtime.sovereign_core import SovereignAutomationCore

        return SovereignAutomationCore()

    _OBJECTIVE = "Deploy production and send client email"
    _VEC = [0.2, 0.2, 0.2, 0.2]

    def test_approved_execution_resumes(self, tmp_path, monkeypatch):
        core = self._core(tmp_path, monkeypatch)
        first = core.execute("system", "ctx", self._OBJECTIVE, self._VEC)
        assert first.status == "approval_required"

        aid = core.approval_gate.pending()[0]["id"]
        core.approval_gate.decide(aid, "approve")

        resumed = core.execute(
            "system", "ctx", self._OBJECTIVE, self._VEC, approval_id=aid,
        )
        assert resumed.status == "ok"
        # no duplicate pending requests were created
        assert core.approval_gate.pending() == []

    def test_vetoed_execution_is_blocked(self, tmp_path, monkeypatch):
        core = self._core(tmp_path, monkeypatch)
        core.execute("system", "ctx", self._OBJECTIVE, self._VEC)
        aid = core.approval_gate.pending()[0]["id"]
        core.approval_gate.decide(aid, "veto")

        resumed = core.execute(
            "system", "ctx", self._OBJECTIVE, self._VEC, approval_id=aid,
        )
        assert resumed.status == "vetoed"

    def test_still_pending_does_not_duplicate(self, tmp_path, monkeypatch):
        core = self._core(tmp_path, monkeypatch)
        core.execute("system", "ctx", self._OBJECTIVE, self._VEC)
        aid = core.approval_gate.pending()[0]["id"]

        resumed = core.execute(
            "system", "ctx", self._OBJECTIVE, self._VEC, approval_id=aid,
        )
        assert resumed.status == "approval_required"
        assert len(core.approval_gate.pending()) == 1
