"""Sentiment Analysis Agent

Extracts and aggregates sentiment data from multiple news sources.
Applies reliability weights to normalize sentiment scores across sources
with different historical accuracy and credibility profiles.

Sources & Reliability Weights:
  - Bloomberg (1.0): Financial news, high institutional credibility
  - Reuters (0.9): International news, rigorous editorial standards
  - MarketWatch (0.8): Financial analysis, moderately established
  - CNBC (0.7): Cable news, real-time reporting with editorial variance
  - Seeking Alpha (0.6): User-generated financial content, variable quality

Methods:
- extract(): Fetch and extract sentiment from individual news sources
- aggregate(): Combine multiple sentiment signals into unified score
- weight(): Apply reliability-based weighting to normalize scores

Sentiment Calculation:
  weighted_score = Σ(source_sentiment × reliability_weight) / Σ(reliability_weights)
  confidence = min(data_points, max_sources) / max_sources
"""

from __future__ import annotations

import logging
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("AgentSentiment")


class SentimentLevel(Enum):
    """Sentiment classification levels."""
    EXTREMELY_NEGATIVE = "extremely_negative"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"
    EXTREMELY_POSITIVE = "extremely_positive"


class NewsSource(Enum):
    """Recognized news sources with reliability weights."""
    BLOOMBERG = ("bloomberg", 1.0)
    REUTERS = ("reuters", 0.9)
    MARKETWATCH = ("marketwatch", 0.8)
    CNBC = ("cnbc", 0.7)
    SEEKING_ALPHA = ("seeking_alpha", 0.6)

    @property
    def source_name(self) -> str:
        """Get source name."""
        return self.value[0]

    @property
    def weight(self) -> float:
        """Get reliability weight (0.6 to 1.0)."""
        return self.value[1]


@dataclass
class SentimentScore:
    """Individual sentiment measurement from a single source."""
    source: str
    raw_score: float  # -1.0 to 1.0
    reliability_weight: float  # 0.6 to 1.0
    weighted_score: float = 0.0
    headline: str = ""
    article_count: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    details: Dict[str, Any] = field(default_factory=dict)

    def calculate_weighted(self) -> None:
        """Calculate weighted sentiment score."""
        self.weighted_score = self.raw_score * self.reliability_weight

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        return data


@dataclass
class AggregatedSentiment:
    """Combined sentiment analysis from multiple sources."""
    signal_id: str
    aggregate_score: float = 0.0  # -1.0 to 1.0
    aggregate_level: SentimentLevel = SentimentLevel.NEUTRAL
    confidence_score: float = 0.0  # 0.0 to 1.0 (data quality indicator)
    num_sources: int = 0
    total_articles: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source_breakdown: Dict[str, float] = field(default_factory=dict)
    source_weights: Dict[str, float] = field(default_factory=dict)
    trend_direction: str = ""  # "bullish", "bearish", "mixed", "flat"
    volatility_score: float = 0.0  # measure of sentiment variance across sources
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["aggregate_level"] = self.aggregate_level.value
        return data


