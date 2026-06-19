# Printify POD Product Publisher

Automated print-on-demand (POD) product creation from blog content. Generates t-shirts, mugs, hoodies, hats, and books with competitive 25% profit margins.

## Quick Start

### 1. Setup Environment Variables

```bash
export PRINTIFY_API_TOKEN="your-printify-api-token"
export PRINTIFY_SHOP_ID="your-printify-shop-id"
```

Find these in your Printify dashboard:
- **API Token**: Account Settings → API
- **Shop ID**: Dashboard → Your Shop

### 2. Publish Products from an Article

```python
from scripts.printify_product_publisher import PrintifyPublisher

publisher = PrintifyPublisher()

result = publisher.publish_article(
    title="How to Build a Profitable SaaS in 30 Days",
    summary="A step-by-step guide covering market research, MVP development, and launch strategy.",
    keywords=["SaaS", "startup", "profitability", "lean"],
    article_url="https://example.com/article",
    auto_publish=False,  # Draft first, review, then publish
    max_products=4
)

print(f"Created {len(result.products)} products")
for product in result.products:
    print(f"  • {product.title} - ${product.price_usd} (${product.profit} margin)")
```

### 3. Get Product Recommendations

The system intelligently recommends product types based on article content:

```python
publisher = PrintifyPublisher()

recommendations = publisher.recommend_products(
    keywords=["AI", "automation", "productivity"],
    article_topic="Using AI Tools to 10x Your Productivity"
)

# Returns: ['tshirt', 'hoodie', 'mug']
```

### 4. View Inventory and Sales

```python
# Get stats
stats = publisher.get_inventory_stats()
print(f"Total Products: {stats['total_products']}")
print(f"Published: {stats['published_products']}")
print(f"Total Sales: {stats['total_sales']}")

# Get detailed sales report
report = publisher.get_sales_report()
print(f"Total Revenue: ${report['total_revenue']:.2f}")
print(f"Total Profit: ${report['total_profit']:.2f}")
print(f"Best Performing: {report['best_performing'][0]['title']}")
```

## Product Types & Pricing

All products are optimized for 50%+ profit margins:

| Product | Retail Price | Cost | Profit | Margin |
|---------|-------------|------|--------|--------|
| T-Shirt | $29.99 | $8.00 | $21.99 | 73.3% |
| Mug | $14.99 | $3.50 | $11.49 | 76.6% |
| Hoodie | $49.99 | $15.00 | $34.99 | 70.0% |
| Cap | $19.99 | $4.50 | $15.49 | 77.5% |
| Paperback Book | $24.99 | $5.00 | $19.99 | 80.0% |

## Smart Product Recommendations

The system automatically recommends products based on article keywords:

### AI / Automation / Tech Topics
Recommends: **T-Shirt, Hoodie, Mug**
- Keywords: AI, automation, ChatGPT, machine learning, Python, JavaScript
- Reasoning: Tech audience appreciates branded apparel

### Business / SaaS / Startup Topics
Recommends: **T-Shirt, Hoodie, Book**
- Keywords: SaaS, startup, founder, scaling, business
- Reasoning: Founders want both apparel and educational content

### Passive Income / Monetization Topics
Recommends: **T-Shirt, Hoodie, Book, Mug**
- Keywords: Passive income, affiliate, monetize, revenue
- Reasoning: Diverse audience wants multiple product options

### Blogging / Content Topics
Recommends: **T-Shirt, Mug, Cap**
- Keywords: Blog, content, SEO, writing, keywords
- Reasoning: Content creators want wearables + drinkware

### Development / Coding Topics
Recommends: **T-Shirt, Hoodie, Cap**
- Keywords: Developer, code, programming, React, Node.js
- Reasoning: Developers want statement pieces

### Finance / Crypto Topics
Recommends: **T-Shirt, Hoodie, Book**
- Keywords: Finance, crypto, Bitcoin, trading, investment
- Reasoning: Finance audience values both apparel and guides

### Design / Creative Topics
Recommends: **Hoodie, Cap, Mug**
- Keywords: Design, creative, brand, UX, UI
- Reasoning: Designers appreciate quality merchandise

## CLI Usage

### Publish Article

```bash
python scripts/printify_product_publisher.py publish \
  --title "How to Build a Profitable Niche Blog" \
  --summary "Complete guide to niche selection and monetization" \
  --keywords "blog,SEO,passive income" \
  --url "https://example.com/article" \
  --auto-publish
```

### List Products

```bash
# All products
python scripts/printify_product_publisher.py list

# Filter by type
python scripts/printify_product_publisher.py list --type tshirt

# Filter by status
python scripts/printify_product_publisher.py list --status draft
```

### View Stats

```bash
python scripts/printify_product_publisher.py stats
```

### Generate Report

```bash
python scripts/printify_product_publisher.py report
```

## API Reference

### PrintifyPublisher

Main class for managing POD products.

#### Constructor

```python
PrintifyPublisher(
    api_token: Optional[str] = None,
    shop_id: Optional[str] = None,
    base_url: str = "https://api.printify.com/v1"
)
```

