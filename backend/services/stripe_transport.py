"""Stripe transport — native `stripe` SDK only.

Uses the official stripe Python SDK for all operations.
Works anywhere: Vercel, OCI, local dev.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class CheckoutSession:
    url: str
    session_id: str


@dataclass
class CheckoutStatus:
    status: str            # "open" | "complete" | "expired"
    payment_status: str    # "paid" | "unpaid" | "no_payment_required"
    amount_total: int | None  # cents
    currency: str | None
    metadata: dict


@dataclass
class WebhookEvent:
    event_id: str
    event_type: str
    session_id: str | None
    payment_status: str | None
    metadata: dict


class StripeTransport:
    """Thin async wrapper around the official stripe SDK.
    Stripe's SDK is sync-only; all calls run via asyncio.to_thread."""

    def __init__(self, api_key: str, *, webhook_secret: str | None = None) -> None:
        self.api_key = api_key
        self.webhook_secret = webhook_secret or os.environ.get("STRIPE_WEBHOOK_SECRET")

    # ── Create checkout session ──────────────────────────────────────────────
    async def create_checkout_session(self, *, amount: float, currency: str,
                                      success_url: str, cancel_url: str,
                                      metadata: dict) -> CheckoutSession:
        import asyncio
        import stripe
        stripe.api_key = self.api_key
        unit_amount = int(round(amount * 100))  # dollars → cents
        session = await asyncio.to_thread(
            stripe.checkout.Session.create,
            mode="payment",
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": currency,
                    "product_data": {"name": metadata.get("package_id", "service")},
                    "unit_amount": unit_amount,
                },
                "quantity": 1,
            }],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=metadata,
        )
        return CheckoutSession(url=session.url, session_id=session.id)

    # ── Status ───────────────────────────────────────────────────────────────
    async def get_checkout_status(self, session_id: str) -> CheckoutStatus:
        import asyncio
        import stripe
        stripe.api_key = self.api_key
        s = await asyncio.to_thread(stripe.checkout.Session.retrieve, session_id)
        return CheckoutStatus(
            status=s.status or "open",
            payment_status=s.payment_status or "unpaid",
            amount_total=s.amount_total,
            currency=s.currency,
            metadata=dict(s.metadata or {}),
        )

    # ── Webhook ──────────────────────────────────────────────────────────────
    async def handle_webhook(self, body: bytes, sig: str) -> WebhookEvent:
        import stripe
        if not self.webhook_secret:
            raise RuntimeError("STRIPE_WEBHOOK_SECRET not set — required for webhook verification")
        event = stripe.Webhook.construct_event(body, sig, self.webhook_secret)
        data = (event.get("data") or {}).get("object") or {}
        return WebhookEvent(
            event_id=event["id"],
            event_type=event["type"],
            session_id=data.get("id") if event["type"].startswith("checkout.session") else None,
            payment_status=data.get("payment_status"),
            metadata=dict(data.get("metadata") or {}),
        )
