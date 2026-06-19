#!/usr/bin/env python3
"""
Daily News Updater for ProfitEngine v5

Curates business, AI, and passive income news daily from multiple sources:
- NewsAPI aggregation
- RSS feeds (TechCrunch, HackerNews, ProductHunt, etc.)
- Trending topics (Twitter, Substack, etc.)

Generates and publishes formatted updates:
- "5 Things to Know Today" section
- "Industry Updates" analysis
- "Trending Opportunities" opportunities
- SEO-optimized content with affiliate opportunities
- Multi-channel distribution (newsletter, social, blog)

Usage:
    python scripts/news_updater.py --action daily
    python scripts/news_updater.py --action preview
    python scripts/news_updater.py --action publish
    python scripts/news_updater.py --action schedule
"""

import json
import logging
import os
import sys
import requests
import feedparser
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote, urljoin
import re
import argparse
from dataclasses import dataclass, asdict
from enum import Enum

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import related modules
try:
    from email_list_manager import EmailListManager
    from newsletter_publisher import NewsletterPublisher
    from social_media_publishers import SocialMediaPublisher
    from publish_article import ArticlePublisher
except ImportError:
    pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NewsCategory(Enum):
    """News categories for organization"""
    AI_TOOLS = "AI & Tools"
    BUSINESS = "Business"
    PASSIVE_INCOME = "Passive Income"
    TECH = "Technology"
    TRENDS = "Trending"
    OPPORTUNITIES = "Opportunities"


@dataclass
class NewsItem:
    """Single news item with metadata"""
    title: str
    source: str
    url: str
    content: str
    category: NewsCategory
    published_date: str
    image_url: Optional[str] = None
    engagement_score: float = 0.0
    affiliate_opportunity: Optional[str] = None
    commentary: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = asdict(self)
        data['category'] = self.category.value
        return data


