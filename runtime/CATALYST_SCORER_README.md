# ProfitEngine v5 — Catalyst Scoring System

## Overview

The Catalyst Scorer is an intelligent detection and scoring module for identifying potential price catalysts in equities trading. It integrates with Finnhub (news/earnings) and Alpaca (analyst consensus) APIs to quantify the strength of upcoming catalysts and amplify trading signals accordingly.

**Key Feature:** Converts raw catalyst data into a normalized 0-100 score that multiplies trading signal confidence.

## What is a Catalyst?

In trading, a **catalyst** is an upcoming event or discovery that may cause significant price movement:

- **FDA Approval** (biotech) — Regulatory win
- **Earnings Surprise** — Beat guidance by >5%
- **Analyst Upgrade** — Consensus shifts to buy
- **Positive News** — > 50% recent articles are bullish
- **Short Squeeze** — High short interest + bullish signal
- **Sector Momentum** — Sector outperforming indices

## Features

### 1. Catalyst Detection
Automatically detects 6+ catalyst types across multiple data sources:
- FDA drug approvals (biotech/pharma)
- Earnings surprises (beat/miss)
- Analyst rating changes
- News sentiment analysis
- Sector relative strength
- Short squeeze potential

### 2. Scoring System
Converts catalysts into a 0-100 normalized score:
- **0-20:** No catalysts
- **20-40:** Weak catalysts (minor event)
- **40-60:** Moderate catalysts (notable event)
- **60-80:** Strong catalysts (significant event)
- **80-100:** Very strong catalysts (major event)

### 3. Signal Amplification
Adjusts trading signals based on catalyst strength:
```
adjusted_signal = base_signal × (1 + catalyst_score/100 × 0.5)
```

At catalyst_score=100, a 0.75 signal becomes 1.0 (50% boost).

### 4. Detailed Reporting
Returns comprehensive catalyst breakdown:
```python
{
    'symbol': 'AAPL',
    'total_score': 65.0,
    'catalysts': [
        {
            'type': 'earnings_surprise',
            'impact': 0.65,
            'confidence': 0.90,
            'metadata': {...}
        }
    ],
    'breakdown': {
        'earnings_surprise': 75,
        'analyst_upgrades': 50,
        'news_sentiment': 30
    }
}
```

## Architecture

```
CatalystScorer (Main Class)
├── Finnhub Integration
│   ├── Company News API (news sentiment, FDA approvals)
│   ├── Earnings Surprise API (earnings beats)
│   └── Company News Search (keyword matching)
├── Alpaca Integration
│   ├── Analyst Consensus (rating changes)
│   └── Estimates (analyst count, target prices)
└── Scoring Engine
    ├── Score Calculation (0-100)
    ├── Detail Extraction (catalyst metadata)
    └── Signal Weighting (amplification formula)
```

## Installation

### 1. Copy Module

The module is located at:
```
runtime/catalyst_scorer.py
```

### 2. Install Dependencies

```bash
pip install httpx>=0.28.0  # HTTP client for API calls
pip install pytest>=8.3.0   # For running tests
```

Dependencies are already in `requirements.txt`.

### 3. Set API Keys

Obtain free API keys:

**Finnhub:**
1. Go to https://finnhub.io
2. Sign up (free tier available)
3. Get API key from dashboard
4. Set: `export FINNHUB_API_KEY="sk_..."`

**Alpaca:**
1. Go to https://alpaca.markets
2. Create account
3. Generate API key
4. Set: `export ALPACA_API_KEY="pk_live_..."`

Or set in `.env`:
```
FINNHUB_API_KEY=sk_...
ALPACA_API_KEY=pk_live_...
```

## Usage

### Quick Start

```python
from runtime.catalyst_scorer import CatalystScorer

# Create scorer instance
scorer = CatalystScorer()

# Get catalyst score (0-100)
score = scorer.score_catalysts('AAPL')
print(f"AAPL Catalyst Score: {score}")  # e.g., 65

# Get detailed catalyst information
details = scorer.get_catalyst_details('AAPL')
print(f"Active Catalysts: {details['catalysts']}")

# Adjust trading signal by catalyst strength
base_signal = 0.75
adjusted = scorer.weight_signal_by_catalyst(base_signal, score)
print(f"Signal: {base_signal} → {adjusted}")
```

