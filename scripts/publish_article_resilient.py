#!/usr/bin/env python3
"""
Resilient ProfitEngine article publisher.

Purpose:
- Preserve the existing scripts/publish_article.py implementation.
- Add a deterministic article fallback when all LLM providers fail.
- Make GitHub Pages publication mandatory instead of silently passing after failure.
- Keep verify-only mode aligned with the current provider chain: Groq (free) -> HuggingFace -> Gemini.
- Optimize affiliate output so posts monetize without becoming link catalogs.
- Attach a revenue execution brief so each article becomes a business action trigger.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import httpx

import publish_article as publisher

# Gracefully import distribution modules with fallback handling
try:
    from social_media_publishers import publish_to_all_platforms
except (ImportError, AttributeError) as e:
    print(f"[WARN] social_media_publishers import failed: {e}")
    publish_to_all_platforms = None  # type: ignore[assignment]

try:
    from ecommerce_publishers import publish_to_all_ecommerce
except (ImportError, AttributeError) as e:
    print(f"[WARN] ecommerce_publishers import failed: {e}")
    publish_to_all_ecommerce = None  # type: ignore[assignment]

try:
    from priority_publishers import publish_to_priority_platforms, generate_priority_report
except (ImportError, AttributeError) as e:
    print(f"[WARN] priority_publishers import failed: {e}")
    publish_to_priority_platforms = None  # type: ignore[assignment]
    generate_priority_report = None  # type: ignore[assignment]

_ORIGINAL_VERIFY_AI_PROVIDER: Callable[[], bool] = publisher._verify_ai_provider  # type: ignore[attr-defined]
_ORIGINAL_AFFILIATE_MAP: Callable[[], Dict[str, str]] = publisher._affiliate_map  # type: ignore[attr-defined]

AFFILIATE_PROMPT_LIMIT = max(1, int(os.getenv("AFFILIATE_PROMPT_LIMIT", "12")))
AFFILIATE_TOOL_LIMIT = max(1, min(8, int(os.getenv("AFFILIATE_TOOL_LIMIT", "8"))))
AFFILIATE_FEATURED_LIMIT = max(1, min(3, int(os.getenv("AFFILIATE_FEATURED_LIMIT", "3"))))
AFFILIATE_UTM_CAMPAIGN = os.getenv("AFFILIATE_UTM_CAMPAIGN", "profitengine_content")
AFFILIATE_DISCLOSURE = os.getenv(
    "AFFILIATE_DISCLOSURE",
    "Some links below are affiliate or referral links. Already Here LLC may earn a commission or referral credit at no extra cost to you.",
).strip()
ACTION_BRIEF_ENABLED = os.getenv("CONTENT_ACTION_BRIEF_ENABLED", "true").strip().lower() not in {"0", "false", "no", "off"}

# Gumroad & Printify configuration
GUMROAD_API_KEY = os.getenv("GUMROAD_API_KEY", "").strip()
GUMROAD_ENABLED = os.getenv("GUMROAD_ENABLED", "true").strip().lower() not in {"0", "false", "no", "off"} and bool(GUMROAD_API_KEY)
PRINTIFY_API_KEY = os.getenv("PRINTIFY_API_KEY", "").strip()
PRINTIFY_ENABLED = os.getenv("PRINTIFY_ENABLED", "true").strip().lower() not in {"0", "false", "no", "off"} and bool(PRINTIFY_API_KEY)
EBOOK_WORD_LIMIT = max(500, int(os.getenv("EBOOK_WORD_LIMIT", "1000")))
GUMROAD_BASE_PRICE = float(os.getenv("GUMROAD_BASE_PRICE", "4.99"))
GUMROAD_AMAZON_TAG = os.getenv("GUMROAD_AMAZON_TAG", "alreadyhere-20")


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9-]", "", text.lower().replace(" ", "-"))
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:60] or "profitengine-content-update"


def _title_from_topic(topic: str) -> str:
    cleaned = re.sub(r"\s+", " ", topic).strip(" .:-")
    if not cleaned:
        cleaned = "AI Automation Systems for Small Business Revenue"
    return cleaned[:1].upper() + cleaned[1:]


def _deterministic_article(topic: str) -> Dict[str, Any]:
    """Create a publishable operational article without external LLM access."""
    title = _title_from_topic(topic)
    slug = _slugify(title)
    meta = (
        f"A practical operator guide to {title.lower()} with workflow steps, risk controls, "
        "and a revenue-first implementation path."
    )[:158]

    body = f"""## Why {title} Matters Now

Small businesses do not need more disconnected tools. They need practical systems that reduce missed opportunities, improve response time, and turn existing demand into booked work. {title} is useful when it is treated as an operating workflow, not as a novelty project.

A profitable automation system starts with a clear business outcome. The target should be specific: capture missed calls, qualify leads, prepare quotes, book appointments, publish useful content, recover abandoned prospects, or document service work. If the workflow cannot connect to revenue, time saved, or risk reduced, it should not be the first build.

## Start With the Revenue Event

The first step is to define the revenue event. For a local service business, that may be a scheduled appointment, a paid invoice, a signed estimate, or a confirmed dispatch. For a digital product business, it may be an email signup, checkout, affiliate click, or product sale. The automation should be designed backward from that event.

This keeps the build focused. Instead of asking what an AI tool can do, ask what stops the customer from buying. Common blockers include slow replies, weak follow-up, unclear pricing, missing proof, no payment link, or no simple booking path. The automation should remove one blocker at a time.

## Build the Minimum Working System

A minimum working system needs five parts. First, a capture point such as a form, phone intake, chatbot, landing page, or content call to action. Second, a qualification step that collects the customer need, location, urgency, budget, and contact details. Third, a response path that gives the customer a useful next step. Fourth, a tracking layer that records where the lead came from. Fifth, a review process that shows whether the work produced revenue.

This is enough to start. A business does not need a complex dashboard on day one. It needs a workflow that can be tested against real buyers. Once the basic path works, the system can be expanded with automatic reminders, quote templates, service packages, payment links, and content distribution.

## Protect Margin Before Scaling

Automation can create more activity without creating more profit. That is a failure mode. Every workflow should include margin rules. For service work, define the minimum dispatch value, travel limit, two-hour minimum, cancellation rule, and paid return-trip rule. For products, define platform fees, fulfillment cost, refund exposure, and expected net profit.

The system should reject or flag low-margin work before it consumes time. This is especially important for field service, hauling, delivery, and consumer support work, where unpaid travel and vague scope can turn a busy day into a weak day. The best automation is not the one that accepts everything. It is the one that routes attention toward the work worth doing.

## Use Content as Proof, Not Noise

Content should support the sales path. A useful article, post, video, or checklist should answer a buyer question and point to the next action. Good content shows competence before a sales call. It can explain the problem, show the process, define the offer, reduce risk, and make the buyer more comfortable taking action.

For a small IT or automation company, strong content topics include missed-call recovery, AI receptionist setup, service dispatch workflows, payment-link setup, field technician closeout, local SEO pages, and practical automation checklists. These topics are not just traffic plays. They can become reusable sales assets.

## Add Human Approval at the Right Points

Not every step should be automatic. Pricing changes, client commitments, credential changes, public publishing, and money movement should remain approval-gated. The system can prepare the draft, score the opportunity, calculate margin, and recommend the next action. The operator should approve anything that creates liability or commits the business.

This approach keeps speed without losing control. It also improves trust. A business owner is more likely to adopt automation when the system clearly separates safe automatic actions from actions that need review.

## Practical Implementation Path

