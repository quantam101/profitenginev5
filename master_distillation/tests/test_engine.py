import copy
import json
import os
import socket
from types import SimpleNamespace

import pytest
import torch
import torch.distributed as dist
import torch.multiprocessing as mp
from torch import nn
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data import DataLoader, DistributedSampler

from dataset import CacheWriter, DistributedCachedTeacherDataset, PadCollator, worker_init_fn
from distill_ddp import (
    DDPDistillationEngine,
    DistillationModel,
    batches_on_device,
    layer_map,
    precision,
)


class TinyClassifier(nn.Module):
    def __init__(self, width=4):
        super().__init__()
        self.emb = nn.Embedding(16, width)
        self.head = nn.Linear(width, 2)

    def forward(self, input_ids, attention_mask, output_hidden_states=False):
        hidden = self.emb(input_ids)
        pooled = (hidden * attention_mask[..., None]).sum(1) / attention_mask.sum(1, keepdim=True)
        return SimpleNamespace(logits=self.head(pooled), hidden_states=(hidden, hidden))


def rows(n=10, width=4):
    g = torch.Generator().manual_seed(5)
    return [
        {
            "input_ids": torch.arange(1, i % 3 + 3),
            "attention_mask": torch.ones(i % 3 + 2, dtype=torch.long),
            "labels": torch.tensor(i % 2),
            "logits": torch.randn(2, generator=g),
            "hidden_1": torch.randn(i % 3 + 2, width, generator=g),
        }
        for i in range(n)
    ]


def model(width=4):
    return DistillationModel(TinyClassifier(), [(1, 1)], 4, width)


def test_padding_invariance_and_projection_gradients():
    torch.manual_seed(1)
    m = model(6)
    batch = PadCollator(0, multiple=1)(rows(2, 6))
    a = m(batch)[0]
    padded = {}
    for k, v in batch.items():
        if k in ("labels", "logits"):
            padded[k] = v
        else:
            padded[k] = torch.cat([v, v.new_zeros((2, 3, *v.shape[2:]))], dim=1)
    b = m(padded)[0]
    torch.testing.assert_close(a, b)
    a.sum().backward()
    assert m.projections[0].weight.grad.abs().sum() > 0


def test_partial_accumulation_equals_large_batches():
    torch.manual_seed(9)
    m = model()
    ref = copy.deepcopy(m)
    data = rows(9)
    sampler = DistributedSampler(data, num_replicas=1, rank=0, shuffle=False)
    loader = DataLoader(data, batch_size=2, sampler=sampler, collate_fn=PadCollator(0))
    opt = torch.optim.SGD(m.parameters(), lr=0.01)
    engine = DDPDistillationEngine(
        m, opt, torch.device("cpu"), grad_accum_steps=3, max_grad_norm=1e6
    )
    metrics = engine.train_epoch(loader, sampler, 0)
    refopt = torch.optim.SGD(ref.parameters(), lr=0.01)
    for batch in DataLoader(data, batch_size=6, collate_fn=PadCollator(0)):
        refopt.zero_grad()
        ref(batch)[0].mean().backward()
        refopt.step()
    assert engine.updates == 2
    assert metrics["samples"] == 9
    for p, q in zip(m.parameters(), ref.parameters(), strict=True):
        torch.testing.assert_close(p, q, atol=1e-7, rtol=1e-5)


def make_cache(path):
    meta = dict(
        teacher_layers=[1],
        teacher_width=4,
        max_length=16,
        num_labels=2,
        vocab_size=16,
        pad_token_id=0,
    )
    w = CacheWriter(path, meta, map_size=1 << 24)
    for row in rows(5):
        w.append(row)
    w.close()


def test_cache_roundtrip_and_checksum(tmp_path):
    path = tmp_path / "cache"
    make_cache(path)
    ds = DistributedCachedTeacherDataset(path)
    assert len(ds) == 5
    torch.testing.assert_close(ds[0]["logits"], rows(5)[0]["logits"])
    ds.close()
    manifest = json.loads((path / "manifest.json").read_text())
    manifest["data_sha256"] = "bad"
    (path / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="checksum"):
        DistributedCachedTeacherDataset(path)


def require_socket_bind(family):
    try:
        with socket.socket(family, socket.SOCK_STREAM) as sock:
            if family == socket.AF_INET:
                sock.bind(("127.0.0.1", 0))
            else:
                sock.bind(b"\0distillation-pytest-probe")
    except PermissionError:
        if os.environ.get("CI"):
            raise
        pytest.skip("Execution environment prohibits required socket binding")


def test_cache_spawn_worker_handoff(tmp_path):
    require_socket_bind(socket.AF_UNIX)
    path = tmp_path / "cache"
    make_cache(path)
    ds = DistributedCachedTeacherDataset(path)
    ds[0]  # Parent access must not leak a handle into spawned workers.
    loader = DataLoader(
        ds,
        batch_size=2,
        num_workers=2,
        multiprocessing_context="spawn",
        timeout=30,
        worker_init_fn=worker_init_fn,
        collate_fn=PadCollator(0),
    )
    assert sum(len(b["labels"]) for b in loader) == 5
    ds.close()


def test_bad_weights_and_task():
    with pytest.raises(ValueError):
        DistillationModel(TinyClassifier(), [(1, 1)], 4, 4, alpha_logit=0.8, alpha_feature=0.3)
    batch = PadCollator(0)(rows(1))
    batch["logits"] = torch.randn(1, 2, 2)
    with pytest.raises(ValueError, match="shapes"):
        model()(batch)
    assert layer_map(3, 12) == [(1, 4), (2, 8), (3, 12)]
    assert precision(torch.device("cpu")) is None


