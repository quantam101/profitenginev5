"""Deterministic pre-review topical relevance gate for paid field-IT work.

This gate is independent of pricing, distance, and buyer urgency: none of those
can turn an unrelated job into an IT opportunity.  It intentionally does not
use substring hits for ambiguous "it", "ap", "av", or "pos".
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Relevance:
    score: int
    accepted: bool
    matched: tuple[str, ...]
    reasons: tuple[str, ...]


# Labels represent distinct technical evidence categories rather than repeated
# keyword occurrences.  One job repeating "network" 100 times gets one match.
_SIGNALS: tuple[tuple[str, str, int], ...] = (
    ("network_infrastructure", r"\b(?:network(?:ing)?|lan|wan|sd-wan|ethernet|router|switches|network switch|firewall|vpn)\b", 36),
    ("structured_cabling", r"\b(?:cat\s*[56][ae]?|fiber optic|structured cabling|low.voltage|patch panel|cable pull|cabling)\b", 36),
    ("endpoint_support", r"\b(?:desktop support|help\s*desk|laptop|computer repair|pc repair|workstation|imaging|intune)\b", 30),
    ("onsite_it", r"\b(?:it support|it technician|it field service|smart hands|smart.hands|tech dispatch)\b", 35),
    ("datacenter", r"\b(?:data center|datacenter|rack.and.stack|pdu|ups installation|server installation)\b", 36),
    ("wifi", r"\b(?:wi.fi|wireless access point|access point|aruba|meraki|ubiquiti)\b", 32),
    ("retail_it", r"\b(?:point.of.sale|pos terminal|pos system|barcode scanner|receipt printer|kiosk install)\b", 32),
    ("security_systems", r"\b(?:cctv|ip camera|nvr|door access|access control|badge reader)\b", 32),
    ("av_install", r"\b(?:tv parts swap|tv installation|display mount|digital signage|av equipment|video conferencing)\b", 31),
    ("printers", r"\b(?:printer repair|printer installation|print server|multifunction printer)\b", 29),
    ("general_technology", r"\b(?:telecom|voip|rfid|computer|printer|wireless|display|server)\b", 16),
)
_EXCLUSIONS: tuple[tuple[str, str], ...] = (
    ("network_marketing", r"\bnetwork marketing\b"),
    ("financial_products", r"\b(?:credit repair|mortgage broker|insurance sales|financial advisor|tax preparer)\b"),
    ("unrelated_services", r"\b(?:house cleaning|food delivery|restaurant server|cashier job|pet sitter|roofing contractor)\b"),
    ("unrelated_content", r"\b(?:seo copywriting|social media influencer|affiliate marketing|content writer)\b"),
)


def assess_relevance(text: str, work_type: str = "") -> Relevance:
    """Fail closed when substantive evidence of supported field-IT work is absent.

    Use independent evidence categories, not a large number of keyword hits.
    An explicit unrelated-work exclusion overrides generic technology words.
    """
    haystack = f"{work_type or ''}\n{text or ''}"
    matched = tuple(name for name, pattern, _ in _SIGNALS
                    if re.search(pattern, haystack, flags=re.IGNORECASE))
    excluded = tuple(name for name, pattern in _EXCLUSIONS
                     if re.search(pattern, haystack, flags=re.IGNORECASE))
    weights = {name: weight for name, _, weight in _SIGNALS}
    score = min(100, sum(weights[name] for name in matched))
    robust = any(weights[name] >= 29 for name in matched)
    accepted = bool(matched) and robust and not excluded
    reasons = excluded or (("no_supported_technical_scope",) if not accepted else ())
    return Relevance(score=score, accepted=accepted,
                     matched=matched, reasons=tuple(reasons))
