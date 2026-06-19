"""
DYNAMIC RISK MANAGEMENT
ProfitEngine v5 Risk Management Engine

Provides ATR-based position sizing, stop-loss, and take-profit calculations
with volatility-aware adjustments using IV rank percentile.

Features:
- calculate_stop_loss() - ATR-based stop loss with direction support
- calculate_take_profit() - ATR-based profit targets
- calculate_position_size() - Risk-based position sizing with max limits
- get_volatility_adjustment() - IV rank multiplier (0.5x to 2.0x)

Risk Constraints:
- Max single position: $5,000
- Max concurrent positions: $15,000
- Default risk per trade: 2% of account
- ATR period: 14 candles (5-minute bars)
"""

import logging
import math
from typing import Optional, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class RiskMetrics:
    """Complete risk profile for a potential trade"""
    symbol: str
    entry_price: float
    direction: str  # LONG or SHORT
    stop_price: float
    target_price: float
    position_size: int  # number of shares
    position_value: float  # entry_price * position_size
    risk_amount: float  # entry_price - stop (LONG) or stop - entry (SHORT)
    reward_amount: float  # target - entry (LONG) or entry - target (SHORT)
    risk_reward_ratio: float
    atr_value: float
    iv_rank: float
    volatility_multiplier: float
    max_loss_usd: float
    max_gain_usd: float
    timestamp: str

    def __repr__(self):
        return (
            f"RiskMetrics({self.symbol} {self.direction} @ {self.entry_price:.2f}) "
            f"Stop: {self.stop_price:.2f}, Target: {self.target_price:.2f}, "
            f"Size: {self.position_size} shares (${self.position_value:.2f}), "
            f"RR: {self.risk_reward_ratio:.2f}:1"
        )


@dataclass
class VolatilityContext:
    """Market volatility snapshot for a symbol"""
    symbol: str
    atr_14: float  # 14-period Average True Range
    iv_rank: float  # 0-100, percentile of IV
    historical_volatility: float  # annualized std dev
    volatility_multiplier: float  # 0.5 to 2.0
    last_updated: str


# ============================================================================
# ATR CALCULATION
# ============================================================================

def calculate_atr(
    high_prices: list,
    low_prices: list,
    close_prices: list,
    period: int = 14
) -> float:
    """
    Calculate Average True Range (ATR) from OHLC data.

    Args:
        high_prices: List of high prices (oldest first)
        low_prices: List of low prices (oldest first)
        close_prices: List of close prices (oldest first)
        period: ATR lookback period (default 14)

    Returns:
        ATR value (float)

    Notes:
        - Requires at least period + 1 data points
        - True Range = max(H-L, |H-PC|, |L-PC|)
        - ATR = SMA of True Range over period
    """
    if len(high_prices) < period + 1 or len(close_prices) < period + 1:
        logger.warning(f"Insufficient data for ATR calc: have {len(high_prices)}, need {period + 1}")
        return 0.0

    true_ranges = []
    for i in range(1, len(high_prices)):
        h = high_prices[i]
        l = low_prices[i]
        pc = close_prices[i - 1]

        tr = max(
            h - l,  # high - low
            abs(h - pc),  # high - previous close
            abs(l - pc)  # low - previous close
        )
        true_ranges.append(tr)

    # Calculate SMA of true ranges
    if len(true_ranges) < period:
        return sum(true_ranges) / len(true_ranges)

    atr = sum(true_ranges[-period:]) / period
    return max(atr, 0.01)  # Ensure minimum ATR


