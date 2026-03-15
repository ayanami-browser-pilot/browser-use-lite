"""Session CRUD resources for browser-use cloud browser SDK."""

from __future__ import annotations

from typing import Any

from .exceptions import SessionNotFoundError
from .models import (
    ContextAttach,
    FingerprintConfig,
    ManagedProxyConfig,
    ProxyConfig,
    RecordingConfig,
    SessionInfo,
    map_status,
)


def _to_session_info(
    data: dict[str, Any],
    delete_fn: Any = None,
) -> SessionInfo:
    """Map browser-use API response dict to SessionInfo.

    Field mapping:
        id (UUID)    -> session_id (str)
        cdpUrl       -> cdp_url
        status       -> status (active->active, stopped->closed)
        liveUrl      -> inspect_url
        startedAt    -> created_at
        remaining    -> metadata
    """
    info = SessionInfo(
        session_id=str(data.get("id", "")),
        cdp_url=data.get("cdpUrl"),
        status=map_status(data.get("status", "active")),
        created_at=data.get("startedAt"),
        inspect_url=data.get("liveUrl"),
        metadata={
            k: v
            for k, v in data.items()
            if k not in {
                "id",
                "cdpUrl",
                "status",
                "startedAt",
                "liveUrl",
            }
        },
    )
    if delete_fn is not None:
        info.set_delete_fn(delete_fn)
    return info


def _build_create_body(
    proxy: ProxyConfig | ManagedProxyConfig | None,
    vendor_params: dict[str, Any],
) -> dict[str, Any]:
    """Build the JSON body for POST /browsers."""
    body: dict[str, Any] = {}

    # Managed proxy -> proxyCountryCode
    if isinstance(proxy, ManagedProxyConfig):
        body["proxyCountryCode"] = proxy.country.upper()

    # Custom proxy -> customProxy object
    if isinstance(proxy, ProxyConfig):
        host_port = proxy.server.split(":", 1)
        custom: dict[str, Any] = {"host": host_port[0]}
        if len(host_port) > 1:
            try:
                custom["port"] = int(host_port[1])
            except ValueError:
                custom["port"] = host_port[1]
        if proxy.username:
            custom["username"] = proxy.username
        if proxy.password:
            custom["password"] = proxy.password
        body["customProxy"] = custom

    # Vendor params passthrough with key mapping
    _VENDOR_KEY_MAP: dict[str, str] = {
        "profile_id": "profileId",
        "timeout": "timeout",
        "browser_screen_width": "browserScreenWidth",
        "browser_screen_height": "browserScreenHeight",
        "allow_resizing": "allowResizing",
    }
    for sdk_key, api_key in _VENDOR_KEY_MAP.items():
        if sdk_key in vendor_params:
            body[api_key] = vendor_params[sdk_key]

    return body


class SessionsResource:
    """Synchronous session CRUD operations."""

    def __init__(self, http: Any) -> None:
        self._http = http

    def create(
        self,
        *,
        proxy: ProxyConfig | ManagedProxyConfig | None = None,
        recording: RecordingConfig | None = None,
        fingerprint: FingerprintConfig | str | None = None,
        context: ContextAttach | None = None,
        **vendor_params: Any,
    ) -> SessionInfo:
        """Create a browser session.

        Returns a SessionInfo with cdp_url ready for connection.
        browser-use returns cdpUrl directly — no polling needed.
        """
        body = _build_create_body(proxy, vendor_params)
        data = self._http.request("POST", "/browsers", json=body)

        session_id = str(data.get("id", ""))

        def _delete() -> None:
            self.delete(session_id)

        return _to_session_info(data, delete_fn=_delete)

    def get(self, session_id: str) -> SessionInfo:
        """Get session info by ID."""
        data = self._http.request("GET", f"/browsers/{session_id}")
        return _to_session_info(data)

    def list(
        self,
        *,
        page_size: int | None = None,
        page_number: int | None = None,
        filter_by: str | None = None,
        **filters: Any,
    ) -> list[SessionInfo]:
        """List sessions, optionally filtered."""
        params: dict[str, Any] = {}
        if page_size is not None:
            params["pageSize"] = page_size
        if page_number is not None:
            params["pageNumber"] = page_number
        if filter_by is not None:
            params["filterBy"] = filter_by
        params.update(filters)

        data = self._http.request(
            "GET", "/browsers", params=params if params else None
        )
        if isinstance(data, list):
            return [_to_session_info(item) for item in data]
        # Handle wrapped responses
        items = data.get("browsers") or data.get("items") or []
        return [_to_session_info(item) for item in items]

    def delete(self, session_id: str) -> None:
        """Stop a browser session. Idempotent — ignores 404."""
        try:
            self._http.request(
                "PATCH", f"/browsers/{session_id}", json={"action": "stop"}
            )
        except SessionNotFoundError:
            pass  # Already stopped or deleted


class AsyncSessionsResource:
    """Asynchronous session CRUD operations."""

    def __init__(self, http: Any) -> None:
        self._http = http

    async def create(
        self,
        *,
        proxy: ProxyConfig | ManagedProxyConfig | None = None,
        recording: RecordingConfig | None = None,
        fingerprint: FingerprintConfig | str | None = None,
        context: ContextAttach | None = None,
        **vendor_params: Any,
    ) -> SessionInfo:
        """Create a browser session (async).

        Returns a SessionInfo with cdp_url ready for connection.
        browser-use returns cdpUrl directly — no polling needed.
        """
        body = _build_create_body(proxy, vendor_params)
        data = await self._http.request("POST", "/browsers", json=body)

        session_id = str(data.get("id", ""))

        def _delete() -> None:
            import asyncio

            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                loop.create_task(self.delete(session_id))
            else:
                asyncio.run(self.delete(session_id))

        return _to_session_info(data, delete_fn=_delete)

    async def get(self, session_id: str) -> SessionInfo:
        """Get session info by ID (async)."""
        data = await self._http.request("GET", f"/browsers/{session_id}")
        return _to_session_info(data)

    async def list(
        self,
        *,
        page_size: int | None = None,
        page_number: int | None = None,
        filter_by: str | None = None,
        **filters: Any,
    ) -> list[SessionInfo]:
        """List sessions (async), optionally filtered."""
        params: dict[str, Any] = {}
        if page_size is not None:
            params["pageSize"] = page_size
        if page_number is not None:
            params["pageNumber"] = page_number
        if filter_by is not None:
            params["filterBy"] = filter_by
        params.update(filters)

        data = await self._http.request(
            "GET", "/browsers", params=params if params else None
        )
        if isinstance(data, list):
            return [_to_session_info(item) for item in data]
        items = data.get("browsers") or data.get("items") or []
        return [_to_session_info(item) for item in items]

    async def delete(self, session_id: str) -> None:
        """Stop a browser session (async). Idempotent — ignores 404."""
        try:
            await self._http.request(
                "PATCH", f"/browsers/{session_id}", json={"action": "stop"}
            )
        except SessionNotFoundError:
            pass
