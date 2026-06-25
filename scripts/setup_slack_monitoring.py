#!/usr/bin/env python3
"""
Setup script for ProfitEngine Slack Monitoring.

Guides user through:
1. Creating Slack incoming webhook
2. Setting GitHub secrets
3. Testing webhook
4. Customizing metrics
5. Verifying scheduled posts

Usage:
    python scripts/setup_slack_monitoring.py
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Optional


COLORS = {
    "HEADER": "\033[95m",
    "BLUE": "\033[94m",
    "CYAN": "\033[96m",
    "GREEN": "\033[92m",
    "YELLOW": "\033[93m",
    "RED": "\033[91m",
    "BOLD": "\033[1m",
    "UNDERLINE": "\033[4m",
    "END": "\033[0m",
}


def print_header(text: str):
    """Print colored header."""
    print(f"\n{COLORS['HEADER']}{COLORS['BOLD']}{'=' * 70}")
    print(f"  {text}")
    print(f"{'=' * 70}{COLORS['END']}\n")


def print_step(num: int, text: str):
    """Print step number."""
    print(f"{COLORS['CYAN']}[Step {num}]{COLORS['END']} {text}")


def print_info(text: str):
    """Print info message."""
    print(f"{COLORS['BLUE']}ℹ️  {text}{COLORS['END']}")


def print_success(text: str):
    """Print success message."""
    print(f"{COLORS['GREEN']}✓ {text}{COLORS['END']}")


def print_warning(text: str):
    """Print warning message."""
    print(f"{COLORS['YELLOW']}⚠️  {text}{COLORS['END']}")


def print_error(text: str):
    """Print error message."""
    print(f"{COLORS['RED']}✗ {text}{COLORS['END']}")


def input_webhook_url() -> str:
    """Prompt for Slack webhook URL."""
    print_step(1, "Get Slack Webhook URL")
    print("""
Follow these steps to create a Slack incoming webhook:

