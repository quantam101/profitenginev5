"""Tests for runtime.resilience — bounded retry on transient HTTP failures."""

import urllib.error
import urllib.request

import pytest

from runtime.resilience import (
    classify_exception,
    classify_http_status,
    call_with_retries,
    urlopen_with_retries,
)


def _http_error(code, headers=None):
    return urllib.error.HTTPError(
        url="https://example.com/x", code=code, msg="err",
        hdrs=headers, fp=None,
    )


class TestClassify:
    @pytest.mark.parametrize("code", [408, 425, 429, 500, 502, 503, 504])
    def test_transient_statuses_retryable(self, code):
        assert classify_http_status(code).retryable

    @pytest.mark.parametrize("code", [400, 401, 403, 404, 409, 422])
    def test_client_errors_not_retryable(self, code):
        assert not classify_http_status(code).retryable

    def test_url_error_retryable(self):
        assert classify_exception(urllib.error.URLError("conn refused")).retryable

    def test_timeout_retryable(self):
        assert classify_exception(TimeoutError()).retryable
        assert classify_exception(ConnectionError()).retryable

    def test_httpx_status_classification(self):
        httpx = pytest.importorskip("httpx")
        resp = httpx.Response(503, request=httpx.Request("GET", "https://x"))
        exc = httpx.HTTPStatusError("e", request=resp.request, response=resp)
        assert classify_exception(exc).retryable

    def test_httpx_4xx_not_retryable(self):
        httpx = pytest.importorskip("httpx")
        resp = httpx.Response(404, request=httpx.Request("GET", "https://x"))
        exc = httpx.HTTPStatusError("e", request=resp.request, response=resp)
        assert not classify_exception(exc).retryable

    def test_httpx_request_error_retryable(self):
        httpx = pytest.importorskip("httpx")
        exc = httpx.ConnectError("boom", request=httpx.Request("GET", "https://x"))
        assert classify_exception(exc).retryable

    def test_other_exceptions_not_retryable(self):
        assert not classify_exception(ValueError("bad")).retryable


class TestCallWithRetries:
    def test_succeeds_first_try(self):
        calls = []
        out = call_with_retries(lambda: calls.append(1) or "ok", sleep=lambda s: None)
        assert out == "ok"
        assert calls == [1]

    def test_retries_transient_then_succeeds(self):
        attempts = []

        def flaky():
            attempts.append(1)
            if len(attempts) < 3:
                raise urllib.error.URLError("blip")
            return "done"

        out = call_with_retries(flaky, retries=3, sleep=lambda s: None)
        assert out == "done"
        assert len(attempts) == 3

    def test_gives_up_after_retries(self):
        def always_fail():
            raise urllib.error.URLError("down")

        with pytest.raises(urllib.error.URLError):
            call_with_retries(always_fail, retries=2, sleep=lambda s: None)

    def test_permanent_error_not_retried(self):
        attempts = []

        def bad():
            attempts.append(1)
            raise _http_error(403)

        with pytest.raises(urllib.error.HTTPError):
            call_with_retries(bad, retries=5, sleep=lambda s: None)
        assert len(attempts) == 1

    def test_retry_after_header_controls_delay(self):
        sleeps = []

        def rate_limited():
            raise _http_error(429, headers={"Retry-After": "7"})

        with pytest.raises(urllib.error.HTTPError):
            call_with_retries(
                rate_limited, retries=1, sleep=sleeps.append, max_delay=60,
            )
        assert sleeps == [7.0]

    def test_on_retry_callback(self):
        seen = []

        def once():
            raise urllib.error.URLError("x")

        with pytest.raises(urllib.error.URLError):
            call_with_retries(
                once, retries=1, sleep=lambda s: None,
                on_retry=lambda n, e, d: seen.append((n, d)),
            )
        assert len(seen) == 1 and seen[0][0] == 1


class TestUrlopenWithRetries:
    def test_retries_on_transient(self, monkeypatch):
        attempts = []

        class _Resp:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def read(self):
                return b'{"ok": true}'

        def fake_urlopen(req, timeout=0):
            attempts.append(1)
            if len(attempts) == 1:
                raise urllib.error.URLError("conn reset")
            return _Resp()

        monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
        req = urllib.request.Request("https://example.com", method="GET")
        with urlopen_with_retries(req, timeout=5, sleep=lambda s: None) as r:
            assert r.read() == b'{"ok": true}'
        assert len(attempts) == 2