def estimate_atr_from_volatility(
    entry_price: float,
    historical_volatility: float
) -> float:
    """
    Estimate ATR from historical volatility when candle data unavailable.

    Args:
        entry_price: Current price level
        historical_volatility: Annualized volatility (e.g., 0.25 = 25%)

    Returns:
        Estimated ATR value

    Notes:
        - ATR approximation: (daily_volatility * price)
        - daily_volatility ≈ annual_volatility / sqrt(252)
        - 5-min candles: multiply by sqrt(78) for typical trading day
    """
    if historical_volatility <= 0:
        return entry_price * 0.02  # Default 2% if unknown

    daily_volatility = historical_volatility / math.sqrt(252)
    five_min_volatility = daily_volatility * math.sqrt(78)  # 78 = 5-min bars per day
    atr_estimate = entry_price * five_min_volatility

    return max(atr_estimate, 0.01)


# ============================================================================
# VOLATILITY ADJUSTMENTS
# ============================================================================

def get_volatility_adjustment(
    iv_rank: float,
    base_atr: float,
    min_multiplier: float = 0.5,
    max_multiplier: float = 2.0
) -> Tuple[float, str]:
    """
    Calculate volatility-based ATR multiplier for stop/target calculations.

    Args:
        iv_rank: IV percentile (0-100, where 100 = highest volatility)
        base_atr: Base ATR value for context
        min_multiplier: Minimum allowed multiplier (default 0.5x)
        max_multiplier: Maximum allowed multiplier (default 2.0x)

    Returns:
        (multiplier: float, regime: str)
        - multiplier: 0.5 to 2.0 based on volatility
        - regime: "low", "normal", "elevated", or "extreme"

    Rules:
        - IV rank < 25: tighten stops (0.5x to 0.8x) → "low" vol
        - IV rank 25-50: normal (0.9x to 1.0x) → "normal" vol
        - IV rank 50-75: elevated (1.1x to 1.3x) → "elevated" vol
        - IV rank > 75: loosen stops (1.4x to 2.0x) → "extreme" vol
    """
    if iv_rank < 0 or iv_rank > 100:
        logger.warning(f"Invalid IV rank {iv_rank}, clamping to [0, 100]")
        iv_rank = max(0, min(100, iv_rank))

    if iv_rank < 25:
        # Low volatility: tighten stops
        multiplier = min_multiplier + (iv_rank / 25) * (0.8 - min_multiplier)
        regime = "low"
    elif iv_rank < 50:
        # Normal volatility
        t = (iv_rank - 25) / 25
        multiplier = 0.8 + t * (1.0 - 0.8)
        regime = "normal"
    elif iv_rank < 75:
        # Elevated volatility
        t = (iv_rank - 50) / 25
        multiplier = 1.0 + t * (1.3 - 1.0)
        regime = "elevated"
    else:
        # Extreme volatility: loosen stops
        t = (iv_rank - 75) / 25
        multiplier = 1.3 + t * (max_multiplier - 1.3)
        regime = "extreme"

    return min(multiplier, max_multiplier), regime


def normalize_iv_rank(
    current_iv: float,
    iv_52week_low: float,
    iv_52week_high: float
) -> float:
    """
    Normalize IV to percentile rank (0-100).

    Args:
        current_iv: Current IV value
        iv_52week_low: 52-week low IV
        iv_52week_high: 52-week high IV

    Returns:
        IV rank percentile (0-100)

    Notes:
        - If range is zero, returns 50 (middle of range)
        - Clamps result to [0, 100]
    """
    iv_range = iv_52week_high - iv_52week_low
    if iv_range == 0:
        return 50.0

    iv_rank = ((current_iv - iv_52week_low) / iv_range) * 100
    return max(0, min(100, iv_rank))


# ============================================================================
# STOP LOSS CALCULATION
# ============================================================================