Start with one offer and one channel. For example, use a landing page for an AI missed-call receptionist offer, a simple intake form, a lead tracker, a payment link, and three follow-up templates. Track every lead source and every paid conversion. After the first sale, improve the workflow. After the third sale, package the process. After the tenth sale, turn it into a repeatable operating system.

The goal is not to look automated. The goal is to become easier to buy from, faster to respond, better documented, and more profitable per hour. When the system proves that it can create revenue, it becomes an asset instead of an experiment.

## Next Step

Choose one revenue event and build the shortest reliable path to it. Capture the lead, qualify the need, respond quickly, track the result, and keep improving the workflow from real outcomes. That is how {title.lower()} becomes a practical profit system instead of another unfinished tool stack.
"""

    return {
        "title": title,
        "slug": slug,
        "meta_description": meta,
        "tags": ["ai", "automation", "revenue", "smallbusiness"],
        "body": body.strip(),
    }


def _action_brief_type(title: str, tags: List[str]) -> str:
    haystack = " ".join([title, *tags]).lower()
    if any(term in haystack for term in ("dropshipping", "ecommerce", "shopify", "print-on-demand", "etsy")):
        return "commerce"
    if any(term in haystack for term in ("hosting", "vps", "cloud", "website", "deployment")):
        return "infrastructure"
    if any(term in haystack for term in ("affiliate", "seo", "content", "blog")):
        return "content"
    if any(term in haystack for term in ("receptionist", "missed-call", "lead", "small business")):
        return "service-automation"
    return "automation"


def _revenue_action_brief(topic: str, article: Dict[str, Any]) -> str:
    title = str(article.get("title") or topic or "Revenue action")
    tags = [str(t) for t in article.get("tags", []) if str(t).strip()]
    kind = _action_brief_type(title, tags)

    offers = {
        "commerce": "AI-assisted product research, storefront setup, supplier workflow, product-page copy, and order-flow automation.",
        "infrastructure": "Small-business hosting setup, landing-page deployment, monitoring, backup, and automation-ready infrastructure.",
        "content": "SEO content system, affiliate article engine, analytics, sitemap setup, and conversion tracking.",
        "service-automation": "AI receptionist, missed-call recovery, lead intake, quote-prep, booking, and follow-up automation.",
        "automation": "Workflow audit, automation buildout, tracking dashboard, and revenue-focused implementation support.",
    }

    first_actions = {
        "commerce": [
            "Pick one narrow product category with clear buyer intent and non-fragile shipping.",
            "Build a 25-product validation sheet with supplier, margin, shipping time, refund risk, and ad angle.",
            "Create one landing/storefront page, one product-page template, and one abandoned-cart follow-up sequence.",
            "Run a small organic-content or local-market validation test before spending on ads.",
        ],
        "infrastructure": [
            "Turn the article into a hosting setup checklist for one defined buyer type.",
            "Package the setup as a fixed-price deployment offer with backup and monitoring add-ons.",
            "Create a one-page intake form that captures domain, email, site type, budget, and launch deadline.",
            "Publish a comparison CTA that routes readers to the recommended setup path.",
        ],
        "content": [
            "Convert the article into one reusable lead magnet, checklist, or comparison table.",
            "Add internal links from related articles to the highest-converting offer page.",
            "Track affiliate clicks, CTA clicks, and email signups as separate conversion events.",
            "Use the top-performing article theme as the next article cluster topic.",
        ],
        "service-automation": [
            "Convert the article into a service offer with a clear outcome, setup scope, and monthly support option.",
            "Create a buyer-intake form for missed calls, lead source, service area, urgency, and current bottleneck.",
            "Add a low-friction CTA: request workflow review, book setup call, or send current process for diagnosis.",
            "Track every lead through contact, quote, booked job, invoice, and follow-up.",
        ],
        "automation": [
            "Identify the revenue event this article points to: lead, click, signup, sale, or booked call.",
            "Create one offer page or intake form tied to that event.",
            "Add a follow-up sequence that moves interested readers toward a paid action.",
            "Review analytics weekly and promote the article if it creates clicks or leads.",
        ],
    }

    tasks = "\n".join(f"- {item}" for item in first_actions[kind])
    tags_text = ", ".join(tags[:5]) if tags else "automation, revenue"
    return f"""

## Revenue Execution Brief

**How Already Here LLC can use this idea:** {offers[kind]}

**Best-fit offer angle:** Turn this topic into a fixed-scope implementation package, not just an information article. The article should attract the reader; the offer should give them a clear next step that saves time, reduces risk, or creates measurable revenue.

**First execution actions:**
{tasks}

**Automation asset to build from this article:** Create a simple intake workflow that captures the reader's goal, current setup, budget range, urgency, and preferred next step. Store those responses as structured data so future articles, offers, and follow-ups become smarter.

