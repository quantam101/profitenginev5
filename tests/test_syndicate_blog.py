"""Syndication reads Jekyll posts from the quantam101/content checkout."""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("syndicate_blog", ROOT / "scripts" / "syndicate_blog.py")
syndicate_blog = importlib.util.module_from_spec(spec)
sys.modules["syndicate_blog"] = syndicate_blog
spec.loader.exec_module(syndicate_blog)

POST = """---
title: "Field Service Automation: How Modern MSPs Dispatch"
description: "How MSPs schedule and dispatch technicians."
date: 2026-08-27
tags:
  - Field Service Automation
  - MSP
  - Dispatch Scheduling
  - Tech Management
  - Digital Automation
layout: post
noindex: false
sitemap: true
---

## Introduction
See [our RFQ form](/rfq) for details.
"""


def _write(tmp_path, name, text):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_parse_jekyll_post_builds_content_canonical(tmp_path):
    post = syndicate_blog.parse_post(_write(tmp_path, "2026-08-27-field-service-automation-msp.md", POST))
    assert post["slug"] == "field-service-automation-msp"
    assert post["canonical"] == "https://www.alreadyherellc.com/content/posts/field-service-automation-msp/"
    assert post["date"] == "2026-08-27"
    assert post["title"].startswith("Field Service Automation")
    assert post["excerpt"] == "How MSPs schedule and dispatch technicians."
    assert "](https://www.alreadyherellc.com/rfq)" in post["body"]
    assert post["canonical"] in post["body"]


def test_tags_map_to_platform_limits(tmp_path):
    post = syndicate_blog.parse_post(_write(tmp_path, "2026-08-27-x.md", POST))
    assert post["tags"]["devto"] == ["fieldserviceautomati", "msp", "dispatchscheduling", "techmanagement"]
    assert post["tags"]["hashnode"][0] == {"slug": "field-service-automation", "name": "Field Service Automation"}
    assert len(post["tags"]["hashnode"]) == 4


def test_untagged_post_falls_back_to_default_tags(tmp_path):
    text = POST.replace("tags:\n  - Field Service Automation\n  - MSP\n  - Dispatch Scheduling\n  - Tech Management\n  - Digital Automation\n", "")
    post = syndicate_blog.parse_post(_write(tmp_path, "2026-08-27-x.md", text))
    assert post["tags"]["devto"] == syndicate_blog.DEFAULT_TAGS[0]


def test_noindex_posts_are_not_syndicated(tmp_path):
    text = POST.replace("noindex: false", "noindex: true")
    assert syndicate_blog.parse_post(_write(tmp_path, "2026-08-27-x.md", text)) is None


def test_files_without_front_matter_are_skipped(tmp_path):
    assert syndicate_blog.parse_post(_write(tmp_path, "2026-08-27-x.md", "# no front matter")) is None


def test_devto_tag_is_capped_at_20_chars():
    devto, _hashnode = syndicate_blog._tag_sets(
        ["Field Service Automation", "MSP", "Dispatch Scheduling", "Tech Management", "Digital Automation"]
    )
    assert all(len(t) <= 20 and t.isalnum() for t in devto)
    assert devto[0] == "fieldserviceautomation"[:20]


def test_hashnode_tags_survive_devto_prefix_collision():
    devto, hashnode = syndicate_blog._tag_sets(
        ["abcdefghij klmnopqrst1", "abcdefghij klmnopqrst2", "msp"]
    )
    assert devto == ["abcdefghijklmnopqrst", "msp"]
    assert [h["slug"] for h in hashnode] == [
        "abcdefghij-klmnopqrst1", "abcdefghij-klmnopqrst2", "msp"]


def _post(tmp_path, name="2026-08-27-x.md"):
    return syndicate_blog.parse_post(_write(tmp_path, name, POST))


def test_devto_postmap_unchanged_skips(tmp_path, monkeypatch, capsys):
    post = _post(tmp_path)
    monkeypatch.setenv("DEVTO_API_KEY", "k")
    calls = []

    def fake_api(url, headers, body=None, method=None):
        calls.append(url)
        return [] if method is None else {}

    monkeypatch.setattr(syndicate_blog, "_api", fake_api)
    postmap = {post["slug"]: {"devto": {"id": 42, "url": "u", "hash": syndicate_blog._content_hash(post)}}}
    assert syndicate_blog.devto_publish([post], False, postmap) is False
    assert calls == ["https://dev.to/api/articles/me/all?per_page=200"], "no write call for unchanged post"
    assert "unchanged" in capsys.readouterr().out


def test_devto_postmap_changed_updates_via_put(tmp_path, monkeypatch):
    post = _post(tmp_path)
    monkeypatch.setenv("DEVTO_API_KEY", "k")
    monkeypatch.setattr(syndicate_blog.time, "sleep", lambda *_: None)
    calls = []

    def fake_api(url, headers, body=None, method=None):
        calls.append((method, url))
        return [] if method is None else {"id": 42, "url": "https://dev.to/x"}

    monkeypatch.setattr(syndicate_blog, "_api", fake_api)
    postmap = {post["slug"]: {"devto": {"id": 42, "url": "u", "hash": "stale"}}}
    assert syndicate_blog.devto_publish([post], False, postmap) is True
    assert ("PUT", "https://dev.to/api/articles/42") in calls, "changed content updates the same article"
    assert postmap[post["slug"]]["devto"]["hash"] == syndicate_blog._content_hash(post)


def test_devto_new_slug_publishes_and_records(tmp_path, monkeypatch):
    post = _post(tmp_path)
    monkeypatch.setenv("DEVTO_API_KEY", "k")
    monkeypatch.setattr(syndicate_blog.time, "sleep", lambda *_: None)

    def fake_api(url, headers, body=None, method=None):
        return [] if body is None else {"id": 7, "url": "https://dev.to/new"}

    monkeypatch.setattr(syndicate_blog, "_api", fake_api)
    postmap = {}
    assert syndicate_blog.devto_publish([post], False, postmap) is True
    assert postmap[post["slug"]]["devto"] == {
        "id": 7, "url": "https://dev.to/new", "hash": syndicate_blog._content_hash(post)}


def test_hashnode_postmap_survives_listing_gaps(tmp_path, monkeypatch, capsys):
    post = _post(tmp_path)
    monkeypatch.setenv("HASHNODE_API_KEY", "k")
    monkeypatch.setenv("HASHNODE_PUB_ID", "p")
    published = []

    def fake_api(url, headers, body=None, method=None):
        if body and "publishPost" in body.get("query", ""):
            published.append(body)
            return {"data": {"publishPost": {"post": {"url": "https://hn/x"}}}}
        return {"data": {"publication": {"posts": {"edges": []}}}}

    monkeypatch.setattr(syndicate_blog, "_api", fake_api)
    postmap = {post["slug"]: {"hashnode": {"url": "https://hn/existing"}}}
    assert syndicate_blog.hashnode_publish([post], False, postmap) is False
    assert published == [], "postmap hit must not re-publish even when the listing is empty"
    assert "already published" in capsys.readouterr().out


def test_postmap_roundtrip(tmp_path, monkeypatch):
    target = tmp_path / "state" / "postmap.json"
    monkeypatch.setattr(syndicate_blog, "POSTMAP_PATH", target)
    assert syndicate_blog._load_postmap() == {}
    syndicate_blog._save_postmap({"a": {"devto": {"id": 1}}})
    assert syndicate_blog._load_postmap() == {"a": {"devto": {"id": 1}}}
