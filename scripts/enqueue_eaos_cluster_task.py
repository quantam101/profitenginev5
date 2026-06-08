from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

if not os.environ.get("EAOS_DB_PATH") and os.environ.get("EAOS_CLUSTER_DB"):
    os.environ["EAOS_DB_PATH"] = os.environ["EAOS_CLUSTER_DB"]

from runtime.eaos.cluster_master import ClusterTaskQueue

VALID_LANES = ("VIDEO", "SOCIAL", "POD", "MESH")


def main() -> int:
    agent_type = os.environ.get("AGENT_TYPE", "").strip().upper()
    if not agent_type:
        print("ERROR: AGENT_TYPE is required")
        return 1

    if agent_type != "ALL" and agent_type not in VALID_LANES:
        print(f"ERROR: unsupported AGENT_TYPE {agent_type}")
        return 1

    directive = os.environ.get("DIRECTIVE", "").strip()
    if not directive:
        print("ERROR: DIRECTIVE is required")
        return 1

    payload_raw = os.environ.get("PAYLOAD_JSON", "{}")
    try:
        extra = json.loads(payload_raw) if payload_raw.strip() else {}
    except json.JSONDecodeError as exc:
        print(f"ERROR: payload_json must be valid JSON: {exc}")
        return 2

    if not isinstance(extra, dict):
        print("ERROR: payload_json must be a JSON object")
        return 2

    payload = {"directive": directive, **extra}
    queue = ClusterTaskQueue()

    lanes = VALID_LANES if agent_type == "ALL" else (agent_type,)
    for lane in lanes:
        task_id = queue.enqueue(lane, payload)
        print(f"[Cluster] Enqueued {lane}::{directive} task_id={task_id}")

    print("The cluster_master daemon on the OCI server picks up queued tasks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
