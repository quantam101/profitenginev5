"""
Already Here Agentic Trading Control OS — MCP Server
Days 0-10 Accelerated Implementation
"""

import asyncio
import yaml
import numpy as np
from decimal import Decimal
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import logging
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from models import (
    MarketSnapshot, AccountState, OrderState, TradeProposal,
    TradeOutcome
)
from agents_impl import TechnicalAgent, MicrostructureAgent, RegimeAgent, PortfolioAgent
from synthesis_engine import ProposalSynthesisEngine
from risk_kernel import DeterministicRiskKernel
from paper_broker import PaperBroker
from audit_ledger import AuditLedger

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TradingControlOS:
    def __init__(self, config_path: str = "./config.yaml"):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)

        self.synthesis_engine = ProposalSynthesisEngine(self.config)
        self.risk_kernel = DeterministicRiskKernel(self.config['risk']['hard_limits'])
        self.paper_broker = PaperBroker(self.config)
        self.audit_ledger = AuditLedger()

        self.open_proposals = {}
        self.open_orders = {}
        self.rejected_proposals = []

    async def process_market_snapshot(self, snapshot: Dict) -> Optional[str]:
        """Main loop: snapshot → proposal → risk check → execution."""

        market_snapshot = MarketSnapshot(
            symbol=snapshot['symbol'],
            timestamp=datetime.utcnow(),  # Use current time to ensure quote freshness
            bid=Decimal(str(snapshot['bid'])),
            ask=Decimal(str(snapshot['ask'])),
            last=Decimal(str(snapshot['last'])),
            volume=snapshot['volume'],
            volume_24h=Decimal(str(snapshot['volume_24h'])),
            volatility=snapshot['volatility'],
            prices=snapshot.get('prices', []),
            volumes=snapshot.get('volumes', []),
            orderbook=snapshot.get('orderbook', {}),
            trade_flow=snapshot.get('trade_flow', []),
            state=snapshot.get('state', {})
        )

        account_state = AccountState(
            timestamp=datetime.utcnow(),
            account_equity=Decimal(str(snapshot['account_equity'])),
            buying_power=Decimal(str(snapshot['buying_power'])),
            cash=Decimal(str(snapshot['cash'])),
            daily_pnl=Decimal(str(snapshot['daily_pnl'])),
            weekly_pnl=Decimal(str(snapshot['weekly_pnl'])),
            max_drawdown_pct=snapshot['max_drawdown_pct'],
            open_positions=snapshot.get('open_positions', []),
            position_mismatch=snapshot.get('position_mismatch', False),
            broker_offline=snapshot.get('broker_offline', False)
        )

        # STEP 1: Generate proposal
        proposal = self.synthesis_engine.generate(
            market_snapshot,
            account_state.account_equity,
            account_state.daily_pnl,
            account_state.open_positions
        )

        if not proposal:
            logger.info(f"[{snapshot['symbol']}] No proposal generated (regime forbids or reward/risk low)")
            return None

        logger.info(f"[{proposal.symbol}] Proposal: {proposal.direction} @ {proposal.entry_price}")

        # Log proposal
        self.audit_ledger.log_proposal(proposal)
        self.open_proposals[proposal.proposal_id] = proposal

        # STEP 2: Risk evaluation
        risk_decision = self.risk_kernel.evaluate(
            proposal,
            {
                'bid': proposal.entry_price,
                'ask': proposal.entry_price,
                'timestamp': datetime.utcnow(),
                **snapshot
            },
            account_state,
            list(self.open_orders.values())
        )

        self.audit_ledger.log_risk_decision(proposal.proposal_id, risk_decision)

        if not risk_decision.approved:
            logger.warning(f"[{proposal.symbol}] Risk REJECTED: {risk_decision.rejection_reasons}")
            self.rejected_proposals.append({
                'proposal_id': proposal.proposal_id,
                'reasons': [r.value for r in risk_decision.rejection_reasons],
                'timestamp': datetime.utcnow()
            })
            return None

        logger.info(f"[{proposal.symbol}] Risk APPROVED (score: {risk_decision.risk_score:.2f})")

        # STEP 3: Execute
        result = await self.paper_broker.submit_proposal(proposal)
        self.audit_ledger.log_execution(result, proposal.proposal_id)
        self.open_orders[result.order_id] = result

        logger.info(f"[{proposal.symbol}] FILLED @ {result.fill_price} (slippage: {result.slippage})")

        return result.order_id

    async def close_position(self, symbol: str, exit_price: Decimal):
        """Close trade and record outcome."""
        pnl = await self.paper_broker.close_position(symbol, exit_price)
        logger.info(f"[{symbol}] Position closed, P&L: ${pnl}")

    def get_paper_stats(self) -> Dict:
        """Get paper trading performance."""
        return self.paper_broker.get_stats()

    def get_audit_stats(self) -> Dict:
        """Get audit ledger stats."""
        return self.audit_ledger.get_stats()

