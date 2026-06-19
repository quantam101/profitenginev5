"""
Catalyst Scorer Integration Examples

This file contains real-world examples of using the catalyst scoring system
in various contexts: trading strategies, risk management, logging, and APIs.

Run individual examples with:
    python -c "from catalyst_scorer_examples import example_1; example_1()"
"""

import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

# Configure logging for examples
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Example 1: Basic Catalyst Scoring
# ============================================================================

def example_1_basic_scoring():
    """Example 1: Get catalyst score for a symbol."""
    from catalyst_scorer import CatalystScorer

    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Catalyst Scoring")
    print("="*70)

    # Initialize scorer
    scorer = CatalystScorer()

    # Score catalysts for a few symbols
    symbols = ['AAPL', 'TSLA', 'XBIO', 'MRNA']

    for symbol in symbols:
        score = scorer.score_catalysts(symbol)
        print(f"{symbol:6s} — Catalyst Score: {score:6.1f}/100")

    print("\nScore Ranges:")
    print("  0-20:  No catalysts detected")
    print("  20-40: Weak catalysts (minor event)")
    print("  40-60: Moderate catalysts (notable event)")
    print("  60-80: Strong catalysts (significant event)")
    print("  80-100: Very strong catalysts (major event)")


# ============================================================================
# Example 2: Detailed Catalyst Analysis
# ============================================================================

def example_2_detailed_analysis():
    """Example 2: Get detailed catalyst information."""
    from catalyst_scorer import CatalystScorer

    print("\n" + "="*70)
    print("EXAMPLE 2: Detailed Catalyst Analysis")
    print("="*70)

    scorer = CatalystScorer()
    symbol = 'AAPL'

    # Get detailed catalyst information
    details = scorer.get_catalyst_details(symbol)

    print(f"\nCatalyst Analysis for {symbol}:")
    print(f"  Total Score: {details['total_score']:.1f}/100")
    print(f"  Timestamp: {details['timestamp']}")

    print(f"\nActive Catalysts:")
    for catalyst in details['catalysts']:
        print(f"  • {catalyst['type'].upper()}")
        print(f"    Source: {catalyst['source']}")
        print(f"    Impact: {catalyst['impact']:.2%}")
        print(f"    Confidence: {catalyst['confidence']:.0%}")
        if catalyst['metadata']:
            print(f"    Details: {json.dumps(catalyst['metadata'], indent=6)}")

    print(f"\nScore Breakdown:")
    for catalyst_type, points in sorted(
        details['breakdown'].items(),
        key=lambda x: x[1],
        reverse=True
    ):
        if points > 0:
            print(f"  {catalyst_type:20s}: {points:6.1f} points")


# ============================================================================
# Example 3: Signal Adjustment
# ============================================================================

def example_3_signal_adjustment():
    """Example 3: Adjust trading signals based on catalysts."""
    from catalyst_scorer import CatalystScorer

    print("\n" + "="*70)
    print("EXAMPLE 3: Signal Adjustment (Amplification)")
    print("="*70)

    scorer = CatalystScorer()
    symbol = 'AAPL'

    # Get catalyst score
    catalyst_score = scorer.score_catalysts(symbol)

    # Example trading signals from technical analysis
    technical_signals = [
        ('RSI Breakout', 0.65),
        ('MACD Crossover', 0.75),
        ('Moving Average Cross', 0.55),
        ('Volume Surge', 0.45),
        ('Support Break', 0.85),
    ]

    print(f"\n{symbol} — Catalyst Score: {catalyst_score:.1f}/100")
    print("\nSignal Adjustment (Catalyst Amplification):")
    print("-" * 70)
    print(f"{'Signal Type':<25} {'Base':<8} {'Adjusted':<8} {'Boost':<8} {'Action'}")
    print("-" * 70)

    for signal_name, base_signal in technical_signals:
        adjusted = scorer.weight_signal_by_catalyst(base_signal, catalyst_score)
        boost_factor = adjusted / base_signal if base_signal > 0 else 1.0
        boost_pct = (boost_factor - 1) * 100

        action = "BUY" if adjusted > 0.70 else "HOLD" if adjusted > 0.50 else "WAIT"

        print(
            f"{signal_name:<25} {base_signal:.3f}    {adjusted:.3f}    "
            f"{boost_pct:+.0f}%     {action}"
        )

    print("\nFormula: adjusted = base × (1 + (catalyst_score / 100) × 0.5)")
    print(f"  At catalyst_score=0: multiplier = 1.0 (no change)")
    print(f"  At catalyst_score={catalyst_score:.0f}: multiplier = {1 + (catalyst_score/100)*0.5:.2f}")


