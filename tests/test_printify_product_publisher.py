"""
Tests for Printify product publisher module.
"""
from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.printify_product_publisher import (
    PRODUCT_TEMPLATES,
    TOPIC_PRODUCT_MAP,
    PODProduct,
    PrintifyPublisher,
    ProductDesign,
    PublishResult,
)


@pytest.fixture
def mock_env(monkeypatch):
    """Mock Printify environment variables."""
    monkeypatch.setenv("PRINTIFY_API_TOKEN", "test-token-12345")
    monkeypatch.setenv("PRINTIFY_SHOP_ID", "test-shop-67890")


@pytest.fixture
def publisher(mock_env, tmp_path):
    """Create PrintifyPublisher instance with temp directory."""
    publisher = PrintifyPublisher(
        api_token="test-token-12345",
        shop_id="test-shop-67890",
    )
    publisher.products_file = tmp_path / "pod_products.jsonl"
    publisher.products_file.parent.mkdir(parents=True, exist_ok=True)
    return publisher


class TestProductTemplates:
    """Test product template configurations."""

    def test_all_templates_have_required_fields(self):
        """Verify all product templates have required fields."""
        required_fields = {"name", "price", "cost", "profit", "variants", "print_provider"}

        for product_type, template in PRODUCT_TEMPLATES.items():
            assert all(field in template for field in required_fields), (
                f"Template {product_type} missing required fields"
            )
            assert template["price"] > 0
            assert template["cost"] > 0
            assert template["profit"] > 0
            assert len(template["variants"]) > 0

    def test_profit_calculations(self):
        """Verify profit margin calculations."""
        for product_type, template in PRODUCT_TEMPLATES.items():
            expected_profit = template["price"] - template["cost"]
            assert abs(template["profit"] - expected_profit) < 0.01, (
                f"Template {product_type} profit mismatch"
            )

    def test_pricing_structure(self):
        """Verify pricing tiers are reasonable."""
        # T-shirt should be cheaper than hoodie
        assert PRODUCT_TEMPLATES["tshirt"]["price"] < PRODUCT_TEMPLATES["hoodie"]["price"]
        # Mug should be cheapest
        assert PRODUCT_TEMPLATES["mug"]["price"] == min(
            t["price"] for t in PRODUCT_TEMPLATES.values()
        )
        # Book should be mid-tier
        assert (
            PRODUCT_TEMPLATES["mug"]["price"]
            < PRODUCT_TEMPLATES["book"]["price"]
            < PRODUCT_TEMPLATES["hoodie"]["price"]
        )


class TestProductRecommendations:
    """Test product recommendation engine."""

    def test_recommend_for_ai_keywords(self, publisher):
        """Test recommendations for AI-related content."""
        recommendations = publisher.recommend_products(
            keywords=["AI", "automation", "ChatGPT"],
            article_topic="How to Use AI for Productivity",
        )

        # AI topics should recommend tshirt and hoodie
        assert "tshirt" in recommendations
        assert "hoodie" in recommendations

    def test_recommend_for_business_keywords(self, publisher):
        """Test recommendations for business-related content."""
        recommendations = publisher.recommend_products(
            keywords=["SaaS", "startup", "founder"],
            article_topic="Building a SaaS in 30 Days",
        )

        # Business topics should recommend tshirt and hoodie
        assert "tshirt" in recommendations
        assert "hoodie" in recommendations

    def test_recommend_for_passive_income(self, publisher):
        """Test recommendations for passive income topics."""
        recommendations = publisher.recommend_products(
            keywords=["passive income", "affiliate", "monetize"],
        )

        # Passive income should recommend multiple products
        assert len(recommendations) > 0
        assert "tshirt" in recommendations or "hoodie" in recommendations

    def test_fallback_recommendations(self, publisher):
        """Test fallback to defaults for unknown topics."""
        recommendations = publisher.recommend_products(
            keywords=["obscureunique123", "xyzabc999"],
        )

        # Should fall back to defaults
        assert len(recommendations) > 0
        assert all(rec in PRODUCT_TEMPLATES for rec in recommendations)

    def test_recommendation_limit(self, publisher):
        """Test max recommendations limit."""
        recommendations = publisher.recommend_products(
            keywords=["AI", "business", "passive income"],
            max_recommendations=2,
        )

        assert len(recommendations) <= 2

    def test_recommendations_are_valid_product_types(self, publisher):
        """Verify all recommendations are valid product types."""
        for i in range(100):  # Test multiple combinations
            recommendations = publisher.recommend_products(
                keywords=[f"keyword{i}"],
            )

            for rec in recommendations:
                assert rec in PRODUCT_TEMPLATES


