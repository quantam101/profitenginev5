"""Region-ranked keyword demand via Google Trends (pytrends).

Ported from quantam101/ai-profit-suite ``expansion_insights.py`` and
hardened for the ProfitEngine failover rule: pytrends is an optional
dependency and Google Trends is a free-but-unreliable endpoint, so
every failure mode (missing package, 429, timeout, empty frame)
degrades to ``None`` / the caller's static ordering — never raises.

Usage::

    from runtime.trend_regions import region_interest, prioritize_cities

    ranking = region_interest("it support")           # [(city, state, score)]
    cities  = prioritize_cities(_CITIES, "it support") # reorders in place-safe copy

CLI::

    python -m runtime.trend_regions "managed IT services" --top 15
"""

from __future__ import annotations

import argparse
import logging
from typing import List, Optional, Sequence, Tuple

logger = logging.getLogger("TrendRegions")

# (city, state, interest 0-100)
RegionScore = Tuple[str, str, int]


def _fetch_interest_by_region(
    keyword: str,
    geo: str = "US",
    timeframe: str = "today 12-m",
    resolution: str = "CITY",
):
    """Return a pandas DataFrame or None on any failure."""
    try:
        from pytrends.request import TrendReq  # optional dependency
    except ImportError:
        logger.warning("[TrendRegions] pytrends not installed — static ordering")
        return None
    try:
        pytrends = TrendReq(hl="en-US", tz=360, timeout=(10, 25))
        pytrends.build_payload([keyword], geo=geo, timeframe=timeframe)
        data = pytrends.interest_by_region(
            resolution=resolution, inc_low_vol=True, inc_geo_code=True
        )
    except Exception as exc:  # network, 429, Google changes — all degraded
        logger.warning(f"[TrendRegions] pytrends failed ({exc}) — static ordering")
        return None
    if data is None or data.empty or keyword not in data.columns:
        logger.warning("[TrendRegions] empty interest frame — static ordering")
        return None
    return data


def region_interest(
    keyword: str,
    geo: str = "US",
    timeframe: str = "today 12-m",
    top: Optional[int] = None,
) -> Optional[List[RegionScore]]:
    """City-level interest ranking for a keyword, highest first.

    Returns ``[(city_name, geo_code, interest_0_100)]`` or ``None`` when
    Trends data is unavailable (caller keeps static ordering).
    """
    data = _fetch_interest_by_region(keyword, geo=geo, timeframe=timeframe)
    if data is None:
        return None
    ranked = data.sort_values(by=keyword, ascending=False)
    out: List[RegionScore] = []
    for name, row in ranked.iterrows():
        score = int(row[keyword])
        if score <= 0:
            continue
        geo_code = str(row.get("geoCode", ""))
        state = geo_code.split("-")[-1] if "-" in geo_code else geo_code
        out.append((str(name), state, score))
        if top and len(out) >= top:
            break
    return out or None


def prioritize_cities(
    cities: Sequence[Tuple[str, str, str]],
    keyword: str,
    geo: str = "US",
    timeframe: str = "today 12-m",
) -> List[Tuple[str, str, str]]:
    """Reorder ``(city, state, tier)`` rows by measured Trends demand.

    Cities absent from the Trends frame keep their relative static order
    after ranked cities. On any Trends failure the input order is
    returned unchanged — failover to static tier ordering.
    """
    ranking = region_interest(keyword, geo=geo, timeframe=timeframe)
    if not ranking:
        return list(cities)

    # Map Trends region names back onto our city list by (city, state).
    interest = {(name.lower(), st.upper()): score for name, st, score in ranking}
    scored: List[Tuple[int, int, Tuple[str, str, str]]] = []
    for idx, (city, state, tier) in enumerate(cities):
        key = (city.lower(), state.upper())
        score = interest.get(key, -1)
        # Negative index keeps unmatched cities in original order at the end.
        scored.append((score if score >= 0 else -1, -idx if score < 0 else idx, (city, state, tier)))
    scored.sort(key=lambda t: (-t[0], t[1]))
    return [c for _, __, c in scored]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Rank US regions by Google Trends interest for a keyword"
    )
    parser.add_argument("keyword", help="search term to analyze")
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--geo", default="US")
    parser.add_argument("--timeframe", default="today 12-m")
    args = parser.parse_args()

    ranking = region_interest(
        args.keyword, geo=args.geo, timeframe=args.timeframe, top=args.top
    )
    if not ranking:
        print("No Trends data — static tier ordering applies.")
        return
    for name, state, score in ranking:
        print(f"{score:3d}  {name}, {state}")


if __name__ == "__main__":
    main()
