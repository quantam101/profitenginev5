#!/usr/bin/env python3
"""
Unit tests for social_media_publishers.py

Tests cover:
- Credential validation and graceful skipping when not configured
- Mock API responses for each platform
- Error handling and logging
- URL format validation
- Cross-platform batch publishing

Run: pytest tests/test_social_media_publishers.py -v
"""
from __future__ import annotations

import os
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from typing import Dict, Any

# Check for optional dependencies
TWEEPY_AVAILABLE = True
PRAW_AVAILABLE = True
try:
    import tweepy
except ImportError:
    TWEEPY_AVAILABLE = False

try:
    import praw
except ImportError:
    PRAW_AVAILABLE = False

# Import the publishers module
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from social_media_publishers import (
    publish_twitter,
    publish_reddit,
    publish_linkedin,
    publish_facebook,
    publish_instagram,
    publish_tiktok,
    publish_youtube,
    publish_to_all_platforms,
)


# ── Test Data ──────────────────────────────────────────────────────────────────

SAMPLE_ARTICLE = {
    "title": "10 Proven Trading Strategies for 2024",
    "meta_description": "Learn the most effective trading strategies used by professional traders",
    "body": "In this comprehensive guide, we explore 10 proven trading strategies that have been tested in real market conditions...",
    "author": "ProfitEngine Team",
    "published_date": "2024-01-15",
}

CANONICAL_URL = "https://profitengine.alreadyherellc.com/blog/trading-strategies"
IMAGE_URL = "https://cdn.profitengine.com/trading-strategies.jpg"
VIDEO_URL = "https://cdn.profitengine.com/trading-strategies.mp4"
VIDEO_PATH = "/tmp/trading-strategies.mp4"


# ── Twitter/X Tests ────────────────────────────────────────────────────────────

@pytest.mark.skipif(not TWEEPY_AVAILABLE, reason="tweepy library not installed")
class TestTwitterPublisher:
    """Test Twitter/X publishing with OAuth 2.0"""

    def test_skip_without_credentials(self, monkeypatch):
        """Should skip publishing when API credentials not configured"""
        monkeypatch.delenv("TWITTER_API_KEY", raising=False)
        monkeypatch.delenv("TWITTER_API_SECRET", raising=False)
        monkeypatch.delenv("TWITTER_BEARER_TOKEN", raising=False)

        result = publish_twitter(SAMPLE_ARTICLE, CANONICAL_URL)
        assert result is None

    @patch("tweepy.Client")
    def test_publish_with_bearer_token(self, mock_client_class, monkeypatch):
        """Should publish using Bearer Token (preferred OAuth 2.0 v2)"""
        monkeypatch.setenv("TWITTER_BEARER_TOKEN", "test-bearer-token")

        # Mock tweepy.Client
        mock_client = MagicMock()
        mock_client.create_tweet.return_value.data = {"id": "1234567890"}
        mock_client_class.return_value = mock_client

        result = publish_twitter(SAMPLE_ARTICLE, CANONICAL_URL)

        assert result is not None
        assert "1234567890" in result
        assert result.startswith("https://twitter.com/")

    def test_skip_without_tweepy(self, monkeypatch):
        """Should gracefully skip if tweepy not installed"""
        monkeypatch.setenv("TWITTER_API_KEY", "test-key")
        monkeypatch.setenv("TWITTER_API_SECRET", "test-secret")

        with patch.dict("sys.modules", {"tweepy": None}):
            result = publish_twitter(SAMPLE_ARTICLE, CANONICAL_URL)
            assert result is None


# ── Reddit Tests ───────────────────────────────────────────────────────────────

@pytest.mark.skipif(not PRAW_AVAILABLE, reason="praw library not installed")
class TestRedditPublisher:
    """Test Reddit OAuth 2.0 publishing"""

    def test_skip_without_credentials(self, monkeypatch):
        """Should skip when Reddit credentials not configured"""
        monkeypatch.delenv("REDDIT_CLIENT_ID", raising=False)
        monkeypatch.delenv("REDDIT_CLIENT_SECRET", raising=False)

        result = publish_reddit(SAMPLE_ARTICLE, CANONICAL_URL)
        assert result is None

    def test_skip_without_subreddit(self, monkeypatch):
        """Should skip when target subreddit not specified"""
        monkeypatch.setenv("REDDIT_CLIENT_ID", "test-id")
        monkeypatch.setenv("REDDIT_CLIENT_SECRET", "test-secret")
        monkeypatch.setenv("REDDIT_USERNAME", "bot_account")
        monkeypatch.setenv("REDDIT_PASSWORD", "password123")
        monkeypatch.delenv("REDDIT_SUBREDDIT", raising=False)

        result = publish_reddit(SAMPLE_ARTICLE, CANONICAL_URL)
        assert result is None

    @patch("praw.Reddit")
    def test_publish_link_post(self, mock_reddit_class, monkeypatch):
        """Should submit link post to Reddit subreddit"""
        monkeypatch.setenv("REDDIT_CLIENT_ID", "test-id")
        monkeypatch.setenv("REDDIT_CLIENT_SECRET", "test-secret")
        monkeypatch.setenv("REDDIT_USERNAME", "bot_account")
        monkeypatch.setenv("REDDIT_PASSWORD", "password123")
        monkeypatch.setenv("REDDIT_SUBREDDIT", "investing")

        # Mock Reddit instance
        mock_reddit = MagicMock()
        mock_reddit.user.me.return_value = MagicMock()  # Auth check
        mock_subreddit = MagicMock()
        mock_submission = MagicMock()
        mock_submission.permalink = "/r/investing/comments/abc123/..."

        mock_reddit.subreddit.return_value = mock_subreddit
        mock_subreddit.submit.return_value = mock_submission
        mock_reddit_class.return_value = mock_reddit

        result = publish_reddit(SAMPLE_ARTICLE, CANONICAL_URL)

        assert result is not None
        assert "reddit.com" in result
        assert "abc123" in result


