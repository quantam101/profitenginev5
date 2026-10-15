"""
Shared bounded retry for outbound HTTP calls.

Every runtime client used to fire each external request exactly once, so a
transient failure (DNS blip, connect timeout, 429, 5xx) permanently dropped
whatever it was carrying — a publish, a newsletter send, or a revenue-system
event headed for Daily Command. This module centralizes the recover-from-error
half of action planning: bounded retries with exponential backoff + jitter,
``Retry-After`` honored, and *only* transient failures retried — a 4xx
(other than 429) is a caller bug or a dead credential and is raised
immediately.

Stdlib ``urllib.error`` and ``httpx`` exceptions are both classified lazily —
httpx is an optional dependency in some runtimes, so it is imported inside the
predicate rather than at module level.
"""
from __future__ import annotations

import logging
import random
import time
import urllib.error
from dataclasses import dataclass
from typing import Any, Callable, Optional, TypeVar

logger = logging.getLogger("resilience")

T = TypeVar("T")

# Seconds. Deliberately short ceilings: these calls run inside cron jobs and
# CI workers where a 5-minute stall is worse than a clean failure.
DEFAULT_RETRIES = 3
DEFAULT_BASE_DELAY = 0.5
DEFAULT_MAX_DELAY = 30.0

_TRANSIENT_STATUSES = frozenset({408, 425, 429, 500, 502, 503, 504})


@dataclass(frozen=True)
class RetryDecision:
    retryable: bool
    retry_after: Optional[float] = None


def classify_http_status(status: int, retry_after: Optional[float] = None) -> RetryDecision:
    """429/5xx/timeouts are transient; every other status fails fast."""
    return RetryDecision(retryable=status in _TRANSIENT_STATUSES, retry_after=retry_after)


def _parse_retry_after(value: Optional[str]) -> Optional[float]:
    if not value:
        return None
    value = value.strip()
    if value.isdigit():
        return float(value)
    # HTTP-date form is rare from JSON APIs; parsing it is stdlib-cheap.
    from email.utils import parsedate_to_datetime

    try:
        dt = parsedate_to_datetime(value)
        return max(0.0, dt.timestamp() - time.time())
    except (TypeError, ValueError):
        return None


def _httpx_retry_after(exc: BaseException) -> Optional[float]:
    response = getattr(exc, "response", None)
    if response is None:
        return None
    try:
        return _parse_retry_after(response.headers.get("Retry-After"))
    except Exception:
        return None


def classify_exception(exc: BaseException) -> RetryDecision:
    """Decide whether ``exc`` is worth retrying.

    Transient: connection/timeout errors (urllib URLError without an HTTP
    status, OSError, TimeoutError) and HTTP 429/5xx. Permanent: every other
    HTTP status — a 401/403/404/422 will fail identically on retry.
    """
    if isinstance(exc, urllib.error.HTTPError):
        return classify_http_status(exc.code, _parse_retry_after(exc.headers.get("Retry-After") if exc.headers else None))
    if isinstance(exc, urllib.error.URLError):
        return RetryDecision(retryable=True)
    if isinstance(exc, (TimeoutError, ConnectionError, OSError)):
        return RetryDecision(retryable=True)

    # httpx (optional dep) — duck-typed so this module imports cleanly without it.
    try:
        import httpx  # noqa: PLC0415

        if isinstance(exc, httpx.HTTPStatusError):
            return classify_http_status(
                exc.response.status_code, _httpx_retry_after(exc)
            )
        if isinstance(exc, httpx.RequestError):
            return RetryDecision(retryable=True)
    except ImportError:  # pragma: no cover - httpx is present in this repo
        pass

    return RetryDecision(retryable=False)


def call_with_retries(
    fn: Callable[[], T],
    *,
    retries: int = DEFAULT_RETRIES,
    base_delay: float = DEFAULT_BASE_DELAY,
    max_delay: float = DEFAULT_MAX_DELAY,
    sleep: Callable[[float], None] = time.sleep,
    on_retry: Optional[Callable[[int, BaseException, float], None]] = None,
    label: str = "request",
) -> T:
    """Call ``fn`` with up to ``retries`` additional attempts on transient failure.

    Delay is ``base_delay * 2**attempt`` with +/-25% jitter, capped at
    ``max_delay``; a server-provided ``Retry-After`` overrides it (still
    capped). Non-retryable exceptions propagate immediately.
    """
    attempt = 0
    while True:
        try:
            return fn()
        except Exception as exc:
            decision = classify_exception(exc)
            if not decision.retryable or attempt >= retries:
                raise
            delay = min(
                max_delay,
                decision.retry_after
                if decision.retry_after is not None
                else base_delay * (2**attempt) * random.uniform(0.75, 1.25),
            )
            logger.warning(
                "%s transient failure (attempt %d/%d): %s — retrying in %.1fs",
                label, attempt + 1, retries + 1, exc, delay,
            )
            if on_retry is not None:
                on_retry(attempt + 1, exc, delay)
            sleep(delay)
            attempt += 1


def urlopen_with_retries(
    request: Any,
    *,
    timeout: float = 20,
    retries: int = DEFAULT_RETRIES,
    base_delay: float = DEFAULT_BASE_DELAY,
    max_delay: float = DEFAULT_MAX_DELAY,
    label: Optional[str] = None,
    **kwargs: Any,
) -> Any:
    """``urllib.request.urlopen`` with bounded retry on transient failures.

    The caller still owns status handling for non-2xx responses that
    ``urlopen`` surfaces as ``HTTPError`` after retries are exhausted.
    """
    import urllib.request

    return call_with_retries(
        lambda: urllib.request.urlopen(request, timeout=timeout),
        retries=retries,
        base_delay=base_delay,
        max_delay=max_delay,
        label=label or f"{request.get_method()} {request.full_url}",
        **kwargs,
    )
