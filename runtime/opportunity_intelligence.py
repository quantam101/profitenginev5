from __future__ import annotations

import hashlib
import html
import json
import re
import sqlite3
import tempfile
import time
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable


FIELD_SERVICE_KEYWORDS = {
    "it": 1.0,
    "network": 1.0,
    "printer": 0.85,
    "pos": 0.8,
    "access control": 0.95,
    "cctv": 0.9,
    "wireless": 0.95,
    "ap": 0.7,
    "cabling": 0.85,
    "low-voltage": 0.85,
    "smart hands": 0.9,
    "computer": 0.7,
    "tv": 0.45,
    "display": 0.5,
    "av": 0.55,
}

HIGH_RISK_TERMS = {
    "ladder": "ladder_required",
    "heavy": "heavy_lift_exposure",
    "85-inch": "large_format_display",
    "85 inch": "large_format_display",
    "86-inch": "large_format_display",
    "wall mount": "wall_mount_scope",
    "wall-mount": "wall_mount_scope",
    "remove from wall": "wall_removal_scope",
    "return trip": "return_trip_exposure",
    "parts": "parts_exposure",
    "helper": "helper_coordination",
    "vague": "vague_scope",
    "diagnose": "diagnostic_expansion",
}

PHOENIX_PRIORITY_CITIES = {
    "phoenix",
    "tempe",
    "chandler",
    "mesa",
    "scottsdale",
    "glendale",
    "gilbert",
    "peoria",
    "surprise",
    "avondale",
    "goodyear",
}

DEFAULT_POLICY = {
    "preferred_effective_hourly": 65.0,
    "minimum_dispatch_value": 130.0,
    "default_minimum_hours": 2.0,
    "priority_radius_miles": 60.0,
    "counter_floor_large_format": 175.0,
    "counter_floor_standard": 130.0,
    "same_day_priority_bonus": 8.0,
    "next_day_priority_bonus": 5.0,
    "clear_scope_bonus": 8.0,
    "phoenix_city_bonus": 6.0,
    "low_travel_bonus": 5.0,
    "under_minimum_penalty": 35.0,
    "vague_scope_penalty": 14.0,
    "heavy_lift_penalty": 18.0,
    "return_trip_penalty": 18.0,
    "unknown_pay_penalty": 25.0,
}


