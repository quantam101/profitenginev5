# Catalyst Scorer Integration Guide

## Overview

The `catalyst_scorer.py` module provides intelligent catalyst detection and scoring for the ProfitEngine trading system. It integrates with Finnhub (news/earnings data) and Alpaca (analyst consensus) to identify trading catalysts and quantify their impact on trading signals.

## Quick Start

### 1. Environment Setup

Set these environment variables:

```bash
export FINNHUB_API_KEY="your-finnhub-key"
export ALPACA_API_KEY="your-alpaca-key"
```

Or configure in your runtime `.env` file:

```
FINNHUB_API_KEY=sk_...
ALPACA_API_KEY=pk_live_...
```

### 2. Basic Usage

```python
from runtime.catalyst_scorer import CatalystScorer

# Create scorer instance
scorer = CatalystScorer()

# Score catalysts (0-100)
score = scorer.score_catalysts('AAPL')
print(f"AAPL Catalyst Score: {score}")  # e.g., 65.0

# Get detailed catalyst information
details = scorer.get_catalyst_details('AAPL')
print(details['catalysts'])  # List of active catalysts with confidence

# Adjust trading signal by catalyst strength
base_signal = 0.75
adjusted_signal = scorer.weight_signal_by_catalyst(base_signal, score)
print(f"Adjusted Signal: {adjusted_signal}")  # 0.75 -> 0.85+
```

## API Reference

### CatalystScorer Class

#### Constructor

```python
CatalystScorer(finnhub_api_key: str, alpaca_api_key: str)
```

Creates a catalyst scorer instance. API keys default to environment variables if not provided.

#### Methods

##### `score_catalysts(symbol: str) → float`

Calculate overall catalyst score (0-100) for a stock symbol.

**Returns:** Float score where:
- 0-20: No catalysts detected
- 20-40: Weak catalysts
- 40-60: Moderate catalysts
- 60-80: Strong catalysts
- 80-100: Very strong catalysts present

**Example:**
```python
score = scorer.score_catalysts('TSLA')
# Returns: 75.5 (high catalyst score)
```

##### `get_catalyst_details(symbol: str) → Dict`

Get comprehensive catalyst information for a symbol.

**Returns:** Dictionary with structure:
```python
{
    'symbol': 'AAPL',
    'total_score': 65.0,
    'catalysts': [
        {
            'type': 'earnings_surprise',
            'source': 'Finnhub Earnings',
            'impact': 0.65,  # 0-1 normalized
            'confidence': 0.90,  # Confidence in detection
            'timestamp': '2024-01-15T10:30:00Z',
            'metadata': {
                'actual_eps': 2.18,
                'estimate_eps': 2.05,
                'surprise_pct': 0.0634
            }
        },
        {
            'type': 'analyst_upgrades',
            'source': 'Alpaca Analyst Data',
            'impact': 0.75,
            'confidence': 0.85,
            'timestamp': '2024-01-15T10:30:00Z',
            'metadata': {
                'consensus_rating': 1.8,  # 1=buy, 5=sell
                'analyst_count': 42
            }
        }
    ],
    'breakdown': {
        'earnings_surprise': 75.0,
        'analyst_upgrades': 50.0,
        'fda_approval': 0,
        'news_sentiment': 30.0,
        'sector_momentum': 0,
        'short_squeeze': 0
    },
    'timestamp': '2024-01-15T10:30:00Z'
}
```

##### `weight_signal_by_catalyst(base_signal_strength: float, catalyst_score: float) → float`

Adjust a trading signal by catalyst strength.

**Parameters:**
- `base_signal_strength`: Original signal (0-1)
- `catalyst_score`: Catalyst score from `score_catalysts()` (0-100)

**Returns:** Adjusted signal strength (0-1)

**Formula:**
```
adjusted = base_signal * (1 + (catalyst_score / 100) * 0.5)
```

This creates a multiplicative adjustment:
- catalyst_score = 0 → no amplification (adjusted = base_signal)
- catalyst_score = 50 → 25% amplification (adjusted = base_signal * 1.25)
- catalyst_score = 100 → 50% amplification (adjusted = base_signal * 1.5)

**Example:**
```python
base_signal = 0.75
catalyst_score = 80.0
adjusted = scorer.weight_signal_by_catalyst(base_signal, catalyst_score)
# adjusted = 0.75 * 1.4 = 1.05, capped at 1.0
```

## Catalyst Types & Scoring

### FDA Approval (Biotech/Pharma)
- **Points:** 100
- **Source:** Finnhub News API
- **Trigger:** "FDA approval", "FDA approved", "FDA breakthrough" in recent news
- **Confidence:** 95%
- **Recency:** Within 30 days

### Earnings Surprise
- **Points:** 75
- **Source:** Finnhub Earnings Surprise API
- **Trigger:** Beat earnings estimate by > 5%
- **Confidence:** 90%
- **Note:** Uses actual vs. estimate EPS

### Analyst Upgrades
- **Points:** 50
- **Source:** Alpaca Analyst Consensus
- **Trigger:** Consensus rating < 2.0 (1=strong buy, 5=strong sell)
- **Confidence:** Scales with analyst count
- **Note:** Weighted by number of analysts

### News Sentiment
- **Points:** 30
- **Source:** Finnhub News API
- **Trigger:** > 50% of recent articles positive
- **Confidence:** Scales with article count
- **Keywords:** surge, beat, gain, profit, bullish, upgrade, rally

### Sector Momentum
- **Points:** 20
- **Source:** Requires external sector data
- **Status:** Placeholder (requires additional integration)

