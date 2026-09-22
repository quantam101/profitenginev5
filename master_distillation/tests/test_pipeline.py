import json
from types import SimpleNamespace

import torch
from transformers import BertTokenizerFast, DistilBertConfig, DistilBertForSequenceClassification

from build_cache import build
from main import run


def test_local_hf_cache_training_export_and_resume(tmp_path):
    torch.set_num_threads(1)
    vocab = ["[PAD]", "[UNK]", "[CLS]", "[SEP]", "[MASK]", "good", "bad", "service", "very"]
    vocab_file = tmp_path / "vocab.txt"
    vocab_file.write_text("\n".join(vocab))
    tokenizer = BertTokenizerFast(vocab_file=str(vocab_file), do_lower_case=True)
    for name, depth, width in [("teacher", 2, 12), ("student", 1, 8)]:
        path = tmp_path / name
        config = DistilBertConfig(
            vocab_size=len(tokenizer),
            n_layers=depth,
            dim=width,
            hidden_dim=width * 2,
            n_heads=2,
            num_labels=2,
            max_position_embeddings=32,
            dropout=0,
            attention_dropout=0,
            seq_classif_dropout=0,
        )
        DistilBertForSequenceClassification(config).save_pretrained(path)
        tokenizer.save_pretrained(path)
    texts = {"train": "good service", "val": "bad service"}
    for split, n in [("train", 7), ("val", 3)]:
        source = tmp_path / f"{split}.jsonl"
        source.write_text(
            "\n".join(
                json.dumps({"text": ("very " * i) + texts[split], "label": i % 2}) for i in range(n)
            )
        )
        build(
            SimpleNamespace(
                teacher=str(tmp_path / "teacher"),
                student=str(tmp_path / "student"),
                input=str(source),
                output=str(tmp_path / split),
                device="cpu",
                max_length=24,
                batch_size=2,
                target_dtype="bf16",
                reference=None,
                overlap_threshold=0.85,
            )
        )
    args = SimpleNamespace(
        student=str(tmp_path / "student"),
        cache=str(tmp_path / "train"),
        validation_cache=str(tmp_path / "val"),
        output=str(tmp_path / "output"),
        resume=None,
        cpu=True,
        seed=5,
        workers=0,
        batch_size=2,
        accum=2,
        epochs=2,
        lr=0.001,
        weight_decay=0.01,
        warmup_steps=1,
        precision="auto",
        compile=False,
        compile_mode="default",
        temperature=3.5,
        alpha_logit=0.5,
        alpha_feature=0.3,
        max_grad_norm=1.0,
        no_prefetch=False,
        prefetch_factor=2,
        min_validation_accuracy=None,
        min_macro_recall=None,
        min_per_class_recall=None,
        overlap_threshold=0.85,
        skip_overlap_check=False,
        force_lock=False,
    )
    run(args)
    metrics = [
        json.loads(line) for line in (tmp_path / "output/metrics.jsonl").read_text().splitlines()
    ]
    assert len(metrics) == 2 and metrics[-1]["updates"] == 4
    assert metrics[-1]["validation_samples"] == 3
    exported = DistilBertForSequenceClassification.from_pretrained(
        tmp_path / "output/student", local_files_only=True
    )
    assert exported.config.dim == 8
    args.resume = str(tmp_path / "output/checkpoint.pt")
    run(args)
    assert len((tmp_path / "output/metrics.jsonl").read_text().splitlines()) == 2
