"""
Integration of analytics tracking into publish_article_resilient.py.

This module provides hooks to log all publishing events, distribution results,
and engagement metrics into MongoDB and PostgreSQL.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from analytics_tracker import (
    AnalyticsTrackingManager,
    PublishPlatform,
    EngagementType,
)


class PublishingAnalyticsHook:
    """Hook to integrate analytics tracking into article publishing workflow."""

    def __init__(self, analytics_manager: Optional[AnalyticsTrackingManager] = None) -> None:
        """Initialize with optional analytics manager."""
        if analytics_manager is None:
            analytics_manager = AnalyticsTrackingManager()
        self.analytics = analytics_manager

    def on_article_generated(
        self,
        article: Dict[str, Any],
        topic: str,
    ) -> str:
        """Log when an article is generated."""
        if not self.analytics:
            return ""

        title = article.get("title", "Untitled")
        slug = article.get("slug", "")
        body = article.get("body", "")
        tags = article.get("tags", [])

        # Calculate word count
        word_count = len(body.split())

        # Calculate quality score (basic: 0.0-1.0 based on word count and tag count)
        quality_score = min(1.0, (word_count / 1000) * 0.7 + (len(tags) / 10) * 0.3)

        article_id = self.analytics.log_article_published(
            title=title,
            topic=topic,
            slug=slug,
            word_count=word_count,
            tags=tags,
            quality_score=quality_score,
        )

        print(f"[ANALYTICS] Article logged: {article_id}")
        return article_id

    def on_github_published(
        self,
        article_id: str,
        canonical_url: str,
    ) -> bool:
        """Log when article is published to GitHub Pages."""
        if not self.analytics:
            return False

        return self.analytics.log_platform_distribution(
            article_id=article_id,
            platform=PublishPlatform.BLOG,
            url=canonical_url,
            status="success",
            metadata={"source": "github_pages"},
        )

    def on_social_distribution_complete(
        self,
        article_id: str,
        social_results: Dict[str, Any],
    ) -> None:
        """Log social media distribution results."""
        if not self.analytics:
            return

        platform_map = {
            "twitter": PublishPlatform.TWITTER,
            "reddit": PublishPlatform.REDDIT,
            "facebook": PublishPlatform.FACEBOOK,
            "linkedin": PublishPlatform.LINKEDIN,
            "instagram": PublishPlatform.INSTAGRAM,
            "tiktok": PublishPlatform.TIKTOK,
            "telegram": PublishPlatform.TELEGRAM,
            "mastodon": PublishPlatform.MASTODON,
            "bluesky": PublishPlatform.BLUESKY,
        }

        for platform_name, result in social_results.items():
            if not isinstance(result, dict):
                continue

            platform = platform_map.get(platform_name)
            if not platform:
                continue

            status = result.get("status", "unknown")
            url = result.get("url", "")
            error = result.get("error", None) if status == "failed" else None

            self.analytics.log_platform_distribution(
                article_id=article_id,
                platform=platform,
                url=url,
                status=status,
                error_message=error,
                metadata=result,
            )

            print(f"[ANALYTICS] Social distribution logged: {platform_name} - {status}")

    def on_ecommerce_distribution_complete(
        self,
        article_id: str,
        ecommerce_results: Dict[str, Any],
    ) -> None:
        """Log e-commerce distribution results (Gumroad, Printify)."""
        if not self.analytics:
            return

        # Gumroad ebook
        gumroad_result = ecommerce_results.get("gumroad")
        if isinstance(gumroad_result, dict):
            status = gumroad_result.get("status", "unknown")
            url = gumroad_result.get("url", "")
            price = gumroad_result.get("price", 0)

            if status == "success":
                self.analytics.log_platform_distribution(
                    article_id=article_id,
                    platform=PublishPlatform.GUMROAD,
                    url=url,
                    status=status,
                    metadata={"product_id": gumroad_result.get("product_id"), "price": price},
                )

                # Log potential revenue (estimate: 1-2% conversion rate)
                estimated_revenue = price * 0.01  # Conservative 1% conversion
                self.analytics.log_channel_revenue(
                    article_id=article_id,
                    platform=PublishPlatform.GUMROAD,
                    channel="ebook",
                    revenue_usd=estimated_revenue,
                )

                print(f"[ANALYTICS] Gumroad distribution logged: {url}")

        # Printify POD products
        printify_result = ecommerce_results.get("printify")
        if isinstance(printify_result, dict):
            for product_type, result in printify_result.items():
                if isinstance(result, dict):
                    status = result.get("status", "unknown")
                    url = result.get("url", "")

                    if status in ("success", "pending_design"):
                        self.analytics.log_platform_distribution(
                            article_id=article_id,
                            platform=PublishPlatform.PRINTIFY,
                            url=url,
                            status=status,
                            metadata={"product_type": product_type},
                        )

                        # Log potential revenue per product
                        estimated_revenue = 5.0  # Conservative $5 profit per POD product
                        self.analytics.log_channel_revenue(
                            article_id=article_id,
                            platform=PublishPlatform.PRINTIFY,
                            channel=f"pod_{product_type}",
                            revenue_usd=estimated_revenue,
                        )

                        print(f"[ANALYTICS] Printify {product_type} logged: {url}")

    def on_priority_platforms_distribution(
        self,
        article_id: str,
        priority_results: Dict[str, Any],
    ) -> None:
        """Log priority platform distribution (Dev.to, Hashnode, Beehiiv, YouTube)."""
        if not self.analytics:
            return

        platform_map = {
            "devto": PublishPlatform.DEVTO,
            "dev.to": PublishPlatform.DEVTO,
            "hashnode": PublishPlatform.HASHNODE,
            "beehiiv": PublishPlatform.BEEHIIV,
            "youtube": PublishPlatform.YOUTUBE,
        }

        for platform_name, result in priority_results.items():
            if not isinstance(result, dict):
                continue

            platform = platform_map.get(platform_name.lower())
            if not platform:
                continue

            status = result.get("status", "unknown")
            url = result.get("url", "")
            error = result.get("error") if status == "failed" else None

            self.analytics.log_platform_distribution(
                article_id=article_id,
                platform=platform,
                url=url,
                status=status,
                error_message=error,
                metadata=result,
            )

            print(f"[ANALYTICS] Priority platform logged: {platform_name} - {status}")

    def on_newsletter_sent(
        self,
        article_id: str,
        newsletter_info: Dict[str, Any],
    ) -> bool:
        """Log newsletter distribution."""
        if not self.analytics:
            return False

        return self.analytics.log_platform_distribution(
            article_id=article_id,
            platform=PublishPlatform.NEWSLETTER,
            url=newsletter_info.get("featured_article_url", ""),
            status="success",
            metadata={
                "subject": newsletter_info.get("subject"),
                "send_to_segments": newsletter_info.get("send_to_segments"),
            },
        )

    def on_user_click(
        self,
        article_id: str,
        platform: str,
        click_source: str = "direct",
        user_country: Optional[str] = None,
        user_device: Optional[str] = None,
    ) -> bool:
        """Log user click event."""
        if not self.analytics:
            return False

        platform_enum = PublishPlatform[platform.upper()] if platform.upper() in PublishPlatform.__members__ else PublishPlatform.BLOG

        return self.analytics.log_user_engagement(
            article_id=article_id,
            platform=platform_enum,
            engagement_type=EngagementType.CLICK,
            is_conversion=False,
            click_source=click_source,
            user_country=user_country,
            user_device=user_device,
        )

    def on_conversion(
        self,
        article_id: str,
        platform: str,
        conversion_value_usd: float,
        click_source: str = "direct",
        user_country: Optional[str] = None,
    ) -> bool:
        """Log conversion event."""
        if not self.analytics:
            return False

        platform_enum = PublishPlatform[platform.upper()] if platform.upper() in PublishPlatform.__members__ else PublishPlatform.BLOG

        return self.analytics.log_user_engagement(
            article_id=article_id,
            platform=platform_enum,
            engagement_type=EngagementType.CLICK,
            is_conversion=True,
            conversion_value_usd=conversion_value_usd,
            click_source=click_source,
            user_country=user_country,
        )

    def on_social_engagement_update(
        self,
        article_id: str,
        platform: str,
        post_id: str,
        likes: int = 0,
        shares: int = 0,
        comments: int = 0,
        saves: int = 0,
        impressions: int = 0,
        reach: int = 0,
    ) -> bool:
        """Log social media engagement metrics."""
        if not self.analytics:
            return False

        platform_enum = PublishPlatform[platform.upper()] if platform.upper() in PublishPlatform.__members__ else PublishPlatform.BLOG

        return self.analytics.log_social_metrics(
            article_id=article_id,
            platform=platform_enum,
            post_id=post_id,
            likes=likes,
            shares=shares,
            comments=comments,
            saves=saves,
            impressions=impressions,
            reach=reach,
        )

    def on_video_published(
        self,
        article_id: str,
        platform: str,
        video_id: str,
        video_title: str,
        views: int = 0,
        watch_time_minutes: float = 0.0,
        clicks: int = 0,
        shares: int = 0,
    ) -> bool:
        """Log video metrics."""
        if not self.analytics:
            return False

        platform_enum = PublishPlatform[platform.upper()] if platform.upper() in PublishPlatform.__members__ else PublishPlatform.BLOG

        return self.analytics.log_video_metrics(
            article_id=article_id,
            platform=platform_enum,
            video_id=video_id,
            video_title=video_title,
            views=views,
            watch_time_minutes=watch_time_minutes,
            clicks=clicks,
            shares=shares,
        )

    def generate_analytics_report(self, article_id: str) -> Dict[str, Any]:
        """Generate comprehensive analytics report for an article."""
        if not self.analytics:
            return {}

        return self.analytics.get_analytics_summary(article_id)

    def close(self) -> None:
        """Close analytics connections."""
        if self.analytics:
            self.analytics.close()


def create_analytics_hook() -> PublishingAnalyticsHook:
    """Factory function to create analytics hook."""
    manager = AnalyticsTrackingManager()
    return PublishingAnalyticsHook(manager)
