"""
Catalyst Scoring System for ProfitEngine v5

Provides intelligent catalyst detection and scoring for trading signals.
Integrates with Finnhub news API and Alpaca analyst consensus data.

Features:
- FDA approval detection (biotech)
- Earnings surprise analysis
- Analyst upgrade tracking
- News sentiment analysis
- Sector momentum measurement
- Short squeeze potential detection

Usage:
    scorer = CatalystScorer(finnhub_api_key, alpaca_api_key)
    score = scorer.score_catalysts('AAPL')
    details = scorer.get_catalyst_details('AAPL')
    adjusted = scorer.weight_signal_by_catalyst(base_signal=0.75, catalyst_score=score)
"""

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta

try:
    import httpx
except ImportError:
    httpx = None

logger = logging.getLogger(__name__)


@dataclass
class CatalystDetail:
    """Detailed catalyst information."""
    type: str
    source: str
    impact: float  # 0-1 normalized impact
    confidence: float  # 0-1 confidence level
    timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScoringResult:
    """Complete catalyst scoring result."""
    symbol: str
    total_score: float  # 0-100
    catalysts: List[Tuple[str, float]]  # List of (catalyst_type, points)
    details: List[CatalystDetail]
    breakdown: Dict[str, float]  # Component breakdown
    timestamp: str


