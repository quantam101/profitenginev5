"""
Blog Publisher agent.

Takes a generated article (from content-gen) and publishes it to:
  1. Dev.to (developer community, free, indexed by Google quickly)
  2. GitHub Pages (your own site, permanent, no platform lock-in)
  3. Sends Gmail digest notification

Required .env vars:
  DEVTO_API_KEY          — from dev.to/settings/extensions
  GITHUB_CONTENT_TOKEN   — GitHub personal access token (repo scope)
  GITHUB_CONTENT_OWNER   — GitHub username
  GITHUB_CONTENT_REPO    — content repository name
  GMAIL_USER + GMAIL_APP_PASSWORD + ALERT_EMAIL — for digest emails
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, List

from runtime.agents import AgentExecution
from runtime.devto_client import publish_article as devto_publish
from runtime.github_client import publish_file as github_publish
from runtime.gmail_client import send_email


def _extract_article(context: str) -> Dict[str, Any]:
    """Extract article JSON from content-gen output."""
    match = re.search(r"ARTICLE_JSON:(\{.+\})", context, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    return {}


def _make_devto_body(article: Dict[str, Any]) -> str:
    """Prepend meta description as a callout to the markdown body."""
    meta = article.get("meta_description", "")
    body = article.get("body", "")
    if meta:
        return f"> {meta}\n\n{body}"
    return body


def _make_github_markdown(article: Dict[str, Any], date_str: str) -> str:
    """Build Jekyll-compatible frontmatter + markdown for GitHub Pages."""
    title = article.get("title", "Untitled").replace('"', '\\"')
    meta = article.get("meta_description", "").replace('"', '\\"')
    tags = article.get("tags", [])
    body = article.get("body", "")
    tags_yaml = "\n".join(f"  - {t}" for t in tags)
    return (
        f"---\n"
        f'title: "{title}"\n'
        f'description: "{meta}"\n'
        f"date: {date_str}\n"
        f"tags:\n{tags_yaml}\n"
        f"layout: post\n"
        f"---\n\n"
        f"{body}"
    )


class Agent:
    id = "blog-publisher"

    def run(self, objective: str, context: str, connectors: List[str]) -> AgentExecution:
        article = _extract_article(context)

        # If no article in context, treat objective as the article title with body as context
        if not article.get("body"):
            article = {
                "title": objective[:80],
                "meta_description": "",
                "slug": objective[:50].lower().replace(" ", "-").strip("-"),
                "tags": ["ai", "automation"],
                "body": context or f"# {objective}\n\nContent coming soon.",
            }

        title = article.get("title", "Untitled")
        slug = article.get("slug", title[:40].lower().replace(" ", "-"))
        tags = article.get("tags", [])
        now = datetime.now(tz=timezone.utc)
        date_str = now.strftime("%Y-%m-%d")
        filename = f"{date_str}-{slug}.md"

        published: List[Dict[str, str]] = []
        errors: List[str] = []

        # ── Publish to Dev.to ──────────────────────────────────────────────
        try:
            devto_resp = devto_publish(
                title=title,
                body_markdown=_make_devto_body(article),
                tags=tags,
                published=True,
            )
            url = devto_resp.get("url", "")
            published.append({"platform": "Dev.to", "title": title, "url": url})
        except RuntimeError as exc:
            errors.append(f"Dev.to: {exc}")

        # ── Publish to GitHub Pages ────────────────────────────────────────
        try:
            gh_resp = github_publish(
                filename=filename,
                content=_make_github_markdown(article, date_str),
                commit_message=f"Add post: {title}",
            )
            url = gh_resp.get("html_url", "")
            published.append({"platform": "GitHub Pages", "title": title, "url": url})
        except RuntimeError as exc:
            errors.append(f"GitHub: {exc}")

        # ── Send email digest ──────────────────────────────────────────────
        if published:
            rows = "".join(
                f"<li><a href='{p['url']}'>{p['title']}</a> — {p['platform']}</li>"
                for p in published
            )
            send_email(
                subject=f"ProfitEngine: Published '{title}'",
                body_html=(
                    f"<h2>Article Published ✅</h2><ul>{rows}</ul>"
                    f"<p>{'Errors: ' + str(errors) if errors else ''}</p>"
                ),
            )

        # ── Build output ───────────────────────────────────────────────────
        status = "ok" if published else "failed"
        output_lines = [
            f"BLOG_PUBLISHER_RESULT",
            f"Title: {title}",
            f"Status: {status}",
            f"Published to: {', '.join(p['platform'] for p in published) or 'none'}",
        ]
        for p in published:
            output_lines.append(f"  {p['platform']}: {p['url']}")
        if errors:
            output_lines.append(f"Errors: {'; '.join(errors)}")

        return AgentExecution(
            output="\n".join(output_lines),
            metrics={
                "agent": self.id,
                "tier": "deterministic",
                "published_count": len(published),
                "platforms": ",".join(p["platform"] for p in published),
                "errors": len(errors),
            },
        )
