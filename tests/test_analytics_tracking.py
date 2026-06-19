"""
Unit tests for analytics tracking system.

Tests MongoDB and PostgreSQL tracking layers with sample data.

Run with:
    pytest tests/test_analytics_tracking.py -v
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

import pytest

# Make sure lib is in path
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))

from analytics_tracker import (
    AnalyticsTrackingManager,
    ArticleMetadata,
    PlatformDistribution,
    UserEngagement,
    ChannelRevenue,
    SocialEngagement,
    VideoMetrics,
    PublishPlatform,
    EngagementType,
)


class TestAnalyticsDataModels:
    """Test data model initialization."""

    def test_article_metadata_creation(self) -> None:
        """Test ArticleMetadata dataclass."""
        meta = ArticleMetadata(
            article_id="test-123",
            title="Test Article",
            topic="automation",
            slug="test-article",
            publish_date=datetime.now(timezone.utc).isoformat(),
            word_count=1500,
            tags=["automation", "revenue"],
            quality_score=0.85,
        )

        assert meta.article_id == "test-123"
        assert meta.title == "Test Article"
        assert meta.word_count == 1500
        assert meta.quality_score == 0.85
        assert meta.created_at  # Should be auto-filled

    def test_platform_distribution_creation(self) -> None:
        """Test PlatformDistribution dataclass."""
        dist = PlatformDistribution(
            distribution_id="dist-123",
            article_id="article-123",
            platform=PublishPlatform.TWITTER,
            published_at=datetime.now(timezone.utc).isoformat(),
            url="https://twitter.com/...",
            status="success",
        )

        assert dist.platform == PublishPlatform.TWITTER
        assert dist.status == "success"
        assert dist.metadata == {}  # Should be initialized
        assert dist.created_at  # Should be auto-filled

    def test_user_engagement_creation(self) -> None:
        """Test UserEngagement dataclass."""
        engagement = UserEngagement(
            engagement_id="eng-123",
            article_id="article-123",
            platform=PublishPlatform.BLOG,
            engagement_type=EngagementType.CLICK,
            user_country="US",
            user_device="mobile",
            click_source="social",
            is_conversion=True,
            conversion_value_usd=5.50,
        )

        assert engagement.engagement_type == EngagementType.CLICK
        assert engagement.is_conversion is True
        assert engagement.conversion_value_usd == 5.50
        assert engagement.created_at

    def test_social_engagement_creation(self) -> None:
        """Test SocialEngagement dataclass."""
        social = SocialEngagement(
            metric_id="social-123",
            article_id="article-123",
            platform=PublishPlatform.TWITTER,
            post_id="tweet-123",
            likes=42,
            shares=8,
            comments=3,
            impressions=500,
            reach=300,
        )

        assert social.likes == 42
        assert social.shares == 8
        # Engagement rate should be calculated: (42 + 8 + 3) / 500 * 100 = 10.6%
        expected_rate = (42 + 8 + 3 + 0) / 500 * 100
        assert social.engagement_rate == expected_rate

    def test_video_metrics_creation(self) -> None:
        """Test VideoMetrics dataclass."""
        video = VideoMetrics(
            video_id="video-123",
            article_id="article-123",
            platform=PublishPlatform.YOUTUBE,
            video_title="Test Video",
            views=1000,
            watch_time_minutes=500.0,
            clicks=50,
            shares=10,
        )

        assert video.views == 1000
        assert video.watch_time_minutes == 500.0
        # Watch time % should be: (500 / 1000) * 100 = 50% (only capped at 100 if exceeds)
        assert video.watch_time_percentage == 50.0


class TestAnalyticsTrackingManager:
    """Test the unified tracking manager."""

    @pytest.fixture
    def manager(self) -> AnalyticsTrackingManager:
        """Create a test analytics manager (with MongoDB/PostgreSQL if available)."""
        manager = AnalyticsTrackingManager()
        yield manager
        manager.close()

    def test_manager_initialization(self) -> None:
        """Test manager can be initialized."""
        manager = AnalyticsTrackingManager()
        # Should not raise even if databases not available
        assert manager is not None
        manager.close()

    def test_log_article_published(self, manager: AnalyticsTrackingManager) -> None:
        """Test logging a published article."""
        article_id = manager.log_article_published(
            title="Test Article",
            topic="automation",
            slug="test-article",
            word_count=1500,
            tags=["automation", "revenue"],
            quality_score=0.85,
        )

        assert article_id
        assert len(article_id) > 0

    def test_log_platform_distribution(self, manager: AnalyticsTrackingManager) -> None:
        """Test logging platform distribution."""
        article_id = manager.log_article_published(
            title="Test",
            topic="test",
            slug="test",
            word_count=100,
            tags=[],
        )

        success = manager.log_platform_distribution(
            article_id=article_id,
            platform=PublishPlatform.TWITTER,
            url="https://twitter.com/...",
            status="success",
        )

        assert isinstance(success, bool)

    def test_log_user_engagement(self, manager: AnalyticsTrackingManager) -> None:
        """Test logging user engagement."""
        article_id = manager.log_article_published(
            title="Test",
            topic="test",
            slug="test",
            word_count=100,
            tags=[],
        )

        success = manager.log_user_engagement(
            article_id=article_id,
            platform=PublishPlatform.BLOG,
            engagement_type=EngagementType.CLICK,
            is_conversion=False,
        )

        assert isinstance(success, bool)

    def test_log_channel_revenue(self, manager: AnalyticsTrackingManager) -> None:
        """Test logging channel revenue."""
        article_id = manager.log_article_published(
            title="Test",
            topic="test",
            slug="test",
            word_count=100,
            tags=[],
        )

        success = manager.log_channel_revenue(
            article_id=article_id,
            platform=PublishPlatform.GUMROAD,
            channel="ebook",
            revenue_usd=4.99,
        )

        assert isinstance(success, bool)

    def test_log_social_metrics(self, manager: AnalyticsTrackingManager) -> None:
        """Test logging social metrics."""
        article_id = manager.log_article_published(
            title="Test",
            topic="test",
            slug="test",
            word_count=100,
            tags=[],
        )

        success = manager.log_social_metrics(
            article_id=article_id,
            platform=PublishPlatform.TWITTER,
            post_id="tweet-123",
            likes=42,
            shares=8,
            impressions=500,
        )

        assert isinstance(success, bool)

    def test_log_video_metrics(self, manager: AnalyticsTrackingManager) -> None:
        """Test logging video metrics."""
        article_id = manager.log_article_published(
            title="Test",
            topic="test",
            slug="test",
            word_count=100,
            tags=[],
        )

        success = manager.log_video_metrics(
            article_id=article_id,
            platform=PublishPlatform.YOUTUBE,
            video_id="vid-123",
            video_title="Test Video",
            views=1000,
            watch_time_minutes=500,
        )

        assert isinstance(success, bool)

    def test_get_analytics_summary(self, manager: AnalyticsTrackingManager) -> None:
        """Test getting analytics summary."""
        article_id = manager.log_article_published(
            title="Test",
            topic="test",
            slug="test",
            word_count=100,
            tags=[],
        )

        # Log some events
        manager.log_platform_distribution(
            article_id=article_id,
            platform=PublishPlatform.BLOG,
            url="https://blog.example.com/test",
            status="success",
        )

        manager.log_user_engagement(
            article_id=article_id,
            platform=PublishPlatform.BLOG,
            engagement_type=EngagementType.CLICK,
        )

        # Get summary
        summary = manager.get_analytics_summary(article_id)
        assert summary["article_id"] == article_id
        assert "timestamp" in summary
        assert "mongodb" in summary
        assert "postgresql" in summary


class TestEnumValues:
    """Test enum values."""

    def test_publish_platform_enum(self) -> None:
        """Test PublishPlatform enum."""
        assert PublishPlatform.BLOG.value == "blog"
        assert PublishPlatform.TWITTER.value == "twitter"
        assert PublishPlatform.GUMROAD.value == "gumroad"
        assert PublishPlatform.YOUTUBE.value == "youtube"

    def test_engagement_type_enum(self) -> None:
        """Test EngagementType enum."""
        assert EngagementType.CLICK.value == "click"
        assert EngagementType.VIEW.value == "view"
        assert EngagementType.LIKE.value == "like"
        assert EngagementType.SHARE.value == "share"


class TestIntegrationWithPublisher:
    """Test integration with publish_article_resilient.py."""

    def test_analytics_hook_import(self) -> None:
        """Test that analytics integration can be imported."""
        try:
            from analytics_integration import (  # type: ignore[import-not-found]
                PublishingAnalyticsHook,
                create_analytics_hook,
            )

            hook = create_analytics_hook()
            assert hook is not None
            hook.close()
        except ImportError as e:
            pytest.skip(f"analytics_integration not available: {e}")

    def test_analytics_hook_methods(self) -> None:
        """Test analytics hook has required methods."""
        try:
            from analytics_integration import create_analytics_hook  # type: ignore[import-not-found]

            hook = create_analytics_hook()

            # Check methods exist
            assert hasattr(hook, "on_article_generated")
            assert hasattr(hook, "on_github_published")
            assert hasattr(hook, "on_social_distribution_complete")
            assert hasattr(hook, "on_ecommerce_distribution_complete")
            assert hasattr(hook, "on_user_click")
            assert hasattr(hook, "on_conversion")
            assert hasattr(hook, "generate_analytics_report")

            hook.close()
        except ImportError as e:
            pytest.skip(f"analytics_integration not available: {e}")


class TestDataIntegrity:
    """Test data integrity and validation."""

    @pytest.fixture
    def manager(self) -> AnalyticsTrackingManager:
        """Create a test analytics manager (with MongoDB/PostgreSQL if available)."""
        manager = AnalyticsTrackingManager()
        yield manager
        manager.close()

    def test_article_id_uniqueness(self, manager: AnalyticsTrackingManager) -> None:
        """Test that article IDs are unique."""
        id1 = manager.log_article_published(
            title="Article 1",
            topic="test",
            slug="article-1",
            word_count=100,
            tags=[],
        )

        id2 = manager.log_article_published(
            title="Article 2",
            topic="test",
            slug="article-2",
            word_count=100,
            tags=[],
        )

        assert id1 != id2

    def test_engagement_rate_calculation(self) -> None:
        """Test engagement rate is calculated correctly."""
        social = SocialEngagement(
            metric_id="test-123",
            article_id="article-123",
            platform=PublishPlatform.TWITTER,
            post_id="tweet-123",
            likes=100,
            shares=20,
            comments=10,
            impressions=1000,
        )

        # Expected: (100 + 20 + 10) / 1000 * 100 = 13%
        expected = (100 + 20 + 10 + 0) / 1000 * 100
        assert social.engagement_rate == expected

    def test_watch_time_percentage_capped(self) -> None:
        """Test watch time percentage is capped at 100."""
        # Very high watch time (10 min video, 500 min watched)
        video = VideoMetrics(
            video_id="test-123",
            article_id="article-123",
            platform=PublishPlatform.YOUTUBE,
            video_title="Test",
            views=100,
            watch_time_minutes=500.0,
        )

        assert video.watch_time_percentage == 100.0  # Capped


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
