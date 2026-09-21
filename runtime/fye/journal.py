"""
Append-only, hash-chained decision journal.

Every agent gate decision is journaled with a sha256 chain so the record is
tamper-evident and replayable — this is the "journaled-decision verification"
side of the Command OS contract.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


class DecisionJournal:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("", encoding="utf-8")

    def _entries(self) -> List[Dict[str, Any]]:
        text = self.path.read_text(encoding="utf-8").strip()
        if not text:
            return []
        return [json.loads(line) for line in text.splitlines() if line.strip()]

    def _last_hash(self) -> str:
        entries = self._entries()
        return entries[-1]["hash"] if entries else "genesis"

    def append(self, agent: str, decision: str, data: Dict[str, Any]) -> Dict[str, Any]:
        entry = {
            "ts": time.time(),
            "agent": agent,
            "decision": decision,
            "data": data,
            "prev": self._last_hash(),
        }
        entry["hash"] = hashlib.sha256(
            json.dumps(entry, sort_keys=True).encode()
        ).hexdigest()
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, sort_keys=True) + "\n")
        return entry

    def verify_chain(self) -> bool:
        entries = self._entries()
        prev = "genesis"
        for e in entries:
            if e.get("prev") != prev:
                return False
            body = {k: v for k, v in e.items() if k != "hash"}
            if hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest() != e.get("hash"):
                return False
            prev = e["hash"]
        return True

    def find(self, agent: Optional[str] = None, decision: Optional[str] = None) -> List[Dict[str, Any]]:
        return [
            e for e in self._entries()
            if (agent is None or e["agent"] == agent)
            and (decision is None or e["decision"] == decision)
        ]

    def stats(self) -> Dict[str, Any]:
        entries = self._entries()
        return {
            "entries": len(entries),
            "chain_valid": self.verify_chain(),
            "path": os.fspath(self.path),
        }
