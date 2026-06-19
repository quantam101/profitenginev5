#!/usr/bin/env python3
"""
DAILY METRICS SCHEDULER
=======================
Runs daily at 6 PM MST to generate and export all proof-of-performance metrics.

Performs:
1. Generate daily system metrics
2. Validate all marketing claims
3. Identify customer success stories
4. Check for milestone achievements
5. Update competitive analysis
6. Export reports and PDFs
7. Generate email digest for stakeholders

Requires:
- clients.db populated with real trading data
- reportlab (optional) for PDF export

Usage:
    # Run manually
    python runtime/daily_metrics_scheduler.py

    # Run scheduled via cron/GitHub Actions
    0 18 * * * cd /app && python runtime/daily_metrics_scheduler.py
"""

import logging
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

try:
    from proof_of_performance import ProofOfPerformance
except ImportError:
    from runtime.proof_of_performance import ProofOfPerformance

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path(__file__).parent / "metrics_scheduler.log")
    ]
)
logger = logging.getLogger(__name__)


class MetricsScheduler:
    """Orchestrates daily metrics generation and delivery."""

    def __init__(self):
        """Initialize scheduler."""
        self.pof = ProofOfPerformance()
        self.reports_dir = Path(__file__).parent / "metrics_reports"
        self.reports_dir.mkdir(exist_ok=True)
        logger.info(f"MetricsScheduler initialized. Reports dir: {self.reports_dir}")

    def run_daily_report(self) -> Dict[str, Any]:
        """
        Generate complete daily report package.

        Returns:
            Dictionary with all report sections
        """
        logger.info("Starting daily metrics report generation...")
        report_date = datetime.now().strftime("%Y-%m-%d")

        try:
            # 1. Generate daily metrics
            logger.info("Generating daily metrics...")
            metrics = self.pof.generate_daily_metrics()
            logger.info(f"Daily metrics: Win Rate {metrics.overall_win_rate:.1f}%, "
                       f"P&L ${metrics.total_pnl_generated:,.2f}, Users {metrics.total_users}")

            # 2. Validate claims
            logger.info("Validating marketing claims...")
            claims = self.pof.validate_all_claims()
            validated_claims = {
                claim.claim: {
                    "validated": claim.validated,
                    "actual": claim.actual_value,
                    "target": claim.target_value,
                    "evidence": claim.evidence
                }
                for claim in claims
            }

            # 3. Get success stories
            logger.info("Identifying top performers...")
            top_performers = self.pof.get_top_performers(30, 10)
            success_stories = [
                {
                    "email": perf.email,
                    "roi": perf.roi_percentage,
                    "total_pnl": perf.total_pnl_generated,
                    "win_rate": perf.win_rate,
                    "days_active": perf.days_active,
                    "starting_balance": perf.starting_balance,
                    "current_balance": perf.current_balance
                }
                for perf in top_performers
            ]

            # 4. Check milestones
            logger.info("Checking for milestone achievements...")
            milestones = self.pof.check_milestones()
            milestone_list = [
                {
                    "type": m.milestone_type,
                    "date": m.achieved_date,
                    "description": m.description,
                    "value": m.value,
                    "ready_for_press": m.press_release_ready
                }
                for m in milestones
            ]

            # 5. Competitive analysis
            logger.info("Generating competitive analysis...")
            competitive = self.pof.generate_competitive_report()

            # 6. Marketing dashboard
            logger.info("Compiling marketing dashboard...")
            dashboard = self.pof.get_marketing_dashboard()

            # 7. Compile full report
            full_report = {
                "report_date": report_date,
                "generated_at": datetime.now().isoformat(),
                "metrics": {
                    "date": metrics.timestamp,
                    "total_users": metrics.total_users,
                    "active_users": metrics.active_users,
                    "total_trades": metrics.total_trades,
                    "total_wins": metrics.total_wins,
                    "total_losses": metrics.total_losses,
                    "win_rate": metrics.overall_win_rate,
                    "total_pnl": metrics.total_pnl_generated,
                    "total_pnl_pct": metrics.total_pnl_percentage,
                    "avg_roi": metrics.average_customer_roi,
                    "uptime": metrics.uptime_percentage,
                    "customer_growth": metrics.customer_growth_rate,
                    "free": metrics.free_users,
                    "basic": metrics.basic_users,
                    "pro": metrics.pro_users,
                    "elite": metrics.elite_users
                },
                "validated_claims": validated_claims,
                "success_stories": success_stories,
                "milestones": milestone_list,
                "competitive_advantage": competitive,
                "marketing_dashboard": dashboard
            }

            # 8. Save report
            self._save_report(full_report)

            # 9. Export PDFs
            logger.info("Exporting PDF reports...")
            self._export_reports(metrics)

            # 10. Generate email digest
            logger.info("Generating email digest...")
            email_content = self._generate_email_digest(full_report, metrics)

            logger.info("Daily metrics report completed successfully")
            return {
                "success": True,
                "report": full_report,
                "email_content": email_content
            }

        except Exception as e:
            logger.error(f"Error generating daily report: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    def _save_report(self, report: Dict[str, Any]):
        """Save report to JSON file."""
        report_date = report["report_date"]
        filepath = self.reports_dir / f"daily_report_{report_date}.json"

        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Report saved to {filepath}")

    def _export_reports(self, metrics):
        """Export various report formats."""
        report_date = metrics.timestamp

        # PDF export
        pdf_filename = f"proof_of_performance_{report_date}.pdf"
        try:
            pdf_path = self.pof.export_pdf(metrics, pdf_filename)
            logger.info(f"PDF exported: {pdf_path}")
        except Exception as e:
            logger.warning(f"PDF export failed: {e}. Continuing with JSON.")

        # Investor report
        try:
            investor_report = self.pof.generate_investor_report()
            filepath = self.reports_dir / f"investor_report_{report_date}.json"
            with open(filepath, 'w') as f:
                json.dump(investor_report, f, indent=2, default=str)
            logger.info(f"Investor report saved: {filepath}")
        except Exception as e:
            logger.error(f"Investor report export failed: {e}")

    def _generate_email_digest(self, report: Dict[str, Any], metrics) -> str:
        """
        Generate HTML email digest for stakeholders.

        Returns:
            HTML email content
        """
        metrics_data = report["metrics"]
        claims = report["validated_claims"]
        stories = report["success_stories"][:3]  # Top 3

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; color: #333; }}
                .header {{ background-color: #1f77b4; color: white; padding: 20px; }}
                .section {{ margin: 20px 0; padding: 15px; border-left: 4px solid #1f77b4; }}
                .metric {{ display: inline-block; margin: 10px 20px 10px 0; }}
                .metric-value {{ font-size: 24px; font-weight: bold; color: #1f77b4; }}
                .metric-label {{ font-size: 12px; color: #666; }}
                table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                th {{ background-color: #aec7e8; padding: 10px; text-align: left; }}
                td {{ padding: 8px; border-bottom: 1px solid #ddd; }}
                .success {{ color: #28a745; font-weight: bold; }}
                .warning {{ color: #ffc107; font-weight: bold; }}
                .footer {{ text-align: center; font-size: 12px; color: #999; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>ProfitEngine v5 - Daily Metrics Report</h1>
                <p>{report['report_date']}</p>
            </div>

            <div class="section">
                <h2>Key Metrics Summary</h2>
                <div class="metric">
                    <div class="metric-label">System Win Rate</div>
                    <div class="metric-value">{metrics_data['win_rate']:.1f}%</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Total P&L</div>
                    <div class="metric-value">${metrics_data['total_pnl']:,.0f}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Total Users</div>
                    <div class="metric-value">{metrics_data['total_users']}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Active Users (7d)</div>
                    <div class="metric-value">{metrics_data['active_users']}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Total Trades</div>
                    <div class="metric-value">{metrics_data['total_trades']}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Uptime</div>
                    <div class="metric-value">{metrics_data['uptime']:.1f}%</div>
                </div>
            </div>

            <div class="section">
                <h2>Performance Claims Validation</h2>
                <table>
                    <tr>
                        <th>Claim</th>
                        <th>Status</th>
                        <th>Actual vs Target</th>
                    </tr>
        """

        for claim, data in claims.items():
            status = '<span class="success">✓ VALID</span>' if data['validated'] else '<span class="warning">⚠ UNMET</span>'
            html += f"""
                    <tr>
                        <td>{claim}</td>
                        <td>{status}</td>
                        <td>{data['actual']:.1f} / {data['target']:.1f}</td>
                    </tr>
            """

        html += """
                </table>
            </div>

            <div class="section">
                <h2>Top Performers (Marketing Stories)</h2>
                <table>
                    <tr>
                        <th>Email</th>
                        <th>ROI</th>
                        <th>Total P&L</th>
                        <th>Win Rate</th>
                        <th>Days Active</th>
                    </tr>
        """

        for story in stories:
            html += f"""
                    <tr>
                        <td>{story['email']}</td>
                        <td>{story['roi']:.1f}%</td>
                        <td>${story['total_pnl']:,.2f}</td>
                        <td>{story['win_rate']:.1f}%</td>
                        <td>{story['days_active']}</td>
                    </tr>
            """

        html += """
                </table>
            </div>

            <div class="section">
                <h2>Tier Breakdown</h2>
                <table>
                    <tr>
                        <th>Tier</th>
                        <th>Count</th>
                        <th>% of Total</th>
                    </tr>
        """

        total = (metrics_data['free'] + metrics_data['basic'] +
                 metrics_data['pro'] + metrics_data['elite'])
        for tier, count in [('Free', metrics_data['free']),
                            ('Basic', metrics_data['basic']),
                            ('Pro', metrics_data['pro']),
                            ('Elite', metrics_data['elite'])]:
            pct = (count / total * 100) if total > 0 else 0
            html += f"""
                    <tr>
                        <td>{tier}</td>
                        <td>{count}</td>
                        <td>{pct:.1f}%</td>
                    </tr>
            """

        html += """
                </table>
            </div>

            <div class="footer">
                <p>This report was automatically generated by ProfitEngine's Proof of Performance system.</p>
                <p>All data sourced from real client.db with no vanity metrics.</p>
            </div>
        </body>
        </html>
        """

        return html

    def send_email_digest(self, report_result: Dict[str, Any], recipients: List[str]):
        """
        Send email digest to stakeholders.

        Args:
            report_result: Result from run_daily_report()
            recipients: List of email addresses
        """
        if not report_result.get("success"):
            logger.error("Skipping email send - report generation failed")
            return False

        # Email configuration (from environment)
        sender = os.getenv("METRICS_EMAIL_SENDER", "metrics@profitengine.ai")
        smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER")
        smtp_pass = os.getenv("SMTP_PASSWORD")

        if not smtp_user or not smtp_pass:
            logger.warning("Email credentials not configured. Skipping email send.")
            return False

        try:
            email_html = report_result["email_content"]
            report_date = report_result["report"]["report_date"]

            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"ProfitEngine Daily Report - {report_date}"
            msg["From"] = sender

            # Attach HTML content
            msg.attach(MIMEText(email_html, "html"))

            # Send to each recipient
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)

                for recipient in recipients:
                    msg["To"] = recipient
                    server.send_message(msg)
                    logger.info(f"Report sent to {recipient}")

            return True

        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False


def main():
    """Run daily metrics generation."""
    logger.info("=" * 60)
    logger.info("DAILY METRICS SCHEDULER - STARTING")
    logger.info("=" * 60)

    scheduler = MetricsScheduler()

    # Generate report
    result = scheduler.run_daily_report()

    if not result["success"]:
        logger.error(f"Report generation failed: {result.get('error')}")
        return 1

    # Get email recipients from environment
    recipients = os.getenv("METRICS_EMAIL_RECIPIENTS", "").split(",")
    recipients = [r.strip() for r in recipients if r.strip()]

    if recipients:
        logger.info(f"Sending report to {len(recipients)} recipients...")
        scheduler.send_email_digest(result, recipients)
    else:
        logger.info("No email recipients configured. Report saved locally.")

    # Print summary to stdout
    metrics = result["report"]["metrics"]
    print("\n" + "=" * 60)
    print("DAILY METRICS REPORT - SUMMARY")
    print("=" * 60)
    print(f"Date: {result['report']['report_date']}")
    print(f"\nSystem Performance:")
    print(f"  Win Rate: {metrics['win_rate']:.1f}%")
    print(f"  Total P&L: ${metrics['total_pnl']:,.2f}")
    print(f"  Total Trades: {metrics['total_trades']}")
    print(f"  Uptime: {metrics['uptime']:.1f}%")
    print(f"\nUser Metrics:")
    print(f"  Total Users: {metrics['total_users']}")
    print(f"  Active Users: {metrics['active_users']}")
    print(f"  Free: {metrics['free']} | Basic: {metrics['basic']} | "
          f"Pro: {metrics['pro']} | Elite: {metrics['elite']}")
    print(f"\nAverage ROI: {metrics['avg_roi']:.1f}%")
    print(f"Customer Growth: {result['report']['metrics'].get('customer_growth', 0):.1f}%")
    print("\n" + "=" * 60)

    logger.info("Daily metrics scheduler completed successfully")
    return 0


if __name__ == "__main__":
    exit(main())