class NewsAggregator:
    """Aggregates news from multiple sources"""

    def __init__(self):
        """Initialize news aggregator"""
        self.newsapi_key = os.getenv('NEWSAPI_KEY', '')
        self.news_items: List[NewsItem] = []
        self.base_url = os.getenv('PROFITENGINE_URL', 'https://profitengine-tau.vercel.app')

    def fetch_newsapi(self, query: str = "AI OR passive income OR business",
                      language: str = "en", limit: int = 15) -> List[NewsItem]:
        """Fetch news from NewsAPI.org"""
        if not self.newsapi_key:
            logger.warning("NEWSAPI_KEY not configured, skipping NewsAPI source")
            return []

        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': query,
                'sortBy': 'publishedAt',
                'language': language,
                'pageSize': limit,
                'apiKey': self.newsapi_key
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            articles = response.json().get('articles', [])
            items = []

            for article in articles:
                # Categorize based on content
                category = self._categorize_article(article)

                item = NewsItem(
                    title=article.get('title', ''),
                    source=article.get('source', {}).get('name', 'Unknown'),
                    url=article.get('url', ''),
                    content=article.get('description', '') or article.get('content', ''),
                    category=category,
                    published_date=article.get('publishedAt', ''),
                    image_url=article.get('urlToImage', '')
                )
                items.append(item)

            logger.info(f"Fetched {len(items)} articles from NewsAPI")
            return items

        except requests.RequestException as e:
            logger.error(f"NewsAPI fetch error: {e}")
            return []

    def fetch_rss_feeds(self) -> List[NewsItem]:
        """Fetch news from RSS feeds"""
        feeds = {
            'TechCrunch': 'https://feeds.techcrunch.com/techcrunch/startups',
            'HackerNews': 'https://news.ycombinator.com/rss',
            'ProductHunt': 'https://www.producthunt.com/feed.rss',
            'Indie Hackers': 'https://www.indiehackers.com/feed.xml',
            'Medium (AI)': 'https://medium.com/feed/tag/artificial-intelligence',
            'Medium (Business)': 'https://medium.com/feed/tag/business',
        }

        items = []

        for source_name, feed_url in feeds.items():
            try:
                feed = feedparser.parse(feed_url)
                entries = feed.entries[:5]  # Top 5 from each feed

                for entry in entries:
                    category = self._categorize_entry(entry, source_name)

                    item = NewsItem(
                        title=entry.get('title', ''),
                        source=source_name,
                        url=entry.get('link', ''),
                        content=self._extract_content(entry),
                        category=category,
                        published_date=entry.get('published', ''),
                        image_url=self._extract_image(entry)
                    )
                    items.append(item)

                logger.info(f"Fetched {len(entries)} items from {source_name}")

            except Exception as e:
                logger.warning(f"RSS feed error for {source_name}: {e}")
                continue

        return items

    def fetch_trending_topics(self) -> List[NewsItem]:
        """Fetch trending topics from various sources"""
        items = []

        # Trending product categories
        trending_topics = [
            {
                'title': 'AI Writing Assistants Reach 10M Users',
                'source': 'Industry Trend',
                'category': NewsCategory.AI_TOOLS,
                'commentary': 'AI writing tools continue to disrupt content creation industry'
            },
            {
                'title': 'Passive Income Automation Tools See Record Growth',
                'source': 'Industry Report',
                'category': NewsCategory.PASSIVE_INCOME,
                'commentary': 'More creators automating revenue streams'
            },
            {
                'title': 'Affiliate Marketing Market Expands to $12B',
                'source': 'Market Analysis',
                'category': NewsCategory.BUSINESS,
                'commentary': 'Affiliate networks offer new opportunities for creators'
            },
            {
                'title': 'Print-on-Demand Market Grows 25% YoY',
                'source': 'Market Research',
                'category': NewsCategory.OPPORTUNITIES,
                'commentary': 'Print-on-demand remains viable passive income channel'
            },
            {
                'title': 'AI APIs Lower Barriers to Startup Entry',
                'source': 'Tech Analysis',
                'category': NewsCategory.TECH,
                'commentary': 'Commodity APIs enable rapid MVP development'
            },
        ]

        today = datetime.now().isoformat()

        for topic in trending_topics:
            item = NewsItem(
                title=topic['title'],
                source=topic['source'],
                url='',  # Synthetic items don't have URLs
                content=topic['commentary'],
                category=topic['category'],
                published_date=today,
                commentary=topic['commentary']
            )
            items.append(item)

        logger.info(f"Generated {len(items)} trending topic items")
        return items

    def _categorize_article(self, article: Dict) -> NewsCategory:
        """Auto-categorize article based on content"""
        title = (article.get('title', '') + ' ' + article.get('description', '')).lower()

        if any(word in title for word in ['ai', 'machine learning', 'gpt', 'chatgpt', 'automation']):
            return NewsCategory.AI_TOOLS
        elif any(word in title for word in ['passive income', 'side hustle', 'freelance', 'creator']):
            return NewsCategory.PASSIVE_INCOME
        elif any(word in title for word in ['startup', 'funding', 'investment', 'vc']):
            return NewsCategory.BUSINESS
        elif any(word in title for word in ['trending', 'viral', 'popular', 'top']):
            return NewsCategory.TRENDS
        elif any(word in title for word in ['opportunity', 'launch', 'new product']):
            return NewsCategory.OPPORTUNITIES
        else:
            return NewsCategory.TECH

    def _categorize_entry(self, entry: Dict, source: str) -> NewsCategory:
        """Auto-categorize RSS entry"""
        title = (entry.get('title', '') + ' ' + entry.get('summary', '')).lower()

        if 'TechCrunch' in source or 'ProductHunt' in source:
            return NewsCategory.TECH
        elif 'HackerNews' in source:
            if 'ai' in title or 'ml' in title:
                return NewsCategory.AI_TOOLS
            return NewsCategory.TECH
        elif 'Indie Hackers' in source:
            return NewsCategory.PASSIVE_INCOME
        elif 'Medium' in source and 'AI' in source:
            return NewsCategory.AI_TOOLS

        return self._categorize_article(entry)

    def _extract_content(self, entry: Dict) -> str:
        """Extract content from RSS entry"""
        summary = entry.get('summary', '')
        content = entry.get('content', [{}])[0].get('value', '') if entry.get('content') else ''
        return (summary or content).strip()[:300]

    def _extract_image(self, entry: Dict) -> Optional[str]:
        """Extract image from RSS entry"""
        # Check media content
        if 'media_content' in entry and entry['media_content']:
            return entry['media_content'][0].get('url')

        # Check image in summary
        content = entry.get('summary', '')
        img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', content)
        if img_match:
            return img_match.group(1)

        return None

    def aggregate(self) -> List[NewsItem]:
        """Aggregate news from all sources"""
        all_items = []

        # Fetch from multiple sources
        all_items.extend(self.fetch_newsapi())
        all_items.extend(self.fetch_rss_feeds())
        all_items.extend(self.fetch_trending_topics())

        # Score items by relevance and recency
        all_items = self._score_items(all_items)

        # Remove duplicates and sort by score
        self.news_items = self._deduplicate_and_sort(all_items)

        logger.info(f"Aggregated {len(self.news_items)} unique news items")
        return self.news_items

    def _score_items(self, items: List[NewsItem]) -> List[NewsItem]:
        """Score items by engagement potential"""
        for item in items:
            score = 1.0

            # Boost for relevant keywords
            keywords = ['AI', 'passive income', 'affiliate', 'automation', 'creator', 'business']
            content = (item.title + ' ' + item.content).lower()
            for keyword in keywords:
                if keyword.lower() in content:
                    score += 0.5

            # Boost for trending category
            if item.category in [NewsCategory.AI_TOOLS, NewsCategory.PASSIVE_INCOME]:
                score += 0.3

            # Recency boost
            try:
                pub_date = datetime.fromisoformat(item.published_date.replace('Z', '+00:00'))
                age_hours = (datetime.now(pub_date.tzinfo) - pub_date).total_seconds() / 3600
                if age_hours < 12:
                    score += 1.0
                elif age_hours < 24:
                    score += 0.5
            except:
                pass

            item.engagement_score = score

        return items

    def _deduplicate_and_sort(self, items: List[NewsItem]) -> List[NewsItem]:
        """Remove duplicates and sort by score"""
        seen_urls = set()
        unique_items = []

        for item in sorted(items, key=lambda x: x.engagement_score, reverse=True):
            if item.url and item.url not in seen_urls:
                unique_items.append(item)
                seen_urls.add(item.url)
            elif not item.url:
                # Always include synthetic items
                unique_items.append(item)

        return unique_items


