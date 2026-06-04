"""
EAOS Enterprise Mesh — Shared-memory IPC bus.
POSIX mmap + fcntl for zero-copy inter-agent messaging.
"""
import os
import json
import mmap
import fcntl
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger("EAOS.Mesh")


@dataclass
class IPCMessage:
    sequence_id: int
    agent_target: str
    action_directive: str
    payload: Dict[str, Any]


class SharedMemoryEventBus:
    def __init__(self, filepath: str = "/tmp/eaos_ipc_ring.bus", size_bytes: int = 1024 * 1024):  # noqa: S108
        self.filepath   = filepath
        self.size       = size_bytes
        self._seq       = 0
        self._init_bus()

    def _init_bus(self) -> None:
        if not os.path.exists(self.filepath):
            with open(self.filepath, "wb") as f:
                f.write(b"\x00" * self.size)
        self._fh  = open(self.filepath, "r+b")
        self._mmap = mmap.mmap(self._fh.fileno(), self.size, access=mmap.ACCESS_WRITE)
        logger.info(f"[Mesh] Shared memory bus connected: {self.filepath} ({self.size // 1024} KB)")

    def broadcast(self, target: str, directive: str, payload: Dict[str, Any]) -> int:
        self._seq += 1
        msg = IPCMessage(self._seq, target, directive, payload)
        data = json.dumps({
            "seq": msg.sequence_id, "target": msg.agent_target,
            "directive": msg.action_directive, "data": msg.payload,
        }).encode("utf-8")
        if len(data) > self.size - 4:
            raise MemoryError("Message exceeds shared memory segment size")
        fcntl.flock(self._fh.fileno(), fcntl.LOCK_EX)
        try:
            self._mmap.seek(0)
            self._mmap.write(len(data).to_bytes(4, "big"))
            self._mmap.write(data)
            self._mmap.flush()
        finally:
            fcntl.flock(self._fh.fileno(), fcntl.LOCK_UN)
        logger.debug(f"[Mesh] Broadcast seq={self._seq} → {target}::{directive}")
        return self._seq

    def read_latest(self) -> Optional[Dict[str, Any]]:
        fcntl.flock(self._fh.fileno(), fcntl.LOCK_SH)
        try:
            self._mmap.seek(0)
            size = int.from_bytes(self._mmap.read(4), "big")
            if size == 0:
                return None
            return json.loads(self._mmap.read(size).decode("utf-8"))
        except Exception:
            return None
        finally:
            fcntl.flock(self._fh.fileno(), fcntl.LOCK_UN)

    def close(self) -> None:
        self._mmap.close()
        self._fh.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    bus = SharedMemoryEventBus()
    bus.broadcast("SOCIAL", "POST_ARTICLE", {"title": "Test", "url": "https://example.com"})
    msg = bus.read_latest()
    logger.info(f"[Mesh] Read back: {msg}")
    bus.close()
