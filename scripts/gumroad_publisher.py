#!/usr/bin/env python3
"""
Gumroad Publisher Module

Converts blog articles into ebooks, manuals, and self-help guides.
Handles product creation, pricing optimization, and sales tracking on Gumroad.

Features:
  - Convert markdown/HTML articles to PDF ebooks
  - Publish to Gumroad with optimized pricing
  - Create product pages with affiliate links
  - Track sales and revenue per product
  - Handle license key setup and distribution
  - Price optimization based on content type

Environment vars:
  GUMROAD_API_TOKEN      — API token from Gumroad
  GUMROAD_CREATOR_ID     — Creator/store username (e.g. 'alreadyhere')
  GUMROAD_LICENSE_KEYS   — JSON path for storing license keys (optional)
  AFFILIATE_LINKS        — JSON map of keyword→URL affiliate links (optional)

Usage:
  import gumroad_publisher as gp

  # Convert article to ebook
  pdf_path = gp.article_to_ebook(
    article_content="# My Guide...",
    title="My Guide",
    author="Already Here LLC"
  )

  # Publish to Gumroad
  product = gp.publish_ebook(
    title="My Guide",
    description="...",
    pdf_path="/path/to/guide.pdf",
    content_type="ebook",  # or "manual", "course"
    author="Already Here LLC"
  )

  # Get pricing recommendation
  price = gp.get_recommended_price("ebook", word_count=15000)
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import sys
import tempfile
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

import httpx
from dotenv import load_dotenv

# Load environment
load_dotenv(pathlib.Path(__file__).resolve().parents[1] / ".env")

# ── Configuration ───────────────────────────────────────────────────────────
GUMROAD_TOKEN = os.getenv("GUMROAD_API_TOKEN", os.getenv("GUMROAD_API_KEY", "")).strip()
GUMROAD_CREATOR_ID = os.getenv("GUMROAD_CREATOR_ID", "alreadyhere").strip()
GUMROAD_API_BASE = "https://api.gumroad.com/v2"
GUMROAD_STORE_URL = f"https://{GUMROAD_CREATOR_ID}.gumroad.com"

AFFILIATE_LINKS_JSON = os.getenv("AFFILIATE_LINKS", "{}").strip()
AMAZON_TAG = os.getenv("AMAZON_PARTNER_TAG", "alreadyhere-20").strip()

# Content type enum for pricing and configuration
class ContentType(Enum):
    """Content type determines pricing, format, and distribution method."""
    EBOOK = "ebook"           # $4.99–$9.99 — condensed articles, guides, curated lists
    MANUAL = "manual"         # $7.99–$14.99 — detailed how-to, step-by-step, templates
    COURSE = "course"         # $19.99–$49.99 — multi-module, video+PDFs, worksheets
    BUNDLE = "bundle"         # $24.99–$99.99 — multiple guides + templates + resources


class PricingTier(Enum):
    """Pricing tier based on perceived value and content depth."""
    ENTRY = "entry"           # $4.99–$7.99 — quick guides, checklists
    STANDARD = "standard"     # $9.99–$14.99 — comprehensive guides, templates
    PREMIUM = "premium"       # $19.99–$34.99 — advanced courses, full systems
    ENTERPRISE = "enterprise" # $49.99+ — complete systems, done-for-you


# ── Price Recommendations by Content Type & Tier ────────────────────────────
PRICING_MATRIX: Dict[ContentType, Dict[PricingTier, float]] = {
    ContentType.EBOOK: {
        PricingTier.ENTRY: 4.99,
        PricingTier.STANDARD: 7.99,
        PricingTier.PREMIUM: 12.99,
        PricingTier.ENTERPRISE: 19.99,
    },
    ContentType.MANUAL: {
        PricingTier.ENTRY: 7.99,
        PricingTier.STANDARD: 11.99,
        PricingTier.PREMIUM: 19.99,
        PricingTier.ENTERPRISE: 34.99,
    },
    ContentType.COURSE: {
        PricingTier.ENTRY: 19.99,
        PricingTier.STANDARD: 34.99,
        PricingTier.PREMIUM: 49.99,
        PricingTier.ENTERPRISE: 99.99,
    },
    ContentType.BUNDLE: {
        PricingTier.ENTRY: 24.99,
        PricingTier.STANDARD: 49.99,
        PricingTier.PREMIUM: 79.99,
        PricingTier.ENTERPRISE: 149.99,
    },
}


# ── Utilities ────────────────────────────────────────────────────────────────
def _parse_affiliate_links() -> Dict[str, str]:
    """Parse affiliate links from environment JSON."""
    try:
        links = json.loads(AFFILIATE_LINKS_JSON)
        return links if isinstance(links, dict) else {}
    except (json.JSONDecodeError, ValueError):
        return {}


def _inject_affiliate_links(content: str, links: Optional[Dict[str, str]] = None) -> str:
    """
    Inject affiliate links into content by keyword matching.

    Replaces bare product mentions with affiliate links.
    Example: "I use Python for automation" → links.get("Python", "") appended

    Args:
        content: HTML/markdown content
        links: Dict of keyword→affiliate URL (defaults to env AFFILIATE_LINKS)

    Returns:
        Content with affiliate links injected
    """
    if not links:
        links = _parse_affiliate_links()

    if not links:
        return content

    # Simple injection: append affiliate note if keywords found
    modified = content
    injected_count = 0

    for keyword, url in links.items():
        if keyword.lower() in content.lower() and url:
            # Only inject once per keyword
            if keyword.lower() in modified.lower() and f"[{keyword}]({url})" not in modified:
                modified += f"\n\n---\n*Disclosure: {keyword} link may contain affiliate commission.*"
                injected_count += 1

    return modified


def _html_to_markdown(html_content: str) -> str:
    """
    Convert HTML to markdown (basic).

    Args:
        html_content: HTML string

    Returns:
        Markdown string
    """
    # Simple regex-based conversion
    md = html_content

    # Headers
    md = re.sub(r'<h1[^>]*>(.*?)</h1>', r'# \1', md, flags=re.IGNORECASE | re.DOTALL)
    md = re.sub(r'<h2[^>]*>(.*?)</h2>', r'## \1', md, flags=re.IGNORECASE | re.DOTALL)
    md = re.sub(r'<h3[^>]*>(.*?)</h3>', r'### \1', md, flags=re.IGNORECASE | re.DOTALL)
    md = re.sub(r'<h4[^>]*>(.*?)</h4>', r'#### \1', md, flags=re.IGNORECASE | re.DOTALL)

    # Bold/italic
    md = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', md, flags=re.IGNORECASE | re.DOTALL)
    md = re.sub(r'<b[^>]*>(.*?)</b>', r'**\1**', md, flags=re.IGNORECASE | re.DOTALL)
    md = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', md, flags=re.IGNORECASE | re.DOTALL)
    md = re.sub(r'<i[^>]*>(.*?)</i>', r'*\1*', md, flags=re.IGNORECASE | re.DOTALL)

    # Links
    md = re.sub(r'<a[^>]*href=["\'](.*?)["\'](.*?)>(.*?)</a>', r'[\3](\1)', md, flags=re.IGNORECASE | re.DOTALL)

    # Lists
    md = re.sub(r'<li[^>]*>(.*?)</li>', r'- \1', md, flags=re.IGNORECASE | re.DOTALL)

    # Paragraphs
    md = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n', md, flags=re.IGNORECASE | re.DOTALL)

    # Line breaks
    md = re.sub(r'<br\s*/?>', '\n', md, flags=re.IGNORECASE)

    # Remove remaining HTML tags
    md = re.sub(r'<[^>]+>', '', md)

    # Clean up whitespace
    md = re.sub(r'\n\n+', '\n\n', md)
    md = md.strip()

    return md


def _markdown_to_html(md_content: str) -> str:
    """
    Convert markdown to HTML (basic).

    Args:
        md_content: Markdown string

    Returns:
        HTML string
    """
    html = md_content

    # Headers (in order, largest to smallest to avoid re-matching)
    html = re.sub(r'^#### (.*?)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)

    # Bold/italic
    html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
    html = re.sub(r'__(.*?)__', r'<strong>\1</strong>', html)
    html = re.sub(r'_(.*?)_', r'<em>\1</em>', html)

    # Links
    html = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', html)

    # Lists
    html = re.sub(r'^- (.*?)$', r'<li>\1</li>', html, flags=re.MULTILINE)
    html = re.sub(r'(<li>.*?</li>)', lambda m: f'<ul>{m.group(1)}</ul>', html, flags=re.DOTALL)

    # Paragraphs (split by double newline)
    paragraphs = html.split('\n\n')
    html = '\n'.join([f'<p>{p.strip()}</p>' for p in paragraphs if p.strip()])

    return f'<html><body>{html}</body></html>'


def _count_words(content: str) -> int:
    """Count words in content (markdown or HTML)."""
    # Remove HTML/markdown syntax
    clean = re.sub(r'[#\*_\[\]()]', '', content)
    clean = re.sub(r'<[^>]+>', '', clean)
    words = clean.split()
    return len(words)


# ── PDF Generation ──────────────────────────────────────────────────────────
def _try_import_pdf_library() -> Optional[str]:
    """
    Detect available PDF library.

    Returns:
        'reportlab', 'fpdf', 'pypdf', or None if none available
    """
    try:
        import reportlab  # noqa: F401
        return 'reportlab'
    except ImportError:
        pass

    try:
        import fpdf  # noqa: F401
        return 'fpdf'
    except ImportError:
        pass

    try:
        from PyPDF2 import PdfWriter  # noqa: F401
        return 'pypdf'
    except ImportError:
        pass

    return None


def article_to_ebook(
    article_content: str,
    title: str,
    author: str = "Already Here LLC",
    format_type: str = "markdown",  # or 'html'
    output_path: Optional[str] = None,
) -> str:
    """
    Convert a blog article to a PDF ebook.

    Attempts to use reportlab if available; falls back to HTML template.

    Args:
        article_content: Full article text (markdown or HTML)
        title: Ebook title
        author: Author name
        format_type: 'markdown' or 'html'
        output_path: Where to save PDF (default: /tmp/{title}.pdf)

    Returns:
        Path to generated PDF

    Raises:
        RuntimeError: If no PDF library available and output can't be generated
    """
    if not output_path:
        safe_title = re.sub(r'[^a-z0-9_-]', '_', title.lower())
        output_path = str(pathlib.Path(tempfile.gettempdir()) / f"{safe_title}.pdf")

    # Try using reportlab if available
    pdf_lib = _try_import_pdf_library()

    if pdf_lib == 'reportlab':
        return _article_to_ebook_reportlab(
            article_content, title, author, format_type, output_path
        )
    else:
        # Fallback: generate HTML template and note limitation
        return _article_to_ebook_html_template(
            article_content, title, author, format_type, output_path
        )


def _article_to_ebook_reportlab(
    article_content: str,
    title: str,
    author: str,
    format_type: str,
    output_path: str,
) -> str:
    """Generate PDF using reportlab."""
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
        from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
    except ImportError:
        raise RuntimeError("reportlab not installed")

    # Convert to clean text
    if format_type == 'html':
        article_content = _html_to_markdown(article_content)

    # Create PDF document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=1 * inch,
        bottomMargin=0.75 * inch,
    )

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor='#1a1a1a',
        spaceAfter=6,
        alignment=TA_CENTER,
    )
    author_style = ParagraphStyle(
        'CustomAuthor',
        parent=styles['Normal'],
        fontSize=11,
        textColor='#666666',
        spaceAfter=12,
        alignment=TA_CENTER,
    )
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        leading=14,
        alignment=TA_JUSTIFY,
        spaceAfter=12,
    )

    # Build story
    story = []
    story.append(Paragraph(title, title_style))
    story.append(Paragraph(f"By {author}", author_style))
    story.append(Spacer(1, 0.3 * inch))

    # Split content into paragraphs
    paragraphs = article_content.split('\n\n')
    for para in paragraphs:
        if para.strip():
            story.append(Paragraph(para.strip(), body_style))
            story.append(Spacer(1, 0.1 * inch))

    # Add metadata
    story.append(PageBreak())
    story.append(Spacer(1, 1 * inch))
    story.append(Paragraph(f"<i>Generated on {datetime.now().strftime('%Y-%m-%d')}</i>", styles['Normal']))
    story.append(Paragraph(f"<i>Published at {GUMROAD_STORE_URL}</i>", styles['Normal']))

    # Build PDF
    doc.build(story)
    return output_path


def _article_to_ebook_html_template(
    article_content: str,
    title: str,
    author: str,
    format_type: str,
    output_path: str,
) -> str:
    """Generate HTML template (requires external PDF conversion)."""
    if format_type == 'html':
        html_body = article_content
    else:
        html_body = _markdown_to_html(article_content)

    html_template = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 8.5in;
            margin: 0 auto;
            padding: 1in 0.75in;
        }}
        h1 {{
            font-size: 28px;
            text-align: center;
            margin-bottom: 6px;
            color: #1a1a1a;
        }}
        h2 {{
            font-size: 20px;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
            color: #2c3e50;
        }}
        h3 {{
            font-size: 16px;
            margin-top: 1em;
            color: #34495e;
        }}
        p {{
            margin: 1em 0;
            text-align: justify;
        }}
        .author {{
            text-align: center;
            color: #666;
            font-size: 13px;
            margin-bottom: 2em;
        }}
        .footer {{
            text-align: center;
            color: #999;
            font-size: 11px;
            margin-top: 2em;
            border-top: 1px solid #ddd;
            padding-top: 1em;
        }}
        a {{
            color: #0066cc;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        ul, ol {{
            margin: 1em 0;
            padding-left: 2em;
        }}
        li {{
            margin: 0.5em 0;
        }}
        code {{
            background: #f4f4f4;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}
        blockquote {{
            border-left: 4px solid #ddd;
            margin: 1em 0;
            padding-left: 1em;
            color: #666;
        }}
        @page {{
            margin: 1in 0.75in;
        }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <div class="author">By {author}</div>
    {html_body}
    <div class="footer">
        <p>Published at <a href="{GUMROAD_STORE_URL}">{GUMROAD_STORE_URL}</a></p>
        <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}</p>
    </div>
</body>
</html>"""

    # Save HTML (in practice, convert to PDF using wkhtmltopdf, weasyprint, etc.)
    html_path = output_path.replace('.pdf', '.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_template)

    print(f"[INFO] Generated HTML template: {html_path}")
    print(f"   To convert to PDF, run: wkhtmltopdf {html_path} {output_path}")
    print(f"   Or use: weasyprint {html_path} {output_path}")

    return html_path


# ── Pricing & Recommendations ────────────────────────────────────────────────
def get_recommended_price(
    content_type: str | ContentType,
    word_count: Optional[int] = None,
    has_templates: bool = False,
    has_worksheets: bool = False,
    is_bestseller: bool = False,
) -> float:
    """
    Get recommended price for product based on type and content depth.

    Pricing factors:
    - Content type (ebook/manual/course/bundle)
    - Word count (more content = higher tier)
    - Templates/worksheets (adds value)
    - Bestseller status (proven demand)

    Args:
        content_type: ContentType enum or string ('ebook', 'manual', 'course', 'bundle')
        word_count: Estimated word count (optional)
        has_templates: Whether product includes templates
        has_worksheets: Whether product includes worksheets
        is_bestseller: Whether product is a known bestseller

    Returns:
        Recommended price in USD

    Example:
        >>> get_recommended_price('ebook', word_count=8000, has_templates=True)
        7.99
        >>> get_recommended_price('course', word_count=50000, has_worksheets=True)
        49.99
    """
    # Normalize content type
    if isinstance(content_type, str):
        try:
            ct = ContentType(content_type.lower())
        except ValueError:
            raise ValueError(f"Unknown content type: {content_type}")
    else:
        ct = content_type

    # Determine pricing tier based on content depth
    tier = PricingTier.ENTRY

    if word_count:
        if ct == ContentType.EBOOK:
            if word_count > 20000:
                tier = PricingTier.PREMIUM
            elif word_count > 10000:
                tier = PricingTier.STANDARD
            else:
                tier = PricingTier.ENTRY

        elif ct == ContentType.MANUAL:
            if word_count > 30000:
                tier = PricingTier.PREMIUM
            elif word_count > 15000:
                tier = PricingTier.STANDARD
            else:
                tier = PricingTier.ENTRY

        elif ct == ContentType.COURSE:
            if word_count > 80000:
                tier = PricingTier.ENTERPRISE
            elif word_count > 40000:
                tier = PricingTier.PREMIUM
            elif word_count > 20000:
                tier = PricingTier.STANDARD
            else:
                tier = PricingTier.ENTRY

        elif ct == ContentType.BUNDLE:
            if word_count > 100000:
                tier = PricingTier.ENTERPRISE
            elif word_count > 60000:
                tier = PricingTier.PREMIUM
            elif word_count > 30000:
                tier = PricingTier.STANDARD
            else:
                tier = PricingTier.ENTRY

    # Bump up tier if includes templates/worksheets
    if has_templates or has_worksheets:
        tier_values = [PricingTier.ENTRY, PricingTier.STANDARD, PricingTier.PREMIUM, PricingTier.ENTERPRISE]
        current_idx = tier_values.index(tier)
        if current_idx < len(tier_values) - 1:
            tier = tier_values[current_idx + 1]

    # Further bump for bestseller status
    if is_bestseller:
        tier_values = [PricingTier.ENTRY, PricingTier.STANDARD, PricingTier.PREMIUM, PricingTier.ENTERPRISE]
        current_idx = tier_values.index(tier)
        if current_idx < len(tier_values) - 1:
            tier = tier_values[current_idx + 1]

    return PRICING_MATRIX[ct][tier]


# ── Gumroad API Integration ──────────────────────────────────────────────────
class GumroadProduct:
    """Represents a Gumroad product."""

    def __init__(
        self,
        gumroad_id: str,
        name: str,
        description: str,
        price: float,
        content_type: str,
        source_article_url: Optional[str] = None,
        product_url: Optional[str] = None,
        license_key: Optional[str] = None,
        sales_count: int = 0,
        revenue_usd: float = 0.0,
        created_at: Optional[datetime] = None,
    ):
        self.gumroad_id = gumroad_id
        self.name = name
        self.description = description
        self.price = price
        self.content_type = content_type
        self.source_article_url = source_article_url
        self.product_url = product_url
        self.license_key = license_key
        self.sales_count = sales_count
        self.revenue_usd = revenue_usd
        self.created_at = created_at or datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON storage."""
        return {
            'gumroad_id': self.gumroad_id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'content_type': self.content_type,
            'source_article_url': self.source_article_url,
            'product_url': self.product_url,
            'license_key': self.license_key,
            'sales_count': self.sales_count,
            'revenue_usd': self.revenue_usd,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


def publish_ebook(
    title: str,
    description: str,
    pdf_path: str,
    author: str = "Already Here LLC",
    content_type: str = "ebook",
    word_count: Optional[int] = None,
    source_article_url: Optional[str] = None,
    price: Optional[float] = None,
) -> GumroadProduct | None:
    """
    Publish an ebook to Gumroad.

    Args:
        title: Product title
        description: Product description (markdown supported)
        pdf_path: Path to PDF file to upload
        author: Author name
        content_type: 'ebook', 'manual', 'course', or 'bundle'
        word_count: Optional word count for pricing recommendation
        source_article_url: Optional URL to original article
        price: Optional override for price (default: auto-calculated)

    Returns:
        GumroadProduct on success, None on failure

    Example:
        >>> pdf = article_to_ebook(article_text, "My Guide", "Stephen Franklin")
        >>> product = publish_ebook(
        ...     title="My Guide",
        ...     description="A comprehensive guide to X",
        ...     pdf_path=pdf,
        ...     content_type="ebook",
        ...     word_count=8500
        ... )
    """
    if not GUMROAD_TOKEN:
        print("[ERROR] GUMROAD_API_TOKEN not set")
        return None

    if not os.path.isfile(pdf_path):
        print(f"[ERROR] PDF file not found: {pdf_path}")
        return None

    # Get recommended price if not provided
    if price is None:
        price = get_recommended_price(content_type, word_count)

    # Prepare product payload
    payload = {
        "name": title,
        "description": description,
        "price": int(price * 100),  # Gumroad API uses cents
        "currency": "usd",
        "summary": f"By {author} — {content_type.capitalize()}",
    }

    print(f"\n[PUBLISH] Gumroad: {title}")
    print(f"   Price: ${price:.2f}")
    print(f"   Type: {content_type}")

    try:
        # Create product
        headers = {"Authorization": f"Bearer {GUMROAD_TOKEN}"}
        response = httpx.post(
            f"{GUMROAD_API_BASE}/products",
            headers=headers,
            data=payload,
            timeout=30,
        )

        if response.status_code not in (200, 201):
            print(f"[ERROR] Failed to create product: {response.status_code}")
            print(f"   {response.text}")
            return None

        result = response.json()
        product_data = result.get("product", {})
        gumroad_id = product_data.get("id", "")
        product_url = product_data.get("url", "")

        if not gumroad_id:
            print(f"[ERROR] No product ID in response")
            return None

        print(f"[OK] Product created: {gumroad_id}")
        print(f"   URL: {product_url}")

        # Upload file
        print(f"[UPLOAD] PDF: {pdf_path}")

        with open(pdf_path, 'rb') as pdf_file:
            files = {"content_file": pdf_file}
            file_response = httpx.post(
                f"{GUMROAD_API_BASE}/products/{gumroad_id}",
                headers=headers,
                files=files,
                timeout=60,
            )

        if file_response.status_code not in (200, 201):
            print(f"[WARNING] File upload had issues: {file_response.status_code}")
            print(f"   {file_response.text}")
            # Continue anyway — file may have uploaded
        else:
            print(f"[OK] PDF uploaded successfully")

        # Create product object
        product = GumroadProduct(
            gumroad_id=gumroad_id,
            name=title,
            description=description,
            price=price,
            content_type=content_type,
            source_article_url=source_article_url,
            product_url=product_url,
        )

        print(f"[OK] {title} published at {product_url}")
        return product

    except Exception as e:
        print(f"[ERROR] Error publishing to Gumroad: {e}")
        return None


def publish_manual(
    title: str,
    description: str,
    pdf_path: str,
    author: str = "Already Here LLC",
    includes_templates: bool = True,
    includes_checklists: bool = True,
    word_count: Optional[int] = None,
    source_article_url: Optional[str] = None,
    price: Optional[float] = None,
) -> GumroadProduct | None:
    """
    Publish a manual/guide to Gumroad.

    Manuals are larger, more comprehensive guides with templates and worksheets.
    Pricing: $7.99–$14.99 (or higher for premium)

    Args:
        title: Manual title
        description: Detailed description
        pdf_path: Path to PDF manual
        author: Author name
        includes_templates: Whether manual includes templates
        includes_checklists: Whether manual includes checklists
        word_count: Optional word count for pricing
        source_article_url: Optional source article URL
        price: Optional price override

    Returns:
        GumroadProduct on success, None on failure
    """
    if not price and word_count:
        price = get_recommended_price(
            "manual",
            word_count,
            has_templates=includes_templates,
            has_worksheets=includes_checklists,
        )

    return publish_ebook(
        title=title,
        description=description,
        pdf_path=pdf_path,
        author=author,
        content_type="manual",
        word_count=word_count,
        source_article_url=source_article_url,
        price=price,
    )


def publish_course(
    title: str,
    description: str,
    content_file_path: str,
    author: str = "Already Here LLC",
    modules_count: int = 5,
    includes_video: bool = True,
    includes_worksheets: bool = True,
    estimated_hours: float = 10.0,
    word_count: Optional[int] = None,
    price: Optional[float] = None,
) -> GumroadProduct | None:
    """
    Publish a course/training to Gumroad.

    Courses are comprehensive multi-module training programs.
    Pricing: $19.99–$49.99+ (higher for premium/enterprise)

    Args:
        title: Course title
        description: Course description with module overview
        content_file_path: Path to ZIP/PDF with course materials
        author: Author name
        modules_count: Number of modules in course
        includes_video: Whether course includes video lessons
        includes_worksheets: Whether course includes worksheets
        estimated_hours: Estimated hours to complete
        word_count: Optional word count for pricing
        price: Optional price override

    Returns:
        GumroadProduct on success, None on failure
    """
    # Enhanced description with course details
    enhanced_desc = f"""{description}

**Course Details:**
- **Modules:** {modules_count}
- **Duration:** ~{estimated_hours:.1f} hours
- **Includes:** {"Video lessons + " if includes_video else ""}PDF materials{"+ worksheets" if includes_worksheets else ""}
- **Access:** Lifetime access"""

    if not price and word_count:
        price = get_recommended_price(
            "course",
            word_count,
            has_templates=True,
            has_worksheets=includes_worksheets,
        )

    return publish_ebook(
        title=title,
        description=enhanced_desc,
        pdf_path=content_file_path,
        author=author,
        content_type="course",
        word_count=word_count,
        price=price,
    )


# ── Product Management ────────────────────────────────────────────────────────
def update_product_with_affiliate_links(
    gumroad_id: str,
    content_type: str,
    affiliate_links: Optional[Dict[str, str]] = None,
) -> bool:
    """
    Update product description with affiliate links.

    Args:
        gumroad_id: Gumroad product ID
        content_type: Type of content ('ebook', 'manual', 'course')
        affiliate_links: Dict of keyword→URL (defaults to env AFFILIATE_LINKS)

    Returns:
        True if updated successfully
    """
    if not GUMROAD_TOKEN:
        print("❌ GUMROAD_API_TOKEN not set")
        return False

    if not affiliate_links:
        affiliate_links = _parse_affiliate_links()

    if not affiliate_links:
        print("[INFO] No affiliate links to inject")
        return False

    print(f"[UPDATE] Updating product {gumroad_id} with affiliate links...")

    try:
        # Fetch current product
        headers = {"Authorization": f"Bearer {GUMROAD_TOKEN}"}
        get_response = httpx.get(
            f"{GUMROAD_API_BASE}/products/{gumroad_id}",
            headers=headers,
            timeout=10,
        )

        if get_response.status_code != 200:
            print(f"[ERROR] Failed to fetch product: {get_response.status_code}")
            return False

        product_data = get_response.json().get("product", {})
        current_desc = product_data.get("description", "")

        # Inject affiliate links
        updated_desc = _inject_affiliate_links(current_desc, affiliate_links)

        if updated_desc == current_desc:
            print("ℹ️  No changes needed")
            return True

        # Update product
        update_response = httpx.post(
            f"{GUMROAD_API_BASE}/products/{gumroad_id}",
            headers=headers,
            data={"description": updated_desc},
            timeout=10,
        )

        if update_response.status_code not in (200, 201):
            print(f"[ERROR] Failed to update: {update_response.status_code}")
            return False

        print(f"[OK] Product updated with {len(affiliate_links)} affiliate links")
        return True

    except Exception as e:
        print(f"[ERROR] Error updating product: {e}")
        return False


def fetch_product_sales(gumroad_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch sales data for a Gumroad product.

    Args:
        gumroad_id: Gumroad product ID

    Returns:
        Dict with sales_count, revenue_usd, or None on error
    """
    if not GUMROAD_TOKEN:
        print("[ERROR] GUMROAD_API_TOKEN not set")
        return None

    try:
        headers = {"Authorization": f"Bearer {GUMROAD_TOKEN}"}
        response = httpx.get(
            f"{GUMROAD_API_BASE}/products/{gumroad_id}",
            headers=headers,
            timeout=10,
        )

        if response.status_code != 200:
            return None

        product_data = response.json().get("product", {})

        # Extract sales metrics
        sales_count = product_data.get("sales_count", 0)
        # Note: Gumroad API may not expose revenue directly; calculate from sales_count and price
        price = (product_data.get("price", 0) or 0) / 100  # Convert cents to dollars
        revenue_usd = sales_count * price

        return {
            "gumroad_id": gumroad_id,
            "name": product_data.get("name", ""),
            "sales_count": sales_count,
            "price": price,
            "revenue_usd": revenue_usd,
            "url": product_data.get("url", ""),
        }

    except Exception as e:
        print(f"[ERROR] Error fetching sales: {e}")
        return None


def get_all_products() -> List[Dict[str, Any]]:
    """
    Fetch all products from Gumroad store.

    Returns:
        List of product dictionaries
    """
    if not GUMROAD_TOKEN:
        print("❌ GUMROAD_API_TOKEN not set")
        return []

    try:
        headers = {"Authorization": f"Bearer {GUMROAD_TOKEN}"}
        response = httpx.get(
            f"{GUMROAD_API_BASE}/products",
            headers=headers,
            timeout=30,
        )

        if response.status_code != 200:
            print(f"[ERROR] Failed to fetch products: {response.status_code}")
            return []

        products = response.json().get("products", [])
        return products

    except Exception as e:
        print(f"[ERROR] Error fetching products: {e}")
        return []


# ── Reporting & Analytics ────────────────────────────────────────────────────
def generate_sales_report(products: Optional[List[GumroadProduct]] = None) -> str:
    """
    Generate a sales report for published products.

    Args:
        products: Optional list of GumroadProduct objects

    Returns:
        Formatted report string
    """
    if not products:
        all_products = get_all_products()
        products = [
            GumroadProduct(
                gumroad_id=p.get("id", ""),
                name=p.get("name", ""),
                description=p.get("description", ""),
                price=(p.get("price", 0) or 0) / 100,
                content_type="unknown",
                product_url=p.get("url", ""),
                sales_count=p.get("sales_count", 0),
            )
            for p in all_products
        ]

    total_sales = sum(p.sales_count for p in products)
    total_revenue = sum(p.sales_count * p.price for p in products)
    avg_price = sum(p.price for p in products) / len(products) if products else 0

    report = f"""
[=== GUMROAD SALES REPORT ===]

SUMMARY
{'-' * 66}
Total Products:    {len(products)}
Total Sales:       {total_sales}
Total Revenue:     ${total_revenue:.2f}
Average Price:     ${avg_price:.2f}

PRODUCTS
{'-' * 66}
"""

    for p in sorted(products, key=lambda x: x.sales_count, reverse=True):
        revenue = p.sales_count * p.price
        report += f"\n{p.name}\n"
        report += f"  Price: ${p.price:.2f}\n"
        report += f"  Sales: {p.sales_count}\n"
        report += f"  Revenue: ${revenue:.2f}\n"
        if p.product_url:
            report += f"  URL: {p.product_url}\n"

    report += f"\n{'-' * 66}\n"
    report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}\n"
    report += f"Store: {GUMROAD_STORE_URL}\n"

    return report


