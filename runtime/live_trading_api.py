"""
LIVE TRADING API ENDPOINTS
FastAPI endpoints for live trading control, monitoring, and user-facing operations
Integrate into main runtime/api.py FastAPI app
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from runtime.live_trading_trigger import LiveTradingTrigger
from runtime.live_trading_safety import CircuitBreaker, ManualOverride
from runtime.live_trading_state import get_live_trading_stats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/live-trading", tags=["live-trading"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class DeploymentConfirmRequest(BaseModel):
    """User confirmation of live trading deployment"""
    user_id: int = Field(..., gt=0)
    approval_code: str = Field(..., min_length=6, max_length=8)
    two_fa_token: Optional[str] = None


class AdminActionRequest(BaseModel):
    """Admin override action"""
    user_id: int = Field(..., gt=0)
    reason: str = Field(..., min_length=5, max_length=200)


class RollbackRequest(BaseModel):
    """Rollback to paper trading"""
    user_id: int = Field(..., gt=0)
    reason: str = Field(default="User requested", max_length=200)


class LiveTradingStatusResponse(BaseModel):
    """Live account status"""
    user_id: int
    email: str
    status: str  # active, paused, closed
    deployment_amount: Decimal
    current_balance: Decimal
    daily_pnl: Decimal
    drawdown_pct: Decimal
    circuit_state: str  # green, yellow, red
    positions_count: int
    last_trade_time: Optional[str]


class DeploymentStatusResponse(BaseModel):
    """Deployment request status"""
    deployment_id: int
    user_id: int
    status: str
    paper_balance: Decimal
    deployment_amount: Decimal
    max_daily_loss: Decimal
    expires_at: str
    created_at: str


class LiveTradingHealthResponse(BaseModel):
    """System health status"""
    status: str  # healthy, degraded, error
    active_accounts: int
    total_live_capital: Decimal
    red_state_count: int
    yellow_state_count: int
    robinhood_connected: bool
    recent_errors: list


# ============================================================================
# DEPENDENCY: USER AUTHENTICATION
# ============================================================================

async def get_current_user(user_id: int = Query(..., gt=0)):
    """
    Extract and validate user from query param or JWT token.
    TODO: Integrate with actual auth system.
    """
    # Placeholder: in production, extract from JWT token or session
    if user_id < 1:
        raise HTTPException(status_code=401, detail="Invalid user")
    return {"user_id": user_id}


async def get_admin_user(user_id: int = Query(..., gt=0)):
    """Verify user is admin"""
    # Placeholder: check if user has admin role
    admin_emails = ["admin@alreadyherellc.com", "dispatch@alreadyherellc.com"]
    # TODO: Check actual user role
    return {"user_id": user_id, "is_admin": True}


# ============================================================================
# ENDPOINTS: USER-FACING
# ============================================================================

@router.post("/confirm", response_model=dict)
async def confirm_deployment(
    request: DeploymentConfirmRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    User confirms live trading deployment via approval code.

    Args:
        user_id: User ID
        approval_code: 6-digit code from email
        two_fa_token: Optional 2FA code

    Returns:
        { "success": bool, "message": str }
    """
    if request.user_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Cannot confirm for other user")

    trigger = LiveTradingTrigger()

    try:
        success, message = await trigger.confirm_deployment(
            user_id=request.user_id,
            approval_code=request.approval_code,
            two_fa_token=request.two_fa_token
        )

        if not success:
            raise HTTPException(status_code=400, detail=message)

        logger.info(f"Deployment confirmed for user {request.user_id}")
        return {"success": True, "message": message}

    except Exception as e:
        logger.error(f"Deployment confirmation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{user_id}", response_model=Optional[LiveTradingStatusResponse])
async def get_live_status(user_id: int, current_user: dict = Depends(get_current_user)):
    """Get live trading account status for a user"""
    if user_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Cannot view other user's account")

    # TODO: Query live_accounts, circuit_breakers, live_daily_pnl tables
    # and return comprehensive status
    pass


@router.get("/deployment/{user_id}", response_model=Optional[DeploymentStatusResponse])
async def get_deployment_status(user_id: int, current_user: dict = Depends(get_current_user)):
    """Get deployment request status"""
    if user_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Cannot view other user's deployment")

    # TODO: Query deployments and deployment_approvals tables
    pass


@router.post("/rollback")
async def request_rollback(
    request: RollbackRequest,
    current_user: dict = Depends(get_current_user)
):
    """User requests rollback from live to paper trading"""
    if request.user_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Cannot rollback for other user")

    trigger = LiveTradingTrigger()

    try:
        success = await trigger.rollback_to_paper(
            user_id=request.user_id,
            reason=request.reason
        )

        if not success:
            raise HTTPException(status_code=400, detail="Rollback failed")

        return {"success": True, "message": "Account rolled back to paper trading"}

    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS: ADMIN-ONLY
# ============================================================================

