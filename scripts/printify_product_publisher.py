"""
Printify Product Publisher — Automated POD product creation from blog content.

Creates print-on-demand products (t-shirts, mugs, hoodies, hats, books) from
articles using Printify API. Auto-generates designs, manages inventory, and
recommends product types based on article topics.

Environment Variables:
- PRINTIFY_API_TOKEN: Printify API token (required)
- PRINTIFY_SHOP_ID: Printify shop ID (required)
- PROFITENGINE_URL: Base URL for product tracking (optional)

Usage:
    from scripts.printify_product_publisher import PrintifyPublisher

    publisher = PrintifyPublisher()

    # Create products from article
    result = publisher.publish_article(
        title="How to Build a SaaS in 30 Days",
        summary="A step-by-step guide...",
        keywords=["SaaS", "startup", "lean"],
        article_url="https://example.com/article",
        content="Full article text..."
    )

    # Get recommended products for topic
    recommendations = publisher.recommend_products(
        keywords=["AI", "automation", "business"],
        article_topic="AI Tools for Productivity"
    )

    # Track inventory and sales
    stats = publisher.get_inventory_stats()
"""
from __future__ import annotations

import json
import logging
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

# Product type templates with profit margins
PRODUCT_TEMPLATES = {
    "tshirt": {
        "name": "T-Shirt",
        "price": 19.99,
        "cost": 14.99,
        "profit": 5.00,
        "print_area": "chest",
        "design_template": "text_and_summary",
        "variants": ["XS", "S", "M", "L", "XL", "2XL", "3XL"],
        "print_provider": "printful",  # Printify's Printful integration
    },
    "mug": {
        "name": "Ceramic Mug",
        "price": 9.99,
        "cost": 7.49,
        "profit": 2.50,
        "print_area": "wrap",
        "design_template": "circular_logo",
        "variants": ["11oz", "15oz"],
        "print_provider": "printful",
    },
    "hoodie": {
        "name": "Hoodie",
        "price": 34.99,
        "cost": 26.24,
        "profit": 8.75,
        "print_area": "chest",
        "design_template": "large_logo",
        "variants": ["XS", "S", "M", "L", "XL", "2XL", "3XL"],
        "print_provider": "printful",
    },
    "hat": {
        "name": "Baseball Cap",
        "price": 12.99,
        "cost": 9.74,
        "profit": 3.25,
        "print_area": "front",
        "design_template": "small_logo",
        "variants": ["One Size"],
        "print_provider": "printful",
    },
    "book": {
        "name": "Paperback Book",
        "price": 16.99,
        "cost": 12.74,
        "profit": 4.25,
        "print_area": "full_page",
        "design_template": "book_content",
        "variants": ["6x9in-bw", "6x9in-color"],
        "print_provider": "printful",
    },
}

# Topic-to-product recommendation mapping
TOPIC_PRODUCT_MAP = {
    # AI / Automation / Tech
    r"(AI|artificial intelligence|machine learning|automation|chatgpt|claude)": [
        "tshirt",
        "hoodie",
        "mug",
    ],
    # Business / SaaS / Startup
    r"(SaaS|startup|founder|entrepreneur|business|scaling)": [
        "tshirt",
        "hoodie",
        "book",
    ],
    # Passive Income / Monetization
    r"(passive income|affiliate|monetize|earning|revenue)": [
        "tshirt",
        "hoodie",
        "book",
        "mug",
    ],
    # Blogging / Content
    r"(blog|content|writing|SEO|keyword)": [
        "tshirt",
        "mug",
        "hat",
    ],
    # Development / Coding
    r"(developer|code|programming|javascript|python|react)": [
        "tshirt",
        "hoodie",
        "hat",
    ],
    # Finance / Crypto
    r"(finance|crypto|bitcoin|trading|investment)": [
        "tshirt",
        "hoodie",
        "book",
    ],
    # Design / Creative
    r"(design|creative|brand|ux|ui)": [
        "hoodie",
        "hat",
        "mug",
    ],
    # Default fallback
    "default": ["tshirt", "mug", "hoodie"],
}


