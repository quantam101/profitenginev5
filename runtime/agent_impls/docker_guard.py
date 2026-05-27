"""
Docker Guard agent — analyzes Docker/Ollama health and recommends actions.

Processes the distilled output from scripts/docker-guard.sh, applies the
data distillation pipeline to compress it further, then uses the inference
cascade (Ollama → Groq → Gemini → stub) to produce a structured remediation
recommendation.

Architecture note:
  This agent does NOT call Docker directly — the runtime container lacks the
  Docker socket. Feed it pre-collected guard output via the 'context' field.
  The GitHub Actions workflow (docker-guard.yml) SSHes into the server to run
  docker-guard.sh, then passes the output here for analysis.

Token budget: 512 output tokens (health reports must be terse)

Distillation metrics:
  Typical docker-guard.sh output: ~2 000 chars → ~500 tokens
  After distillation:             ~600 chars   → ~150 tokens  (70% reduction)
  Inference call cost: $0 (Ollama local → Groq free tier)
"""
from __future__ import annotations

import re
from typing import List

from runtime.agents import AgentExecution
from runtime.distillation import distill, estimate_tokens
from runtime.inference_cascade import infer
from runtime.structured_output import OUTPUT_CONSTRAINT_CONCISE

_SYSTEM = (
    "You are a Docker infrastructure guardian for ProfitEngine v5 (OCI 30 GB boot volume). "
    "Analyze the distilled health report and reply in EXACTLY this 4-line format:\n"
    "STATUS: ok | warn | critical\n"
    "DISK: <free GB> free, <used %> used, trend=<stable|filling|critical>\n"
    "ISSUES: <comma-separated issues or 'none'>\n"
    "ACTIONS: <up to 3 shell one-liners or 'none required'>\n"
    "No prose. No extra lines. Just the 4 fields."
    + OUTPUT_CONSTRAINT_CONCISE
)

# Patterns that add no signal for Docker health analysis
_ANSI_RE  = re.compile(r"\x1b\[[0-9;]*m")
_TS_RE    = re.compile(r"ts=\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\s+")
_LEVEL_RE = re.compile(r"level=info\s+")   # keep warn/critical, drop info label


def _normalise_log(raw: str) -> str:
    """Strip log envelope overhead — keep only the signal fields."""
    text = _ANSI_RE.sub("", raw)
    text = _TS_RE.sub("", text)           # timestamps add no distillation value
    text = _LEVEL_RE.sub("", text)        # 'level=info' is boilerplate
    return text


class Agent:
    id = "docker-guard"

    def run(self, objective: str, context: str, connectors: List[str]) -> AgentExecution:
        """
        Analyse Docker/Ollama health data.

        Args:
            objective: Human-readable goal (e.g. "check server health")
            context:   Raw output from scripts/docker-guard.sh
            connectors: Ignored — agent is analysis-only (no external calls)

        Returns:
            AgentExecution with structured STATUS/DISK/ISSUES/ACTIONS block.
        """
        raw = context or "no docker-guard data provided"

        # Stage 0: normalise (strip log envelopes, ANSI codes)
        normalised = _normalise_log(raw)

        # Stages 1-4: data distillation — focus on disk/health/error signals
        distilled = distill(
            normalised,
            objective="disk free space container health unhealthy error critical ollama model",
            char_budget=2048,
        )

        before_tokens = estimate_tokens(raw)
        after_tokens  = estimate_tokens(distilled)
        reduction_pct = round(100 * (1 - after_tokens / max(1, before_tokens)), 1)

        # Inference: Ollama-first (free, local) — health reports are short
        prompt = (
            f"Guard report ({before_tokens}→{after_tokens} tok, "
            f"{reduction_pct}% distillation):\n{distilled}"
        )
        result, tier = infer(
            _SYSTEM,
            prompt,
            max_tokens=512,
        )

        return AgentExecution(
            output=f"DOCKER_GUARD_ANALYSIS\n{result}",
            metrics={
                "agent":           self.id,
                "tier":            tier,
                "tokens_before":   before_tokens,
                "tokens_after":    after_tokens,
                "reduction_pct":   reduction_pct,
                "distilled_chars": len(distilled),
            },
        )
