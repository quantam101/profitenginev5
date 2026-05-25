"""
Article topic rotation for ProfitEngine daily content pipeline.

Topics rotate by day-of-year so each day gets a unique, relevant topic.
Add new topics to grow the cycle; duplicates are fine after 90+ days.

Usage (from publish_article.py or GitHub Actions):
    from scripts.article_topics import pick_topic
    topic = pick_topic()   # picks based on today's date
"""
from __future__ import annotations

from datetime import date
from typing import List

# ── 90 topics covering: passive income, AI tools, freelancing,
#    blogging, affiliate marketing, hosting, SaaS, automation ──────────────────
TOPICS: List[str] = [
    # AI tools for income
    "Best Free AI Tools to Build Passive Income Streams in 2026",
    "How to Use ChatGPT to Start a Freelance Writing Business",
    "Top AI Writing Tools That Actually Save Time for Content Creators",
    "How to Make $500/Month with AI-Powered Niche Blogs",
    "AI Tools for Social Media Automation: Grow Accounts on Autopilot",
    "Best AI Image Generators for Print-on-Demand Businesses",
    "How to Use AI to Create and Sell Online Courses in 2026",
    "AI-Powered Keyword Research: Find Low-Competition Niches Fast",
    "Using AI to Write Amazon Listings That Actually Convert",
    "How to Build a Newsletter Business with AI in Under 30 Days",

    # Passive income ideas
    "10 Realistic Passive Income Ideas That Work Without a Large Audience",
    "How to Start a Digital Products Business with No Upfront Investment",
    "Selling Notion Templates: A Complete Guide to Passive Income in 2026",
    "How to Build and Monetize a Micro-SaaS in 90 Days",
    "Passive Income with Stock Photos: Best Platforms and Tips for 2026",
    "How to Earn Royalties from Self-Published Books Using AI Assistance",
    "Building a Faceless YouTube Channel with AI Voiceover Tools",
    "Making Money with Print-on-Demand: A Beginner's Complete Guide",
    "How to Create and Sell SVG Files on Etsy Using Free AI Tools",
    "Passive Income with Domain Flipping: How to Find Valuable Domains",

    # Blogging and SEO
    "How to Start a Profitable Niche Blog in 2026 with AI Content",
    "The Complete Guide to On-Page SEO for AI-Generated Content",
    "How to Build Topical Authority with a Content Cluster Strategy",
    "Best Free SEO Tools for Bloggers That Actually Work in 2026",
    "How to Monetize a Blog with Affiliate Marketing: Step-by-Step",
    "Using Internal Linking to Double Your Blog's Organic Traffic",
    "How Long Should Blog Posts Be for SEO in 2026?",
    "The Fastest Way to Get a New Blog Indexed by Google",
    "Best WordPress Alternatives for AI-Generated Content Sites",
    "How to Write SEO Meta Descriptions That Increase Click-Through Rate",

    # Affiliate marketing
    "Affiliate Marketing for Beginners: Complete Guide for 2026",
    "Best High-Ticket Affiliate Programs for Tech Bloggers",
    "How to Promote DigitalOcean and Earn $25 Per Referral",
    "Amazon Associates vs ShareASale: Which Is Better for Your Niche?",
    "How to Create an Affiliate Review Article That Ranks on Google",
    "Best Recurring Commission Affiliate Programs in the Tech Niche",
    "How to Disclose Affiliate Links Properly (FTC Compliance Guide)",
    "Building an Affiliate Marketing Site with AI: Zero to $500/Month",
    "How to Pick the Right Affiliate Products for Your Audience",
    "Email Marketing for Affiliate Income: Build a List from Scratch",

    # Cloud hosting and tech
    "Best Free Cloud Hosting Platforms for Side Projects in 2026",
    "OCI Always Free: How to Host 5 Side Projects at Zero Cost",
    "DigitalOcean vs Linode vs Vultr: Best VPS for Developers in 2026",
    "How to Deploy a Python App on Oracle Cloud Free Tier",
    "Self-Hosting vs Managed Hosting: When Each Makes Sense",
    "GitHub Pages vs Netlify vs Vercel: Best Free Static Hosting",
    "How to Set Up a Free Postgres Database on Supabase",
    "Best Free APIs for Building Income-Generating Side Projects",
    "How to Build a REST API with FastAPI and Deploy It for Free",
    "Cloudflare Workers: Build and Deploy APIs at No Cost",

    # Freelancing and remote work
    "How to Land Your First Freelance Client on Upwork in 2026",
    "Freelance Rates Guide: What to Charge for AI-Assisted Work",
    "Building a Personal Brand as a Freelance Developer in 2026",
    "How to Use AI to Write Freelance Proposals That Win Projects",
    "Best Platforms for Selling AI Prompts and Automation Scripts",
    "How to Package Your Skills as Digital Products on Gumroad",
    "Freelance SEO Writing: How to Earn $0.10+ Per Word with AI Help",
    "How to Build Recurring Revenue as a Freelancer",
    "Cold Email Templates That Get Responses for Freelancers",
    "Time Management for Freelancers Using AI Productivity Tools",

    # Automation and no-code
    "Best No-Code Tools to Automate Your Side Business in 2026",
    "How to Build a Zapier Automation That Earns You Money",
    "Make.com vs Zapier vs n8n: Best Automation Platform in 2026",
    "Building an Automated Lead Generation System with Free Tools",
    "How to Create a Chatbot That Handles Customer Support Automatically",
    "Automating Social Media Posts with Free AI Tools: Full Guide",
    "How to Build a Price Tracking Bot That Makes You Money",
    "Web Scraping for Profit: Ethical Ways to Monetize Data",
    "Building a Job Board SaaS with No-Code Tools in 2026",
    "How to Automate Invoice Generation and Payments for Freelancers",

    # Finance and mindset
    "How to Reach $1000/Month in Passive Income: A Realistic Timeline",
    "Diversifying Online Income: 5 Streams That Work Together",
    "The $0 Budget Business: Starting a Side Hustle with No Money",
    "How to Track and Optimize Your Passive Income Streams",
    "Tax Tips for Bloggers and Affiliate Marketers in 2026",
    "Building Wealth with Micro-Income Streams: The Compounding Effect",
    "How to Validate a Side Hustle Idea Before Spending Time on It",
    "The 80/20 Rule for Online Business: Focus on What Actually Pays",
    "Building a Second Income While Working a Full-Time Job",
    "How to Quit Your Job with Passive Income: Honest Realistic Plan",

    # Dev tools and SaaS
    "Best AI Coding Assistants for Side Projects and Freelancing",
    "How to Turn a Useful Script into a SaaS Product",
    "Building a Subscription Product with Stripe and Free Hosting",
    "How to Validate a SaaS Idea with Landing Page Tests",
    "Lifetime Deal Sites: Buy Cheap, Resell Access, or Build Features",
    "How to Build a Chrome Extension That People Pay For",
    "API Monetization: Turn Your Project Into a Revenue Stream",
    "Building a Price Comparison Tool and Earning Affiliate Commissions",
    "How to Launch a Product on Product Hunt and Get 500 Users",
    "The Indie Hacker Roadmap: From $0 to $1000 MRR in 2026",
]


def pick_topic(day_offset: int = 0) -> str:
    """
    Pick today's topic based on the day of year.
    day_offset lets you preview tomorrow's (+1) or yesterday's (-1) topic.
    """
    day_of_year = date.today().timetuple().tm_yday + day_offset
    return TOPICS[day_of_year % len(TOPICS)]


if __name__ == "__main__":
    import sys
    offset = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    print(pick_topic(offset))
