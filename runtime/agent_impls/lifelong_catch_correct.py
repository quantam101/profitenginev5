"""
Lifelong Catch & Correct (LC&C) agent implementation.

Reads the recent correction history, asks Claude to identify one specific
improvement, then records the suggestion back into the corrections log.

With ANTHROPIC_API_KEY: runs the full self-improvement loop.
Without the key: returns a deterministic stub and skips recording.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List

from runtime.agents import AgentExecution
from runtime.claude_gateway import call_claude
from runtime.lifelong_catch_correct import LifelongCatchCorrect

_SYSTEM = (
    "You are the ProfitEngine v5 LC&C (Lifelong Catch and Correct) engine. "
    "Your job is to inspect the recent correction history and identify exactly one "
    "concrete, testable improvement to a prompt, heuristic, or agent configuration. "
    "Be specific: state the original behaviour, what to change, and the expected "
    "improvement in output quality or CTR. Keep the response under 200 words."
)

_MAX_HISTORY_LINES = 10


def _load_recent_corrections(path: str) -> str:
    p = Path(path)
    if not p.exists():
        return "No correction history yet — this is the first LC&C run."
    lines = p.read_text(encoding="utf-8").strip().splitlines()
    recent = lines[-_MAX_HISTORY_LINES:]
    records = []
    for line in recent:
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
        recent_history = _load_recent_corrections(corrections_path)

        prompt = (
            f"Recent correction history:\n{recent_history}\n\n"
            f"Objective: {objective}\n"
            + (f"Additional context: {context}" if context else "")
        )

        lcc = LifelongCatchCorrect(path=corrections_path)
        result = call_claude(_SYSTEM, prompt, max_tokens=256)

        if result is not None and not result.startswith("CLAUDE_ERROR"):
            lcc.record(
                category="lcc_self_improve",
                issue=objective,
                correction=result[:500],
                metadata={"source": "lcc_agent", "history_lines": len(recent_history.splitlines())},
            )
            return AgentExecution(
                output=f"LC&C_RESULT\nImprovement identified and recorded:\n\n{result}",
                metrics={"agent": self.id, "tier": "claude_api", "connector_count": len(connectors)},
            )

        reason = result or "no_api_key"
        return AgentExecution(
            output="\n".join([
                "LC&C_RESULT",
                f"Objective: {objective}",
                f"Status: skipped ({reason})",
                "Next step: set ANTHROPIC_API_KEY to enable LC&C self-improvement.",
            ]),
            metrics={"agent": self.id, "tier": "deterministic_fallback", "connector_count": len(connectors)},
        )
