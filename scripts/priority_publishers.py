#!/usr/bin/env python3
"""
Priority Stack Publishers for ProfitEngine

Integrates highest-value distribution channels:
1. Dev.to (500K+ developers)
2. Hashnode (2M+ tech audience)
3. YouTube (video upload + AdSense)
4. Beehiiv (newsletter + sponsorships)
5. Telegram (notifications)

Each publisher is independent and handles credential fallback gracefully.
"""
from __future__ import annotations

import os
import json
import httpx
from typing import Any, Dict, Optional
from datetime import datetime

# ── Environment Variables ────────────────────────────────────────────────────

DEVTO_API_KEY = os.getenv("DEVTO_API_KEY", "").strip()
HASHNODE_API_KEY = os.getenv("HASHNODE_API_KEY", "").strip()
HASHNODE_PUB_ID = os.getenv("HASHNODE_PUBLICATION_ID", "").strip()
YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID", "").strip()
YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET", "").strip()
YOUTUBE_REFRESH_TOKEN = os.getenv("YOUTUBE_REFRESH_TOKEN", "").strip()
BEEHIIV_API_KEY = os.getenv("BEEHIIV_API_KEY", "").strip()
BEEHIIV_PUB_ID = os.getenv("BEEHIIV_PUBLICATION_ID", "").strip()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

# ── Dev.to Publisher ────────────────────────────────────────────────────────

def publish_to_devto(article: Dict[str, Any]) -> Optional[str]:
    """Publish article to Dev.to"""
    if not DEVTO_API_KEY:
        print("[SKIP] Dev.to: DEVTO_API_KEY not configured")
        return None

    try:
        payload = {
            "article": {
                "title": article.get("title", ""),
                "body_markdown": article.get("body", ""),
                "published": True,
                "canonical_url": article.get("canonical_url", ""),
                "description": article.get("meta_description", "")[:160],
                "tags": article.get("tags", [])[:4],
            }
        }

        response = httpx.post(
            "https://dev.to/api/articles",
            headers={"api-key": DEVTO_API_KEY},
            json=payload,
            timeout=30,
        )

        if response.status_code == 201:
            data = response.json()
            url = data.get("url", "")
            print(f"[OK] Dev.to: Published → {url}")
            return url
        else:
            print(f"[FAIL] Dev.to {response.status_code}: {response.text[:200]}")
            return None
    except Exception as e:
        print(f"[FAIL] Dev.to: {e}")
        return None


# ── Hashnode Publisher ────────────────────────────────────────────────────────

def publish_to_hashnode(article: Dict[str, Any]) -> Optional[str]:
    """Publish article to Hashnode"""
    if not HASHNODE_API_KEY or not HASHNODE_PUB_ID:
        print("[SKIP] Hashnode: HASHNODE_API_KEY or HASHNODE_PUBLICATION_ID not configured")
        return None

    try:
        query = """
        mutation createPost($input: CreatePostInput!) {
            createPost(input: $input) {
                post {
                    slug
                }
            }
        }
        """

        variables = {
            "input": {
                "title": article.get("title", ""),
                "contentMarkdown": article.get("body", ""),
                "publicationId": HASHNODE_PUB_ID,
                "isRepublished": {
                    "originalArticleURL": article.get("canonical_url", "")
                } if article.get("canonical_url") else None,
            }
        }

        response = httpx.post(
            "https://gql.hashnode.com",
            json={"query": query, "variables": variables},
            headers={"Authorization": f"Bearer {HASHNODE_API_KEY}"},
            timeout=30,
        )

        if response.status_code == 200:
            data = response.json()
            if "data" in data and data["data"].get("createPost"):
                slug = data["data"]["createPost"]["post"]["slug"]
                url = f"https://hashnode.com/post/{slug}"
                print(f"[OK] Hashnode: Published → {url}")
                return url
            else:
                error = data.get("errors", [{}])[0].get("message", "Unknown error")
                print(f"[FAIL] Hashnode: {error}")
                return None
        else:
            print(f"[FAIL] Hashnode {response.status_code}: {response.text[:200]}")
            return None
    except Exception as e:
        print(f"[FAIL] Hashnode: {e}")
        return None


# ── YouTube Publisher ────────────────────────────────────────────────────────

def publish_to_youtube(article: Dict[str, Any], video_path: Optional[str] = None) -> Optional[str]:
    """Publish video to YouTube (placeholder - requires full OAuth setup)"""
    if not YOUTUBE_CLIENT_ID or not YOUTUBE_CLIENT_SECRET or not YOUTUBE_REFRESH_TOKEN:
        print("[SKIP] YouTube: YOUTUBE credentials not configured")
        return None

    if not video_path:
        print("[SKIP] YouTube: Video file not provided")
        return None

    try:
        # This is a placeholder - full implementation requires:
        # 1. Google API OAuth token refresh
        # 2. MediaFileUpload handling
        # 3. Proper error handling
        print("[INFO] YouTube: Video upload requires full OAuth setup (see documentation)")
        return None
    except Exception as e:
        print(f"[FAIL] YouTube: {e}")
        return None


# ── Beehiiv Newsletter Publisher ────────────────────────────────────────────

