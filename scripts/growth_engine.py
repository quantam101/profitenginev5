#!/usr/bin/env python3
"""Weekly growth engine — SEO content ideas, lead tracking, revenue actions.

Runs on GitHub Actions every Monday. Outputs a growth digest to GitHub Issues.
Env: GITHUB_TOKEN, GITHUB_REPO, STRIPE_SECRET_KEY
"""

import os
import json
import datetime
import urllib.request
import urllib.error
import urllib.parse

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "quantam101/profitenginev5")
STRIPE_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
RUN_MODE = os.environ.get("RUN_MODE", "full")

# High-intent keywords for TokenForge + ProfitEngine
CONTENT_TOPICS = [
    ("reduce openai api costs", "tutorial", "How to Cut Your OpenAI API Bill by 60% Without Changing Your Model"),
    ("llm token optimization", "guide", "The Complete Guide to LLM Token Optimization in 2026"),
    ("anthropic api cost", "comparison", "Claude vs GPT-4o API Costs: Optimization Strategies That Actually Work"),
    ("prompt compression python", "tutorial", "Prompt Compression in Python: Shave 40% Off Every LLM Request"),
    ("gemini api pricing", "comparison", "Gemini 2.5 Pro vs Flash: When to Use Each and How to Save More"),
    ("openai token limit", "guide", "Hitting OpenAI Token Limits? Here's the Engineering Fix"),
    ("ai api cost management", "guide", "AI API Cost Management: The FinOps Playbook for LLM Teams"),
    ("semantic cache llm", "tutorial", "Semantic Caching for LLMs: Cut Duplicate Costs by 30%"),
    ("llm proxy server", "comparison", "Top LLM Proxy Servers in 2026: TokenForge vs LiteLLM vs PortKey"),
    ("reduce ai inference cost", "guide", "10 Ways to Reduce AI Inference Costs in Production"),
]

# Communities to share new content (manual — these are just reminders, not automated)
SHARE_CHANNELS = [
    "r/MachineLearning (weekly threads)",
    "r/LocalLLaMA (usage posts)",
    "Hacker News (Show HN: ...)",
    "dev.to (cross-post with canonical link)",
    "IndieHackers (product page + updates)",
    "LinkedIn (company page post)",
    "X/Twitter (@tokenforge handle)",
]

# Revenue growth levers ranked by impact/effort
GROWTH_LEVERS = [
    ("SSL fix on api.alreadyherellc.com", "CRITICAL", "Unblocks ALL TokenForge paid conversions"),
    ("Annual plan upsell", "HIGH", "Enterprise annual = $5,988/yr upfront cash"),
    ("Affiliate program launch", "HIGH", "30% recurring — viral distribution"),
    ("Show HN post for TokenForge", "HIGH", "HN front page = 500-2000 signups spike"),
    ("Enterprise cold outreach", "HIGH", "5 enterprise closes = $24,950 annual"),
    ("RapidAPI marketplace listing", "MEDIUM", "Passive inbound from 4M+ developers"),
    ("ProductHunt launch", "MEDIUM", "Badge + traffic spike + PR"),
    ("Dev.to content series", "MEDIUM", "SEO compound interest over 60-90 days"),
    ("YouTube tutorial (TokenForge)", "MEDIUM", "30% of developers discover SaaS via YouTube"),
    ("Discord community", "LOW", "Community moat, longer-term retention"),
]


def stripe_mrr() -> float:
    if not (STRIPE_KEY and STRIPE_KEY.startswith("sk_")):
        return 0.0
    try:
        req = urllib.request.Request(
            "https://api.stripe.com/v1/subscriptions?status=active&limit=100",
            headers={"Authorization": f"Bearer {STRIPE_KEY}"},
        )
        data = json.loads(urllib.request.urlopen(req, timeout=10).read())
        return sum(s.get("plan", {}).get("amount", 0) for s in data.get("data", [])) / 100
    except Exception:
        return 0.0


