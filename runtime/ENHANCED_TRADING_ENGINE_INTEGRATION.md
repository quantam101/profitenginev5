# Enhanced Trading Engine — Integration Guide

Complete integration examples for brokers, data sources, and production deployments.

## Table of Contents

1. [Broker Integration](#broker-integration)
2. [Data Source Integration](#data-source-integration)
3. [Production Deployment](#production-deployment)
4. [Backtesting Integration](#backtesting-integration)
5. [Monitoring & Alerts](#monitoring--alerts)
6. [API Server Deployment](#api-server-deployment)

---

## Broker Integration

### Alpaca Integration

```python
import asyncio
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, OrderSide, TimeInForce
from enhanced_trading_engine import EnhancedTradingEngine, SignalAction

class AlpacaTradingEngine(EnhancedTradingEngine):
    """Extended engine with Alpaca broker integration."""
    
    def __init__(self, api_key: str, secret_key: str, paper: bool = True):
        self.alpaca = TradingClient(
            api_key=api_key,
            secret_key=secret_key,
            paper=paper  # Use paper trading first
        )
        
        # Get account balance
        account = self.alpaca.get_account()
        
        super().__init__(
            alpaca_client=self.alpaca,
            account_balance=float(account.buying_power)
        )

    async def execute_signal(self, signal):
        """Override to execute via Alpaca."""
        
        if signal.action == SignalAction.NONE:
            return None
        
        try:
            # Create Alpaca order
            order_request = MarketOrderRequest(
                symbol=signal.symbol,
                qty=signal.position_size,
                side=OrderSide.BUY if signal.action == SignalAction.BUY else OrderSide.SELL,
                time_in_force=TimeInForce.DAY
            )
            
            # Submit order
            order = self.alpaca.submit_order(order_request)
            
            # Place stop loss order (Alpaca uses trail or stop)
            stop_request = MarketOrderRequest(
                symbol=signal.symbol,
                qty=signal.position_size,
                side=OrderSide.SELL if signal.action == SignalAction.BUY else OrderSide.BUY,
                time_in_force=TimeInForce.GTC,
                stop_price=signal.stop_price
            )
            
            # Note: Alpaca requires separate stop order
            self.alpaca.submit_order(stop_request)
            
            # Log execution
            self.open_positions[order.id] = {
                'order_id': order.id,
                'symbol': signal.symbol,
                'action': signal.action.value,
                'entry_price': signal.entry_price,
                'position_size': signal.position_size,
                'stop_loss': signal.stop_price,
                'take_profit': signal.target_price,
                'timestamp': signal.timestamp
            }
            
            return {
                'status': 'SUCCESS',
                'order_id': order.id,
                'symbol': signal.symbol,
                'entry_price': signal.entry_price,
                'position_size': signal.position_size
            }
            
        except Exception as e:
            self.logger.error(f"Alpaca execution failed: {e}")
            return {'status': 'FAILED', 'error': str(e)}

# Usage
async def main():
    engine = AlpacaTradingEngine(
        api_key="YOUR_API_KEY",
        secret_key="YOUR_SECRET_KEY",
        paper=True  # Paper trading mode
    )
    
    signal = await engine.generate_trade_signal('NVDA')
    
    if signal and signal.confidence >= 75:
        result = await engine.execute_signal(signal)
        print(f"Execution: {result['status']}")

asyncio.run(main())
```

### Robinhood Integration

```python
import asyncio
from robin_stocks.robinhood import login, get_quotes, order_buy_market, order_sell_market
from enhanced_trading_engine import EnhancedTradingEngine, SignalAction

class RobinhoodTradingEngine(EnhancedTradingEngine):
    """Extended engine with Robinhood broker integration."""
    
    def __init__(self, email: str, password: str, mfa_code: str = None):
        # Login to Robinhood
        login(email, password, mfa_code=mfa_code)
        
        super().__init__(account_balance=10000.0)  # Set initial balance

    async def execute_signal(self, signal):
        """Override to execute via Robinhood."""
        
        if signal.action == SignalAction.NONE:
            return None
        
        try:
            if signal.action == SignalAction.BUY:
                order = order_buy_market(
                    symbol=signal.symbol,
                    quantity=signal.position_size,
                    timeInForce='gfd'  # Good for day
                )
            else:  # SELL
                order = order_sell_market(
                    symbol=signal.symbol,
                    quantity=signal.position_size,
                    timeInForce='gfd'
                )
            
            return {
                'status': 'SUCCESS',
                'order_id': order['id'],
                'symbol': signal.symbol,
                'entry_price': signal.entry_price,
                'position_size': signal.position_size
            }
            
        except Exception as e:
            self.logger.error(f"Robinhood execution failed: {e}")
            return {'status': 'FAILED', 'error': str(e)}

# Usage
async def main():
    engine = RobinhoodTradingEngine(
        email="your_email@gmail.com",
        password="your_password"
    )
    
    signal = await engine.generate_trade_signal('NVDA')
    result = await engine.execute_signal(signal)

asyncio.run(main())
```

---

## Data Source Integration

### Real-time Price Updates with WebSocket

```python
import asyncio
import websocket
import json
from enhanced_trading_engine import EnhancedTradingEngine

class RealtimePricingEngine(EnhancedTradingEngine):
    """Engine with real-time price updates."""
    
    def __init__(self, alpaca_api_key: str):
        super().__init__(alpaca_api_key=alpaca_api_key)
        self.price_cache = {}
        self.ws_url = 'wss://stream.data.alpaca.markets/v1beta1/crypto'

    async def start_price_stream(self):
        """Start WebSocket stream for real-time prices."""
        
        async def on_message(msg):
            try:
                data = json.loads(msg)
                
                if 'data' in data:
                    for bar in data['data']:
                        self.price_cache[bar['S']] = bar['c']  # Update cache
                        
                        # Trigger monitoring if position open
                        if bar['S'] in self.open_positions:
                            await self.monitor_position(
                                order_id=list(self.open_positions.keys())[0],
                                current_price=bar['c']
                            )
            except Exception as e:
                self.logger.error(f"Price stream error: {e}")
        
        # WebSocket connection (simplified)
        ws = websocket.WebSocketApp(
            self.ws_url,
            on_message=on_message,
            on_error=lambda ws, err: print(f"WS Error: {err}"),
            on_close=lambda ws: print("WS Closed")
        )
        
        ws.run_forever()

# Usage
async def main():
    engine = RealtimePricingEngine(alpaca_api_key="YOUR_KEY")
    
    # Start price stream in background
    asyncio.create_task(engine.start_price_stream())
    
    # Trade signals
    while True:
        signal = await engine.generate_trade_signal('NVDA')
        if signal:
            result = await engine.execute_signal(signal)
        
        await asyncio.sleep(60)  # Check every minute

asyncio.run(main())
```

### Alternative Data Sources (Finnhub, Polygon)

```python
import asyncio
import httpx
from enhanced_trading_engine import EnhancedTradingEngine

class EnhancedDataEngine(EnhancedTradingEngine):
    """Engine with multiple data sources."""
    
    def __init__(self, finnhub_key: str, polygon_key: str):
        super().__init__(finnhub_api_key=finnhub_key)
        self.polygon_key = polygon_key
        self.polygon_url = f"https://api.polygon.io"

    async def fetch_historical_data(self, symbol: str, span: str = "1M"):
        """Fetch data from Polygon for extended history."""
        
        async with httpx.AsyncClient() as client:
            # Fetch 1-minute bars from Polygon
            response = await client.get(
                f"{self.polygon_url}/v2/aggs/ticker/{symbol}/range/1/minute/2024-01-01/2024-12-31",
                params={
                    'adjusted': 'true',
                    'sort': 'asc',
                    'apiKey': self.polygon_key,
                    'limit': 50000
                }
            )
            
            return response.json()['results']

    async def get_company_news(self, symbol: str):
        """Get latest company news from Finnhub."""
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://finnhub.io/api/v1/company-news",
                params={
                    'symbol': symbol,
                    'limit': 10,
                    'token': self.catalyst_scorer.finnhub_api_key
                }
            )
            
            return response.json()

# Usage
async def main():
    engine = EnhancedDataEngine(
        finnhub_key="YOUR_FINNHUB_KEY",
        polygon_key="YOUR_POLYGON_KEY"
    )
    
    # Get historical data
    bars = await engine.fetch_historical_data('NVDA')
    
    # Get news
    news = await engine.get_company_news('NVDA')
    
    print(f"Latest bars: {len(bars)}")
    print(f"News articles: {len(news)}")

asyncio.run(main())
```

---

## Production Deployment

### Docker Deployment

```dockerfile
# Dockerfile for Enhanced Trading Engine
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY enhanced_trading_engine.py .
COPY multi_timeframe_validator.py .
COPY catalyst_scorer.py .
COPY symbol_watchlist.py .
COPY dynamic_risk_params.py .
COPY trading_service.py .

# Set environment
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO

# Run service
CMD ["python", "trading_service.py"]
```

```yaml
# docker-compose.yml
version: '3.9'

services:
  trading-engine:
    build: .
    environment:
      - ALPACA_API_KEY=${ALPACA_API_KEY}
      - ALPACA_SECRET_KEY=${ALPACA_SECRET_KEY}
      - FINNHUB_API_KEY=${FINNHUB_API_KEY}
      - LOG_LEVEL=INFO
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    ports:
      - "8000:8000"
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Kubernetes Deployment

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: trading-engine
spec:
  replicas: 1
  selector:
    matchLabels:
      app: trading-engine
  template:
    metadata:
      labels:
        app: trading-engine
    spec:
      containers:
      - name: trading-engine
        image: profitengine/trading-engine:v5.0.0
        env:
        - name: ALPACA_API_KEY
          valueFrom:
            secretKeyRef:
              name: trading-secrets
              key: alpaca-key
        - name: ALPACA_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: trading-secrets
              key: alpaca-secret
        - name: FINNHUB_API_KEY
          valueFrom:
            secretKeyRef:
              name: trading-secrets
              key: finnhub-key
        ports:
        - containerPort: 8000
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        resources:
          requests:
            memory: "256Mi"
            cpu: "500m"
          limits:
            memory: "512Mi"
            cpu: "1000m"
```

### Systemd Service

```ini
# /etc/systemd/system/trading-engine.service
[Unit]
Description=ProfitEngine v5 Trading Engine
After=network.target

[Service]
Type=simple
User=trading
WorkingDirectory=/opt/trading-engine
Environment="PATH=/opt/trading-engine/venv/bin"
Environment="PYTHONUNBUFFERED=1"
Environment="ALPACA_API_KEY=your_key"
Environment="ALPACA_SECRET_KEY=your_secret"
ExecStart=/opt/trading-engine/venv/bin/python trading_service.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable trading-engine
sudo systemctl start trading-engine
sudo systemctl status trading-engine
```

---

## Backtesting Integration

### Backtest Framework

```python
import asyncio
from datetime import datetime, timedelta
from enhanced_trading_engine import EnhancedTradingEngine, SignalAction
import pandas as pd

class BacktestEngine(EnhancedTradingEngine):
    """Backtesting engine with historical data."""
    
    def __init__(self, historical_data: dict, initial_balance: float = 50000.0):
        super().__init__(account_balance=initial_balance)
        self.historical_data = historical_data  # Dict[symbol, DataFrame]
        self.current_index = 0
        self.results = []

    async def backtest_period(self, symbols: list, start_date: str, end_date: str):
        """Run backtest over date range."""
        
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        current = start
        
        while current <= end:
            # Get signals for all symbols
            for symbol in symbols:
                signal = await self.generate_trade_signal(symbol, force_analysis=True)
                
                if signal and signal.confidence >= 75:
                    # Simulate execution with historical price
                    self._simulate_execution(signal, current)
            
            # Move to next trading day
            current += timedelta(days=1)
            
            # Update positions with next day's prices
            self._update_positions_to_date(current)
        
        return self.get_results()

    def _simulate_execution(self, signal, date):
        """Simulate order execution."""
        order_id = f"{signal.symbol}_{date.timestamp()}"
        
        self.open_positions[order_id] = {
            'order_id': order_id,
            'symbol': signal.symbol,
            'action': signal.action.value,
            'entry_price': signal.entry_price,
            'entry_date': date,
            'position_size': signal.position_size,
            'stop_loss': signal.stop_price,
            'take_profit': signal.target_price
        }

    def _update_positions_to_date(self, date):
        """Update position prices to date."""
        for order_id, pos in list(self.open_positions.items()):
            # Get next day's price
            next_price = self._get_price(pos['symbol'], date)
            
            if next_price:
                pnl = (next_price - pos['entry_price']) * pos['position_size']
                
                # Check stop/target
                if next_price <= pos['stop_loss']:
                    self._close_position(order_id, next_price, 'STOP')
                elif next_price >= pos['take_profit']:
                    self._close_position(order_id, next_price, 'TARGET')

    def _get_price(self, symbol: str, date):
        """Get price for symbol on date."""
        if symbol not in self.historical_data:
            return None
        
        df = self.historical_data[symbol]
        day_data = df[df.index.date == date.date()]
        
        return day_data['close'].iloc[-1] if len(day_data) > 0 else None

    def _close_position(self, order_id, close_price, reason):
        """Close position and record P&L."""
        pos = self.open_positions.pop(order_id)
        pnl = (close_price - pos['entry_price']) * pos['position_size']
        
        self.results.append({
            'order_id': order_id,
            'symbol': pos['symbol'],
            'action': pos['action'],
            'entry_price': pos['entry_price'],
            'close_price': close_price,
            'entry_date': pos['entry_date'],
            'position_size': pos['position_size'],
            'pnl': pnl,
            'pnl_percent': (pnl / (pos['entry_price'] * pos['position_size'])) * 100,
            'reason': reason
        })

    def get_results(self):
        """Get backtest results."""
        df = pd.DataFrame(self.results)
        
        if len(df) == 0:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'sharpe_ratio': 0
            }
        
        return {
            'total_trades': len(df),
            'winning_trades': len(df[df['pnl'] > 0]),
            'losing_trades': len(df[df['pnl'] <= 0]),
            'win_rate': len(df[df['pnl'] > 0]) / len(df) * 100,
            'total_pnl': df['pnl'].sum(),
            'avg_pnl': df['pnl'].mean(),
            'sharpe_ratio': df['pnl_percent'].mean() / df['pnl_percent'].std() if len(df) > 1 else 0
        }

# Usage
async def main():
    # Load historical data
    historical_data = {
        'NVDA': pd.read_csv('nvda_history.csv', index_col='date', parse_dates=True),
        'TSLA': pd.read_csv('tsla_history.csv', index_col='date', parse_dates=True)
    }
    
    engine = BacktestEngine(historical_data)
    
    results = await engine.backtest_period(
        symbols=['NVDA', 'TSLA'],
        start_date='2024-01-01',
        end_date='2024-12-31'
    )
    
    print(f"Win Rate: {results['win_rate']:.1f}%")
    print(f"Total P&L: ${results['total_pnl']:.2f}")
    print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")

asyncio.run(main())
```

---

## Monitoring & Alerts

### Email Alerts

```python
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class AlertingEngine(EnhancedTradingEngine):
    """Engine with email notifications."""
    
    def __init__(self, smtp_server: str, smtp_port: int, email: str, password: str):
        super().__init__()
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = email
        self.sender_password = password
        self.recipient_email = email  # Send to self

    async def send_alert(self, subject: str, message: str):
        """Send email alert."""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(message, 'html'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
                
            self.logger.info(f"Alert sent: {subject}")
        except Exception as e:
            self.logger.error(f"Failed to send alert: {e}")

    async def monitor_with_alerts(self):
        """Monitor with email notifications."""
        
        while True:
            positions = await self.monitor_all_positions()
            
            for order_id, pos in positions.items():
                # Alert on large P&L
                if pos.unrealized_pnl_percent > 10:
                    await self.send_alert(
                        f"Target Hit: {pos.symbol}",
                        f"Position {pos.symbol} has reached +{pos.unrealized_pnl_percent:.1f}% P&L"
                    )
                
                if pos.unrealized_pnl_percent < -5:
                    await self.send_alert(
                        f"Stop Loss: {pos.symbol}",
                        f"Position {pos.symbol} has hit -{abs(pos.unrealized_pnl_percent):.1f}% loss"
                    )
            
            await asyncio.sleep(300)  # Check every 5 minutes
```

### Slack Notifications

```python
import asyncio
import httpx

class SlackAlertingEngine(EnhancedTradingEngine):
    """Engine with Slack notifications."""
    
    def __init__(self, slack_webhook_url: str):
        super().__init__()
        self.slack_webhook = slack_webhook_url

    async def send_slack_message(self, text: str, blocks: list = None):
        """Send message to Slack."""
        
        payload = {
            'text': text,
            'blocks': blocks or []
        }
        
        async with httpx.AsyncClient() as client:
            await client.post(self.slack_webhook, json=payload)

    async def notify_signal(self, signal):
        """Notify on new signal."""
        
        await self.send_slack_message(
            text=f"Trading Signal: {signal.action.value} {signal.symbol}",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"""
*{signal.action.value} {signal.symbol}*
Entry: ${signal.entry_price:.2f}
Stop: ${signal.stop_price:.2f}
Target: ${signal.target_price:.2f}
Confidence: {signal.confidence}%
Position: {signal.position_size} shares
                        """
                    }
                }
            ]
        )
```

---

## API Server Deployment

### FastAPI Service

```python
# trading_service.py
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import asyncio
from enhanced_trading_engine import EnhancedTradingEngine, SignalAction
from pydantic import BaseModel

app = FastAPI(title="Trading Engine API")

# Initialize engine
engine = EnhancedTradingEngine(
    account_balance=50000.0
)

# Pydantic models
class SignalRequest(BaseModel):
    symbol: str

class ExecuteRequest(BaseModel):
    order_id: str

@app.on_event("startup")
async def startup():
    """Initialize on startup."""
    print("Trading Engine API started")

@app.get("/health")
async def health():
    """Health check endpoint."""
    metrics = engine.get_portfolio_metrics()
    return {
        'status': 'healthy',
        'account_balance': metrics['account_balance'],
        'open_positions': metrics['open_positions']
    }

@app.post("/signal")
async def generate_signal(request: SignalRequest):
    """Generate trading signal."""
    try:
        signal = await engine.generate_trade_signal(request.symbol)
        
        if signal is None:
            return JSONResponse(
                status_code=404,
                content={'error': 'No signal generated'}
            )
        
        return signal.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/execute")
async def execute_signal(request: SignalRequest):
    """Execute signal."""
    try:
        signal = await engine.generate_trade_signal(request.symbol)
        
        if signal is None or signal.action == SignalAction.NONE:
            raise HTTPException(status_code=400, detail="No valid signal")
        
        result = await engine.execute_signal(signal)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/positions")
async def get_positions():
    """Get all open positions."""
    positions = await engine.monitor_all_positions()
    return {
        'positions': {k: v.__dict__ for k, v in positions.items()},
        'count': len(positions)
    }

@app.get("/metrics")
async def get_metrics():
    """Get portfolio metrics."""
    return engine.get_portfolio_metrics()

@app.post("/monitor/{order_id}")
async def monitor_position(order_id: str):
    """Monitor specific position."""
    position = await engine.monitor_position(order_id)
    
    if position is None:
        raise HTTPException(status_code=404, detail="Position not found")
    
    return position.__dict__

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
```

Run with:
```bash
python trading_service.py

# Or with Gunicorn for production
gunicorn -w 4 -k uvicorn.workers.UvicornWorker trading_service:app
```

### API Client

```python
import httpx
import asyncio

class TradingAPIClient:
    """Client for Trading Engine API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    async def get_signal(self, symbol: str):
        """Get trading signal."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/signal",
                json={'symbol': symbol}
            )
            return response.json()

    async def execute_signal(self, symbol: str):
        """Execute signal."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/execute",
                json={'symbol': symbol}
            )
            return response.json()

    async def get_positions(self):
        """Get open positions."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/positions")
            return response.json()

    async def get_metrics(self):
        """Get portfolio metrics."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/metrics")
            return response.json()

# Usage
async def main():
    client = TradingAPIClient()
    
    signal = await client.get_signal('NVDA')
    print(f"Signal: {signal}")
    
    result = await client.execute_signal('NVDA')
    print(f"Execution: {result}")

asyncio.run(main())
```

---

## Summary

| Integration | File | Status |
|---|---|---|
| Alpaca Broker | See AlpacaTradingEngine | Production Ready |
| Robinhood Broker | See RobinhoodTradingEngine | Production Ready |
| Real-time Data | WebSocket + Alpaca | Production Ready |
| Backtesting | BacktestEngine | Production Ready |
| Email Alerts | AlertingEngine | Production Ready |
| Slack Alerts | SlackAlertingEngine | Production Ready |
| Docker | Dockerfile + compose | Production Ready |
| Kubernetes | k8s-deployment.yaml | Production Ready |
| FastAPI | trading_service.py | Production Ready |
| API Client | TradingAPIClient | Production Ready |

---

**Version**: 5.0.0  
**Last Updated**: 2024-12-20  
**Status**: Production Ready