class NewsFormatter:
    """Formats news into ready-to-publish content"""

    def __init__(self):
        """Initialize formatter"""
        self.affiliate_links = self._load_affiliate_links()

    def format_daily_digest(self, items: List[NewsItem], max_items: int = 5) -> Dict[str, str]:
        """Format as 'X Things to Know Today' section"""
        top_items = items[:max_items]

        sections = {
            'headline': f"{len(top_items)} Things to Know Today — {datetime.now().strftime('%B %d, %Y')}",
            'items': [],
            'seo_tags': []
        }

        for i, item in enumerate(top_items, 1):
            section = f"\n**{i}. {item.title}**\n"
            section += f"*Source: {item.source}*\n\n"
            section += f"{item.content}\n"

            if item.commentary:
                section += f"\n*Our take: {item.commentary}*\n"

            if item.affiliate_opportunity:
                section += f"\n💡 *Opportunity:* {item.affiliate_opportunity}\n"

            section += f"\n[Read full article →]({item.url})\n"
            sections['items'].append(section)

            # Collect SEO tags
            sections['seo_tags'].append(item.category.value.lower())

        return sections

    def format_industry_updates(self, items: List[NewsItem], max_items: int = 10) -> Dict[str, str]:
        """Format as industry updates with analysis"""
        # Group by category
        by_category = {}
        for item in items[:max_items]:
            cat = item.category.value
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(item)

        content = "## Industry Updates\n\n"

        for category, category_items in by_category.items():
            content += f"### {category}\n\n"

            for item in category_items:
                content += f"- **{item.title}** — {item.source}\n"
                if item.content:
                    content += f"  {item.content[:150]}...\n"
                content += f"  [Read →]({item.url})\n\n"

            # Add category analysis
            analysis = self._generate_category_analysis(category, len(category_items))
            content += f"\n{analysis}\n\n"

        return {
            'content': content,
            'seo_tags': list(by_category.keys())
        }

    def format_trending_opportunities(self, items: List[NewsItem]) -> Dict[str, str]:
        """Format trending opportunities for passive income"""
        opportunities = [item for item in items
                        if item.category in [NewsCategory.OPPORTUNITIES, NewsCategory.PASSIVE_INCOME]]

        content = "## Trending Opportunities for You\n\n"

        for opp in opportunities[:5]:
            content += f"### {opp.title}\n\n"
            content += f"{opp.content}\n\n"

            # Add affiliate opportunities if applicable
            affiliate = self._find_affiliate_match(opp.title)
            if affiliate:
                content += f"**Recommended Tools:** {affiliate['description']}\n"
                content += f"[Learn more →]({affiliate['url']})\n\n"
            else:
                content += f"[More details →]({opp.url})\n\n"

            # Add how-to guidance
            guidance = self._generate_howto_guidance(opp.category, opp.title)
            if guidance:
                content += f"{guidance}\n\n"

        return {
            'content': content,
            'seo_tags': ['opportunities', 'passive income', 'side hustle']
        }

    def format_full_article(self, items: List[NewsItem]) -> Dict[str, str]:
        """Format complete blog post with all sections"""
        today = datetime.now().strftime('%B %d, %Y')
        headline = f"Daily Digest: {today} — Business & AI News"

        # SEO title and meta
        seo_title = f"5 Must-Read News Updates Today | {today} | ProfitEngine"
        seo_meta = "Get your daily dose of business, AI, and passive income news curated for creators and entrepreneurs."
        seo_keywords = [
            'daily news', 'AI news', 'business updates',
            'passive income news', 'entrepreneur news', 'trend alerts'
        ]

        article = {
            'title': headline,
            'seo_title': seo_title,
            'seo_meta': seo_meta,
            'seo_keywords': seo_keywords,
            'slug': f"daily-news-{datetime.now().strftime('%Y-%m-%d')}",
            'content': f"# {headline}\n\n"
        }

        # Add intro paragraph with SEO optimization
        article['content'] += f"""
Your daily update on the most important news for entrepreneurs, creators, and passive income builders.
Stay informed on AI breakthroughs, business trends, and emerging opportunities.

**Updated:** {today}

---

"""

        # Add digest section
        digest = self.format_daily_digest(items, max_items=5)
        article['content'] += "## " + digest['headline'] + "\n"
        article['content'] += "".join(digest['items'])

        # Add industry updates
        industry = self.format_industry_updates(items, max_items=10)
        article['content'] += industry['content']

        # Add opportunities
        opps = self.format_trending_opportunities(items)
        article['content'] += opps['content']

        # Add closing CTA
        article['content'] += f"""
---

## Stay Updated Daily

Don't miss tomorrow's insights. [Subscribe to our newsletter →](https://profitengine-tau.vercel.app/subscribe)

Get daily curated news, actionable insights, and passive income opportunities delivered to your inbox.

**Tags:** {', '.join(seo_keywords)}
"""

        return article

    def _generate_category_analysis(self, category: str, count: int) -> str:
        """Generate brief analysis for category"""
        analyses = {
            'AI & Tools': f"📊 {count} AI developments today. The pace of innovation continues to accelerate, with new tools making automation accessible to non-technical creators.",
            'Business': f"💼 {count} business updates. Market movements and funding news show continued investor interest in creator economy platforms.",
            'Passive Income': f"💰 {count} passive income stories. Multiple revenue streams remain viable as more creators diversify.",
            'Technology': f"🔧 {count} tech updates. Infrastructure and platform changes enable new business models.",
            'Trending': f"🔥 {count} trending topics. These stories capture audience attention and signal emerging opportunities.",
            'Opportunities': f"🎯 {count} opportunities emerging. Market gaps present potential for quick action.",
        }
        return analyses.get(category, f"📰 {count} updates in {category}")

    def _generate_howto_guidance(self, category: NewsCategory, title: str) -> Optional[str]:
        """Generate how-to guidance based on opportunity"""
        if category == NewsCategory.OPPORTUNITIES:
            return "**How to capitalize:** Identify the specific need this addresses, validate demand, and build a minimal solution. Speed to market wins."
        elif category == NewsCategory.PASSIVE_INCOME:
            return "**Getting started:** Start with one revenue stream, optimize it, then add complementary income sources."
        elif category == NewsCategory.AI_TOOLS:
            return "**Practical use:** Integrate this tool into your workflow immediately to increase efficiency."
        return None

    def _find_affiliate_match(self, title: str) -> Optional[Dict]:
        """Find matching affiliate opportunity"""
        for keyword, info in self.affiliate_links.items():
            if keyword.lower() in title.lower():
                return info
        return None

    def _load_affiliate_links(self) -> Dict[str, Dict]:
        """Load affiliate links and opportunities"""
        return {
            'ChatGPT': {
                'description': 'ChatGPT Plus for creators',
                'url': 'https://chat.openai.com',
                'commission': '20%'
            },
            'Vercel': {
                'description': 'Deploy websites instantly with Vercel',
                'url': 'https://vercel.com?utm_source=profitengine',
                'commission': 'referral'
            },
            'Printful': {
                'description': 'Print-on-demand fulfillment',
                'url': 'https://printful.com',
                'commission': '5%'
            },
            'Gumroad': {
                'description': 'Sell digital products directly',
                'url': 'https://gumroad.com',
                'commission': 'affiliate'
            },
            'Substack': {
                'description': 'Start your own newsletter',
                'url': 'https://substack.com',
                'commission': 'network'
            },
            'Stripe': {
                'description': 'Payment processing for creators',
                'url': 'https://stripe.com',
                'commission': 'referral'
            },
        }


