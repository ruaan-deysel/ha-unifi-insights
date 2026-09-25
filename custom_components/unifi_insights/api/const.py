"""Constants for the UniFi Official API library."""

from __future__ import annotations

from enum import Enum
from typing import Final

__version__: Final[str] = "1.2.0+vendored"


class ConnectionType(str, Enum):
    """
    Connection type for UniFi API access.

    LOCAL: Direct connection to the UniFi console (e.g., https://192.168.1.1)
           - Uses local API key generated on the console
           - Endpoints: /proxy/network/integration/v1/...

    REMOTE: Cloud connection via Ubiquiti's API (https://api.ui.com)
            - Uses cloud API key from account.ui.com
            - Endpoints: /v1/connector/consoles/{consoleId}/network/integration/v1/...
    """

    LOCAL = "local"
    REMOTE = "remote"


# API Base URLs
NETWORK_API_BASE_URL: Final[str] = "https://api.ui.com"
PROTECT_API_BASE_URL: Final[str] = "https://api.ui.com"
INNERSPACE_API_BASE_URL: Final[str] = "https://api.ui.com"

# API Versions
NETWORK_API_VERSION: Final[str] = "v1"
PROTECT_API_VERSION: Final[str] = "v1"
INNERSPACE_API_VERSION: Final[str] = "v1"

# Network Integration API path prefix (used for both local and remote)
NETWORK_INTEGRATION_PATH: Final[str] = "/proxy/network/integration/v1"

# Network legacy API path prefix (used for both local and remote)
NETWORK_LEGACY_PATH: Final[str] = "/proxy/network/api"

# Network legacy v2 API path prefix (used for traffic routes / policy-based routes)
NETWORK_LEGACY_V2_PATH: Final[str] = "/proxy/network/v2/api"

# Network legacy v2 endpoints
ENDPOINT_TRAFFIC_ROUTES: Final[str] = "trafficroutes"

# Network legacy REST endpoints
ENDPOINT_NETWORKCONF: Final[str] = "rest/networkconf"
# Live state of VPN clients and site-to-site tunnels (v2, per connection).
ENDPOINT_VPN_CONNECTIONS: Final[str] = "vpn/connections"

# Protect Integration API path prefix (used for both local and remote)
PROTECT_INTEGRATION_PATH: Final[str] = "/proxy/protect/integration/v1"

# InnerSpace Integration API path prefix (used for both local and remote)
INNERSPACE_INTEGRATION_PATH: Final[str] = "/proxy/innerspace/integration/v1"

# Default timeouts (in seconds)
DEFAULT_TIMEOUT: Final[int] = 30
DEFAULT_CONNECT_TIMEOUT: Final[int] = 10

# Rate limiting
DEFAULT_RATE_LIMIT_RETRY_AFTER: Final[int] = 60

# The local Protect Integration API allows 10 requests per fixed 1-second
# window per API key, and advertises it on every response
# (`RateLimit-Policy: "10-in-1sec"; q=10; w=1`). A 429 carries
# `Retry-After: 1`. The Network Integration API sends no rate-limit headers
# and its requests do not draw from the Protect allowance.
PROTECT_RATE_LIMIT_REQUESTS: Final[int] = 10
PROTECT_RATE_LIMIT_WINDOW: Final[float] = 1.0
# Added to the window on the client side so request-arrival jitter cannot
# land an 11th request inside one of the server's fixed windows.
RATE_LIMIT_WINDOW_MARGIN: Final[float] = 0.1
# A 429 is retried once after its Retry-After only when the server asks for a
# short wait; a longer (or missing, i.e. defaulted) Retry-After is raised to
# the caller as before, so a request never blocks for a minute.
RATE_LIMIT_MAX_RETRY_AFTER: Final[int] = 5

# User agent - uses version from single source of truth
USER_AGENT: Final[str] = f"unifi-official-api/{__version__}"

# HTTP Headers
HEADER_CONTENT_TYPE: Final[str] = "Content-Type"
HEADER_ACCEPT: Final[str] = "Accept"
HEADER_USER_AGENT: Final[str] = "User-Agent"
HEADER_API_KEY: Final[str] = "X-API-Key"

# Content types
CONTENT_TYPE_JSON: Final[str] = "application/json"
