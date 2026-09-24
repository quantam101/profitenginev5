from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from medical_agent_mesh import MedicalAgentMesh, Settings


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the local medical logistics agent mesh")
    parser.add_argument("--source", type=Path, help="Verified local JSON opportunity source")
    parser.add_argument("--check", action="store_true", help="Validate configuration and Ollama only")
    args = parser.parse_args()
    try:
        mesh = MedicalAgentMesh(Settings())
        mesh.repo.initialize()
        mesh.client.healthcheck()
        result = {"status": "ready"} if args.check else mesh.run(args.source)
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}), file=sys.stderr)
        return 1
    print(json.dumps({"status": "completed", **result}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
