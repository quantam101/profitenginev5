import numpy as np
from decimal import Decimal
from typing import List, Dict
from sklearn.ensemble import RandomForestClassifier

try:
    from .models import (
        TechnicalSignal, MicrostructureSignal, RegimeSignal, PortfolioSignal,
        MarketRegime
    )
except ImportError:
    from models import (
        TechnicalSignal, MicrostructureSignal, RegimeSignal, PortfolioSignal,
        MarketRegime
    )

def calculate_rsi(prices, period=14):
    """Calculate RSI without talib."""
    if len(prices) < period + 1:
        return np.full_like(prices, 50.0)

    deltas = np.diff(prices)
    seed = deltas[:period]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    rs = up / down if down != 0 else 0
    rsi = np.full_like(prices, 0.0, dtype=float)
    rsi[period] = 100.0 - 100.0 / (1.0 + rs)

    for i in range(period + 1, len(prices)):
        delta = deltas[i - 1]
        up = (up * (period - 1) + (delta if delta > 0 else 0)) / period
        down = (down * (period - 1) + (-delta if delta < 0 else 0)) / period
        rs = up / down if down != 0 else 0
        rsi[i] = 100.0 - 100.0 / (1.0 + rs)

    return rsi

def calculate_macd(prices, fast=12, slow=26, signal_period=9):
    """Calculate MACD without talib."""
    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)
    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, signal_period)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def calculate_ema(prices, timeperiod=None, period=None):
    """Calculate EMA."""
    p = timeperiod if timeperiod is not None else (period if period is not None else 12)
    ema = np.full_like(prices, np.nan, dtype=float)
    sma = np.mean(prices[:p])
    ema[p-1] = sma
    multiplier = 2.0 / (p + 1)
    for i in range(p, len(prices)):
        ema[i] = prices[i] * multiplier + ema[i-1] * (1 - multiplier)
    return ema

def calculate_sma(prices, timeperiod=None, period=None):
    """Calculate SMA."""
    p = timeperiod if timeperiod is not None else (period if period is not None else 20)
    return np.convolve(prices, np.ones(p)/p, mode='same')

class TechnicalAgent:
    def __init__(self, config: Dict):
        self.rsi_period = config.get('rsi_period', 14)
        self.rsi_oversold = config.get('rsi_oversold_threshold', 35)
        self.macd_fast = config.get('macd_fast', 12)
        self.macd_slow = config.get('macd_slow', 26)
        self.macd_signal = config.get('macd_signal', 9)
        self.confidence_min = config.get('confidence_min', 0.65)

    def analyze(self, prices: np.ndarray, volumes: np.ndarray) -> TechnicalSignal:
        if len(prices) < max(self.macd_slow, self.rsi_period) + 1:
            return TechnicalSignal(
                rsi_oversold_recovery=0.0,
                macd_bullish_cross=0.0,
                support_bounce=0.0,
                trend_alignment=0.0,
                pattern_score=0.0,
                confidence=0.0
            )

        prices_arr = np.array(prices, dtype=float)

        # RSI
        rsi = calculate_rsi(prices_arr, period=self.rsi_period)
        current_rsi = rsi[-1]

        # RSI recovery: was oversold, now bouncing up
        rsi_recovery = 1.0 if (current_rsi > self.rsi_oversold and
                               rsi[-2] < current_rsi) else 0.5

        # MACD
        macd, signal, hist = calculate_macd(
            prices_arr,
            fast=self.macd_fast,
            slow=self.macd_slow,
            signal_period=self.macd_signal
        )
        current_macd_hist = hist[-1]
        macd_bullish = 1.0 if current_macd_hist > 0 else 0.0

        # Trend
        sma_20 = calculate_sma(prices_arr, timeperiod=20)
        sma_50 = calculate_sma(prices_arr, timeperiod=50)
        trend_alignment = 1.0 if (sma_20[-1] > sma_50[-1] and
                                  prices_arr[-1] > sma_20[-1]) else 0.0

        # Support bounce
        min_price = np.min(prices_arr[-20:])
        support_bounce = max(0.0, (prices_arr[-1] - min_price) / (prices_arr[-1] + 1e-6))

        # Pattern score (simplified: price above EMA)
        ema_12 = calculate_ema(prices_arr, timeperiod=12)
        pattern_score = 1.0 if prices_arr[-1] > ema_12[-1] else 0.5

        # Aggregate confidence
        confidence = np.mean([rsi_recovery, macd_bullish, trend_alignment,
                             support_bounce, pattern_score])

        return TechnicalSignal(
            rsi_oversold_recovery=float(rsi_recovery),
            macd_bullish_cross=float(macd_bullish),
            support_bounce=float(support_bounce),
            trend_alignment=float(trend_alignment),
            pattern_score=float(pattern_score),
            confidence=float(confidence)
        )

