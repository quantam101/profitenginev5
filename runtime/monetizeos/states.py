"""Task lifecycle for MonetizeOS orchestration.

Explicit states per the MonetizeOS execution spec:

    pending -> ready -> running -> verifying -> completed

plus blocked, retry_wait, failed, cancelled.  Transitions are enforced
transactionally by the store; this module only defines the legal graph.
"""
from __future__ import annotations

TASK_STATES = (
    "pending",
    "ready",
    "running",
    "verifying",
    "completed",
    "blocked",
    "retry_wait",
    "failed",
    "cancelled",
)

TERMINAL_STATES = frozenset({"completed", "failed", "cancelled"})

TRANSITIONS: dict[str, frozenset[str]] = {
    # pending -> ready happens when all dependency edges resolve (store-side).
    "pending": frozenset({"ready", "cancelled"}),
    # ready -> running on claim; ready -> blocked when a dependency fails.
    "ready": frozenset({"running", "blocked", "cancelled"}),
    # running -> verifying when the specialist reports a completion candidate.
    "running": frozenset({"verifying", "retry_wait", "failed", "blocked", "cancelled"}),
    # verifying -> completed on accepted evidence, or back to retry/failed.
    "verifying": frozenset({"completed", "retry_wait", "failed", "cancelled"}),
    # retry_wait -> ready once next_attempt_at passes (swept by claim()).
    "retry_wait": frozenset({"ready", "failed", "cancelled"}),
    # blocked -> ready when the blocker clears.
    "blocked": frozenset({"ready", "cancelled"}),
    # Terminal states admit no transitions.
    "completed": frozenset(),
    "failed": frozenset(),
    "cancelled": frozenset(),
}


class IllegalTransition(ValueError):
    def __init__(self, task_id: str, src: str, dst: str) -> None:
        super().__init__(f"task {task_id}: illegal transition {src} -> {dst}")
        self.task_id = task_id
        self.src = src
        self.dst = dst


def check(task_id: str, src: str, dst: str) -> None:
    if dst not in TRANSITIONS.get(src, frozenset()):
        raise IllegalTransition(task_id, src, dst)