def calculate_stop_loss(
    symbol: str,
    entry_price: float,
    direction: str = "LONG",
    atr_value: float = None,
    atr_multiplier: float = 1.5,
    volatility_multiplier: float = 1.0,
    high_prices: list = None,
    low_prices: list = None,
    close_prices: list = None,
) -> float:
    """
    Calculate ATR-based stop-loss price.

    Args:
        symbol: Ticker symbol
        entry_price: Entry price for the trade
        direction: "LONG" or "SHORT"
        atr_value: Pre-calculated ATR (if None, estimated from volatility)
        atr_multiplier: Stop distance multiplier (default 1.5x ATR)
        volatility_multiplier: Volatility adjustment factor (0.5x to 2.0x)
        high_prices: List of recent high prices (for ATR calc)
        low_prices: List of recent low prices (for ATR calc)
        close_prices: List of recent close prices (for ATR calc)

    Returns:
        Stop-loss price (float)

    Logic:
        LONG:  stop = entry - (ATR × multiplier × vol_adj)
        SHORT: stop = entry + (ATR × multiplier × vol_adj)
    """
    # Calculate or use provided ATR
    if atr_value is None:
        if high_prices and low_prices and close_prices:
            atr_value = calculate_atr(high_prices, low_prices, close_prices, period=14)
        else:
            # Fallback: estimate from entry price
            atr_value = entry_price * 0.02  # 2% as default

    logger.info(
        f"[{symbol}] calculate_stop_loss: "
        f"entry={entry_price:.2f}, direction={direction}, "
        f"atr={atr_value:.2f}, vol_adj={volatility_multiplier:.2f}"
    )

    # Apply volatility adjustment to ATR
    adjusted_atr = atr_value * atr_multiplier * volatility_multiplier

    if direction.upper() == "LONG":
        stop_price = entry_price - adjusted_atr
    elif direction.upper() == "SHORT":
        stop_price = entry_price + adjusted_atr
    else:
        raise ValueError(f"Invalid direction: {direction}. Use 'LONG' or 'SHORT'.")

    # Ensure stop price is reasonable
    stop_price = max(stop_price, 0.01)
    return round(stop_price, 2)


# ============================================================================
# TAKE PROFIT CALCULATION
# ============================================================================

def calculate_take_profit(
    symbol: str,
    entry_price: float,
    direction: str = "LONG",
    atr_value: float = None,
    atr_multiplier: float = 2.5,
    volatility_multiplier: float = 1.0,
    high_prices: list = None,
    low_prices: list = None,
    close_prices: list = None,
) -> float:
    """
    Calculate ATR-based take-profit target.

    Args:
        symbol: Ticker symbol
        entry_price: Entry price for the trade
        direction: "LONG" or "SHORT"
        atr_value: Pre-calculated ATR (if None, estimated from volatility)
        atr_multiplier: Target distance multiplier (default 2.5x ATR)
        volatility_multiplier: Volatility adjustment factor (0.5x to 2.0x)
        high_prices: List of recent high prices (for ATR calc)
        low_prices: List of recent low prices (for ATR calc)
        close_prices: List of recent close prices (for ATR calc)

    Returns:
        Take-profit price (float)

    Logic:
        LONG:  target = entry + (ATR × multiplier × vol_adj)
        SHORT: target = entry - (ATR × multiplier × vol_adj)
    """
    # Calculate or use provided ATR
    if atr_value is None:
        if high_prices and low_prices and close_prices:
            atr_value = calculate_atr(high_prices, low_prices, close_prices, period=14)
        else:
            # Fallback: estimate from entry price
            atr_value = entry_price * 0.02  # 2% as default

    logger.info(
        f"[{symbol}] calculate_take_profit: "
        f"entry={entry_price:.2f}, direction={direction}, "
        f"atr={atr_value:.2f}, vol_adj={volatility_multiplier:.2f}"
    )

    # Apply volatility adjustment to ATR
    adjusted_atr = atr_value * atr_multiplier * volatility_multiplier

    if direction.upper() == "LONG":
        target_price = entry_price + adjusted_atr
    elif direction.upper() == "SHORT":
        target_price = entry_price - adjusted_atr
    else:
        raise ValueError(f"Invalid direction: {direction}. Use 'LONG' or 'SHORT'.")

    # Ensure target is reasonable
    target_price = max(target_price, 0.01)
    return round(target_price, 2)