**Parameters:**
- `api_token`: Printify API token (uses `PRINTIFY_API_TOKEN` env var if not provided)
- `shop_id`: Printify shop ID (uses `PRINTIFY_SHOP_ID` env var if not provided)
- `base_url`: Printify API endpoint

**Raises:** `ValueError` if credentials are missing

#### Methods

##### `recommend_products()`

```python
recommend_products(
    keywords: list[str],
    article_topic: str = "",
    max_recommendations: int = 4
) -> list[str]
```

Get recommended product types for article content.

**Parameters:**
- `keywords`: Article keywords (e.g., `["AI", "automation"]`)
- `article_topic`: Full article topic/title
- `max_recommendations`: Maximum products to recommend

**Returns:** List of product type strings (e.g., `["tshirt", "hoodie"]`)

##### `publish_article()`

```python
publish_article(
    title: str,
    summary: str,
    keywords: list[str],
    article_url: str,
    content: str = "",
    auto_publish: bool = False,
    max_products: int = 4
) -> PublishResult
```

Create POD products for an article.

**Parameters:**
- `title`: Article title
- `summary`: Article summary/excerpt
- `keywords`: Article keywords
- `article_url`: URL to the article
- `content`: Full article text (used for book products)
- `auto_publish`: Publish to Printify immediately (vs draft only)
- `max_products`: Maximum products to create

**Returns:** `PublishResult` object with created products

##### `get_inventory_stats()`

```python
get_inventory_stats() -> dict[str, Any]
```

Get inventory and sales statistics.

**Returns:** Dictionary with:
- `total_products`: Total products created
- `draft_products`: Products in draft status
- `published_products`: Published products
- `total_sales`: Total units sold
- `total_inventory`: Total inventory count
- `products_by_type`: Breakdown by product type
- `total_potential_profit`: Total profit if all sold

##### `list_products()`

```python
list_products(
    product_type: Optional[str] = None,
    status: Optional[str] = None
) -> list[PODProduct]
```

List created products with optional filters.

**Parameters:**
- `product_type`: Filter by type (e.g., `"tshirt"`)
- `status`: Filter by status (e.g., `"draft"`, `"published"`)

**Returns:** List of `PODProduct` objects

##### `get_sales_report()`

```python
get_sales_report() -> dict[str, Any]
```

Generate detailed sales and profitability report.

**Returns:** Dictionary with:
- `total_revenue`: Total revenue from sales
- `total_costs`: Total manufacturing costs
- `total_profit`: Net profit
- `average_profit_margin_pct`: Average profit margin
- `best_performing`: Top 5 products by profit
- `by_product_type`: Breakdown by product type

### PODProduct

Represents a POD product listing.

```python
@dataclass
class PODProduct:
    id: str                          # Unique product ID
    external_id: Optional[str]       # Printify product ID
    product_type: str                # tshirt, mug, hoodie, hat, book
    title: str                       # Product title
    description: str                 # Product description
    price_usd: float                 # Retail price
    cost_usd: float                  # Manufacturing cost
    profit_margin_pct: float         # Profit margin percentage
    article_title: str               # Source article title
    article_url: str                 # Source article URL
    keywords: list[str]              # Article keywords
    design: Optional[ProductDesign]  # Design specifications
    status: str                      # draft, published, live
    created_at: datetime             # Creation timestamp
    sales_count: int                 # Units sold
    inventory_count: int             # Current inventory
    images: list[str]                # Product images
```

### PublishResult

Result of publishing products for an article.

```python
@dataclass
class PublishResult:
    success: bool                    # Whether publishing succeeded
    article_title: str              # Source article title
    products: list[PODProduct]      # Created products
    errors: list[str]               # Any errors during publishing
    published_at: datetime          # Publishing timestamp
```

## Workflow Integration

### GitHub Actions

Publish POD products automatically when articles are published:

```yaml
name: POD Publisher

on:
  repository_dispatch:
    types: [article_published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Publish POD products
        env:
          PRINTIFY_API_TOKEN: ${{ secrets.PRINTIFY_API_TOKEN }}
          PRINTIFY_SHOP_ID: ${{ secrets.PRINTIFY_SHOP_ID }}
        run: |
          python scripts/printify_product_publisher.py publish \
            --title "${{ github.event.client_payload.title }}" \
            --summary "${{ github.event.client_payload.summary }}" \
            --keywords "${{ github.event.client_payload.keywords }}" \
            --url "${{ github.event.client_payload.url }}" \
            --auto-publish
```

### Content Pipeline Integration

```python
from scripts.printify_product_publisher import PrintifyPublisher
from scripts.article_topics import pick_topic

# After publishing article
article = publish_article(
    title="How to Use Claude AI for Content Creation",
    summary="...",
    content="...",
)

# Auto-create POD products
publisher = PrintifyPublisher()
result = publisher.publish_article(
    title=article.title,
    summary=article.summary,
    keywords=article.keywords,
    article_url=article.url,
    content=article.content,
    auto_publish=False  # Review first
)

# Log results
for product in result.products:
    print(f"Created: {product.title} - ${product.profit} margin")
```

