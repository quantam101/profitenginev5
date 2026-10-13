"""Growth experiment tracker — hypothesis → variant → measured result.

Zero-cost, deterministic, append-only. Experiments are events in a JSONL
ledger (event-sourced, so every conclusion traces back to the raw
observations — same lineage rule as the decision journal). No metric is
ever synthesized: ``record`` only stores values the caller actually
measured (CTR, publish rate, revenue, eval pass rate — whatever the
experiment declares as its ``metric``).

Ledger events (one JSON object per line):
    {"type": "created",    "id", "hypothesis", "metric", "variants": [...], "at"}
    {"type": "started",    "id", "at"}
    {"type": "observation", "id", "variant", "value", "unit?", "at", "note?"}
    {"type": "concluded",  "id", "winner", "reason", "at"}

A variant wins by highest mean observed value, but only after
``min_samples`` observations — a lead on one data point is noise, not a
result, so ``conclude`` refuses early and reports how many samples each
variant still needs.

CLI:
    python -m runtime.growth_experiments create \
        --id exp-seo-title-01 --hypothesis "Question titles lift CTR" \
        --metric ctr --variant control --variant question
    python -m runtime.growth_experiments start --id exp-seo-title-01
    python -m runtime.growth_experiments record --id exp-seo-title-01 \
        --variant question --value 0.043
    python -m runtime.growth_experiments conclude --id exp-seo-title-01
    python -m runtime.growth_experiments list [--json]
"""
from __future__ import annotations

import argparse
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

DEFAULT_LEDGER = Path("data/experiments/ledger.jsonl")
DEFAULT_MIN_SAMPLES = 3


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class Variant:
    name: str
    values: list[float] = field(default_factory=list)

    @property
    def mean(self) -> float | None:
        return round(sum(self.values) / len(self.values), 6) if self.values else None


@dataclass
class Experiment:
    id: str
    hypothesis: str
    metric: str
    variants: dict[str, Variant]
    status: str = "draft"  # draft | running | concluded
    created_at: str = ""
    started_at: str = ""
    concluded_at: str = ""
    winner: str = ""
    conclusion_reason: str = ""


def _append(ledger: Path, event: dict[str, Any]) -> None:
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, sort_keys=True) + "\n")


def load_experiments(ledger: Path) -> dict[str, Experiment]:
    """Replay the ledger into current experiment state."""
    exps: dict[str, Experiment] = {}
    if not ledger.exists():
        return exps
    for line in ledger.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        e = json.loads(line)
        etype = e.get("type")
        eid = e.get("id")
        if etype == "created":
            exps[eid] = Experiment(
                id=eid,
                hypothesis=e["hypothesis"],
                metric=e["metric"],
                variants={v: Variant(name=v) for v in e["variants"]},
                created_at=e.get("at", ""),
            )
        elif eid not in exps:
            # Events for unknown experiments are ignored — the ledger is
            # append-only and a missing create means a corrupt prefix.
            continue
        elif etype == "started":
            exps[eid].status = "running"
            exps[eid].started_at = e.get("at", "")
        elif etype == "observation":
            vname = e.get("variant")
            if vname in exps[eid].variants:
                exps[eid].variants[vname].values.append(float(e["value"]))
        elif etype == "concluded":
            exps[eid].status = "concluded"
            exps[eid].winner = e.get("winner", "")
            exps[eid].conclusion_reason = e.get("reason", "")
            exps[eid].concluded_at = e.get("at", "")
    return exps


def get_experiment(ledger: Path, exp_id: str) -> Experiment:
    exp = load_experiments(ledger).get(exp_id)
    if exp is None:
        raise SystemExit(f"unknown experiment: {exp_id}")
    return exp


def create_experiment(
    ledger: Path,
    hypothesis: str,
    metric: str,
    variants: Iterable[str],
    exp_id: str | None = None,
) -> Experiment:
    variants = [v.strip() for v in variants if v.strip()]
    if len(variants) < 2:
        raise SystemExit("an experiment needs at least 2 variants")
    if len(set(variants)) != len(variants):
        raise SystemExit("variant names must be unique")
    exp_id = exp_id or f"exp-{uuid.uuid4().hex[:8]}"
    if exp_id in load_experiments(ledger):
        raise SystemExit(f"experiment already exists: {exp_id}")
    _append(ledger, {
        "type": "created", "id": exp_id, "hypothesis": hypothesis,
        "metric": metric, "variants": variants, "at": _now(),
    })
    return get_experiment(ledger, exp_id)