### In Trading Strategy

```python
from runtime.catalyst_scorer import CatalystScorer

class TradingStrategy:
    def __init__(self):
        self.scorer = CatalystScorer()
    
    def calculate_position_size(self, symbol: str, base_size: int = 100) -> int:
        """Increase position size if strong catalysts present."""
        
        # Score catalysts
        catalyst_score = self.scorer.score_catalysts(symbol)
        
        # Scale position size by catalyst strength
        if catalyst_score >= 80:
            return base_size * 2      # 200 shares if strong catalyst
        elif catalyst_score >= 60:
            return base_size * 1.5    # 150 shares if moderate catalyst
        else:
            return base_size          # 100 shares baseline
    
    def execute_trade(self, symbol: str):
        # Get base signal from technical indicators
        base_signal = self.calculate_technical_signal(symbol)
        
        # Adjust by catalysts
        catalyst_score = self.scorer.score_catalysts(symbol)
        adjusted_signal = self.scorer.weight_signal_by_catalyst(
            base_signal,
            catalyst_score
        )
        
        # Get catalyst details for logging/transparency
        details = self.scorer.get_catalyst_details(symbol)
        
        print(f"Trade {symbol}:")
        print(f"  Base Signal: {base_signal:.3f}")
        print(f"  Catalyst Score: {catalyst_score:.1f}/100")
        print(f"  Adjusted Signal: {adjusted_signal:.3f}")
        print(f"  Active Catalysts: {[c['type'] for c in details['catalysts']]}")
        
        # Place trade if signal strong enough
        if adjusted_signal > 0.70:
            self.place_buy_order(symbol)
```

### FastAPI Integration

Add these endpoints to your runtime API:

```python
from fastapi import FastAPI
from runtime.catalyst_scorer import CatalystScorer

app = FastAPI()
scorer = CatalystScorer()

@app.post("/api/v1/catalysts/score/{symbol}")
async def get_catalyst_score(symbol: str):
    """Get catalyst score for a symbol."""
    score = scorer.score_catalysts(symbol.upper())
    return {
        'symbol': symbol.upper(),
        'catalyst_score': score,
        'strength': classify_strength(score)
    }

@app.get("/api/v1/catalysts/details/{symbol}")
async def get_catalyst_details(symbol: str):
    """Get detailed catalyst breakdown."""
    return scorer.get_catalyst_details(symbol.upper())

@app.post("/api/v1/catalysts/adjust-signal")
async def adjust_signal(base_signal: float, catalyst_score: float):
    """Adjust trading signal by catalyst score."""
    adjusted = scorer.weight_signal_by_catalyst(base_signal, catalyst_score)
    return {
        'base_signal': base_signal,
        'catalyst_score': catalyst_score,
        'adjusted_signal': adjusted,
        'amplification_factor': adjusted / base_signal if base_signal > 0 else 1.0
    }

def classify_strength(score: float) -> str:
    if score >= 80:
        return 'very_strong'
    elif score >= 60:
        return 'strong'
    elif score >= 40:
        return 'moderate'
    elif score >= 20:
        return 'weak'
    else:
        return 'none'
```

## Catalyst Types

### 1. FDA Approval (100 points)
**Source:** Finnhub News API  
**Trigger:** "FDA approval", "FDA approved", "FDA breakthrough" in recent news  
**Confidence:** 95%  
**Recency:** Within 30 days

Used for biotech/pharma stocks. A successful FDA approval is typically the most significant catalyst.

**Example:**
```
Headline: "XYZ Pharma Gets FDA Approval for COVID-19 Drug"
Score Added: +100 points
```

### 2. Earnings Surprise (75 points)
**Source:** Finnhub Earnings Surprise API  
**Trigger:** Beat earnings by > 5%  
**Confidence:** 90%  
**Formula:** `(actual_eps - estimate_eps) / estimate_eps > 0.05`

