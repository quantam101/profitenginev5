# Multi-GPU Master Distillation Engine — corrected engineering package

Status: CPU validation results are in VALIDATION.md. CUDA, NCCL multi-node,
compiled GPU execution, and real task quality remain release gates. No numerical
speedup, compression ratio, or production certification is claimed.

## Scope and requirements

Single-text, single-label sequence classification, matching the supplied
AutoModelForSequenceClassification entrypoint. This is not a causal language model
trainer. Student and teacher must use identical tokenization and class ordering.
Teacher must already be trained for the task. Local complete safetensors model
folders and separate labeled train/validation JSONL data are required. No model
weights or private data were supplied, so the package does not contain them.

Each JSONL record has a string `text` and integer `label` in [0, num_labels).
Sentence pairs, multilabel classification, regression, token classification,
LLM next-token shifting, token-vocabulary KL, different tokenizers, sparse top-k
teacher distributions and attention distillation are not supported by this version.
BERT-style encoder classifiers must expose num_hidden_layers, hidden_size,
max_position_embeddings and per-layer hidden states. A real local DistilBERT
pipeline is exercised in the integration test. Other architectures need validation.

Linux and Python 3.12 are the tested runtime family. Install the CUDA-compatible
PyTorch 2.14.0 wheel for your driver using PyTorch's official installer selector;
then install `requirements.txt`. The CPU suite uses torch 2.14.0+cpu. Version pins
record tested direct dependencies, not a full dependency supply-chain attestation.

```
python -m pip install -r requirements.txt
python -m ruff check .
OMP_NUM_THREADS=1 python -m pytest -q
```

## Build teacher caches

Paths below are operator-supplied local artifacts, not bundled demonstration models.
The same student architecture must be selected for cache creation and training.
Every cache directory must be new. Never modify an active cache, including replacing
its data.mdb in place. Copy completed caches to node-local NVMe on every host.
Lock files must be writable; data reads use normal LMDB reader locking.

```
python build_cache.py --teacher /models/teacher --student /models/student \
  --input /data/train.jsonl --output /data/train-cache --max-length 512
python build_cache.py --teacher /models/teacher --student /models/student \
  --input /data/validation.jsonl --output /data/validation-cache --max-length 512
```

Only mapped teacher layers are saved; hidden tensors default to BF16 storage and
logits to FP32. This saves storage and transfer bytes compared with FP32 hidden
caches, with possible precision tradeoffs. `--target-dtype fp32` is available.
Cache creation uses teacher FP32 inference to prioritize target quality. It is
single-process and can be expensive; cache-generation cost belongs in end-to-end
ROI calculations. A completion manifest appears only after successful generation.
Existing pickle caches must be rebuilt; no unsafe pickle migration is included.

## Train

Single host, four GPUs:

```
python -m torch.distributed.run --standalone --nproc-per-node=4 main.py \
  --student /models/student --cache /data/train-cache \
  --validation-cache /data/validation-cache --output /runs/distillation \
  --epochs 3 --batch-size 32 --accum 2
```

Effective full-window batch = batch per rank × accumulation × world size (256
above). The last window is normalized by its actual global example count. Training
sampler drops fewer than WORLD_SIZE examples per epoch instead of duplicating
examples; the shuffled omissions rotate. The count is logged. DataLoader keeps
partial batches. Validation covers every record exactly once across all ranks.

Multi-node: use the same source, model artifacts, manifests and arguments on every
host, and a shared output/checkpoint directory. Set TRAIN_RDZV to a reachable private
coordinator host:port and TRAIN_JOB_ID to a unique run ID before launching on each host:

```
python -m torch.distributed.run --nnodes=2 --nproc-per-node=4 \
  --rdzv-backend=c10d --rdzv-endpoint="$TRAIN_RDZV" --rdzv-id="$TRAIN_JOB_ID" \
  main.py --student /models/student --cache /data/train-cache \
  --validation-cache /data/validation-cache --output /shared/runs/distillation
```

