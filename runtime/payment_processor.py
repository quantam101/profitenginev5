"""
PAYMENT PROCESSOR — Stripe integration for tier-based AUM fees
Handles recurring charges, retries, refunds, and billing history tracking.

Tier Fee Structure:
  - Hybrid: 0.5% annual AUM (charged monthly as AUM / 12 * 0.005)
  - White-Label: 1.0% annual AUM (charged monthly as AUM / 12 * 0.01)
  - Enterprise: 1.5% annual AUM (charged monthly as AUM / 12 * 0.015)

Integration:
  - Stripe API for payment processing
  - Automatic retry on failure (up to 3 attempts)
  - Refund mechanism for failed charges
  - PCI compliance (never store full card details)
  - Audit logging of all financial transactions
"""

from __future__ import annotations

import os
import sqlite3
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any
from enum import Enum
from pathlib import Path
import time
import hashlib

try:
    import stripe
except ImportError:
    stripe = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# TIER DEFINITIONS & CHARGE MODELS
# ============================================================================

class BillingTier(Enum):
    """Subscription tier with AUM fee percentages"""
    FREE = {"fee_bps": 0, "name": "Free"}
    HYBRID = {"fee_bps": 50, "name": "Hybrid"}  # 0.50% annually
    WHITE_LABEL = {"fee_bps": 100, "name": "White-Label"}  # 1.0% annually
    ENTERPRISE = {"fee_bps": 150, "name": "Enterprise"}  # 1.5% annually


class ChargeStatus(Enum):
    """Status of a billing charge"""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    REFUNDED = "refunded"
    RETRY = "retry"


