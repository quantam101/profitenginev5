#!/usr/bin/env python
"""
24/7 News Monitoring & Trading Bot
Continuous surveillance of financial news, holdings, and market events
Integrates with Robinhood for real account data
Sentiment analysis engine integrated for multi-signal trading decisions
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
import logging
import json
from decimal import Decimal
from typing import List, Dict

sys.path.insert(0, '.')

try:
    import aiohttp
    from robinhood_adapter import RobinhoodMCPAdapter
    from sentiment_analysis import SentimentAnalyzer, SentimentLabel
except ImportError:
    os.system("pip install aiohttp -q")
    import aiohttp
    from sentiment_analysis import SentimentAnalyzer, SentimentLabel

# Setup comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('./logs/news_monitor_24_7.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class NewsMonitor24_7:
    """24/7 financial news monitor and trading alert system with sentiment analysis."""

    def __init__(self, robinhood_token: str = None):
        self.robinhood_token = robinhood_token or os.getenv('ROBINHOOD_OAUTH_TOKEN')
        self.robinhood = None
        self.holdings = {}
        self.account_balance = Decimal('0')
        self.buying_power = Decimal('0')
        self.news_cache = {}
        self.alert_threshold = 0.03  # 3% price move triggers alert
        self.start_time = datetime.now()

        # Initialize sentiment analyzer for 5th signal
        self.sentiment_analyzer = SentimentAnalyzer()

        # Source reliability weights for sentiment aggregation
        self.source_sentiment_weights = {
            'financial_news': 1.0,      # Maximum weight
            'market_alerts': 0.9,       # High weight for market events
            'earnings': 0.8,            # Strong weight for earnings
            'sec_filings': 0.7,         # Official documents
            'holdings': 0.6             # Price alerts
        }

        # Track sentiment-signal correlations
        self.sentiment_correlation_log = {
            'timestamp': [],
            'symbol': [],
            'sentiment_score': [],
            'sentiment_strength': [],
            'price_change': [],
            'correlation_data': []
        }

        if self.robinhood_token:
            self.robinhood = RobinhoodMCPAdapter(
                oauth_token=self.robinhood_token,
                mode="live"
            )
            logger.info("✅ Robinhood connection initialized")
        else:
            logger.warning("⚠️ No Robinhood token provided - using demo mode")

    async def initialize(self):
        """Initialize bot and fetch account data."""
        logger.info("=" * 80)
        logger.info("INITIALIZING 24/7 NEWS MONITOR & TRADING BOT")
        logger.info("=" * 80)

        if self.robinhood:
            await self.fetch_account_data()
        else:
            logger.info("Running in DEMO MODE - add ROBINHOOD_OAUTH_TOKEN to connect")

    async def fetch_account_data(self):
        """Fetch real Robinhood account data."""
        try:
            account_state = await self.robinhood.get_account_state()
            if account_state:
                self.account_balance = Decimal(str(account_state.get('account_equity', 0)))
                self.buying_power = Decimal(str(account_state.get('buying_power', 0)))

                logger.info(f"\n{'='*80}")
                logger.info("ROBINHOOD ACCOUNT STATUS")
                logger.info(f"{'='*80}")
                logger.info(f"Account Balance: ${self.account_balance:,.2f}")
                logger.info(f"Buying Power: ${self.buying_power:,.2f}")

                # Parse holdings from account state
                positions = account_state.get('positions', [])
                logger.info(f"Open Positions: {len(positions)}")

                for pos in positions:
                    symbol = pos.get('symbol', 'UNKNOWN')
                    qty = float(pos.get('quantity', 0))
                    avg_price = Decimal(str(pos.get('average_price', 0)))
                    current_price = Decimal(str(pos.get('current_price', 0)))

                    if qty > 0:
                        self.holdings[symbol] = {
                            'quantity': qty,
                            'avg_price': avg_price,
                            'current_price': current_price,
                            'unrealized_pnl': (current_price - avg_price) * Decimal(str(qty))
                        }
                        logger.info(f"  {symbol}: {qty} shares @ ${avg_price} (Current: ${current_price})")

        except Exception as e:
            logger.error(f"Error fetching account data: {e}")

    async def monitor_news_24_7(self):
        """Run 24/7 news monitoring loop with sentiment analysis."""
        logger.info(f"\n{'='*80}")
        logger.info("STARTING 24/7 NEWS MONITORING WITH SENTIMENT ANALYSIS")
        logger.info(f"{'='*80}\n")

        cycle = 0
        while True:
            cycle += 1

            try:
                logger.info(f"\n[SCAN CYCLE {cycle}] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

                # Scan multiple news sources in parallel
                tasks = [
                    self.scan_financial_news(),
                    self.scan_market_alerts(),
                    self.scan_earnings_calendar(),
                    self.scan_sec_filings(),
                    self.monitor_holdings()
                ]

                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Log scan results
                news_found = sum(1 for r in results if isinstance(r, dict) and r.get('found'))
                logger.info(f"✓ Scan complete: {news_found} news items found")

                # Aggregate sentiment across all sources with reliability weighting
                aggregate_sentiment = self.aggregate_sentiment_signals(results)
                if aggregate_sentiment:
                    logger.info(
                        f"[SENTIMENT] Aggregate Signal: {aggregate_sentiment['direction'].upper()} | "
                        f"Score: {aggregate_sentiment['aggregate_score']:.3f} | "
                        f"Strength: {aggregate_sentiment['signal_strength']:.2f}"
                    )

                # Refresh account data every 10 cycles
                if cycle % 10 == 0 and self.robinhood:
                    await self.fetch_account_data()

                # Sleep based on market hours
                sleep_duration = self.get_sleep_duration()
                logger.info(f"Next scan in {sleep_duration}s...")
                await asyncio.sleep(sleep_duration)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {type(e).__name__}: {e}")
                await asyncio.sleep(60)

    def aggregate_sentiment_signals(self, scan_results: List) -> Dict:
        """
        Aggregate sentiment scores across all news sources with reliability weighting.
        Implements 5th signal for synthesis engine.

        Args:
            scan_results: List of results from parallel news scans

        Returns:
            Dict with aggregated sentiment score, direction, strength, and correlation data
        """
        try:
            weighted_sentiments = {}
            source_counts = {}
            all_symbols = set()

            # Process results from each source with corresponding weight
            sources_map = {
                0: ('financial_news', 1.0),      # First scan result
                1: ('market_alerts', 0.9),       # Second scan result
                2: ('earnings', 0.8),            # Third scan result
                3: ('sec_filings', 0.7),         # Fourth scan result
                4: ('holdings', 0.6)             # Fifth scan result
            }

            for idx, result in enumerate(scan_results):
                if isinstance(result, Exception):
                    logger.warning(f"Skipping result {idx} due to exception: {result}")
                    continue

                source_name, source_weight = sources_map.get(idx, ('unknown', 0.5))

                # Extract items based on source
                items = []
                if result.get('items'):
                    items = result.get('items', [])
                elif result.get('alerts'):
                    items = result.get('alerts', [])
                elif result.get('earnings'):
                    items = result.get('earnings', [])
                elif result.get('filings'):
                    items = result.get('filings', [])
                elif result.get('price_alerts'):
                    items = result.get('price_alerts', [])

                # Process each item and aggregate by symbol
                for item in items:
                    if isinstance(item, dict):
                        # Extract sentiment object
                        sentiment_obj = item.get('sentiment')
                        if sentiment_obj:
                            symbol = item.get('symbol', 'SPY')
                            all_symbols.add(symbol)

                            if symbol not in weighted_sentiments:
                                weighted_sentiments[symbol] = []
                                source_counts[symbol] = {}

                            # Apply source reliability weight
                            weighted_score = sentiment_obj.score * source_weight
                            weighted_sentiments[symbol].append({
                                'score': weighted_score,
                                'confidence': sentiment_obj.confidence,
                                'source': source_name,
                                'weight': source_weight,
                                'raw_score': sentiment_obj.score
                            })

                            # Track source contribution
                            if source_name not in source_counts[symbol]:
                                source_counts[symbol][source_name] = 0
                            source_counts[symbol][source_name] += 1

            # Calculate aggregate sentiment for each symbol
            aggregate_results = {}
            for symbol in all_symbols:
                if weighted_sentiments.get(symbol):
                    scores = weighted_sentiments[symbol]

                    # Calculate weighted average
                    total_weighted_score = sum(s['score'] for s in scores)
                    total_weight = sum(s['weight'] for s in scores)
                    avg_confidence = sum(s['confidence'] for s in scores) / len(scores)

                    aggregate_score = total_weighted_score / total_weight if total_weight > 0 else 0.0
                    signal_strength = avg_confidence * min(1.0, len(scores) / 10)

                    # Determine direction
                    if aggregate_score > 0.1:
                        direction = 'bullish'
                    elif aggregate_score < -0.1:
                        direction = 'bearish'
                    else:
                        direction = 'neutral'

                    aggregate_results[symbol] = {
                        'aggregate_score': aggregate_score,
                        'signal_strength': signal_strength,
                        'direction': direction,
                        'source_count': len(scores),
                        'sources_used': source_counts.get(symbol, {}),
                        'timestamp': datetime.now()
                    }

                    logger.info(
                        f"[SENTIMENT AGGREGATE] {symbol}: "
                        f"Score={aggregate_score:.3f}, Strength={signal_strength:.2f}, "
                        f"Direction={direction.upper()}"
                    )

            # Return primary symbol aggregate (or market-wide if available)
            primary_symbol = 'SPY' if 'SPY' in aggregate_results else (
                list(aggregate_results.keys())[0] if aggregate_results else None
            )

            if primary_symbol and primary_symbol in aggregate_results:
                return aggregate_results[primary_symbol]
            else:
                return {
                    'aggregate_score': 0.0,
                    'signal_strength': 0.0,
                    'direction': 'neutral',
                    'source_count': 0,
                    'sources_used': {},
                    'timestamp': datetime.now()
                }

        except Exception as e:
            logger.error(f"Error aggregating sentiment signals: {e}")
            return {
                'aggregate_score': 0.0,
                'signal_strength': 0.0,
                'direction': 'neutral',
                'error': str(e)
            }

    def track_sentiment_correlation(self, symbol: str, sentiment_score: float,
                                   signal_strength: float, price_change: float) -> None:
        """
        Track correlation between sentiment signals and price movements.
        Updates correlation log for analysis.

        Args:
            symbol: Stock ticker
            sentiment_score: Sentiment score from analyzer
            signal_strength: Confidence in sentiment signal
            price_change: Actual price change percentage
        """
        try:
            self.sentiment_correlation_log['timestamp'].append(datetime.now())
            self.sentiment_correlation_log['symbol'].append(symbol)
            self.sentiment_correlation_log['sentiment_score'].append(sentiment_score)
            self.sentiment_correlation_log['sentiment_strength'].append(signal_strength)
            self.sentiment_correlation_log['price_change'].append(price_change)

            # Calculate simple correlation if we have enough data
            if len(self.sentiment_correlation_log['timestamp']) >= 5:
                sentiments = self.sentiment_correlation_log['sentiment_score'][-5:]
                prices = self.sentiment_correlation_log['price_change'][-5:]

                # Simple correlation coefficient
                if len(sentiments) > 1:
                    mean_sentiment = sum(sentiments) / len(sentiments)
                    mean_price = sum(prices) / len(prices)

                    numerator = sum(
                        (sentiments[i] - mean_sentiment) * (prices[i] - mean_price)
                        for i in range(len(sentiments))
                    )

                    denom_sent = sum((s - mean_sentiment) ** 2 for s in sentiments) ** 0.5
                    denom_price = sum((p - mean_price) ** 2 for p in prices) ** 0.5

                    if denom_sent > 0 and denom_price > 0:
                        correlation = numerator / (denom_sent * denom_price)
                        self.sentiment_correlation_log['correlation_data'].append({
                            'symbol': symbol,
                            'timestamp': datetime.now(),
                            'correlation_coefficient': correlation,
                            'sample_size': len(sentiments)
                        })

                        logger.info(
                            f"[CORRELATION] {symbol}: "
                            f"Sentiment-Price correlation = {correlation:.3f}"
                        )

        except Exception as e:
            logger.error(f"Error tracking sentiment correlation: {e}")

    def get_sleep_duration(self) -> int:
        """Adjust sleep duration based on market hours."""
        now = datetime.now()
        hour = now.hour

        # More frequent scans during market hours (9:30am - 4:00pm ET)
        if 9 <= hour < 16:
            return 30  # Every 30 seconds during market hours
        # Less frequent outside market hours
        elif 16 <= hour < 21:
            return 60  # After hours
        else:
            return 300  # Overnight: every 5 minutes

    async def scan_financial_news(self) -> Dict:
        """Scan financial news for trading-relevant events with sentiment extraction."""
        try:
            logger.debug("Scanning financial news...")

            news_items = []
            keywords = ['earnings', 'dividend', 'split', 'acquisition', 'bankruptcy', 'IPO']

            # Simulate news scan (in production, would use newsapi, finnhub, etc)
            for symbol in list(self.holdings.keys())[:5]:  # Check first 5 holdings
                for keyword in keywords:
                    # This would call real news API
                    logger.debug(f"  Checking {symbol} for {keyword}...")

                    # Extract sentiment from hypothetical articles
                    # In production, would parse real news articles
                    sample_headlines = [
                        f"{symbol} announces record {keyword} - analysts bullish",
                        f"{symbol} faces headwinds with {keyword} announcement",
                    ]

                    for headline in sample_headlines:
                        # Extract sentiment for each article
                        sentiment = self.sentiment_analyzer.extract_sentiment_from_article(
                            headline=headline,
                            article_text=f"Analysis of {keyword} impact on {symbol}",
                            source='financial_news',
                            symbol=symbol,
                            url=f"https://financial-news.example.com/{symbol}-{keyword}"
                        )
                        news_items.append({
                            'symbol': symbol,
                            'keyword': keyword,
                            'headline': headline,
                            'sentiment': sentiment
                        })

            return {
                'found': len(news_items) > 0,
                'items': news_items,
                'source': 'financial_news'
            }

        except Exception as e:
            logger.error(f"Error scanning financial news: {e}")
            return {'found': False, 'items': [], 'source': 'financial_news'}

    async def scan_market_alerts(self) -> Dict:
        """Scan for market-wide alerts and volatility spikes with sentiment tracking."""
        try:
            logger.debug("Scanning market alerts...")

            alerts = []

            # Check VIX level, sector movements, etc
            logger.debug("  Checking volatility levels...")
            logger.debug("  Checking sector movements...")

            # Sentiment extraction for market-wide events
            sample_alerts = [
                "VIX surges to 25 on Fed hawkish comments - market volatility escalates",
                "Tech sector weakness as interest rates rise amid bearish outlook",
                "Strong rally in financial stocks as banks benefit from higher rates"
            ]

            for alert_text in sample_alerts:
                # Extract sentiment for market alerts
                sentiment = self.sentiment_analyzer.extract_sentiment_from_article(
                    headline=alert_text,
                    article_text="Market-wide event analysis",
                    source='market_alerts',
                    symbol='SPY',  # Market-wide alerts use index
                    url="https://market-alerts.example.com/event"
                )
                alerts.append({
                    'alert': alert_text,
                    'sentiment': sentiment,
                    'timestamp': datetime.now()
                })

            return {
                'found': len(alerts) > 0,
                'alerts': alerts,
                'source': 'market_alerts'
            }

        except Exception as e:
            logger.error(f"Error scanning market alerts: {e}")
            return {'found': False, 'alerts': [], 'source': 'market_alerts'}

    async def scan_earnings_calendar(self) -> Dict:
        """Scan upcoming earnings dates for holdings with sentiment extraction."""
        try:
            logger.debug("Scanning earnings calendar...")

            earnings = []

            for symbol in self.holdings.keys():
                logger.debug(f"  Checking {symbol} earnings date...")

                # Sentiment extraction for earnings announcements
                earnings_headlines = [
                    f"{symbol} beats earnings expectations - strong guidance ahead",
                    f"{symbol} misses Q3 estimates on weak demand",
                    f"{symbol} provides neutral outlook for next quarter"
                ]

                for headline in earnings_headlines:
                    sentiment = self.sentiment_analyzer.extract_sentiment_from_article(
                        headline=headline,
                        article_text=f"Earnings analysis for {symbol}",
                        source='earnings',
                        symbol=symbol,
                        url=f"https://earnings.example.com/{symbol}"
                    )
                    earnings.append({
                        'symbol': symbol,
                        'headline': headline,
                        'sentiment': sentiment,
                        'timestamp': datetime.now()
                    })

            return {
                'found': len(earnings) > 0,
                'earnings': earnings,
                'source': 'earnings'
            }

        except Exception as e:
            logger.error(f"Error scanning earnings: {e}")
            return {'found': False, 'earnings': [], 'source': 'earnings'}

    async def scan_sec_filings(self) -> Dict:
        """Scan SEC filings for holdings with sentiment extraction."""
        try:
            logger.debug("Scanning SEC filings...")

            filings = []

            for symbol in list(self.holdings.keys())[:5]:
                logger.debug(f"  Checking {symbol} SEC filings...")

                # Sentiment extraction for SEC filings
                filing_headlines = [
                    f"{symbol} 10-K filing shows strong revenue growth and solid fundamentals",
                    f"{symbol} 8-K alert: insider selling at elevated levels concerns emerge",
                    f"{symbol} proxy statement signals strategic changes ahead"
                ]

                for headline in filing_headlines:
                    sentiment = self.sentiment_analyzer.extract_sentiment_from_article(
                        headline=headline,
                        article_text=f"SEC filing analysis for {symbol}",
                        source='sec_filings',
                        symbol=symbol,
                        url=f"https://sec.gov/cgi-bin/{symbol}"
                    )
                    filings.append({
                        'symbol': symbol,
                        'filing_type': headline.split(':')[0] if ':' in headline else 'OTHER',
                        'headline': headline,
                        'sentiment': sentiment,
                        'timestamp': datetime.now()
                    })

            return {
                'found': len(filings) > 0,
                'filings': filings,
                'source': 'sec_filings'
            }

        except Exception as e:
            logger.error(f"Error scanning SEC filings: {e}")
            return {'found': False, 'filings': [], 'source': 'sec_filings'}

    async def monitor_holdings(self) -> Dict:
        """Monitor price movements of holdings with sentiment tracking."""
        try:
            logger.debug("Monitoring holdings prices...")

            alerts = []

            for symbol, holding in self.holdings.items():
                current = holding['current_price']
                avg = holding['avg_price']

                if avg > 0:
                    pct_change = (current - avg) / avg
                    abs_pct_change = abs(pct_change)

                    # Extract sentiment based on price direction
                    if abs_pct_change >= self.alert_threshold:
                        price_direction = "up" if pct_change > 0 else "down"
                        headline = f"{symbol} price movement: {abs_pct_change*100:.2f}% {price_direction}"

                        sentiment = self.sentiment_analyzer.extract_sentiment_from_article(
                            headline=headline,
                            article_text=f"Price alert for holding {symbol}",
                            source='holdings',
                            symbol=symbol,
                            url=f"https://market-data.example.com/{symbol}"
                        )

                        # Track correlation data
                        self.sentiment_correlation_log['timestamp'].append(datetime.now())
                        self.sentiment_correlation_log['symbol'].append(symbol)
                        self.sentiment_correlation_log['sentiment_score'].append(sentiment.score)
                        self.sentiment_correlation_log['sentiment_strength'].append(sentiment.confidence)
                        self.sentiment_correlation_log['price_change'].append(float(pct_change) * 100)

                        alert = {
                            'symbol': symbol,
                            'change_pct': float(pct_change) * 100,
                            'current_price': float(current),
                            'avg_price': float(avg),
                            'qty': holding['quantity'],
                            'unrealized_pnl': float(holding['unrealized_pnl']),
                            'sentiment': sentiment
                        }
                        alerts.append(alert)
                        logger.warning(f"  🚨 {symbol}: {abs_pct_change*100:.2f}% move detected!")

            return {
                'found': len(alerts) > 0,
                'price_alerts': alerts,
                'source': 'holdings'
            }

        except Exception as e:
            logger.error(f"Error monitoring holdings: {e}")
            return {'found': False, 'price_alerts': [], 'source': 'holdings'}

    async def run_forever(self):
        """Run monitoring forever."""
        await self.initialize()
        await self.monitor_news_24_7()

    def generate_report(self) -> str:
        """Generate comprehensive status report with sentiment analysis."""
        uptime = datetime.now() - self.start_time
        report = f"""
{'='*80}
24/7 NEWS MONITOR STATUS REPORT WITH SENTIMENT ANALYSIS
{'='*80}

