"""
CLIENT API — REST endpoints for querying client trading data
Serves profitengine-tau, content, and other external repos
Provides: stats, leaderboard, upsell candidates, individual performance, daily summary
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from decimal import Decimal
from functools import wraps
import hashlib
import hmac
import time

from fastapi import FastAPI, HTTPException, Request, Header, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


# ============================================================================
# CONFIGURATION
# ============================================================================

API_KEY_HASH = os.environ.get(
    "CLIENT_API_KEY_HASH",
    hashlib.sha256(b"default-dev-key").hexdigest()
)
WEBHOOK_SECRET = os.environ.get(
    "CLIENT_API_WEBHOOK_SECRET",
    "default-webhook-secret"
)
DB_PATH = os.environ.get(
    "CLIENTS_DB_PATH",
    "clients.db"
)
RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_WINDOW = 3600  # seconds


# ============================================================================
# SCHEMAS
# ============================================================================

class ClientStats(BaseModel):
    """Aggregate trading statistics across all clients"""
    total_traders: int
    active_traders: int
    avg_win_rate: float
    total_pnl: float
    total_trades: int
    avg_trades_per_trader: float
    timestamp: str


class LeaderboardEntry(BaseModel):
    """Single leaderboard entry"""
    rank: int
    user_id: str
    username: Optional[str] = None
    metric_value: float
    secondary_value: Optional[float] = None
    days_active: int
    account_age_days: int


class Leaderboard(BaseModel):
    """Complete leaderboard response"""
    metric: str
    entries: List[LeaderboardEntry]
    timestamp: str
    updated_at: Optional[str] = None


class UpsellCandidate(BaseModel):
    """Client ready for premium upgrade"""
    user_id: str
    username: Optional[str] = None
    current_pnl: float
    win_rate: float
    total_trades: int
    days_active: int
    recommendation: str
    potential_value: Optional[float] = None
    urgency: str  # "low", "medium", "high"


class TraderPerformance(BaseModel):
    """Individual trader's performance metrics"""
    user_id: str
    username: Optional[str] = None
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    consecutive_wins: int
    consecutive_losses: int
    days_active: int
    account_created: str
    last_trade: Optional[str] = None
    current_streak: str
    account_status: str


class DailyTrade(BaseModel):
    """Single trade from today"""
    trade_id: str
    user_id: str
    symbol: str
    side: str
    entry_price: float
    exit_price: Optional[float] = None
    shares: int
    pnl: float
    pnl_percent: float
    entry_time: str
    exit_time: Optional[str] = None
    status: str


class DailySummary(BaseModel):
    """Today's trading activity summary"""
    date: str
    total_trades: int
    trades_by_user: Dict[str, int]
    total_pnl: float
    pnl_by_user: Dict[str, float]
    top_symbol: Optional[str] = None
    win_rate: float
    active_users: int
    recent_trades: List[DailyTrade] = Field(default_factory=list)
    timestamp: str


# ============================================================================
# RATE LIMITING
# ============================================================================

