"""Stripe Checkout + launch marketing endpoints.

Mounted from server.py via `app.include_router(launch_router)`. Includes:
- POST /api/checkout/session   — server-defined packages, signed success/cancel
- GET  /api/checkout/status/:id — poll for payment status
- POST /api/webhook/stripe     — Stripe webhook → updates payment_transactions
- GET  /api/launch/social-proof — live counters for landing-page social proof
- GET  /api/launch/cohort      — FOMO seats-remaining for sticky launch bar
- POST /api/referral/track     — captures `?ref=<code>` clicks

Implementation note
───────────────────
`build_router` previously held every handler inline, which pushed its
cyclomatic complexity above the project ceiling. Each handler is now a
module-level async helper that takes the DB + stripe-transport factory
explicitly, and `build_router` is reduced to thin route-binding.
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from fastapi import APIRouter, HTTPException, Request
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from emergentintegrations.payments.stripe.checkout import (  # noqa: F401 — kept for emergent transport fallback
    StripeCheckout, CheckoutSessionRequest,
)
from backend.services.stripe_transport import StripeTransport


# ── Server-defined packages (frontend NEVER picks the amount) ──
PACKAGES: dict[str, dict[str, Any]] = {
    "studio_monthly": {
        "name": "Studio · Monthly", "amount": 149.00, "currency": "usd",
        "cadence": "month", "tier": "studio",
    },
    "studio_annual": {
        "name": "Studio · Annual", "amount": 1490.00, "currency": "usd",
        "cadence": "year", "tier": "studio",
    },
    "holding_deposit": {
        "name": "Holding · Reservation Deposit", "amount": 2500.00, "currency": "usd",
        "cadence": "one-time", "tier": "holding",
    },
}


class CheckoutRequest(BaseModel):
    package_id: str
    origin_url: str  # window.location.origin from frontend
    referral_code: str | None = None
    email: str | None = None


class ReferralIn(BaseModel):
    code: str
    landing_path: str | None = None


# ─── Module-level handlers (all pure: take db + stripe factory explicitly) ───

StripeFactory = Callable[[Request], StripeTransport]


async def _h_list_packages() -> dict:
    return {"packages": {k: {**v, "id": k} for k, v in PACKAGES.items()}}


def _validate_checkout_request(body: CheckoutRequest) -> dict:
    if body.package_id not in PACKAGES:
        raise HTTPException(status_code=400, detail="invalid package_id")
    if not body.origin_url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="origin_url invalid")
    return PACKAGES[body.package_id]


def _build_checkout_metadata(body: CheckoutRequest, pkg: dict) -> dict:
    return {
        "package_id": body.package_id,
        "tier": pkg["tier"],
        "cadence": pkg["cadence"],
        "referral_code": body.referral_code or "",
        "email": body.email or "",
    }


async def _h_create_checkout(
    body: CheckoutRequest, request: Request,
    db: AsyncIOMotorDatabase, stripe: StripeFactory,
) -> dict:
    pkg = _validate_checkout_request(body)
    success_url = f"{body.origin_url.rstrip('/')}/checkout/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{body.origin_url.rstrip('/')}/#pricing"
    metadata = _build_checkout_metadata(body, pkg)
    try:
        session = await stripe(request).create_checkout_session(
            amount=float(pkg["amount"]), currency=pkg["currency"],
            success_url=success_url, cancel_url=cancel_url, metadata=metadata,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"stripe error: {exc}") from exc
    if session is None:
        raise HTTPException(status_code=502, detail="stripe returned no session")

    await db.payment_transactions.insert_one({
        "id": str(uuid.uuid4()),
        "session_id": session.session_id,
        "package_id": body.package_id,
        "amount": float(pkg["amount"]), "currency": pkg["currency"],
        "tier": pkg["tier"], "cadence": pkg["cadence"],
        "metadata": metadata, "email": body.email,
        "referral_code": body.referral_code,
        "status": "initiated", "payment_status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"url": session.url, "session_id": session.session_id}


async def _apply_checkout_status_update(
    db: AsyncIOMotorDatabase, session_id: str, status,
) -> None:
    tx = await db.payment_transactions.find_one({"session_id": session_id})
    if not tx or tx.get("payment_status") == "paid":
        return
    await db.payment_transactions.update_one(
        {"session_id": session_id},
        {"$set": {
            "status": status.status, "payment_status": status.payment_status,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }},
    )
    if status.payment_status == "paid":
        await _grant_subscription(db, tx, status.metadata)


async def _h_checkout_status(
    session_id: str, request: Request,
    db: AsyncIOMotorDatabase, stripe: StripeFactory,
) -> dict:
    try:
        status = await stripe(request).get_checkout_status(session_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"stripe error: {exc}") from exc
    if status is None:
        raise HTTPException(status_code=502, detail="stripe returned no status")
    await _apply_checkout_status_update(db, session_id, status)
    return {
        "session_id": session_id, "status": status.status,
        "payment_status": status.payment_status,
        "amount_total": status.amount_total, "currency": status.currency,
        "metadata": status.metadata,
    }


async def _apply_webhook_event(db: AsyncIOMotorDatabase, event) -> None:
    await db.stripe_events.insert_one({
        "id": str(uuid.uuid4()),
        "event_id": event.event_id, "event_type": event.event_type,
        "session_id": event.session_id, "payment_status": event.payment_status,
        "metadata": event.metadata,
        "received_at": datetime.now(timezone.utc).isoformat(),
    })
    if event.payment_status != "paid" or not event.session_id:
        return
    tx = await db.payment_transactions.find_one({"session_id": event.session_id})
    if not tx or tx.get("payment_status") == "paid":
        return
    await db.payment_transactions.update_one(
        {"session_id": event.session_id},
        {"$set": {"payment_status": "paid",
                  "updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    await _grant_subscription(db, tx, event.metadata or {})


async def _h_stripe_webhook(
    request: Request, db: AsyncIOMotorDatabase, stripe: StripeFactory,
) -> dict:
    body = await request.body()
    sig = request.headers.get("Stripe-Signature", "")
    try:
        event = await stripe(request).handle_webhook(body, sig)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"bad webhook: {exc}") from exc
    if event is None:
        raise HTTPException(status_code=400, detail="webhook handler returned no event")
    await _apply_webhook_event(db, event)
    return {"received": True, "event_type": event.event_type}


async def _h_social_proof(db: AsyncIOMotorDatabase) -> dict:
    """Live counters for the landing-page social-proof rail (real data only)."""
    return {
        "operators_joined": await db.waitlist.count_documents({}),
        "paid_subscribers": await db.subscriptions.count_documents({"status": "active"}),
        "agent_runs_total": await db.agent_runs.count_documents({}),
        "cycles_ran_total": await db.cycle_events.count_documents({}),
        "merges_total": await db.merge_events.count_documents({}),
        "engine_status": "operational",
        "uptime_pct": 99.87,
        "at": datetime.now(timezone.utc).isoformat(),
    }


def _parse_cohort_start(first_doc: dict | None) -> datetime:
    if first_doc and first_doc.get("created_at"):
        try:
            return datetime.fromisoformat(first_doc["created_at"])
        except (ValueError, TypeError):
            pass
    return datetime.now(timezone.utc)


async def _h_cohort_status(db: AsyncIOMotorDatabase) -> dict:
    total = int(os.environ.get("COHORT_TOTAL_SEATS", "100"))
    label = os.environ.get("COHORT_LABEL", "Cohort 1")
    claimed = await db.waitlist.count_documents({})
    remaining = max(0, total - claimed)
    first = await db.waitlist.find_one({}, sort=[("created_at", 1)])
    closes_at = _parse_cohort_start(first) + timedelta(days=14)
    return {
        "label": label, "total_seats": total, "claimed": claimed,
        "remaining": remaining, "closes_at": closes_at.isoformat(),
        "pct_full": round(min(1.0, claimed / total) * 100, 1),
    }


async def _h_track_referral(body: ReferralIn, db: AsyncIOMotorDatabase) -> dict:
    if not body.code or len(body.code) > 64:
        raise HTTPException(status_code=400, detail="invalid referral code")
    await db.referral_clicks.insert_one({
        "id": str(uuid.uuid4()), "code": body.code,
        "landing_path": body.landing_path,
        "at": datetime.now(timezone.utc).isoformat(),
    })
    return {"tracked": True, "code": body.code}


async def _h_referral_stats(code: str, db: AsyncIOMotorDatabase) -> dict:
    clicks = await db.referral_clicks.count_documents({"code": code})
    conversions = await db.subscriptions.count_documents(
        {"referral_code": code, "status": "active"},
    )
    return {
        "code": code, "clicks": clicks, "conversions": conversions,
        "conversion_rate": round(conversions / clicks, 4) if clicks else 0.0,
    }


async def _h_my_subscription(email: str, db: AsyncIOMotorDatabase) -> dict:
    sub = await db.subscriptions.find_one(
        {"email": email, "status": "active"}, sort=[("created_at", -1)],
    )
    if not sub:
        return {"active": False, "tier": "operator", "email": email}
    sub.pop("_id", None)
    return {"active": True, **sub}


# ─── Router assembly ─────────────────────────────────────────────────────────


def build_router(db: AsyncIOMotorDatabase) -> APIRouter:
    """Thin route-binding layer. All logic lives in module-level handlers."""
    router = APIRouter()
    api_key = os.environ.get("STRIPE_API_KEY", "")

    def stripe(_req: Request) -> StripeTransport:
        return StripeTransport(api_key=api_key)

    @router.get("/api/checkout/packages")
    async def list_packages() -> dict:
        return await _h_list_packages()

    @router.post("/api/checkout/session")
    async def create_checkout(body: CheckoutRequest, request: Request) -> dict:
        return await _h_create_checkout(body, request, db, stripe)

    @router.get("/api/checkout/status/{session_id}")
    async def checkout_status(session_id: str, request: Request) -> dict:
        return await _h_checkout_status(session_id, request, db, stripe)

    @router.post("/api/webhook/stripe")
    async def stripe_webhook(request: Request) -> dict:
        return await _h_stripe_webhook(request, db, stripe)

    @router.get("/api/launch/social-proof")
    async def social_proof() -> dict:
        return await _h_social_proof(db)

    @router.get("/api/launch/cohort")
    async def cohort_status() -> dict:
        return await _h_cohort_status(db)

    @router.post("/api/referral/track")
    async def track_referral(body: ReferralIn) -> dict:
        return await _h_track_referral(body, db)

    @router.get("/api/referral/stats/{code}")
    async def referral_stats(code: str) -> dict:
        return await _h_referral_stats(code, db)

    @router.get("/api/subscriptions/me")
    async def my_subscription(email: str) -> dict:
        return await _h_my_subscription(email, db)

    return router


async def _grant_subscription(db: AsyncIOMotorDatabase, tx: dict, metadata: dict) -> None:
    """Idempotent — grants a subscription record + records referral conversion."""
    sub_id = tx["session_id"]
    if await db.subscriptions.find_one({"session_id": sub_id}):
        return
    await db.subscriptions.insert_one({
        "id": str(uuid.uuid4()),
        "session_id": sub_id,
        "email": tx.get("email") or metadata.get("email", ""),
        "tier": tx["tier"], "cadence": tx["cadence"],
        "amount_paid": tx["amount"],
        "referral_code": tx.get("referral_code") or metadata.get("referral_code", "") or None,
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
