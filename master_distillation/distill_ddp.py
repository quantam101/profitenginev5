"""Correctness-first DDP engine with per-example normalized objectives."""

import contextlib
import time

import torch
import torch.distributed as dist
import torch.nn as nn
import torch.nn.functional as F


def world():
    return dist.get_world_size() if dist.is_initialized() else 1


def reduce(tensor, op=dist.ReduceOp.SUM):
    if dist.is_initialized():
        dist.all_reduce(tensor, op=op)
    return tensor


def layer_map(student_depth, teacher_depth):
    if min(student_depth, teacher_depth) < 1:
        raise ValueError("Both models need transformer layers")
    return [
        (i, max(1, round(i * teacher_depth / student_depth))) for i in range(1, student_depth + 1)
    ]


class DistillationModel(nn.Module):
    def __init__(
        self,
        student,
        mapping,
        student_width,
        teacher_width,
        temperature=3.5,
        alpha_logit=0.5,
        alpha_feature=0.3,
    ):
        super().__init__()
        if (
            temperature <= 0
            or min(alpha_logit, alpha_feature) < 0
            or alpha_logit + alpha_feature > 1
        ):
            raise ValueError("Temperature must be positive; loss weights must sum to <= 1")
        if alpha_feature and not mapping:
            raise ValueError("Feature loss requires a layer mapping")
        self.student = student
        self.mapping = mapping
        self.temperature = temperature
        self.alpha_logit = alpha_logit
        self.alpha_feature = alpha_feature
        self.projections = (
            nn.ModuleList(
                [
                    nn.Identity()
                    if student_width == teacher_width
                    else nn.Linear(student_width, teacher_width, bias=False)
                    for _ in mapping
                ]
            )
            if alpha_feature
            else nn.ModuleList()
        )

    def forward(self, batch):
        outputs = self.student(
            input_ids=batch["input_ids"],
            attention_mask=batch["attention_mask"],
            output_hidden_states=bool(self.alpha_feature),
        )
        logits = outputs.logits.float()
        teacher = batch["logits"].float()
        if logits.shape != teacher.shape or logits.ndim != 2:
            raise ValueError("Student/teacher classification logit shapes differ")
        ce = F.cross_entropy(logits, batch["labels"], reduction="none")
        t = self.temperature
        kl = (
            F.kl_div(
                F.log_softmax(logits / t, dim=-1),
                F.log_softmax(teacher / t, dim=-1),
                reduction="none",
                log_target=True,
            ).sum(-1)
            * t
            * t
        )
        feature = torch.zeros_like(ce)
        mask = batch["attention_mask"].float()
        if self.alpha_feature:
            for (s, teacher_layer), projection in zip(self.mapping, self.projections, strict=True):
                sh = projection(outputs.hidden_states[s]).float()
                th = batch[f"hidden_{teacher_layer}"].float()
                if sh.shape != th.shape:
                    raise ValueError("Token alignment or hidden feature dimensions differ")
                # Equal per-example weight, independent of sequence length/padding.
                error = (
                    (F.layer_norm(sh, (sh.shape[-1],)) - F.layer_norm(th, (th.shape[-1],)))
                    .square()
                    .mean(-1)
                )
                feature = feature + (error * mask).sum(-1) / mask.sum(-1).clamp_min(1)
            feature = feature / len(self.mapping)
        losses = (
            (1 - self.alpha_logit - self.alpha_feature) * ce
            + self.alpha_logit * kl
            + self.alpha_feature * feature
        )
        return (
            losses,
            logits,
            torch.stack((ce.detach().sum(), kl.detach().sum(), feature.detach().sum())),
        )


def transfer(batch, device):
    return {k: v.to(device, non_blocking=True) for k, v in batch.items()}


