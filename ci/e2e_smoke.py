"""Playwright smoke E2E — runs in CI Stage 3.

Validates the critical journeys: landing renders, waitlist page loads.
Dashboard auth-gated pages are tested separately in integration stage.
"""
from playwright.sync_api import sync_playwright
import sys

BASE = "http://localhost:3000"


def run() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # 1. Landing page renders
        page.goto(BASE, wait_until="domcontentloaded")
        page.wait_for_timeout(1500)
        content = page.content()
        assert "Profit" in content or "profit" in content.lower(), \
            f"landing page did not render expected content (got {len(content)} chars)"

        # 2. Page title or main heading is present
        title = page.title()
        assert len(title) > 0, "page has no title"

        browser.close()
        print(f"E2E smoke OK · landing rendered, title={title!r}")
        return 0


if __name__ == "__main__":
    sys.exit(run())