# ── LinkedIn Tests ─────────────────────────────────────────────────────────────

class TestLinkedInPublisher:
    """Test LinkedIn OAuth 2.0 REST API publishing"""

    def test_skip_without_token(self, monkeypatch):
        """Should skip without access token"""
        monkeypatch.delenv("LINKEDIN_ACCESS_TOKEN", raising=False)

        result = publish_linkedin(SAMPLE_ARTICLE, CANONICAL_URL)
        assert result is None

    def test_skip_without_urn(self, monkeypatch):
        """Should skip without Person URN or Organization URN"""
        monkeypatch.setenv("LINKEDIN_ACCESS_TOKEN", "test-token")
        monkeypatch.delenv("LINKEDIN_PERSON_URN", raising=False)
        monkeypatch.delenv("LINKEDIN_ORGANIZATION_URN", raising=False)

        result = publish_linkedin(SAMPLE_ARTICLE, CANONICAL_URL)
        assert result is None

    @patch("httpx.post")
    def test_publish_personal_post(self, mock_post, monkeypatch):
        """Should publish to personal LinkedIn profile"""
        monkeypatch.setenv("LINKEDIN_ACCESS_TOKEN", "test-token")
        monkeypatch.setenv("LINKEDIN_PERSON_URN", "urn:li:person:123456")

        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": "urn:li:activity:1234567890"}
        mock_post.return_value = mock_response

        result = publish_linkedin(SAMPLE_ARTICLE, CANONICAL_URL)

        assert result is not None
        assert "linkedin.com" in result

    @patch("httpx.post")
    def test_publish_company_post(self, mock_post, monkeypatch):
        """Should publish to company LinkedIn page"""
        monkeypatch.setenv("LINKEDIN_ACCESS_TOKEN", "test-token")
        monkeypatch.setenv("LINKEDIN_ORGANIZATION_URN", "urn:li:organization:12345")

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": "urn:li:activity:9876543210"}
        mock_post.return_value = mock_response

        result = publish_linkedin(SAMPLE_ARTICLE, CANONICAL_URL)

        assert result is not None


# ── Facebook Tests ────────────────────────────────────────────────────────────

class TestFacebookPublisher:
    """Test Facebook Graph API publishing"""

    def test_skip_without_credentials(self, monkeypatch):
        """Should skip without page ID or token"""
        monkeypatch.delenv("FB_PAGE_ID", raising=False)

        result = publish_facebook(SAMPLE_ARTICLE, CANONICAL_URL)
        assert result is None

    @patch("httpx.post")
    def test_publish_feed_post(self, mock_post, monkeypatch):
        """Should post to Facebook page feed"""
        monkeypatch.setenv("FB_PAGE_ID", "123456789")
        monkeypatch.setenv("FB_PAGE_ACCESS_TOKEN", "test-token")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "123456789_987654321"}
        mock_post.return_value = mock_response

        result = publish_facebook(SAMPLE_ARTICLE, CANONICAL_URL)

        assert result is not None
        assert "facebook.com" in result


# ── Instagram Tests ────────────────────────────────────────────────────────────

class TestInstagramPublisher:
    """Test Instagram Graph API publishing (business account)"""

    def test_skip_without_image(self, monkeypatch):
        """Should skip without image_url"""
        monkeypatch.setenv("IG_USER_ID", "123456")
        monkeypatch.setenv("FB_PAGE_ACCESS_TOKEN", "test-token")

        result = publish_instagram(SAMPLE_ARTICLE)
        assert result is None

    @patch("httpx.post")
    def test_publish_photo_post(self, mock_post, monkeypatch):
        """Should create and publish Instagram photo post (2-step process)"""
        monkeypatch.setenv("IG_USER_ID", "123456")
        monkeypatch.setenv("FB_PAGE_ACCESS_TOKEN", "test-token")

        # Mock create media response
        create_response = MagicMock()
        create_response.status_code = 200
        create_response.json.return_value = {"id": "media123"}
        create_response.headers = {"content-type": "application/json"}

        # Mock publish response
        publish_response = MagicMock()
        publish_response.status_code = 200
        publish_response.json.return_value = {"id": "media123"}
        publish_response.headers = {"content-type": "application/json"}

        mock_post.side_effect = [create_response, publish_response]

        result = publish_instagram(SAMPLE_ARTICLE, image_url=IMAGE_URL)

        assert result is not None
        assert "instagram.com" in result