# ============================================================================
# Example 4: Trading Strategy Integration
# ============================================================================

class CatalystAwareTradingStrategy:
    """Example trading strategy that uses catalyst scoring."""

    def __init__(self):
        from catalyst_scorer import CatalystScorer
        self.scorer = CatalystScorer()

    def calculate_buy_signal(self, symbol: str, rsi: float, macd_signal: float) -> Dict:
        """
        Calculate a buy signal adjusted by catalyst strength.

        Args:
            symbol: Stock ticker
            rsi: RSI value (0-100)
            macd_signal: MACD signal (e.g., 0-1)

        Returns:
            Trade decision with details
        """
        # Calculate base signal from technicals
        rsi_signal = (100 - rsi) / 100 if rsi > 50 else rsi / 100
        base_signal = (rsi_signal + macd_signal) / 2

        # Score catalysts
        catalyst_score = self.scorer.score_catalysts(symbol)

        # Adjust signal by catalyst strength
        adjusted_signal = self.scorer.weight_signal_by_catalyst(base_signal, catalyst_score)

        # Get catalyst details
        catalyst_details = self.scorer.get_catalyst_details(symbol)

        # Determine action
        if adjusted_signal > 0.75:
            action = 'BUY'
            position_size = 'LARGE'  # 150 shares
        elif adjusted_signal > 0.65:
            action = 'BUY'
            position_size = 'MEDIUM'  # 100 shares
        elif adjusted_signal > 0.50:
            action = 'BUY'
            position_size = 'SMALL'  # 50 shares
        else:
            action = 'WAIT'
            position_size = 'NONE'

        return {
            'symbol': symbol,
            'action': action,
            'position_size': position_size,
            'base_signal': base_signal,
            'catalyst_score': catalyst_score,
            'adjusted_signal': adjusted_signal,
            'amplification': adjusted_signal / base_signal if base_signal > 0 else 1.0,
            'active_catalysts': [c['type'] for c in catalyst_details['catalysts']],
            'confidence': self._calculate_confidence(base_signal, catalyst_score),
        }

    def _calculate_confidence(self, base_signal: float, catalyst_score: float) -> float:
        """Calculate overall confidence in the trade."""
        # Higher catalyst score increases confidence
        return min(base_signal * (1 + catalyst_score / 200), 1.0)


def example_4_trading_strategy():
    """Example 4: Using catalyst scores in a trading strategy."""
    print("\n" + "="*70)
    print("EXAMPLE 4: Trading Strategy Integration")
    print("="*70)

    strategy = CatalystAwareTradingStrategy()

    # Example: Analyze AAPL with RSI=35 (oversold), MACD signal=0.80 (strong)
    decision = strategy.calculate_buy_signal('AAPL', rsi=35, macd_signal=0.80)

    print(f"\nTrade Decision for {decision['symbol']}:")
    print(f"  Action: {decision['action']}")
    print(f"  Position Size: {decision['position_size']}")
    print(f"  Base Signal: {decision['base_signal']:.3f}")
    print(f"  Catalyst Score: {decision['catalyst_score']:.1f}/100")
    print(f"  Adjusted Signal: {decision['adjusted_signal']:.3f}")
    print(f"  Amplification: {decision['amplification']:.2f}x")
    print(f"  Confidence: {decision['confidence']:.0%}")
    print(f"  Active Catalysts: {', '.join(decision['active_catalysts']) or 'None'}")