A significant earnings beat indicates management execution.

**Example:**
```
Actual EPS: $2.50, Estimate: $2.30
Beat: (2.50 - 2.30) / 2.30 = 8.7% ✓ (> 5%)
Score Added: +75 points
```

### 3. Analyst Upgrades (50 points)
**Source:** Alpaca Analyst Consensus API  
**Trigger:** Consensus rating < 2.0 (scale: 1=strong buy, 5=strong sell)  
**Confidence:** Scales with analyst count  

Wall Street consensus shift is a strong indicator of sentiment change.

**Example:**
```
Consensus Rating: 1.8 (strong buy range)
Analyst Count: 42
Confidence: 0.85 (high)
Score Added: +50 points
```

### 4. News Sentiment (30 points)
**Source:** Finnhub News API  
**Trigger:** > 50% of recent articles positive  
**Confidence:** Scales with article count  
**Keywords:** surge, beat, gain, profit, bullish, upgrade, rally

Positive sentiment can precede actual price moves.

**Example:**
```
Recent 20 Articles:
  - Positive: 13
  - Negative: 7
  Ratio: 65% positive ✓ (> 50%)
Score Added: +30 points
```

### 5. Sector Momentum (20 points)
**Status:** Placeholder for future implementation  
**Source:** Sector indices (SPY, QQQ, XLK, etc.)  
**Trigger:** Sector outperforming S&P 500

### 6. Short Squeeze (15 points)
**Status:** Placeholder for future implementation  
**Source:** Short interest data (Finviz, SEC)  
**Trigger:** Short interest > 20% of float + bullish signal

## Signal Weighting Formula

The catalyst score modifies trading signals using multiplicative amplification:

```
adjusted_signal = base_signal × (1 + (catalyst_score / 100) × 0.5)
```

**Amplification Factor:**
- At catalyst_score = 0: amplification = 1.0 (no change)
- At catalyst_score = 50: amplification = 1.25 (+25%)
- At catalyst_score = 100: amplification = 1.5 (+50%)

**Examples:**

| Base Signal | Catalyst Score | Amplification | Adjusted Signal |
|---|---|---|---|
| 0.50 | 0 | 1.0x | 0.50 |
| 0.50 | 50 | 1.25x | 0.625 |
| 0.50 | 100 | 1.5x | 0.75 |
| 0.75 | 50 | 1.25x | 0.9375 |
| 0.75 | 100 | 1.5x | 1.0 (capped) |
| 0.90 | 100 | 1.5x | 1.0 (capped) |

**Key Properties:**
- Monotonic: Higher catalyst score always increases signal
- Capped: Result never exceeds 1.0
- Proportional: Effect scales with base signal strength
- Reversible: No catalyst (score=0) leaves signal unchanged

## Testing

The module includes comprehensive unit tests covering:

### Run All Tests
```bash
cd runtime
pytest test_catalyst_scorer.py -v
```

### Test Categories

**Catalyst Detection:**
- FDA approval keyword matching
- Earnings surprise calculation
- Analyst consensus interpretation
- News sentiment analysis

**Signal Weighting:**
- Correct amplification formula
- Capping at 1.0
- Edge cases (invalid inputs)

**API Integration:**
- Finnhub news fetch
- Alpaca consensus fetch
- Error handling
- Network timeout handling

**Edge Cases:**
- Missing data (None values)
- Empty lists
- Invalid timestamps
- Zero estimates

### Example Test Output
```
test_fda_approval_detection PASSED
test_earnings_surprise_detection PASSED
test_analyst_upgrade_detection PASSED
test_weight_signal_base_amplification PASSED
test_weight_signal_max_amplification PASSED
test_weight_signal_capped_at_one PASSED
test_score_catalysts_returns_valid_range PASSED
...
======= 25 passed in 2.34s =======
```

## Performance

### API Latency
- Finnhub: ~500ms (news), ~300ms (earnings)
- Alpaca: ~400ms (consensus)
- **Total:** ~2 seconds per symbol (sequential)