@dataclass
class ProductDesign:
    """POD product design specification."""

    product_type: str
    article_title: str
    article_summary: str
    keywords: list[str]
    design_url: Optional[str] = None
    design_text: Optional[str] = None
    print_area: str = "chest"
    design_template: str = "text_and_summary"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PODProduct:
    """POD product listing."""

    id: str
    external_id: Optional[str] = None  # Printify product ID
    product_type: str = ""
    title: str = ""
    description: str = ""
    price_usd: float = 0.0
    cost_usd: float = 0.0
    profit_margin_pct: float = 0.0
    article_title: str = ""
    article_url: str = ""
    keywords: list[str] = field(default_factory=list)
    design: Optional[ProductDesign] = None
    status: str = "draft"  # draft, published, live
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    sales_count: int = 0
    inventory_count: int = 0
    images: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        if self.design:
            data["design"] = self.design.to_dict()
        if self.created_at:
            data["created_at"] = self.created_at.isoformat()
        return data


@dataclass
class PublishResult:
    """Result of publishing products for an article."""

    success: bool
    article_title: str
    products: list[PODProduct]
    errors: list[str] = field(default_factory=list)
    published_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "article_title": self.article_title,
            "product_count": len(self.products),
            "products": [p.to_dict() for p in self.products],
            "errors": self.errors,
            "published_at": self.published_at.isoformat(),
        }


