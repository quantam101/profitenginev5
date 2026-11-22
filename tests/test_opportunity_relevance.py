"""Regression cases for high-signal, fail-closed IT opportunity intake."""
from __future__ import annotations

from runtime.opportunity_relevance import assess_relevance
from runtime.agent_impls.proposal_optimizer import stable_source_key
from runtime.opportunity_intelligence import (
    OpportunityInput, OpportunityIntelligenceEngine, OpportunityStore,
)


def test_generic_it_and_ap_substrings_do_not_establish_scope():
    item = assess_relevance("It is available to apply for an apartment loan.")
    assert not item.accepted
    assert item.matched == ()


def test_network_marketing_is_not_msp_work():
    item = assess_relevance("Network marketing sales representative, $350 today")
    assert not item.accepted
    assert "network_marketing" in item.reasons


def test_explicit_field_service_scope_is_high_relevance():
    item = assess_relevance(
        "Install 10 Aruba wireless access points, terminate Cat6 cabling "
        "and test VLAN connectivity in Phoenix."
    )
    assert item.accepted
    assert item.score >= 60
    assert "wifi" in item.matched
    assert "structured_cabling" in item.matched


def test_tv_parts_swap_is_technical_but_not_automatically_profitable():
    assert assess_relevance("85-inch TV parts swap and display repair").accepted


def test_off_topic_is_discarded_before_review_or_proposal(tmp_path):
    eng = OpportunityIntelligenceEngine(store=OpportunityStore(tmp_path / "scope.db"))
    result = eng.evaluate(OpportunityInput(
        source_platform="WorkMarket",
        source_url="workmarket://offtopic-001",
        raw_text="Apply today: credit repair sales agent. Earn $800 per day.",
        location="Phoenix, AZ",
        pay_text="$800",
        work_type="Sales",
        distance_miles=3,
    ), persist=False)
    assert result.grade == "Avoid"
    assert result.decision == "DISCARD"
    assert "off_topic_scope" in result.risk_flags
    assert result.score <= 30
    assert not result.pitch.generated_cover_letter


def test_viable_network_job_still_passes_existing_price_gate(tmp_path):
    eng = OpportunityIntelligenceEngine(store=OpportunityStore(tmp_path / "viable.db"))
    result = eng.evaluate(OpportunityInput(
        source_platform="WorkMarket",
        source_url="workmarket://network-2026",
        raw_text="Network troubleshooting, wireless access points and smart hands",
        location="Phoenix, AZ",
        pay_text="$260 fixed",
        work_type="Network Support",
        distance_miles=8,
    ), persist=False)
    assert result.grade in {"A", "B"}
    assert result.decision == "PROCEED"


def test_repeated_terms_do_not_inflate_relevance():
    single = assess_relevance("network")
    repeated = assess_relevance("network " * 100)
    assert single.score == repeated.score


def test_proposal_source_id_stable_across_calls_and_changes_with_input():
    first = stable_source_key("network support", "Phoenix, AZ")
    assert first == stable_source_key("network support", "Phoenix, AZ")
    assert first != stable_source_key("printer support", "Phoenix, AZ")
    assert len(first) == 24
