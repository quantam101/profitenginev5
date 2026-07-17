#!/usr/bin/env python3
"""Blog syndication — republishes alreadyherellc.com blog posts to Dev.to and
Hashnode with canonical URLs pointing back to the site (SEO-safe backlinks).

Reads posts from a checkout of quantam101/already-here-llc (public repo) at
BLOG_DIR, dedupes against what each platform already has, and publishes only
what's missing. Fails soft per platform.

Env:
  BLOG_DIR            — path to content/blog (default: site/content/blog)
  DEVTO_API_KEY       — dev.to API key (optional; platform skipped if absent)
  HASHNODE_API_KEY    — Hashnode PAT (optional)
  HASHNODE_PUB_ID     — Hashnode publication id (required for Hashnode)
  SYNDICATE_LIMIT     — newest N posts considered (default 6)

Usage:  python scripts/syndicate_blog.py [--dry-run]
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

SITE = "https://www.alreadyherellc.com"

TAGS_BY_CATEGORY = {
    "Field Operations": (["fieldservice", "msp", "datacenter", "business"],
                         [{"slug": "field-service", "name": "Field Service"},
                          {"slug": "msp", "name": "MSP"},
                          {"slug": "business", "name": "Business"}]),
    "AI Operations": (["ai", "automation", "business", "productivity"],
                      [{"slug": "ai", "name": "AI"},
                       {"slug": "automation", "name": "Automation"},
                       {"slug": "business", "name": "Business"}]),
}
DEFAULT_TAGS = (["business", "technology"],
                [{"slug": "business", "name": "Business"},
                 {"slug": "technology", "name": "Technology"}])


def _api(url: str, headers: dict, body: dict | None = None,
         method: str | None = None) -> dict:
    req = urllib.request.Request(
        url, data=json.dumps(body).encode() if body is not None else None,
        method=method or ("POST" if body is not None else "GET"),
        headers={"Content-Type": "application/json", "Accept": "application/json",
                 # Cloudflare on gql.hashnode.com serves HTML challenges to
                 # script-looking agents; a browser-style UA passes
                 "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                "AppleWebKit/537.36 (KHTML, like Gecko) "
                                "Chrome/126.0 Safari/537.36"), **headers})
    with urllib.request.urlopen(req, timeout=45) as r:
        raw = r.read()
    try:
        return json.loads(raw)
    except ValueError:
        raise RuntimeError(f"non-JSON response ({raw[:120]!r})") from None


def parse_post(path: Path) -> dict | None:
    raw = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", raw, re.S)
    if not m:
        return None
    meta = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(":")
        if _:
            meta[k.strip()] = v.strip().strip("\"'")
    slug = re.sub(r"[^a-zA-Z0-9_-]", "-", path.stem)
    body = m.group(2).strip()
    # absolute-ify site-relative links for off-site readers
    body = re.sub(r"\]\((/[^)\s]*)\)", rf"]({SITE}\1)", body)
    canonical = f"{SITE}/blog/{slug}"
    body += (f"\n\n---\n\n*Originally published at "
             f"[alreadyherellc.com]({canonical}). Arizona field coverage "
             f"retainers and our 42-service fixed-price catalog: "
             f"[{SITE.removeprefix('https://')}]({SITE}/arizona-field-coverage).*")
    return {"slug": slug, "canonical": canonical, "body": body,
            "title": meta.get("title", path.stem),
            "date": meta.get("date", "1970-01-01"),
            "excerpt": meta.get("excerpt", ""),
            "category": meta.get("category", "")}


def devto_publish(posts: list[dict], dry: bool) -> None:
    key = os.getenv("DEVTO_API_KEY", "").strip()
    if not key:
        print("dev.to: no DEVTO_API_KEY — skipped")
        return
    try:
        mine = _api("https://dev.to/api/articles/me/all?per_page=200",
                    {"api-key": key})
        have = {a.get("canonical_url") for a in mine} | {a.get("title") for a in mine}
    except Exception as e:
        print(f"dev.to: listing failed ({str(e)[:120]}) — skipped")
        return
    for p in posts:
        if p["canonical"] in have or p["title"] in have:
            print(f"dev.to: already there — {p['slug']}")
            continue
        if dry:
            print(f"dev.to: would publish {p['slug']}")
            continue
        tags = TAGS_BY_CATEGORY.get(p["category"], DEFAULT_TAGS)[0]
        payload = {"article": {"title": p["title"], "published": True,
                               "body_markdown": p["body"],
                               "canonical_url": p["canonical"],
                               "description": p["excerpt"][:150],
                               "tags": tags}}
        for attempt in (1, 2):
            try:
                art = _api("https://dev.to/api/articles", {"api-key": key}, payload)
                print(f"dev.to: published {p['slug']} -> {art.get('url')}")
                break
            except Exception as e:
                if "429" in str(e) and attempt == 1:
                    print(f"dev.to: rate limited on {p['slug']} — waiting 65s")
                    time.sleep(65)
                    continue
                print(f"dev.to: publish failed for {p['slug']} ({str(e)[:150]})")
                break
        time.sleep(35)  # dev.to write limit is ~1 article per 30s


def hashnode_publish(posts: list[dict], dry: bool) -> None:
    key = os.getenv("HASHNODE_API_KEY", "").strip()
    pub = os.getenv("HASHNODE_PUB_ID", "").strip()
    if not (key and pub):
        print("hashnode: missing HASHNODE_API_KEY/HASHNODE_PUB_ID — skipped")
        return
    gql = "https://gql.hashnode.com"
    try:
        q = ("query($id: ObjectId!){ publication(id:$id){ "
             "posts(first:50){ edges{ node{ title } } } } }")
        d = _api(gql, {"Authorization": key},
                 {"query": q, "variables": {"id": pub}})
        edges = (d.get("data") or {}).get("publication", {}).get("posts", {}).get("edges", [])
        have = {e["node"]["title"] for e in edges}
    except Exception as e:
        print(f"hashnode: listing failed ({str(e)[:120]}) — skipped")
        return
    mut = ("mutation($input: PublishPostInput!){ publishPost(input:$input){ "
           "post{ url } } }")
    for p in posts:
        if p["title"] in have:
            print(f"hashnode: already there — {p['slug']}")
            continue
        if dry:
            print(f"hashnode: would publish {p['slug']}")
            continue
        tags = TAGS_BY_CATEGORY.get(p["category"], DEFAULT_TAGS)[1]
        try:
            d = _api(gql, {"Authorization": key},
                     {"query": mut, "variables": {"input": {
                         "title": p["title"], "contentMarkdown": p["body"],
                         "publicationId": pub, "tags": tags,
                         "originalArticleURL": p["canonical"]}}})
            if d.get("errors"):
                print(f"hashnode: publish failed for {p['slug']} "
                      f"({json.dumps(d['errors'])[:200]})")
            else:
                url = d["data"]["publishPost"]["post"]["url"]
                print(f"hashnode: published {p['slug']} -> {url}")
        except Exception as e:
            print(f"hashnode: publish failed for {p['slug']} ({str(e)[:150]})")
        time.sleep(2)


def main() -> None:
    dry = "--dry-run" in sys.argv
    blog_dir = Path(os.getenv("BLOG_DIR", "site/content/blog"))
    if not blog_dir.is_dir():
        print(f"::error::blog dir not found: {blog_dir}")
        sys.exit(1)
    posts = [p for p in (parse_post(f) for f in sorted(blog_dir.glob("*.md"))) if p]
    limit = int(os.getenv("SYNDICATE_LIMIT", "6"))
    posts = sorted(posts, key=lambda p: p["date"], reverse=True)[:limit]
    print(f"{len(posts)} candidate post(s): {[p['slug'] for p in posts]}")
    devto_publish(posts, dry)
    hashnode_publish(posts, dry)


if __name__ == "__main__":
    main()