class TestDesignBrief:
    """Test design brief generation."""

    def test_generate_design_brief(self, publisher):
        """Test design brief creation."""
        brief = publisher.generate_design_brief(
            article_title="How to Build a Profitable SaaS Business",
            article_summary="A comprehensive guide to SaaS fundamentals",
            keywords=["SaaS", "business", "profitability"],
        )

        assert brief.article_title == "How to Build a Profitable SaaS Business"
        assert brief.article_summary == "A comprehensive guide to SaaS fundamentals"
        assert "SaaS" in brief.keywords
        assert brief.design_text is not None

    def test_design_text_truncation(self, publisher):
        """Test design text is truncated to 40 chars."""
        long_title = "A" * 100
        brief = publisher.generate_design_brief(
            article_title=long_title,
            article_summary="Summary",
            keywords=["test"],
        )

        assert len(brief.design_text) <= 43  # 40 chars + "..."


class TestPODProduct:
    """Test POD product creation and serialization."""

    def test_pod_product_creation(self):
        """Test PODProduct object creation."""
        product = PODProduct(
            id="test_product_1",
            product_type="tshirt",
            title="Test T-Shirt",
            description="A test product",
            price_usd=29.99,
            cost_usd=8.00,
            profit_margin_pct=73.3,
            article_title="Test Article",
            article_url="https://example.com/article",
            keywords=["test", "product"],
        )

        assert product.id == "test_product_1"
        assert product.product_type == "tshirt"
        assert product.price_usd == 29.99
        assert product.status == "draft"

    def test_pod_product_serialization(self):
        """Test PODProduct serialization to dict."""
        product = PODProduct(
            id="test_1",
            product_type="mug",
            title="Test Mug",
            price_usd=14.99,
            cost_usd=3.50,
            profit_margin_pct=76.6,
        )

        data = product.to_dict()

        assert isinstance(data, dict)
        assert data["id"] == "test_1"
        assert data["product_type"] == "mug"
        assert "created_at" in data


class TestPublishArticle:
    """Test article publishing workflow."""

    @patch("scripts.printify_product_publisher.PrintifyPublisher._create_product_on_printify")
    def test_publish_article_draft(self, mock_create, publisher):
        """Test publishing article in draft mode."""
        result = publisher.publish_article(
            title="How to Use AI Tools for Passive Income",
            summary="A guide to leveraging AI for revenue generation",
            keywords=["AI", "passive income", "automation"],
            article_url="https://example.com/article",
            auto_publish=False,
        )

        assert result.success
        assert result.article_title == "How to Use AI Tools for Passive Income"
        assert len(result.products) > 0

        # Should not call Printify API in draft mode
        mock_create.assert_not_called()

    @patch("scripts.printify_product_publisher.PrintifyPublisher._create_product_on_printify")
    def test_publish_article_auto_publish(self, mock_create, publisher):
        """Test publishing article with auto_publish enabled."""
        mock_create.return_value = "printify-product-123"

        result = publisher.publish_article(
            title="Building a SaaS Business",
            summary="A guide to SaaS development",
            keywords=["SaaS", "startup"],
            article_url="https://example.com",
            auto_publish=True,
            max_products=2,
        )

        assert result.success
        assert len(result.products) > 0
        # Should call Printify API for each product
        assert mock_create.call_count == len(result.products)

    def test_publish_article_saves_to_file(self, publisher):
        """Test that published products are saved to tracking file."""
        publisher.publish_article(
            title="Test Article",
            summary="Test summary",
            keywords=["test"],
            article_url="https://example.com",
        )

        assert publisher.products_file.exists()
        lines = publisher.products_file.read_text().strip().split("\n")
        assert len(lines) > 0

        # Verify saved data is valid JSON
        for line in lines:
            data = json.loads(line)
            assert "id" in data
            assert "product_type" in data

    def test_publish_article_product_titles(self, publisher):
        """Test product titles include article and product type."""
        result = publisher.publish_article(
            title="AI Tools Guide",
            summary="Summary",
            keywords=["AI"],
            article_url="https://example.com",
        )

        for product in result.products:
            assert "AI Tools Guide" in product.title
            assert PRODUCT_TEMPLATES[product.product_type]["name"] in product.title


class TestInventoryStats:
    """Test inventory and sales statistics."""

    def test_empty_inventory_stats(self, publisher):
        """Test stats for empty inventory."""
        stats = publisher.get_inventory_stats()

        assert stats["total_products"] == 0
        assert stats["draft_products"] == 0
        assert stats["published_products"] == 0
        assert stats["total_sales"] == 0

    def test_inventory_stats_with_products(self, publisher):
        """Test stats calculation with products."""
        # Create some products
        publisher.publish_article(
            title="Article 1",
            summary="Summary",
            keywords=["AI", "business"],
            article_url="https://example.com/1",
        )

        publisher.publish_article(
            title="Article 2",
            summary="Summary",
            keywords=["AI"],
            article_url="https://example.com/2",
        )

        stats = publisher.get_inventory_stats()

        assert stats["total_products"] >= 2
        assert stats["draft_products"] >= 2
        assert "tshirt" in stats["products_by_type"]

    def test_product_type_breakdown(self, publisher):
        """Test product type breakdown in stats."""
        publisher.publish_article(
            title="Test Article",
            summary="Summary",
            keywords=["AI", "business", "passive income"],
            article_url="https://example.com",
        )

        stats = publisher.get_inventory_stats()
        product_types = stats["products_by_type"]

        # Should have created multiple product types
        assert len(product_types) > 0
        # All should be valid types
        assert all(ptype in PRODUCT_TEMPLATES for ptype in product_types.keys())


