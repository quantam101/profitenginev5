#!/usr/bin/env python
"""
Integration test: Sentiment Analysis with News Monitor 24/7
Demonstrates how SentimentAnalyzer integrates as 5th agent signal
"""

import asyncio
import sys
import os
import json
import logging
from datetime import datetime
from typing import Dict

sys.path.insert(0, '.')

from sentiment_analysis import SentimentAnalyzer, SentimentLabel
from news_monitor_24_7 import NewsMonitor24_7

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


class IntegratedNewsAndSentimentMonitor:
    """Combines news monitoring with sentiment analysis for 5-agent decision system."""

    def __init__(self):
        self.news_monitor = NewsMonitor24_7()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.agent_signals = {}

    async def run_integrated_scan(self):
        """Run integrated news + sentiment scan."""
        logger.info("\n" + "="*80)
        logger.info("INTEGRATED NEWS & SENTIMENT MONITORING CYCLE")
        logger.info("="*80 + "\n")

        # Initialize news monitor
        await self.news_monitor.initialize()

        # Sample news items (in production, from real APIs)
        sample_news = self._generate_sample_news()

        # Process each article: extract sentiment
        logger.info("[1/4] Processing articles through sentiment analyzer...\n")
        for article in sample_news:
            sentiment = self.sentiment_analyzer.extract_sentiment_from_article(
                headline=article['headline'],
                article_text=article.get('text'),
                source=article['source'],
                symbol=article['symbol'],
                url=article['url']
            )
            logger.info(f"  -> {article['symbol']}: {sentiment.label.value}")

        # Aggregate sentiments by symbol
        logger.info("\n[2/4] Aggregating sentiment by symbol...\n")
        symbols = set(a['symbol'] for a in sample_news)
        aggregated_sentiments = {}

        for symbol in symbols:
            agg = self.sentiment_analyzer.aggregate_source_sentiment(symbol, hours=24)
            aggregated_sentiments[symbol] = agg
            logger.info(
                f"  -> {symbol}: Score={agg.aggregate_score:.3f}, "
                f"Strength={agg.signal_strength:.2f}, "
                f"Sources={len(agg.reliability_weights)}"
            )

        # Generate agent signals (5th signal for trading decision system)
        logger.info("\n[3/4] Generating sentiment agent signals...\n")
        self.agent_signals = {}

        for symbol in symbols:
            signal = self.sentiment_analyzer.get_agent_signal(symbol)
            self.agent_signals[symbol] = signal
            logger.info(f"  -> {symbol}: {signal['direction'].upper()}")
            logger.info(f"     Strength: {signal['strength']:.2f}")
            logger.info(f"     Recommendation: {signal['recommendation']}\n")

        # Simulate sentiment-outcome correlation tracking
        logger.info("[4/4] Tracking sentiment-outcome correlations...\n")

        # Sample price movements (in production, from market data)
        sample_price_changes = {
            '2026-06-17 09:00:00': (2.5, 1),
            '2026-06-17 10:00:00': (-1.2, 1),
        }

        for symbol in symbols:
            correlations = self.sentiment_analyzer.correlate_with_outcomes(
                symbol=symbol,
                price_changes=sample_price_changes,
                lookback_days=1
            )
            if correlations:
                logger.info(f"  -> {symbol}: {len(correlations)} correlation(s) recorded")

        # Display final 5-agent signal report
        logger.info("\n" + "="*80)
        logger.info("5-AGENT DECISION SYSTEM: SENTIMENT SIGNAL SUMMARY")
        logger.info("="*80 + "\n")

        for symbol, signal in self.agent_signals.items():
            self._display_agent_signal(symbol, signal)

        return self.agent_signals

    def _generate_sample_news(self) -> list:
        """Generate sample news articles for testing."""
        return [
            {
                'headline': 'Apple Reports Record Q2 Revenue, Beats Expectations',
                'text': 'Apple surged to record revenue in Q2 with strong iPhone sales and bullish '
                        'guidance from management. Analysts rally around positive momentum.',
                'source': 'bloomberg',
                'symbol': 'AAPL',
                'url': 'https://bloomberg.com/apple-q2-2026'
            },
            {
                'headline': 'Tech Sector Faces Recession Headwinds, Analysts Downgrade',
                'text': 'Weak economic data and rising interest rates create bearish outlook for '
                        'technology stocks. Investors reduce exposure amid declining growth forecasts.',
                'source': 'reuters',
                'symbol': 'AAPL',
                'url': 'https://reuters.com/tech-recession-2026'
            },
            {
                'headline': 'Microsoft Cloud Division Achieves 40% Growth, AI Momentum Strong',
                'text': 'Microsoft reports bullish cloud growth with AI services driving positive '
                        'results. Management upbeat on future prospects.',
                'source': 'cnbc',
                'symbol': 'MSFT',
                'url': 'https://cnbc.com/msft-cloud-growth-2026'
            },
            {
                'headline': 'Tesla Production Issues Weigh on Outlook',
                'text': 'Production challenges and reduced demand create negative outlook. Analysts '
                        'express bearish sentiment on near-term performance.',
                'source': 'seekingalpha',
                'symbol': 'TSLA',
                'url': 'https://seekingalpha.com/tesla-production-2026'
            },
            {
                'headline': 'Tesla Announces Major Efficiency Gains',
                'text': 'Management highlights bullish efficiency improvements and cost reductions. '
                        'Positive momentum in manufacturing.',
                'source': 'cnbc',
                'symbol': 'TSLA',
                'url': 'https://cnbc.com/tesla-efficiency-2026'
            }
        ]

    def _display_agent_signal(self, symbol: str, signal: Dict) -> None:
        """Display formatted agent signal."""
        logger.info(f"SYMBOL: {symbol}")
        logger.info(f"  Agent: {signal['agent']}")
        logger.info(f"  Direction: {signal['direction'].upper()}")
        logger.info(f"  Strength: {signal['strength']:.2f}")
        logger.info(f"  Score: {signal['score']:.3f}")
        logger.info(f"  Confidence: {signal['confidence']:.2f}")
        logger.info(f"  Articles - Bullish: {signal['bullish_articles']}, "
                   f"Neutral: {signal['neutral_articles']}, "
                   f"Bearish: {signal['bearish_articles']}")
        logger.info(f"  Sources: {signal['source_count']}")
        logger.info(f"  Recommendation: {signal['recommendation']}")
        logger.info("")


async def main():
    """Run integration test."""
    monitor = IntegratedNewsAndSentimentMonitor()
    await monitor.run_integrated_scan()

    logger.info("\n[SUCCESS] Integration test complete")
    logger.info("Sentiment Analysis is ready to integrate as 5th agent signal")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user")
        sys.exit(0)
