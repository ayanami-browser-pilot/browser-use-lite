"""browser-use Cloud Browser SDK -- minimal interface for browser session lifecycle.

Quick Start
-----------
::

    from browser_use_lite import BrowserUseCloud

    client = BrowserUseCloud(api_key="bu-...")  # or set BROWSER_USE_API_KEY env var

    # Create a cloud browser session
    session = client.sessions.create()
    print(session.cdp_url)   # wss://...
    print(session.session_id)

    # Use with Playwright (or any CDP client)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser = pw.chromium.connect_over_cdp(session.cdp_url)
        page = browser.contexts[0].new_page()
        page.goto("https://example.com")

    # Cleanup
    client.sessions.delete(session.session_id)

    # Or use context manager for auto-cleanup:
    with client.sessions.create() as session:
        ...  # session auto-deleted on exit

API Reference
-------------

Client Classes
~~~~~~~~~~~~~~
- ``BrowserUseCloud(api_key, *, base_url, timeout, max_retries)``  -- Sync client
- ``AsyncBrowserUseCloud(api_key, *, base_url, timeout, max_retries)`` -- Async client
- ``BrowserUse`` / ``AsyncBrowserUse`` -- Short aliases

Client Properties
~~~~~~~~~~~~~~~~~
- ``client.sessions``     -- SessionsResource for CRUD operations
- ``client.contexts``     -- Always None (context persistence via CDP at framework layer)
- ``client.capabilities`` -- Returns ``["proxy", "custom_proxy", "screen_size"]``

Session CRUD (``client.sessions``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- ``create(*, proxy, recording, fingerprint, context, **vendor_params) -> SessionInfo``
- ``get(session_id) -> SessionInfo``
- ``list(*, page_size, page_number, filter_by, **filters) -> list[SessionInfo]``
- ``delete(session_id) -> None``  (idempotent, safe to call multiple times)

Vendor Parameters (pass via ``**vendor_params`` in ``create()``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- ``profile_id: str``            -- Browser profile ID (maps to profileId)
- ``timeout: int``               -- Session timeout in minutes (1-240)
- ``browser_screen_width: int``  -- Browser screen width
- ``browser_screen_height: int`` -- Browser screen height
- ``allow_resizing: bool``       -- Allow browser resizing

Feature Support Matrix
~~~~~~~~~~~~~~~~~~~~~~
=========================  =========  ==================================================
Feature                    Supported  Notes
=========================  =========  ==================================================
Managed proxy              Yes        200+ country codes via proxyCountryCode
Custom proxy               Yes        host/port/username/password via customProxy
Screen size                Yes        browserScreenWidth/Height
Session timeout            Yes        1-240 minutes
Profile                    Yes        profileId as vendor_param (context via CDP)
Browser fingerprint        No         API does not support fingerprint parameters
Recording                  No         Only via Task API, not BaaS
Extensions                 No         API does not support extensions
=========================  =========  ==================================================

SessionInfo Fields
~~~~~~~~~~~~~~~~~~
- ``session_id: str``           -- Unique session identifier (UUID as string)
- ``cdp_url: str | None``       -- CDP WebSocket URL (wss://)
- ``status: str``               -- "active" or "closed"
- ``created_at: datetime | None``
- ``inspect_url: str | None``   -- Live browser view URL
- ``metadata: dict``            -- Vendor-specific data (timeoutAt, finishedAt, costs, etc.)

Proxy Configuration
~~~~~~~~~~~~~~~~~~~
- ``ManagedProxyConfig(country="US")``        -- Use browser-use managed proxy
- ``ProxyConfig(server="host:port", ...)``    -- Use custom proxy server

Exception Hierarchy
~~~~~~~~~~~~~~~~~~~
::

    CloudBrowserError          # Base exception
    +-- AuthenticationError    # 401/403 -- invalid or expired API key
    +-- QuotaExceededError     # 429 -- rate limit (has .retry_after attribute)
    +-- SessionNotFoundError   # 404 -- session doesn't exist
    +-- ProviderError          # 5xx -- server error (has .status_code, .request_id)
    +-- TimeoutError           # Operation timed out
    +-- NetworkError           # Connection failure
"""

from .client import AsyncBrowserUseCloud, BrowserUseCloud
from .exceptions import (
    AuthenticationError,
    CloudBrowserError,
    NetworkError,
    ProviderError,
    QuotaExceededError,
    SessionNotFoundError,
    TimeoutError,
)
from .models import (
    ContextAttach,
    FingerprintConfig,
    ManagedProxyConfig,
    ProxyConfig,
    RecordingConfig,
    SessionInfo,
    ViewportConfig,
)

# Short aliases
BrowserUse = BrowserUseCloud
AsyncBrowserUse = AsyncBrowserUseCloud

__all__ = [
    # Clients
    "BrowserUseCloud",
    "AsyncBrowserUseCloud",
    "BrowserUse",
    "AsyncBrowserUse",
    # Models
    "SessionInfo",
    "ContextAttach",
    "FingerprintConfig",
    "ViewportConfig",
    "ProxyConfig",
    "ManagedProxyConfig",
    "RecordingConfig",
    # Exceptions
    "CloudBrowserError",
    "AuthenticationError",
    "QuotaExceededError",
    "SessionNotFoundError",
    "ProviderError",
    "TimeoutError",
    "NetworkError",
]
