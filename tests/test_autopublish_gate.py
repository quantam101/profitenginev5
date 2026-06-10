import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "autopublish_gate.py"
CAMPAIGN = REPO_ROOT / "campaigns" / "referrals" / "acorns-2026-06-09.json"


def run_gate(channel: str, as_of: str, campaign: Path = CAMPAIGN) -> dict:
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--campaign",
            str(campaign),
            "--channel",
            channel,
            "--as-of",
            as_of,
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(result.stdout)


def test_gate_blocks_public_publish_during_warmup():
    decision = run_gate("owned_website_news", "2026-06-09")

    assert decision["mode"] == "generate_queue_review"
    assert decision["publish_allowed"] is False
    assert decision["external_inference_allowed"] is False
    assert any("Warmup mode active" in reason for reason in decision["reasons"])


def test_gate_allows_supervised_publish_after_start_date():
    decision = run_gate("owned_website_news", "2026-06-23")

    assert decision["mode"] == "supervised_autopublish"
    assert decision["publish_allowed"] is True
    assert decision["external_inference_allowed"] is True


def test_gate_blocks_unknown_channel():
    decision = run_gate("random_unapproved_channel", "2026-06-23")

    assert decision["mode"] == "blocked"
    assert decision["publish_allowed"] is False
    assert "Channel is not allowlisted." in decision["reasons"]


def test_gate_blocks_explicitly_blocked_channel():
    decision = run_gate("cold_dm", "2026-06-23")

    assert decision["mode"] == "blocked"
    assert decision["publish_allowed"] is False
    assert any("Cold direct messaging" in reason for reason in decision["reasons"])


def test_gate_blocks_financial_referral_without_disclosure(tmp_path):
    campaign = json.loads(CAMPAIGN.read_text(encoding="utf-8"))
    campaign["risk_controls"] = {}
    campaign["primary_copy"] = "Small steps build real momentum."
    campaign["short_copy"] = "Start small and stay consistent."
    temp_campaign = tmp_path / "campaign.json"
    temp_campaign.write_text(json.dumps(campaign), encoding="utf-8")

    decision = run_gate("owned_website_news", "2026-06-23", temp_campaign)

    assert decision["mode"] == "blocked"
    assert decision["publish_allowed"] is False
    assert any("missing required disclosure" in reason for reason in decision["reasons"])


def test_gate_blocks_guaranteed_claim_language(tmp_path):
    campaign = json.loads(CAMPAIGN.read_text(encoding="utf-8"))
    campaign["primary_copy"] = "This is a guaranteed return opportunity."
    temp_campaign = tmp_path / "campaign.json"
    temp_campaign.write_text(json.dumps(campaign), encoding="utf-8")

    decision = run_gate("owned_website_news", "2026-06-23", temp_campaign)

    assert decision["mode"] == "blocked"
    assert decision["publish_allowed"] is False
    assert any("guaranteed-outcome" in reason for reason in decision["reasons"])
