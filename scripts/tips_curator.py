#!/usr/bin/env python3
"""
Tips Curator — Extract actionable "tip of the day" content from published articles.

Extracts tips from published articles and formats them for multiple channels:
- Twitter threads (30-second reads, shareable hooks)
- LinkedIn posts (professional insights, engagement)
- Instagram graphics (visual, inspirational)
- Email snippets (newsletter-ready)
- Blog "Daily Tip" sections (SEO-optimized)

Monetization built-in:
- Promote tools/services in tips
- Generate "101 Tips" ebook for Gumroad
- Create sponsor opportunities
- Track engagement metrics per tip

Usage:
    python scripts/tips_curator.py --extract
    python scripts/tips_curator.py --generate-daily
    python scripts/tips_curator.py --format twitter
    python scripts/tips_curator.py --publish all
    TIPS_VERIFY_ONLY=true python scripts/tips_curator.py

Required env vars:
    GROQ_API_KEY           — for tip extraction via LLM
    GITHUB_CONTENT_TOKEN   — to fetch published articles
    GITHUB_CONTENT_OWNER   — repo owner (e.g. quantam101)
    GITHUB_CONTENT_REPO    — repo name (e.g. content)

Optional:
    TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET
    LINKEDIN_ACCESS_TOKEN, LINKEDIN_PERSON_URN
    INSTAGRAM_ACCESS_TOKEN (via Facebook Business API)
    GUMROAD_ACCESS_TOKEN
    TIPS_OUTPUT_DIR        — directory to store formatted tips (default: data/tips)
    TIPS_EBOOK_CHAPTERS    — number of chapters for ebook (default: 5)
    AFFILIATE_LINKS        — JSON map of {tool_name: affiliate_url}
    MONETIZATION_ENABLED   — set to false to disable sponsor/promo injection
"""
from __future__ import annotations

import asyncio
import argparse
import base64
import json
import os
import pathlib
import re
import sys
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from urllib.parse import urljoin

import httpx
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv(pathlib.Path(__file__).resolve().parents[1] / ".env")

# ── Config ─────────────────────────────────────────────────────────────────────

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GH_BASE = "https://api.github.com"

GROQ_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GMAOS_GROQ_MODEL", "llama-3.3-70b-versatile")

GH_TOKEN = os.getenv("GITHUB_CONTENT_TOKEN", "").strip()
GH_OWNER = os.getenv("GITHUB_CONTENT_OWNER", "quantam101").strip()
GH_REPO = os.getenv("GITHUB_CONTENT_REPO", "content").strip()
GH_BRANCH = os.getenv("GITHUB_CONTENT_BRANCH", "main").strip()
GH_DIR = os.getenv("GITHUB_CONTENT_DIR", "posts").strip()

TWITTER_API_KEY = os.getenv("TWITTER_API_KEY", "").strip()
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET", "").strip()
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN", "").strip()
TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET", "").strip()

LINKEDIN_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN", "").strip()
LINKEDIN_URN = os.getenv("LINKEDIN_PERSON_URN", "").strip()

INSTAGRAM_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN", "").strip()
IG_USER_ID = os.getenv("IG_USER_ID", "").strip()

GUMROAD_TOKEN = os.getenv("GUMROAD_ACCESS_TOKEN", "").strip()

AFFILIATE_LINKS_JSON = os.getenv("AFFILIATE_LINKS", "{}").strip()
AMAZON_TAG = os.getenv("AMAZON_PARTNER_TAG", "alreadyhere-20").strip()

TIPS_OUTPUT_DIR = pathlib.Path(os.getenv("TIPS_OUTPUT_DIR", "data/tips"))
TIPS_EBOOK_CHAPTERS = int(os.getenv("TIPS_EBOOK_CHAPTERS", "5"))
MONETIZATION_ENABLED = os.getenv("MONETIZATION_ENABLED", "true").lower() in {"1", "true", "yes", "on"}
VERIFY_ONLY = os.getenv("TIPS_VERIFY_ONLY", "").strip().lower() in {"1", "true", "yes", "on"}

