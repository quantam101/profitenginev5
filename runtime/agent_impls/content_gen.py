"""
Content Gen agent — SEO blog article writer.

Token efficiency changes (Data Distillation):
  • System prompt ends with OUTPUT_CONSTRAINT_JSON (no preamble / filler)
  • Uses structured_output.extract_json() instead of ad-hoc json slice
  • Activates distillation on long context (distill=True in infer())
  • max_tokens capped at 2 048 (tier budget enforcement handles the rest)
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List

from runtime.agents import AgentExecution
from runtime.inference_cascade import infer
from runtime.structured_output import OUTPUT_CONSTRAINT_JSON, extract_json

_SYSTEM = (
    "You are a senior SEO content writer and affiliate marketer. "
    "Write long-form, helpful, authoritative blog articles that rank on Google, "
    "provide genuine value, and naturally recommend relevant products. "
    "Target 1 000–1 500 words with clear H2/H3 subheadings. "
    "Include 2-3 product/tool recommendations with [AFFILIATE:keyword] placeholders."
    "\n\nOutput schema:"
    "\n{"
    '\n  "title": "<Full article title>",'
    '\n  "meta_description": "<155-char SEO description>",'
    '\n  "slug": "<url-friendly-slug>",'
    '\n  "tags": ["tag1","tag2","tag3"],'
    '\n  "body": "<Full markdown article>"'
    "\n}"
    + OUTPUT_CONSTRAINT_JSON
)

_FALLBACK_ARTICLE: Dict[str, Any] = {
    "title": "",
    "meta_description": "",
    "slug": "",
    "tags": ["ai", "automation", "productivity"],
    "body": "",
}


def _load_affiliate_map() -> Dict[str, str]:
    raw = os.getenv("AFFILIATE_LINKS", "{}").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def _inject_affiliate_links(body: str, affiliate_map: Dict[str, str]) -> str:
    for keyword, url in affiliate_map.items():
        body = body.replace(f"[AFFILIATE:{keyword}]", f"[{keyword}]({url})")
    return re.sub(r"\[AFFILIATE:([^\]]+)\]", r"\1", body)


class Agent:
    id = "content-gen"

    def run(self, objective: str, context: str, connectors: List[str]) -> AgentExecution:
        prompt = (
            f"Write a complete SEO blog article about:\n{objective}"
            + (f"\n\nAdditional context:\n{context}" if context.strip() else "")
            + "\n\nReturn the full JSON object — no other text."
        )

        # Use distillation when context is substantial (> 800 chars)
        use_distill = len(context) > 800
        result, tier = infer(
            _SYSTEM, prompt, max_tokens=2048,
            distill=use_distill, objective=objective,
        )

        # Robust structured extraction
        parsed = extract_json(
            result,
            required_keys=["title", "body"],
            fallback={**_FALLBACK_ARTICLE, "title": objective[:80], "body": result},
        )

        article: Dict[str, Any] = parsed.data if parsed.ok else parsed.fallback  # type: ignore[assignment]

        # Ensure slug and tags have sensible defaults
        if not article.get("slug"):
            article["slug"] = re.sub(r"[^a-z0-9]+", "-", objective[:50].lower()).strip("-")
        if not article.get("tags"):
            article["tags"] = ["ai", "automation", "productivity"]
        if not article.get("meta_description"):
            article["meta_description"] = objective[:155]

        # Inject affiliate links
        affiliate_map = _load_affiliate_map()
        article["body"] = _inject_affiliate_links(article.get("body", ""), affiliate_map)

        word_count = len(article.get("body", "").split())

        output = (
            "CONTENT_GEN_RESULT\n"
            f"Title: {article.get('title', '')}\n"
            f"Slug: {article.get('slug', '')}\n"
            f"Words: {word_count}\n"
            f"Tags: {', '.join(article.get('tags', []))}\n"
            f"Meta: {article.get('meta_description', '')}\n\n"
            f"ARTICLE_JSON:{json.dumps(article)}"
        )

        return AgentExecution(
            output=output,
            metrics={
                "agent":                   self.id,
                "tier":                    tier,
                "word_count":              word_count,
                "affiliate_links_injected": len(affiliate_map),
                "json_parse_ok":           parsed.ok,
                "distilled":               use_distill,
            },
        )
