"""
Test suite for multi_timeframe_validator.py

Tests all core functionality:
- TimeframeSignal interpretation
- MultiTimeframeAnalysis confirmation counting
- Technical indicator calculations
- Complete validator workflows
"""

import asyncio
import pytest
from unittest.mock import Mock, patch, AsyncMock
from multi_timeframe_validator import (
    TimeframeSignal,
    MultiTimeframeAnalysis,
    TechnicalIndicators,
    TimeframeDataFetcher,
    MultiTimeframeValidator,
)


# ============================================================================
# TESTS FOR TimeframeSignal
# ============================================================================

class TestTimeframeSignal:
    """Tests for individual timeframe signal interpretation"""

    def test_rsi_oversold_uptrend_generates_buy(self):
        """RSI < 30 + SMA50 > SMA200 should generate BUY"""
        signal = TimeframeSignal(
            timeframe="5min",
            symbol="AAPL",
            rsi=25.0,  # Oversold
            sma50=150.0,
            sma200=145.0,  # Uptrend
            price=148.0,
            timestamp=1000.0
        )
        assert signal.get_signal() == "BUY"
        assert signal.is_uptrend is True
        assert signal.rsi_signal == "OVERSOLD"

    def test_rsi_overbought_downtrend_generates_sell(self):
        """RSI > 70 + SMA50 < SMA200 should generate SELL"""
        signal = TimeframeSignal(
            timeframe="30min",
            symbol="MSFT",
            rsi=75.0,  # Overbought
            sma50=300.0,
            sma200=305.0,  # Downtrend
            price=302.0,
            timestamp=2000.0
        )
        assert signal.get_signal() == "SELL"
        assert signal.is_uptrend is False
        assert signal.rsi_signal == "OVERBOUGHT"

    def test_rsi_neutral_no_signal(self):
        """RSI between 30-70 should not generate signal"""
        signal = TimeframeSignal(
            timeframe="day",
            symbol="GOOG",
            rsi=50.0,  # Neutral
            sma50=2800.0,
            sma200=2850.0,
            price=2810.0,
            timestamp=3000.0
        )
        assert signal.get_signal() is None
        assert signal.rsi_signal == "NEUTRAL"

    def test_oversold_but_downtrend_no_signal(self):
        """Oversold RSI but downtrend should not generate BUY"""
        signal = TimeframeSignal(
            timeframe="5min",
            symbol="NVDA",
            rsi=20.0,  # Oversold
            sma50=500.0,
            sma200=510.0,  # Downtrend
            price=505.0,
            timestamp=4000.0
        )
        assert signal.get_signal() is None


# ============================================================================
# TESTS FOR MultiTimeframeAnalysis
# ============================================================================

class TestMultiTimeframeAnalysis:
    """Tests for multi-timeframe signal aggregation"""

    def test_confirmation_counting(self):
        """Should count signals matching the signal type"""
        signals = {
            "5min": TimeframeSignal("5min", "AAPL", 25.0, 150.0, 145.0, 148.0, 1000.0),
            "30min": TimeframeSignal("30min", "AAPL", 28.0, 150.5, 145.5, 149.0, 2000.0),
            "day": TimeframeSignal("day", "AAPL", 50.0, 150.0, 150.0, 150.0, 3000.0),
        }
        analysis = MultiTimeframeAnalysis("AAPL", signals)

        assert analysis.get_confirmation_count("BUY") == 2
        assert analysis.get_confirmation_count("SELL") == 0

    def test_alignment_check(self):
        """Should verify if all timeframes agree"""
        # All aligned on BUY
        signals_buy = {
            "5min": TimeframeSignal("5min", "AAPL", 25.0, 150.0, 145.0, 148.0, 1000.0),
            "30min": TimeframeSignal("30min", "AAPL", 28.0, 150.5, 145.5, 149.0, 2000.0),
            "day": TimeframeSignal("day", "AAPL", 29.0, 151.0, 146.0, 150.0, 3000.0),
        }
        analysis = MultiTimeframeAnalysis("AAPL", signals_buy)
        assert analysis.is_aligned("BUY") is True

        # Not aligned
        signals_mixed = {
            "5min": TimeframeSignal("5min", "AAPL", 25.0, 150.0, 145.0, 148.0, 1000.0),
            "30min": TimeframeSignal("30min", "AAPL", 50.0, 150.5, 150.5, 149.0, 2000.0),
            "day": TimeframeSignal("day", "AAPL", 75.0, 149.0, 151.0, 150.0, 3000.0),
        }
        analysis = MultiTimeframeAnalysis("AAPL", signals_mixed)
        assert analysis.is_aligned("BUY") is False

    def test_strongest_signal(self):
        """Should identify strongest signal"""
        signals = {
            "5min": TimeframeSignal("5min", "AAPL", 25.0, 150.0, 145.0, 148.0, 1000.0),
            "30min": TimeframeSignal("30min", "AAPL", 28.0, 150.5, 145.5, 149.0, 2000.0),
            "day": TimeframeSignal("day", "AAPL", 50.0, 150.0, 150.0, 150.0, 3000.0),
        }
        analysis = MultiTimeframeAnalysis("AAPL", signals)

        strongest = analysis.get_strongest_signal()
        assert strongest == ("BUY", 2)