# ============================================================================
# POSITION SIZING
# ============================================================================

def calculate_position_size(
    symbol: str,
    account_balance: float,
    entry_price: float,
    stop_price: float,
    risk_percent: float = 2.0,
    max_single_position: float = 5000.0,
    max_concurrent_value: float = 15000.0,
    current_positions_value: float = 0.0,
) -> Dict[str, float]:
    """
    Calculate position size based on risk management rules.

    Args:
        symbol: Ticker symbol
        account_balance: Total account balance (USD)
        entry_price: Entry price per share
        stop_price: Stop-loss price per share
        risk_percent: Risk per trade as % of account (default 2%)
        max_single_position: Max USD value per single position (default $5,000)
        max_concurrent_value: Max total USD value of concurrent positions (default $15,000)
        current_positions_value: Current value of open positions (USD)

    Returns:
        Dict with keys:
            - shares: Number of shares to buy/sell
            - position_value: Total value of position (entry_price × shares)
            - risk_amount: USD amount at risk (if stop is hit)
            - max_loss: Maximum possible loss on position
            - available_for_concurrent: Remaining concurrent position capacity
            - limited_by: Reason for final sizing ("account_balance", "max_position",
                         "concurrent_limit", "risk_percent", or "none")

    Logic:
        1. Risk amount = account_balance × risk_percent
        2. Share size = risk_amount / |entry - stop|
        3. Position value = entry_price × shares
        4. Apply position limits and concurrent limits
        5. Return final safe sizing
    """
    risk_amount = account_balance * (risk_percent / 100)
    price_risk_per_share = abs(entry_price - stop_price)

    if price_risk_per_share <= 0:
        logger.error(f"[{symbol}] Invalid stop price: entry={entry_price}, stop={stop_price}")
        return {
            "shares": 0,
            "position_value": 0.0,
            "risk_amount": 0.0,
            "max_loss": 0.0,
            "available_for_concurrent": max_concurrent_value - current_positions_value,
            "limited_by": "invalid_stop_price"
        }

    # Calculate initial share size from risk
    shares = int(risk_amount / price_risk_per_share)
    position_value = entry_price * shares
    limited_by = None

    # Limit 1: Maximum single position
    if position_value > max_single_position:
        shares = int(max_single_position / entry_price)
        position_value = entry_price * shares
        limited_by = "max_position"
        logger.info(f"[{symbol}] Position limited by max_single_position: {shares} shares")

    # Limit 2: Concurrent positions
    available_concurrent = max_concurrent_value - current_positions_value
    if position_value > available_concurrent:
        shares = int(available_concurrent / entry_price)
        position_value = entry_price * shares
        limited_by = "concurrent_limit"
        logger.info(f"[{symbol}] Position limited by concurrent_limit: {shares} shares")

    # Limit 3: Account balance
    if position_value > account_balance:
        shares = int(account_balance / entry_price)
        position_value = entry_price * shares
        limited_by = "account_balance"
        logger.warning(f"[{symbol}] Position limited by account_balance: {shares} shares")

    max_loss = abs(price_risk_per_share * shares)
    actual_risk_amount = min(risk_amount, max_loss)

    if limited_by is None:
        limited_by = "none"

    return {
        "shares": max(0, shares),
        "position_value": position_value,
        "risk_amount": actual_risk_amount,
        "max_loss": max_loss,
        "available_for_concurrent": max(0, available_concurrent - position_value),
        "limited_by": limited_by
    }


# ============================================================================
# COMPLETE RISK PROFILE
# ============================================================================