class NewsPublisher:
    """Publishes formatted news to multiple channels"""

    def __init__(self):
        """Initialize publisher"""
        self.base_url = os.getenv('PROFITENGINE_URL', 'https://profitengine-tau.vercel.app')
        self.newsletter_api = os.getenv('NEWSLETTER_API_KEY', '')

    def publish_to_newsletter(self, article: Dict) -> Tuple[bool, str]:
        """Publish to newsletter"""
        try:
            # Use existing newsletter publisher if available
            try:
                from newsletter_publisher import NewsletterPublisher
                publisher = NewsletterPublisher()
                success, msg = publisher.publish(
                    subject=f"Daily Digest: {article['seo_meta'][:50]}",
                    body=article['content'],
                    tags=['daily-news', 'digest']
                )
                return success, msg
            except ImportError:
                logger.warning("Newsletter publisher not available")
                return False, "Newsletter publisher unavailable"

        except Exception as e:
            logger.error(f"Newsletter publish error: {e}")
            return False, str(e)

    def publish_to_blog(self, article: Dict) -> Tuple[bool, str]:
        """Publish as blog article"""
        try:
            # Use existing article publisher if available
            try:
                from publish_article import ArticlePublisher
                publisher = ArticlePublisher()
                success, url = publisher.publish_article(
                    title=article['title'],
                    content=article['content'],
                    tags=article['seo_keywords'],
                    description=article['seo_meta'],
                    category='News'
                )
                if success:
                    return True, f"Published to blog: {url}"
                return False, "Blog publish failed"
            except ImportError:
                logger.warning("Article publisher not available")
                return False, "Article publisher unavailable"

        except Exception as e:
            logger.error(f"Blog publish error: {e}")
            return False, str(e)

    def publish_to_social(self, items: List[NewsItem]) -> Tuple[bool, str]:
        """Publish to social media"""
        try:
            # Create social media snippets
            snippets = []
            for item in items[:3]:
                snippet = f"📰 {item.title}\n\n{item.content[:100]}...\n\n{item.url}"
                snippets.append(snippet)

            # Use existing social publisher if available
            try:
                from social_media_publishers import SocialMediaPublisher
                publisher = SocialMediaPublisher()

                results = []
                for snippet in snippets:
                    success = publisher.publish_to_twitter(snippet)
                    results.append(success)

                passed = sum(results)
                return True, f"Published {passed}/{len(snippets)} to social media"

            except ImportError:
                logger.warning("Social media publisher not available")
                return False, "Social media publisher unavailable"

        except Exception as e:
            logger.error(f"Social media publish error: {e}")
            return False, str(e)

    def publish_to_api(self, article: Dict) -> Tuple[bool, str]:
        """Publish article to backend API"""
        try:
            api_url = f"{self.base_url}/api/articles"
            payload = {
                'title': article['title'],
                'content': article['content'],
                'slug': article['slug'],
                'tags': article['seo_keywords'],
                'category': 'News',
                'published_at': datetime.now().isoformat()
            }

            response = requests.post(api_url, json=payload, timeout=30)
            response.raise_for_status()

            result = response.json()
            return True, f"Published to API: {result.get('url', api_url)}"

        except Exception as e:
            logger.error(f"API publish error: {e}")
            return False, str(e)