class PrintifyPublisher:
    """Automated Printify POD product publisher."""

    def __init__(
        self,
        api_token: Optional[str] = None,
        shop_id: Optional[str] = None,
        base_url: str = "https://api.printify.com/v1",
    ):
        """Initialize publisher with Printify credentials.

        Args:
            api_token: Printify API token. Defaults to PRINTIFY_API_TOKEN env var.
            shop_id: Printify shop ID. Defaults to PRINTIFY_SHOP_ID env var.
            base_url: Printify API base URL.

        Raises:
            ValueError: If required credentials are missing.
        """
        self.api_token = api_token or os.environ.get("PRINTIFY_API_TOKEN")
        self.shop_id = shop_id or os.environ.get("PRINTIFY_SHOP_ID")

        if not self.api_token or not self.shop_id:
            raise ValueError(
                "Missing Printify credentials. Set PRINTIFY_API_TOKEN and "
                "PRINTIFY_SHOP_ID environment variables."
            )

        self.base_url = base_url
        self.client = httpx.Client(
            headers={"Authorization": f"Bearer {self.api_token}"},
            timeout=30.0,
        )
        self.products_file = Path(".runtime/pod_products.jsonl")
        self.products_file.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized PrintifyPublisher for shop {self.shop_id}")

    def __del__(self):
        """Clean up HTTP client."""
        if hasattr(self, "client"):
            self.client.close()

    def recommend_products(
        self,
        keywords: list[str],
        article_topic: str = "",
        max_recommendations: int = 4,
    ) -> list[str]:
        """Recommend product types based on article keywords and topic.

        Args:
            keywords: Article keywords (e.g., ["AI", "automation", "SaaS"])
            article_topic: Full article topic/title
            max_recommendations: Max products to recommend

        Returns:
            List of recommended product type keys (e.g., ["tshirt", "hoodie"])
        """
        recommended = set()
        topic_str = f"{article_topic} {' '.join(keywords)}".lower()

        # Check each pattern against combined topic+keywords
        for pattern, products in TOPIC_PRODUCT_MAP.items():
            if pattern != "default" and re.search(pattern, topic_str, re.IGNORECASE):
                recommended.update(products)

        # Fallback to defaults if no matches
        if not recommended:
            recommended.update(TOPIC_PRODUCT_MAP["default"])

        # Return up to max_recommendations, prioritizing higher-margin products
        sorted_products = sorted(
            recommended,
            key=lambda p: PRODUCT_TEMPLATES.get(p, {}).get("profit", 0),
            reverse=True,
        )
        return sorted_products[:max_recommendations]

    def generate_design_brief(
        self,
        article_title: str,
        article_summary: str,
        keywords: list[str],
    ) -> ProductDesign:
        """Generate design brief for a product.

        Args:
            article_title: Title of the article
            article_summary: Summary/excerpt from article
            keywords: Article keywords

        Returns:
            ProductDesign object with design specifications
        """
        # Clean title for design text (max 40 chars)
        design_text = article_title[:40].strip()
        if len(article_title) > 40:
            design_text += "..."

        return ProductDesign(
            product_type="tshirt",  # Will be set per product
            article_title=article_title,
            article_summary=article_summary,
            keywords=keywords,
            design_text=design_text,
            design_template="text_and_summary",
        )

    def _get_printable_products(self) -> dict[str, int]:
        """Fetch available printable products from Printify.

        Returns:
            Dict of product name → Printify product ID
        """
        try:
            resp = self.client.get(f"{self.base_url}/shops/{self.shop_id}/products")
            resp.raise_for_status()
            products = resp.json()
            return {p["title"]: p["id"] for p in products.get("data", [])}
        except Exception as e:
            logger.error(f"Failed to fetch printable products: {e}")
            return {}

    def _create_product_on_printify(
        self,
        title: str,
        description: str,
        keywords: list[str],
        design_brief: ProductDesign,
        template: dict[str, Any],
    ) -> Optional[str]:
        """Create product on Printify API.

        Args:
            title: Product title
            description: Product description
            keywords: Product keywords
            design_brief: Design specifications
            template: Product template config

        Returns:
            Printify product ID if created, None otherwise
        """
        payload = {
            "title": title,
            "description": description,
            "tags": keywords,
            "type": template.get("print_provider", "printful"),
        }

        try:
            resp = self.client.post(
                f"{self.base_url}/shops/{self.shop_id}/products",
                json=payload,
            )
            resp.raise_for_status()
            product = resp.json()
            logger.info(f"Created Printify product: {product.get('id')}")
            return product.get("id")
        except Exception as e:
            logger.error(f"Failed to create product on Printify: {e}")
            return None

    def publish_article(
        self,
        title: str,
        summary: str,
        keywords: list[str],
        article_url: str,
        content: str = "",
        auto_publish: bool = False,
        max_products: int = 4,
    ) -> PublishResult:
        """Publish POD products for an article.

        Args:
            title: Article title
            summary: Article summary/excerpt
            keywords: Article keywords
            article_url: URL to article
            content: Full article content (for book products)
            auto_publish: Auto-publish to Printify (vs draft only)
            max_products: Max number of products to create

        Returns:
            PublishResult with created products and status
        """
        products = []
        errors = []

        # Recommend products based on topic
        recommended = self.recommend_products(keywords, title, max_products)

        if not recommended:
            errors.append("No products recommended for topic")
            return PublishResult(
                success=False,
                article_title=title,
                products=products,
                errors=errors,
            )

        # Generate design brief
        design_brief = self.generate_design_brief(title, summary, keywords)

        # Create products for each recommended type
        for product_type in recommended:
            try:
                template = PRODUCT_TEMPLATES[product_type]
                product_title = f"{title} — {template['name']}"

                # Build description
                product_desc = f"""Product: {template['name']}
Article: {title}
URL: {article_url}
Keywords: {', '.join(keywords)}

{summary}"""

                # Truncate description for Printify (max 1000 chars)
                product_desc = product_desc[:1000]

                # Update design brief for this product type
                design_brief_copy = ProductDesign(
                    product_type=product_type,
                    article_title=title,
                    article_summary=summary,
                    keywords=keywords,
                    design_text=design_brief.design_text,
                    print_area=template.get("print_area", "chest"),
                    design_template=template.get("design_template", "text_and_summary"),
                )

                # Create on Printify if auto_publish enabled
                printify_id = None
                if auto_publish:
                    printify_id = self._create_product_on_printify(
                        product_title,
                        product_desc,
                        keywords,
                        design_brief_copy,
                        template,
                    )

                # Create POD product object
                product = PODProduct(
                    id=f"{product_type}_{re.sub(r'[^a-z0-9]', '_', title.lower())[:30]}",
                    external_id=printify_id,
                    product_type=product_type,
                    title=product_title,
                    description=product_desc,
                    price_usd=template["price"],
                    cost_usd=template["cost"],
                    profit_margin_pct=round(
                        ((template["price"] - template["cost"]) / template["price"])
                        * 100,
                        1,
                    ),
                    article_title=title,
                    article_url=article_url,
                    keywords=keywords,
                    design=design_brief_copy,
                    status="published" if auto_publish and printify_id else "draft",
                )

                products.append(product)
                logger.info(
                    f"Created {product_type} product for '{title}' "
                    f"(${template['profit']} margin)"
                )

            except Exception as e:
                msg = f"Error creating {product_type}: {str(e)}"
                logger.error(msg)
                errors.append(msg)

        # Save to local tracking file
        self._save_products(products)

        return PublishResult(
            success=len(products) > 0,
            article_title=title,
            products=products,
            errors=errors,
        )

    def _save_products(self, products: list[PODProduct]) -> None:
        """Append products to tracking file.

        Args:
            products: List of PODProduct objects to save
        """
        try:
            with self.products_file.open("a", encoding="utf-8") as f:
                for product in products:
                    f.write(json.dumps(product.to_dict()) + "\n")
        except Exception as e:
            logger.error(f"Failed to save products to file: {e}")

    def get_inventory_stats(self) -> dict[str, Any]:
        """Get inventory and sales statistics.

        Returns:
            Dict with sales and inventory metrics
        """
        stats = {
            "total_products": 0,
            "draft_products": 0,
            "published_products": 0,
            "total_sales": 0,
            "total_inventory": 0,
            "products_by_type": {},
            "total_potential_profit": 0.0,
        }

        if not self.products_file.exists():
            return stats

        try:
            with self.products_file.open("r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue

                    data = json.loads(line)
                    product_type = data.get("product_type", "unknown")
                    status = data.get("status", "draft")
                    sales = data.get("sales_count", 0)
                    profit = data.get("profit_margin_pct", 0)
                    price = data.get("price_usd", 0)

                    stats["total_products"] += 1
                    stats["total_sales"] += sales
                    stats["total_potential_profit"] += (price - data.get("cost_usd", 0))

                    if status == "draft":
                        stats["draft_products"] += 1
                    elif status == "published":
                        stats["published_products"] += 1

                    if product_type not in stats["products_by_type"]:
                        stats["products_by_type"][product_type] = 0
                    stats["products_by_type"][product_type] += 1

        except Exception as e:
            logger.error(f"Error reading inventory stats: {e}")

        return stats

    def list_products(
        self, product_type: Optional[str] = None, status: Optional[str] = None
    ) -> list[PODProduct]:
        """List created POD products with optional filters.

        Args:
            product_type: Filter by product type (e.g., 'tshirt')
            status: Filter by status (e.g., 'published')

        Returns:
            List of PODProduct objects
        """
        products = []

        if not self.products_file.exists():
            return products

        try:
            with self.products_file.open("r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue

                    data = json.loads(line)

                    # Apply filters
                    if product_type and data.get("product_type") != product_type:
                        continue
                    if status and data.get("status") != status:
                        continue

                    # Reconstruct PODProduct object
                    design_data = data.get("design")
                    design = (
                        ProductDesign(**design_data) if design_data else None
                    )

                    product = PODProduct(
                        id=data["id"],
                        external_id=data.get("external_id"),
                        product_type=data.get("product_type", ""),
                        title=data.get("title", ""),
                        description=data.get("description", ""),
                        price_usd=data.get("price_usd", 0.0),
                        cost_usd=data.get("cost_usd", 0.0),
                        profit_margin_pct=data.get("profit_margin_pct", 0.0),
                        article_title=data.get("article_title", ""),
                        article_url=data.get("article_url", ""),
                        keywords=data.get("keywords", []),
                        design=design,
                        status=data.get("status", "draft"),
                        sales_count=data.get("sales_count", 0),
                        inventory_count=data.get("inventory_count", 0),
                        images=data.get("images", []),
                    )
                    products.append(product)

        except Exception as e:
            logger.error(f"Error listing products: {e}")

        return products

    def get_sales_report(self) -> dict[str, Any]:
        """Generate sales and profitability report.

        Returns:
            Dict with sales metrics and profitability analysis
        """
        products = self.list_products()

        report = {
            "generated_at": datetime.now(UTC).isoformat(),
            "total_products": len(products),
            "total_revenue": 0.0,
            "total_costs": 0.0,
            "total_profit": 0.0,
            "average_profit_margin_pct": 0.0,
            "best_performing": [],
            "by_product_type": {},
        }

        for product in products:
            revenue = product.price_usd * product.sales_count
            cost = product.cost_usd * product.sales_count
            profit = revenue - cost

            report["total_revenue"] += revenue
            report["total_costs"] += cost
            report["total_profit"] += profit

            # Track by product type
            ptype = product.product_type
            if ptype not in report["by_product_type"]:
                report["by_product_type"][ptype] = {
                    "count": 0,
                    "revenue": 0.0,
                    "profit": 0.0,
                    "avg_profit_margin_pct": 0.0,
                }

            report["by_product_type"][ptype]["count"] += 1
            report["by_product_type"][ptype]["revenue"] += revenue
            report["by_product_type"][ptype]["profit"] += profit

        # Calculate average margin
        if products:
            report["average_profit_margin_pct"] = round(
                sum(p.profit_margin_pct for p in products) / len(products), 1
            )

        # Find best performing
        if products:
            report["best_performing"] = [
                {
                    "title": p.title,
                    "type": p.product_type,
                    "sales": p.sales_count,
                    "revenue": p.price_usd * p.sales_count,
                    "profit": (p.price_usd - p.cost_usd) * p.sales_count,
                }
                for p in sorted(
                    products, key=lambda x: x.sales_count * x.profit_margin_pct / 100,
                    reverse=True
                )[:5]
            ]

        return report


def main():
    """CLI interface for Printify product publisher."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Printify POD Product Publisher"
    )
    parser.add_argument("command", choices=["publish", "list", "stats", "report"])
    parser.add_argument("--title", help="Article title")
    parser.add_argument("--summary", help="Article summary")
    parser.add_argument("--keywords", help="Comma-separated keywords")
    parser.add_argument("--url", help="Article URL")
    parser.add_argument("--auto-publish", action="store_true", help="Auto-publish to Printify")
    parser.add_argument("--type", help="Product type filter")
    parser.add_argument("--status", help="Status filter")

    args = parser.parse_args()

    try:
        publisher = PrintifyPublisher()

        if args.command == "publish":
            if not all([args.title, args.summary, args.keywords, args.url]):
                print("publish requires: --title, --summary, --keywords, --url")
                sys.exit(1)

            result = publisher.publish_article(
                title=args.title,
                summary=args.summary,
                keywords=[k.strip() for k in args.keywords.split(",")],
                article_url=args.url,
                auto_publish=args.auto_publish,
            )

            print(json.dumps(result.to_dict(), indent=2))

        elif args.command == "list":
            products = publisher.list_products(
                product_type=args.type,
                status=args.status,
            )
            print(f"Found {len(products)} products:")
            for p in products:
                print(f"  • {p.title} ({p.status}) - ${p.price_usd}")

        elif args.command == "stats":
            stats = publisher.get_inventory_stats()
            print(json.dumps(stats, indent=2))

        elif args.command == "report":
            report = publisher.get_sales_report()
            print(json.dumps(report, indent=2))

    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
