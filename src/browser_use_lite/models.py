"""Data models for cloud browser SDK."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Status mapping: browser-use -> spec
# ---------------------------------------------------------------------------

_STATUS_MAP: dict[str, str] = {
    "active": "active",
    "stopped": "closed",
}


def map_status(browser_use_status: str) -> str:
    """Map a browser-use status string to the unified spec status."""
    return _STATUS_MAP.get(browser_use_status, browser_use_status)


# ---------------------------------------------------------------------------
# Configuration models
# ---------------------------------------------------------------------------


class ManagedProxyConfig(BaseModel):
    """Managed proxy configuration -- provider handles the proxy.

    browser-use supports 200+ country codes via proxyCountryCode.
    Pass the ISO country code directly (e.g., "US", "GB", "DE").
    """

    country: str
    city: str | None = None


class ProxyConfig(BaseModel):
    """Custom proxy configuration (server + credentials).

    browser-use supports custom proxies via the customProxy field.
    The server field should be in "host:port" format.
    """

    server: str
    username: str | None = None
    password: str | None = None


class RecordingConfig(BaseModel):
    """Recording configuration.

    Note: browser-use BaaS API does not support recording.
    Only available via the Task/Sessions API.
    """

    enabled: bool = True


class ViewportConfig(BaseModel):
    """Viewport dimensions."""

    width: int = 1920
    height: int = 1080
    device_scale_factor: float = 1.0
    is_mobile: bool = False


class FingerprintConfig(BaseModel):
    """Browser fingerprint configuration. All fields optional.

    Note: browser-use API does not support fingerprint parameters.
    """

    user_agent: str | None = None
    viewport: ViewportConfig | None = None
    locale: str | None = None
    timezone: str | None = None
    webgl_vendor: str | None = None
    webgl_renderer: str | None = None
    platform: str | None = None


class ContextAttach(BaseModel):
    """Context attachment for session creation."""

    context_id: str
    mode: str = "read_write"


# ---------------------------------------------------------------------------
# SessionInfo
# ---------------------------------------------------------------------------


class SessionInfo(BaseModel):
    """Browser session information returned by create/get/list."""

    session_id: str
    cdp_url: str | None = None
    status: str = "active"
    created_at: datetime | None = None
    inspect_url: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Internal: deletion callback for context manager support.
    # Excluded from serialization.
    _delete_fn: Callable[[], None] | None = None

    model_config = {"arbitrary_types_allowed": True}

    def set_delete_fn(self, fn: Callable[[], None]) -> None:
        """Attach a deletion callback for context manager support."""
        object.__setattr__(self, "_delete_fn", fn)

    # --- Context manager protocol ---

    def __enter__(self) -> "SessionInfo":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        fn = getattr(self, "_delete_fn", None)
        if fn is not None:
            fn()
