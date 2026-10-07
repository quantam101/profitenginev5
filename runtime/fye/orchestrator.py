"""
FYE orchestrator — the single supervising AI that runs one agent per
pipeline process and journals every decision through the hash-chained
DecisionJournal.
"""
from __future__ import annotations

import logging
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .agents import (
    AssemblyAgent, ComplianceAgent, PublishGateAgent, ResearchAgent,
    ScriptAgent, ShotListAgent, StillsAgent, VoiceoverAgent, package_id_for,
)
from .command_os import pending_package_ids
from .config import FyeConfig
from .journal import DecisionJournal

logger = logging.getLogger("fye.orchestrator")


class FyeOrchestrator:
    """
    Runs the FYE pipeline: research → script → shots → stills → voiceover →
    assembly → compliance → publish gate. Each process has exactly one
    agent; every outcome is journaled. Fail-closed: a failed compliance
    gate or unsubmitted approval halts the package.
    """

    def __init__(self, cfg: Optional[FyeConfig] = None) -> None:
        self.cfg = cfg or FyeConfig()
        self.root = Path(self.cfg.root)
        self.journal = DecisionJournal(os.fspath(self.root / "journal.jsonl"))
        self.agents: List[Any] = [
            ResearchAgent(),
            ScriptAgent(),
            ShotListAgent(),
            StillsAgent(self.cfg),
            VoiceoverAgent(),
            AssemblyAgent(),
            ComplianceAgent(),
            PublishGateAgent(self.cfg),
        ]

    def run(self, *, topic: str, niche: str = "science-explainer",
            title: str = "", monthly_views_target: int = 100_000,
            subscribers: int = 0, watch_hours: float = 0.0,
            shorts_views: int = 0, human_reviewed: bool = False,
            package_id: str = "",
            on_agent: Optional[Callable[[str, Dict[str, Any]], None]] = None
            ) -> Dict[str, Any]:
        pkg_id = package_id or package_id_for(topic)
        pkg_dir = self.root / pkg_id
        pkg_dir.mkdir(parents=True, exist_ok=True)

        ctx: Dict[str, Any] = {
            "package_id": pkg_id,
            "pkg_dir": os.fspath(pkg_dir),
            "topic": topic,
            "niche": niche,
            "title": title,
            "monthly_views_target": monthly_views_target,
            "subscribers": subscribers,
            "watch_hours": watch_hours,
            "shorts_views": shorts_views,
            "human_reviewed": human_reviewed,
        }
        self.journal.append("orchestrator", "package.started",
                            {"package_id": pkg_id, "topic": topic, "niche": niche})

        def _run(agent) -> Optional[Dict[str, Any]]:
            try:
                result = agent.run(ctx)
            except Exception as exc:
                self.journal.append(agent.name, "agent.failed", {"error": str(exc)})
                logger.exception("[FYE] agent %s failed", agent.name)
                return {"_failed": agent.name, "error": str(exc)}
            ctx[agent.name] = result
            self.journal.append(agent.name, "agent.completed", _summarize(result))
            if on_agent:
                on_agent(agent.name, result)
            return result

        i = 0
        while i < len(self.agents):
            agent = self.agents[i]
            # Stills and voiceover are independent (both consume shots/script) —
            # run them concurrently on separate threads, one agent each.
            if agent.name == "stills" and i + 1 < len(self.agents) \
                    and self.agents[i + 1].name == "voiceover":
                pair = [agent, self.agents[i + 1]]
                with ThreadPoolExecutor(max_workers=2) as pool:
                    results = list(pool.map(_run, pair))
                for a, result in zip(pair, results):
                    if result and result.get("_failed"):
                        return {"ok": False, "package_id": pkg_id,
                                "failed_agent": a.name, "error": result["error"]}
                i += 2
                continue
            result = _run(agent)
            if result is None or result.get("_failed"):
                return {"ok": False, "package_id": pkg_id, "failed_agent": agent.name,
                        "error": (result or {}).get("error", "agent returned nothing")}
            if agent.name == "compliance" and not result.get("passed"):
                self.journal.append("orchestrator", "package.blocked",
                                    {"package_id": pkg_id, "issues": result["issues"]})
                return {"ok": False, "package_id": pkg_id,
                        "blocked_by": "compliance", "issues": result["issues"]}
            i += 1

        self.journal.append("orchestrator", "package.completed",
                            {"package_id": pkg_id,
                             "manifest": ctx["publish_gate"]["manifest_path"],
                             "approval_id": ctx["publish_gate"].get("approval_id")})
        return {
            "ok": True,
            "package_id": pkg_id,
            "pkg_dir": os.fspath(pkg_dir),
            "manifest": ctx["publish_gate"]["manifest_path"],
            "master": ctx["assembly"]["master_path"],
            "approval": ctx["publish_gate"],
        }

    def pending_packages(self) -> Optional[List[str]]:
        """Pending-only read from Command OS (fye:* approval targets)."""
        return pending_package_ids(self.cfg)

    def verify_decision(self, approval_id: str) -> Optional[Dict[str, Any]]:
        """Journaled-decision verification for one approval id."""
        gate = next((a for a in self.agents if isinstance(a, PublishGateAgent)), None)
        return gate.verify_decision(approval_id) if gate else None

    def status(self) -> Dict[str, Any]:
        return {
            "root": os.fspath(self.root),
            "dc_configured": self.cfg.dc_configured,
            "replicate_enabled": self.cfg.replicate_enabled,
            "journal": self.journal.stats(),
            "agents": [a.name for a in self.agents],
        }


def _summarize(result: Dict[str, Any]) -> Dict[str, Any]:
    """Compact journal payload — no big blobs (script bodies, manifests)."""
    out: Dict[str, Any] = {}
    for k, v in result.items():
        if isinstance(v, (str, int, float, bool)):
            out[k] = v if not isinstance(v, str) or len(v) <= 200 else v[:200] + "…"
        elif isinstance(v, list):
            out[k] = f"<{len(v)} items>"
        elif isinstance(v, dict):
            out[k] = f"<{len(v)} keys>"
    return out
