# Proof of Performance — Quick Reference

Fast guide to extracting marketing data from ProfitEngine.

---

## 30-Second Setup

```bash
cd /app
python runtime/proof_of_performance.py
```

**Output:** See all metrics printed to console + saves JSON reports.

---

## One-Liner Usage

### Get today's metrics
```python
from runtime.proof_of_performance import ProofOfPerformance
pof = ProofOfPerformance()
metrics = pof.generate_daily_metrics()
print(f"Win Rate: {metrics.overall_win_rate}% | P&L: ${metrics.total_pnl_generated:,.0f}")
```

### Validate claims
```python
claims = pof.validate_all_claims()
for c in claims:
    print(f"{'✓' if c.validated else '✗'} {c.claim}: {c.actual_value}")
```

### Get top 3 performers
```python
stories = pof.get_top_performers(days=30, limit=3)
for s in stories:
    print(f"{s.email}: {s.roi_percentage:.0f}% ROI, {s.win_rate:.0f}% win rate")
```

### Check for milestones
```python
milestones = pof.check_milestones()
for m in milestones:
    print(f"🎉 {m.description}")
```

### Export PDF
```python
metrics = pof.generate_daily_metrics()
pdf = pof.export_pdf(metrics, "deck.pdf")
```

---

## Common Questions

### Q: What's the win rate TODAY?
```python
metrics = pof.generate_daily_metrics()
print(metrics.overall_win_rate)  # Returns float like 87.2
```

### Q: How much P&L did we generate?
```python
print(f"${metrics.total_pnl_generated:,.2f}")
```

### Q: Can we claim "90%+ win rate"?
```python
claim = pof.validate_claim_win_rate(90.0)
if claim.validated:
    print("YES - Use in marketing!")
else:
    print(f"NO - We're at {claim.actual_value}%")
```

### Q: Who are our best customers?
```python
top = pof.get_top_performers(30, 10)
for i, s in enumerate(top, 1):
    print(f"{i}. {s.email} - {s.roi_percentage}% ROI")
```

### Q: Did we hit any milestones?
```python
milestones = pof.check_milestones()
if milestones:
    for m in milestones:
        print(f"Press release ready: {m.press_release_ready}")
```

### Q: How do we compare to competitors?
```python
comp = pof.generate_competitive_report()
print(comp["win_rate_comparison"])
```

### Q: What's our conversion funnel?
```python
dash = pof.get_marketing_dashboard()
funnel = dash["conversion_funnel"]
print(f"Signups → Active: {funnel['conversion_signups_to_active']:.0f}%")
print(f"Active → Paying: {funnel['conversion_active_to_paying']:.0f}%")
```

### Q: What should we tell the board?
```python
report = pof.generate_investor_report()
print(report["executive_summary"])
```

---

## Marketing Copy Templates

### For Sales Pages
> "Our system achieves **87%+ win rates** consistently, with average customers seeing **24% ROI** in their first month."

**Where to get:** `metrics.overall_win_rate`, `metrics.average_customer_roi`

### For Testimonials
> "I turned my $10,000 into $24,530 in just 45 days with a 87.5% win rate. No manual trading. Completely autonomous."

**Where to get:** `top_performers[0]` (email with permission)

### For Twitter/LinkedIn
> "Just hit 245 customers with an average 87% win rate. $1.2M total P&L generated. Zero manual intervention. This is what autonomous trading looks like. 🚀"

**Where to get:** `metrics.total_users`, `metrics.overall_win_rate`, `metrics.total_pnl_generated`

### For Email Subject Lines
> "How one trader turned $1K into $12K in 30 days"
> 
> "87% win rate: Here's our secret"
> 
> "See the real results: Our top customer made $24K profit"

**Where to get:** Top performers data

### For Press Release
> ProfitEngine announced today that the system has generated over $1 million in total P&L across its customer base, with an average win rate of 87% and zero manual interventions required.

**Where to get:** Milestones, `metrics.total_pnl_generated`, `metrics.overall_win_rate`

---

## Daily Checklist

```
□ Run: python runtime/proof_of_performance.py
□ Check: Are any metrics > 0?
□ Check: Are any claims validated?
□ Check: Any new milestones?
□ Share: Email report to stakeholders
□ Archive: Save daily_report_*.json
```

---

## Files & Folders

