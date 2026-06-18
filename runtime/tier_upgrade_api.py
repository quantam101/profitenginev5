"""
TIER UPGRADE API — REST endpoints for tier management and billing operations
Integrates with FastAPI for dashboard, admin, and customer APIs.

Endpoints:
  GET  /api/billing/subscription          - Get client's current subscription
  POST /api/billing/upgrade                - Manually trigger upgrade
  POST /api/billing/downgrade              - Manually trigger downgrade
  GET  /api/billing/history                - Get billing history
  GET  /api/billing/monthly-revenue        - Get revenue report
  POST /api/billing/retry-failed-charges   - Retry failed charges
  GET  /api/admin/tier-candidates          - Get current upgrade candidates (admin only)
"""

from __future__ import annotations

import os
import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from decimal import Decimal
from functools import wraps

from fastapi import FastAPI, HTTPException, Request, Header, Query, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from payment_processor import StripePaymentProcessor, BillingTier, ChargeStatus
from upsell_intelligence import UpsellScorer, generate_daily_upsell_report
from tier_upgrade_automation import TierUpgradeAutomation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================

API_KEY = os.environ.get("BILLING_API_KEY", "default-api-key")
ADMIN_API_KEY = os.environ.get("BILLING_ADMIN_API_KEY", "default-admin-key")
DB_PATH = os.environ.get("CLIENTS_DB_PATH", "clients.db")
BILLING_DB_PATH = os.environ.get("BILLING_DB_PATH", "clients.db")


# ============================================================================
# SCHEMAS
# ============================================================================

class SubscriptionInfo(BaseModel):
    """Client's current subscription status"""
    client_id: str
    username: str
    current_tier: str
    stripe_subscription_id: Optional[str] = None
    next_billing_date: Optional[str] = None
    monthly_charge_usd: float
    annual_charge_usd: float
    status: str


class BillingHistoryEntry(BaseModel):
    """Single billing history entry"""
    charge_id: str
    charge_type: str
    tier: str
    amount_usd: float
    tax_usd: float
    total_usd: float
    status: str
    created_at: str
    processed_at: Optional[str] = None
    failure_reason: Optional[str] = None


class UpgradeRequest(BaseModel):
    """Request to upgrade a client"""
    client_id: str
    target_tier: str = Field(..., description="Target tier: hybrid, white_label, enterprise")


class DowngradeRequest(BaseModel):
    """Request to downgrade a client"""
    client_id: str
    target_tier: str = Field(..., description="Target tier: free, hybrid, white_label")
    reason: Optional[str] = None


class RevenueReport(BaseModel):
    """Monthly revenue report"""
    period: str
    mrr_usd: float
    total_charges_usd: float
    total_tax_usd: float
    total_refunds_usd: float
    net_revenue_usd: float
    tier_breakdown: List[Dict[str, Any]]


class UpgradeCandidate(BaseModel):
    """Client ready for tier upgrade"""
    client_id: str
    username: str
    current_tier: str
    score: float
    eligible_tier: str
    estimated_monthly_charge_usd: float


# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="ProfitEngine Tier Upgrade API",
    description="Automated tier management and billing operations",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize processors
payment_processor = StripePaymentProcessor(BILLING_DB_PATH)
upsell_scorer = UpsellScorer(DB_PATH)


# ============================================================================
# AUTHENTICATION
# ============================================================================

def verify_api_key(api_key: str = Header(..., alias="X-API-Key")) -> str:
    """Verify API key"""
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key


def verify_admin_api_key(api_key: str = Header(..., alias="X-Admin-API-Key")) -> str:
    """Verify admin API key"""
    if api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid admin API key")
    return api_key


# ============================================================================
# CUSTOMER ENDPOINTS (authenticated with standard API key)
# ============================================================================

