#!/usr/bin/env python3
"""Deterministic ProfitEngine autopublish gate.

This script does not publish content. It decides whether a campaign is blocked,
queue-only, or eligible for supervised autopublish under the local policy files.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

DEFAULT_ALLOWLIST = Path("ops/autopublish/channel-allowlist.json")
DEFAULT_AUTOPUBLISH_START = date(2026, 6, 23)
FINANCIAL_REFERRAL_TYPES = {"referral_financial"}
REFERRAL_TYPES = {"referral_financial", "affiliate"}


@dataclass(frozen=True)
class GateDecision:
    campaign_id: str
    campaign_type: str
    channel: str
    as_of: str
    mode: str
    publish_allowed: bool
    external_inference_allowed: bool
    reasons: list[str]
    required_next_action: str

    def to_json(self) -> str:
        return json.dumps(self.__dict__, indent=2, sort_keys=True)


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def parse_date(value: str | None) -> date:
    if not value:
        return date.today()
    return date.fromisoformat(value)


def get_channel_config(allowlist: dict[str, Any], channel: str) -> tuple[dict[str, Any] | None, str | None]:
    channels = allowlist.get("channels", {})
    if channel in channels:
        return channels[channel], None

    blocked_channels = allowlist.get("blocked_channels", {})
    if channel in blocked_channels:
        return None, blocked_channels[channel].get("reason", "Channel is blocked.")

    return None, "Channel is not allowlisted."


def requires_disclosure(campaign_type: str, channel_config: dict[str, Any]) -> bool:
    return campaign_type in REFERRAL_TYPES and bool(channel_config.get("requires_disclosure_for_referral", False))


def campaign_has_required_disclosure(campaign: dict[str, Any]) -> bool:
    controls = campaign.get("risk_controls", {})
    primary_copy = str(campaign.get("primary_copy", "")).lower()
    short_copy = str(campaign.get("short_copy", "")).lower()
    return bool(controls.get("requires_referral_disclosure", False)) or "referral" in primary_copy or "referral" in short_copy


def has_forbidden_claims(campaign: dict[str, Any]) -> bool:
    text = " ".join(
        str(campaign.get(key, ""))
        for key in ["primary_copy", "short_copy", "campaign_type"]
    ).lower()
    forbidden_fragments = [
        "guaranteed return",
        "guaranteed income",
        "risk-free profit",
        "no risk investment",
        "guaranteed investment",
    ]
    return any(fragment in text for fragment in forbidden_fragments)


def decide(campaign: dict[str, Any], allowlist: dict[str, Any], channel: str, as_of: date) -> GateDecision:
    campaign_id = str(campaign.get("campaign_id", "unknown-campaign"))
    campaign_type = str(campaign.get("campaign_type", "unknown"))
    reasons: list[str] = []

    channel_config, channel_block_reason = get_channel_config(allowlist, channel)
    if channel_config is None:
        return GateDecision(
            campaign_id=campaign_id,
            campaign_type=campaign_type,
            channel=channel,
            as_of=as_of.isoformat(),
            mode="blocked",
            publish_allowed=False,
            external_inference_allowed=False,
            reasons=[channel_block_reason or "Channel unavailable."],
            required_next_action="Choose an allowlisted channel or update the channel allowlist intentionally.",
        )

    if not channel_config.get("enabled", False):
        reasons.append("Channel is disabled.")

    allowed_campaign_types = set(channel_config.get("allowed_campaign_types", []))
    if campaign_type not in allowed_campaign_types:
        reasons.append(f"Campaign type '{campaign_type}' is not allowed on channel '{channel}'.")

    if requires_disclosure(campaign_type, channel_config) and not campaign_has_required_disclosure(campaign):
        reasons.append("Referral/affiliate campaign is missing required disclosure controls.")

    if has_forbidden_claims(campaign):
        reasons.append("Campaign contains blocked guaranteed-outcome language.")

    channel_start = parse_date(channel_config.get("allow_autopublish_after"))
    policy_start = parse_date(allowlist.get("supervised_autopublish_starts", DEFAULT_AUTOPUBLISH_START.isoformat()))
    effective_start = max(channel_start, policy_start)

    if as_of < effective_start:
        reasons.append(f"Warmup mode active until {effective_start.isoformat()}; queue and review only.")
        return GateDecision(
            campaign_id=campaign_id,
            campaign_type=campaign_type,
            channel=channel,
            as_of=as_of.isoformat(),
            mode="generate_queue_review",
            publish_allowed=False,
            external_inference_allowed=False,
            reasons=reasons,
            required_next_action="Generate assets, queue variants, validate disclosures, and record audit events.",
        )

    if reasons:
        return GateDecision(
            campaign_id=campaign_id,
            campaign_type=campaign_type,
            channel=channel,
            as_of=as_of.isoformat(),
            mode="blocked",
            publish_allowed=False,
            external_inference_allowed=False,
            reasons=reasons,
            required_next_action="Correct policy, channel, disclosure, or campaign-risk issues before publishing.",
        )

    return GateDecision(
        campaign_id=campaign_id,
        campaign_type=campaign_type,
        channel=channel,
        as_of=as_of.isoformat(),
        mode="supervised_autopublish",
        publish_allowed=True,
        external_inference_allowed=True,
        reasons=["All deterministic gate checks passed for allowlisted supervised autopublish."],
        required_next_action="Publish only through the approved adapter with audit logging and rollback record.",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate a ProfitEngine campaign against the supervised autopublish gate.")
    parser.add_argument("--campaign", required=True, type=Path, help="Path to campaign JSON payload")
    parser.add_argument("--channel", required=True, help="Allowlisted channel key")
    parser.add_argument("--allowlist", default=DEFAULT_ALLOWLIST, type=Path, help="Path to channel allowlist JSON")
    parser.add_argument("--as-of", default=None, help="ISO date for deterministic evaluation, e.g. 2026-06-23")
    parser.add_argument("--strict", action="store_true", help="Exit nonzero when publishing is not allowed")
    args = parser.parse_args()

    campaign = load_json(args.campaign)
    allowlist = load_json(args.allowlist)
    decision = decide(campaign, allowlist, args.channel, parse_date(args.as_of))
    print(decision.to_json())

    if args.strict and not decision.publish_allowed:
        return 2
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, indent=2), file=sys.stderr)
        raise SystemExit(1)
