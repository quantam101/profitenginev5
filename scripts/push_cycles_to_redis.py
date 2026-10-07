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



def redis_post(command: list):
    """POST a Redis pipeline command. Returns (ok, error_detail)."""
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
            return True, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read()[:200]
        print(f"[push_cycles_to_redis] Redis POST error {e.code}: {body}", file=sys.stderr)
        return False, f"HTTP {e.code}"
    except Exception as e:
        print(f"[push_cycles_to_redis] Redis POST failed: {e}", file=sys.stderr)
        return False, str(e)[:120]


def main() -> int:
    """Push records; exit nonzero when persistence cannot be proven."""
    configured = bool(REDIS_URL and REDIS_TOKEN)
    log_path = Path(CYCLE_LOG_PATH)
    if not log_path.exists():
        print(f"[push_cycles_to_redis] No cycle log found at {log_path} — nothing to push")
        if not configured:
            print("::error::UPSTASH_REDIS_REST_URL/TOKEN not configured — cycles are not persisted")
            return 2
        return 0

    lines = [l.strip() for l in log_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    if not lines:
        print("[push_cycles_to_redis] Cycle log is empty — nothing to push")
        return 0 if configured else 2

    records = []
    for line in lines:
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    if not records:
        print("[push_cycles_to_redis] No valid JSON records found")
        return 0 if configured else 2

    if not configured:
        print(f"::error::{len(records)} cycle record(s) generated but Redis credentials are "
              "missing — profit cycle did NOT persist its results")
        return 2

    # Push each record to Redis list (newest first)
    pushed = 0
    errors = []
    for rec in reversed(records):
        ok, detail = redis_post(["LPUSH", RECORDS_KEY, json.dumps(rec)])
        if ok:
            pushed += 1
        else:
            errors.append(detail)

    if pushed < len(records):
        print(f"::error::Only {pushed}/{len(records)} records persisted "
              f"({len(errors)} failures: {errors[:3]})")
        if pushed == 0:
            return 3

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
    ok_m, _ = redis_post(["SET", METRICS_KEY, json.dumps(metrics), "EX", str(86400 * 7)])
    if not ok_m:
        print("::warning::metrics snapshot write failed")

    print(f"[push_cycles_to_redis] Pushed {pushed}/{total} records, metrics updated. "
          f"Success rate: {success_rate}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
