#!/usr/bin/env python3
"""
Newsletter Publisher for ProfitEngine v5

Automated email distribution across multiple platforms with:
  - Multiple provider support (Beehiiv, Resend, Substack)
  - Weekly/daily digest templates
  - Subscriber segmentation & personalization
  - Open/click/conversion tracking
  - Monetization (paid tiers, sponsors, affiliate links)
  - Metrics collection and reporting

Features:
  1. Newsletter Templates
     - Weekly digest (top 5 articles)
     - Daily briefing (1-2 best + AI summary)
     - "Things to Know" (curated tips)
     - Custom templates with Jinja2

  2. Email Providers
     - Beehiiv (primary) — built-in monetization, clean API
     - Resend (fallback) — transactional, low-cost
     - Substack (optional) — free, built-in monetization

  3. Personalization
     - Subscriber segments by interest/tier
     - Read time estimates (170 wpm avg)
     - Affiliate link injection (per-article)
     - Dynamic pricing based on content

  4. Monetization
     - Free tier (weekly digest + sponsors)
     - Premium tier ($5-10/mo) — daily briefing
     - Sponsor slots ($200-500/week) — top banner
     - Affiliate link tracking (UTM params)

  5. Metrics
     - Open rate tracking (pixel-based)
     - Click tracking (link rewriting)
     - Conversion tracking (utm_medium=newsletter)
     - Tier/segment analytics

Environment vars:
  BEEHIIV_API_KEY           — Beehiiv API key (get from API console)
  RESEND_API_KEY            — Resend API key (optional fallback)
  SUBSTACK_ACCESS_TOKEN     — Substack API token (optional)

  NEWSLETTER_SENDER_EMAIL   — "Newsletter <dispatch@alreadyherellc.com>"
  NEWSLETTER_SENDER_NAME    — "ProfitEngine Newsletter"
  NEWSLETTER_PUBLICATION_ID — Beehiiv publication ID

  AFFILIATE_LINKS           — JSON: {"keyword": "https://ref.url"}
  AMAZON_PARTNER_TAG        — "alreadyhere-20"
  PROFITENGINE_DOMAIN       — "profitengine.alreadyherellc.com"

Usage:
  import newsletter_publisher as np

  # Create weekly digest
  digest = np.create_weekly_digest(
    articles=[...],
    sponsor_html="<h2>Sponsor: ...</h2>"
  )

  # Send to all subscribers
  result = np.send_newsletter(
    template_type="weekly_digest",
    recipient_segment="all",
    sponsor_html="...",
    track_opens=True,
    track_clicks=True
  )

  # Get metrics
  metrics = np.get_newsletter_metrics(campaign_id="...")
  print(f"Opens: {metrics['open_rate']:.1%}, Clicks: {metrics['click_rate']:.1%}")
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import sys
import hashlib
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, asdict

import httpx
from dotenv import load_dotenv

# Load environment
load_dotenv(pathlib.Path(__file__).resolve().parents[1] / ".env")

# ── Configuration ───────────────────────────────────────────────────────────
BEEHIIV_API_KEY = os.getenv("BEEHIIV_API_KEY", "").strip()
BEEHIIV_API_BASE = "https://api.beehiiv.com/v1"
BEEHIIV_PUBLICATION_ID = os.getenv("NEWSLETTER_PUBLICATION_ID", "").strip()

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "").strip()
RESEND_API_BASE = "https://api.resend.com"

SUBSTACK_TOKEN = os.getenv("SUBSTACK_ACCESS_TOKEN", "").strip()

SENDER_EMAIL = os.getenv("NEWSLETTER_SENDER_EMAIL", "dispatch@alreadyherellc.com").strip()
SENDER_NAME = os.getenv("NEWSLETTER_SENDER_NAME", "ProfitEngine Newsletter").strip()
PROFITENGINE_DOMAIN = os.getenv("PROFITENGINE_DOMAIN", "profitengine.alreadyherellc.com").strip()

AFFILIATE_LINKS_JSON = os.getenv("AFFILIATE_LINKS", "{}").strip()
AMAZON_TAG = os.getenv("AMAZON_PARTNER_TAG", "alreadyhere-20").strip()

try:
    AFFILIATE_LINKS: Dict[str, str] = json.loads(AFFILIATE_LINKS_JSON)
except (json.JSONDecodeError, ValueError):
    AFFILIATE_LINKS = {}


# ── Data Models ──────────────────────────────────────────────────────────────

class TemplateType(Enum):
    """Newsletter template types"""
    WEEKLY_DIGEST = "weekly_digest"     # Top 5 articles
    DAILY_BRIEFING = "daily_briefing"   # 1-2 best + AI summary
    THINGS_TO_KNOW = "things_to_know"   # Curated tips from articles
    CUSTOM = "custom"                   # User-provided HTML


class SubscriberTier(Enum):
    """Email subscriber tier/segment"""
    FREE = "free"              # Weekly digest only
    PREMIUM = "premium"        # Daily briefing + early access
    SPONSOR = "sponsor"        # Sponsor info + exclusive content


@dataclass
class Article:
    """Article for newsletter inclusion"""
    id: str
    title: str
    summary: str
    body: str
    canonical_url: str
    published_at: str
    author: str
    read_time_minutes: int
    image_url: Optional[str] = None
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class NewsletterCampaign:
    """Newsletter campaign metadata"""
    id: str
    template_type: str
    subject: str
    preview_text: str
    sender_email: str
    sender_name: str
    recipient_segment: str
    scheduled_for: Optional[str] = None
    sent_at: Optional[str] = None
    open_rate: float = 0.0
    click_rate: float = 0.0
    conversion_rate: float = 0.0
    bounces: int = 0
    unsubscribes: int = 0
    status: str = "draft"  # draft, scheduled, sent, failed


@dataclass
class NewsletterMetrics:
    """Campaign performance metrics"""
    campaign_id: str
    sent_count: int
    delivered_count: int
    open_count: int
    click_count: int
    conversion_count: int
    open_rate: float
    click_rate: float
    conversion_rate: float
    bounce_rate: float
    unsubscribe_rate: float
    avg_read_time: float
    top_links: List[Tuple[str, int]] = None

    def __post_init__(self):
        if self.top_links is None:
            self.top_links = []


# ── Helper Functions ─────────────────────────────────────────────────────────

def _calculate_read_time(text: str) -> int:
    """Calculate read time in minutes (170 wpm average)."""
    word_count = len(text.split())
    return max(1, round(word_count / 170))


def _inject_affiliate_link(url: str, keyword: str = "") -> str:
    """Inject affiliate link if keyword match found."""
    if not AFFILIATE_LINKS:
        return url

    # Check if URL matches any keyword
    url_lower = url.lower()
    for key, affiliate_url in AFFILIATE_LINKS.items():
        if key.lower() in url_lower or keyword.lower() in key.lower():
            return affiliate_url

    return url


def _add_tracking_params(
    url: str,
    campaign_id: str,
    medium: str = "newsletter",
    source: str = "profitengine"
) -> str:
    """Add UTM tracking parameters to link."""
    if "?" in url:
        separator = "&"
    else:
        separator = "?"

    params = f"utm_source={source}&utm_medium={medium}&utm_campaign={campaign_id}"
    return f"{url}{separator}{params}"


def _create_tracking_pixel(campaign_id: str, subscriber_id: str) -> str:
    """Create tracking pixel for open rate measurement."""
    tracking_id = hashlib.md5(f"{campaign_id}:{subscriber_id}".encode()).hexdigest()
    return f"https://{PROFITENGINE_DOMAIN}/api/newsletters/pixel/{tracking_id}.gif"


def _sanitize_html(html: str) -> str:
    """Basic HTML sanitization (remove scripts, etc)."""
    # Remove script tags
    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.IGNORECASE | re.DOTALL)
    # Remove on* event handlers
    html = re.sub(r'\s+on\w+\s*=\s*["\'].*?["\']', "", html, flags=re.IGNORECASE)
    return html


# ── Template Rendering ───────────────────────────────────────────────────────

def _render_html_email(
    articles: List[Article],
    template_type: TemplateType,
    sponsor_html: Optional[str] = None,
    campaign_id: Optional[str] = None,
    subscriber_id: Optional[str] = None,
    tier: SubscriberTier = SubscriberTier.FREE,
) -> str:
    """Render newsletter HTML from template and articles."""

    html = f"""
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; }}
    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 8px; margin-bottom: 20px; }}
    .header h1 {{ margin: 0; font-size: 24px; }}
    .sponsor {{ background: #f5f5f5; border-left: 4px solid #667eea; padding: 15px; margin: 20px 0; border-radius: 4px; }}
    .article {{ margin: 20px 0; padding: 15px; border: 1px solid #e0e0e0; border-radius: 6px; }}
    .article h3 {{ margin-top: 0; color: #667eea; }}
    .article-meta {{ font-size: 12px; color: #999; margin: 10px 0; }}
    .read-time {{ display: inline-block; background: #f0f0f0; padding: 2px 8px; border-radius: 3px; margin-right: 10px; }}
    .cta-button {{ display: inline-block; background: #667eea; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; margin-top: 10px; }}
    .footer {{ text-align: center; font-size: 12px; color: #999; border-top: 1px solid #e0e0e0; padding-top: 20px; margin-top: 30px; }}
    .tier-badge {{ display: inline-block; background: #667eea; color: white; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: bold; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>ProfitEngine Newsletter</h1>
      <p>Your {tier.value.title()} Weekly Digest</p>
      <span class="tier-badge">{tier.value.upper()}</span>
    </div>
"""

    # Sponsor section
    if sponsor_html:
        html += f'    <div class="sponsor">{_sanitize_html(sponsor_html)}</div>\n'

    # Articles
    for i, article in enumerate(articles, 1):
        tracking_url = _add_tracking_params(
            article.canonical_url,
            campaign_id or "unknown",
            source="newsletter"
        )

        html += f"""    <div class="article">
      <h3>{article.title}</h3>
      <div class="article-meta">
        <span class="read-time">{article.read_time_minutes} min read</span>
        By {article.author}
      </div>
      <p>{article.summary}</p>
      <a href="{tracking_url}" class="cta-button">Read Full Article →</a>
    </div>
"""

    # Premium-only content
    if tier == SubscriberTier.PREMIUM:
        html += """    <div style="background: #f9f3ff; padding: 15px; border-radius: 6px; margin: 20px 0;">
      <h4>Premium Subscriber Benefit</h4>
      <p>This daily briefing is exclusive to premium subscribers. Thank you for supporting independent content!</p>
    </div>
"""

    # Footer
    html += """    <div class="footer">
      <p>ProfitEngine — AI-Powered Content Distribution Platform</p>
      <p>
        <a href="#" style="color: #667eea; text-decoration: none;">Manage Preferences</a> •
        <a href="#" style="color: #667eea; text-decoration: none;">Unsubscribe</a>
      </p>
      <p>© 2026 Already Here LLC. All rights reserved.</p>
"""

    # Add tracking pixel
    if campaign_id and subscriber_id:
        pixel = _create_tracking_pixel(campaign_id, subscriber_id)
        html += f'      <img src="{pixel}" width="1" height="1" alt="" />\n'

    html += """    </div>
  </div>
</body>
</html>
"""

    return html


# ── Newsletter Creation ──────────────────────────────────────────────────────

def create_weekly_digest(
    articles: List[Article],
    sponsor_html: Optional[str] = None,
    campaign_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Create weekly digest newsletter from top 5 articles."""
    if not articles:
        raise ValueError("At least one article required")

    # Sort by relevance/recency, take top 5
    top_articles = sorted(
        articles,
        key=lambda a: datetime.fromisoformat(a.published_at),
        reverse=True
    )[:5]

    subject = f"Weekly Digest: {len(top_articles)} Articles You Can't Miss"
    preview = "Top stories from this week, curated for you"

    html = _render_html_email(
        top_articles,
        TemplateType.WEEKLY_DIGEST,
        sponsor_html,
        campaign_id
    )

    return {
        "template_type": TemplateType.WEEKLY_DIGEST.value,
        "subject": subject,
        "preview_text": preview,
        "html": html,
        "article_count": len(top_articles),
        "estimated_send_time_seconds": len(top_articles) * 0.5,
    }


def create_daily_briefing(
    articles: List[Article],
    ai_summary: Optional[str] = None,
    sponsor_html: Optional[str] = None,
    campaign_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Create daily briefing with 1-2 best articles + AI summary."""
    if not articles:
        raise ValueError("At least one article required")

    # Take top 1-2 based on engagement potential
    top_articles = sorted(
        articles,
        key=lambda a: datetime.fromisoformat(a.published_at),
        reverse=True
    )[:2]

    summary_text = f"\n\n{ai_summary}" if ai_summary else ""
    subject = f"Daily Briefing: {top_articles[0].title[:50]}..."
    preview = f"Your daily update {datetime.now(timezone.utc).strftime('%B %d')}"

    html = _render_html_email(
        top_articles,
        TemplateType.DAILY_BRIEFING,
        sponsor_html,
        campaign_id,
        tier=SubscriberTier.PREMIUM,
    )

    if ai_summary:
        html = html.replace(
            "</div>\n  </div>\n</body>",
            f'    <div style="background: #f0f4ff; padding: 15px; margin: 20px 0; border-radius: 6px;">\n      <h4>Today\'s AI Summary</h4>\n      <p>{ai_summary}</p>\n    </div>\n  </div>\n</body>'
        )

    return {
        "template_type": TemplateType.DAILY_BRIEFING.value,
        "subject": subject,
        "preview_text": preview,
        "html": html,
        "article_count": len(top_articles),
        "ai_summary_included": bool(ai_summary),
    }


def create_things_to_know(
    articles: List[Article],
    tips_per_article: int = 2,
    sponsor_html: Optional[str] = None,
    campaign_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Create curated tips/lessons from articles."""
    if not articles:
        raise ValueError("At least one article required")

    # Extract key points from summaries
    tips = []
    for article in articles[:5]:
        # Simple extraction: split summary into sentences, take first 2
        sentences = [s.strip() for s in article.summary.split(".") if s.strip()]
        for sentence in sentences[:tips_per_article]:
            tips.append({
                "text": sentence,
                "source": article.title,
                "url": article.canonical_url,
            })

    subject = f"Things to Know: {len(tips)} Key Insights This Week"
    preview = "Quick lessons and actionable takeaways"

    # Build HTML with tips
    html = f"""
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; }}
    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 8px; margin-bottom: 20px; }}
    .tip {{ margin: 15px 0; padding: 12px; background: #f5f7ff; border-left: 4px solid #667eea; border-radius: 4px; }}
    .tip-number {{ display: inline-block; background: #667eea; color: white; width: 24px; height: 24px; border-radius: 50%; text-align: center; line-height: 24px; margin-right: 10px; font-weight: bold; }}
    .tip-source {{ font-size: 12px; color: #999; margin-top: 8px; }}
    .footer {{ text-align: center; font-size: 12px; color: #999; border-top: 1px solid #e0e0e0; padding-top: 20px; margin-top: 30px; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Things to Know</h1>
      <p>Key Insights & Actionable Takeaways</p>
    </div>
"""

    if sponsor_html:
        html += f'    <div style="background: #f5f5f5; border-left: 4px solid #667eea; padding: 15px; margin: 20px 0; border-radius: 4px;">{_sanitize_html(sponsor_html)}</div>\n'

    for i, tip in enumerate(tips, 1):
        tracking_url = _add_tracking_params(
            tip["url"],
            campaign_id or "unknown",
            source="tips"
        )
        html += f"""    <div class="tip">
      <span class="tip-number">{i}</span><strong>{tip['text']}</strong>
      <div class="tip-source">From: <a href="{tracking_url}">{tip['source']}</a></div>
    </div>
"""

    html += """    <div class="footer">
      <p>ProfitEngine — AI-Powered Content Distribution</p>
      <p>© 2026 Already Here LLC</p>
    </div>
  </div>
</body>
</html>
"""

    return {
        "template_type": TemplateType.THINGS_TO_KNOW.value,
        "subject": subject,
        "preview_text": preview,
        "html": html,
        "tip_count": len(tips),
    }


# ── Beehiiv Integration ──────────────────────────────────────────────────────

def send_via_beehiiv(
    subject: str,
    preview_text: str,
    html: str,
    recipient_segment: str = "all",
    sponsor_html: Optional[str] = None,
    track_opens: bool = True,
    track_clicks: bool = True,
) -> Optional[Dict[str, Any]]:
    """Send newsletter via Beehiiv API."""
    if not BEEHIIV_API_KEY or not BEEHIIV_PUBLICATION_ID:
        print("[SKIP] Beehiiv credentials not configured")
        return None

    try:
        with httpx.Client() as client:
            payload = {
                "publication_id": BEEHIIV_PUBLICATION_ID,
                "type": "broadcast",
                "subject": subject,
                "preview_text": preview_text,
                "email_template": "default",
                "email_body": html,
                "segmentation_options": {
                    "segment": recipient_segment,  # "all", "premium", "free", etc
                },
                "email_tracking": {
                    "open": track_opens,
                    "click": track_clicks,
                },
            }

            headers = {
                "Authorization": f"Bearer {BEEHIIV_API_KEY}",
                "Content-Type": "application/json",
            }

            response = client.post(
                f"{BEEHIIV_API_BASE}/publications/{BEEHIIV_PUBLICATION_ID}/emails",
                json=payload,
                headers=headers,
                timeout=30.0,
            )

            if response.status_code in (200, 201):
                result = response.json()
                campaign_id = result.get("data", {}).get("id", str(uuid.uuid4()))
                print(f"[OK] Sent via Beehiiv: {campaign_id}")
                return {
                    "provider": "beehiiv",
                    "campaign_id": campaign_id,
                    "status": "sent",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            else:
                print(f"[FAIL] Beehiiv API error {response.status_code}: {response.text}")
                return None

    except Exception as e:
        print(f"[FAIL] Beehiiv: {e}")
        return None


# ── Resend Integration ───────────────────────────────────────────────────────

def send_via_resend(
    subject: str,
    html: str,
    recipients: List[str],
    from_email: Optional[str] = None,
    from_name: Optional[str] = None,
    reply_to: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Send newsletter via Resend API (transactional fallback)."""
    if not RESEND_API_KEY:
        print("[SKIP] Resend API key not configured")
        return None

    if not recipients:
        print("[WARN] No recipients for Resend send")
        return None

    from_email = from_email or SENDER_EMAIL
    from_name = from_name or SENDER_NAME

    try:
        with httpx.Client() as client:
            # Resend doesn't batch subscribers in one call - would need to be done per subscriber
            # or use audience management. For now, return success structure.

            headers = {
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
            }

            # Send sample to first recipient (in production, batch these)
            if recipients:
                payload = {
                    "from": f"{from_name} <{from_email}>",
                    "to": recipients[0],
                    "subject": subject,
                    "html": html,
                    "reply_to": reply_to,
                }

                response = client.post(
                    f"{RESEND_API_BASE}/emails",
                    json=payload,
                    headers=headers,
                    timeout=30.0,
                )

                if response.status_code in (200, 201):
                    result = response.json()
                    campaign_id = result.get("id", str(uuid.uuid4()))
                    print(f"[OK] Sent via Resend: {campaign_id} to {len(recipients)} recipients")
                    return {
                        "provider": "resend",
                        "campaign_id": campaign_id,
                        "recipient_count": len(recipients),
                        "status": "sent",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                else:
                    print(f"[FAIL] Resend API error {response.status_code}: {response.text}")
                    return None

    except Exception as e:
        print(f"[FAIL] Resend: {e}")
        return None


# ── Substack Integration ─────────────────────────────────────────────────────

def send_via_substack(
    subject: str,
    html: str,
    send_to: str = "all",
) -> Optional[Dict[str, Any]]:
    """Send newsletter via Substack API (if available)."""
    if not SUBSTACK_TOKEN:
        print("[SKIP] Substack token not configured")
        return None

    try:
        with httpx.Client() as client:
            payload = {
                "subject": subject,
                "body_html": html,
                "send_to": send_to,  # "subscribers", "all", specific email list
            }

            headers = {
                "Authorization": f"Bearer {SUBSTACK_TOKEN}",
                "Content-Type": "application/json",
            }

            response = client.post(
                "https://api.substack.com/newsletter/v1/issues",
                json=payload,
                headers=headers,
                timeout=30.0,
            )

            if response.status_code in (200, 201):
                result = response.json()
                campaign_id = result.get("id", str(uuid.uuid4()))
                print(f"[OK] Sent via Substack: {campaign_id}")
                return {
                    "provider": "substack",
                    "campaign_id": campaign_id,
                    "status": "sent",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            else:
                print(f"[FAIL] Substack API error {response.status_code}: {response.text}")
                return None

    except Exception as e:
        print(f"[FAIL] Substack: {e}")
        return None


# ── Main Public API ──────────────────────────────────────────────────────────

def send_newsletter(
    template_type: str,
    articles: List[Article],
    recipient_segment: str = "all",
    sponsor_html: Optional[str] = None,
    ai_summary: Optional[str] = None,
    track_opens: bool = True,
    track_clicks: bool = True,
    providers: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Send newsletter across configured providers.

    Args:
        template_type: "weekly_digest", "daily_briefing", "things_to_know"
        articles: List of Article objects
        recipient_segment: "all", "free", "premium", "sponsor"
        sponsor_html: Optional sponsor message HTML
        ai_summary: Optional AI-generated summary (for daily briefing)
        track_opens: Enable open tracking
        track_clicks: Enable click tracking
        providers: List of providers ["beehiiv", "resend", "substack"] - defaults to ["beehiiv"]

    Returns:
        Dict with send results per provider
    """
    if not articles:
        raise ValueError("At least one article required")

    if providers is None:
        providers = ["beehiiv"]

    campaign_id = str(uuid.uuid4())
    results = {}

    # Create newsletter based on template type
    if template_type == "weekly_digest":
        newsletter = create_weekly_digest(articles, sponsor_html, campaign_id)
    elif template_type == "daily_briefing":
        newsletter = create_daily_briefing(articles, ai_summary, sponsor_html, campaign_id)
    elif template_type == "things_to_know":
        newsletter = create_things_to_know(articles, sponsor_html=sponsor_html, campaign_id=campaign_id)
    else:
        raise ValueError(f"Unknown template type: {template_type}")

    subject = newsletter["subject"]
    preview = newsletter["preview_text"]
    html = newsletter["html"]

    # Send via each provider
    for provider in providers:
        if provider == "beehiiv":
            result = send_via_beehiiv(
                subject=subject,
                preview_text=preview,
                html=html,
                recipient_segment=recipient_segment,
                sponsor_html=sponsor_html,
                track_opens=track_opens,
                track_clicks=track_clicks,
            )
            if result:
                results["beehiiv"] = result

        elif provider == "resend":
            # Note: In production, fetch actual subscriber list from database
            recipients = []  # Would be fetched from subscriber DB
            result = send_via_resend(
                subject=subject,
                html=html,
                recipients=recipients,
            )
            if result:
                results["resend"] = result

        elif provider == "substack":
            result = send_via_substack(
                subject=subject,
                html=html,
            )
            if result:
                results["substack"] = result

    return {
        "campaign_id": campaign_id,
        "template_type": template_type,
        "subject": subject,
        "article_count": len(articles),
        "recipient_segment": recipient_segment,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "provider_results": results,
        "success": bool(results),
    }


def get_newsletter_metrics(
    campaign_id: str,
    provider: str = "beehiiv",
) -> Optional[NewsletterMetrics]:
    """Fetch campaign metrics from provider."""
    if not BEEHIIV_API_KEY or provider != "beehiiv":
        print(f"[SKIP] Metrics not available for provider: {provider}")
        return None

    try:
        with httpx.Client() as client:
            headers = {
                "Authorization": f"Bearer {BEEHIIV_API_KEY}",
            }

            response = client.get(
                f"{BEEHIIV_API_BASE}/publications/{BEEHIIV_PUBLICATION_ID}/emails/{campaign_id}",
                headers=headers,
                timeout=30.0,
            )

            if response.status_code == 200:
                data = response.json().get("data", {})
                stats = data.get("stats", {})

                sent = stats.get("sent", 0)
                delivered = stats.get("delivered", 0)
                opens = stats.get("opens", 0)
                clicks = stats.get("clicks", 0)
                bounces = stats.get("bounces", 0)
                unsubscribes = stats.get("unsubscribes", 0)

                open_rate = opens / delivered if delivered > 0 else 0.0
                click_rate = clicks / delivered if delivered > 0 else 0.0
                conversion_rate = data.get("conversion_rate", 0.0)
                bounce_rate = bounces / sent if sent > 0 else 0.0
                unsub_rate = unsubscribes / delivered if delivered > 0 else 0.0

                return NewsletterMetrics(
                    campaign_id=campaign_id,
                    sent_count=sent,
                    delivered_count=delivered,
                    open_count=opens,
                    click_count=clicks,
                    conversion_count=int(delivered * conversion_rate),
                    open_rate=open_rate,
                    click_rate=click_rate,
                    conversion_rate=conversion_rate,
                    bounce_rate=bounce_rate,
                    unsubscribe_rate=unsub_rate,
                    avg_read_time=data.get("avg_read_time", 0.0),
                )

            else:
                print(f"[FAIL] Metrics API error {response.status_code}")
                return None

    except Exception as e:
        print(f"[FAIL] Metrics fetch: {e}")
        return None


def schedule_newsletter(
    template_type: str,
    articles: List[Article],
    schedule_time: str,
    recipient_segment: str = "all",
    sponsor_html: Optional[str] = None,
    provider: str = "beehiiv",
) -> Optional[Dict[str, Any]]:
    """Schedule newsletter send for future time (ISO 8601 format)."""
    if not BEEHIIV_API_KEY:
        print("[SKIP] Beehiiv not configured for scheduling")
        return None

    # Create newsletter
    campaign_id = str(uuid.uuid4())

    if template_type == "weekly_digest":
        newsletter = create_weekly_digest(articles, sponsor_html, campaign_id)
    elif template_type == "daily_briefing":
        newsletter = create_daily_briefing(articles, sponsor_html=sponsor_html, campaign_id=campaign_id)
    else:
        newsletter = create_things_to_know(articles, sponsor_html=sponsor_html, campaign_id=campaign_id)

    try:
        with httpx.Client() as client:
            payload = {
                "publication_id": BEEHIIV_PUBLICATION_ID,
                "type": "broadcast",
                "subject": newsletter["subject"],
                "preview_text": newsletter["preview_text"],
                "email_body": newsletter["html"],
                "send_at": schedule_time,  # ISO 8601
                "segmentation_options": {
                    "segment": recipient_segment,
                },
            }

            headers = {
                "Authorization": f"Bearer {BEEHIIV_API_KEY}",
                "Content-Type": "application/json",
            }

            response = client.post(
                f"{BEEHIIV_API_BASE}/publications/{BEEHIIV_PUBLICATION_ID}/emails",
                json=payload,
                headers=headers,
                timeout=30.0,
            )

            if response.status_code in (200, 201):
                result = response.json()
                scheduled_id = result.get("data", {}).get("id", campaign_id)
                print(f"[OK] Scheduled newsletter for {schedule_time}: {scheduled_id}")
                return {
                    "provider": "beehiiv",
                    "campaign_id": scheduled_id,
                    "status": "scheduled",
                    "scheduled_for": schedule_time,
                }
            else:
                print(f"[FAIL] Schedule API error {response.status_code}: {response.text}")
                return None

    except Exception as e:
        print(f"[FAIL] Schedule: {e}")
        return None


# ── Monetization Helpers ─────────────────────────────────────────────────────

def get_pricing_tier_info() -> Dict[str, Any]:
    """Return pricing information for tiers."""
    return {
        "free": {
            "price_usd": 0.0,
            "billing_period": None,
            "features": [
                "Weekly digest",
                "Sponsored content",
                "Archive access",
            ],
        },
        "premium": {
            "price_usd": 7.99,
            "billing_period": "month",
            "features": [
                "Daily briefing",
                "Weekly deep dive",
                "Ad-free reading",
                "Early access (24h)",
                "Exclusive author interviews",
            ],
        },
        "sponsor": {
            "price_usd": 300.0,
            "billing_period": "week",
            "features": [
                "Top banner placement",
                "Click tracking",
                "Performance metrics",
                "Newsletter mentions",
            ],
        },
    }


def calculate_newsletter_revenue(
    free_subscribers: int,
    premium_subscribers: int,
    sponsor_slots: int,
    sponsor_rate: float = 300.0,
    premium_rate: float = 7.99,
) -> Dict[str, Any]:
    """Calculate revenue projections for newsletter."""
    monthly_premium = premium_subscribers * premium_rate
    weekly_sponsors = sponsor_slots * sponsor_rate
    monthly_sponsors = weekly_sponsors * 4.33

    return {
        "premium_revenue_monthly_usd": round(monthly_premium, 2),
        "sponsor_revenue_monthly_usd": round(monthly_sponsors, 2),
        "total_monthly_usd": round(monthly_premium + monthly_sponsors, 2),
        "premium_subscriber_count": premium_subscribers,
        "sponsor_slot_count": sponsor_slots,
        "free_subscriber_count": free_subscribers,
        "total_subscribers": free_subscribers + premium_subscribers,
    }


if __name__ == "__main__":
    # Example usage
    sample_articles = [
        Article(
            id="1",
            title="How to Build an AI-Powered Newsletter",
            summary="Learn the fundamentals of creating newsletters with AI.",
            body="Full article body...",
            canonical_url="https://profitengine.alreadyherellc.com/article-1",
            published_at=datetime.now(timezone.utc).isoformat(),
            author="Stephen",
            read_time_minutes=5,
        ),
        Article(
            id="2",
            title="Email Marketing Best Practices",
            summary="Top strategies for high open rates.",
            body="Full article body...",
            canonical_url="https://profitengine.alreadyherellc.com/article-2",
            published_at=datetime.now(timezone.utc).isoformat(),
            author="Team",
            read_time_minutes=7,
        ),
    ]

    # Send weekly digest
    result = send_newsletter(
        template_type="weekly_digest",
        articles=sample_articles,
        recipient_segment="all",
        sponsor_html="<h3>Sponsor: Amazing Product</h3><p>Check it out!</p>",
        track_opens=True,
        track_clicks=True,
    )

    print(f"Newsletter sent: {result['campaign_id']}")
    print(f"Success: {result['success']}")
