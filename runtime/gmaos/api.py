"""
G-MAOS FastAPI Router
=====================
Mounts under /api/gmaos in the backend server.

Endpoints:
  POST /api/gmaos/run          — submit task(s) and wait for results
  POST /api/gmaos/fire         — submit task(s) fire-and-forget
  GET  /api/gmaos/health       — mesh health + circuit breaker map
  GET  /api/gmaos/task/{id}    — task status lookup
  GET  /api/gmaos/metrics      — Prometheus text metrics
  GET  /api/gmaos/dlq          — dead-letter queue listing
  POST /api/gmaos/dlq/drain    — manually trigger DLQ drain
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from .schema import Task, TaskPriority
from .metrics import metrics_text

router = APIRouter(prefix="/api/gmaos", tags=["gmaos"])


# ── request/response models ───────────────────────────────────────────────────

class TaskRequest(BaseModel):
    agent:      str
    payload:    dict[str, Any]             = Field(default_factory=dict)
    priority:   str                        = "NORMAL"
    max_retries: int                       = 3
    timeout_sec: float                     = 120.0

    def to_task(self) -> Task:
        return Task(
            agent       = self.agent,
            payload     = self.payload,
            priority    = TaskPriority[self.priority.upper()],
            max_retries = self.max_retries,
            timeout_sec = self.timeout_sec,
        )


class BatchRequest(BaseModel):
    tasks: list[TaskRequest]


# ── helpers ───────────────────────────────────────────────────────────────────

async def _get_mesh(request: Request):
    from .core import get_mesh
    return await get_mesh()


def _result_to_dict(r) -> dict:
    return {
        "task_id":    r.task_id,
        "agent":      r.agent,
        "status":     r.status.value,
        "output":     r.output,
        "tier":       r.tier,
        "duration_ms": r.duration_ms,
        "retry_count": r.retry_count,
        "cached":     r.cached,
        "trace_id":   r.trace_id,
        "error":      r.error,
        "tokens_in":  r.tokens_in,
        "tokens_out": r.tokens_out,
        "distilled":  r.distilled,
    }


# ── endpoints ─────────────────────────────────────────────────────────────────

@router.post("/run")
async def run_tasks(body: BatchRequest, request: Request):
    """Submit tasks and wait for all results."""
    if not body.tasks:
        raise HTTPException(status_code=400, detail="tasks list is empty")
    mesh  = await _get_mesh(request)
    tasks = [t.to_task() for t in body.tasks]
    results = await mesh.run(tasks)
    return {"results": [_result_to_dict(r) for r in results]}


@router.post("/run/single")
async def run_single(body: TaskRequest, request: Request):
    """Submit one task and wait for result."""
    mesh   = await _get_mesh(request)
    result = (await mesh.run([body.to_task()]))[0]
    return _result_to_dict(result)


@router.post("/fire")
async def fire_tasks(body: BatchRequest, request: Request):
    """Submit tasks fire-and-forget; returns task IDs immediately."""
    mesh  = await _get_mesh(request)
    ids   = []
    for req in body.tasks:
        task = req.to_task()
        await mesh.fire(task)
        ids.append(task.id)
    return {"queued": ids}


@router.get("/health")
async def health(request: Request):
    mesh = await _get_mesh(request)
    return mesh.health()


@router.get("/task/{task_id}")
async def get_task(task_id: str, request: Request):
    mesh   = await _get_mesh(request)
    record = mesh.store.load_task(task_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return record


@router.get("/metrics", response_class=PlainTextResponse)
async def prometheus_metrics():
    return PlainTextResponse(metrics_text(), media_type="text/plain")


@router.get("/dlq")
async def get_dlq(limit: int = 50, request: Request = None):
    mesh = await _get_mesh(request)
    return {"dlq": mesh.store.get_dlq(limit=limit)}


@router.post("/dlq/drain")
async def drain_dlq(request: Request):
    """Manually trigger watchdog DLQ drain."""
    mesh = await _get_mesh(request)
    mesh._watchdog._drain_dlq()
    return {"ok": True}
