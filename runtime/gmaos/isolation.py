"""
One agent call per OS process (opt-in: GMAOS_AGENT_ISOLATION=process).

A thread cannot be stopped: when a mesh task times out, its agent call keeps
running and holds a worker slot. A process can be killed, and a crash or
memory leak in one agent cannot take the mesh down with it.
"""
from __future__ import annotations

import multiprocessing as mp
import os
from typing import Any, Callable

_CTX = mp.get_context("spawn")  # fork is unsafe in a multi-threaded mesh


class IsolatedCallError(RuntimeError):
    """The child process failed, crashed, or was killed at its deadline."""


def isolation_enabled() -> bool:
    return os.getenv("GMAOS_AGENT_ISOLATION", "thread").lower() == "process"


def _child(conn, fn: Callable[..., Any], args: tuple, kwargs: dict) -> None:
    try:
        conn.send((True, fn(*args, **kwargs)))
    except BaseException as exc:  # noqa: BLE001 - report every failure to the parent
        conn.send((False, f"{type(exc).__name__}: {exc}"))
    finally:
        conn.close()


def call_in_process(
    fn: Callable[..., Any], *args: Any, timeout: float, **kwargs: Any
) -> Any:
    """Run fn(*args, **kwargs) in its own process; kill it after `timeout` seconds.

    fn, its arguments and its result must be picklable. Blocking: call it from
    a worker thread, not from the event loop.
    """
    parent, child = _CTX.Pipe(duplex=False)
    proc = _CTX.Process(target=_child, args=(child, fn, args, kwargs), daemon=True)
    proc.start()
    child.close()
    try:
        if not parent.poll(timeout):
            raise IsolatedCallError(f"TIMEOUT: killed after {timeout}s")
        try:
            ok, value = parent.recv()
        except EOFError:
            proc.join(1)
            raise IsolatedCallError(f"CRASHED: exit code {proc.exitcode}") from None
        if not ok:
            raise IsolatedCallError(value)
        return value
    finally:
        parent.close()
        if proc.is_alive():
            proc.kill()
        proc.join()