@app.get("/api/billing/subscription", response_model=SubscriptionInfo)
async def get_subscription(
    client_id: str = Query(...),
    api_key: str = Depends(verify_api_key),
) -> SubscriptionInfo:
    """
    Get client's current subscription status.

    Args:
        client_id: Client identifier

    Returns:
        SubscriptionInfo with tier, next billing date, charge amount
    """
    conn = sqlite3.connect(BILLING_DB_PATH)
    cursor = conn.cursor()

    try:
        # Get subscription info
        cursor.execute("""
            SELECT s.tier, s.stripe_subscription_id, s.next_billing_date, s.status,
                   c.username, c.account_balance
            FROM subscriptions s
            JOIN clients c ON s.client_id = c.client_id
            WHERE s.client_id = ? AND s.status = 'active'
        """, (client_id,))

        result = cursor.fetchone()
        if not result:
            # Client may be on free tier
            cursor.execute(
                "SELECT client_id, username FROM clients WHERE client_id = ?",
                (client_id,)
            )
            client_result = cursor.fetchone()
            if not client_result:
                raise HTTPException(status_code=404, detail="Client not found")

            return SubscriptionInfo(
                client_id=client_id,
                username=client_result[1],
                current_tier="free",
                status="active",
                monthly_charge_usd=0.0,
                annual_charge_usd=0.0,
                next_billing_date=None,
            )

        tier, stripe_sub_id, next_billing, status, username, account_balance = result

        # Calculate charges
        tier_info = payment_processor._get_tier_info(tier)
        monthly_charge = payment_processor._calculate_monthly_charge(
            Decimal(str(account_balance)), tier
        )
        annual_charge = monthly_charge * 12

        return SubscriptionInfo(
            client_id=client_id,
            username=username,
            current_tier=tier,
            stripe_subscription_id=stripe_sub_id,
            next_billing_date=str(next_billing) if next_billing else None,
            monthly_charge_usd=float(monthly_charge),
            annual_charge_usd=float(annual_charge),
            status=status,
        )

    finally:
        conn.close()


@app.get("/api/billing/history", response_model=List[BillingHistoryEntry])
async def get_billing_history(
    client_id: str = Query(...),
    limit: int = Query(100, ge=1, le=500),
    api_key: str = Depends(verify_api_key),
) -> List[BillingHistoryEntry]:
    """
    Get billing history for a client.

    Args:
        client_id: Client identifier
        limit: Number of entries to return (max 500)

    Returns:
        List of billing history entries
    """
    history = payment_processor.get_billing_history(
        client_id=client_id,
        limit=limit,
    )

    return [
        BillingHistoryEntry(
            charge_id=entry["charge_id"],
            charge_type=entry["charge_type"],
            tier=entry["tier"],
            amount_usd=entry["charge_amount_usd"],
            tax_usd=entry["tax_amount_usd"],
            total_usd=entry["total_amount_usd"],
            status=entry["status"],
            created_at=entry["created_at"],
            processed_at=entry.get("processed_at"),
            failure_reason=entry.get("failure_reason"),
        )
        for entry in history
    ]


@app.post("/api/billing/upgrade")
async def request_upgrade(
    request: UpgradeRequest,
    api_key: str = Depends(verify_api_key),
) -> Dict[str, Any]:
    """
    Request manual tier upgrade for a client.
    (Normally handled automatically by tier_upgrade_automation)

    Args:
        request: UpgradeRequest with client_id and target_tier

    Returns:
        Upgrade result with subscription ID, charge amount, next billing date
    """
    # Verify client exists and get details
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT client_id, username, account_balance FROM clients WHERE client_id = ?",
        (request.client_id,)
    )
    result = cursor.fetchone()
    conn.close()

    if not result:
        raise HTTPException(status_code=404, detail="Client not found")

    client_id, username, account_balance = result

    # Process upgrade
    upgrade_result = payment_processor.upgrade_client_tier(
        client_id=client_id,
        username=username,
        new_tier=request.target_tier,
        account_balance=Decimal(str(account_balance)),
    )

    if not upgrade_result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=upgrade_result.get("error", "Upgrade failed"),
        )

    return upgrade_result


