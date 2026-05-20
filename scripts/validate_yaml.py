from __future__ import annotations

import json
from pathlib import Path
import sys

import yaml
from jsonschema import Draft202012Validator

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runtime.agents import implemented_agent_ids


CHECKS = [
    ("agents/registry.yaml", "schemas/agents.schema.json"),
    ("connectors/registry.yaml", "schemas/connectors.schema.json"),
    ("eaos.config.yaml", "schemas/eaos.schema.json"),
    ("observability/slo.yaml", "schemas/slo.schema.json"),
]


def load_yaml(path: str) -> object:
    with Path(path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_json(path: str) -> object:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    failed = False
    loaded_yaml = {}
    for yaml_path, schema_path in CHECKS:
        data = load_yaml(yaml_path)
        loaded_yaml[yaml_path] = data
        schema = load_json(schema_path)
        validator = Draft202012Validator(schema)
        errors = sorted(validator.iter_errors(data), key=lambda err: list(err.path))
        if errors:
            failed = True
            print(f"{yaml_path} failed {schema_path}:")
            for error in errors:
                location = ".".join(str(part) for part in error.path) or "<root>"
                print(f"  - {location}: {error.message}")
        else:
            print(f"{yaml_path}: schema ok")

    agents = loaded_yaml.get("agents/registry.yaml", {}).get("agents", [])
    connectors = set(loaded_yaml.get("connectors/registry.yaml", {}).get("connectors", {}))
    implemented_agents = implemented_agent_ids()
    for agent in agents:
        for connector in agent.get("allowed_connectors", []):
            if connector not in connectors:
                failed = True
                print(f"agents/registry.yaml: {agent['id']} references unknown connector {connector}")
        if agent["id"] not in implemented_agents and agent["id"] != "sovereign-orchestrator":
            failed = True
            print(f"agents/registry.yaml: {agent['id']} has no runtime.agent_impls implementation")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