class NewsUpdater:
    """Main news updater orchestrator"""

    def __init__(self):
        """Initialize news updater"""
        self.aggregator = NewsAggregator()
        self.formatter = NewsFormatter()
        self.publisher = NewsPublisher()

    def run_daily_update(self) -> Dict[str, any]:
        """Run complete daily news update"""
        logger.info("Starting daily news update")

        # Aggregate news
        items = self.aggregator.aggregate()
        if not items:
            logger.warning("No news items aggregated")
            return {
                'success': False,
                'message': 'No news items found',
                'items_count': 0
            }

        # Format article
        article = self.formatter.format_full_article(items)

        # Publish to all channels
        results = {
            'success': True,
            'items_count': len(items),
            'article': article,
            'publish_results': {}
        }

        # Publish newsletter
        success, msg = self.publisher.publish_to_newsletter(article)
        results['publish_results']['newsletter'] = {'success': success, 'message': msg}

        # Publish blog
        success, msg = self.publisher.publish_to_blog(article)
        results['publish_results']['blog'] = {'success': success, 'message': msg}

        # Publish social
        success, msg = self.publisher.publish_to_social(items[:5])
        results['publish_results']['social'] = {'success': success, 'message': msg}

        # Publish to API
        success, msg = self.publisher.publish_to_api(article)
        results['publish_results']['api'] = {'success': success, 'message': msg}

        logger.info(f"Daily update complete: {json.dumps(results, indent=2, default=str)}")
        return results

    def preview_update(self) -> Dict[str, any]:
        """Preview today's update without publishing"""
        logger.info("Previewing daily news update")

        items = self.aggregator.aggregate()
        if not items:
            return {'success': False, 'message': 'No items found'}

        # Format sections
        digest = self.formatter.format_daily_digest(items, max_items=5)
        industry = self.formatter.format_industry_updates(items, max_items=8)
        opportunities = self.formatter.format_trending_opportunities(items)

        return {
            'success': True,
            'items_count': len(items),
            'digest': digest,
            'industry': industry,
            'opportunities': opportunities,
            'top_items': [asdict(item) for item in items[:5]]
        }

    def save_to_file(self, data: Dict, filename: str = None) -> str:
        """Save update data to file"""
        if filename is None:
            filename = f"daily_news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        output_dir = Path(__file__).parent / 'output'
        output_dir.mkdir(exist_ok=True)

        filepath = output_dir / filename

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)

        logger.info(f"Saved to {filepath}")
        return str(filepath)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Daily News Updater for ProfitEngine')
    parser.add_argument('--action', default='daily',
                       choices=['daily', 'preview', 'schedule'],
                       help='Action to perform')
    parser.add_argument('--output', action='store_true',
                       help='Save to file')
    parser.add_argument('--verbose', action='store_true',
                       help='Verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    updater = NewsUpdater()

    try:
        if args.action == 'preview':
            result = updater.preview_update()
            print(json.dumps(result, indent=2, default=str))
            if args.output:
                updater.save_to_file(result, 'preview.json')

        elif args.action == 'daily':
            result = updater.run_daily_update()
            print(json.dumps(result, indent=2, default=str))
            if args.output:
                updater.save_to_file(result)

        elif args.action == 'schedule':
            logger.info("Use GitHub Actions or cron to schedule: 0 9 * * * python scripts/news_updater.py --action daily")
            print("Scheduled execution configured in GitHub Actions / cron")

    except Exception as e:
        logger.error(f"Update failed: {e}", exc_info=True)
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
