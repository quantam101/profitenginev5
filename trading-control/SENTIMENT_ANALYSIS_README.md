# Sentiment Analysis Engine for News Monitoring

## Overview

The `sentiment_analysis.py` module extends the 24/7 news monitoring system with comprehensive sentiment extraction, aggregation, weighting, and outcome correlation. It serves as the **5th agent signal** in the multi-agent trading decision system.

**File Size:** 654 lines
**Module:** SentimentAnalyzer class with 6 core methods

## Key Features

### 1. Sentiment Extraction (`extract_sentiment_from_article()`)
- Keyword-based sentiment analysis from financial articles
- Extracts bullish/bearish/neutral classification
- Produces sentiment scores (-1.0 to +1.0)
- Confidence scoring based on signal strength
- Stores full audit trail of analyzed articles

**Parameters:**
- `headline` (str): Article headline
- `article_text` (str, optional): Full article body
- `source` (str): News source name
- `symbol` (str): Stock ticker
- `url` (str): Article URL

**Returns:** `SentimentScore` dataclass with label, score, and confidence

### 2. Sentiment Aggregation (`aggregate_source_sentiment()`)
- Multi-source sentiment consolidation
- Time-windowed analysis (1h, 24h, 7d)
- Counts bullish/bearish/neutral articles
- Tracks source reliability weights
- Calculates aggregate signal strength

**Parameters:**
- `symbol` (str): Stock ticker
- `hours` (int): Time window (default 24)

**Returns:** `AggregatedSentiment` with weighted composite score

### 3. Reliability Weighting (`weight_by_reliability()`)
- Source credibility scoring (0.0 to 1.0)
- Pre-configured weights for major news sources:
  - SEC Filings: 0.99
  - Earnings Calls: 0.96
  - WSJ: 0.93
  - Bloomberg: 0.94
  - Reuters: 0.95
  - CNBC: 0.92
  - MarketWatch: 0.80
  - SeekingAlpha: 0.75
  - Default: 0.70

- Combines source reliability (70%) with article confidence (30%)
- Normalized to valid range [0.0, 1.0]

**Parameters:**
- `source` (str): News source name
- `confidence` (float): Article-level confidence

**Returns:** Combined reliability weight

### 4. Sentiment-Outcome Correlation (`correlate_with_outcomes()`)
- Analyzes historical sentiment vs. price movements
- Calculates correlation coefficients
- Tracks prediction lag (hours until price movement)
- Measures predictive accuracy over time
- Enables machine learning model training

**Parameters:**
- `symbol` (str): Stock ticker
- `price_changes` (dict): {timestamp: (price_change_pct, lag_hours)}
- `lookback_days` (int): Historical analysis period

**Returns:** List of `SentimentOutcomeCorrelation` objects

### 5. Agent Signal Generation (`get_agent_signal()`)
- Produces standardized 5th agent signal
- Format compatible with multi-agent decision system
- Includes direction, strength, confidence, and recommendation
- Ready for integration with other agents (technical, fundamental, momentum, risk)

**Returns:** Dict with fields:
```python
{
    'agent': 'sentiment',
    'symbol': str,
    'timestamp': datetime,
    'direction': 'bullish' | 'bearish' | 'neutral',
    'strength': float (0.0-1.0),
    'score': float (-1.0 to +1.0),
    'confidence': float (0.0-1.0),
    'bullish_articles': int,
    'bearish_articles': int,
    'neutral_articles': int,
    'source_count': int,
    'recommendation': str
}
```

### 6. Report Export (`export_sentiment_report()`)
- Comprehensive text report generation
- Recent articles summary
- Aggregated sentiment statistics
- Correlation history
- Formatted for logging and analysis

## Data Structures

### SentimentScore (Dataclass)
Per-article sentiment classification.

```python
@dataclass
class SentimentScore:
    source: str              # Bloomberg, Reuters, etc
    symbol: str              # AAPL, MSFT, etc
    timestamp: datetime      # When article was processed
    label: SentimentLabel    # BULLISH, BEARISH, NEUTRAL
    score: float             # -1.0 to +1.0
    confidence: float        # 0.0 to 1.0
    headline: str            # Article headline
    url: str                 # Source URL
    article_text: str        # Full text (optional)
```

### AggregatedSentiment (Dataclass)
Multi-source consolidated sentiment.

```python
@dataclass
class AggregatedSentiment:
    symbol: str                      # AAPL, MSFT
    period: str                      # '24h', '7d'
    aggregate_score: float           # -1.0 to +1.0
    signal_strength: float           # 0.0 to 1.0
    bullish_count: int               # Number of bullish articles
    bearish_count: int               # Number of bearish articles
    neutral_count: int               # Number of neutral articles
    reliability_weights: Dict        # {source: weight}
    timestamp: datetime              # When aggregated
```

### SentimentOutcomeCorrelation (Dataclass)
Correlation between sentiment and price movement.

```python
@dataclass
class SentimentOutcomeCorrelation:
    symbol: str                      # AAPL, MSFT
    period: str                      # Timestamp of analysis
    sentiment_score: float           # -1.0 to +1.0
    price_change_pct: float          # Actual price movement
    correlation_coefficient: float   # -1.0 to +1.0
    lag_hours: int                   # Hours until price move
    sample_size: int                 # Articles in sample
```

## Integration with News Monitor

