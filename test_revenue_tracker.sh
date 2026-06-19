#!/bin/bash
# Test script for revenue tracker

echo "========================================"
echo "Revenue Tracker - Full Feature Test"
echo "========================================"
echo ""

echo "[1] Adding sample revenue entries..."
python3 scripts/revenue_tracker.py --action add --channel newsletter --amount 200 --description "Email sponsor - June week 1" 2>&1 | grep -i "ok\|error"
python3 scripts/revenue_tracker.py --action add --channel newsletter --amount 150 --description "Email sponsor - June week 2" 2>&1 | grep -i "ok\|error"
python3 scripts/revenue_tracker.py --action add --channel gumroad --amount 320 --description "Ebook bundle: Trading + Investing" 2>&1 | grep -i "ok\|error"
python3 scripts/revenue_tracker.py --action add --channel printify --amount 650 --description "T-shirt & hoodie sales" 2>&1 | grep -i "ok\|error"
python3 scripts/revenue_tracker.py --action add --channel affiliate --amount 145.75 --description "Amazon Associates commissions" 2>&1 | grep -i "ok\|error"

echo ""
echo "[2] Displaying revenue dashboard..."
python3 scripts/revenue_tracker.py --action dashboard

echo ""
echo "[3] Exporting JSON report..."
python3 scripts/revenue_tracker.py --action export --output test_report.json 2>&1 | grep -i "ok\|error"

echo ""
echo "[4] JSON Report Preview (first 40 lines)..."
head -40 test_report.json

echo ""
echo "[5] Test complete!"
echo "========================================"