# ============================================================================
# Example 5: Risk Management - Position Sizing
# ============================================================================

def example_5_position_sizing():
    """Example 5: Scale position size based on catalysts."""
    from catalyst_scorer import CatalystScorer

    print("\n" + "="*70)
    print("EXAMPLE 5: Risk Management - Position Sizing")
    print("="*70)

    scorer = CatalystScorer()
    base_position_size = 100  # Base position: 100 shares

    symbols = [
        ('AAPL', 'Stable, mature company'),
        ('TSLA', 'Volatile, growth stock'),
        ('XBIO', 'Small-cap biotech'),
        ('NVDA', 'AI/chip leader'),
    ]

    print(f"\nBase Position Size: {base_position_size} shares")
    print("\nPosition Sizing Rules:")
    print("  Catalyst Score 0-20:   100 shares (baseline)")
    print("  Catalyst Score 20-40:  100 shares (baseline)")
    print("  Catalyst Score 40-60:  125 shares (+25%)")
    print("  Catalyst Score 60-80:  150 shares (+50%)")
    print("  Catalyst Score 80-100: 200 shares (+100%)")

    print("\n" + "-"*70)
    print(f"{'Symbol':<10} {'Catalyst Score':<20} {'Position Size':<15} {'Risk Level'}")
    print("-"*70)

    for symbol, description in symbols:
        catalyst_score = scorer.score_catalysts(symbol)

        if catalyst_score >= 80:
            position = int(base_position_size * 2.0)
            risk = 'AGGRESSIVE'
        elif catalyst_score >= 60:
            position = int(base_position_size * 1.5)
            risk = 'ELEVATED'
        elif catalyst_score >= 40:
            position = int(base_position_size * 1.25)
            risk = 'MODERATE'
        else:
            position = base_position_size
            risk = 'CONSERVATIVE'

        print(
            f"{symbol:<10} {catalyst_score:6.1f}/100            "
            f"{position:6d} shares      {risk}"
        )


# ============================================================================
# Example 6: Batch Processing Multiple Symbols
# ============================================================================

def example_6_batch_processing():
    """Example 6: Score multiple symbols efficiently."""
    from catalyst_scorer import CatalystScorer

    print("\n" + "="*70)
    print("EXAMPLE 6: Batch Processing Multiple Symbols")
    print("="*70)

    scorer = CatalystScorer()

    # Watchlist: Different sectors
    watchlist = [
        ('AAPL', 'Technology'),
        ('MSFT', 'Technology'),
        ('JPM', 'Finance'),
        ('KO', 'Consumer Staples'),
        ('XOM', 'Energy'),
        ('JNJ', 'Healthcare'),
        ('TSLA', 'Automotive'),
    ]

    print("\nScoring all symbols...")
    results = []

    for symbol, sector in watchlist:
        score = scorer.score_catalysts(symbol)
        results.append({
            'symbol': symbol,
            'sector': sector,
            'catalyst_score': score,
        })

    # Sort by catalyst score (highest first)
    results.sort(key=lambda x: x['catalyst_score'], reverse=True)

    print("\nCatalyst Scores by Sector:")
    print("-" * 50)
    print(f"{'Symbol':<10} {'Sector':<20} {'Catalyst Score':<15}")
    print("-" * 50)

    for result in results:
        print(
            f"{result['symbol']:<10} {result['sector']:<20} "
            f"{result['catalyst_score']:6.1f}/100"
        )

    # Find best catalyst play
    best = max(results, key=lambda x: x['catalyst_score'])
    print(f"\nBest Catalyst Play: {best['symbol']} ({best['sector']}) — "
          f"{best['catalyst_score']:.1f} points")


