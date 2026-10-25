from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


class ApprovalRequired(RuntimeError):
    pass


class ApprovalNotFound(KeyError):
    pass


class ApprovalGate:
    """File-backed queue for human approval of sensitive agent actions.

    ``require()`` records a pending approval and raises ``ApprovalRequired``;
    the caller surfaces that status and stops. A human then decides via
    ``decide()`` (or ``python -m runtime.approval_gate approve|veto <id>``),
    and the work can be re-submitted — ``is_approved()`` finally has a path
    to True, so gated actions are resumable instead of permanently blocked.
    """

    _DECISIONS = ("approved", "vetoed")

    def __init__(self, path: str | None = None) -> None:
        self.path = Path(path or os.getenv("GMAOS_APPROVAL_DB", "./data/approvals.json"))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("{}", encoding="utf-8")

    def _load(self) -> Dict[str, Any]:
        return json.loads(self.path.read_text(encoding="utf-8") or "{}")

    def _save(self, data: Dict[str, Any]) -> None:
        self.path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")

    def require(self, action: str, reason: str, payload: Dict[str, Any]) -> str:
        approvals = self._load()
        approval_id = f"approval-{int(time.time() * 1000)}-{os.urandom(4).hex()}"
        approvals[approval_id] = {
            "action": action,
            "reason": reason,
            "payload": payload,
            "status": "pending",
            "created_at": time.time(),
        }
        self._save(approvals)
        raise ApprovalRequired(f"Approval required: {approval_id} for action={action}")

    def get(self, approval_id: str) -> Optional[Dict[str, Any]]:
        return self._load().get(approval_id)

    def pending(self) -> List[Dict[str, Any]]:
        """All undecided approvals, oldest first (each dict includes its id)."""
        items = [
            {"id": aid, **record}
            for aid, record in self._load().items()
            if record.get("status") == "pending"
        ]
        return sorted(items, key=lambda r: r.get("created_at", 0))

    def decide(self, approval_id: str, decision: str, actor: str = "human") -> Dict[str, Any]:
        """Record a human decision on a pending approval.

        ``decision`` is 'approve' or 'veto' (stored as approved/vetoed).
        Raises ApprovalNotFound for unknown ids and ValueError for an
        already-decided or invalid approval — decisions are immutable so an
        audit trail can never be silently rewritten.
        """
        if decision not in ("approve", "veto"):
            raise ValueError(f"decision must be 'approve' or 'veto', got {decision!r}")
        approvals = self._load()
        record = approvals.get(approval_id)
        if record is None:
            raise ApprovalNotFound(approval_id)
        if record.get("status") != "pending":
            raise ValueError(
                f"approval {approval_id} already decided: {record.get('status')}"
            )
        record["status"] = "approved" if decision == "approve" else "vetoed"
        record["decided_by"] = actor
        record["decided_at"] = time.time()
        self._save(approvals)
        return {"id": approval_id, **record}

    def is_approved(self, approval_id: str) -> bool:
        approvals = self._load()
        return approvals.get(approval_id, {}).get("status") == "approved"


def _cli(argv: Optional[List[str]] = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(
        prog="python -m runtime.approval_gate",
        description="Decide pending agent-approval requests.",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="show pending approvals")
    for name in ("approve", "veto"):
        p = sub.add_parser(name, help=f"{name} an approval by id")
        p.add_argument("approval_id")
        p.add_argument("--actor", default=os.getenv("USER", "operator"))
    args = ap.parse_args(argv)

    gate = ApprovalGate()
    if args.cmd == "list":
        pending = gate.pending()
        if not pending:
            print("no pending approvals")
            return 0
        for record in pending:
            print(f"{record['id']}\t{record.get('action')}\t{record.get('reason')}")
        return 0
    try:
        result = gate.decide(args.approval_id, args.cmd, actor=args.actor)
    except ApprovalNotFound:
        print(f"unknown approval id: {args.approval_id}")
        return 1
    except ValueError as exc:
        print(str(exc))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
