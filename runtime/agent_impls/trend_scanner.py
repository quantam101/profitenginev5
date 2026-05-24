"""
Trend Scanner agent.

Scrapes free, no-auth sources for trending topics that have affiliate/content potential:
  - Hacker News top stories (Firebase API, no auth)
  - Reddit hot posts from high-traffic subreddits (public JSON API)
  - GitHub trending repos (public, no auth)

Returns a ranked list of content-ready topics.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List
from urllib.request import Request, urlopen
from urllib.error import URLError

from runtime.agents import AgentExecution
from runtime.inference_cascade import infer

# High-value subreddits for affiliate content niches
_SUBREDDITS = [
    "passive_income",
    "SideProject",
    "entrepreneur",
    "productivity",
    "homelab",
    "selfhosted",
    "learnprogramming",
]

_SYSTEM = (
    "You are a content strategist. Given a list of trending topics, "
    "select the top 3 that would make the best SEO blog posts for "
    "generating affiliate revenue. For each, provide: "
    "1) a compelling article title, 2) target keyword, 3) affiliate angle "
    "(what product/service could be recommended). "
    "Format as JSON array: [{\"title\": ..., \"keyword\": ..., \"affiliate_angle\": ...}]"
)


def _fetch_json(url: str, headers: dict | None = None, timeout: int = 10) -> Any:
    """Fetch JSON from a URL. Returns None on failure."""
    try:
        req = Request(url, headers=headers or {"User-Agent": "ProfitEngine/5.0 (content bot)"})
        with urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (URLError, json.JSONDecodeError, Exception):
        return None


def _hackernews_topics() -> List[str]:
    """Get top HN story titles."""
    ids = _fetch_json("https://hacker-news.firebaseio.com/v0/topstories.json")
    if not ids:
        return []
    topics = []
    for story_id in ids[:8]:
        story = _fetch_json(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json")
        if story and story.get("title") and story.get("type") == "story":
            topics.append(story["title"])
        if len(topics) >= 5:
            break
    return topics


def _reddit_topics() -> List[str]:
    """Get hot Reddit post titles from high-value subreddits."""
    topics = []
    for sub in _SUBREDDITS[:3]:
        data = _fetch_json(
            f"https://www.reddit.com/r/{sub}/hot.json?limit=5&t=day",
            headers={"User-Agent": "ProfitEngine/5.0 (content bot)"},
        )
        if not data:
            continue
        posts = data.get("data", {}).get("children", [])
        for post in posts[:3]:
            title = post.get("data", {}).get("title", "")
            if title and len(title) > 10 and not title.startswith("["):
                topics.append(f"{title} (r/{sub})")
        if len(topics) >= 6:
            break
    return topics


def _github_trending_topics() -> List[str]:
    """Get GitHub trending repo names/descriptions as topic hints."""
    data = _fetch_json(
        "https://api.github.com/search/repositories"
        "?q=created:>2026-01-01&sort=stars&order=desc&per_page=5",
        headers={"User-Agent": "ProfitEngine/5.0"},
    )
    if not data:
        return []
    topics = []
    for repo in data.get("items", [])[:5]:
        desc = repo.get("description") or repo.get("full_name", "")
        if desc:
            topics.append(f"GitHub: {desc}")
    return topics


class Agent:
    id = "trend-scanner"

    def run(self, objective: str, context: str, connectors: List[str]) -> AgentExecution:
        raw_topics: List[str] = []
        raw_topics.extend(_hackernews_topics())
        raw_topics.extend(_reddit_topics())
        raw_topics.extend(_github_trending_topics())

        if not raw_topics:
            raw_topics = [
                "Best free AI tools for small businesses 2026",
                "How to make passive income with AI automation",
                "Top self-hosted alternatives to expensive SaaS",
                "Build an automated income system with open source AI",
                "Best OCI free tier projects for developers",
            ]

        topics_text = "\n".join(f"- {t}" for t in raw_topics[:15])
        prompt = f"Trending topics:\n{topics_text}\n\nObjective: {objective}"

        result, tier = infer(_SYSTEM, prompt, max_tokens=800)

        # Try to extract JSON from AI response
        selected_topics: List[Dict[str, str]] = []
        try:
            start = result.find("[")
            end = result.rfind("]") + 1
            if start >= 0 and end > start:
                selected_topics = json.loads(result[start:end])
        except (json.JSONDecodeError, ValueError):
            # Fallback: use raw topics as titles
            selected_topics = [
                {"title": t, "keyword": t.split()[0], "affiliate_angle": ""}
                for t in raw_topics[:3]
            ]

        output = (
            f"TREND_SCANNER_RESULT\n"
            f"Raw topics found: {len(raw_topics)}\n"
            f"AI-selected topics: {len(selected_topics)}\n\n"
            + json.dumps(selected_topics, indent=2)
        )

        return AgentExecution(
            output=output,
            metrics={
                "agent": self.id,
                "tier": tier,
                "topics_found": len(raw_topics),
                "topics_selected": len(selected_topics),
            },
        )
