"""
backend/services/proof_publisher.py
====================================
ProofPublish engine — reliability-first content publishing with receipts.

Adapted from ProofPublish (proofpublish_production_20260104) for the
ProfitEngine v5 FastAPI + MongoDB stack.

Core concepts:
  ContentManifest  — SHA-256 fingerprinted content record (immutable once created)
  PublishJob       — 9-state lifecycle: DRAFT→READY→QUEUED→SENT→ACCEPTED→PUBLISHED
  PublishReceipt   — append-only proof-of-work record with platform URL + hash

No duplicate posts ever: idempotency enforced at manifest level (content hash)
and at job level (hash of manifest_id + platform + account + scheduled_at).
"""
from __future__ import annotations

import hashlib
import secrets
import string
from datetime import datetime, timezone
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase


# ── Job state machine ───────────────────────────────────────────
# Mirrors ProofPublish 9-state lifecycle
JOB_STATES = {
    "DRAFT":                   ["READY", "CANCELED"],
    "READY":                   ["QUEUED", "CANCELED"],
    "QUEUED":                  ["SENT", "FAILED_ACTION_REQUIRED", "CANCELED"],
    "SENT":                    ["ACCEPTED_BY_PLATFORM", "FAILED_ACTION_REQUIRED", "FAILED_PERMANENT"],
    "ACCEPTED_BY_PLATFORM":    ["PUBLISHED", "FAILED_ACTION_REQUIRED"],
    "PUBLISHED":               [],
    "FAILED_ACTION_REQUIRED":  ["READY", "QUEUED", "FAILED_PERMANENT", "CANCELED"],
    "FAILED_PERMANENT":        [],
    "CANCELED":                [],
}
TERMINAL_STATES = {"PUBLISHED", "FAILED_PERMANENT", "CANCELED"}

# Platforms and their char limits
PLATFORM_LIMITS = {
    "github":   999_999,   # GitHub Pages — no practical limit
    "devto":    100_000,
    "medium":   100_000,
    "hashnode":  50_000,
    "twitter":     280,
    "linkedin":   3_000,
    "reddit":   40_000,
}


def _nanoid(prefix: str, size: int = 21) -> str:
    alphabet = string.ascii_lowercase + string.digits
    return prefix + "_" + "".join(secrets.choice(alphabet) for _ in range(size))


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _idempotency_key(manifest_id: str, platform: str, account: str, scheduled_at: str) -> str:
    raw = ":".join([manifest_id, platform, account, scheduled_at]).lower()
    return _sha256(raw)[:32]


def _extract_title(content: str) -> str:
    lines = content.strip().split("\n")
    first = lines[0].strip()
    if first.startswith("# "):
        first = first[2:].strip()
    if 0 < len(first) <= 100 and not first.endswith("."):
        return first
    sentences = content.split(".")
    s = sentences[0].strip()
    return s[:97] + "..." if len(s) > 100 else s


def _optimize_for_platform(content: str, platform: str) -> str:
    limit = PLATFORM_LIMITS.get(platform, 999_999)
    if len(content) <= limit:
        return content
    return content[: limit - 3] + "..."


def can_transition(current: str, next_state: str) -> bool:
    return next_state in JOB_STATES.get(current, [])


def is_terminal(state: str) -> bool:
    return state in TERMINAL_STATES


# ── ProofPublisher service ──────────────────────────────────────