Distributed collectives are for a trusted private cluster. Do not expose rendezvous
or NCCL ports to the public internet. This package does not provision a network,
credentials, GPUs, Kubernetes, or an authentication layer.

Resume: repeat the exact launch with `--resume /runs/distillation/checkpoint.pt`.
Checkpoints commit at epoch boundaries and include projections, optimizer,
scheduler, scaler and every rank's Python/CPU/CUDA RNG state. Resume rejects changed
models, cache identities, world size and training settings. A mid-epoch failure
replays from the prior completed epoch; world-size-changing elastic resume is not
supported. The fixed epoch schedule cannot be extended through this resume path.

Output includes `student/` (model and tokenizer), `checkpoint.pt`, `best.pt`,
`run.json`, `metrics.jsonl`, and `acceptance.json` inside the export. Export
removes teacher and feature projections from inference and always publishes the
best-validation-epoch student weights, not the last epoch. Checkpoint files use
restricted `weights_only=True` loading. Use only artifacts from trusted storage;
checksums detect accidental changes, not malicious replacement of both payload
and manifest.

## Run ownership, split overlap and quality gates

- `output/run.lock` grants exclusive run ownership per output directory. A stale
  lock from a dead process is reclaimed automatically; `--force-lock` overrides a
  live holder. Journal rows are durable before each epoch checkpoint, and resume
  reconciles `metrics.jsonl` against the restored epoch.
- Caches carry a checksummed `dedup.safetensors` index (normalized-text SHA-256
  plus a 64-permutation MinHash signature per row). `main.py` fails closed on any
  exact or near-duplicate train/validation overlap (`--overlap-threshold`,
  `--skip-overlap-check` to bypass); `build_cache.py --reference <cache>` applies
  the same check at cache build time. The manifest records `source_path`,
  `label_histogram` and `exact_duplicate_rows` as data lineage.
- Held-out quality gates withhold export when thresholds are not met:
  `--min-validation-accuracy`, `--min-macro-recall` and
  `--min-per-class-recall`. Rejection writes `rejected.json` and exits nonzero;
  acceptance publishes `student/` atomically with `acceptance.json` recording
  the epoch and metrics. Evaluation reports per-class precision/recall/F1 and
  macro scores every epoch.

## Correctness changes

- Global RANK selects sampler shards; LOCAL_RANK selects a GPU. Only global rank 0 writes.
- no_sync covers both forward and backward; the final partial window always synchronizes.
- Gradients use true global example normalization, including unequal final microbatch sizes.
- Explicit layer-depth mapping replaces silent zip truncation; trainable width projections
  live inside DDP and optimizer state. Feature loss is padding-masked, layer-normalized,
  averaged per layer, then per example. This objective differs from raw unmasked MSE.
- CE/KL/features use weights (1-alpha_logit-alpha_feature, alpha_logit, alpha_feature).
  Defaults are 0.2/0.5/0.3; your original objective was 0.5/0.5/0.3 (total 1.3).
- FP32 loss math, hardware-selected BF16 or FP16 AMP, FP16-only scaling, gradient
  clipping and rank-consistent nonfinite rejection. Nonfinite steps abort instead
  of silently claiming recovery; diagnose before resuming.
- Dynamic padding handles variable lengths. Spawned persistent workers isolate LMDB
  handles. Records use zstd+safetensors, shape/dtype/finite validation and a checksum.
- Dedicated H2D stream, dependency waits and record_stream guard device tensor lifetimes.
  GPU-bound transfer sources are pinned by DataLoader. Overlap is hardware/workload dependent.
- No per-microbatch loss.item(). The finite-gradient decision synchronizes once per
  optimizer update intentionally. Metrics accumulate on-device and reduce per epoch.
- Exact validation records both student and cached-teacher accuracy. No automatic model
  promotion: acceptance requires your task's held-out quality and operational criteria.

## Tune using measurements

