"""Tests for client classes."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from browser_use_lite import AsyncBrowserUseCloud, BrowserUseCloud
from browser_use_lite.sessions import AsyncSessionsResource, SessionsResource


class TestBrowserUseCloud:
    def test_init_with_api_key(self):
        client = BrowserUseCloud(api_key="test-key")
        assert isinstance(client.sessions, SessionsResource)
        client.close()

    def test_init_from_env(self):
        with patch.dict(os.environ, {"BROWSER_USE_API_KEY": "env-key"}):
            client = BrowserUseCloud()
            assert isinstance(client.sessions, SessionsResource)
            client.close()

    def test_init_raises_without_key(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="api_key must be provided"):
                BrowserUseCloud()

    def test_contexts_returns_none(self):
        client = BrowserUseCloud(api_key="test-key")
        assert client.contexts is None
        client.close()

    def test_capabilities(self):
        client = BrowserUseCloud(api_key="test-key")
        assert "proxy" in client.capabilities
        assert "custom_proxy" in client.capabilities
        assert "screen_size" in client.capabilities
        client.close()

    def test_context_manager(self):
        with BrowserUseCloud(api_key="test-key") as client:
            assert isinstance(client.sessions, SessionsResource)

    def test_custom_base_url(self):
        client = BrowserUseCloud(api_key="key", base_url="https://custom.api.com")
        assert client._http._client.base_url == "https://custom.api.com"
        client.close()

    def test_custom_timeout(self):
        client = BrowserUseCloud(api_key="key", timeout=30.0)
        client.close()


class TestAsyncBrowserUseCloud:
    def test_init_with_api_key(self):
        client = AsyncBrowserUseCloud(api_key="test-key")
        assert isinstance(client.sessions, AsyncSessionsResource)

    def test_init_raises_without_key(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="api_key must be provided"):
                AsyncBrowserUseCloud()

    def test_contexts_returns_none(self):
        client = AsyncBrowserUseCloud(api_key="test-key")
        assert client.contexts is None

    def test_capabilities(self):
        client = AsyncBrowserUseCloud(api_key="test-key")
        assert client.capabilities == ["proxy", "custom_proxy", "screen_size"]

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        async with AsyncBrowserUseCloud(api_key="test-key") as client:
            assert isinstance(client.sessions, AsyncSessionsResource)


class TestAliases:
    def test_browser_use_alias(self):
        from browser_use_lite import BrowserUse

        assert BrowserUse is BrowserUseCloud

    def test_async_browser_use_alias(self):
        from browser_use_lite import AsyncBrowserUse

        assert AsyncBrowserUse is AsyncBrowserUseCloud
