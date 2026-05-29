"""Tiny in-process pub/sub for WebSocket cycle events.

The hub keeps a set of live WebSocket connections. Anywhere in the backend
that wants to broadcast a cycle/agent/approval event calls `ws_hub.broadcast`
and every connected dashboard receives a JSON payload.

This is intentionally simple (no Redis, no fanout server) — pev5 runs in a
single FastAPI process for the preview / first cohort. Swap for Redis pub-sub
when scaling out.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from fastapi import WebSocket


class WSHub:
    def __init__(self) -> None:
        self._conns: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._conns.add(ws)

    async def disconnect(self, ws: WebSocket) -> None:
        async with self._lock:
            self._conns.discard(ws)

    async def broadcast(self, event: str, payload: dict[str, Any]) -> None:
        msg = {
            "event": event,
            "payload": payload,
            "at": datetime.now(timezone.utc).isoformat(),
        }
        # Snapshot to avoid mutation during iteration
        async with self._lock:
            conns = list(self._conns)
        dead: list[WebSocket] = []
        for ws in conns:
            try:
                await ws.send_json(msg)
            except Exception:  # noqa: BLE001
                dead.append(ws)
        if dead:
            async with self._lock:
                for ws in dead:
                    self._conns.discard(ws)


ws_hub = WSHub()
