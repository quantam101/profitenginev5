"""
Distillation engine — orchestrates the five pillars end-to-end.

Public API
----------
::

    engine = DistillationEngine()
    result = engine.distill("<html>... long text ...</html>", task="summarize")

    result.compressed_text    # already-distilled text, safe to send to an LLM
    result.tier               # 'low' | 'mid' | 'high'
    result.recommended_model
    result.estimated_cost_usd
    result.cache_hit          # True when served from the cache
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any

from .cache import DistillationCache
from .compressor import CompressionStats, compress
from .router import RoutingDecision, route_tier


_SYSTEM_PROMPT_TEMPLATE = (
    "You are a senior engineer. Respond in {format} only. "
    "No conversational filler, no apologies."
)


@dataclass
class DistillationResult:
    original_text: str
    compressed_text: str
    compression: CompressionStats
    routing: RoutingDecision
    cache_hit: bool = False
    served_value: Any = None
    suggested_system_prompt: str = ""

    @property
    def estimated_cost_usd(self) -> float:
        return 0.0 if self.cache_hit else self.routing.estimated_cost_usd

    @property
    def tier(self) -> str:
        return self.routing.tier.value

    @property
    def recommended_model(self) -> str:
        return self.routing.recommended_model

    def to_dict(self) -> dict[str, Any]:
        return {
            "tier": self.tier,
            "recommended_model": self.recommended_model,
            "estimated_cost_usd": self.estimated_cost_usd,
            "cache_hit": self.cache_hit,
            "compression": asdict(self.compression),
            "routing": {
                "tier": self.routing.tier.value,
                "reason": self.routing.reason,
                "recommended_model": self.routing.recommended_model,
                "estimated_cost_usd": self.routing.estimated_cost_usd,
                "estimated_tokens": self.routing.estimated_tokens,
            },
            "suggested_system_prompt": self.suggested_system_prompt,
            "compressed_text": self.compressed_text,
            "served_value": self.served_value,
        }


@dataclass
class DistillationEngine:
    """Stateful orchestrator. One instance per process is fine."""
    cache: DistillationCache = field(default_factory=DistillationCache)

    def distill(
        self,
        text: str,
        *,
        task: str = "extract",
        output_format: str = "JSON",
        use_cache: bool = True,
    ) -> DistillationResult:
        compressed, comp_stats = compress(text)
        routing = route_tier(compressed, task=task)
        served = None
        cache_hit = False
        if use_cache:
            served = self.cache.get(task, compressed)
            cache_hit = served is not None
        prompt = _SYSTEM_PROMPT_TEMPLATE.format(format=output_format)
        return DistillationResult(
            original_text=text,
            compressed_text=compressed,
            compression=comp_stats,
            routing=routing,
            cache_hit=cache_hit,
            served_value=served,
            suggested_system_prompt=prompt,
        )

    def remember(self, task: str, text: str, value: Any) -> None:
        """Store a model's response so future identical requests skip the LLM."""
        compressed, _ = compress(text)
        saved = route_tier(compressed, task=task).estimated_tokens
        self.cache.put(task, compressed, value, saved_tokens=saved)

    def metrics(self) -> dict[str, Any]:
        """Snapshot for the /api/distillation/* endpoints + dashboard."""
        return self.cache.stats()