**Reuse path:** Break this article into a short social post, a checklist, a comparison table, and a sales CTA. Tag the asset cluster as: {tags_text}.
""".rstrip()


def _attach_revenue_action_brief(topic: str, article: Dict[str, Any]) -> Dict[str, Any]:
    if not ACTION_BRIEF_ENABLED:
        return article
    body = str(article.get("body", ""))
    if "## Revenue Execution Brief" in body:
        return article
    article["body"] = body.rstrip() + "\n" + _revenue_action_brief(topic, article)
    tags = article.get("tags", [])
    if isinstance(tags, list) and "revenue-action" not in tags:
        article["tags"] = [*tags, "revenue-action"]
    return article


def _affiliate_domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().removeprefix("www.")
    except Exception:
        return ""


def _keyword_score(keyword: str, url: str, body: str) -> int:
    text = body.lower()
    kw = keyword.lower()
    occurrences = len(re.findall(re.escape(kw), text, flags=re.IGNORECASE))
    if occurrences == 0:
        return -1

    score = occurrences * 10
    first_pos = text.find(kw)
    if 0 <= first_pos < 900:
        score += 35
    elif 0 <= first_pos < 1800:
        score += 20

    domain = _affiliate_domain(url)
    if any(term in kw for term in ("vps", "hosting", "cloud", "automation", "email", "seo", "ai")):
        score += 12
    if any(term in domain for term in ("hostinger", "digitalocean", "vultr", "cloudways", "bluehost", "siteground")):
        score += 8
    return score


def _rank_affiliate_tools(body: str, affiliate_map: Dict[str, str], limit: int = AFFILIATE_TOOL_LIMIT) -> List[Tuple[str, str]]:
    ranked: List[Tuple[int, int, str, str]] = []
    for order, (keyword, url) in enumerate(affiliate_map.items()):
        if not keyword or not url:
            continue
        score = _keyword_score(keyword, url, body)
        if score >= 0:
            ranked.append((score, -order, keyword, url))
    ranked.sort(reverse=True)
    return [(kw, url) for _, _, kw, url in ranked[:limit]]


def _limited_affiliate_map() -> Dict[str, str]:
    raw = _ORIGINAL_AFFILIATE_MAP()
    if len(raw) <= AFFILIATE_PROMPT_LIMIT:
        return raw
    return dict(list(raw.items())[:AFFILIATE_PROMPT_LIMIT])


def _destination_with_utm(url: str, keyword: str, placement: str) -> str:
    try:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return url
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        query.setdefault("utm_source", "alreadyherellc")
        query.setdefault("utm_medium", "affiliate")
        query.setdefault("utm_campaign", AFFILIATE_UTM_CAMPAIGN)
        query.setdefault("utm_content", re.sub(r"[^a-z0-9_-]", "-", f"{placement}-{keyword}".lower()).strip("-"))
        return urlunparse(parsed._replace(query=urlencode(query)))
    except Exception:
        return url


def _tracked_link(keyword: str, url: str, placement: str) -> str:
    return f"[{keyword}]({_destination_with_utm(url, keyword, placement)})"


def _affiliate_disclosure() -> str:
    if not AFFILIATE_DISCLOSURE:
        return ""
    return f"> **Affiliate disclosure:** {AFFILIATE_DISCLOSURE}\n\n"


def _top_picks_section(tools: List[Tuple[str, str]]) -> str:
    featured = tools[:AFFILIATE_FEATURED_LIMIT]
    if not featured:
        return ""
    items = "\n".join(f"- **{_tracked_link(keyword, url, 'top-pick')}**" for keyword, url in featured)
    return f"\n\n## Top Picks\n\n{items}\n"


def _recommended_tools_section(body: str, affiliate_map: Dict[str, str]) -> str:
    matched = _rank_affiliate_tools(body, affiliate_map, AFFILIATE_TOOL_LIMIT)
    if not matched:
        return ""
    items = "\n".join(f"- {_tracked_link(keyword, url, 'recommended-tools')}" for keyword, url in matched)
    return f"\n\n## Recommended Tools\n\n{items}\n"


def _wrap_existing_affiliate_links(body: str, affiliate_map: Dict[str, str]) -> str:
    url_to_keyword = {url.rstrip("/"): keyword for keyword, url in affiliate_map.items() if url}

    def repl(match: "re.Match[str]") -> str:
        label = match.group(1)
        url = match.group(2)
        keyword = url_to_keyword.get(url.rstrip("/"))
        if not keyword:
            host = _affiliate_domain(url)
            for configured_url, configured_keyword in url_to_keyword.items():
                if host and host == _affiliate_domain(configured_url):
                    keyword = configured_keyword
                    break
        if not keyword:
            return match.group(0)
        return f"[{label}]({_destination_with_utm(url, keyword, 'inline')})"

    return re.sub(r"\[([^\]]+)\]\((https?://[^\)\s]+)\)", repl, body)


def _insert_after_intro(body: str, insertion: str) -> str:
    if not insertion or "## Top Picks" in body:
        return body
    paragraphs = body.split("\n\n")
    if len(paragraphs) < 2:
        return body + insertion
    return "\n\n".join(paragraphs[:2]) + insertion + "\n\n" + "\n\n".join(paragraphs[2:])


def _optimized_inject_affiliates(body: str) -> str:
    affiliate_map = _limited_affiliate_map()
    if not affiliate_map:
        return publisher._tag_amazon_links(body)  # type: ignore[attr-defined]

    for keyword, url in affiliate_map.items():
        body = body.replace(f"[AFFILIATE:{keyword}]", f"[{keyword}]({url})")

    body = re.sub(r"\[AFFILIATE:([^\]]+)\]", r"\1", body)
    body = publisher._auto_link_keywords(body, affiliate_map)  # type: ignore[attr-defined]
    body = publisher._tag_amazon_links(body)  # type: ignore[attr-defined]

    selected_tools = _rank_affiliate_tools(body, affiliate_map, AFFILIATE_TOOL_LIMIT)
    if selected_tools:
        body = _affiliate_disclosure() + body
        body = _insert_after_intro(body, _top_picks_section(selected_tools))
        body += _recommended_tools_section(body, dict(selected_tools))

    return _wrap_existing_affiliate_links(body, affiliate_map)


def _check_social_credentials() -> Dict[str, bool]:
    """Check which social media platforms have credentials available."""
    credentials = {
        "twitter": bool(os.getenv("TWITTER_API_KEY") or os.getenv("TWITTER_BEARER_TOKEN")),
        "reddit": bool(os.getenv("REDDIT_CLIENT_ID") and os.getenv("REDDIT_CLIENT_SECRET")),
        "facebook": bool(os.getenv("FACEBOOK_PAGE_TOKEN") or os.getenv("FACEBOOK_ACCESS_TOKEN")),
        "linkedin": bool(os.getenv("LINKEDIN_ACCESS_TOKEN")),
        "instagram": bool(os.getenv("INSTAGRAM_ACCESS_TOKEN")),
        "tiktok": bool(os.getenv("TIKTOK_ACCESS_TOKEN")),
        "telegram": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
        "mastodon": bool(os.getenv("MASTODON_ACCESS_TOKEN")),
        "bluesky": bool(os.getenv("BLUESKY_USERNAME") and os.getenv("BLUESKY_PASSWORD")),
    }
    return credentials


def _check_ecommerce_credentials() -> Dict[str, bool]:
    """Check which e-commerce platforms have credentials available."""
    credentials = {
        "shopify": bool(os.getenv("SHOPIFY_STORE_URL") and os.getenv("SHOPIFY_ACCESS_TOKEN")),
        "etsy": bool(os.getenv("ETSY_API_KEY") and os.getenv("ETSY_API_SECRET")),
        "amazon": bool(os.getenv("AMAZON_ACCESS_KEY") and os.getenv("AMAZON_SECRET_KEY")),
        "ebay": bool(os.getenv("EBAY_APP_ID") and os.getenv("EBAY_DEV_ID")),
        "woocommerce": bool(os.getenv("WOOCOMMERCE_API_KEY") and os.getenv("WOOCOMMERCE_API_SECRET")),
        "gumroad": GUMROAD_ENABLED,
        "printify": PRINTIFY_ENABLED,
    }
    return credentials


def _verify_huggingface_token() -> bool | None:
    hf_token = getattr(publisher, "HF_TOKEN", "")
    if hf_token:
        try:
            r = httpx.get(
                "https://huggingface.co/api/whoami-v2",
                headers={"Authorization": f"Bearer {hf_token}"},
                timeout=20,
            )
            if r.is_success:
                print("[VERIFY][OK] HuggingFace: token accepted")
                return True
            print(f"[VERIFY][FAIL] HuggingFace {r.status_code}: {r.text[:240]}")
        except Exception as exc:
            print(f"[VERIFY][FAIL] HuggingFace request failed: {exc}")
            return False
    return None


def _verify_ai_provider_hf_aware() -> bool:
    """Verify the active provider chain and report HuggingFace token health."""
    provider_ok = False
    try:
        provider_ok = bool(_ORIGINAL_VERIFY_AI_PROVIDER())
    except Exception as exc:
        print(f"[VERIFY][WARN] Default AI provider verification raised: {exc}")

    hf_ok = _verify_huggingface_token()
    if provider_ok or hf_ok:
        return True

    print("[VERIFY][FAIL] AI provider: no usable Groq, Gemini, or HuggingFace provider verified")
    return False


def _word_count(text: str) -> int:
    """Count words in text, excluding markdown formatting."""
    cleaned = re.sub(r"[#*_`\[\]\(\)]", " ", text)
    return len(cleaned.split())


def _get_product_suggestions(article: Dict[str, Any]) -> List[str]:
    """Suggest POD products based on article topic and tags."""
    title = str(article.get("title", "")).lower()
    tags = [str(t).lower() for t in article.get("tags", [])]
    body = str(article.get("body", "")).lower()[:2000]
    haystack = f"{title} {' '.join(tags)} {body}"

    suggestions = []

    # Topic-based product suggestions
    topic_products = {
        "automation": ["t-shirt", "mug", "hoodie", "sticker"],
        "ai": ["t-shirt", "mug", "hat", "notebook"],
        "small business": ["notebook", "mug", "poster", "desk-pad"],
        "revenue": ["poster", "canvas-print", "calendar"],
        "seo": ["notebook", "guide-book", "poster"],
        "ecommerce": ["t-shirt", "mug", "canvas-print"],
        "content": ["guide-book", "poster", "notebook"],
        "affiliate": ["guide-book", "poster"],
        "smallbusiness": ["notebook", "t-shirt", "mug"],
    }

    for topic, products in topic_products.items():
        if topic in haystack:
            suggestions.extend(products)

    # Remove duplicates while preserving order
    seen = set()
    unique_suggestions = []
    for product in suggestions:
        if product not in seen:
            seen.add(product)
            unique_suggestions.append(product)

    # Return top 3, with defaults
    if not unique_suggestions:
        unique_suggestions = ["t-shirt", "mug", "notebook"]

    return unique_suggestions[:3]


def _convert_article_to_ebook(article: Dict[str, Any], output_dir: str = ".") -> Optional[str]:
    """
    Convert article to ebook format (markdown-based for simplicity, ready for PDF conversion).
    Returns path to generated ebook file.
    """
    try:
        title = str(article.get("title", "Untitled"))
        body = str(article.get("body", ""))
        tags = article.get("tags", [])
        slug = _slugify(title)

        # Create ebook markdown with front matter
        ebook_content = f"""# {title}