def post_github_issue(title: str, body: str, labels: list[str]) -> str:
    if not GITHUB_TOKEN:
        print(body)
        return ""
    owner, repo = GITHUB_REPO.split("/")
    req = urllib.request.Request(
        f"https://api.github.com/repos/{owner}/{repo}/issues",
        data=json.dumps({"title": title, "body": body, "labels": labels}).encode(),
        headers={
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    result = json.loads(urllib.request.urlopen(req, timeout=10).read())
    return result.get("html_url", "")


def build_weekly_digest() -> str:
    week = datetime.datetime.utcnow().strftime("Week of %B %d, %Y")
    mrr = stripe_mrr()
    target = 25000
    mrr_to_target = max(0, target - mrr * 12)

    # Pick 3 content topics to write this week (rotate by week number)
    week_num = datetime.datetime.utcnow().isocalendar()[1]
    week_topics = CONTENT_TOPICS[(week_num * 3) % len(CONTENT_TOPICS) : (week_num * 3) % len(CONTENT_TOPICS) + 3]

    lines = [
        f"## 📈 Weekly Growth Digest — {week}",
        "",
        "### Revenue Pulse",
        f"- Current MRR: **${mrr:,.2f}/mo**",
        f"- Annualized: **${mrr * 12:,.2f}**",
        f"- Gap to $25K target: **${mrr_to_target:,.2f}**",
        f"- {'✅ On track' if mrr * 12 >= target * 0.5 else '⚡ Needs acceleration'}",
        "",
        "### This Week's Content Targets",
        "",
        "Write + publish these 3 posts to the ProfitEngine blog:",
        "",
    ]

    for kw, type_, title in week_topics:
        lines.append(f"- [ ] **[{type_.upper()}]** {title}")
        lines.append(f"  - Target keyword: `{kw}`")

    lines += [
        "",
        "### Growth Levers (ranked)",
        "",
    ]
    for lever, priority, detail in GROWTH_LEVERS:
        icon = "🔴" if priority == "CRITICAL" else "🟠" if priority == "HIGH" else "🟡" if priority == "MEDIUM" else "⚪"
        lines.append(f"- {icon} **{lever}** — {detail}")

    lines += [
        "",
        "### Share This Week's Content",
        "",
        "After publishing, cross-post to:",
        "",
    ]
    for ch in SHARE_CHANNELS:
        lines.append(f"- [ ] {ch}")

    lines += [
        "",
        "### 5-Enterprise-Closes Sprint",
        "",
        "Each enterprise close = $499/mo = $5,988/yr. 5 closes = $29,940/yr = **goal achieved**.",
        "",
        "**Outreach targets this week:**",
        "- [ ] Search LinkedIn for 'Head of AI' or 'ML Platform' at Series B+ startups",
        "- [ ] Find 3 dev.to / HN threads complaining about high OpenAI bills → reply with ROI calc",
        "- [ ] DM 5 IndieHackers building LLM products → offer free Pro trial",
        "- [ ] Post in r/MachineLearning weekly thread with TokenForge savings example",
        "- [ ] Email enterprise@tokenforge.io sequence to last week's leads",
        "",
        "### Affiliate Activation",
        "",
        "- [ ] Reach out to 5 AI/dev YouTubers (under 50K subs) for affiliate deals",
        "- [ ] Post in dev Discord servers: 'earn 30% recurring, no cap'",
        "- [ ] Add affiliate CTA to TokenForge email confirmation",
        "",
        "---",
        "_Auto-generated by growth_engine.py · Runs every Monday 09:00 UTC_",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    print("Running growth engine...")
    digest = build_weekly_digest()

    week_label = datetime.datetime.utcnow().strftime("%Y-W%V")
    title = f"📈 Growth Digest — {week_label}"
    url = post_github_issue(title, digest, ["growth", "weekly-digest"])
    if url:
        print(f"Created: {url}")
    else:
        print(digest)