try:
    AFFILIATE_LINKS = json.loads(AFFILIATE_LINKS_JSON)
except (json.JSONDecodeError, ValueError):
    AFFILIATE_LINKS = {}

# ── Data Models ────────────────────────────────────────────────────────────────

@dataclass
class Tip:
    """Single actionable tip extracted from an article."""
    id: str
    title: str
    content: str
    category: str  # "quick_hack", "tool_rec", "productivity", "business_insight", "ai_prompt"
    reading_time_seconds: int  # target 30 seconds
    source_article: str  # URL or filename
    key_takeaway: str
    curiosity_hook: str  # opening line to intrigue reader
    monetization: Optional[Dict[str, Any]] = None  # {type: "tool_promo"|"sponsor", link, cta}
    created_at: str = None
    engagement_data: Optional[Dict[str, Any]] = None  # {impressions, clicks, shares}

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc).isoformat()


@dataclass
class FormattedTip:
    """Tip formatted for a specific channel."""
    tip_id: str
    channel: str  # "twitter", "linkedin", "instagram", "email", "blog"
    headline: str
    body: str
    cta: str  # call-to-action
    hashtags: List[str]
    image_prompt: Optional[str] = None  # for Instagram/graphics
    thread_posts: Optional[List[str]] = None  # for Twitter threads
    formatted_at: str = None

    def __post_init__(self):
        if self.formatted_at is None:
            self.formatted_at = datetime.now(timezone.utc).isoformat()


# ── LLM Tip Extraction ─────────────────────────────────────────────────────────

async def extract_tips_from_article(
    article_content: str,
    article_url: str,
    article_title: str,
    max_tips: int = 5,
) -> List[Tip]:
    """
    Use Groq to extract 3-5 actionable tips from an article.
    Each tip should be a quick hack, tool recommendation, productivity tip, business insight, or AI prompt.
    """
    if not GROQ_KEY:
        print("[ERROR] GROQ_API_KEY not set; cannot extract tips")
        return []

    prompt = f"""You are a content curator expert. Extract {max_tips} highly actionable, shareable tips from this article.

Article Title: {article_title}
Article Content:
{article_content[:2000]}

For EACH tip, respond with a JSON object containing:
{{
  "title": "Short title (5-8 words)",
  "content": "Main tip (1-2 sentences, under 100 words)",
  "category": "quick_hack|tool_rec|productivity|business_insight|ai_prompt",
  "reading_time_seconds": <30 or less>,
  "key_takeaway": "The core insight (one sentence)",
  "curiosity_hook": "Opening hook that makes reader want to read (e.g., 'Did you know...', 'This one trick...', 'The secret to...'"
}}

Respond with ONLY a valid JSON array of tip objects. No markdown, no explanation.
Example output:
[
  {{"title": "The 80/20 Rule for Content", "content": "80% of your results come from 20% of your effort. Focus tips on the highest-leverage tasks.", "category": "productivity", "reading_time_seconds": 20, "key_takeaway": "Prioritize ruthlessly.", "curiosity_hook": "This one simple principle changed everything"}},
  ...
]
"""

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.post(
                GROQ_URL,
                headers={"Authorization": f"Bearer {GROQ_KEY}"},
                json={
                    "model": GROQ_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 2000,
                },
            )
            response.raise_for_status()
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

            # Parse JSON array from response
            tips_data = json.loads(content)
            if not isinstance(tips_data, list):
                tips_data = [tips_data]

            tips = []
            for i, tip_data in enumerate(tips_data[:max_tips]):
                tip = Tip(
                    id=f"{article_url.split('/')[-1]}_tip_{i+1}",
                    title=tip_data.get("title", ""),
                    content=tip_data.get("content", ""),
                    category=tip_data.get("category", "quick_hack"),
                    reading_time_seconds=min(tip_data.get("reading_time_seconds", 30), 30),
                    source_article=article_url,
                    key_takeaway=tip_data.get("key_takeaway", ""),
                    curiosity_hook=tip_data.get("curiosity_hook", ""),
                )
                tips.append(tip)

            print(f"[EXTRACT] Got {len(tips)} tips from {article_title}")
            return tips

        except Exception as e:
            print(f"[ERROR] Failed to extract tips: {e}")
            return []


