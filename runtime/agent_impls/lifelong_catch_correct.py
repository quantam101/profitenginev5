"""
Lifelong Catch & Correct (LC&C) agent implementation.

Reads recent correction history, generates one concrete improvement,
and records it back to corrections.jsonl.

Inference cascade (lowest cost first):
  1. Ollama local model — free forever
  2. Claude API        — key-gated fallback
  3. Deterministic stub — no recording, returns instructions only
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List

from runtime.agents import AgentExecution
from runtime.claude_gateway import call_claude
from runtime.lifelong_catch_correct import LifelongCatchCorrect
from runtime.ollama_gateway import call_ollama

_SYSTEM = (
    "You are the ProfitEngine v5 LC&C (Lifelong Catch and Correct) engine. "
    "Inspect the recent correction history and identify exactly one concrete, "
    "testable improvement to a prompt, heuristic, or agent configuration. "
    "State: (1) the original behaviour, (2) the specific change, "
    "(3) expected improvement in output quality or CTR. "
    "Be specific. Keep the response under 150 words."
)

_MAX_HISTORY_LINES = 10


def _load_recent_corrections(path: str) -> str:
    p = Path(path)
    if not p.exists():
        return "No correction history yet — this is the first LC&C run."
    lines = p.read_text(encoding="utf-8").strip().splitlines()
    records = []
    for line in lines[-_MAX_HISTORY_LINES:]:
        try:
            r = json.loads(line)
            records.append(f"[{r.get('category', '?')}] {r.get('issue', '')} → {r.get('correction', '')}")
        except json.JSONDecodeError:
            pass
    return "\n".join(records) if records else "No parseable corrections found."


class Agent:
    id = "lifelong-catch-correct"

    def run(self, objective: str, context: str, connectors: List[str]) -> AgentExecution:
        corrections_path = os.getenv("GMAOS_CORRECTIONS_PATH", "./data/corrections.jsonl")
        recent = _load_recent_corrections(corrections_path)
        prompt = (
            f"Recent correction history:\n{recent}\n\n"
            f"Objective: {objective}"
            + (f"\nAdditional context: {context}" if context else "")
        )
        lcc = LifelongCatchCorrect(path=corrections_path)

        # Tier 1 — Ollama (free, local)
        result = call_ollama(_SYSTEM, prompt, max_tokens=256)
        if result is not None and not result.startswith("OLLAMA_ERROR"):
            lcc.record(
                category="lcc_self_improve",
                issue=objective,
                correction=result[:500],
                metadata={"source": "lcc_agent", "tier": "ollama"},
            )
            return AgentExecution(
                output=f"LC&C_RESULT\nImprovement identified and recorded:\n\n{result}",
                metrics={"agent": self.id, "tier": "ollama", "connector_count": len(connectors)},
            )

        # Tier 2 — Claude API (key-gated)
        result = call_claude(_SYSTEM, prompt, max_tokens=256)
        if result is not None and not result.startswith("CLAUDE_ERROR"):
            lcc.record(
                category="lcc_self_improve",
                issue=objective,
                correction=result[:500],
                metadata={"source": "lcc_agent", "tier": "claude_api"},
            )
            return AgentExecution(
                output=f"LC&C_RESULT\nImprovement identified and recorded:\n\n{result}",
                metrics={"agent": self.id, "tier": "claude_api", "connector_count": len(connectors)},
            )

        # Tier 3 — deterministic stub
        reason = result or "no_model_available"
        return AgentExecution(
            output="\n".join([
                "LC&C_RESULT",
                f"Objective: {objective}",
                f"Status: skipped ({reason})",
                "Next step: set GMAOS_LOCAL_MODEL_ENABLED=true (Ollama) or ANTHROPIC_API_KEY (Claude).",
            ]),
            metrics={"agent": self.id, "tier": "deterministic_fallback", "connector_count": len(connectors)},
        )
