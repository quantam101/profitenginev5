"""
Enhanced ProfitEngine article publisher with MongoDB/PostgreSQL analytics tracking.

This is a wrapper around publish_article_resilient.py that adds comprehensive
analytics logging for all publishing events, distributions, and engagement metrics.

Usage:
    python publish_article_with_analytics.py "Article Topic"
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

# Add lib directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))

try:
    from analytics_integration import create_analytics_hook
except ImportError as e:
    print(f"[ERROR] Failed to import analytics integration: {e}")
    print("[ERROR] Make sure lib/analytics_tracker.py and lib/analytics_integration.py exist")
    sys.exit(1)

import publish_article_resilient as resilient_publisher


def wrap_main_with_analytics() -> None:
    """Wrap the resilient publisher's main function with analytics tracking."""
    analytics_hook = create_analytics_hook()
    article_id = ""

    try:
        # Store original functions
        original_generate_article = resilient_publisher.publisher.generate_article
        original_publish_github = resilient_publisher.publisher.publish_github
        original_publish_to_all_platforms = resilient_publisher.publish_to_all_platforms
        original_publish_to_all_ecommerce = resilient_publisher.publish_to_all_ecommerce

        # Create wrapped functions
        def generate_article_with_tracking(topic: str) -> Dict[str, Any]:
            nonlocal article_id
            article = original_generate_article(topic)
            # Log article generation
            article_id = analytics_hook.on_article_generated(article, topic)
            return article

        def publish_github_with_tracking(filename: str, content: str, commit_msg: str) -> str:
            nonlocal article_id
            url = original_publish_github(filename, content, commit_msg)
            # Log GitHub publication
            if article_id:
                analytics_hook.on_github_published(article_id, url)
            return url

        def publish_to_all_platforms_with_tracking(article: Dict[str, Any], url: str, **kwargs) -> Dict[str, Any]:
            nonlocal article_id
            results = original_publish_to_all_platforms(article, url, **kwargs) if original_publish_to_all_platforms else {}
            # Log social media distribution
            if article_id and results:
                analytics_hook.on_social_distribution_complete(article_id, results)
            return results

        def publish_to_all_ecommerce_with_tracking(article: Dict[str, Any]) -> Dict[str, Any]:
            nonlocal article_id
            results = original_publish_to_all_ecommerce(article) if original_publish_to_all_ecommerce else {}
            # Log e-commerce distribution
            if article_id and results:
                analytics_hook.on_ecommerce_distribution_complete(article_id, results)
            return results

        # Apply wrappers
        resilient_publisher.publisher.generate_article = generate_article_with_tracking
        resilient_publisher.publisher.publish_github = publish_github_with_tracking
        if original_publish_to_all_platforms:
            resilient_publisher.publish_to_all_platforms = publish_to_all_platforms_with_tracking
        if original_publish_to_all_ecommerce:
            resilient_publisher.publish_to_all_ecommerce = publish_to_all_ecommerce_with_tracking

        # Run the resilient publisher
        print("[ANALYTICS] Starting resilient publisher with analytics tracking...")
        resilient_publisher.main()

        # Generate analytics report
        if article_id:
            print(f"\n[ANALYTICS] Generating report for article {article_id}...")
            report = analytics_hook.generate_analytics_report(article_id)

            # Save report
            report_file = f"analytics_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, "w") as f:
                json.dump(report, f, indent=2, default=str)
            print(f"[ANALYTICS] Report saved to {report_file}")

    except Exception as e:
        print(f"[ERROR] Analytics wrapper failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        analytics_hook.close()


if __name__ == "__main__":
    wrap_main_with_analytics()
