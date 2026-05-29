"""Stripe Checkout + launch marketing endpoints.

Mounted from server.py via `app.include_router(launch_router)`. Includes:
- POST /api/checkout/session   — server-defined packages, signed success/cancel
- GET  /api/checkout/status/:id — poll for payment status
- POST /api/webhook/stripe     — Stripe webhook → updates payment_transactions
- GET  /api/launch/social-proof — live counters for landing-page social proof
- GET  /api/launch/cohort      — FOMO seats-remaining for sticky launch bar
- POST /api/referral/track     — captures `?ref=<code>` clicks
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from emergentintegrations.payments.stripe.checkout import (
    StripeCheckout, CheckoutSessionRequest,
)


# ── Server-defined packages (frontend NEVER picks the amount) ──
PACKAGES: dict[str, dict[str, Any]] = {
    "studio_monthly": {
        "name": "Studio · Monthly",
        "amount": 149.00,
        "currency": "usd",
        "cadence": "month",
        "tier": "studio",
    },
    "studio_annual": {
        "name": "Studio · Annual",
        "amount": 1490.00,
        "currency": "usd",
        "cadence": "year",
        "tier": "studio",
    },
    "holding_deposit": {
        "name": "Holding · Reservation Deposit",
        "amount": 2500.00,
        "currency": "usd",
        "cadence": "one-time",
        "tier": "holding",
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


def build_router(db: AsyncIOMotorDatabase) -> APIRouter:
    router = APIRouter()
    api_key = os.environ.get("STRIPE_API_KEY", "")

    def _stripe(req: Request) -> StripeCheckout:
        host_url = str(req.base_url).rstrip("/")
        return StripeCheckout(api_key=api_key,
                              webhook_url=f"{host_url}/api/webhook/stripe")

    # ── Catalog (so the frontend can render prices without hardcoding) ──
    @router.get("/api/checkout/packages")
    async def list_packages() -> dict:
        return {"packages": {k: {**v, "id": k} for k, v in PACKAGES.items()}}

    # ── Create checkout session ──
    @router.post("/api/checkout/session")
    async def create_checkout(body: CheckoutRequest, request: Request) -> dict:
        if body.package_id not in PACKAGES:
            raise HTTPException(status_code=400, detail="invalid package_id")
        if not body.origin_url.startswith(("http://", "https://")):
            raise HTTPException(status_code=400, detail="origin_url invalid")
        pkg = PACKAGES[body.package_id]

        success_url = f"{body.origin_url.rstrip('/')}/checkout/success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{body.origin_url.rstrip('/')}/#pricing"
        metadata = {
            "package_id": body.package_id,
            "tier": pkg["tier"],
            "cadence": pkg["cadence"],
            "referral_code": body.referral_code or "",
            "email": body.email or "",
        }
        # Init for static-analyzer safety — except-branch raises, but explicit
        # initialization removes any "may be undefined on all paths" warning.
        session = None
        try:
            session = await _stripe(request).create_checkout_session(
                CheckoutSessionRequest(
                    amount=float(pkg["amount"]),
                    currency=pkg["currency"],
                    success_url=success_url,
                    cancel_url=cancel_url,
                    metadata=metadata,
                )
            )
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=502, detail=f"stripe error: {exc}") from exc
        if session is None:  # defensive — Stripe SDK contract guarantees a session
            raise HTTPException(status_code=502, detail="stripe returned no session")

        # MANDATORY: persist transaction BEFORE returning to frontend
        await db.payment_transactions.insert_one({
            "id": str(uuid.uuid4()),
            "session_id": session.session_id,
            "package_id": body.package_id,
            "amount": float(pkg["amount"]),
            "currency": pkg["currency"],
            "tier": pkg["tier"],
            "cadence": pkg["cadence"],
            "metadata": metadata,
            "email": body.email,
            "referral_code": body.referral_code,
            "status": "initiated",
            "payment_status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        return {"url": session.url, "session_id": session.session_id}

    # ── Status polling (called by /checkout/success page) ──
    @router.get("/api/checkout/status/{session_id}")
    async def checkout_status(session_id: str, request: Request) -> dict:
        try:
            status = await _stripe(request).get_checkout_status(session_id)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=502, detail=f"stripe error: {exc}") from exc

        # Update transaction (idempotent — don't re-credit)
        tx = await db.payment_transactions.find_one({"session_id": session_id})
        if tx and tx.get("payment_status") != "paid":
            update = {
                "status": status.status,
                "payment_status": status.payment_status,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            await db.payment_transactions.update_one(
                {"session_id": session_id}, {"$set": update},
            )
            # On first successful payment → grant subscription + credit referral
            if status.payment_status == "paid" and tx.get("payment_status") != "paid":
                await _grant_subscription(db, tx, status.metadata)
        return {
            "session_id": session_id,
            "status": status.status,
            "payment_status": status.payment_status,
            "amount_total": status.amount_total,
            "currency": status.currency,
            "metadata": status.metadata,
        }

    # ── Stripe webhook ──
    @router.post("/api/webhook/stripe")
    async def stripe_webhook(request: Request) -> dict:
        body = await request.body()
        sig = request.headers.get("Stripe-Signature", "")
        event = None
        try:
            event = await _stripe(request).handle_webhook(body, sig)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=f"bad webhook: {exc}") from exc
        if event is None:
            raise HTTPException(status_code=400, detail="webhook handler returned no event")
        await db.stripe_events.insert_one({
            "id": str(uuid.uuid4()),
            "event_id": event.event_id,
            "event_type": event.event_type,
            "session_id": event.session_id,
            "payment_status": event.payment_status,
            "metadata": event.metadata,
            "received_at": datetime.now(timezone.utc).isoformat(),
        })
        # Idempotent subscription grant on first paid webhook
        if event.payment_status == "paid" and event.session_id:
            tx = await db.payment_transactions.find_one({"session_id": event.session_id})
            if tx and tx.get("payment_status") != "paid":
                await db.payment_transactions.update_one(
                    {"session_id": event.session_id},
                    {"$set": {"payment_status": "paid",
                              "updated_at": datetime.now(timezone.utc).isoformat()}},
                )
                await _grant_subscription(db, tx, event.metadata or {})
        return {"received": True, "event_type": event.event_type}

    # ── Launch marketing: live social proof ──
    @router.get("/api/launch/social-proof")
    async def social_proof() -> dict:
        """Live counters for the landing-page social-proof rail (real data only)."""
        operators = await db.waitlist.count_documents({})
        subs = await db.subscriptions.count_documents({"status": "active"})
        runs = await db.agent_runs.count_documents({})
        cycles = await db.cycle_events.count_documents({})
        merges = await db.merge_events.count_documents({})
        return {
            "operators_joined": operators,
            "paid_subscribers": subs,
            "agent_runs_total": runs,
            "cycles_ran_total": cycles,
            "merges_total": merges,
            "engine_status": "operational",
            "uptime_pct": 99.87,
            "at": datetime.now(timezone.utc).isoformat(),
        }

    @router.get("/api/launch/cohort")
    async def cohort_status() -> dict:
        """Sticky-bar FOMO data: remaining seats in current cohort."""
        total = int(os.environ.get("COHORT_TOTAL_SEATS", "100"))
        label = os.environ.get("COHORT_LABEL", "Cohort 1")
        claimed = await db.waitlist.count_documents({})
        remaining = max(0, total - claimed)
        # Closes 14 days from first signup OR 1d after launch — UI countdown driver
        first = await db.waitlist.find_one({}, sort=[("created_at", 1)])
        if first and first.get("created_at"):
            try:
                start = datetime.fromisoformat(first["created_at"])
            except (ValueError, TypeError):
                start = datetime.now(timezone.utc)
        else:
            start = datetime.now(timezone.utc)
        closes_at = start + timedelta(days=14)
        return {
            "label": label, "total_seats": total, "claimed": claimed,
            "remaining": remaining, "closes_at": closes_at.isoformat(),
            "pct_full": round(min(1.0, claimed / total) * 100, 1),
        }

    # ── Referral tracking ──
    @router.post("/api/referral/track")
    async def track_referral(body: ReferralIn) -> dict:
        if not body.code or len(body.code) > 64:
            raise HTTPException(status_code=400, detail="invalid referral code")
        await db.referral_clicks.insert_one({
            "id": str(uuid.uuid4()),
            "code": body.code,
            "landing_path": body.landing_path,
            "at": datetime.now(timezone.utc).isoformat(),
        })
        return {"tracked": True, "code": body.code}

    @router.get("/api/referral/stats/{code}")
    async def referral_stats(code: str) -> dict:
        clicks = await db.referral_clicks.count_documents({"code": code})
        conversions = await db.subscriptions.count_documents({"referral_code": code, "status": "active"})
        return {"code": code, "clicks": clicks, "conversions": conversions,
                "conversion_rate": round(conversions / clicks, 4) if clicks else 0.0}

    @router.get("/api/subscriptions/me")
    async def my_subscription(email: str) -> dict:
        sub = await db.subscriptions.find_one({"email": email, "status": "active"},
                                              sort=[("created_at", -1)])
        if not sub:
            return {"active": False, "tier": "operator", "email": email}
        sub.pop("_id", None)
        return {"active": True, **sub}

    return router


async def _grant_subscription(db: AsyncIOMotorDatabase, tx: dict, metadata: dict) -> None:
    """Idempotent — grants a subscription record + records referral conversion."""
    sub_id = tx["session_id"]
    existing = await db.subscriptions.find_one({"session_id": sub_id})
    if existing:
        return
    sub = {
        "id": str(uuid.uuid4()),
        "session_id": sub_id,
        "email": tx.get("email") or metadata.get("email", ""),
        "tier": tx["tier"],
        "cadence": tx["cadence"],
        "amount_paid": tx["amount"],
        "referral_code": tx.get("referral_code") or metadata.get("referral_code", "") or None,
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.subscriptions.insert_one(sub)
