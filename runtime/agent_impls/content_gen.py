"""
Content Gen agent.

Generates SEO-optimized long-form blog articles using the inference cascade.
Cascade order: Ollama → Groq → Gemini → Claude → stub

Each article includes:
  - Compelling H1 title
  - Meta description (for SEO)
  - 1,000-1,500 word body with H2/H3 subheadings
  - Affiliate keyword markers (replaced by blog_publisher)
  - Natural internal/external link suggestions

Set AFFILIATE_LINKS in .env as JSON to inject real affiliate links:
  AFFILIATE_LINKS={"Python book": "https://amzn.to/xxx", "VPS hosting": "https://ref.url"}
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List

from runtime.agents import AgentExecution
from runtime.inference_cascade import infer

_SYSTEM = """You are a senior SEO content writer and affiliate marketer.
Write long-form, helpful, authoritative blog articles that:
1. Rank on Google for the target keyword
2. Provide genuine value to readers
3. Naturally recommend relevant products/services
4. Are 1,000-1,500 words with clear H2/H3 subheadings

Format your response as JSON:
{
  "title": "Full article title",
  "meta_description": "155 character SEO description",
  "slug": "url-friendly-slug",
  "tags": ["tag1", "tag2", "tag3", "tag4"],
  "body": "Full markdown article here..."
}

The body should use markdown: # for H1, ## for H2, ### for H3, **bold**, *italic*.
Include 2-3 product/tool recommendations with [AFFILIATE:keyword] placeholders."""


def _load_affiliate_map() -> Dict[str, str]:
    """Load affiliate links from AFFILIATE_LINKS env var (JSON)."""
    raw = os.getenv("AFFILIATE_LINKS", "{}").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def _inject_affiliate_links(body: str, affiliate_map: Dict[str, str]) -> str:
    """Replace [AFFILIATE:keyword] placeholders with real markdown links."""
    for keyword, url in affiliate_map.items():
        placeholder = f"[AFFILIATE:{keyword}]"
        link = f"[{keyword}]({url})"
        body = body.replace(placeholder, link)
    # Remove any remaining unresolved placeholders (no URL configured yet)
    import re
    body = re.sub(r"\[AFFILIATE:([^\]]+)\]", r"\1", body)
    return body


class Agent:
    id = "content-gen"

    def run(self, objective: str, context: str, connectors: List[str]) -> AgentExecution:
        # Build the content brief
        prompt = (
            f"Write a complete SEO blog article about:\n{objective}\n\n"
            + (f"Additional context:\n{context}\n\n" if context else "")
            + "Return the full JSON response with title, meta_description, slug, tags, and body."
        )

        result, tier = infer(_SYSTEM, prompt, max_tokens=2048)

        # Parse article JSON
        article: Dict[str, Any] = {}
        try:
            start = result.find("{")
            end = result.rfind("}") + 1
            if start >= 0 and end > start:
                article = json.loads(result[start:end])
        except (json.JSONDecodeError, ValueError):
            pass

        # Fallback: treat entire result as body
        if not article.get("body"):
            article = {
                "title": objective[:80],
                "meta_description": objective[:155],
                "slug": objective[:50].lower().replace(" ", "-").strip("-"),
                "tags": ["ai", "automation", "productivity"],
                "body": result,
            }

        # Inject affiliate links
        affiliate_map = _load_affiliate_map()
        article["body"] = _inject_affiliate_links(article.get("body", ""), affiliate_map)

        # Word count check
        word_count = len(article.get("body", "").split())

        output = (
            f"CONTENT_GEN_RESULT\n"
            f"Title: {article.get('title', 'Unknown')}\n"
            f"Slug: {article.get('slug', '')}\n"
            f"Words: {word_count}\n"
            f"Tags: {', '.join(article.get('tags', []))}\n"
            f"Meta: {article.get('meta_description', '')}\n\n"
            f"ARTICLE_JSON:{json.dumps(article)}"
        )

        return AgentExecution(
            output=output,
            metrics={
                "agent": self.id,
                "tier": tier,
                "word_count": word_count,
                "affiliate_links_injected": len(affiliate_map),
            },
        )
