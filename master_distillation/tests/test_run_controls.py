import json
from types import SimpleNamespace

import pytest
import torch
from test_engine import PadCollator, model, rows
from torch.utils.data import DataLoader

from build_cache import text_signature
from dataset import CacheWriter, dedup_index, find_overlap
from distill_ddp import DDPDistillationEngine
from main import RunLock, gate_failures, publish_dir


def signatures(texts):
    return zip(*[text_signature(t) for t in texts], strict=True)


def test_text_signature_normalizes_case_and_whitespace():
    a_digest, a_sig = text_signature("  The   QUICK brown FOX ")
    b_digest, b_sig = text_signature("the quick brown fox")
    assert a_digest == b_digest
    assert torch.equal(a_sig, b_sig)


def test_find_overlap_detects_exact_and_near_duplicates(tmp_path):
    meta = dict(
        teacher_layers=[1],
        teacher_width=4,
        max_length=16,
        num_labels=2,
        vocab_size=16,
        pad_token_id=0,
    )
    for name, texts in {
        "a": ["the quick brown fox jumps over", "a completely unrelated sentence here"],
        "b": ["The QUICK brown FOX jumps over", "the quick brown fox jumps over!"],
    }.items():
        w = CacheWriter(tmp_path / name, meta, map_size=1 << 24)
        for record, text in zip(rows(2), texts, strict=True):
            w.append(record)
            w.track_dedup(*text_signature(text))
        w.close()
    index_a, index_b = dedup_index(tmp_path / "a"), dedup_index(tmp_path / "b")
    exact, near = find_overlap(index_a, index_b)
    assert len(exact) == 1  # "the quick brown fox jumps over" normalized
    # Exact duplicates also satisfy the near-duplicate threshold.
    assert near == [(0, 0), (0, 1)]
    manifest = json.loads((tmp_path / "a" / "manifest.json").read_text())
    assert manifest["dedup_sha256"] and manifest["exact_duplicate_rows"] == 0


def test_run_lock_exclusive_stale_and_forced(tmp_path):
    path = tmp_path / "run.lock"
    lock = RunLock(path)
    lock.acquire()
    with pytest.raises(RuntimeError, match="live pid"):
        RunLock(path).acquire()
    lock.release()
    RunLock(path).acquire()
    assert path.exists()

    # Stale lock: dead pid is reclaimed without force.
    path.write_text(json.dumps({"pid": 2**22 - 3, "host": "gone"}))
    import os

    assert not os.path.exists(f"/proc/{2**22 - 3}")
    RunLock(path).acquire()

    # Force overrides a live holder.
    path.write_text(json.dumps({"pid": os.getpid(), "host": "self"}))
    RunLock(path).acquire(force=True)


def test_gate_failures_thresholds():
    args = SimpleNamespace(
        min_validation_accuracy=0.9,
        min_macro_recall=0.8,
        min_per_class_recall=0.7,
    )
    metrics = {
        "validation_accuracy": 0.95,
        "macro_recall": 0.75,
        "per_class": [
            {"label": 0, "precision": 0.9, "recall": 0.8, "f1": 0.85, "support": 4},
            {"label": 1, "precision": 0.9, "recall": 0.6, "f1": 0.72, "support": 4},
        ],
    }
    failures = gate_failures(args, metrics)
    assert len(failures) == 2
    assert any("macro_recall" in f for f in failures)
    assert any("1" in f for f in failures)
    assert (
        gate_failures(
            SimpleNamespace(
                min_validation_accuracy=None,
                min_macro_recall=None,
                min_per_class_recall=None,
            ),
            metrics,
        )
        == []
    )


def test_publish_dir_swaps_atomically(tmp_path):
    final = tmp_path / "student"
    final.mkdir()
    (final / "old.bin").write_text("old")
    staging = tmp_path / "student.staging"
    staging.mkdir()
    (staging / "new.bin").write_text("new")
    publish_dir(staging, final)
    assert (final / "new.bin").exists()
    assert not (final / "old.bin").exists()
    assert not (tmp_path / "student.previous").exists()
    assert not staging.exists()


def test_evaluate_reports_per_class_metrics():
    torch.manual_seed(3)
    m = model()
    data = rows(8)
    loader = DataLoader(data, batch_size=3, collate_fn=PadCollator(0))
    engine = DDPDistillationEngine(m, torch.optim.SGD(m.parameters(), lr=0.0), torch.device("cpu"))
    result = engine.evaluate(m, loader)
    assert result["validation_samples"] == 8
    assert len(result["per_class"]) == 2
    assert sum(c["support"] for c in result["per_class"]) == 8
    assert 0.0 <= result["macro_recall"] <= 1.0
    assert 0.0 <= result["macro_f1"] <= 1.0
