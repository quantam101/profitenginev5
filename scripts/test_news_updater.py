#!/usr/bin/env python3
"""
Unit tests for News Updater

Run: python -m pytest scripts/test_news_updater.py -v
Run with coverage: pytest --cov=scripts.news_updater scripts/test_news_updater.py -v
"""

import unittest
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from news_updater import (
    NewsCategory, NewsItem, NewsAggregator,
    NewsFormatter, NewsPublisher, NewsUpdater
)


class TestNewsItem(unittest.TestCase):
    """Test NewsItem dataclass"""

    def test_create_news_item(self):
        """Test creating a news item"""
        item = NewsItem(
            title="Test News",
            source="Test Source",
            url="https://example.com",
            content="Test content",
            category=NewsCategory.AI_TOOLS,
            published_date="2024-12-19T09:00:00Z"
        )

        self.assertEqual(item.title, "Test News")
        self.assertEqual(item.source, "Test Source")
        self.assertEqual(item.category, NewsCategory.AI_TOOLS)

    def test_news_item_to_dict(self):
        """Test converting news item to dict"""
        item = NewsItem(
            title="Test",
            source="Source",
            url="https://test.com",
            content="Content",
            category=NewsCategory.BUSINESS,
            published_date="2024-12-19T09:00:00Z"
        )

        data = item.to_dict()
        self.assertEqual(data['title'], "Test")
        self.assertEqual(data['category'], "Business")

    def test_news_item_with_affiliate(self):
        """Test news item with affiliate opportunity"""
        item = NewsItem(
            title="ChatGPT News",
            source="TechNews",
            url="https://example.com",
            content="About ChatGPT",
            category=NewsCategory.AI_TOOLS,
            published_date="2024-12-19T09:00:00Z",
            affiliate_opportunity="ChatGPT Plus subscription"
        )

        self.assertIsNotNone(item.affiliate_opportunity)


class TestNewsAggregator(unittest.TestCase):
    """Test NewsAggregator"""

    def setUp(self):
        """Set up test fixtures"""
        self.aggregator = NewsAggregator()

    def test_aggregator_initialization(self):
        """Test aggregator initializes correctly"""
        self.assertIsNotNone(self.aggregator)
        self.assertEqual(self.aggregator.news_items, [])

    def test_categorize_article_ai(self):
        """Test article categorization for AI"""
        article = {
            'title': 'ChatGPT Reaches 100M Users',
            'description': 'Machine learning breakthrough'
        }

        category = self.aggregator._categorize_article(article)
        self.assertEqual(category, NewsCategory.AI_TOOLS)

    def test_categorize_article_passive_income(self):
        """Test article categorization for passive income"""
        article = {
            'title': 'How to Build Passive Income',
            'description': 'Freelance side hustles'
        }

        category = self.aggregator._categorize_article(article)
        self.assertEqual(category, NewsCategory.PASSIVE_INCOME)

    def test_categorize_article_business(self):
        """Test article categorization for business"""
        article = {
            'title': 'Startup Raises $50M Series B',
            'description': 'VC funding news'
        }

        category = self.aggregator._categorize_article(article)
        self.assertEqual(category, NewsCategory.BUSINESS)

    def test_deduplicate_items(self):
        """Test deduplication of news items"""
        items = [
            NewsItem(
                title="News 1",
                source="Source 1",
                url="https://example.com/1",
                content="Content 1",
                category=NewsCategory.AI_TOOLS,
                published_date="2024-12-19T09:00:00Z",
                engagement_score=2.0
            ),
            NewsItem(
                title="News 2",
                source="Source 2",
                url="https://example.com/1",  # Duplicate URL
                content="Content 2",
                category=NewsCategory.BUSINESS,
                published_date="2024-12-19T09:00:00Z",
                engagement_score=1.0
            ),
        ]

        unique = self.aggregator._deduplicate_and_sort(items)
        self.assertEqual(len(unique), 1)
        self.assertEqual(unique[0].title, "News 1")  # Higher score kept

    def test_score_items(self):
        """Test engagement scoring"""
        items = [
            NewsItem(
                title="AI breakthrough news",
                source="Source",
                url="https://example.com/1",
                content="AI related content",
                category=NewsCategory.AI_TOOLS,
                published_date=datetime.now().isoformat()
            ),
        ]

        scored = self.aggregator._score_items(items)
        self.assertGreater(scored[0].engagement_score, 0)

    def test_trending_topics_generation(self):
        """Test synthetic trending topics"""
        items = self.aggregator.fetch_trending_topics()
        self.assertGreater(len(items), 0)
        self.assertTrue(all(isinstance(item, NewsItem) for item in items))


