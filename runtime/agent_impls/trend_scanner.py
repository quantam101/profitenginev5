"""
Trend Scanner agent — finds affiliate-ready topics from free public APIs.

Sources (all zero-cost, no auth):
  • Hacker News top stories   (Firebase JSON API)
  • Reddit hot posts          (public .json endpoint)
  • GitHub trending repos     (search API, unauthenticated)

Token efficiency changes (Data Distillation):
  • Offloads topic fetching + formatting to Python (Tier 0 — zero token cost)
  • Sends only a compact topic list to the LLM (≤ 15 items × ~15 words each)
  • OUTPUT_CONSTRAINT_JSON enforces JSON-only response — no preamble
  • Uses structured_output.extract_json() for robust parsing
  • max_tokens reduced from 800 → 512 (3 compact JSON objects is plenty)
"""
from __future__ import annotations

import json
from typing import Any, Dict, List
from urllib.request import Request, urlopen
from urllib.error import URLError

from runtime.agents import AgentExecution
from runtime.inference_cascade import infer
from runtime.structured_output import OUTPUT_CONSTRAINT_JSON, extract_json

_SUBREDDITS = [
    "passive_income", "SideProject", "entrepreneur",
    "productivity", "homelab", "selfhosted", "learnprogramming",
]

# ── system prompt (token-lean, JSON-constrained) ──────────────────────────────
_SYSTEM = (
    "You are a content strategist. "
    "From the trending topics list, select the top 3 for SEO affiliate blog posts. "
    "For each: title, keyword, affiliate_angle (product/service to recommend). "
    "Output schema: [{\"title\":\"...\",\"keyword\":\"...\",\"affiliate_angle\":\"...\"}]"
    + OUTPUT_CONSTRAINT_JSON
)

_FALLBACK_TOPICS = [
    "Best free AI tools for small businesses 2026",
    "How to make passive income with AI automation",
    "Top self-hosted alternatives to expensive SaaS",
    "Build an automated income system with open source AI",
    "Best OCI free tier projects for developers",
]


# ── deterministic data-fetching (Tier 0 — zero token cost) ───────────────────

def _fetch_json(url: str, headers: dict | None = None, timeout: int = 10) -> Any:
    try:
        req = Request(url, headers=headers or {"User-Agent": "ProfitEngine/5.0 (content-bot)"})
        with urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def _hackernews_topics(limit: int = 5) -> List[str]:
    ids = _fetch_json("https://hacker-news.firebaseio.com/v0/topstories.json")
    if not ids:
        return []
    topics: List[str] = []
    for story_id in ids[:limit * 2]:
        story = _fetch_json(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json")
        if story and story.get("type") == "story" and story.get("title"):
            topics.append(story["title"])
        if len(topics) >= limit:
            break
    return topics


def _reddit_topics(limit: int = 6) -> List[str]:
    topics: List[str] = []
    for sub in _SUBREDDITS[:3]:
        data = _fetch_json(
            f"https://www.reddit.com/r/{sub}/hot.json?limit=5&t=day",
            headers={"User-Agent": "ProfitEngine/5.0 (content-bot)"},
        )
        if not data:
            continue
        for post in data.get("data", {}).get("children", [])[:3]:
            title = post.get("data", {}).get("title", "")
            if title and len(title) > 10 and not title.startswith("["):
                topics.append(f"{title} (r/{sub})")
        if len(topics) >= limit:
            break
    return topics


def _github_trending_topics(limit: int = 4) -> List[str]:
    data = _fetch_json(
        "https://api.github.com/search/repositories"
        "?q=created:>2026-01-01&sort=stars&order=desc&per_page=8",
        headers={"User-Agent": "ProfitEngine/5.0"},
    )
    if not data:
        return []
    return [
        f"GitHub: {repo.get('description') or repo.get('full_name', '')}"
        for repo in data.get("items", [])[:limit]
        if repo.get("description") or repo.get("full_name")
    ]


def _build_topics_text(topics: List[str], max_items: int = 15) -> str:
    """
    Compress the topic list into a compact bullet string.
    Deterministic formatting — zero token cost.
    """
    deduped = list(dict.fromkeys(t.strip() for t in topics if t.strip()))[:max_items]
    return "\n".join(f"- {t}" for t in deduped)


# ── agent ─────────────────────────────────────────────────────────────────────

class Agent:
    id = "trend-scanner"

    def run(self, objective: str, context: str, connectors: List[str]) -> AgentExecution:
        # Tier 0: collect topics deterministically (no LLM, no tokens)
        raw_topics: List[str] = (
            _hackernews_topics()
            + _reddit_topics()
            + _github_trending_topics()
        )
        if not raw_topics:
            raw_topics = _FALLBACK_TOPICS

        # Pre-format into a compact string (Python formatting, not LLM)
        topics_text = _build_topics_text(raw_topics)

        # Tier 1+: LLM only sees the compact list + objective (low token count)
        prompt = f"Trending topics:\n{topics_text}\n\nObjective: {objective}"

        result, tier = infer(_SYSTEM, prompt, max_tokens=512)

        # Robust JSON array extraction
        parsed = extract_json(
            result,
            required_keys=None,     # array — no key check
            fallback=[
                {"title": t, "keyword": t.split()[0], "affiliate_angle": ""}
                for t in raw_topics[:3]
            ],
            allow_array=True,
        )

        selected: List[Dict[str, str]] = parsed.data if parsed.ok else parsed.fallback  # type: ignore[assignment]
        if not isinstance(selected, list):
            selected = parsed.fallback  # type: ignore[assignment]

        output = (
            "TREND_SCANNER_RESULT\n"
            f"Raw topics found: {len(raw_topics)}\n"
            f"AI-selected topics: {len(selected)}\n\n"
            + json.dumps(selected, indent=2)
        )

        return AgentExecution(
            output=output,
            metrics={
                "agent":            self.id,
                "tier":             tier,
                "topics_found":     len(raw_topics),
                "topics_selected":  len(selected),
                "json_parse_ok":    parsed.ok,
            },
        )