class RateLimiter:
    """Simple in-memory rate limiter"""

    def __init__(self, requests: int = RATE_LIMIT_REQUESTS, window: int = RATE_LIMIT_WINDOW):
        self.requests = requests
        self.window = window
        self.calls = {}

    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed"""
        now = time.time()
        if identifier not in self.calls:
            self.calls[identifier] = []

        # Clean old calls outside window
        self.calls[identifier] = [
            ts for ts in self.calls[identifier]
            if now - ts < self.window
        ]

        if len(self.calls[identifier]) < self.requests:
            self.calls[identifier].append(now)
            return True
        return False


rate_limiter = RateLimiter()


# ============================================================================
# DATABASE HELPERS
# ============================================================================

class ClientDB:
    """SQLite database wrapper for client trading data"""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._ensure_schema()

    def _ensure_schema(self):
        """Create tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Clients table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clients (
                    user_id TEXT PRIMARY KEY,
                    username TEXT,
                    email TEXT UNIQUE,
                    account_created TEXT NOT NULL,
                    account_status TEXT DEFAULT 'active',
                    tier TEXT DEFAULT 'free'
                )
            """)

            # Trades table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    trade_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    entry_price REAL NOT NULL,
                    exit_price REAL,
                    shares INTEGER NOT NULL,
                    pnl REAL NOT NULL,
                    pnl_percent REAL,
                    entry_time TEXT NOT NULL,
                    exit_time TEXT,
                    status TEXT DEFAULT 'closed',
                    FOREIGN KEY (user_id) REFERENCES clients(user_id)
                )
            """)

            # Performance cache (materialized view for speed)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trader_stats (
                    user_id TEXT PRIMARY KEY,
                    total_trades INTEGER,
                    winning_trades INTEGER,
                    losing_trades INTEGER,
                    total_pnl REAL,
                    win_rate REAL,
                    days_active INTEGER,
                    last_updated TEXT,
                    FOREIGN KEY (user_id) REFERENCES clients(user_id)
                )
            """)

            conn.commit()

    def get_connection(self):
        """Get connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def client_exists(self, user_id: str) -> bool:
        """Check if client exists"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM clients WHERE user_id = ?", (user_id,))
            return cursor.fetchone() is not None

    def get_all_clients(self) -> List[Dict]:
        """Get all registered clients"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clients WHERE account_status = 'active'")
            return [dict(row) for row in cursor.fetchall()]

    def get_client_trades(self, user_id: str, days: int = 30) -> List[Dict]:
        """Get trades for a client in last N days"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            since = datetime.now(timezone.utc) - timedelta(days=days)
            cursor.execute(
                "SELECT * FROM trades WHERE user_id = ? AND entry_time > ? ORDER BY entry_time DESC",
                (user_id, since.isoformat())
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_today_trades(self) -> List[Dict]:
        """Get all trades from today"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            today = datetime.now(timezone.utc).date()
            cursor.execute(
                "SELECT * FROM trades WHERE DATE(entry_time) = ? ORDER BY entry_time DESC",
                (today.isoformat(),)
            )
            return [dict(row) for row in cursor.fetchall()]

    def calculate_stats(self, user_id: str, trades: List[Dict]) -> Dict[str, Any]:
        """Calculate performance statistics"""
        if not trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "total_pnl": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "largest_win": 0.0,
                "largest_loss": 0.0,
            }

        wins = [t for t in trades if t["pnl"] > 0]
        losses = [t for t in trades if t["pnl"] < 0]
        total_pnl = sum(t["pnl"] for t in trades)

        return {
            "total_trades": len(trades),
            "winning_trades": len(wins),
            "losing_trades": len(losses),
            "win_rate": (len(wins) / len(trades) * 100) if trades else 0.0,
            "total_pnl": total_pnl,
            "avg_win": (sum(t["pnl"] for t in wins) / len(wins)) if wins else 0.0,
            "avg_loss": (sum(t["pnl"] for t in losses) / len(losses)) if losses else 0.0,
            "largest_win": max((t["pnl"] for t in wins), default=0.0),
            "largest_loss": min((t["pnl"] for t in losses), default=0.0),
        }


client_db = ClientDB()


# ============================================================================
# AUTHENTICATION
# ============================================================================

def verify_api_key(api_key: str) -> bool:
    """Verify API key against stored hash"""
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    return hmac.compare_digest(key_hash, API_KEY_HASH)


def verify_webhook_signature(body: bytes, signature: str) -> bool:
    """Verify webhook signature (HMAC-SHA256)"""
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)


async def verify_auth(authorization: Optional[str] = Header(None), request: Optional[Request] = None) -> str:
    """Middleware to verify API key or webhook"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization format")

    api_key = parts[1]
    if not verify_api_key(api_key):
        raise HTTPException(status_code=403, detail="Invalid API key")

    return api_key


# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="ProfitEngine Client API",
    version="1.0.0",
    description="REST endpoints for querying client trading data",
)

# CORS middleware for cross-repo access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# ============================================================================
# MIDDLEWARE & HELPERS
# ============================================================================

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Apply rate limiting to all requests"""
    # Get client identifier (IP or API key)
    api_key = request.headers.get("Authorization", "").split(" ")[-1] if "Authorization" in request.headers else request.client.host
    identifier = hashlib.sha256(api_key.encode()).hexdigest()[:16]

    if not rate_limiter.is_allowed(identifier):
        return JSONResponse(
            status_code=429,
            content={"error": "Rate limit exceeded", "limit": RATE_LIMIT_REQUESTS, "window": RATE_LIMIT_WINDOW},
        )

    return await call_next(request)


