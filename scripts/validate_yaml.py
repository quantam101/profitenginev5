from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator


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
    for yaml_path, schema_path in CHECKS:
        data = load_yaml(yaml_path)
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
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
