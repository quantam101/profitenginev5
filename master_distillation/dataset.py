"""Immutable, versioned classification caches; never deserialize arbitrary pickle."""

import hashlib
import json
import os
from pathlib import Path

import lmdb
import torch
import zstandard as zstd
from safetensors.torch import load, load_file, save, save_file
from torch.utils.data import Dataset

MAX_RECORD = 256 * 1024 * 1024
MINHASH_SIZE = 64


def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def tokenizer_digest(tokenizer):
    if not tokenizer.is_fast:
        raise ValueError("A fast tokenizer is required for a reproducible tokenization fingerprint")
    state = json.loads(tokenizer.backend_tokenizer.to_str())
    # Padding/truncation settings vary with each call; preprocessing is in manifest.
    state.pop("padding", None)
    state.pop("truncation", None)
    return hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest()


def validate_record(p, meta):
    expected = {"input_ids", "attention_mask", "labels", "logits"} | {
        f"hidden_{i}" for i in meta["teacher_layers"]
    }
    if set(p) != expected:
        raise ValueError("Cache record has missing or unexpected fields")
    ids, mask = p["input_ids"], p["attention_mask"]
    if ids.dtype != torch.long or ids.ndim != 1 or not 0 < ids.numel() <= meta["max_length"]:
        raise ValueError("Invalid input ids or sequence length")
    if mask.dtype != torch.long or mask.shape != ids.shape or not bool((mask == 1).all()):
        raise ValueError("Records must be unpadded; mask must contain only ones")
    if int(ids.min()) < 0 or int(ids.max()) >= meta["vocab_size"]:
        raise ValueError("Token outside vocabulary")
    if p["labels"].dtype != torch.long or p["labels"].ndim != 0:
        raise ValueError("Expected scalar integer classification label")
    if not 0 <= int(p["labels"]) < meta["num_labels"]:
        raise ValueError("Label outside class range")
    if p["logits"].shape != (meta["num_labels"],):
        raise ValueError("Expected sequence classification logits [classes]")
    for name, t in p.items():
        if name.startswith("hidden_") and t.shape != (len(ids), meta["teacher_width"]):
            raise ValueError("Hidden state shape mismatch")
        if name == "logits" or name.startswith("hidden_"):
            if not t.is_floating_point() or not bool(torch.isfinite(t).all()):
                raise ValueError("Nonfinite or non-floating teacher target")


class CacheWriter:
    """Write to a new directory. Manifest appears only after successful completion."""

    def __init__(self, path, meta, map_size=1 << 40):
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=False)
        self.meta = dict(meta, schema=1, task="sequence_classification")
        self.env = lmdb.open(str(self.path), map_size=map_size, max_readers=2048)
        self.compressor = zstd.ZstdCompressor(level=3)
        self.count = 0
        self._text_hashes = []
        self._minhashes = []

    def append(self, record):
        validate_record(record, self.meta)
        blob = save({k: v.detach().cpu().contiguous() for k, v in record.items()})
        if len(blob) > MAX_RECORD:
            raise ValueError("Record exceeds size limit")
        blob = self.compressor.compress(blob)
        with self.env.begin(write=True) as txn:
            txn.put(f"{self.count:012d}".encode(), blob, overwrite=False)
        self.count += 1

    def track_dedup(self, text_digest, minhash):
        """Record one row's normalized-text digest and MinHash signature, in row order."""
        if isinstance(text_digest, bytes) and len(text_digest) == 32:
            text_digest = torch.tensor(list(text_digest), dtype=torch.uint8)
        if (
            text_digest.dtype != torch.uint8
            or text_digest.shape != (32,)
            or minhash.dtype != torch.int64
            or minhash.shape != (MINHASH_SIZE,)
        ):
            raise ValueError("Invalid dedup signature shapes")
        self._text_hashes.append(text_digest.clone())
        self._minhashes.append(minhash.clone())

    def close(self, success=True):
        if self.env is None:
            return
        self.env.sync()
        self.env.close()
        self.env = None
        if success:
            if not self.count:
                raise ValueError("Empty cache")
            self.meta.update(length=self.count, data_sha256=digest(self.path / "data.mdb"))
            if self._text_hashes or self._minhashes:
                if len(self._text_hashes) != self.count or len(self._minhashes) != self.count:
                    raise ValueError("Dedup signature count does not match record count")
                sidecar = self.path / "dedup.safetensors"
                temp = self.path / "dedup.tmp"
                save_file(
                    {
                        "text_sha256": torch.stack(self._text_hashes),
                        "minhash": torch.stack(self._minhashes),
                    },
                    str(temp),
                )
                os.replace(temp, sidecar)
                self.meta.update(
                    dedup_sha256=digest(sidecar),
                    exact_duplicate_rows=self.count
                    - len({bytes(t.tolist()) for t in self._text_hashes}),
                )
            temp = self.path / "manifest.tmp"
            temp.write_text(json.dumps(self.meta, indent=2))
            os.replace(temp, self.path / "manifest.json")


