"""Playwright smoke E2E — runs in CI Stage 3.

Validates the critical journeys: landing renders, dashboard renders, fleet
contains at least one agent.
"""
from playwright.sync_api import sync_playwright
import sys

BASE = "http://localhost:3000"


def run() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        page.goto(BASE, wait_until="domcontentloaded")
        page.wait_for_timeout(1500)
        assert "Profit" in page.content(), "landing did not render"

        page.goto(f"{BASE}/dashboard", wait_until="domcontentloaded")
        page.wait_for_timeout(2500)
        assert page.locator("[data-testid='dashboard-layout']").is_visible(), "dashboard not visible"

        page.goto(f"{BASE}/dashboard/agents", wait_until="domcontentloaded")
        page.wait_for_timeout(2500)
        cards = page.eval_on_selector_all("[data-testid='agents-grid'] > article", "els => els.length")
        assert cards >= 1, f"expected at least 1 agent card, got {cards}"

        browser.close()
        print(f"E2E smoke OK · {cards} agents rendered")
        return 0


if __name__ == "__main__":
    sys.exit(run())