class TestNewsFormatter(unittest.TestCase):
    """Test NewsFormatter"""

    def setUp(self):
        """Set up test fixtures"""
        self.formatter = NewsFormatter()
        self.sample_items = [
            NewsItem(
                title=f"News {i}",
                source=f"Source {i}",
                url=f"https://example.com/{i}",
                content=f"Content about {category.value}",
                category=category,
                published_date="2024-12-19T09:00:00Z"
            )
            for i, category in enumerate(NewsCategory)
        ]

    def test_formatter_initialization(self):
        """Test formatter initializes"""
        self.assertIsNotNone(self.formatter)
        self.assertIsNotNone(self.formatter.affiliate_links)

    def test_format_daily_digest(self):
        """Test formatting daily digest"""
        result = self.formatter.format_daily_digest(self.sample_items, max_items=3)

        self.assertIn('headline', result)
        self.assertIn('items', result)
        self.assertIn('seo_tags', result)
        self.assertEqual(len(result['items']), 3)

    def test_format_industry_updates(self):
        """Test formatting industry updates"""
        result = self.formatter.format_industry_updates(self.sample_items, max_items=5)

        self.assertIn('content', result)
        self.assertIn('seo_tags', result)
        self.assertGreater(len(result['content']), 0)

    def test_format_trending_opportunities(self):
        """Test formatting opportunities"""
        result = self.formatter.format_trending_opportunities(self.sample_items)

        self.assertIn('content', result)
        self.assertIn('seo_tags', result)

    def test_format_full_article(self):
        """Test formatting complete article"""
        result = self.formatter.format_full_article(self.sample_items)

        self.assertIn('title', result)
        self.assertIn('seo_title', result)
        self.assertIn('seo_meta', result)
        self.assertIn('seo_keywords', result)
        self.assertIn('slug', result)
        self.assertIn('content', result)

        # Verify SEO elements
        self.assertGreater(len(result['seo_title']), 0)
        self.assertLess(len(result['seo_meta']), 160)  # Meta description limit
        self.assertGreater(len(result['seo_keywords']), 0)

    def test_generate_category_analysis(self):
        """Test category analysis generation"""
        analysis = self.formatter._generate_category_analysis('AI & Tools', 5)
        self.assertIn('5', analysis)
        self.assertIn('AI', analysis)

    def test_find_affiliate_match(self):
        """Test affiliate link matching"""
        title = "ChatGPT for Content Creators"
        match = self.formatter._find_affiliate_match(title)
        self.assertIsNotNone(match)
        self.assertIn('description', match)

    def test_no_affiliate_match(self):
        """Test when no affiliate match found"""
        title = "Random News About Clouds"
        match = self.formatter._find_affiliate_match(title)
        self.assertIsNone(match)


