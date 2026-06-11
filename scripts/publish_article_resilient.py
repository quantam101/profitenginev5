#!/usr/bin/env python3
"""
Resilient ProfitEngine article publisher.

Purpose:
- Preserve the existing scripts/publish_article.py implementation.
- Add a deterministic article fallback when all LLM providers fail.
- Make GitHub Pages publication mandatory instead of silently passing after failure.
- Keep verify-only mode aligned with the current provider chain: Groq -> Gemini -> HuggingFace.
"""
from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from typing import Any, Callable, Dict

import httpx

import publish_article as publisher

_ORIGINAL_VERIFY_AI_PROVIDER: Callable[[], bool] = publisher._verify_ai_provider  # type: ignore[attr-defined]


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

    original_generate_article = publisher.generate_article
    original_publish_github = publisher.publish_github
    publish_state: Dict[str, str] = {"canonical_url": ""}

    def generate_article_with_fallback(topic: str) -> Dict[str, Any]:
        try:
            return original_generate_article(topic)
        except SystemExit as exc:
            print(f"[AI][WARN] Provider generation exited: {exc}. Using deterministic article fallback.")
            return _deterministic_article(topic)
        except Exception as exc:
            print(f"[AI][WARN] Provider generation failed: {exc}. Using deterministic article fallback.")
            return _deterministic_article(topic)

    def publish_github_strict(filename: str, content: str, commit_msg: str) -> str:
        url = original_publish_github(filename, content, commit_msg)
        publish_state["canonical_url"] = url
        return url

    publisher.generate_article = generate_article_with_fallback  # type: ignore[assignment]
    publisher.publish_github = publish_github_strict  # type: ignore[assignment]

    started = datetime.now(timezone.utc).isoformat()
    print(f"[RESILIENT] Strict publisher started at {started}")
    publisher.main()

    if not getattr(publisher, "VERIFY_ONLY", False) and not publish_state["canonical_url"]:
        sys.exit("[PUBLISH][FAIL] No GitHub Pages canonical URL was produced. Treating as failed publish.")

    if publish_state["canonical_url"]:
        print(f"[PUBLISH][OK] Strict publish verified: {publish_state['canonical_url']}")


if __name__ == "__main__":
    main()
