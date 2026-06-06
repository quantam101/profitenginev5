from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runtime.enterprise_mesh import dispatch_default


def main() -> int:
    objective = " ".join(sys.argv[1:]).strip() or "maximize proof-first ProfitEngine revenue today"
    payload = dispatch_default(objective)
    print(json.dumps(payload, indent=2))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
