#!/usr/bin/env python
"""
Sentiment Analysis Engine for 24/7 News Monitoring
Extracts sentiment scores from financial news, aggregates across sources,
weights by reliability, and correlates sentiment with trading outcomes.
Integrates as 5th signal for multi-agent trading decision system.
"""

import asyncio
import sys
import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from decimal import Decimal
from enum import Enum
from dataclasses import dataclass, asdict

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('./logs/sentiment_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SentimentLabel(Enum):
    """Sentiment classification labels."""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


@dataclass
class SentimentScore:
    """Sentiment score for a single article."""
    source: str
    symbol: str
    timestamp: datetime
    label: SentimentLabel
    score: float  # -1.0 (bearish) to +1.0 (bullish)
    confidence: float  # 0.0 to 1.0
    headline: str
    url: str
    article_text: Optional[str] = None


@dataclass
class AggregatedSentiment:
    """Aggregated sentiment across multiple sources."""
    symbol: str
    period: str  # '1h', '24h', '7d'
    aggregate_score: float  # -1.0 to +1.0
    signal_strength: float  # 0.0 to 1.0 (confidence)
    bullish_count: int
    bearish_count: int
    neutral_count: int
    reliability_weights: Dict[str, float]
    timestamp: datetime


@dataclass
class SentimentOutcomeCorrelation:
    """Correlation between sentiment and price movement."""
    symbol: str
    period: str
    sentiment_score: float
    price_change_pct: float
    correlation_coefficient: float
    lag_hours: int  # How many hours after sentiment did price move
    sample_size: int


class SentimentAnalyzer:
    """
    Comprehensive sentiment analysis engine for financial news.
    Extracts, aggregates, weights, and correlates sentiment with trading outcomes.
    """

    def __init__(self):
        """Initialize sentiment analyzer with source reliability weights."""
        self.sentiment_history: List[SentimentScore] = []
        self.aggregated_sentiments: Dict[str, List[AggregatedSentiment]] = {}
        self.correlations: Dict[str, List[SentimentOutcomeCorrelation]] = {}

        # Source reliability weights (0.0 to 1.0)
        # Higher = more reliable source
        self.source_reliability = {
            'reuters': 0.95,
            'bloomberg': 0.94,
            'cnbc': 0.92,
            'wsj': 0.93,
            'ft': 0.91,
            'seekingalpha': 0.75,
            'marketwatch': 0.80,
            'nasdaq': 0.88,
            'sec_filings': 0.99,  # Official documents
            'earnings_call': 0.96,
            'default': 0.70
        }

        # Sentiment keywords for keyword-based extraction (fallback)
        self.bullish_keywords = [
            'surge', 'rally', 'profit', 'beat', 'upgrade', 'outperform',
            'strong', 'gains', 'bull', 'positive', 'growth', 'momentum',
            'breakout', 'bullish', 'upside', 'strength'
        ]

        self.bearish_keywords = [
            'plunge', 'crash', 'loss', 'miss', 'downgrade', 'underperform',
            'weak', 'decline', 'bear', 'negative', 'recession', 'weakness',
            'breakdown', 'bearish', 'downside', 'struggle'
        ]

        logger.info("[INIT] Sentiment Analyzer initialized")

    def extract_sentiment_from_article(
        self,
        headline: str,
        article_text: Optional[str],
        source: str,
        symbol: str,
        url: str
    ) -> SentimentScore:
        """
        Extract sentiment from a financial news article.
        Uses keyword analysis + heuristic scoring.

        Args:
            headline: Article headline
            article_text: Full article text (optional for detailed analysis)
            source: News source name
            symbol: Stock ticker
            url: Article URL

        Returns:
            SentimentScore object with label, score, and confidence
        """
        try:
            # Combine headline and text for analysis
            combined_text = f"{headline} {article_text or ''}".lower()

            # Count keyword occurrences
            bullish_count = sum(combined_text.count(kw) for kw in self.bullish_keywords)
            bearish_count = sum(combined_text.count(kw) for kw in self.bearish_keywords)

            # Calculate sentiment score
            total_signals = bullish_count + bearish_count

            if total_signals == 0:
                # No strong signals detected
                sentiment_label = SentimentLabel.NEUTRAL
                sentiment_score = 0.0
                confidence = 0.3
            else:
                # Net sentiment calculation
                net_sentiment = (bullish_count - bearish_count) / total_signals
                sentiment_score = net_sentiment

                # Determine label
                if sentiment_score > 0.2:
                    sentiment_label = SentimentLabel.BULLISH
                elif sentiment_score < -0.2:
                    sentiment_label = SentimentLabel.BEARISH
                else:
                    sentiment_label = SentimentLabel.NEUTRAL

                # Confidence based on signal strength
                confidence = min(1.0, abs(sentiment_score) * (total_signals / 10))

            score_obj = SentimentScore(
                source=source,
                symbol=symbol,
                timestamp=datetime.now(),
                label=sentiment_label,
                score=sentiment_score,
                confidence=confidence,
                headline=headline,
                url=url,
                article_text=article_text
            )

            self.sentiment_history.append(score_obj)

            logger.info(
                f"[SENTIMENT] {symbol} from {source} | "
                f"{sentiment_label.value} ({sentiment_score:.2f}) | "
                f"Confidence: {confidence:.2f}"
            )

            return score_obj

        except Exception as e:
            logger.error(f"Error extracting sentiment: {e}")
            return SentimentScore(
                source=source,
                symbol=symbol,
                timestamp=datetime.now(),
                label=SentimentLabel.NEUTRAL,
                score=0.0,
                confidence=0.0,
                headline=headline,
                url=url
            )

    def aggregate_source_sentiment(
        self,
        symbol: str,
        hours: int = 24
    ) -> AggregatedSentiment:
        """
        Aggregate sentiment scores across all sources for a symbol.
        Uses time-windowing (e.g., last 24 hours).

        Args:
            symbol: Stock ticker
            hours: Time window in hours (default 24h)

        Returns:
            AggregatedSentiment with weighted scores and statistics
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)

            # Filter relevant sentiments
            relevant = [
                s for s in self.sentiment_history
                if s.symbol == symbol and s.timestamp >= cutoff_time
            ]

            if not relevant:
                logger.warning(f"No sentiment data for {symbol} in last {hours}h")
                return AggregatedSentiment(
                    symbol=symbol,
                    period=f'{hours}h',
                    aggregate_score=0.0,
                    signal_strength=0.0,
                    bullish_count=0,
                    bearish_count=0,
                    neutral_count=0,
                    reliability_weights={},
                    timestamp=datetime.now()
                )

            # Weight by reliability and aggregate
            weighted_scores = []
            bullish_count = sum(1 for s in relevant if s.label == SentimentLabel.BULLISH)
            bearish_count = sum(1 for s in relevant if s.label == SentimentLabel.BEARISH)
            neutral_count = sum(1 for s in relevant if s.label == SentimentLabel.NEUTRAL)

            reliability_weights = {}

            for sentiment in relevant:
                weight = self.weight_by_reliability(
                    sentiment.source,
                    sentiment.confidence
                )
                reliability_weights[sentiment.source] = weight
                weighted_scores.append(sentiment.score * weight)

            # Calculate aggregate
            total_weight = sum(reliability_weights.values())
            if total_weight > 0:
                aggregate_score = sum(weighted_scores) / total_weight
            else:
                aggregate_score = 0.0

            # Signal strength = average confidence * source count factor
            avg_confidence = sum(s.confidence for s in relevant) / len(relevant)
            signal_strength = avg_confidence * min(1.0, len(relevant) / 10)

            aggregated = AggregatedSentiment(
                symbol=symbol,
                period=f'{hours}h',
                aggregate_score=aggregate_score,
                signal_strength=signal_strength,
                bullish_count=bullish_count,
                bearish_count=bearish_count,
                neutral_count=neutral_count,
                reliability_weights=reliability_weights,
                timestamp=datetime.now()
            )

            # Cache aggregated sentiment
            if symbol not in self.aggregated_sentiments:
                self.aggregated_sentiments[symbol] = []
            self.aggregated_sentiments[symbol].append(aggregated)

            logger.info(
                f"[AGGREGATE] {symbol}: {aggregated.aggregate_score:.3f} | "
                f"Strength: {signal_strength:.2f} | "
                f"B:{bullish_count} N:{neutral_count} Bear:{bearish_count}"
            )

            return aggregated

        except Exception as e:
            logger.error(f"Error aggregating sentiment: {e}")
            return AggregatedSentiment(
                symbol=symbol,
                period=f'{hours}h',
                aggregate_score=0.0,
                signal_strength=0.0,
                bullish_count=0,
                bearish_count=0,
                neutral_count=0,
                reliability_weights={},
                timestamp=datetime.now()
            )

    def weight_by_reliability(
        self,
        source: str,
        confidence: float
    ) -> float:
        """
        Weight a sentiment score by source reliability and confidence.
        Combines source track record with article confidence.

        Args:
            source: News source name
            confidence: Individual article confidence (0.0 to 1.0)

        Returns:
            Combined reliability weight (0.0 to 1.0)
        """
        try:
            # Get source reliability (default to 0.70 if unknown)
            source_weight = self.source_reliability.get(
                source.lower(),
                self.source_reliability['default']
            )

            # Combine source reliability with article confidence
            # Formula: source_weight has 70% influence, confidence has 30%
            combined_weight = (source_weight * 0.7) + (confidence * 0.3)

            # Ensure weight is in valid range
            combined_weight = max(0.0, min(1.0, combined_weight))

            return combined_weight

        except Exception as e:
            logger.error(f"Error calculating reliability weight: {e}")
            return 0.5  # Neutral weight on error

    def correlate_with_outcomes(
        self,
        symbol: str,
        price_changes: Dict[str, Tuple[float, int]],  # timestamp: (price_change_pct, lag_hours)
        lookback_days: int = 30
    ) -> List[SentimentOutcomeCorrelation]:
        """
        Calculate correlation between sentiment signals and actual price movements.
        Tracks how well sentiment predicts price outcomes.

        Args:
            symbol: Stock ticker
            price_changes: Dict mapping timestamps to (price_change_pct, lag_hours)
            lookback_days: Historical period to analyze

        Returns:
            List of SentimentOutcomeCorrelation objects showing correlations
        """
        try:
            cutoff_time = datetime.now() - timedelta(days=lookback_days)

            # Get historical sentiments
            relevant_sentiments = [
                s for s in self.sentiment_history
                if s.symbol == symbol and s.timestamp >= cutoff_time
            ]

            if not relevant_sentiments:
                logger.warning(f"No sentiment history for {symbol} in last {lookback_days} days")
                return []

            correlations_list = []

            # Group sentiments by hour and correlate with price movements
            hourly_sentiments = {}
            for sentiment in relevant_sentiments:
                hour_key = sentiment.timestamp.strftime('%Y-%m-%d %H:00:00')
                if hour_key not in hourly_sentiments:
                    hourly_sentiments[hour_key] = []
                hourly_sentiments[hour_key].append(sentiment)

            # Calculate correlation for each hour
            for hour_key, sentiments in hourly_sentiments.items():
                # Get average sentiment for the hour
                avg_score = sum(s.score for s in sentiments) / len(sentiments)
                avg_strength = sum(s.confidence for s in sentiments) / len(sentiments)

                # Check if we have matching price change data
                # (In real usage, this would be populated from market data)
                if hour_key in price_changes:
                    price_change_pct, lag_hours = price_changes[hour_key]

                    # Calculate correlation coefficient (simplified Pearson-like)
                    # In production, would use scipy.stats.pearsonr
                    correlation = self._calculate_simple_correlation(
                        avg_score,
                        price_change_pct
                    )

                    correlation_obj = SentimentOutcomeCorrelation(
                        symbol=symbol,
                        period=hour_key,
                        sentiment_score=avg_score,
                        price_change_pct=price_change_pct,
                        correlation_coefficient=correlation,
                        lag_hours=lag_hours,
                        sample_size=len(sentiments)
                    )

                    correlations_list.append(correlation_obj)

                    logger.info(
                        f"[CORRELATION] {symbol} at {hour_key}: "
                        f"Sentiment={avg_score:.3f}, Price Change={price_change_pct:.2f}%, "
                        f"Correlation={correlation:.3f}, Lag={lag_hours}h"
                    )

            # Cache correlations
            if symbol not in self.correlations:
                self.correlations[symbol] = []
            self.correlations[symbol].extend(correlations_list)

            return correlations_list

        except Exception as e:
            logger.error(f"Error correlating sentiment with outcomes: {e}")
            return []

    @staticmethod
    def _calculate_simple_correlation(sentiment_score: float, price_change: float) -> float:
        """
        Calculate simple correlation between sentiment and price change.
        Returns value between -1.0 and 1.0.

        Args:
            sentiment_score: Sentiment score (-1.0 to 1.0)
            price_change: Price change percentage

        Returns:
            Correlation coefficient
        """
        # Normalize price change to -1.0 to 1.0 range
        # Assuming ±10% is extreme
        normalized_price = max(-1.0, min(1.0, price_change / 10))

        # Simple correlation: multiply and cap
        correlation = (sentiment_score * normalized_price)

        return max(-1.0, min(1.0, correlation))

    def get_agent_signal(self, symbol: str) -> Dict:
        """
        Generate sentiment signal for multi-agent trading decision system.
        Returns standardized 5th agent signal format.

        Args:
            symbol: Stock ticker

        Returns:
            Dict with signal strength, direction, confidence for agent consumption
        """
        try:
            # Get latest aggregated sentiment
            if symbol not in self.aggregated_sentiments:
                # Generate if not cached
                aggregated = self.aggregate_source_sentiment(symbol, hours=24)
            else:
                # Use most recent
                aggregated = self.aggregated_sentiments[symbol][-1]

            # Generate signal
            signal = {
                'agent': 'sentiment',
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'direction': 'bullish' if aggregated.aggregate_score > 0.1 else (
                    'bearish' if aggregated.aggregate_score < -0.1 else 'neutral'
                ),
                'strength': float(aggregated.signal_strength),
                'score': float(aggregated.aggregate_score),
                'confidence': float(aggregated.signal_strength),
                'bullish_articles': aggregated.bullish_count,
                'bearish_articles': aggregated.bearish_count,
                'neutral_articles': aggregated.neutral_count,
                'source_count': len(aggregated.reliability_weights),
                'recommendation': self._generate_recommendation(aggregated)
            }

            logger.info(f"[SIGNAL] Agent signal generated for {symbol}: {signal['direction']}")
            return signal

        except Exception as e:
            logger.error(f"Error generating agent signal: {e}")
            return {
                'agent': 'sentiment',
                'symbol': symbol,
                'direction': 'neutral',
                'strength': 0.0,
                'score': 0.0,
                'confidence': 0.0,
                'error': str(e)
            }

    @staticmethod
    def _generate_recommendation(aggregated: AggregatedSentiment) -> str:
        """Generate recommendation text based on aggregated sentiment."""
        score = aggregated.aggregate_score
        strength = aggregated.signal_strength

        if strength < 0.2:
            return "Insufficient sentiment data for reliable signal"

        if score > 0.5:
            return "Strong bullish sentiment - consider long positions"
        elif score > 0.1:
            return "Moderate bullish sentiment - consider accumulating"
        elif score < -0.5:
            return "Strong bearish sentiment - consider reducing exposure"
        elif score < -0.1:
            return "Moderate bearish sentiment - exercise caution"
        else:
            return "Mixed sentiment - monitor for directional conviction"

    def export_sentiment_report(self, symbol: str) -> str:
        """
        Export comprehensive sentiment analysis report for a symbol.

        Args:
            symbol: Stock ticker

        Returns:
            Formatted report string
        """
        try:
            report = f"\n{'='*80}\n"
            report += f"SENTIMENT ANALYSIS REPORT: {symbol}\n"
            report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            report += f"{'='*80}\n\n"

            # Recent sentiments
            recent = [s for s in self.sentiment_history if s.symbol == symbol][-10:]
            if recent:
                report += f"RECENT ARTICLES ({len(recent)} most recent):\n"
                for s in recent:
                    report += f"  • [{s.label.value.upper()}] {s.headline[:60]}...\n"
                    report += f"    Source: {s.source} | Score: {s.score:.2f} | {s.url}\n"
                report += "\n"

            # Aggregated sentiments
            if symbol in self.aggregated_sentiments:
                agg = self.aggregated_sentiments[symbol][-1]
                report += f"24-HOUR AGGREGATED SENTIMENT:\n"
                report += f"  Aggregate Score: {agg.aggregate_score:.3f}\n"
                report += f"  Signal Strength: {agg.signal_strength:.2f}\n"
                report += f"  Bullish: {agg.bullish_count} | "
                report += f"Neutral: {agg.neutral_count} | "
                report += f"Bearish: {agg.bearish_count}\n"
                report += f"  Sources: {len(agg.reliability_weights)}\n"
                report += "\n"

            # Correlations
            if symbol in self.correlations:
                corr = self.correlations[symbol][-5:]
                if corr:
                    report += f"SENTIMENT-OUTCOME CORRELATION (recent):\n"
                    for c in corr:
                        report += f"  • {c.period}: Sentiment={c.sentiment_score:.2f}, "
                        report += f"Price Change={c.price_change_pct:.2f}%, "
                        report += f"Correlation={c.correlation_coefficient:.3f}\n"

            report += f"{'='*80}\n"
            return report

        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return f"Error generating sentiment report: {e}"


async def demo_sentiment_analysis():
    """Demo: Test sentiment analyzer with sample articles."""
    logger.info("Starting Sentiment Analysis Demo...")

    analyzer = SentimentAnalyzer()

    # Sample articles for testing
    sample_articles = [
        {
            'headline': 'Apple Reports Strong Q2 Earnings Beat, Revenue Surge Expected',
            'text': 'Apple surged higher today as investors rally behind strong guidance',
            'source': 'bloomberg',
            'symbol': 'AAPL',
            'url': 'https://bloomberg.com/apple-q2'
        },
        {
            'headline': 'Tech Sector Faces Headwinds as Interest Rates Rise',
            'text': 'The bearish outlook for technology stocks continues as weak economic data emerges',
            'source': 'reuters',
            'symbol': 'AAPL',
            'url': 'https://reuters.com/tech-rates'
        },
        {
            'headline': 'Microsoft Cloud Division Shows Positive Momentum',
            'text': 'Microsoft bullish commentary on AI growth drives optimism among analysts',
            'source': 'cnbc',
            'symbol': 'MSFT',
            'url': 'https://cnbc.com/msft-cloud'
        },
    ]

    # Extract sentiment from articles
    logger.info("\n1. EXTRACTING SENTIMENT FROM ARTICLES...")
    for article in sample_articles:
        analyzer.extract_sentiment_from_article(
            headline=article['headline'],
            article_text=article['text'],
            source=article['source'],
            symbol=article['symbol'],
            url=article['url']
        )

    # Aggregate sentiments
    logger.info("\n2. AGGREGATING SENTIMENTS...")
    agg_aapl = analyzer.aggregate_source_sentiment('AAPL', hours=24)
    agg_msft = analyzer.aggregate_source_sentiment('MSFT', hours=24)

    # Get agent signals
    logger.info("\n3. GENERATING AGENT SIGNALS...")
    signal_aapl = analyzer.get_agent_signal('AAPL')
    signal_msft = analyzer.get_agent_signal('MSFT')

    logger.info(f"\nAPPL Signal: {json.dumps(signal_aapl, indent=2)}")
    logger.info(f"\nMSFT Signal: {json.dumps(signal_msft, indent=2)}")

    # Generate reports
    logger.info("\n4. GENERATING REPORTS...")
    report_aapl = analyzer.export_sentiment_report('AAPL')
    logger.info(report_aapl)

    logger.info("\n[COMPLETE] Sentiment Analysis Demo Complete")


if __name__ == "__main__":
    asyncio.run(demo_sentiment_analysis())
