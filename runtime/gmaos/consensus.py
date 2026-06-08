"""
G-MAOS Consensus Engine
=======================
Supermajority vote over parallel agent outputs.

Algorithm
---------
1. Discard failed results; keep COMPLETED / COMPLETED_LOCAL / COMPLETED_DISTILL.
2. SHA-256 fingerprint each surviving output (first 16 hex chars).
3. Count fingerprint occurrences.
4. Quorum met when the plurality count / total agents >= threshold (default 0.67).
5. Return the full output of the first agent that produced the majority fingerprint.
6. If no valid results exist, return NO_QUORUM with empty output.

This is intentionally output-format agnostic: works with plain text, JSON strings,
or any binary-safe UTF-8 content stored in MeshResult.output.
"""
from __future__ import annotations

import hashlib
import time
from collections import Counter
from dataclasses import dataclass, field
from typing import Sequence

from .schema import MeshResult, TaskStatus

_SUCCESS_STATUSES = {
    TaskStatus.COMPLETED,
    TaskStatus.COMPLETED_LOCAL,
    TaskStatus.COMPLETED_DISTILL,
}


@dataclass(frozen=True)
class ConsensusResult:
    quorum_met: bool
    status: str                   # "VERIFIED_CONSENSUS" | "DIVERGENCE_FLAGGED" | "NO_QUORUM"
    majority_fingerprint: str     # SHA-256[:16] of the winning output
    winning_output: str           # full output of the winning agent
    winning_tier: str             # inference tier that produced the winner
    winning_agent: str            # agent that produced the winner
    agent_count: int              # total agents submitted
    valid_count: int              # agents that succeeded
    agreement_count: int          # agents that matched the majority fingerprint
    threshold: float              # quorum threshold used
    duration_ms: int
    processed_at: float
    results: list[dict] = field(default_factory=list)


def _fp(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _result_dict(r: MeshResult) -> dict:
    return {
        "agent": r.agent,
        "status": r.status.value if hasattr(r.status, "value") else str(r.status),
        "tier": r.tier,
        "fingerprint": _fp(r.output) if r.output else "",
        "cached": r.cached,
        "duration_ms": r.duration_ms,
        "tokens_in": r.tokens_in,
        "tokens_out": r.tokens_out,
        "error": r.error,
    }


def supermajority_vote(
    results: Sequence[MeshResult],
    threshold: float = 0.67,
) -> ConsensusResult:
    """
    Apply supermajority vote over a sequence of MeshResults.

    Parameters
    ----------
    results   : Outputs from Mesh.run() — one per agent.
    threshold : Fraction of total agents required for quorum (default 2-of-3 = 0.67).

    Returns
    -------
    ConsensusResult with the winning output and quorum metadata.
    """
    t0 = time.perf_counter()
    total = len(results)
    result_dicts = [_result_dict(r) for r in results]

    valid = [r for r in results if r.status in _SUCCESS_STATUSES]

    if not valid:
        return ConsensusResult(
            quorum_met=False,
            status="NO_QUORUM",
            majority_fingerprint="",
            winning_output="",
            winning_tier="error",
            winning_agent="",
            agent_count=total,
            valid_count=0,
            agreement_count=0,
            threshold=threshold,
            duration_ms=int((time.perf_counter() - t0) * 1000),
            processed_at=time.time(),
            results=result_dicts,
        )

    fp_map: dict[str, str] = {r.agent: _fp(r.output) for r in valid}
    counts: Counter[str] = Counter(fp_map.values())
    majority_fp, majority_count = counts.most_common(1)[0]

    quorum_met = majority_count / total >= threshold
    status = "VERIFIED_CONSENSUS" if quorum_met else "DIVERGENCE_FLAGGED"

    winner = next(r for r in valid if _fp(r.output) == majority_fp)

    return ConsensusResult(
        quorum_met=quorum_met,
        status=status,
        majority_fingerprint=majority_fp,
        winning_output=winner.output,
        winning_tier=winner.tier,
        winning_agent=winner.agent,
        agent_count=total,
        valid_count=len(valid),
        agreement_count=majority_count,
        threshold=threshold,
        duration_ms=int((time.perf_counter() - t0) * 1000),
        processed_at=time.time(),
        results=result_dicts,
    )
