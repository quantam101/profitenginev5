# Validation evidence

Re-executed in this workspace on 2026-09-22 using Python 3.10.12,
PyTorch 2.14.0+cpu, Transformers 5.17.0, LMDB 2.3.0, safetensors 0.8.0,
zstandard 0.25.0, pytest 9.1.1 and Ruff 0.16.8.

Final result: **14 passed, 1 skipped (environment/hardware blocked)** in ~6 seconds.
Ruff lint checks pass for all Python files.

| Test | Result |
|---|---|
| Padding invariance and unequal-width projection gradients | Passed |
| Partial gradient accumulation equals true larger-batch updates | Passed |
| LMDB/safetensors cache round-trip and checksum rejection | Passed |
| Spawned DataLoader tensor handoff | Passed |
| Invalid loss weights/task shape rejection and depth mapping | Passed |
| Two-rank Gloo DDP versus global-batch numerical reference | Passed |
| Epoch checkpoint restore produces bitwise-identical subsequent CPU weights | Passed |
| Local Hugging Face cache creation, training, evaluation, export, resume | Passed |
| Text signature normalization (case/whitespace invariance) | Passed |
| Exact and near-duplicate split-overlap detection + dedup index integrity | Passed |
| Exclusive run lock: live-holder rejection, stale reclaim, forced override | Passed |
| Quality-gate failure enumeration | Passed |
| Atomic export directory publication | Passed |
| Per-class validation metrics | Passed |
| CUDA stream prefetch, GPU precision and training | Skipped: no CUDA hardware |

The local Hugging Face integration test uses small randomly initialized DistilBERT
models and deterministic synthetic text fixtures. It proves execution and data/model
contracts, not useful trained-model quality. Those fixtures are test-only; runtime
training requires real local model weights and labeled data.

The initial distributed test attempts returned actual environment errors, preserved
in environment-blocked-attempt.txt. Tests now identify only those specific permission
failures as environmental skips; unrelated errors still fail. In CI, these CPU
communication gates must pass and are not downgraded to skips. CUDA stays an explicit
hardware gate. Neither multi-GPU nor multi-node behavior was proven in this workspace.

## Required before production acceptance

1. Pass CUDA precision/prefetch tests; validate two-or-more GPU NCCL synchronization,
   unequal final accumulation windows and an actual multi-node run. (Gloo CPU
   equivalence and spawned-loader gates now pass in this workspace; NCCL and
   multi-node still require the target host.)
2. Compare eager/compiled results and inspect recompilation logs on representative
   variable sequence lengths. Run FP32 versus AMP numerical checks.
3. Interrupt a real distributed training run, restore the last completed epoch,
   verify optimizer/RNG continuity and exported inference behavior. (Single-rank
   resume correctness, journal/checkpoint reconciliation and lock reclamation are
   covered; a live multi-rank interruption remains a host gate.)
4. Establish teacher quality and real held-out student thresholds for the task,
   then set `--min-validation-accuracy`/`--min-macro-recall`/`--min-per-class-recall`.
   Split contamination is now fail-closed: exact and MinHash near-duplicate
   train/validation overlap aborts the run; per-class metrics are reported each
   epoch. Task-appropriate threshold values remain a data decision.
5. Measure 1/2/4/8-GPU throughput, allocated/reserved VRAM, host memory, storage,
   cache build cost and sustained runtime. Record hardware, driver, CUDA/NCCL,
   exact dependency lock and repeated trials.

Current conclusion: P0 quality gates, split-overlap detection and atomic
run/export controls implemented and CPU-verified. Production release, numerical
GPU equivalence, model quality, speedups, scaling and percentage VRAM savings
remain unverified. No claim of "100% optimized" or A+ certification.
