"""
Affiliate injection in scripts/publish_article.py.

The 2026-06-12 funnel audit found published articles carried zero external
affiliate links: token replacement only fires on [AFFILIATE:...] tokens the
generator never emits. These tests pin the full monetization pass.
"""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _load(monkeypatch, links: dict | None = None, amazon_tag: str = "alreadyhere-20"):
    monkeypatch.setenv("AFFILIATE_LINKS", json.dumps(links or {}))
    monkeypatch.setenv("AMAZON_PARTNER_TAG", amazon_tag)
    import scripts.publish_article as pa
    importlib.reload(pa)
    return pa


class TestInjectAffiliates:
    def test_noop_when_map_empty(self, monkeypatch):
        pa = _load(monkeypatch, {})
        body = "Plain article about VPS hosting with no links."
        assert pa._inject_affiliates(body) == body

    def test_token_replacement(self, monkeypatch):
        pa = _load(monkeypatch, {"VPS hosting": "https://m.do.co/c/realref"})
        out = pa._inject_affiliates("Try [AFFILIATE:VPS hosting] today.")
        assert "[VPS hosting](https://m.do.co/c/realref)" in out

    def test_unresolved_tokens_stripped(self, monkeypatch):
        pa = _load(monkeypatch, {})
        out = pa._inject_affiliates("Check [AFFILIATE:Unknown Tool] now.")
        assert "[AFFILIATE:" not in out
        assert "Unknown Tool" in out

    def test_keyword_auto_linked_once(self, monkeypatch):
        pa = _load(monkeypatch, {"VPS hosting": "https://m.do.co/c/realref"})
        body = "VPS hosting is great.\n\nMore about VPS hosting here."
        out = pa._inject_affiliates(body)
        prose, _, recommended = out.partition("## Recommended Tools")
        # first occurrence linked, second left plain; link repeats in the box
        assert prose.count("[VPS hosting](https://m.do.co/c/realref)") == 1
        assert "More about VPS hosting here." in prose
        assert recommended.count("https://m.do.co/c/realref") == 1

    def test_headings_and_code_not_linked(self, monkeypatch):
        pa = _load(monkeypatch, {"VPS hosting": "https://m.do.co/c/realref"})
        body = "## VPS hosting\n\n```\nVPS hosting in code\n```\n"
        out = pa._inject_affiliates(body)
        assert "## VPS hosting\n" in out
        assert "```\nVPS hosting in code\n```" in out

    def test_existing_links_not_double_wrapped(self, monkeypatch):
        pa = _load(monkeypatch, {"VPS hosting": "https://m.do.co/c/realref"})
        body = "See [VPS hosting guide](https://example.org/guide) for details."
        out = pa._inject_affiliates(body)
        assert "[[" not in out
        assert "https://example.org/guide" in out

    def test_recommended_section_only_for_matched(self, monkeypatch):
        pa = _load(monkeypatch, {
            "VPS hosting": "https://m.do.co/c/realref",
            "email marketing": "https://convertkit.com/?ref=real",
        })
        out = pa._inject_affiliates("All about VPS hosting performance.")
        assert "## Recommended Tools" in out
        assert "https://m.do.co/c/realref" in out
        assert "convertkit" not in out  # unmatched keyword stays out

    def test_amazon_tag_appended_and_not_duplicated(self, monkeypatch):
        pa = _load(monkeypatch, {})
        body = ("Buy https://www.amazon.com/dp/B08N5WRWNW and "
                "https://www.amazon.com/dp/B07X?tag=other-20 today.")
        out = pa._inject_affiliates(body)
        assert "B08N5WRWNW?tag=alreadyhere-20" in out
        assert out.count("tag=") == 2
        assert "tag=other-20" in out


class TestPromptEnrichment:
    def test_prompt_lists_affiliate_keywords(self, monkeypatch):
        pa = _load(monkeypatch, {"VPS hosting": "https://m.do.co/c/realref"})
        keys = list(pa._affiliate_map().keys())
        assert keys == ["VPS hosting"]