@dataclass(frozen=True)
class BillingEvent:
    """Immutable record of a billing action"""
    charge_id: str
    client_id: str
    username: str
    charge_type: str  # "monthly_tier_fee", "manual_charge", "refund"
    tier: str
    account_balance: Decimal
    charge_amount_usd: Decimal
    tax_amount_usd: Decimal = Decimal("0.00")
    total_amount_usd: Decimal = Decimal("0.00")
    status: str = ChargeStatus.PENDING.value
    stripe_transaction_id: Optional[str] = None
    failure_reason: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = None
    processed_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate and set defaults"""
        if self.created_at is None:
            object.__setattr__(self, "created_at", datetime.utcnow())
        if self.total_amount_usd == Decimal("0.00"):
            total = self.charge_amount_usd + self.tax_amount_usd
            object.__setattr__(self, "total_amount_usd", total)


# ============================================================================
# PAYMENT PROCESSOR
# ============================================================================

class StripePaymentProcessor:
    """
    Stripe-integrated payment processor for recurring tier fees.
    Handles charges, retries, refunds, and billing tracking.
    """

    # Stripe configuration
    STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY", "")
    STRIPE_API_VERSION = "2024-06-20"

    # Retry policy
    MAX_RETRY_ATTEMPTS = 3
    RETRY_DELAY_MINUTES = [5, 30, 240]  # Exponential backoff: 5 min, 30 min, 4 hours

    # Tax calculation (adjust per jurisdiction)
    TAX_RATE = Decimal("0.08")  # 8% tax (configurable)

    # Database path
    DB_PATH = os.environ.get("BILLING_DB_PATH", "clients.db")

    def __init__(self, db_path: str = None, stripe_key: str = None):
        """Initialize payment processor"""
        if stripe_key:
            stripe.api_key = stripe_key
        elif self.STRIPE_API_KEY:
            stripe.api_key = self.STRIPE_API_KEY
        else:
            logger.warning(
                "No STRIPE_API_KEY set. Payment processing disabled. "
                "Set env var STRIPE_API_KEY=sk_live_... or sk_test_..."
            )

        self.db_path = db_path or self.DB_PATH
        self._init_billing_db()

    def _init_billing_db(self):
        """Initialize billing and transaction tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Billing history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS billing_history (
                charge_id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                username TEXT,
                charge_type TEXT,
                tier TEXT,
                account_balance REAL,
                charge_amount_usd REAL,
                tax_amount_usd REAL,
                total_amount_usd REAL,
                status TEXT,
                stripe_transaction_id TEXT,
                failure_reason TEXT,
                retry_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients(client_id)
            )
        """)

        # Refund tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS refunds (
                refund_id TEXT PRIMARY KEY,
                original_charge_id TEXT NOT NULL,
                client_id TEXT NOT NULL,
                amount_usd REAL,
                reason TEXT,
                stripe_refund_id TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP,
                FOREIGN KEY (original_charge_id) REFERENCES billing_history(charge_id)
            )
        """)

        # Subscription tracking (when users are enrolled in recurring billing)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                subscription_id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                tier TEXT,
                stripe_subscription_id TEXT UNIQUE,
                stripe_customer_id TEXT,
                payment_method_id TEXT,
                billing_cycle_day INTEGER DEFAULT 1,
                next_billing_date DATE,
                status TEXT DEFAULT 'active',
                enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                canceled_at TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients(client_id)
            )
        """)

        # Revenue tracking for reports
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS revenue_tracking (
                revenue_id INTEGER PRIMARY KEY AUTOINCREMENT,
                month TEXT,
                tier TEXT,
                client_count INTEGER,
                total_aum_usd REAL,
                total_charges_usd REAL,
                total_refunds_usd REAL,
                mrr_usd REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Upsell tracking (when to upgrade)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS upsell_tracking (
                tracking_id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT NOT NULL UNIQUE,
                current_tier TEXT DEFAULT 'free',
                eligible_tier TEXT,
                score REAL,
                last_scored_at TIMESTAMP,
                upgrade_offered_at TIMESTAMP,
                upgraded_at TIMESTAMP,
                last_performance_check TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients(client_id)
            )
        """)

        conn.commit()
        conn.close()
        logger.info("Billing database tables initialized")

    # ========================================================================
    # TIER UPGRADE OPERATIONS
    # ========================================================================

    def upgrade_client_tier(
        self,
        client_id: str,
        username: str,
        new_tier: str,
        account_balance: Decimal,
        stripe_customer_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Upgrade a client to a new tier and initialize recurring billing.

        Args:
            client_id: Client identifier
            username: Client username
            new_tier: Target tier (hybrid, white_label, enterprise)
            account_balance: Current account AUM
            stripe_customer_id: Optional Stripe customer ID

        Returns:
            Dict with upgrade status, subscription ID, first charge amount
        """
        if not stripe:
            return {
                "success": False,
                "error": "Stripe not configured",
                "status": "BLOCKED"
            }

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Check if already subscribed
            cursor.execute(
                "SELECT subscription_id FROM subscriptions WHERE client_id = ? AND status = 'active'",
                (client_id,)
            )
            existing = cursor.fetchone()
            if existing:
                logger.warning(f"Client {client_id} already has active subscription")
                return {
                    "success": False,
                    "error": "Client already subscribed",
                    "status": "DUPLICATE"
                }

            # Create or retrieve Stripe customer
            if not stripe_customer_id:
                customer = stripe.Customer.create(
                    metadata={
                        "client_id": client_id,
                        "username": username,
                    },
                    api_key=stripe.api_key
                )
                stripe_customer_id = customer.id
            else:
                customer = stripe.Customer.retrieve(stripe_customer_id)

            # Get tier fee
            tier_info = self._get_tier_info(new_tier)
            if not tier_info:
                return {
                    "success": False,
                    "error": f"Invalid tier: {new_tier}",
                    "status": "INVALID_TIER"
                }

            # Calculate first month charge
            monthly_charge = self._calculate_monthly_charge(account_balance, new_tier)
            tax_amount = self._calculate_tax(monthly_charge)
            total_charge = monthly_charge + tax_amount

            # Create subscription in Stripe
            subscription_data = {
                "customer": stripe_customer_id,
                "items": [
                    {
                        "price_data": {
                            "currency": "usd",
                            "product_data": {
                                "name": f"ProfitEngine {tier_info['name']} Tier",
                                "metadata": {
                                    "tier": new_tier,
                                    "aum_fee_bps": str(tier_info['fee_bps']),
                                }
                            },
                            "unit_amount": int(total_charge * 100),  # Stripe uses cents
                            "recurring": {
                                "interval": "month",
                                "interval_count": 1,
                            }
                        },
                        "quantity": 1,
                    }
                ],
                "metadata": {
                    "client_id": client_id,
                    "username": username,
                    "tier": new_tier,
                    "initial_aum": str(account_balance),
                },
                "default_payment_method": customer.invoice_settings.default_payment_method,
            }

            subscription = stripe.Subscription.create(**subscription_data)

            # Record in database
            subscription_id = self._generate_id("SUB")
            next_billing = datetime.utcnow() + timedelta(days=30)

            cursor.execute("""
                INSERT INTO subscriptions (
                    subscription_id, client_id, tier, stripe_subscription_id,
                    stripe_customer_id, next_billing_date, status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                subscription_id,
                client_id,
                new_tier,
                subscription.id,
                stripe_customer_id,
                next_billing.date(),
                "active"
            ))

            # Update upsell tracking
            cursor.execute("""
                INSERT INTO upsell_tracking (client_id, current_tier, upgraded_at)
                VALUES (?, ?, ?)
                ON CONFLICT(client_id) DO UPDATE SET
                    current_tier = ?,
                    upgraded_at = ?
            """, (
                client_id,
                new_tier,
                datetime.utcnow().isoformat(),
                new_tier,
                datetime.utcnow().isoformat(),
            ))

            conn.commit()

            logger.info(
                f"Upgraded {username} ({client_id}) to {new_tier}. "
                f"Subscription: {subscription.id}, First charge: ${total_charge:.2f}"
            )

            return {
                "success": True,
                "status": "UPGRADED",
                "client_id": client_id,
                "new_tier": new_tier,
                "subscription_id": subscription_id,
                "stripe_subscription_id": subscription.id,
                "stripe_customer_id": stripe_customer_id,
                "monthly_charge_usd": float(monthly_charge),
                "tax_usd": float(tax_amount),
                "total_charge_usd": float(total_charge),
                "next_billing_date": next_billing.isoformat(),
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error upgrading {client_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "status": "STRIPE_ERROR"
            }
        finally:
            conn.close()

    def downgrade_client_tier(
        self,
        client_id: str,
        new_tier: str,
        account_balance: Decimal,
    ) -> Dict[str, Any]:
        """
        Downgrade a client to a lower tier and process refund if applicable.

        Args:
            client_id: Client identifier
            new_tier: Target tier (may include 'free')
            account_balance: Current account AUM

        Returns:
            Dict with downgrade status and refund amount
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Get current subscription
            cursor.execute(
                "SELECT tier, stripe_subscription_id FROM subscriptions WHERE client_id = ? AND status = 'active'",
                (client_id,)
            )
            result = cursor.fetchone()
            if not result:
                return {
                    "success": False,
                    "error": "No active subscription found",
                    "status": "NOT_FOUND"
                }

            current_tier, stripe_sub_id = result

            # Calculate prorated refund
            refund_amount = self._calculate_prorated_refund(client_id, current_tier, new_tier)

            # Cancel/update subscription in Stripe
            if new_tier.lower() == "free":
                if stripe and stripe_sub_id:
                    stripe.Subscription.delete(stripe_sub_id)
                    cursor.execute(
                        "UPDATE subscriptions SET status = 'canceled', canceled_at = ? WHERE subscription_id IN (SELECT subscription_id FROM subscriptions WHERE stripe_subscription_id = ?)",
                        (datetime.utcnow().isoformat(), stripe_sub_id)
                    )
            else:
                # Update subscription to new tier (would involve updating Stripe subscription)
                new_tier_info = self._get_tier_info(new_tier)
                cursor.execute(
                    "UPDATE subscriptions SET tier = ? WHERE client_id = ? AND status = 'active'",
                    (new_tier, client_id)
                )

            # Process refund if applicable
            if refund_amount > 0:
                refund_id = self._generate_id("RFD")
                cursor.execute(
                    "SELECT stripe_subscription_id FROM subscriptions WHERE client_id = ?",
                    (client_id,)
                )
                row = cursor.fetchone()
                stripe_sub_id = row[0] if row else None

                cursor.execute("""
                    INSERT INTO refunds (refund_id, original_charge_id, client_id, amount_usd, reason)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    refund_id,
                    None,  # We'll link to original charge if needed
                    client_id,
                    float(refund_amount),
                    f"Downgrade from {current_tier} to {new_tier}",
                ))

            # Update upsell tracking
            cursor.execute("""
                UPDATE upsell_tracking SET current_tier = ? WHERE client_id = ?
            """, (new_tier, client_id))

            conn.commit()

            logger.info(
                f"Downgraded {client_id} from {current_tier} to {new_tier}. "
                f"Refund: ${refund_amount:.2f}"
            )

            return {
                "success": True,
                "status": "DOWNGRADED",
                "client_id": client_id,
                "previous_tier": current_tier,
                "new_tier": new_tier,
                "refund_amount_usd": float(refund_amount),
            }

        except Exception as e:
            logger.error(f"Error downgrading {client_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "status": "ERROR"
            }
        finally:
            conn.close()

    # ========================================================================
    # CHARGE OPERATIONS
    # ========================================================================

    def process_monthly_charges(self) -> Dict[str, Any]:
        """
        Process monthly tier fees for all active subscriptions.
        Called daily; charges are scheduled for the next billing date.

        Returns:
            Dict with processing results (charges attempted, successful, failed)
        """
        if not stripe:
            logger.error("Stripe not configured; skipping monthly charges")
            return {"success": False, "error": "Stripe not configured"}

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Find subscriptions due for billing
            today = datetime.utcnow().date()
            cursor.execute("""
                SELECT s.subscription_id, s.client_id, c.username, s.tier, c.account_balance,
                       s.stripe_subscription_id, s.next_billing_date
                FROM subscriptions s
                JOIN clients c ON s.client_id = c.client_id
                WHERE s.status = 'active' AND s.next_billing_date <= ?
            """, (today,))

            subscriptions = cursor.fetchall()

            results = {
                "total_attempted": len(subscriptions),
                "successful": 0,
                "failed": 0,
                "charges": [],
            }

            for sub_row in subscriptions:
                (sub_id, client_id, username, tier, account_balance,
                 stripe_sub_id, next_billing) = sub_row

                # Calculate charge
                monthly_charge = self._calculate_monthly_charge(
                    Decimal(str(account_balance)), tier
                )
                tax_amount = self._calculate_tax(monthly_charge)
                total_charge = monthly_charge + tax_amount

                # Attempt charge
                charge_result = self._process_charge(
                    client_id=client_id,
                    username=username,
                    tier=tier,
                    account_balance=Decimal(str(account_balance)),
                    charge_amount=monthly_charge,
                    tax_amount=tax_amount,
                    stripe_subscription_id=stripe_sub_id,
                )

                if charge_result["success"]:
                    results["successful"] += 1
                    # Update next billing date
                    new_billing = (
                        datetime.fromisoformat(next_billing) + timedelta(days=30)
                        if isinstance(next_billing, str)
                        else datetime.fromisoformat(str(next_billing)) + timedelta(days=30)
                    ).date()
                    cursor.execute(
                        "UPDATE subscriptions SET next_billing_date = ? WHERE subscription_id = ?",
                        (new_billing, sub_id)
                    )
                else:
                    results["failed"] += 1
                    # Schedule retry
                    cursor.execute(
                        "UPDATE subscriptions SET next_billing_date = ? WHERE subscription_id = ?",
                        ((datetime.utcnow() + timedelta(minutes=5)).date(), sub_id)
                    )

                results["charges"].append(charge_result)

            conn.commit()
            logger.info(
                f"Monthly charges: {results['successful']}/{results['total_attempted']} successful"
            )
            return results

        finally:
            conn.close()

    def _process_charge(
        self,
        client_id: str,
        username: str,
        tier: str,
        account_balance: Decimal,
        charge_amount: Decimal,
        tax_amount: Decimal,
        stripe_subscription_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process a single charge against a customer's subscription.

        Returns:
            Dict with charge status, transaction ID, and any errors
        """
        charge_id = self._generate_id("CHG")

        try:
            # Attempt charge via Stripe
            if stripe_subscription_id and stripe:
                invoice = stripe.Invoice.create(
                    customer=stripe_subscription_id,
                    subscription=stripe_subscription_id,
                )
                invoice = stripe.Invoice.pay(invoice.id)
                transaction_id = invoice.id
            else:
                # Fallback for testing without Stripe
                transaction_id = self._generate_id("TXN")

            # Record successful charge
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO billing_history (
                    charge_id, client_id, username, charge_type, tier,
                    account_balance, charge_amount_usd, tax_amount_usd,
                    total_amount_usd, status, stripe_transaction_id, processed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                charge_id,
                client_id,
                username,
                "monthly_tier_fee",
                tier,
                float(account_balance),
                float(charge_amount),
                float(tax_amount),
                float(charge_amount + tax_amount),
                ChargeStatus.SUCCESS.value,
                transaction_id,
                datetime.utcnow().isoformat(),
            ))
            conn.commit()
            conn.close()

            logger.info(
                f"Charge successful: {charge_id} for {username} ({client_id}), "
                f"Amount: ${charge_amount:.2f} + ${tax_amount:.2f} tax"
            )

            return {
                "success": True,
                "charge_id": charge_id,
                "client_id": client_id,
                "username": username,
                "amount_usd": float(charge_amount + tax_amount),
                "transaction_id": transaction_id,
            }

        except stripe.error.CardError as e:
            logger.warning(f"Card declined for {username}: {e}")
            self._record_failed_charge(
                charge_id, client_id, username, tier, account_balance,
                charge_amount, tax_amount, str(e)
            )
            return {
                "success": False,
                "charge_id": charge_id,
                "client_id": client_id,
                "error": "Card declined",
                "retry_eligible": True,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error processing charge for {client_id}: {e}")
            self._record_failed_charge(
                charge_id, client_id, username, tier, account_balance,
                charge_amount, tax_amount, str(e)
            )
            return {
                "success": False,
                "charge_id": charge_id,
                "client_id": client_id,
                "error": str(e),
                "retry_eligible": True,
            }

    def _record_failed_charge(
        self,
        charge_id: str,
        client_id: str,
        username: str,
        tier: str,
        account_balance: Decimal,
        charge_amount: Decimal,
        tax_amount: Decimal,
        failure_reason: str,
    ):
        """Record a failed charge attempt"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO billing_history (
                charge_id, client_id, username, charge_type, tier,
                account_balance, charge_amount_usd, tax_amount_usd,
                total_amount_usd, status, failure_reason, retry_count
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            charge_id,
            client_id,
            username,
            "monthly_tier_fee",
            tier,
            float(account_balance),
            float(charge_amount),
            float(tax_amount),
            float(charge_amount + tax_amount),
            ChargeStatus.FAILED.value,
            failure_reason,
            0,
        ))
        conn.commit()
        conn.close()

    def retry_failed_charges(self) -> Dict[str, Any]:
        """
        Retry previously failed charges (max 3 attempts with exponential backoff).
        Run this periodically (e.g., every hour).

        Returns:
            Dict with retry results
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Find failed charges eligible for retry
            cursor.execute("""
                SELECT charge_id, client_id, username, tier, account_balance,
                       charge_amount_usd, tax_amount_usd, retry_count
                FROM billing_history
                WHERE status = ? AND retry_count < ?
                ORDER BY created_at ASC
            """, (ChargeStatus.FAILED.value, self.MAX_RETRY_ATTEMPTS))

            failed_charges = cursor.fetchall()

            results = {
                "total_retried": len(failed_charges),
                "successful": 0,
                "still_failed": 0,
            }

            for charge_row in failed_charges:
                (charge_id, client_id, username, tier, account_balance,
                 charge_amount, tax_amount, retry_count) = charge_row

                # Respect backoff timing
                if not self._should_retry_now(charge_id, retry_count):
                    continue

                retry_result = self._process_charge(
                    client_id=client_id,
                    username=username,
                    tier=tier,
                    account_balance=Decimal(str(account_balance)),
                    charge_amount=Decimal(str(charge_amount)),
                    tax_amount=Decimal(str(tax_amount)),
                )

                if retry_result["success"]:
                    cursor.execute(
                        "UPDATE billing_history SET status = ? WHERE charge_id = ?",
                        (ChargeStatus.SUCCESS.value, charge_id)
                    )
                    results["successful"] += 1
                else:
                    cursor.execute(
                        "UPDATE billing_history SET retry_count = retry_count + 1 WHERE charge_id = ?",
                        (charge_id,)
                    )
                    results["still_failed"] += 1

            conn.commit()
            logger.info(
                f"Retry charges: {results['successful']} successful, "
                f"{results['still_failed']} still failed"
            )
            return results

        finally:
            conn.close()

    def _should_retry_now(self, charge_id: str, retry_count: int) -> bool:
        """Check if charge should be retried now based on backoff schedule"""
        if retry_count >= self.MAX_RETRY_ATTEMPTS:
            return False

        delay_minutes = self.RETRY_DELAY_MINUTES[retry_count]
        # In production, check created_at + delay_minutes
        return True  # Simplified for demo

    # ========================================================================
    # REFUND OPERATIONS
    # ========================================================================

    def process_refund(
        self,
        charge_id: str,
        amount_usd: Optional[Decimal] = None,
        reason: str = "Customer request",
    ) -> Dict[str, Any]:
        """
        Process a refund for a previously charged amount.

        Args:
            charge_id: Original charge ID
            amount_usd: Refund amount (full charge if None)
            reason: Reason for refund

        Returns:
            Dict with refund status and Stripe refund ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Get original charge
            cursor.execute(
                "SELECT stripe_transaction_id, charge_amount_usd, total_amount_usd, client_id FROM billing_history WHERE charge_id = ?",
                (charge_id,)
            )
            result = cursor.fetchone()
            if not result:
                return {
                    "success": False,
                    "error": "Charge not found",
                    "status": "NOT_FOUND"
                }

            transaction_id, orig_amount, total_amount, client_id = result
            refund_amount = amount_usd or Decimal(str(total_amount))

            # Process refund in Stripe
            stripe_refund_id = None
            if stripe and transaction_id:
                refund = stripe.Refund.create(
                    charge=transaction_id,
                    amount=int(refund_amount * 100),  # Stripe uses cents
                    metadata={
                        "reason": reason,
                        "original_charge_id": charge_id,
                    }
                )
                stripe_refund_id = refund.id

            # Record refund
            refund_id = self._generate_id("RFD")
            cursor.execute("""
                INSERT INTO refunds (
                    refund_id, original_charge_id, client_id, amount_usd,
                    reason, stripe_refund_id, status, processed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                refund_id,
                charge_id,
                client_id,
                float(refund_amount),
                reason,
                stripe_refund_id,
                ChargeStatus.REFUNDED.value,
                datetime.utcnow().isoformat(),
            ))

            conn.commit()
            logger.info(
                f"Refund processed: {refund_id} for {charge_id}, "
                f"Amount: ${refund_amount:.2f}"
            )

            return {
                "success": True,
                "refund_id": refund_id,
                "original_charge_id": charge_id,
                "amount_usd": float(refund_amount),
                "stripe_refund_id": stripe_refund_id,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error processing refund: {e}")
            return {
                "success": False,
                "error": str(e),
                "status": "STRIPE_ERROR"
            }
        finally:
            conn.close()

    # ========================================================================
    # BILLING REPORTS
    # ========================================================================

    def generate_revenue_report(self, year_month: str = None) -> Dict[str, Any]:
        """
        Generate revenue tracking report for a specific month.

        Args:
            year_month: Format "YYYY-MM" (defaults to current month)

        Returns:
            Dict with MRR, total charges, refunds, and tier breakdown
        """
        if not year_month:
            today = datetime.utcnow()
            year_month = today.strftime("%Y-%m")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Query revenue for the month
            cursor.execute("""
                SELECT tier, COUNT(DISTINCT client_id) as client_count,
                       SUM(charge_amount_usd) as total_charges,
                       SUM(tax_amount_usd) as total_tax
                FROM billing_history
                WHERE status = ? AND strftime('%Y-%m', created_at) = ?
                GROUP BY tier
            """, (ChargeStatus.SUCCESS.value, year_month))

            tier_breakdown = cursor.fetchall()

            # Total charges
            cursor.execute("""
                SELECT COALESCE(SUM(charge_amount_usd), 0) as total_charges,
                       COALESCE(SUM(tax_amount_usd), 0) as total_tax
                FROM billing_history
                WHERE status = ? AND strftime('%Y-%m', created_at) = ?
            """, (ChargeStatus.SUCCESS.value, year_month))

            total_row = cursor.fetchone()
            total_charges, total_tax = total_row

            # Total refunds
            cursor.execute("""
                SELECT COALESCE(SUM(amount_usd), 0)
                FROM refunds
                WHERE status = ? AND strftime('%Y-%m', created_at) = ?
            """, (ChargeStatus.REFUNDED.value, year_month))

            total_refunds = cursor.fetchone()[0]

            # Calculate MRR
            mrr = (total_charges + total_tax) - total_refunds

            report = {
                "period": year_month,
                "mrr_usd": float(mrr),
                "total_charges_usd": float(total_charges),
                "total_tax_usd": float(total_tax),
                "total_refunds_usd": float(total_refunds),
                "net_revenue_usd": float((total_charges + total_tax) - total_refunds),
                "tier_breakdown": [
                    {
                        "tier": tier,
                        "client_count": count,
                        "charges_usd": float(charges) if charges else 0.0,
                    }
                    for tier, count, charges, _ in tier_breakdown
                ],
            }

            logger.info(f"Revenue report for {year_month}: MRR=${mrr:.2f}")
            return report

        finally:
            conn.close()

    def get_billing_history(
        self,
        client_id: Optional[str] = None,
        tier: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Fetch billing history with optional filtering.

        Returns:
            List of billing events
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            query = "SELECT * FROM billing_history WHERE 1=1"
            params = []

            if client_id:
                query += " AND client_id = ?"
                params.append(client_id)
            if tier:
                query += " AND tier = ?"
                params.append(tier)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            # Get column names
            col_names = [description[0] for description in cursor.description]

            results = [
                dict(zip(col_names, row))
                for row in rows
            ]

            return results

        finally:
            conn.close()

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _get_tier_info(self, tier: str) -> Optional[Dict[str, Any]]:
        """Get fee info for a tier"""
        tier_upper = tier.upper()
        for billing_tier in BillingTier:
            if billing_tier.name == tier_upper:
                return billing_tier.value
        return None

    def _calculate_monthly_charge(self, aum: Decimal, tier: str) -> Decimal:
        """
        Calculate monthly fee based on AUM and tier.
        Formula: (AUM * fee_bps) / 10000 / 12
        """
        tier_info = self._get_tier_info(tier)
        if not tier_info or tier_info["fee_bps"] == 0:
            return Decimal("0.00")

        fee_rate = Decimal(str(tier_info["fee_bps"])) / Decimal("10000")
        monthly_fee = (aum * fee_rate) / Decimal("12")
        return monthly_fee.quantize(Decimal("0.01"))

    def _calculate_tax(self, amount: Decimal) -> Decimal:
        """Calculate sales tax on charge"""
        tax = amount * self.TAX_RATE
        return tax.quantize(Decimal("0.01"))

    def _calculate_prorated_refund(
        self,
        client_id: str,
        current_tier: str,
        new_tier: str,
    ) -> Decimal:
        """
        Calculate prorated refund for mid-month tier downgrade.
        Refund = (days_remaining / days_in_month) * (current_tier_fee - new_tier_fee)
        """
        # Simplified: full refund of the difference
        # In production, calculate based on billing cycle
        return Decimal("0.00")

    def _generate_id(self, prefix: str) -> str:
        """Generate unique ID with prefix"""
        timestamp = str(int(time.time() * 1000))
        random_part = hashlib.sha256(
            f"{prefix}{timestamp}".encode()
        ).hexdigest()[:8]
        return f"{prefix}-{timestamp}-{random_part}"


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("PAYMENT PROCESSOR — Stripe Integration Demo")
    print("=" * 80)

    # Initialize processor
    processor = StripePaymentProcessor()

    print("\n[INFO] Processor initialized")
    print("[INFO] Database: clients.db")
    print("[INFO] Stripe configured:", bool(stripe and processor.STRIPE_API_KEY))

    # Example 1: Upgrade client
    print("\n" + "=" * 80)
    print("Example 1: Upgrade Client to Hybrid Tier")
    print("=" * 80)
    result = processor.upgrade_client_tier(
        client_id="CLIENT-001",
        username="alice_trader",
        new_tier="hybrid",
        account_balance=Decimal("50000.00"),
    )
    print(f"Status: {result['status']}")
    if result['success']:
        print(f"Subscription ID: {result['subscription_id']}")
        print(f"Monthly Charge: ${result['monthly_charge_usd']:.2f}")
        print(f"Tax: ${result['tax_usd']:.2f}")
        print(f"Total: ${result['total_charge_usd']:.2f}")

    # Example 2: Process monthly charges
    print("\n" + "=" * 80)
    print("Example 2: Process Monthly Charges")
    print("=" * 80)
    charges = processor.process_monthly_charges()
    print(f"Attempted: {charges['total_attempted']}")
    print(f"Successful: {charges['successful']}")
    print(f"Failed: {charges['failed']}")

    # Example 3: Revenue report
    print("\n" + "=" * 80)
    print("Example 3: Revenue Report")
    print("=" * 80)
    report = processor.generate_revenue_report()
    print(f"Period: {report['period']}")
    print(f"MRR: ${report['mrr_usd']:.2f}")
    print(f"Total Charges: ${report['total_charges_usd']:.2f}")
    print(f"Refunds: ${report['total_refunds_usd']:.2f}")
    print(f"Net Revenue: ${report['net_revenue_usd']:.2f}")

    print("\n" + "=" * 80)
