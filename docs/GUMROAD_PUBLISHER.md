# Gumroad Publisher Module

Complete Python module for publishing ebooks, manuals, and self-help courses to Gumroad with automated pricing optimization, affiliate link injection, and sales tracking.

## Features

### Content Publishing
- Convert blog articles (markdown/HTML) to PDF ebooks
- Publish ebooks ($4.99–$9.99), manuals ($7.99–$14.99), courses ($19.99–$49.99+)
- Create product pages with rich descriptions
- Automatic affiliate link injection
- License key generation and management

### Pricing Intelligence
- Automatic price recommendations based on content type
- Pricing tiers: Entry, Standard, Premium, Enterprise
- Factors: word count, templates, worksheets, bestseller status
- Example: 15K-word ebook with templates → $12.99

### Sales & Analytics
- Track sales count per product
- Calculate revenue and ROI
- Generate sales reports
- Fetch product metrics from Gumroad API

### Integration
- Gumroad API v2 integration (full product lifecycle)
- Webhook-ready architecture (sales events)
- Environment variable configuration
- Graceful degradation if dependencies missing

## Installation

### Requirements

```bash
pip install httpx python-dotenv
```

### Optional PDF Generation

For PDF generation from HTML/markdown:

```bash
# Option 1: ReportLab (best for pure Python)
pip install reportlab

# Option 2: WeasyPrint (CSS-based rendering)
pip install weasyprint

# Option 3: System utility (simplest)
sudo apt-get install wkhtmltopdf  # Linux
brew install wkhtmltopdf           # macOS
```

If no PDF library installed, module generates HTML template you can convert externally.

## Environment Setup

### Required Variables

```bash
# Set in server .env or GitHub Secrets (never commit real values)
GUMROAD_API_TOKEN=your_gumroad_api_token_here
GUMROAD_CREATOR_ID=alreadyhere  # Your Gumroad store username
```

### Optional Variables

```bash
# Affiliate links (JSON map keyword → URL)
AFFILIATE_LINKS={"Python book": "https://amzn.to/xxx", "VPS hosting": "https://ref.url"}

# Amazon Associates tag
AMAZON_PARTNER_TAG=alreadyhere-20

# Content repository (for source tracking)
GITHUB_CONTENT_OWNER=quantam101
GITHUB_CONTENT_REPO=content
```

## Quick Start

### 1. Convert Article to Ebook

```python
import gumroad_publisher as gp

# Convert markdown article to PDF
pdf_path = gp.article_to_ebook(
    article_content="""
# My Guide
## Section 1
This is my guide content...
""",
    title="My Complete Guide",
    author="Already Here LLC",
    format_type="markdown"  # or "html"
)

print(f"Generated: {pdf_path}")
```

### 2. Publish to Gumroad

```python
# Publish ebook with auto-pricing
product = gp.publish_ebook(
    title="My Complete Guide",
    description="A comprehensive guide to X with templates and examples",
    pdf_path="/path/to/guide.pdf",
    content_type="ebook",  # or "manual", "course", "bundle"
    word_count=12000,      # Used for price recommendation
)

if product:
    print(f"Published: {product.product_url}")
    print(f"Price: ${product.price:.2f}")
```

### 3. Get Price Recommendation

```python
# Get recommended price based on content
price = gp.get_recommended_price(
    content_type="ebook",
    word_count=15000,
    has_templates=True,
    has_worksheets=False,
)
print(f"Recommended price: ${price:.2f}")
```

### 4. Publish Manual with Templates

```python
product = gp.publish_manual(
    title="Complete Sales Playbook",
    description="Email scripts, templates, and checklists...",
    pdf_path="/path/to/manual.pdf",
    includes_templates=True,
    includes_checklists=True,
    word_count=18000,
)
```

### 5. Publish Course

```python
product = gp.publish_course(
    title="Complete Business System",
    description="5 modules covering all revenue streams...",
    content_file_path="/path/to/course.zip",
    modules_count=5,
    includes_video=True,
    includes_worksheets=True,
    estimated_hours=12.5,
    word_count=45000,
)
```

### 6. Track Sales

```python
# Fetch sales for specific product
sales = gp.fetch_product_sales(product.gumroad_id)
print(f"Sales: {sales['sales_count']}")
print(f"Revenue: ${sales['revenue_usd']:.2f}")

# Generate full report
products = [product1, product2, product3]
report = gp.generate_sales_report(products)
print(report)
```

