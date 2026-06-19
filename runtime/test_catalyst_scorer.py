"""
Unit tests for catalyst_scorer.py

Tests cover:
- Catalyst score calculation
- Catalyst detail retrieval
- Signal weighting formula
- API integration
- Error handling
- Edge cases
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from catalyst_scorer import (
    CatalystScorer,
    CatalystDetail,
    score_catalysts,
    get_catalyst_details,
    weight_signal_by_catalyst,
)


class TestCatalystScorer:
    """Test suite for CatalystScorer class."""

    @pytest.fixture
    def scorer(self):
        """Create a scorer instance for testing."""
        return CatalystScorer(
            finnhub_api_key='test-finnhub-key',
            alpaca_api_key='test-alpaca-key'
        )

    # --- Basic Functionality Tests ---

    def test_initialization_with_api_keys(self):
        """Test scorer initialization with API keys."""
        scorer = CatalystScorer(
            finnhub_api_key='test-finnhub',
            alpaca_api_key='test-alpaca'
        )
        assert scorer.finnhub_api_key == 'test-finnhub'
        assert scorer.alpaca_api_key == 'test-alpaca'

    def test_initialization_from_env(self, monkeypatch):
        """Test scorer initialization from environment variables."""
        monkeypatch.setenv('FINNHUB_API_KEY', 'env-finnhub-key')
        monkeypatch.setenv('ALPACA_API_KEY', 'env-alpaca-key')

        scorer = CatalystScorer()
        assert scorer.finnhub_api_key == 'env-finnhub-key'
        assert scorer.alpaca_api_key == 'env-alpaca-key'

    def test_score_catalysts_returns_valid_range(self, scorer):
        """Test that score_catalysts returns value in valid range."""
        with patch.object(scorer, '_fetch_finnhub_news', return_value=[]):
            with patch.object(scorer, '_fetch_finnhub_earnings', return_value=[]):
                with patch.object(scorer, '_fetch_analyst_consensus', return_value=None):
                    score = scorer.score_catalysts('AAPL')

                    assert isinstance(score, float)
                    assert 0 <= score <= 100

    def test_score_catalysts_caps_at_100(self, scorer):
        """Test that total score is capped at 100."""
        # Mock all catalysts to return max points
        with patch.object(scorer, '_score_fda_approval', return_value=100):
            with patch.object(scorer, '_score_earnings_surprise', return_value=75):
                with patch.object(scorer, '_score_analyst_upgrades', return_value=50):
                    score = scorer.score_catalysts('AAPL')

                    # Would be 225 without cap
                    assert score == 100
                    assert score <= 100

    def test_get_catalyst_details_structure(self, scorer):
        """Test that catalyst details have correct structure."""
        with patch.object(scorer, '_get_fda_detail', return_value=None):
            with patch.object(scorer, '_get_earnings_detail', return_value=None):
                with patch.object(scorer, '_get_analyst_detail', return_value=None):
                    with patch.object(scorer, '_get_news_detail', return_value=None):
                        with patch.object(scorer, '_get_sector_detail', return_value=None):
                            with patch.object(scorer, '_get_squeeze_detail', return_value=None):
                                with patch.object(scorer, 'score_catalysts', return_value=50.0):
                                    details = scorer.get_catalyst_details('AAPL')

                                    assert 'symbol' in details
                                    assert 'total_score' in details
                                    assert 'catalysts' in details
                                    assert 'breakdown' in details
                                    assert 'timestamp' in details
                                    assert details['symbol'] == 'AAPL'
                                    assert isinstance(details['catalysts'], list)
                                    assert isinstance(details['breakdown'], dict)

    def test_get_catalyst_details_with_error(self, scorer):
        """Test catalyst details handles errors gracefully."""
        with patch.object(scorer, '_get_fda_detail', side_effect=Exception('API error')):
            with patch.object(scorer, 'score_catalysts', side_effect=Exception('API error')):
                details = scorer.get_catalyst_details('AAPL')

                assert 'error' in details
                assert details['total_score'] == 0.0
                assert details['catalysts'] == []

    # --- Signal Weighting Tests ---

    def test_weight_signal_base_amplification(self, scorer):
        """Test signal weighting uses correct amplification formula."""
        base_signal = 0.5
        catalyst_score = 0.0

        adjusted = scorer.weight_signal_by_catalyst(base_signal, catalyst_score)

        # At catalyst_score=0, amplification factor should be 1.0
        assert adjusted == pytest.approx(base_signal, abs=0.001)

    def test_weight_signal_max_amplification(self, scorer):
        """Test signal weighting at max catalyst score."""
        base_signal = 0.5
        catalyst_score = 100.0

        adjusted = scorer.weight_signal_by_catalyst(base_signal, catalyst_score)

        # At catalyst_score=100, amplification should be 1.5
        expected = base_signal * 1.5
        assert adjusted == pytest.approx(expected, abs=0.001)

    def test_weight_signal_mid_amplification(self, scorer):
        """Test signal weighting at mid catalyst score."""
        base_signal = 0.8
        catalyst_score = 50.0

        adjusted = scorer.weight_signal_by_catalyst(base_signal, catalyst_score)

        # At catalyst_score=50, amplification should be 1.25
        expected = base_signal * 1.25
        assert adjusted == pytest.approx(expected, abs=0.001)

    def test_weight_signal_capped_at_one(self, scorer):
        """Test that adjusted signal is capped at 1.0."""
        base_signal = 0.9
        catalyst_score = 100.0

        adjusted = scorer.weight_signal_by_catalyst(base_signal, catalyst_score)

        # 0.9 * 1.5 = 1.35, should be capped at 1.0
        assert adjusted == 1.0
        assert adjusted <= 1.0

    def test_weight_signal_clamps_invalid_base_signal(self, scorer):
        """Test that invalid base signal is clamped to [0, 1]."""
        # Test value > 1
        adjusted = scorer.weight_signal_by_catalyst(1.5, 50.0)
        assert 0 <= adjusted <= 1.0

        # Test value < 0
        adjusted = scorer.weight_signal_by_catalyst(-0.5, 50.0)
        assert 0 <= adjusted <= 1.0

    def test_weight_signal_clamps_invalid_catalyst_score(self, scorer):
        """Test that invalid catalyst score is clamped to [0, 100]."""
        # Test value > 100
        adjusted = scorer.weight_signal_by_catalyst(0.5, 150.0)
        # Should be treated as 100
        expected = 0.5 * 1.5
        assert adjusted == pytest.approx(expected, abs=0.001)

        # Test value < 0
        adjusted = scorer.weight_signal_by_catalyst(0.5, -50.0)
        # Should be treated as 0
        assert adjusted == pytest.approx(0.5, abs=0.001)

    # --- Catalyst Detection Tests ---

    def test_fda_approval_detection(self, scorer):
        """Test FDA approval catalyst detection."""
        # Mock news with FDA approval
        mock_news = [
            {
                'headline': 'Company Gets FDA Approval for New Drug',
                'summary': 'FDA approved the new treatment',
                'datetime': int(datetime.utcnow().timestamp()),
                'source': 'Reuters',
            }
        ]

        with patch.object(scorer, '_fetch_finnhub_news', return_value=mock_news):
            score = scorer._score_fda_approval('XBIO')

            assert score == scorer.CATALYST_WEIGHTS['fda_approval']

    def test_fda_approval_old_news_ignored(self, scorer):
        """Test that old FDA approval news is ignored."""
        # Mock news from 60 days ago
        old_timestamp = int((datetime.utcnow() - timedelta(days=60)).timestamp())

        mock_news = [
            {
                'headline': 'Company Gets FDA Approval for New Drug',
                'summary': 'FDA approved the new treatment',
                'datetime': old_timestamp,
                'source': 'Reuters',
            }
        ]

        with patch.object(scorer, '_fetch_finnhub_news', return_value=mock_news):
            score = scorer._score_fda_approval('XBIO')

            assert score == 0.0

    def test_earnings_surprise_detection(self, scorer):
        """Test earnings surprise catalyst detection."""
        mock_earnings = [
            {
                'actual': 2.50,
                'estimate': 2.30,
                'symbol': 'AAPL',
                'period': 'Q4',
                'year': 2024,
            }
        ]

        with patch.object(scorer, '_fetch_finnhub_earnings', return_value=mock_earnings):
            score = scorer._score_earnings_surprise('AAPL')

            # Beat by 8.7%
            assert score == scorer.CATALYST_WEIGHTS['earnings_surprise']

    def test_earnings_surprise_small_beat_ignored(self, scorer):
        """Test that small earnings beats are ignored."""
        mock_earnings = [
            {
                'actual': 2.32,
                'estimate': 2.30,
                'symbol': 'AAPL',
            }
        ]

        with patch.object(scorer, '_fetch_finnhub_earnings', return_value=mock_earnings):
            score = scorer._score_earnings_surprise('AAPL')

            # Beat by only 0.87%, below 5% threshold
            assert score == 0.0

    def test_earnings_surprise_miss(self, scorer):
        """Test that earnings misses don't score."""
        mock_earnings = [
            {
                'actual': 2.10,
                'estimate': 2.30,
                'symbol': 'AAPL',
            }
        ]

        with patch.object(scorer, '_fetch_finnhub_earnings', return_value=mock_earnings):
            score = scorer._score_earnings_surprise('AAPL')

            # Miss by 8.7%, but we only reward beats
            assert score == 0.0

    def test_analyst_upgrade_detection(self, scorer):
        """Test analyst upgrade catalyst detection."""
        mock_consensus = {
            'analyst_consensus': 1.8,
            'analyst_count': 42,
        }

        with patch.object(scorer, '_fetch_analyst_consensus', return_value=mock_consensus):
            score = scorer._score_analyst_upgrades('AAPL')

            # Rating 1.8 is strong buy (< 2.0)
            assert score == scorer.CATALYST_WEIGHTS['analyst_upgrade']

    def test_analyst_neutral_not_detected(self, scorer):
        """Test that neutral analyst consensus is not detected."""
        mock_consensus = {
            'analyst_consensus': 3.0,
            'analyst_count': 42,
        }

        with patch.object(scorer, '_fetch_analyst_consensus', return_value=mock_consensus):
            score = scorer._score_analyst_upgrades('AAPL')

            # Rating 3.0 is neutral
            assert score == 0.0

    def test_news_sentiment_detection(self, scorer):
        """Test positive news sentiment detection."""
        mock_news = [
            {'headline': 'Stock Surges on Earnings Beat', 'sentiment': 0.85},
            {'headline': 'Analyst Bullish on Outlook', 'sentiment': 0.90},
            {'headline': 'Company Gains Market Share', 'sentiment': 0.80},
            {'headline': 'Revenue Beats Expectations', 'sentiment': 0.87},
            {'headline': 'Stock Rally Continues', 'sentiment': 0.88},
        ]

        with patch.object(scorer, '_fetch_finnhub_news', return_value=mock_news):
            score = scorer._score_news_sentiment('AAPL')

            # 5/5 articles positive, > 50%
            assert score == scorer.CATALYST_WEIGHTS['news_sentiment']

    def test_news_sentiment_requires_majority(self, scorer):
        """Test that news sentiment requires > 50% positive articles."""
        mock_news = [
            {'headline': 'Stock Rises', 'sentiment': 0.85},
            {'headline': 'Stock Falls', 'sentiment': 0.15},
            {'headline': 'Stock Neutral', 'sentiment': 0.50},
        ]

        with patch.object(scorer, '_fetch_finnhub_news', return_value=mock_news):
            score = scorer._score_news_sentiment('AAPL')

            # Only 1/3 positive, < 50%
            assert score == 0.0

    # --- API Integration Tests ---

    def test_fetch_finnhub_news_success(self, scorer):
        """Test successful Finnhub news fetch."""
        mock_response = [
            {
                'headline': 'Test headline',
                'summary': 'Test summary',
                'datetime': int(datetime.utcnow().timestamp()),
                'source': 'Reuters',
                'url': 'https://example.com',
            }
        ]

        with patch.object(scorer.client, 'get') as mock_get:
            mock_get.return_value.json.return_value = mock_response

            news = scorer._fetch_finnhub_news('AAPL')

            assert len(news) == 1
            assert news[0]['headline'] == 'Test headline'

    def test_fetch_finnhub_news_handles_error(self, scorer):
        """Test that news fetch handles API errors gracefully."""
        with patch.object(scorer.client, 'get', side_effect=Exception('API error')):
            news = scorer._fetch_finnhub_news('AAPL')

            assert news == []

    def test_fetch_analyst_consensus_success(self, scorer):
        """Test successful Alpaca analyst consensus fetch."""
        mock_response = {
            'analyst_consensus': 1.9,
            'analyst_count': 35,
            'symbol': 'AAPL',
        }

        with patch.object(scorer.client, 'get') as mock_get:
            mock_get.return_value.json.return_value = mock_response

            consensus = scorer._fetch_analyst_consensus('AAPL')

            assert consensus['analyst_consensus'] == 1.9
            assert consensus['analyst_count'] == 35

    def test_fetch_analyst_consensus_handles_error(self, scorer):
        """Test that consensus fetch handles API errors gracefully."""
        with patch.object(scorer.client, 'get', side_effect=Exception('API error')):
            consensus = scorer._fetch_analyst_consensus('AAPL')

            assert consensus is None

    # --- Edge Cases ---

    def test_empty_news_list(self, scorer):
        """Test handling of empty news list."""
        with patch.object(scorer, '_fetch_finnhub_news', return_value=[]):
            score = scorer._score_fda_approval('AAPL')
            assert score == 0.0

    def test_none_values_in_earnings_data(self, scorer):
        """Test handling of None values in earnings data."""
        mock_earnings = [
            {
                'actual': None,
                'estimate': 2.30,
            }
        ]

        with patch.object(scorer, '_fetch_finnhub_earnings', return_value=mock_earnings):
            score = scorer._score_earnings_surprise('AAPL')

            assert score == 0.0

    def test_zero_estimate_eps(self, scorer):
        """Test handling of zero estimate EPS."""
        mock_earnings = [
            {
                'actual': 1.0,
                'estimate': 0.0,
            }
        ]

        with patch.object(scorer, '_fetch_finnhub_earnings', return_value=mock_earnings):
            score = scorer._score_earnings_surprise('AAPL')

            assert score == 0.0

    def test_missing_api_key(self):
        """Test that missing API keys are handled gracefully."""
        scorer = CatalystScorer(finnhub_api_key='', alpaca_api_key='')

        with patch.object(scorer, '_fetch_finnhub_news', return_value=[]):
            score = scorer._score_fda_approval('AAPL')
            assert score == 0.0

    def test_is_recent_timestamp(self, scorer):
        """Test timestamp recency check."""
        # Recent timestamp (within 30 days)
        recent_ts = int(datetime.utcnow().timestamp())
        assert scorer._is_recent(recent_ts, days=30) is True

        # Old timestamp (60 days ago)
        old_ts = int((datetime.utcnow() - timedelta(days=60)).timestamp())
        assert scorer._is_recent(old_ts, days=30) is False

        # No timestamp
        assert scorer._is_recent(None, days=30) is False
        assert scorer._is_recent(0, days=30) is False