class AgentSentiment:
    """Multi-source sentiment extraction and aggregation engine."""

    def __init__(
        self,
        max_sources: int = 5,
        min_confidence_threshold: float = 0.4,
        sentiment_history_limit: int = 100,
    ):
        """Initialize sentiment analysis agent.

        Args:
            max_sources: Maximum number of sources to aggregate (default 5)
            min_confidence_threshold: Minimum confidence to trust aggregated score
            sentiment_history_limit: Max historical scores to retain
        """
        self.max_sources = max_sources
        self.min_confidence_threshold = min_confidence_threshold
        self.sentiment_history_limit = sentiment_history_limit
        self.logger = logging.getLogger("AgentSentiment")
        self.sentiment_history: List[AggregatedSentiment] = []
        self.source_cache: Dict[str, SentimentScore] = {}

    def extract(
        self,
        source: NewsSource,
        raw_score: float,
        headline: str = "",
        article_count: int = 1,
        details: Optional[Dict[str, Any]] = None,
    ) -> SentimentScore:
        """Extract and normalize sentiment from a single news source.

        Args:
            source: NewsSource enum value
            raw_score: Raw sentiment score from -1.0 to 1.0
            headline: Sample headline or summary
            article_count: Number of articles analyzed for this source
            details: Additional metadata dictionary

        Returns:
            SentimentScore object with normalized values
        """
        # Validate and clamp raw score
        clamped_score = max(-1.0, min(1.0, raw_score))

        # Create sentiment score object
        sentiment = SentimentScore(
            source=source.source_name,
            raw_score=clamped_score,
            reliability_weight=source.weight,
            headline=headline,
            article_count=article_count,
            details=details or {},
        )

        # Calculate weighted score
        sentiment.calculate_weighted()

        # Cache the result
        cache_key = source.source_name
        self.source_cache[cache_key] = sentiment

        self.logger.info(
            f"Extracted sentiment from {source.source_name}: "
            f"raw={clamped_score:.3f}, weighted={sentiment.weighted_score:.3f}"
        )

        return sentiment

    def weight(
        self,
        sentiment_scores: List[SentimentScore],
    ) -> Tuple[float, float]:
        """Apply reliability-based weighting and normalize aggregate score.

        Calculates weighted average using reliability weights:
        weighted_score = Σ(sentiment × weight) / Σ(weights)

        Args:
            sentiment_scores: List of SentimentScore objects from extract()

        Returns:
            Tuple of (weighted_aggregate_score, weight_sum) for verification
        """
        if not sentiment_scores:
            self.logger.warning("No sentiment scores provided for weighting")
            return 0.0, 0.0

        total_weighted_score = 0.0
        total_weight = 0.0

        for score in sentiment_scores:
            total_weighted_score += score.weighted_score
            total_weight += score.reliability_weight

        if total_weight == 0:
            self.logger.warning("Total weight is zero, cannot calculate weighted average")
            return 0.0, 0.0

        # Normalize to -1.0 to 1.0 range
        weighted_average = total_weighted_score / total_weight

        self.logger.info(
            f"Weighting complete: aggregate={weighted_average:.3f}, "
            f"total_weight={total_weight:.2f}"
        )

        return weighted_average, total_weight

    def aggregate(
        self,
        sentiment_scores: List[SentimentScore],
        signal_id: Optional[str] = None,
    ) -> AggregatedSentiment:
        """Aggregate sentiment scores from multiple sources into unified analysis.

        Combines weighted scores, calculates confidence, detects trends,
        and measures variance across sources.

        Args:
            sentiment_scores: List of SentimentScore objects from extract()
            signal_id: Optional identifier for this aggregation batch

        Returns:
            AggregatedSentiment with comprehensive multi-source analysis
        """
        if not sentiment_scores:
            self.logger.warning("No sentiment scores to aggregate")
            return AggregatedSentiment(
                signal_id=signal_id or self._generate_signal_id(),
            )

        # Limit to max sources
        limited_scores = sentiment_scores[:self.max_sources]

        # Calculate weighted aggregate
        weighted_score, total_weight = self.weight(limited_scores)

        # Calculate confidence (based on number of sources and weight consistency)
        num_sources = len(limited_scores)
        source_weight_variance = self._calculate_weight_variance(limited_scores)
        confidence = self._calculate_confidence(
            num_sources, source_weight_variance
        )

        # Classify sentiment level
        sentiment_level = self._classify_sentiment(weighted_score)

        # Determine trend direction
        trend_direction = self._determine_trend(limited_scores)

        # Calculate volatility (variance across sources)
        volatility = self._calculate_volatility(limited_scores)

        # Build source breakdown
        source_breakdown = {
            score.source: score.weighted_score for score in limited_scores
        }
        source_weights = {score.source: score.reliability_weight for score in limited_scores}

        # Calculate total articles
        total_articles = sum(score.article_count for score in limited_scores)

        # Create aggregated sentiment
        aggregated = AggregatedSentiment(
            signal_id=signal_id or self._generate_signal_id(),
            aggregate_score=weighted_score,
            aggregate_level=sentiment_level,
            confidence_score=confidence,
            num_sources=num_sources,
            total_articles=total_articles,
            source_breakdown=source_breakdown,
            source_weights=source_weights,
            trend_direction=trend_direction,
            volatility_score=volatility,
        )

        # Generate summary message
        aggregated.message = self._generate_message(aggregated)

        # Add to history
        self._add_to_history(aggregated)

        self.logger.info(
            f"Aggregated sentiment: score={weighted_score:.3f}, "
            f"level={sentiment_level.value}, confidence={confidence:.3f}, "
            f"sources={num_sources}"
        )

        return aggregated

    def _generate_signal_id(self) -> str:
        """Generate unique signal ID."""
        timestamp = datetime.now(timezone.utc).isoformat()
        hash_input = f"sentiment_{timestamp}_{len(self.sentiment_history)}".encode()
        return hashlib.md5(hash_input).hexdigest()[:12]

    def _classify_sentiment(self, score: float) -> SentimentLevel:
        """Classify sentiment score into categorical level."""
        if score >= 0.6:
            return SentimentLevel.EXTREMELY_POSITIVE
        elif score >= 0.2:
            return SentimentLevel.POSITIVE
        elif score >= -0.2:
            return SentimentLevel.NEUTRAL
        elif score >= -0.6:
            return SentimentLevel.NEGATIVE
        else:
            return SentimentLevel.EXTREMELY_NEGATIVE

    def _determine_trend(self, scores: List[SentimentScore]) -> str:
        """Determine overall trend direction from source breakdown."""
        if not scores:
            return "flat"

        positive_count = sum(1 for s in scores if s.weighted_score > 0.1)
        negative_count = sum(1 for s in scores if s.weighted_score < -0.1)

        total = len(scores)
        if positive_count / total >= 0.7:
            return "bullish"
        elif negative_count / total >= 0.7:
            return "bearish"
        elif positive_count / total >= 0.4:
            return "mixed"
        else:
            return "flat"

    def _calculate_volatility(self, scores: List[SentimentScore]) -> float:
        """Calculate volatility (variance) of sentiment across sources."""
        if len(scores) < 2:
            return 0.0

        weighted_scores = [s.weighted_score for s in scores]
        mean = sum(weighted_scores) / len(weighted_scores)
        variance = sum((x - mean) ** 2 for x in weighted_scores) / len(weighted_scores)
        volatility = variance ** 0.5  # Standard deviation

        return min(volatility, 1.0)  # Cap at 1.0

    def _calculate_weight_variance(self, scores: List[SentimentScore]) -> float:
        """Calculate variance in reliability weights across sources."""
        if len(scores) < 2:
            return 0.0

        weights = [s.reliability_weight for s in scores]
        mean = sum(weights) / len(weights)
        variance = sum((w - mean) ** 2 for w in weights) / len(weights)
        return variance ** 0.5

    def _calculate_confidence(
        self,
        num_sources: int,
        weight_variance: float,
    ) -> float:
        """Calculate confidence score (0.0 to 1.0).

        Confidence increases with number of sources and decreases with
        weight variance (diverse sources boost confidence).
        """
        source_factor = min(num_sources / self.max_sources, 1.0)
        variance_penalty = weight_variance * 0.3  # Max 0.3 penalty

        confidence = (source_factor * 0.7) + ((1.0 - variance_penalty) * 0.3)
        return max(0.0, min(1.0, confidence))

    def _generate_message(self, agg: AggregatedSentiment) -> str:
        """Generate human-readable summary message."""
        level = agg.aggregate_level.value.replace("_", " ").title()
        score_pct = int(abs(agg.aggregate_score) * 100)

        if agg.confidence_score < self.min_confidence_threshold:
            return (
                f"Sentiment: {level} ({score_pct}%) | "
                f"Confidence: LOW ({agg.confidence_score:.1%}) | "
                f"Sources: {agg.num_sources}/5"
            )

        return (
            f"Sentiment: {level} ({score_pct}%) | "
            f"Trend: {agg.trend_direction.upper()} | "
            f"Confidence: {agg.confidence_score:.1%} | "
            f"Articles: {agg.total_articles}"
        )

    def _add_to_history(self, aggregated: AggregatedSentiment) -> None:
        """Add aggregated sentiment to history, maintaining size limit."""
        self.sentiment_history.append(aggregated)
        if len(self.sentiment_history) > self.sentiment_history_limit:
            self.sentiment_history.pop(0)

    def get_history(self, limit: Optional[int] = None) -> List[AggregatedSentiment]:
        """Retrieve sentiment history.

        Args:
            limit: Maximum number of recent entries (None for all)

        Returns:
            List of recent AggregatedSentiment objects
        """
        if limit is None:
            return self.sentiment_history.copy()
        return self.sentiment_history[-limit:]

    def get_source_performance(self) -> Dict[str, Dict[str, Any]]:
        """Analyze performance and reliability of cached sources.

        Returns:
            Dictionary mapping source names to performance metrics
        """
        performance = {}
        for source_name, score in self.source_cache.items():
            performance[source_name] = {
                "reliability_weight": score.reliability_weight,
                "last_raw_score": score.raw_score,
                "last_weighted_score": score.weighted_score,
                "article_count": score.article_count,
                "timestamp": score.timestamp,
            }
        return performance

    def clear_cache(self) -> None:
        """Clear source cache."""
        self.source_cache.clear()
        self.logger.info("Source cache cleared")

    def clear_history(self) -> None:
        """Clear sentiment history."""
        self.sentiment_history.clear()
        self.logger.info("Sentiment history cleared")