@app.post("/api/billing/downgrade")
async def request_downgrade(
    request: DowngradeRequest,
    api_key: str = Depends(verify_api_key),
) -> Dict[str, Any]:
    """
    Request manual tier downgrade for a client.

    Args:
        request: DowngradeRequest with client_id and target_tier

    Returns:
        Downgrade result with refund amount (if applicable)
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT client_id, username, account_balance FROM clients WHERE client_id = ?",
        (request.client_id,)
    )
    result = cursor.fetchone()
    conn.close()

    if not result:
        raise HTTPException(status_code=404, detail="Client not found")

    client_id, username, account_balance = result

    # Process downgrade
    downgrade_result = payment_processor.downgrade_client_tier(
        client_id=client_id,
        new_tier=request.target_tier,
        account_balance=Decimal(str(account_balance)),
    )

    if not downgrade_result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=downgrade_result.get("error", "Downgrade failed"),
        )

    return downgrade_result


# ============================================================================
# ADMIN ENDPOINTS (authenticated with admin API key)
# ============================================================================

@app.get("/api/admin/tier-candidates", response_model=List[UpgradeCandidate])
async def get_upgrade_candidates(
    admin_key: str = Depends(verify_admin_api_key),
) -> List[UpgradeCandidate]:
    """
    Get current tier upgrade candidates (admin only).

    Returns:
        List of clients eligible for upgrades
    """
    report = generate_daily_upsell_report(DB_PATH)

    candidates = []

    # Enterprise
    for cand in report.get("enterprise_candidates", []):
        candidates.append(
            UpgradeCandidate(
                client_id=cand["client_id"],
                username=cand["username"],
                current_tier="free",  # Would need to fetch from DB
                score=cand["base_score"],
                eligible_tier="enterprise",
                estimated_monthly_charge_usd=cand["estimated_upsell_value_usd"] / 12,
            )
        )

    # White-Label
    for cand in report.get("white_label_candidates", []):
        candidates.append(
            UpgradeCandidate(
                client_id=cand["client_id"],
                username=cand["username"],
                current_tier="free",
                score=cand["base_score"],
                eligible_tier="white_label",
                estimated_monthly_charge_usd=cand["estimated_upsell_value_usd"] / 12,
            )
        )

    # Hybrid
    for cand in report.get("hybrid_candidates", []):
        candidates.append(
            UpgradeCandidate(
                client_id=cand["client_id"],
                username=cand["username"],
                current_tier="free",
                score=cand["base_score"],
                eligible_tier="hybrid",
                estimated_monthly_charge_usd=cand["estimated_upsell_value_usd"] / 12,
            )
        )

    return sorted(candidates, key=lambda x: x.score, reverse=True)


@app.get("/api/admin/revenue-report", response_model=RevenueReport)
async def get_revenue_report(
    year_month: Optional[str] = Query(None, description="Format: YYYY-MM"),
    admin_key: str = Depends(verify_admin_api_key),
) -> RevenueReport:
    """
    Get monthly revenue report (admin only).

    Args:
        year_month: Format "YYYY-MM" (defaults to current month)

    Returns:
        RevenueReport with MRR, charges, refunds, tier breakdown
    """
    report = payment_processor.generate_revenue_report(year_month)
    return RevenueReport(**report)


@app.post("/api/admin/run-upgrade-cycle")
async def run_upgrade_cycle(
    admin_key: str = Depends(verify_admin_api_key),
) -> Dict[str, Any]:
    """
    Manually trigger tier upgrade/downgrade cycle (admin only).
    Normally runs daily automatically via cron.

    Returns:
        Cycle results with upgrades, downgrades, failures
    """
    engine = TierUpgradeAutomation(DB_PATH, BILLING_DB_PATH)
    results = engine.run_daily_upgrade_cycle()
    return results


@app.post("/api/admin/retry-failed-charges")
async def retry_failed_charges(
    admin_key: str = Depends(verify_admin_api_key),
) -> Dict[str, Any]:
    """
    Retry all failed charges (admin only).
    Normally runs periodically via cron.

    Returns:
        Retry results with successes and failures
    """
    results = payment_processor.retry_failed_charges()
    return results


@app.post("/api/admin/process-monthly-charges")
async def process_monthly_charges(
    admin_key: str = Depends(verify_admin_api_key),
) -> Dict[str, Any]:
    """
    Process monthly tier charges for all active subscriptions (admin only).
    Normally runs daily via cron.

    Returns:
        Processing results with charges attempted, successful, failed
    """
    results = payment_processor.process_monthly_charges()
    return results


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "tier-upgrade-api",
        "timestamp": datetime.utcnow().isoformat(),
    }


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    print("=" * 80)
    print("TIER UPGRADE API — FastAPI Server")
    print("=" * 80)
    print("\nStarting server on http://localhost:8000")
    print("\nAPI Endpoints:")
    print("  GET  /api/billing/subscription         - Get subscription info")
    print("  GET  /api/billing/history              - Get billing history")
    print("  POST /api/billing/upgrade              - Request upgrade")
    print("  POST /api/billing/downgrade            - Request downgrade")
    print("  GET  /api/admin/tier-candidates        - Get upgrade candidates (admin)")
    print("  GET  /api/admin/revenue-report         - Get revenue report (admin)")
    print("  POST /api/admin/run-upgrade-cycle      - Run upgrade cycle (admin)")
    print("  POST /api/admin/retry-failed-charges   - Retry failed charges (admin)")
    print("  POST /api/admin/process-monthly-charges - Process monthly charges (admin)")
    print("\nDocs: http://localhost:8000/docs")
    print("=" * 80)

    uvicorn.run(
        "tier_upgrade_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
