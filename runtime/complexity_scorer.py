"""
ComplexityScorer — route tasks to the cheapest capable inference tier.

Score breakdown (all components clamped to [0, 1], final score = min(sum, 1)):

  base      (0 – 0.45)  word count / 1 000   — longer tasks need more reasoning
  token_len (0 – 0.20)  input token estimate  — very large contexts → higher tier
  risk      (0 – 0.55)  high-risk term hits   — sensitive domains need better models

Routing thresholds (overridable via env):
  GMAOS_THRESH_DETERMINISTIC  default 0.25  → DETERMINISTIC_LOCAL  (no LLM)
  GMAOS_THRESH_LOCAL_MODEL    default 0.70  → LOCAL_MODEL          (Ollama)
  GMAOS_THRESH_CLAUDE         default 0.90  → CLAUDE_API           (Claude)
  else                                      → HUMAN_REVIEW_QUEUE

The token_len component ensures that even a short objective attached to a
very long context (e.g. summarising a 10 000-word document) gets routed to
a model with sufficient context window rather than the smallest local model.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .distillation import estimate_tokens


@dataclass(frozen=True)
class ComplexityResult:
    score:       float
    reason:      str
    token_est:   int     # estimated input token count
    risk_terms:  list    # which high-risk terms triggered


class ComplexityScorer:
    HIGH_RISK_TERMS = {
        "deploy", "payment", "stripe", "send email", "delete",
        "production", "merge", "purchase", "client", "legal",
        "tax", "password", "secret", "token", "api key", "bank",
    }

    # Token count thresholds for the token_len component
    _TOKEN_MID  = 1_024   # above this → +0.10
    _TOKEN_HIGH = 4_096   # above this → +0.20

    def score(self, objective: str, context: str = "") -> ComplexityResult:
        text  = f"{objective} {context}".lower()
        words = re.findall(r"[a-z0-9_]+", text)

        # ── component 1: base (word count) ──────────────────────────────
        base = min(len(words) / 1_000.0, 0.45)

        # ── component 2: input token length ─────────────────────────────
        tok_est = estimate_tokens(text)
        if tok_est >= self._TOKEN_HIGH:
            token_len = 0.20
        elif tok_est >= self._TOKEN_MID:
            token_len = 0.10
        else:
            token_len = 0.00

        # ── component 3: high-risk term hits ────────────────────────────
        risk_hits = [term for term in self.HIGH_RISK_TERMS if term in text]
        risk = min(len(risk_hits) * 0.12, 0.55)

        final_score = min(base + token_len + risk, 1.0)

        if risk_hits:
            reason = "risk_terms=" + ",".join(risk_hits)
        elif token_len > 0:
            reason = f"large_context_est_{tok_est}_tokens"
        else:
            reason = "low_static_complexity"

        return ComplexityResult(
            score      = round(final_score, 4),
            reason     = reason,
            token_est  = tok_est,
            risk_terms = risk_hits,
        )
