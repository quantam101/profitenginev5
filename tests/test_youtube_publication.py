from __future__ import annotations

import io
import json
import sys
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from youtube_publication import (  # noqa: E402
    canonical_video_url,
    verified_youtube_uploads,
    video_id_from_upload,
)


class FakeResponse:
    def __init__(self, payload: dict, status: int = 200) -> None:
        self.status = status
        self._body = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return self._body


def ok_opener(request, timeout=0):
    assert "youtube.com/oembed" in request.full_url
    assert timeout > 0
    return FakeResponse({"title": "Verified video", "author_name": "Already Here LLC"})


def missing_opener(request, timeout=0):
    raise urllib.error.HTTPError(request.full_url, 404, "Not Found", {}, io.BytesIO())


def test_extracts_standard_watch_and_shorts_ids():
    video_id = "AbCdEf123_-"
    assert video_id_from_upload({"video_id": video_id}) == video_id
    assert video_id_from_upload({"url": f"https://www.youtube.com/watch?v={video_id}"}) == video_id
    assert video_id_from_upload({"url": f"https://www.youtube.com/shorts/{video_id}"}) == video_id
    assert video_id_from_upload({"url": f"https://youtu.be/{video_id}"}) == video_id
    assert canonical_video_url({"video_id": video_id}) == f"https://www.youtube.com/watch?v={video_id}"


def test_rejects_invalid_or_non_youtube_ids():
    assert video_id_from_upload({"video_id": "short"}) == ""
    assert video_id_from_upload({"url": "https://example.com/watch?v=AbCdEf123_-"}) == ""
    assert video_id_from_upload({}) == ""


def test_only_verified_successful_uploads_survive_and_duplicates_collapse():
    video_id = "AbCdEf123_-"
    uploads = [
        {"status": "success", "video_id": video_id, "url": "https://youtu.be/AbCdEf123_-"},
        {"status": "success", "video_id": video_id},
        {"status": "failed", "video_id": "ZyXwVu987_-"},
    ]
    result = verified_youtube_uploads(uploads, opener=ok_opener)
    assert len(result) == 1
    assert result[0]["video_id"] == video_id
    assert result[0]["url"] == f"https://www.youtube.com/watch?v={video_id}"
    assert result[0]["verified_public"] is True


def test_http_failure_fails_closed():
    uploads = [{"status": "success", "video_id": "AbCdEf123_-"}]
    assert verified_youtube_uploads(uploads, opener=missing_opener) == []