## Pricing Matrix

### By Content Type

| Type | Entry | Standard | Premium | Enterprise |
|------|-------|----------|---------|------------|
| **Ebook** | $4.99 | $7.99 | $12.99 | $19.99 |
| **Manual** | $7.99 | $11.99 | $19.99 | $34.99 |
| **Course** | $19.99 | $34.99 | $49.99 | $99.99 |
| **Bundle** | $24.99 | $49.99 | $79.99 | $149.99 |

### How Pricing Tiers Are Determined

**Ebook (Entry → Premium)**
- Entry: < 5K words, no templates
- Standard: 5K-10K words, basic templates
- Premium: 10K-20K words, + worksheets
- Enterprise: 20K+ words, + video, + worksheets

**Manual (Entry → Premium)**
- Entry: < 10K words
- Standard: 10K-20K words, templates
- Premium: 20K-30K words, templates + worksheets
- Enterprise: 30K+ words, advanced templates

**Course (Entry → Enterprise)**
- Entry: 1-2 modules, < 20K words
- Standard: 3-4 modules, 20K-40K words
- Premium: 4-5 modules, 40K-80K words, video
- Enterprise: 5+ modules, 80K+ words, video + worksheets

**Bonuses**
- `+has_templates` or `+has_worksheets`: bump up one tier
- `+is_bestseller`: bump up one additional tier
- Example: 15K-word ebook (Standard) + templates = Premium ($12.99)

## API Reference

### Core Functions

#### `article_to_ebook()`

Convert markdown/HTML article to PDF.

```python
article_to_ebook(
    article_content: str,
    title: str,
    author: str = "Already Here LLC",
    format_type: str = "markdown",  # or "html"
    output_path: Optional[str] = None
) -> str
```

**Returns:** Path to generated PDF

**Raises:** `RuntimeError` if no PDF library available

---

#### `publish_ebook()`

Publish ebook to Gumroad.

```python
publish_ebook(
    title: str,
    description: str,
    pdf_path: str,
    author: str = "Already Here LLC",
    content_type: str = "ebook",
    word_count: Optional[int] = None,
    source_article_url: Optional[str] = None,
    price: Optional[float] = None
) -> GumroadProduct | None
```

**Returns:** `GumroadProduct` on success, `None` on error

**Requires:** `GUMROAD_API_TOKEN` environment variable

---

#### `publish_manual()`

Publish manual/guide to Gumroad (convenience wrapper).

```python
publish_manual(
    title: str,
    description: str,
    pdf_path: str,
    author: str = "Already Here LLC",
    includes_templates: bool = True,
    includes_checklists: bool = True,
    word_count: Optional[int] = None,
    source_article_url: Optional[str] = None,
    price: Optional[float] = None
) -> GumroadProduct | None
```

---

#### `publish_course()`

Publish course/training to Gumroad.

```python
publish_course(
    title: str,
    description: str,
    content_file_path: str,
    author: str = "Already Here LLC",
    modules_count: int = 5,
    includes_video: bool = True,
    includes_worksheets: bool = True,
    estimated_hours: float = 10.0,
    word_count: Optional[int] = None,
    price: Optional[float] = None
) -> GumroadProduct | None
```

---

#### `get_recommended_price()`

Get recommended price for product.

```python
get_recommended_price(
    content_type: str | ContentType,
    word_count: Optional[int] = None,
    has_templates: bool = False,
    has_worksheets: bool = False,
    is_bestseller: bool = False
) -> float
```

**Returns:** Recommended price in USD

**Example:**
```python
price = gp.get_recommended_price(
    "manual",
    word_count=25000,
    has_templates=True,
    has_worksheets=True
)
# Returns: $34.99
```

---

#### `fetch_product_sales()`

Fetch sales data for a product.

```python
fetch_product_sales(gumroad_id: str) -> Optional[Dict[str, Any]]
```

**Returns:** Dict with keys: `gumroad_id`, `name`, `sales_count`, `price`, `revenue_usd`, `url`

---

#### `update_product_with_affiliate_links()`

Inject affiliate links into product description.

```python
update_product_with_affiliate_links(
    gumroad_id: str,
    content_type: str,
    affiliate_links: Optional[Dict[str, str]] = None
) -> bool
```