def publish_to_beehiiv_newsletter(article: Dict[str, Any]) -> Optional[str]:
    """Queue article for Beehiiv newsletter"""
    if not BEEHIIV_API_KEY:
        print("[SKIP] Beehiiv: BEEHIIV_API_KEY not configured")
        return None

    try:
        # Beehiiv API for creating newsletter edition
        payload = {
            "publication_id": BEEHIIV_PUB_ID if BEEHIIV_PUB_ID else "",
            "name": f"Newsletter: {article.get('title', '')[:50]}",
            "content": article.get("body", ""),
            "seo_title": article.get("title", ""),
            "seo_description": article.get("meta_description", "")[:160],
        }

        response = httpx.post(
            "https://api.beehiiv.com/v1/editions",
            headers={"Authorization": f"Bearer {BEEHIIV_API_KEY}"},
            json=payload,
            timeout=30,
        )

        if response.status_code in [200, 201]:
            data = response.json()
            edition_id = data.get("data", {}).get("id", "")
            print(f"[OK] Beehiiv: Newsletter queued → Edition {edition_id}")
            return f"beehiiv://edition/{edition_id}"
        else:
            print(f"[FAIL] Beehiiv {response.status_code}: {response.text[:200]}")
            return None
    except Exception as e:
        print(f"[FAIL] Beehiiv: {e}")
        return None


# ── Telegram Notification ────────────────────────────────────────────────────

def notify_telegram_publication(article: Dict[str, Any], platform_results: Dict[str, Optional[str]]) -> bool:
    """Send Telegram notification of new publication"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[SKIP] Telegram: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not configured")
        return False

    try:
        platforms_published = [p for p, url in platform_results.items() if url]
        platforms_text = "\n".join([f"✅ {p}" for p in platforms_published])

        message = f"""
📝 *New Article Published*

*{article.get('title', 'Untitled')}*

Published to:
{platforms_text}

🔗 GitHub: {article.get('canonical_url', 'N/A')}
💰 Revenue streams: Gumroad, Affiliates, AdSense
"""

        response = httpx.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "Markdown",
            },
            timeout=10,
        )

        if response.status_code == 200:
            print(f"[OK] Telegram: Notification sent")
            return True
        else:
            print(f"[FAIL] Telegram {response.status_code}: {response.text[:100]}")
            return False
    except Exception as e:
        print(f"[FAIL] Telegram: {e}")
        return False


# ── Priority Publishers Orchestrator ────────────────────────────────────────

def publish_to_priority_platforms(article: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """Publish article to all priority platforms (B stack)"""
    results = {}

    print("\n[PUBLISHING] Priority Stack Platforms")
    print("-" * 60)

    # Dev.to
    results["dev.to"] = publish_to_devto(article)

    # Hashnode
    results["hashnode"] = publish_to_hashnode(article)

    # YouTube (placeholder)
    results["youtube"] = publish_to_youtube(article)

    # Beehiiv Newsletter
    results["beehiiv"] = publish_to_beehiiv_newsletter(article)

    # Telegram Notification
    notify_telegram_publication(article, results)

    print("-" * 60)
    return results


def generate_priority_report(article: Dict[str, Any], results: Dict[str, Optional[str]]) -> Dict[str, Any]:
    """Generate priority publisher report"""
    return {
        "timestamp": datetime.now().isoformat(),
        "article_title": article.get("title", ""),
        "platforms": {
            "dev_to": {
                "published": results.get("dev.to") is not None,
                "url": results.get("dev.to"),
            },
            "hashnode": {
                "published": results.get("hashnode") is not None,
                "url": results.get("hashnode"),
            },
            "youtube": {
                "published": results.get("youtube") is not None,
                "url": results.get("youtube"),
                "note": "Requires OAuth setup",
            },
            "beehiiv": {
                "published": results.get("beehiiv") is not None,
                "reference": results.get("beehiiv"),
            },
            "telegram": {
                "note": "Notification sent if configured",
            },
        },
        "reach_estimate": {
            "dev_to": "500K+ developers",
            "hashnode": "2M+ tech audience",
            "youtube": "Subscribers + suggested videos",
            "beehiiv": "Email subscribers + sponsors",
        },
        "revenue_impact": {
            "dev_to": "$20-100/mo (discovery → Gumroad)",
            "hashnode": "$20-100/mo (SEO + discovery)",
            "youtube": "$100-200/mo (AdSense pending)",
            "beehiiv": "$100-500/mo (sponsorships)",
            "total": "$240-900/mo additional",
        },
    }


# ── Main Entry ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Test with sample article
    test_article = {
        "title": "Building APIs with Cloudflare Workers",
        "body": "Full article content here...",
        "meta_description": "Learn to build and deploy APIs using Cloudflare Workers serverless platform.",
        "tags": ["api", "cloudflare", "serverless"],
        "canonical_url": "https://quantam101.github.io/content/posts/cloudflare-workers-api",
    }

    print("=" * 60)
    print("PRIORITY STACK PUBLISHER TEST")
    print("=" * 60)

    results = publish_to_priority_platforms(test_article)
    report = generate_priority_report(test_article, results)

    print("\n" + "=" * 60)
    print("PRIORITY PUBLISHER REPORT")
    print("=" * 60)
    print(json.dumps(report, indent=2))
