"""
FYE job store — the immutable control-plane record for one approved
render/publish unit.

Target flow: Command OS approval → immutable job record → authenticated
dispatch → Actions worker → artifact → QA gate → publish approval →
channel publisher → revenue attribution.

A merge or push is never authorization to produce content. Every state
change goes through ``transition`` which validates the lifecycle and
appends the move to the hash-chained DecisionJournal (the audit ledger).

Lifecycle:
    DRAFT → APPROVED → QUEUED → CLAIMED → RENDERING → QA → READY
        → PUBLISH_APPROVED → PUBLISHED
    terminal: FAILED, REJECTED, EXPIRED, CANCELLED
"""
from __future__ import annotations

import contextlib
import hashlib
import json
import os
import re
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from .config import FyeConfig
from .journal import DecisionJournal

try:
    import fcntl
except ImportError:
    fcntl = None  # type: ignore[assignment]

# Legal transitions. RENDERING→CLAIMED is allowed for retry-after-crash
# recovery when the previous lease has expired (see claim()).
_TRANSITIONS: Dict[str, List[str]] = {
    "DRAFT": ["APPROVED", "REJECTED", "EXPIRED", "CANCELLED"],
    "APPROVED": ["QUEUED", "EXPIRED", "CANCELLED"],
    "QUEUED": ["CLAIMED", "EXPIRED", "CANCELLED"],
    "CLAIMED": ["RENDERING", "QUEUED", "FAILED", "EXPIRED", "CANCELLED"],
    "RENDERING": ["QA", "CLAIMED", "FAILED", "EXPIRED", "CANCELLED"],
    "QA": ["READY", "FAILED"],
    "READY": ["PUBLISH_APPROVED", "FAILED", "EXPIRED", "CANCELLED"],
    # PUBLISHING is the single-flight publish lease: the channel call
    # happens only after this transition commits, so two concurrent
    # publishers cannot both reach the adapter.
    "PUBLISH_APPROVED": ["PUBLISHING", "FAILED", "EXPIRED", "CANCELLED"],
    "PUBLISHING": ["PUBLISHED", "PUBLISH_APPROVED", "FAILED", "CANCELLED"],
    "PUBLISHED": [],
    "FAILED": ["QUEUED"],  # retry allowed only via explicit re-queue
    "REJECTED": [],
    "EXPIRED": [],
    "CANCELLED": [],
}

TERMINAL = {"FAILED", "REJECTED", "EXPIRED", "CANCELLED", "PUBLISHED"}


def legal_targets(frm: str) -> List[str]:
    return list(_TRANSITIONS.get(frm, []))

# Fields hashed into payload_hash — the dispatch contract. An altered
# payload produces a different hash and the worker refuses to run.
PAYLOAD_FIELDS = (
    "topic", "niche", "title", "channel", "monthly_views_target",
    "subscribers", "watch_hours", "shorts_views", "human_reviewed",
    "render_params",
)

LEASE_TTL_S = 3600.0  # one CLAIMED/RENDERING worker per job at a time


class JobError(Exception):
    """Base for control-plane refusals."""


class PayloadMismatch(JobError):
    """job_id exists but the payload_hash does not — never overwrite."""


class IllegalTransition(JobError):
    pass


def canonical_payload(fields: Dict[str, Any]) -> Dict[str, Any]:
    """Canonical dispatch payload — fixed keys, JSON-stable."""
    out: Dict[str, Any] = {}
    for k in PAYLOAD_FIELDS:
        v = fields.get(k)
        if v is None:
            continue
        out[k] = v
    return out


def payload_hash(fields: Dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(canonical_payload(fields), sort_keys=True).encode()
    ).hexdigest()


