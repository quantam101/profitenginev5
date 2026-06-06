from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runtime.edge_failover import EdgeFailoverEngine


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage or process a signed edge failover payload.")
    parser.add_argument("--tenant-id", required=True)
    parser.add_argument("--tracking-id", required=True)
    parser.add_argument("--payload", required=True)
    parser.add_argument("--signature", required=True)
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()

    engine = EdgeFailoverEngine()
    result = engine.ingest(
        tenant_id=args.tenant_id,
        tracking_id=args.tracking_id,
        payload=args.payload,
        signature=args.signature,
        server_online=not args.offline,
    )
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
