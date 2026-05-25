"""
Blog Publisher agent.

Takes a generated article (from content-gen) and publishes it to:
  1. Dev.to          — free, indexed by Google quickly (DEVTO_API_KEY)
  2. Hashnode        — SEO backlinks + dev audience (HASHNODE_API_KEY + HASHNODE_PUBLICATION_ID)
  3. Medium          — large general audience (MEDIUM_API_KEY + MEDIUM_AUTHOR_ID)
  4. GitHub Pages    — permanent, no lock-in (GITHUB_CONTENT_TOKEN)
  5. Gmail digest    — email notification on success (GMAIL_APP_PASSWORD)

Required .env vars (at least one blog platform + GitHub):
  GITHUB_CONTENT_TOKEN   — GitHub personal access token (repo scope)
  GITHUB_CONTENT_OWNER   — GitHub username (default: quantam101)
  GITHUB_CONTENT_REPO    — content repo (default: content)
  GMAIL_USER + GMAIL_APP_PASSWORD + ALERT_EMAIL — for digest emails

Optional blog platform keys (enable any/all):
  DEVTO_API_KEY          — from dev.to/settings/extensions
  HASHNODE_API_KEY + HASHNODE_PUBLICATION_ID — from hashnode.com/settings/developer
  MEDIUM_API_KEY + MEDIUM_AUTHOR_ID — from medium.com/me/settings

Optional affiliate injection:
  AFFILIATE_LINKS        — JSON string {"keyword": "https://url"}
  AMAZON_PARTNER_TAG     — Amazon Associates tag (default: alreadyhere-20)
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List

from runtime.agents import AgentExecution
from runtime.devto_client import publish_article as devto_publish
from runtime.github_client import publish_file as github_publish
from runtime.gmail_client import send_email

# Import optional platform clients
try:
    from runtime.hashnode_client import publish_article as hashnode_publish
    _HAS_HASHNODE = True
except ImportError:
    _HAS_HASHNODE = False

try:
    from runtime.medium_client import publish_article as medium_publish
    _HAS_MEDIUM = True
except ImportError:
    _HAS_MEDIUM = False

_AMAZON_TAG = os.getenv("AMAZON_PARTNER_TAG", "alreadyhere-20")


def _extract_article(context: str) -> Dict[str, Any]:
    """Extract article JSON from content-gen output."""
    match = re.search(r"ARTICLE_JSON:(\{.+\})", context, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    return {}


def _inject_affiliates(body: str) -> str:
    """Inject affiliate links for [AFFILIATE:keyword] placeholders."""
    try:
        affiliate_map: Dict[str, str] = json.loads(os.getenv("AFFILIATE_LINKS", "{}"))
    except json.JSONDecodeError:
        affiliate_map = {}

    # Inject Amazon Associates tag into Amazon product links that don't already have a tag
    if _AMAZON_TAG:
        def _add_amazon_tag(m: "re.Match[str]") -> str:
            url: str = m.group(0)
            if "tag=" in url:
                return url
            sep = "&" if "?" in url else "?"
            return f"{url}{sep}tag={_AMAZON_TAG}"

        body = re.sub(
            r"https?://(?:www\.)?amazon\.com/[^\s\)\"'>]+",
            _add_amazon_tag,
            body,
        )

    # Resolve [AFFILIATE:keyword] placeholders
    for keyword, url in affiliate_map.items():
        body = body.replace(f"[AFFILIATE:{keyword}]", f"[{keyword}]({url})")

    # Strip any remaining unresolved placeholders
    body = re.sub(r"\[AFFILIATE:([^\]]+)\]", r"\1", body)
    return body


def _make_devto_body(article: Dict[str, Any]) -> str:
    meta = article.get("meta_description", "")
    body = _inject_affiliates(article.get("body", ""))
    return f"> {meta}\n\n{body}" if meta else body


def _make_github_markdown(article: Dict[str, Any], date_str: str) -> str:
    title = article.get("title", "Untitled").replace('"', '\\"')
    meta = article.get("meta_description", "").replace('"', '\\"')
    tags = article.get("tags", [])
    body = _inject_affiliates(article.get("body", ""))
    tags_yaml = "\n".join(f"  - {t}" for t in tags)
    return (
        f"---\n"
        f'title: "{title}"\n'
        f'description: "{meta}"\n'
        f"date: {date_str}\n"
        f"tags:\n{tags_yaml}\n"
        f"layout: post\n"
        f"---\n\n"
        f"<!-- FTC Disclosure: This post may contain affiliate links. We may earn a small "
        f"commission at no extra cost to you. -->\n\n"
        f"{body}"
    )


class Agent:
    id = "blog-publisher"

    def run(self, objective: str, context: str, connectors: List[str]) -> AgentExecution:
        article = _extract_article(context)

        if not article.get("body"):
            article = {
                "title": objective[:80],
                "meta_description": "",
                "slug": re.sub(r"[^a-z0-9-]", "", objective[:50].lower().replace(" ", "-")).strip("-"),
                "tags": ["ai", "automation"],
                "body": context or f"# {objective}\n\nContent coming soon.",
            }

        title = article.get("title", "Untitled")
        slug = re.sub(r"[^a-z0-9-]", "", (article.get("slug") or title[:40]).lower().replace(" ", "-")).strip("-")
        tags = article.get("tags", [])
        now = datetime.now(tz=timezone.utc)
        date_str = now.strftime("%Y-%m-%d")
        filename = f"{date_str}-{slug}.md"

        published: List[Dict[str, str]] = []
        errors: List[str] = []
        canonical_url = ""

        # ── 1. Publish to GitHub Pages first (canonical URL source) ───────
        try:
            gh_resp = github_publish(
                filename=filename,
                content=_make_github_markdown(article, date_str),
                commit_message=f"Add post: {title}",
            )
            gh_owner = os.getenv("GITHUB_CONTENT_OWNER", "quantam101")
            gh_repo = os.getenv("GITHUB_CONTENT_REPO", "content")
            canonical_url = f"https://{gh_owner}.github.io/{gh_repo}/posts/{filename.replace('.md', '.html')}"
            url = gh_resp.get("html_url", canonical_url)
            published.append({"platform": "GitHub Pages", "title": title, "url": url})
        except RuntimeError as exc:
            errors.append(f"GitHub: {exc}")

        # ── 2. Dev.to ──────────────────────────────────────────────────────
        try:
            devto_resp = devto_publish(
                title=title,
                body_markdown=_make_devto_body(article),
                tags=tags,
                canonical_url=canonical_url or None,
                published=True,
            )
            published.append({"platform": "Dev.to", "title": title, "url": devto_resp.get("url", "")})
        except RuntimeError as exc:
            errors.append(f"Dev.to: {exc}")

        # ── 3. Hashnode ────────────────────────────────────────────────────
        if _HAS_HASHNODE and os.getenv("HASHNODE_API_KEY") and os.getenv("HASHNODE_PUBLICATION_ID"):
            try:
                hn_resp = hashnode_publish(
                    title=title,
                    body_markdown=_make_devto_body(article),
                    tags=tags,
                    canonical_url=canonical_url or None,
                )
                published.append({"platform": "Hashnode", "title": title, "url": hn_resp.get("url", "")})
            except RuntimeError as exc:
                errors.append(f"Hashnode: {exc}")

        # ── 4. Medium ──────────────────────────────────────────────────────
        if _HAS_MEDIUM and os.getenv("MEDIUM_API_KEY") and os.getenv("MEDIUM_AUTHOR_ID"):
            try:
                med_resp = medium_publish(
                    title=title,
                    body_markdown=_make_devto_body(article),
                    tags=tags,
                    canonical_url=canonical_url or None,
                )
                published.append({"platform": "Medium", "title": title, "url": med_resp.get("url", "")})
            except RuntimeError as exc:
                errors.append(f"Medium: {exc}")

        # ── 5. Send email digest ───────────────────────────────────────────
        if published:
            rows = "".join(
                f"<li><a href='{p['url']}'>{p['title']}</a> — {p['platform']}</li>"
                for p in published
            )
            try:
                send_email(
                    subject=f"ProfitEngine: Published '{title}'",
                    body_html=(
                        f"<h2>Article Published</h2><ul>{rows}</ul>"
                        f"<p>Platforms: {', '.join(p['platform'] for p in published)}</p>"
                        f"{'<p style=\"color:red\">Errors: ' + '; '.join(errors) + '</p>' if errors else ''}"
                    ),
                )
            except Exception as exc:  # noqa: BLE001
                errors.append(f"Email digest: {exc}")

        # ── 6. Build output ────────────────────────────────────────────────
        status = "ok" if published else "failed"
        output_lines = [
            "BLOG_PUBLISHER_RESULT",
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