def create_risk_profile(
    symbol: str,
    entry_price: float,
    account_balance: float,
    direction: str = "LONG",
    atr_value: float = None,
    iv_rank: float = 50.0,
    current_positions_value: float = 0.0,
    risk_percent: float = 2.0,
    stop_atr_multiplier: float = 1.5,
    target_atr_multiplier: float = 2.5,
    high_prices: list = None,
    low_prices: list = None,
    close_prices: list = None,
) -> RiskMetrics:
    """
    Create a complete risk profile for a potential trade.

    Args:
        symbol: Ticker symbol
        entry_price: Entry price per share
        account_balance: Total account balance (USD)
        direction: "LONG" or "SHORT"
        atr_value: Pre-calculated ATR
        iv_rank: IV percentile (0-100)
        current_positions_value: Current open position value (USD)
        risk_percent: Risk per trade as % of account
        stop_atr_multiplier: Stop loss distance (default 1.5x ATR)
        target_atr_multiplier: Target profit distance (default 2.5x ATR)
        high_prices: Recent high prices for ATR calculation
        low_prices: Recent low prices for ATR calculation
        close_prices: Recent close prices for ATR calculation

    Returns:
        RiskMetrics object with complete trade profile
    """
    # Calculate ATR
    if atr_value is None:
        if high_prices and low_prices and close_prices:
            atr_value = calculate_atr(high_prices, low_prices, close_prices, period=14)
        else:
            atr_value = entry_price * 0.02

    # Get volatility adjustment
    vol_multiplier, regime = get_volatility_adjustment(iv_rank, atr_value)

    # Calculate stop and target
    stop_price = calculate_stop_loss(
        symbol, entry_price, direction, atr_value,
        stop_atr_multiplier, vol_multiplier
    )
    target_price = calculate_take_profit(
        symbol, entry_price, direction, atr_value,
        target_atr_multiplier, vol_multiplier
    )

    # Calculate position size
    sizing = calculate_position_size(
        symbol, account_balance, entry_price, stop_price,
        risk_percent, current_positions_value=current_positions_value
    )

    position_size = sizing["shares"]
    position_value = sizing["position_value"]

    # Calculate risk/reward amounts
    if direction.upper() == "LONG":
        risk_amount = entry_price - stop_price
        reward_amount = target_price - entry_price
    else:  # SHORT
        risk_amount = stop_price - entry_price
        reward_amount = entry_price - target_price

    # Avoid division by zero
    if risk_amount > 0:
        risk_reward_ratio = reward_amount / risk_amount
    else:
        risk_reward_ratio = 0.0

    metrics = RiskMetrics(
        symbol=symbol,
        entry_price=round(entry_price, 2),
        direction=direction.upper(),
        stop_price=stop_price,
        target_price=target_price,
        position_size=position_size,
        position_value=round(position_value, 2),
        risk_amount=round(risk_amount, 2),
        reward_amount=round(reward_amount, 2),
        risk_reward_ratio=round(risk_reward_ratio, 2),
        atr_value=round(atr_value, 2),
        iv_rank=round(iv_rank, 1),
        volatility_multiplier=round(vol_multiplier, 2),
        max_loss_usd=sizing["max_loss"],
        max_gain_usd=round(reward_amount * position_size, 2),
        timestamp=datetime.now(timezone.utc).isoformat()
    )

    logger.info(f"Created risk profile: {metrics}")
    return metrics


# ============================================================================
# VALIDATION & COMPLIANCE
# ============================================================================

def validate_risk_profile(
    metrics: RiskMetrics,
    min_risk_reward_ratio: float = 1.0,
    max_position_loss_percent: float = 5.0,
) -> Tuple[bool, str]:
    """
    Validate risk profile meets compliance requirements.

    Args:
        metrics: RiskMetrics object to validate
        min_risk_reward_ratio: Minimum acceptable RR ratio (default 1.0)
        max_position_loss_percent: Max loss as % of position value (default 5.0%)

    Returns:
        (is_valid: bool, reason: str)
    """
    if metrics.position_size <= 0:
        return False, "Position size must be positive"

    if metrics.risk_amount <= 0:
        return False, "Risk amount must be positive"

    if metrics.risk_reward_ratio < min_risk_reward_ratio:
        return False, f"Risk/reward ratio {metrics.risk_reward_ratio:.2f} below minimum {min_risk_reward_ratio}"

    position_loss_pct = (metrics.max_loss_usd / metrics.position_value * 100) if metrics.position_value > 0 else 0
    if position_loss_pct > max_position_loss_percent:
        return False, f"Position loss {position_loss_pct:.1f}% exceeds max {max_position_loss_percent}%"

    return True, "Valid"


