"""
RPM planning priors for faceless YouTube niches.

These are US-weighted planning priors only — NOT revenue promises. Real RPM
depends on audience geography, watch time, seasonality, and ad demand, and a
channel must first clear the YouTube Partner Program bar (1,000 subs +
4,000 public watch-hours or 10M Shorts views) before any monetization exists.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

# YouTube Partner Program eligibility bar.
YPP_SUBSCRIBERS = 1_000
YPP_WATCH_HOURS = 4_000
YPP_SHORTS_VIEWS = 10_000_000


@dataclass(frozen=True)
class RpmPrior:
    niche: str
    rpm_low: float   # USD per 1,000 monetized views — conservative bound
    rpm_high: float  # optimistic bound, still not a promise
    note: str

    def mid(self) -> float:
        return round((self.rpm_low + self.rpm_high) / 2, 2)


# US-weighted ranges compiled from public creator-reported figures; treat as
# directional priors for planning, not forecasts.
RPM_PRIORS: Dict[str, RpmPrior] = {
    "personal-finance":   RpmPrior("personal-finance",   6.0, 18.0, "High ad demand; volatile with season."),
    "business-software":  RpmPrior("business-software",  8.0, 22.0, "B2B buyers pay more; smaller reach."),
    "ai-tools":           RpmPrior("ai-tools",           5.0, 15.0, "Crowded niche; RPM swings with launches."),
    "history-explainer":  RpmPrior("history-explainer",  3.0,  9.0, "Long watch time; broad audience."),
    "science-explainer":  RpmPrior("science-explainer",  4.0, 11.0, "Steady evergreen demand."),
    "true-crime":         RpmPrior("true-crime",         3.0, 10.0, "High engagement; advertiser sensitivity."),
    "how-to-diy":         RpmPrior("how-to-diy",         3.0,  8.0, "Search-driven; durable."),
    "motivation":         RpmPrior("motivation",         1.5,  5.0, "Lowest RPM tier; high competition."),
}

DEFAULT_PRIOR = RpmPrior("general", 2.0, 8.0, "Fallback prior for unlisted niches.")


def prior_for(niche: str) -> RpmPrior:
    return RPM_PRIORS.get(niche, DEFAULT_PRIOR)


def revenue_band(niche: str, monthly_views: int) -> Dict[str, float]:
    """Planning band for a view target — explicitly labeled a prior."""
    p = prior_for(niche)
    return {
        "monthly_views": monthly_views,
        "rpm_low": p.rpm_low,
        "rpm_high": p.rpm_high,
        "low_usd": round(monthly_views / 1000 * p.rpm_low, 2),
        "high_usd": round(monthly_views / 1000 * p.rpm_high, 2),
    }


def ypp_gate(subscribers: int = 0, watch_hours: float = 0.0,
             shorts_views: int = 0) -> Dict[str, object]:
    """Whether a channel can monetize at all — the gate before RPM matters."""
    eligible = (
        subscribers >= YPP_SUBSCRIBERS
        and (watch_hours >= YPP_WATCH_HOURS or shorts_views >= YPP_SHORTS_VIEWS)
    )
    return {
        "eligible": eligible,
        "subscribers": subscribers,
        "watch_hours": watch_hours,
        "shorts_views": shorts_views,
        "required": {
            "subscribers": YPP_SUBSCRIBERS,
            "watch_hours_or": YPP_WATCH_HOURS,
            "shorts_views_or": YPP_SHORTS_VIEWS,
        },
    }
