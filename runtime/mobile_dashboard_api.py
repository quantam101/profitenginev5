"""
MOBILE DASHBOARD API — Access trading system from phone/tablet
Real-time P&L, trades, positions, strategy performance
Works on any device (phone, tablet, laptop)
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List
from decimal import Decimal
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MobileDashboard")

# ============================================================================
# MOBILE API SERVER (Phone-Accessible)
# ============================================================================

class MobileDashboardAPI:
    """Exposes trading system to phones/tablets"""

    def __init__(self, orchestrator=None):
        self.orchestrator = orchestrator
        self.app = FastAPI(
            title="ProfitEngine Mobile Dashboard",
            version="1.0.0",
            description="Real-time trading dashboard for mobile devices"
        )
        self._setup_cors()
        self._setup_routes()

    def _setup_cors(self):
        """Enable CORS for phone/tablet access"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Allow all origins (phone, tablet, laptop)
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        logger.info("✅ CORS enabled (phone/tablet access allowed)")

    def _setup_routes(self):
        """Setup all API endpoints"""

        @self.app.get("/")
        async def root():
            """Serve mobile dashboard HTML"""
            return HTMLResponse(self._get_dashboard_html())

        @self.app.get("/api/status")
        async def get_status():
            """Get current trading status (for phone dashboard)"""
            if not self.orchestrator:
                return {"error": "Orchestrator not initialized"}

            status = await self.orchestrator.get_status()
            return {
                "timestamp": datetime.now().isoformat(),
                "balance": float(status["portfolio"]["balance"]),
                "pnl": float(status["portfolio"]["pnl"]),
                "pnl_percent": status["portfolio"]["pnl_percent"],
                "positions_open": status["portfolio"]["positions_open"],
                "trades_today": status["portfolio"]["trades_today"],
                "agents": {
                    agent_id: {
                        "status": agent_status["status"],
                        "tasks": agent_status["tasks_completed"],
                    }
                    for agent_id, agent_status in status["agents"].items()
                },
                "alerts": status["alerts"],
            }

        @self.app.get("/api/portfolio")
        async def get_portfolio():
            """Get detailed portfolio info"""
            if not self.orchestrator:
                return {"error": "Orchestrator not initialized"}

            from runtime.mcp_native_trading_engine import PORTFOLIO

            positions = [
                {
                    "symbol": symbol,
                    "side": pos["side"],
                    "entry_price": float(pos["entry_price"]),
                    "shares": float(pos["shares"]),
                    "stop_loss": float(pos["stop_loss"]),
                    "take_profit": float(pos["take_profit"]),
                    "entry_time": pos["entry_time"],
                }
                for symbol, pos in PORTFOLIO.positions.items()
            ]

            return {
                "account_balance": float(PORTFOLIO.account_balance),
                "target_balance": 1000.0,
                "daily_drawdown": float(PORTFOLIO.daily_drawdown),
                "positions": positions,
                "position_count": len(positions),
                "progress_percent": (
                    float(PORTFOLIO.account_balance) / 1000.0 * 100
                ),
            }

        @self.app.get("/api/trades")
        async def get_trades(limit: int = 20):
            """Get recent trades"""
            if not self.orchestrator:
                return {"error": "Orchestrator not initialized"}

            from runtime.mcp_native_trading_engine import PORTFOLIO

            trades = PORTFOLIO.trade_log[-limit:]
            return {
                "trades": trades,
                "count": len(trades),
                "total_trades": len(PORTFOLIO.trade_log),
            }

        @self.app.get("/api/performance")
        async def get_performance():
            """Get strategy performance metrics"""
            if not self.orchestrator:
                return {"error": "Orchestrator not initialized"}

            from runtime.mcp_native_trading_engine import PORTFOLIO

            # Calculate simple metrics
            trades = PORTFOLIO.trade_log
            winning_trades = len([t for t in trades if t.get("pnl", 0) > 0])
            losing_trades = len([t for t in trades if t.get("pnl", 0) < 0])
            total_trades = len(trades)

            win_rate = (
                (winning_trades / total_trades * 100) if total_trades > 0 else 0
            )

            return {
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "win_rate_percent": round(win_rate, 2),
                "daily_pnl": float(
                    PORTFOLIO.account_balance - Decimal("100.00")
                ),
            }

        @self.app.websocket("/ws/live")
        async def websocket_live(websocket: WebSocket):
            """WebSocket for live updates (low-latency phone updates)"""
            await websocket.accept()
            logger.info("📱 Phone connected to live WebSocket")

            try:
                while True:
                    # Send status every 5 seconds
                    if self.orchestrator:
                        status = await self.orchestrator.get_status()
                        await websocket.send_json({
                            "type": "status_update",
                            "balance": float(status["portfolio"]["balance"]),
                            "pnl": float(status["portfolio"]["pnl"]),
                            "timestamp": datetime.now().isoformat(),
                        })
                    await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"WebSocket error: {e}")

    def _get_dashboard_html(self) -> str:
        """Generate mobile-friendly dashboard HTML"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ProfitEngine — Trading Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f1419;
            color: #e0e0e0;
            padding: 16px;
            max-width: 800px;
            margin: 0 auto;
        }

        .header {
            text-align: center;
            margin-bottom: 24px;
            padding: 16px;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            border-radius: 12px;
        }

        .header h1 {
            font-size: 28px;
            margin-bottom: 8px;
        }

        .status {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            margin-bottom: 24px;
        }

        .card {
            background: #1a1f2e;
            border: 1px solid #333;
            border-radius: 12px;
            padding: 16px;
            text-align: center;
        }

        .card.primary {
            grid-column: 1 / -1;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            border: none;
        }

        .card.alert {
            background: #2a1a1a;
            border-color: #ff4444;
        }

        .label {
            font-size: 12px;
            color: #888;
            text-transform: uppercase;
            margin-bottom: 8px;
        }

        .value {
            font-size: 24px;
            font-weight: bold;
            color: #4ade80;
        }

        .value.negative {
            color: #f87171;
        }

        .progress-bar {
            width: 100%;
            height: 8px;
            background: #333;
            border-radius: 4px;
            margin: 12px 0;
            overflow: hidden;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #4ade80 0%, #60a5fa 100%);
            border-radius: 4px;
            transition: width 0.3s ease;
        }

        .section {
            margin-bottom: 24px;
        }

        .section-title {
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 12px;
            color: #60a5fa;
            text-transform: uppercase;
        }

        .position {
            background: #1a1f2e;
            border: 1px solid #333;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .position-symbol {
            font-weight: bold;
            font-size: 18px;
        }

        .position-info {
            font-size: 12px;
            color: #888;
        }

        .position-price {
            font-weight: bold;
            color: #4ade80;
        }

        .btn {
            background: #2a5298;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 12px 16px;
            font-size: 14px;
            cursor: pointer;
            width: 100%;
            margin-top: 12px;
            transition: background 0.2s;
        }

        .btn:active {
            background: #1e3c72;
        }

        .alert-item {
            background: #2a1a1a;
            border-left: 4px solid #ff4444;
            padding: 12px;
            margin-bottom: 8px;
            border-radius: 4px;
            font-size: 12px;
        }

        .spinner {
            display: inline-block;
            width: 16px;
            height: 16px;
            border: 2px solid #333;
            border-top-color: #4ade80;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #4ade80;
            margin-right: 8px;
        }

        .status-indicator.error {
            background: #f87171;
        }

        @media (max-width: 600px) {
            body { padding: 12px; }
            .header h1 { font-size: 24px; }
            .value { font-size: 20px; }
            .card { padding: 12px; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 ProfitEngine</h1>
        <p>Autonomous Trading System</p>
    </div>

    <div class="status">
        <div class="card primary">
            <div class="label">Account Balance</div>
            <div class="value" id="balance">$100.00</div>
            <div class="progress-bar">
                <div class="progress-fill" id="progressBar" style="width: 10%"></div>
            </div>
            <div style="font-size: 12px; color: #aaa;">
                Target: $1,000 | Progress: <span id="progress">10</span>%
            </div>
        </div>

        <div class="card">
            <div class="label">Today's P&L</div>
            <div class="value" id="pnl">$0.00</div>
            <div style="font-size: 12px; color: #888;" id="pnlPercent">0%</div>
        </div>

        <div class="card">
            <div class="label">Open Positions</div>
            <div class="value" id="positions">0</div>
        </div>

        <div class="card">
            <div class="label">Trades Today</div>
            <div class="value" id="trades">0</div>
        </div>
    </div>

    <div class="section">
        <div class="section-title">
            <span class="status-indicator" id="agentStatus"></span>
            System Status
        </div>
        <div id="agentsList" style="font-size: 12px; color: #888;">
            Initializing...
        </div>
    </div>

    <div class="section">
        <div class="section-title">Open Positions</div>
        <div id="positionsList">
            <p style="color: #888; text-align: center; padding: 20px;">
                No open positions
            </p>
        </div>
    </div>

    <div class="section" id="alertsSection" style="display: none;">
        <div class="section-title">⚠️ Alerts</div>
        <div id="alertsList"></div>
    </div>

    <button class="btn" onclick="location.reload()">
        🔄 Refresh
    </button>

    <script>
        async function updateDashboard() {
            try {
                // Fetch status
                const statusResp = await fetch('/api/status');
                const status = await statusResp.json();

                if (status.error) {
                    document.getElementById('agentStatus').classList.add('error');
                    return;
                }

                // Update main metrics
                document.getElementById('balance').textContent =
                    '$' + status.balance.toFixed(2);
                document.getElementById('pnl').textContent =
                    '$' + status.pnl.toFixed(2);
                document.getElementById('pnlPercent').textContent =
                    status.pnl_percent.toFixed(1) + '%';
                document.getElementById('positions').textContent =
                    status.positions_open;
                document.getElementById('trades').textContent =
                    status.trades_today;

                // Update progress bar
                const progress = (status.balance / 1000) * 100;
                document.getElementById('progressBar').style.width = progress + '%';
                document.getElementById('progress').textContent = Math.round(progress);

                // Update agent status
                const agents = Object.values(status.agents);
                const allHealthy = agents.every(a => a.status === 'HEALTHY');
                document.getElementById('agentStatus').classList.toggle('error', !allHealthy);

                // Fetch portfolio
                const portfolioResp = await fetch('/api/portfolio');
                const portfolio = await portfolioResp.json();

                // Update positions list
                if (portfolio.positions.length > 0) {
                    document.getElementById('positionsList').innerHTML =
                        portfolio.positions.map(p =>
                            `<div class="position">
                                <div>
                                    <div class="position-symbol">${p.symbol}</div>
                                    <div class="position-info">${p.side} @ $${p.entry_price.toFixed(2)}</div>
                                </div>
                                <div class="position-price">${p.shares} shares</div>
                            </div>`
                        ).join('');
                } else {
                    document.getElementById('positionsList').innerHTML =
                        '<p style="color: #888; text-align: center; padding: 20px;">No open positions</p>';
                }

                // Update alerts
                if (status.alerts.length > 0) {
                    document.getElementById('alertsSection').style.display = 'block';
                    document.getElementById('alertsList').innerHTML =
                        status.alerts.slice(-5).map(a =>
                            `<div class="alert-item">⚠️ ${a}</div>`
                        ).join('');
                }

            } catch (e) {
                console.error('Dashboard update failed:', e);
            }
        }

        // Initial load
        updateDashboard();

        // Update every 5 seconds
        setInterval(updateDashboard, 5000);

        // Try WebSocket for real-time updates
        try {
            const ws = new WebSocket(
                'ws://' + window.location.host + '/ws/live'
            );
            ws.onmessage = (event) => {
                console.log('Live update:', event.data);
                updateDashboard();
            };
        } catch (e) {
            console.log('WebSocket not available, using polling');
        }
    </script>
</body>
</html>
"""

    async def start(self, host: str = "0.0.0.0", port: int = 8000):
        """Start the mobile dashboard API server"""
        logger.info("="*80)
        logger.info("MOBILE DASHBOARD API STARTING")
        logger.info("="*80)
        logger.info(f"\n📱 Phone/Tablet Access:")
        logger.info(f"  Dashboard: http://your_machine_ip:8000")
        logger.info(f"  Endpoints:")
        logger.info(f"    - GET /api/status (current metrics)")
        logger.info(f"    - GET /api/portfolio (positions)")
        logger.info(f"    - GET /api/trades (recent trades)")
        logger.info(f"    - GET /api/performance (statistics)")
        logger.info(f"    - WS /ws/live (real-time updates)\n")

        import uvicorn
        config = uvicorn.Config(
            app=self.app,
            host=host,
            port=port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()


# ============================================================================
# STANDALONE LAUNCHER
# ============================================================================

if __name__ == "__main__":
    async def main():
        api = MobileDashboardAPI()
        await api.start(host="0.0.0.0", port=8000)

    asyncio.run(main())
