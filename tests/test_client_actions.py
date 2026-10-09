"""Unit tests for classic-API client actions and WiFi/known-client helpers.

These cover the fixes for:
- #44: block/unblock/reconnect/forget go through the classic ``cmd/stamgr``
  endpoint (the official Integration API does not support them).
- #40: known/offline clients fetched from the classic ``/rest/user`` endpoint.
- #49: classic ``/rest/wlanconf`` (secrets) and ``/stat/sta`` (per-SSID counts).
"""

from __future__ import annotations

import json
from typing import Any, Self
from unittest.mock import AsyncMock

import pytest
from yarl import URL

from custom_components.unifi_insights.api import ConnectionType, LocalAuth
from custom_components.unifi_insights.api.exceptions import UniFiResponseError
from custom_components.unifi_insights.api.network import UniFiNetworkClient


@pytest.fixture
def network_client() -> UniFiNetworkClient:
    """Create a local network client with the HTTP layer mocked."""
    client = UniFiNetworkClient(
        auth=LocalAuth(api_key="key", verify_ssl=False),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
    )
    client._request = AsyncMock(return_value={"meta": {"rc": "ok"}, "data": []})  # type: ignore[method-assign]
    return client


@pytest.mark.parametrize(
    ("method", "command"),
    [
        ("block", "block-sta"),
        ("unblock", "unblock-sta"),
        ("reconnect", "kick-sta"),
        ("forget", "forget-sta"),
    ],
)
async def test_client_actions_use_classic_stamgr(
    network_client: UniFiNetworkClient, method: str, command: str
) -> None:
    """block/unblock/reconnect/forget POST to /cmd/stamgr with the MAC."""
    result = await getattr(network_client.clients, method)(
        "default", "aa:bb:cc:dd:ee:ff"
    )

    assert result is True
    network_client._request.assert_awaited_once()
    args, kwargs = network_client._request.call_args
    assert args[0] == "POST"
    assert args[1] == "/proxy/network/api/s/default/cmd/stamgr"
    assert kwargs["json_data"] == {"cmd": command, "mac": "aa:bb:cc:dd:ee:ff"}


async def test_execute_action_maps_to_command(
    network_client: UniFiNetworkClient,
) -> None:
    """execute_action maps friendly names to classic commands."""
    await network_client.clients.execute_action("default", "aa:bb", "reconnect")
    _, kwargs = network_client._request.call_args
    assert kwargs["json_data"]["cmd"] == "kick-sta"


async def test_execute_action_rejects_unknown(
    network_client: UniFiNetworkClient,
) -> None:
    """execute_action rejects unsupported actions."""
    with pytest.raises(ValueError, match="Action must be one of"):
        await network_client.clients.execute_action("default", "aa:bb", "bogus")


async def test_stamgr_raises_on_classic_error_envelope(
    network_client: UniFiNetworkClient,
) -> None:
    """A classic API error envelope (HTTP 200, rc=error) raises."""
    network_client._request = AsyncMock(  # type: ignore[method-assign]
        return_value={
            "meta": {"rc": "error", "msg": "api.err.NoSuchObject"},
            "data": [],
        }
    )
    with pytest.raises(UniFiResponseError) as excinfo:
        await network_client.clients.block("default", "aa:bb:cc:dd:ee:ff")
    assert "api.err.NoSuchObject" in str(excinfo.value.args[0])


@pytest.mark.parametrize(
    ("method", "action"),
    [
        ("authorize_guest", "AUTHORIZE_GUEST_ACCESS"),
        ("unauthorize_guest", "UNAUTHORIZE_GUEST_ACCESS"),
    ],
)
async def test_guest_actions_use_official_actions_endpoint(
    network_client: UniFiNetworkClient, method: str, action: str
) -> None:
    """Guest authorization uses the official /actions endpoint."""
    await getattr(network_client.clients, method)("site1", "client1")
    args, kwargs = network_client._request.call_args
    assert args[0] == "POST"
    assert args[1] == (
        "/proxy/network/integration/v1/sites/site1/clients/client1/actions"
    )
    assert kwargs["json_data"] == {"action": action}


async def test_get_active_legacy_parses_data(
    network_client: UniFiNetworkClient,
) -> None:
    """get_active_legacy returns the classic /stat/sta client list."""
    network_client._request = AsyncMock(  # type: ignore[method-assign]
        return_value={"data": [{"mac": "aa:bb", "essid": "Home"}]}
    )
    active = await network_client.clients.get_active_legacy("default")
    assert active == [{"mac": "aa:bb", "essid": "Home"}]
    args, _ = network_client._request.call_args
    assert args[1] == "/proxy/network/api/s/default/stat/sta"


async def test_get_legacy_wlan_configs(network_client: UniFiNetworkClient) -> None:
    """wifi.get_legacy_configs returns the classic /rest/wlanconf list."""
    network_client._request = AsyncMock(  # type: ignore[method-assign]
        return_value={"data": [{"name": "Home", "x_passphrase": "secret"}]}
    )
    configs = await network_client.wifi.get_legacy_configs("default")
    assert configs == [{"name": "Home", "x_passphrase": "secret"}]
    args, _ = network_client._request.call_args
    assert args[1] == "/proxy/network/api/s/default/rest/wlanconf"


