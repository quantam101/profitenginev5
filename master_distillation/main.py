"""Local-model sequence classification distillation; torchrun multi-node support."""

import argparse
import json
import math
import os
import random
import shutil
import time
from datetime import timedelta
from pathlib import Path

import torch
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data import DataLoader, DistributedSampler
from transformers import AutoTokenizer

from build_cache import load_classifier, model_signature
from dataset import (
    DistributedCachedTeacherDataset,
    PadCollator,
    dedup_index,
    find_overlap,
    tokenizer_digest,
    worker_init_fn,
)
from distill_ddp import DDPDistillationEngine, DistillationModel, layer_map, precision


def fsync_dir(path):
    fd = os.open(Path(path), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_save(state, path):
    tmp = path.with_suffix(".tmp")
    with open(tmp, "wb") as f:
        torch.save(state, f)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    fsync_dir(path.parent)


def publish_dir(staging, final):
    """Publish a staged export via an atomic symlink swap; readers never see a gap."""
    staging, final = Path(staging), Path(final)
    if final.is_symlink():
        pass
    elif final.exists():
        # Legacy plain-directory export: one-time migration before symlink publish.
        legacy = final.with_name(final.name + ".legacy")
        if legacy.exists():
            shutil.rmtree(legacy)
        os.rename(final, legacy)
    versioned = staging.with_name(f"{final.name}.{os.getpid()}.{int(time.time() * 1000)}")
    os.rename(staging, versioned)
    link = final.with_name(final.name + ".new")
    if link.exists() or link.is_symlink():
        link.unlink()
    link.symlink_to(versioned.name)
    os.replace(link, final)
    fsync_dir(versioned)
    fsync_dir(final.parent)
    for stale in final.parent.glob(final.name + ".*"):
        if stale == versioned or stale.is_symlink() or stale.name.endswith(".new"):
            continue
        if stale.is_dir():
            shutil.rmtree(stale)
    legacy = final.with_name(final.name + ".legacy")
    if legacy.exists():
        shutil.rmtree(legacy)


class RunLock:
    """Exclusive run ownership via an O_EXCL lock file with stale-pid reclaim."""

    def __init__(self, path):
        self.path = Path(path)
        self.acquired = False

    def acquire(self, force=False):
        payload = json.dumps(
            {"pid": os.getpid(), "host": os.uname().nodename, "created": time.time()}
        ).encode()
        for _ in range(2):
            try:
                fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                self._reclaim(force)
                continue
            os.write(fd, payload)
            os.fsync(fd)
            os.close(fd)
            self.acquired = True
            return
        raise RuntimeError(f"Could not acquire run lock at {self.path}")

    def _reclaim(self, force):
        try:
            info = json.loads(self.path.read_text())
            pid = int(info["pid"])
        except (OSError, ValueError, KeyError, TypeError):
            pid = None
        if pid is not None and not force:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                pass
            except PermissionError:
                raise RuntimeError(f"Run lock held by pid {pid} owned by another user")
            else:
                raise RuntimeError(
                    f"Run lock held by live pid {pid} ({info.get('host')}); "
                    "use --force-lock to override"
                )
        try:
            os.unlink(self.path)
        except FileNotFoundError:
            pass

    def release(self):
        if not self.acquired:
            return
        self.acquired = False
        try:
            os.unlink(self.path)
        except FileNotFoundError:
            pass


def gate_failures(args, metrics):
    failures = []
    if (
        args.min_validation_accuracy is not None
        and metrics["validation_accuracy"] < args.min_validation_accuracy
    ):
        failures.append(
            f"validation_accuracy {metrics['validation_accuracy']:.4f} "
            f"< {args.min_validation_accuracy}"
        )
    if args.min_macro_recall is not None and metrics["macro_recall"] < args.min_macro_recall:
        failures.append(f"macro_recall {metrics['macro_recall']:.4f} < {args.min_macro_recall}")
    if args.min_per_class_recall is not None:
        weak = [c["label"] for c in metrics["per_class"] if c["recall"] < args.min_per_class_recall]
        if weak:
            failures.append(f"per-class recall below {args.min_per_class_recall} on labels {weak}")
    return failures


def atomic_save_text(path, content):
    tmp = Path(path).with_suffix(".tmp")
    with open(tmp, "w") as f:
        f.write(content)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    fsync_dir(Path(path).parent)


def checkpoint(path, module, engine, epoch, contract, rank, world_size, device):
    rng = {
        "python": random.getstate(),
        "torch": torch.get_rng_state(),
        "cuda": torch.cuda.get_rng_state(device) if device.type == "cuda" else None,
    }
    states = [None] * world_size
    if dist.is_initialized():
        dist.all_gather_object(states, rng)
    else:
        states = [rng]
    if rank == 0:
        atomic_save(
            {
                "schema": 1,
                "epoch": epoch,
                "contract": contract,
                "model": module.state_dict(),
                "optimizer": engine.optimizer.state_dict(),
                "scheduler": engine.scheduler.state_dict(),
                "scaler": engine.scaler.state_dict(),
                "updates": engine.updates,
                "rng": states,
            },
            path,
        )
    if dist.is_initialized():
        dist.barrier()


def restore(path, module, engine, contract, rank, device):
    state = torch.load(path, map_location="cpu", weights_only=True)
    if state["schema"] != 1 or state["contract"] != contract:
        raise ValueError(
            "Resume contract changed: data, model, world size, or training configuration"
        )
    module.load_state_dict(state["model"])
    engine.optimizer.load_state_dict(state["optimizer"])
    engine.scheduler.load_state_dict(state["scheduler"])
    engine.scaler.load_state_dict(state["scaler"])
    engine.updates = state["updates"]
    rng = state["rng"][rank]
    random.setstate(rng["python"])
    torch.set_rng_state(rng["torch"])
    if device.type == "cuda":
        torch.cuda.set_rng_state(rng["cuda"], device)
    return state["epoch"] + 1


def loader_for(dataset, sampler, args, device):
    options = dict(
        batch_size=args.batch_size,
        sampler=sampler,
        num_workers=args.workers,
        pin_memory=device.type == "cuda",
        drop_last=False,
        collate_fn=PadCollator(dataset.meta["pad_token_id"], max_length=dataset.meta["max_length"]),
        generator=torch.Generator().manual_seed(args.seed + 17),
    )
    if args.workers:
        options.update(
            worker_init_fn=worker_init_fn,
            multiprocessing_context="spawn",
            persistent_workers=True,
            timeout=120,
            prefetch_factor=args.prefetch_factor,
        )
    return DataLoader(dataset, **options)


def run(args):
    rank = int(os.environ.get("RANK", "0"))
    local_rank = int(os.environ.get("LOCAL_RANK", "0"))
    world_size = int(os.environ.get("WORLD_SIZE", "1"))
    cuda = torch.cuda.is_available() and not args.cpu
    device = torch.device("cuda", local_rank) if cuda else torch.device("cpu")
    if cuda:
        torch.cuda.set_device(device)
    if world_size > 1:
        dist.init_process_group("nccl" if cuda else "gloo", timeout=timedelta(minutes=15))
    datasets = []
    try:
        random.seed(args.seed)
        torch.manual_seed(args.seed)
        if cuda:
            torch.cuda.manual_seed_all(args.seed)
        train = DistributedCachedTeacherDataset(args.cache)
        datasets.append(train)
        val = DistributedCachedTeacherDataset(args.validation_cache)
        datasets.append(val)
        for key in (
            "tokenizer_sha256",
            "teacher_sha256",
            "teacher_layers",
            "teacher_width",
            "teacher_depth",
            "num_labels",
            "id2label",
            "max_length",
            "pad_token_id",
        ):
            if train.meta[key] != val.meta[key]:
                raise ValueError(f"Train/validation metadata mismatch: {key}")
        if train.meta["source_sha256"] == val.meta["source_sha256"]:
            raise ValueError("Training and validation sources are identical")
        if not args.skip_overlap_check:
            exact, near = find_overlap(dedup_index(train), dedup_index(val), args.overlap_threshold)
            if exact or near:
                raise ValueError(
                    "Train/validation overlap detected: "
                    f"{len(exact)} exact duplicates, {len(near)} near-duplicate pairs"
                )
        if len(train) < world_size:
            raise ValueError("Fewer training examples than distributed ranks")
        tokenizer = AutoTokenizer.from_pretrained(
            args.student, local_files_only=True, trust_remote_code=False
        )
        if tokenizer_digest(tokenizer) != train.meta["tokenizer_sha256"]:
            raise ValueError("Student tokenizer does not match teacher cache")
        student = load_classifier(args.student)
        config = student.config
        if (
            config.num_labels != train.meta["num_labels"]
            or config.vocab_size != train.meta["vocab_size"]
        ):
            raise ValueError("Student class count or vocabulary differs from cache")
        if {str(k): v for k, v in config.id2label.items()} != train.meta["id2label"]:
            raise ValueError("Student class ordering differs from cache")
        if config.max_position_embeddings < train.meta["max_length"]:
            raise ValueError("Cache sequences exceed student positional limit")
        mapping = layer_map(config.num_hidden_layers, train.meta["teacher_depth"])
        if not {t for _, t in mapping}.issubset(train.meta["teacher_layers"]):
            raise ValueError("Cache lacks required teacher layers; rebuild for this student")
        module = DistillationModel(
            student,
            mapping,
            config.hidden_size,
            train.meta["teacher_width"],
            args.temperature,
            args.alpha_logit,
            args.alpha_feature,
        ).to(device)
        model = (
            DDP(
                module,
                device_ids=[local_rank] if cuda else None,
                broadcast_buffers=False,
                gradient_as_bucket_view=True,
            )
            if world_size > 1
            else module
        )
        if args.compile:
            model = torch.compile(model, dynamic=True, mode=args.compile_mode)
        sampler = DistributedSampler(
            train, num_replicas=world_size, rank=rank, shuffle=True, seed=args.seed, drop_last=True
        )
        train_loader = loader_for(train, sampler, args, device)
        # Exact nonduplicating validation partition; no padding or dropped examples.
        val_loader = loader_for(val, list(range(rank, len(val), world_size)), args, device)
        optimizer = torch.optim.AdamW(
            module.parameters(),
            lr=args.lr,
            weight_decay=args.weight_decay,
            fused=True if cuda else False,
        )
        steps = args.epochs * math.ceil(len(train_loader) / args.accum)
        warmup = min(args.warmup_steps, max(0, steps - 1))

        def multiplier(step):
            if step < warmup:
                return (step + 1) / max(1, warmup)
            return max(0.0, (steps - step) / max(1, steps - warmup))

        scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, multiplier)
        dtype = precision(device, args.precision)
        engine = DDPDistillationEngine(
            model,
            optimizer,
            device,
            args.accum,
            dtype,
            scheduler,
            args.max_grad_norm,
            not args.no_prefetch,
        )
        contract = {
            "student_sha256": model_signature(args.student),
            "train": train.meta,
            "validation": val.meta,
            "world_size": world_size,
            "arguments": {
                k: v
                for k, v in vars(args).items()
                if k not in ("resume", "output", "cache", "validation_cache", "student")
            },
            "torch": str(torch.__version__),
            "dtype": str(dtype),
        }
        output = Path(args.output)
        lock = RunLock(output / "run.lock")
        if rank == 0:
            output.mkdir(parents=True, exist_ok=True)
            lock.acquire(args.force_lock)
            if (output / "metrics.jsonl").exists() and not args.resume:
                raise FileExistsError("Existing run: use --resume or a new output directory")
        if dist.is_initialized():
            dist.barrier()
        try:
            start = (
                restore(args.resume, module, engine, contract, rank, device) if args.resume else 0
            )
            best_path = output / "best.pt"
            best = {"epoch": -1, "validation_accuracy": -math.inf, "validation_loss": math.inf}
            if rank == 0:
                (output / "run.json").write_text(json.dumps(contract, indent=2))
                if args.resume:
                    # Reconcile: drop metric rows from epochs the checkpoint did not commit.
                    journal = output / "metrics.jsonl"
                    if journal.exists():
                        kept = [
                            line
                            for line in journal.read_text().splitlines()
                            if json.loads(line).get("epoch", -1) < start
                        ]
                        atomic_save_text(journal, "\n".join(kept) + ("\n" if kept else ""))
                if best_path.exists():
                    prior = torch.load(best_path, map_location="cpu", weights_only=True)
                    best.update(
                        epoch=prior["epoch"],
                        validation_accuracy=prior["metrics"]["validation_accuracy"],
                        validation_loss=prior["metrics"]["validation_loss"],
                    )
            for epoch in range(start, args.epochs):
                metrics = engine.train_epoch(train_loader, sampler, epoch)
                metrics.update(engine.evaluate(module, val_loader))
                metrics.update(
                    dropped_training_examples=len(train) % world_size,
                    effective_full_batch=args.batch_size * args.accum * world_size,
                )
                if rank == 0:
                    # Metrics are durable before the checkpoint so a crash can never
                    # leave a committed checkpoint without its journal row.
                    with open(output / "metrics.jsonl", "a") as f:
                        f.write(json.dumps(metrics) + "\n")
                        f.flush()
                        os.fsync(f.fileno())
                    print(json.dumps(metrics), flush=True)
                better = metrics["validation_accuracy"] > best["validation_accuracy"] or (
                    metrics["validation_accuracy"] == best["validation_accuracy"]
                    and metrics["validation_loss"] < best["validation_loss"]
                )
                if better:
                    best.update(
                        epoch=epoch,
                        validation_accuracy=metrics["validation_accuracy"],
                        validation_loss=metrics["validation_loss"],
                    )
                    if rank == 0:
                        # best.pt commits before checkpoint.pt: a crash between them
                        # replays the epoch on resume rather than losing the best model.
                        atomic_save(
                            {
                                "epoch": epoch,
                                "metrics": metrics,
                                "model": module.student.state_dict(),
                            },
                            best_path,
                        )
                checkpoint(
                    output / "checkpoint.pt",
                    module,
                    engine,
                    epoch,
                    contract,
                    rank,
                    world_size,
                    device,
                )
            if rank == 0:
                if not best_path.exists():
                    raise RuntimeError("No best checkpoint recorded; nothing to export")
                state = torch.load(best_path, map_location="cpu", weights_only=True)
                failures = gate_failures(args, state["metrics"])
                if failures:
                    atomic_save_text(
                        output / "rejected.json",
                        json.dumps(
                            {
                                "accepted": False,
                                "failures": failures,
                                "epoch": state["epoch"],
                                "metrics": state["metrics"],
                            },
                            indent=2,
                        ),
                    )
                    raise RuntimeError("Export withheld: " + "; ".join(failures))
                module.student.load_state_dict(state["model"])
                staging = output / "student.staging"
                if staging.exists():
                    shutil.rmtree(staging)
                module.student.save_pretrained(staging, safe_serialization=True)
                tokenizer.save_pretrained(staging)
                acceptance = {
                    "schema": 1,
                    "accepted": True,
                    "epoch": state["epoch"],
                    "metrics": state["metrics"],
                }
                atomic_save_text(staging / "acceptance.json", json.dumps(acceptance, indent=2))
                publish_dir(staging, output / "student")
            if dist.is_initialized():
                dist.barrier()
        finally:
            lock.release()
    finally:
        for dataset in datasets:
            dataset.close()
        if dist.is_initialized():
            dist.destroy_process_group()


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("student", "cache", "validation-cache", "output"):
        p.add_argument("--" + name, required=True)
    p.add_argument("--resume")
    p.add_argument("--epochs", type=int, default=3)
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--accum", type=int, default=2)
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--prefetch-factor", type=int, default=2)
    p.add_argument("--lr", type=float, default=5e-5)
    p.add_argument("--weight-decay", type=float, default=0.01)
    p.add_argument("--warmup-steps", type=int, default=100)
    p.add_argument("--max-grad-norm", type=float, default=1.0)
    p.add_argument("--temperature", type=float, default=3.5)
    p.add_argument("--alpha-logit", type=float, default=0.5)
    p.add_argument("--alpha-feature", type=float, default=0.3)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--precision", choices=["auto", "bf16", "fp16", "fp32"], default="auto")
    p.add_argument("--compile", action="store_true")
    p.add_argument(
        "--compile-mode", choices=["default", "max-autotune-no-cudagraphs"], default="default"
    )
    p.add_argument("--no-prefetch", action="store_true")
    p.add_argument("--cpu", action="store_true")
    p.add_argument("--min-validation-accuracy", type=float)
    p.add_argument("--min-macro-recall", type=float)
    p.add_argument("--min-per-class-recall", type=float)
    p.add_argument("--overlap-threshold", type=float, default=0.85)
    p.add_argument("--skip-overlap-check", action="store_true")
    p.add_argument("--force-lock", action="store_true")
    args = p.parse_args()
    if not 0.75 < args.overlap_threshold <= 1:
        p.error("overlap-threshold must exceed 0.75 (banded MinHash recall bound)")
    if min(args.epochs, args.batch_size, args.accum, args.prefetch_factor) < 1 or args.workers < 0:
        p.error("Invalid batch/epoch/accumulation/worker setting")
    if args.lr <= 0 or args.weight_decay < 0 or args.warmup_steps < 0:
        p.error("Invalid learning rate, weight decay, or warmup")
    return args


if __name__ == "__main__":
    run(parse_args())
