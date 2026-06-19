#!/usr/bin/env python3
"""
Stripe Failed Payment Recovery System

Sends automated email sequences for failed Stripe charges:
- Day 0: Payment failed notification with retry link
- Day 3: Reminder email
- Day 5: Final warning before suspension

Environment variables:
  STRIPE_SECRET_KEY - Stripe API key
  RESEND_API_KEY - Resend email service key
"""

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx

STRIPE_API_KEY = os.getenv("STRIPE_SECRET_KEY", "").strip()
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "").strip()

STRIPE_API = "https://api.stripe.com/v1"


def get_failed_charges(days_back: int = 30) -> list[dict]:
    """Fetch failed payment attempts from Stripe."""
    if not STRIPE_API_KEY:
        print("[ERROR] STRIPE_SECRET_KEY not configured")
        return []

    try:
        cutoff_time = int((datetime.now(timezone.utc) - timedelta(days=days_back)).timestamp())

        response = httpx.get(
            f"{STRIPE_API}/charges",
            params={
                "limit": 100,
                "created[gte]": cutoff_time,
                "status": "failed",
            },
            auth=(STRIPE_API_KEY, ""),
            timeout=10,
        )
        response.raise_for_status()

        data = response.json()
        return data.get("data", [])
    except Exception as e:
        print(f"[ERROR] Failed to fetch Stripe charges: {e}")
        return []


def send_recovery_email(email: str, customer_name: str, amount: float, day: int = 0) -> bool:
    """Send payment recovery email via Resend."""
    if not RESEND_API_KEY:
        print("[ERROR] RESEND_API_KEY not configured")
        return False

    if day == 0:
        subject = f"Payment Failed: ${amount:.2f} retry needed"
        body = f"""
Hi {customer_name},

Your recent payment of ${amount:.2f} failed to process. This might be due to:
- Insufficient funds
- Card expiration
- Incorrect address/CVV
- Bank decline

**Retry your payment:** [Update Payment Method](https://app.alreadyherellc.com/billing/update-card)

If you need help, reply to this email.

Already Here LLC
"""
    elif day == 3:
        subject = f"Reminder: Payment retry needed (${amount:.2f})"
        body = f"""
Hi {customer_name},

This is a friendly reminder that your payment of ${amount:.2f} is still pending.

Without an update, your account may be suspended on June 24.

[Retry Payment](https://app.alreadyherellc.com/billing/update-card)

Already Here LLC
"""
    elif day == 5:
        subject = f"Final notice: Account suspension in 2 days"
        body = f"""
Hi {customer_name},

Your account will be suspended in 2 days unless payment is updated.

**Amount due:** ${amount:.2f}

[Update Payment Now](https://app.alreadyherellc.com/billing/update-card)

Already Here LLC
"""
    else:
        return False

    try:
        response = httpx.post(
            "https://api.resend.com/emails",
            json={
                "from": "billing@alreadyherellc.com",
                "to": email,
                "subject": subject,
                "html": body.replace("\n", "<br>"),
            },
            headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
            timeout=10,
        )
        response.raise_for_status()
        print(f"[OK] Sent day-{day} recovery email to {email}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send email to {email}: {e}")
        return False


def process_failed_charges() -> None:
    """Find failed charges and send recovery emails."""
    charges = get_failed_charges(days_back=5)
    print(f"[INFO] Found {len(charges)} failed charges")

    for charge in charges:
        customer_email = charge.get("billing_details", {}).get("email") or charge.get("receipt_email")
        customer_id = charge.get("customer")
        amount = charge.get("amount", 0) / 100  # Convert cents to dollars
        created = charge.get("created", 0)

        if not customer_email:
            print(f"[SKIP] Charge {charge['id']} has no email")
            continue

        # Calculate days since failure
        days_since = int((datetime.now(timezone.utc).timestamp() - created) / 86400)

        # Send appropriate email
        if days_since == 0:
            send_recovery_email(customer_email, customer_id or "valued customer", amount, day=0)
        elif days_since == 3:
            send_recovery_email(customer_email, customer_id or "valued customer", amount, day=3)
        elif days_since == 5:
            send_recovery_email(customer_email, customer_id or "valued customer", amount, day=5)


if __name__ == "__main__":
    process_failed_charges()
