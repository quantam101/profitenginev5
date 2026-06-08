"""
G-MAOS Distillation Engine
===========================
Three-stage token compression pipeline, fully wired into the inference cascade.

Stage 1 — Structural strip (deterministic, zero cost, <1 ms)
    Removes HTML, markdown, boilerplate using the existing runtime.distillation module.

Stage 2 — Semantic compression (deterministic, zero cost, ~5 ms)
    Deduplicates sentences, keyword-focuses on the task objective,
    budget-truncates to configured char limit.

Stage 3 — LLM summarisation (only when Stage 1+2 output still exceeds threshold)
    Calls the inference cascade (cheapest available tier) to produce a dense
    prose summary. Result is cached in the StateStore so repeat calls are free.

Compression targets:
    - Routine agent input:   reduce to ≤ 30% of original tokens
    - Snapshot store:        keep ≤ 1024 tokens per agent snapshot
    - Audit trail:           keep 1-sentence distilled summary

All numeric thresholds are overridable via environment variables.
"""
from __future__ import annotations

import hashlib
import logging
import os
import uuid
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .store import StateStore

log = logging.getLogger("gmaos.distill")

# ── thresholds (env-overridable) ──────────────────────────────────────────────
_STAGE3_TRIGGER_TOKENS  = int(os.getenv("GMAOS_DISTILL_STAGE3_TOKENS",  "800"))
_SNAPSHOT_MAX_TOKENS    = int(os.getenv("GMAOS_DISTILL_SNAPSHOT_TOKENS","1024"))
_BUDGET_CHARS           = int(os.getenv("GMAOS_DISTILL_BUDGET_CHARS",   "8192"))
_STAGE3_MAX_OUT_TOKENS  = int(os.getenv("GMAOS_DISTILL_OUT_TOKENS",     "400"))


def _estimate_tokens(text: str) -> int:
    """Fast approximation: 1 token ≈ 4 chars."""
    return max(1, len(text) // 4)


def _structural_distill(text: str, objective: str = "") -> str:
    """Stage 1+2: deterministic, no LLM."""
    try:
        from runtime.distillation import distill
        return distill(text, objective=objective, char_budget=_BUDGET_CHARS)
    except Exception:
        # Fallback: naive truncation
        return text[:_BUDGET_CHARS]


def _llm_summarise(text: str, objective: str, max_tokens: int) -> tuple[str, str]:
    """
    Stage 3: LLM-based compression.
    Returns (summary, tier_used).
    """
    system = (
        "You are a precision data distillation engine. "
        "Compress the input to the absolute minimum tokens needed to preserve "
        "all facts required for the stated objective. "
        "Output ONLY the compressed content — no preamble, no explanation."
    )
    prompt = (
        f"Objective: {objective}\n\n"
        f"Content to compress:\n{text}"
    )
    try:
        from runtime.inference_cascade import infer
        summary, tier = infer(system, prompt, max_tokens=max_tokens)
        if summary.startswith("INFERENCE_STUB"):
            return text[:max_tokens * 4], "stub"
        return summary, tier
    except Exception as exc:
        log.warning("Stage-3 distillation LLM call failed: %s", exc)
        return text[:max_tokens * 4], "fallback"


def distill_task_input(
    system: str,
    user: str,
    objective: str = "",
    agent_id: str = "",
    store: Optional["StateStore"] = None,
    task_id: str = "",
) -> tuple[str, str, bool, int, int]:
    """
    Full three-stage distillation pipeline.

    Returns:
        (distilled_system, distilled_user, was_stage3_used, raw_tokens, out_tokens)
    """
    raw = system + "\n" + user
    raw_tokens = _estimate_tokens(raw)

    # Stage 1+2 always runs
    dist_system = _structural_distill(system, objective)
    dist_user   = _structural_distill(user,   objective)
    stage12_tokens = _estimate_tokens(dist_system + dist_user)

    stage3 = False
    if stage12_tokens > _STAGE3_TRIGGER_TOKENS:
        combined = dist_system + "\n" + dist_user
        # Cache check: avoid repeated LLM calls for identical input
        cache_key = hashlib.sha256(
            (combined + objective + agent_id).encode()
        ).hexdigest()[:24]

        cached_out: Optional[str] = None
        if store:
            cached_out = store.load_snapshot(f"distill:{cache_key}")

        if cached_out:
            dist_user  = cached_out
            dist_system = ""
        else:
            compressed, tier = _llm_summarise(
                combined, objective or (user[:120] if user else "task"),
                max_tokens=_STAGE3_MAX_OUT_TOKENS,
            )
            dist_user   = compressed
            dist_system = ""
            stage3      = True
            if store:
                store.save_snapshot(f"distill:{cache_key}", compressed, tier,
                                    distilled=True,
                                    tokens_in=stage12_tokens,
                                    tokens_out=_estimate_tokens(compressed))
            # Write distillation audit
            if store and task_id:
                store.distill_log(
                    log_id    = uuid.uuid4().hex[:16],
                    task_id   = task_id,
                    agent     = agent_id,
                    summary   = compressed[:200],
                    raw_tokens= raw_tokens,
                    out_tokens= _estimate_tokens(compressed),
                )

    out_tokens = _estimate_tokens(dist_system + dist_user)
    ratio = out_tokens / raw_tokens
    log.debug("distill[%s]: %d→%d tokens (%.0f%%) stage3=%s",
              agent_id or task_id, raw_tokens, out_tokens, ratio * 100, stage3)
    return dist_system, dist_user, stage3, raw_tokens, out_tokens


def distill_snapshot(output: str, agent_id: str) -> str:
    """
    Compress an agent's output before persisting as a snapshot.
    Keeps the snapshot store lean without losing semantic content.
    """
    if _estimate_tokens(output) <= _SNAPSHOT_MAX_TOKENS:
        return output
    compressed, _ = _llm_summarise(
        output,
        objective=f"Summarise the output of agent '{agent_id}' for cache storage.",
        max_tokens=_SNAPSHOT_MAX_TOKENS,
    )
    return compressed
