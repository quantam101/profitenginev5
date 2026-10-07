"""YouTube retention priors — closes the loop between published videos and
future scripts.

A weekly workflow runs `python -m runtime.fye.retention <out.json>` which:
  1. refreshes the upload OAuth token (same chain as daily_revenue_tracker),
  2. pulls per-video retention via the YouTube Analytics API (free),
  3. joins titles via the Data API,
  4. summarizes which title patterns and topics actually held viewers.

The ScriptAgent reads the committed priors file and biases title/hook format
toward patterns that historically retained viewers. All steps fail closed:
missing creds or API errors leave priors absent and scripts run unaffected.

Env: YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.parse
import urllib.request

from pathlib import Path
from typing import Any, Dict, List, Optional

_OAUTH_URL = "https://oauth2.googleapis.com/token"
_ANALYTICS_URL = "https://youtubeanalytics.googleapis.com/v2/reports"
_VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"
_UA = "already-here-fye/1.0"

# Title-shape patterns scored against retention. First matching pattern wins.
_TITLE_PATTERNS = [
    ("question", re.compile(r"\?", re.I)),
    ("how_to", re.compile(r"^how (to|i|we|you)\b", re.I)),
    ("why", re.compile(r"^why\b", re.I)),
    ("numbered", re.compile(r"^\d+\s|top \d+|\b\d+ (ways|rules|mistakes|steps|tips)\b", re.I)),
    ("versus", re.compile(r"\bvs\.?\b|\bversus\b|\bor\b.*\?$", re.I)),
    ("negative", re.compile(r"\b(never|stop|avoid|mistake|wrong|fail)\b", re.I)),
    ("year_number", re.compile(r"\b20\d\d\b", re.I)),
]
_STOPWORDS = set("""the a an and or of to in for on at is are was be your you our we it this
that how why what when with from by as about vs into over under explained minutes""".split())


def _post(url: str, data: Dict[str, str], timeout: int = 20) -> Dict[str, Any]:
    req = urllib.request.Request(  # noqa: S310 — fixed Google URL
        url, data=urllib.parse.urlencode(data).encode(),
        headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310 — fixed Google URL
        return json.loads(r.read())


def _get_json(url: str, headers: Dict[str, str], timeout: int = 30) -> Dict[str, Any]:
    req = urllib.request.Request(url,  # noqa: S310 — fixed Google URL
                                 headers={**headers, "User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310 — fixed Google URL
        return json.loads(r.read())


def _access_token(client_id: str, client_secret: str, refresh_token: str) -> str:
    tok = _post(_OAUTH_URL, {
        "client_id": client_id, "client_secret": client_secret,
        "refresh_token": refresh_token, "grant_type": "refresh_token"})
    return str(tok.get("access_token") or "")


def _fetch_video_metrics(headers: Dict[str, str], days: int = 90,
                         limit: int = 50) -> List[Dict[str, Any]]:
    """Per-video viewership via YouTube Analytics; best-recent first."""
    import datetime as _dt
    end = _dt.date.today()
    start = end - _dt.timedelta(days=days)
    q = urllib.parse.urlencode({
        "ids": "channel==MINE",
        "startDate": start.isoformat(), "endDate": end.isoformat(),
        "dimensions": "video",
        "metrics": "views,averageViewPercentage,averageViewDuration,likes",
        "sort": "-views", "maxResults": str(limit),
    })
    data = _get_json(f"{_ANALYTICS_URL}?{q}", headers)
    cols = [c["name"] for c in data.get("columnHeaders", [])]
    rows = []
    for r in data.get("rows", []):
        rows.append(dict(zip(cols, r)))
    return rows


def _fetch_titles(headers: Dict[str, str], ids: List[str]) -> Dict[str, str]:
    titles: Dict[str, str] = {}
    for i in range(0, len(ids), 50):
        q = urllib.parse.urlencode({"part": "snippet", "id": ",".join(ids[i:i + 50]),
                                    "fields": "items(id,snippet(title))"})
        data = _get_json(f"{_VIDEOS_URL}?{q}", headers)
        for item in data.get("items", []):
            titles[item["id"]] = item.get("snippet", {}).get("title", "")
    return titles


def _title_pattern(title: str) -> str:
    for name, rx in _TITLE_PATTERNS:
        if rx.search(title):
            return name
    return "statement"


def _keywords(title: str) -> List[str]:
    return [w for w in re.findall(r"[a-z]{4,}", title.lower()) if w not in _STOPWORDS]


def build_priors(rows: List[Dict[str, Any]], titles: Dict[str, str]) -> Dict[str, Any]:
    """Rank title patterns + keywords by mean audience retention."""
    vids: List[Dict[str, Any]] = []
    for r in rows:
        vid = str(r.get("video") or "")
        title = titles.get(vid, "")
        views = float(r.get("views") or 0)
        pct = float(r.get("averageViewPercentage") or 0)
        if not title or views < 5 or pct <= 0:
            continue
        vids.append({"video": vid, "title": title, "views": views,
                     "avg_view_pct": round(pct, 1),
                     "pattern": _title_pattern(title),
                     "keywords": _keywords(title)})
    if not vids:
        return {"videos": 0}

    def _mean(items):
        return round(sum(v["avg_view_pct"] for v in items) / len(items), 1) if items else 0.0

    pattern_stats: Dict[str, List[Dict[str, Any]]] = {}
    kw_stats: Dict[str, List[float]] = {}
    for v in vids:
        pattern_stats.setdefault(v["pattern"], []).append(v)
        for k in v["keywords"]:
            kw_stats.setdefault(k, []).append(v["avg_view_pct"])

    patterns = {p: {"n": len(vs), "avg_view_pct": _mean(vs)}
                for p, vs in sorted(pattern_stats.items(),
                                    key=lambda kv: -_mean(kv[1]))}
    keywords = {k: {"n": len(v), "avg_view_pct": round(sum(v) / len(v), 1)}
                for k, v in sorted(kw_stats.items(), key=lambda kv: -sum(kv[1]) / len(kv[1]))
                if len(v) >= 2}

    ranked = sorted(vids, key=lambda v: -v["avg_view_pct"])
    return {
        "videos": len(vids),
        "channel_avg_view_pct": _mean(vids),
        "best_patterns": patterns,
        "best_keywords": dict(list(keywords.items())[:25]),
        "winners": [{"title": v["title"], "avg_view_pct": v["avg_view_pct"]}
                    for v in ranked[:5]],
        "losers": [{"title": v["title"], "avg_view_pct": v["avg_view_pct"]}
                   for v in ranked[-5:]],
    }


def preferred_pattern(priors: Dict[str, Any]) -> Optional[str]:
    """Title pattern with the best retention, needing >=2 samples to trust."""
    best = None
    for name, st in (priors.get("best_patterns") or {}).items():
        if st.get("n", 0) >= 2:
            best = name
            break
    return best


def load_priors(path: Path, max_age_days: int = 30) -> Optional[Dict[str, Any]]:
    """Committed priors file → dict, or None when missing/stale/corrupt."""
    try:
        priors = json.loads(path.read_text())
        import datetime as _dt
        fetched = _dt.date.fromisoformat(str(priors.get("fetched", "")))
        if (_dt.date.today() - fetched).days > max_age_days:
            return None
        return priors if priors.get("videos") else None
    except Exception:
        return None


def default_priors_path() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "fye" / "retention_priors.json"


def fetch_priors(client_id: str, client_secret: str, refresh_token: str,
                 days: int = 90) -> Optional[Dict[str, Any]]:
    token = _access_token(client_id, client_secret, refresh_token)
    if not token:
        return None
    headers = {"Authorization": f"Bearer {token}"}
    rows = _fetch_video_metrics(headers, days=days)
    titles = _fetch_titles(headers, [r["video"] for r in rows])
    priors = build_priors(rows, titles)
    if not priors.get("videos"):
        return None
    import datetime as _dt
    priors["fetched"] = _dt.date.today().isoformat()
    priors["window_days"] = days
    return priors


def main(argv: List[str]) -> int:
    import os
    out = Path(argv[1]) if len(argv) > 1 else default_priors_path()
    priors = fetch_priors(
        os.getenv("YOUTUBE_CLIENT_ID", "").strip(),
        os.getenv("YOUTUBE_CLIENT_SECRET", "").strip(),
        os.getenv("YOUTUBE_REFRESH_TOKEN", "").strip())
    if not priors:
        print("no priors (missing creds, no metrics, or API error)", file=sys.stderr)
        return 1
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(priors, indent=2))
    print(f"wrote {out}: {priors['videos']} videos, "
          f"channel avg {priors['channel_avg_view_pct']}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
