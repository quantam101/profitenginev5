from runtime.asi_engine_adapter import score_revenue_signal


def test_asi_adapter_keeps_500_floor():
    decision = score_revenue_signal(
        {
            "company": "Phoenix MSP",
            "title": "Server smart hands outage",
            "location": "Phoenix, AZ",
            "service_type": "server_smart_hands",
            "fixed_pay": 500,
            "estimated_travel_minutes": 20,
            "estimated_onsite_minutes": 120,
            "retainer_potential": True,
        }
    )
    assert decision.grade == "A"
    assert decision.expected_revenue == 500
    assert decision.approval_required is True


def test_asi_adapter_rejects_low_pay_travel():
    decision = score_revenue_signal(
        {
            "company": "Distant Buyer",
            "title": "LTE test",
            "location": "Flagstaff, AZ",
            "service_type": "network_support",
            "listed_rate": 65,
            "max_hours": 2,
            "estimated_travel_minutes": 240,
            "estimated_onsite_minutes": 90,
        }
    )
    assert decision.grade == "AVOID"
    assert "travel_burden" in decision.risk_flags
    assert decision.target_rate >= 450
