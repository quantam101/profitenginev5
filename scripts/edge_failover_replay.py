from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runtime.edge_failover import EdgeFailoverEngine


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay staged edge failover payloads through the local mesh.")
    parser.add_argument("--limit", type=int, default=25)
    args = parser.parse_args()

    result = EdgeFailoverEngine().replay(limit=args.limit)
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
