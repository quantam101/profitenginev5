#!/usr/bin/env python3
"""ProfitEngine deterministic content factory.

Converts one campaign JSON payload into reusable owned assets without network calls,
paid adapters, account logins, or public posting.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REQUIRED_FIELDS = {
    "campaign_id",
    "campaign_type",
    "owner",
    "approval_required",
    "referral_url",
    "primary_copy",
    "short_copy",
}


def slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return value or "campaign"


def load_campaign(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    missing = sorted(REQUIRED_FIELDS - set(data))
    if missing:
        raise ValueError(f"Missing required campaign fields: {', '.join(missing)}")
    return data


def disclosure(campaign: dict[str, Any]) -> str:
    controls = campaign.get("risk_controls", {})
    if controls.get("requires_referral_disclosure", False):
        return "Disclosure: Referral rewards and eligibility are subject to provider terms."
    return "Disclosure: Review provider terms before participating."


def hashtags(campaign: dict[str, Any]) -> str:
    return " ".join(f"#{str(tag).lstrip('#')}" for tag in campaign.get("hashtags", []))


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def build_book(campaign: dict[str, Any]) -> str:
    return f"""# Chapter 1 — The Small-Step Wealth Habit

Most people do not fail financially because they lack ambition. They fail because the system around them makes starting feel larger than it needs to be.

The first move is not perfection. The first move is motion.

A small, repeatable investing habit is more valuable than a perfect plan that never gets executed. When a person starts small, they lower the psychological barrier. They stop waiting for the perfect income level, the perfect market, or the perfect timing. They begin building an operating rhythm.

## Principle

Small steps create momentum. Momentum creates consistency. Consistency creates optionality.

## Tool Mention

Acorns is one simple tool for people who want a low-friction way to begin saving and investing. Eligible users can review this referral offer:

{campaign['referral_url']}

{disclosure(campaign)}
"""


def build_blog(campaign: dict[str, Any]) -> str:
    return f"""# Small Steps Build Financial Momentum

Saving and investing can feel intimidating when the starting point is small. The practical answer is not to wait until everything is perfect. The practical answer is to build the habit, keep the process simple, and let consistency do part of the work.

Acorns is one option that can help people begin with small, repeatable actions. It is not a guaranteed outcome and it is not a substitute for a personal financial plan, but it can be a useful starting point for people who need a simple way to begin.

## Referral Offer

Eligible new users who join through this referral link can receive a free $5 investment:

{campaign['referral_url']}

As part of the referral program, I may receive a referral reward too.

## Operating Principle

Start small. Stay consistent. Let the habit compound.

{disclosure(campaign)}
"""


def build_video(campaign: dict[str, Any]) -> str:
    return f"""# Short-Form Video Script — 45 Seconds

## Hook

You do not need to start big to start building better money habits.

## Body

Small steps build real momentum. Acorns can make it easier to begin saving and investing in small increments. The goal is not to promise a result. The goal is to build the habit and keep moving.

## Call To Action

Eligible new users can join through my referral link and receive a free $5 investment. I may receive a referral reward too.

## On-Screen Text

Start small. Stay consistent. Let the habit compound.

## Link

{campaign['referral_url']}

## Compliance Line

{disclosure(campaign)}
"""


def build_social(campaign: dict[str, Any]) -> str:
    tags = hashtags(campaign)
    disc = disclosure(campaign)
    return f"""# Platform Social Variants

## LinkedIn / Facebook

{campaign['primary_copy']}

{tags}

## X / Threads

Small steps build real momentum. Acorns can make it easier to start saving and investing in small increments.

Join through my link and eligible users can receive a free $5 investment. I may receive a referral reward too. Terms apply.

{campaign['referral_url']}

{tags}

## Instagram Caption

Start small. Stay consistent. Build the habit.

Acorns can make it easier to begin saving and investing. My referral link includes a free $5 investment for eligible new users, and I may receive a referral reward too.

{campaign['referral_url']}

{disc}

{tags}

## Personal Text Only

{campaign['short_copy']}

{disc}
"""


def build_email(campaign: dict[str, Any]) -> str:
    return f"""Subject: A simple way to start building better money habits

Small steps build real momentum.

I’m sharing Acorns because it can make saving and investing easier to start, even if you are beginning small. The goal is simple: build better habits, put money to work, and keep moving one step at a time.

Eligible new users can join through my link and receive a free $5 investment. As a referral perk, I may receive a reward too.

{campaign['referral_url']}

Start small. Stay consistent. Let the habit compound.

{disclosure(campaign)}
"""


def build_course(campaign: dict[str, Any]) -> str:
    return f"""# Micro-Class Outline — Start Small With Investing Habits

## Lesson 1 — Why Starting Small Works

Objective: reduce friction and create repeatable behavior.

## Lesson 2 — Habit Before Scale

Objective: understand why consistency comes before optimization.

## Lesson 3 — Tool Review

Objective: show how a simple app can support beginner saving and investing behavior without promising results.

Referral resource:
{campaign['referral_url']}

## Lesson 4 — Action Step

Choose one low-friction savings or investing habit and commit to repeating it.

## Required Disclosure

{disclosure(campaign)}
"""


def build_manifest(campaign: dict[str, Any], files: list[str]) -> str:
    manifest = {
        "campaign_id": campaign["campaign_id"],
        "campaign_type": campaign["campaign_type"],
        "owner": campaign["owner"],
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "approval_required_before_publish": bool(campaign["approval_required"]),
        "publication_state": "not_published",
        "generated_files": files,
        "external_runtime_required": False,
        "huggingface_optional": True,
    }
    return json.dumps(manifest, indent=2, ensure_ascii=False)


def generate(campaign_path: Path, output_root: Path) -> Path:
    campaign = load_campaign(campaign_path)
    campaign_dir = output_root / slugify(campaign["campaign_id"])
    outputs = {
        "book/chapter-01.md": build_book(campaign),
        "blog/article.md": build_blog(campaign),
        "video/short-form-45s.md": build_video(campaign),
        "social/platform-variants.md": build_social(campaign),
        "email/newsletter.md": build_email(campaign),
        "course/micro-class-outline.md": build_course(campaign),
    }
    for relative_path, content in outputs.items():
        write(campaign_dir / relative_path, content)
    write(campaign_dir / "manifest.json", build_manifest(campaign, sorted(outputs)))
    return campaign_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate ProfitEngine content assets from a campaign JSON payload.")
    parser.add_argument("--campaign", required=True, type=Path, help="Path to campaign JSON payload")
    parser.add_argument("--output", default=Path("generated-content"), type=Path, help="Output root directory")
    args = parser.parse_args()
    generated_dir = generate(args.campaign, args.output)
    print(f"Generated content pack: {generated_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