### Short Squeeze
- **Points:** 15
- **Source:** Requires short interest data
- **Status:** Placeholder (requires additional integration)

## Integration Examples

### 1. With Trading Strategy

```python
from runtime.catalyst_scorer import CatalystScorer
from runtime.signal_generator import SignalGenerator

class CatalystAwareStrategy:
    def __init__(self):
        self.scorer = CatalystScorer()
        self.signal_gen = SignalGenerator()
    
    def execute(self, symbol: str) -> Dict:
        # Generate base trading signal
        base_signal = self.signal_gen.calculate_signal(symbol)
        
        # Score catalysts
        catalyst_score = self.scorer.score_catalysts(symbol)
        
        # Adjust signal by catalyst strength
        adjusted_signal = self.scorer.weight_signal_by_catalyst(
            base_signal.strength,
            catalyst_score
        )
        
        # Get details for logging
        details = self.scorer.get_catalyst_details(symbol)
        
        return {
            'symbol': symbol,
            'base_signal': base_signal.strength,
            'catalyst_score': catalyst_score,
            'adjusted_signal': adjusted_signal,
            'catalysts': details['catalysts'],
            'confidence': self._calculate_confidence(
                base_signal.confidence,
                catalyst_score
            )
        }
    
    def _calculate_confidence(self, signal_conf: float, catalyst_score: float) -> float:
        # Higher catalyst score increases overall confidence
        return min(signal_conf * (1 + catalyst_score / 200), 1.0)
```

### 2. With Risk Management

```python
def should_increase_position_size(
    base_signal: float,
    catalyst_score: float,
    max_position_size: float = 10000
) -> float:
    """Increase position size if strong catalysts present."""
    
    adjusted_signal = scorer.weight_signal_by_catalyst(base_signal, catalyst_score)
    
    if catalyst_score >= 80:
        # Strong catalysts: up to 1.5x base position
        return max_position_size * 1.5
    elif catalyst_score >= 60:
        # Moderate catalysts: up to 1.25x base position
        return max_position_size * 1.25
    else:
        # Weak catalysts: standard position
        return max_position_size
```

### 3. With Logging/Monitoring

```python
import json
from runtime.cycle_log import CycleLog

cycle_log = CycleLog()

def log_catalyst_analysis(symbol: str):
    details = scorer.get_catalyst_details(symbol)
    
    cycle_log.log({
        'event': 'catalyst_analysis',
        'symbol': symbol,
        'score': details['total_score'],
        'catalysts': [
            {
                'type': c['type'],
                'impact': c['impact'],
                'confidence': c['confidence']
            }
            for c in details['catalysts']
        ]
    })
    
    print(f"Catalyst analysis logged for {symbol}")
```

## FastAPI Integration

Add these endpoints to your runtime API:

```python
from fastapi import FastAPI, HTTPException
from runtime.catalyst_scorer import CatalystScorer

app = FastAPI()
scorer = CatalystScorer()

@app.post("/api/v1/catalysts/score/{symbol}")
async def score_catalysts_endpoint(symbol: str):
    """Score catalysts for a symbol."""
    try:
        score = scorer.score_catalysts(symbol.upper())
        return {
            'symbol': symbol.upper(),
            'score': score,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/catalysts/details/{symbol}")
async def get_catalysts_endpoint(symbol: str):
    """Get detailed catalyst information."""
    try:
        details = scorer.get_catalyst_details(symbol.upper())
        return details
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/catalysts/adjust-signal")
async def adjust_signal_endpoint(
    base_signal: float,
    catalyst_score: float
):
    """Adjust signal by catalyst score."""
    try:
        adjusted = scorer.weight_signal_by_catalyst(base_signal, catalyst_score)
        return {
            'base_signal': base_signal,
            'catalyst_score': catalyst_score,
            'adjusted_signal': adjusted,
            'amplification_factor': adjusted / base_signal if base_signal > 0 else 1.0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Data Source Configuration

### Finnhub Setup

1. Sign up at https://finnhub.io
2. Create API key in dashboard
3. Set `FINNHUB_API_KEY` environment variable
4. Endpoints used:
   - `/company-news` — News articles
   - `/stock/earnings-surprise` — Earnings data

### Alpaca Setup

1. Create account at https://alpaca.markets
2. Generate API key in dashboard
3. Set `ALPACA_API_KEY` environment variable
4. Endpoints used:
   - `/v2/stocks/estimates` — Analyst consensus

## Performance Notes

- **Caching:** Implement Redis caching for catalyst scores (TTL: 1-6 hours)
- **Rate Limits:** Finnhub free tier has 60 req/min; Alpaca has generous limits
- **Timeout:** All requests have 30-second timeout
- **Error Handling:** Missing data returns 0 for that catalyst type

## Future Enhancements

1. **Sector Momentum:** Integrate sector index data (SPY, QQQ, etc.)
2. **Short Interest:** Add Finviz or SEC data for short squeeze detection
3. **Options Flow:** Monitor unusual options activity
4. **Insider Trading:** Track insider buying/selling signals
5. **Technical Catalysts:** Support/resistance breakouts
6. **Momentum Catalysts:** RSI/MACD divergence signals
7. **Sentiment ML:** Train models on news headlines for better sentiment
8. **Real-time Updates:** WebSocket integration for live updates

## Testing

See `test_catalyst_scorer.py` for comprehensive test suite covering:
- Score calculation
- API integration mocking
- Catalyst detection logic
- Signal adjustment formula
- Error handling
