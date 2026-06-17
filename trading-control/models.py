from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
import uuid

class OrderState(Enum):
    PROPOSED = "proposed"
    RISK_APPROVED = "risk_approved"
    SUBMITTED = "submitted"
    ACKNOWLEDGED = "acknowledged"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    PROTECTED = "protected"
    EXIT_PENDING = "exit_pending"
    CLOSED = "closed"
    RECONCILED = "reconciled"
    REVIEWED = "reviewed"
    REJECTED = "rejected"
    SUBMIT_FAILED = "submit_failed"
    BROKER_TIMEOUT = "broker_timeout"
    DATA_STALE = "data_stale"
    KILL_SWITCH = "kill_switch"

class MarketRegime(Enum):
    BULL_CONSOLIDATING = "bull_consolidating"
    BULL_TRENDING = "bull_trending"
    BEAR_CONSOLIDATING = "bear_consolidating"
    BEAR_TRENDING = "bear_trending"
    HIGH_VOLATILITY = "high_volatility"
    NEWS_DRIVEN = "news_driven"
    NO_TRADE = "no_trade"

class RejectionReason(Enum):
    REGIME_FORBIDS = "regime_forbids_trading"
    DAILY_LOSS_HIT = "daily_loss_limit_exceeded"
    WEEKLY_LOSS_HIT = "weekly_loss_limit_exceeded"
    CAPITAL_INSUFFICIENT = "insufficient_capital"
    DUPLICATE_ORDER = "duplicate_order_exists"
    SPREAD_TOO_WIDE = "spread_exceeds_threshold"
    LIQUIDITY_INSUFFICIENT = "volume_too_low"
    DATA_STALE = "quote_data_stale"
    REWARD_RISK_LOW = "reward_to_risk_below_minimum"
    CORRELATION_HIGH = "correlated_exposure_too_high"
    ACCOUNT_UNRECONCILED = "broker_position_unknown"
    BROKER_OFFLINE = "broker_connection_lost"
    EVENT_RISK_HIGH = "news_event_risk_detected"
    POSITION_MISMATCH = "position_state_conflict"

@dataclass
class TechnicalSignal:
    rsi_oversold_recovery: float
    macd_bullish_cross: float
    support_bounce: float
    trend_alignment: float
    pattern_score: float
    confidence: float

@dataclass
class MicrostructureSignal:
    bid_ask_imbalance: float
    smart_money_flow: float
    liquidity_score: float
    front_running_risk: float
    time_to_fill: float
    confidence: float

@dataclass
class RegimeSignal:
    regime: MarketRegime
    volatility_level: float
    event_risk: float
    correlation_stress: float
    regime_confidence: float
    approved_to_trade: bool

@dataclass
class PortfolioSignal:
    position_size_kelly: float
    max_correlated_exposure: float
    drawdown_forecast: float
    risk_budget_remaining: float
    recommended_action: str

@dataclass
class TradeProposal:
    symbol: str
    direction: str
    entry_price: Decimal
    stop_loss: Decimal
    take_profit: Decimal
    position_size_usd: Decimal
    position_size_pct: float
    time_in_force: str
    order_type: str

    technical_signal: TechnicalSignal
    microstructure_signal: MicrostructureSignal
    regime_signal: RegimeSignal
    portfolio_signal: PortfolioSignal

    overall_confidence: float
    expected_reward_risk: float
    rationale: str

    proposal_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass
class RiskApprovalDecision:
    approved: bool
    rejection_reasons: List[RejectionReason]
    risk_score: float
    final_decision: str

@dataclass
class ExecutionResult:
    order_id: str
    state: OrderState
    timestamp: datetime
    entry_price: Decimal
    quantity: Decimal
    fill_price: Decimal
    slippage: Decimal
    fee: Decimal
    realized_pnl: Decimal
    is_complete: bool

@dataclass
class TradeOutcome:
    trade_id: str
    proposal: TradeProposal
    execution: ExecutionResult
    exit_price: Decimal
    exit_time: datetime
    realized_pnl: Decimal
    return_pct: float
    duration_minutes: float
    max_favorable_excursion: Decimal
    max_adverse_excursion: Decimal

@dataclass
class MarketSnapshot:
    symbol: str
    timestamp: datetime
    bid: Decimal
    ask: Decimal
    last: Decimal
    volume: int
    volume_24h: Decimal
    volatility: float
    prices: List[Decimal] = field(default_factory=list)
    volumes: List[int] = field(default_factory=list)
    orderbook: Dict = field(default_factory=dict)
    trade_flow: List[Dict] = field(default_factory=list)
    state: Dict = field(default_factory=dict)

@dataclass
class AccountState:
    timestamp: datetime
    account_equity: Decimal
    buying_power: Decimal
    cash: Decimal
    daily_pnl: Decimal
    weekly_pnl: Decimal
    max_drawdown_pct: float
    open_positions: List[Dict]
    position_mismatch: bool
    broker_offline: bool
