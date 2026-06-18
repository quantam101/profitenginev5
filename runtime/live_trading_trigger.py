"""
LIVE TRADING TRIGGER SYSTEM
Automatically deploys live capital when paper trading account hits $1,000

Monitors paper trading balance daily. When $1,000 is achieved:
1. Verifies user confirmed live trading (2FA/email confirmation)
2. Creates or connects live Robinhood account
3. Deploys $500 real capital to live trading
4. Switches user from PAPER -> LIVE tier
5. Sends deployment notification
6. Establishes daily loss limits ($100 max)
7. Logs full deployment audit trail

Circuit breakers:
- Pause if daily losses exceed $100
- Manual override capability for Already Here LLC
- Rollback to paper if needed
- 12% max drawdown circuit breaker
"""

import asyncio
import logging
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List
from decimal import Decimal
import os
import time
import hashlib
import uuid

from runtime.robinhood_integration import RobinhoodLiveTrader
from runtime.live_trading_safety import (
    LiveTradingSafetyGate,
    DeploymentApproval,
    DeploymentStatus
)
from runtime.gmail_client import send_email

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# DEPLOYMENT CONSTANTS
# ============================================================================
PAPER_TO_LIVE_THRESHOLD = Decimal("1000.00")
LIVE_CAPITAL_DEPLOYMENT = Decimal("500.00")
MAX_DAILY_LOSS = Decimal("100.00")
MAX_DRAWDOWN_PCT = Decimal("12.00")
MONITORING_INTERVAL = 1800  # Check every 30 minutes
CONFIRMATION_TIMEOUT = 3600 * 24 * 7  # 7 days to confirm


