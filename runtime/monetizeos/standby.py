"""Independent primary/hot-standby MonetizeOS Director service.

Run two OS processes with the SAME durable SQLite DB on the SAME filesystem.
A standby is passive until the current lease has expired or been released.
SQLite is not a multi-host consensus system; do not share this file over NFS
or claim cross-region failover without a transactional shared-store adapter.
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import time
from pathlib import Path

from runtime.monetizeos import Director, FencingStale, LeaseConflict, Store


def serve(*, db: str, project_id: str, mode: str = "standby",
          ttl_s: float = 6.0, poll_s: float = 0.5,
          run_seconds: float = 0.0, repo_root: str = ".",
          artifact_dir: str | None = None, once: bool = False) -> int:
    """Run as an independent process. Returns a process exit code.

    The standby never steals a live Director lease.  The live Director
    renews during specialist execution via parent-side heartbeats.
    """
    if mode not in {"primary", "standby"}:
        raise ValueError("mode must be primary or standby")
    if ttl_s <= 0 or poll_s <= 0:
        raise ValueError("ttl_s and poll_s must be positive")
    if poll_s >= ttl_s:
        raise ValueError("poll_s must be less than ttl_s")

    store = Store(db)
    store.create_project(project_id, project_id, {}, {})
    director = Director(store=store, project_id=project_id, lease_ttl_s=ttl_s)
    shutdown = False

    def stop(_signum: int, _frame: object) -> None:
        nonlocal shutdown
        shutdown = True

    previous: dict[int, object] = {}
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            previous[sig] = signal.signal(sig, stop)
        except ValueError:
            # Signals only install in the main thread.
            pass

    started = time.monotonic()
    had_lease = False
    # A standby started before the primary must remain passive: it has to
    # observe an incumbent lease before it is eligible to take over.
    observed_incumbent = mode == "primary"
    try:
        while not shutdown:
            if run_seconds and time.monotonic() - started >= run_seconds:
                break
            if not observed_incumbent:
                observed_incumbent = store.status(project_id)["director"] is not None
                if not observed_incumbent:
                    time.sleep(poll_s)
                    continue
            try:
                director.acquire()
                had_lease = True
                print(json.dumps({"event": "director_acquired", "project": project_id,
                                  "holder": director.holder, "fencing": director.fencing,
                                  "mode": mode}), flush=True)
                break
            except LeaseConflict:
                if mode == "primary":
                    print(json.dumps({"event": "primary_conflict", "project": project_id}), flush=True)
                    return 3
                # A standby observes and retries; acquisition is the atomic
                # decision, not the lease expiry value read in a status view.
                time.sleep(min(poll_s, max(0.01, ttl_s / 3)))

        if not had_lease:
            return 0
        ctx = {"repo_root": str(Path(repo_root).resolve()),
               "artifact_dir": artifact_dir}
        while not shutdown:
            if run_seconds and time.monotonic() - started >= run_seconds:
                break
            try:
                outcome = director.run_once(worker=director.holder, ctx=ctx)
                print(json.dumps({"event": "cycle", "outcome": outcome,
                                  "fencing": director.fencing}), flush=True)
            except (FencingStale, LeaseConflict) as exc:
                print(json.dumps({"event": "lease_lost",
                                  "reason": type(exc).__name__}), flush=True)
                return 4
            if once:
                break
            if outcome in {"idle", "no_handler"}:
                time.sleep(min(poll_s, max(0.01, ttl_s / 3)))
        return 0
    finally:
        if had_lease:
            director.release()
        store.close()
        for sig, handler in previous.items():
            signal.signal(sig, handler)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=os.environ.get("MONETIZEOS_DB", "data/monetizeos.db"))
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--mode", choices=("primary", "standby"), default="standby")
    parser.add_argument("--ttl", type=float, default=6.0)
    parser.add_argument("--poll", type=float, default=0.5)
    parser.add_argument("--run-seconds", type=float, default=0,
                        help="0 means keep serving until SIGTERM/SIGINT")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--artifact-dir")
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    return serve(db=args.db, project_id=args.project_id, mode=args.mode,
                 ttl_s=args.ttl, poll_s=args.poll, run_seconds=args.run_seconds,
                 repo_root=args.repo_root, artifact_dir=args.artifact_dir, once=args.once)


if __name__ == "__main__":
    raise SystemExit(main())
