#!/usr/bin/env python3
"""Daily newsletter composer. Builds the digest from real pipeline data —
the content site's Atom feed (today's freshly published article),
trending_topics.json + youtube_uploads.json (video pipeline artifacts) and the
live Gumroad catalog — then POSTs it to the runtime /newsletter/publish
endpoint (Resend broadcast).

A permanent content ledger (data/newsletter_ledger.json, committed by the
workflow) records everything ever featured: id/url, semantic title
fingerprint, kind, and date. Items already in the ledger are never featured
again, matched by id/url AND by title-token similarity, so the same story
under a different headline is still rejected.

Hard publishing rule: no new source material = no issue. If nothing new is
available (no new article, no unfeatured upload, no unfeatured trend), the
send is SKIPPED (exit 0 with a warning) — repeat content is worse than a
missed day.

Env:
  RUNTIME_API_URL        — required; Render runtime base URL
  GUMROAD_ACCESS_TOKEN   — optional; enables the rotating product spotlight
  OPENROUTER/GROQ/...    — optional; free-LLM keys for the daily insight line

Usage:  python scripts/make_daily_digest.py [--dry-run]
"""
from __future__ import annotations

import html
import json
import os
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from generate_shorts import ai_complete  # noqa: E402

PAGES_BASE = "https://quantam101.github.io/content"
BLUEPRINT_URL = f"{PAGES_BASE}/ebooks/blueprint/"
EBOOK_URL = f"{PAGES_BASE}/ebooks/zero-dollar-content-engine/"
FEED_URL = "https://www.alreadyherellc.com/content/feed.xml"
LEDGER_PATH = Path("data/newsletter_ledger.json")
MAX_ARTICLE_AGE_DAYS = 3   # a feed entry older than this is not "new today"
SIMILARITY_THRESHOLD = 0.6  # Jaccard overlap of title tokens => same story

_STOPWORDS = frozenset(
    "a an and are as at be by for from how in is it of on or the to that this "
    "these those with you your what why when where will can our we i".split())


def fingerprint(title: str) -> list[str]:
    """Semantic-ish fingerprint: sorted content tokens of the title."""
    tokens = {t for t in "".join(
        c.lower() if c.isalnum() else " " for c in title).split()
        if len(t) > 2 and t not in _STOPWORDS}
    return sorted(tokens)


def _similar(a: list[str], b: list[str]) -> bool:
    sa, sb = set(a), set(b)
    if not sa or not sb:
        return False
    return len(sa & sb) / len(sa | sb) >= SIMILARITY_THRESHOLD


def _norm_url(url: str) -> str:
    """Canonical form for dedup: drop query/fragment and trailing slash."""
    if not url:
        return ""
    p = urllib.parse.urlsplit(url)
    return f"{p.scheme.lower()}://{p.netloc.lower()}{p.path.rstrip('/')}"


class Ledger:
    """Permanent record of every item ever featured in the digest."""

    def __init__(self) -> None:
        self.entries: list[dict] = []
        if LEDGER_PATH.exists():
            # fail CLOSED: an unreadable permanent history must never be
            # treated as empty, or the next issue repeats old content and
            # the save overwrites the damaged file
            try:
                data = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
                self.entries = data["featured"]
                if not isinstance(self.entries, list):
                    raise TypeError("'featured' is not a list")
            except Exception as e:
                print(f"::error::ledger {LEDGER_PATH} unreadable ({e}) — "
                      "aborting so history is not lost; fix or restore the file")
                sys.exit(1)
        self._new: list[dict] = []

    def seen(self, key: str, title: str = "", url: str = "") -> bool:
        fp = fingerprint(title) if title else []
        nu = _norm_url(url)
        for e in self.entries:
            if key and key == e.get("key"):
                return True
            if nu and nu == _norm_url(e.get("url", "")):
                return True
            if fp and _similar(fp, e.get("fingerprint", [])):
                return True
        return False

    def add(self, kind: str, key: str, title: str, url: str) -> None:
        entry = {"kind": kind, "key": key, "title": title, "url": url,
                 "fingerprint": fingerprint(title),
                 "date": time.strftime("%Y-%m-%d", time.gmtime())}
        self.entries.append(entry)
        self._new.append(entry)

    def save(self) -> None:
        if not self._new:
            return
        LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
        LEDGER_PATH.write_text(
            json.dumps({"featured": self.entries}, indent=2) + "\n",
            encoding="utf-8")
        print(f"ledger: recorded {len(self._new)} new item(s) "
              f"({len(self.entries)} total) -> {LEDGER_PATH}")


