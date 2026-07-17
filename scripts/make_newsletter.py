#!/usr/bin/env python3
"""Weekly newsletter composer. Gathers the week's pipeline artifacts
(youtube_uploads.json, videos_manifest.json, trending_topics.json — all
optional) and composes a ready-to-send issue.

Delivery, in order of preference (each fails soft to the next):
  1. Beehiiv API draft (needs BEEHIIV_API_KEY + BEEHIIV_PUBLICATION_ID;
     create-post API is Enterprise-only, so this often 4xxs — that's fine)
  2. Publish issue HTML to the public content repo (GitHub Pages) via `gh`
  3. Always writes newsletter.html locally as the artifact of record

Usage:  python scripts/make_newsletter.py [--no-page]
"""
from __future__ import annotations

import base64
import html
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from generate_shorts import ai_complete  # noqa: E402

CONTENT_REPO = "quantam101/content"
PAGES_BASE = "https://quantam101.github.io/content"
EBOOK_URL = f"{PAGES_BASE}/ebooks/zero-dollar-content-engine/"
BLUEPRINT_URL = f"{PAGES_BASE}/ebooks/blueprint/"


def _load(name: str):
    p = Path(name)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return None


def compose() -> tuple[str, str]:
    """Returns (subject, html_body)."""
    week = time.strftime("%B %d, %Y", time.gmtime())
    uploads = _load("youtube_uploads.json") or []
    manifest = {v["program"]: v for v in (_load("videos_manifest.json") or [])}
    trending = (_load("trending_topics.json") or [])[:3]

    ok_uploads = [u for u in uploads if u.get("status") == "success"]
    subject = f"This week from Already Here — {len(ok_uploads)} new videos" \
        if ok_uploads else f"This week from Already Here — {week}"

    intro = ai_complete(
        "Write a 2-sentence friendly newsletter intro for a weekly digest from a "
        "company that automates short-form content with free tools. Plain text, "
        "no emojis, no hashtags, warm but concise.", min_len=40, max_len=400) \
        or ("Another week, another batch of content shipped entirely by our $0 "
            "automation stack. Here's what went out and what the data says is "
            "worth your attention.")

    parts = [f"<p>{html.escape(intro)}</p>"]

    if ok_uploads:
        parts.append("<h2>This week's videos</h2><ul>")
        for u in ok_uploads:
            m = manifest.get(u["program"], {})
            title = html.escape(m.get("title", u["program"]))
            url = u.get("url") or f"https://www.youtube.com/shorts/{u.get('video_id', '')}"
            parts.append(f'<li><a href="{url}">{title}</a></li>')
        parts.append("</ul><p>Also on Instagram — "
                     '<a href="https://www.instagram.com/alreadyherellc/">@alreadyherellc</a> '
                     "and our Facebook page.</p>")

    if trending:
        parts.append("<h2>What the data says is working</h2>"
                     "<p>Highest views-per-day topics in our niches this week:</p><ul>")
        for t in trending:
            vpd = t.get("views_per_day")
            stat = f" — ~{vpd:,} views/day" if vpd else ""
            parts.append(f"<li>{html.escape(t['title'])}{stat}</li>")
        parts.append("</ul>")

    parts.append(
        f'<h2>Free playbook</h2><p>Everything we use to run this — voiceovers, '
        f'captions, B-roll, trend research, auto-posting — is free, and the whole '
        f'system is documented in <a href="{EBOOK_URL}">The $0 Content Engine</a>.</p>'
        f'<p>Ready to build it yourself? The <a href="{BLUEPRINT_URL}">Complete '
        f'Blueprint</a> has every script, prompt, command, and workflow — the '
        f'exact build manual for the engine that produced this email.</p>'
        f"<p>Questions or want this built for your business? Reply to this email "
        f"or reach us at dispatch@alreadyherellc.com.</p>"
        f"<p><em>Some links in our content are affiliate links — they may earn "
        f"us a commission at no cost to you.</em></p>")
    return subject, "\n".join(parts)


def try_beehiiv(subject: str, body: str) -> bool:
    key = os.getenv("BEEHIIV_API_KEY", "").strip()
    pub = os.getenv("BEEHIIV_PUBLICATION_ID", "").strip()
    if not (key and pub):
        print("no Beehiiv creds — skipping API")
        return False
    try:
        req = urllib.request.Request(
            f"https://api.beehiiv.com/v2/publications/{pub}/posts",
            data=json.dumps({"title": subject, "body_content": body,
                             "status": "draft"}).encode(),
            method="POST",
            headers={"Authorization": f"Bearer {key}",
                     "Content-Type": "application/json",
                     "User-Agent": "already-here-newsletter/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.loads(r.read())
        print(f"beehiiv draft created: {d.get('data', {}).get('preview_url', d)}")
        return True
    except urllib.error.HTTPError as e:
        print(f"beehiiv API unavailable (HTTP {e.code}: {e.read()[:200]!r}) — falling back")
    except Exception as e:
        print(f"beehiiv API failed ({str(e)[:100]}) — falling back")
    return False


def publish_page(html_page: str) -> None:
    slug = time.strftime("%Y-%m-%d", time.gmtime())
    dest = f"newsletters/{slug}/index.html"
    b64 = base64.b64encode(html_page.encode()).decode()
    probe = subprocess.run(["gh", "api", f"repos/{CONTENT_REPO}/contents/{dest}"],
                           capture_output=True, text=True)
    args = ["gh", "api", "-X", "PUT", f"repos/{CONTENT_REPO}/contents/{dest}",
            "-f", f"message=newsletter: {slug}", "-f", f"content={b64}"]
    if probe.returncode == 0:
        args += ["-f", f"sha={json.loads(probe.stdout)['sha']}"]
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode == 0:
        print(f"issue page: {PAGES_BASE}/newsletters/{slug}/  "
              f"(paste into Beehiiv to send)")
    else:
        print(f"page publish failed: {r.stderr[:200]}")


def main() -> None:
    subject, body = compose()
    page = (f"<!doctype html><html><head><meta charset=\"utf-8\">"
            f"<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            f"<title>{html.escape(subject)}</title>"
            f"<style>body{{max-width:640px;margin:0 auto;padding:2rem 1.2rem;"
            f"font:16px/1.6 Georgia,serif}}h2{{margin-top:1.8rem}}</style></head>"
            f"<body><h1>{html.escape(subject)}</h1>{body}</body></html>")
    Path("newsletter.html").write_text(page, encoding="utf-8")
    print(f"subject: {subject}")
    print("newsletter.html written")
    if not try_beehiiv(subject, body) and "--no-page" not in sys.argv:
        publish_page(page)


if __name__ == "__main__":
    main()
