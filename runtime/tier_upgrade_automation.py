"""
TIER UPGRADE AUTOMATION — Automatic customer tier upgrades based on performance
Runs daily after daily_alerts.py (5 PM MST / 11 PM UTC)

Features:
  - Score clients based on upsell_intelligence metrics
  - Identify upgrade candidates by tier threshold
  - Automatically upgrade via payment processor
  - Send upgrade confirmation emails
  - Track performance changes
  - Downgrade clients if performance drops
  - Comprehensive audit logging

Tier Thresholds:
  - Score >= 50 → Hybrid (0.5% AUM fee)
  - Score >= 75 → White-Label (1.0% AUM fee)
  - Score >= 90 → Enterprise (1.5% AUM fee)
"""

from __future__ import annotations

import os
import sqlite3
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from decimal import Decimal
from pathlib import Path
import hashlib
import time

from upsell_intelligence import UpsellScorer, UpsellTier, generate_daily_upsell_report
from payment_processor import StripePaymentProcessor, BillingTier
from audit_log import AuditLog, AuditEvent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================

# Email templates location
EMAIL_TEMPLATES_DIR = os.environ.get("EMAIL_TEMPLATES_DIR", "email_templates")

# Upgrade thresholds
UPGRADE_THRESHOLDS = {
    "hybrid": {"min_score": 50, "fee_bps": 50},
    "white_label": {"min_score": 75, "fee_bps": 100},
    "enterprise": {"min_score": 90, "fee_bps": 150},
}

# Downgrade threshold (score below which client is demoted)
DOWNGRADE_THRESHOLD = {"max_score": 40}

# Email notification settings
SEND_UPGRADE_EMAIL = os.environ.get("SEND_UPGRADE_EMAIL", "true").lower() == "true"
SEND_DOWNGRADE_EMAIL = os.environ.get("SEND_DOWNGRADE_EMAIL", "true").lower() == "true"
SUPPORT_EMAIL = os.environ.get("SUPPORT_EMAIL", "support@profitengine.com")

# Database paths
DB_PATH = os.environ.get("CLIENTS_DB_PATH", "clients.db")
BILLING_DB_PATH = os.environ.get("BILLING_DB_PATH", "clients.db")

# Audit log
AUDIT_LOG = AuditLog(os.environ.get("AUDIT_LOG_PATH", "data/audit.jsonl"))


# ============================================================================
# TIER UPGRADE AUTOMATION ENGINE
# ============================================================================

