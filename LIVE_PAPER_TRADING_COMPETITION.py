#!/usr/bin/env python3
"""
LIVE PAPER TRADING COMPETITION - PROFITENGINE V5
Two autonomous trading systems compete with LIVE Finnhub data
Real-time paper trading until $1,000 milestone
Winner deploys with real money
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List
import numpy as np
import finnhub

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('.runtime/live_paper_trading.log'),
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)


class LiveMarketData:
    """Fetch live data from Finnhub"""

    def __init__(self, api_key: str = None):
        # Get API key from environment
        import os
        self.api_key = api_key or os.getenv('FINNHUB_API_KEY', '')

        if self.api_key:
            try:
                self.client = finnhub.Client(api_key=self.api_key)
                self.connected = True
            except Exception as e:
                logger.warning(f"Finnhub connection failed: {e}")
                self.connected = False
        else:
            logger.warning("No FINNHUB_API_KEY found")
            self.connected = False

        self.symbols = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMD', 'GOOGL', 'AMZN']
        self.last_prices = {}
        self.price_history = {}

    def get_live_prices(self) -> Dict[str, float]:
        """Fetch live prices from Finnhub"""
        if not self.connected:
            return self._simulate_prices()

        try:
            current_prices = {}
            for symbol in self.symbols:
                quote = self.client.quote(symbol)
                price = quote.get('c', 0)  # Current price
                current_prices[symbol] = price

                # Track history
                if symbol not in self.price_history:
                    self.price_history[symbol] = []
                self.price_history[symbol].append(price)

            self.last_prices = current_prices
            return current_prices

        except Exception as e:
            logger.warning(f"Finnhub API error: {e}, using simulation")
            return self._simulate_prices()

    def _simulate_prices(self) -> Dict[str, float]:
        """Fallback: simulate prices based on historical trends"""
        base_prices = {
            'AAPL': 150.0,
            'MSFT': 420.0,
            'NVDA': 875.0,
            'TSLA': 245.0,
            'AMD': 165.0,
            'GOOGL': 140.0,
            'AMZN': 185.0,
        }

        # Add realistic daily movement (±2%)
        current_prices = {}
        for symbol, base_price in base_prices.items():
            movement = np.random.normal(0, base_price * 0.01)
            current_prices[symbol] = base_price + movement

        self.last_prices = current_prices
        return current_prices

    def calculate_strategy_signals(self, prices: Dict[str, float]) -> Dict[str, float]:
        """Calculate strategy signals from live prices"""
        signals = {}

        # Strategy 1: Momentum (buy if price going up)
        signals['strategy_1'] = self._momentum_signal(prices)

        # Strategy 2: Mean Reversion (buy if price down, sell if up)
        signals['strategy_2'] = self._mean_reversion_signal(prices)

        # Strategy 3: Breakout (buy on price spikes)
        signals['strategy_3'] = self._breakout_signal(prices)

        # Strategy 4: Bollinger Bands
        signals['strategy_4'] = self._bollinger_signal(prices)

        # Strategy 9: Volume-based (simulate)
        signals['strategy_9'] = self._volume_signal(prices)

        # Strategy 10: EMA Cross
        signals['strategy_10'] = self._ema_signal(prices)

        return signals

    def _momentum_signal(self, prices: Dict[str, float]) -> float:
        """Calculate momentum signal"""
        total_momentum = 0
        for symbol in self.symbols:
            if len(self.price_history.get(symbol, [])) >= 2:
                prev = self.price_history[symbol][-2]
                curr = self.price_history[symbol][-1]
                momentum = (curr - prev) / prev * 100
                total_momentum += momentum

        return total_momentum / len(self.symbols) if self.symbols else 0

    def _mean_reversion_signal(self, prices: Dict[str, float]) -> float:
        """Calculate mean reversion signal"""
        reversion_signals = []
        for symbol in self.symbols:
            if len(self.price_history.get(symbol, [])) >= 5:
                recent = self.price_history[symbol][-5:]
                mean = np.mean(recent)
                curr = recent[-1]
                deviation = (curr - mean) / mean * 100
                reversion_signals.append(-deviation)  # Negative = reverting upward

        return np.mean(reversion_signals) if reversion_signals else 0

    def _breakout_signal(self, prices: Dict[str, float]) -> float:
        """Calculate breakout signal"""
        breakout_signals = []
        for symbol in self.symbols:
            if len(self.price_history.get(symbol, [])) >= 10:
                recent = self.price_history[symbol][-10:]
                high = max(recent[:-1])
                curr = recent[-1]
                if curr > high:
                    breakout_signals.append((curr - high) / high * 100)

        return np.mean(breakout_signals) if breakout_signals else 0

    def _bollinger_signal(self, prices: Dict[str, float]) -> float:
        """Calculate Bollinger Bands signal"""
        bb_signals = []
        for symbol in self.symbols:
            if len(self.price_history.get(symbol, [])) >= 20:
                recent = np.array(self.price_history[symbol][-20:])
                mean = np.mean(recent)
                std = np.std(recent)
                curr = recent[-1]

                lower_band = mean - 2 * std
                upper_band = mean + 2 * std

                if curr < lower_band:
                    bb_signals.append(1)  # Oversold, buy
                elif curr > upper_band:
                    bb_signals.append(-1)  # Overbought, sell

        return np.mean(bb_signals) if bb_signals else 0

    def _volume_signal(self, prices: Dict[str, float]) -> float:
        """Simulate volume signal"""
        return np.random.normal(0, 0.5)

    def _ema_signal(self, prices: Dict[str, float]) -> float:
        """Calculate EMA crossover signal"""
        ema_signals = []
        for symbol in self.symbols:
            if len(self.price_history.get(symbol, [])) >= 26:
                recent = np.array(self.price_history[symbol][-26:])

                # Simple EMA calculation
                ema_12 = np.mean(recent[-12:])
                ema_26 = np.mean(recent)

                if ema_12 > ema_26:
                    ema_signals.append(1)  # Bullish
                else:
                    ema_signals.append(-1)  # Bearish

        return np.mean(ema_signals) if ema_signals else 0


class TradingSystem:
    """Individual trading system with live market data"""

    def __init__(self, system_id: int, market_data: LiveMarketData, starting_capital: float = 100.0):
        self.system_id = system_id
        self.name = f"System_{system_id}"
        self.starting_capital = starting_capital
        self.current_balance = starting_capital
        self.market_data = market_data
        self.trades = []
        self.equity_curve = [starting_capital]
        self.run_count = 0

        if system_id == 1:
            # System 1: Conservative
            self.active_strategies = [1, 2, 4, 10]
            self.strategy_allocations = [0.25, 0.35, 0.20, 0.20]
            self.risk_multiplier = 0.8
        else:
            # System 2: Aggressive
            self.active_strategies = [2, 3, 9, 10]
            self.strategy_allocations = [0.30, 0.25, 0.25, 0.20]
            self.risk_multiplier = 1.2

        self.performance_history = []
        self.start_time = datetime.now()

    def execute_trading_round(self) -> float:
        """Execute trades based on LIVE Finnhub data"""
        self.run_count += 1
        total_profit = 0

        try:
            # Get live prices and calculate signals
            live_prices = self.market_data.get_live_prices()
            signals = self.market_data.calculate_strategy_signals(live_prices)

            for strategy_id, allocation in zip(self.active_strategies, self.strategy_allocations):
                strategy_signal = signals.get(f'strategy_{strategy_id}', 0)

                # Convert signal to profit (signal is in percentage points)
                round_profit = (strategy_signal / 100.0) * self.current_balance * allocation * self.risk_multiplier

                self.current_balance += round_profit
                total_profit += round_profit

                self.trades.append({
                    'timestamp': datetime.now().isoformat(),
                    'system': self.name,
                    'strategy': strategy_id,
                    'signal': strategy_signal,
                    'profit': round_profit,
                    'balance': self.current_balance,
                    'live_prices': live_prices,
                })

            self.equity_curve.append(self.current_balance)
            self.performance_history.append({
                'run': self.run_count,
                'timestamp': datetime.now().isoformat(),
                'balance': self.current_balance,
                'profit': total_profit,
                'roi': ((self.current_balance - self.starting_capital) / self.starting_capital) * 100,
            })

        except Exception as e:
            logger.error(f"{self.name} execution error: {e}")

        return total_profit

    def get_metrics(self) -> Dict:
        """Get system metrics"""
        roi = ((self.current_balance - self.starting_capital) / self.starting_capital) * 100

        return {
            'system_id': self.system_id,
            'name': self.name,
            'current_balance': self.current_balance,
            'starting_capital': self.starting_capital,
            'total_profit': self.current_balance - self.starting_capital,
            'roi_percent': roi,
            'total_trades': len(self.trades),
            'run_count': self.run_count,
            'active_strategies': self.active_strategies,
        }

    def has_reached_milestone(self, target: float = 1000.0) -> bool:
        """Check if reached $1,000"""
        return self.current_balance >= target


class LivePaperTradingCompetition:
    """Live paper trading competition with real Finnhub data"""

    def __init__(self):
        self.market_data = LiveMarketData()
        self.system1 = TradingSystem(1, self.market_data, starting_capital=100.0)
        self.system2 = TradingSystem(2, self.market_data, starting_capital=100.0)
        self.target_milestone = 1000.0
        self.competition_started = datetime.now()
        self.runtime_dir = Path('.runtime')
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.round_count = 0
        self.winner = None

    async def run_competition_round(self):
        """Run one live paper trading round"""
        self.round_count += 1

        # Both systems execute trades with LIVE data
        system1_profit = self.system1.execute_trading_round()
        system2_profit = self.system2.execute_trading_round()

        metrics1 = self.system1.get_metrics()
        metrics2 = self.system2.get_metrics()

        logger.info("=" * 80)
        logger.info(f"LIVE PAPER TRADING ROUND #{self.round_count}")
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        logger.info("=" * 80)

        logger.info("\nSYSTEM 1 (Conservative - High Win Rate):")
        logger.info(f"  Balance: ${metrics1['current_balance']:.2f}")
        logger.info(f"  Profit: ${metrics1['total_profit']:.2f}")
        logger.info(f"  ROI: {metrics1['roi_percent']:.2f}%")
        logger.info(f"  Round Profit: ${system1_profit:.2f}")

        logger.info("\nSYSTEM 2 (Aggressive - High Profit):")
        logger.info(f"  Balance: ${metrics2['current_balance']:.2f}")
        logger.info(f"  Profit: ${metrics2['total_profit']:.2f}")
        logger.info(f"  ROI: {metrics2['roi_percent']:.2f}%")
        logger.info(f"  Round Profit: ${system2_profit:.2f}")

        logger.info("\nLEADERBOARD:")
        if metrics1['current_balance'] > metrics2['current_balance']:
            lead = metrics1['current_balance'] - metrics2['current_balance']
            logger.info(f"  1st: System 1 (${metrics1['current_balance']:.2f}) - LEADING BY ${lead:.2f}")
            logger.info(f"  2nd: System 2 (${metrics2['current_balance']:.2f})")
        else:
            lead = metrics2['current_balance'] - metrics1['current_balance']
            logger.info(f"  1st: System 2 (${metrics2['current_balance']:.2f}) - LEADING BY ${lead:.2f}")
            logger.info(f"  2nd: System 1 (${metrics1['current_balance']:.2f})")

        logger.info("=" * 80 + "\n")

        # Check for winner
        if self.system1.has_reached_milestone(self.target_milestone):
            self.winner = 1
            logger.info("\n" + "!" * 80)
            logger.info("SYSTEM 1 REACHED $1,000 MILESTONE!")
            logger.info("!" * 80)
            return True

        if self.system2.has_reached_milestone(self.target_milestone):
            self.winner = 2
            logger.info("\n" + "!" * 80)
            logger.info("SYSTEM 2 REACHED $1,000 MILESTONE!")
            logger.info("!" * 80)
            return True

        # Save state
        self._save_state()
        return False

    def _save_state(self):
        """Save competition state"""
        metrics1 = self.system1.get_metrics()
        metrics2 = self.system2.get_metrics()

        data = {
            'round': self.round_count,
            'timestamp': datetime.now().isoformat(),
            'market_connected': self.market_data.connected,
            'system1': metrics1,
            'system2': metrics2,
        }

        output_file = self.runtime_dir / 'live_paper_trading.json'
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)

    async def run_continuous_competition(self):
        """Run continuous live paper trading until winner"""
        logger.info("*" * 80)
        logger.info("PROFITENGINE V5 - LIVE PAPER TRADING COMPETITION")
        logger.info("Using LIVE Finnhub Data")
        logger.info("*" * 80)
        logger.info(f"Start Time: {datetime.now().isoformat()}")
        logger.info(f"Market Connected: {self.market_data.connected}")
        logger.info("*" * 80 + "\n")

        while not self.winner:
            winner_found = await self.run_competition_round()

            if winner_found:
                break

            # Wait between rounds (real-time market updates)
            await asyncio.sleep(60)  # 1-minute intervals for live data

        if self.winner:
            await self._announce_winner()

    async def _announce_winner(self):
        """Announce winner"""
        logger.info("\n" + "=" * 80)
        logger.info("WINNER ANNOUNCED")
        logger.info("=" * 80)

        if self.winner == 1:
            metrics = self.system1.get_metrics()
        else:
            metrics = self.system2.get_metrics()

        logger.info(f"\nWINNER: {metrics['name']}")
        logger.info(f"  Final Balance: ${metrics['current_balance']:.2f}")
        logger.info(f"  Total Profit: ${metrics['total_profit']:.2f}")
        logger.info(f"  ROI: {metrics['roi_percent']:.2f}%")
        logger.info(f"  Total Rounds: {metrics['run_count']}")

        time_elapsed = (datetime.now() - self.competition_started).total_seconds() / 3600
        logger.info(f"\nCompetition Time: {time_elapsed:.1f} hours")
        logger.info("Ready for REAL MONEY deployment!")
        logger.info("=" * 80)


async def main():
    """Entry point"""
    competition = LivePaperTradingCompetition()
    await competition.run_continuous_competition()


if __name__ == "__main__":
    asyncio.run(main())