class CleanTextExtractor(HTMLParser):
    """Dependency-free structural HTML text extractor for trusted input payloads."""

    ignored_tags = {"script", "style", "iframe", "svg", "footer", "header", "nav", "colgroup"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._ignore_depth = 0
        self._chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in self.ignored_tags:
            self._ignore_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in self.ignored_tags and self._ignore_depth:
            self._ignore_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._ignore_depth == 0 and data.strip():
            self._chunks.append(data)

    def clean_text(self) -> str:
        return normalize_text(" ".join(self._chunks))


def normalize_text(value: str) -> str:
    return " ".join(html.unescape(value or "").split())


def stable_signature(source_url: str, clean_text: str) -> str:
    digest_input = f"{source_url.strip()}::{clean_text[:600]}".encode("utf-8")
    return hashlib.sha256(digest_input).hexdigest()


def deterministic_vector(text: str, dimensions: int = 64) -> list[float]:
    """Small local embedding surrogate for ranking and dedupe when model APIs are unavailable."""
    normalized = normalize_text(text).lower()
    if not normalized:
        return [0.0] * dimensions
    buckets = [0.0] * dimensions
    for token in re.findall(r"[a-z0-9][a-z0-9+\-_.#/]*", normalized):
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        bucket = int.from_bytes(digest[:2], "big") % dimensions
        sign = 1.0 if digest[2] % 2 == 0 else -1.0
        buckets[bucket] += sign
    norm = sum(value * value for value in buckets) ** 0.5 or 1.0
    return [round(value / norm, 6) for value in buckets]


@dataclass(frozen=True)
class OpportunityInput:
    source_platform: str
    source_url: str
    raw_text: str = ""
    raw_html: str = ""
    wo_number: str = ""
    client: str = ""
    location: str = ""
    schedule: str = ""
    pay_text: str = ""
    work_type: str = ""
    distance_miles: float | None = None
    deadline: str = ""
    buyer_message: str = ""


@dataclass(frozen=True)
class PitchArtifact:
    strategic_angle: str
    portfolio_alignment: list[str]
    generated_cover_letter: str
    counter_message: str
    decision: str


@dataclass(frozen=True)
class OpportunityEvaluation:
    signature: str
    source_platform: str
    wo_number: str
    client: str
    location: str
    schedule: str
    pay_text: str
    work_type: str
    distance_miles: float | None
    estimated_effective_hourly: float | None
    minimum_acceptable_total: float
    risk_flags: list[str]
    matched_keywords: list[str]
    score: float
    grade: str
    decision: str
    exact_next_action: str
    pitch: PitchArtifact
    generated_at: str
    vector: list[float] = field(repr=False)


def _extract_money(pay_text: str, clean_text: str) -> float | None:
    joined = f"{pay_text} {clean_text}"
    candidates = []
    for match in re.finditer(r"\$\s*([0-9]{2,5}(?:\.[0-9]{1,2})?)", joined):
        candidates.append(float(match.group(1)))
    return max(candidates) if candidates else None


def _extract_hours(clean_text: str) -> float:
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*(?:hour|hr|hrs|hours)", clean_text, flags=re.I)
    if not match:
        return DEFAULT_POLICY["default_minimum_hours"]
    return max(float(match.group(1)), 0.5)


def _infer_fields(payload: OpportunityInput, clean_text: str) -> OpportunityInput:
    text = clean_text
    wo_number = payload.wo_number
    if not wo_number:
        match = re.search(r"\b(?:WO|work\s*order)\s*#?\s*:?\s*([0-9]{6,12})\b", text, flags=re.I)
        wo_number = match.group(1) if match else ""

    pay_text = payload.pay_text
    if not pay_text:
        money = _extract_money("", text)
        pay_text = f"${money:.0f}" if money else ""

    location = payload.location
    if not location:
        match = re.search(
            r"\b(Phoenix|Tempe|Chandler|Mesa|Scottsdale|Glendale|Gilbert|Peoria|Surprise|Avondale|Goodyear|Maricopa),?\s+AZ(?:\s+[0-9]{5})?",
            text,
            flags=re.I,
        )
        location = match.group(0) if match else ""

    work_type = payload.work_type
    if not work_type:
        lowered = text.lower()
        for keyword in sorted(FIELD_SERVICE_KEYWORDS, key=len, reverse=True):
            if keyword in lowered:
                work_type = keyword.title()
                break

    return OpportunityInput(
        source_platform=payload.source_platform,
        source_url=payload.source_url,
        raw_text=payload.raw_text,
        raw_html=payload.raw_html,
        wo_number=wo_number,
        client=payload.client,
        location=location,
        schedule=payload.schedule,
        pay_text=pay_text,
        work_type=work_type,
        distance_miles=payload.distance_miles,
        deadline=payload.deadline,
        buyer_message=payload.buyer_message,
    )


class OpportunityStore:
    def __init__(self, db_path: str | Path | None = None) -> None:
        base = Path(tempfile.gettempdir()) / "profitengine_opportunity_intelligence"
        base.mkdir(parents=True, exist_ok=True)
        self.db_path = Path(db_path) if db_path else base / "opportunity_intelligence.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=20)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def _init_db(self) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS opportunities (
                    signature TEXT PRIMARY KEY,
                    wo_number TEXT,
                    source_platform TEXT NOT NULL,
                    client TEXT,
                    location TEXT,
                    schedule TEXT,
                    pay_text TEXT,
                    work_type TEXT,
                    grade TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    score REAL NOT NULL,
                    payload_json TEXT NOT NULL,
                    vector_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS outcomes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    signature TEXT NOT NULL,
                    conversion_status TEXT NOT NULL,
                    weight_delta_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS weights (
                    key TEXT PRIMARY KEY,
                    value REAL NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def get_weight(self, key: str, default: float) -> float:
        with self.connect() as conn:
            row = conn.execute("SELECT value FROM weights WHERE key = ?", (key,)).fetchone()
        return float(row["value"]) if row else default

    def set_weight(self, key: str, value: float) -> None:
        bounded = max(0.1, min(3.0, float(value)))
        with self.connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO weights (key, value, updated_at) VALUES (?, ?, ?)",
                (key, bounded, datetime.now(UTC).isoformat()),
            )
            conn.commit()

    def save(self, evaluation: OpportunityEvaluation) -> None:
        now = datetime.now(UTC).isoformat()
        payload = asdict(evaluation)
        payload["pitch"] = asdict(evaluation.pitch)
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO opportunities (
                    signature, wo_number, source_platform, client, location, schedule,
                    pay_text, work_type, grade, decision, score, payload_json,
                    vector_json, created_at, updated_at
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?,
                    COALESCE((SELECT created_at FROM opportunities WHERE signature = ?), ?),
                    ?
                )
                """,
                (
                    evaluation.signature,
                    evaluation.wo_number,
                    evaluation.source_platform,
                    evaluation.client,
                    evaluation.location,
                    evaluation.schedule,
                    evaluation.pay_text,
                    evaluation.work_type,
                    evaluation.grade,
                    evaluation.decision,
                    evaluation.score,
                    json.dumps(payload, sort_keys=True),
                    json.dumps(evaluation.vector),
                    evaluation.signature,
                    now,
                    now,
                ),
            )
            conn.commit()

    def recent(self, limit: int = 25) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT payload_json FROM opportunities ORDER BY updated_at DESC LIMIT ?",
                (max(1, limit),),
            ).fetchall()
        return [json.loads(row["payload_json"]) for row in rows]

    def register_outcome(self, signature: str, conversion_status: str) -> dict[str, float]:
        status = conversion_status.strip().upper()
        if status not in {"INTERVIEW_SECURED", "ACCEPTED", "REJECTED_INSTANTLY", "NO_RESPONSE", "DECLINED"}:
            raise ValueError(f"unsupported conversion_status={conversion_status!r}")

        with self.connect() as conn:
            row = conn.execute("SELECT payload_json FROM opportunities WHERE signature = ?", (signature,)).fetchone()
        if not row:
            raise KeyError(f"unknown opportunity signature={signature}")

        payload = json.loads(row["payload_json"])
        direction = 1.0 if status in {"INTERVIEW_SECURED", "ACCEPTED"} else -1.0 if status in {"REJECTED_INSTANTLY", "DECLINED"} else 0.0
        deltas: dict[str, float] = {}
        if direction:
            for keyword in payload.get("matched_keywords", []):
                key = f"keyword:{keyword}"
                current = self.get_weight(key, 1.0)
                updated = current + (0.05 * direction)
                self.set_weight(key, updated)
                deltas[key] = max(0.1, min(3.0, updated))

        with self.connect() as conn:
            conn.execute(
                "INSERT INTO outcomes (signature, conversion_status, weight_delta_json, created_at) VALUES (?, ?, ?, ?)",
                (signature, status, json.dumps(deltas, sort_keys=True), datetime.now(UTC).isoformat()),
            )
            conn.commit()
        return deltas


class OpportunityIntelligenceEngine:
    def __init__(self, store: OpportunityStore | None = None, policy: dict[str, float] | None = None) -> None:
        self.store = store or OpportunityStore()
        self.policy = {**DEFAULT_POLICY, **(policy or {})}

    def transform(self, raw_html: str, raw_text: str, source_url: str) -> tuple[str, str]:
        if raw_html.strip():
            parser = CleanTextExtractor()
            parser.feed(raw_html)
            clean_text = parser.clean_text()
        else:
            clean_text = normalize_text(raw_text)
        return stable_signature(source_url, clean_text), clean_text

    def evaluate(self, payload: OpportunityInput, persist: bool = True) -> OpportunityEvaluation:
        signature, clean_text = self.transform(payload.raw_html, payload.raw_text, payload.source_url)
        inferred = _infer_fields(payload, clean_text)
        context = normalize_text(" ".join([
            clean_text,
            inferred.work_type,
            inferred.location,
            inferred.pay_text,
            inferred.buyer_message,
        ]))
        vector = deterministic_vector(context)
        pay = _extract_money(inferred.pay_text, clean_text)
        hours = _extract_hours(clean_text)
        effective = (pay / hours) if pay is not None else None

        lowered = context.lower()
        matched_keywords = [
            keyword for keyword in FIELD_SERVICE_KEYWORDS
            if keyword in lowered
        ]

        risk_flags = sorted({
            flag for term, flag in HIGH_RISK_TERMS.items()
            if term in lowered
        })
        if not inferred.work_type:
            risk_flags.append("scope_not_classified")
        if not inferred.location:
            risk_flags.append("location_missing")
        if pay is None:
            risk_flags.append("pay_missing")
        elif pay < self.policy["minimum_dispatch_value"]:
            risk_flags.append("below_minimum_dispatch_value")
        if inferred.distance_miles and inferred.distance_miles > self.policy["priority_radius_miles"]:
            risk_flags.append("outside_priority_radius")
        elif inferred.distance_miles and inferred.distance_miles > 35:
            risk_flags.append("high_travel_time")

        minimum_total = self._minimum_total(inferred, risk_flags)
        score = self._score(inferred, matched_keywords, risk_flags, pay, effective)
        grade = self._grade(score, risk_flags, pay)
        decision = self._decision(grade, risk_flags, pay, minimum_total)
        next_action = self._next_action(decision, minimum_total)
        pitch = self._pitch(inferred, risk_flags, minimum_total, decision, matched_keywords)

        evaluation = OpportunityEvaluation(
            signature=signature,
            source_platform=inferred.source_platform,
            wo_number=inferred.wo_number,
            client=inferred.client,
            location=inferred.location,
            schedule=inferred.schedule,
            pay_text=inferred.pay_text,
            work_type=inferred.work_type,
            distance_miles=inferred.distance_miles,
            estimated_effective_hourly=round(effective, 2) if effective is not None else None,
            minimum_acceptable_total=round(minimum_total, 2),
            risk_flags=risk_flags,
            matched_keywords=matched_keywords,
            score=round(score, 2),
            grade=grade,
            decision=decision,
            exact_next_action=next_action,
            pitch=pitch,
            generated_at=datetime.now(UTC).isoformat(),
            vector=vector,
        )
        if persist:
            self.store.save(evaluation)
        return evaluation

    def _score(
        self,
        payload: OpportunityInput,
        matched_keywords: list[str],
        risk_flags: list[str],
        pay: float | None,
        effective: float | None,
    ) -> float:
        score = 50.0
        city = payload.location.lower()
        if any(priority_city in city for priority_city in PHOENIX_PRIORITY_CITIES):
            score += self.policy["phoenix_city_bonus"]
        if payload.distance_miles is not None and payload.distance_miles <= 25:
            score += self.policy["low_travel_bonus"]
        if payload.buyer_message:
            score += 4.0
        if payload.schedule and any(term in payload.schedule.lower() for term in ("today", "tomorrow", "same-day", "same day")):
            score += self.policy["same_day_priority_bonus"]

        for keyword in matched_keywords:
            score += 6.0 * FIELD_SERVICE_KEYWORDS[keyword] * self.store.get_weight(f"keyword:{keyword}", 1.0)

        if pay is None:
            score -= self.policy["unknown_pay_penalty"]
        elif pay < self.policy["minimum_dispatch_value"]:
            score -= self.policy["under_minimum_penalty"]
        elif effective is not None and effective >= self.policy["preferred_effective_hourly"]:
            score += 14.0

        if "vague_scope" in risk_flags or "scope_not_classified" in risk_flags:
            score -= self.policy["vague_scope_penalty"]
        if "large_format_display" in risk_flags or "heavy_lift_exposure" in risk_flags:
            score -= self.policy["heavy_lift_penalty"]
        if "return_trip_exposure" in risk_flags or "diagnostic_expansion" in risk_flags:
            score -= self.policy["return_trip_penalty"]
        if "high_travel_time" in risk_flags:
            score -= 8.0
        return max(0.0, min(100.0, score))

    def _minimum_total(self, payload: OpportunityInput, risk_flags: Iterable[str]) -> float:
        flags = set(risk_flags)
        if "large_format_display" in flags or "heavy_lift_exposure" in flags or "helper_coordination" in flags:
            return max(self.policy["counter_floor_large_format"], self.policy["minimum_dispatch_value"])
        if payload.distance_miles and payload.distance_miles > 35:
            return max(150.0, self.policy["minimum_dispatch_value"])
        return self.policy["counter_floor_standard"]

    def _grade(self, score: float, risk_flags: list[str], pay: float | None) -> str:
        if pay is not None and pay < self.policy["minimum_dispatch_value"]:
            return "C"
        if "pay_missing" in risk_flags or "scope_not_classified" in risk_flags:
            return "C"
        if score >= 82:
            return "A"
        if score >= 68:
            return "B"
        if score >= 45:
            return "C"
        return "Avoid"

    def _decision(self, grade: str, risk_flags: list[str], pay: float | None, minimum_total: float) -> str:
        if grade == "Avoid":
            return "DISCARD"
        if pay is None:
            return "COUNTER"
        if pay < minimum_total:
            return "COUNTER"
        if any(flag in risk_flags for flag in ("return_trip_exposure", "wall_removal_scope", "helper_coordination")):
            return "HUMAN_APPROVAL"
        return "PROCEED"

    def _next_action(self, decision: str, minimum_total: float) -> str:
        if decision == "PROCEED":
            return "Proceed only after confirming calendar availability and platform payment/admin status."
        if decision == "COUNTER":
            return f"Counter at ${minimum_total:.0f} fixed minimum or discard if buyer rejects."
        if decision == "HUMAN_APPROVAL":
            return "Hold for human approval before any platform response or external send."
        return "Discard; do not spend time on this opportunity."

    def _pitch(
        self,
        payload: OpportunityInput,
        risk_flags: list[str],
        minimum_total: float,
        decision: str,
        matched_keywords: list[str],
    ) -> PitchArtifact:
        platform = payload.source_platform or "the platform"
        work_type = payload.work_type or "field service"
        location = payload.location or "the listed site"
        strategic_angle = (
            f"Position Already Here LLC as the low-risk onsite execution option for {work_type} in {location}. "
            "Lead with speed, documentation quality, and scope control."
        )
        alignment = [
            "Already Here LLC onsite IT, smart-hands, AV/display, POS, printer, AP/wireless, and low-voltage field execution",
            "Closeout documentation: photos, sign-off, risk notes, and escalation trail",
            "Stephen Franklin: veteran field engineer with enterprise, healthcare, retail, and rollout experience",
        ]
        risk_sentence = ", ".join(risk_flags) if risk_flags else "standard field-service controls"
        if decision == "COUNTER":
            counter = (
                "Hello,\n\n"
                "Thank you for reaching out.\n\n"
                f"Due to travel, scheduling commitment, and the {work_type} scope, my minimum rate for this dispatch is "
                f"${minimum_total:.0f} fixed. This includes onsite labor, standard diagnosis/remediation within approved scope, "
                "documentation, and checkout.\n\n"
                "Any additional visits, waiting time, helper requirements beyond approved scope, parts, mounting work, or scope expansion "
                "requires prior approval before proceeding.\n\n"
                "If approved, I can confirm availability.\n\n"
                "Thank you,\n\n"
                "Stephen Franklin\n"
                "Already Here LLC"
            )
        else:
            counter = ""
        cover = (
            f"I can handle this {work_type} request through Already Here LLC with clean onsite execution and closeout documentation. "
            f"I will control the main risk areas before work starts: {risk_sentence}. "
            f"For {platform}, I will proceed only inside the approved scope and documented payment terms."
        )
        return PitchArtifact(
            strategic_angle=strategic_angle,
            portfolio_alignment=alignment if matched_keywords else alignment[:2],
            generated_cover_letter=cover,
            counter_message=counter,
            decision=decision,
        )


def evaluate_payload(payload: dict[str, Any], db_path: str | Path | None = None) -> dict[str, Any]:
    engine = OpportunityIntelligenceEngine(store=OpportunityStore(db_path=db_path))
    evaluation = engine.evaluate(OpportunityInput(**payload))
    result = asdict(evaluation)
    result["pitch"] = asdict(evaluation.pitch)
    return result