## Data Persistence

Products are tracked in `.runtime/pod_products.jsonl` (one JSON object per line):

```json
{
  "id": "tshirt_how_to_build_profitable_saas",
  "external_id": "printify-12345",
  "product_type": "tshirt",
  "title": "How to Build a Profitable SaaS in 30 Days — T-Shirt",
  "description": "...",
  "price_usd": 29.99,
  "cost_usd": 8.0,
  "profit_margin_pct": 73.3,
  "article_title": "How to Build a Profitable SaaS in 30 Days",
  "article_url": "https://example.com/article",
  "keywords": ["SaaS", "startup"],
  "status": "draft",
  "created_at": "2026-06-19T10:30:00+00:00",
  "sales_count": 0,
  "inventory_count": 0
}
```

## Printify API Integration

The publisher connects to Printify's REST API:

- **Endpoint**: `https://api.printify.com/v1`
- **Authentication**: Bearer token in `Authorization` header
- **Shop Operations**: `/shops/{shop_id}/products`
- **Timeout**: 30 seconds per request

### Error Handling

The publisher gracefully handles API failures:

```python
result = publisher.publish_article(...)

if not result.success:
    for error in result.errors:
        print(f"Error: {error}")
else:
    print(f"Successfully created {len(result.products)} products")
```

## Best Practices

### 1. Review Before Publishing

Always test with `auto_publish=False` first:

```python
# Step 1: Create drafts
result = publisher.publish_article(
    title="Your Article",
    summary="Summary",
    keywords=["tag1", "tag2"],
    article_url="https://example.com",
    auto_publish=False  # Draft mode
)

# Step 2: Review products
for p in result.products:
    print(f"✓ {p.title} - ${p.price_usd}")

# Step 3: Publish when ready
publisher.publish_article(..., auto_publish=True)
```

### 2. Use Relevant Keywords

Better keywords = better product recommendations:

```python
# Good: Specific, descriptive keywords
publisher.recommend_products(
    keywords=["AI", "automation", "ChatGPT", "productivity"]
)

# Less effective: Vague keywords
publisher.recommend_products(
    keywords=["stuff", "things"]
)
```

### 3. Monitor Sales and Profit

Regularly review which products are performing:

```python
report = publisher.get_sales_report()

# Identify best performers
for product in report["best_performing"]:
    print(f"{product['title']}: {product['sales']} sales, ${product['profit']} profit")

# Focus on high-margin categories
for ptype, stats in report["by_product_type"].items():
    roi = stats["profit"] / stats["count"] if stats["count"] > 0 else 0
    print(f"{ptype}: ${roi:.2f} profit per product")
```

### 4. Title and Summary Quality

Better content = more compelling products:

```python
# Good summary: Clear, actionable
summary = "A step-by-step guide to building SaaS businesses from scratch, including market research, MVP development, validation strategies, and launch tactics."

# Less effective: Vague
summary = "About SaaS"
```

## Troubleshooting

### Missing Credentials

```
ValueError: Missing Printify credentials. Set PRINTIFY_API_TOKEN and PRINTIFY_SHOP_ID environment variables.
```

**Solution:**
```bash
export PRINTIFY_API_TOKEN="your-token"
export PRINTIFY_SHOP_ID="your-shop-id"
```

### No Products Created

Check the recommendations:
```python
recommendations = publisher.recommend_products(
    keywords=["your", "keywords"],
    article_topic="Your article title"
)
print(recommendations)  # Should return non-empty list
```

### API Timeouts

Increase timeout in constructor:
```python
publisher = PrintifyPublisher(
    api_token="...",
    shop_id="...",
    base_url="https://api.printify.com/v1"
)
# Note: timeout is fixed at 30s in current implementation
```

## Performance

- **Product Creation**: ~2-3 seconds per product
- **API Calls**: ~1 call per product + 1 initial call
- **File I/O**: Minimal (single append per product)
- **Recommendations**: <100ms (local pattern matching)

## Testing

Run tests with:
```bash
pytest tests/test_printify_product_publisher.py -v
```

All 31 tests cover:
- Product template validation
- Recommendation engine accuracy
- Design brief generation
- Publishing workflow
- Inventory tracking
- Sales reporting
- Error handling
- Price calculations

## Future Enhancements

- [ ] Design upload to Printify (auto-generate from article content)
- [ ] Multi-language product variants
- [ ] A/B testing different product designs
- [ ] Inventory sync with sales data
- [ ] Automated reordering when inventory low
- [ ] Social media card generation
- [ ] Email campaign templates

## Support

For issues with:
- **Printify API**: See [Printify Documentation](https://developers.printify.com)
- **Product types**: Check PRODUCT_TEMPLATES in `scripts/printify_product_publisher.py`
- **Recommendations**: Review TOPIC_PRODUCT_MAP for your keywords