class MicrostructureAgent:
    def __init__(self, config: Dict):
        self.depth_levels = config.get('liquidity_depth_levels', 5)
        self.imbalance_threshold = config.get('imbalance_threshold', 0.2)
        self.confidence_min = config.get('confidence_min', 0.60)

    def analyze(self, orderbook: Dict, trade_flow: List[Dict]) -> MicrostructureSignal:
        bids = np.array(orderbook.get('bids', []), dtype=float)
        asks = np.array(orderbook.get('asks', []), dtype=float)

        if len(bids) == 0 or len(asks) == 0:
            return MicrostructureSignal(
                bid_ask_imbalance=0.0,
                smart_money_flow=0.0,
                liquidity_score=0.0,
                front_running_risk=0.0,
                time_to_fill=60.0,
                confidence=0.0
            )

        # Bid-ask imbalance
        bid_vol = np.sum(bids[:self.depth_levels, 1]) if len(bids) >= self.depth_levels else np.sum(bids[:, 1])
        ask_vol = np.sum(asks[:self.depth_levels, 1]) if len(asks) >= self.depth_levels else np.sum(asks[:, 1])
        imbalance = (bid_vol - ask_vol) / (bid_vol + ask_vol + 1e-6)

        # Smart money detection (simplified)
        large_orders = sum(1 for order in trade_flow if order.get('size', 0) > 1000)
        smart_money = min(1.0, large_orders / max(1, len(trade_flow)))

        # Liquidity score (bid-ask spread relative to price)
        spread = (float(asks[0, 0]) - float(bids[0, 0])) / float(bids[0, 0]) if len(bids) > 0 else 0.1
        liquidity = max(0.0, 1.0 - (spread * 1000))  # Convert to bps equivalent

        # Front-running risk (rising ask side)
        ask_trend = asks[0, 0] - asks[min(1, len(asks)-1), 0] if len(asks) > 1 else 0
        front_running_risk = max(0.0, ask_trend / (asks[0, 0] + 1e-6))

        # Time to fill (simplified: based on top-level volume)
        time_to_fill = 5.0 if bid_vol > 50000 else 15.0

        confidence = np.mean([abs(imbalance), liquidity, smart_money])

        return MicrostructureSignal(
            bid_ask_imbalance=float(imbalance),
            smart_money_flow=float(smart_money),
            liquidity_score=float(liquidity),
            front_running_risk=float(front_running_risk),
            time_to_fill=float(time_to_fill),
            confidence=float(confidence)
        )

class RegimeAgent:
    def __init__(self, config: Dict):
        self.vol_threshold = config.get('volatility_percentile_threshold', 60)
        self.event_risk_max = config.get('event_risk_max', 0.3)
        self.correlation_stress = config.get('correlation_stress_threshold', 0.4)

    def analyze(self, prices: np.ndarray, volatility: float,
                market_state: Dict) -> RegimeSignal:
        prices_arr = np.array(prices, dtype=float)

        if len(prices_arr) < 20:
            return RegimeSignal(
                regime=MarketRegime.NO_TRADE,
                volatility_level=0.0,
                event_risk=0.5,
                correlation_stress=0.0,
                regime_confidence=0.0,
                approved_to_trade=False
            )

        # Volatility regime
        returns = np.diff(np.log(prices_arr))
        rolling_vol = np.std(returns[-20:]) * np.sqrt(252) * 100
        vol_percentile = min(100.0, rolling_vol * 10)

        # Trend
        sma_50 = calculate_sma(prices_arr, timeperiod=50)
        if sma_50[-1] > 0:
            trend_up = prices_arr[-1] > sma_50[-1]
        else:
            trend_up = False

        # Regime classification
        if rolling_vol > 30:
            regime = MarketRegime.HIGH_VOLATILITY
        elif trend_up:
            regime = MarketRegime.BULL_TRENDING if volatility < 15 else MarketRegime.BULL_CONSOLIDATING
        else:
            regime = MarketRegime.BEAR_TRENDING if volatility < 15 else MarketRegime.BEAR_CONSOLIDATING

        # Event risk (simplified: check market state)
        event_risk = market_state.get('event_risk', 0.0)

        # Correlation stress
        corr_stress = market_state.get('correlation_stress', 0.0)

        # Approval to trade
        approved = (regime != MarketRegime.NO_TRADE and
                   event_risk < self.event_risk_max and
                   corr_stress < self.correlation_stress)

        return RegimeSignal(
            regime=regime,
            volatility_level=float(vol_percentile),
            event_risk=float(event_risk),
            correlation_stress=float(corr_stress),
            regime_confidence=0.85,
            approved_to_trade=approved
        )

class PortfolioAgent:
    def __init__(self, config: Dict):
        self.kelly_fraction = config.get('kelly_fraction', 0.25)
        self.max_correlation = config.get('max_correlated_exposure', 0.7)
        self.max_daily_loss = Decimal(str(config.get('max_daily_loss_usd', 200)))

    def analyze(self, open_positions: List[Dict], proposed_trade: Dict,
                account_equity: Decimal, daily_pnl: Decimal) -> PortfolioSignal:

        # Kelly sizing (simplified)
        win_rate = proposed_trade.get('win_rate', 0.45)
        avg_win = proposed_trade.get('avg_win_pct', 0.04)
        avg_loss = proposed_trade.get('avg_loss_pct', 0.02)

        kelly = ((win_rate * avg_win) - ((1 - win_rate) * avg_loss)) / avg_win if avg_win > 0 else 0.01
        kelly_fraction = max(0.01, min(self.kelly_fraction, kelly))
        position_size = float(kelly_fraction)

        # Correlation (simplified: count existing positions)
        corr_load = min(self.max_correlation, len(open_positions) * 0.25)

        # Drawdown forecast (simplified)
        worst_case = float(-account_equity * Decimal('0.05'))

        # Risk budget
        risk_budget = 1.0 - float(abs(daily_pnl) / self.max_daily_loss) if self.max_daily_loss > 0 else 1.0

        # Recommendation
        if risk_budget < 0.2:
            action = "SKIP"
        elif corr_load > self.max_correlation:
            action = "SCALE_DOWN"
        else:
            action = "SCALE_UP" if position_size < 0.05 else "NORMAL"

        return PortfolioSignal(
            position_size_kelly=float(position_size),
            max_correlated_exposure=float(corr_load),
            drawdown_forecast=float(worst_case),
            risk_budget_remaining=float(max(0.0, risk_budget)),
            recommended_action=action
        )
