"""Tests for data models."""

import pytest

from browser_use_lite.models import (
    ContextAttach,
    FingerprintConfig,
    ManagedProxyConfig,
    ProxyConfig,
    RecordingConfig,
    SessionInfo,
    ViewportConfig,
    map_status,
)


class TestStatusMapping:
    def test_active_maps_to_active(self):
        assert map_status("active") == "active"

    def test_stopped_maps_to_closed(self):
        assert map_status("stopped") == "closed"

    def test_unknown_passthrough(self):
        assert map_status("unknown_status") == "unknown_status"


class TestSessionInfo:
    def test_required_fields(self):
        info = SessionInfo(
            session_id="s1",
            cdp_url="wss://example.com/devtools",
            status="active",
        )
        assert info.session_id == "s1"
        assert info.cdp_url == "wss://example.com/devtools"
        assert info.status == "active"

    def test_optional_fields_default(self):
        info = SessionInfo(session_id="s1")
        assert info.cdp_url is None
        assert info.created_at is None
        assert info.inspect_url is None
        assert info.metadata == {}

    def test_context_manager_calls_delete(self):
        called = False

        def _delete():
            nonlocal called
            called = True

        info = SessionInfo(session_id="s1", cdp_url="ws://test")
        info.set_delete_fn(_delete)

        with info as s:
            assert s.session_id == "s1"

        assert called

    def test_context_manager_without_delete_fn(self):
        info = SessionInfo(session_id="s1")
        with info:
            pass  # should not raise

    def test_context_manager_calls_delete_on_exception(self):
        called = False

        def _delete():
            nonlocal called
            called = True

        info = SessionInfo(session_id="s1", cdp_url="ws://test")
        info.set_delete_fn(_delete)

        with pytest.raises(ValueError, match="test error"):
            with info:
                raise ValueError("test error")

        assert called

    def test_metadata_dict(self):
        info = SessionInfo(
            session_id="s1",
            metadata={"timeoutAt": "2026-01-15T11:00:00Z", "proxyCost": 0.05},
        )
        assert info.metadata["timeoutAt"] == "2026-01-15T11:00:00Z"
        assert info.metadata["proxyCost"] == 0.05


class TestProxyModels:
    def test_managed_proxy_config(self):
        cfg = ManagedProxyConfig(country="US")
        assert cfg.country == "US"
        assert cfg.city is None

    def test_managed_proxy_config_with_city(self):
        cfg = ManagedProxyConfig(country="US", city="New York")
        assert cfg.city == "New York"

    def test_proxy_config(self):
        cfg = ProxyConfig(server="proxy.example.com:8080", username="u", password="p")
        assert cfg.server == "proxy.example.com:8080"
        assert cfg.username == "u"
        assert cfg.password == "p"

    def test_proxy_config_no_credentials(self):
        cfg = ProxyConfig(server="proxy.example.com:8080")
        assert cfg.username is None
        assert cfg.password is None


class TestConfigModels:
    def test_recording_config(self):
        cfg = RecordingConfig()
        assert cfg.enabled is True

    def test_viewport_config_defaults(self):
        cfg = ViewportConfig()
        assert cfg.width == 1920
        assert cfg.height == 1080
        assert cfg.device_scale_factor == 1.0
        assert cfg.is_mobile is False

    def test_fingerprint_config_all_none(self):
        cfg = FingerprintConfig()
        assert cfg.user_agent is None
        assert cfg.viewport is None

    def test_context_attach(self):
        ctx = ContextAttach(context_id="ctx-1", mode="read_only")
        assert ctx.context_id == "ctx-1"
        assert ctx.mode == "read_only"

    def test_context_attach_default_mode(self):
        ctx = ContextAttach(context_id="ctx-1")
        assert ctx.mode == "read_write"
