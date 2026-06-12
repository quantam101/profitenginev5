from __future__ import annotations

from dataclasses import dataclass
from typing import Any

MINIMUM_DAILY_FIELD_REVENUE = 500.0
MINIMUM_DISPATCH_VALUE = 130.0
MINIMUM_EFFECTIVE_HOURLY = 65.0
PREFERRED_SMART_HANDS_FLAT = 200.0
RETAINER_FLOOR_MONTHLY = 1500.0

PREMIUM_SERVICE_TYPES = {
    "server_smart_hands",
    "data_center",
    "network_support",
    "ap_wireless",
    "pos_support",
    "access_control",
    "healthcare_equipment",
    "project_management",
    "field_project_lead",
    "retainer_coverage",
}

LOW_MARGIN_TERMS = ("helper", "labor only", "unknown pay", "commission only", "intern", "w2", "full-time", "employee")
LONG_TRAVEL_TERMS = ("flagstaff", "show low", "tucson", "yuma", "prescott")


@dataclass(frozen=True)
class ASIAdapterDecision:
    grade: str
    expected_revenue: float
    target_rate: float
    effective_hourly: float | None
    retainer_potential: int
    data_value_score: int
    next_action: str
    risk_flags: tuple[str, ...]
    approval_required: bool = True


def _num(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        return float(str(value).replace("$", "").replace(",", ""))
    except ValueError:
        return default


def _contains_any(value: str, terms: set[str] | tuple[str, ...]) -> bool:
    lower = value.lower()
    return any(term.lower() in lower for term in terms)


def score_revenue_signal(payload: dict[str, Any]) -> ASIAdapterDecision:
    title = str(payload.get("title", ""))
    description = str(payload.get("description", ""))
    location = str(payload.get("location", ""))
    service_type = str(payload.get("service_type", payload.get("serviceType", ""))).strip().lower()
    combined = " ".join([title, description, location, service_type])

    listed_rate = _num(payload.get("listed_rate", payload.get("listedRate")))
    max_hours = _num(payload.get("max_hours", payload.get("maxHours")), 2.0)
    fixed_pay = _num(payload.get("fixed_pay", payload.get("fixedPay")))
    expected_revenue = fixed_pay or (listed_rate * max_hours if listed_rate else _num(payload.get("expected_revenue", payload.get("expectedRevenue"))))
    travel_minutes = _num(payload.get("estimated_travel_minutes", payload.get("estimatedTravelMinutes")))
    onsite_minutes = _num(payload.get("estimated_onsite_minutes", payload.get("estimatedOnsiteMinutes")), max_hours * 60 if max_hours else 120)
    total_hours = max((travel_minutes + onsite_minutes) / 60.0, 0.25)
    effective_hourly = expected_revenue / total_hours if expected_revenue else None

    risk_flags: list[str] = []
    if expected_revenue < MINIMUM_DISPATCH_VALUE:
        risk_flags.append("below_minimum_dispatch_value")
    if effective_hourly is not None and effective_hourly < MINIMUM_EFFECTIVE_HOURLY:
        risk_flags.append("below_effective_hourly_floor")
    if _contains_any(combined, LOW_MARGIN_TERMS):
        risk_flags.append("employment_or_low_margin_language")
    if _contains_any(location, LONG_TRAVEL_TERMS) or travel_minutes > 90:
        risk_flags.append("travel_burden")
    if not expected_revenue:
        risk_flags.append("pay_not_visible")

    premium = service_type in PREMIUM_SERVICE_TYPES or _contains_any(
        combined,
        {"server", "data center", "hpe", "storage", "access control", "pos", "wireless", "project manager", "site lead", "field lead", "retainer"},
    )

    retainer_potential = 3 if payload.get("retainer_potential") or payload.get("retainerPotential") else 0
    if _contains_any(combined, {"overflow", "coverage", "vendor list", "municipal", "procurement", "msp", "retainer", "recurring"}):
        retainer_potential += 2
    if service_type in {"project_management", "field_project_lead", "retainer_coverage"}:
        retainer_potential += 2
    retainer_potential = min(retainer_potential, 5)

    data_value_score = 1 + retainer_potential
    if payload.get("company") or payload.get("contact_email") or payload.get("contactEmail"):
        data_value_score += 2
    if premium:
        data_value_score += 2
    data_value_score = min(data_value_score, 10)

    if expected_revenue >= MINIMUM_DAILY_FIELD_REVENUE:
        grade = "A"
    elif expected_revenue >= 250 and "travel_burden" not in risk_flags:
        grade = "B"
    elif expected_revenue >= 150 and "travel_burden" not in risk_flags:
        grade = "C"
    elif retainer_potential >= 4 and data_value_score >= 7:
        grade = "B_STRATEGIC"
    else:
        grade = "AVOID"

    if "travel_burden" in risk_flags and expected_revenue < MINIMUM_DAILY_FIELD_REVENUE:
        grade = "AVOID"
    if "employment_or_low_margin_language" in risk_flags and retainer_potential < 4:
        grade = "AVOID"

    target_rate = max(expected_revenue, PREFERRED_SMART_HANDS_FLAT if premium else MINIMUM_DISPATCH_VALUE)
    if "travel_burden" in risk_flags:
        target_rate = max(target_rate, 450.0)

    next_action = {
        "A": "Pursue as a $500 daily field anchor or premium project/SOW.",
        "B": "Pursue only if it stacks locally or converts into project/retainer work.",
        "B_STRATEGIC": "Store as database intelligence and convert to retainer, procurement, vendor, or software workflow.",
        "C": "Use only as tightly clustered filler after premium work is secured.",
        "AVOID": "Pass unless the buyer approves a premium or travel-adjusted counter.",
    }[grade]

    return ASIAdapterDecision(
        grade=grade,
        expected_revenue=expected_revenue,
        target_rate=target_rate,
        effective_hourly=effective_hourly,
        retainer_potential=retainer_potential,
        data_value_score=data_value_score,
        next_action=next_action,
        risk_flags=tuple(risk_flags),
    )