# ── TikTok Tests ───────────────────────────────────────────────────────────────

class TestTikTokPublisher:
    """Test TikTok OAuth 2.0 publishing"""

    def test_skip_without_token(self, monkeypatch):
        """Should skip without access token"""
        monkeypatch.delenv("TIKTOK_ACCESS_TOKEN", raising=False)

        result = publish_tiktok(SAMPLE_ARTICLE, video_url=VIDEO_URL)
        assert result is None

    def test_skip_without_video_url(self, monkeypatch):
        """Should skip without video_url"""
        monkeypatch.setenv("TIKTOK_ACCESS_TOKEN", "test-token")

        result = publish_tiktok(SAMPLE_ARTICLE)
        assert result is None

    @patch("httpx.post")
    def test_publish_video(self, mock_post, monkeypatch):
        """Should upload video to TikTok"""
        monkeypatch.setenv("TIKTOK_ACCESS_TOKEN", "test-token")
        monkeypatch.setenv("TIKTOK_OPEN_ID", "ot12345")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "data": {"video_id": "vid123456"}
        }
        mock_post.return_value = mock_response

        result = publish_tiktok(SAMPLE_ARTICLE, video_url=VIDEO_URL)

        assert result is not None
        assert "tiktok.com" in result


# ── YouTube Tests ──────────────────────────────────────────────────────────────

class TestYouTubePublisher:
    """Test YouTube OAuth 2.0 publishing"""

    def test_skip_without_credentials(self, monkeypatch):
        """Should skip without OAuth 2.0 credentials"""
        monkeypatch.delenv("YOUTUBE_CLIENT_ID", raising=False)

        result = publish_youtube(SAMPLE_ARTICLE, video_path=VIDEO_PATH)
        assert result is None

    def test_skip_without_valid_video_path(self, monkeypatch):
        """Should skip if video file not found"""
        monkeypatch.setenv("YOUTUBE_CLIENT_ID", "test-id")
        monkeypatch.setenv("YOUTUBE_CLIENT_SECRET", "test-secret")
        monkeypatch.setenv("YOUTUBE_REFRESH_TOKEN", "test-refresh")

        result = publish_youtube(SAMPLE_ARTICLE, video_path="/nonexistent/video.mp4")
        assert result is None


# ── Integration Tests ──────────────────────────────────────────────────────────

class TestBatchPublishing:
    """Test publishing to multiple platforms simultaneously"""

    @patch("scripts.social_media_publishers.publish_twitter")
    @patch("scripts.social_media_publishers.publish_reddit")
    @patch("scripts.social_media_publishers.publish_linkedin")
    def test_publish_to_all_platforms(self, mock_ln, mock_reddit, mock_twitter):
        """Should batch publish to all platforms and collect results"""
        mock_twitter.return_value = "https://twitter.com/i/web/status/123"
        mock_reddit.return_value = "https://reddit.com/r/investing/comments/abc"
        mock_ln.return_value = "https://linkedin.com/feed/update/urn:li:activity:123"

        results = publish_to_all_platforms(
            article=SAMPLE_ARTICLE,
            canonical_url=CANONICAL_URL,
            image_url=IMAGE_URL,
            video_url=VIDEO_URL,
        )

        assert isinstance(results, dict)
        assert "twitter" in results
        assert "reddit" in results
        assert "linkedin" in results


# ── Error Handling Tests ───────────────────────────────────────────────────────

class TestErrorHandling:
    """Test graceful error handling across all platforms"""

    @patch("httpx.post")
    def test_linkedin_api_error(self, mock_post, monkeypatch):
        """Should handle LinkedIn API 400 error"""
        monkeypatch.setenv("LINKEDIN_ACCESS_TOKEN", "test-token")
        monkeypatch.setenv("LINKEDIN_PERSON_URN", "urn:li:person:123")

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": {"message": "Invalid request"}
        }
        mock_response.headers = {"content-type": "application/json"}
        mock_post.return_value = mock_response

        result = publish_linkedin(SAMPLE_ARTICLE, CANONICAL_URL)
        assert result is None

    @patch("httpx.post")
    def test_facebook_api_error(self, mock_post, monkeypatch):
        """Should handle Facebook Graph API error"""
        monkeypatch.setenv("FB_PAGE_ID", "123456789")
        monkeypatch.setenv("FB_PAGE_ACCESS_TOKEN", "test-token")

        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.json.return_value = {
            "error": {"message": "Invalid token"}
        }
        mock_response.headers = {"content-type": "application/json"}
        mock_post.return_value = mock_response

        result = publish_facebook(SAMPLE_ARTICLE, CANONICAL_URL)
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