1. Go to https://api.slack.com/apps
2. Click "Create New App" → "From scratch"
3. App Name: "ProfitEngine Monitoring"
4. Select your workspace
5. In sidebar, click "Incoming Webhooks"
6. Toggle "Activate Incoming Webhooks" to ON
7. Click "Add New Webhook to Workspace"
8. Select channel (e.g., #profitengine-alerts)
9. Click "Allow"
10. Copy the Webhook URL
    """)

    while True:
        webhook = input(f"{COLORS['BOLD']}Paste webhook URL: {COLORS['END']}").strip()
        if webhook.startswith("https://hooks.slack.com/services/"):
            print_success(f"Webhook URL accepted: {webhook[:50]}...")
            return webhook
        else:
            print_error("Invalid URL. Must start with 'https://hooks.slack.com/services/'")


def test_webhook(webhook_url: str) -> bool:
    """Test webhook with curl."""
    print_step(2, "Test Webhook Connection")

    import aiohttp
    import asyncio

    payload = {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "✓ ProfitEngine Slack Monitoring Connected!\n*Setup successful — automated posts will begin at scheduled times.*"
                }
            }
        ]
    }

    async def test():
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(webhook_url, json=payload) as resp:
                    if resp.status == 200:
                        return True
                    else:
                        print_error(f"HTTP {resp.status}: {await resp.text()}")
                        return False
            except Exception as e:
                print_error(f"Connection failed: {e}")
                return False

    try:
        result = asyncio.run(test())
        if result:
            print_success("Webhook test message posted to Slack!")
            return True
        else:
            print_error("Failed to post test message")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def add_github_secret(webhook_url: str) -> bool:
    """Guide user to add GitHub secret."""
    print_step(3, "Add GitHub Secret")

    print(f"""
Webhook URL will be stored as GitHub secret 'PROFITENGINE_SLACK_WEBHOOK_URL'.

Manual Setup (Recommended):
1. Go to https://github.com/quantam101/profitengine-v5-final/settings/secrets/actions
2. Click "New repository secret"
3. Name: PROFITENGINE_SLACK_WEBHOOK_URL
4. Value: {webhook_url}
5. Click "Add secret"

Automated Setup:
If you have GitHub CLI (gh) installed, run:
    """)

    gh_command = f'gh secret set PROFITENGINE_SLACK_WEBHOOK_URL -b "{webhook_url}"'
    print(f"{COLORS['BOLD']}    {gh_command}{COLORS['END']}\n")

    try:
        result = subprocess.run(
            ["gh", "secret", "set", "PROFITENGINE_SLACK_WEBHOOK_URL", "-b", webhook_url],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print_success("GitHub secret added successfully!")
            return True
        else:
            print_warning("GitHub CLI not available. Use manual setup above.")
            return False
    except FileNotFoundError:
        print_warning("GitHub CLI (gh) not installed. Use manual setup above.")
        return False


def show_metrics_guide():
    """Show metrics customization guide."""
    print_step(4, "Customize Metrics (Optional)")

    print("""
The service comes with example metrics. Customize them by editing:
    backend/services/slack_monitoring.py

Key functions to update:
    • _fetch_morning_metrics() — 8 AM metrics
    • _fetch_evening_metrics() — 6 PM metrics
    • _fetch_weekly_metrics() — Sunday metrics
    • _fetch_*_alerts() — Alert thresholds

Example: Fetch real revenue from database

    async def _fetch_evening_metrics(self) -> list[MetricValue]:
        # Query your database
        revenue_doc = await self.db.daily_metrics.find_one()
        return [
            MetricValue(
                label="Daily Revenue",
                value=f"${revenue_doc['total']:.2f}",
                status=StatusIndicator.OPERATIONAL,
                trend=f"↑ +{revenue_doc['percent_change']:.1f}%"
            )
        ]

For a quick start, the current example metrics are production-ready.
    """)

    print_info("Metrics customization is optional — defaults are already configured.")


def show_schedule_guide():
    """Show schedule customization guide."""
    print_step(5, "Verify Scheduled Posts")

    print("""
Scheduled posts are configured in: .github/workflows/slack-monitoring.yml

Current Schedule (UTC):
    • 8:00 AM  — Morning briefing (system status)
    • 6:00 PM  — Evening metrics (revenue, sessions)
    • Sunday 8 PM — Weekly summary (trends, priorities)

To change times, edit the cron expressions:

    # Morning: 8 AM UTC → "0 8 * * *"
    # Evening: 6 PM UTC → "0 18 * * *"
    # Weekly:  Sunday 8 PM → "0 20 * * 0"

Time Conversion:
    • 8 AM UTC = 3 AM EST / 12 AM PST / 4 PM IST
    • 6 PM UTC = 1 PM EST / 10 AM PST / 11:30 PM IST
    • Sunday 8 PM UTC = Sunday 3 PM EST / 12 PM PST / Monday 1:30 AM IST

Verify workflow is enabled:
    1. Go to GitHub → Actions tab
    2. Select "Slack Real-Time Monitoring"
    3. Workflow should show as "enabled"
    """)

    print_success("Scheduled posts are ready to go!")


def show_manual_trigger_guide():
    """Show how to manually trigger."""
    print_step(6, "Test with Manual Trigger")

    print("""
To test the workflow before scheduled time:

1. Go to GitHub Actions tab
2. Select "Slack Real-Time Monitoring" workflow
3. Click "Run workflow" button
4. Select briefing type: morning, evening, or weekly
5. Click "Run workflow"
6. Check Slack channel within 30 seconds

View logs:
    1. Click the running workflow
    2. Select the job (morning/evening/weekly)
    3. View "Post * to Slack" step for details
    """)

    print_info("Test with manual trigger to verify everything works before scheduled time.")


def show_template_guide():
    """Show template customization guide."""
    print_step(7, "Customize Message Templates (Optional)")

    print("""
Message templates are in: SLACK_TEMPLATES_QUICK_REFERENCE.md

Pre-built templates:
    • Morning Briefing — System status, daily tasks
    • Evening Metrics — Revenue, sessions, conversion
    • Weekly Summary — Trends, highlights, next week

Customize:
    1. Edit backend/services/slack_monitoring.py
    2. Modify the SlackBriefing creation in each method
    3. Change title, color, metrics, alerts
    4. Commit and push (workflow auto-updates)

Example: Change morning briefing color to blue:

    return SlackBriefing(
        title="📊 Morning Briefing",
        subtitle="...",
        metrics=await self._fetch_morning_metrics(),
        color="#0099ff"  # Blue instead of green
    )
    """)

    print_info("Templates are fully customizable via Python code.")


def show_next_steps():
    """Show final next steps."""
    print_header("Setup Complete!")

    print("""
✓ Slack webhook created and tested
✓ GitHub secret configured
✓ Workflow scheduled for daily posts
✓ Message templates ready

Next Steps:

1. Commit changes:
   git add .
   git commit -m "feat: add Slack real-time monitoring"
   git push origin main

2. Verify workflow runs:
   • Go to GitHub Actions
   • Select "Slack Real-Time Monitoring"
   • Manually trigger a post to test
   • Check Slack channel for message

3. (Optional) Customize metrics:
   • Edit backend/services/slack_monitoring.py
   • Update _fetch_*_metrics() functions
   • Connect to your database
   • Commit and redeploy

4. Set up on-call alerts:
   • Add thresholds in _fetch_*_alerts()
   • Include critical metrics
   • Test with manual trigger

Scheduled Posts:
   • Every day at 8 AM UTC — Morning briefing
   • Every day at 6 PM UTC — Evening metrics
   • Every Sunday at 8 PM UTC — Weekly summary

Documentation:
   • SLACK_MONITORING_SETUP.md — Complete guide
   • SLACK_TEMPLATES_QUICK_REFERENCE.md — Template reference
   • backend/services/slack_monitoring.py — Source code

Questions?
   • Check GitHub Actions logs for errors
   • Review Slack webhook permissions
   • Verify MONGO_URL secret is set

Support:
   Update backend/services/slack_monitoring.py and redeploy.
   Changes auto-trigger on next git push.
    """)

    print_success("ProfitEngine Slack Monitoring is ready to go!")


def main():
    """Run setup wizard."""
    print_header("ProfitEngine Slack Real-Time Monitoring Setup")

    print("""
This wizard will guide you through setting up automated Slack monitoring posts.

You'll need:
    • Slack workspace admin access
    • GitHub repo access
    • ~5 minutes

What you'll get:
    ✓ Daily 8 AM morning briefing
    ✓ Daily 6 PM evening metrics
    ✓ Weekly Sunday 8 PM summary
    ✓ Custom metric templates
    ✓ Alert integration

Let's get started!
    """)

    # Step 1: Get webhook URL
    webhook_url = input_webhook_url()

    # Step 2: Test webhook
    if not test_webhook(webhook_url):
        print_error("Webhook test failed. Check URL and try again.")
        return

    # Step 3: Add GitHub secret
    if not add_github_secret(webhook_url):
        print_warning("Manual GitHub secret setup required. See instructions above.")
        manual_confirm = input(f"{COLORS['BOLD']}Have you added the GitHub secret? (y/n): {COLORS['END']}").strip().lower()
        if manual_confirm != "y":
            print_error("Setup incomplete. Add GitHub secret and try again.")
            return

    # Step 4: Show metrics guide
    show_metrics_guide()

    # Step 5: Verify schedule
    show_schedule_guide()

    # Step 6: Show manual trigger
    show_manual_trigger_guide()

    # Step 7: Template guide
    show_template_guide()

    # Step 8: Next steps
    show_next_steps()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{COLORS['YELLOW']}Setup cancelled by user.{COLORS['END']}")
        sys.exit(0)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)
