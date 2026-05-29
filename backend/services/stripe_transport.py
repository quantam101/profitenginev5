"""Stripe transport abstraction — native `stripe` SDK with a fallback to the
Emergent-wrapped library. Same shape, different transport.

When `STRIPE_API_KEY` is set (whether sk_test_emergent OR sk_live_...) the
native `stripe` SDK is used by default. This works ANYWHERE: Emergent preview,
Railway, AWS, Vercel — no platform lock-in.

Set `STRIPE_USE_EMERGENT=1` to force the legacy Emergent wrapper if you ever
need to compare behaviour.
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


def _use_native(api_key: str = "") -> bool:
    """Route real Stripe keys to the native SDK; Emergent magic key to the
    Emergent transport. Force with STRIPE_USE_EMERGENT=1 / =0."""
    forced = os.environ.get("STRIPE_USE_EMERGENT")
    if forced == "1":
        return False
    if forced == "0":
        return True
    # Real Stripe keys are sk_test_<24chars>+ or sk_live_<24chars>+.
    # Emergent's preview magic key is literally "sk_test_emergent" (16 chars).
    return bool(api_key) and len(api_key) > 25


class StripeTransport:
    """Thin async wrapper. Native path uses official `stripe` SDK in sync mode
    (Stripe's SDK doesn't ship async; we run sync calls in a thread via
    `asyncio.to_thread`)."""

    def __init__(self, api_key: str, *, webhook_secret: str | None = None) -> None:
        self.api_key = api_key
        self.webhook_secret = webhook_secret or os.environ.get("STRIPE_WEBHOOK_SECRET")

    # ── Create checkout session ──
    async def create_checkout_session(self, *, amount: float, currency: str,
                                      success_url: str, cancel_url: str,
                                      metadata: dict) -> CheckoutSession:
        if _use_native(self.api_key):
            return await self._native_create(amount=amount, currency=currency,
                                             success_url=success_url,
                                             cancel_url=cancel_url, metadata=metadata)
        return await self._emergent_create(amount=amount, currency=currency,
                                           success_url=success_url,
                                           cancel_url=cancel_url, metadata=metadata)

    async def _native_create(self, *, amount: float, currency: str,
                             success_url: str, cancel_url: str,
                             metadata: dict) -> CheckoutSession:
        import asyncio
        import stripe
        stripe.api_key = self.api_key
        unit_amount = int(round(amount * 100))  # cents
        session = await asyncio.to_thread(
            stripe.checkout.Session.create,
            mode="payment",
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": currency,
                    "product_data": {"name": metadata.get("package_id", "subscription")},
                    "unit_amount": unit_amount,
                },
                "quantity": 1,
            }],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=metadata,
        )
        return CheckoutSession(url=session.url, session_id=session.id)

    async def _emergent_create(self, *, amount: float, currency: str,
                               success_url: str, cancel_url: str,
                               metadata: dict) -> CheckoutSession:
        from emergentintegrations.payments.stripe.checkout import (
            StripeCheckout, CheckoutSessionRequest,
        )
        wrapper = StripeCheckout(api_key=self.api_key, webhook_url="")
        s = await wrapper.create_checkout_session(CheckoutSessionRequest(
            amount=amount, currency=currency,
            success_url=success_url, cancel_url=cancel_url,
            metadata=metadata,
        ))
        return CheckoutSession(url=s.url, session_id=s.session_id)

    # ── Status ──
    async def get_checkout_status(self, session_id: str) -> CheckoutStatus:
        if _use_native(self.api_key):
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
        from emergentintegrations.payments.stripe.checkout import StripeCheckout
        wrapper = StripeCheckout(api_key=self.api_key, webhook_url="")
        r = await wrapper.get_checkout_status(session_id)
        return CheckoutStatus(
            status=r.status, payment_status=r.payment_status,
            amount_total=r.amount_total, currency=r.currency,
            metadata=r.metadata or {},
        )

    # ── Webhook ──
    async def handle_webhook(self, body: bytes, sig: str) -> WebhookEvent:
        if _use_native(self.api_key):
            import stripe
            if not self.webhook_secret:
                raise RuntimeError("STRIPE_WEBHOOK_SECRET not set — required for native webhook verification")
            event = stripe.Webhook.construct_event(body, sig, self.webhook_secret)
            data = (event.get("data") or {}).get("object") or {}
            return WebhookEvent(
                event_id=event["id"],
                event_type=event["type"],
                session_id=data.get("id") if event["type"].startswith("checkout.session") else None,
                payment_status=data.get("payment_status"),
                metadata=dict(data.get("metadata") or {}),
            )
        from emergentintegrations.payments.stripe.checkout import StripeCheckout
        wrapper = StripeCheckout(api_key=self.api_key, webhook_url="")
        r = await wrapper.handle_webhook(body, sig)
        return WebhookEvent(
            event_id=r.event_id, event_type=r.event_type,
            session_id=r.session_id, payment_status=r.payment_status,
            metadata=r.metadata or {},
        )
