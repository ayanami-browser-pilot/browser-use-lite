# browser-use-lite

Minimal cloud browser SDK for [browser-use](https://browser-use.com) — session lifecycle management via CDP.

## Install

```bash
pip install browser-use-lite
```

## Quick Start

```python
from browser_use_lite import BrowserUseCloud

client = BrowserUseCloud(api_key="bu-...")  # or set BROWSER_USE_API_KEY env var

# Create a cloud browser session
session = client.sessions.create()
print(session.cdp_url)    # wss://...
print(session.session_id)

# Use with Playwright
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    browser = pw.chromium.connect_over_cdp(session.cdp_url)
    page = browser.contexts[0].new_page()
    page.goto("https://example.com")

# Cleanup
client.sessions.delete(session.session_id)

# Or use context manager for auto-cleanup
with client.sessions.create() as session:
    ...  # session auto-deleted on exit
```

## Session CRUD

```python
session = client.sessions.create()       # POST /browsers
info    = client.sessions.get(session_id) # GET  /browsers/{id}
items   = client.sessions.list()          # GET  /browsers
client.sessions.delete(session_id)        # PATCH /browsers/{id} (stop)
```

## Proxy Support

```python
from browser_use_lite import ManagedProxyConfig, ProxyConfig

# Managed proxy (200+ countries)
session = client.sessions.create(proxy=ManagedProxyConfig(country="US"))

# Custom proxy
session = client.sessions.create(proxy=ProxyConfig(
    server="proxy.example.com:8080",
    username="user",
    password="pass",
))
```

## Vendor Parameters

```python
session = client.sessions.create(
    profile_id="prof-123",          # Browser profile
    timeout=120,                    # Minutes (1-240)
    browser_screen_width=1920,
    browser_screen_height=1080,
    allow_resizing=True,
)
```

## Feature Matrix

| Feature | Supported | Notes |
|---------|-----------|-------|
| Managed proxy | Yes | 200+ country codes |
| Custom proxy | Yes | host/port/username/password |
| Screen size | Yes | browserScreenWidth/Height |
| Timeout | Yes | 1-240 minutes |
| Profile | Yes | profileId as vendor_param |
| Fingerprint | No | API does not support |
| Recording | No | Only via Task API |

## Exception Hierarchy

```
CloudBrowserError
├── AuthenticationError     # 401/403
├── QuotaExceededError      # 429 (has .retry_after)
├── SessionNotFoundError    # 404
├── ProviderError           # 5xx (has .status_code, .request_id)
├── TimeoutError
└── NetworkError
```

## Async Support

```python
from browser_use_lite import AsyncBrowserUseCloud

async with AsyncBrowserUseCloud(api_key="bu-...") as client:
    session = await client.sessions.create()
    await client.sessions.delete(session.session_id)
```

## License

MIT