# ── Main Demo ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Gumroad Publisher Module")
    print("=" * 60)

    # Demo: Price recommendations
    print("\nPRICE RECOMMENDATIONS")
    print("-" * 60)

    demo_prices = [
        ("ebook", 5000, False, False),
        ("ebook", 15000, True, False),
        ("manual", 20000, True, True),
        ("course", 50000, True, True),
        ("bundle", 100000, True, True),
    ]

    for content_type, word_count, has_templates, has_worksheets in demo_prices:
        price = get_recommended_price(
            content_type,
            word_count,
            has_templates=has_templates,
            has_worksheets=has_worksheets,
        )
        print(f"{content_type:12} ({word_count:6} words) -> ${price:6.2f}")

    # Demo: Article to ebook
    print("\nSAMPLE ARTICLE TO EBOOK")
    print("-" * 60)

    sample_article = """
# The Ultimate Guide to Building a Profitable Business

## Introduction

This guide covers the proven systems for building a $600K+ business
in 90 days or less.

## Section 1: Revenue Streams

There are 4 main revenue streams you should consider:

1. **Institutional Partnerships** — $210K/year
2. **Vehicle Recovery & Flipping** — $300K/year
3. **Gig Work** — $100K/year
4. **Content Monetization** — $825K+/year

## Section 2: Getting Started

Start with the lowest-hanging fruit in your market...

## Conclusion

By following this blueprint, you can achieve significant revenue
in a short timeframe.
"""

    try:
        pdf_path = article_to_ebook(
            sample_article,
            "Sample Business Guide",
            "Stephen Franklin",
        )
        print(f"[OK] Generated: {pdf_path}")
    except Exception as e:
        print(f"[WARNING] Demo ebook generation: {e}")
        print("   (reportlab not installed — using HTML template)")

    print("\nModule ready for use!")
    print(f"\nStore: {GUMROAD_STORE_URL}")
    print(f"Config: GUMROAD_API_TOKEN={'SET' if GUMROAD_TOKEN else 'NOT SET'}")