Start eager. `--compile` enables DDP-aware compilation with dynamic=True;
`--compile-mode max-autotune-no-cudagraphs` is optional. Dynamic shapes reduce some
shape specialization; they do not guarantee zero recompiles. Use
`TORCH_LOGS=recompiles` to inspect behavior. Max autotune can cost more than it saves
on short runs. Do not suppress compiler errors silently.

Compare workers 0/2/4/8, prefetch-factor 1/2, H2D prefetch enabled/disabled,
precision auto/fp32, batch size and compilation independently. Keep effective batch,
seed, data, optimizer schedule and task accuracy comparable. Profile on the actual
GPU/interconnect/storage combination. Increase batch size only within a measured
VRAM margin; do not auto-catch OOM on individual ranks and continue a corrupted run.

The engine reports training samples/sec, maximum rank time, peak allocated rank VRAM,
loss components, validation accuracy and teacher validation accuracy. Throughput
excludes validation/checkpoint/checksum time and includes data iteration and training.
First-epoch measurements may include compiler warmup. Peak allocated VRAM is not
whole-process/device reserved memory. Repeat timed trials and report medians and
spread. Benchmark 1/2/4/8 GPUs; scaling efficiency is throughput_N/(N*throughput_1).
Include cache build time, storage, host RAM and validation quality in comparisons.

Caching removes teacher-model residency from the training step, but cached teacher
activations, student activations, projection parameters, gradients, optimizer state
and prefetch buffers still occupy memory. DDP replicates the whole student per GPU;
use a separately validated FSDP/ZeRO implementation if one replica does not fit.
Do not bolt FSDP onto this code without revisiting checkpoint and gradient logic.

## Mobile results and maintenance

```
python report.py /runs/distillation/metrics.jsonl /runs/distillation/report.html
```

The resulting offline HTML opens on desktop or mobile and contains real recorded
metrics. It is a results viewer, not a mobile GPU trainer or an AI chat assistant.
The delivered review.html opens without setup and reports this package's validation.
No secret keys are embedded or required. No cloud API calls occur during local
training. SEO is not applicable to a private training process; metrics remain local.

Ruff lint/auto-fix/format, VS Code Pylance recommendations and CPU CI are included.
The Lifelong Catch and Correct workflow catches regressions and records results.
It does not pretend to install paid coding assistants or run an autonomous Codex
service without an authorized account/runtime. Automatic code repair is limited
to Ruff's explicit safe fixes; semantic repairs require tests and review.

## Original claims review

| Claim | Finding |
|---|---|
| All bottlenecks eliminated | Unsupported; decoding, PCIe, storage, all-reduce and compute remain |
| Zero-copy end to end | False; original txn.get returns bytes, decompression allocates, unpickling/casts copy, H2D copies |
| Worker threads | DataLoader num_workers uses processes |
| No lock contention | Read-only environments do not establish this; lock=False requires external concurrency discipline |
| Overlapped CUDA streams | No dedicated stream was present in the original code |
| No shape recompilation | compile mode alone cannot guarantee this |
| 65% VRAM reduction | Requires measured model/batch/optimizer baseline |
| 4–6x speedup | Requires matched hardware, quality, warmup and cache-cost accounting |
| Linear GPU scaling | Depends on batch size, topology, communication and storage |
| Universal distillation | Supplied CE/input head supports classification, not general causal-LM training |

Original grade: C for production readiness; useful architectural direction, blocked
by correctness and missing operational evidence. No A+ runtime grade is awarded
until target-hardware correctness, recovery, quality and sustained performance pass.

## Primary references reviewed

- https://docs.pytorch.org/docs/2.14/notes/ddp.html
- https://docs.pytorch.org/docs/2.14/notes/amp_examples.html
- https://docs.pytorch.org/docs/2.14/generated/torch.compile.html
- https://docs.pytorch.org/docs/stable/generated/torch.Tensor.record_stream.html
- https://lmdb.readthedocs.io/en/latest/