def batches_on_device(loader, device, prefetch=True):
    """One batch ahead, explicit stream dependency and allocator lifetime tracking."""
    if device.type != "cuda" or not prefetch:
        for batch in loader:
            yield transfer(batch, device)
        return
    stream = torch.cuda.Stream(device=device)
    iterator = iter(loader)
    next_batch = None

    def enqueue():
        host = next(iterator, None)
        if host is None:
            return None
        with torch.cuda.stream(stream):
            return transfer(host, device)

    next_batch = enqueue()
    while next_batch is not None:
        current = torch.cuda.current_stream(device)
        current.wait_stream(stream)
        batch = next_batch
        for tensor in batch.values():
            tensor.record_stream(current)
        next_batch = enqueue()
        yield batch


def precision(device, requested="auto"):
    if device.type != "cuda":
        if requested not in ("auto", "fp32"):
            raise ValueError("CPU execution supports fp32 in this package")
        return None
    if requested == "auto":
        requested = "bf16" if torch.cuda.is_bf16_supported() else "fp16"
    if requested == "bf16" and not torch.cuda.is_bf16_supported():
        raise ValueError("This GPU does not support BF16")
    return {"bf16": torch.bfloat16, "fp16": torch.float16, "fp32": None}[requested]


class DDPDistillationEngine:
    def __init__(
        self,
        model,
        optimizer,
        device,
        grad_accum_steps=2,
        dtype=None,
        scheduler=None,
        max_grad_norm=1.0,
        prefetch=True,
    ):
        if grad_accum_steps < 1 or max_grad_norm <= 0:
            raise ValueError("Accumulation and max gradient norm must be positive")
        self.model, self.optimizer, self.device = model, optimizer, device
        self.accum, self.dtype = grad_accum_steps, dtype
        self.scheduler, self.max_grad_norm, self.prefetch = scheduler, max_grad_norm, prefetch
        self.scaler = torch.amp.GradScaler("cuda", enabled=dtype == torch.float16)
        self.updates = 0

    def autocast(self):
        return (
            torch.autocast(self.device.type, dtype=self.dtype)
            if self.dtype
            else contextlib.nullcontext()
        )

    def train_epoch(self, loader, sampler, epoch):
        if not len(loader):
            raise ValueError("No training batches: increase data or reduce world size")
        sampler.set_epoch(epoch)
        self.model.train()
        self.optimizer.zero_grad(set_to_none=True)
        # [total objective, CE, KL, features, samples, correct]
        stats = torch.zeros(6, device=self.device, dtype=torch.float64)
        count = torch.zeros((), device=self.device)
        nominal = loader.batch_size * self.accum
        if self.device.type == "cuda":
            torch.cuda.synchronize(self.device)
            torch.cuda.reset_peak_memory_stats(self.device)
        start = time.perf_counter()
        for step, batch in enumerate(batches_on_device(loader, self.device, self.prefetch)):
            boundary = (step + 1) % self.accum == 0 or step + 1 == len(loader)
            sync = (
                self.model.no_sync()
                if not boundary and hasattr(self.model, "no_sync")
                else contextlib.nullcontext()
            )
            with sync:
                with self.autocast():
                    losses, logits, parts = self.model(batch)
                    loss = losses.sum() / nominal
                self.scaler.scale(loss).backward()
            n = batch["labels"].numel()
            count.add_(n)
            stats[0].add_(losses.detach().sum())
            stats[1:4].add_(parts)
            stats[4].add_(n)
            stats[5].add_((logits.argmax(-1) == batch["labels"]).sum())
            if boundary:
                self.scaler.unscale_(self.optimizer)
                reduce(count)
                # DDP averages rank gradients; recover true global sample mean.
                factor = nominal * world() / count
                parameters = [p for p in self.model.parameters() if p.grad is not None]
                for p in parameters:
                    p.grad.mul_(factor)
                norm = nn.utils.clip_grad_norm_(parameters, self.max_grad_norm)
                finite = torch.isfinite(norm).to(torch.int32)
                reduce(finite, dist.ReduceOp.MIN)
                if not bool(finite):
                    raise FloatingPointError(
                        "Nonfinite gradients on a rank; no optimizer step committed"
                    )
                self.scaler.step(self.optimizer)
                self.scaler.update()
                if self.scheduler:
                    self.scheduler.step()
                self.optimizer.zero_grad(set_to_none=True)
                self.updates += 1
                count.zero_()
        if self.device.type == "cuda":
            torch.cuda.synchronize(self.device)
        elapsed = torch.tensor(time.perf_counter() - start, device=self.device)
        reduce(elapsed, dist.ReduceOp.MAX)
        reduce(stats)
        data = stats.cpu().tolist()
        peak = torch.tensor(
            torch.cuda.max_memory_allocated(self.device) if self.device.type == "cuda" else 0,
            device=self.device,
            dtype=torch.float64,
        )
        reduce(peak, dist.ReduceOp.MAX)
        return dict(
            epoch=epoch,
            loss=data[0] / data[4],
            ce=data[1] / data[4],
            kl=data[2] / data[4],
            feature=data[3] / data[4],
            accuracy=data[5] / data[4],
            samples=int(data[4]),
            seconds=elapsed.item(),
            samples_per_second=data[4] / elapsed.item(),
            peak_rank_vram_bytes=int(peak.item()),
            updates=self.updates,
        )

    @torch.inference_mode()
    def evaluate(self, module, loader):
        # Unwrapped model avoids DDP forward collectives with uneven validation shards.
        module.eval()
        stats = torch.zeros(4, device=self.device, dtype=torch.float64)
        confusion = None
        for batch in batches_on_device(loader, self.device, self.prefetch):
            with self.autocast():
                losses, logits, _ = module(batch)
            predictions = logits.argmax(-1)
            if confusion is None:
                confusion = torch.zeros(
                    logits.shape[-1], logits.shape[-1], device=self.device, dtype=torch.float64
                )
            confusion.index_put_(
                (batch["labels"], predictions),
                torch.ones_like(batch["labels"], dtype=confusion.dtype),
                accumulate=True,
            )
            stats[0].add_(losses.sum())
            stats[1].add_((predictions == batch["labels"]).sum())
            stats[2].add_(len(losses))
            stats[3].add_((batch["logits"].argmax(-1) == batch["labels"]).sum())
        reduce(stats)
        loss, correct, n, teacher_correct = stats.cpu().tolist()
        if not n:
            raise ValueError("Empty validation dataset")
        # Ranks with empty validation shards hold no confusion matrix; agree on
        # class count collectively so every rank enters this reduction.
        classes = torch.tensor(
            confusion.shape[0] if confusion is not None else 0,
            device=self.device,
            dtype=torch.int64,
        )
        reduce(classes, dist.ReduceOp.MAX)
        classes = int(classes.item())
        if not classes:
            raise ValueError("Empty validation dataset")
        if confusion is None:
            confusion = torch.zeros(classes, classes, device=self.device, dtype=torch.float64)
        reduce(confusion)
        confusion = confusion.cpu()
        per_class = []
        for index in range(confusion.shape[0]):
            tp = confusion[index, index].item()
            support = confusion[index].sum().item()
            predicted = confusion[:, index].sum().item()
            class_precision = tp / predicted if predicted else 0.0
            recall = tp / support if support else 0.0
            f1 = (
                2 * class_precision * recall / (class_precision + recall)
                if class_precision + recall
                else 0.0
            )
            per_class.append(
                {
                    "label": index,
                    "precision": class_precision,
                    "recall": recall,
                    "f1": f1,
                    "support": int(support),
                }
            )
        return {
            "validation_loss": loss / n,
            "validation_accuracy": correct / n,
            "validation_samples": int(n),
            "teacher_validation_accuracy": teacher_correct / n,
            "macro_recall": sum(c["recall"] for c in per_class) / len(per_class),
            "macro_f1": sum(c["f1"] for c in per_class) / len(per_class),
            "per_class": per_class,
        }
