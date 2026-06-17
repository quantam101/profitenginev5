"""
Already Here Agentic Trading Control OS
Accelerated 2-3 week implementation
"""

__version__ = "0.1.0"

from .models import (
    OrderState, MarketRegime, RejectionReason,
    TechnicalSignal, MicrostructureSignal, RegimeSignal, PortfolioSignal,
    TradeProposal, RiskApprovalDecision, ExecutionResult, TradeOutcome,
    MarketSnapshot, AccountState
)

from .agents_impl import (
    TechnicalAgent, MicrostructureAgent, RegimeAgent, PortfolioAgent
)

from .synthesis_engine import ProposalSynthesisEngine
from .risk_kernel import DeterministicRiskKernel
from .paper_broker import PaperBroker
from .audit_ledger import AuditLedger
from .app import TradingControlOS

__all__ = [
    'OrderState', 'MarketRegime', 'RejectionReason',
    'TechnicalSignal', 'MicrostructureSignal', 'RegimeSignal', 'PortfolioSignal',
    'TradeProposal', 'RiskApprovalDecision', 'ExecutionResult', 'TradeOutcome',
    'MarketSnapshot', 'AccountState',
    'TechnicalAgent', 'MicrostructureAgent', 'RegimeAgent', 'PortfolioAgent',
    'ProposalSynthesisEngine', 'DeterministicRiskKernel', 'PaperBroker',
    'AuditLedger', 'TradingControlOS'
]