# ============================================================================
# Example 7: Logging and Monitoring
# ============================================================================

def example_7_logging_monitoring():
    """Example 7: Log catalyst analysis for transparency and monitoring."""
    from catalyst_scorer import CatalystScorer

    print("\n" + "="*70)
    print("EXAMPLE 7: Logging and Monitoring")
    print("="*70)

    scorer = CatalystScorer()
    symbol = 'AAPL'

    details = scorer.get_catalyst_details(symbol)

    # Create a log entry
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'event': 'catalyst_analysis',
        'symbol': symbol,
        'catalyst_score': details['total_score'],
        'catalysts': [
            {
                'type': c['type'],
                'impact': c['impact'],
                'confidence': c['confidence'],
                'source': c['source'],
            }
            for c in details['catalysts']
        ],
        'breakdown': details['breakdown'],
    }

    print(f"\nLog Entry (JSON):")
    print(json.dumps(log_entry, indent=2))

    print(f"\nLogging to file:")
    print(f"  Event: catalyst_analysis")
    print(f"  Symbol: {symbol}")
    print(f"  Score: {details['total_score']:.1f}")
    print(f"  Catalysts: {len(details['catalysts'])} active")
    print(f"  Timestamp: {log_entry['timestamp']}")


# ============================================================================
# Example 8: Error Handling and Edge Cases
# ============================================================================

def example_8_error_handling():
    """Example 8: Handling errors gracefully."""
    from catalyst_scorer import CatalystScorer

    print("\n" + "="*70)
    print("EXAMPLE 8: Error Handling and Edge Cases")
    print("="*70)

    scorer = CatalystScorer()

    # Test various edge cases
    test_cases = [
        ('AAPL', 'Normal stock'),
        ('INVALID', 'Non-existent symbol'),
        ('PENNY', 'Penny stock (no data)'),
        ('', 'Empty symbol'),
    ]

    print("\nTesting error handling:")
    print("-" * 50)

    for symbol, description in test_cases:
        try:
            score = scorer.score_catalysts(symbol)
            print(f"{symbol:12s} ({description:25s}): {score:6.1f}")
        except Exception as e:
            print(f"{symbol:12s} ({description:25s}): ERROR — {e}")

    print("\nNote: Returns 0.0 if no data found (safe default)")
    print("      Never raises exception — always returns a score")


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Run all examples."""
    examples = [
        (example_1_basic_scoring, "Basic Catalyst Scoring"),
        (example_2_detailed_analysis, "Detailed Analysis"),
        (example_3_signal_adjustment, "Signal Adjustment"),
        (example_4_trading_strategy, "Trading Strategy"),
        (example_5_position_sizing, "Position Sizing"),
        (example_6_batch_processing, "Batch Processing"),
        (example_7_logging_monitoring, "Logging/Monitoring"),
        (example_8_error_handling, "Error Handling"),
    ]

    print("\n" + "="*70)
    print("CATALYST SCORER — INTEGRATION EXAMPLES")
    print("="*70)
    print("\nRun individual examples:")
    print("  python catalyst_scorer_examples.py 1")
    print("  python catalyst_scorer_examples.py 2")
    print("  ... etc")
    print("\nOr run all examples:")
    print("  python catalyst_scorer_examples.py all")

    import sys

    if len(sys.argv) > 1:
        choice = sys.argv[1]

        if choice == 'all':
            for func, name in examples:
                try:
                    func()
                except Exception as e:
                    print(f"\nError in {name}: {e}")
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(examples):
                    examples[idx][0]()
                else:
                    print(f"Invalid example number. Choose 1-{len(examples)}")
            except ValueError:
                print(f"Invalid example number: {choice}")
    else:
        print("\nRun with an example number (1-8) or 'all'")


if __name__ == '__main__':
    main()
