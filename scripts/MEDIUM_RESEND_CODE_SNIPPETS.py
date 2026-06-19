#!/usr/bin/env python3
"""
Medium & Resend Integration Code Snippets
Quick reference for using new publishing functions
"""

from priority_publishers import (
    publish_to_medium,
    publish_beehiiv_weekly_digest,
    publish_to_resend_email,
    publish_to_priority_platforms,
    generate_priority_report
)
import json


# ─────────────────────────────────────────────────────────────────────────────
# EXAMPLE 1: Publish Single Article to Medium
# ─────────────────────────────────────────────────────────────────────────────

def example_publish_to_medium():
    """Publish an article to Medium only"""

    article = {
        "title": "Building Scalable APIs with Cloudflare Workers",
        "body": """
# Building Scalable APIs

## Problem
Service businesses struggle with expensive API infrastructure.

## Solution
Cloudflare Workers provides serverless edge computing.

## Implementation
Deploy a simple Worker to handle incoming requests.
""",
        "tags": ["api", "cloudflare", "serverless"],
        "canonical_url": "https://quantam101.github.io/posts/cloudflare-api",
    }

    result = publish_to_medium(article)

    if result:
        print(f"Published to Medium: {result}")
    else:
        print("Failed to publish to Medium")


# ─────────────────────────────────────────────────────────────────────────────
# EXAMPLE 2: Publish to All Priority Platforms (including Medium & Resend)
# ─────────────────────────────────────────────────────────────────────────────

def example_publish_everywhere():
    """Publish article to all platforms at once"""

    article = {
        "title": "Zero-Cost Business Automation with Google Workspace",
        "body": """
# Automation on a Budget

We showed how to use Google Forms + Sheets + Apps Script to build workflows
without monthly costs. Already Here LLC can help you set this up.

## Zero-Cost Path
Use the free tier of Google Workspace (Forms, Sheets, Apps Script).

## Next Steps
Book a consultation with Already Here LLC for your specific use case.
""",
        "meta_description": "Learn cost-free automation using Google Workspace",
        "tags": ["automation", "google", "forms", "free"],
        "canonical_url": "https://quantam101.github.io/posts/google-automation",
    }

    # Publish to all platforms including Medium and Resend email
    results = publish_to_priority_platforms(article, include_email=True)

    # Generate report with reach and revenue impact
    report = generate_priority_report(article, results)

    print(json.dumps(report, indent=2))

    return results


# ─────────────────────────────────────────────────────────────────────────────
# EXAMPLE 3: Publish Weekly Digest to Beehiiv
# ─────────────────────────────────────────────────────────────────────────────

def example_weekly_digest():
    """Compile week's articles into a single Beehiiv digest"""

    articles = [
        {
            "title": "Article 1: API Best Practices",
            "meta_description": "Essential API design patterns for small businesses",
            "canonical_url": "https://quantam101.github.io/posts/api-patterns",
        },
        {
            "title": "Article 2: Forms to Automation",
            "meta_description": "Convert your intake forms into automated workflows",
            "canonical_url": "https://quantam101.github.io/posts/forms-automation",
        },
        {
            "title": "Article 3: CRM Setup Guide",
            "meta_description": "Free CRM workflows for service businesses",
            "canonical_url": "https://quantam101.github.io/posts/crm-setup",
        },
    ]

    digest_result = publish_beehiiv_weekly_digest(articles)

    if digest_result:
        print(f"Weekly digest published: {digest_result}")
        return True
    else:
        print("Failed to publish digest")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# EXAMPLE 4: Send Email via Resend
# ─────────────────────────────────────────────────────────────────────────────

def example_send_email():
    """Send an article as email via Resend"""

    article = {
        "title": "Your Weekly Tech Digest",
        "body": """
# This Week's Top Articles

We've published 3 new articles on automation, APIs, and CRM workflows.

Check them all out on our website.
""",
        "meta_description": "Weekly roundup of technical content",
    }

    # Queue email for later sending (send_now=False)
    # Or send immediately to audience (send_now=True if RESEND_AUDIENCE_ID set)
    result = publish_to_resend_email(article, send_now=False)

    if result:
        print(f"Email queued: {result}")
    else:
        print("Failed to queue email")