# ============================================================================
# TESTS FOR TechnicalIndicators
# ============================================================================

class TestTechnicalIndicators:
    """Tests for technical indicator calculations"""

    def test_rsi_calculation(self):
        """RSI should calculate correctly"""
        # Simple uptrend: closes = [1, 2, 3, 4, 5, ...]
        closes = list(range(1, 20))  # [1, 2, 3, ..., 19]
        rsi = TechnicalIndicators.rsi(closes, period=14)

        assert 0 <= rsi <= 100
        assert rsi > 50  # Uptrend should have higher RSI

    def test_rsi_oversold(self):
        """RSI should approach 0 in downtrend"""
        # Downtrend: closes = [20, 19, 18, ..., 1]
        closes = list(range(20, 0, -1))
        rsi = TechnicalIndicators.rsi(closes, period=14)

        assert 0 <= rsi <= 100
        assert rsi < 50  # Downtrend should have lower RSI

    def test_sma_calculation(self):
        """SMA should be correct mean"""
        closes = [100.0, 101.0, 102.0, 103.0, 104.0]
        sma = TechnicalIndicators.sma(closes, period=5)

        assert sma == 102.0  # Mean of [100, 101, 102, 103, 104]

    def test_sma_short_data(self):
        """SMA with insufficient data should use available"""
        closes = [100.0, 101.0]
        sma = TechnicalIndicators.sma(closes, period=5)

        assert sma == 100.5  # Mean of available

    def test_extract_closes(self):
        """Should extract closing prices from bars"""
        bars = [
            {"open": 100, "high": 102, "low": 99, "close": 101, "volume": 1000},
            {"open": 101, "high": 103, "low": 100, "close": 102, "volume": 1100},
        ]
        closes = TechnicalIndicators.extract_closes(bars)

        assert closes == [101, 102]


# ============================================================================
# TESTS FOR MultiTimeframeValidator
# ============================================================================