| Path | Contains |
|------|----------|
| `runtime/proof_of_performance.py` | Main system (run this) |
| `runtime/daily_metrics_scheduler.py` | Daily automation |
| `.github/workflows/daily-metrics.yml` | GitHub Actions trigger |
| `runtime/metrics_reports/` | Generated reports (JSON, PDF) |
| `runtime/metrics_history/` | Historical snapshots (for trends) |
| `runtime/metrics_scheduler.log` | Execution log |

---

## Automated Daily Report

The GitHub Actions workflow runs daily at **6 PM MST** and:

1. ✓ Generates all metrics
2. ✓ Validates all claims
3. ✓ Exports PDFs
4. ✓ Sends email digest
5. ✓ Saves to repo
6. ✓ Creates artifacts

**No manual action needed.**

---

## Dataclass Quick Reference

### PerformanceMetrics
```python
metrics.timestamp              # str: "2026-06-18"
metrics.total_users            # int: 245
metrics.active_users           # int: 156
metrics.overall_win_rate       # float: 87.2
metrics.total_pnl_generated    # float: 1234567.89
metrics.total_pnl_percentage   # float: 2.34
metrics.average_customer_roi   # float: 24.3
metrics.uptime_percentage      # float: 99.9
metrics.customer_growth_rate   # float: 12.5
```

### PerformanceClaim
```python
claim.claim                    # str: "90%+ win rate"
claim.validated                # bool: True/False
claim.actual_value             # float: 87.2
claim.target_value             # float: 90.0
claim.evidence                 # List[str]: Proof points
claim.example_users            # List[Dict]: Real examples
```

### CustomerStory
```python
story.email                    # str: "user@example.com"
story.tier                     # str: "Pro"
story.roi_percentage           # float: 245.3
story.total_pnl_generated      # float: 24530.00
story.win_rate                 # float: 87.5
story.days_active              # int: 45
story.best_day                 # float: 2100.50
story.worst_day                # float: -450.25
```

### Milestone
```python
milestone.milestone_type       # str: "customer", "revenue", "pnl", "win_rate"
milestone.achieved_date        # str: "2026-06-15"
milestone.description          # str: "100th customer signed up"
milestone.value                # float: 100.0
milestone.press_release_ready  # bool: True
milestone.proof                # List[str]: Evidence
```

---

## Pro Tips

1. **Daily metrics auto-save** → Check `runtime/metrics_history/` for trends
2. **Export to PDF** → Great for presentations/board meetings
3. **Share investor report** → Use `generate_investor_report()` monthly
4. **Get examples** → `example_users` field has real customer data
5. **Track trends** → Use `get_metrics_trend(days=14)` for growth charts
6. **Validate before claiming** → Always use `validate_*()` methods
7. **Anonymize for public** → Replace emails with "Customer #1" etc.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `FileNotFoundError: clients.db` | Run `python scripts/init-clients-db.py` |
| Empty metrics (all zeros) | Add test data to database |
| PDF export fails | `pip install reportlab` |
| Wrong date/time | Check system timezone |
| Email not sent | Verify SMTP secrets in GitHub |

---

## Next Steps

1. **Run daily report:** `python runtime/proof_of_performance.py`
2. **Check output:** `cat runtime/metrics_reports/daily_report_*.json`
3. **Use in marketing:** Copy metrics to sales deck
4. **Set up automation:** Ensure `.github/workflows/daily-metrics.yml` is enabled
5. **Share with team:** Email `metrics@profitengine.ai` list

---

## Examples

### Quick Fact-Check
```python
pof = ProofOfPerformance()
metrics = pof.generate_daily_metrics()

# Can we say "industry-leading win rate"?
if metrics.overall_win_rate >= 80:
    print(f"YES! We're at {metrics.overall_win_rate}%")
```

### Build Funnel Chart
```python
dash = pof.get_marketing_dashboard()
funnel = dash["conversion_funnel"]

stages = [
    ("Signups", funnel["total_signups"]),
    ("Active (30d)", funnel["active_traders_30d"]),
    ("Paying", funnel["paying_customers"]),
    ("Profitable", funnel["profitable_customers"])
]

for stage, count in stages:
    print(f"{stage}: {count}")
```

### Find Testimonial Candidate
```python
stories = pof.get_top_performers(days=30, limit=1)
top = stories[0]

testimonial = f"""
I started with ${top.starting_balance:,.0f} and grew it to 
${top.current_balance:,.0f} — a {top.roi_percentage:.0f}% return 
in {top.days_active} days with a {top.win_rate:.0f}% win rate. 
Completely hands-off trading.
"""
print(testimonial)
```

---

**Last updated:** 2026-06-18
**Version:** 1.0.0