# ─────────────────────────────────────────────────────────────────────────────
# EXAMPLE 5: Selective Publishing (Skip Email for Draft Articles)
# ─────────────────────────────────────────────────────────────────────────────

def example_skip_email_for_draft():
    """Publish to platforms but skip email for draft articles"""

    article = {
        "title": "Draft: Advanced CloudFlare Techniques (WIP)",
        "body": "Still writing this one...",
        "tags": ["cloudflare", "advanced"],
        "canonical_url": "https://quantam101.github.io/posts/cloudflare-advanced",
    }

    # Skip email distribution for articles still in development
    results = publish_to_priority_platforms(article, include_email=False)

    print(f"Published to {len([r for r in results.values() if r])} platforms (email skipped)")


# ─────────────────────────────────────────────────────────────────────────────
# EXAMPLE 6: Check Platform Coverage
# ─────────────────────────────────────────────────────────────────────────────

def example_check_coverage():
    """See which platforms are configured and ready"""

    import os

    platforms = {
        "Dev.to": os.getenv("DEVTO_API_KEY"),
        "Hashnode": os.getenv("HASHNODE_API_KEY") and os.getenv("HASHNODE_PUBLICATION_ID"),
        "Medium": os.getenv("MEDIUM_API_KEY") and os.getenv("MEDIUM_AUTHOR_ID"),
        "Beehiiv": os.getenv("BEEHIIV_API_KEY"),
        "Resend": os.getenv("RESEND_API_KEY") and os.getenv("RESEND_AUDIENCE_ID"),
        "Telegram": os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID"),
    }

    print("\n=== Platform Configuration Status ===\n")
    for platform, configured in platforms.items():
        status = "✓ Ready" if configured else "✗ Not configured"
        print(f"{platform:15} {status}")

    return platforms


# ─────────────────────────────────────────────────────────────────────────────
# ENVIRONMENT SETUP
# ─────────────────────────────────────────────────────────────────────────────

"""
Required environment variables for full integration:

DEVTO_API_KEY                 = from https://dev.to/settings/account
HASHNODE_API_KEY              = from https://hashnode.com/settings/api
HASHNODE_PUBLICATION_ID       = your publication ID
MEDIUM_API_KEY                = from https://medium.com/settings/security
MEDIUM_AUTHOR_ID              = from curl -H "Authorization: Bearer TOKEN" https://api.medium.com/v1/me
BEEHIIV_API_KEY               = from https://beehiiv.com/settings/api-keys
BEEHIIV_PUBLICATION_ID        = your publication ID
RESEND_API_KEY                = from https://resend.com/api-keys
RESEND_AUDIENCE_ID            = from https://resend.com/audiences
YOUTUBE_CLIENT_ID             = from Google Cloud Console
YOUTUBE_CLIENT_SECRET         = from Google Cloud Console
YOUTUBE_REFRESH_TOKEN         = from OAuth flow
TELEGRAM_BOT_TOKEN            = from @BotFather on Telegram
TELEGRAM_CHAT_ID              = your chat ID

Setup:
-------

1. Medium:
   export MEDIUM_API_KEY="<token>"
   export MEDIUM_AUTHOR_ID="<id>"

2. Resend:
   export RESEND_API_KEY="re_<key>"
   export RESEND_AUDIENCE_ID="<id>"

3. Beehiiv:
   export BEEHIIV_API_KEY="<key>"
   export BEEHIIV_PUBLICATION_ID="<id>"
"""


if __name__ == "__main__":
    print("Medium & Resend Integration Examples\n")

    # Check which platforms are ready
    example_check_coverage()

    # Uncomment to run examples:
    # example_publish_to_medium()
    # example_publish_everywhere()
    # example_weekly_digest()
    # example_send_email()
    # example_skip_email_for_draft()
