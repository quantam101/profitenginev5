from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .approval_gate import ApprovalGate, ApprovalRequired
from .audit_log import AuditLog
from .complexity_scorer import ComplexityScorer
from .cost_guard import CostGuard, CostGuardError
from .agents import load_agent
from .cycle_log import CycleLog, CycleRecord
from .local_model_router import LocalModelRouter
from .memory_commit import MemoryCommit
from .minifier import ManifestMinifier
from .registry import RegistryError, RuntimeRegistry
from .vector_cache import VectorCache
from .verifier import Verifier


@dataclass(frozen=True)
class ExecutionResult:
    status: str
    route_tier: str
    output: str
    cached: bool
    details: Dict[str, Any]


class SovereignAutomationCore:
    """
    Local-first, no-spend EAOS execution primitive.

    This is not a paid API wrapper. It is a guarded execution router that:
    - compresses registry-driven intent,
    - checks local verified memory first,
    - scores complexity,
    - routes simple work locally,
    - queues high-risk work for approval,
    - blocks paid/cloud escalation by default,
    - logs everything.
    """

    def __init__(self) -> None:
        self.audit = AuditLog()
        self.cycle_log = CycleLog()
        self.cost_guard = CostGuard()
        self.approval_gate = ApprovalGate()
        self.minifier = ManifestMinifier()
        self.cache = VectorCache()
        self.scorer = ComplexityScorer()
        self.router = LocalModelRouter()
        self.verifier = Verifier()
        self.memory = MemoryCommit(self.cache, self.verifier)
        self.registry = RuntimeRegistry()

    def execute(
        self,
        system_declaration: str,
        dynamic_context: str,
        objective: str,
        embedding_vector: List[float],
        namespace: str = "default",
        actor: str = "sovereign-core",
        agent_id: str = "sovereign-orchestrator",
    ) -> ExecutionResult:
        started_at = time.time()
        correlation_id = hashlib.sha256(f"{objective}|{namespace}".encode("utf-8")).hexdigest()[:16]
        agent_policy = self.registry.agent(agent_id)
        self.audit.info(
            actor,
            "execution_received",
            {"namespace": namespace, "agent_id": agent_id, "objective": objective[:250]},
            correlation_id,
        )

        clean_system, clean_context = self.minifier.minify(system_declaration, dynamic_context)
        self.audit.info(actor, "manifest_minified", {"system_chars": len(clean_system), "context_chars": len(clean_context)}, correlation_id)

        cache_hit = self.cache.search(embedding_vector, namespace=namespace)
        if cache_hit:
            self.audit.info(actor, "vector_cache_hit", {"record_id": cache_hit.record_id, "confidence": cache_hit.confidence}, correlation_id)
            result = ExecutionResult(
                status="ok",
                route_tier="VERIFIED_VECTOR_CACHE",
                output=cache_hit.output,
                cached=True,
                details={"confidence": cache_hit.confidence, "record_id": cache_hit.record_id},
            )
            self._log_cycle(correlation_id, agent_id, result, objective, started_at)
            return result

        complexity = self.scorer.score(objective=objective, context=clean_context)
        route = self.router.route(complexity.score)
        connector_id = self._connector_for_route(route.decision.tier)

        try:
            self.registry.assert_connector_allowed(agent_id, connector_id)
        except RegistryError as exc:
            self.audit.blocked(
                actor,
                "connector_policy_block",
                {"error": str(exc), "agent_id": agent_id, "connector_id": connector_id},
                correlation_id,
            )
            raise

        try:
            self.cost_guard.assert_allowed(route.decision)
        except CostGuardError as exc:
            self.audit.blocked(actor, "cost_guard_block", {"error": str(exc), "route": route.decision.__dict__}, correlation_id)
            raise

        self.audit.info(
            actor,
            "route_selected",
            {
                "agent_id": agent_id,
                "connector_id": connector_id,
                "route": route.decision.__dict__,
                "reason": route.reason,
                "complexity": complexity.__dict__,
            },
            correlation_id,
        )

        if route.decision.tier == "HUMAN_REVIEW_QUEUE":
            try:
                self.approval_gate.require(
                    action="complex_or_external_execution",
                    reason=route.reason,
                    payload={
                        "objective": objective,
                        "complexity": complexity.__dict__,
                        "route": route.decision.__dict__,
                    },
                )
            except ApprovalRequired as exc:
                self.audit.blocked(actor, "approval_required", {"message": str(exc)}, correlation_id)
                result = ExecutionResult(
                    status="approval_required",
                    route_tier="HUMAN_REVIEW_QUEUE",
                    output=str(exc),
                    cached=False,
                    details={"complexity": complexity.__dict__, "reason": route.reason},
                )
                self._log_cycle(correlation_id, agent_id, result, objective, started_at)
                return result

        if route.decision.tier in ("DETERMINISTIC_LOCAL", "LOCAL_MODEL", "CLAUDE_API"):
            # All executable tiers go through the agent's run() method.
            # The agent internally cascades: Ollama → Claude → deterministic stub.
            output, agent_metrics = self._deterministic_execute(agent_id, clean_system, clean_context, objective, [connector_id])
        else:
            output = "Execution queued. No unsafe route executed."
            agent_metrics = {"agent": agent_id}

        if agent_policy.verifier_required:
            verified = self.verifier.verify_text_output(output)
            if not verified.passed:
                self.audit.blocked(actor, "verification_failed", {"reason": verified.reason}, correlation_id)
                result = ExecutionResult("blocked", route.decision.tier, verified.reason, False, {"verification": verified.__dict__})
                self._log_cycle(correlation_id, agent_id, result, objective, started_at)
                return result

        record_id = self.memory.commit_verified(embedding_vector, output, namespace=namespace)
        self.audit.info(
            actor,
            "execution_committed",
            {"record_id": record_id, "route_tier": route.decision.tier, "agent_metrics": agent_metrics},
            correlation_id,
        )
        result = ExecutionResult(
            status="ok",
            route_tier=route.decision.tier,
            output=output,
            cached=False,
            details={
                "record_id": record_id,
                "agent_id": agent_id,
                "connector_id": connector_id,
                "agent_metrics": agent_metrics,
                "complexity": complexity.__dict__,
            },
        )
        self._log_cycle(correlation_id, agent_id, result, objective, started_at)
        return result

    def _log_cycle(
        self,
        cycle_id: str,
        agent_id: str,
        result: ExecutionResult,
        objective: str,
        started_at: float,
    ) -> None:
        import datetime
        ts = time.time()
        try:
            self.cycle_log.record(CycleRecord(
                cycle_id=cycle_id,
                timestamp=ts,
                iso_timestamp=datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                agent_id=agent_id,
                route_tier=result.route_tier,
                objective_excerpt=objective[:120],
                output_excerpt=result.output[:200],
                status=result.status,
                duration_ms=int((ts - started_at) * 1000),
                cached=result.cached,
                details={k: v for k, v in result.details.items() if k in ("record_id", "agent_metrics", "confidence")},
            ))
        except Exception:
            # Cycle logging must never crash a live execution.
            pass

    def _connector_for_route(self, tier: str) -> str:
        if tier == "LOCAL_MODEL":
            return "ollama_local"
        # DETERMINISTIC_LOCAL, CLAUDE_API, and fallback all use local_files
        # (Claude is called by the agent implementation, not via a registered connector).
        return "local_files"

    def _deterministic_execute(
        self,
        agent_id: str,
        clean_system: str,
        clean_context: str,
        objective: str,
        connectors: List[str],
    ) -> tuple[str, Dict[str, Any]]:
        try:
            agent = load_agent(agent_id)
            result = agent.run(objective, clean_context, connectors)
            return result.output, result.metrics
        except ModuleNotFoundError:
            pass
        return (
            "DETERMINISTIC_LOCAL_RESULT\n"
            f"Objective: {objective}\n"
            f"System chars: {len(clean_system)}\n"
            f"Context chars: {len(clean_context)}\n"
            "Status: draft_created_no_external_execution"
        ), {"agent": agent_id, "system_chars": len(clean_system), "context_chars": len(clean_context)}