**Returns:** `True` if successful

---

#### `get_all_products()`

Fetch all products from Gumroad store.

```python
get_all_products() -> List[Dict[str, Any]]
```

---

#### `generate_sales_report()`

Generate formatted sales report.

```python
generate_sales_report(
    products: Optional[List[GumroadProduct]] = None
) -> str
```

**Returns:** Formatted report string

---

### Data Classes

#### `GumroadProduct`

Represents a published product.

```python
class GumroadProduct:
    gumroad_id: str
    name: str
    description: str
    price: float
    content_type: str
    source_article_url: Optional[str]
    product_url: Optional[str]
    license_key: Optional[str]
    sales_count: int
    revenue_usd: float
    created_at: datetime
```

**Methods:**
- `to_dict()` — Convert to JSON-serializable dictionary

---

#### `ContentType`

Enum for content types.

```python
class ContentType(Enum):
    EBOOK = "ebook"      # $4.99–$9.99
    MANUAL = "manual"    # $7.99–$14.99
    COURSE = "course"    # $19.99–$49.99+
    BUNDLE = "bundle"    # $24.99–$99.99+
```

---

#### `PricingTier`

Enum for pricing tiers.

```python
class PricingTier(Enum):
    ENTRY = "entry"            # $4.99–$7.99
    STANDARD = "standard"      # $9.99–$14.99
    PREMIUM = "premium"        # $19.99–$34.99
    ENTERPRISE = "enterprise"  # $49.99+
```

## Usage Examples

### Example 1: Blog Article → Ebook → Publish

```python
import gumroad_publisher as gp

# 1. Load article from file
with open("my_guide.md", "r") as f:
    article = f.read()

# 2. Convert to PDF
pdf = gp.article_to_ebook(
    article_content=article,
    title="My Complete Guide",
    author="Stephen Franklin"
)

# 3. Publish to Gumroad
product = gp.publish_ebook(
    title="My Complete Guide",
    description="Everything you need to know...",
    pdf_path=pdf,
    word_count=12000,
    price=9.99
)

# 4. Share
print(f"Published: {product.product_url}")
```

### Example 2: Batch Publish Multiple Products

```python
articles = [
    ("guide1.md", "Quick Start Guide", "ebook"),
    ("guide2.md", "Advanced Playbook", "manual"),
    ("course.md", "Complete Course", "course"),
]

products = []

for filepath, title, content_type in articles:
    with open(filepath, "r") as f:
        content = f.read()
    
    pdf = gp.article_to_ebook(content, title)
    
    product = gp.publish_ebook(
        title=title,
        description=f"Comprehensive {title.lower()}",
        pdf_path=pdf,
        content_type=content_type,
        word_count=len(content.split()),
    )
    
    if product:
        products.append(product)

# Generate report
report = gp.generate_sales_report(products)
print(report)
```

### Example 3: Price Optimization

```python
# Calculate optimal prices for your product line
products = [
    ("ebook", 8000, False, False),
    ("manual", 15000, True, True),
    ("course", 50000, True, True),
]

for content_type, words, has_templates, has_worksheets in products:
    price = gp.get_recommended_price(
        content_type,
        word_count=words,
        has_templates=has_templates,
        has_worksheets=has_worksheets,
    )
    print(f"{content_type}: ${price:.2f} ({words} words)")
```

### Example 4: Track Sales Daily

```python
import json
from datetime import datetime

# Fetch all products
all_products = gp.get_all_products()

# Track sales
sales_log = {
    "timestamp": datetime.now().isoformat(),
    "products": []
}

for p in all_products:
    sales = gp.fetch_product_sales(p["id"])
    if sales:
        sales_log["products"].append({
            "name": sales["name"],
            "sales": sales["sales_count"],
            "revenue": sales["revenue_usd"],
        })

# Save to file
with open("sales_log.jsonl", "a") as f:
    f.write(json.dumps(sales_log) + "\n")
```

## Security Considerations

### API Token Storage

**Never** commit GUMROAD_API_TOKEN to version control.

```bash
# .gitignore
.env
.env.local
.env.production
```

Store token in:
- GitHub Secrets (for CI/CD)
- Server environment variables
- `.env` file (never committed)