def new_job_id() -> str:
    stamp = time.strftime("%Y-%m-%d")
    return f"fye-job-{stamp}-{uuid.uuid4().hex[:10]}"


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class FyeJobStore:
    """
    File-backed job ledger under ``<FYE_ROOT>/jobs/<job_id>.json`` plus a
    lock file. One job_id = one immutable payload; replaying a dispatch
    with the same hash returns the stored record instead of rendering twice.
    """

    def __init__(self, cfg: Optional[FyeConfig] = None,
                 journal: Optional[DecisionJournal] = None) -> None:
        self.cfg = cfg or FyeConfig()
        self.dir = Path(self.cfg.root) / "jobs"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.journal = journal or DecisionJournal(
            os.fspath(Path(self.cfg.root) / "journal.jsonl"))

    # ---------- storage ----------

    _JOB_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")

    def _path(self, job_id: str) -> Path:
        # Strict allowlist — the id becomes a filename on every store
        # host, so control chars, separators, and platform-unsafe glyphs
        # are refused before the filesystem is ever touched.
        if not self._JOB_ID_RE.fullmatch(job_id) or ".." in job_id:
            raise JobError(f"invalid job_id {job_id!r}")
        return self.dir / f"{job_id}.json"

    @contextlib.contextmanager
    def _locked(self, job_id: str) -> Iterator[None]:
        self._path(job_id)  # validate before touching the filesystem
        lock_path = self.dir / f"{job_id}.lock"
        with open(lock_path, "a+b") as lock:
            if fcntl is not None:
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                if fcntl is not None:
                    fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

    def get(self, job_id: str) -> Optional[Dict[str, Any]]:
        p = self._path(job_id)
        if not p.exists():
            return None
        return json.loads(p.read_text(encoding="utf-8"))

    def _write(self, job: Dict[str, Any]) -> None:
        p = self._path(job["job_id"])
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(job, indent=2, sort_keys=True),
                       encoding="utf-8")
        os.replace(tmp, p)  # atomic — a torn write never corrupts READY

    def list(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        jobs = []
        for p in sorted(self.dir.glob("*.json")):
            job = json.loads(p.read_text(encoding="utf-8"))
            if status is None or job.get("status") == status:
                jobs.append(job)
        return jobs

    # ---------- lifecycle ----------

    def create(self, *, job_id: Optional[str] = None,
               approval_id: str, fields: Dict[str, Any],
               ttl_s: Optional[float] = None,
               attribution: Optional[Dict[str, Any]] = None
               ) -> Dict[str, Any]:
        """Idempotent create. Same job_id + same payload_hash returns the
        existing record; same job_id + different hash is refused."""
        job_id = job_id or new_job_id()
        ph = payload_hash(fields)
        with self._locked(job_id):
            existing = self.get(job_id)
            if existing is not None:
                if existing["payload_hash"] != ph:
                    raise PayloadMismatch(
                        f"job {job_id} exists with different payload")
                existing["replayed"] = True
                return existing
            now = time.time()
            job = {
                "job_id": job_id,
                "status": "DRAFT",
                "payload_hash": ph,
                "payload": canonical_payload(fields),
                "approval_id": approval_id,
                "created_at": now,
                "expires_at": now + (ttl_s if ttl_s is not None
                                     else self.cfg.job_ttl_s),
                "attempts": 0,
                "lease": None,
                "artifacts": {},
                "publish": {"idempotency_key": f"fye-publish-{job_id}",
                            "post_id": None, "posted_at": None},
                # #95 revenue spine: asset → channel → campaign → revenue.
                "attribution": {
                    "asset_id": job_id,
                    "channel_id": fields.get("channel", ""),
                    "campaign": (attribution or {}).get("campaign", ""),
                    "source": (attribution or {}).get("source", "fye"),
                },
                "history": [],
            }
            self._write(job)
            self.journal.append("job_store", "job.created",
                                {"job_id": job_id, "payload_hash": ph,
                                 "approval_id": approval_id})
            return job

    def _transition_locked(self, job: Dict[str, Any], to: str,
                           **meta: Any) -> Dict[str, Any]:
        """Transition body — caller must already hold the job lock."""
        frm = job["status"]
        if to not in _TRANSITIONS.get(frm, []):
            raise IllegalTransition(f"{frm} → {to} not allowed")
        job["status"] = to
        if to == "PUBLISH_APPROVED":
            # Publish authorization has its own TTL, starting when the
            # publish decision is granted — a late human approval must
            # not inherit the render job's creation deadline.
            job["publish_expires_at"] = time.time() + self.cfg.job_ttl_s
        event = {"from": frm, "to": to, "at": time.time()}
        event.update(meta)
        job["history"].append(event)
        self._write(job)
        self.journal.append("job_store", "job.transition", {
            "job_id": job["job_id"], "from": frm, "to": to, **{
                k: v for k, v in meta.items()
                if isinstance(v, (str, int, float, bool))}})
        return job

    def transition(self, job_id: str, to: str, **meta: Any) -> Dict[str, Any]:
        """Validated, journaled status move. Illegal moves raise."""
        with self._locked(job_id):
            job = self.get(job_id)
            if job is None:
                raise JobError(f"unknown job {job_id}")
            return self._transition_locked(job, to, **meta)

    def is_expired(self, job: Dict[str, Any]) -> bool:
        return time.time() > float(job.get("expires_at", 0))

    def publish_expired(self, job: Dict[str, Any]) -> bool:
        """Publish-authorization TTL — set when PUBLISH_APPROVED is
        granted, independent of the render job's creation deadline."""
        deadline = job.get("publish_expires_at") or job.get("expires_at", 0)
        return time.time() > float(deadline)

    def approve(self, job_id: str, *, approved_by: str = "") -> Dict[str, Any]:
        with self._locked(job_id):
            job = self.get(job_id)
            if job is None:
                raise JobError(f"unknown job {job_id}")
            if self.is_expired(job):
                self._transition_locked(job, "EXPIRED")
                raise JobError(f"job {job_id} approval expired")
            return self._transition_locked(
                job, "APPROVED", approved_by=approved_by)

    def enqueue(self, job_id: str) -> Dict[str, Any]:
        job = self.get(job_id)
        if job is None:
            raise JobError(f"unknown job {job_id}")
        if job["status"] == "FAILED":
            return self.transition(job_id, "QUEUED", retry=True)
        return self.transition(job_id, "QUEUED")

    def claim(self, job_id: str, worker: str,
              ttl_s: float = LEASE_TTL_S) -> bool:
        """Acquire the single-worker lease. Only one active CLAIMED/
        RENDERING holder; an expired lease may be reclaimed (crash
        recovery) — never duplicated concurrently."""
        with self._locked(job_id):
            job = self.get(job_id)
            if job is None:
                raise JobError(f"unknown job {job_id}")
            if self.is_expired(job):
                if job["status"] not in TERMINAL:
                    self._transition_locked(job, "EXPIRED")
                raise JobError(f"job {job_id} expired")
            now = time.time()
            lease = job.get("lease") or {}
            if (lease.get("owner") and lease.get("until", 0) > now
                    and lease.get("owner") != worker):
                return False
            if job["status"] in ("QUEUED",):
                job = self._transition_locked(job, "CLAIMED", worker=worker)
            elif job["status"] not in ("CLAIMED", "RENDERING"):
                raise IllegalTransition(
                    f"cannot claim job in {job['status']}")
            job["lease"] = {"owner": worker, "until": now + ttl_s}
            job["attempts"] = int(job.get("attempts", 0)) + 1
            self._write(job)
            return True

    def verify_payload(self, job_id: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Fail-closed dispatch check: job must exist, hash must match."""
        job = self.get(job_id)
        if job is None:
            raise JobError(f"unknown job {job_id}")
        if job["payload_hash"] != payload_hash(fields):
            raise PayloadMismatch(f"job {job_id} payload altered")
        return job

    # ---------- artifacts / publish ----------

    def record_artifact(self, job_id: str, path: str,
                        max_bytes: Optional[int] = None) -> Dict[str, Any]:
        """Verify + record a rendered artifact. Fails closed on a missing,
        empty, or oversize file."""
        p = Path(path)
        if not p.exists() or p.stat().st_size < 100:
            raise JobError(f"artifact missing or empty: {path}")
        limit = max_bytes if max_bytes is not None else self.cfg.max_artifact_bytes
        if p.stat().st_size > limit:
            raise JobError(
                f"artifact exceeds limit ({p.stat().st_size} > {limit})")
        sha = sha256_file(path)
        with self._locked(job_id):
            job = self.get(job_id)
            if job is None:
                raise JobError(f"unknown job {job_id}")
            job["artifacts"][os.path.basename(path)] = {
                "path": os.fspath(p), "sha256": sha,
                "bytes": p.stat().st_size, "recorded_at": time.time()}
            self._write(job)
            self.journal.append("job_store", "job.artifact",
                                {"job_id": job_id, "sha256": sha,
                                 "bytes": p.stat().st_size})
            return job

    def record_reported_artifacts(self, job_id: str,
                                  artifacts: Dict[str, Any]) -> Dict[str, Any]:
        """Merge artifact metadata reported by a remote worker (via the
        Command OS event ledger) — the control plane never sees the
        runner's files, so this carries only the verified metadata the
        runner already recorded: name → {path, sha256, bytes}."""
        if not isinstance(artifacts, dict):
            raise JobError("reported artifacts must be a dict")
        with self._locked(job_id):
            job = self.get(job_id)
            if job is None:
                raise JobError(f"unknown job {job_id}")
            merged = dict(job.get("artifacts") or {})
            for name, meta in artifacts.items():
                if name in merged and merged[name].get("sha256") != \
                        (meta or {}).get("sha256"):
                    raise JobError(
                        f"artifact {name} hash conflict on reconcile")
                merged[name] = meta
            job["artifacts"] = merged
            self._write(job)
            self.journal.append("job_store", "job.artifact.reconciled",
                                {"job_id": job_id,
                                 "names": sorted(artifacts)})
            return job

    def begin_publish(self, job_id: str) -> Dict[str, Any]:
        """Atomic publish lease: PUBLISH_APPROVED → PUBLISHING before any
        channel call. A concurrent caller sees PUBLISHING (not
        PUBLISH_APPROVED) and is refused — one channel post per job.
        Returns a replay marker for an already-PUBLISHED job."""
        with self._locked(job_id):
            job = self.get(job_id)
            if job is None:
                raise JobError(f"unknown job {job_id}")
            if job["status"] == "PUBLISHED":
                job["replayed"] = True
                return job
            return self._transition_locked(job, "PUBLISHING")

    def end_publish_failure(self, job_id: str, error: str) -> Dict[str, Any]:
        """Adapter call failed after the publish lease — roll the job back
        to PUBLISH_APPROVED so a retry can re-lease it."""
        with self._locked(job_id):
            job = self.get(job_id)
            if job is None:
                raise JobError(f"unknown job {job_id}")
            return self._transition_locked(job, "PUBLISH_APPROVED",
                                           error=error)

    def record_publish(self, job_id: str, post_id: str) -> Dict[str, Any]:
        """Idempotent publish record — a second call with the same job_id
        returns the existing post, guaranteeing one channel post per job."""
        with self._locked(job_id):
            job = self.get(job_id)
            if job is None:
                raise JobError(f"unknown job {job_id}")
            if job["status"] == "PUBLISHED":
                job["replayed"] = True
                return job
            if job["status"] not in ("PUBLISHING", "PUBLISH_APPROVED"):
                raise IllegalTransition(
                    f"cannot publish job in {job['status']}")
            job["publish"]["post_id"] = post_id
            job["publish"]["posted_at"] = time.time()
            self._write(job)
            self.journal.append("job_store", "job.published",
                                {"job_id": job_id, "post_id": post_id})
            return self._transition_locked(job, "PUBLISHED", post_id=post_id)
