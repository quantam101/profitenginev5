"""
UPSELL INTELLIGENCE — Integration Examples & Usage Guide
Demonstrates how to integrate upsell scoring into sales automation workflows.
"""

from datetime import datetime, timedelta
from decimal import Decimal
import json
import sqlite3
from pathlib import Path

from upsell_intelligence import (
    UpsellScorer,
    generate_daily_upsell_report,
    export_campaign_csv,
    UpsellTier,
    ClientMetrics,
)


# ============================================================================
# EXAMPLE 1: SETUP — Create Test Database with Sample Clients
# ============================================================================
def example_01_setup_test_database():
    """
    Initialize demo database with sample trading clients for testing.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Setup Test Database with Sample Clients")
    print("=" * 80)

    db_path = "test_clients.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables
    cursor.execute("""
        DROP TABLE IF EXISTS trades
    """)
    cursor.execute("""
        DROP TABLE IF EXISTS daily_snapshots
    """)
    cursor.execute("""
        DROP TABLE IF EXISTS clients
    """)

    cursor.execute("""
        CREATE TABLE clients (
            client_id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT,
            account_balance REAL NOT NULL,
            total_trades INTEGER DEFAULT 0,
            winning_trades INTEGER DEFAULT 0,
            losing_trades INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_trade_at TIMESTAMP,
            subscription_tier TEXT DEFAULT 'free'
        )
    """)

    cursor.execute("""
        CREATE TABLE trades (
            trade_id TEXT PRIMARY KEY,
            client_id TEXT NOT NULL,
            symbol TEXT,
            side TEXT,
            entry_price REAL,
            exit_price REAL,
            shares INTEGER,
            pnl_usd REAL,
            win BOOLEAN,
            executed_at TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(client_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE daily_snapshots (
            snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT NOT NULL,
            balance REAL,
            trade_count INTEGER,
            daily_pnl REAL,
            captured_at TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(client_id)
        )
    """)

    # Insert sample clients
    sample_clients = [
        ("client_001", "alice_trader", "alice@example.com", 10000.0),
        ("client_002", "bob_scalper", "bob@example.com", 25000.0),
        ("client_003", "charlie_swing", "charlie@example.com", 5000.0),
        ("client_004", "diana_pro", "diana@example.com", 50000.0),
        ("client_005", "eve_newbie", "eve@example.com", 1000.0),
    ]

    for client_id, username, email, balance in sample_clients:
        now = datetime.now()
        created_at = now - timedelta(days=30)
        cursor.execute(
            """
            INSERT INTO clients
            (client_id, username, email, account_balance, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (client_id, username, email, balance, created_at.isoformat()),
        )

    conn.commit()

    # Insert sample trades for each client
    trades_data = {
        "client_001": [  # Alice: 88% win rate (high performer)
            (1.25, True, -5),
            (2.50, True, -4),
            (-1.00, False, -3),
            (3.75, True, -2),
            (1.50, True, -1),
            (2.00, True, 0),
            (1.75, True, 1),
        ],
        "client_002": [  # Bob: 90% win rate (exceptional)
            (5.00, True, -5),
            (7.50, True, -4),
            (2.25, True, -3),
            (-3.00, False, -2),
            (8.00, True, -1),
            (6.00, True, 0),
            (4.50, True, 1),
            (5.75, True, 2),
            (3.00, True, 3),
            (6.25, True, 4),
        ],
        "client_003": [  # Charlie: 50% win rate (mediocre)
            (0.50, True, -4),
            (-2.00, False, -3),
            (1.00, True, -2),
            (-1.50, False, -1),
            (0.75, True, 0),
            (-0.50, False, 1),
            (1.25, True, 2),
        ],
        "client_004": [  # Diana: 86% win rate (enterprise candidate)
            (10.00, True, -6),
            (15.00, True, -5),
            (8.50, True, -4),
            (-5.00, False, -3),
            (12.00, True, -2),
            (18.00, True, -1),
            (14.00, True, 0),
            (20.00, True, 1),
            (11.00, True, 2),
            (16.50, True, 3),
        ],
        "client_005": [  # Eve: 40% win rate (new, struggling)
            (-5.00, False, -3),
            (2.00, True, -2),
            (-3.00, False, -1),
            (1.00, True, 0),
            (-2.00, False, 1),
        ],
    }

    for client_id, trades in trades_data.items():
        for idx, (pnl, win, days_offset) in enumerate(trades):
            trade_id = f"{client_id}_trade_{idx:03d}"
            executed_at = datetime.now() + timedelta(days=days_offset)
            cursor.execute(
                """
                INSERT INTO trades
                (trade_id, client_id, symbol, side, entry_price, exit_price, shares, pnl_usd, win, executed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    trade_id,
                    client_id,
                    "AAPL",
                    "BUY",
                    150.0,
                    150.0 + (pnl / 100),
                    100,
                    pnl,
                    win,
                    executed_at.isoformat(),
                ),
            )

    conn.commit()

    # Insert daily snapshots for balance tracking
    for client_id, _, _, initial_balance in sample_clients:
        for days_ago in range(7, -1, -1):
            snapshot_date = datetime.now() - timedelta(days=days_ago)
            # Simulate balance growth
            growth_factor = 1.0 + (0.05 * ((7 - days_ago) / 7))  # 5% growth over 7 days
            balance = initial_balance * growth_factor
            cursor.execute(
                """
                INSERT INTO daily_snapshots
                (client_id, balance, trade_count, daily_pnl, captured_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (client_id, balance, 5, 2.50, snapshot_date.isoformat()),
            )

    conn.commit()
    conn.close()

    print(f"[OK] Test database created: {db_path}")
    print(f"[OK] Inserted {len(sample_clients)} sample clients with trading history")
    print()


# ============================================================================
# EXAMPLE 2: BASIC SCORING — Run Daily Upsell Report
# ============================================================================
def example_02_basic_scoring():
    """
    Generate daily upsell report and display key metrics.
    """
    print("=" * 80)
    print("EXAMPLE 2: Run Daily Upsell Scoring")
    print("=" * 80)

    report = generate_daily_upsell_report("test_clients.db")

    print(f"\nReport Generated: {report['generated_at']}")
    print(f"Total Clients Analyzed: {report['total_clients']}")
    print(f"Total Pipeline Value: ${report['pipeline_value_usd']:,.2f}")
    print()

    print(f"TIER BREAKDOWN:")
    print(f"  Enterprise Tier:   {report['enterprise_count']} clients")
    print(f"  White-Label Tier:  {report['white_label_count']} clients")
    print(f"  Hybrid Tier:       {report['hybrid_count']} clients")
    print()

    # Show enterprise candidates (highest value)
    if report["enterprise_candidates"]:
        print("TOP ENTERPRISE CANDIDATES:")
        for i, cand in enumerate(report["enterprise_candidates"], 1):
            print(
                f"  {i}. {cand['username']} (#{cand['priority_rank']})"
                f" | Score: {cand['base_score']:.1f}/100"
                f" | Est. Value: ${cand['estimated_upsell_value_usd']:.2f}/year"
            )
        print()

    # Show white-label candidates
    if report["white_label_candidates"]:
        print("TOP WHITE-LABEL CANDIDATES:")
        for i, cand in enumerate(report["white_label_candidates"][:3], 1):
            print(
                f"  {i}. {cand['username']} (#{cand['priority_rank']})"
                f" | Score: {cand['base_score']:.1f}/100"
                f" | Est. Value: ${cand['estimated_upsell_value_usd']:.2f}/year"
            )
        if len(report["white_label_candidates"]) > 3:
            print(f"  ... and {len(report['white_label_candidates']) - 3} more")
        print()

    # Show hybrid candidates
    if report["hybrid_candidates"]:
        print("TOP HYBRID CANDIDATES:")
        for i, cand in enumerate(report["hybrid_candidates"][:3], 1):
            print(
                f"  {i}. {cand['username']} (#{cand['priority_rank']})"
                f" | Score: {cand['base_score']:.1f}/100"
                f" | Est. Value: ${cand['estimated_upsell_value_usd']:.2f}/year"
            )
        if len(report["hybrid_candidates"]) > 3:
            print(f"  ... and {len(report['hybrid_candidates']) - 3} more")
        print()


# ============================================================================
# EXAMPLE 3: DETAILED BREAKDOWN — Inspect Individual Client Scoring
# ============================================================================
def example_03_detailed_scoring():
    """
    Show detailed scoring breakdown for a specific high-value client.
    """
    print("=" * 80)
    print("EXAMPLE 3: Detailed Scoring Breakdown (Enterprise Candidate)")
    print("=" * 80)

    scorer = UpsellScorer("test_clients.db")
    campaign = scorer.score_all_clients()

    if not campaign.enterprise_candidates:
        print("No enterprise candidates in test database.")
        return

    top_enterprise = campaign.enterprise_candidates[0]

    print(f"\nCLIENT: {top_enterprise.username}")
    print(f"Client ID: {top_enterprise.client_id}")
    print(f"Priority Rank: #{top_enterprise.priority_rank}")
    print()

    print("SCORE BREAKDOWN:")
    print(
        f"  Win Rate Component:    {top_enterprise.win_rate_score:6.1f} / 25 pts"
        f" ({(top_enterprise.win_rate_score/25*100):5.1f}%)"
    )
    print(
        f"  Balance Growth:        {top_enterprise.growth_score:6.1f} / 25 pts"
        f" ({(top_enterprise.growth_score/25*100):5.1f}%)"
    )
    print(
        f"  Consistency:           {top_enterprise.consistency_score:6.1f} / 25 pts"
        f" ({(top_enterprise.consistency_score/25*100):5.1f}%)"
    )
    print(
        f"  Engagement:            {top_enterprise.engagement_score:6.1f} / 25 pts"
        f" ({(top_enterprise.engagement_score/25*100):5.1f}%)"
    )
    print("-" * 60)
    print(f"  TOTAL SCORE:           {top_enterprise.base_score:6.1f} / 100 pts")
    print()

    print(f"TIER RECOMMENDATION: {top_enterprise.tier_recommendation.value.upper()}")
    print(
        f"ESTIMATED ANNUAL VALUE: ${top_enterprise.estimated_upsell_value_usd:,.2f}"
    )
    print()

    print("SCORING SIGNALS:")
    for signal, message in top_enterprise.signals:
        print(f"  [OK] {signal.value}: {message}")
    print()

    print("PERSONALIZED SALES MESSAGE:")
    print("-" * 60)
    print(top_enterprise.sales_message)
    print("-" * 60)
    print()


# ============================================================================
# EXAMPLE 4: EXPORT FOR SALES TEAM — Generate CSV Campaign File
# ============================================================================
def example_04_export_campaign():
    """
    Export scoring results to CSV for sales team CRM import.
    """
    print("=" * 80)
    print("EXAMPLE 4: Export Campaign to CSV")
    print("=" * 80)

    scorer = UpsellScorer("test_clients.db")
    campaign = scorer.score_all_clients()

    export_path = "upsell_campaign_example.csv"
    export_campaign_csv(campaign, export_path)

    print(f"\n[OK] Campaign exported to {export_path}")
    print(f"  Rows: {len(campaign.enterprise_candidates) + len(campaign.white_label_candidates) + len(campaign.hybrid_candidates)}")
    print(f"  Ready for: Salesforce, HubSpot, or custom CRM import")
    print()


# ============================================================================
# EXAMPLE 5: INTEGRATION WITH DAILY CRON — Automated Sales Outreach
# ============================================================================
def example_05_daily_cron_integration():
    """
    Shows how to integrate upsell scoring into automated daily cron job.
    Suitable for scheduler: cron, APScheduler, or GitHub Actions.
    """
    print("=" * 80)
    print("EXAMPLE 5: Daily Cron Integration Pattern")
    print("=" * 80)

    example_code = """
    # File: scripts/daily_upsell_cron.py
    # Run via: python scripts/daily_upsell_cron.py
    # Cron job: 0 8 * * * cd /app && python scripts/daily_upsell_cron.py

    from datetime import datetime
    from runtime.upsell_intelligence import generate_daily_upsell_report, export_campaign_csv
    import json
    import os

    def main():
        db_path = os.getenv("CLIENTS_DB_PATH", "clients.db")

        # Generate report
        report = generate_daily_upsell_report(db_path)

        # Log results
        print(f"[{datetime.now()}] Upsell Report Generated")
        print(f"  Total clients: {report['total_clients']}")
        print(f"  Enterprise: {report['enterprise_count']}")
        print(f"  White-Label: {report['white_label_count']}")
        print(f"  Hybrid: {report['hybrid_count']}")
        print(f"  Pipeline value: ${report['pipeline_value_usd']:,.2f}")

        # Export CSV
        export_campaign_csv(report_to_campaign(report))

        # Send to sales team via email/Slack/API
        # send_to_sales_team(report)

        # Store in S3 for dashboard
        # upload_to_s3(json.dumps(report))

    if __name__ == "__main__":
        main()
    """

    print(example_code)
    print()


# ============================================================================
# EXAMPLE 6: INTEGRATION WITH FAST API — REST Endpoint
# ============================================================================
def example_06_fastapi_integration():
    """
    Shows how to add upsell scoring as FastAPI REST endpoint.
    """
    print("=" * 80)
    print("EXAMPLE 6: FastAPI REST Endpoint Integration")
    print("=" * 80)

    example_code = """
    # Add to runtime/api.py or create runtime/upsell_api.py

    from fastapi import FastAPI, Query
    from runtime.upsell_intelligence import (
        UpsellScorer,
        generate_daily_upsell_report
    )

    app = FastAPI()

    @app.get("/api/sales/upsell-report")
    async def get_upsell_report(
        tier: str = Query(None, description="Filter by tier: enterprise, white_label, hybrid")
    ):
        "\"\"Get daily upsell campaign report"\"\"
        report = generate_daily_upsell_report()

        if tier == "enterprise":
            return report["enterprise_candidates"]
        elif tier == "white_label":
            return report["white_label_candidates"]
        elif tier == "hybrid":
            return report["hybrid_candidates"]

        return report

    @app.get("/api/sales/pipeline-value")
    async def get_pipeline_value():
        "\"\"Get total upsell pipeline value"\"\"
        report = generate_daily_upsell_report()
        return {
            "total_pipeline_usd": report["pipeline_value_usd"],
            "generated_at": report["generated_at"]
        }

    # Usage:
    # curl http://localhost:8000/api/sales/upsell-report
    # curl http://localhost:8000/api/sales/upsell-report?tier=enterprise
    # curl http://localhost:8000/api/sales/pipeline-value
    """

    print(example_code)
    print()


# ============================================================================
# EXAMPLE 7: INTEGRATION WITH EMAIL CAMPAIGN — Send Daily Digest to Sales
# ============================================================================
def example_07_email_campaign_integration():
    """
    Shows how to send daily upsell report via email to sales team.
    """
    print("=" * 80)
    print("EXAMPLE 7: Daily Email Campaign Integration")
    print("=" * 80)

    example_code = """
    # File: runtime/upsell_email_service.py

    from datetime import datetime
    from runtime.upsell_intelligence import generate_daily_upsell_report
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    def send_daily_upsell_email(sales_team_email: str):
        "\"\"Generate report and email to sales team"\"\"
        report = generate_daily_upsell_report()

        # Build HTML email
        html_body = f\"\"\"
        <h2>Daily Upsell Campaign Report</h2>
        <p><strong>Generated:</strong> {report['generated_at']}</p>
        <hr/>

        <h3>Pipeline Overview</h3>
        <ul>
            <li>Total Clients: {report['total_clients']}</li>
            <li>Total Pipeline Value: ${report['pipeline_value_usd']:,.2f}</li>
        </ul>

        <h3>Enterprise Candidates ({report['enterprise_count']})</h3>
        <ul>
        \"\"\"

        for cand in report["enterprise_candidates"]:
            html_body += f\"\"\"
            <li>
                <strong>{cand['username']}</strong>
                | Score: {cand['base_score']:.1f}/100
                | Est. Value: ${cand['estimated_upsell_value_usd']:.2f}/year
            </li>
            \"\"\"

        html_body += \"\"\"</ul>\"\"\"

        # Send email
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Upsell Campaign Report - {datetime.now().strftime('%Y-%m-%d')}"
        msg["From"] = "noreply@profitengine.com"
        msg["To"] = sales_team_email
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login("your-email@gmail.com", "your-app-password")
            server.send_message(msg)

        print(f"[OK] Email sent to {sales_team_email}")

    # Usage:
    # send_daily_upsell_email("sales@alreadyherellc.com")
    """

    print(example_code)
    print()


# ============================================================================
# EXAMPLE 8: SCORING METRICS REFERENCE — What Each Score Means
# ============================================================================
def example_08_scoring_reference():
    """
    Reference guide for interpreting upsell scores.
    """
    print("=" * 80)
    print("EXAMPLE 8: Scoring Metrics Reference")
    print("=" * 80)

    reference = """
    UPSELL SCORING SYSTEM (0-100 Points)

    ┌─────────────────────────────────────────────────────────────────────┐
    │ COMPONENT SCORES (0-25 each)                                        │
    ├─────────────────────────────────────────────────────────────────────┤
    │                                                                     │
    │ 1. WIN RATE SCORE (0-25)                                            │
    │    └─ >= 85% win rate: 25 pts (Enterprise-ready)                   │
    │    └─ >= 70% win rate: 20 pts (Hybrid-ready)                       │
    │    └─ 50-70% win rate: Partial credit (0-15 pts)                   │
    │    └─ < 50% win rate: 0 pts (Not ready)                            │
    │                                                                     │
    │ 2. BALANCE GROWTH SCORE (0-25)                                      │
    │    └─ >= 50% growth in 7 days: 25 pts (High-value)                │
    │    └─ 25-50% growth: 12-24 pts (Good trajectory)                   │
    │    └─ < 25% growth: 0-11 pts (Slow growth)                         │
    │    └─ Negative growth: 0 pts (Losing money)                        │
    │                                                                     │
    │ 3. CONSISTENCY SCORE (0-25)                                         │
    │    └─ >= 5 consecutive winning days: 25 pts (Very consistent)      │
    │    └─ 3-4 consecutive winning days: 15-20 pts (Consistent)         │
    │    └─ 1-2 consecutive winning days: 5-10 pts (Choppy)              │
    │    └─ 0 consecutive winning days: 0 pts (Losing streak)            │
    │                                                                     │
    │ 4. ENGAGEMENT SCORE (0-25)                                          │
    │    └─ >= 10 trades/day average: 25 pts (High-volume)              │
    │    └─ 5-10 trades/day: 10-20 pts (Active)                          │
    │    └─ 1-5 trades/day: 3-9 pts (Low activity)                       │
    │    └─ < 1 trade/day: 0 pts (Dormant)                               │
    │                                                                     │
    └─────────────────────────────────────────────────────────────────────┘

    TIER THRESHOLDS:

    ENTERPRISE TIER (Minimum 85/100):
    ├─ Win rate >= 85%
    ├─ Consistency score >= 15/25
    ├─ Engagement score >= 15/25
    └─ Annual fee: 1.5% AUM

    WHITE-LABEL TIER (Minimum 50/100):
    ├─ Win rate >= 70%
    ├─ Base score >= 50/100
    └─ Annual fee: 1.0% AUM

    HYBRID TIER (Minimum 70% win rate):
    ├─ Win rate >= 70%
    └─ Annual fee: 0.50% AUM

    FREE TIER:
    └─ Win rate < 70%

    ESTIMATED ANNUAL VALUE CALCULATION:

    Enterprise: Account Balance * 1.5% = Annual Revenue
    White-Label: Account Balance * 1.0% = Annual Revenue
    Hybrid: Account Balance * 0.50% = Annual Revenue

    Example:
    ├─ Diana with $50,000 account and 86% win rate (Enterprise):
    │   └─ Annual Value = $50,000 * 1.5% = $750/year
    │
    └─ Alice with $10,000 account and 70% win rate (Hybrid):
        └─ Annual Value = $10,000 * 0.5% = $50/year
    """

    print(reference)
    print()


# ============================================================================
# MAIN: Run All Examples
# ============================================================================
if __name__ == "__main__":
    print("\n")
    print("=" * 80)
    print("PROFITENGINE UPSELL INTELLIGENCE")
    print("Integration Examples & Usage Guide")
    print("=" * 80)
    print("=" * 80)
    print()

    # Run examples in sequence
    example_01_setup_test_database()
    example_02_basic_scoring()
    example_03_detailed_scoring()
    example_04_export_campaign()
    example_05_daily_cron_integration()
    example_06_fastapi_integration()
    example_07_email_campaign_integration()
    example_08_scoring_reference()

    print("=" * 80)
    print("All examples completed!")
    print("=" * 80)
    print()
