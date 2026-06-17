# Signal Correlation Analyzer

## Overview

The `SignalCorrelationAnalyzer` is a rolling correlation engine that analyzes the interdependencies between the 4 primary trading agents:
- **Technical Agent** — RSI, MACD, trend alignment
- **Microstructure Agent** — liquidity, order flow, bid-ask dynamics
- **Regime Agent** — market volatility and trend regime classification
- **Portfolio Agent** — position sizing and risk management

The analyzer maintains a **rolling 20-trade window** and provides:
1. **Correlation matrix** between agent confidence signals
2. **Correlated failure detection** — identifies when 2+ agents fail together
3. **Auto-weighting system** — adjusts trust in each agent based on diversity + performance
4. **Diversity reporting** — comprehensive analysis with actionable recommendations

## Architecture

### Core Components

```
SignalCorrelationAnalyzer
├── record_trade()                    # Record signals from all 4 agents
├── calculate_correlation_matrix()    # 4x4 correlation matrix
├── detect_correlated_failures()      # Find failure patterns
├── adjust_agent_weights()            # Rebalance trust based on diversity
├── generate_diversity_report()       # Comprehensive analysis report
└── get_aggregated_signal()           # Weighted confidence score
```

### Data Structures

**Signal History (per agent):**
```python
{
    "confidence": float,          # Primary metric (0-1)
    "metric_1": float,            # Agent-specific metric
    "metric_2": float,            # Agent-specific metric
    ...
}
```

**Trade Outcomes:**
- `1` = winning trade
- `0` = losing trade
- `None` = pending/unknown

**Agent Weights:**
- Initialized at 0.25 each (equal trust)
- Dynamically adjusted based on:
  - **Diversity component (60% default)** — penalizes correlation with other agents
  - **Performance component (40% default)** — rewards agents whose confidence predicts wins

## Usage

### Basic Integration into Synthesis Engine

```python
from synthesis_engine import ProposalSynthesisEngine

engine = ProposalSynthesisEngine(config)

# When generating a trade proposal:
proposal = engine.generate(market_snapshot, account_equity, daily_pnl)

# The analyzer automatically:
# 1. Records all 4 agent signals
# 2. Adjusts confidence using diversity-weighted averaging
# 3. Adds diversity alerts to rationale if correlation is high

# After trade closes, record outcome:
engine.record_trade_outcome(outcome=1)  # 1=win, 0=loss

# Get full correlation analysis:
report = engine.get_correlation_analysis()
print(report)
```

### Standalone Usage

```python
from signal_correlation_analyzer import SignalCorrelationAnalyzer

analyzer = SignalCorrelationAnalyzer(window_size=20)

# Record trades
for trade in trades:
    analyzer.record_trade(
        technical=technical_signal,
        microstructure=microstructure_signal,
        regime=regime_signal,
        portfolio=portfolio_signal,
        outcome=trade_result  # 1 or 0
    )

# Calculate correlation matrix
corr_matrix = analyzer.calculate_correlation_matrix()
# Returns 4x4 numpy array with Pearson correlations

# Detect correlated failures
failures = analyzer.detect_correlated_failures(correlation_threshold=0.75)
# Returns list of agent pairs that tend to fail together

# Adjust weights
weights = analyzer.adjust_agent_weights(
    diversity_importance=0.6,
    performance_importance=0.4
)
# Returns: {"technical": 0.28, "microstructure": 0.22, ...}

# Full analysis
report = analyzer.generate_diversity_report()
# Returns comprehensive report with matrix, weights, recommendations
```

## Key Methods

### `calculate_correlation_matrix() → np.ndarray`
Calculates a 4x4 Pearson correlation matrix between agent confidence signals over the rolling window.

**Returns:**
- 4x4 numpy array where element [i,j] is correlation between agents i and j
- Diagonal elements are 1.0 (self-correlation)
- Values range from -1 to 1

**Example Output:**
```
[[1.0,   0.82,  0.45,  0.30],
 [0.82,  1.0,   0.38,  0.25],
 [0.45,  0.38,  1.0,   0.60],
 [0.30,  0.25,  0.60,  1.0 ]]
```

### `detect_correlated_failures(correlation_threshold=0.75) → List[Dict]`
Identifies pairs of agents that consistently fail together (high correlation of losses).

**Returns:**
List of detected patterns with structure:
```python
{
    "agent_pair": ["technical", "regime"],
    "correlation": 0.87,
    "shared_losses": 5,
    "severity": "high",  # or "medium"
    "timestamp": "2024-06-17T10:30:45.123456"
}
```

**Severity levels:**
- `high`: correlation > 0.85 (very strong co-failure pattern)
- `medium`: correlation 0.75–0.85 (notable pattern)

### `adjust_agent_weights(diversity_importance=0.6, performance_importance=0.4) → Dict[str, float]`
Rebalances trust in each agent based on:
1. **Diversity score** — how uncorrelated is this agent from others?
2. **Performance score** — how well does this agent's confidence predict wins?

**Parameters:**
- `diversity_importance` (0-1): How much to weight independence from other agents
- `performance_importance` (0-1): How much to weight predictive accuracy

**Returns:**
```python
{
    "technical": 0.30,
    "microstructure": 0.18,
    "regime": 0.35,
    "portfolio": 0.17
}  # Sum = 1.0
```

**Weighting Logic:**
```
combined_score = (diversity_score × diversity_importance) 
               + (performance_score × performance_importance)

final_weight = combined_score / sum(all_combined_scores)
```