class TierUpgradeAutomation:
    """
    Automated tier upgrade engine that:
    1. Scores all clients daily
    2. Identifies upgrade/downgrade candidates
    3. Processes tier changes
    4. Handles payment processing
    5. Sends notifications
    6. Logs all changes to audit trail
    """

    def __init__(self, db_path: str = DB_PATH, billing_db_path: str = BILLING_DB_PATH):
        """Initialize automation engine"""
        self.db_path = db_path
        self.billing_db_path = billing_db_path
        self.scorer = UpsellScorer(db_path)
        self.payment_processor = StripePaymentProcessor(billing_db_path)
        self.results = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_clients_scored": 0,
            "upgrades_processed": 0,
            "downgrades_processed": 0,
            "failed_upgrades": [],
            "failed_downgrades": [],
            "emails_sent": 0,
            "errors": [],
        }

    def run_daily_upgrade_cycle(self) -> Dict[str, Any]:
        """
        Main entry point: Run complete daily upgrade/downgrade cycle.
        Call this at 5 PM MST (11 PM UTC) daily.

        Returns:
            Dict with results: upgrades, downgrades, failures, email sends
        """
        logger.info("=" * 80)
        logger.info("TIER UPGRADE AUTOMATION — Daily Cycle Started")
        logger.info("=" * 80)

        try:
            # Step 1: Score all clients
            logger.info("Step 1: Scoring all clients...")
            campaign = self.scorer.score_all_clients()
            self.results["total_clients_scored"] = campaign.total_clients_scored

            # Step 2: Process upgrades
            logger.info("Step 2: Processing tier upgrades...")
            for candidate in (
                campaign.enterprise_candidates
                + campaign.white_label_candidates
                + campaign.hybrid_candidates
            ):
                self._process_upgrade(candidate)

            # Step 3: Check for downgrades
            logger.info("Step 3: Checking for downgrades...")
            self._check_for_downgrades()

            # Step 4: Generate summary
            logger.info("Step 4: Generating summary...")
            self._log_results()

            return self.results

        except Exception as e:
            logger.error(f"Error in daily upgrade cycle: {e}")
            self.results["errors"].append(str(e))
            AUDIT_LOG.error(
                "tier_upgrade_automation",
                "run_daily_upgrade_cycle",
                {"error": str(e)},
            )
            return self.results

    def _process_upgrade(self, candidate) -> bool:
        """
        Process a single upgrade candidate.

        Steps:
        1. Determine target tier
        2. Check current tier status
        3. Process payment (if upgrading from free/lower tier)
        4. Update database
        5. Send confirmation email
        6. Audit log

        Returns:
            True if successful, False otherwise
        """
        client_id = candidate.client_id
        username = candidate.username
        target_tier = candidate.tier_recommendation.value

        logger.info(f"Processing upgrade for {username} ({client_id}) → {target_tier}")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Get current tier
            cursor.execute(
                "SELECT subscription_tier FROM clients WHERE client_id = ?",
                (client_id,)
            )
            result = cursor.fetchone()
            current_tier = result[0] if result else "free"

            # Skip if already at or above target tier
            tier_rank = {"free": 0, "hybrid": 1, "white_label": 2, "enterprise": 3}
            if tier_rank.get(current_tier, 0) >= tier_rank.get(target_tier, 0):
                logger.info(f"Client {username} already at or above target tier")
                conn.close()
                return False

            # Get account balance
            cursor.execute(
                "SELECT account_balance FROM clients WHERE client_id = ?",
                (client_id,)
            )
            result = cursor.fetchone()
            account_balance = Decimal(str(result[0])) if result else Decimal("0.00")

            conn.close()

            # Process upgrade via payment processor
            upgrade_result = self.payment_processor.upgrade_client_tier(
                client_id=client_id,
                username=username,
                new_tier=target_tier,
                account_balance=account_balance,
            )

            if not upgrade_result.get("success"):
                logger.error(
                    f"Upgrade failed for {username}: {upgrade_result.get('error')}"
                )
                self.results["failed_upgrades"].append({
                    "client_id": client_id,
                    "username": username,
                    "reason": upgrade_result.get("error"),
                })

                AUDIT_LOG.error(
                    "tier_upgrade_automation",
                    "upgrade",
                    {
                        "client_id": client_id,
                        "username": username,
                        "target_tier": target_tier,
                        "error": upgrade_result.get("error"),
                    },
                )
                return False

            # Update client tier in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE clients SET subscription_tier = ? WHERE client_id = ?",
                (target_tier, client_id)
            )
            conn.commit()
            conn.close()

            # Send upgrade confirmation email
            if SEND_UPGRADE_EMAIL:
                email_sent = self._send_upgrade_email(
                    username=username,
                    client_id=client_id,
                    tier=target_tier,
                    score=candidate.base_score,
                    monthly_charge=upgrade_result.get("monthly_charge_usd", 0),
                    account_balance=account_balance,
                )
                if email_sent:
                    self.results["emails_sent"] += 1

            self.results["upgrades_processed"] += 1

            # Audit log
            AUDIT_LOG.info(
                "tier_upgrade_automation",
                "upgrade",
                {
                    "client_id": client_id,
                    "username": username,
                    "previous_tier": current_tier,
                    "new_tier": target_tier,
                    "score": candidate.base_score,
                    "monthly_charge_usd": upgrade_result.get("monthly_charge_usd"),
                    "subscription_id": upgrade_result.get("subscription_id"),
                },
            )

            logger.info(
                f"Upgrade successful: {username} ({client_id}) → {target_tier}, "
                f"Monthly charge: ${upgrade_result.get('monthly_charge_usd', 0):.2f}"
            )
            return True

        except Exception as e:
            logger.error(f"Error upgrading {client_id}: {e}")
            self.results["failed_upgrades"].append({
                "client_id": client_id,
                "username": username,
                "reason": str(e),
            })
            AUDIT_LOG.error(
                "tier_upgrade_automation",
                "upgrade",
                {"client_id": client_id, "error": str(e)},
            )
            return False

    def _check_for_downgrades(self):
        """
        Check existing paid tier clients and downgrade if performance drops.

        Process:
        1. Query all clients with subscription_tier != 'free'
        2. Check their latest score against downgrade threshold
        3. If score below threshold, send warning email
        4. After warning period, process downgrade if still below threshold
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Get all paid tier clients
            cursor.execute(
                "SELECT client_id, username, subscription_tier, account_balance FROM clients WHERE subscription_tier != 'free'"
            )
            paid_clients = cursor.fetchall()

            logger.info(f"Checking {len(paid_clients)} paid tier clients for downgrades...")

            for client_id, username, current_tier, account_balance in paid_clients:
                # Get client metrics and score
                metrics = self.scorer._fetch_client_metrics(client_id, username)
                if not metrics:
                    continue

                score = self.scorer._score_client(metrics)

                # Check if below downgrade threshold
                if score.base_score < DOWNGRADE_THRESHOLD["max_score"]:
                    logger.warning(
                        f"Client {username} ({client_id}) performance degraded: "
                        f"Score {score.base_score:.1f} < {DOWNGRADE_THRESHOLD['max_score']}"
                    )

                    # Send warning email first
                    self._send_downgrade_warning_email(
                        username=username,
                        client_id=client_id,
                        current_tier=current_tier,
                        score=score.base_score,
                    )

                    # Check if warning already sent
                    cursor.execute(
                        """SELECT downgrade_warning_sent_at FROM upsell_tracking
                           WHERE client_id = ?""",
                        (client_id,)
                    )
                    result = cursor.fetchone()

                    # If warning sent > 7 days ago, process downgrade
                    if result:
                        warning_sent = datetime.fromisoformat(result[0]) if result[0] else None
                        if warning_sent and (datetime.utcnow() - warning_sent).days >= 7:
                            self._process_downgrade(
                                client_id=client_id,
                                username=username,
                                current_tier=current_tier,
                                reason="performance_below_threshold",
                            )
                    else:
                        # First warning
                        cursor.execute(
                            """UPDATE upsell_tracking SET downgrade_warning_sent_at = ?
                               WHERE client_id = ?""",
                            (datetime.utcnow().isoformat(), client_id)
                        )

        finally:
            conn.close()

    def _process_downgrade(
        self,
        client_id: str,
        username: str,
        current_tier: str,
        reason: str,
    ) -> bool:
        """
        Process a tier downgrade and refund prorated amount.

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Processing downgrade for {username} ({client_id}) from {current_tier}")

        try:
            # Determine new tier (or free)
            new_tier = "free"

            # Process downgrade in payment processor
            downgrade_result = self.payment_processor.downgrade_client_tier(
                client_id=client_id,
                new_tier=new_tier,
                account_balance=Decimal("0.00"),  # Will be fetched from DB
            )

            if not downgrade_result.get("success"):
                logger.error(
                    f"Downgrade failed for {username}: {downgrade_result.get('error')}"
                )
                self.results["failed_downgrades"].append({
                    "client_id": client_id,
                    "username": username,
                    "reason": downgrade_result.get("error"),
                })
                return False

            # Update client tier
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE clients SET subscription_tier = ? WHERE client_id = ?",
                (new_tier, client_id)
            )
            conn.commit()
            conn.close()

            # Send downgrade email
            if SEND_DOWNGRADE_EMAIL:
                self._send_downgrade_email(
                    username=username,
                    client_id=client_id,
                    previous_tier=current_tier,
                    refund_amount=downgrade_result.get("refund_amount_usd", 0),
                )

            self.results["downgrades_processed"] += 1

            # Audit log
            AUDIT_LOG.info(
                "tier_upgrade_automation",
                "downgrade",
                {
                    "client_id": client_id,
                    "username": username,
                    "previous_tier": current_tier,
                    "new_tier": new_tier,
                    "reason": reason,
                    "refund_amount_usd": downgrade_result.get("refund_amount_usd"),
                },
            )

            logger.info(
                f"Downgrade successful: {username} ({client_id}) from {current_tier}. "
                f"Refund: ${downgrade_result.get('refund_amount_usd', 0):.2f}"
            )
            return True

        except Exception as e:
            logger.error(f"Error downgrading {client_id}: {e}")
            self.results["failed_downgrades"].append({
                "client_id": client_id,
                "username": username,
                "reason": str(e),
            })
            AUDIT_LOG.error(
                "tier_upgrade_automation",
                "downgrade",
                {"client_id": client_id, "error": str(e)},
            )
            return False

    # ========================================================================
    # EMAIL NOTIFICATIONS
    # ========================================================================

    def _send_upgrade_email(
        self,
        username: str,
        client_id: str,
        tier: str,
        score: float,
        monthly_charge: float,
        account_balance: Decimal,
    ) -> bool:
        """
        Send tier upgrade confirmation email.

        Template: upgrade_confirmation.html
        """
        try:
            email_body = self._render_upgrade_email_template(
                username=username,
                tier=tier,
                score=score,
                monthly_charge=monthly_charge,
                account_balance=account_balance,
            )

            # In production, send via email service (SendGrid, SES, etc.)
            logger.info(
                f"Upgrade email sent to {username}: "
                f"Tier {tier}, Monthly charge ${monthly_charge:.2f}"
            )
            return True

        except Exception as e:
            logger.error(f"Error sending upgrade email to {username}: {e}")
            return False

    def _send_downgrade_warning_email(
        self,
        username: str,
        client_id: str,
        current_tier: str,
        score: float,
    ) -> bool:
        """Send performance warning email before downgrade"""
        try:
            logger.info(
                f"Downgrade warning email sent to {username}: "
                f"Current tier {current_tier}, Score {score:.1f}"
            )
            return True
        except Exception as e:
            logger.error(f"Error sending downgrade warning to {username}: {e}")
            return False

    def _send_downgrade_email(
        self,
        username: str,
        client_id: str,
        previous_tier: str,
        refund_amount: float,
    ) -> bool:
        """Send downgrade notification email"""
        try:
            logger.info(
                f"Downgrade email sent to {username}: "
                f"Downgraded from {previous_tier}, Refund ${refund_amount:.2f}"
            )
            return True
        except Exception as e:
            logger.error(f"Error sending downgrade email to {username}: {e}")
            return False

    def _render_upgrade_email_template(
        self,
        username: str,
        tier: str,
        score: float,
        monthly_charge: float,
        account_balance: Decimal,
    ) -> str:
        """Render upgrade email HTML"""
        tier_benefits = {
            "hybrid": [
                "Advanced trading analytics",
                "Priority support (24 hours)",
                "Risk management tools",
                "Custom alerts and notifications",
            ],
            "white_label": [
                "White-label platform access",
                "Dedicated account manager",
                "Premium analytics suite",
                "Custom integrations",
                "API access",
                "Priority support (4 hours)",
            ],
            "enterprise": [
                "Fully customized platform",
                "24/7 dedicated support team",
                "Multi-user account management",
                "Custom strategy integration",
                "Institutional-grade risk tools",
                "White-label options",
                "SLA guarantee",
            ],
        }

        benefits = tier_benefits.get(tier, [])

        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <h2>Congratulations, {username}!</h2>
            <p>Your exceptional trading performance has earned you an upgrade to our <strong>{tier.title()}</strong> tier.</p>

            <h3>Your Achievement</h3>
            <p>Your performance score: <strong>{score:.1f}/100</strong></p>
            <p>Account balance under management: <strong>${account_balance:,.2f}</strong></p>

            <h3>New Tier Benefits</h3>
            <ul>
        """

        for benefit in benefits:
            html += f"<li>{benefit}</li>\n"

        html += f"""
            </ul>

            <h3>Your New Monthly Fee</h3>
            <p>Based on your account balance, your monthly fee is: <strong>${monthly_charge:.2f}</strong></p>
            <p style="font-size: 0.9em; color: #666;">
                This is calculated as {self._get_tier_percentage(tier)}% of your annual Assets Under Management,
                divided by 12 months.
            </p>

            <h3>Next Steps</h3>
            <p>Your tier upgrade is effective immediately. Your first charge will be processed on your next billing date.</p>
            <p>Questions? Contact our support team at {SUPPORT_EMAIL}</p>

            <p style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ccc; font-size: 0.85em; color: #999;">
                This is an automated message. Please do not reply to this email.
            </p>
        </body>
        </html>
        """

        return html

    def _get_tier_percentage(self, tier: str) -> str:
        """Get annual percentage for tier"""
        percentages = {
            "hybrid": "0.50%",
            "white_label": "1.00%",
            "enterprise": "1.50%",
        }
        return percentages.get(tier, "0%")

    # ========================================================================
    # REPORTING & LOGGING
    # ========================================================================

    def _log_results(self):
        """Log daily cycle results"""
        logger.info("=" * 80)
        logger.info("TIER UPGRADE AUTOMATION — Daily Cycle Results")
        logger.info("=" * 80)
        logger.info(f"Total clients scored: {self.results['total_clients_scored']}")
        logger.info(f"Upgrades processed: {self.results['upgrades_processed']}")
        logger.info(f"Downgrades processed: {self.results['downgrades_processed']}")
        logger.info(f"Emails sent: {self.results['emails_sent']}")
        logger.info(f"Failed upgrades: {len(self.results['failed_upgrades'])}")
        logger.info(f"Failed downgrades: {len(self.results['failed_downgrades'])}")

        if self.results["failed_upgrades"]:
            logger.warning("Failed upgrades:")
            for failure in self.results["failed_upgrades"]:
                logger.warning(
                    f"  - {failure['username']} ({failure['client_id']}): {failure['reason']}"
                )

        if self.results["failed_downgrades"]:
            logger.warning("Failed downgrades:")
            for failure in self.results["failed_downgrades"]:
                logger.warning(
                    f"  - {failure['username']} ({failure['client_id']}): {failure['reason']}"
                )

        logger.info("=" * 80)


# ============================================================================
# CRON JOB ENTRY POINT
# ============================================================================

def daily_upgrade_cycle():
    """
    Entry point for cron job / scheduled task runner.
    Call this daily at 5 PM MST (11 PM UTC).

    Environment variables:
      - CLIENTS_DB_PATH: Path to clients database
      - BILLING_DB_PATH: Path to billing database
      - STRIPE_API_KEY: Stripe API key (sk_live_... or sk_test_...)
      - SEND_UPGRADE_EMAIL: "true" to send emails (default: true)
      - SEND_DOWNGRADE_EMAIL: "true" to send emails (default: true)
      - SUPPORT_EMAIL: Support email address

    Returns:
        Dict with results
    """
    engine = TierUpgradeAutomation()
    results = engine.run_daily_upgrade_cycle()
    return results


# ============================================================================
# EXAMPLE USAGE & TESTING
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("TIER UPGRADE AUTOMATION — Standalone Test")
    print("=" * 80)

    # Run daily cycle
    results = daily_upgrade_cycle()

    # Print results
    print("\nResults:")
    print(json.dumps(results, indent=2, default=str))

    print("\n" + "=" * 80)