def fetch_new_articles(ledger: Ledger) -> list[dict]:
    """Freshly published posts from the content site's Atom feed that have
    never been featured before."""
    try:
        req = urllib.request.Request(
            FEED_URL, headers={"User-Agent": "already-here-digest/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            root = ET.fromstring(r.read())  # noqa: S314 - our own Pages feed
    except Exception as e:
        print(f"feed fetch failed ({str(e)[:80]}) — no article section")
        return []
    ns = {"a": "http://www.w3.org/2005/Atom"}
    now = time.time()
    fresh = []
    for entry in root.findall("a:entry", ns):
        title = (entry.findtext("a:title", "", ns) or "").strip()
        link = entry.find("a:link[@rel='alternate']", ns)
        url = link.get("href") if link is not None else ""
        eid = entry.findtext("a:id", "", ns) or url
        published = entry.findtext("a:published", "", ns)[:10]
        try:
            age_days = (now - time.mktime(
                time.strptime(published, "%Y-%m-%d"))) / 86400
        except ValueError:
            continue
        if age_days > MAX_ARTICLE_AGE_DAYS:
            continue
        if not title or not url or ledger.seen(eid, title, url):
            continue
        fresh.append({"id": eid, "title": title, "url": url,
                      "published": published})
    return fresh


def utm(url: str, campaign: str = "daily-digest") -> str:
    """Append UTM params to our own / partner links (not third-party YouTube)."""
    sep = "&" if "?" in url else "?"
    return (f"{url}{sep}utm_source=newsletter&utm_medium=email"
            f"&utm_campaign={urllib.parse.quote(campaign)}")


def _load(name: str):
    p = Path(name)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return None


def gumroad_products() -> list[dict]:
    """Live product list (name, short_url, price) from the Gumroad API."""
    token = os.getenv("GUMROAD_ACCESS_TOKEN", "").strip()
    if not token:
        return []
    try:
        req = urllib.request.Request(
            f"https://api.gumroad.com/v2/products?access_token={token}",
            headers={"User-Agent": "already-here-digest/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
        products = data.get("products", [])
        # missing "published" key must not hide live products (the public
        # product pages 200 even when the API omits the flag)
        live = [p for p in products
                if p.get("short_url") and p.get("published", True) is not False]
        print(f"gumroad: {len(live)}/{len(products)} products usable for spotlight")
        return live
    except Exception as e:
        print(f"gumroad fetch failed ({str(e)[:80]}) — skipping product spotlight")
        return []


def compose(ledger: Ledger) -> tuple[str, list[dict], str] | None:
    """Returns (headline, sections, cta_url), or None when there is nothing
    genuinely new to say (caller should skip the send)."""
    today = time.strftime("%B %d, %Y", time.gmtime())
    manifest = {v["program"]: v for v in (_load("videos_manifest.json") or [])}

    # Selection reserves each accepted item in the ledger immediately, so
    # duplicates within the same batch (or across source categories) are
    # rejected too, not just items featured in past issues.
    articles = []
    for a in fetch_new_articles(ledger):
        if len(articles) >= 3:
            break
        if ledger.seen(a["id"], a["title"], a["url"]):
            continue
        ledger.add("article", a["id"], a["title"], a["url"])
        articles.append(a)

    uploads = []
    for u in (_load("youtube_uploads.json") or []):
        if len(uploads) >= 5:
            break
        if u.get("status") != "success":
            continue
        m = manifest.get(u.get("program", ""), {})
        title = m.get("title", u.get("program", ""))
        url = u.get("url") or \
            f"https://www.youtube.com/shorts/{u.get('video_id', '')}"
        if ledger.seen(u.get("video_id", ""), title, url):
            continue
        ledger.add("upload", u.get("video_id", ""), title, url)
        uploads.append(u)

    trending = []
    for t in (_load("trending_topics.json") or []):
        if len(trending) >= 3:
            break
        key = t.get("id", "") or t.get("url", "")
        if ledger.seen(key, t.get("title", ""), t.get("url", "")):
            continue
        ledger.add("trend", key, t.get("title", ""), t.get("url", ""))
        trending.append(t)

    # Hard publishing rule: no new source material = no issue. Product
    # spotlight and AI insight alone never justify a send.
    if not (articles or uploads or trending):
        return None

    products = gumroad_products()
    sections: list[dict] = []

    if articles:
        items = []
        for a in articles:
            link = html.escape(utm(a["url"], "daily-digest-article"), quote=True)
            items.append(f'&bull; <a href="{link}">'
                         f'{html.escape(a["title"])}</a>')
        sections.append({"heading": "New today",
                         "body": ("Freshly published on our site:<br>"
                                  + "<br>".join(items))})

    insight = ai_complete(
        "Write a 2-3 sentence practical daily insight for small-business "
        "owners about automating content, lead capture, or customer service "
        "with free AI tools. Concrete and specific, plain text, no emojis, "
        "no hashtags.", min_len=60, max_len=500)
    if insight:
        sections.append({"heading": "Today's automation insight",
                         "body": html.escape(insight)})

    if uploads:
        items = []
        for u in uploads:
            m = manifest.get(u.get("program", ""), {})
            raw_title = m.get("title", u.get("program", "New video"))
            url = u.get("url") or \
                f"https://www.youtube.com/shorts/{u.get('video_id', '')}"
            items.append(f'&bull; <a href="{html.escape(url, quote=True)}">'
                         f'{html.escape(raw_title)}</a>')
        sections.append({"heading": "Fresh from our channel",
                         "body": "<br>".join(items)})

    if trending:
        items = []
        for t in trending:
            raw_title = t.get("title", "")
            url = t.get("url", "")
            vpd = t.get("views_per_day")
            stat = f" — ~{vpd:,} views/day" if vpd else ""
            items.append(f'&bull; <a href="{html.escape(url, quote=True)}">'
                         f'{html.escape(raw_title[:80])}</a>{stat}')
        sections.append({
            "heading": "What's pulling views right now",
            "body": ("Top performers in our niches, live from today's "
                     "trend scan:<br>" + "<br>".join(items))})

    cta_url = utm(BLUEPRINT_URL)
    if products:
        # rotate the spotlight daily so no two consecutive issues match
        pick = products[int(time.strftime("%j")) % len(products)]
        name = html.escape(pick.get("name", ""))
        price = pick.get("formatted_price") or ""
        link = utm(pick["short_url"], campaign="daily-digest-product")
        sections.append({
            "heading": "From our toolkit",
            "body": (f'<a href="{link}">{name}</a>'
                     f'{f" — {html.escape(str(price))}" if price else ""}. '
                     f'Built from the same automation stack that writes this '
                     f'email. The full build manual is in '
                     f'<a href="{utm(BLUEPRINT_URL)}">the Complete Blueprint</a>, '
                     f'and the free intro is '
                     f'<a href="{utm(EBOOK_URL)}">The $0 Content Engine</a>.')})

    headline = f"AI Income Digest — {today}"
    return headline, sections[:10], cta_url


def publish(headline: str, sections: list[dict], cta_url: str) -> dict:
    base = os.environ["RUNTIME_API_URL"].rstrip("/")
    payload = {"headline": headline, "sections": sections,
               "tags": ["ai", "automation", "already-here"],
               "cta_url": cta_url}
    req = urllib.request.Request(
        f"{base}/newsletter/publish", data=json.dumps(payload).encode(),
        method="POST", headers={"Content-Type": "application/json",
                                "User-Agent": "already-here-digest/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def main() -> None:
    ledger = Ledger()
    composed = compose(ledger)
    if not composed:
        print("::warning::no NEW source material (article/uploads/trends all "
              "already featured or empty) — skipping today's send to avoid "
              "repeat content")
        return
    headline, sections, cta_url = composed
    print(f"headline: {headline}")
    for s in sections:
        print(f"  section: {s['heading']}")
    if "--dry-run" in sys.argv:
        Path("daily_digest_preview.json").write_text(
            json.dumps({"headline": headline, "sections": sections,
                        "cta_url": cta_url}, indent=2), encoding="utf-8")
        print("dry run — wrote daily_digest_preview.json, nothing sent "
              "(ledger not updated)")
        return
    result = publish(headline, sections, cta_url)
    print(json.dumps(result))
    if not result.get("ok"):
        print(f"::error::newsletter publish failed: {result.get('error')}")
        sys.exit(1)
    ledger.save()


if __name__ == "__main__":
    main()
