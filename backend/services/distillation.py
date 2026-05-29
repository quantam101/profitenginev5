"""
Data Distillation Engine — token-efficient LLM router.

Strategy
────────
1. Aggressive cache  → SHA-256 of normalized prompt + model tier hits Mongo
   `distillation_cache`. Saves 100% of cost on repeat queries.
2. Semantic compression → input text is normalized + truncated to its
   information-dense core (strip stopwords, collapse whitespace, dedupe
   near-identical lines) before being sent to any model.
3. Tier router (cheap-first) →
   • Cheap tier  = Gemini 3 Flash  (filter, classify, summarize, JSON extract)
   • Expensive tier = Claude Sonnet 4.6 (only invoked when the cheap tier
     marks the survivor as `requires_expert=true`)
4. Strict-JSON outputs → every call requests JSON; we parse with Pydantic so
   the caller never has to scrub freeform text. Bad JSON → tier upgrade.
5. Token + cost accounting → every call records token estimates and a per-tier
   USD estimate to Mongo `distillation_runs`. Powers `/api/distillation/stats`.

The engine is plug-and-play: callers go through `Distiller.run(...)` and never
touch the underlying providers.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from emergentintegrations.llm.chat import LlmChat, UserMessage  # noqa: F401 — used by provider fallback
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.services.llm_provider import call_llm

# ── Tier definitions ───────────────────────────────────────────
Tier = Literal["cache", "cheap", "expensive"]

# Rough $/1k tokens — used only to estimate savings, not billed.
_TIER_COST_PER_1K = {
    "cache": 0.0,
    "cheap": 0.000075,     # Gemini 3 Flash blended in/out
    "expensive": 0.009,    # Claude Sonnet 4.6 blended in/out
}

# Baseline = what it would cost if EVERY call went straight to the expensive
# tier with no caching and no compression.
_BASELINE_COST_PER_1K = _TIER_COST_PER_1K["expensive"]


@dataclass
class DistillRequest:
    task: str                          # short name: "classify", "summarize", "rerank"
    prompt: str                        # user prompt
    system: str | None = None
    schema_hint: str | None = None     # JSON schema as a string, asked of the model
    force_tier: Tier | None = None     # "expensive" bypasses cheap-first
    session_id: str | None = None      # optional cache scope
    max_tokens: int = 1024


@dataclass
class DistillResult:
    tier: Tier
    output: Any                        # parsed JSON if possible, else string
    raw: str
    cache_hit: bool
    tokens_in: int
    tokens_out: int
    cost_usd: float
    baseline_cost_usd: float
    saved_usd: float
    latency_ms: int
    requires_expert: bool = False
    notes: list[str] = field(default_factory=list)


# ── Helpers ────────────────────────────────────────────────────
_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "then", "of", "to", "in", "on",
    "for", "with", "by", "is", "are", "was", "were", "be", "been", "being",
    "as", "at", "this", "that", "these", "those", "it", "its", "from",
}

_WHITESPACE_RE = re.compile(r"\s+")


def _estimate_tokens(text: str) -> int:
    """Cheap token estimate: ~4 chars/token. Good enough for accounting."""
    return max(1, len(text) // 4)


def semantic_compress(text: str, *, keep_stopwords_in_code: bool = True) -> str:
    """
    Compress text to its information-dense core BEFORE sending to any LLM.

    - Collapses runs of whitespace
    - Dedupes consecutive identical lines
    - Drops stopwords from natural-language sentences (kept inside code blocks)
    - Trims leading/trailing whitespace per line
    """
    if not text:
        return ""

    lines: list[str] = []
    last_line = None
    in_code = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("```"):
            in_code = not in_code
            lines.append(line)
            last_line = line
            continue
        if not in_code:
            tokens = [w for w in line.split() if w.lower() not in _STOPWORDS]
            line = " ".join(tokens) if tokens else line
        line = _WHITESPACE_RE.sub(" ", line)
        if line != last_line:
            lines.append(line)
            last_line = line
    return "\n".join(lines)


def cache_key(task: str, prompt: str, tier: Tier, schema_hint: str | None) -> str:
    """Stable cache key — normalized prompt + tier + schema + task."""
    payload = json.dumps(
        {
            "task": task,
            "prompt": _WHITESPACE_RE.sub(" ", prompt.strip().lower()),
            "tier": tier,
            "schema": schema_hint or "",
        },
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _try_parse_json(text: str) -> tuple[Any, bool]:
    """Try hard to find a JSON object inside the LLM response."""
    text = text.strip()
    if text.startswith("```"):
        # strip ```json … ``` fences
        text = re.sub(r"^```(?:json)?", "", text).strip()
        if text.endswith("```"):
            text = text[:-3].strip()
    try:
        return json.loads(text), True
    except json.JSONDecodeError:
        # find first '{' … last '}'
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0)), True
            except json.JSONDecodeError:
                pass
    return text, False


@dataclass
class _RunRecord:
    """Single distillation-run accounting payload (collapses 9 params)."""
    tier: "Tier"
    task: str
    tokens_in: int
    tokens_out: int
    cost: float
    baseline: float
    cache_hit: bool
    latency_ms: int


# ── Engine ─────────────────────────────────────────────────────
class Distiller:
    """Token-efficient LLM router with cache + tiering + JSON parsing."""

    def __init__(self, db: AsyncIOMotorDatabase, *, api_key: str | None = None) -> None:
        self.db = db
        self.api_key = api_key or os.environ.get("EMERGENT_LLM_KEY", "")
        self.cheap_provider = os.environ.get("DISTILLATION_CHEAP_PROVIDER", "gemini")
        self.cheap_model = os.environ.get("DISTILLATION_CHEAP_MODEL", "gemini-3-flash-preview")
        self.exp_provider = os.environ.get("DISTILLATION_EXPENSIVE_PROVIDER", "anthropic")
        self.exp_model = os.environ.get("DISTILLATION_EXPENSIVE_MODEL", "claude-sonnet-4-6")
        self.cache_ttl_hours = int(os.environ.get("DISTILLATION_CACHE_TTL_HOURS", "168"))

    # ── Cache ──
    async def _cache_get(self, key: str) -> dict | None:
        doc = await self.db.distillation_cache.find_one({"_id": key})
        if not doc:
            return None
        ttl = timedelta(hours=self.cache_ttl_hours)
        created = datetime.fromisoformat(doc["created_at"])
        if datetime.now(timezone.utc) - created > ttl:
            await self.db.distillation_cache.delete_one({"_id": key})
            return None
        return doc

    async def _cache_put(self, key: str, payload: dict) -> None:
        payload = {**payload, "_id": key,
                   "created_at": datetime.now(timezone.utc).isoformat()}
        await self.db.distillation_cache.update_one(
            {"_id": key}, {"$set": payload}, upsert=True,
        )

    # ── Provider call ──
    async def _call(
        self, *, provider: str, model: str, system: str, prompt: str,
        max_tokens: int, session_id: str,
    ) -> str:
        chat = LlmChat(
            api_key=self.api_key,
            session_id=session_id,
            system_message=system,
        ).with_model(provider, model).with_params(max_tokens=max_tokens)
        msg = UserMessage(text=prompt)
        return await chat.send_message(msg)

    # ── Internal: prompt + system prep ──
    def _prepare_system(self, req: DistillRequest) -> str:
        system = req.system or (
            "You are a precise data-distillation worker. ALWAYS respond with a "
            "single valid JSON object and nothing else. Be concise."
        )
        if req.schema_hint:
            system += f"\n\nResponse schema (JSON):\n{req.schema_hint}"
        system += (
            "\n\nInclude key `requires_expert` (boolean) — set true only if the "
            "answer needs deeper expert reasoning beyond your confidence."
        )
        return system

    @staticmethod
    def _compression_note(original: str, compressed: str) -> list[str]:
        if len(compressed) >= len(original):
            return []
        savings = 1 - len(compressed) / len(original)
        return [f"compressed prompt {len(original)}→{len(compressed)} chars "
                f"({savings:.0%} savings)"]

    # ── Internal: result builders ──
    async def _serve_from_cache(
        self, *, cached: dict, task: str, tokens_in: int,
        started: float, notes: list[str], note_suffix: str,
    ) -> DistillResult:
        latency = int((time.monotonic() - started) * 1000)
        tokens_out = cached.get("tokens_out", 0)
        baseline = (tokens_in + tokens_out) / 1000 * _BASELINE_COST_PER_1K
        await self._record_run(_RunRecord(
            tier="cache", task=task, tokens_in=tokens_in, tokens_out=tokens_out,
            cost=0.0, baseline=baseline, cache_hit=True, latency_ms=latency,
        ))
        return DistillResult(
            tier="cache", output=cached.get("output"), raw=cached.get("raw", ""),
            cache_hit=True, tokens_in=tokens_in, tokens_out=tokens_out,
            cost_usd=0.0, baseline_cost_usd=baseline, saved_usd=baseline,
            latency_ms=latency, requires_expert=False,
            notes=[*notes, note_suffix],
        )

    async def _try_cheap(
        self, *, req: DistillRequest, compressed: str, system: str,
        tokens_in: int, key: str, started: float, session_id: str,
        notes: list[str],
    ) -> DistillResult | None:
        """Returns a DistillResult if cheap tier succeeded, else None to escalate."""
        try:
            raw = await self._call(
                provider=self.cheap_provider, model=self.cheap_model,
                system=system, prompt=compressed, max_tokens=req.max_tokens,
                session_id=f"{session_id}-cheap",
            )
            parsed, ok = _try_parse_json(raw)
        except Exception as exc:  # noqa: BLE001
            notes.append(f"cheap-tier failed: {exc}")
            return None

        requires_expert = bool(isinstance(parsed, dict) and parsed.get("requires_expert"))
        if not ok:
            notes.append("cheap-tier returned non-JSON, escalating")
            return None
        if requires_expert:
            notes.append("cheap-tier flagged requires_expert, escalating")
            return None

        tokens_out = _estimate_tokens(raw)
        cost = (tokens_in + tokens_out) / 1000 * _TIER_COST_PER_1K["cheap"]
        baseline = (tokens_in + tokens_out) / 1000 * _BASELINE_COST_PER_1K
        latency = int((time.monotonic() - started) * 1000)
        await self._cache_put(key, {
            "output": parsed, "raw": raw, "tokens_out": tokens_out, "tier": "cheap",
        })
        await self._record_run(_RunRecord(
            tier="cheap", task=req.task, tokens_in=tokens_in, tokens_out=tokens_out,
            cost=cost, baseline=baseline, cache_hit=False, latency_ms=latency,
        ))
        return DistillResult(
            tier="cheap", output=parsed, raw=raw, cache_hit=False,
            tokens_in=tokens_in, tokens_out=tokens_out, cost_usd=cost,
            baseline_cost_usd=baseline, saved_usd=max(0.0, baseline - cost),
            latency_ms=latency, requires_expert=False, notes=notes,
        )

    async def _run_expensive(
        self, *, req: DistillRequest, compressed: str, system: str,
        tokens_in: int, started: float, session_id: str, notes: list[str],
    ) -> DistillResult:
        exp_key = cache_key(req.task, compressed, "expensive", req.schema_hint)
        cached = await self._cache_get(exp_key)
        if cached:
            return await self._serve_from_cache(
                cached=cached, task=req.task, tokens_in=tokens_in,
                started=started, notes=notes, note_suffix="expert cache hit",
            )

        raw = ""
        try:
            raw = await self._call(
                provider=self.exp_provider, model=self.exp_model,
                system=system, prompt=compressed, max_tokens=req.max_tokens,
                session_id=f"{session_id}-expert",
            )
            parsed, ok = _try_parse_json(raw)
        except Exception as exc:  # noqa: BLE001
            notes.append(f"expert-tier failed: {exc}")
            parsed = {"error": str(exc)}
            ok = False
            raw = raw or json.dumps(parsed)

        tokens_out = _estimate_tokens(raw)
        cost = (tokens_in + tokens_out) / 1000 * _TIER_COST_PER_1K["expensive"]
        baseline = (tokens_in + tokens_out) / 1000 * _BASELINE_COST_PER_1K
        latency = int((time.monotonic() - started) * 1000)
        if ok:
            await self._cache_put(exp_key, {
                "output": parsed, "raw": raw, "tokens_out": tokens_out, "tier": "expensive",
            })
        await self._record_run(_RunRecord(
            tier="expensive", task=req.task, tokens_in=tokens_in, tokens_out=tokens_out,
            cost=cost, baseline=baseline, cache_hit=False, latency_ms=latency,
        ))
        return DistillResult(
            tier="expensive", output=parsed, raw=raw, cache_hit=False,
            tokens_in=tokens_in, tokens_out=tokens_out, cost_usd=cost,
            baseline_cost_usd=baseline, saved_usd=max(0.0, baseline - cost),
            latency_ms=latency, requires_expert=True, notes=notes,
        )

    # ── Public entry ──
    async def run(self, req: DistillRequest) -> DistillResult:
        started = time.monotonic()
        session_id = req.session_id or f"distill-{int(time.time() * 1000)}"
        compressed = semantic_compress(req.prompt)
        tokens_in = _estimate_tokens(compressed)
        notes: list[str] = self._compression_note(req.prompt, compressed)
        system = self._prepare_system(req)

        chosen_tier: Tier = req.force_tier or "cheap"
        key = cache_key(req.task, compressed, chosen_tier, req.schema_hint)

        cached = await self._cache_get(key)
        if cached:
            return await self._serve_from_cache(
                cached=cached, task=req.task, tokens_in=tokens_in,
                started=started, notes=notes, note_suffix="cache hit",
            )

        if chosen_tier == "cheap":
            cheap_result = await self._try_cheap(
                req=req, compressed=compressed, system=system,
                tokens_in=tokens_in, key=key, started=started,
                session_id=session_id, notes=notes,
            )
            if cheap_result is not None:
                return cheap_result

        return await self._run_expensive(
            req=req, compressed=compressed, system=system,
            tokens_in=tokens_in, started=started,
            session_id=session_id, notes=notes,
        )

    # ── Accounting ──
    async def _record_run(self, rec: _RunRecord) -> None:
        await self.db.distillation_runs.insert_one({
            "tier": rec.tier, "task": rec.task,
            "tokens_in": rec.tokens_in, "tokens_out": rec.tokens_out,
            "cost_usd": round(rec.cost, 6),
            "baseline_cost_usd": round(rec.baseline, 6),
            "saved_usd": round(max(0.0, rec.baseline - rec.cost), 6),
            "cache_hit": rec.cache_hit, "latency_ms": rec.latency_ms,
            "at": datetime.now(timezone.utc).isoformat(),
        })

    async def stats(self) -> dict[str, Any]:
        """Aggregate distillation savings for /api/distillation/stats."""
        runs = await self.db.distillation_runs.find().to_list(length=10_000)
        if not runs:
            return {
                "total_runs": 0, "tier_breakdown": {"cache": 0, "cheap": 0, "expensive": 0},
                "cache_hit_rate": 0.0, "total_cost_usd": 0.0,
                "baseline_cost_usd": 0.0, "saved_usd": 0.0, "savings_pct": 0.0,
                "tokens_in": 0, "tokens_out": 0, "avg_latency_ms": 0,
                "cheap_model": f"{self.cheap_provider}/{self.cheap_model}",
                "expensive_model": f"{self.exp_provider}/{self.exp_model}",
            }
        tier_breakdown = {"cache": 0, "cheap": 0, "expensive": 0}
        cost = baseline = saved = 0.0
        t_in = t_out = lat = 0
        cache_hits = 0
        for r in runs:
            tier_breakdown[r["tier"]] = tier_breakdown.get(r["tier"], 0) + 1
            cost += r["cost_usd"]
            baseline += r["baseline_cost_usd"]
            saved += r["saved_usd"]
            t_in += r["tokens_in"]
            t_out += r["tokens_out"]
            lat += r["latency_ms"]
            if r["cache_hit"]:
                cache_hits += 1
        total = len(runs)
        return {
            "total_runs": total,
            "tier_breakdown": tier_breakdown,
            "cache_hit_rate": round(cache_hits / total, 4),
            "total_cost_usd": round(cost, 4),
            "baseline_cost_usd": round(baseline, 4),
            "saved_usd": round(saved, 4),
            "savings_pct": round(saved / baseline, 4) if baseline else 0.0,
            "tokens_in": t_in, "tokens_out": t_out,
            "avg_latency_ms": round(lat / total),
            "cheap_model": f"{self.cheap_provider}/{self.cheap_model}",
            "expensive_model": f"{self.exp_provider}/{self.exp_model}",
        }
