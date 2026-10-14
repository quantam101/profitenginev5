import sys
import types

from runtime import trend_regions


CITIES = [
    ("Phoenix", "AZ", "A"),
    ("Tucson", "AZ", "C"),
    ("Chicago", "IL", "A"),
]


def _fake_trendreq(frame):
    mod = types.ModuleType("pytrends.request")

    class TrendReq:
        def __init__(self, *a, **kw):
            pass

        def build_payload(self, *a, **kw):
            pass

        def interest_by_region(self, **kw):
            return frame

    mod.TrendReq = TrendReq
    return mod


class _Row:
    def __init__(self, data):
        self._d = data

    def __getitem__(self, k):
        return self._d[k]

    def get(self, k, default=None):
        return self._d.get(k, default)


class _FakeFrame:
    """Minimal pandas stand-in for interest_by_region results."""

    def __init__(self, rows):
        self._rows = rows  # list of (index_name, {col: val})
        self.empty = not rows
        self.columns = [k for _, r in rows for k in r] if rows else []

    def sort_values(self, by, ascending=False):
        return _FakeFrame(
            sorted(self._rows, key=lambda r: r[1][by], reverse=not ascending)
        )

    def iterrows(self):
        for name, row in self._rows:
            yield name, _Row(row)


def test_region_interest_ranks_and_filters(monkeypatch):
    frame = _FakeFrame([
        ("Chicago", {"it support": 55, "geoCode": "US-IL"}),
        ("Phoenix", {"it support": 100, "geoCode": "US-AZ"}),
        ("Nowhere", {"it support": 0, "geoCode": "US-XX"}),
    ])
    pkg = types.ModuleType("pytrends")
    pkg.request = _fake_trendreq(frame)
    monkeypatch.setitem(sys.modules, "pytrends", pkg)
    monkeypatch.setitem(sys.modules, "pytrends.request", pkg.request)

    ranking = trend_regions.region_interest("it support")
    assert ranking[0] == ("Phoenix", "AZ", 100)
    assert ranking[1] == ("Chicago", "IL", 55)
    assert len(ranking) == 2  # zero-interest rows dropped


def test_region_interest_returns_none_without_pytrends(monkeypatch):
    monkeypatch.setitem(sys.modules, "pytrends", None)
    monkeypatch.setitem(sys.modules, "pytrends.request", None)
    assert trend_regions.region_interest("it support") is None


def test_region_interest_returns_none_on_api_failure(monkeypatch):
    mod = types.ModuleType("pytrends.request")

    class TrendReq:
        def __init__(self, *a, **kw):
            pass

        def build_payload(self, *a, **kw):
            raise RuntimeError("429")

    mod.TrendReq = TrendReq
    pkg = types.ModuleType("pytrends")
    pkg.request = mod
    monkeypatch.setitem(sys.modules, "pytrends", pkg)
    monkeypatch.setitem(sys.modules, "pytrends.request", mod)

    assert trend_regions.region_interest("it support") is None


def test_prioritize_cities_reorders_by_demand(monkeypatch):
    monkeypatch.setattr(
        trend_regions,
        "region_interest",
        lambda *a, **kw: [("Tucson", "AZ", 90), ("Phoenix", "AZ", 50)],
    )
    out = trend_regions.prioritize_cities(CITIES, "it support")
    assert out[0] == ("Tucson", "AZ", "C")
    assert out[1] == ("Phoenix", "AZ", "A")
    assert out[2] == ("Chicago", "IL", "A")  # unmatched keeps position


def test_prioritize_cities_unmatched_keep_static_order(monkeypatch):
    cities = [
        ("Boston", "MA", "B"),
        ("Tucson", "AZ", "C"),
        ("Denver", "CO", "B"),
        ("Phoenix", "AZ", "A"),
    ]
    monkeypatch.setattr(
        trend_regions,
        "region_interest",
        lambda *a, **kw: [("Phoenix", "AZ", 80)],
    )
    out = trend_regions.prioritize_cities(cities, "it support")
    assert out[0] == ("Phoenix", "AZ", "A")
    # Unmatched cities must keep their original relative order (not reversed).
    assert out[1:] == [("Boston", "MA", "B"), ("Tucson", "AZ", "C"), ("Denver", "CO", "B")]


def test_prioritize_cities_failover_keeps_static_order(monkeypatch):
    monkeypatch.setattr(trend_regions, "region_interest", lambda *a, **kw: None)
    assert trend_regions.prioritize_cities(CITIES, "x") == CITIES
