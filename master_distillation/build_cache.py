"""Generate teacher targets from JSONL {text, label} using local model artifacts."""

import argparse
import hashlib
import json
from pathlib import Path

import torch
from transformers import AutoConfig, AutoModelForSequenceClassification, AutoTokenizer

from dataset import (
    MINHASH_SIZE,
    CacheWriter,
    dedup_index,
    digest,
    find_overlap,
    tokenizer_digest,
)
from distill_ddp import layer_map

_UINT64_MASK = (1 << 64) - 1
_INT63_MASK = (1 << 63) - 1


def _normalize(text):
    return " ".join(text.lower().split())


def _shingles(normalized, width=5):
    if len(normalized) <= width:
        return {normalized.encode()}
    return {normalized[i : i + width].encode() for i in range(len(normalized) - width + 1)}


def text_signature(text):
    """Normalized-text sha256 plus a MinHash signature over character shingles.

    Uses the standard two-universal-hash MinHash construction (h_i = h1 + i*h2);
    signatures are masked to 63 bits so they fit signed int64 storage.
    """
    normalized = _normalize(text)
    text_digest = hashlib.sha256(normalized.encode()).digest()
    signature = [_INT63_MASK] * MINHASH_SIZE
    for shingle in _shingles(normalized):
        h = hashlib.sha256(shingle).digest()
        h1 = int.from_bytes(h[:8], "little")
        h2 = int.from_bytes(h[8:16], "little") | 1
        values = [(h1 + i * h2) & _UINT64_MASK for i in range(MINHASH_SIZE)]
        signature = [
            current if current < candidate else candidate
            for current, candidate in zip([v & _INT63_MASK for v in values], signature, strict=True)
        ]
    return text_digest, torch.tensor(signature, dtype=torch.int64)


def model_signature(path):
    files = sorted(
        p
        for p in Path(path).rglob("*")
        if p.is_file() and (p.suffix in (".json", ".safetensors") or p.name.endswith(".model"))
    )
    if not files:
        raise ValueError("No local model artifacts found")
    records = [(str(p.relative_to(path)), digest(p)) for p in files]
    return hashlib.sha256(json.dumps(records).encode()).hexdigest()


def load_classifier(path):
    model, info = AutoModelForSequenceClassification.from_pretrained(
        path,
        local_files_only=True,
        trust_remote_code=False,
        use_safetensors=True,
        output_loading_info=True,
    )
    if info.get("missing_keys") or info.get("mismatched_keys") or info.get("error_msgs"):
        raise ValueError(
            "Model has missing or mismatched weights; save a complete classifier first"
        )
    return model


