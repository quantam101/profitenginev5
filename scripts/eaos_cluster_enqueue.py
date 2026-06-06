#!/usr/bin/env python3
"""
EAOS cluster enqueue script — adds a task to the cluster queue.
Run by eaos-cluster.yml GitHub Actions workflow.
"""
from __future__ import annotations
import json, os, sys, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from runtime.eaos.cluster_master import ClusterTaskQueue

agent_type  = os.environ["AGENT_TYPE"]
directive   = os.environ["DIRECTIVE"]
payload_raw = os.environ.get("PAYLOAD_JSON", "{}").strip()
payload     = json.loads(payload_raw) if payload_raw else {}

queue = ClusterTaskQueue()

if agent_type == "ALL":
    for lane in ["VIDEO", "SOCIAL", "POD"]:
        tid = queue.enqueue(lane, directive, payload)
        print(f"[Cluster] Enqueued {lane}::{directive} → task_id={tid}")
else:
    tid = queue.enqueue(agent_type, directive, payload)
    print(f"[Cluster] Enqueued {agent_type}::{directive} → task_id={tid}")

print(f"\nNote: cluster_master.py daemon on OCI server picks up queued tasks.")
print(f"OCI Server: 129.146.167.73")