# ── Fetch Published Articles ───────────────────────────────────────────────────

async def fetch_recent_articles(days: int = 7) -> List[Dict[str, Any]]:
    """Fetch recent published articles from GitHub content repo."""
    if not all([GH_TOKEN, GH_OWNER, GH_REPO, GH_DIR]):
        print("[ERROR] GitHub credentials not configured")
        return []

    headers = {"Authorization": f"token {GH_TOKEN}"}
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    async with httpx.AsyncClient(headers=headers, timeout=30) as client:
        try:
            # Get list of files in posts directory
            url = f"{GH_BASE}/repos/{GH_OWNER}/{GH_REPO}/contents/{GH_DIR}"
            response = await client.get(url)
            response.raise_for_status()
            files = response.json()

            articles = []
            for file_obj in files:
                if file_obj.get("type") != "file" or not file_obj.get("name", "").endswith(".md"):
                    continue

                if file_obj.get("updated_at", "") < cutoff:
                    continue

                # Fetch file content
                content_response = await client.get(file_obj["url"])
                content_response.raise_for_status()
                content_data = content_response.json()

                if "content" in content_data:
                    decoded = base64.b64decode(content_data["content"]).decode("utf-8")
                    articles.append({
                        "filename": file_obj["name"],
                        "path": file_obj["path"],
                        "content": decoded,
                        "url": f"https://github.com/{GH_OWNER}/{GH_REPO}/blob/{GH_BRANCH}/{file_obj['path']}",
                        "updated_at": file_obj.get("updated_at", ""),
                    })

            print(f"[FETCH] Got {len(articles)} recent articles")
            return articles

        except Exception as e:
            print(f"[ERROR] Failed to fetch articles: {e}")
            return []


# ── Format Tips for Channels ───────────────────────────────────────────────────

def format_tip_for_twitter(tip: Tip) -> FormattedTip:
    """Format tip as Twitter thread with curiosity hook + CTA."""
    thread_posts = [
        f"{tip.curiosity_hook} 🧵\n\n{tip.content}",
        f"Key takeaway: {tip.key_takeaway}",
        f"Category: {tip.category.replace('_', ' ').title()}\nReadable in ~{tip.reading_time_seconds}sec",
    ]

    if tip.monetization and tip.monetization.get("type") == "tool_promo":
        thread_posts.append(f"👉 Try: {tip.monetization.get('link', 'link.com')}\n{tip.monetization.get('cta', '')}")

    hashtags = [
        "#TipOfTheDay",
        f"#{tip.category.replace('_', '').title()}",
        "#ProductivityTips",
        "#AlreadyHere",
    ]

    return FormattedTip(
        tip_id=tip.id,
        channel="twitter",
        headline=tip.title,
        body="\n\n".join(thread_posts),
        cta="Read more in our daily tips →",
        hashtags=hashtags,
        thread_posts=thread_posts,
    )


def format_tip_for_linkedin(tip: Tip) -> FormattedTip:
    """Format tip as professional LinkedIn post with engagement hooks."""
    headline = f"💡 {tip.title}"
    body = f"""{tip.curiosity_hook}

{tip.content}

🎯 Key Insight: {tip.key_takeaway}

📌 {tip.category.replace('_', ' ').title()} — readable in ~{tip.reading_time_seconds}sec

#ProductivityTips #BusinessInsights #AlreadyHere"""

    if tip.monetization and tip.monetization.get("type") == "tool_promo":
        body += f"\n\n🔗 Check this out: {tip.monetization.get('link', 'link.com')}"

    return FormattedTip(
        tip_id=tip.id,
        channel="linkedin",
        headline=headline,
        body=body,
        cta="Share your thoughts in the comments",
        hashtags=["#ProductivityTips", "#BusinessInsights", "#AlreadyHere"],
    )