class _Response:
    """Minimal aiohttp response replacement for transport tests."""

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
        if isinstance(self._body, (dict, list)):
            return json.dumps(self._body)
        if self._body is None:
            return ""
        return str(self._body)

    async def json(self) -> Any:
        if self._body is None or isinstance(self._body, str):
            msg = "No JSON body"
            raise ValueError(msg)
        return self._body


class _Session:
    """Mock session recording requests and returning queued responses."""

    closed = False

    def __init__(
        self, responses: list[_Response | dict[str, Any] | list[Any] | None]
    ) -> None:
        self._responses = iter(
            [r if isinstance(r, _Response) else _Response(r) for r in responses]
        )
        self.requests: list[dict[str, Any]] = []

    def request(self, method: str, url: object, **kwargs: Any) -> _Response:
        self.requests.append({"method": method, "url": str(url), **kwargs})
        return next(self._responses)

    async def close(self) -> None:
        self.closed = True


def _create_http_client(session: _Session) -> UniFiNetworkClient:
    return UniFiNetworkClient(
        auth=LocalAuth(api_key="key", verify_ssl=False),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
        session=session,  # type: ignore[arg-type]
    )


async def test_get_historical_legacy_parses_data() -> None:
    """get_historical_legacy returns the classic /stat/alluser client list."""
    session = _Session(
        [{"meta": {"rc": "ok"}, "data": [{"mac": "aa:bb", "name": "User"}]}]
    )
    client = _create_http_client(session)
    historical = await client.clients.get_historical_legacy("default")
    assert historical == [{"mac": "aa:bb", "name": "User"}]
    assert len(session.requests) == 1
    req = session.requests[0]
    assert req["method"] == "GET"
    assert req["url"] == "https://192.168.1.1/proxy/network/api/s/default/stat/alluser"


async def test_get_historical_legacy_rc_error() -> None:
    """get_historical_legacy raises UniFiResponseError when meta.rc == error."""
    session = _Session([{"meta": {"rc": "error", "msg": "api.err.InvalidSite"}}])
    client = _create_http_client(session)
    with pytest.raises(UniFiResponseError) as excinfo:
        await client.clients.get_historical_legacy("default")
    assert "api.err.InvalidSite" in str(excinfo.value.args[0])


async def test_get_historical_legacy_rc_failed() -> None:
    """get_historical_legacy raises UniFiResponseError when meta.rc == failed."""
    session = _Session([{"meta": {"rc": "failed", "msg": "api.err.Failed"}}])
    client = _create_http_client(session)
    with pytest.raises(UniFiResponseError) as excinfo:
        await client.clients.get_historical_legacy("default")
    assert "api.err.Failed" in str(excinfo.value.args[0])


async def test_get_historical_legacy_missing_meta() -> None:
    """get_historical_legacy raises UniFiResponseError when meta is missing."""
    session = _Session([{"data": [{"mac": "aa:bb"}]}])
    client = _create_http_client(session)
    with pytest.raises(UniFiResponseError) as excinfo:
        await client.clients.get_historical_legacy("default")
    assert "missing meta envelope" in str(excinfo.value.args[0])


async def test_forget_batch_posts_macs() -> None:
    """forget_batch posts {cmd: forget-sta, macs: [...]} to /cmd/stamgr."""
    session = _Session([{"meta": {"rc": "ok"}}])
    client = _create_http_client(session)
    result = await client.clients.forget_batch(
        "default", ["aa:bb:cc:dd:ee:ff", "11:22:33:44:55:66"]
    )
    assert result is True
    assert len(session.requests) == 1
    req = session.requests[0]
    assert req["method"] == "POST"
    assert req["url"] == "https://192.168.1.1/proxy/network/api/s/default/cmd/stamgr"
    assert req["json"] == {
        "cmd": "forget-sta",
        "macs": ["aa:bb:cc:dd:ee:ff", "11:22:33:44:55:66"],
    }


async def test_forget_batch_empty_macs_sends_no_request() -> None:
    """forget_batch with empty list sends no request and returns True."""
    session = _Session([])
    client = _create_http_client(session)
    result = await client.clients.forget_batch("default", [])
    assert result is True
    assert len(session.requests) == 0


async def test_forget_batch_rc_error() -> None:
    """forget_batch raises UniFiResponseError on error envelope."""
    session = _Session([{"meta": {"rc": "error", "msg": "api.err.CommandFailed"}}])
    client = _create_http_client(session)
    with pytest.raises(UniFiResponseError) as excinfo:
        await client.clients.forget_batch("default", ["aa:bb:cc:dd:ee:ff"])
    assert "api.err.CommandFailed" in str(excinfo.value.args[0])


async def test_forget_batch_rc_failed() -> None:
    """forget_batch raises UniFiResponseError on failed envelope."""
    session = _Session([{"meta": {"rc": "failed", "msg": "api.err.Failed"}}])
    client = _create_http_client(session)
    with pytest.raises(UniFiResponseError) as excinfo:
        await client.clients.forget_batch("default", ["aa:bb:cc:dd:ee:ff"])
    assert "api.err.Failed" in str(excinfo.value.args[0])


async def test_forget_batch_missing_meta() -> None:
    """forget_batch raises UniFiResponseError when meta is missing."""
    session = _Session([{"result": "success"}])
    client = _create_http_client(session)
    with pytest.raises(UniFiResponseError) as excinfo:
        await client.clients.forget_batch("default", ["aa:bb:cc:dd:ee:ff"])
    assert "missing meta envelope" in str(excinfo.value.args[0])