class TestNewsPublisher(unittest.TestCase):
    """Test NewsPublisher"""

    def setUp(self):
        """Set up test fixtures"""
        self.publisher = NewsPublisher()
        self.sample_article = {
            'title': 'Test Article',
            'content': 'Test content',
            'seo_meta': 'Test meta',
            'seo_keywords': ['test', 'keywords'],
            'slug': 'test-article'
        }

    def test_publisher_initialization(self):
        """Test publisher initializes"""
        self.assertIsNotNone(self.publisher)

    @patch('news_updater.requests.post')
    def test_publish_to_api(self, mock_post):
        """Test API publishing"""
        mock_response = Mock()
        mock_response.json.return_value = {'url': 'https://example.com/article'}
        mock_post.return_value = mock_response

        success, msg = self.publisher.publish_to_api(self.sample_article)
        self.assertTrue(success)
        self.assertIn('https://', msg)

    @patch('news_updater.requests.post')
    def test_publish_to_api_failure(self, mock_post):
        """Test API publishing failure"""
        mock_post.side_effect = Exception("Connection error")

        success, msg = self.publisher.publish_to_api(self.sample_article)
        self.assertFalse(success)


class TestNewsUpdater(unittest.TestCase):
    """Test NewsUpdater orchestration"""

    def setUp(self):
        """Set up test fixtures"""
        self.updater = NewsUpdater()

    def test_updater_initialization(self):
        """Test updater initializes"""
        self.assertIsNotNone(self.updater.aggregator)
        self.assertIsNotNone(self.updater.formatter)
        self.assertIsNotNone(self.updater.publisher)

    @patch('news_updater.NewsAggregator.aggregate')
    def test_preview_update(self, mock_aggregate):
        """Test preview update"""
        mock_items = [
            NewsItem(
                title="Test",
                source="Source",
                url="https://test.com",
                content="Content",
                category=NewsCategory.AI_TOOLS,
                published_date="2024-12-19T09:00:00Z"
            )
        ]
        mock_aggregate.return_value = mock_items

        result = self.updater.preview_update()
        self.assertTrue(result['success'])
        self.assertEqual(result['items_count'], 1)

    @patch('news_updater.NewsAggregator.aggregate')
    def test_save_to_file(self, mock_aggregate):
        """Test saving output to file"""
        mock_items = []
        mock_aggregate.return_value = mock_items

        data = {'test': 'data'}
        filepath = self.updater.save_to_file(data, 'test.json')

        self.assertTrue(Path(filepath).exists())
        with open(filepath) as f:
            saved = json.load(f)
        self.assertEqual(saved['test'], 'data')

        # Cleanup
        Path(filepath).unlink()


class TestIntegration(unittest.TestCase):
    """Integration tests"""

    @patch('news_updater.NewsAggregator.fetch_newsapi')
    @patch('news_updater.NewsAggregator.fetch_rss_feeds')
    @patch('news_updater.NewsAggregator.fetch_trending_topics')
    def test_full_pipeline(self, mock_trending, mock_rss, mock_newsapi):
        """Test complete pipeline"""
        # Mock data
        mock_newsapi.return_value = [
            NewsItem(
                title="AI News",
                source="NewsAPI",
                url="https://newsapi.com/1",
                content="AI content",
                category=NewsCategory.AI_TOOLS,
                published_date="2024-12-19T09:00:00Z"
            )
        ]
        mock_rss.return_value = [
            NewsItem(
                title="Startup News",
                source="TechCrunch",
                url="https://techcrunch.com/1",
                content="Startup content",
                category=NewsCategory.BUSINESS,
                published_date="2024-12-19T09:00:00Z"
            )
        ]
        mock_trending.return_value = [
            NewsItem(
                title="Trend",
                source="Analysis",
                url="",
                content="Trending",
                category=NewsCategory.TRENDS,
                published_date="2024-12-19T09:00:00Z"
            )
        ]

        aggregator = NewsAggregator()
        items = aggregator.aggregate()

        self.assertGreater(len(items), 0)

        formatter = NewsFormatter()
        article = formatter.format_full_article(items)

        self.assertIn('title', article)
        self.assertGreater(len(article['content']), 100)


if __name__ == '__main__':
    unittest.main()
