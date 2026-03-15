"""Cloud browser SDK clients for browser-use."""

from __future__ import annotations

import os
from typing import Any

from ._http import AsyncHttpClient, SyncHttpClient
from .sessions import AsyncSessionsResource, SessionsResource

_DEFAULT_BASE_URL = "https://api.browser-use.com/api/v2"
_ENV_API_KEY = "BROWSER_USE_API_KEY"


class BrowserUseCloud:
    """Synchronous browser-use cloud browser client.

    Usage::

        client = BrowserUseCloud(api_key="bu-...")
        session = client.sessions.create()
        print(session.cdp_url)
        client.sessions.delete(session.session_id)
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str | None = None,
        timeout: float = 60.0,
        max_retries: int = 2,
    ):
        resolved_key = api_key or os.environ.get(_ENV_API_KEY)
        if not resolved_key:
            raise ValueError(
                f"api_key must be provided or set {_ENV_API_KEY} environment variable"
            )
        self._http = SyncHttpClient(
            base_url=base_url or _DEFAULT_BASE_URL,
            api_key=resolved_key,
            timeout=timeout,
            max_retries=max_retries,
        )
        self._sessions = SessionsResource(self._http)

    @property
    def sessions(self) -> SessionsResource:
        """Session lifecycle management."""
        return self._sessions

    @property
    def contexts(self) -> None:
        """browser-use context persistence is handled via CDP at the framework layer."""
        return None

    @property
    def capabilities(self) -> list[str]:
        """Declare supported enhanced capabilities."""
        return ["proxy", "custom_proxy", "screen_size"]

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._http.close()

    def __enter__(self) -> "BrowserUseCloud":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


class AsyncBrowserUseCloud:
    """Asynchronous browser-use cloud browser client.

    Usage::

        async with AsyncBrowserUseCloud(api_key="bu-...") as client:
            session = await client.sessions.create()
            print(session.cdp_url)
            await client.sessions.delete(session.session_id)
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str | None = None,
        timeout: float = 60.0,
        max_retries: int = 2,
    ):
        resolved_key = api_key or os.environ.get(_ENV_API_KEY)
        if not resolved_key:
            raise ValueError(
                f"api_key must be provided or set {_ENV_API_KEY} environment variable"
            )
        self._http = AsyncHttpClient(
            base_url=base_url or _DEFAULT_BASE_URL,
            api_key=resolved_key,
            timeout=timeout,
            max_retries=max_retries,
        )
        self._sessions = AsyncSessionsResource(self._http)

    @property
    def sessions(self) -> AsyncSessionsResource:
        """Session lifecycle management (async)."""
        return self._sessions

    @property
    def contexts(self) -> None:
        """browser-use context persistence is handled via CDP at the framework layer."""
        return None

    @property
    def capabilities(self) -> list[str]:
        """Declare supported enhanced capabilities."""
        return ["proxy", "custom_proxy", "screen_size"]

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._http.close()

    async def __aenter__(self) -> "AsyncBrowserUseCloud":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
