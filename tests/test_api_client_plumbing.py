# Copyright 2026 UniFi Insights contributors
"""Tests for UniFi API client shared plumbing."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Self
from unittest.mock import MagicMock, patch

import aiohttp
import pytest
from yarl import URL

from custom_components.unifi_insights.api import (
    ApiKeyAuth,
    ConnectionType,
    LocalAuth,
)
from custom_components.unifi_insights.api.base import (
    BaseUniFiClient,
    parse_retry_after,
)
from custom_components.unifi_insights.api.const import (
    DEFAULT_RATE_LIMIT_RETRY_AFTER,
    RATE_LIMIT_MAX_RETRY_AFTER,
)
from custom_components.unifi_insights.api.exceptions import (
    UniFiAuthenticationError,
    UniFiConnectionError,
    UniFiTimeoutError,
)
from custom_components.unifi_insights.api.network import UniFiNetworkClient
from custom_components.unifi_insights.api.network.models.application import (
    ApplicationInfo,
)


class _Response:
    """Minimal response for client plumbing tests."""

    def __init__(
        self,
        body: Any = None,
        status: int = 200,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status = status
        self._body = body
        self.headers = headers or {}
        self.url = URL("https://192.168.1.1")
        self.method = "GET"
        self.history = ()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *args: object) -> None:
        pass

    async def text(self) -> str:
        """Return a placeholder body, or empty when there is none."""
        if self._body is None:
            return ""
        return "mock-body"

    async def json(self) -> Any:
        """Return the configured JSON body."""
        return self._body


class _Session:
    """Session recording requests."""

    closed = False

    def __init__(self, responses: list[Any]) -> None:
        self._responses = iter(
            [r if isinstance(r, _Response) else _Response(r) for r in responses]
        )
        self.requests: list[dict[str, Any]] = []

    def request(self, method: str, url: object, **kwargs: Any) -> _Response:
        """Record a request and return the next queued response."""
        self.requests.append({"method": method, "url": str(url), **kwargs})
        return next(self._responses)

    async def close(self) -> None:
        """Mark the session closed."""
        self.closed = True


class _DummyClient(BaseUniFiClient):
    """Concrete BaseUniFiClient for testing base plumbing."""

    async def validate_connection(self) -> bool:
        return True


# -----------------------------------------------------------------------------
# Base API Client Plumbing Tests
# -----------------------------------------------------------------------------


def test_parse_retry_after_edge_cases() -> None:
    """parse_retry_after handles naive datetime and non-finite numbers."""
    # 1. Naive datetime without tzinfo
    with patch("custom_components.unifi_insights.api.base.datetime") as mock_datetime:
        mock_datetime.now.return_value = datetime(2026, 10, 21, 7, 27, tzinfo=UTC)
        res_naive = parse_retry_after({"Retry-After": "Wed, 21 Oct 2026 07:28:00"})
    assert res_naive == 60

    # 2. Non-finite float (inf / nan)
    assert parse_retry_after({"Retry-After": "inf"}) == DEFAULT_RATE_LIMIT_RETRY_AFTER
    assert parse_retry_after({"Retry-After": "nan"}) == DEFAULT_RATE_LIMIT_RETRY_AFTER


async def test_base_client_closed_property() -> None:
    """Base client closed property reflects the open/closed state."""
    client = _DummyClient(
        auth=ApiKeyAuth(api_key="key"),
        base_url="https://192.168.1.1",
    )
    assert client.closed is False
    await client.close()
    assert client.closed is True


def test_base_client_ssl_context_local_and_cloud() -> None:
    """Base client _ssl_context respects LocalAuth verify_ssl flag."""
    client_local_insecure = _DummyClient(
        auth=LocalAuth(api_key="k", verify_ssl=False),
        base_url="https://192.168.1.1",
    )
    assert client_local_insecure._get_ssl_context() is False

    client_local_secure = _DummyClient(
        auth=LocalAuth(api_key="k", verify_ssl=True),
        base_url="https://192.168.1.1",
    )
    assert client_local_secure._get_ssl_context() is True

    client_api_key = _DummyClient(
        auth=ApiKeyAuth(api_key="key"),
        base_url="https://192.168.1.1",
    )
    assert client_api_key._get_ssl_context() is True


def test_base_client_defer_after_rate_limit_defaults_to_max() -> None:
    """_defer_after_rate_limit uses max retry after when None."""
    limiter = MagicMock()
    client = _DummyClient(
        auth=ApiKeyAuth(api_key="key"),
        base_url="https://192.168.1.1",
    )
    client._rate_limiter = limiter
    client._defer_after_rate_limit(retry_after=None)
    limiter.defer.assert_called_once_with(RATE_LIMIT_MAX_RETRY_AFTER)


async def test_base_client_custom_headers_in_request_once() -> None:
    """_request_once merges caller-provided custom headers."""
    session = _Session([{"ok": True}])
    client = _DummyClient(
        auth=ApiKeyAuth(api_key="key"),
        base_url="https://192.168.1.1",
        session=session,  # type: ignore[arg-type]
    )
    await client._request_once(
        "GET", "/endpoint", headers={"X-Custom-Header": "custom-val"}
    )
    assert session.requests[0]["headers"].get("X-Custom-Header") == "custom-val"


async def test_base_client_connection_error_mapping() -> None:
    """_request_once maps ClientConnectorError and TimeoutError."""
    session = MagicMock()
    session.closed = False

    # 1. ClientConnectorError -> UniFiConnectionError
    conn_key = MagicMock()
    session.request.side_effect = aiohttp.ClientConnectorError(
        connection_key=conn_key, os_error=OSError("connection refused")
    )
    client = _DummyClient(
        auth=ApiKeyAuth(api_key="key"),
        base_url="https://192.168.1.1",
        session=session,
    )
    with pytest.raises(UniFiConnectionError, match="Failed to connect"):
        await client._request_once("GET", "/test")

    # 2. TimeoutError -> UniFiTimeoutError
    session.request.side_effect = TimeoutError()
    with pytest.raises(UniFiTimeoutError, match="timed out"):
        await client._request_once("GET", "/test")


async def test_base_client_patch_and_delete_methods() -> None:
    """_patch and _delete delegate to _request with correct verbs and params."""
    session = _Session([{"patched": True}, {"deleted": True}])
    client = _DummyClient(
        auth=ApiKeyAuth(api_key="key"),
        base_url="https://192.168.1.1",
        session=session,  # type: ignore[arg-type]
    )

    patch_res = await client._patch("/items/1", json_data={"enabled": False})
    assert patch_res == {"patched": True}
    assert session.requests[0]["method"] == "PATCH"
    assert session.requests[0]["json"] == {"enabled": False}

    del_res = await client._delete("/items/1", params={"purge": "true"})
    assert del_res == {"deleted": True}
    assert session.requests[1]["method"] == "DELETE"
    assert session.requests[1]["params"] == {"purge": "true"}


async def test_base_client_close_owns_session() -> None:
    """close() closes the session if client created and owns it."""
    client = _DummyClient(
        auth=ApiKeyAuth(api_key="key"),
        base_url="https://192.168.1.1",
    )
    session = await client._ensure_session()
    assert client._owns_session is True
    assert not session.closed

    await client.close()
    assert session.closed


# -----------------------------------------------------------------------------
# UniFi Network Client Plumbing Tests
# -----------------------------------------------------------------------------


def test_network_client_local_without_base_url_raises() -> None:
    """Initializing a LOCAL Network client without base_url raises ValueError."""
    with pytest.raises(ValueError, match="base_url is required"):
        UniFiNetworkClient(
            auth=ApiKeyAuth(api_key="key"),
            connection_type=ConnectionType.LOCAL,
            base_url=None,
        )


def test_network_client_properties_and_path_normalizations() -> None:
    """Network client properties and leading slash handling."""
    client = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="key"),
        connection_type=ConnectionType.LOCAL,
        base_url="https://192.168.1.1",
        console_id="console-local",
    )
    assert client.connection_type == ConnectionType.LOCAL
    assert client.console_id == "console-local"
    assert client.acl is not None
    assert client.dns is not None

    # build_api_path without leading slash
    assert client.build_api_path("sites") == "/proxy/network/integration/v1/sites"

    # build_legacy_global_api_path without leading slash
    assert (
        client.build_legacy_global_api_path("self/sites")
        == "/proxy/network/api/self/sites"
    )

    # build_legacy_api_path with empty site_name raises ValueError
    with pytest.raises(ValueError, match="site_name is required"):
        client.build_legacy_api_path("", "stat/device")


async def test_network_client_validate_connection() -> None:
    """validate_connection() returns True when /sites returns data, False on None."""
    session = _Session([{"data": []}, None])
    client = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="key"),
        connection_type=ConnectionType.LOCAL,
        base_url="https://192.168.1.1",
        session=session,  # type: ignore[arg-type]
    )

    assert await client.validate_connection() is True
    assert await client.validate_connection() is False


async def test_network_client_get_hosts_validations() -> None:
    """get_hosts() enforces REMOTE connection and ApiKeyAuth."""
    # 1. LOCAL connection raises ValueError
    client_local = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="key"),
        connection_type=ConnectionType.LOCAL,
        base_url="https://192.168.1.1",
    )
    with pytest.raises(ValueError, match="only available for REMOTE connections"):
        await client_local.get_hosts()

    # 2. REMOTE with LocalAuth raises ValueError
    client_remote_local_auth = UniFiNetworkClient(
        auth=LocalAuth(api_key="k"),
        connection_type=ConnectionType.REMOTE,
    )
    with pytest.raises(ValueError, match="requires cloud API key authentication"):
        await client_remote_local_auth.get_hosts()


async def test_network_client_get_application_info() -> None:
    """get_application_info() fetches ApplicationInfo model or raises."""
    session = _Session(
        [
            {"data": {"applicationVersion": "10.6.106"}},
            {"data": "not-a-dict"},
        ]
    )
    client = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="key"),
        connection_type=ConnectionType.LOCAL,
        base_url="https://192.168.1.1",
        session=session,  # type: ignore[arg-type]
    )

    info = await client.get_application_info()
    assert isinstance(info, ApplicationInfo)
    assert info.application_version == "10.6.106"

    msg = "Unable to retrieve application info"
    with pytest.raises(ValueError, match=msg):
        await client.get_application_info()


async def test_base_client_context_manager_and_auth_errors() -> None:
    """Base client async context manager and 401/403 status mappings."""
    session = _Session(
        [
            _Response("Unauthorized", status=401),
            _Response("Forbidden", status=403),
        ]
    )
    async with _DummyClient(
        auth=ApiKeyAuth(api_key="key"),
        base_url="https://192.168.1.1",
        session=session,  # type: ignore[arg-type]
    ) as client:
        assert client.base_url == URL("https://192.168.1.1")

        with pytest.raises(UniFiAuthenticationError, match="Authentication failed"):
            await client._get("/unauth")

        with pytest.raises(UniFiAuthenticationError, match="Access forbidden"):
            await client._get("/forbidden")


def test_network_client_build_api_path_remote() -> None:
    """Network client build_api_path prefixes remote connector path."""
    client = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="key"),
        connection_type=ConnectionType.REMOTE,
        console_id="cid-99",
    )
    assert (
        client.build_api_path("sites")
        == "/v1/connector/consoles/cid-99/network/integration/v1/sites"
    )
