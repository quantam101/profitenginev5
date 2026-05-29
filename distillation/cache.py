"""
Caching layer — pillar #4 (logic offloading).

If the same (compressed) input + task is requested again, serve the previous
answer from cache instead of paying tokens for it. Pure in-process dict cache
with optional TTL and size cap; the backend can swap this for Mongo trivially.
"""
from __future__ import annotations

import hashlib
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any


@dataclass
class CacheEntry:
    key: str
    value: Any
    saved_tokens: int
    created_at: float


class DistillationCache:
    """LRU + TTL cache keyed by ``sha256(task + compressed_text)``."""

    def __init__(self, max_entries: int = 512, ttl_seconds: int = 3600) -> None:
        self.max_entries = max_entries
        self.ttl_seconds = ttl_seconds
        self._store: OrderedDict[str, CacheEntry] = OrderedDict()
        self.hits = 0
        self.misses = 0
        self.tokens_saved = 0

    @staticmethod
    def make_key(task: str, text: str) -> str:
        digest = hashlib.sha256(f"{task}::{text}".encode("utf-8")).hexdigest()
        return digest[:32]

    def get(self, task: str, text: str) -> Any | None:
        key = self.make_key(task, text)
        entry = self._store.get(key)
        if entry is None:
            self.misses += 1
            return None
        if (time.time() - entry.created_at) > self.ttl_seconds:
            del self._store[key]
            self.misses += 1
            return None
        # LRU bump
        self._store.move_to_end(key)
        self.hits += 1
        self.tokens_saved += entry.saved_tokens
        return entry.value

    def put(self, task: str, text: str, value: Any, *, saved_tokens: int = 0) -> None:
        key = self.make_key(task, text)
        self._store[key] = CacheEntry(
            key=key, value=value, saved_tokens=saved_tokens, created_at=time.time(),
        )
        self._store.move_to_end(key)
        while len(self._store) > self.max_entries:
            self._store.popitem(last=False)

    def stats(self) -> dict[str, Any]:
        total = self.hits + self.misses
        return {
            "entries": len(self._store),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(self.hits / total, 4) if total else 0.0,
            "tokens_saved": self.tokens_saved,
            "ttl_seconds": self.ttl_seconds,
            "capacity": self.max_entries,
        }

    def clear(self) -> None:
        self._store.clear()
        self.hits = 0
        self.misses = 0
        self.tokens_saved = 0
