from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runtime.opportunity_intelligence import evaluate_payload


def main() -> int:
    source = sys.stdin.read().strip()
    if not source:
        raise SystemExit("stdin must contain a JSON opportunity payload")
    payload = json.loads(source)
    result = evaluate_payload(payload)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["decision"] in {"PROCEED", "COUNTER", "HUMAN_APPROVAL", "DISCARD"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
