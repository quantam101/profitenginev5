from __future__ import annotations

from runtime.opportunity_intelligence import OpportunityInput, OpportunityIntelligenceEngine, OpportunityStore


def test_low_margin_large_format_tv_routes_to_counter(tmp_path):
    engine = OpportunityIntelligenceEngine(store=OpportunityStore(tmp_path / "oi.db"))
    evaluation = engine.evaluate(
        OpportunityInput(
            source_platform="Field Nation",
            source_url="fieldnation://work-order/19309797",
            raw_text="WO #19309797 TV Parts Swap 85-inch display helper parts Maricopa AZ fixed $85",
            wo_number="19309797",
            client="ITI - Indusys Technology, Inc.",
            location="Maricopa, AZ 85138",
            schedule="Sat Jun 13 8:00 AM",
            pay_text="$85 fixed",
            work_type="TV Parts Swap",
            distance_miles=43,
            buyer_message="Can you assist? Please put in your request or counter.",
        )
    )

    assert evaluation.decision == "COUNTER"
    assert evaluation.grade == "C"
    assert evaluation.minimum_acceptable_total >= 175
    assert "large_format_display" in evaluation.risk_flags
    assert "below_minimum_dispatch_value" in evaluation.risk_flags
    assert "Stephen Franklin" in evaluation.pitch.counter_message


def test_high_value_network_support_routes_to_proceed(tmp_path):
    engine = OpportunityIntelligenceEngine(store=OpportunityStore(tmp_path / "oi.db"))
    evaluation = engine.evaluate(
        OpportunityInput(
            source_platform="WorkMarket",
            source_url="workmarket://assignment/active-network-01",
            raw_text="Network support smart hands AP wireless troubleshooting Phoenix AZ $260 2 hours clear scope",
            location="Phoenix, AZ 85004",
            schedule="Tomorrow 10:00 AM",
            pay_text="$260 fixed",
            work_type="Network Support",
            distance_miles=12,
        )
    )

    assert evaluation.decision == "PROCEED"
    assert evaluation.grade in {"A", "B"}
    assert evaluation.estimated_effective_hourly == 130.0


def test_feedback_loop_updates_local_keyword_weights(tmp_path):
    store = OpportunityStore(tmp_path / "oi.db")
    engine = OpportunityIntelligenceEngine(store=store)
    evaluation = engine.evaluate(
        OpportunityInput(
            source_platform="Field Nation",
            source_url="fieldnation://work-order/feedback-network-01",
            raw_text="Network AP wireless support Mesa AZ $220 2 hours",
            location="Mesa, AZ 85201",
            pay_text="$220",
            work_type="Network AP Wireless",
            distance_miles=9,
        )
    )

    before = store.get_weight("keyword:network", 1.0)
    deltas = store.register_outcome(evaluation.signature, "INTERVIEW_SECURED")
    after = store.get_weight("keyword:network", 1.0)

    assert deltas
    assert after > before