class LiveTradingTrigger:
    """Main system for monitoring paper -> live transitions"""

    def __init__(self, db_path: str = "clients.db"):
        self.db_path = db_path
        self.safety_gate = LiveTradingSafetyGate()
        self.running = False
        self.robinhood = None  # Lazy-initialized on first use

    def _get_db_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    async def start_monitoring(self):
        """Start the continuous monitoring loop"""
        logger.info("Starting Live Trading Trigger System...")
        self.running = True

        try:
            while self.running:
                await self.check_paper_trades_once()
                await asyncio.sleep(MONITORING_INTERVAL)
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Monitor loop error: {e}", exc_info=True)
        finally:
            self.running = False

    async def check_paper_trades_once(self):
        """Single check cycle for all users approaching or exceeding $1000"""
        try:
            conn = self._get_db_connection()
            cur = conn.cursor()

            # Find users with paper tier and recent trades >= $1000 balance
            cur.execute("""
                SELECT DISTINCT u.id, u.email, u.trading_tier,
                       MAX(dt.balance) as latest_balance
                FROM users u
                LEFT JOIN daily_trades dt ON u.id = dt.user_id
                WHERE u.trading_tier = 'paper'
                  AND dt.date >= date('now', '-7 days')
                GROUP BY u.id, u.email, u.trading_tier
                HAVING latest_balance >= ?
                ORDER BY u.id
            """, (PAPER_TO_LIVE_THRESHOLD,))

            ready_users = cur.fetchall()

            if ready_users:
                logger.info(f"Found {len(ready_users)} user(s) ready for live trading")
                for user in ready_users:
                    await self.process_user_deployment(
                        user_id=user['id'],
                        email=user['email'],
                        latest_balance=Decimal(str(user['latest_balance']))
                    )
            else:
                logger.debug("No users ready for deployment")

            conn.close()

        except Exception as e:
            logger.error(f"Error in check_paper_trades_once: {e}", exc_info=True)

    async def process_user_deployment(
        self,
        user_id: int,
        email: str,
        latest_balance: Decimal
    ):
        """Process potential deployment for a single user"""
        logger.info(f"Processing user {user_id} ({email}) | Balance: ${latest_balance}")

        # Step 1: Check if already in deployment flow
        deployment = self._get_active_deployment(user_id)
        if deployment:
            logger.info(f"User {user_id} already has active deployment: {deployment['status']}")

            # Check if confirmation timeout expired
            if deployment['status'] == 'pending_confirmation':
                created_at = datetime.fromisoformat(deployment['created_at'])
                if datetime.now() - created_at > timedelta(seconds=CONFIRMATION_TIMEOUT):
                    logger.warning(f"Deployment confirmation expired for user {user_id}")
                    self._update_deployment_status(
                        deployment['id'],
                        DeploymentStatus.CONFIRMATION_EXPIRED
                    )
            return

        # Step 2: Safety checks (account verified, 2FA enabled, etc.)
        is_safe, safety_reason = await self.safety_gate.verify_user_readiness(
            user_id=user_id,
            email=email,
            paper_balance=latest_balance
        )

        if not is_safe:
            logger.warning(f"Safety check failed for user {user_id}: {safety_reason}")
            self._log_deployment_attempt(
                user_id=user_id,
                status=DeploymentStatus.SAFETY_CHECK_FAILED,
                reason=safety_reason
            )
            return

        # Step 3: Create approval request (triggers confirmation email)
        approval = DeploymentApproval(
            user_id=user_id,
            email=email,
            approval_code=self._generate_approval_code(user_id),
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(seconds=CONFIRMATION_TIMEOUT),
            paper_balance=latest_balance,
            live_deployment_amount=LIVE_CAPITAL_DEPLOYMENT,
            max_daily_loss=MAX_DAILY_LOSS
        )

        # Step 4: Store deployment record
        deployment_id = self._create_deployment_record(approval)

        # Step 5: Send confirmation email
        await self._send_deployment_confirmation(approval, deployment_id)

        logger.info(
            f"Deployment initiated for user {user_id}: "
            f"approval_code={approval.approval_code[:8]}..., "
            f"expires={approval.expires_at}"
        )

    async def confirm_deployment(
        self,
        user_id: int,
        approval_code: str,
        two_fa_token: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        User confirms live trading deployment via email link or API.

        Args:
            user_id: User ID
            approval_code: 6-digit or token from email
            two_fa_token: Optional 2FA code

        Returns:
            (success, message)
        """
        logger.info(f"Confirming deployment for user {user_id}")

        # Verify approval code
        approval = self._get_active_approval(user_id, approval_code)
        if not approval:
            logger.warning(f"Invalid approval code for user {user_id}")
            return False, "Invalid or expired approval code"

        if datetime.now() > approval['expires_at']:
            logger.warning(f"Approval code expired for user {user_id}")
            self._update_deployment_status(
                approval['deployment_id'],
                DeploymentStatus.CONFIRMATION_EXPIRED
            )
            return False, "Approval code expired"

        # Step 1: Verify 2FA if enabled
        if two_fa_token and not await self._verify_2fa(user_id, two_fa_token):
            logger.warning(f"2FA verification failed for user {user_id}")
            return False, "2FA verification failed"

        # Step 2: Initialize Robinhood connection
        try:
            robinhood = RobinhoodLiveTrader(
                oauth_token=os.getenv("ROBINHOOD_OAUTH_TOKEN"),
                account_id=approval['robinhood_account_id']
            )
        except Exception as e:
            logger.error(f"Failed to initialize Robinhood for user {user_id}: {e}")
            self._update_deployment_status(
                approval['deployment_id'],
                DeploymentStatus.BROKER_CONNECTION_FAILED,
                reason=str(e)
            )
            return False, f"Broker connection failed: {e}"

        # Step 3: Deploy capital
        try:
            deposit_success = await robinhood.deposit_capital(
                amount=LIVE_CAPITAL_DEPLOYMENT
            )

            if not deposit_success:
                raise Exception("Deposit confirmation failed from broker")

            logger.info(f"Capital deposited for user {user_id}: ${LIVE_CAPITAL_DEPLOYMENT}")

        except Exception as e:
            logger.error(f"Capital deployment failed for user {user_id}: {e}")
            self._update_deployment_status(
                approval['deployment_id'],
                DeploymentStatus.CAPITAL_DEPLOYMENT_FAILED,
                reason=str(e)
            )
            return False, f"Capital deployment failed: {e}"

        # Step 4: Update user tier to LIVE
        try:
            self._update_user_tier(user_id, "live")
            logger.info(f"User {user_id} tier updated to LIVE")
        except Exception as e:
            logger.error(f"Failed to update user tier for {user_id}: {e}")
            return False, f"Tier update failed: {e}"

        # Step 5: Initialize live account tracking
        try:
            self._initialize_live_account(
                user_id=user_id,
                robinhood_account_id=approval['robinhood_account_id'],
                deployment_amount=LIVE_CAPITAL_DEPLOYMENT,
                daily_loss_limit=MAX_DAILY_LOSS,
                max_drawdown_pct=MAX_DRAWDOWN_PCT
            )
            logger.info(f"Live account initialized for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to initialize live account for {user_id}: {e}")
            return False, f"Live account init failed: {e}"

        # Step 6: Update deployment status
        self._update_deployment_status(
            approval['deployment_id'],
            DeploymentStatus.LIVE_ACTIVE,
            reason="Capital deployed and account switched to LIVE tier"
        )

        # Step 7: Send success confirmation
        await self._send_deployment_success_email(
            user_id=user_id,
            email=approval['email'],
            deployment_amount=LIVE_CAPITAL_DEPLOYMENT,
            account_id=approval['robinhood_account_id']
        )

        logger.info(f"Live trading deployment COMPLETE for user {user_id}")
        return True, "Live trading deployment confirmed and activated"

    async def pause_live_trading(
        self,
        user_id: int,
        reason: str = "Manual override"
    ) -> bool:
        """Pause live trading for a user (e.g., circuit breaker or admin action)"""
        logger.warning(f"Pausing live trading for user {user_id}: {reason}")

        try:
            conn = self._get_db_connection()
            cur = conn.cursor()

            # Update live account status
            cur.execute("""
                UPDATE live_accounts
                SET status = 'paused', paused_at = ?, pause_reason = ?
                WHERE user_id = ? AND status = 'active'
            """, (datetime.now().isoformat(), reason, user_id))

            conn.commit()
            conn.close()

            # Send pause notification
            user = self._get_user(user_id)
            if user:
                await self._send_pause_notification(user['email'], reason)

            return True
        except Exception as e:
            logger.error(f"Failed to pause live trading for user {user_id}: {e}")
            return False

    async def resume_live_trading(self, user_id: int) -> bool:
        """Resume paused live trading"""
        logger.info(f"Resuming live trading for user {user_id}")

        try:
            conn = self._get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                UPDATE live_accounts
                SET status = 'active', paused_at = NULL, pause_reason = NULL
                WHERE user_id = ? AND status = 'paused'
            """, (user_id,))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Failed to resume live trading for user {user_id}: {e}")
            return False

    async def rollback_to_paper(
        self,
        user_id: int,
        reason: str = "User requested"
    ) -> bool:
        """Rollback user from LIVE back to PAPER tier"""
        logger.warning(f"Rolling back user {user_id} to paper: {reason}")

        try:
            conn = self._get_db_connection()
            cur = conn.cursor()

            # Get live account data
            cur.execute("""
                SELECT robinhood_account_id, deployment_amount, current_balance
                FROM live_accounts
                WHERE user_id = ?
            """, (user_id,))

            live_account = cur.fetchone()
            if not live_account:
                logger.error(f"No live account found for user {user_id}")
                return False

            # Withdraw remaining capital
            try:
                robinhood = RobinhoodLiveTrader(
                    oauth_token=os.getenv("ROBINHOOD_OAUTH_TOKEN"),
                    account_id=live_account['robinhood_account_id']
                )
                await robinhood.withdraw_capital(
                    amount=Decimal(str(live_account['current_balance']))
                )
            except Exception as e:
                logger.warning(f"Failed to withdraw capital: {e}")
                # Continue with rollback even if withdrawal fails

            # Close live account
            cur.execute("""
                UPDATE live_accounts
                SET status = 'closed', closed_at = ?, closure_reason = ?
                WHERE user_id = ?
            """, (datetime.now().isoformat(), reason, user_id))

            # Revert tier to PAPER
            cur.execute("""
                UPDATE users
                SET trading_tier = 'paper', updated_at = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), user_id))

            # Log rollback event
            cur.execute("""
                INSERT INTO deployment_events (
                    user_id, event_type, event_data, created_at
                ) VALUES (?, 'rollback', ?, ?)
            """, (
                user_id,
                json.dumps({"reason": reason, "withdrawn_amount": str(live_account['current_balance'])}),
                datetime.now().isoformat()
            ))

            conn.commit()
            conn.close()

            # Send notification
            user = self._get_user(user_id)
            if user:
                await self._send_rollback_notification(user['email'], reason)

            logger.info(f"Rollback complete for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Rollback failed for user {user_id}: {e}", exc_info=True)
            return False

    # ========================================================================
    # INTERNAL HELPERS & DATABASE METHODS
    # ========================================================================

    def _get_active_deployment(self, user_id: int) -> Optional[Dict]:
        """Get active deployment for user"""
        try:
            conn = self._get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT * FROM deployments
                WHERE user_id = ? AND status IN ('pending_confirmation', 'in_progress', 'live_active')
                ORDER BY created_at DESC LIMIT 1
            """, (user_id,))
            row = cur.fetchone()
            conn.close()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting active deployment: {e}")
            return None

    def _get_active_approval(self, user_id: int, approval_code: str) -> Optional[Dict]:
        """Get active approval matching code"""
        try:
            conn = self._get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT d.*, da.approval_code, da.robinhood_account_id
                FROM deployments d
                JOIN deployment_approvals da ON d.id = da.deployment_id
                WHERE d.user_id = ? AND da.approval_code = ?
                  AND d.status = 'pending_confirmation'
                  AND da.expires_at > ?
                LIMIT 1
            """, (user_id, approval_code, datetime.now().isoformat()))
            row = cur.fetchone()
            conn.close()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting active approval: {e}")
            return None

    def _create_deployment_record(self, approval: DeploymentApproval) -> int:
        """Create deployment record in database"""
        try:
            conn = self._get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO deployments (
                    user_id, email, status, paper_balance, deployment_amount,
                    max_daily_loss, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                approval.user_id,
                approval.email,
                DeploymentStatus.PENDING_CONFIRMATION,
                str(approval.paper_balance),
                str(approval.live_deployment_amount),
                str(approval.max_daily_loss),
                approval.created_at.isoformat(),
                approval.created_at.isoformat()
            ))

            deployment_id = cur.lastrowid

            # Store approval record
            cur.execute("""
                INSERT INTO deployment_approvals (
                    deployment_id, approval_code, expires_at, robinhood_account_id
                ) VALUES (?, ?, ?, ?)
            """, (
                deployment_id,
                approval.approval_code,
                approval.expires_at.isoformat(),
                approval.robinhood_account_id or ""
            ))

            conn.commit()
            conn.close()

            return deployment_id
        except Exception as e:
            logger.error(f"Error creating deployment record: {e}")
            raise

    def _update_deployment_status(
        self,
        deployment_id: int,
        status: str,
        reason: Optional[str] = None
    ):
        """Update deployment status"""
        try:
            conn = self._get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                UPDATE deployments
                SET status = ?, updated_at = ?, status_reason = ?
                WHERE id = ?
            """, (status, datetime.now().isoformat(), reason, deployment_id))

            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error updating deployment status: {e}")

    def _log_deployment_attempt(
        self,
        user_id: int,
        status: str,
        reason: str
    ):
        """Log deployment attempt"""
        try:
            conn = self._get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO deployment_events (
                    user_id, event_type, event_data, created_at
                ) VALUES (?, 'deployment_attempt', ?, ?)
            """, (
                user_id,
                json.dumps({"status": status, "reason": reason}),
                datetime.now().isoformat()
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error logging deployment attempt: {e}")

    def _update_user_tier(self, user_id: int, tier: str):
        """Update user trading tier"""
        try:
            conn = self._get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                UPDATE users
                SET trading_tier = ?, updated_at = ?
                WHERE id = ?
            """, (tier, datetime.now().isoformat(), user_id))

            # Also update upsell_tracking
            cur.execute("""
                UPDATE upsell_tracking
                SET current_tier = ?, updated_at = ?
                WHERE user_id = ?
            """, (tier, datetime.now().isoformat(), user_id))

            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error updating user tier: {e}")
            raise

    def _initialize_live_account(
        self,
        user_id: int,
        robinhood_account_id: str,
        deployment_amount: Decimal,
        daily_loss_limit: Decimal,
        max_drawdown_pct: Decimal
    ):
        """Initialize live account tracking"""
        try:
            conn = self._get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO live_accounts (
                    user_id, robinhood_account_id, deployment_amount, current_balance,
                    daily_loss_limit, max_drawdown_pct, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?)
            """, (
                user_id,
                robinhood_account_id,
                str(deployment_amount),
                str(deployment_amount),
                str(daily_loss_limit),
                str(max_drawdown_pct),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error initializing live account: {e}")
            raise

    def _get_user(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        try:
            conn = self._get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cur.fetchone()
            conn.close()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None

    def _generate_approval_code(self, user_id: int) -> str:
        """Generate unique approval code (6 digits)"""
        seed = f"{user_id}{datetime.now().isoformat()}{uuid.uuid4()}"
        hash_obj = hashlib.sha256(seed.encode())
        return str(int(hash_obj.hexdigest(), 16) % 1000000).zfill(6)

    async def _verify_2fa(self, user_id: int, token: str) -> bool:
        """Verify 2FA token (placeholder - implement with actual 2FA service)"""
        # TODO: Implement actual 2FA verification
        logger.debug(f"2FA verification placeholder for user {user_id}")
        return True

    async def _send_deployment_confirmation(
        self,
        approval: DeploymentApproval,
        deployment_id: int
    ):
        """Send confirmation email to user"""
        confirmation_link = (
            f"https://profitengine.app/live-confirm?"
            f"deployment_id={deployment_id}&code={approval.approval_code}"
        )

        body_html = f"""
        <html><body style='font-family:sans-serif;color:#333;max-width:600px;margin:auto'>
        <h2 style='color:#00aa55'>ProfitEngine — Live Trading Ready!</h2>

        <p>Congratulations! Your paper trading account has reached <strong>${approval.paper_balance}</strong>.</p>

        <p>We're ready to deploy <strong>${approval.live_deployment_amount}</strong> in real capital to your live Robinhood account.</p>

        <h3 style='color:#00aa55;margin-top:24px'>Deployment Details</h3>
        <ul style='line-height:1.8;font-size:14px'>
            <li><strong>Paper Balance:</strong> ${approval.paper_balance}</li>
            <li><strong>Live Capital Deployment:</strong> ${approval.live_deployment_amount}</li>
            <li><strong>Daily Loss Limit:</strong> ${approval.max_daily_loss} (circuit breaker)</li>
            <li><strong>Max Drawdown:</strong> 12% (auto-pause)</li>
            <li><strong>This offer expires:</strong> {approval.expires_at.strftime('%Y-%m-%d %H:%M UTC')}</li>
        </ul>

        <h3 style='color:#00aa55;margin-top:24px'>What You Need</h3>
        <ol style='line-height:1.8;font-size:14px'>
            <li>Verified Robinhood account (ID + address verification)</li>
            <li>2-Factor Authentication enabled</li>
            <li>Funding source verified (bank account or wire)</li>
        </ol>

        <h3 style='color:#00aa55;margin-top:24px'>Confirm Your Deployment</h3>
        <p style='font-size:14px'>
            <a href='{confirmation_link}'
               style='background:#00aa55;color:white;padding:12px 24px;text-decoration:none;
                      border-radius:4px;display:inline-block;font-weight:bold'>
                Confirm Live Trading Deployment
            </a>
        </p>

        <p style='font-size:12px;color:#999;margin-top:24px'>
            Or enter this code manually: <code style='background:#f5f5f5;padding:4px 8px'>{approval.approval_code}</code>
        </p>

        <hr style='border:none;border-top:1px solid #eee;margin:32px 0'>
        <p style='font-size:12px;color:#666'>
            <strong>Important:</strong> By confirming, you authorize:
            <br>- Deposit of ${approval.live_deployment_amount} to your Robinhood account
            <br>- Real money trading with live market prices
            <br>- Daily loss limits and risk gates enforcement
            <br>- Access to your account for compliance monitoring
        </p>

        <p style='font-size:12px;color:#666'>
            Questions? Reply to this email or contact support@alreadyherellc.com
        </p>
        </body></html>
        """

        send_email(
            subject="Confirm: Deploy $500 Live Capital to Your Trading Account",
            body_html=body_html,
            to=approval.email
        )
        logger.info(f"Confirmation email sent to {approval.email}")

    async def _send_deployment_success_email(
        self,
        user_id: int,
        email: str,
        deployment_amount: Decimal,
        account_id: str
    ):
        """Send deployment success notification"""
        body_html = f"""
        <html><body style='font-family:sans-serif;color:#333;max-width:600px;margin:auto'>
        <h2 style='color:#00aa55'>Live Trading Activated!</h2>

        <p>Your live trading account is now active with <strong>${deployment_amount}</strong> in real capital.</p>

        <h3 style='color:#00aa55;margin-top:24px'>Account Details</h3>
        <ul style='line-height:1.8;font-size:14px;background:#f9f9f9;padding:16px;border-radius:4px'>
            <li><strong>Account ID:</strong> {account_id}</li>
            <li><strong>Live Capital:</strong> ${deployment_amount}</li>
            <li><strong>Daily Loss Limit:</strong> $100 (auto-pause if exceeded)</li>
            <li><strong>Max Drawdown:</strong> 12% (circuit breaker)</li>
            <li><strong>Status:</strong> <span style='color:#00aa55;font-weight:bold'>ACTIVE</span></li>
        </ul>

        <h3 style='color:#00aa55;margin-top:24px'>Next Steps</h3>
        <ol style='line-height:1.8;font-size:14px'>
            <li><a href='https://profitengine.app/dashboard'>View live dashboard</a></li>
            <li>Monitor your positions in real-time</li>
            <li>Check daily P&L and risk metrics</li>
            <li>Set up SMS alerts if needed</li>
        </ol>

        <h3 style='color:#00aa55;margin-top:24px'>Safety Features Active</h3>
        <ul style='line-height:1.8;font-size:14px'>
            <li>✓ Daily loss limit: $100/day</li>
            <li>✓ Drawdown circuit breaker: 12%</li>
            <li>✓ Position size limits enforced</li>
            <li>✓ Audit trail: all trades logged</li>
            <li>✓ Manual override: admin can pause anytime</li>
        </ul>

        <hr style='border:none;border-top:1px solid #eee;margin:32px 0'>
        <p style='font-size:12px;color:#666'>
            For support or issues: support@alreadyherellc.com
        </p>
        </body></html>
        """

        send_email(
            subject="Your Live Trading Account is Active",
            body_html=body_html,
            to=email
        )
        logger.info(f"Success email sent to {email}")

    async def _send_pause_notification(self, email: str, reason: str):
        """Send pause notification"""
        body_html = f"""
        <html><body style='font-family:sans-serif;color:#333;max-width:600px;margin:auto'>
        <h2 style='color:#ff6600'>Live Trading Paused</h2>

        <p>Your live trading account has been paused.</p>
        <p><strong>Reason:</strong> {reason}</p>

        <p style='margin-top:16px'>
            <a href='https://profitengine.app/dashboard'
               style='background:#ff6600;color:white;padding:12px 24px;text-decoration:none;
                      border-radius:4px;display:inline-block;font-weight:bold'>
                View Dashboard
            </a>
        </p>
        </body></html>
        """

        send_email(
            subject="Live Trading Paused",
            body_html=body_html,
            to=email
        )

    async def _send_rollback_notification(self, email: str, reason: str):
        """Send rollback notification"""
        body_html = f"""
        <html><body style='font-family:sans-serif;color:#333;max-width:600px;margin:auto'>
        <h2 style='color:#ff6600'>Rolled Back to Paper Trading</h2>

        <p>Your account has been rolled back to paper trading mode.</p>
        <p><strong>Reason:</strong> {reason}</p>

        <p style='margin-top:16px'>
            Your capital will be withdrawn from your Robinhood account within 3-5 business days.
        </p>
        </body></html>
        """

        send_email(
            subject="Account Rolled Back to Paper Trading",
            body_html=body_html,
            to=email
        )


async def main():
    """Run the trigger system"""
    trigger = LiveTradingTrigger()
    await trigger.start_monitoring()


if __name__ == "__main__":
    asyncio.run(main())
