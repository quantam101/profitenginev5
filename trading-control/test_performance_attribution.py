#!/usr/bin/env python
"""
UNIT TESTS: Performance Attribution Engine
Tests all major functions and edge cases
"""

import pytest
import json
import os
from datetime import datetime, timedelta
from decimal import Decimal
from performance_attribution import (
    PerformanceAttributionEngine,
    TradeAttribution,
    AgentContribution,
    RegimeStats,
    AgentStats
)


class TestAgentContribution:
    """Test AgentContribution data class."""

    def test_agent_contribution_creation(self):
        """Test creating an agent contribution."""
        contrib = AgentContribution(
            agent_name='Technical',
            confidence=0.85,
            signal_strength=0.75,
            attributed_pnl=Decimal('250.00'),
            win_attribution=0.8
        )
        assert contrib.agent_name == 'Technical'
        assert contrib.confidence == 0.85
        assert contrib.attributed_pnl == Decimal('250.00')

    def test_agent_contribution_decimals(self):
        """Test decimal handling in contributions."""
        contrib = AgentContribution(
            agent_name='Microstructure',
            confidence=0.6,
            signal_strength=0.5,
            attributed_pnl=Decimal('150.50'),
            win_attribution=0.5
        )
        assert isinstance(contrib.attributed_pnl, Decimal)
        assert float(contrib.attributed_pnl) == 150.50


