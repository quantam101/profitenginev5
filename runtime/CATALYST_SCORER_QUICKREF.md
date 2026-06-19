# Catalyst Scorer Quick Reference

## Installation

The module is included in `runtime/catalyst_scorer.py`. Ensure httpx is available:

```bash
pip install httpx>=0.28.0
```

## Setup

Set environment variables:

```bash
export FINNHUB_API_KEY="sk_..."
export ALPACA_API_KEY="pk_live_..."
```

## Basic Usage

```python
from runtime.catalyst_scorer import CatalystScorer

# Create scorer
scorer = CatalystScorer()

# Score (0-100)
score = scorer.score_catalysts('AAPL')

# Get details
details = scorer.get_catalyst_details('AAPL')

# Adjust signal
adjusted = scorer.weight_signal_by_catalyst(0.75, score)
```

## API Endpoints

Add to your FastAPI runtime:

```python
@app.post("/api/v1/catalysts/score/{symbol}")
async def score(symbol: str):
    score = scorer.score_catalysts(symbol.upper())
    return {'symbol': symbol, 'score': score}

@app.post("/api/v1/catalysts/details/{symbol}")
async def details(symbol: str):
    return scorer.get_catalyst_details(symbol.upper())

@app.post("/api/v1/catalysts/adjust-signal")
async def adjust(base_signal: float, catalyst_score: float):
    adjusted = scorer.weight_signal_by_catalyst(base_signal, catalyst_score)
    return {'adjusted_signal': adjusted}
```

## Catalyst Types

| Type | Points | Source | Trigger |
|------|--------|--------|---------|
| FDA Approval | 100 | Finnhub News | "FDA approval" in news |
| Earnings Beat | 75 | Finnhub Earnings | Beat by > 5% |
| Analyst Upgrade | 50 | Alpaca Consensus | Rating < 2.0 |
| News Sentiment | 30 | Finnhub News | > 50% positive articles |
| Sector Momentum | 20 | — | (Future) |
| Short Squeeze | 15 | — | (Future) |

## Signal Adjustment Formula

```
adjusted = base_signal * (1 + (catalyst_score / 100) * 0.5)
```

Examples:
- catalyst_score = 0 → no change (multiplier = 1.0)
- catalyst_score = 50 → +25% boost (multiplier = 1.25)
- catalyst_score = 100 → +50% boost (multiplier = 1.5, capped at 1.0)

## Example: Trading Strategy

```python
def execute_trade(symbol: str) -> Dict:
    # Base signal from technical analysis
    base_signal = 0.75
    
    # Check catalysts
    catalyst_score = scorer.score_catalysts(symbol)
    
    # Adjust signal by catalyst strength
    adjusted_signal = scorer.weight_signal_by_catalyst(base_signal, catalyst_score)
    
    # Get catalyst details for logging
    details = scorer.get_catalyst_details(symbol)
    
    return {
        'symbol': symbol,
        'base_signal': base_signal,
        'catalyst_score': catalyst_score,
        'adjusted_signal': adjusted_signal,
        'active_catalysts': [c['type'] for c in details['catalysts']],
    }
```

## Testing

Run unit tests:

```bash
pytest runtime/test_catalyst_scorer.py -v
```

Key test areas:
- Catalyst detection (FDA, earnings, analysts, sentiment)
- Signal weighting formula
- API integration with mocks
- Error handling

## Performance

- Response time: < 2 seconds (depends on API latency)
- Rate limits: Finnhub 60 req/min (free tier)
- Caching: Implement Redis for scores (TTL: 1-6 hours)

## Troubleshooting

**No API key set?**
```python
# Check environment variables
import os
print(os.getenv('FINNHUB_API_KEY'))
print(os.getenv('ALPACA_API_KEY'))
```

**Getting score of 0?**
- Check API keys are valid
- Ensure symbol is valid (use uppercase)
- Check if API calls are succeeding
- Look at logger output for errors

**Signal not amplified?**
- Catalyst score must be 0-100
- Base signal must be 0-1
- Max amplification is 1.5x

## Integration Checklist

- [ ] Set FINNHUB_API_KEY and ALPACA_API_KEY env vars
- [ ] Import CatalystScorer in your trading logic
- [ ] Create scorer instance (once, at startup)
- [ ] Call score_catalysts() for each symbol
- [ ] Adjust base signals using weight_signal_by_catalyst()
- [ ] Log catalyst details for transparency
- [ ] Implement caching for production
- [ ] Add FastAPI endpoints for catalyst API
- [ ] Run tests: `pytest runtime/test_catalyst_scorer.py`

## API Keys

Get free API keys:

1. **Finnhub**: https://finnhub.io/dashboard
   - Free tier: 60 requests/minute
   - News, earnings, company data

2. **Alpaca**: https://alpaca.markets/sign-up
   - Free tier: Generous rate limits
   - Analyst consensus data

## Next Steps

- **Sector Momentum**: Integrate IEX Cloud or Finnhub for sector indices
- **Short Interest**: Add Finviz or SEC data
- **Options Flow**: Monitor unusual options activity
- **Sentiment ML**: Train on headlines for better detection
- **Real-time Updates**: WebSocket feeds for live catalysts

## Support

Refer to full documentation in `catalyst_scorer_integration.md`

Questions or issues? Check:
1. Test coverage in `test_catalyst_scorer.py`
2. Log output (logger named 'catalyst_scorer')
3. API health (Finnhub/Alpaca status pages)