# --- Module-Level Function Tests ---

class TestModuleFunctions:
    """Test module-level convenience functions."""

    def test_score_catalysts_function(self):
        """Test module-level score_catalysts function."""
        with patch('catalyst_scorer.get_scorer') as mock_get_scorer:
            mock_scorer = Mock()
            mock_scorer.score_catalysts.return_value = 75.0
            mock_get_scorer.return_value = mock_scorer

            score = score_catalysts('AAPL')

            assert score == 75.0
            mock_scorer.score_catalysts.assert_called_once_with('AAPL')

    def test_get_catalyst_details_function(self):
        """Test module-level get_catalyst_details function."""
        with patch('catalyst_scorer.get_scorer') as mock_get_scorer:
            mock_scorer = Mock()
            mock_scorer.get_catalyst_details.return_value = {
                'symbol': 'AAPL',
                'total_score': 75.0,
            }
            mock_get_scorer.return_value = mock_scorer

            details = get_catalyst_details('AAPL')

            assert details['symbol'] == 'AAPL'
            assert details['total_score'] == 75.0

    def test_weight_signal_by_catalyst_function(self):
        """Test module-level weight_signal_by_catalyst function."""
        with patch('catalyst_scorer.get_scorer') as mock_get_scorer:
            mock_scorer = Mock()
            mock_scorer.weight_signal_by_catalyst.return_value = 0.85
            mock_get_scorer.return_value = mock_scorer

            adjusted = weight_signal_by_catalyst(0.75, 50.0)

            assert adjusted == 0.85
            mock_scorer.weight_signal_by_catalyst.assert_called_once_with(0.75, 50.0)


