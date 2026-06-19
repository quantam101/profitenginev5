"""
Test suite for content_generator.py

Tests all 5 content generation modules:
- Blog post generator
- Tweet generator
- Email generator
- Milestone detector
- Case study builder
"""

import unittest
import tempfile
import json
from pathlib import Path
from datetime import datetime, timedelta
import sys
import os

# Add runtime to path
sys.path.insert(0, os.path.dirname(__file__))

from content_generator import (
    BlogPostGenerator,
    TweetGenerator,
    EmailGenerator,
    MilestoneGenerator,
    CaseStudyGenerator,
    DailyTradeMetrics,
    CustomerPerformance,
)


class TestBlogPostGenerator(unittest.TestCase):
    """Test blog post generation"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.generator = BlogPostGenerator(self.temp_dir)

    def test_generate_blog_post(self):
        """Test blog post generation"""
        metrics = DailyTradeMetrics(
            date="2026-06-18",
            total_traders=25,
            active_traders=22,
            total_trades=487,
            total_pnl=4250.50,
            avg_win_rate=72.5,
            best_trader_username="alice",
            best_trader_pnl=850.00,
            best_trader_win_rate=85.0,
            best_strategy="RSI Divergence",
            top_3_traders=[
                {"rank": 1, "username": "alice", "email": "alice@example.com", "tier": "pro", "pnl": 850.00, "win_rate": 85.0, "trades": 23},
                {"rank": 2, "username": "bob", "email": "bob@example.com", "tier": "basic", "pnl": 625.50, "win_rate": 78.0, "trades": 18},
                {"rank": 3, "username": "carol", "email": "carol@example.com", "tier": "elite", "pnl": 520.00, "win_rate": 82.0, "trades": 21},
            ],
            new_signups=3,
            milestones=[
                {"type": "1k_profit", "username": "alice", "value": 1050.00},
            ],
        )

        markdown = self.generator.generate(metrics)

        # Verify content
        self.assertIn("72.5%", markdown)
        self.assertIn("+$4,250.50", markdown)
        self.assertIn("alice", markdown)
        self.assertIn("RSI Divergence", markdown)
        self.assertIn("Milestones", markdown)

    def test_save_blog_post(self):
        """Test saving blog post"""
        metrics = DailyTradeMetrics(
            date="2026-06-18",
            total_traders=10,
            active_traders=10,
            total_trades=100,
            total_pnl=1000.0,
            avg_win_rate=70.0,
            best_trader_username="test",
            best_trader_pnl=500.0,
            best_trader_win_rate=80.0,
            best_strategy="Test",
            top_3_traders=[],
            new_signups=1,
            milestones=[],
        )

        markdown = self.generator.generate(metrics)
        filepath = self.generator.save(markdown, "2026-06-18")

        self.assertTrue(Path(filepath).exists())
        with open(filepath) as f:
            content = f.read()
            self.assertIn("70.0%", content)


class TestTweetGenerator(unittest.TestCase):
    """Test tweet generation"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.generator = TweetGenerator(self.temp_dir)

    def test_generate_tweets(self):
        """Test tweet generation"""
        metrics = DailyTradeMetrics(
            date="2026-06-18",
            total_traders=20,
            active_traders=20,
            total_trades=200,
            total_pnl=2000.0,
            avg_win_rate=75.0,
            best_trader_username="trader1",
            best_trader_pnl=750.0,
            best_trader_win_rate=88.0,
            best_strategy="Moving Averages",
            top_3_traders=[],
            new_signups=2,
            milestones=[],
        )

        tweets = self.generator.generate(metrics)

        # Should be 5 different tweets
        self.assertEqual(len(tweets), 5)

        # All should be under 280 chars
        for tweet in tweets:
            self.assertLessEqual(len(tweet), 280)
            self.assertGreater(len(tweet), 50)

        # Should contain key metrics
        self.assertTrue(any("75" in t for t in tweets))
        self.assertTrue(any("200" in t for t in tweets))

    def test_tweet_truncation(self):
        """Test tweet truncation"""
        long_tweet = "x" * 300
        truncated = self.generator._truncate_tweet(long_tweet)
        self.assertLessEqual(len(truncated), 280)