def dedup_index(cache):
    """Verified per-row dedup signatures for a cache (dataset or directory path)."""
    path = Path(getattr(cache, "path", cache))
    meta = getattr(cache, "meta", None)
    if meta is None:
        meta = json.loads((path / "manifest.json").read_text())
    sidecar = path / "dedup.safetensors"
    if not meta.get("dedup_sha256") or not sidecar.exists():
        raise ValueError("Cache lacks a dedup index; rebuild it with this package version")
    if digest(sidecar) != meta["dedup_sha256"]:
        raise ValueError("Dedup index checksum mismatch")
    tensors = load_file(str(sidecar))
    text, minhash = tensors.get("text_sha256"), tensors.get("minhash")
    if (
        text is None
        or minhash is None
        or text.shape != (meta["length"], 32)
        or minhash.shape != (meta["length"], MINHASH_SIZE)
    ):
        raise ValueError("Dedup index does not match cache length or signature width")
    return [row.numpy().tobytes() for row in text], minhash


def find_overlap(a_index, b_index, threshold=0.85, bands=16):
    """Exact digest matches plus banded-MinHash near-duplicate candidates."""
    a_text, a_sig = a_index
    b_text, b_sig = b_index
    width = a_sig.shape[1] // bands
    if a_sig.shape[1] % bands or width < 1:
        raise ValueError("Signature width must divide evenly into bands")
    exact = sorted(set(a_text) & set(b_text))
    index = {}
    for j in range(b_sig.shape[0]):
        for band in range(bands):
            key = (band, tuple(b_sig[j, band * width : (band + 1) * width].tolist()))
            index.setdefault(key, []).append(j)
    near = []
    for i in range(a_sig.shape[0]):
        candidates = set()
        for band in range(bands):
            key = (band, tuple(a_sig[i, band * width : (band + 1) * width].tolist()))
            candidates.update(index.get(key, ()))
        for j in candidates:
            if float((a_sig[i] == b_sig[j]).float().mean()) >= threshold:
                near.append((i, j))
    return exact, near


class DistributedCachedTeacherDataset(Dataset):
    def __init__(self, db_path, verify_hash=True):
        self.path = Path(db_path).resolve()
        self.meta = json.loads((self.path / "manifest.json").read_text())
        if self.meta["schema"] != 1 or self.meta["task"] != "sequence_classification":
            raise ValueError("Unsupported cache schema or task")
        if verify_hash and digest(self.path / "data.mdb") != self.meta["data_sha256"]:
            raise ValueError("Cache checksum mismatch")
        self.env = None
        self.pid = None

    def __len__(self):
        return self.meta["length"]

    def __getstate__(self):
        state = self.__dict__.copy()
        state.update(env=None, pid=None)
        return state

    def _init_db(self):
        if self.env is not None and self.pid == os.getpid():
            return
        self.env = lmdb.open(
            str(self.path),
            readonly=True,
            create=False,
            lock=True,
            readahead=False,
            max_spare_txns=0,
        )
        self.pid = os.getpid()

    def __getitem__(self, index):
        if not 0 <= index < len(self):
            raise IndexError(index)
        self._init_db()
        # Decompress while the LMDB buffer's transaction is alive.
        with self.env.begin(buffers=True) as txn:
            blob = txn.get(f"{index:012d}".encode())
            if blob is None:
                raise KeyError(f"Missing cache row {index}")
            size = zstd.frame_content_size(blob)
            if not 0 < size <= MAX_RECORD:
                raise ValueError("Invalid or oversized compressed frame")
            raw = zstd.ZstdDecompressor().decompress(blob, max_output_size=MAX_RECORD)
        p = load(raw)
        validate_record(p, self.meta)
        return p

    def close(self):
        if self.env is not None and self.pid == os.getpid():
            self.env.close()
        self.env = None


def worker_init_fn(_):
    torch.set_num_threads(1)
    torch.utils.data.get_worker_info().dataset._init_db()


class PadCollator:
    def __init__(self, pad_token_id, multiple=8, max_length=512):
        self.pad = pad_token_id
        self.multiple = multiple
        self.max_length = max_length

    def __call__(self, rows):
        n = max(len(r["input_ids"]) for r in rows)
        n = min(self.max_length, ((n + self.multiple - 1) // self.multiple) * self.multiple)
        out = {}
        for key in rows[0]:
            if key in ("labels", "logits"):
                out[key] = torch.stack([r[key] for r in rows])
                continue
            shape = (len(rows), n, *rows[0][key].shape[1:])
            t = rows[0][key].new_full(shape, self.pad if key == "input_ids" else 0)
            for i, r in enumerate(rows):
                t[i, : len(r[key])] = r[key]
            out[key] = t
        return out