def format_tip_for_instagram(tip: Tip) -> FormattedTip:
    """Format tip as Instagram caption + graphic prompt."""
    caption = f"""{tip.curiosity_hook}

{tip.content}

✨ {tip.key_takeaway}

#TipOfTheDay #ProductivityHacks #AlreadyHere #BusinessTips"""

    if tip.monetization and tip.monetization.get("type") == "tool_promo":
        caption += f"\n\n🔗 Link in bio: {tip.monetization.get('link', 'link.com')}"

    image_prompt = f"Create an Instagram-ready graphic for: {tip.title}. Style: minimalist, 1080x1350px, inspirational color palette, text overlay: '{tip.key_takeaway}'"

    return FormattedTip(
        tip_id=tip.id,
        channel="instagram",
        headline=tip.title,
        body=caption,
        cta="Tap to learn more",
        hashtags=["#TipOfTheDay", "#ProductivityHacks", "#AlreadyHere"],
        image_prompt=image_prompt,
    )


def format_tip_for_email(tip: Tip) -> FormattedTip:
    """Format tip as email snippet for newsletters."""
    subject = f"💡 {tip.title}"
    body = f"""<h3>{tip.curiosity_hook}</h3>
<p>{tip.content}</p>
<p><strong>Key Takeaway:</strong> {tip.key_takeaway}</p>
<p><em>Category: {tip.category.replace('_', ' ').title()} • ~{tip.reading_time_seconds}sec read</em></p>"""

    if tip.monetization and tip.monetization.get("type") == "tool_promo":
        body += f'<p><a href="{tip.monetization.get("link", "http://link.com")}">{tip.monetization.get("cta", "Try it now")}</a></p>'

    return FormattedTip(
        tip_id=tip.id,
        channel="email",
        headline=subject,
        body=body,
        cta="Forward to a friend",
        hashtags=[],
    )


def format_tip_for_blog(tip: Tip) -> FormattedTip:
    """Format tip as SEO-optimized blog section."""
    seo_slug = re.sub(r"[^\w\-]", "", tip.title.lower().replace(" ", "-"))
    body = f"""## {tip.title}

> {tip.curiosity_hook}

{tip.content}

**Key takeaway:** {tip.key_takeaway}

**Category:** {tip.category.replace('_', ' ').title()}
**Read time:** ~{tip.reading_time_seconds} seconds

**Related:** [From {pathlib.Path(tip.source_article).name}]({tip.source_article})
"""

    if tip.monetization and tip.monetization.get("type") == "tool_promo":
        body += f"\n\n[{tip.monetization.get('cta', 'Learn more')}]({tip.monetization.get('link', '#')})"

    return FormattedTip(
        tip_id=tip.id,
        channel="blog",
        headline=tip.title,
        body=body,
        cta="More daily tips →",
        hashtags=["productivity", "business-insights", "tips-and-tricks"],
    )


# ── Inject Monetization ────────────────────────────────────────────────────────

def inject_monetization_context(tip: Tip) -> Tip:
    """Add tool promotions or sponsor CTAs to a tip based on category and keywords."""
    if not MONETIZATION_ENABLED:
        return tip

    # Rule-based tool promotion
    keywords_to_tools = {
        "automation": "zapier",
        "productivity": "notion",
        "ai": "openai",
        "writing": "grammarly",
        "design": "figma",
        "video": "descript",
        "analytics": "mixpanel",
        "scheduling": "calendar",
    }

    for keyword, tool in keywords_to_tools.items():
        if keyword.lower() in (tip.title + " " + tip.content).lower():
            if tool in AFFILIATE_LINKS:
                tip.monetization = {
                    "type": "tool_promo",
                    "link": AFFILIATE_LINKS[tool],
                    "cta": f"Try {tool.title()} →",
                }
                break

    # Add Amazon Associates link if product-related
    if "product" in tip.content.lower() or "tool" in tip.content.lower():
        if not tip.monetization and AMAZON_TAG:
            tip.monetization = {
                "type": "amazon_associates",
                "link": f"https://amazon.com?tag={AMAZON_TAG}",
                "cta": "See recommendations on Amazon",
            }

    return tip


