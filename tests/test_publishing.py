"""
Tests for multi-platform publishing stack:
  - hashnode_client
  - medium_client
  - blog_publisher (affiliate injection, multi-platform logic)
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure repo root is on the path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


# ─── hashnode_client ────────────────────────────────────────────────────────

class TestHashnodeClient:
    def test_raises_without_api_key(self, monkeypatch):
        monkeypatch.delenv("HASHNODE_API_KEY", raising=False)
        from runtime.hashnode_client import publish_article
        with pytest.raises(RuntimeError, match="HASHNODE_API_KEY"):
            publish_article("Test", "body")

    def test_raises_without_pub_id(self, monkeypatch):
        monkeypatch.setenv("HASHNODE_API_KEY", "hn_test_key")
        monkeypatch.delenv("HASHNODE_PUBLICATION_ID", raising=False)
        from runtime.hashnode_client import publish_article
        with pytest.raises(RuntimeError, match="HASHNODE_PUBLICATION_ID"):
            publish_article("Test", "body")

    def test_returns_url_on_success(self, monkeypatch):
        monkeypatch.setenv("HASHNODE_API_KEY", "hn_test_key")
        monkeypatch.setenv("HASHNODE_PUBLICATION_ID", "pub123")
        import httpx
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "data": {"publishPost": {"post": {"url": "https://hn.test/post", "id": "abc"}}}
        }
        with patch("httpx.post", return_value=mock_resp):
            from runtime import hashnode_client
            import importlib; importlib.reload(hashnode_client)
            monkeypatch.setenv("HASHNODE_API_KEY", "hn_test_key")
            monkeypatch.setenv("HASHNODE_PUBLICATION_ID", "pub123")
            result = hashnode_client.publish_article("Test Title", "## Body")
        assert result["url"] == "https://hn.test/post"
        assert result["id"] == "abc"

    def test_raises_on_graphql_error(self, monkeypatch):
        monkeypatch.setenv("HASHNODE_API_KEY", "hn_test_key")
        monkeypatch.setenv("HASHNODE_PUBLICATION_ID", "pub123")
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"errors": [{"message": "Publication not found"}]}
        with patch("httpx.post", return_value=mock_resp):
            from runtime import hashnode_client
            import importlib; importlib.reload(hashnode_client)
            monkeypatch.setenv("HASHNODE_API_KEY", "hn_test_key")
            monkeypatch.setenv("HASHNODE_PUBLICATION_ID", "pub123")
            with pytest.raises(RuntimeError, match="Hashnode API error"):
                hashnode_client.publish_article("Test", "body")


# ─── medium_client ──────────────────────────────────────────────────────────

class TestMediumClient:
    def test_raises_without_api_key(self, monkeypatch):
        monkeypatch.delenv("MEDIUM_API_KEY", raising=False)
        from runtime.medium_client import publish_article
        with pytest.raises(RuntimeError, match="MEDIUM_API_KEY"):
            publish_article("Test", "body")

    def test_raises_without_author_id(self, monkeypatch):
        monkeypatch.setenv("MEDIUM_API_KEY", "med_test_key")
        monkeypatch.delenv("MEDIUM_AUTHOR_ID", raising=False)
        from runtime.medium_client import publish_article
        with pytest.raises(RuntimeError, match="MEDIUM_AUTHOR_ID"):
            publish_article("Test", "body")

    def test_returns_url_on_success(self, monkeypatch):
        monkeypatch.setenv("MEDIUM_API_KEY", "med_test_key")
        monkeypatch.setenv("MEDIUM_AUTHOR_ID", "author123")
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "data": {"url": "https://medium.com/@user/test-post", "id": "xyz"}
        }
        with patch("httpx.post", return_value=mock_resp):
            from runtime import medium_client
            import importlib; importlib.reload(medium_client)
            monkeypatch.setenv("MEDIUM_API_KEY", "med_test_key")
            monkeypatch.setenv("MEDIUM_AUTHOR_ID", "author123")
            result = medium_client.publish_article("Test Title", "## Body")
        assert "medium.com" in result["url"]


# ─── blog_publisher — affiliate injection ───────────────────────────────────

class TestAffiliateInjection:
    def test_affiliate_placeholder_replaced(self, monkeypatch):
        monkeypatch.setenv("AFFILIATE_LINKS", json.dumps({"Hostinger": "https://hostinger.com?ref=test"}))
        monkeypatch.setenv("AMAZON_PARTNER_TAG", "")
        from runtime.agent_impls import blog_publisher
        import importlib; importlib.reload(blog_publisher)
        result = blog_publisher._inject_affiliates("Check out [AFFILIATE:Hostinger] for hosting.")
        assert "[AFFILIATE:Hostinger]" not in result
        assert "https://hostinger.com?ref=test" in result

    def test_unresolved_placeholder_stripped(self, monkeypatch):
        monkeypatch.setenv("AFFILIATE_LINKS", "{}")
        monkeypatch.setenv("AMAZON_PARTNER_TAG", "")
        from runtime.agent_impls import blog_publisher
        import importlib; importlib.reload(blog_publisher)
        result = blog_publisher._inject_affiliates("Check [AFFILIATE:UnknownProduct] now.")
        assert "[AFFILIATE:" not in result
        assert "UnknownProduct" in result  # text preserved, just the brackets removed

    def test_amazon_tag_appended(self, monkeypatch):
        monkeypatch.setenv("AFFILIATE_LINKS", "{}")
        monkeypatch.setenv("AMAZON_PARTNER_TAG", "alreadyhere-20")
        from runtime.agent_impls import blog_publisher
        import importlib; importlib.reload(blog_publisher)
        body = "Buy it: https://www.amazon.com/dp/B08N5WRWNW"
        result = blog_publisher._inject_affiliates(body)
        assert "tag=alreadyhere-20" in result

    def test_amazon_tag_not_duplicated(self, monkeypatch):
        monkeypatch.setenv("AFFILIATE_LINKS", "{}")
        monkeypatch.setenv("AMAZON_PARTNER_TAG", "alreadyhere-20")
        from runtime.agent_impls import blog_publisher
        import importlib; importlib.reload(blog_publisher)
        body = "https://www.amazon.com/dp/B08?tag=other-20"
        result = blog_publisher._inject_affiliates(body)
        assert result.count("tag=") == 1  # existing tag not duplicated


# ─── blog_publisher — multi-platform routing ────────────────────────────────

class TestBlogPublisherRouting:
    def _make_article_context(self) -> str:
        article = {
            "title": "Test Article",
            "slug": "test-article",
            "meta_description": "A test article.",
            "tags": ["ai", "test"],
            "body": "## Section\n\nContent here.",
        }
        return f"ARTICLE_JSON:{json.dumps(article)}"

    def test_publishes_to_github_and_devto(self, monkeypatch, tmp_path):
        monkeypatch.setenv("DEVTO_API_KEY", "devto_test")
        monkeypatch.setenv("AFFILIATE_LINKS", "{}")
        monkeypatch.setenv("AMAZON_PARTNER_TAG", "")
        monkeypatch.delenv("HASHNODE_API_KEY", raising=False)
        monkeypatch.delenv("MEDIUM_API_KEY", raising=False)

        mock_gh = MagicMock(return_value={"html_url": "https://github.com/test/post"})
        mock_devto = MagicMock(return_value={"url": "https://dev.to/user/test"})
        mock_email = MagicMock()

        with patch("runtime.github_client.publish_file", mock_gh), \
             patch("runtime.devto_client.publish_article", mock_devto), \
             patch("runtime.gmail_client.send_email", mock_email):
            from runtime.agent_impls import blog_publisher
            import importlib; importlib.reload(blog_publisher)
            agent = blog_publisher.Agent()
            result = agent.run("Write test", self._make_article_context(), [])

        assert result.metrics["published_count"] == 2
        assert "GitHub Pages" in result.metrics["platforms"]
        assert "Dev.to" in result.metrics["platforms"]

    def test_skips_hashnode_when_no_key(self, monkeypatch):
        monkeypatch.delenv("HASHNODE_API_KEY", raising=False)
        monkeypatch.setenv("AFFILIATE_LINKS", "{}")
        monkeypatch.setenv("AMAZON_PARTNER_TAG", "")

        mock_gh = MagicMock(return_value={"html_url": "https://github.com/test/post"})
        mock_devto = MagicMock(return_value={"url": "https://dev.to/user/test"})
        mock_email = MagicMock()

        with patch("runtime.github_client.publish_file", mock_gh), \
             patch("runtime.devto_client.publish_article", mock_devto), \
             patch("runtime.gmail_client.send_email", mock_email):
            from runtime.agent_impls import blog_publisher
            import importlib; importlib.reload(blog_publisher)
            agent = blog_publisher.Agent()
            result = agent.run("Test", self._make_article_context(), [])

        assert "Hashnode" not in result.metrics["platforms"]

    def test_ftc_disclosure_in_github_markdown(self, monkeypatch):
        monkeypatch.setenv("AFFILIATE_LINKS", "{}")
        monkeypatch.setenv("AMAZON_PARTNER_TAG", "")
        from runtime.agent_impls import blog_publisher
        import importlib; importlib.reload(blog_publisher)
        article = {"title": "T", "meta_description": "", "tags": [], "body": "body"}
        md = blog_publisher._make_github_markdown(article, "2026-05-25")
        assert "FTC Disclosure" in md or "affiliate" in md.lower()
