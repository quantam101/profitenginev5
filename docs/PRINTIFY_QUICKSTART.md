# Printify POD Publisher — Quick Start

Automated print-on-demand product creation from blog articles.

## 30 Second Setup

### 1. Get API Credentials

Visit [Printify Dashboard](https://dashboard.printify.com):
- Copy your **API Token** from Account Settings → API
- Copy your **Shop ID** from Dashboard

### 2. Set Environment Variables

```bash
export PRINTIFY_API_TOKEN="your-api-token-here"
export PRINTIFY_SHOP_ID="your-shop-id-here"
```

Or add to `.env`:
```
PRINTIFY_API_TOKEN=your-api-token-here
PRINTIFY_SHOP_ID=your-shop-id-here
```

### 3. Run It

```python
from scripts.printify_product_publisher import PrintifyPublisher

publisher = PrintifyPublisher()

result = publisher.publish_article(
    title="How to Build a Profitable SaaS",
    summary="Complete guide to SaaS fundamentals",
    keywords=["SaaS", "startup", "business"],
    article_url="https://example.com/article",
    auto_publish=False  # Review first, then publish
)

for product in result.products:
    print(f"✓ {product.title} - ${product.profit} margin")
```

## Key Functions

### Publish Article
```python
result = publisher.publish_article(
    title="Article Title",
    summary="Summary text",
    keywords=["keyword1", "keyword2"],
    article_url="https://example.com",
    auto_publish=False
)
```

Creates t-shirts, mugs, hoodies, caps, and books automatically.

### Get Recommendations
```python
recommendations = publisher.recommend_products(
    keywords=["AI", "automation"],
    article_topic="Using AI for Productivity"
)
# Returns: ['tshirt', 'hoodie', 'mug']
```

Smart recommendations based on article content.

### Check Inventory
```python
stats = publisher.get_inventory_stats()
print(f"Total Products: {stats['total_products']}")
print(f"Total Profit: ${stats['total_potential_profit']}")
```

### View Sales Report
```python
report = publisher.get_sales_report()
print(f"Revenue: ${report['total_revenue']}")
print(f"Best Seller: {report['best_performing'][0]['title']}")
```

## Product Pricing

All products have 70%+ profit margins:

| Product | Retail | Cost | Profit |
|---------|--------|------|--------|
| T-Shirt | $29.99 | $8 | $21.99 |
| Mug | $14.99 | $3.50 | $11.49 |
| Hoodie | $49.99 | $15 | $34.99 |
| Cap | $19.99 | $4.50 | $15.49 |
| Book | $24.99 | $5 | $19.99 |

**Average profit per product: $20.79**

## Smart Recommendations by Topic

### AI / Automation
✓ T-Shirt, Hoodie, Mug  
Keywords: AI, ChatGPT, automation, machine learning

### Business / SaaS / Startup
✓ T-Shirt, Hoodie, Book  
Keywords: SaaS, founder, scaling, revenue

### Passive Income / Monetization
✓ T-Shirt, Hoodie, Book, Mug  
Keywords: Passive income, affiliate, monetize

### Blogging / Content / SEO
✓ T-Shirt, Mug, Cap  
Keywords: Blog, content, SEO, keywords

### Development / Coding
✓ T-Shirt, Hoodie, Cap  
Keywords: Developer, code, Python, React

### Finance / Crypto
✓ T-Shirt, Hoodie, Book  
Keywords: Finance, crypto, Bitcoin, trading

### Design / Creative
✓ Hoodie, Cap, Mug  
Keywords: Design, brand, UX, UI

## CLI Commands

### Publish Article
```bash
python scripts/printify_product_publisher.py publish \
  --title "Your Article Title" \
  --summary "Article summary" \
  --keywords "keyword1,keyword2,keyword3" \
  --url "https://example.com/article" \
  --auto-publish
```

### List Products
```bash
# All products
python scripts/printify_product_publisher.py list

# T-shirts only
python scripts/printify_product_publisher.py list --type tshirt

# Draft products
python scripts/printify_product_publisher.py list --status draft
```

### View Statistics
```bash
python scripts/printify_product_publisher.py stats
```

Output:
```
{
  "total_products": 24,
  "draft_products": 8,
  "published_products": 16,
  "total_sales": 127,
  "products_by_type": {
    "tshirt": 8,
    "hoodie": 4,
    "mug": 6,
    "hat": 3,
    "book": 3
  }
}
```

### Generate Sales Report
```bash
python scripts/printify_product_publisher.py report
```

Output:
```json
{
  "total_revenue": 3847.73,
  "total_profit": 2635.47,
  "average_profit_margin_pct": 74.2,
  "best_performing": [
    {
      "title": "SaaS Pricing Strategies — T-Shirt",
      "sales": 23,
      "profit": 505.77
    }
  ]
}
```

## Integration Examples

### GitHub Actions
```yaml
- name: Publish POD Products
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

### Python Script
```python
from scripts.printify_product_publisher import PrintifyPublisher

publisher = PrintifyPublisher()

# Publish from blog API
articles = fetch_recent_articles()

for article in articles:
    result = publisher.publish_article(
        title=article.title,
        summary=article.summary,
        keywords=article.tags,
        article_url=article.url,
        auto_publish=False
    )

    print(f"Created {len(result.products)} products for '{article.title}'")
```

## Common Patterns

### Draft Before Publishing
```python
# Step 1: Create drafts
result = publisher.publish_article(
    title="Article",
    summary="Summary",
    keywords=["tag1"],
    article_url="https://example.com",
    auto_publish=False  # Draft mode
)

# Step 2: Review in Printify dashboard
print(f"Review {len(result.products)} products at printify.com")

# Step 3: Publish when ready
result = publisher.publish_article(
    title="Article",
    summary="Summary",
    keywords=["tag1"],
    article_url="https://example.com",
    auto_publish=True  # Live
)
```

### Monitor Sales Performance
```python
import json
from datetime import datetime

publisher = PrintifyPublisher()
report = publisher.get_sales_report()

# Log to file
with open("pod_sales_log.jsonl", "a") as f:
    f.write(json.dumps({
        "timestamp": datetime.now().isoformat(),
        "total_revenue": report["total_revenue"],
        "total_profit": report["total_profit"],
        "products": len(report["by_product_type"])
    }) + "\n")
```

### Batch Process Articles
```python
articles = [
    {"title": "Article 1", "summary": "...", "keywords": ["a", "b"]},
    {"title": "Article 2", "summary": "...", "keywords": ["c", "d"]},
]

publisher = PrintifyPublisher()

for article in articles:
    publisher.publish_article(
        title=article["title"],
        summary=article["summary"],
        keywords=article["keywords"],
        article_url=f"https://example.com/{article['title'].lower()}",
        auto_publish=False
    )

# View all drafts
drafts = publisher.list_products(status="draft")
print(f"Created {len(drafts)} draft products ready for review")
```

## Troubleshooting

### Error: Missing Printify credentials
```
ValueError: Missing Printify credentials. Set PRINTIFY_API_TOKEN and PRINTIFY_SHOP_ID environment variables.
```

**Fix:** Set the environment variables:
```bash
export PRINTIFY_API_TOKEN="your-token"
export PRINTIFY_SHOP_ID="your-shop-id"
```

### No products created
Check recommendations:
```python
recs = publisher.recommend_products(
    keywords=["your", "keywords"],
    article_topic="Your article title"
)
print(recs)  # Should return products
```

### Products not appearing on Printify
1. Check they're in "published" status:
   ```python
   products = publisher.list_products(status="published")
   ```

2. Verify API token is valid (check Printify dashboard)

3. Try auto_publish=False first to create drafts and review

## Cost Analysis

**Projected earnings from 10 articles:**
- 10 articles × 4 products each = 40 products
- Average profit per product = $20.79
- Potential profit at 100% sell-through = $831.60

**Realistic scenario (10% sell-through):**
- 40 products × 10% sell = 4 units
- 4 units × $20.79 = $83.16 per article
- 10 articles = $831.60 total

**Conservative scenario (5% sell-through):**
- 40 products × 5% sell = 2 units
- 2 units × $20.79 = $41.58 per article
- 10 articles = $415.80 total

## Next Steps

1. **Get Credentials**: Copy API token and Shop ID from Printify
2. **Set Environment**: Export to `~/.bashrc` or `.env`
3. **Test**: Run `python -m pytest tests/test_printify_product_publisher.py`
4. **Publish**: Create your first product with `publisher.publish_article(...)`
5. **Review**: Check Printify dashboard for created products
6. **Monitor**: Use `publisher.get_sales_report()` to track sales

## Full Documentation

See [PRINTIFY_POD_PUBLISHING.md](PRINTIFY_POD_PUBLISHING.md) for:
- Complete API reference
- Advanced workflows
- Integration patterns
- Performance metrics
- Future enhancements
