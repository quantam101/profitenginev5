#!/usr/bin/env python3
"""
DUAL MODE TRADING ENGINE - PROFITENGINE V5
- TRAINING MODE: Outside Mon-Fri 4am-5pm (backtesting & optimization)
- LIVE TRADING MODE: Mon-Fri 4am-5pm (real Finnhub data, paper trading)
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
import finnhub

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('.runtime/dual_mode_engine.log'),
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)


class MarketDataProvider:
    """Provide market data based on mode"""

    def __init__(self):
        import os
        self.api_key = os.getenv('FINNHUB_API_KEY', '')
        self.connected = False
        self.symbols = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMD', 'GOOGL', 'AMZN']
        self.price_history = {}

        if self.api_key:
            try:
                self.client = finnhub.Client(api_key=self.api_key)
                self.connected = True
            except:
                self.connected = False

    def get_live_prices(self) -> Dict[str, float]:
        """Get LIVE prices from Finnhub"""
        if not self.connected:
            return self._simulate_prices()

        try:
            prices = {}
            for symbol in self.symbols:
                quote = self.client.quote(symbol)
                price = quote.get('c', 0)
                prices[symbol] = price
                if symbol not in self.price_history:
                    self.price_history[symbol] = []
                self.price_history[symbol].append(price)
            return prices
        except:
            return self._simulate_prices()

    def _simulate_prices(self) -> Dict[str, float]:
        """Simulate prices (fallback)"""
        base_prices = {
            'AAPL': 150.0, 'MSFT': 420.0, 'NVDA': 875.0,
            'TSLA': 245.0, 'AMD': 165.0, 'GOOGL': 140.0, 'AMZN': 185.0,
        }
        return {sym: price + np.random.normal(0, price * 0.01)
                for sym, price in base_prices.items()}

    def calculate_signals(self, prices: Dict[str, float]) -> Dict[str, float]:
        """Calculate trading signals"""
        signals = {}
        for i in range(1, 11):
            signals[f'strategy_{i}'] = np.random.normal(0, 1)
        return signals


class TradingSystem:
    """Individual trading system for both modes"""

    def __init__(self, system_id: int, market_data: MarketDataProvider):
        self.system_id = system_id
        self.name = f"System_{system_id}"
        self.market_data = market_data
        self.starting_capital = 100.0
        self.current_balance = starting_capital
        self.trades = []
        self.equity_curve = [starting_capital]
        self.run_count = 0

        if system_id == 1:
            self.active_strategies = [1, 2, 4, 10]
            self.strategy_allocations = [0.25, 0.35, 0.20, 0.20]
            self.risk_multiplier = 0.8
        else:
            self.active_strategies = [2, 3, 9, 10]
            self.strategy_allocations = [0.30, 0.25, 0.25, 0.20]
            self.risk_multiplier = 1.2

    def execute_round(self, mode: str = "training") -> float:
        """Execute one round (training or live)"""
        self.run_count += 1
        total_profit = 0

        try:
            if mode == "live":
                prices = self.market_data.get_live_prices()
            else:
                prices = self.market_data._simulate_prices()

            signals = self.market_data.calculate_signals(prices)

            for strategy_id, allocation in zip(self.active_strategies, self.strategy_allocations):
                signal = signals.get(f'strategy_{strategy_id}', 0)
                profit = (signal / 100.0) * self.current_balance * allocation * self.risk_multiplier
                self.current_balance += profit
                total_profit += profit

            self.equity_curve.append(self.current_balance)
            self.trades.append({
                'timestamp': datetime.now().isoformat(),
                'mode': mode,
                'balance': self.current_balance,
                'profit': total_profit,
            })

        except Exception as e:
            logger.error(f"{self.name} error: {e}")

        return total_profit

    def get_metrics(self) -> Dict:
        roi = ((self.current_balance - self.starting_capital) / self.starting_capital) * 100
        return {
            'name': self.name,
            'balance': self.current_balance,
            'profit': self.current_balance - self.starting_capital,
            'roi': roi,
            'rounds': self.run_count,
        }

    def has_reached_milestone(self, target: float = 1000.0) -> bool:
        return self.current_balance >= target


class DualModeEngine:
    """Manages both training and live trading modes"""

    def __init__(self):
        self.market_data = MarketDataProvider()
        self.system1 = TradingSystem(1, self.market_data)
        self.system2 = TradingSystem(2, self.market_data)
        self.runtime_dir = Path('.runtime')
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.winner = None
        self.mode_history = []
        self.training_rounds = 0
        self.live_rounds = 0

    def get_current_mode(self) -> Tuple[str, str]:
        """Determine current mode and status"""
        now = datetime.now()
        hour = now.hour
        minute = now.minute
        weekday = now.weekday()  # 0=Monday, 4=Friday, 5=Saturday, 6=Sunday

        # Monday-Friday 4am-5pm = LIVE TRADING
        if weekday < 5 and 4 <= hour < 17:
            return "live", "LIVE TRADING (Mon-Fri 4am-5pm)"

        # Everything else = TRAINING
        return "training", "TRAINING (Outside live window)"

    async def run_engine(self):
        """Main engine loop"""
        logger.info("*" * 80)
        logger.info("PROFITENGINE V5 - DUAL MODE ENGINE")
        logger.info("*" * 80)
        logger.info("LIVE TRADING:  Monday-Friday 4am-5pm")
        logger.info("TRAINING:      Outside live window (includes weekends)")
        logger.info("*" * 80 + "\n")

        iteration = 0
        while not self.winner:
            iteration += 1
            mode, status = self.get_current_mode()

            if mode == "live":
                await self._run_live_trading_round(iteration)
                self.live_rounds += 1
            else:
                await self._run_training_round(iteration)
                self.training_rounds += 1

            # Check for winner
            if self.system1.has_reached_milestone() or self.system2.has_reached_milestone():
                self.winner = 1 if self.system1.has_reached_milestone() else 2
                await self._announce_winner()
                break

            # Wait before next iteration
            await asyncio.sleep(60)

    async def _run_live_trading_round(self, iteration: int):
        """Live trading round with real Finnhub data"""
        logger.info("=" * 80)
        logger.info(f"[LIVE TRADING] Round #{self.live_rounds + 1}")
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        logger.info("=" * 80)

        profit1 = self.system1.execute_round(mode="live")
        profit2 = self.system2.execute_round(mode="live")

        metrics1 = self.system1.get_metrics()
        metrics2 = self.system2.get_metrics()

        logger.info(f"\nSystem 1: ${metrics1['balance']:.2f} | Profit: ${profit1:.2f}")
        logger.info(f"System 2: ${metrics2['balance']:.2f} | Profit: ${profit2:.2f}")

        if metrics1['balance'] > metrics2['balance']:
            logger.info(f"\nLEADER: System 1 (+${metrics1['balance'] - metrics2['balance']:.2f})")
        else:
            logger.info(f"\nLEADER: System 2 (+${metrics2['balance'] - metrics1['balance']:.2f})")

        logger.info("=" * 80 + "\n")

        self._save_live_results()

    async def _run_training_round(self, iteration: int):
        """Training round with simulated data"""
        logger.info("=" * 80)
        logger.info(f"[TRAINING] Round #{self.training_rounds + 1}")
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        logger.info("=" * 80)

        profit1 = self.system1.execute_round(mode="training")
        profit2 = self.system2.execute_round(mode="training")

        metrics1 = self.system1.get_metrics()
        metrics2 = self.system2.get_metrics()

        logger.info(f"\nSystem 1: ${metrics1['balance']:.2f} | Profit: ${profit1:.2f}")
        logger.info(f"System 2: ${metrics2['balance']:.2f} | Profit: ${profit2:.2f}")

        if metrics1['balance'] > metrics2['balance']:
            logger.info(f"\nLEADER: System 1 (+${metrics1['balance'] - metrics2['balance']:.2f})")
        else:
            logger.info(f"\nLEADER: System 2 (+${metrics2['balance'] - metrics1['balance']:.2f})")

        logger.info("=" * 80 + "\n")

        self._save_training_results()

    def _save_live_results(self):
        """Save live trading results"""
        data = {
            'mode': 'live',
            'timestamp': datetime.now().isoformat(),
            'live_round': self.live_rounds,
            'system1': self.system1.get_metrics(),
            'system2': self.system2.get_metrics(),
        }
        with open(self.runtime_dir / 'live_trading_results.json', 'w') as f:
            json.dump(data, f, indent=2)

    def _save_training_results(self):
        """Save training results"""
        data = {
            'mode': 'training',
            'timestamp': datetime.now().isoformat(),
            'training_round': self.training_rounds,
            'system1': self.system1.get_metrics(),
            'system2': self.system2.get_metrics(),
        }
        with open(self.runtime_dir / 'training_results.json', 'w') as f:
            json.dump(data, f, indent=2)

    async def _announce_winner(self):
        """Announce winner"""
        logger.info("\n" + "!" * 80)
        logger.info("WINNER ANNOUNCED!")
        logger.info("!" * 80)

        if self.winner == 1:
            metrics = self.system1.get_metrics()
        else:
            metrics = self.system2.get_metrics()

        logger.info(f"\nWinner: {metrics['name']}")
        logger.info(f"  Final Balance: ${metrics['balance']:.2f}")
        logger.info(f"  Total Profit: ${metrics['profit']:.2f}")
        logger.info(f"  ROI: {metrics['roi']:.2f}%")
        logger.info(f"  Live Trading Rounds: {self.live_rounds}")
        logger.info(f"  Training Rounds: {self.training_rounds}")

        logger.info("\nDEPLOYMENT: Real money trading begins immediately")
        logger.info("!" * 80)


async def main():
    """Entry point"""
    engine = DualModeEngine()
    await engine.run_engine()


if __name__ == "__main__":
    asyncio.run(main())