### Rate Limits
- **Finnhub (Free):** 60 requests/minute
- **Alpaca (Free):** Generous limits (500+ req/min)

### Optimization Strategies
1. **Caching:** Cache scores for 1-6 hours
2. **Batch Processing:** Score multiple symbols in parallel
3. **Async:** Use async/await for concurrent API calls
4. **Polling:** Update scores on 5-15 minute intervals

### Recommended Cache Strategy

```python
import redis
from datetime import timedelta

cache = redis.Redis()
TTL = 3600  # 1 hour

def score_catalysts_cached(symbol: str) -> float:
    cache_key = f"catalyst_score:{symbol}"
    
    # Try cache first
    cached = cache.get(cache_key)
    if cached:
        return float(cached)
    
    # Score and cache
    score = scorer.score_catalysts(symbol)
    cache.setex(cache_key, TTL, str(score))
    
    return score
```

## Troubleshooting

### Issue: Score always returns 0

**Check 1: API Keys**
```python
import os
print(os.getenv('FINNHUB_API_KEY'))  # Should not be None
print(os.getenv('ALPACA_API_KEY'))   # Should not be None
```

**Check 2: Symbol Validity**
```python
# Use uppercase
scorer.score_catalysts('AAPL')  # Correct
scorer.score_catalysts('aapl')  # May fail
```

**Check 3: API Status**
- Check https://status.finnhub.io
- Check https://status.alpaca.markets
- Verify internet connectivity

**Check 4: Logs**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
# Run score_catalysts() and check output
```

### Issue: Adjustment factor too small

The formula is designed to provide moderate amplification. Maximum boost is 50% (catalyst_score=100 → amplification=1.5).

For larger adjustments, modify the formula:
```python
# Original: 1.0 + (catalyst_score / 100) * 0.5
# More aggressive: 1.0 + (catalyst_score / 100) * 0.8
adjusted = base_signal * (1.0 + (catalyst_score / 100) * 0.8)
```

### Issue: API timeouts

Increase timeout or add retry logic:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def score_catalysts_with_retry(symbol: str):
    return scorer.score_catalysts(symbol)
```

## Integration Checklist

- [ ] Install dependencies (`pip install httpx`)
- [ ] Obtain Finnhub API key
- [ ] Obtain Alpaca API key
- [ ] Set environment variables
- [ ] Import CatalystScorer in trading logic
- [ ] Create scorer instance at startup
- [ ] Call score_catalysts() for each symbol
- [ ] Adjust signals with weight_signal_by_catalyst()
- [ ] Implement caching (Redis or in-memory)
- [ ] Add FastAPI endpoints (optional)
- [ ] Run tests: `pytest runtime/test_catalyst_scorer.py`
- [ ] Log catalyst details for transparency
- [ ] Monitor API quota usage
- [ ] Set up alerts for high catalyst scores

## Future Enhancements

1. **Sector Momentum:** Integrate sector indices (SPY, QQQ, XLK)
2. **Short Interest:** Add Finviz or SEC data for squeeze detection
3. **Options Flow:** Monitor unusual options activity
4. **Insider Trading:** Track insider buying/selling
5. **Technical Catalysts:** Support/resistance breakouts
6. **Sentiment ML:** Train models on historical headlines
7. **Real-time Updates:** WebSocket feeds for live catalyst alerts
8. **Correlation Analysis:** Track catalyst impact on returns

## Files

| File | Purpose |
|------|---------|
| `catalyst_scorer.py` | Main module (production code) |
| `test_catalyst_scorer.py` | Comprehensive unit tests |
| `catalyst_scorer_integration.md` | Detailed API documentation |
| `CATALYST_SCORER_QUICKREF.md` | Quick reference for developers |
| `CATALYST_SCORER_README.md` | This file |

## Support & Questions

For issues or questions:

1. Check the Quick Reference: `CATALYST_SCORER_QUICKREF.md`
2. Review test examples: `test_catalyst_scorer.py`
3. Read integration guide: `catalyst_scorer_integration.md`
4. Check logs with `logging.basicConfig(level=logging.DEBUG)`

## License

Part of ProfitEngine v5 trading system.