class TestMultiTimeframeValidator:
    """Tests for complete validator workflows"""

    @pytest.mark.asyncio
    async def test_validate_signal_with_confirmations(self):
        """Should validate signal with 2+ confirmations"""
        validator = MultiTimeframeValidator()

        # Mock the get_timeframe_signals method
        mock_analysis = MultiTimeframeAnalysis(
            "AAPL",
            {
                "5min": TimeframeSignal("5min", "AAPL", 25.0, 150.0, 145.0, 148.0, 1000.0),
                "30min": TimeframeSignal("30min", "AAPL", 28.0, 150.5, 145.5, 149.0, 2000.0),
                "day": TimeframeSignal("day", "AAPL", 50.0, 150.0, 150.0, 150.0, 3000.0),
            }
        )

        validator.get_timeframe_signals = AsyncMock(return_value=mock_analysis)

        is_valid = await validator.validate_signal("AAPL", "BUY", min_confirmations=2)
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_signal_insufficient_confirmations(self):
        """Should reject signal with < min_confirmations"""
        validator = MultiTimeframeValidator()

        mock_analysis = MultiTimeframeAnalysis(
            "AAPL",
            {
                "5min": TimeframeSignal("5min", "AAPL", 25.0, 150.0, 145.0, 148.0, 1000.0),
                "30min": TimeframeSignal("30min", "AAPL", 50.0, 150.5, 150.5, 149.0, 2000.0),
                "day": TimeframeSignal("day", "AAPL", 75.0, 149.0, 151.0, 150.0, 3000.0),
            }
        )

        validator.get_timeframe_signals = AsyncMock(return_value=mock_analysis)

        is_valid = await validator.validate_signal("AAPL", "BUY", min_confirmations=2)
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_confidence_score_calculation(self):
        """Should calculate confidence 0-100"""
        validator = MultiTimeframeValidator()

        mock_analysis = MultiTimeframeAnalysis(
            "AAPL",
            {
                "5min": TimeframeSignal("5min", "AAPL", 15.0, 150.0, 145.0, 148.0, 1000.0),  # Extreme RSI
                "30min": TimeframeSignal("30min", "AAPL", 28.0, 150.5, 145.5, 149.0, 2000.0),
                "day": TimeframeSignal("day", "AAPL", 50.0, 150.0, 150.0, 150.0, 3000.0),
            }
        )

        validator.get_timeframe_signals = AsyncMock(return_value=mock_analysis)

        confidence = await validator.confidence_score("AAPL", "BUY")
        assert 0 <= confidence <= 100
        assert confidence > 50  # 2 confirmations + extreme RSI bonus

    @pytest.mark.asyncio
    async def test_confidence_score_max_100(self):
        """Confidence should cap at 100"""
        validator = MultiTimeframeValidator()

        # All aligned + extreme RSI
        mock_analysis = MultiTimeframeAnalysis(
            "AAPL",
            {
                "5min": TimeframeSignal("5min", "AAPL", 15.0, 150.0, 145.0, 148.0, 1000.0),
                "30min": TimeframeSignal("30min", "AAPL", 18.0, 150.5, 145.5, 149.0, 2000.0),
                "day": TimeframeSignal("day", "AAPL", 20.0, 151.0, 146.0, 150.0, 3000.0),
            }
        )

        validator.get_timeframe_signals = AsyncMock(return_value=mock_analysis)

        confidence = await validator.confidence_score("AAPL", "BUY")
        assert confidence == 100

    @pytest.mark.asyncio
    async def test_invalid_signal_type(self):
        """Should reject invalid signal types"""
        validator = MultiTimeframeValidator()

        confidence = await validator.confidence_score("AAPL", "INVALID")
        assert confidence == 0

    @pytest.mark.asyncio
    async def test_get_last_analysis(self):
        """Should cache and return last analysis"""
        validator = MultiTimeframeValidator()

        # First call populates cache
        mock_analysis = MultiTimeframeAnalysis(
            "AAPL",
            {
                "5min": TimeframeSignal("5min", "AAPL", 25.0, 150.0, 145.0, 148.0, 1000.0),
            }
        )

        validator.get_timeframe_signals = AsyncMock(return_value=mock_analysis)
        await validator.get_timeframe_signals("AAPL")

        # Retrieve from cache
        cached = validator.get_last_analysis("AAPL")
        assert cached is not None
        assert cached.symbol == "AAPL"

    @pytest.mark.asyncio
    async def test_get_all_signals_multiple_symbols(self):
        """Should analyze multiple symbols in parallel"""
        validator = MultiTimeframeValidator()

        # Create mock analyses for each symbol
        mock_analyses = {
            "AAPL": MultiTimeframeAnalysis(
                "AAPL",
                {"5min": TimeframeSignal("5min", "AAPL", 25.0, 150.0, 145.0, 148.0, 1000.0)}
            ),
            "MSFT": MultiTimeframeAnalysis(
                "MSFT",
                {"5min": TimeframeSignal("5min", "MSFT", 75.0, 300.0, 305.0, 302.0, 2000.0)}
            ),
        }

        async def mock_get_signals(symbol):
            return mock_analyses[symbol]

        validator.get_timeframe_signals = mock_get_signals

        results = await validator.get_all_signals(["AAPL", "MSFT"])

        assert len(results) == 2
        assert results["AAPL"] is not None
        assert results["MSFT"] is not None


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """End-to-end integration tests"""

    def test_complete_workflow_buy_signal(self):
        """Complete workflow: Create signals and validate BUY"""
        # Create realistic signals
        signals = {
            "5min": TimeframeSignal("5min", "AAPL", 28.0, 150.0, 145.0, 148.0, 1000.0),
            "30min": TimeframeSignal("30min", "AAPL", 32.0, 150.5, 145.5, 149.0, 2000.0),
            "day": TimeframeSignal("day", "AAPL", 45.0, 151.0, 146.0, 150.0, 3000.0),
        }
        analysis = MultiTimeframeAnalysis("AAPL", signals)

        # Verify signals
        assert analysis.get_confirmation_count("BUY") == 2
        assert analysis.is_aligned("BUY") is False  # Not all 3
        assert analysis.get_strongest_signal() == ("BUY", 2)

    def test_complete_workflow_sell_signal(self):
        """Complete workflow: Create signals and validate SELL"""
        signals = {
            "5min": TimeframeSignal("5min", "MSFT", 72.0, 300.0, 305.0, 302.0, 1000.0),
            "30min": TimeframeSignal("30min", "MSFT", 75.0, 299.5, 304.5, 301.0, 2000.0),
            "day": TimeframeSignal("day", "MSFT", 55.0, 299.0, 304.0, 300.0, 3000.0),
        }
        analysis = MultiTimeframeAnalysis("MSFT", signals)

        # Verify signals
        assert analysis.get_confirmation_count("SELL") == 2
        assert analysis.get_strongest_signal() == ("SELL", 2)


# ============================================================================
# RUNNING TESTS
# ============================================================================

if __name__ == "__main__":
    # Run with: pytest test_multi_timeframe_validator.py -v
    pytest.main([__file__, "-v", "-s"])