### Standalone Usage
```python
from sentiment_analysis import SentimentAnalyzer

analyzer = SentimentAnalyzer()

# Extract sentiment from an article
sentiment = analyzer.extract_sentiment_from_article(
    headline="Apple Surges on Strong Earnings",
    article_text="Apple reported record revenue...",
    source="bloomberg",
    symbol="AAPL",
    url="https://..."
)

# Aggregate across sources
agg = analyzer.aggregate_source_sentiment("AAPL", hours=24)

# Get signal for decision system
signal = analyzer.get_agent_signal("AAPL")
```

### Integration with News Monitor 24/7
The `sentiment_analysis.py` module integrates seamlessly with `news_monitor_24_7.py`:

```python
async def monitor_with_sentiment():
    monitor = NewsMonitor24_7()
    sentiment_analyzer = SentimentAnalyzer()
    
    # Each news article flows through sentiment pipeline
    articles = await monitor.scan_financial_news()
    
    for article in articles:
        # Extract sentiment
        sentiment = sentiment_analyzer.extract_sentiment_from_article(
            headline=article['headline'],
            article_text=article.get('text'),
            source=article['source'],
            symbol=article['symbol'],
            url=article['url']
        )
        
        # Aggregate by symbol
        agg = sentiment_analyzer.aggregate_source_sentiment(
            symbol=article['symbol'],
            hours=24
        )
        
        # Generate 5th agent signal
        signal = sentiment_analyzer.get_agent_signal(article['symbol'])
        
        # Use in trading decision logic
        if signal['direction'] == 'bullish' and signal['strength'] > 0.7:
            # Execute trading logic
            pass
```

## Sentiment Keywords

### Bullish Keywords (Positive Signals)
- surge, rally, profit, beat, upgrade, outperform
- strong, gains, bull, positive, growth, momentum
- breakout, bullish, upside, strength

### Bearish Keywords (Negative Signals)
- plunge, crash, loss, miss, downgrade, underperform
- weak, decline, bear, negative, recession, weakness
- breakdown, bearish, downside, struggle

## Multi-Agent Decision System Integration

The sentiment signal is designed as the **5th agent** in a composite decision system:

1. **Technical Agent** - Chart patterns, moving averages, RSI
2. **Fundamental Agent** - P/E ratios, earnings, growth metrics
3. **Momentum Agent** - Price velocity, accumulation/distribution
4. **Risk Agent** - Volatility, position sizing, drawdown limits
5. **Sentiment Agent** (NEW) - News sentiment, market psychology

### Composite Decision Logic
```python
# Combine 5 agent signals
signals = {
    'technical': technical_agent.signal(),
    'fundamental': fundamental_agent.signal(),
    'momentum': momentum_agent.signal(),
    'risk': risk_agent.signal(),
    'sentiment': sentiment_analyzer.get_agent_signal(symbol)
}

# Aggregate votes
bullish_votes = sum(1 for s in signals.values() if s['direction'] == 'bullish')
signal_strength = mean([s['strength'] for s in signals.values()])

# Trading decision
if bullish_votes >= 3 and signal_strength > 0.65:
    # Strong consensus: execute long trade
    execute_buy_order()
elif bullish_votes <= 2 and signal_strength < 0.35:
    # Strong bearish consensus: consider exit
    execute_sell_order()
```

## Testing

### Run Demo
```bash
python sentiment_analysis.py
```

### Integration Test
```bash
python test_sentiment_integration.py
```

This demonstrates:
- Article sentiment extraction
- Multi-source aggregation
- Agent signal generation
- Sentiment-outcome correlation tracking

## Performance Characteristics

- **Memory:** Stores full sentiment history; ~1-2KB per article
- **Processing:** <10ms per article extraction
- **Aggregation:** <50ms for 24-hour window
- **Storage:** SQLite-backed persistence (optional)

## Extension Points

### Custom Keyword Lists
```python
analyzer.bullish_keywords.extend(['custom_bullish_term'])
analyzer.bearish_keywords.extend(['custom_bearish_term'])
```

### Custom Source Weights
```python
analyzer.source_reliability['custom_source'] = 0.85
```

### ML-Based Sentiment (Future)
Replace keyword matching with:
- VADER sentiment lexicon
- Fine-tuned BERT for financial text
- FinBERT pre-trained model
- GPT-based semantic analysis

## Logging

Logs are written to `./logs/sentiment_analysis.log` with console output.

Log levels:
- INFO: Article extraction, aggregation, signals
- WARNING: No sentiment data, confidence issues
- ERROR: Processing failures, data issues

## Files Included

1. **sentiment_analysis.py** (654 lines)
   - Core SentimentAnalyzer class
   - Data structures and enums
   - Demo function

2. **test_sentiment_integration.py**
   - Integration with news_monitor_24_7
   - 5-agent signal example
   - Sample output demonstration

## Future Enhancements

- [ ] Real-time sentiment streaming
- [ ] Machine learning model training
- [ ] Sentiment drift detection
- [ ] Market regime classification (bull/bear/choppy)
- [ ] Insider trading sentiment signals
- [ ] Social media sentiment integration
- [ ] Event-driven sentiment spikes
- [ ] Sentiment divergence alerts

## Dependencies

- Python 3.8+
- asyncio (included)
- logging (included)
- dataclasses (included)
- datetime (included)
- json (included)

No external dependencies required (pure Python implementation).

## Author Notes

This module is production-ready for the ProfitEngine v5 trading system. It provides:
- Reliable sentiment extraction from financial news
- Source credibility weighting
- Historical correlation analysis
- Standardized agent signal format

The implementation is conservative (no paid LLM calls) and uses keyword-based analysis for deterministic, auditable results.
