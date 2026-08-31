"""
White-Label AI Chatbot Builder — Income Stream 1
=================================================
Builds and bills custom AI chatbots for local businesses.
Zero dependency on paid platforms — uses free/open-source stack.

Bot creation tiers (in priority order):
  1. Botpress Cloud  — free tier, visual builder, multi-channel
                       (Web, WhatsApp, Slack, Telegram)
  2. OpenAssistantGPT pattern — BYOK using our own Anthropic key,
                       deployed as a widget on our runtime server
  3. Custom ProfitEngine widget — always available, zero cost

Revenue model (we charge the client, not the platform):
  Starter:    $500 setup  + $99/mo  retainer
  Growth:     $1,000 setup + $199/mo retainer
  Enterprise: $1,500 setup + $299/mo retainer

Environment variables:
  BOTPRESS_TOKEN     — app.botpress.cloud → Account → Personal Access Tokens
  BOTPRESS_WORKSPACE — workspace ID (shown in app.botpress.cloud URL)
  ANTHROPIC_API_KEY  — already set (used for OpenAssistantGPT fallback)
  STRIPE_SECRET_KEY  — already set
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("ChatbotBuilder")

# ── Pricing tiers ──────────────────────────────────────────────────────────────

TIERS: Dict[str, Dict[str, Any]] = {
    "starter": {
        "name":           "Starter Chatbot",
        "setup_cents":    50000,
        "retainer_cents":  9900,
        "description":    "AI chatbot trained on your website — answers FAQs 24/7.",
        "channels":       ["web"],
        "features": [
            "Trained on your website content",
            "Embeddable chat widget",
            "Lead capture (name + email)",
            "Monthly performance report",
        ],
    },
    "growth": {
        "name":           "Growth Chatbot",
        "setup_cents":    100000,
        "retainer_cents":  19900,
        "description":    "Multi-channel AI agent with booking and CRM integration.",
        "channels":       ["web", "whatsapp", "telegram"],
        "features": [
            "Everything in Starter",
            "WhatsApp + Telegram channels",
            "Appointment scheduling",
            "CRM webhook integration",
            "Monthly optimization call",
        ],
    },
    "enterprise": {
        "name":           "Enterprise Chatbot",
        "setup_cents":    150000,
        "retainer_cents":  29900,
        "description":    "Full-stack AI support agent with analytics and multi-location.",
        "channels":       ["web", "whatsapp", "telegram", "slack"],
        "features": [
            "Everything in Growth",
            "Slack + SMS channels",
            "Multi-location support",
            "Advanced analytics",
            "Dedicated account manager",
        ],
    },
}


# ── Client record ──────────────────────────────────────────────────────────────

@dataclass
class ChatbotClient:
    business_name:      str
    contact_email:      str
    website_url:        str
    niche:              str
    tier:               str = "starter"
    bot_platform:       str = ""       # "botpress" | "openassistant" | "custom"
    bot_id:             str = ""
    embed_code:         str = ""
    stripe_setup_url:   str = ""
    stripe_sub_url:     str = ""
    onboarding_sent:    bool = False
    created_at:         str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class BuildResult:
    ok:               bool
    client:           Optional[ChatbotClient] = None
    bot_platform:     str = ""
    bot_id:           str = ""
    embed_code:       str = ""
    setup_url:        str = ""
    subscription_url: str = ""
    error:            str = ""


# ── Website scraper ────────────────────────────────────────────────────────────

def _scrape_text(url: str, max_chars: int = 8000) -> str:
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; ProfitEngine/5.0)"},
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read().decode(errors="replace")
        text = re.sub(r"<style[^>]*>.*?</style>", " ", html, flags=re.DOTALL)
        text = re.sub(r"<script[^>]*>.*?</script>", " ", text, flags=re.DOTALL)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:max_chars]
    except Exception as exc:
        logger.warning(f"[ChatbotBuilder] Scrape failed for {url}: {exc}")
        return ""


def _extract_faqs(business_name: str, niche: str, website_text: str) -> str:
    try:
        from runtime.inference_cascade import infer
        system = (
            "You are a knowledge base extractor. Output 10 FAQ pairs in this format:\n"
            "Q: [question]\nA: [answer]\n\n"
            "Focus on: services, pricing, hours, service area, contact info."
        )
        prompt = (
            f"Business: {business_name} ({niche})\n\n"
            f"Website text:\n{website_text[:4000]}\n\nExtract 10 FAQs:"
        )
        faq, _ = infer(system, prompt, max_tokens=800)
        if not faq.startswith("INFERENCE_STUB") and len(faq) > 100:
            return faq
    except Exception:
        pass
    return (
        f"Q: What services does {business_name} offer?\n"
        f"A: {business_name} provides professional {niche} services in your area.\n\n"
        f"Q: How do I contact {business_name}?\n"
        f"A: Reach us through our website or call during business hours.\n\n"
        f"Q: What areas does {business_name} serve?\n"
        f"A: We serve local areas — contact us to confirm availability."
    )


# ── Platform 1: Botpress Cloud (free tier) ─────────────────────────────────────

_BP_BASE = "https://api.botpress.cloud/v1"


def _bp_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {os.environ.get('BOTPRESS_TOKEN', '')}",
        "Content-Type":  "application/json",
    }


def _bp_request(method: str, path: str, body: Optional[Dict] = None) -> Dict[str, Any]:
    token = os.environ.get("BOTPRESS_TOKEN", "").strip()
    if not token:
        return {"error": "BOTPRESS_TOKEN not set"}
    url  = f"{_BP_BASE}/{path}"
    data = json.dumps(body or {}).encode()
    req  = urllib.request.Request(url, data=data if method != "GET" else None,
                                  headers=_bp_headers(), method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as exc:
        return {"error": f"HTTP {exc.code}: {exc.read().decode(errors='replace')[:200]}"}
    except Exception as exc:
        return {"error": str(exc)}


def _create_botpress_bot(business_name: str, niche: str, faq_text: str) -> Dict[str, Any]:
    """
    Create a Botpress Cloud bot, upload knowledge base, return embed code.
    Free tier allows unlimited bots with generous message quota.
    """
    workspace = os.environ.get("BOTPRESS_WORKSPACE", "").strip()

    # Create bot
    safe_name = re.sub(r"[^a-z0-9-]", "-", business_name.lower())[:40]
    resp = _bp_request("POST", "admin/bots", {
        "name":        f"{business_name} AI Assistant",
        "handle":      f"{safe_name}-assistant",
        "description": f"AI customer service bot for {business_name} ({niche})",
    })

    if "error" in resp:
        return {"error": resp["error"]}

    bot_id = resp.get("bot", {}).get("id", "")
    if not bot_id:
        return {"error": "Botpress did not return a bot ID"}

    # Upload knowledge base
    _bp_request("POST", f"bots/{bot_id}/knowledgebases", {
        "name":    "Website FAQ",
        "content": faq_text,
    })

    # Webchat embed
    embed_code = (
        f'<script src="https://cdn.botpress.cloud/webchat/v2.2/inject.js"></script>\n'
        f'<script>\n'
        f'  window.botpressWebChat.init({{\n'
        f'    botId: "{bot_id}",\n'
        f'    hostUrl: "https://cdn.botpress.cloud/webchat/v2.2",\n'
        f'    messagingUrl: "https://messaging.botpress.cloud",\n'
        f'    clientId: "{bot_id}",\n'
        f'    lazySocket: true,\n'
        f'    botName: "{business_name} AI Assistant",\n'
        f'    backgroundColor: "#1a1a2e",\n'
        f'    textColorOnBackground: "#ffffff",\n'
        f'  }});\n'
        f'</script>'
    )

    logger.info(f"[ChatbotBuilder] Botpress bot created: {bot_id}")
    return {
        "platform":   "botpress",
        "bot_id":     bot_id,
        "embed_code": embed_code,
        "dashboard":  f"https://app.botpress.cloud/workspaces/{workspace}/bots/{bot_id}",
    }


# ── Platform 2: OpenAssistantGPT pattern (BYOK, zero platform cost) ───────────

def _create_openassistant_bot(
    business_name: str,
    niche: str,
    faq_text: str,
) -> Dict[str, Any]:
    """
    OpenAssistantGPT pattern: uses our own Anthropic key, served via our runtime.
    Falls back to the Render runtime; override with RUNTIME_API_URL.
    Cost: only Anthropic token usage (~$0.001 per conversation).
    """
    # Generate a stable bot ID from business name
    bot_id = hashlib.sha256(f"{business_name}:{niche}".encode()).hexdigest()[:16]

    widget_base = os.environ.get("APP_PUBLIC_URL") or os.environ.get("NEXT_PUBLIC_SITE_URL") or os.environ.get("PUBLIC_SITE_URL")
    if not widget_base:
        widget_base = f"https://app.{os.environ.get('SITE_DOMAIN', 'alreadyherellc.com')}"
    widget_base = widget_base.rstrip("/")
    runtime_url = widget_base

    embed_code = (
        f'<!-- {business_name} AI Assistant - Powered by Already Here LLC -->\n'
        f'<script>\n'
        f'  (function() {{\n'
        f'    var s = document.createElement("script");\n'
        f'    s.src = "{runtime_url}/api/widget.js";\n'
        f'    s.setAttribute("data-bot-id", "{bot_id}");\n'
        f'    s.setAttribute("data-name", "{business_name} AI");\n'
        f'    s.setAttribute("data-niche", "{niche}");\n'
        f'    s.setAttribute("data-color", "#1a1a2e");\n'
        f'    s.async = true;\n'
        f'    document.head.appendChild(s);\n'
        f'  }})();\n'
        f'</script>'
    )

    # Store bot config in runtime for widget serving
    config_path = os.path.join(
        os.environ.get("PROFITENGINE_CORE_DIR", ".core_mesh_data"),
        "chatbots",
        f"{bot_id}.json",
    )
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, "w") as f:
        json.dump({
            "bot_id":        bot_id,
            "business_name": business_name,
            "niche":         niche,
            "faq":           faq_text,
            "system_prompt": (
                f"You are a helpful AI assistant for {business_name}, a {niche} business. "
                "Answer customer questions clearly and concisely. "
                "Capture their name and email if they want a quote or appointment. "
                "If unsure, say: 'Let me connect you with our team.'"
            ),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }, f, indent=2)

    logger.info(f"[ChatbotBuilder] OpenAssistant bot created: {bot_id}")
    return {
        "platform":   "openassistant",
        "bot_id":     bot_id,
        "embed_code": embed_code,
        "config":     config_path,
    }


# ── Platform 3: Custom widget fallback ────────────────────────────────────────

def _create_custom_widget(business_name: str, niche: str) -> Dict[str, Any]:
    bot_id     = hashlib.md5(f"{business_name}{niche}".encode(), usedforsecurity=False).hexdigest()[:12]
    widget_base = os.environ.get("APP_PUBLIC_URL") or os.environ.get("NEXT_PUBLIC_SITE_URL") or os.environ.get("PUBLIC_SITE_URL")
    if not widget_base:
        widget_base = f"https://app.{os.environ.get('SITE_DOMAIN', 'alreadyherellc.com')}"
    widget_base = widget_base.rstrip("/")
    runtime_url = widget_base
    embed_code = (
        f'<script src="{runtime_url}/api/widget.js" '
        f'data-bot="{bot_id}" '
        f'data-name="{business_name}" async></script>'
    )
    return {"platform": "custom", "bot_id": bot_id, "embed_code": embed_code}


# ── Stripe payment links ────────────────────────────────────────────────────────

def _stripe_payment_link(price_cents: int, description: str, mode: str = "payment") -> str:
    key = os.environ.get("STRIPE_SECRET_KEY", "").strip()
    if not key:
        return ""
    try:
        price_data = urllib.parse.urlencode({
            "unit_amount":        str(price_cents),
            "currency":           "usd",
            "product_data[name]": description,
            **( {"recurring[interval]": "month"} if mode == "subscription" else {} ),
        }).encode()
        price_req = urllib.request.Request(
            "https://api.stripe.com/v1/prices", data=price_data, method="POST",
            headers={"Authorization": f"Bearer {key}",
                     "Content-Type": "application/x-www-form-urlencoded"},
        )
        price_id = json.loads(urllib.request.urlopen(price_req, timeout=10).read()).get("id", "")
        if not price_id:
            return ""
        link_data = urllib.parse.urlencode({
            "line_items[0][price]":    price_id,
            "line_items[0][quantity]": "1",
        }).encode()
        link_req = urllib.request.Request(
            "https://api.stripe.com/v1/payment_links", data=link_data, method="POST",
            headers={"Authorization": f"Bearer {key}",
                     "Content-Type": "application/x-www-form-urlencoded"},
        )
        return json.loads(urllib.request.urlopen(link_req, timeout=10).read()).get("url", "")
    except Exception as exc:
        logger.warning(f"[ChatbotBuilder] Stripe link failed: {exc}")
        return ""


# ── Onboarding email ────────────────────────────────────────────────────────────

def _send_onboarding_email(client: ChatbotClient, tier_cfg: Dict[str, Any]) -> bool:
    try:
        from pipeline.smtp_dispatch import send_batch
        platform_note = {
            "botpress":      "Built on Botpress Cloud — supports Web, WhatsApp, and Telegram.",
            "openassistant": "Powered by Claude AI — hosted on our servers, no third-party limits.",
            "custom":        "Hosted on Already Here LLC servers — always available.",
        }.get(client.bot_platform, "")

        body = f"""Hi,

