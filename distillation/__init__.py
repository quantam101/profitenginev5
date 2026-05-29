"""
ProfitEngine v5 — Data Distillation Engine
==========================================

A deterministic, zero-token pre-processing layer that maximizes information
density before any LLM call. Implements the five pillars from the spec:

    1. Semantic compression — strip noise (HTML, stopwords, whitespace).
    2. Token-efficient prompts — output constraints + few-shot density helpers.
    3. Structural optimization — YAML vs JSON token comparison.
    4. Logic offloading — deterministic helpers (sort/format/math) do not call LLMs.
    5. Tiered processing — classify each request into low / mid / high tiers.

No external dependencies — pure stdlib so it ships clean in CI.
"""
from .compressor import compress, count_tokens, strip_html, yaml_vs_json
from .router import route_tier, Tier
from .cache import DistillationCache
from .engine import DistillationEngine, DistillationResult

__version__ = "0.1.0"
__all__ = [
    "compress",
    "count_tokens",
    "strip_html",
    "yaml_vs_json",
    "route_tier",
    "Tier",
    "DistillationCache",
    "DistillationEngine",
    "DistillationResult",
]
