# Lifelong Catch and Correct — change record

## 1.1.1 — 2026-09-22

Review hardening: evaluation no longer deadlocks when a rank holds an empty
validation shard (class count is agreed collectively before the confusion
reduction); `best.pt` now commits before `checkpoint.pt` so a crash between them
replays the epoch instead of losing the best model; export publication uses an
atomic symlink swap onto a versioned directory so readers never see a missing
model; the overlap threshold is bounded above 0.75 (the banded-MinHash recall
guarantee) in `find_overlap` and both CLIs; CI coverage moved to the repository
root workflow scoped to this package.

## 1.1.0 — 2026-09-22

Strengthened model-quality selection: evaluation now reports per-class
precision/recall/F1 and macro scores; training tracks the best-validation epoch
(`best.pt`) and export publishes best-epoch student weights rather than last-epoch
weights; `--min-validation-accuracy`, `--min-macro-recall` and
`--min-per-class-recall` withhold export and write `rejected.json` when unmet.

Added split-overlap detection and data lineage: every cache stores a checksummed
`dedup.safetensors` index (normalized-text SHA-256 plus 64-permutation MinHash per
row); `main.py` fails closed on exact or near-duplicate train/validation overlap,
`build_cache.py --reference` enforces separation at build time, and manifests
record `source_path`, `label_histogram` and `exact_duplicate_rows`.

Made run ownership and export publication robust: exclusive `run.lock` with
stale-pid reclaim and `--force-lock`, journal durability ahead of each checkpoint,
`metrics.jsonl` reconciliation on resume, and atomic `student/` publication with
`acceptance.json` inside the export.

## 1.0.0 — 2026-09-22

Corrected global-rank sharding and rank-zero writes, flushed and normalized partial
accumulation windows, integrated feature adapters into DDP, added explicit layer
mapping, masked normalized feature matching and correctly weighted objectives.

Replaced pickle with compressed safetensors records, added cache manifests and
integrity/shape checks, dynamic padding, spawn workers, pinned-memory loading,
dedicated CUDA transfer stream and tensor lifetime tracking.

Added hardware-aware AMP, gradient clipping/nonfinite rejection, optional dynamic
compilation, optimizer scheduling, epoch-level atomic checkpoints and resume
contract checks, exact held-out evaluation and cached-teacher accuracy, model export,
JSONL metrics, a mobile-readable offline report generator, Ruff/IDE integration and CI.

Recorded six passing CPU checks and three explicitly blocked runtime/hardware gates.
Removed unsupported speed, VRAM and linear-scaling promises. No remote model/code
downloads, API keys, autonomous semantic code changes or serving deployment included.