Your AI chatbot for {client.business_name} is live.

PLATFORM: {client.bot_platform.title()} — {platform_note}

EMBED CODE (paste before </body> on your website):
──────────────────────────────────────────────────
{client.embed_code}
──────────────────────────────────────────────────

NEXT STEPS:
1. Paste the embed code into your website
2. Complete setup payment: {client.stripe_setup_url or 'Contact us to complete payment'}
3. Activate monthly retainer: {client.stripe_sub_url or 'Contact us to set up billing'}

Your chatbot is trained on your website FAQs and answers customer
questions 24/7 — capturing leads while you sleep.

{os.environ.get('OUTREACH_SENDER_NAME', 'Already Here LLC Team')}
{os.environ.get('OUTREACH_COMPANY', 'Already Here LLC')}
https://alreadyherellc.com
"""
        send_batch([{"email": client.contact_email, "name": client.business_name}],
                   f"Your AI Chatbot Is Ready — {client.business_name}", body)
        return True
    except Exception as exc:
        logger.warning(f"[ChatbotBuilder] Email failed: {exc}")
        return False


# ── Main builder ────────────────────────────────────────────────────────────────

def build_chatbot(
    business_name: str,
    contact_email: str,
    website_url:   str,
    niche:         str,
    tier:          str = "starter",
    send_email:    bool = True,
) -> BuildResult:
    """
    Full pipeline:
      1. Scrape website → extract FAQs
      2. Create bot: Botpress → OpenAssistantGPT → custom widget
      3. Generate Stripe setup + retainer payment links
      4. Send onboarding email with embed code
    """
    tier_cfg = TIERS.get(tier, TIERS["starter"])
    logger.info(f"[ChatbotBuilder] Building {tier_cfg['name']} for {business_name}")

    website_text = _scrape_text(website_url)
    faq_text     = _extract_faqs(business_name, niche, website_text)

    # Try platforms in order
    bot_result: Dict[str, Any] = {}

    if os.environ.get("BOTPRESS_TOKEN", "").strip():
        bot_result = _create_botpress_bot(business_name, niche, faq_text)
        if "error" in bot_result:
            logger.warning(f"[ChatbotBuilder] Botpress failed: {bot_result['error']} — trying OpenAssistant")
            bot_result = {}

    if not bot_result and os.environ.get("ANTHROPIC_API_KEY", "").strip():
        bot_result = _create_openassistant_bot(business_name, niche, faq_text)

    if not bot_result:
        bot_result = _create_custom_widget(business_name, niche)

    platform   = bot_result.get("platform", "custom")
    bot_id     = bot_result.get("bot_id", "")
    embed_code = bot_result.get("embed_code", "")

    setup_url = _stripe_payment_link(
        tier_cfg["setup_cents"],
        f"{tier_cfg['name']} Setup — {business_name}",
        mode="payment",
    )
    sub_url = _stripe_payment_link(
        tier_cfg["retainer_cents"],
        f"{tier_cfg['name']} Monthly Retainer — {business_name}",
        mode="subscription",
    )

    client = ChatbotClient(
        business_name    = business_name,
        contact_email    = contact_email,
        website_url      = website_url,
        niche            = niche,
        tier             = tier,
        bot_platform     = platform,
        bot_id           = bot_id,
        embed_code       = embed_code,
        stripe_setup_url = setup_url,
        stripe_sub_url   = sub_url,
    )

    if send_email and contact_email:
        client.onboarding_sent = _send_onboarding_email(client, tier_cfg)

    logger.info(f"[ChatbotBuilder] Done — platform={platform} bot={bot_id}")
    return BuildResult(
        ok               = bool(bot_id),
        client           = client,
        bot_platform     = platform,
        bot_id           = bot_id,
        embed_code       = embed_code,
        setup_url        = setup_url,
        subscription_url = sub_url,
    )


# ── Revenue summary ────────────────────────────────────────────────────────────

def revenue_pipeline_summary() -> Dict[str, Any]:
    key = os.environ.get("STRIPE_SECRET_KEY", "").strip()
    if not key:
        return {"ok": False, "error": "STRIPE_SECRET_KEY not set"}
    try:
        req = urllib.request.Request(
            "https://api.stripe.com/v1/subscriptions?status=active&limit=100",
            headers={"Authorization": f"Bearer {key}"},
        )
        resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
        subs = resp.get("data", [])
        mrr  = sum(s.get("plan", {}).get("amount", 0) for s in subs)
        return {
            "ok":              True,
            "active_subs":     len(subs),
            "chatbot_mrr_usd": round(mrr / 100, 2),
            "platform_stack":  ["botpress", "openassistant", "custom-widget"],
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
