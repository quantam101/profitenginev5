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
