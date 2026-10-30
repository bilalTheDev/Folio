"""Unit tests for in-process IP rate limiting."""

from __future__ import annotations

from backend.app.security.rate_limit import _hits, allow_request, client_ip


def setup_function() -> None:
    _hits.clear()


def teardown_function() -> None:
    _hits.clear()


def test_client_ip_from_forwarded_for() -> None:
    assert client_ip({"X-Forwarded-For": "1.2.3.4, 5.6.7.8"}) == "1.2.3.4"
    assert client_ip({"x-real-ip": "9.9.9.9"}) == "9.9.9.9"
    assert client_ip({}, fallback="local") == "local"


def test_allow_request_window() -> None:
    assert allow_request("k", limit=2, window_seconds=60) == (True, 0)
    assert allow_request("k", limit=2, window_seconds=60) == (True, 0)
    allowed, retry = allow_request("k", limit=2, window_seconds=60)
    assert allowed is False
    assert retry >= 1
