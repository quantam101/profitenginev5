#!/usr/bin/env python3
"""Blog syndication — republishes www.alreadyherellc.com/content/ posts to
Dev.to and Hashnode with canonical URLs pointing back to the site (SEO-safe
backlinks).

Reads Jekyll posts from a checkout of quantam101/content (public repo) at
BLOG_DIR (its `_posts/` directory, files named YYYY-MM-DD-<slug>.md with
permalink /posts/:title/ under the /content baseurl), dedupes against what
each platform already has, and publishes only what's missing. Fails soft per
platform.

Env:
  BLOG_DIR            — path to the content repo's _posts (default: content/_posts)
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
CONTENT_BASE = f"{SITE}/content"
POST_FILENAME = re.compile(r"^(\d{4}-\d{2}-\d{2})-(.+)$")

DEFAULT_TAGS = (["business", "technology"],
                [{"slug": "business", "name": "Business"},
                 {"slug": "technology", "name": "Technology"}])


def _api(url: str, headers: dict, body: dict | None = None,
         method: str | None = None) -> dict:
    if not url.startswith("https://"):
        raise ValueError(f"refusing non-https API url: {url}")
    req = urllib.request.Request(  # noqa: S310 - https enforced above
        url, data=json.dumps(body).encode() if body is not None else None,
        method=method or ("POST" if body is not None else "GET"),
        headers={"Content-Type": "application/json", "Accept": "application/json",
                 # Cloudflare on gql.hashnode.com serves HTML challenges to
                 # script-looking agents; a browser-style UA passes
                 "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                "AppleWebKit/537.36 (KHTML, like Gecko) "
                                "Chrome/126.0 Safari/537.36"), **headers})
    with urllib.request.urlopen(req, timeout=45) as r:  # noqa: S310 - https enforced above
        raw = r.read()
    try:
        return json.loads(raw)
    except ValueError:
        raise RuntimeError(f"non-JSON response ({raw[:120]!r})") from None


def _tag_sets(tags: list[str]) -> tuple[list[str], list[dict]]:
    """Map front-matter tags to dev.to (≤4, [a-z0-9]) and Hashnode tag inputs."""
    devto: list[str] = []
    hashnode: list[dict] = []
    for tag in tags:
        slug = re.sub(r"[^a-z0-9]+", "-", tag.lower()).strip("-")
        compact = slug.replace("-", "")
        if not compact or compact in devto:
            continue
        devto.append(compact)
        hashnode.append({"slug": slug, "name": tag})
        if len(devto) == 4:
            break
    if not devto:
        return DEFAULT_TAGS
    return devto, hashnode


def parse_front_matter(block: str) -> dict:
    """Minimal YAML subset: `key: value` scalars plus `key:` followed by `- item` lists."""
    meta: dict = {}
    current_list: str | None = None
    for line in block.splitlines():
        if not line.strip():
            continue
        if current_list and re.match(r"^\s+-\s*", line):
            meta[current_list].append(line.split("-", 1)[1].strip().strip("\"'"))
            continue
        current_list = None
        k, sep, v = line.partition(":")
        if not sep:
            continue
        k, v = k.strip(), v.strip()
        if v.startswith("[") and v.endswith("]"):
            meta[k] = [x.strip().strip("\"'") for x in v[1:-1].split(",") if x.strip()]
        elif v == "":
            meta[k] = []
            current_list = k
        else:
            meta[k] = v.strip("\"'")
    return meta


def parse_post(path: Path) -> dict | None:
    raw = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", raw, re.S)
    if not m:
        return None
    meta = parse_front_matter(m.group(1))
    if str(meta.get("noindex", "false")).lower() == "true" or str(meta.get("published", "true")).lower() == "false":
        return None
    name = POST_FILENAME.match(path.stem)
    date = name.group(1) if name else str(meta.get("date", "1970-01-01"))[:10]
    title_slug = re.sub(r"[^a-zA-Z0-9_-]", "-", name.group(2) if name else path.stem)
    body = m.group(2).strip()
    # absolute-ify site-relative links for off-site readers
    body = re.sub(r"\]\((/[^)\s]*)\)", rf"]({SITE}\1)", body)
    canonical = f"{CONTENT_BASE}/posts/{title_slug}/"
    body += (f"\n\n---\n\n*Originally published at "
             f"[alreadyherellc.com]({canonical}). Arizona field coverage "
             f"retainers and our fixed-price service catalog: "
             f"[{SITE.removeprefix('https://')}]({SITE}/arizona-field-coverage).*")
    tags = meta.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]
    devto_tags, hashnode_tags = _tag_sets(tags)
    return {"slug": title_slug, "canonical": canonical, "body": body,
            "title": meta.get("title", path.stem),
            "date": date,
            "excerpt": meta.get("description", meta.get("excerpt", "")),
            "tags": {"devto": devto_tags, "hashnode": hashnode_tags}}


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
        tags = p["tags"]["devto"]
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
        if "non-JSON" in str(e):
            # gql.hashnode.com 301s non-Pro accounts to the announcement page:
            # the free API tier was removed in 2026; access requires a paid
            # Pro plan, which the $0-cost policy forbids.
            print("hashnode: API is now Pro-plan-gated (paid) — skipped "
                  "under the max_cost_usd:0 policy")
        else:
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
        tags = p["tags"]["hashnode"]
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
    blog_dir = Path(os.getenv("BLOG_DIR", "content/_posts"))
    if not blog_dir.is_dir():
        print(f"::error::blog dir not found: {blog_dir} (expected a quantam101/content checkout)")
        sys.exit(1)
    posts = [p for p in (parse_post(f) for f in sorted(blog_dir.glob("*.md"))) if p]
    if not posts:
        print(f"::error::no publishable posts found under {blog_dir}")
        sys.exit(1)
    limit = int(os.getenv("SYNDICATE_LIMIT", "6"))
    posts = sorted(posts, key=lambda p: p["date"], reverse=True)[:limit]
    print(f"{len(posts)} candidate post(s): {[p['slug'] for p in posts]}")
    devto_publish(posts, dry)
    hashnode_publish(posts, dry)


if __name__ == "__main__":
    main()
