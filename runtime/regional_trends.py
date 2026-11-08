"""
Regional demand signals via pytrends — ported from ai-profit-suite/expansion_insights.py
========================================================================================
Optional, zero-cost signal. Ranks candidate topics/keywords by Google Trends
``interest_by_region`` (city-level) where free pytrends data is available.

Zero-spend rule: pytrends is NOT a hard dependency. If it is absent, rate-limited
(HTTP 429), or fails for any reason, every public function degrades gracefully
and returns the input order unchanged — callers must never depend on this signal.
"""
from __future__ import annotations

import logging
import time
from typing import Dict, List, Optional, Sequence, Tuple

logger = logging.getLogger("RegionalTrends")

# Max pytrends payload calls per run — free endpoint, stay polite to avoid 429s.
_MAX_KEYWORDS = 5
# Seconds to sleep between payload calls.
_CALL_DELAY_S = 0.4


def _load_trendreq():
    """Return the pytrends TrendReq class, or None if pytrends is not installed."""
    try:
        from pytrends.request import TrendReq  # type: ignore[import]
    except Exception:
        return None
    return TrendReq


def interest_by_region(
    keyword: str,
    geo: str = "US",
    timeframe: str = "today 12-m",
) -> List[Tuple[str, float]]:
    """
    City-level demand ranking for one keyword.

    Returns a list of ``(region_name, interest)`` sorted highest → lowest.
    Returns ``[]`` when pytrends is missing, rate-limited, or errors.
    """
    trend_req = _load_trendreq()
    if trend_req is None:
        return []
    try:
        pytrends = trend_req()
        pytrends.build_payload([keyword], geo=geo, timeframe=timeframe)
        data = pytrends.interest_by_region(
            resolution="CITY", inc_low_vol=True, inc_geo_code=False
        )
        if data is None or keyword not in getattr(data, "columns", []):
            return []
        ranked = data.sort_values(by=keyword, ascending=False)
        return [(str(region), float(row[keyword])) for region, row in ranked.iterrows()]
    except Exception as exc:
        logger.warning("[RegionalTrends] interest_by_region failed for %r: %s", keyword, exc)
        return []


def regional_interest_score(
    keywords: Sequence[str],
    geo: str = "US",
    timeframe: str = "today 12-m",
    max_regions: int = 25,
) -> Dict[str, float]:
    """
    Score each keyword by its summed city-level interest across the top regions.

    Returns ``{keyword: score}``. Keywords that could not be measured score 0.0.
    Only the first ``_MAX_KEYWORDS`` keywords are queried.
    """
    scores: Dict[str, float] = {}
    for i, kw in enumerate(keywords[:_MAX_KEYWORDS]):
        regions = interest_by_region(kw, geo=geo, timeframe=timeframe)
        scores[kw] = sum(v for _, v in regions[:max_regions])
        if i < len(keywords) - 1:
            time.sleep(_CALL_DELAY_S)
    for kw in keywords[_MAX_KEYWORDS:]:
        scores.setdefault(kw, 0.0)
    return scores


def rank_by_regional_interest(
    keywords: Sequence[str],
    geo: str = "US",
    timeframe: str = "today 12-m",
) -> List[str]:
    """
    Re-rank candidate keywords by regional demand (highest first).

    Degrades gracefully: if no keyword produced measurable interest (pytrends
    absent / rate-limited / no data), the input order is returned unchanged.
    """
    if not keywords:
        return []
    scores = regional_interest_score(keywords, geo=geo, timeframe=timeframe)
    if not any(scores.values()):
        return list(keywords)
    return sorted(keywords, key=lambda k: scores.get(k, 0.0), reverse=True)


def rank_cities_by_interest(
    keyword: str,
    cities: Sequence[Tuple[str, str]],
    geo: str = "US",
    timeframe: str = "today 12-m",
) -> List[Tuple[str, str]]:
    """
    Order ``(city, state)`` candidates by measured interest for ``keyword``.

    Used by the city SEO engine to prioritize which cities get pages first.
    Degrades to the input order when pytrends data is unavailable.
    """
    if not cities:
        return []
    regions = interest_by_region(keyword, geo=geo, timeframe=timeframe)
    if not regions:
        return list(cities)
    interest = {name.lower(): value for name, value in regions}
    # City-level data carries no state, so a name shared across states
    # (e.g. Springfield IL vs MO) can't be attributed — score it 0 rather
    # than let one state's twin inherit the other's measured interest.
    counts: Dict[str, int] = {}
    for c, _s in cities:
        counts[c.lower()] = counts.get(c.lower(), 0) + 1
    return sorted(
        cities,
        key=lambda cs: interest.get(cs[0].lower(), 0.0)
        if counts[cs[0].lower()] == 1
        else 0.0,
        reverse=True,
    )