class TestListProducts:
    """Test product listing and filtering."""

    def test_list_all_products(self, publisher):
        """Test listing all products."""
        publisher.publish_article(
            title="Article 1",
            summary="Summary",
            keywords=["AI"],
            article_url="https://example.com",
        )

        products = publisher.list_products()

        assert len(products) > 0
        assert all(isinstance(p, PODProduct) for p in products)

    def test_filter_by_product_type(self, publisher):
        """Test filtering products by type."""
        publisher.publish_article(
            title="Test Article",
            summary="Summary",
            keywords=["AI", "business"],
            article_url="https://example.com",
        )

        tshirts = publisher.list_products(product_type="tshirt")
        hoodies = publisher.list_products(product_type="hoodie")

        # Both should have items since we recommend both
        assert all(p.product_type == "tshirt" for p in tshirts)
        assert all(p.product_type == "hoodie" for p in hoodies)

    def test_filter_by_status(self, publisher):
        """Test filtering products by status."""
        publisher.publish_article(
            title="Test Article",
            summary="Summary",
            keywords=["test"],
            article_url="https://example.com",
        )

        draft_products = publisher.list_products(status="draft")

        assert len(draft_products) > 0
        assert all(p.status == "draft" for p in draft_products)


class TestSalesReport:
    """Test sales reporting."""

    def test_empty_sales_report(self, publisher):
        """Test sales report with no products."""
        report = publisher.get_sales_report()

        assert report["total_products"] == 0
        assert report["total_revenue"] == 0
        assert report["total_profit"] == 0

    def test_sales_report_structure(self, publisher):
        """Test sales report includes all fields."""
        publisher.publish_article(
            title="Test Article",
            summary="Summary",
            keywords=["test"],
            article_url="https://example.com",
        )

        report = publisher.get_sales_report()

        assert "generated_at" in report
        assert "total_products" in report
        assert "total_revenue" in report
        assert "total_profit" in report
        assert "average_profit_margin_pct" in report
        assert "by_product_type" in report


class TestPublishResult:
    """Test PublishResult object."""

    def test_publish_result_serialization(self):
        """Test PublishResult serialization."""
        products = [
            PODProduct(
                id="p1",
                product_type="tshirt",
                title="Test T-Shirt",
                price_usd=29.99,
                cost_usd=8.00,
                profit_margin_pct=73.3,
            )
        ]

        result = PublishResult(
            success=True,
            article_title="Test Article",
            products=products,
        )

        data = result.to_dict()

        assert data["success"]
        assert data["article_title"] == "Test Article"
        assert data["product_count"] == 1
        assert "products" in data


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_missing_credentials(self):
        """Test error when credentials are missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError):
                PrintifyPublisher()

    def test_publish_with_empty_keywords(self, publisher):
        """Test publishing with empty keywords."""
        result = publisher.publish_article(
            title="Test Article",
            summary="Summary",
            keywords=[],
            article_url="https://example.com",
        )

        # Should still create products with fallback recommendations
        assert result.success

    def test_publish_with_special_characters(self, publisher):
        """Test publishing with special characters in title."""
        result = publisher.publish_article(
            title='Article: "How to Build $1M SaaS" (2026)',
            summary="Summary",
            keywords=["SaaS"],
            article_url="https://example.com",
        )

        assert result.success
        assert len(result.products) > 0


class TestPriceCalculations:
    """Test price and margin calculations."""

    def test_margin_percentage_accuracy(self, publisher):
        """Test profit margin calculations are accurate."""
        result = publisher.publish_article(
            title="Test Article",
            summary="Summary",
            keywords=["test"],
            article_url="https://example.com",
        )

        for product in result.products:
            template = PRODUCT_TEMPLATES[product.product_type]
            expected_margin = (
                (template["price"] - template["cost"]) / template["price"]
            ) * 100
            assert abs(product.profit_margin_pct - expected_margin) < 0.1

    def test_pricing_in_templates(self):
        """Verify pricing meets margin requirements."""
        for product_type, template in PRODUCT_TEMPLATES.items():
            margin_pct = (
                (template["price"] - template["cost"]) / template["price"]
            ) * 100
            # Minimum 25% margin for competitive pricing
            assert margin_pct >= 25, (
                f"Product {product_type} margin below 25%: {margin_pct}%"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
