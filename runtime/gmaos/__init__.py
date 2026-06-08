"""
G-MAOS — Zero-Origin Global Multi-Agent Operating System
=========================================================
Production-grade, async-first orchestration mesh for ProfitEngine v5.

Public surface area (everything else is internal):

    from runtime.gmaos import Mesh, Task, TaskPriority, MeshResult

    mesh = Mesh()
    await mesh.start()
    results = await mesh.run([Task(id="t1", agent="content_gen", payload={...})])
    await mesh.stop()

Or use the singleton:

    from runtime.gmaos import get_mesh
    mesh = await get_mesh()
    results = await mesh.run(tasks)
"""

from .core import Mesh, get_mesh
from .schema import Task, TaskPriority, MeshResult, AgentStatus
from .metrics import metrics_text

__all__ = [
    "Mesh",
    "get_mesh",
    "Task",
    "TaskPriority",
    "MeshResult",
    "AgentStatus",
    "metrics_text",
]