@router.post("/admin/pause/{user_id}")
async def admin_pause(
    user_id: int,
    request: AdminActionRequest,
    admin_user: dict = Depends(get_admin_user)
):
    """Admin pause live trading for user"""
    if not admin_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin only")

    trigger = LiveTradingTrigger()

    try:
        success = await trigger.pause_live_trading(
            user_id=user_id,
            reason=request.reason
        )

        if not success:
            raise HTTPException(status_code=400, detail="Pause failed")

        logger.warning(f"Admin {admin_user['user_id']} paused user {user_id}: {request.reason}")
        return {"success": True, "message": f"Paused user {user_id}"}

    except Exception as e:
        logger.error(f"Admin pause failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/resume/{user_id}")
async def admin_resume(
    user_id: int,
    admin_user: dict = Depends(get_admin_user)
):
    """Admin resume live trading for user"""
    if not admin_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin only")

    trigger = LiveTradingTrigger()

    try:
        success = await trigger.resume_live_trading(user_id=user_id)

        if not success:
            raise HTTPException(status_code=400, detail="Resume failed")

        logger.warning(f"Admin {admin_user['user_id']} resumed user {user_id}")
        return {"success": True, "message": f"Resumed user {user_id}"}

    except Exception as e:
        logger.error(f"Admin resume failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/rollback/{user_id}")
async def admin_rollback(
    user_id: int,
    request: RollbackRequest,
    admin_user: dict = Depends(get_admin_user)
):
    """Admin force rollback for user"""
    if not admin_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin only")

    trigger = LiveTradingTrigger()

    try:
        success = await trigger.rollback_to_paper(
            user_id=user_id,
            reason=f"ADMIN: {request.reason}"
        )

        if not success:
            raise HTTPException(status_code=400, detail="Rollback failed")

        logger.warning(f"Admin {admin_user['user_id']} rolled back user {user_id}: {request.reason}")
        return {"success": True, "message": f"Rolled back user {user_id}"}

    except Exception as e:
        logger.error(f"Admin rollback failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/active-accounts")
async def admin_get_active_accounts(admin_user: dict = Depends(get_admin_user)):
    """Admin view all active live accounts"""
    if not admin_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin only")

    # TODO: Query all active live_accounts with users, circuit_breaker states
    pass


@router.get("/admin/deployments")
async def admin_get_deployments(
    status: Optional[str] = Query(None),
    admin_user: dict = Depends(get_admin_user)
):
    """Admin view all deployments (optionally filtered by status)"""
    if not admin_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin only")

    # TODO: Query deployments table
    pass


@router.get("/admin/audit-log/{user_id}")
async def admin_get_audit_log(
    user_id: int,
    admin_user: dict = Depends(get_admin_user)
):
    """Admin view audit trail for user"""
    if not admin_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin only")

    # TODO: Query deployment_events and admin_actions tables
    pass


# ============================================================================
# ENDPOINTS: MONITORING & HEALTH
# ============================================================================

@router.get("/health", response_model=LiveTradingHealthResponse)
async def health_check():
    """System health check"""
    try:
        stats = get_live_trading_stats()

        return {
            "status": "healthy",
            "active_accounts": stats.get("live_accounts_by_status", {}).get("active", 0),
            "total_live_capital": Decimal(str(stats.get("total_live_capital", 0))),
            "red_state_count": 0,  # TODO: Count from circuit_breakers
            "yellow_state_count": 0,  # TODO: Count from circuit_breakers
            "robinhood_connected": True,  # TODO: Test connection
            "recent_errors": []
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


@router.get("/stats")
async def get_stats(admin_user: dict = Depends(get_admin_user)):
    """Get live trading system statistics"""
    if not admin_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin only")

    try:
        stats = get_live_trading_stats()
        return stats
    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS: DEBUGGING (DEV ONLY)
# ============================================================================

@router.post("/debug/trigger-check")
async def debug_trigger_check(admin_user: dict = Depends(get_admin_user)):
    """Manually trigger a single check cycle (admin/dev only)"""
    if not admin_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin only")

    trigger = LiveTradingTrigger()

    try:
        await trigger.check_paper_trades_once()
        return {"success": True, "message": "Check cycle completed"}
    except Exception as e:
        logger.error(f"Manual check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/debug/send-test-email")
async def debug_send_test_email(
    email: str = Query(...),
    admin_user: dict = Depends(get_admin_user)
):
    """Send test email (admin/dev only)"""
    if not admin_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin only")

    from runtime.gmail_client import send_email

    try:
        success = send_email(
            subject="ProfitEngine Test Email",
            body_html="<p>This is a test email from live trading system.</p>",
            to=email
        )

        if not success:
            raise HTTPException(status_code=400, detail="Email send failed")

        return {"success": True, "message": f"Test email sent to {email}"}

    except Exception as e:
        logger.error(f"Test email failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # Example: Integrate into main FastAPI app
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)

    # Run: uvicorn runtime.live_trading_api:app --reload