def start_experiment(ledger: Path, exp_id: str) -> Experiment:
    exp = get_experiment(ledger, exp_id)
    if exp.status != "draft":
        raise SystemExit(f"cannot start experiment in status {exp.status}")
    _append(ledger, {"type": "started", "id": exp_id, "at": _now()})
    return get_experiment(ledger, exp_id)


def record_observation(
    ledger: Path, exp_id: str, variant: str, value: float, note: str = ""
) -> Experiment:
    exp = get_experiment(ledger, exp_id)
    if exp.status != "running":
        raise SystemExit(f"cannot record on experiment in status {exp.status}")
    if variant not in exp.variants:
        raise SystemExit(f"unknown variant '{variant}' (have: {sorted(exp.variants)})")
    event: dict[str, Any] = {
        "type": "observation", "id": exp_id, "variant": variant,
        "value": float(value), "at": _now(),
    }
    if note:
        event["note"] = note
    _append(ledger, event)
    return get_experiment(ledger, exp_id)


def conclude_experiment(
    ledger: Path, exp_id: str, min_samples: int = DEFAULT_MIN_SAMPLES
) -> Experiment:
    """Pick the winning variant by mean observed value.

    Refuses to conclude while any variant has fewer than ``min_samples``
    observations — calling a winner early manufactures confidence.
    """
    exp = get_experiment(ledger, exp_id)
    if exp.status == "draft":
        raise SystemExit("start the experiment before concluding")
    if exp.status == "concluded":
        raise SystemExit(f"already concluded: winner={exp.winner}")

    short = {v.name: min_samples - len(v.values)
             for v in exp.variants.values() if len(v.values) < min_samples}
    if short:
        needs = ", ".join(f"{k} needs {n} more" for k, n in sorted(short.items()))
        raise SystemExit(f"insufficient samples to conclude honestly: {needs}")

    winner = max(exp.variants.values(), key=lambda v: v.mean or 0.0)
    means = {v.name: v.mean for v in exp.variants.values()}
    reason = (
        f"{winner.name} mean {winner.mean} vs "
        + ", ".join(f"{k}={v}" for k, v in sorted(means.items()) if k != winner.name)
    )
    _append(ledger, {
        "type": "concluded", "id": exp_id, "winner": winner.name,
        "reason": reason, "at": _now(),
    })
    return get_experiment(ledger, exp_id)


def experiment_summary(exp: Experiment) -> dict[str, Any]:
    return {
        "id": exp.id,
        "status": exp.status,
        "hypothesis": exp.hypothesis,
        "metric": exp.metric,
        "variants": {
            name: {"samples": len(v.values), "mean": v.mean}
            for name, v in exp.variants.items()
        },
        "winner": exp.winner or None,
        "conclusion_reason": exp.conclusion_reason or None,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("create")
    p.add_argument("--id")
    p.add_argument("--hypothesis", required=True)
    p.add_argument("--metric", required=True)
    p.add_argument("--variant", action="append", required=True)

    p = sub.add_parser("start")
    p.add_argument("--id", required=True)

    p = sub.add_parser("record")
    p.add_argument("--id", required=True)
    p.add_argument("--variant", required=True)
    p.add_argument("--value", type=float, required=True)
    p.add_argument("--note", default="")

    p = sub.add_parser("conclude")
    p.add_argument("--id", required=True)
    p.add_argument("--min-samples", type=int, default=DEFAULT_MIN_SAMPLES)

    p = sub.add_parser("list")
    p.add_argument("--json", action="store_true")

    args = ap.parse_args(argv)

    if args.cmd == "create":
        exp = create_experiment(args.ledger, args.hypothesis, args.metric,
                                args.variant, args.id)
    elif args.cmd == "start":
        exp = start_experiment(args.ledger, args.id)
    elif args.cmd == "record":
        exp = record_observation(args.ledger, args.id, args.variant,
                                 args.value, args.note)
    elif args.cmd == "conclude":
        exp = conclude_experiment(args.ledger, args.id, args.min_samples)
    elif args.cmd == "list":
        exps = load_experiments(args.ledger)
        if args.json:
            print(json.dumps([experiment_summary(e) for e in exps.values()], indent=2))
        else:
            for e in exps.values():
                win = f" winner={e.winner}" if e.winner else ""
                print(f"{e.id} [{e.status}] {e.metric}: {e.hypothesis}{win}")
        return 0
    else:  # pragma: no cover
        return 2

    print(json.dumps(experiment_summary(exp), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