def distributed_worker(rank, path):
    torch.set_num_threads(1)
    dist.init_process_group(
        "gloo", init_method="file://" + path + "/rendezvous", rank=rank, world_size=2
    )
    try:
        torch.manual_seed(7)
        m = model(6)
        ddp = DDP(m)
        data = rows(10, 6)
        sampler = DistributedSampler(data, num_replicas=2, rank=rank, shuffle=False, drop_last=True)
        loader = DataLoader(data, batch_size=2, sampler=sampler, collate_fn=PadCollator(0))
        engine = DDPDistillationEngine(
            ddp,
            torch.optim.SGD(m.parameters(), lr=0.01),
            torch.device("cpu"),
            grad_accum_steps=2,
            max_grad_norm=1e6,
        )
        metrics = engine.train_epoch(loader, sampler, 0)
        # Uneven validation: 3 examples on rank 0, 2 on rank 1.
        validation = DataLoader(
            data[:5], batch_size=2, sampler=list(range(rank, 5, 2)), collate_fn=PadCollator(0)
        )
        result = engine.evaluate(m, validation)
        assert result["validation_samples"] == 5
        assert metrics["samples"] == 10
        assert engine.updates == 2
        torch.save(m.state_dict(), path + f"/rank{rank}.pt")
    finally:
        dist.destroy_process_group()


def test_two_rank_ddp_matches_global_batches(tmp_path):
    require_socket_bind(socket.AF_INET)
    try:
        mp.spawn(distributed_worker, args=(str(tmp_path),), nprocs=2, join=True)
    except mp.ProcessRaisedException as exc:
        # Only the observed Gloo permission failure is an environment skip.
        # CI must run this gate successfully, never downgrade it to a skip.
        if (
            "gloo/transport/tcp/device.cc" in str(exc)
            and "Operation not permitted" in str(exc)
            and not os.environ.get("CI")
        ):
            pytest.skip("Gloo transport creation denied by execution environment")
        raise
    a = torch.load(tmp_path / "rank0.pt", weights_only=True)
    b = torch.load(tmp_path / "rank1.pt", weights_only=True)
    for key in a:
        torch.testing.assert_close(a[key], b[key])
    torch.manual_seed(7)
    ref = model(6)
    opt = torch.optim.SGD(ref.parameters(), lr=0.01)
    data = rows(10, 6)
    for selected in (data[:8], data[8:]):
        opt.zero_grad()
        ref(PadCollator(0)(selected))[0].mean().backward()
        opt.step()
    for key, tensor in ref.state_dict().items():
        torch.testing.assert_close(a[key], tensor, atol=1e-7, rtol=1e-5)


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA hardware unavailable")
def test_cuda_prefetch_and_precision():
    device = torch.device("cuda", 0)
    loader = DataLoader(rows(5), batch_size=2, pin_memory=True, collate_fn=PadCollator(0))
    expected = list(loader)
    actual = list(batches_on_device(loader, device))
    torch.cuda.synchronize()
    for cpu, gpu in zip(expected, actual, strict=True):
        for key in cpu:
            torch.testing.assert_close(cpu[key], gpu[key].cpu())
    m = model().to(device)
    sampler = DistributedSampler(rows(5), num_replicas=1, rank=0, shuffle=False)
    loader = DataLoader(
        rows(5), batch_size=2, sampler=sampler, pin_memory=True, collate_fn=PadCollator(0)
    )
    engine = DDPDistillationEngine(
        m, torch.optim.AdamW(m.parameters()), device, dtype=precision(device)
    )
    assert engine.train_epoch(loader, sampler, 0)["samples"] == 5


def test_epoch_checkpoint_resume_matches_uninterrupted(tmp_path):
    from main import checkpoint, restore

    torch.manual_seed(17)
    data = rows(9)
    sampler = DistributedSampler(data, num_replicas=1, rank=0, shuffle=True, seed=9)
    loader = DataLoader(data, sampler=sampler, batch_size=2, collate_fn=PadCollator(0))

    def setup():
        m = model()
        opt = torch.optim.AdamW(m.parameters(), lr=0.002)
        scheduler = torch.optim.lr_scheduler.StepLR(opt, step_size=2, gamma=0.9)
        engine = DDPDistillationEngine(
            m, opt, torch.device("cpu"), grad_accum_steps=3, scheduler=scheduler
        )
        return m, engine

    a, engine_a = setup()
    engine_a.train_epoch(loader, sampler, 0)
    path = tmp_path / "checkpoint.pt"
    checkpoint(path, a, engine_a, 0, {"id": "test"}, 0, 1, torch.device("cpu"))
    engine_a.train_epoch(loader, sampler, 1)
    b, engine_b = setup()
    start = restore(path, b, engine_b, {"id": "test"}, 0, torch.device("cpu"))
    assert start == 1
    engine_b.train_epoch(loader, sampler, start)
    for p, q in zip(a.parameters(), b.parameters(), strict=True):
        torch.testing.assert_close(p, q, rtol=0, atol=0)
    assert engine_a.updates == engine_b.updates
    with pytest.raises(ValueError, match="contract"):
        restore(path, b, engine_b, {"id": "different"}, 0, torch.device("cpu"))