# --- Integration Tests ---

class TestIntegration:
    """Integration tests with multiple components."""

    def test_full_catalyst_analysis_workflow(self):
        """Test complete catalyst analysis workflow."""
        scorer = CatalystScorer(
            finnhub_api_key='test-key',
            alpaca_api_key='test-key'
        )

        # Mock all data sources
        with patch.object(scorer, '_fetch_finnhub_news') as mock_news:
            with patch.object(scorer, '_fetch_finnhub_earnings') as mock_earnings:
                with patch.object(scorer, '_fetch_analyst_consensus') as mock_consensus:
                    mock_news.return_value = [
                        {
                            'headline': 'Stock Surges on Earnings Beat',
                            'sentiment': 0.85,
                            'datetime': int(datetime.utcnow().timestamp()),
                        }
                    ]
                    mock_earnings.return_value = [
                        {'actual': 2.50, 'estimate': 2.30}
                    ]
                    mock_consensus.return_value = {
                        'analyst_consensus': 1.8,
                        'analyst_count': 42,
                    }

                    # Get comprehensive analysis
                    score = scorer.score_catalysts('AAPL')
                    details = scorer.get_catalyst_details('AAPL')
                    adjusted = scorer.weight_signal_by_catalyst(0.70, score)

                    # Verify results
                    assert score > 0
                    assert len(details['catalysts']) > 0
                    assert adjusted >= 0.70  # Should be amplified
                    assert adjusted <= 1.0  # Should be capped


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