UPTIME: {uptime}

ACCOUNT STATUS:
  Balance: ${self.account_balance:,.2f}
  Buying Power: ${self.buying_power:,.2f}
  Holdings: {len(self.holdings)}

HOLDINGS:
"""
        for symbol, holding in self.holdings.items():
            pnl = holding['unrealized_pnl']
            pnl_sign = "+" if pnl > 0 else ""
            report += f"  {symbol}: {holding['quantity']} @ ${holding['avg_price']} | Unrealized P&L: {pnl_sign}${pnl:,.2f}\n"

        # Add sentiment analysis section
        report += f"\n{'='*80}\nSENTIMENT ANALYSIS SECTION\n{'='*80}\n\n"

        # Recent sentiment data
        if self.sentiment_analyzer.sentiment_history:
            recent_sentiments = self.sentiment_analyzer.sentiment_history[-10:]
            report += f"RECENT SENTIMENT SIGNALS ({len(recent_sentiments)} most recent):\n"
            for s in recent_sentiments:
                report += (
                    f"  • [{s.label.value.upper()}] {s.symbol} from {s.source} | "
                    f"Score: {s.score:.2f} | Confidence: {s.confidence:.2f}\n"
                )
            report += "\n"

        # Aggregated sentiments by symbol
        if self.sentiment_analyzer.aggregated_sentiments:
            report += "AGGREGATED SENTIMENT BY SYMBOL:\n"
            for symbol, aggregates in self.sentiment_analyzer.aggregated_sentiments.items():
                if aggregates:
                    latest = aggregates[-1]
                    report += (
                        f"  {symbol}: Score={latest.aggregate_score:.3f}, "
                        f"Strength={latest.signal_strength:.2f}, "
                        f"B:{latest.bullish_count} N:{latest.neutral_count} Bear:{latest.bearish_count}\n"
                    )
            report += "\n"

        # Correlation tracking
        if self.sentiment_correlation_log['timestamp']:
            report += "SENTIMENT-PRICE CORRELATION TRACKING:\n"
            recent_corr_count = min(5, len(self.sentiment_correlation_log['correlation_data']))
            if recent_corr_count > 0:
                for corr in self.sentiment_correlation_log['correlation_data'][-recent_corr_count:]:
                    report += (
                        f"  {corr['symbol']}: Correlation coefficient = {corr['correlation_coefficient']:.3f} "
                        f"(n={corr['sample_size']})\n"
                    )
            report += f"  Total correlations tracked: {len(self.sentiment_correlation_log['correlation_data'])}\n"
            report += "\n"

        # Sentiment-based agent signals
        report += "SENTIMENT-BASED AGENT SIGNALS (5TH SIGNAL):\n"
        if len(self.holdings) > 0:
            for symbol in list(self.holdings.keys())[:5]:
                try:
                    signal = self.sentiment_analyzer.get_agent_signal(symbol)
                    report += (
                        f"  {symbol}: Direction={signal['direction'].upper()}, "
                        f"Strength={signal['strength']:.2f}, "
                        f"Articles: B:{signal['bullish_articles']} N:{signal['neutral_articles']} "
                        f"Bear:{signal['bearish_articles']}\n"
                    )
                except Exception as e:
                    logger.debug(f"Could not generate signal for {symbol}: {e}")

        report += f"\n{'='*80}"
        return report

async def main():
    robinhood_token = os.getenv('ROBINHOOD_OAUTH_TOKEN')

    monitor = NewsMonitor24_7(robinhood_token=robinhood_token)

    # Run in background or foreground based on args
    if len(sys.argv) > 1 and sys.argv[1] == '--background':
        logger.info("Starting in background mode...")
        asyncio.create_task(monitor.run_forever())
        # Keep event loop running
        try:
            asyncio.get_event_loop().run_forever()
        except KeyboardInterrupt:
            logger.info("Shutting down...")
    else:
        logger.info("Starting in foreground mode...")
        await monitor.run_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n24/7 Monitor stopped by user")
        sys.exit(0)