# ============================================================================
# REPORTING & ANALYSIS
# ============================================================================

def format_risk_summary(metrics: RiskMetrics) -> str:
    """Format risk metrics as human-readable summary."""
    return f"""
RISK PROFILE SUMMARY
{'=' * 60}
Symbol:             {metrics.symbol}
Direction:          {metrics.direction}
Entry Price:        ${metrics.entry_price:.2f}
Stop Loss:          ${metrics.stop_price:.2f}
Take Profit:        ${metrics.target_price:.2f}
Position Size:      {metrics.position_size} shares
Position Value:     ${metrics.position_value:,.2f}

RISK/REWARD
Risk per Share:     ${metrics.risk_amount:.2f}
Reward per Share:   ${metrics.reward_amount:.2f}
Risk/Reward Ratio:  {metrics.risk_reward_ratio:.2f}:1
Max Loss:           ${metrics.max_loss_usd:,.2f}
Max Gain:           ${metrics.max_gain_usd:,.2f}

VOLATILITY CONTEXT
ATR (14):           ${metrics.atr_value:.2f}
IV Rank:            {metrics.iv_rank:.1f}%
Vol Multiplier:     {metrics.volatility_multiplier:.2f}x

Timestamp:          {metrics.timestamp}
{'=' * 60}
"""


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Example 1: LONG trade with ATR
    print("EXAMPLE 1: LONG Trade with ATR Calculation")
    print("-" * 60)

    high_prices = [100.0, 101.0, 102.0, 101.5, 100.5] + [99.5] * 15
    low_prices = [98.0, 99.0, 100.0, 99.5, 98.5] + [97.5] * 15
    close_prices = [99.5, 100.5, 101.0, 100.5, 99.5] + [98.5] * 15

    metrics = create_risk_profile(
        symbol="SPY",
        entry_price=101.0,
        account_balance=50000.0,
        direction="LONG",
        iv_rank=35.0,
        high_prices=high_prices,
        low_prices=low_prices,
        close_prices=close_prices,
    )

    print(format_risk_summary(metrics))
    is_valid, reason = validate_risk_profile(metrics)
    print(f"Valid: {is_valid} - {reason}\n")

    # Example 2: SHORT trade with low volatility
    print("EXAMPLE 2: SHORT Trade - Low Volatility Regime")
    print("-" * 60)

    metrics_short = create_risk_profile(
        symbol="QQQ",
        entry_price=350.0,
        account_balance=50000.0,
        direction="SHORT",
        iv_rank=15.0,
        atr_value=2.5,
    )

    print(format_risk_summary(metrics_short))
    is_valid, reason = validate_risk_profile(metrics_short)
    print(f"Valid: {is_valid} - {reason}\n")

    # Example 3: Volatility adjustment demonstration
    print("EXAMPLE 3: Volatility Adjustments Across IV Ranks")
    print("-" * 60)

    print(f"{'IV Rank':<12} {'Multiplier':<12} {'Regime':<15} {'Stop (ATR×1.5)':<20}")
    print("-" * 60)
    for iv in [10, 25, 40, 60, 75, 90]:
        mult, regime = get_volatility_adjustment(iv, base_atr=2.0)
        stop_dist = 2.0 * 1.5 * mult
        print(f"{iv:<12} {mult:<12.2f} {regime:<15} ${stop_dist:<20.2f}")
