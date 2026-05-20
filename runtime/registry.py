from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from .manifest_loader import load_yaml


class RegistryError(RuntimeError):
    pass


@dataclass(frozen=True)
class AgentPolicy:
    id: str
    name: str
    allowed_connectors: List[str]
    forbidden_actions: List[str]
    approval_required_actions: List[str]
    max_cost_usd: float
    verifier_required: bool


@dataclass(frozen=True)
class ConnectorPolicy:
    id: str
    state: str
    enabled: bool
    permissions: List[str]


class RuntimeRegistry:
    ALLOWED_CONNECTOR_STATES = {"free_core", "free_external"}

    def __init__(
        self,
        agents_path: str | Path = "agents/registry.yaml",
        connectors_path: str | Path = "connectors/registry.yaml",
    ) -> None:
        self.agents_path = Path(agents_path)
        self.connectors_path = Path(connectors_path)
        self.agents = self._load_agents()
        self.connectors = self._load_connectors()

    def _load_agents(self) -> Dict[str, AgentPolicy]:
        data = load_yaml(str(self.agents_path))
        agents = data.get("agents")
        if not isinstance(agents, list) or not agents:
            raise RegistryError("agents registry must contain a non-empty agents list")
        loaded: Dict[str, AgentPolicy] = {}
        for item in agents:
            if not isinstance(item, dict) or not item.get("id"):
                raise RegistryError("each agent entry must be an object with id")
            agent_id = str(item["id"])
            loaded[agent_id] = AgentPolicy(
                id=agent_id,
                name=str(item.get("name", agent_id)),
                allowed_connectors=list(item.get("allowed_connectors", [])),
                forbidden_actions=list(item.get("forbidden_actions", [])),
                approval_required_actions=list(item.get("approval_required_actions", [])),
                max_cost_usd=float(item.get("max_cost_usd", 0)),
                verifier_required=bool(item.get("verifier_required", True)),
            )
        return loaded

    def _load_connectors(self) -> Dict[str, ConnectorPolicy]:
        data = load_yaml(str(self.connectors_path))
        connectors = data.get("connectors")
        if not isinstance(connectors, dict) or not connectors:
            raise RegistryError("connector registry must contain a non-empty connectors object")
        loaded: Dict[str, ConnectorPolicy] = {}
        for connector_id, item in connectors.items():
            if not isinstance(item, dict):
                raise RegistryError(f"connector {connector_id} must be an object")
            loaded[str(connector_id)] = ConnectorPolicy(
                id=str(connector_id),
                state=str(item.get("state", "")),
                enabled=bool(item.get("enabled", False)),
                permissions=list(item.get("permissions", [])),
            )
        return loaded

    def agent(self, agent_id: str) -> AgentPolicy:
        try:
            return self.agents[agent_id]
        except KeyError as exc:
            raise RegistryError(f"unknown agent: {agent_id}") from exc

    def assert_connector_allowed(self, agent_id: str, connector_id: str) -> None:
        agent = self.agent(agent_id)
        connector = self.connectors.get(connector_id)
        if connector is None:
            raise RegistryError(f"unknown connector: {connector_id}")
        if connector_id not in agent.allowed_connectors:
            raise RegistryError(f"agent {agent_id} cannot use connector {connector_id}")
        if not connector.enabled:
            raise RegistryError(f"connector {connector_id} is disabled")
        if connector.state not in self.ALLOWED_CONNECTOR_STATES:
            raise RegistryError(f"connector {connector_id} has disallowed state {connector.state}")

    def status(self) -> Dict[str, Any]:
        return {
            "agents": sorted(self.agents),
            "enabled_connectors": sorted(connector_id for connector_id, connector in self.connectors.items() if connector.enabled),
        }