async def demo_backtest(os_instance: TradingControlOS, symbol: str = "AAPL", trades: int = 30):
    """Run simulated trading loop."""
    logger.info(f"Starting demo backtest: {trades} trades on {symbol}")

    for i in range(trades):
        # Simulate market data
        snapshot = {
            'symbol': symbol,
            'timestamp': datetime.utcnow().isoformat(),
            'bid': 150.0 + np.random.randn() * 2,
            'ask': 150.0 + np.random.randn() * 2 + 0.05,
            'last': 150.0 + np.random.randn() * 2,
            'volume': int(1000000 + np.random.randint(-100000, 100000)),
            'volume_24h': Decimal('50000000'),
            'volatility': max(1.0, 10.0 + np.random.randn() * 3),
            'prices': [150.0 + np.random.randn() for _ in range(50)],
            'volumes': [int(100000 + np.random.randint(-10000, 10000)) for _ in range(50)],
            'orderbook': {
                'bids': [[150.0 - j*0.01, 10000] for j in range(5)],
                'asks': [[150.0 + j*0.01, 10000] for j in range(5)]
            },
            'trade_flow': [],
            'state': {'event_risk': 0.1, 'correlation_stress': 0.2},
            'account_equity': 100000.0,
            'buying_power': 95000.0,
            'cash': 50000.0,
            'daily_pnl': -50.0 + (i * 10),
            'weekly_pnl': 0.0,
            'max_drawdown_pct': 2.5,
            'open_positions': [],
            'position_mismatch': False,
            'broker_offline': False
        }

        order_id = await os_instance.process_market_snapshot(snapshot)

        if order_id:
            # Simulate exit after 5 iterations
            if i % 5 == 4:
                exit_price = Decimal(str(150.0 + np.random.randn()))
                await os_instance.close_position(symbol, exit_price)

        await asyncio.sleep(0.01)

    # Print stats
    paper_stats = os_instance.get_paper_stats()
    audit_stats = os_instance.get_audit_stats()

    logger.info("\n=== DEMO RESULTS ===")
    logger.info(f"Paper Trades: {paper_stats['total_trades']}")
    logger.info(f"Win Rate: {paper_stats['win_rate']*100:.1f}%")
    logger.info(f"Cash: ${paper_stats['cash']:,.2f}")
    logger.info(f"Equity: ${paper_stats['equity']:,.2f}")
    logger.info(f"\nAudit Stats:")
    logger.info(f"Total Proposals: {audit_stats['total_trades']}")
    logger.info(f"Approval Rate: {audit_stats['approval_rate_pct']:.1f}%")
    logger.info(f"Win Rate: {audit_stats['win_rate_pct']:.1f}%")
    logger.info(f"Total P&L: ${audit_stats['total_pnl']:,.2f}")

if __name__ == "__main__":
    os_instance = TradingControlOS()
    asyncio.run(demo_backtest(os_instance, trades=30))