### Webhook Verification (Future)

When implementing sales webhooks:

```python
import hmac
import hashlib

def verify_webhook(payload: str, signature: str, secret: str) -> bool:
    """Verify Gumroad webhook signature."""
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)
```

## Troubleshooting

### PDF Generation Fails

**Problem:** "No PDF library available"

**Solution:**
```bash
# Install reportlab (recommended)
pip install reportlab

# Or install weasyprint
pip install weasyprint

# Or install system utility
sudo apt-get install wkhtmltopdf
```

### Gumroad API Errors

**Problem:** "Failed to create product: 401"

**Solution:** Verify API token is correct and has scope.

```bash
# Test API token
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.gumroad.com/v2/products
```

### File Not Found

**Problem:** "PDF file not found: /path/to/file.pdf"

**Solution:** Verify file path is absolute and exists.

```python
import os
pdf_path = os.path.abspath("guide.pdf")
assert os.path.exists(pdf_path), f"File not found: {pdf_path}"
```

## Advanced Usage

### Custom Pricing Strategy

```python
def get_dynamic_price(content_type: str, sales_count: int) -> float:
    """Adjust price based on sales performance."""
    base_price = gp.get_recommended_price(content_type, 15000)
    
    if sales_count > 100:
        return base_price * 1.5  # Bestseller premium
    elif sales_count < 10:
        return base_price * 0.8  # Discount to accelerate
    else:
        return base_price

price = get_dynamic_price("ebook", sales_count=45)
```

### Affiliate Link Management

```python
# Load affiliate links from external source
import requests

response = requests.get("https://api.example.com/affiliate-links")
affiliate_links = response.json()

# Update all products
for product_id in product_ids:
    gp.update_product_with_affiliate_links(
        product_id,
        "ebook",
        affiliate_links
    )
```

### Multi-Platform Publishing

```python
# After Gumroad, publish to other platforms
from social_media_publishers import publish_to_platform

product = gp.publish_ebook(...)

# Cross-post to other platforms
publish_to_platform("gumroad", product.product_url)
publish_to_platform("medium", product.product_url)
publish_to_platform("substack", product.product_url)
```

## Integration with ProfitEngine

### Webhook Handler

```python
from fastapi import FastAPI, HTTPException
import gumroad_publisher as gp

app = FastAPI()

@app.post("/webhooks/gumroad/sale")
async def on_gumroad_sale(data: dict):
    """Handle Gumroad sale webhook."""
    product_id = data.get("product_id")
    buyer_email = data.get("buyer_email")
    
    # Log sale
    sales = gp.fetch_product_sales(product_id)
    
    # Generate license key (future)
    license_key = gp.generate_license_key(product_id)
    
    # Send confirmation email
    # send_email(buyer_email, f"License: {license_key}")
    
    return {"status": "ok"}
```

### Dashboard Widget

```python
def get_sales_summary():
    """Get sales data for dashboard."""
    products = gp.get_all_products()
    
    total_revenue = 0
    total_sales = 0
    
    for p in products:
        sales = gp.fetch_product_sales(p["id"])
        if sales:
            total_revenue += sales["revenue_usd"]
            total_sales += sales["sales_count"]
    
    return {
        "total_products": len(products),
        "total_sales": total_sales,
        "total_revenue": total_revenue,
        "average_price": total_revenue / total_sales if total_sales > 0 else 0,
    }
```

## File Structure

```
scripts/
├── gumroad_publisher.py          # Main module
├── gumroad_publisher_examples.py # Usage examples
└── ... other scripts

docs/
└── GUMROAD_PUBLISHER.md          # This file
```

## Testing

```bash
# Basic smoke test (no API token required)
python scripts/gumroad_publisher.py

# Run examples (requires GUMROAD_API_TOKEN for publishing)
python scripts/gumroad_publisher_examples.py

# Check pricing logic
python -c "
import gumroad_publisher as gp
price = gp.get_recommended_price('ebook', 15000, True, False)
print(f'Price: ${price:.2f}')
"
```

## Support & Development

For issues, examples, or feature requests:

1. Check troubleshooting section above
2. Review example scripts
3. Test with minimal example first
4. Check Gumroad API documentation

## License

Part of ProfitEngine v5. Proprietary — Not for redistribution.

## Author

Already Here LLC — Content Monetization System
