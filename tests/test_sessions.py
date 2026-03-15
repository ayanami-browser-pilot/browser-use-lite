"""Tests for session CRUD resources."""

from __future__ import annotations

from typing import Any

import pytest

from browser_use_lite.exceptions import SessionNotFoundError
from browser_use_lite.models import ManagedProxyConfig, ProxyConfig
from browser_use_lite.sessions import SessionsResource, _build_create_body, _to_session_info

from .conftest import SAMPLE_BROWSER_RESPONSE, FakeAsyncHttp, FakeSyncHttp


class TestToSessionInfo:
    def test_maps_fields(self):
        info = _to_session_info(SAMPLE_BROWSER_RESPONSE)
        assert info.session_id == "550e8400-e29b-41d4-a716-446655440000"
        assert info.cdp_url == "wss://browser.browser-use.com/devtools/browser/abc"
        assert info.status == "active"
        assert info.inspect_url == "https://live.browser-use.com/sessions/550e8400"

    def test_stopped_status_maps_to_closed(self):
        data = {**SAMPLE_BROWSER_RESPONSE, "status": "stopped"}
        info = _to_session_info(data)
        assert info.status == "closed"

    def test_extra_fields_in_metadata(self):
        data = {
            **SAMPLE_BROWSER_RESPONSE,
            "timeoutAt": "2026-01-15T11:00:00Z",
            "proxyCost": 0.05,
            "browserCost": 0.10,
        }
        info = _to_session_info(data)
        assert info.metadata["timeoutAt"] == "2026-01-15T11:00:00Z"
        assert info.metadata["proxyCost"] == 0.05
        assert info.metadata["browserCost"] == 0.10

    def test_delete_fn_attached(self):
        called = False

        def _delete():
            nonlocal called
            called = True

        info = _to_session_info(SAMPLE_BROWSER_RESPONSE, delete_fn=_delete)
        info.__exit__(None, None, None)
        assert called


class TestBuildCreateBody:
    def test_empty_body(self):
        body = _build_create_body(None, {})
        assert body == {}

    def test_managed_proxy(self):
        proxy = ManagedProxyConfig(country="us")
        body = _build_create_body(proxy, {})
        assert body["proxyCountryCode"] == "US"

    def test_custom_proxy(self):
        proxy = ProxyConfig(
            server="proxy.example.com:8080",
            username="user",
            password="pass",
        )
        body = _build_create_body(proxy, {})
        custom = body["customProxy"]
        assert custom["host"] == "proxy.example.com"
        assert custom["port"] == 8080
        assert custom["username"] == "user"
        assert custom["password"] == "pass"

    def test_custom_proxy_no_credentials(self):
        proxy = ProxyConfig(server="proxy.example.com:8080")
        body = _build_create_body(proxy, {})
        custom = body["customProxy"]
        assert custom["host"] == "proxy.example.com"
        assert custom["port"] == 8080
        assert "username" not in custom
        assert "password" not in custom

    def test_vendor_params_passthrough(self):
        body = _build_create_body(
            None,
            {
                "profile_id": "prof-123",
                "timeout": 120,
                "browser_screen_width": 1920,
                "browser_screen_height": 1080,
                "allow_resizing": True,
            },
        )
        assert body["profileId"] == "prof-123"
        assert body["timeout"] == 120
        assert body["browserScreenWidth"] == 1920
        assert body["browserScreenHeight"] == 1080
        assert body["allowResizing"] is True

    def test_unknown_vendor_params_ignored(self):
        body = _build_create_body(None, {"unknown_param": "x"})
        assert "unknown_param" not in body
        assert body == {}