class ProofPublisher:
    """
    MongoDB-backed ProofPublish engine.

    Collections:
      proof_manifests  — content manifests (SHA-256 keyed, immutable body)
      proof_jobs       — publish jobs (9-state machine + idempotency)
      proof_receipts   — append-only publish receipts (proof of work)
    """

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._db = db
        self._manifests = db["proof_manifests"]
        self._jobs = db["proof_jobs"]
        self._receipts = db["proof_receipts"]

    # ── Manifest ─────────────────────────────────────────────────

    async def create_manifest(
        self,
        *,
        content: str,
        author_id: str | None = None,
        niche: str | None = None,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Hash and store content. Returns existing manifest if content already seen.
        No duplicate content ever published.
        """
        if not content or not content.strip():
            raise ValueError("Content must not be empty")

        canonical = content.strip()
        content_hash = _sha256(canonical)

        # Deduplication check
        existing = await self._manifests.find_one({"content_hash": content_hash})
        if existing:
            existing["is_duplicate"] = True
            existing.pop("_id", None)
            return existing

        title = _extract_title(canonical)
        words = [w for w in canonical.split() if w]
        manifest_id = _nanoid("man")
        now = datetime.now(timezone.utc).isoformat()

        # Pre-compute platform variants
        variants = {
            platform: {
                "optimized_body": _optimize_for_platform(canonical, platform),
                "char_limit": PLATFORM_LIMITS[platform],
            }
            for platform in PLATFORM_LIMITS
        }

        doc: dict[str, Any] = {
            "manifest_id": manifest_id,
            "content_hash": content_hash,
            "canonical_title": title,
            "canonical_body": canonical,
            "word_count": len(words),
            "character_count": len(canonical),
            "niche": niche,
            "tags": tags or [],
            "author_id": author_id,
            "platform_variants": variants,
            "is_duplicate": False,
            "created_at": now,
        }
        await self._manifests.insert_one(doc)
        doc.pop("_id", None)
        return doc

    async def get_manifest(self, manifest_id: str) -> dict[str, Any] | None:
        doc = await self._manifests.find_one({"manifest_id": manifest_id})
        if doc:
            doc.pop("_id", None)
        return doc

    # ── Publish Job ───────────────────────────────────────────────

    async def create_job(
        self,
        *,
        manifest_id: str,
        platform: str,
        account_id: str = "default",
        scheduled_at: str | None = None,
        publish_mode: str = "NOTIFICATION",
        client_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a publish job for a manifest. Idempotent — returns existing job
        if the same (manifest, platform, account, scheduled_at) combo already exists.
        """
        manifest = await self._manifests.find_one({"manifest_id": manifest_id})
        if not manifest:
            raise ValueError(f"Manifest {manifest_id} not found")

        idem_key = _idempotency_key(
            manifest_id,
            platform,
            account_id,
            scheduled_at or "immediate",
        )

        existing = await self._jobs.find_one({"idempotency_key": idem_key})
        if existing:
            existing["is_duplicate"] = True
            existing.pop("_id", None)
            return existing

        job_id = _nanoid("job")
        now = datetime.now(timezone.utc).isoformat()
        status = "READY" if scheduled_at else "DRAFT"

        doc: dict[str, Any] = {
            "job_id": job_id,
            "manifest_id": manifest_id,
            "platform": platform,
            "account_id": account_id,
            "scheduled_at": scheduled_at,
            "publish_mode": publish_mode,
            "idempotency_key": idem_key,
            "status": status,
            "client_id": client_id,
            "is_duplicate": False,
            "attempt_count": 0,
            "last_error": None,
            "created_at": now,
            "updated_at": now,
        }
        await self._jobs.insert_one(doc)
        doc.pop("_id", None)
        return doc

    async def transition_job(
        self,
        job_id: str,
        next_state: str,
        *,
        platform_url: str | None = None,
        error: str | None = None,
    ) -> dict[str, Any]:
        job = await self._jobs.find_one({"job_id": job_id})
        if not job:
            raise ValueError(f"Job {job_id} not found")
        current = job["status"]
        if not can_transition(current, next_state):
            raise ValueError(f"Cannot transition {current} → {next_state}")

        now = datetime.now(timezone.utc).isoformat()
        update: dict[str, Any] = {
            "status": next_state,
            "updated_at": now,
        }
        if error:
            update["last_error"] = error
            update["attempt_count"] = job.get("attempt_count", 0) + 1
        if platform_url:
            update["platform_url"] = platform_url

        await self._jobs.update_one({"job_id": job_id}, {"$set": update})

        # Create receipt when PUBLISHED
        if next_state == "PUBLISHED":
            await self._create_receipt(job, platform_url=platform_url)

        updated = {**job, **update}
        updated.pop("_id", None)
        return updated

    async def _create_receipt(
        self,
        job: dict[str, Any],
        *,
        platform_url: str | None,
    ) -> dict[str, Any]:
        manifest = await self._manifests.find_one({"manifest_id": job["manifest_id"]})
        receipt_id = _nanoid("rcpt")
        now = datetime.now(timezone.utc).isoformat()
        doc: dict[str, Any] = {
            "receipt_id": receipt_id,
            "job_id": job["job_id"],
            "manifest_id": job["manifest_id"],
            "content_hash": manifest["content_hash"] if manifest else None,
            "canonical_title": manifest["canonical_title"] if manifest else None,
            "word_count": manifest["word_count"] if manifest else None,
            "niche": manifest.get("niche") if manifest else None,
            "platform": job["platform"],
            "account_id": job.get("account_id"),
            "platform_url": platform_url,
            "client_id": job.get("client_id"),
            "published_at": now,
            "proof": {
                "content_hash": manifest["content_hash"] if manifest else None,
                "idempotency_key": job["idempotency_key"],
                "receipt_hash": _sha256(receipt_id + now),
            },
        }
        await self._receipts.insert_one(doc)
        doc.pop("_id", None)
        return doc

    # ── Queries ───────────────────────────────────────────────────

    async def list_receipts(
        self,
        *,
        client_id: str | None = None,
        platform: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        query: dict[str, Any] = {}
        if client_id:
            query["client_id"] = client_id
        if platform:
            query["platform"] = platform
        cursor = self._receipts.find(query, {"_id": 0}).sort("published_at", -1).limit(limit)
        return await cursor.to_list(length=limit)

    async def get_job(self, job_id: str) -> dict[str, Any] | None:
        doc = await self._jobs.find_one({"job_id": job_id})
        if doc:
            doc.pop("_id", None)
        return doc

    async def pending_jobs(self, limit: int = 20) -> list[dict[str, Any]]:
        """Jobs in DRAFT or READY state awaiting execution."""
        cursor = self._jobs.find(
            {"status": {"$in": ["DRAFT", "READY"]}},
            {"_id": 0},
        ).sort("created_at", 1).limit(limit)
        return await cursor.to_list(length=limit)

    async def proof_of_work_summary(self, client_id: str | None = None) -> dict[str, Any]:
        """Dashboard summary: receipts, platforms, word count, hashes."""
        query: dict[str, Any] = {}
        if client_id:
            query["client_id"] = client_id

        receipts = await self._receipts.find(query, {"_id": 0}).to_list(length=1000)
        platform_counts: dict[str, int] = {}
        total_words = 0
        niches: set[str] = set()

        for r in receipts:
            plat = r.get("platform", "unknown")
            platform_counts[plat] = platform_counts.get(plat, 0) + 1
            total_words += r.get("word_count") or 0
            if r.get("niche"):
                niches.add(r["niche"])

        return {
            "total_published": len(receipts),
            "total_words": total_words,
            "platforms": platform_counts,
            "niches": sorted(niches),
            "latest_receipt": receipts[0] if receipts else None,
            "proof_hash": _sha256(str(len(receipts)) + str(total_words)),
        }