# ── Save Formatted Tips ────────────────────────────────────────────────────────

def save_formatted_tips(formatted_tips: List[FormattedTip]) -> None:
    """Save formatted tips to JSON files organized by channel."""
    TIPS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    by_channel = {}
    for formatted in formatted_tips:
        channel = formatted.channel
        if channel not in by_channel:
            by_channel[channel] = []
        by_channel[channel].append(asdict(formatted))

    for channel, tips in by_channel.items():
        output_file = TIPS_OUTPUT_DIR / f"{channel}_tips_{datetime.now().strftime('%Y%m%d')}.json"
        with open(output_file, "w") as f:
            json.dump(tips, f, indent=2)
        print(f"[SAVE] Saved {len(tips)} tips for {channel} → {output_file}")

    # Save all tips manifest
    manifest_file = TIPS_OUTPUT_DIR / "manifest.json"
    with open(manifest_file, "w") as f:
        json.dump(by_channel, f, indent=2)
    print(f"[SAVE] Manifest saved → {manifest_file}")


# ── Generate Ebook ────────────────────────────────────────────────────────────

def generate_ebook_chapters(all_tips: List[Tip]) -> Dict[str, Any]:
    """Organize tips into chapters for "101 Tips" ebook."""
    categories = {}
    for tip in all_tips:
        cat = tip.category
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(tip)

    chapters = []
    chapter_num = 1
    for category, tips in categories.items():
        chapter = {
            "number": chapter_num,
            "title": f"{category.replace('_', ' ').title()} Tips",
            "description": f"A collection of {len(tips)} practical tips about {category.replace('_', ' ').lower()}.",
            "tips": [asdict(t) for t in tips[:10]],  # Max 10 tips per chapter
        }
        chapters.append(chapter)
        chapter_num += 1

    ebook = {
        "title": "101 Tips for Productivity, Business, and AI Success",
        "subtitle": "Actionable insights from Already Here LLC",
        "chapters": chapters,
        "total_tips": len(all_tips),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "monetization": {
            "platform": "gumroad",
            "url": f"https://gumroad.com/l/101tips?affiliate={AMAZON_TAG}",
            "price": "$9.99",
            "description": "Get all 101 tips in a formatted guide you can reference anytime.",
        }
    }

    return ebook


def save_ebook_draft(ebook: Dict[str, Any]) -> None:
    """Save ebook draft as JSON + Markdown."""
    TIPS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # JSON version
    ebook_json = TIPS_OUTPUT_DIR / "ebook_draft.json"
    with open(ebook_json, "w") as f:
        json.dump(ebook, f, indent=2)
    print(f"[EBOOK] JSON draft saved → {ebook_json}")

    # Markdown version for Gumroad
    ebook_md = TIPS_OUTPUT_DIR / "ebook_draft.md"
    with open(ebook_md, "w") as f:
        f.write(f"# {ebook['title']}\n\n")
        f.write(f"*{ebook['subtitle']}*\n\n")
        f.write(f"**{ebook['total_tips']} actionable tips** organized into {len(ebook['chapters'])} chapters.\n\n")

        for chapter in ebook["chapters"]:
            f.write(f"## {chapter['title']}\n\n")
            f.write(f"{chapter['description']}\n\n")
            for i, tip in enumerate(chapter["tips"], 1):
                f.write(f"### Tip {i}: {tip['title']}\n\n")
                f.write(f"> {tip['curiosity_hook']}\n\n")
                f.write(f"{tip['content']}\n\n")
                f.write(f"**Key takeaway:** {tip['key_takeaway']}\n\n")

        f.write("---\n\n")
        f.write("**Purchase on Gumroad** to support Already Here LLC and get instant access.\n")

    print(f"[EBOOK] Markdown draft saved → {ebook_md}")


# ── Verify Credentials ─────────────────────────────────────────────────────────