### `generate_diversity_report() → Dict`
Comprehensive analysis combining all metrics into a actionable report.

**Returns full report structure:**
```python
{
    "timestamp": "2024-06-17T10:30:45.123456",
    "window_size": 20,
    "trades_analyzed": 18,
    "correlation_matrix": {
        "values": [[1.0, ...], ...],
        "agent_order": ["technical", "microstructure", "regime", "portfolio"],
        "average_correlation": 0.52
    },
    "agent_weights": {
        "technical": 0.30,
        "microstructure": 0.18,
        "regime": 0.35,
        "portfolio": 0.17
    },
    "diversity_score": 0.68,  # 1.0 = perfect diversity, 0.0 = all identical
    "correlated_failures_detected": 1,
    "correlated_failures": [...],
    "performance_metrics": {
        "win_rate": 0.556,  # 5 wins out of 9 trades with outcomes
        "total_trades_with_outcomes": 9
    },
    "recommendations": [
        "GOOD: Signal diversity is healthy...",
        "INFO: Agent weighting is imbalanced..."
    ]
}
```

### `get_aggregated_signal(technical, microstructure, regime, portfolio) → float`
Generates a single weighted confidence score using current agent weights.

**Formula:**
```
aggregated = (technical.confidence × weight_technical)
           + (micro.confidence × weight_microstructure)
           + (regime.confidence × weight_regime)
           + (0.75 × weight_portfolio)
```

**Example:**
```python
signal = analyzer.get_aggregated_signal(
    technical=TechnicalSignal(confidence=0.75),
    microstructure=MicrostructureSignal(confidence=0.60),
    regime=RegimeSignal(regime_confidence=0.80),
    portfolio=PortfolioSignal()
)
# Returns 0.71 (weighted by current weights)
```

## Integration with Synthesis Engine

The analyzer is fully integrated into `ProposalSynthesisEngine`:

### In `generate()`:
1. Records all 4 agent signals after analysis
2. Calculates diversity-adjusted confidence: `0.7 × base_confidence + 0.3 × diversity_adjusted`
3. Adds diversity alerts to trade rationale if correlation > 0.6

### In `record_trade_outcome()`:
Updates the outcome for the most recent recorded trade signals

### In `get_correlation_analysis()`:
Returns full report for monitoring/auditing

## Correlation Interpretation

| Correlation | Meaning | Implication |
|-------------|---------|------------|
| 0.0–0.3 | Weakly correlated | Good — agents provide independent signals |
| 0.3–0.6 | Moderately correlated | Acceptable — some redundancy but not excessive |
| 0.6–0.8 | Strongly correlated | Warning — agents may be seeing same patterns |
| 0.8–1.0 | Very strongly correlated | Critical — agents are nearly identical, reduced diversification |

## Failure Correlation Interpretation

High correlation of **failures** (not just signals) indicates systematic weakness:

**Example:** Technical and Regime both high confidence, but trade loses 40% of the time together.
- **Recommendation:** Reduce position size when both agents are highly confident
- **Root cause:** Both agents may be fooled by similar market dynamics (e.g., false breakouts)

## Performance Scoring

For each agent, performance score = correlation between agent confidence and trade outcomes.
- Normalized to 0–1 range: `(correlation + 1.0) / 2.0`
- Score near 1.0 = agent's confidence strongly predicts wins
- Score near 0.5 = agent's confidence is neutral/random
- Score near 0.0 = agent's confidence predicts losses (inverse signal)

## File Structure

```
trading-control/
├── signal_correlation_analyzer.py    # Main analyzer (374 lines)
├── synthesis_engine.py               # Updated with analyzer integration
├── test_correlation_analyzer.py      # Test suite with examples
└── CORRELATION_ANALYZER_README.md    # This file
```

## Testing

Run the comprehensive test suite:
```bash
cd trading-control
python test_correlation_analyzer.py
```

**Test coverage:**
1. `test_basic_correlation_matrix()` — Verifies matrix calculation with correlated signals
2. `test_detect_correlated_failures()` — Tests failure pattern detection
3. `test_adjust_weights()` — Validates weight rebalancing
4. `test_diversity_report()` — Full report generation and format
5. `test_aggregated_signal()` — Weighted signal aggregation

## Configuration

Default settings in `SignalCorrelationAnalyzer.__init__()`:
- Window size: 20 trades (configurable)
- Failure correlation threshold: 0.75 (configurable in `detect_correlated_failures()`)
- Diversity weight: 0.6, Performance weight: 0.4 (configurable in `adjust_agent_weights()`)

## Performance Characteristics

- **Time Complexity:** O(n) for n trades in window (typically 20)
- **Space Complexity:** O(n × 4) for signal history + O(16) for correlation matrix
- **Computation:** Matrix calculation ~0.1ms, full report ~1ms on modern hardware
- **No blocking operations** — suitable for real-time trading

## Edge Cases Handled

1. **Insufficient data** (<2 trades): Returns identity correlation matrix
2. **Constant signals** (all same confidence): NaN values replaced with 0.0
3. **No outcomes recorded**: Performance scoring returns neutral 0.5
4. **All trades pending**: Win rate reported as `None`
5. **Single agent failing**: Correctly identified even without pairs

## Future Enhancements

Potential extensions:
- Regime-specific correlation (e.g., correlation differs in bull vs bear)
- Time-decay weighting (recent trades weighted higher)
- Multi-timeframe analysis (1min, 5min, hourly correlation patterns)
- Spectral analysis for cyclical failure patterns
- Cross-correlation lags (agent A leading agent B failures)
