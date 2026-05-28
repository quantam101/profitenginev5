"""
backend/services/content_generation_service.py — ProfitEngine v5.0
Script/content generation service backed by the LLM failover chain.
Mirrors agents/content/index.js logic in Python.
"""

import hashlib
import os
import re
import time
from dataclasses import dataclass, field
from typing import Any, Optional

from .llm_runner import llm_complete

# ── Config ────────────────────────────────────────────────────────────────────

MIN_WORD_COUNT = int(os.environ.get("MIN_WORD_COUNT", "600"))
MAX_WORD_COUNT = int(os.environ.get("MAX_WORD_COUNT", "2000"))
SITE_DOMAIN    = os.environ.get("SITE_DOMAIN", "alreadyherellc.com")

CONTENT_TYPES = [
    "how-to guide",
    "listicle",
    "case study",
    "product review",
    "comparison post",
    "ultimate guide",
]

# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class ContentScript:
    id:           str
    slug:         str
    title:        str
    content_type: str
    niche:        Optional[str]
    keywords:     list[str]
    body:         str
    word_count:   int
    generated_at: str
    published:    bool
    metadata:     dict[str, Any]

# ── Helpers ───────────────────────────────────────────────────────────────────

def _title_hash(title: str) -> str:
    return hashlib.md5(title.encode()).hexdigest()[:12]

def _slugify(title: str) -> str:
    return re.sub(r"^-|-$", "", re.sub(r"[^a-z0-9]+", "-", title.lower()))

def _word_count(text: str) -> int:
    return len(text.split())

def _build_prompt(idea: str, content_type: str, niche: Optional[str] = None) -> str:
    niche_str = niche or "general"
    return f"""Write a comprehensive {content_type} blog post optimized for SEO, reader engagement, and affiliate revenue.

Topic: "{idea}"
Niche: {niche_str}
Angle: practical guide for beginners

Requirements:
- {MIN_WORD_COUNT}-{MAX_WORD_COUNT} words
- Compelling H1 title (different from topic if needed)
- SEO-optimized H2/H3 subheadings
- Natural affiliate mentions with [AMAZON_LINK] placeholder
- Engaging hook in first 2 sentences
- Expert-level insights (not generic)
- Concrete examples and data points
- Clear action steps in each section
- Strong CTA at end

Frontmatter required:
---
title: [compelling SEO title]
description: [150-char meta description]
tags: [comma list]
date: {time.strftime("%Y-%m-%d")}
niche: {niche_str}
---"""

def _quality_gate(body: str, title: str) -> bool:
    wc = _word_count(body)
    if wc < MIN_WORD_COUNT:
        return False
    if "##" not in body:
        return False
    return True

# ── Public API ────────────────────────────────────────────────────────────────

def generate_script_from_idea(
    idea: str,
    content_type: Optional[str] = None,
    niche: Optional[str] = None,
    keywords: Optional[list[str]] = None,
) -> ContentScript:
    """Generate a full blog script from a topic idea using the LLM failover chain."""
    ct = content_type or CONTENT_TYPES[0]
    prompt = _build_prompt(idea, ct, niche)

    body = llm_complete(prompt, max_tokens=1800)

    if not _quality_gate(body, idea):
        retry_prompt = prompt + "\n\nCRITICAL: Must be at least 800 words. Expand each section significantly."
        body = llm_complete(retry_prompt, max_tokens=2000)

    slug         = _slugify(idea)
    title_hash   = _title_hash(idea)
    generated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    return ContentScript(
        id           = f"script_{int(time.time())}_{title_hash}",
        slug         = slug,
        title        = idea,
        content_type = ct,
        niche        = niche,
        keywords     = keywords or [],
        body         = body,
        word_count   = _word_count(body),
        generated_at = generated_at,
        published    = False,
        metadata     = {
            "generated_by": "ai",
            "model":        "groq/llama-3.3-70b-versatile (failover chain)",
        },
    )