def verify_credentials() -> bool:
    """Verify all configured credentials and APIs."""
    print("\n[VERIFY] Checking credentials...\n")

    checks = {
        "Groq API": GROQ_KEY,
        "GitHub Token": GH_TOKEN,
        "Twitter API": all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET]),
        "LinkedIn Token": LINKEDIN_TOKEN,
        "Instagram Token": INSTAGRAM_TOKEN,
        "Gumroad Token": GUMROAD_TOKEN,
    }

    all_ok = True
    for name, check in checks.items():
        status = "✓" if check else "✗"
        print(f"  {status} {name}")
        if not check:
            all_ok = False

    print()
    return all_ok


# ── Main Entrypoint ────────────────────────────────────────────────────────────

async def main() -> None:
    """Main workflow: fetch articles → extract tips → format → save → ebook."""
    parser = argparse.ArgumentParser(description="Tips Curator for ProfitEngine")
    parser.add_argument(
        "--extract",
        action="store_true",
        help="Extract tips from recent articles",
    )
    parser.add_argument(
        "--generate-daily",
        action="store_true",
        help="Generate tip of the day",
    )
    parser.add_argument(
        "--format",
        choices=["twitter", "linkedin", "instagram", "email", "blog", "all"],
        default="all",
        help="Format tips for specific channel(s)",
    )
    parser.add_argument(
        "--publish",
        choices=["twitter", "linkedin", "instagram", "email", "all", "none"],
        default="none",
        help="Publish formatted tips to platform(s)",
    )
    parser.add_argument(
        "--ebook",
        action="store_true",
        help="Generate ebook chapters",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Fetch articles from past N days (default: 7)",
    )

    args = parser.parse_args()

    # Verify credentials
    if not verify_credentials():
        print("[WARN] Some credentials missing; proceeding with available services")

    if VERIFY_ONLY:
        print("[VERIFY_ONLY MODE] Credentials verified. Exiting.")
        return

    all_tips: List[Tip] = []
    all_formatted: List[FormattedTip] = []

    # Extract tips from recent articles
    if args.extract or args.generate_daily:
        print("\n[EXTRACT] Fetching recent articles...")
        articles = await fetch_recent_articles(days=args.days)

        if articles:
            print(f"[EXTRACT] Processing {len(articles)} articles for tips...\n")
            for article in articles:
                title = article.get("filename", "Unknown").replace(".md", "").replace("-", " ").title()
                content = article.get("content", "")
                url = article.get("url", "")

                tips = await extract_tips_from_article(content, url, title, max_tips=5)
                all_tips.extend(tips)

            print(f"[EXTRACT] Total tips extracted: {len(all_tips)}\n")

            # Inject monetization
            all_tips = [inject_monetization_context(tip) for tip in all_tips]

    # Format tips for channels
    if args.format in ["twitter", "all"]:
        all_formatted.extend([format_tip_for_twitter(t) for t in all_tips])
    if args.format in ["linkedin", "all"]:
        all_formatted.extend([format_tip_for_linkedin(t) for t in all_tips])
    if args.format in ["instagram", "all"]:
        all_formatted.extend([format_tip_for_instagram(t) for t in all_tips])
    if args.format in ["email", "all"]:
        all_formatted.extend([format_tip_for_email(t) for t in all_tips])
    if args.format in ["blog", "all"]:
        all_formatted.extend([format_tip_for_blog(t) for t in all_tips])

    # Save formatted tips
    if all_formatted:
        print(f"\n[FORMAT] Formatted {len(all_formatted)} tips for distribution")
        save_formatted_tips(all_formatted)

    # Generate ebook
    if args.ebook and all_tips:
        print("\n[EBOOK] Generating ebook chapters...")
        ebook = generate_ebook_chapters(all_tips)
        save_ebook_draft(ebook)

    print("\n[DONE] Tips curation workflow complete!")
    print(f"  Total tips extracted: {len(all_tips)}")
    print(f"  Total formatted: {len(all_formatted)}")
    print(f"  Output directory: {TIPS_OUTPUT_DIR}")


if __name__ == "__main__":
    asyncio.run(main())