def build(args):
    teacher_config = AutoConfig.from_pretrained(
        args.teacher, local_files_only=True, trust_remote_code=False
    )
    student_config = AutoConfig.from_pretrained(
        args.student, local_files_only=True, trust_remote_code=False
    )
    if teacher_config.num_labels != student_config.num_labels:
        raise ValueError("Teacher and student must have matching classification heads")
    if teacher_config.id2label != student_config.id2label:
        raise ValueError("Teacher/student class ordering differs")
    tokenizer = AutoTokenizer.from_pretrained(
        args.teacher, local_files_only=True, trust_remote_code=False
    )
    student_tokenizer = AutoTokenizer.from_pretrained(
        args.student, local_files_only=True, trust_remote_code=False
    )
    if tokenizer_digest(tokenizer) != tokenizer_digest(student_tokenizer):
        raise ValueError(
            "Teacher and student tokenizers differ; token feature alignment is invalid"
        )
    if tokenizer.pad_token_id is None:
        raise ValueError("Tokenizer needs a pad token")
    if args.max_length > min(
        teacher_config.max_position_embeddings, student_config.max_position_embeddings
    ):
        raise ValueError("Max length exceeds model positional limit")
    device = torch.device(args.device)
    teacher = load_classifier(args.teacher).to(device).eval()
    tokenizer.padding_side = "right"
    layers = sorted(
        {
            t
            for _, t in layer_map(
                student_config.num_hidden_layers, teacher_config.num_hidden_layers
            )
        }
    )
    meta = dict(
        teacher_sha256=model_signature(args.teacher),
        source_sha256=digest(args.input),
        source_path=str(Path(args.input).resolve()),
        tokenizer_sha256=tokenizer_digest(tokenizer),
        teacher_layers=layers,
        teacher_depth=teacher_config.num_hidden_layers,
        teacher_width=teacher_config.hidden_size,
        num_labels=teacher_config.num_labels,
        id2label=teacher_config.id2label,
        pad_token_id=tokenizer.pad_token_id,
        vocab_size=teacher_config.vocab_size,
        max_length=args.max_length,
        target_dtype=args.target_dtype,
    )
    writer = CacheWriter(args.output, meta)
    success = False
    dtype = {"fp32": torch.float32, "fp16": torch.float16, "bf16": torch.bfloat16}[
        args.target_dtype
    ]
    try:
        with open(args.input) as source, torch.inference_mode():
            pending = []

            def flush(rows):
                encoded = tokenizer(
                    [r["text"] for r in rows],
                    padding=True,
                    truncation=True,
                    max_length=args.max_length,
                    return_tensors="pt",
                )
                # This package intentionally supports single-text classifiers only.
                inputs = {k: encoded[k].to(device) for k in ("input_ids", "attention_mask")}
                outputs = teacher(**inputs, output_hidden_states=True)
                for i, row in enumerate(rows):
                    n = int(encoded["attention_mask"][i].sum())
                    record = dict(
                        input_ids=encoded["input_ids"][i, :n].clone(),
                        attention_mask=encoded["attention_mask"][i, :n].clone(),
                        labels=torch.tensor(row["label"], dtype=torch.long),
                        logits=outputs.logits[i].float().cpu(),
                    )
                    record.update(
                        {
                            f"hidden_{layer}": outputs.hidden_states[layer][i, :n].to(dtype).cpu()
                            for layer in layers
                        }
                    )
                    writer.append(record)
                    writer.track_dedup(*text_signature(row["text"]))

            histogram = {}
            for line_number, line in enumerate(source, 1):
                row = json.loads(line)
                if not isinstance(row.get("text"), str) or type(row.get("label")) is not int:
                    raise ValueError(f"Invalid text/label at line {line_number}")
                if not 0 <= row["label"] < teacher_config.num_labels:
                    raise ValueError(f"Invalid label at line {line_number}")
                pending.append(row)
                histogram[row["label"]] = histogram.get(row["label"], 0) + 1
                if len(pending) == args.batch_size:
                    flush(pending)
                    pending.clear()
            if pending:
                flush(pending)
        writer.meta["label_histogram"] = {str(k): v for k, v in sorted(histogram.items())}
        success = True
    finally:
        writer.close(success)
    if args.reference:
        exact, near = find_overlap(
            dedup_index(args.output), dedup_index(args.reference), args.overlap_threshold
        )
        if exact or near:
            raise ValueError(
                "Split overlap with reference cache: "
                f"{len(exact)} exact, {len(near)} near-duplicate"
            )
    print(json.dumps({"cache": args.output, "records": writer.count}))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--teacher", required=True)
    p.add_argument("--student", required=True)
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    p.add_argument("--batch-size", type=int, default=16)
    p.add_argument("--max-length", type=int, default=512)
    p.add_argument("--target-dtype", choices=["bf16", "fp16", "fp32"], default="bf16")
    p.add_argument(
        "--reference",
        help="Existing cache directory this split must not overlap (e.g. the validation cache)",
    )
    p.add_argument("--overlap-threshold", type=float, default=0.85)
    args = p.parse_args()
    if args.batch_size < 1 or args.max_length < 1 or not 0 < args.overlap_threshold <= 1:
        p.error("batch-size/max-length must be positive; threshold in (0, 1]")
    build(args)


if __name__ == "__main__":
    main()
