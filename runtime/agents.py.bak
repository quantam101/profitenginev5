from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Dict, List


@dataclass(frozen=True)
class AgentExecution:
    output: str
    metrics: Dict[str, int | str]


def implementation_module(agent_id: str) -> str:
    return agent_id.replace("-", "_")


def load_agent(agent_id: str):
    module = import_module(f"runtime.agent_impls.{implementation_module(agent_id)}")
    agent = module.Agent()
    if getattr(agent, "id", None) != agent_id:
        raise ValueError(f"agent implementation id mismatch: expected={agent_id}, actual={getattr(agent, 'id', None)}")
    return agent


def implemented_agent_ids() -> set[str]:
    from pathlib import Path

    impl_dir = Path(__file__).parent / "agent_impls"
    return {
        path.stem.replace("_", "-")
        for path in impl_dir.glob("*.py")
        if path.name != "__init__.py"
    }
