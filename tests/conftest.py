"""Shared test fixtures."""

from __future__ import annotations

from typing import Any

import pytest

from browser_use_lite.sessions import AsyncSessionsResource, SessionsResource


class FakeSyncHttp:
    """Fake sync HTTP client for testing."""

    def __init__(self, responses: dict[str, Any] | None = None):
        self.responses: dict[str, Any] = responses or {}
        self.calls: list[tuple[str, str, dict[str, Any] | None]] = []

    def request(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.calls.append((method, path, json))
        key = f"{method} {path}"
        response = self.responses.get(key, {})
        if callable(response):
            return response()
        if isinstance(response, Exception):
            raise response
        return response


class FakeAsyncHttp:
    """Fake async HTTP client for testing."""

    def __init__(self, responses: dict[str, Any] | None = None):
        self.responses: dict[str, Any] = responses or {}
        self.calls: list[tuple[str, str, dict[str, Any] | None]] = []

    async def request(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.calls.append((method, path, json))
        key = f"{method} {path}"
        response = self.responses.get(key, {})
        if callable(response):
            return response()
        if isinstance(response, Exception):
            raise response
        return response


SAMPLE_BROWSER_RESPONSE = {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "cdpUrl": "wss://browser.browser-use.com/devtools/browser/abc",
    "status": "active",
    "startedAt": "2026-01-15T10:00:00Z",
    "liveUrl": "https://live.browser-use.com/sessions/550e8400",
}


@pytest.fixture
def sample_response() -> dict[str, Any]:
    return dict(SAMPLE_BROWSER_RESPONSE)


@pytest.fixture
def fake_sync_http() -> FakeSyncHttp:
    return FakeSyncHttp()


@pytest.fixture
def fake_async_http() -> FakeAsyncHttp:
    return FakeAsyncHttp()


@pytest.fixture
def sync_sessions(fake_sync_http: FakeSyncHttp) -> SessionsResource:
    return SessionsResource(fake_sync_http)


@pytest.fixture
def async_sessions(fake_async_http: FakeAsyncHttp) -> AsyncSessionsResource:
    return AsyncSessionsResource(fake_async_http)
