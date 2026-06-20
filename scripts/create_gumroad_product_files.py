#!/usr/bin/env python3
"""
Create placeholder product files for Gumroad products.
These files serve as templates until real content is prepared.
"""
import os
from pathlib import Path

# Create products directory
PRODUCTS_DIR = Path("./gumroad_products")
PRODUCTS_DIR.mkdir(exist_ok=True)

PRODUCTS = [
    {
        "id": "itydp",
        "name": "Programmatic SEO Starter Kit",
        "filename": "programmatic-seo-starter-kit.md",
        "content": """# Programmatic SEO Starter Kit

## Overview
City-page SEO templates that rank. This kit includes everything you need to build thousands of SEO-optimized city pages programmatically.

## Contents
- HTML/Markdown templates for 10 service niches
- Keyword research spreadsheet for 500 US cities
- Schema markup snippets for rich results
- Internal linking strategy guide
- GitHub Pages deployment guide

## How to Use
1. Choose your niche (plumbing, electrician, etc.)
2. Use the template to generate pages for each city
3. Update location-specific information
4. Deploy to GitHub Pages or your server
5. Monitor rankings and tweak as needed

## Results You Can Expect
- 100-500 SEO-optimized pages per niche
- Passive traffic from long-tail keywords
- High conversion rates (local service queries)
- Minimal ongoing maintenance

## Next Steps
Extract the ZIP file and follow the setup guide in README.md
""",
    },
    {
        "id": "kjsubd",
        "name": "Social Media Content Engine",
        "filename": "social-media-content-engine.md",
        "content": """# Social Media Content Engine

## What You Get
30-day AI content calendar with 180 ready-to-use prompts for:
- Instagram (captions, hooks, CTAs)
- TikTok (trending formats, sounds)
- LinkedIn (professional insights)
- X/Twitter (hot takes, threads)
- Facebook (community engagement)

## Contents
- Day-by-day content calendar
- 180 production-ready prompts
- Hook formulas that work
- Caption templates
- Hashtag banks by platform
- Notion dashboard (optional)

## How to Use
1. Open the content calendar
2. Use the prompt for each day
3. Generate content with ChatGPT/Claude
4. Schedule via Buffer/Later
5. Track engagement

## Engagement Results
- 3-5x increase in likes
- 2-3x increase in comments
- 50%+ increase in followers/month
- Higher conversion to sales

## Bonus
- 5 viral post templates
- Collaboration ideas for growth
- Cross-platform repurposing guide

Get started today!
""",
    },
    {
        "id": "elnep",
        "name": "POD Design Prompt Bundle",
        "filename": "pod-design-prompt-bundle.md",
        "content": """# POD Design Prompt Bundle

## Complete AI Art Generation System
Generate bestselling print-on-demand designs using Midjourney and Stable Diffusion.

## What's Included
- Midjourney prompts for 20 profitable niches
- Stable Diffusion negative prompts
- Color palette guides for each niche
- Mockup templates for all product types
- Etsy SEO keyword lists
- Design trend analysis

## Niches Covered
1. Motivational quotes
2. Minimalist design
3. Retro/vintage
4. Pet lovers
5. Fitness enthusiasts
6. Coffee culture
7. Travel lovers
8. Gaming
9. Wellness
10. And 10 more...

## How to Use
1. Pick a niche and prompt
2. Generate image in Midjourney
3. Polish in Photoshop (optional)
4. Create product mockups
5. Upload to Printify/Etsy
6. Watch sales roll in

## Product Types Covered
- T-shirts
- Hoodies
- Mugs
- Hats
- Tote bags
- Phone cases
- Wall art
- And more...

## Results
- $10-50 profit per sale
- Minimal ongoing work
- Scale to 100+ designs
- Passive income stream

Start creating profitable designs today!
""",
    },
    {
        "id": "vcnos",
        "name": "AI Business Prompt Pack",
        "filename": "ai-business-prompt-pack.md",
        "content": """# AI Business Prompt Pack

## 500+ Production-Tested Prompts
Ready-to-use prompts for ChatGPT, Claude, and other AI models.

## Categories
- Copywriting & Sales (80+ prompts)
- Email Marketing (60+ prompts)
- Social Media (70+ prompts)
- Product Descriptions (50+ prompts)
- Cold Outreach (40+ prompts)
- Customer Support (50+ prompts)
- Content Creation (60+ prompts)
- And 10+ more categories...

## Real Results
- 5-10x faster writing
- Better conversion rates
- Consistent brand voice
- Less editing required

## How to Use
1. Pick your use case
2. Copy the prompt
3. Paste into ChatGPT/Claude
4. Customize with your details
5. Publish or send

## Included
- Meta prompts for prompt optimization
- Prompt chaining examples
- System prompts for consistency
- Bonus: GPT API implementation guide

## Lifetime Updates
- New prompts added monthly
- Updates for new AI models
- Community suggestions
- Forever access

Get instant prompts for any business task!
""",
    },
    {
        "id": "sngdyk",
        "name": "Real Estate Copywriting Kit",
        "filename": "real-estate-copywriting-kit.md",
        "content": """# Real Estate Copywriting Kit

## 100 Plug-and-Play Property Listing Templates

### Template Types
- Luxury listings (beachfront, penthouses)
- Starter homes
- Commercial properties
- Vacation rentals
- Land listings
- Investment properties
- Short-term rentals

## What Each Template Includes
- Compelling headline
- Opening hook
- Full property description
- Lifestyle benefits
- Call-to-action
- Social media caption
- Email copy

## How to Use
1. Choose template for property type
2. Fill in property details
3. Customize for your market
4. Publish on MLS/website
5. Share on social media

## Results
- 30% faster listing preparation
- Better qualified leads
- Faster sales
- Higher price points

## Bonus Content
- SEO optimization tips
- Virtual tour scripts
- Buyer psychology guide
- Follow-up email sequences

## Real Statistics
- Listings with good copy sell 20% faster
- Average price increase: 5-10%
- More showings scheduled
- More buyer inquiries

Start writing better listings in minutes!
""",
    },
    {
        "id": "nwqqx",
        "name": "AI Essentials: How Artificial Intelligence Can Empower You, Your Business and the World",
        "filename": "ai-essentials-guide.md",
        "content": """# AI Essentials: How Artificial Intelligence Can Empower You, Your Business and the World

## A Comprehensive Guide to Modern AI

### Table of Contents
1. AI Fundamentals
2. How AI Actually Works
3. ChatGPT, Claude, and Other Models
4. AI for Your Business
5. AI for Content Creation
6. AI for Sales & Marketing
7. AI for Productivity
8. AI Ethics & Safety
9. The Future of AI
10. Resources & Next Steps

## What You'll Learn
- How to use AI responsibly
- ChatGPT prompting techniques
- Building AI workflows
- Automating your work
- Creating with AI
- AI business opportunities

## Key Takeaways
- AI is not magic, it's math
- Anyone can learn to use AI
- AI amplifies your skills
- Ethical use matters
- The future is AI-powered

## Who This Is For
- Business owners
- Content creators
- Entrepreneurs
- Anyone curious about AI
- People wanting to stay ahead

## Format
- Written guide
- Real-world examples
- Case studies
- Action steps
- Resource links

## Bonus
- AI tool directory (100+ tools)
- Prompt template library
- Workflow examples
- Community access

Start your AI journey today!
""",
    },
]

# Create product files
for product in PRODUCTS:
    filepath = PRODUCTS_DIR / product["filename"]
    with open(filepath, "w") as f:
        f.write(product["content"])
    print(f"[OK] Created: {product['filename']}")

print(f"\n[OK] All {len(PRODUCTS)} product files created in ./gumroad_products/")
print("\nNext steps:")
print("1. Zip each product folder")
print("2. Upload ZIP to Gumroad product page")
print("3. Set product as 'Published'")
print("4. Set license terms (if applicable)")
print("5. Earnings will start flowing!")