class TestEmailGenerator(unittest.TestCase):
    """Test email generation"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.generator = EmailGenerator(self.temp_dir)

    def test_generate_email(self):
        """Test email generation"""
        customer = CustomerPerformance(
            user_id=1,
            email="john@example.com",
            username="john",
            tier="free",
            daily_pnl=250.0,
            daily_win_rate=80.0,
            daily_trades=10,
            balance=5250.0,
            pnl_30d=3500.0,
            win_rate_30d=75.5,
            account_age_days=15,
            is_new=False,
            is_top_performer=True,
        )

        metrics = DailyTradeMetrics(
            date="2026-06-18",
            total_traders=10,
            active_traders=10,
            total_trades=100,
            total_pnl=1000.0,
            avg_win_rate=70.0,
            best_trader_username="test",
            best_trader_pnl=500.0,
            best_trader_win_rate=80.0,
            best_strategy="Test",
            top_3_traders=[],
            new_signups=1,
            milestones=[],
        )

        subject, html, text = self.generator.generate_for_customer(customer, metrics)

        # Verify email components (subject is personalized, so check for key content)
        self.assertTrue(len(subject) > 10)  # Subject exists
        self.assertIn("john", text.lower())
        self.assertIn("250.00", html)
        self.assertIn("80.0", html)  # Win rate

    def test_new_customer_email(self):
        """Test new customer email"""
        customer = CustomerPerformance(
            user_id=2,
            email="newbie@example.com",
            username="newbie",
            tier="free",
            daily_pnl=100.0,
            daily_win_rate=65.0,
            daily_trades=8,
            balance=5100.0,
            pnl_30d=100.0,
            win_rate_30d=65.0,
            account_age_days=1,
            is_new=True,
            is_top_performer=False,
        )

        metrics = DailyTradeMetrics(
            date="2026-06-18",
            total_traders=10,
            active_traders=10,
            total_trades=100,
            total_pnl=1000.0,
            avg_win_rate=70.0,
            best_trader_username="test",
            best_trader_pnl=500.0,
            best_trader_win_rate=80.0,
            best_strategy="Test",
            top_3_traders=[],
            new_signups=1,
            milestones=[],
        )

        subject, html, text = self.generator.generate_for_customer(customer, metrics)

        # New customers should have welcome message
        self.assertIn("Welcome", subject)
        self.assertIn("First Day", subject)


class TestMilestoneGenerator(unittest.TestCase):
    """Test milestone detection and content"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.generator = MilestoneGenerator(self.temp_dir)

    def test_generate_milestone_emails(self):
        """Test milestone email generation"""
        milestones = [
            {"type": "1k_profit", "username": "trader1", "value": 1050.0},
            {"type": "elite_win_rate", "username": "trader2", "value": 92.0},
        ]

        emails = self.generator.generate_milestone_emails(milestones, "2026-06-18")

        self.assertEqual(len(emails), 2)

        # Check 1K profit email
        subject1, html1, text1 = emails[0]
        self.assertIn("Congratulations", subject1)
        self.assertIn("$1,000", html1)

        # Check elite win rate email
        subject2, html2, text2 = emails[1]
        self.assertIn("Elite", subject2)
        self.assertIn("92", html2)


class TestCaseStudyGenerator(unittest.TestCase):
    """Test case study generation"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.generator = CaseStudyGenerator(self.temp_dir)

    def test_generate_case_study(self):
        """Test case study generation"""
        performer = {
            "username": "top_trader",
            "email": "top@example.com",
            "tier": "elite",
            "signup_date": "2026-05-01",
            "lifetime_pnl": 5500.0,
            "avg_win_rate": 85.5,
            "starting_balance": 5000.0,
            "current_balance": 10500.0,
            "trading_days": 30,
            "roi_percent": 110.0,
        }

        html = self.generator.generate(performer)

        # Verify case study content
        self.assertIn("TOP_TRADER", html)
        self.assertIn("5,500", html)  # Formatted with comma
        self.assertIn("85.5", html)
        self.assertIn("110.0", html)  # Formatted with decimal

    def test_save_case_studies(self):
        """Test saving case studies"""
        performers = [
            {
                "username": "trader_a",
                "email": "a@example.com",
                "tier": "elite",
                "signup_date": "2026-05-01",
                "lifetime_pnl": 3000.0,
                "avg_win_rate": 82.0,
                "starting_balance": 5000.0,
                "current_balance": 8000.0,
                "trading_days": 30,
                "roi_percent": 60.0,
            },
        ]

        case_study_dir = self.generator.save_all(performers)

        # Verify directory created
        self.assertTrue(Path(case_study_dir).exists())

        # Verify manifest exists
        manifest_file = Path(case_study_dir) / "manifest.json"
        self.assertTrue(manifest_file.exists())

        with open(manifest_file) as f:
            manifest = json.load(f)
            self.assertEqual(len(manifest), 1)


class TestTweetLength(unittest.TestCase):
    """Test tweet character limits"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.generator = TweetGenerator(self.temp_dir)

    def test_all_tweets_under_limit(self):
        """Verify all tweet variations respect 280 char limit"""
        metrics = DailyTradeMetrics(
            date="2026-06-18",
            total_traders=100,
            active_traders=95,
            total_trades=1500,
            total_pnl=25000.0,
            avg_win_rate=78.5,
            best_trader_username="master_trader",
            best_trader_pnl=5000.0,
            best_trader_win_rate=95.0,
            best_strategy="Advanced Harmonic Patterns",
            top_3_traders=[],
            new_signups=15,
            milestones=[],
        )

        tweets = self.generator.generate(metrics)

        for i, tweet in enumerate(tweets):
            self.assertLessEqual(
                len(tweet),
                280,
                f"Tweet {i+1} exceeds 280 chars: {len(tweet)} chars"
            )


if __name__ == "__main__":
    unittest.main()