class TestPerformanceAttributionEngine:
    """Test PerformanceAttributionEngine methods."""

    @pytest.fixture
    def engine(self):
        """Create engine instance for tests."""
        engine = PerformanceAttributionEngine()
        yield engine
        # No DB cleanup needed for this test

    def test_engine_initialization(self, engine):
        """Test engine initialization."""
        assert engine.db_path == './trading-control/audit.db'
        assert engine.risk_free_rate == 0.02

    def test_analyze_single_winning_trade(self, engine):
        """Test attribution analysis on a winning trade."""
        trade = {
            'trade_id': 'test_001',
            'symbol': 'AAPL',
            'direction': 'BUY',
            'entry_price': '150.00',
            'exit_price': '155.00',
            'realized_pnl': '500.00',
            'return_pct': 3.33,
            'regime': 'bull_trending',
            'duration_minutes': 45.0,
            'timestamp': datetime.now().isoformat()
        }

        signals = {
            'technical': {'confidence': 0.8, 'strength': 0.75},
            'microstructure': {'confidence': 0.6, 'strength': 0.5},
            'regime': {'confidence': 0.9, 'strength': 0.85},
            'portfolio': {'confidence': 0.7, 'strength': 0.65}
        }

        attr = engine.analyze_trade_contribution(trade, signals)

        # Verify attribution object
        assert attr.trade_id == 'test_001'
        assert attr.symbol == 'AAPL'
        assert attr.realized_pnl == Decimal('500.00')
        assert attr.direction == 'BUY'

        # Verify P&L decomposition sums to total
        total_attributed = (
            attr.total_pnl_technical +
            attr.total_pnl_microstructure +
            attr.total_pnl_regime +
            attr.total_pnl_portfolio
        )
        # Allow small rounding error
        assert abs(float(total_attributed - attr.realized_pnl)) < 0.01

    def test_analyze_losing_trade(self, engine):
        """Test attribution on a losing trade."""
        trade = {
            'trade_id': 'test_002',
            'symbol': 'TSLA',
            'direction': 'BUY',
            'entry_price': '250.00',
            'exit_price': '245.00',
            'realized_pnl': '-300.00',
            'return_pct': -2.0,
            'regime': 'bear_trending',
            'duration_minutes': 20.0,
            'timestamp': datetime.now().isoformat()
        }

        signals = {
            'technical': {'confidence': 0.5, 'strength': 0.4},
            'microstructure': {'confidence': 0.4, 'strength': 0.3},
            'regime': {'confidence': 0.8, 'strength': 0.7},
            'portfolio': {'confidence': 0.6, 'strength': 0.5}
        }

        attr = engine.analyze_trade_contribution(trade, signals)

        assert attr.realized_pnl == Decimal('-300.00')
        assert attr.return_pct == -2.0

        # Losing trade: win attributions should be 0
        assert attr.technical_contrib.win_attribution == 0.0
        assert attr.microstructure_contrib.win_attribution == 0.0

    def test_analyze_zero_signals(self, engine):
        """Test attribution when all signals have zero confidence."""
        trade = {
            'trade_id': 'test_003',
            'symbol': 'SPY',
            'direction': 'SELL',
            'entry_price': '450.00',
            'exit_price': '449.00',
            'realized_pnl': '100.00',
            'return_pct': 0.22,
            'regime': 'unknown',
            'duration_minutes': 10.0,
            'timestamp': datetime.now().isoformat()
        }

        signals = {
            'technical': {'confidence': 0.0, 'strength': 0.0},
            'microstructure': {'confidence': 0.0, 'strength': 0.0},
            'regime': {'confidence': 0.0, 'strength': 0.0},
            'portfolio': {'confidence': 0.0, 'strength': 0.0}
        }

        attr = engine.analyze_trade_contribution(trade, signals)

        # Should use default weights: [0.35, 0.25, 0.25, 0.15]
        assert attr.technical_contrib.attributed_pnl > 0

    def test_calculate_information_ratio(self, engine):
        """Test information ratio calculation."""
        # Create multiple trades for stats
        attributions = []
        pnls = [100, 150, -50, 200, -100, 120, 180, -30]

        for i, pnl in enumerate(pnls):
            trade = {
                'trade_id': f'ir_test_{i}',
                'symbol': 'TEST',
                'direction': 'BUY',
                'entry_price': '100.00',
                'exit_price': '101.00',
                'realized_pnl': str(pnl),
                'return_pct': pnl / 100.0,
                'regime': 'bull_trending',
                'duration_minutes': 30.0,
                'timestamp': (datetime.now() - timedelta(days=i)).isoformat()
            }

            signals = {
                'technical': {'confidence': 0.8, 'strength': 0.75},
                'microstructure': {'confidence': 0.6, 'strength': 0.5},
                'regime': {'confidence': 0.9, 'strength': 0.85},
                'portfolio': {'confidence': 0.7, 'strength': 0.65}
            }

            attr = engine.analyze_trade_contribution(trade, signals)
            attributions.append(attr)

        # Calculate IR for Technical agent
        ir = engine.calculate_information_ratio(attributions, 'Technical')
        assert isinstance(ir, float)
        # For positive trend, IR should be positive
        assert ir > 0

    def test_information_ratio_empty(self, engine):
        """Test IR with no trades."""
        ir = engine.calculate_information_ratio([], 'Technical')
        assert ir == 0.0

    def test_regime_breakdown(self, engine):
        """Test regime breakdown statistics."""
        attributions = []

        # Bull regime trades
        for i in range(3):
            trade = {
                'trade_id': f'bull_{i}',
                'symbol': 'TEST',
                'direction': 'BUY',
                'entry_price': '100.00',
                'exit_price': f'{101 + i}.00',
                'realized_pnl': f'{100 + (50*i)}.00',
                'return_pct': 1.0 + i,
                'regime': 'bull_trending',
                'duration_minutes': 30.0,
                'timestamp': datetime.now().isoformat()
            }
            signals = {
                'technical': {'confidence': 0.8, 'strength': 0.75},
                'microstructure': {'confidence': 0.6, 'strength': 0.5},
                'regime': {'confidence': 0.9, 'strength': 0.85},
                'portfolio': {'confidence': 0.7, 'strength': 0.65}
            }
            attr = engine.analyze_trade_contribution(trade, signals)
            attributions.append(attr)

        # Bear regime trades
        for i in range(2):
            trade = {
                'trade_id': f'bear_{i}',
                'symbol': 'TEST',
                'direction': 'SELL',
                'entry_price': '100.00',
                'exit_price': f'{99 - i}.00',
                'realized_pnl': f'{50 - (100*i)}.00',
                'return_pct': -1.0 - i,
                'regime': 'bear_trending',
                'duration_minutes': 20.0,
                'timestamp': datetime.now().isoformat()
            }
            signals = {
                'technical': {'confidence': 0.7, 'strength': 0.6},
                'microstructure': {'confidence': 0.5, 'strength': 0.4},
                'regime': {'confidence': 0.8, 'strength': 0.7},
                'portfolio': {'confidence': 0.6, 'strength': 0.5}
            }
            attr = engine.analyze_trade_contribution(trade, signals)
            attributions.append(attr)

        stats = engine.generate_regime_breakdown(attributions)

        assert 'bull_trending' in stats
        assert 'bear_trending' in stats
        assert stats['bull_trending'].num_trades == 3
        assert stats['bear_trending'].num_trades == 2
        assert stats['bull_trending'].win_rate_pct > 50.0

    def test_agent_statistics(self, engine):
        """Test agent statistics calculation."""
        attributions = []

        # Create test trades
        for i in range(5):
            trade = {
                'trade_id': f'stats_{i}',
                'symbol': 'TEST',
                'direction': 'BUY',
                'entry_price': '100.00',
                'exit_price': f'{102 + i}.00',
                'realized_pnl': f'{200 + (100*i)}.00',
                'return_pct': 2.0 + i,
                'regime': 'bull_trending',
                'duration_minutes': 30.0,
                'timestamp': datetime.now().isoformat()
            }

            signals = {
                'technical': {'confidence': 0.8, 'strength': 0.75},
                'microstructure': {'confidence': 0.6, 'strength': 0.5},
                'regime': {'confidence': 0.9, 'strength': 0.85},
                'portfolio': {'confidence': 0.7, 'strength': 0.65}
            }

            attr = engine.analyze_trade_contribution(trade, signals)
            attributions.append(attr)

        stats = engine.calculate_agent_statistics(attributions)

        # Verify all agents are present
        assert 'Technical' in stats
        assert 'Microstructure' in stats
        assert 'Regime' in stats
        assert 'Portfolio' in stats

        # Verify stats objects
        tech_stats = stats['Technical']
        assert isinstance(tech_stats, AgentStats)
        assert isinstance(tech_stats.total_attributed_pnl, Decimal)
        assert 0 <= tech_stats.avg_confidence <= 1.0
        assert tech_stats.information_ratio >= 0

    def test_export_attribution_report(self, engine, tmp_path):
        """Test report export."""
        attributions = []

        # Create test trades
        for i in range(3):
            trade = {
                'trade_id': f'export_{i}',
                'symbol': f'TEST{i}',
                'direction': 'BUY',
                'entry_price': '100.00',
                'exit_price': '105.00',
                'realized_pnl': '500.00',
                'return_pct': 5.0,
                'regime': 'bull_trending',
                'duration_minutes': 30.0,
                'timestamp': datetime.now().isoformat()
            }

            signals = {
                'technical': {'confidence': 0.8, 'strength': 0.75},
                'microstructure': {'confidence': 0.6, 'strength': 0.5},
                'regime': {'confidence': 0.9, 'strength': 0.85},
                'portfolio': {'confidence': 0.7, 'strength': 0.65}
            }

            attr = engine.analyze_trade_contribution(trade, signals)
            attributions.append(attr)

        # Export report
        output_path = os.path.join(str(tmp_path), 'test_report.json')
        result_path = engine.export_attribution_report(
            attributions,
            report_type='daily',
            output_path=output_path
        )

        # Verify file was created
        assert os.path.exists(result_path)

        # Verify report structure
        with open(result_path) as f:
            report = json.load(f)

        assert 'metadata' in report
        assert 'summary' in report
        assert 'agent_statistics' in report
        assert 'regime_breakdown' in report
        assert 'top_trades' in report

        # Verify summary
        assert report['summary']['total_trades'] == 3
        assert report['summary']['winning_trades'] == 3
        assert report['summary']['winning_trades'] == 3


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def engine(self):
        """Create engine instance for tests."""
        return PerformanceAttributionEngine()

    def test_zero_pnl_trade(self, engine):
        """Test trade with zero P&L."""
        trade = {
            'trade_id': 'zero_pnl',
            'symbol': 'TEST',
            'direction': 'BUY',
            'entry_price': '100.00',
            'exit_price': '100.00',
            'realized_pnl': '0.00',
            'return_pct': 0.0,
            'regime': 'flat',
            'duration_minutes': 5.0,
            'timestamp': datetime.now().isoformat()
        }

        signals = {
            'technical': {'confidence': 0.5, 'strength': 0.5},
            'microstructure': {'confidence': 0.5, 'strength': 0.5},
            'regime': {'confidence': 0.5, 'strength': 0.5},
            'portfolio': {'confidence': 0.5, 'strength': 0.5}
        }

        attr = engine.analyze_trade_contribution(trade, signals)
        assert attr.realized_pnl == Decimal('0.00')

    def test_very_small_pnl(self, engine):
        """Test trade with very small P&L."""
        trade = {
            'trade_id': 'small_pnl',
            'symbol': 'TEST',
            'direction': 'BUY',
            'entry_price': '100.00',
            'exit_price': '100.01',
            'realized_pnl': '0.01',
            'return_pct': 0.01,
            'regime': 'consolidating',
            'duration_minutes': 1.0,
            'timestamp': datetime.now().isoformat()
        }

        signals = {
            'technical': {'confidence': 0.3, 'strength': 0.2},
            'microstructure': {'confidence': 0.7, 'strength': 0.8},
            'regime': {'confidence': 0.4, 'strength': 0.3},
            'portfolio': {'confidence': 0.5, 'strength': 0.4}
        }

        attr = engine.analyze_trade_contribution(trade, signals)
        assert attr.realized_pnl == Decimal('0.01')

    def test_high_confidence_signals(self, engine):
        """Test with all signals at maximum confidence."""
        trade = {
            'trade_id': 'high_conf',
            'symbol': 'TEST',
            'direction': 'BUY',
            'entry_price': '100.00',
            'exit_price': '110.00',
            'realized_pnl': '1000.00',
            'return_pct': 10.0,
            'regime': 'bull_strong',
            'duration_minutes': 120.0,
            'timestamp': datetime.now().isoformat()
        }

        signals = {
            'technical': {'confidence': 0.99, 'strength': 0.99},
            'microstructure': {'confidence': 0.99, 'strength': 0.99},
            'regime': {'confidence': 0.99, 'strength': 0.99},
            'portfolio': {'confidence': 0.99, 'strength': 0.99}
        }

        attr = engine.analyze_trade_contribution(trade, signals)
        # Should still distribute according to target percentages
        assert attr.technical_contrib.confidence == 0.99


def run_all_tests():
    """Run all tests programmatically."""
    pytest.main([__file__, '-v'])


if __name__ == '__main__':
    run_all_tests()