**Author:** Already Here LLC
**Published:** {datetime.now(timezone.utc).strftime('%B %d, %Y')}
**Tags:** {', '.join(str(t) for t in tags)}

---

## About This Ebook

This is a companion ebook to our article on **{title}**. It includes the full article content, action checklists, and a revenue execution brief for immediate implementation.

**What You'll Learn:**
- Practical workflow steps for {title.lower()}
- Revenue-focused implementation strategy
- First actions to take this week
- Risk controls and margin rules

---

## Content

{body}

---

## Implementation Checklist

- [ ] Review the core concepts and identify the one blocker that costs you most time or revenue
- [ ] Define your specific revenue event (sale, booking, signup, affiliate click)
- [ ] Build the minimum working system with capture, qualify, respond, track, review
- [ ] Test with 3-5 real prospects or customers
- [ ] Document what worked and what didn't
- [ ] Expand one successful path into a repeatable workflow
- [ ] Measure revenue impact and adjust

---

## Next Steps

1. Share this ebook with your team
2. Pick one revenue event and build backward from it
3. Email us at dispatch@alreadyherellc.com to share your results

**Already Here LLC**
Practical AI automation for small business revenue
{GUMROAD_AMAZON_TAG}

---

_This ebook is published under the Creative Commons Attribution-NonCommercial license._
"""

        output_path = Path(output_dir) / f"{slug}_ebook.md"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(ebook_content)

        print(f"[EBOOK][OK] Generated ebook markdown: {output_path}")
        return str(output_path)

    except Exception as exc:
        print(f"[EBOOK][FAIL] Failed to generate ebook: {exc}")
        return None


def _publish_to_gumroad(ebook_path: str, article: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """
    Publish ebook to Gumroad via API.
    Returns dict with gumroad_url and product_id if successful.
    """
    if not GUMROAD_ENABLED:
        print("[GUMROAD][SKIP] Gumroad disabled or no API key configured")
        return None

    try:
        title = str(article.get("title", "Ebook"))
        slug = _slugify(title)
        tags = article.get("tags", [])

        # Build product description
        description = f"""This is a premium ebook companion to our article on {title}.

Includes:
- Full article content with implementation steps
- Revenue execution brief
- Action checklist for immediate implementation
- Best practices and margin rules

