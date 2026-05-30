"""Unit tests for classic-API client actions and WiFi/known-client helpers.

These cover the fixes for:
- #44: block/unblock/reconnect/forget go through the classic ``cmd/stamgr``
  endpoint (the official Integration API does not support them).
- #40: known/offline clients fetched from the classic ``/rest/user`` endpoint.
- #49: classic ``/rest/wlanconf`` (secrets) and ``/stat/sta`` (per-SSID counts).
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

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
