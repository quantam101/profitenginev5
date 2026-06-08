from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runtime.eaos.cluster_master import ClusterTaskQueue


def main() -> int:
    agent_type = os.environ.get("AGENT_TYPE", "").strip()
    if not agent_type:
        print("[EAOS] ERROR: AGENT_TYPE is required")
        return 1

    directive = os.environ.get("DIRECTIVE", "").strip()
    if not directive:
        print("[EAOS] ERROR: DIRECTIVE is required")
        return 1

    payload_raw = os.environ.get("PAYLOAD_JSON", "{}")
    extra = json.loads(payload_raw) if payload_raw.strip() else {}
    # Merge directive into payload dict so ClusterTaskQueue.enqueue(agent_type, payload) works
    payload = {"directive": directive, **extra}
    queue = ClusterTaskQueue()

    if agent_type == "ALL":
        for lane in ["VIDEO", "SOCIAL", "POD"]:
            task_id = queue.enqueue(lane, payload)
            print(f"[Cluster] Enqueued {lane}::{directive} task_id={task_id}")
    else:
        task_id = queue.enqueue(agent_type, payload)
        print(f"[Cluster] Enqueued {agent_type}::{directive} task_id={task_id}")

    print("The cluster_master daemon on the OCI server picks up queued tasks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