class CatalystScorer:
    """
    Intelligent catalyst detection and scoring system.

    Combines multiple data sources to identify and quantify potential catalysts
    that could drive significant price movements.
    """

    # Catalyst point allocations
    CATALYST_WEIGHTS = {
        'fda_approval': 100,           # FDA drug approval (biotech)
        'earnings_surprise': 75,        # Beat earnings > 5%
        'analyst_upgrade': 50,          # Positive analyst consensus
        'news_sentiment': 30,           # Positive news articles
        'sector_momentum': 20,          # Sector outperforming
        'short_squeeze': 15,            # High short interest
        'earnings_beat': 60,            # Earnings beat
        'revenue_beat': 50,             # Revenue beat
        'guidance_raise': 55,           # Raised guidance
        'product_launch': 65,           # New product launch
        'partnership': 45,              # Strategic partnership
        'insider_buying': 40,           # Insider buying activity
    }

    def __init__(self, finnhub_api_key: Optional[str] = None, alpaca_api_key: Optional[str] = None):
        """
        Initialize catalyst scorer.

        Args:
            finnhub_api_key: Finnhub API key (defaults to FINNHUB_API_KEY env var)
            alpaca_api_key: Alpaca API key (defaults to ALPACA_API_KEY env var)
        """
        self.finnhub_api_key = finnhub_api_key or os.getenv('FINNHUB_API_KEY', '')
        self.alpaca_api_key = alpaca_api_key or os.getenv('ALPACA_API_KEY', '')
        self.alpaca_base_url = 'https://api.alpaca.markets'
        self.finnhub_base_url = 'https://finnhub.io/api/v1'
        self.client = httpx.Client(timeout=30.0) if httpx else None

    def score_catalysts(self, symbol: str) -> float:
        """
        Calculate overall catalyst score (0-100) for a symbol.

        Args:
            symbol: Stock ticker symbol

        Returns:
            Catalyst score from 0-100, where higher indicates stronger catalysts present
        """
        try:
            score = 0.0

            # FDA approval catalyst (biotech/pharma)
            score += self._score_fda_approval(symbol)

            # Earnings surprise catalyst
            score += self._score_earnings_surprise(symbol)

            # Analyst upgrade catalyst
            score += self._score_analyst_upgrades(symbol)

            # News sentiment catalyst
            score += self._score_news_sentiment(symbol)

            # Sector momentum catalyst
            score += self._score_sector_momentum(symbol)

            # Short squeeze potential
            score += self._score_short_squeeze(symbol)

            # Cap at 100
            return min(score, 100.0)

        except Exception as e:
            logger.error(f"Error scoring catalysts for {symbol}: {e}")
            return 0.0

    def get_catalyst_details(self, symbol: str) -> Dict[str, Any]:
        """
        Get detailed catalyst information for a symbol.

        Returns dictionary with:
        {
            'symbol': str,
            'total_score': float (0-100),
            'catalysts': [{'type': str, 'source': str, 'impact': float, 'confidence': float}],
            'breakdown': {'catalyst_type': score, ...},
            'timestamp': ISO datetime string
        }

        Args:
            symbol: Stock ticker symbol

        Returns:
            Dictionary with detailed catalyst information
        """
        try:
            details = []
            breakdown = {}
            timestamp = datetime.utcnow().isoformat() + 'Z'

            # Collect details from each catalyst source
            fda_detail = self._get_fda_detail(symbol)
            if fda_detail:
                details.append(fda_detail)
                breakdown['fda_approval'] = fda_detail.impact * 100

            earnings_detail = self._get_earnings_detail(symbol)
            if earnings_detail:
                details.append(earnings_detail)
                breakdown['earnings_surprise'] = earnings_detail.impact * 100

            analyst_detail = self._get_analyst_detail(symbol)
            if analyst_detail:
                details.append(analyst_detail)
                breakdown['analyst_upgrades'] = analyst_detail.impact * 100

            news_detail = self._get_news_detail(symbol)
            if news_detail:
                details.append(news_detail)
                breakdown['news_sentiment'] = news_detail.impact * 100

            sector_detail = self._get_sector_detail(symbol)
            if sector_detail:
                details.append(sector_detail)
                breakdown['sector_momentum'] = sector_detail.impact * 100

            squeeze_detail = self._get_squeeze_detail(symbol)
            if squeeze_detail:
                details.append(squeeze_detail)
                breakdown['short_squeeze'] = squeeze_detail.impact * 100

            total_score = self.score_catalysts(symbol)

            return {
                'symbol': symbol,
                'total_score': total_score,
                'catalysts': [
                    {
                        'type': d.type,
                        'source': d.source,
                        'impact': d.impact,
                        'confidence': d.confidence,
                        'timestamp': d.timestamp,
                        'metadata': d.metadata,
                    }
                    for d in details
                ],
                'breakdown': breakdown,
                'timestamp': timestamp,
            }

        except Exception as e:
            logger.error(f"Error getting catalyst details for {symbol}: {e}")
            return {
                'symbol': symbol,
                'total_score': 0.0,
                'catalysts': [],
                'breakdown': {},
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'error': str(e),
            }

    def weight_signal_by_catalyst(self, base_signal_strength: float, catalyst_score: float) -> float:
        """
        Adjust base signal strength by catalyst score.

        Stronger catalysts increase confidence in the signal.
        Signal is amplified multiplicatively, capped at 1.0.

        Formula: adjusted = base_signal * (1 + (catalyst_score / 100) * 0.5)
        - At catalyst_score=0: adjusted = base_signal
        - At catalyst_score=100: adjusted = base_signal * 1.5

        Args:
            base_signal_strength: Original signal strength (0-1)
            catalyst_score: Catalyst score (0-100)

        Returns:
            Adjusted signal strength (0-1), capped at 1.0
        """
        if not 0 <= base_signal_strength <= 1:
            logger.warning(f"Signal strength {base_signal_strength} outside [0, 1], clamping")
            base_signal_strength = max(0, min(1, base_signal_strength))

        if not 0 <= catalyst_score <= 100:
            logger.warning(f"Catalyst score {catalyst_score} outside [0, 100], clamping")
            catalyst_score = max(0, min(100, catalyst_score))

        # Amplification factor: 1.0 at catalyst_score=0, 1.5 at catalyst_score=100
        amplification = 1.0 + (catalyst_score / 100.0) * 0.5

        # Apply amplification
        adjusted = base_signal_strength * amplification

        # Cap at 1.0
        return min(adjusted, 1.0)

    # --- Catalyst Detection Methods ---

    def _score_fda_approval(self, symbol: str) -> float:
        """Detect FDA approval catalysts (biotech/pharma)."""
        try:
            if not self.finnhub_api_key:
                logger.debug(f"Finnhub API key not configured, skipping FDA approval check")
                return 0.0

            news = self._fetch_finnhub_news(symbol)

            for article in news:
                title = (article.get('headline', '') or '').lower()
                summary = (article.get('summary', '') or '').lower()

                # Check for FDA approval keywords
                if any(keyword in title or keyword in summary for keyword in [
                    'fda approval', 'fda approved', 'fda breakthrough',
                    'fda breakthrough designation', 'pdufa', 'bla approval'
                ]):
                    # Verify publication is recent (within 30 days)
                    pub_time = article.get('datetime', 0)
                    if self._is_recent(pub_time, days=30):
                        logger.info(f"FDA approval catalyst found for {symbol}")
                        return self.CATALYST_WEIGHTS['fda_approval']

            return 0.0

        except Exception as e:
            logger.error(f"Error checking FDA approval for {symbol}: {e}")
            return 0.0

    def _score_earnings_surprise(self, symbol: str) -> float:
        """Detect earnings surprise catalysts."""
        try:
            if not self.finnhub_api_key:
                logger.debug(f"Finnhub API key not configured, skipping earnings check")
                return 0.0

            earnings_data = self._fetch_finnhub_earnings(symbol)

            if not earnings_data:
                return 0.0

            # Check most recent earnings
            latest = earnings_data[0] if earnings_data else None
            if not latest:
                return 0.0

            actual_eps = latest.get('actual')
            estimate_eps = latest.get('estimate')

            if actual_eps is None or estimate_eps is None:
                return 0.0

            # Calculate surprise percentage
            if estimate_eps == 0:
                return 0.0

            surprise_pct = abs(actual_eps - estimate_eps) / abs(estimate_eps)

            if actual_eps > estimate_eps and surprise_pct > 0.05:
                # Beat by more than 5%
                logger.info(f"Earnings surprise found for {symbol}: {surprise_pct:.2%}")
                return self.CATALYST_WEIGHTS['earnings_surprise']

            return 0.0

        except Exception as e:
            logger.error(f"Error checking earnings surprise for {symbol}: {e}")
            return 0.0

    def _score_analyst_upgrades(self, symbol: str) -> float:
        """Detect analyst upgrade catalysts."""
        try:
            if not self.alpaca_api_key:
                logger.debug(f"Alpaca API key not configured, skipping analyst check")
                return 0.0

            consensus = self._fetch_analyst_consensus(symbol)

            if not consensus:
                return 0.0

            rating = consensus.get('analyst_consensus')

            # Rating scale: 1=strong buy, 5=strong sell
            # Strong consensus positive: < 2.0
            if rating and rating < 2.0:
                logger.info(f"Positive analyst consensus for {symbol}: {rating:.2f}")
                return self.CATALYST_WEIGHTS['analyst_upgrade']

            return 0.0

        except Exception as e:
            logger.error(f"Error checking analyst upgrades for {symbol}: {e}")
            return 0.0

    def _score_news_sentiment(self, symbol: str) -> float:
        """Detect positive news sentiment catalysts."""
        try:
            if not self.finnhub_api_key:
                logger.debug(f"Finnhub API key not configured, skipping news sentiment check")
                return 0.0

            news = self._fetch_finnhub_news(symbol)

            if not news:
                return 0.0

            # Analyze sentiment of recent articles
            positive_count = 0
            total_articles = min(len(news), 20)  # Analyze last 20 articles

            for article in news[:total_articles]:
                sentiment = article.get('sentiment', 0)  # 0-1 scale typically
                headline = (article.get('headline', '') or '').lower()

                # Simple heuristic: look for positive keywords and sentiment
                if sentiment > 0.6 or any(keyword in headline for keyword in [
                    'surge', 'beat', 'gain', 'profit', 'bullish',
                    'upgrade', 'rally', 'strong', 'outperform'
                ]):
                    positive_count += 1

            # If > 50% of recent articles are positive
            if total_articles > 0 and positive_count / total_articles > 0.5:
                logger.info(f"Positive news sentiment for {symbol}: {positive_count}/{total_articles}")
                return self.CATALYST_WEIGHTS['news_sentiment']

            return 0.0

        except Exception as e:
            logger.error(f"Error checking news sentiment for {symbol}: {e}")
            return 0.0

    def _score_sector_momentum(self, symbol: str) -> float:
        """Detect sector momentum catalysts."""
        try:
            # This would require sector performance data
            # For now, return 0 as it requires additional data source
            # In production, integrate with data provider that has sector indices
            return 0.0

        except Exception as e:
            logger.error(f"Error checking sector momentum for {symbol}: {e}")
            return 0.0

    def _score_short_squeeze(self, symbol: str) -> float:
        """Detect short squeeze potential catalysts."""
        try:
            # This would require short interest data
            # Available from Finviz, MarketWatch, or broker data
            # For now, return 0 as it requires additional data source
            return 0.0

        except Exception as e:
            logger.error(f"Error checking short squeeze for {symbol}: {e}")
            return 0.0

    # --- Detail Retrieval Methods ---

    def _get_fda_detail(self, symbol: str) -> Optional[CatalystDetail]:
        """Get FDA approval catalyst detail."""
        try:
            if not self.finnhub_api_key:
                return None

            news = self._fetch_finnhub_news(symbol)

            for article in news:
                title = (article.get('headline', '') or '').lower()

                if any(keyword in title for keyword in [
                    'fda approval', 'fda approved', 'fda breakthrough'
                ]):
                    if self._is_recent(article.get('datetime', 0), days=30):
                        return CatalystDetail(
                            type='fda_approval',
                            source='Finnhub News',
                            impact=1.0,
                            confidence=0.95,
                            timestamp=datetime.utcnow().isoformat() + 'Z',
                            metadata={
                                'headline': article.get('headline'),
                                'source': article.get('source'),
                                'url': article.get('url'),
                            }
                        )

            return None

        except Exception as e:
            logger.error(f"Error getting FDA detail for {symbol}: {e}")
            return None

    def _get_earnings_detail(self, symbol: str) -> Optional[CatalystDetail]:
        """Get earnings surprise catalyst detail."""
        try:
            if not self.finnhub_api_key:
                return None

            earnings_data = self._fetch_finnhub_earnings(symbol)

            if not earnings_data:
                return None

            latest = earnings_data[0]
            actual_eps = latest.get('actual')
            estimate_eps = latest.get('estimate')

            if actual_eps is None or estimate_eps is None:
                return None

            if estimate_eps == 0:
                return None

            surprise_pct = abs(actual_eps - estimate_eps) / abs(estimate_eps)

            if actual_eps > estimate_eps and surprise_pct > 0.05:
                return CatalystDetail(
                    type='earnings_surprise',
                    source='Finnhub Earnings',
                    impact=min(surprise_pct, 1.0),
                    confidence=0.9,
                    timestamp=datetime.utcnow().isoformat() + 'Z',
                    metadata={
                        'actual_eps': actual_eps,
                        'estimate_eps': estimate_eps,
                        'surprise_pct': surprise_pct,
                    }
                )

            return None

        except Exception as e:
            logger.error(f"Error getting earnings detail for {symbol}: {e}")
            return None

    def _get_analyst_detail(self, symbol: str) -> Optional[CatalystDetail]:
        """Get analyst upgrade catalyst detail."""
        try:
            if not self.alpaca_api_key:
                return None

            consensus = self._fetch_analyst_consensus(symbol)

            if not consensus:
                return None

            rating = consensus.get('analyst_consensus')
            count = consensus.get('analyst_count', 0)

            if rating and rating < 2.0:
                return CatalystDetail(
                    type='analyst_upgrades',
                    source='Alpaca Analyst Data',
                    impact=(5.0 - rating) / 5.0,  # Normalize to 0-1
                    confidence=min(count / 50.0, 1.0) if count > 0 else 0.5,
                    timestamp=datetime.utcnow().isoformat() + 'Z',
                    metadata={
                        'consensus_rating': rating,
                        'analyst_count': count,
                    }
                )

            return None

        except Exception as e:
            logger.error(f"Error getting analyst detail for {symbol}: {e}")
            return None

    def _get_news_detail(self, symbol: str) -> Optional[CatalystDetail]:
        """Get news sentiment catalyst detail."""
        try:
            if not self.finnhub_api_key:
                return None

            news = self._fetch_finnhub_news(symbol)

            if not news:
                return None

            positive_count = 0
            total_articles = min(len(news), 20)

            for article in news[:total_articles]:
                sentiment = article.get('sentiment', 0)
                headline = (article.get('headline', '') or '').lower()

                if sentiment > 0.6 or any(keyword in headline for keyword in [
                    'surge', 'beat', 'gain', 'profit', 'bullish'
                ]):
                    positive_count += 1

            if total_articles > 0 and positive_count / total_articles > 0.5:
                return CatalystDetail(
                    type='news_sentiment',
                    source='Finnhub News Analysis',
                    impact=positive_count / total_articles,
                    confidence=min(total_articles / 20.0, 1.0),
                    timestamp=datetime.utcnow().isoformat() + 'Z',
                    metadata={
                        'positive_articles': positive_count,
                        'total_analyzed': total_articles,
                    }
                )

            return None

        except Exception as e:
            logger.error(f"Error getting news detail for {symbol}: {e}")
            return None

    def _get_sector_detail(self, symbol: str) -> Optional[CatalystDetail]:
        """Get sector momentum catalyst detail."""
        # Placeholder for sector analysis
        return None

    def _get_squeeze_detail(self, symbol: str) -> Optional[CatalystDetail]:
        """Get short squeeze catalyst detail."""
        # Placeholder for squeeze analysis
        return None

    # --- API Integration Methods ---

    def _fetch_finnhub_news(self, symbol: str) -> List[Dict[str, Any]]:
        """Fetch recent news for symbol from Finnhub."""
        if not self.client or not self.finnhub_api_key:
            return []

        try:
            from_date = (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d')
            to_date = datetime.utcnow().strftime('%Y-%m-%d')

            url = f"{self.finnhub_base_url}/company-news"
            params = {
                'symbol': symbol,
                'from': from_date,
                'to': to_date,
                'token': self.finnhub_api_key,
            }

            response = self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            return data if isinstance(data, list) else data.get('data', [])

        except Exception as e:
            logger.error(f"Error fetching Finnhub news for {symbol}: {e}")
            return []

    def _fetch_finnhub_earnings(self, symbol: str) -> List[Dict[str, Any]]:
        """Fetch earnings surprises from Finnhub."""
        if not self.client or not self.finnhub_api_key:
            return []

        try:
            url = f"{self.finnhub_base_url}/stock/earnings-surprise"
            params = {
                'symbol': symbol,
                'token': self.finnhub_api_key,
            }

            response = self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            return data if isinstance(data, list) else data.get('data', [])

        except Exception as e:
            logger.error(f"Error fetching Finnhub earnings for {symbol}: {e}")
            return []

    def _fetch_analyst_consensus(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch analyst consensus from Alpaca."""
        if not self.client or not self.alpaca_api_key:
            return None

        try:
            url = f"{self.alpaca_base_url}/v2/stocks/estimates"
            headers = {
                'Authorization': f'Bearer {self.alpaca_api_key}',
                'Content-Type': 'application/json',
            }
            params = {'symbol': symbol}

            response = self.client.get(url, headers=headers, params=params)
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"Error fetching analyst consensus from Alpaca for {symbol}: {e}")
            return None

    # --- Helper Methods ---

    def _is_recent(self, timestamp: int, days: int = 30) -> bool:
        """Check if Unix timestamp is within N days."""
        if not timestamp:
            return False

        try:
            article_date = datetime.fromtimestamp(timestamp)
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            return article_date >= cutoff_date
        except Exception:
            return False

    def __del__(self):
        """Clean up HTTP client."""
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass


# --- Convenience Functions ---

_global_scorer: Optional[CatalystScorer] = None


def get_scorer(finnhub_key: Optional[str] = None, alpaca_key: Optional[str] = None) -> CatalystScorer:
    """Get or create global catalyst scorer instance."""
    global _global_scorer

    if _global_scorer is None:
        _global_scorer = CatalystScorer(finnhub_key, alpaca_key)

    return _global_scorer


def score_catalysts(symbol: str) -> float:
    """Score catalysts for a symbol using global scorer."""
    return get_scorer().score_catalysts(symbol)


def get_catalyst_details(symbol: str) -> Dict[str, Any]:
    """Get catalyst details for a symbol using global scorer."""
    return get_scorer().get_catalyst_details(symbol)


def weight_signal_by_catalyst(base_signal: float, catalyst_score: float) -> float:
    """Adjust signal strength by catalyst score using global scorer."""
    return get_scorer().weight_signal_by_catalyst(base_signal, catalyst_score)


if __name__ == '__main__':
    """Example usage."""
    import json

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Example: Score catalysts for AAPL
    scorer = CatalystScorer()

    # Get score
    score = scorer.score_catalysts('AAPL')
    print(f"\nAPPL Catalyst Score: {score:.2f}/100")

    # Get details
    details = scorer.get_catalyst_details('AAPL')
    print(f"\nCatalyst Details:")
    print(json.dumps(details, indent=2, default=str))

    # Adjust signal by catalyst
    base_signal = 0.75
    adjusted = scorer.weight_signal_by_catalyst(base_signal, score)
    print(f"\nSignal Adjustment:")
    print(f"  Base signal: {base_signal:.3f}")
    print(f"  Catalyst score: {score:.2f}/100")
    print(f"  Adjusted signal: {adjusted:.3f}")
    print(f"  Amplification: {adjusted/base_signal:.2f}x")
