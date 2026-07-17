#!/usr/bin/env python3
"""URL-as-trigger: once the Gumroad product is published, run this with the
live product URL and the funnel flips over automatically:

  1. Verifies the URL actually serves a live page (no promo before that)
  2. Rewrites both buy-CTAs on the sales page source
  3. Republishes the sales page to GitHub Pages via make_ebook's publisher
  4. Prints the remaining description-link touchpoints to update

Usage: python scripts/set_product_url.py https://alreadyhere.gumroad.com/l/content-engine
"""
from __future__ import annotations

import base64
import json
import re
import subprocess
import sys
from pathlib import Path

import requests

SALES_PAGE = Path("content/funnel/blueprint-sales.html")
CONTENT_REPO = "quantam101/content"
DEST = "ebooks/blueprint/index.html"
PAGES_URL = "https://quantam101.github.io/content/ebooks/blueprint/"
STORE_ROOT = "https://alreadyhere.gumroad.com"


def verify_live(url: str) -> bool:
    try:
        r = requests.get(url, timeout=30, allow_redirects=True,
                         headers={"User-Agent": "Mozilla/5.0"})
    except Exception as e:  # noqa: BLE001
        print(f"URL check failed: {str(e)[:200]}")
        return False
    ok = r.status_code == 200
    print(f"{'live' if ok else 'NOT LIVE'}: {url} (http {r.status_code})")
    return ok


def flip_ctas(url: str) -> int:
    html = SALES_PAGE.read_text(encoding="utf-8")
    # swap every buy-CTA href still pointing at the store root (or an older
    # product link) for the new product URL
    new_html, n = re.subn(
        r'class="cta" href="[^"]+"', f'class="cta" href="{url}"', html)
    if n and new_html != html:
        SALES_PAGE.write_text(new_html, encoding="utf-8")
    print(f"sales page: {n} CTA(s) -> {url}")
    return n


def republish() -> bool:
    b64 = base64.b64encode(SALES_PAGE.read_bytes()).decode()
    probe = subprocess.run(
        ["gh", "api", f"repos/{CONTENT_REPO}/contents/{DEST}"],
        capture_output=True, text=True)
    args = ["gh", "api", "-X", "PUT", f"repos/{CONTENT_REPO}/contents/{DEST}",
            "-f", "message=funnel: flip blueprint CTA to live product",
            "-f", f"content={b64}"]
    if probe.returncode == 0:
        args += ["-f", f"sha={json.loads(probe.stdout)['sha']}"]
    r = subprocess.run(args, capture_output=True, text=True)
    ok = r.returncode == 0
    print(f"{'republished' if ok else 'republish FAILED'}: {PAGES_URL}"
          + ("" if ok else f" — {r.stderr[:200]}"))
    return ok


def main() -> None:
    if len(sys.argv) < 2 or not sys.argv[1].startswith(STORE_ROOT):
        print(__doc__)
        print(f"error: pass the live product URL (must start {STORE_ROOT})")
        sys.exit(1)
    url = sys.argv[1].strip().rstrip("/")
    if not verify_live(url):
        sys.exit(1)  # blueprint rule: nothing flips until the page is live
    if not flip_ctas(url):
        sys.exit(1)
    if not republish():
        sys.exit(1)
    print("\nfunnel is LIVE end to end. Remaining (optional) touchpoints:\n"
          "  - commit the sales-page change in this repo\n"
          "  - video descriptions already point at the sales page (no edit "
          "needed)\n"
          "  - next Monday newsletter picks up the paid CTA automatically")


if __name__ == "__main__":
    main()
