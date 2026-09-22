#!/usr/bin/env python3
"""FYE queue runner — executes fye_run.py for every request JSON in
fye-queue/ and archives each request under fye-queue/processed/.

Triggered by the 'FYE pipeline run' workflow's push trigger (paths:
fye-queue/*.json), so a plain `git push` of a request file runs the
pipeline without needing an Actions-scope dispatch token. Processed files
move to processed/ so later pushes don't re-run old requests.

Request file shape (all fields optional except topic):
    {
      "topic": "Why the sky is blue",
      "niche": "science-explainer",
      "title": "optional video title",
      "monthly_views_target": 100000,
      "subscribers": 0,
      "watch_hours": 0,
      "shorts_views": 0,
      "human_reviewed": false
    }

Usage:
    python scripts/fye_queue.py run          # run every pending request
    python scripts/fye_queue.py list         # show pending requests
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

QUEUE_DIR = Path("fye-queue")
DONE_DIR = QUEUE_DIR / "processed"

_FIELDS = (
    ("topic", "--topic", str),
    ("niche", "--niche", str),
    ("title", "--title", str),
    ("monthly_views_target", "--monthly-views-target", str),
    ("subscribers", "--subscribers", str),
    ("watch_hours", "--watch-hours", str),
    ("shorts_views", "--shorts-views", str),
)


def _pending() -> list[Path]:
    if not QUEUE_DIR.is_dir():
        return []
    return sorted(p for p in QUEUE_DIR.glob("*.json") if p.is_file())


def _args_for(request_path: Path) -> list[str]:
    spec = json.loads(request_path.read_text())
    if not isinstance(spec, dict) or not spec.get("topic"):
        raise ValueError(f"{request_path}: needs a 'topic' string")
    args: list[str] = []
    for key, flag, conv in _FIELDS:
        if spec.get(key) not in (None, ""):
            args += [flag, conv(spec[key])]
    if spec.get("human_reviewed"):
        args.append("--human-reviewed")
    return args


def cmd_list() -> int:
    pending = _pending()
    if not pending:
        print("queue is empty")
        return 0
    for path in pending:
        spec = json.loads(path.read_text())
        print(f"{path.name}: topic={spec.get('topic')!r} niche={spec.get('niche')!r}")
    return 0


def cmd_run() -> int:
    pending = _pending()
    if not pending:
        print("queue is empty — nothing to run")
        return 0
    DONE_DIR.mkdir(parents=True, exist_ok=True)
    fye_script = Path(__file__).with_name("fye_run.py")
    failures = 0
    for request_path in pending:
        print(f"=== FYE queue: {request_path.name} ===")
        try:
            args = _args_for(request_path)
        except (ValueError, json.JSONDecodeError) as exc:
            print(f"invalid request: {exc}")
            failures += 1
            continue
        proc = subprocess.run(  # noqa: S603 -- fixed script path, args from committed JSON
            [sys.executable, os.fspath(fye_script), *args],
            capture_output=False,
            shell=False,
        )
        if proc.returncode != 0:
            failures += 1
            print(f"{request_path.name}: exited {proc.returncode}")
            continue
        dest = DONE_DIR / request_path.name
        dest.write_bytes(request_path.read_bytes())
        request_path.unlink()
        print(f"{request_path.name}: done -> {dest}")
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    command = argv[0] if argv else "run"
    if command == "run":
        return cmd_run()
    if command == "list":
        return cmd_list()
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
