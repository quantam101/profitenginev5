#!/bin/bash
# Quick-start script for Proof of Performance system
# Run: ./run_metrics.sh

set -e

echo "=========================================="
echo "ProfitEngine Metrics System"
echo "=========================================="
echo

# Check Python
echo "✓ Checking Python..."
python3 --version || { echo "✗ Python 3 not found"; exit 1; }

# Check database
echo "✓ Checking database..."
if [ ! -f "clients.db" ]; then
    echo "  Warning: clients.db not found"
    echo "  Run: python scripts/init-clients-db.py"
else
    USERS=$(sqlite3 clients.db "SELECT COUNT(*) FROM users;" 2>/dev/null || echo "0")
    TRADES=$(sqlite3 clients.db "SELECT COUNT(*) FROM daily_trades;" 2>/dev/null || echo "0")
    echo "  Users: $USERS"
    echo "  Trades: $TRADES"
fi

# Run metrics
echo
echo "=========================================="
echo "Generating metrics report..."
echo "=========================================="
echo

python runtime/proof_of_performance.py

echo
echo "=========================================="
echo "✓ Success!"
echo "=========================================="
echo
echo "Reports saved to:"
echo "  - runtime/metrics_reports/daily_report_*.json"
echo "  - runtime/metrics_reports/investor_report_*.json"
echo "  - runtime/metrics_history/metrics_*.json"
echo
echo "Next steps:"
echo "  1. Check reports: cat runtime/metrics_reports/daily_report_*.json | jq ."
echo "  2. Share with team: tail runtime/metrics_scheduler.log"
echo "  3. Set up automation: .github/workflows/daily-metrics.yml"
echo
echo "For help: cat runtime/PROOF_OF_PERFORMANCE_QUICKREF.md"