class TestSessionsResourceCreate:
    def test_create_returns_session_info(self, sample_response: dict[str, Any]):
        http = FakeSyncHttp(responses={
            "POST /browsers": sample_response,
        })
        sessions = SessionsResource(http)
        info = sessions.create()
        assert info.session_id == "550e8400-e29b-41d4-a716-446655440000"
        assert info.cdp_url == "wss://browser.browser-use.com/devtools/browser/abc"
        assert info.status == "active"

    def test_create_context_manager(self, sample_response: dict[str, Any]):
        http = FakeSyncHttp(responses={
            "POST /browsers": sample_response,
            "PATCH /browsers/550e8400-e29b-41d4-a716-446655440000": {},
        })
        sessions = SessionsResource(http)

        with sessions.create() as session:
            assert session.session_id == "550e8400-e29b-41d4-a716-446655440000"

        # Verify delete (stop) was called
        patch_calls = [c for c in http.calls if c[0] == "PATCH"]
        assert len(patch_calls) == 1
        assert patch_calls[0][2] == {"action": "stop"}

    def test_create_with_managed_proxy(self, sample_response: dict[str, Any]):
        http = FakeSyncHttp(responses={
            "POST /browsers": sample_response,
        })
        sessions = SessionsResource(http)
        sessions.create(proxy=ManagedProxyConfig(country="US"))
        assert http.calls[0][2] == {"proxyCountryCode": "US"}

    def test_create_with_custom_proxy(self, sample_response: dict[str, Any]):
        http = FakeSyncHttp(responses={
            "POST /browsers": sample_response,
        })
        sessions = SessionsResource(http)
        sessions.create(proxy=ProxyConfig(
            server="proxy.example.com:8080",
            username="user",
            password="pass",
        ))
        body = http.calls[0][2]
        assert body["customProxy"]["host"] == "proxy.example.com"
        assert body["customProxy"]["port"] == 8080

    def test_create_with_profile_id(self, sample_response: dict[str, Any]):
        http = FakeSyncHttp(responses={
            "POST /browsers": sample_response,
        })
        sessions = SessionsResource(http)
        sessions.create(profile_id="prof-abc")
        assert http.calls[0][2] == {"profileId": "prof-abc"}


class TestSessionsResourceGet:
    def test_get(self, sample_response: dict[str, Any]):
        http = FakeSyncHttp(responses={
            "GET /browsers/550e8400": sample_response,
        })
        sessions = SessionsResource(http)
        info = sessions.get("550e8400")
        assert info.session_id == "550e8400-e29b-41d4-a716-446655440000"


class TestSessionsResourceList:
    def test_list_array_response(self, sample_response: dict[str, Any]):
        http = FakeSyncHttp(responses={
            "GET /browsers": [sample_response, sample_response],
        })
        sessions = SessionsResource(http)
        result = sessions.list()
        assert len(result) == 2
        assert all(
            s.session_id == "550e8400-e29b-41d4-a716-446655440000" for s in result
        )

    def test_list_wrapped_response(self, sample_response: dict[str, Any]):
        http = FakeSyncHttp(responses={
            "GET /browsers": {
                "browsers": [sample_response],
            },
        })
        sessions = SessionsResource(http)
        result = sessions.list()
        assert len(result) == 1


class TestSessionsResourceDelete:
    def test_delete_success(self):
        http = FakeSyncHttp(responses={
            "PATCH /browsers/sess-123": {},
        })
        sessions = SessionsResource(http)
        sessions.delete("sess-123")  # should not raise
        assert http.calls[0] == ("PATCH", "/browsers/sess-123", {"action": "stop"})

    def test_delete_idempotent_on_404(self):
        http = FakeSyncHttp(responses={
            "PATCH /browsers/sess-123": SessionNotFoundError("not found"),
        })
        sessions = SessionsResource(http)
        sessions.delete("sess-123")  # should not raise


class TestAsyncSessionsResource:
    @pytest.mark.asyncio
    async def test_create(self, sample_response: dict[str, Any]):
        from browser_use_lite.sessions import AsyncSessionsResource

        http = FakeAsyncHttp(responses={
            "POST /browsers": sample_response,
        })
        sessions = AsyncSessionsResource(http)
        info = await sessions.create()
        assert info.session_id == "550e8400-e29b-41d4-a716-446655440000"

    @pytest.mark.asyncio
    async def test_get(self, sample_response: dict[str, Any]):
        from browser_use_lite.sessions import AsyncSessionsResource

        http = FakeAsyncHttp(responses={
            "GET /browsers/550e8400": sample_response,
        })
        sessions = AsyncSessionsResource(http)
        info = await sessions.get("550e8400")
        assert info.session_id == "550e8400-e29b-41d4-a716-446655440000"

    @pytest.mark.asyncio
    async def test_delete_idempotent(self):
        from browser_use_lite.sessions import AsyncSessionsResource

        http = FakeAsyncHttp(responses={
            "PATCH /browsers/sess-123": SessionNotFoundError("gone"),
        })
        sessions = AsyncSessionsResource(http)
        await sessions.delete("sess-123")  # should not raise

    @pytest.mark.asyncio
    async def test_list(self, sample_response: dict[str, Any]):
        from browser_use_lite.sessions import AsyncSessionsResource

        http = FakeAsyncHttp(responses={
            "GET /browsers": [sample_response],
        })
        sessions = AsyncSessionsResource(http)
        result = await sessions.list()
        assert len(result) == 1
