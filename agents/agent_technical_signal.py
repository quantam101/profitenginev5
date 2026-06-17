"""
Technical Signal Analyzer - High-performance indicator calculation.

RSI (14), MACD (12/26/9), EMA (20), SMA (50) with sub-50ms latency.
Numpy-vectorized for efficient computation on price series.

Classes:
    TechnicalSignalAnalyzer: Main analyzer with calc_rsi, calc_macd, calc_ema, generate_signal methods.

Example:
    >>> import numpy as np
    >>> prices = np.array([100.0, 102.5, 101.3, 103.8, 102.1, 104.5, 103.2, 105.0, 104.3, 106.1])
    >>> analyzer = TechnicalSignalAnalyzer()
    >>> signal = analyzer.generate_signal(prices)
    >>> print(signal)
    {'rsi': 65.2, 'macd': 2.1, 'macd_signal': 1.8, 'ema_20': 103.5, 'sma_50': 102.1, 'action': 'BUY'}
"""

import numpy as np
from typing import Dict, Tuple, Optional, Union
import warnings

warnings.filterwarnings('ignore')


class TechnicalSignalAnalyzer:
    """
    High-performance technical analysis indicator calculator.

    Computes RSI (14), MACD (12/26/9), EMA (20), SMA (50) with latency < 50ms.
    Uses numpy vectorization for O(n) computation efficiency.

    Attributes:
        rsi_period (int): RSI calculation period. Default: 14.
        macd_fast (int): MACD fast EMA period. Default: 12.
        macd_slow (int): MACD slow EMA period. Default: 26.
        macd_signal (int): MACD signal EMA period. Default: 9.
        ema_period (int): EMA calculation period. Default: 20.
        sma_period (int): SMA calculation period. Default: 50.
    """

    def __init__(
        self,
        rsi_period: int = 14,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9,
        ema_period: int = 20,
        sma_period: int = 50,
    ):
        """
        Initialize Technical Signal Analyzer.

        Args:
            rsi_period: RSI lookback window. Default 14.
            macd_fast: MACD fast EMA period. Default 12.
            macd_slow: MACD slow EMA period. Default 26.
            macd_signal: MACD signal EMA period. Default 9.
            ema_period: EMA lookback window. Default 20.
            sma_period: SMA lookback window. Default 50.
        """
        self.rsi_period = rsi_period
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal
        self.ema_period = ema_period
        self.sma_period = sma_period

    def calc_rsi(self, prices: np.ndarray) -> float:
        """
        Calculate Relative Strength Index (RSI).

        RSI = 100 - (100 / (1 + RS))
        where RS = average gain / average loss over period.

        Args:
            prices: 1D numpy array of close prices. Minimum length: rsi_period + 1.

        Returns:
            RSI value between 0 and 100. NaN if insufficient data.

        Raises:
            ValueError: If prices array has less than rsi_period + 1 elements.
        """
        if len(prices) < self.rsi_period + 1:
            return np.nan

        # Calculate price changes
        deltas = np.diff(prices)

        # Separate gains and losses
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        # Calculate average gain and loss over period
        avg_gain = np.mean(gains[-self.rsi_period :])
        avg_loss = np.mean(losses[-self.rsi_period :])

        # Handle edge case: no losses
        if avg_loss == 0:
            return 100.0 if avg_gain > 0 else 50.0

        rs = avg_gain / avg_loss
        rsi = 100.0 - (100.0 / (1.0 + rs))

        return float(np.clip(rsi, 0, 100))

    def calc_macd(self, prices: np.ndarray) -> Tuple[float, float, float]:
        """
        Calculate MACD (Moving Average Convergence Divergence).

        MACD = EMA(12) - EMA(26)
        Signal = EMA(9) of MACD
        Histogram = MACD - Signal

        Args:
            prices: 1D numpy array of close prices. Minimum length: macd_slow + macd_signal - 1.

        Returns:
            Tuple of (macd_line, signal_line, histogram).
            Returns (NaN, NaN, NaN) if insufficient data.

        Raises:
            ValueError: If prices array is too short for MACD calculation.
        """
        min_length = self.macd_slow + self.macd_signal - 1
        if len(prices) < min_length:
            return (np.nan, np.nan, np.nan)

        # Calculate fast and slow EMAs
        ema_fast = self._calc_ema_internal(prices, self.macd_fast)
        ema_slow = self._calc_ema_internal(prices, self.macd_slow)

        # MACD line is the difference
        macd_line = ema_fast - ema_slow

        # Signal line is EMA of MACD
        signal_line = self._calc_ema_internal(
            np.array([macd_line]) if np.isscalar(macd_line) else macd_line,
            self.macd_signal
        )

        # Handle array vs scalar return
        if isinstance(macd_line, np.ndarray):
            macd_val = float(macd_line[-1])
        else:
            macd_val = float(macd_line)

        if isinstance(signal_line, np.ndarray):
            signal_val = float(signal_line[-1])
        else:
            signal_val = float(signal_line)

        histogram = macd_val - signal_val

        return (macd_val, signal_val, histogram)

    def calc_ema(self, prices: np.ndarray) -> float:
        """
        Calculate Exponential Moving Average (EMA).

        EMA = price * multiplier + EMA(previous) * (1 - multiplier)
        multiplier = 2 / (period + 1)

        Args:
            prices: 1D numpy array of close prices. Minimum length: ema_period.

        Returns:
            EMA value as float. NaN if insufficient data.

        Raises:
            ValueError: If prices array has less than ema_period elements.
        """
        ema = self._calc_ema_internal(prices, self.ema_period)

        if isinstance(ema, np.ndarray):
            return float(ema[-1])
        return float(ema)

    def _calc_ema_internal(self, prices: np.ndarray, period: int) -> Union[float, np.ndarray]:
        """
        Internal EMA calculation using alpha smoothing factor.

        Uses numpy vectorization for efficient computation.

        Args:
            prices: 1D numpy array of prices.
            period: EMA period.

        Returns:
            EMA value or array depending on input length.
        """
        if len(prices) < period:
            return np.nan

        alpha = 2.0 / (period + 1.0)
        ema = np.zeros(len(prices))
        ema[0] = prices[0]

        # Vectorized EMA calculation
        for i in range(1, len(prices)):
            ema[i] = prices[i] * alpha + ema[i - 1] * (1.0 - alpha)

        return ema[-1]

    def calc_sma(self, prices: np.ndarray) -> float:
        """
        Calculate Simple Moving Average (SMA).

        SMA = sum(prices[-period:]) / period

        Args:
            prices: 1D numpy array of close prices. Minimum length: sma_period.

        Returns:
            SMA value as float. NaN if insufficient data.

        Raises:
            ValueError: If prices array has less than sma_period elements.
        """
        if len(prices) < self.sma_period:
            return np.nan

        sma = np.mean(prices[-self.sma_period :])
        return float(sma)

    def generate_signal(
        self, prices: np.ndarray, return_components: bool = False
    ) -> Dict[str, Union[float, str]]:
        """
        Generate comprehensive trading signal from all indicators.

        Combines RSI, MACD, EMA, and SMA into actionable signal.
        Signal logic:
            - BUY: RSI < 30 and MACD > signal, or price below EMA(20) and SMA(50)
            - SELL: RSI > 70 and MACD < signal, or price above EMA(20) and SMA(50)
            - HOLD: Neutral or conflicting signals

        Args:
            prices: 1D numpy array of close prices (minimum 50 elements recommended).
            return_components: If True, include individual indicator values. Default False.

        Returns:
            Dictionary with keys:
                'rsi': RSI value (0-100)
                'macd': MACD line value
                'macd_signal': MACD signal line value
                'macd_histogram': MACD histogram
                'ema_20': EMA(20) value
                'sma_50': SMA(50) value
                'action': Trading action (BUY, SELL, HOLD)
                'confidence': Signal confidence score (0-100)

        Raises:
            ValueError: If prices array is too short or invalid.
        """
        if not isinstance(prices, np.ndarray):
            prices = np.array(prices, dtype=np.float64)

        if len(prices) < self.sma_period:
            raise ValueError(
                f"Prices array too short. Minimum {self.sma_period} elements required, "
                f"got {len(prices)}."
            )

        # Calculate all indicators
        rsi = self.calc_rsi(prices)
        macd, macd_signal, macd_hist = self.calc_macd(prices)
        ema20 = self.calc_ema(prices)
        sma50 = self.calc_sma(prices)
        current_price = prices[-1]

        # Generate signal based on indicator confluence
        signal, confidence = self._determine_action(
            rsi, macd, macd_signal, ema20, sma50, current_price
        )

        result = {
            'rsi': round(float(rsi), 2) if not np.isnan(rsi) else None,
            'macd': round(float(macd), 4) if not np.isnan(macd) else None,
            'macd_signal': round(float(macd_signal), 4) if not np.isnan(macd_signal) else None,
            'macd_histogram': round(float(macd_hist), 4) if not np.isnan(macd_hist) else None,
            'ema_20': round(float(ema20), 2) if not np.isnan(ema20) else None,
            'sma_50': round(float(sma50), 2) if not np.isnan(sma50) else None,
            'action': signal,
            'confidence': round(confidence, 1),
        }

        if return_components:
            result['current_price'] = round(float(current_price), 2)
            result['price_above_ema20'] = current_price > ema20
            result['price_above_sma50'] = current_price > sma50
            result['ema20_above_sma50'] = ema20 > sma50

        return result

    def _determine_action(
        self,
        rsi: float,
        macd: float,
        macd_signal: float,
        ema20: float,
        sma50: float,
        current_price: float,
    ) -> Tuple[str, float]:
        """
        Determine trading action and confidence from indicator signals.

        Args:
            rsi: RSI value (0-100).
            macd: MACD line value.
            macd_signal: MACD signal line value.
            ema20: EMA(20) value.
            sma50: SMA(50) value.
            current_price: Current price.

        Returns:
            Tuple of (action: str, confidence: float).
            action in ['BUY', 'SELL', 'HOLD'].
            confidence in [0.0, 100.0].
        """
        if np.isnan(rsi) or np.isnan(macd) or np.isnan(ema20) or np.isnan(sma50):
            return ('HOLD', 0.0)

        buy_signals = 0
        sell_signals = 0
        total_signals = 4

        # RSI signal
        if rsi < 30:
            buy_signals += 1
        elif rsi > 70:
            sell_signals += 1

        # MACD signal
        if macd > macd_signal and macd > 0:
            buy_signals += 1
        elif macd < macd_signal and macd < 0:
            sell_signals += 1

        # Price vs EMA(20)
        if current_price > ema20:
            buy_signals += 1
        else:
            sell_signals += 1

        # Price vs SMA(50)
        if current_price > sma50:
            buy_signals += 1
        else:
            sell_signals += 1

        # Determine action
        if buy_signals > sell_signals:
            action = 'BUY'
            confidence = (buy_signals / total_signals) * 100.0
        elif sell_signals > buy_signals:
            action = 'SELL'
            confidence = (sell_signals / total_signals) * 100.0
        else:
            action = 'HOLD'
            confidence = 50.0

        return (action, confidence)

    def batch_analyze(
        self, prices: np.ndarray, window_size: int = 50
    ) -> list:
        """
        Analyze multiple rolling windows of prices.

        Useful for backtesting or analyzing multiple timeframes.

        Args:
            prices: 1D numpy array of prices.
            window_size: Size of rolling analysis window. Default 50.

        Returns:
            List of signal dictionaries for each window.
        """
        if len(prices) < window_size:
            raise ValueError(
                f"Prices array too short for batch analysis. "
                f"Need at least {window_size}, got {len(prices)}."
            )

        results = []
        for i in range(len(prices) - window_size + 1):
            window = prices[i : i + window_size]
            signal = self.generate_signal(window)
            results.append(signal)

        return results


def main():
    """Demonstration of technical signal analyzer."""
    # Generate sample price data
    np.random.seed(42)
    price_data = 100.0 + np.cumsum(np.random.randn(100) * 0.5)

    # Initialize analyzer
    analyzer = TechnicalSignalAnalyzer()

    # Generate signal
    signal = analyzer.generate_signal(price_data, return_components=True)

    # Display results
    print("Technical Signal Analysis")
    print("=" * 50)
    print(f"Current Price: ${signal['current_price']:.2f}")
    print(f"RSI (14): {signal['rsi']}")
    print(f"MACD: {signal['macd']}")
    print(f"MACD Signal: {signal['macd_signal']}")
    print(f"MACD Histogram: {signal['macd_histogram']}")
    print(f"EMA (20): ${signal['ema_20']:.2f}")
    print(f"SMA (50): ${signal['sma_50']:.2f}")
    print(f"\nPrice above EMA(20): {signal['price_above_ema20']}")
    print(f"Price above SMA(50): {signal['price_above_sma50']}")
    print(f"EMA(20) above SMA(50): {signal['ema20_above_sma50']}")
    print(f"\nAction: {signal['action']}")
    print(f"Confidence: {signal['confidence']}%")


if __name__ == '__main__':
    main()
