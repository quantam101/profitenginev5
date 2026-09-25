#!/usr/bin/env python3
"""MonetizeOS CLI — Director/worker entrypoint and Lifelong Catch and Correct view.

    monetizeos.py init <project_id> --name "..."      create a project
    monetizeos.py audit <project_id>                  run the repository_auditor
    monetizeos.py enqueue <project_id> <contract.json>   delegate a task contract
    monetizeos.py run <project_id> [--worker NAME]    run scheduling cycles until idle
    monetizeos.py status <project_id>                 Lifelong Catch and Correct view
    monetizeos.py cancel <task_id>                    request task cancellation
    monetizeos.py gates <project_id>                  release-gate board
    monetizeos.py gate-pass <project_id> <gate>       mark a gate passed (needs evidence)

Recurring work requires a persistent runtime — this CLI is stateless;
schedule it via cron/systemd/GitHub Actions for continuous operation.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runtime.monetizeos import (  # noqa: E402
    Director, GateBoard, RELEASE_GATES, Store, TaskContract,
)
from runtime.monetizeos.specialists import repository_audit_handler  # noqa: E402


def _director(db: str, project_id: str) -> Director:
    store = Store(db)
    store.create_project(project_id, project_id, {}, {})
    d = Director(store=store, project_id=project_id)
    d.acquire()
    return d


def cmd_init(args) -> int:
    store = Store(args.db)
    baseline = json.loads(Path(args.baseline).read_text()) if args.baseline else {}
    store.create_project(args.project_id, args.name or args.project_id,
                         spec={}, baseline=baseline)
    print(json.dumps({"created": args.project_id, "db": args.db}))
    return 0


def cmd_audit(args) -> int:
    d = _director(args.db, args.project_id)
    ctx = {"repo_root": args.repo_root, "artifact_dir": args.artifact_dir}
    contract = TaskContract(
        task_id=f"audit-{int(time.time())}", process_owner="repository_auditor",
        objective="Evidence-linked asset inventory of the repository",
        business_purpose="Establish the factual baseline before optimization",
        verification_method="handler completes a full walk and emits inventory.json",
    )
    report = repository_audit_handler(contract, ctx)
    baseline = {"audit": report.artifact_refs, "at": time.time()}
    d.store.update_baseline(args.project_id, baseline)
    print(report.to_json())
    return 0


def cmd_enqueue(args) -> int:
    d = _director(args.db, args.project_id)
    spec = json.loads(Path(args.contract).read_text())
    contract = TaskContract(**spec)
    task_id = d.delegate(contract, priority=args.priority)
    print(json.dumps({"task_id": task_id, "state": d.store.get_task(task_id)["state"]}))
    return 0


def cmd_run(args) -> int:
    d = _director(args.db, args.project_id)
    ctx = {"repo_root": args.repo_root, "artifact_dir": args.artifact_dir}
    cycles = 0
    while cycles < args.max_cycles:
        outcome = d.run_once(args.worker, ctx)
        print(json.dumps({"cycle": cycles, "outcome": outcome}))
        if outcome in ("idle", "no_handler"):
            break
        cycles += 1
    print(json.dumps(d.status(), default=str))
    return 0


def cmd_status(args) -> int:
    store = Store(args.db)
    status = store.status(args.project_id)
    tasks = store.list_tasks(args.project_id)
    board = GateBoard(store, args.project_id).state()
    print(json.dumps({
        "lifelong_catch_and_correct": {
            "objective": (store.get_project(args.project_id) or {}).get("spec", {}).get("objective"),
            "director": status["director"],
            "tasks_by_state": status["tasks"],
            "task_list": tasks,
            "open_incidents": status["open_incidents"],
            "pending_outbox": status["pending_outbox"],
            "cost": {"tokens": status["tokens"], "usd": status["usd"]},
            "throughput": {"attempts": status["attempts"],
                           "avg_attempt_seconds": status["avg_attempt_seconds"]},
            "next_gate": board["next_gate"],
        }
    }, indent=2))
    return 0


def cmd_cancel(args) -> int:
    d = _director(args.db, args.project_id)
    d.store.cancel(args.task_id, fencing=d.fencing)
    print(json.dumps({"cancelled": args.task_id}))
    return 0


def cmd_gates(args) -> int:
    store = Store(args.db)
    print(json.dumps(GateBoard(store, args.project_id).state(), indent=2))
    return 0


def cmd_gate_pass(args) -> int:
    d = _director(args.db, args.project_id)
    evidence = json.loads(args.evidence) if args.evidence else {}
    GateBoard(d.store, args.project_id).mark_passed(args.gate, d.fencing, evidence)
    print(json.dumps({"passed": args.gate}))
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--db", default="data/monetizeos.db")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init")
    s.add_argument("project_id")
    s.add_argument("--name")
    s.add_argument("--baseline")
    s.set_defaults(f=cmd_init)

    s = sub.add_parser("audit")
    s.add_argument("project_id")
    s.add_argument("--repo-root", default=".")
    s.add_argument("--artifact-dir")
    s.set_defaults(f=cmd_audit)

    s = sub.add_parser("enqueue")
    s.add_argument("project_id")
    s.add_argument("contract")
    s.add_argument("--priority", type=int, default=100)
    s.set_defaults(f=cmd_enqueue)

    s = sub.add_parser("run")
    s.add_argument("project_id")
    s.add_argument("--worker", default="worker-1")
    s.add_argument("--repo-root", default=".")
    s.add_argument("--artifact-dir")
    s.add_argument("--max-cycles", type=int, default=64)
    s.set_defaults(f=cmd_run)

    s = sub.add_parser("status")
    s.add_argument("project_id")
    s.set_defaults(f=cmd_status)
    s = sub.add_parser("cancel")
    s.add_argument("project_id")
    s.add_argument("task_id")
    s.set_defaults(f=cmd_cancel)
    s = sub.add_parser("gates")
    s.add_argument("project_id")
    s.set_defaults(f=cmd_gates)
    s = sub.add_parser("gate-pass")
    s.add_argument("project_id")
    s.add_argument("gate",
                                                  choices=RELEASE_GATES)
    s.add_argument("--evidence")
    s.set_defaults(f=cmd_gate_pass)

    args = p.parse_args()
    return args.f(args)


if __name__ == "__main__":
    raise SystemExit(main())