Tags: {', '.join(str(t) for t in tags[:5])}"""

        # Prepare multipart form data for file upload
        with open(ebook_path, "rb") as f:
            files = {"file": (f"{slug}_ebook.md", f)}
            data = {
                "name": f"{title} - Premium Ebook",
                "description": description,
                "price": str(GUMROAD_BASE_PRICE),
                "require_email": "true",
                "tags": ",".join(str(t) for t in tags[:3]),
            }

            headers = {"Authorization": f"Bearer {GUMROAD_API_KEY}"}

            response = httpx.post(
                "https://api.gumroad.com/v2/products",
                data=data,
                files=files,
                headers=headers,
                timeout=30,
            )

            if response.is_success:
                result = response.json()
                product_data = result.get("product", {})
                product_id = product_data.get("id", "")
                product_url = product_data.get("url", f"https://gumroad.com/d/{product_id}")

                print(f"[GUMROAD][OK] Product published: {product_url}")
                return {
                    "status": "success",
                    "product_id": product_id,
                    "url": product_url,
                    "price": GUMROAD_BASE_PRICE,
                }
            else:
                print(f"[GUMROAD][FAIL] API error {response.status_code}: {response.text[:240]}")
                return {
                    "status": "failed",
                    "error": f"HTTP {response.status_code}",
                }

    except FileNotFoundError:
        print(f"[GUMROAD][FAIL] Ebook file not found: {ebook_path}")
        return {"status": "failed", "error": "ebook_file_not_found"}
    except Exception as exc:
        print(f"[GUMROAD][FAIL] {exc}")
        return {"status": "failed", "error": str(exc)[:200]}


def _create_printify_product(article: Dict[str, Any], product_type: str) -> Optional[Dict[str, str]]:
    """
    Queue POD product creation on Printify (requires manual design approval).
    Returns dict with printify_url and product_id if successful.
    """
    if not PRINTIFY_ENABLED:
        print(f"[PRINTIFY][SKIP] Printify disabled or no API key configured")
        return None

    try:
        title = str(article.get("title", "Untitled"))
        slug = _slugify(title)
        tags = article.get("tags", [])

        # Product type mappings to Printify print providers
        product_configs = {
            "t-shirt": {
                "title_suffix": "T-Shirt",
                "description": f"Premium quality t-shirt featuring {title.lower()}. Perfect for automation enthusiasts.",
            },
            "mug": {
                "title_suffix": "Coffee Mug",
                "description": f"High-quality ceramic mug with {title.lower()} design. Great for your desk or workspace.",
            },
            "hoodie": {
                "title_suffix": "Hoodie",
                "description": f"Comfortable and durable hoodie featuring {title.lower()} artwork.",
            },
            "notebook": {
                "title_suffix": "Workbook",
                "description": f"Premium workbook with {title.lower()} content, checklists, and implementation guides.",
            },
            "poster": {
                "title_suffix": "Poster",
                "description": f"Eye-catching poster covering key concepts from {title.lower()}.",
            },
            "sticker": {
                "title_suffix": "Sticker Pack",
                "description": f"Set of premium stickers featuring {title.lower()} themes.",
            },
        }

        if product_type not in product_configs:
            print(f"[PRINTIFY][SKIP] Unknown product type: {product_type}")
            return None

        config = product_configs[product_type]
        product_title = f"{title} - {config['title_suffix']}"

        # Build product data for Printify API
        product_data = {
            "title": product_title,
            "description": config["description"],
            "tags": ",".join(str(t) for t in tags[:3]),
            "variants": [
                {
                    "title": config["title_suffix"],
                    "price": 2499,  # Printify price in cents
                }
            ],
        }

        headers = {"Authorization": f"Bearer {PRINTIFY_API_KEY}"}

        response = httpx.post(
            "https://api.printify.com/v1/shops/me/products",
            json=product_data,
            headers=headers,
            timeout=30,
        )

        if response.is_success:
            result = response.json()
            product_id = result.get("id", "")
            product_url = f"https://printify.com/dashboard/products/{product_id}"

            print(f"[PRINTIFY][OK] Product queued for {product_type}: {product_url}")
            return {
                "status": "pending_design",
                "product_id": product_id,
                "product_type": product_type,
                "url": product_url,
                "note": "Product created. Requires design upload and manual approval before publishing.",
            }
        else:
            print(f"[PRINTIFY][FAIL] API error {response.status_code}: {response.text[:240]}")
            return {
                "status": "failed",
                "product_type": product_type,
                "error": f"HTTP {response.status_code}",
            }

    except Exception as exc:
        print(f"[PRINTIFY][FAIL] {exc}")
        return {
            "status": "failed",
            "product_type": product_type,
            "error": str(exc)[:200],
        }


def _extract_tips_from_article(article: Dict[str, Any]) -> List[Dict[str, str]]:
    """Extract 5-10 'Tip of the Day' posts from article content."""
    body = str(article.get("body", ""))
    title = str(article.get("title", ""))
    tags = article.get("tags", [])

    tips = []

    # Extract tips from section headers
    sections = re.split(r'^## ', body, flags=re.MULTILINE)[1:]

    for i, section in enumerate(sections[:10], 1):
        lines = section.split('\n')
        section_title = lines[0] if lines else "Tip"
        section_body = '\n'.join(lines[1:])

        # Extract first 1-2 sentences as tip
        sentences = re.split(r'(?<=[.!?])\s+', section_body)
        if sentences:
            tip_text = ' '.join(sentences[:2]).strip()
            if len(tip_text) > 20:
                tips.append({
                    "title": f"Tip {i}: {section_title[:50]}",
                    "content": tip_text[:280],  # Keep short for social
                    "source_article": title,
                    "tags": tags,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

    return tips[:10]


def _generate_video_script(article: Dict[str, Any]) -> Dict[str, str]:
    """Generate short-form video script from article (for TikTok/Reels)."""
    title = str(article.get("title", ""))
    body = str(article.get("body", ""))
    tags = article.get("tags", [])

    # Extract 2-3 key points for 15-30 second video
    sentences = re.split(r'(?<=[.!?])\s+', body)
    key_points = [s.strip() for s in sentences if len(s.strip()) > 30][:3]

    script_lines = [
        f"Did you know? {title}",
        "",
    ]

    for i, point in enumerate(key_points, 1):
        # Truncate to video-friendly length
        truncated = point[:120] + ("..." if len(point) > 120 else "")
        script_lines.append(f"{i}. {truncated}")

    script_lines.extend([
        "",
        "Read the full article for implementation details.",
        "Link in bio / Check pinned comment",
    ])

    return {
        "platform": "short_form",  # TikTok, Instagram Reels, YouTube Shorts
        "duration": "15-30 seconds",
        "script": "\n".join(script_lines),
        "tags": tags,
        "hashtags": ["#" + t for t in tags[:5]] + ["#automation", "#smallbusiness"],
        "cta": "Read full article",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _generate_youtube_ai_video_option(article: Dict[str, Any]) -> Dict[str, str]:
    """Generate AI video script for YouTube (longer form, 3-5 min)."""
    title = str(article.get("title", ""))
    body = str(article.get("body", ""))
    tags = article.get("tags", [])

    # Break body into sections for video chapters
    sections = re.split(r'^## ', body, flags=re.MULTILINE)[1:]

    chapters = []
    for i, section in enumerate(sections[:5], 1):
        lines = section.split('\n')
        section_title = lines[0] if lines else f"Point {i}"
        section_body = '\n'.join(lines[1:])

        # Extract first 2-3 sentences
        sentences = re.split(r'(?<=[.!?])\s+', section_body)
        chapter_content = ' '.join(sentences[:3]).strip()

        chapters.append({
            "timestamp": f"0:{i*45}-0:{(i+1)*45}",  # Rough timing estimate
            "title": section_title[:60],
            "content": chapter_content[:500],
        })

    intro = f"In this video, we explore {title.lower()}. Whether you're looking to improve efficiency, increase revenue, or reduce risk, this guide walks you through practical implementation steps."

    outro = f"If this was helpful, please like and subscribe for more automation and revenue strategies. Check the description for the full article, ebook, and related resources."

    return {
        "platform": "youtube",
        "duration": "3-5 minutes",
        "title": f"{title} - Complete Guide",
        "intro": intro,
        "chapters": chapters,
        "outro": outro,
        "tags": tags,
        "description_highlights": [
            "Full article available on our blog",
            "Free ebook PDF download link",
            "Related videos in playlist",
            "Implementation checklist in comments",
        ],
        "thumbnail_description": f"{title} - Small Business Automation",
        "cta_timestamp": "3:45",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _create_newsletter_issue(article: Dict[str, Any], canonical_url: str) -> Dict[str, str]:
    """Create a newsletter issue featuring the article."""
    title = str(article.get("title", ""))
    body = str(article.get("body", ""))
    tags = article.get("tags", [])

    # Extract summary (first 2-3 paragraphs)
    paragraphs = body.split('\n\n')
    summary = '\n\n'.join(paragraphs[:2])

    # Extract action items from Revenue Execution Brief
    action_section = ""
    if "## Revenue Execution Brief" in body:
        brief_start = body.find("## Revenue Execution Brief")
        action_section = body[brief_start:brief_start+1000]

    newsletter_content = f"""Subject: {title} + Implementation Guide

Hi there,

We just published a detailed guide on {title.lower()}.

**Key Takeaway:**
{summary[:250]}...

**What You'll Learn:**
- Practical workflow steps
- Revenue-focused implementation
- First actions to take this week
- Risk controls and margin rules

**Read the Full Article:**
{canonical_url}

**Download the Ebook:**
Premium version with checklists and templates available on Gumroad.

{action_section if action_section else ""}

**Next Steps:**
1. Read the article (5-10 min)
2. Pick one revenue event to improve
3. Build your minimum working system
4. Share your results with us

Questions? Reply to this email.

