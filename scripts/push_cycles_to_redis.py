"""
push_cycles_to_redis.py

Reads the local CycleLog JSONL written during this GitHub Actions run
and pushes records + updated metrics to Upstash Redis.

Run after every cycle execution in CI.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

REDIS_URL = os.environ.get("UPSTASH_REDIS_REST_URL", "").rstrip("/")
REDIS_TOKEN = os.environ.get("UPSTASH_REDIS_REST_TOKEN", "")
CYCLE_LOG_PATH = os.environ.get("GMAOS_CYCLE_LOG", "./data/logs/cycles.jsonl")
RECORDS_KEY = "cycles:records"
METRICS_KEY = "cycles:metrics"
MAX_RECORDS = 1000


def redis_cmd(*args):
    """Execute a single Redis REST command."""
    if not REDIS_URL or not REDIS_TOKEN:
        print("[push_cycles_to_redis] UPSTASH env vars not set — skipping", file=sys.stderr)
        return None
    path = "/" + "/".join(str(a) for a in args)
    req = urllib.request.Request(
        REDIS_URL + path,
        headers={"Authorization": f"Bearer {REDIS_TOKEN}"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"[push_cycles_to_redis] Redis error {e.code}: {e.read()}", file=sys.stderr)
        return None


def redis_post(command: list):
    """POST a Redis pipeline command."""
    if not REDIS_URL or not REDIS_TOKEN:
        return None
    data = json.dumps(command).encode()
    req = urllib.request.Request(
        REDIS_URL,
        data=data,
        headers={
            "Authorization": f"Bearer {REDIS_TOKEN}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"[push_cycles_to_redis] Redis POST error {e.code}: {e.read()}", file=sys.stderr)
        return None


def main():
    log_path = Path(CYCLE_LOG_PATH)
    if not log_path.exists():
        print(f"[push_cycles_to_redis] No cycle log found at {log_path} — nothing to push")
        return

    lines = [l.strip() for l in log_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    if not lines:
        print("[push_cycles_to_redis] Cycle log is empty — nothing to push")
        return

    records = []
    for line in lines:
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    if not records:
        print("[push_cycles_to_redis] No valid JSON records found")
        return

    # Push each record to Redis list (newest first)
    pushed = 0
    for rec in reversed(records):
        result = redis_post(["LPUSH", RECORDS_KEY, json.dumps(rec)])
        if result:
            pushed += 1

    # Trim to max
    redis_post(["LTRIM", RECORDS_KEY, "0", str(MAX_RECORDS - 1)])

    # Compute and store metrics
    total = len(records)
    ok_count = sum(1 for r in records if r.get("status") == "ok")
    success_rate = round(ok_count / total * 100, 1) if total else 0.0
    durations = [r["duration_ms"] for r in records if isinstance(r.get("duration_ms"), (int, float))]
    avg_dur = round(sum(durations) / len(durations)) if durations else 0
    tier_dist: dict = {}
    agent_dist: dict = {}
    last_iso = None
    for r in records:
        tier = r.get("route_tier", "unknown")
        tier_dist[tier] = tier_dist.get(tier, 0) + 1
        agent = r.get("agent_id", "unknown")
        agent_dist[agent] = agent_dist.get(agent, 0) + 1
        if r.get("iso_timestamp"):
            last_iso = r["iso_timestamp"]

    metrics = {
        "total_cycles": total,
        "successful_cycles": ok_count,
        "success_rate_pct": success_rate,
        "avg_duration_ms": avg_dur,
        "tier_distribution": tier_dist,
        "agent_distribution": agent_dist,
        "last_cycle_iso": last_iso,
    }
    redis_post(["SET", METRICS_KEY, json.dumps(metrics), "EX", str(86400 * 7)])

    print(f"[push_cycles_to_redis] Pushed {pushed}/{total} records, metrics updated. Success rate: {success_rate}%")


if __name__ == "__main__":
    main()