def decode_pnl(value):
    """Safely convert PnL value to float"""
    if value is None:
        return 0.0
    if isinstance(value, str):
        return float(value) if value else 0.0
    return float(value)


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/api/health")
async def health() -> Dict[str, Any]:
    """Health check endpoint (no auth required)"""
    return {
        "ok": True,
        "service": "client-api",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "db_ready": client_db.client_exists("_test") or True,
    }


# ============================================================================
# STATS ENDPOINT
# ============================================================================

@app.get("/api/clients/stats", response_model=ClientStats)
async def get_aggregate_stats(
    authorization: Optional[str] = Header(None),
    days: int = Query(30, ge=1, le=365),
) -> ClientStats:
    """
    Get aggregate trading statistics across all clients.
    Returns: total traders, active traders, avg win rate, total P&L
    """
    await verify_auth(authorization)

    clients = client_db.get_all_clients()
    if not clients:
        return ClientStats(
            total_traders=0,
            active_traders=0,
            avg_win_rate=0.0,
            total_pnl=0.0,
            total_trades=0,
            avg_trades_per_trader=0.0,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    all_trades = []
    win_rates = []
    trader_trade_counts = []

    for client in clients:
        trades = client_db.get_client_trades(client["user_id"], days=days)
        if trades:
            all_trades.extend(trades)
            stats = client_db.calculate_stats(client["user_id"], trades)
            win_rates.append(stats["win_rate"])
            trader_trade_counts.append(len(trades))

    avg_win_rate = sum(win_rates) / len(win_rates) if win_rates else 0.0
    total_pnl = sum(decode_pnl(t["pnl"]) for t in all_trades)
    avg_trades = sum(trader_trade_counts) / len(trader_trade_counts) if trader_trade_counts else 0.0

    return ClientStats(
        total_traders=len(clients),
        active_traders=len([c for c in clients if trader_trade_counts]),
        avg_win_rate=round(avg_win_rate, 2),
        total_pnl=round(total_pnl, 2),
        total_trades=len(all_trades),
        avg_trades_per_trader=round(avg_trades, 1),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


# ============================================================================
# LEADERBOARD ENDPOINTS
# ============================================================================

@app.get("/api/clients/leaderboard", response_model=Leaderboard)
async def get_leaderboard(
    authorization: Optional[str] = Header(None),
    metric: str = Query("win_rate", regex="^(win_rate|pnl|days_active|total_trades)$"),
    limit: int = Query(10, ge=1, le=100),
    days: int = Query(30, ge=1, le=365),
) -> Leaderboard:
    """
    Get top traders by metric: win_rate, pnl, days_active, or total_trades.
    Returns ranked leaderboard with top N entries.
    """
    await verify_auth(authorization)

    clients = client_db.get_all_clients()
    entries = []

    for client in clients:
        trades = client_db.get_client_trades(client["user_id"], days=days)
        if not trades:
            continue

        stats = client_db.calculate_stats(client["user_id"], trades)
        account_created = datetime.fromisoformat(client["account_created"])
        days_active = (datetime.now(timezone.utc) - account_created).days

        if metric == "win_rate":
            value = stats["win_rate"]
            secondary = stats["total_pnl"]
        elif metric == "pnl":
            value = stats["total_pnl"]
            secondary = stats["win_rate"]
        elif metric == "days_active":
            value = float(days_active)
            secondary = stats["total_trades"]
        else:  # total_trades
            value = float(stats["total_trades"])
            secondary = stats["total_pnl"]

        entries.append({
            "user_id": client["user_id"],
            "username": client.get("username"),
            "metric_value": round(value, 2),
            "secondary_value": round(secondary, 2) if secondary else None,
            "days_active": days_active,
            "account_age_days": days_active,
        })

    # Sort by metric value descending
    entries.sort(key=lambda x: x["metric_value"], reverse=True)

    # Add ranks
    for idx, entry in enumerate(entries[:limit], 1):
        entry["rank"] = idx

    return Leaderboard(
        metric=metric,
        entries=[LeaderboardEntry(**e) for e in entries[:limit]],
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


# ============================================================================
# UPSELL CANDIDATES
# ============================================================================

@app.get("/api/clients/upsell-candidates")
async def get_upsell_candidates(
    authorization: Optional[str] = Header(None),
    days: int = Query(30, ge=1, le=365),
) -> Dict[str, Any]:
    """
    Identify clients ready for premium tier upgrade.
    Criteria: consistent profitability, high trade count, strong win rate.
    Returns list of candidates with recommendation and urgency level.
    """
    await verify_auth(authorization)

    clients = client_db.get_all_clients()
    candidates = []

    for client in clients:
        # Only free/standard tier users
        if client.get("tier", "free") not in ("free", "standard"):
            continue

        trades = client_db.get_client_trades(client["user_id"], days=days)
        if len(trades) < 10:  # Minimum trade requirement
            continue

        stats = client_db.calculate_stats(client["user_id"], trades)
        account_created = datetime.fromisoformat(client["account_created"])
        days_active = (datetime.now(timezone.utc) - account_created).days

        # Scoring logic
        pnl_score = min(stats["total_pnl"] / 1000, 1.0) if stats["total_pnl"] > 0 else 0.0
        win_rate_score = min(stats["win_rate"] / 100, 1.0)
        trade_score = min(stats["total_trades"] / 100, 1.0)
        consistency_score = min(days_active / 30, 1.0)

        total_score = (pnl_score + win_rate_score + trade_score + consistency_score) / 4
        potential_value = stats["total_pnl"] * 2.5 if stats["total_pnl"] > 0 else 0.0

        # Urgency: high (>0.75), medium (0.5-0.75), low (<0.5)
        urgency = "high" if total_score > 0.75 else "medium" if total_score > 0.5 else "low"

        if total_score > 0.5:  # Only include qualifying candidates
            candidates.append(
                UpsellCandidate(
                    user_id=client["user_id"],
                    username=client.get("username"),
                    current_pnl=round(stats["total_pnl"], 2),
                    win_rate=round(stats["win_rate"], 2),
                    total_trades=stats["total_trades"],
                    days_active=days_active,
                    recommendation=f"Ready for premium: {stats['total_trades']} trades, {stats['win_rate']:.1f}% win rate",
                    potential_value=round(potential_value, 2),
                    urgency=urgency,
                )
            )

    # Sort by urgency and potential value
    urgency_order = {"high": 0, "medium": 1, "low": 2}
    candidates.sort(
        key=lambda x: (urgency_order[x.urgency], -x.potential_value if x.potential_value else 0)
    )

    return {
        "count": len(candidates),
        "candidates": candidates,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ============================================================================
# INDIVIDUAL TRADER PERFORMANCE
# ============================================================================

@app.get("/api/clients/{user_id}", response_model=TraderPerformance)
async def get_trader_performance(
    user_id: str,
    authorization: Optional[str] = Header(None),
    days: int = Query(30, ge=1, le=365),
) -> TraderPerformance:
    """
    Get individual trader's performance metrics.
    Returns: total/winning/losing trades, win rate, P&L, streaks, etc.
    """
    await verify_auth(authorization)

    if not client_db.client_exists(user_id):
        raise HTTPException(status_code=404, detail=f"Trader {user_id} not found")

    with client_db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clients WHERE user_id = ?", (user_id,))
        client = cursor.fetchone()

    if not client:
        raise HTTPException(status_code=404, detail=f"Trader {user_id} not found")

    trades = client_db.get_client_trades(user_id, days=days)
    stats = client_db.calculate_stats(user_id, trades)

    # Calculate streaks
    consecutive_wins = 0
    consecutive_losses = 0
    current_streak = "neutral"

    if trades:
        trades_sorted = sorted(trades, key=lambda x: x["entry_time"])
        for trade in reversed(trades_sorted):
            if trade["pnl"] > 0:
                consecutive_wins += 1
                consecutive_losses = 0
                current_streak = "winning"
                if consecutive_wins == 1:
                    break
            elif trade["pnl"] < 0:
                consecutive_losses += 1
                consecutive_wins = 0
                current_streak = "losing"
                if consecutive_losses == 1:
                    break

    account_created = datetime.fromisoformat(client["account_created"])
    days_active = (datetime.now(timezone.utc) - account_created).days
    last_trade = trades[0]["exit_time"] if trades else None

    return TraderPerformance(
        user_id=user_id,
        username=client.get("username"),
        total_trades=stats["total_trades"],
        winning_trades=stats["winning_trades"],
        losing_trades=stats["losing_trades"],
        win_rate=round(stats["win_rate"], 2),
        total_pnl=round(stats["total_pnl"], 2),
        avg_win=round(stats["avg_win"], 2),
        avg_loss=round(stats["avg_loss"], 2),
        largest_win=round(stats["largest_win"], 2),
        largest_loss=round(stats["largest_loss"], 2),
        consecutive_wins=consecutive_wins,
        consecutive_losses=consecutive_losses,
        days_active=days_active,
        account_created=client["account_created"],
        last_trade=last_trade,
        current_streak=current_streak,
        account_status=client["account_status"],
    )


# ============================================================================
# DAILY SUMMARY
# ============================================================================

@app.get("/api/clients/daily-summary", response_model=DailySummary)
async def get_daily_summary(
    authorization: Optional[str] = Header(None),
    limit: int = Query(50, ge=1, le=500),
) -> DailySummary:
    """
    Get today's trading activity summary.
    Returns: number of trades, P&L, symbols, win rate, active users, recent trades.
    """
    await verify_auth(authorization)

    trades = client_db.get_today_trades()
    if not trades:
        return DailySummary(
            date=datetime.now(timezone.utc).date().isoformat(),
            total_trades=0,
            trades_by_user={},
            total_pnl=0.0,
            pnl_by_user={},
            win_rate=0.0,
            active_users=0,
            recent_trades=[],
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    # Aggregate by user
    trades_by_user = {}
    pnl_by_user = {}
    symbols = {}

    for trade in trades:
        user_id = trade["user_id"]
        symbol = trade["symbol"]
        pnl = decode_pnl(trade["pnl"])

        trades_by_user[user_id] = trades_by_user.get(user_id, 0) + 1
        pnl_by_user[user_id] = round(pnl_by_user.get(user_id, 0.0) + pnl, 2)
        symbols[symbol] = symbols.get(symbol, 0) + 1

    # Calculate aggregate stats
    total_pnl = sum(decode_pnl(t["pnl"]) for t in trades)
    winning_trades = len([t for t in trades if decode_pnl(t["pnl"]) > 0])
    win_rate = (winning_trades / len(trades) * 100) if trades else 0.0
    top_symbol = max(symbols, key=symbols.get) if symbols else None

    # Format recent trades
    recent_trades_list = []
    for trade in trades[:limit]:
        recent_trades_list.append(
            DailyTrade(
                trade_id=trade["trade_id"],
                user_id=trade["user_id"],
                symbol=trade["symbol"],
                side=trade["side"],
                entry_price=float(trade["entry_price"]),
                exit_price=float(trade["exit_price"]) if trade["exit_price"] else None,
                shares=trade["shares"],
                pnl=round(decode_pnl(trade["pnl"]), 2),
                pnl_percent=float(trade["pnl_percent"]) if trade["pnl_percent"] else 0.0,
                entry_time=trade["entry_time"],
                exit_time=trade["exit_time"],
                status=trade.get("status", "closed"),
            )
        )

    return DailySummary(
        date=datetime.now(timezone.utc).date().isoformat(),
        total_trades=len(trades),
        trades_by_user=trades_by_user,
        total_pnl=round(total_pnl, 2),
        pnl_by_user=pnl_by_user,
        top_symbol=top_symbol,
        win_rate=round(win_rate, 2),
        active_users=len(trades_by_user),
        recent_trades=recent_trades_list,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


# ============================================================================
# INITIALIZATION
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