Best,
Already Here LLC
---
Practical AI automation for small business revenue
dispatch@alreadyherellc.com"""

    return {
        "type": "newsletter",
        "title": f"Newsletter Issue: {title}",
        "subject": f"{title} + Implementation Guide",
        "content": newsletter_content,
        "featured_article_url": canonical_url,
        "tags": tags,
        "send_to_segments": ["all_subscribers"],
        "estimated_read_time": "5-7 minutes",
        "cta_primary": "Read Full Article",
        "cta_primary_url": canonical_url,
        "cta_secondary": "Download Ebook",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _create_news_update(article: Dict[str, Any], canonical_url: str) -> Dict[str, str]:
    """Create a news/update post from article."""
    title = str(article.get("title", ""))
    body = str(article.get("body", ""))
    tags = article.get("tags", [])

    # Extract key insight
    sentences = re.split(r'(?<=[.!?])\s+', body)
    key_insight = next((s.strip() for s in sentences if len(s.strip()) > 50), body[:150])

    return {
        "type": "news_update",
        "headline": f"UPDATE: {title}",
        "summary": key_insight[:280],
        "full_article_url": canonical_url,
        "tags": tags,
        "priority": "high" if any(t in tags for t in ["revenue", "automation", "ai"]) else "normal",
        "notification": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _build_unified_distribution_plan(
    article: Dict[str, Any],
    canonical_url: str,
) -> Dict[str, Any]:
    """Build unified content distribution plan from single article."""
    title = str(article.get("title", ""))
    body = str(article.get("body", ""))
    word_count = _word_count(body)

    # Extract all content variants
    tips = _extract_tips_from_article(article)
    short_video = _generate_video_script(article)
    long_video = _generate_youtube_ai_video_option(article)
    newsletter = _create_newsletter_issue(article, canonical_url)
    news_update = _create_news_update(article, canonical_url)

    # Count total distribution channels
    total_channels = 10 + (len(tips) // 2)  # Base 10 + social tips

    return {
        "article": {
            "title": title,
            "url": canonical_url,
            "word_count": word_count,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        "distribution_plan": {
            "primary_channels": {
                "blog": canonical_url,
                "ebook": "gumroad",
                "pod_products": "printify",
                "newsletter": newsletter,
                "news_update": news_update,
            },
            "short_form_content": {
                "tiktok_reels_shorts": short_video,
                "tips_of_day": tips,
                "tips_count": len(tips),
            },
            "long_form_content": {
                "youtube_video": long_video,
                "video_chapters": len(long_video.get("chapters", [])),
            },
        },
        "content_variants_generated": {
            "blog_article": 1,
            "ebook": 1,
            "pod_products": "2-3",
            "newsletter_issues": 1,
            "news_updates": 1,
            "short_videos": 1,
            "video_scripts": 1,
            "daily_tips": len(tips),
            "total_content_pieces": 1 + 1 + 3 + 1 + 1 + len(tips) + 1,
        },
        "reach_estimate": {
            "total_channels": total_channels,
            "blog_traffic_estimate": "50-200 organic views",
            "social_reach_estimate": "500-2000 impressions",
            "newsletter_reach_estimate": "100-500 subscribers",
            "revenue_potential_usd": {
                "ebook_sales_low": 0.5,
                "ebook_sales_high": 50.0,
                "pod_sales_low": 5.0,
                "pod_sales_high": 100.0,
                "total_potential_low": 5.50,
                "total_potential_high": 150.0,
                "realistic_estimate": 50.0,
            },
        },
        "implementation_timeline": {
            "content_generation": "1-2 hours",
            "distribution": "2-4 hours",
            "monitoring": "ongoing",
            "total_effort_estimate": "3-6 hours",
        },
        "next_actions": [
            "Review and approve all generated content variants",
            "Schedule social media posts (spread over 2 weeks)",
            "Publish newsletter issue to email list",
            "Queue YouTube video for editing and upload",
            "Approve POD product designs on Printify",
            "Monitor conversion metrics across all channels",
            "Collect customer feedback on article usefulness",
            "Link related articles to new content",
            "Create follow-up content series on trending angle",
            "Analyze which channel drives most conversions",
        ],
    }


def _build_monetization_report(
    article: Dict[str, Any],
    canonical_url: str,
    social_results: Dict[str, Any],
    ecommerce_results: Dict[str, Any],
) -> Dict[str, Any]:
    """Build comprehensive monetization report for article publication."""
    title = str(article.get("title", "Untitled"))
    body = str(article.get("body", ""))
    word_count = _word_count(body)
    tags = article.get("tags", [])

    # Check if ebook should be created
    ebook_eligible = word_count >= EBOOK_WORD_LIMIT
    ebook_result = ecommerce_results.get("gumroad", {})
    ebook_created = ebook_result.get("status") == "success"

    # Check POD products
    printify_results = ecommerce_results.get("printify", {})
    pod_products = []
    if isinstance(printify_results, dict):
        for product_type, result in printify_results.items():
            if isinstance(result, dict):
                pod_products.append({
                    "type": product_type,
                    "status": result.get("status", "unknown"),
                    "url": result.get("url", ""),
                })

    # Social platform counts
    social_count = len([v for k, v in social_results.items() if isinstance(v, dict) and v.get("status") == "success"])

    # Extract tips for distribution
    tips = _extract_tips_from_article(article)

    # Estimate revenue potential
    revenue_estimate = {
        "gumroad_ebook": GUMROAD_BASE_PRICE if ebook_created else 0,
        "expected_sales_10_percent": (GUMROAD_BASE_PRICE * 0.1) if ebook_created else 0,
        "expected_sales_1_percent": (GUMROAD_BASE_PRICE * 0.01) if ebook_created else 0,
        "pod_potential_conservative": len(pod_products) * 5.0,  # Assume $5 profit per product, 1 sale each
        "currency": "USD",
        "note": "Conservative estimates based on typical content monetization rates",
    }

    return {
        "article": {
            "title": title,
            "word_count": word_count,
            "tags": tags,
            "canonical_url": canonical_url,
        },
        "monetization": {
            "ebook": {
                "eligible": ebook_eligible,
                "created": ebook_created,
                "price": GUMROAD_BASE_PRICE if ebook_created else None,
                "url": ebook_result.get("url") if ebook_created else None,
            },
            "pod_products": {
                "queued_count": len(pod_products),
                "products": pod_products,
            },
        },
        "distribution": {
            "social_platforms": social_count,
            "daily_tips_queued": len(tips),
            "canonical_url": canonical_url,
        },
        "revenue_potential": revenue_estimate,
        "next_actions": [
            "Monitor Gumroad sales and email opt-ins",
            "Review Printify designs and approve POD products",
            "Add product links to related articles",
            "Create email sequence promoting the ebook",
            "Track affiliate clicks and conversions",
            "Publish daily tips across social platforms",
            "Queue short-form video content for distribution",
            "Schedule newsletter issue delivery",
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def main() -> None:
    publisher._verify_ai_provider = _verify_ai_provider_hf_aware  # type: ignore[attr-defined]
    publisher._affiliate_map = _limited_affiliate_map  # type: ignore[attr-defined]
    publisher._recommended_tools_section = _recommended_tools_section  # type: ignore[attr-defined]
    publisher._inject_affiliates = _optimized_inject_affiliates  # type: ignore[attr-defined]

    original_generate_article = publisher.generate_article
    original_publish_github = publisher.publish_github
    publish_state: Dict[str, Any] = {
        "canonical_url": "",
        "article": {},
        "distribution_report": {},
    }

    def generate_article_with_fallback(topic: str) -> Dict[str, Any]:
        try:
            article = original_generate_article(topic)
        except SystemExit as exc:
            exc_msg = str(exc).encode('ascii', 'replace').decode('ascii')
            print(f"[AI][WARN] Provider generation exited: {exc_msg}. Using deterministic article fallback.")
            article = _deterministic_article(topic)
        except Exception as exc:
            exc_msg = str(exc).encode('ascii', 'replace').decode('ascii')
            print(f"[AI][WARN] Provider generation failed: {exc_msg}. Using deterministic article fallback.")
            article = _deterministic_article(topic)
        article = _attach_revenue_action_brief(topic, article)
        publish_state["article"] = article
        return article

    def publish_github_strict(filename: str, content: str, commit_msg: str) -> str:
        url = original_publish_github(filename, content, commit_msg)
        publish_state["canonical_url"] = url
        return url

    publisher.generate_article = generate_article_with_fallback  # type: ignore[assignment]
    publisher.publish_github = publish_github_strict  # type: ignore[assignment]

    started = datetime.now(timezone.utc).isoformat()
    print(f"[RESILIENT] Strict optimized action publisher started at {started}")
    publisher.main()

    if not getattr(publisher, "VERIFY_ONLY", False) and not publish_state["canonical_url"]:
        sys.exit("[PUBLISH][FAIL] No GitHub Pages canonical URL was produced. Treating as failed publish.")

    if publish_state["canonical_url"]:
        print(f"[PUBLISH][OK] Strict publish verified: {publish_state['canonical_url']}")

    # Distribute to social media and e-commerce platforms after GitHub publish succeeds
    if publish_state["canonical_url"] and not getattr(publisher, "VERIFY_ONLY", False):
        print("[DISTRIBUTE] Starting distribution to social and e-commerce platforms...")

        article = publish_state.get("article", {})
        canonical_url = publish_state["canonical_url"]
        image_url = article.get("image_url", "")
        video_url = article.get("video_url", "")

        distribution_report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "canonical_url": canonical_url,
            "social_media": {},
            "ecommerce": {},
            "summary": {"total_platforms": 0, "successful": 0, "failed": 0, "skipped": 0},
        }

        # Social Media Distribution
        social_creds = _check_social_credentials()
        if social_creds and any(social_creds.values()):
            if publish_to_all_platforms is not None:
                try:
                    social_results = publish_to_all_platforms(article, canonical_url, image_url=image_url, video_url=video_url)
                    distribution_report["social_media"] = social_results
                    print(f"[DISTRIBUTE][OK] Social media distribution completed")
                except (ImportError, AttributeError) as e:
                    print(f"[DISTRIBUTE][SKIP] Social media module unavailable (missing dependencies): {e}")
                    for platform, has_cred in social_creds.items():
                        if has_cred:
                            distribution_report["social_media"][platform] = {"status": "skipped", "reason": "module_unavailable"}
                            distribution_report["summary"]["skipped"] += 1
                except Exception as exc:
                    exc_msg = str(exc).encode('ascii', 'replace').decode('ascii')
                    print(f"[DISTRIBUTE][WARN] Social media distribution failed: {exc_msg}")
                    for platform, has_cred in social_creds.items():
                        if has_cred:
                            distribution_report["social_media"][platform] = {"status": "failed", "error": exc_msg}
            else:
                print("[DISTRIBUTE][SKIP] Social media module not available (import failed)")
                for platform, has_cred in social_creds.items():
                    if has_cred:
                        distribution_report["social_media"][platform] = {"status": "skipped", "reason": "module_import_failed"}
                        distribution_report["summary"]["skipped"] += 1
        else:
            print("[DISTRIBUTE][SKIP] No social media credentials configured")
            for platform in social_creds.keys():
                distribution_report["social_media"][platform] = {"status": "skipped", "reason": "no_credentials"}
                distribution_report["summary"]["skipped"] += 1

        # Priority Stack Publishing (B - Dev.to, Hashnode, Beehiiv, Telegram, YouTube)
        if publish_to_priority_platforms is not None:
            try:
                priority_results = publish_to_priority_platforms(article)
                priority_report = generate_priority_report(article, priority_results) if generate_priority_report else {}
                distribution_report["priority_platforms"] = {
                    "platforms": priority_results,
                    "report": priority_report
                }
                print(f"[DISTRIBUTE][OK] Priority platforms distribution completed")
            except (ImportError, AttributeError) as e:
                print(f"[DISTRIBUTE][SKIP] Priority publishers module unavailable (missing dependencies): {e}")
                distribution_report["priority_platforms"] = {"status": "skipped", "reason": "module_unavailable"}
            except Exception as exc:
                exc_msg = str(exc).encode('ascii', 'replace').decode('ascii')
                print(f"[DISTRIBUTE][WARN] Priority platforms distribution failed: {exc_msg}")
                distribution_report["priority_platforms"] = {"status": "failed", "error": exc_msg}
        else:
            print("[DISTRIBUTE][SKIP] Priority publishers module not available (import failed)")
            distribution_report["priority_platforms"] = {"status": "skipped", "reason": "module_import_failed"}

        # E-commerce Distribution (includes Gumroad & Printify)
        ecommerce_creds = _check_ecommerce_credentials()
        ecommerce_results_all = {}

        # First try the main ecommerce module
        if publish_to_all_ecommerce is not None:
            try:
                ecommerce_results_all = publish_to_all_ecommerce(article)
                print(f"[DISTRIBUTE][OK] E-commerce module distribution completed")
            except (ImportError, AttributeError) as e:
                print(f"[DISTRIBUTE][SKIP] E-commerce module unavailable (missing dependencies): {e}")
            except Exception as exc:
                exc_msg = str(exc).encode('ascii', 'replace').decode('ascii')
                print(f"[DISTRIBUTE][WARN] E-commerce module distribution failed: {exc_msg}")

        # Then handle Gumroad & Printify monetization
        body_text = str(article.get("body", ""))
        word_count = _word_count(body_text)

        if GUMROAD_ENABLED and word_count >= EBOOK_WORD_LIMIT:
            print(f"[MONETIZE] Article has {word_count} words (threshold: {EBOOK_WORD_LIMIT}). Creating ebook...")
            ebook_path = _convert_article_to_ebook(article)
            if ebook_path:
                gumroad_result = _publish_to_gumroad(ebook_path, article)
                ecommerce_results_all["gumroad"] = gumroad_result if gumroad_result else {"status": "failed"}
            else:
                ecommerce_results_all["gumroad"] = {"status": "failed", "error": "ebook_generation_failed"}
        elif GUMROAD_ENABLED:
            print(f"[MONETIZE] Article has {word_count} words (threshold: {EBOOK_WORD_LIMIT}). Skipping ebook.")
            ecommerce_results_all["gumroad"] = {"status": "skipped", "reason": f"word_count_too_low ({word_count}<{EBOOK_WORD_LIMIT})"}
        else:
            ecommerce_results_all["gumroad"] = {"status": "skipped", "reason": "gumroad_disabled"}

        if PRINTIFY_ENABLED:
            print("[MONETIZE] Generating POD product suggestions...")
            product_suggestions = _get_product_suggestions(article)
            printify_results = {}
            for product_type in product_suggestions:
                print(f"[MONETIZE] Queuing {product_type} for Printify...")
                result = _create_printify_product(article, product_type)
                printify_results[product_type] = result if result else {"status": "failed"}
            ecommerce_results_all["printify"] = printify_results
        else:
            ecommerce_results_all["printify"] = {"status": "skipped", "reason": "printify_disabled"}

        distribution_report["ecommerce"] = ecommerce_results_all
        print(f"[DISTRIBUTE][OK] Complete e-commerce/monetization distribution completed")

        # Aggregate summary
        social_success = len([v for k, v in distribution_report["social_media"].items() if isinstance(v, dict) and v.get("status") == "success"])
        social_failed = len([v for k, v in distribution_report["social_media"].items() if isinstance(v, dict) and v.get("status") == "failed"])
        social_skipped = len([v for k, v in distribution_report["social_media"].items() if isinstance(v, dict) and v.get("status") == "skipped"])

        ecommerce_success = len([v for k, v in distribution_report["ecommerce"].items() if isinstance(v, dict) and v.get("status") == "success"])
        ecommerce_failed = len([v for k, v in distribution_report["ecommerce"].items() if isinstance(v, dict) and v.get("status") == "failed"])
        ecommerce_skipped = len([v for k, v in distribution_report["ecommerce"].items() if isinstance(v, dict) and v.get("status") == "skipped"])

        distribution_report["summary"]["successful"] = social_success + ecommerce_success
        distribution_report["summary"]["failed"] = social_failed + ecommerce_failed
        distribution_report["summary"]["skipped"] = social_skipped + ecommerce_skipped
        distribution_report["summary"]["total_platforms"] = (
            len([k for k in distribution_report["social_media"].keys()]) +
            len([k for k in distribution_report["ecommerce"].keys()])
        )

        # Build unified distribution plan
        print("[DISTRIBUTE] Building unified content distribution plan...")
        unified_plan = _build_unified_distribution_plan(article, canonical_url)

        # Build monetization report
        monetization_report = _build_monetization_report(
            article,
            canonical_url,
            distribution_report["social_media"],
            distribution_report["ecommerce"],
        )

        # Generate content dashboard
        tips = _extract_tips_from_article(article)
        short_video = _generate_video_script(article)
        long_video = _generate_youtube_ai_video_option(article)
        newsletter = _create_newsletter_issue(article, canonical_url)
        news_update = _create_news_update(article, canonical_url)

        content_dashboard = {
            "report_date": datetime.now(timezone.utc).isoformat(),
            "article": {
                "title": article.get("title", ""),
                "canonical_url": canonical_url,
                "word_count": _word_count(article.get("body", "")),
                "tags": article.get("tags", []),
            },
            "generated_content_items": {
                "blog_article": {
                    "status": "published",
                    "url": canonical_url,
                    "distribution_channels": 1,
                },
                "ebook": {
                    "status": "queued" if GUMROAD_ENABLED else "disabled",
                    "price": GUMROAD_BASE_PRICE if GUMROAD_ENABLED else None,
                    "distribution_channels": 1,
                },
                "pod_products": {
                    "count": len(_get_product_suggestions(article)),
                    "types": _get_product_suggestions(article),
                    "status": "queued" if PRINTIFY_ENABLED else "disabled",
                    "distribution_channels": len(_get_product_suggestions(article)),
                },
                "daily_tips": {
                    "count": len(tips),
                    "status": "ready_for_distribution",
                    "distribution_channels": len(tips) * 5,  # Each tip can go to multiple platforms
                    "sample_tips": [{"title": t.get("title", ""), "content": t.get("content", "")} for t in tips[:3]],
                },
                "short_form_videos": {
                    "script_generated": True,
                    "platforms": ["tiktok", "instagram_reels", "youtube_shorts"],
                    "duration": "15-30 seconds",
                    "script_preview": short_video.get("script", "")[:200],
                    "hashtags": short_video.get("hashtags", []),
                    "distribution_channels": 3,
                },
                "long_form_video": {
                    "script_generated": True,
                    "platform": "youtube",
                    "duration": "3-5 minutes",
                    "chapters": len(long_video.get("chapters", [])),
                    "title": long_video.get("title", ""),
                    "distribution_channels": 1,
                },
                "newsletter_issue": {
                    "status": "ready_to_send",
                    "subject": newsletter.get("subject", ""),
                    "estimated_reach": "100-500 subscribers",
                    "distribution_channels": 1,
                },
                "news_update": {
                    "status": "ready_to_publish",
                    "headline": news_update.get("headline", ""),
                    "priority": news_update.get("priority", "normal"),
                    "distribution_channels": 1,
                },
            },
            "distribution_summary": {
                "total_content_pieces_generated": (
                    1 +  # Blog article
                    (1 if GUMROAD_ENABLED else 0) +  # Ebook
                    (len(_get_product_suggestions(article)) if PRINTIFY_ENABLED else 0) +  # POD products
                    len(tips) +  # Daily tips
                    1 +  # Short video
                    1 +  # Long video
                    1 +  # Newsletter
                    1  # News update
                ),
                "total_distribution_channels": (
                    1 +  # Blog
                    1 +  # Gumroad
                    (len(_get_product_suggestions(article)) if PRINTIFY_ENABLED else 0) +  # Printify
                    (len(tips) * 5) +  # Tips across platforms
                    3 +  # Short video (TikTok, Reels, Shorts)
                    1 +  # YouTube
                    (len(distribution_report.get("social_media", {})) or 0) +  # Social platforms
                    1 +  # Newsletter
                    1  # News update
                ),
                "revenue_potential": {
                    "ebook_revenue": GUMROAD_BASE_PRICE if GUMROAD_ENABLED else 0,
                    "pod_revenue_conservative": (len(_get_product_suggestions(article)) * 5.0) if PRINTIFY_ENABLED else 0,
                    "estimated_total_low": (GUMROAD_BASE_PRICE if GUMROAD_ENABLED else 0) + (len(_get_product_suggestions(article)) * 5.0 if PRINTIFY_ENABLED else 0),
                    "estimated_total_high": (GUMROAD_BASE_PRICE * 10 if GUMROAD_ENABLED else 0) + (len(_get_product_suggestions(article)) * 20.0 if PRINTIFY_ENABLED else 0),
                    "currency": "USD",
                },
            },
            "implementation_checklist": [
                "Review and approve all generated content",
                "Upload short-form video script to TikTok/Reels/Shorts editor",
                "Send newsletter issue to email subscribers",
                "Post daily tips to social media (staggered schedule)",
                "Approve POD product designs on Printify",
                "Schedule YouTube video for editing and publishing",
                "Monitor conversion metrics across all channels",
                "Collect feedback on article usefulness",
                "Update internal links from related content",
                "Plan next content cluster topic based on performance",
            ],
            "next_steps": [
                "1. Review this dashboard and approve content",
                "2. Begin scheduling social posts (1 tip per day)",
                "3. Upload and publish video content",
                "4. Monitor metrics daily for first week",
                "5. Scale top-performing content to more platforms",
            ],
        }

        # Save distribution report
        report_file = f"distribution_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(report_file, "w") as f:
                json.dump(distribution_report, f, indent=2)
            print(f"[DISTRIBUTE][OK] Report saved to {report_file}")
        except Exception as exc:
            print(f"[DISTRIBUTE][WARN] Failed to save distribution report: {exc}")

        # Save monetization report
        monetization_report_file = f"monetization_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(monetization_report_file, "w") as f:
                json.dump(monetization_report, f, indent=2)
            print(f"[MONETIZE][OK] Monetization report saved to {monetization_report_file}")
        except Exception as exc:
            print(f"[MONETIZE][WARN] Failed to save monetization report: {exc}")

        # Save unified distribution plan
        unified_plan_file = f"unified_distribution_plan_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(unified_plan_file, "w") as f:
                json.dump(unified_plan, f, indent=2)
            print(f"[DISTRIBUTE][OK] Unified plan saved to {unified_plan_file}")
        except Exception as exc:
            print(f"[DISTRIBUTE][WARN] Failed to save unified plan: {exc}")

        # Save content dashboard
        dashboard_file = f"content_dashboard_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(dashboard_file, "w") as f:
                json.dump(content_dashboard, f, indent=2)
            print(f"[DASHBOARD][OK] Content dashboard saved to {dashboard_file}")
        except Exception as exc:
            print(f"[DASHBOARD][WARN] Failed to save content dashboard: {exc}")

        # Log summary
        print(f"[DISTRIBUTE][SUMMARY] Successful: {distribution_report['summary']['successful']}, "
              f"Failed: {distribution_report['summary']['failed']}, "
              f"Skipped: {distribution_report['summary']['skipped']}")

        # Log monetization summary
        ebook_status = "CREATED" if monetization_report.get("monetization", {}).get("ebook", {}).get("created") else "NOT CREATED"
        pod_count = len(monetization_report.get("monetization", {}).get("pod_products", {}).get("products", []))
        total_tips = len(_extract_tips_from_article(article))
        print(f"[MONETIZE][SUMMARY] Ebook: {ebook_status}, POD Products Queued: {pod_count}, Daily Tips: {total_tips}")

        # Log distribution summary
        total_channels = content_dashboard.get("distribution_summary", {}).get("total_distribution_channels", 0)
        revenue_low = content_dashboard.get("distribution_summary", {}).get("revenue_potential", {}).get("estimated_total_low", 0)
        revenue_high = content_dashboard.get("distribution_summary", {}).get("revenue_potential", {}).get("estimated_total_high", 0)
        print(f"[DASHBOARD][SUMMARY] Total Channels: {total_channels}, Revenue Potential: ${revenue_low}-${revenue_high}")

        publish_state["distribution_report"] = distribution_report
        publish_state["monetization_report"] = monetization_report
        publish_state["unified_plan"] = unified_plan
        publish_state["content_dashboard"] = content_dashboard


if __name__ == "__main__":
    main()
