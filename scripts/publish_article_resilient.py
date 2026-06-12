#!/usr/bin/env python3
"""
Resilient ProfitEngine article publisher.

Purpose:
- Preserve the existing scripts/publish_article.py implementation.
- Add a deterministic article fallback when all LLM providers fail.
- Make GitHub Pages publication mandatory instead of silently passing after failure.
- Keep verify-only mode aligned with the current provider chain: Groq -> Gemini -> HuggingFace.
- Optimize affiliate output so posts monetize without becoming link catalogs.
- Attach a revenue execution brief so each article becomes a business action trigger.
"""
from __future__ import annotations

import os
import re
import sys
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Tuple
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import httpx

import publish_article as publisher

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


def _verify_ai_provider_hf_aware() -> bool:
    """Verify the active provider chain without falsely failing HF-only setups."""
    try:
        if _ORIGINAL_VERIFY_AI_PROVIDER():
            return True
    except Exception as exc:
        print(f"[VERIFY][WARN] Default AI provider verification raised: {exc}")

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

    print("[VERIFY][FAIL] AI provider: no usable Groq, Gemini, or HuggingFace provider verified")
    return False


def main() -> None:
    publisher._verify_ai_provider = _verify_ai_provider_hf_aware  # type: ignore[attr-defined]
    publisher._affiliate_map = _limited_affiliate_map  # type: ignore[attr-defined]
    publisher._recommended_tools_section = _recommended_tools_section  # type: ignore[attr-defined]
    publisher._inject_affiliates = _optimized_inject_affiliates  # type: ignore[attr-defined]

    original_generate_article = publisher.generate_article
    original_publish_github = publisher.publish_github
    publish_state: Dict[str, str] = {"canonical_url": ""}

    def generate_article_with_fallback(topic: str) -> Dict[str, Any]:
        try:
            article = original_generate_article(topic)
        except SystemExit as exc:
            print(f"[AI][WARN] Provider generation exited: {exc}. Using deterministic article fallback.")
            article = _deterministic_article(topic)
        except Exception as exc:
            print(f"[AI][WARN] Provider generation failed: {exc}. Using deterministic article fallback.")
            article = _deterministic_article(topic)
        return _attach_revenue_action_brief(topic, article)

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


if __name__ == "__main__":
    main()
