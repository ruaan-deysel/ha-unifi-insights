"""Tests for the vendored UniFi API package."""

from __future__ import annotations

import logging
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from custom_components.unifi_insights.api import (
    ApiKeyAuth,
    ConnectionType,
    LocalAuth,
    UniFiInnerSpaceClient,
)
from custom_components.unifi_insights.api import base as api_base
from custom_components.unifi_insights.api.base import (
    RequestRateLimiter,
    parse_retry_after,
)
from custom_components.unifi_insights.api.const import (
    DEFAULT_RATE_LIMIT_RETRY_AFTER,
    ENDPOINT_TRAFFIC_ROUTES,
    PROTECT_RATE_LIMIT_REQUESTS,
    PROTECT_RATE_LIMIT_WINDOW,
    RATE_LIMIT_MAX_RETRY_AFTER,
    RATE_LIMIT_WINDOW_MARGIN,
)
from custom_components.unifi_insights.api.exceptions import (
    UniFiConnectionError,
    UniFiRateLimitError,
    UniFiResponseError,
    UniFiValidationError,
)
from custom_components.unifi_insights.api.network import (
    PolicyBasedRoute,
    UniFiNetworkClient,
    VpnClient,
    parse_outlet_metrics,
)
from custom_components.unifi_insights.api.protect import UniFiProtectClient


def _network_client() -> UniFiNetworkClient:
    """Build a local Network client for tests."""
    return UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
    )


def _protect_client() -> UniFiProtectClient:
    """Build a local Protect client for tests."""
    return UniFiProtectClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
    )


def test_build_legacy_api_path_local() -> None:
    """Test building legacy API paths for local connections."""
    client = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
    )

    assert (
        client.build_legacy_api_path("default", "/stat/device/aa:bb:cc")
        == "/proxy/network/api/s/default/stat/device/aa:bb:cc"
    )


def test_build_legacy_api_path_remote() -> None:
    """Test building legacy API paths for remote connections."""
    client = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        connection_type=ConnectionType.REMOTE,
        console_id="console-id",
    )

    assert (
        client.build_legacy_api_path("default", "stat/device/aa:bb:cc")
        == "/v1/connector/consoles/console-id/network/api/s/default/"
        "stat/device/aa:bb:cc"
    )


def test_build_api_path_remote_requires_console_id() -> None:
    """Test proxied remote API paths require a console ID."""
    client = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        connection_type=ConnectionType.REMOTE,
    )

    with pytest.raises(ValueError, match="console_id"):
        client.build_api_path("/sites")


def test_build_legacy_global_api_path_remote() -> None:
    """Test building global legacy API paths for remote connections."""
    client = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        connection_type=ConnectionType.REMOTE,
        console_id="console-id",
    )

    assert (
        client.build_legacy_global_api_path("/self/sites")
        == "/v1/connector/consoles/console-id/network/api/self/sites"
    )


def test_build_legacy_v2_api_path_local() -> None:
    """Test building legacy v2 API paths for local connections."""
    client = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
    )

    assert (
        client.build_legacy_v2_api_path("default", f"/{ENDPOINT_TRAFFIC_ROUTES}")
        == f"/proxy/network/v2/api/site/default/{ENDPOINT_TRAFFIC_ROUTES}"
    )


def test_build_legacy_v2_api_path_remote() -> None:
    """Test building legacy v2 API paths for remote connections."""
    client = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        connection_type=ConnectionType.REMOTE,
        console_id="console-id",
    )

    expected = (
        f"/v1/connector/consoles/console-id/network/v2/api/site/default/"
        f"{ENDPOINT_TRAFFIC_ROUTES}"
    )
    assert (
        client.build_legacy_v2_api_path("default", ENDPOINT_TRAFFIC_ROUTES) == expected
    )


def test_build_legacy_v2_api_path_empty_site_raises() -> None:
    """Test building legacy v2 API path with empty site raises ValueError."""
    client = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
    )

    with pytest.raises(ValueError, match="site_name is required"):
        client.build_legacy_v2_api_path("", f"/{ENDPOINT_TRAFFIC_ROUTES}")


async def test_get_hosts_remote_without_console_id() -> None:
    """Test remote host discovery works before a console ID is selected."""
    client = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        connection_type=ConnectionType.REMOTE,
        session=MagicMock(),
    )
    hosts = [
        {
            "id": "console-id",
            "type": "console",
            "reportedState": {"hostname": "Dream Router 7"},
        }
    ]
    with patch(
        "custom_components.unifi_insights.api.network.client.UniFiSiteManagerClient"
    ) as site_manager_class:
        site_manager_class.return_value.list_hosts = AsyncMock(return_value=hosts)
        result = await client.get_hosts()
        site_manager_class.return_value.list_hosts.assert_awaited_once()

    assert result == [
        {
            "id": "console-id",
            "type": "console",
            "reportedState": {"hostname": "Dream Router 7"},
        }
    ]
    site_manager_class.assert_called_once()


@pytest.mark.parametrize(
    ("response", "expected"),
    [
        (
            {"data": [{"_id": "legacy-1", "port_table": []}]},
            {"_id": "legacy-1", "port_table": []},
        ),
        (
            {"_id": "legacy-2", "port_table": [{"port_idx": 1}]},
            {"_id": "legacy-2", "port_table": [{"port_idx": 1}]},
        ),
    ],
)
async def test_get_legacy_device_stats_handles_wrapped_and_unwrapped_responses(
    response: dict[str, object],
    expected: dict[str, object],
) -> None:
    """Test raw legacy device stats parsing for wrapped and unwrapped payloads."""
    client = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        connection_type=ConnectionType.REMOTE,
        console_id="console-id",
    )
    client._get = AsyncMock(return_value=response)

    result = await client.devices.get_legacy_device_stats(
        "default", "aa:bb:cc:dd:ee:ff"
    )

    assert result == expected
    client._get.assert_awaited_once_with(
        "/v1/connector/consoles/console-id/network/api/s/default/"
        "stat/device/aa:bb:cc:dd:ee:ff"
    )


async def test_get_legacy_all_sites_returns_raw_site_dicts() -> None:
    """Test raw legacy site list parsing."""
    client = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
    )
    client._get = AsyncMock(
        return_value={"data": [{"name": "default", "desc": "Default"}]}
    )

    result = await client.sites.get_legacy_all()

    assert result == [{"name": "default", "desc": "Default"}]
    client._get.assert_awaited_once_with("/proxy/network/api/self/sites")


@pytest.mark.parametrize(
    ("response", "expected"),
    [
        (
            {
                "connections": [
                    {
                        "network_id": "tun1",
                        "type": "ipsec-vpn",
                        "status": "CONNECTED",
                        "remote_ip": "198.51.100.9",
                        "local_ip": "198.51.100.7",
                        "rx_rate_bps": 0,
                    },
                    {"type": "openvpn-client", "status": "CONNECTED"},
                    "junk",
                ]
            },
            [{"network_id": "tun1", "type": "ipsec-vpn", "status": "CONNECTED"}],
        ),
        ({"connections": []}, []),
    ],
)
async def test_list_vpn_connections_keeps_identity_and_status_only(
    response: Any, expected: list[dict[str, Any]]
) -> None:
    """Test v2 vpn/connections parsing drops addresses and malformed entries."""
    client = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
    )
    client._get = AsyncMock(return_value=response)

    result = await client.vpn_clients.list_vpn_connections("default")

    assert result == expected
    client._get.assert_awaited_once_with(
        "/proxy/network/v2/api/site/default/vpn/connections"
    )


@pytest.mark.parametrize("response", [{"connections": {}}, {"data": []}, [], None])
async def test_list_vpn_connections_raises_on_unexpected_payload(
    response: Any,
) -> None:
    """An unreadable payload raises rather than reading as "none connected"."""
    client = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
    )
    client._get = AsyncMock(return_value=response)

    with pytest.raises(UniFiResponseError):
        await client.vpn_clients.list_vpn_connections("default")


async def test_list_site_to_site_vpns_filters_site_vpn_entries() -> None:
    """Test only site-vpn networkconf entries are returned, without secrets."""
    client = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
    )
    client._get = AsyncMock(
        return_value={
            "meta": {"rc": "ok"},
            "data": [
                {
                    "_id": "tun1",
                    "purpose": "site-vpn",
                    "name": "Office",
                    "vpn_type": "ipsec-vpn",
                    "x_ipsec_pre_shared_key": "secret",
                },
                {"_id": "tun2", "purpose": "site-vpn", "enabled": False},
                {"_id": "cli1", "purpose": "vpn-client", "name": "Example VPN"},
                {"purpose": "site-vpn", "name": "no id"},
            ],
        }
    )

    result = await client.vpn_clients.list_site_to_site_vpns("default")

    assert result == [
        {"id": "tun1", "name": "Office", "vpn_type": "ipsec-vpn", "enabled": True},
        {"id": "tun2", "name": None, "vpn_type": None, "enabled": False},
    ]
    client._get.assert_awaited_once_with(
        "/proxy/network/api/s/default/rest/networkconf"
    )


async def test_sites_get_all_handles_missing_id_payload() -> None:
    """Sites get_all should handle Dream 7 payloads missing id (Issue 80)."""
    client = _network_client()
    client._get = AsyncMock(
        return_value={"data": [{"internalReference": "default", "name": "Default"}]}
    )

    result = await client.sites.get_all()

    assert len(result) == 1
    assert result[0].id == "default"
    assert result[0].internal_reference == "default"
    assert result[0].name == "Default"
    client._get.assert_awaited_once_with(client.build_api_path("/sites"), params=None)


async def test_sites_get_all_skips_malformed_items() -> None:
    """Sites get_all should skip malformed items that fail ValidationError."""
    client = _network_client()
    client._get = AsyncMock(
        return_value={
            "data": [
                {"internalReference": "default", "name": "Default"},
                {"deviceCount": "not-an-int-and-invalid"},
            ]
        }
    )

    result = await client.sites.get_all()

    assert len(result) == 1
    assert result[0].id == "default"


async def test_sites_get_returns_site() -> None:
    """Sites get should return a parsed Site model."""
    client = _network_client()
    client._get = AsyncMock(return_value={"data": {"id": "site-1", "name": "Default"}})

    result = await client.sites.get("site-1")

    assert result.id == "site-1"
    assert result.name == "Default"
    client._get.assert_awaited_once_with(client.build_api_path("/sites/site-1"))


async def test_sites_get_missing_raises_value_error() -> None:
    """Sites get should raise ValueError if site is not found."""
    client = _network_client()
    client._get = AsyncMock(return_value=None)

    with pytest.raises(ValueError, match="not found"):
        await client.sites.get("missing-site")


async def test_get_legacy_site_devices_returns_device_list() -> None:
    """Test raw legacy site device list parsing."""
    client = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
    )
    client._get = AsyncMock(
        return_value={
            "data": [
                {
                    "mac": "aa:bb:cc:dd:ee:ff",
                    "general_temperature": 47.5,
                }
            ]
        }
    )

    result = await client.devices.get_legacy_site_devices("default")

    assert result == [{"mac": "aa:bb:cc:dd:ee:ff", "general_temperature": 47.5}]
    client._get.assert_awaited_once_with("/proxy/network/api/s/default/stat/device")


async def test_get_port_metrics_normalizes_and_derives_total() -> None:
    """Test normalized legacy port metrics with derived total PoE."""
    client = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        connection_type=ConnectionType.REMOTE,
        console_id="console-id",
    )
    client._get = AsyncMock(
        return_value={
            "data": [
                {
                    "port_table": [
                        {
                            "port_idx": 1,
                            "port_poe": True,
                            "poe_power": "1.25",
                            "rx_bytes": 10,
                            "tx_bytes": 20,
                        },
                        {
                            "portIdx": "2",
                            "portPoe": True,
                            "poePower": "2.75",
                            "rxBytes": 30,
                            "txBytes": 40,
                        },
                    ]
                }
            ]
        }
    )

    metrics = await client.devices.get_port_metrics("default", "aa:bb:cc:dd:ee:ff")

    assert metrics.poe_total_w == 4.0
    assert metrics.poe_ports == {1: 1.25, 2: 2.75}
    assert metrics.port_bytes[1].rx_bytes == 10
    assert metrics.port_bytes[1].tx_bytes == 20
    assert metrics.port_bytes[2].rx_bytes == 30
    assert metrics.port_bytes[2].tx_bytes == 40


async def test_get_port_metrics_skips_non_poe_ports() -> None:
    """Test that ports with port_poe=false are excluded from poe_ports."""
    client = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        connection_type=ConnectionType.REMOTE,
        console_id="console-id",
    )
    client._get = AsyncMock(
        return_value={
            "data": [
                {
                    "port_table": [
                        {
                            "port_idx": 1,
                            "port_poe": False,
                            "poe_power": "0.00",
                            "poe_enable": False,
                            "poe_class": "Class 0",
                            "rx_bytes": 100,
                            "tx_bytes": 200,
                        },
                        {
                            "port_idx": 9,
                            "port_poe": False,
                            "poe_power": "0.00",
                            "rx_bytes": 300,
                            "tx_bytes": 400,
                        },
                    ]
                }
            ]
        }
    )

    metrics = await client.devices.get_port_metrics("default", "aa:bb:cc:dd:ee:ff")

    assert metrics.poe_total_w is None
    assert metrics.poe_ports == {}
    # TX/RX bytes should still be collected
    assert metrics.port_bytes[1].rx_bytes == 100
    assert metrics.port_bytes[9].tx_bytes == 400


async def test_get_port_metrics_returns_defaults_for_empty_payload() -> None:
    """Test empty or malformed payloads return default metrics."""
    client = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
    )
    client._get = AsyncMock(return_value={"data": []})

    metrics = await client.devices.get_port_metrics("default", "aa:bb:cc:dd:ee:ff")

    assert metrics.poe_total_w is None
    assert metrics.poe_ports == {}
    assert metrics.port_bytes == {}


async def test_parse_outlet_metrics() -> None:
    """Test parse_outlet_metrics correctly parses outlet table and power totals."""
    raw = {
        "outlet_ac_power_consumption": "125.5",
        "outlet_ac_power_budget": "1800",
        "outlet_table": [
            {
                "index": 1,
                "name": "Outlet 1",
                "relay_state": True,
                "cycle_enabled": True,
                "outlet_caps": 3,
                "outlet_voltage": "120.5",
                "outlet_current": "1.04",
                "outlet_power": "125.5",
                "outlet_power_factor": "0.99",
            },
            {
                "index": 2,
                "name": "Outlet 2",
                "relay_state": False,
                "cycle_enabled": False,
                "outlet_caps": 1,
                "outlet_voltage": None,
                "outlet_current": None,
                "outlet_power": None,
                "outlet_power_factor": None,
            },
        ],
    }
    metrics = parse_outlet_metrics(raw)
    assert metrics.ac_power_consumption == 125.5
    assert metrics.ac_power_budget == 1800.0
    assert len(metrics.outlets) == 2
    assert metrics.outlets[0].index == 1
    assert metrics.outlets[0].name == "Outlet 1"
    assert metrics.outlets[0].relay_state is True
    assert metrics.outlets[0].cycle_enabled is True
    assert metrics.outlets[0].outlet_caps == 3
    assert metrics.outlets[0].outlet_voltage == 120.5
    assert metrics.outlets[0].outlet_current == 1.04
    assert metrics.outlets[0].outlet_power == 125.5
    assert metrics.outlets[0].outlet_power_factor == 0.99

    assert metrics.outlets[1].index == 2
    assert metrics.outlets[1].relay_state is False
    assert metrics.outlets[1].cycle_enabled is False
    assert metrics.outlets[1].outlet_power is None


async def test_parse_outlet_metrics_empty() -> None:
    """Test parse_outlet_metrics returns empty model for empty or non-dict input."""
    assert parse_outlet_metrics({}).outlets == []
    assert parse_outlet_metrics(None).outlets == []  # type: ignore[arg-type]


async def test_get_outlet_metrics() -> None:
    """Test get_outlet_metrics fetches legacy stats and parses outlet metrics."""
    client = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
    )
    client._get = AsyncMock(
        return_value={
            "data": [
                {
                    "outlet_ac_power_consumption": "50.0",
                    "outlet_table": [
                        {
                            "index": 1,
                            "name": "Port A",
                            "relay_state": True,
                            "outlet_power": "50.0",
                        }
                    ],
                }
            ]
        }
    )
    metrics = await client.devices.get_outlet_metrics("default", "00:11:22:33:44:55")
    assert metrics.ac_power_consumption == 50.0
    assert len(metrics.outlets) == 1
    assert metrics.outlets[0].name == "Port A"
    assert metrics.outlets[0].relay_state is True


async def test_set_outlet_state_existing_override() -> None:
    """Test set_outlet_state updates an existing override."""
    client = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
    )
    client._get = AsyncMock()
    client._put = AsyncMock(return_value={"data": []})

    result = await client.devices.set_outlet_state(
        "default",
        "60a1b2c3d4e5f67890123456",
        1,
        state=False,
        cycle_enabled=False,
        current_device={
            "_id": "60a1b2c3d4e5f67890123456",
            "outlet_overrides": [
                {
                    "index": 1,
                    "relay_state": True,
                    "cycle_enabled": True,
                },
                {
                    "index": 2,
                    "relay_state": False,
                },
            ],
        },
    )
    assert result is True

    # The singular rest/device route is write-only on UniFi OS: never GET it.
    client._get.assert_not_awaited()
    client._put.assert_awaited_once_with(
        "/proxy/network/api/s/default/rest/device/60a1b2c3d4e5f67890123456",
        json_data={
            "outlet_overrides": [
                {
                    "index": 1,
                    "relay_state": False,
                    "cycle_enabled": False,
                },
                {
                    "index": 2,
                    "relay_state": False,
                },
            ]
        },
    )


async def test_set_outlet_state_new_override() -> None:
    """Test set_outlet_state appends a new override when none exists for index."""
    client = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
    )
    client._put = AsyncMock(return_value={"data": []})

    result = await client.devices.set_outlet_state(
        "default",
        "60a1b2c3d4e5f67890123456",
        3,
        state=True,
        current_device={
            "_id": "60a1b2c3d4e5f67890123456",
            "outlet_overrides": [
                {"index": 1, "relay_state": True},
                {"index": 2, "relay_state": False},
            ],
        },
    )
    assert result is True
    client._put.assert_awaited_once_with(
        "/proxy/network/api/s/default/rest/device/60a1b2c3d4e5f67890123456",
        json_data={
            "outlet_overrides": [
                {"index": 1, "relay_state": True},
                {"index": 2, "relay_state": False},
                {
                    "index": 3,
                    "relay_state": True,
                },
            ]
        },
    )


async def test_set_outlet_state_seeds_overrides_from_outlet_table() -> None:
    """Test set_outlet_state seeds a full override array from outlet_table.

    A factory-fresh PDU reports an empty outlet_overrides array. Because the
    controller treats that array as the complete desired state, writing only the
    changed outlet would reset every other outlet to its default.
    """
    client = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
    )
    client._put = AsyncMock(return_value={"data": []})

    result = await client.devices.set_outlet_state(
        "default",
        "60a1b2c3d4e5f67890123456",
        2,
        state=False,
        current_device={
            "_id": "60a1b2c3d4e5f67890123456",
            "outlet_overrides": [],
            "outlet_table": [
                {
                    "index": 1,
                    "name": "Router",
                    "relay_state": True,
                    "cycle_enabled": False,
                },
                {
                    "index": 2,
                    "name": "NAS",
                    "relay_state": True,
                    "cycle_enabled": False,
                },
                {
                    "index": 3,
                    "name": "Spare",
                    "relay_state": False,
                    "cycle_enabled": False,
                },
            ],
        },
    )
    assert result is True

    payload = client._put.await_args.kwargs["json_data"]["outlet_overrides"]

    # Every outlet survives the write, not just the one that changed.
    assert [entry["index"] for entry in payload] == [1, 2, 3]

    # Only the target outlet flipped; siblings keep their sensed state.
    by_index = {entry["index"]: entry for entry in payload}
    assert by_index[2]["relay_state"] is False
    assert by_index[1]["relay_state"] is True
    assert by_index[3]["relay_state"] is False
    assert by_index[1]["name"] == "Router"


async def test_set_outlet_state_rejects_unseedable_write() -> None:
    """Test set_outlet_state refuses to write a partial override array.

    Without existing overrides or an outlet_table to seed from, the sibling
    outlet states are unknown. The controller treats outlet_overrides as the
    complete desired state, so a single-entry write would reset every other
    outlet on the device. Refuse the write instead.
    """
    client = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
    )
    client._get = AsyncMock()
    client._put = AsyncMock(return_value={"data": []})

    with pytest.raises(UniFiValidationError):
        await client.devices.set_outlet_state(
            "default",
            "60a1b2c3d4e5f67890123456",
            4,
            state=True,
            current_device={"_id": "60a1b2c3d4e5f67890123456"},
        )

    client._put.assert_not_awaited()
    client._get.assert_not_awaited()


async def test_set_outlet_state_rejects_missing_snapshot() -> None:
    """Test set_outlet_state refuses to write without a device snapshot."""
    client = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
    )
    client._get = AsyncMock()
    client._put = AsyncMock(return_value={"data": []})

    with pytest.raises(UniFiValidationError):
        await client.devices.set_outlet_state(
            "default", "60a1b2c3d4e5f67890123456", 4, state=True
        )

    client._put.assert_not_awaited()
    client._get.assert_not_awaited()


async def test_wifi_update_uses_put_with_existing_payload() -> None:
    """Test WiFi updates fetch current config and send a full PUT payload."""
    client = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
    )
    client._get = AsyncMock(
        return_value={
            "data": {
                "id": "wifi-1",
                "type": "STANDARD",
                "name": "Guest WiFi",
                "metadata": {"origin": "USER_DEFINED"},
                "enabled": False,
                "network": {"id": "network-1", "type": "CORPORATE"},
                "securityConfiguration": {"type": "OPEN"},
                "multicastToUnicastConversionEnabled": False,
                "clientIsolationEnabled": True,
                "hideName": False,
                "uapsdEnabled": True,
                "broadcastingFrequenciesGHz": ["2.4", "5"],
            }
        }
    )
    client._put = AsyncMock(
        return_value={
            "data": {
                "id": "wifi-1",
                "type": "STANDARD",
                "name": "Guest WiFi",
                "enabled": True,
                "network": {"id": "network-1", "type": "CORPORATE"},
                "securityConfiguration": {"type": "OPEN"},
                "multicastToUnicastConversionEnabled": False,
                "clientIsolationEnabled": True,
                "hideName": False,
                "uapsdEnabled": True,
                "broadcastingFrequenciesGHz": ["2.4", "5"],
            }
        }
    )
    client._patch = AsyncMock()

    result = await client.wifi.update("site-1", "wifi-1", enabled=True)

    path = "/proxy/network/integration/v1/sites/site-1/wifi/broadcasts/wifi-1"
    client._get.assert_awaited_once_with(path)
    client._put.assert_awaited_once_with(
        path,
        json_data={
            "type": "STANDARD",
            "name": "Guest WiFi",
            "enabled": True,
            "network": {"id": "network-1", "type": "CORPORATE"},
            "securityConfiguration": {"type": "OPEN"},
            "multicastToUnicastConversionEnabled": False,
            "clientIsolationEnabled": True,
            "hideName": False,
            "uapsdEnabled": True,
            "broadcastingFrequenciesGHz": ["2.4", "5"],
        },
    )
    client._patch.assert_not_awaited()
    assert result.enabled is True


async def test_clients_get_all_paginates_automatically() -> None:
    """Test that get_all fetches all pages when total exceeds page size."""
    client = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
    )

    page1 = {
        "offset": 0,
        "limit": 100,
        "count": 2,
        "totalCount": 3,
        "data": [
            {
                "id": "c1",
                "macAddress": "aa:bb:cc:dd:ee:01",
                "type": "WIRED",
                "name": "Client 1",
            },
            {
                "id": "c2",
                "macAddress": "aa:bb:cc:dd:ee:02",
                "type": "WIRED",
                "name": "Client 2",
            },
        ],
    }
    page2 = {
        "offset": 2,
        "limit": 100,
        "count": 1,
        "totalCount": 3,
        "data": [
            {
                "id": "c3",
                "macAddress": "aa:bb:cc:dd:ee:03",
                "type": "WIRELESS",
                "name": "Client 3",
            },
        ],
    }
    client._get = AsyncMock(side_effect=[page1, page2])

    result = await client.clients.get_all("site-1")

    assert len(result) == 3
    assert result[0].name == "Client 1"
    assert result[2].name == "Client 3"
    assert client._get.await_count == 2


async def test_clients_get_all_single_page() -> None:
    """Test that get_all stops after one page when all clients fit."""
    client = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
    )
    client._get = AsyncMock(
        return_value={
            "offset": 0,
            "limit": 100,
            "count": 2,
            "totalCount": 2,
            "data": [
                {
                    "id": "c1",
                    "macAddress": "aa:bb:cc:dd:ee:01",
                    "type": "WIRED",
                    "name": "Client 1",
                },
                {
                    "id": "c2",
                    "macAddress": "aa:bb:cc:dd:ee:02",
                    "type": "WIRELESS",
                    "name": "Client 2",
                },
            ],
        }
    )

    result = await client.clients.get_all("site-1")

    assert len(result) == 2
    assert client._get.await_count == 1


async def test_clients_get_all_explicit_limit_no_pagination() -> None:
    """Test that explicit offset/limit skips auto-pagination."""
    client = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
    )
    client._get = AsyncMock(
        return_value={
            "offset": 0,
            "limit": 5,
            "count": 5,
            "totalCount": 20,
            "data": [
                {
                    "id": f"c{i}",
                    "macAddress": f"aa:bb:cc:dd:ee:{i:02d}",
                    "type": "WIRED",
                    "name": f"Client {i}",
                }
                for i in range(5)
            ],
        }
    )

    result = await client.clients.get_all("site-1", limit=5)

    assert len(result) == 5
    assert client._get.await_count == 1


async def test_clients_get_all_redacts_sensitive_validation_data(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Validation warning logs should not include client IDs or MAC addresses."""
    client = _network_client()
    sensitive_mac = "aa:bb:cc:dd:ee:ff"
    sensitive_id = "client-123"
    invalid_item = {"id": sensitive_id, "macAddress": sensitive_mac, "type": object()}
    client._get = AsyncMock(
        return_value={
            "offset": 0,
            "limit": 100,
            "count": 1,
            "totalCount": 1,
            "data": [invalid_item],
        }
    )
    caplog.set_level(
        "WARNING",
        logger="custom_components.unifi_insights.api.network.endpoints.clients",
    )

    result = await client.clients.get_all("site-1")

    assert result == []
    assert "Failed to validate client payload (" in caplog.text
    assert sensitive_id not in caplog.text
    assert sensitive_mac not in caplog.text


async def test_clients_get_all_manual_pagination_redacts_sensitive_validation_data(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Manual pagination path should avoid logging sensitive client values."""
    client = _network_client()
    sensitive_mac = "11:22:33:44:55:66"
    sensitive_id = "client-456"
    invalid_item = {"id": sensitive_id, "macAddress": sensitive_mac, "type": object()}
    client._get = AsyncMock(return_value={"data": [invalid_item]})
    caplog.set_level(
        "WARNING",
        logger="custom_components.unifi_insights.api.network.endpoints.clients",
    )

    result = await client.clients.get_all("site-1", limit=1)

    assert result == []
    assert "Failed to validate client payload (" in caplog.text
    assert sensitive_id not in caplog.text
    assert sensitive_mac not in caplog.text


# ---------------------------------------------------------------------------
# Network v10.4.57 - LAGs, MC-LAG domains, switch stacks
# ---------------------------------------------------------------------------


async def test_lags_get_all_paginates_automatically() -> None:
    """LAG get_all should fetch all pages when total exceeds one page."""
    client = _network_client()
    page1 = {
        "offset": 0,
        "limit": 100,
        "count": 1,
        "totalCount": 2,
        "data": [
            {
                "id": "lag-1",
                "type": "LOCAL",
                "members": [{"deviceId": "dev-1", "portIdxs": [1, 2]}],
            }
        ],
    }
    page2 = {
        "offset": 1,
        "limit": 100,
        "count": 1,
        "totalCount": 2,
        "data": [
            {
                "id": "lag-2",
                "type": "SWITCH_STACK",
                "members": [{"deviceId": "dev-2", "portIdxs": [5]}],
                "switchStackId": "stack-9",
            }
        ],
    }
    client._get = AsyncMock(side_effect=[page1, page2])

    result = await client.lags.get_all("site-1")

    assert len(result) == 2
    assert result[0].id == "lag-1"
    assert result[0].type == "LOCAL"
    assert result[0].members[0].device_id == "dev-1"
    assert result[0].members[0].port_idxs == [1, 2]
    assert result[1].switch_stack_id == "stack-9"
    assert client._get.await_count == 2
    client._get.assert_any_await(
        client.build_api_path("/sites/site-1/switching/lags"),
        params={"offset": 0, "limit": 100},
    )


async def test_lags_get_all_explicit_limit_single_page() -> None:
    """Explicit offset/limit should fetch a single page."""
    client = _network_client()
    client._get = AsyncMock(
        return_value={
            "offset": 0,
            "limit": 5,
            "count": 1,
            "totalCount": 20,
            "data": [{"id": "lag-1", "type": "LOCAL"}],
        }
    )

    result = await client.lags.get_all("site-1", offset=0, limit=5)

    assert len(result) == 1
    assert client._get.await_count == 1
    client._get.assert_awaited_once_with(
        client.build_api_path("/sites/site-1/switching/lags"),
        params={"offset": 0, "limit": 5},
    )


async def test_lags_get_returns_model_from_wrapped_response() -> None:
    """LAG get should unwrap a ``data`` envelope."""
    client = _network_client()
    client._get = AsyncMock(
        return_value={"data": {"id": "lag-1", "type": "MULTI_CHASSIS"}}
    )

    result = await client.lags.get("site-1", "lag-1")

    assert result.id == "lag-1"
    assert result.type == "MULTI_CHASSIS"
    client._get.assert_awaited_once_with(
        client.build_api_path("/sites/site-1/switching/lags/lag-1")
    )


async def test_lags_get_returns_model_from_unwrapped_response() -> None:
    """LAG get should accept a bare object response."""
    client = _network_client()
    client._get = AsyncMock(return_value={"id": "lag-2", "type": "LOCAL"})

    result = await client.lags.get("site-1", "lag-2")

    assert result.id == "lag-2"


async def test_lags_get_missing_raises_value_error() -> None:
    """LAG get should raise ValueError when nothing is returned."""
    client = _network_client()
    client._get = AsyncMock(return_value=None)

    with pytest.raises(ValueError, match="not found"):
        await client.lags.get("site-1", "missing")


async def test_mc_lag_domains_get_all() -> None:
    """MC-LAG domain get_all should parse peers and local LAGs."""
    client = _network_client()
    client._get = AsyncMock(
        return_value={
            "offset": 0,
            "limit": 100,
            "count": 1,
            "totalCount": 1,
            "data": [
                {
                    "id": "mclag-1",
                    "name": "Core",
                    "peers": [
                        {"deviceId": "dev-1", "linkPortIdxs": [23], "role": "TOP"},
                        {"deviceId": "dev-2", "linkPortIdxs": [24], "role": "BOTTOM"},
                    ],
                    "lags": [{"id": "lag-1", "members": []}],
                }
            ],
        }
    )

    result = await client.lags.get_mc_lag_domains("site-1")

    assert len(result) == 1
    assert result[0].name == "Core"
    assert result[0].peers[0].role == "TOP"
    assert result[0].peers[1].device_id == "dev-2"
    client._get.assert_awaited_with(
        client.build_api_path("/sites/site-1/switching/mc-lag-domains"),
        params={"offset": 0, "limit": 100},
    )


async def test_stacks_get_all_and_get() -> None:
    """Switch stack get_all and get should parse members and LAGs."""
    client = _network_client()
    client._get = AsyncMock(
        return_value={
            "offset": 0,
            "limit": 100,
            "count": 1,
            "totalCount": 1,
            "data": [
                {
                    "id": "stack-1",
                    "name": "Rack A",
                    "members": [{"deviceId": "dev-1"}, {"deviceId": "dev-2"}],
                    "lags": [{"id": "lag-1", "members": []}],
                }
            ],
        }
    )

    result = await client.stacks.get_all("site-1")

    assert len(result) == 1
    assert result[0].name == "Rack A"
    assert result[0].members[1].device_id == "dev-2"
    client._get.assert_awaited_with(
        client.build_api_path("/sites/site-1/switching/switch-stacks"),
        params={"offset": 0, "limit": 100},
    )

    client._get = AsyncMock(return_value={"data": {"id": "stack-1", "name": "Rack A"}})
    single = await client.stacks.get("site-1", "stack-1")
    assert single.id == "stack-1"
    client._get.assert_awaited_once_with(
        client.build_api_path("/sites/site-1/switching/switch-stacks/stack-1")
    )


# ---------------------------------------------------------------------------
# Protect v7.1.87 - alarm hubs, arm profiles, relays, sirens, speakers, bridges
# ---------------------------------------------------------------------------


async def test_alarm_hubs_get_all_wrapped_and_unwrapped() -> None:
    """Alarm hub get_all should handle wrapped and bare list responses."""
    client = _protect_client()
    client._get = AsyncMock(
        return_value={
            "data": [{"id": "hub-1", "modelKey": "linkStation", "isAlarmHub": True}]
        }
    )

    wrapped = await client.alarm_hubs.get_all()
    assert len(wrapped) == 1
    assert wrapped[0].id == "hub-1"
    assert wrapped[0].is_alarm_hub is True
    client._get.assert_awaited_once_with(client.build_api_path("/alarm-hubs"))

    client._get = AsyncMock(return_value=[{"id": "hub-2", "modelKey": "linkStation"}])
    unwrapped = await client.alarm_hubs.get_all()
    assert len(unwrapped) == 1
    assert unwrapped[0].id == "hub-2"


async def test_alarm_hubs_trigger_output_posts_expected_payload() -> None:
    """Alarm hub trigger_output should POST to the outputs trigger path."""
    client = _protect_client()
    client._post = AsyncMock(return_value=None)

    result = await client.alarm_hubs.trigger_output("hub-1", "out-1", durationMs=5000)

    assert result is True
    client._post.assert_awaited_once_with(
        client.build_api_path("/alarm-hubs/hub-1/outputs/out-1/trigger"),
        json_data={"durationMs": 5000},
    )


async def test_arm_profiles_get_all_and_enable() -> None:
    """Arm profile get_all should parse and enable should POST."""
    client = _protect_client()
    client._get = AsyncMock(
        return_value=[{"id": "profile-1", "name": "Away", "recordEverything": True}]
    )

    profiles = await client.arm_profiles.get_all()
    assert profiles[0].name == "Away"
    assert profiles[0].record_everything is True
    client._get.assert_awaited_once_with(client.build_api_path("/arm-profiles"))

    client._post = AsyncMock(return_value=None)
    assert await client.arm_profiles.enable(armProfileId="profile-1") is True
    client._post.assert_awaited_once_with(
        client.build_api_path("/arm-profiles/enable"),
        json_data={"armProfileId": "profile-1"},
    )


async def test_relays_activate_output_posts_expected_path() -> None:
    """Relay activate_output should POST to the outputs activate path."""
    client = _protect_client()
    client._post = AsyncMock(return_value=None)

    result = await client.relays.activate_output("relay-1", "out-2")

    assert result is True
    client._post.assert_awaited_once_with(
        client.build_api_path("/relays/relay-1/outputs/out-2/activate"),
        json_data=None,
    )


async def test_sirens_play_and_speakers_test_sound() -> None:
    """Siren play and speaker test_sound should POST to their action paths."""
    client = _protect_client()
    client._post = AsyncMock(return_value=None)

    assert await client.sirens.play("siren-1") is True
    client._post.assert_awaited_with(client.build_api_path("/sirens/siren-1/play"))

    assert await client.speakers.test_sound("spk-1") is True
    client._post.assert_awaited_with(
        client.build_api_path("/speakers/spk-1/test-sound")
    )


async def test_bridges_get_all_uses_base_endpoint() -> None:
    """Bridge get_all should parse via the shared device endpoint base."""
    client = _protect_client()
    client._get = AsyncMock(
        return_value=[{"id": "bridge-1", "modelKey": "bridge", "maxClients": 4}]
    )

    result = await client.bridges.get_all()

    assert result[0].id == "bridge-1"
    assert result[0].max_clients == 4
    client._get.assert_awaited_once_with(client.build_api_path("/bridges"))


async def test_link_stations_get_returns_model() -> None:
    """Link station get should return a parsed model from wrapped data."""
    client = _protect_client()
    client._get = AsyncMock(
        return_value={"data": {"id": "ls-1", "modelKey": "linkStation"}}
    )

    result = await client.link_stations.get("ls-1")

    assert result.id == "ls-1"
    client._get.assert_awaited_once_with(client.build_api_path("/link-stations/ls-1"))


async def test_devices_get_all_skips_malformed_items() -> None:
    """Devices get_all should skip invalid/malformed items without failing."""
    client = _network_client()
    client._get = AsyncMock(
        return_value={
            "data": [
                {"id": "dev-1", "name": "Valid AP", "features": ["accessPoint"]},
                "not-a-dict",
                {"name": "Missing ID"},
            ]
        }
    )

    result = await client.devices.get_all("site-1")

    assert len(result) == 1
    assert result[0].id == "dev-1"
    assert result[0].features == ["accessPoint"]


async def test_devices_get_pending_adoption_skips_malformed_items() -> None:
    """Devices get_pending_adoption should skip invalid items."""
    client = _network_client()
    client._get = AsyncMock(
        return_value={
            "data": [
                {"id": "pend-1", "name": "Pending Device"},
                123,
                {"name": "No ID"},
            ]
        }
    )

    result = await client.devices.get_pending_adoption()

    assert len(result) == 1
    assert result[0].id == "pend-1"


def _make_response(
    *,
    status: int = 200,
    text: str = "",
    json_side_effect=None,
    method: str = "GET",
    path: str = "/proxy/network/integration/v1/sites",
):
    """Build a fake aiohttp.ClientResponse for _handle_response tests."""
    response = MagicMock()
    response.status = status
    response.text = AsyncMock(return_value=text)
    response.headers = {}
    response.method = method
    response.url = MagicMock()
    response.url.path = path
    if json_side_effect is not None:
        response.json = AsyncMock(side_effect=json_side_effect)
    else:
        response.json = AsyncMock(return_value={})
    return response


async def test_handle_response_2xx_non_json_raises() -> None:
    """A 2xx status with a non-JSON body must raise, not be treated as success.

    Regression test: a UniFi console/proxy that considers the request
    unauthenticated can return a 2xx status with an HTML login page body.
    Silently returning None here (the old behavior) meant no exception ever
    reached the coordinator, so entities kept serving stale data for 47h in
    production instead of surfacing as unavailable.
    """
    client = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
    )
    response = _make_response(
        status=200,
        text="<!doctype html><html><body>login</body></html>",
        json_side_effect=aiohttp.ContentTypeError(MagicMock(), MagicMock()),
    )

    with pytest.raises(UniFiResponseError) as exc_info:
        await client._handle_response(response)

    assert exc_info.value.status_code == 200


async def test_handle_response_non_json_warning_names_request_path(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The non-JSON warning must name the endpoint that failed.

    Without the request path this warning identifies only the response body,
    so a console returning an HTML page on one of several polled config
    endpoints cannot be attributed to the call that actually failed. That is
    exactly why a sustained burst of this warning in production could not be
    pinned to a culprit endpoint.
    """
    client = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
    )
    path = "/proxy/network/v2/api/site/default/trafficroutes"
    response = _make_response(
        status=200,
        text="<!doctype html><html><body>login</body></html>",
        json_side_effect=aiohttp.ContentTypeError(MagicMock(), MagicMock()),
        method="GET",
        path=path,
    )

    with caplog.at_level(logging.WARNING), pytest.raises(UniFiResponseError):
        await client._handle_response(response)

    message = next(
        record.getMessage()
        for record in caplog.records
        if "Response is not JSON" in record.getMessage()
    )
    assert "GET" in message
    assert path in message


async def test_handle_response_non_json_warning_omits_query_string(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The warning must log url.path, never the full URL.

    A UniFi request URL can carry credentials in its query string. Logging
    `response.url` instead of `response.url.path` would leak them into the
    HA log and into any diagnostics upload, so this pins the safe form.
    """
    client = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
    )
    path = "/proxy/network/integration/v1/sites"
    response = _make_response(
        status=200,
        text="<!doctype html><html><body>login</body></html>",
        json_side_effect=aiohttp.ContentTypeError(MagicMock(), MagicMock()),
        path=path,
    )
    response.url.__str__.return_value = f"https://192.168.1.1{path}?apiKey=SUPER-SECRET"

    with caplog.at_level(logging.WARNING), pytest.raises(UniFiResponseError):
        await client._handle_response(response)

    message = next(
        record.getMessage()
        for record in caplog.records
        if "Response is not JSON" in record.getMessage()
    )
    assert "SUPER-SECRET" not in message
    assert "apiKey" not in message
    assert path in message


async def test_handle_response_empty_body_returns_none() -> None:
    """An empty 2xx body (e.g. a 204-style response) is still a valid no-op."""
    client = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
    )
    response = _make_response(status=200, text="")

    result = await client._handle_response(response)

    assert result is None


async def test_handle_response_valid_json_returns_data() -> None:
    """A normal JSON response still parses and returns as before."""
    client = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
    )
    response = _make_response(status=200, text='{"ok": true}')
    response.json = AsyncMock(return_value={"ok": True})

    result = await client._handle_response(response)

    assert result == {"ok": True}


def test_policy_based_route_model() -> None:
    """Test PolicyBasedRoute model validation and display name."""
    # Test with _id alias
    route: PolicyBasedRoute = PolicyBasedRoute.model_validate(
        {
            "_id": "route123",
            "description": "Route via VPN",
            "enabled": True,
            "matchingTarget": "DOMAIN",
            "interface": "vpn",
            "vpnClientId": "vpn123",
            "killSwitch": True,
            "domains": ["example.com"],
            "ipAddresses": ["1.1.1.1"],
            "clientMacs": ["aa:bb:cc:dd:ee:ff"],
            "networkIds": ["net123"],
        }
    )
    assert route.id == "route123"
    assert route.description == "Route via VPN"
    assert route.enabled is True
    assert route.matching_target == "DOMAIN"
    assert route.interface == "vpn"
    assert route.vpn_client_id == "vpn123"
    assert route.kill_switch is True
    assert route.domains == ["example.com"]
    assert route.ip_addresses == ["1.1.1.1"]
    assert route.client_macs == ["aa:bb:cc:dd:ee:ff"]
    assert route.network_ids == ["net123"]
    assert route.display_name == "Route via VPN"

    # Test display name fallbacks
    route2: PolicyBasedRoute = PolicyBasedRoute.model_validate(
        {"_id": "r2", "name": "Named Route"}
    )
    assert route2.display_name == "Named Route"

    route3: PolicyBasedRoute = PolicyBasedRoute.model_validate(
        {"_id": "r3", "matchingTarget": "INTERNET", "interface": "WAN2"}
    )
    assert route3.display_name == "Route INTERNET to WAN2"

    route4: PolicyBasedRoute = PolicyBasedRoute.model_validate({"_id": "r4"})
    assert route4.display_name == "Route r4"


# Live payloads captured from a UniFi Dream Machine SE (UniFi OS 5.1.31,
# Network 10.6.101) via GET /proxy/network/v2/api/site/default/trafficroutes.
# The controller returns a bare JSON array, and route fields differ from what
# the maintainer's model previously assumed (see routes.py for details).
LIVE_ROUTE_INTERNET: dict[str, Any] = {
    "_id": "67678b976c1d8157c66f44a2",
    "description": "Nord Route",
    "domains": [],
    "enabled": True,
    "ip_addresses": [],
    "ip_ranges": [],
    "kill_switch_enabled": True,
    "matching_target": "INTERNET",
    "network_id": "67678a746c1d8157c66f444e",
    "next_hop": "",
    "regions": [],
    "target_devices": [{"network_id": "67678b326c1d8157c66f4466", "type": "NETWORK"}],
}

LIVE_ROUTE_DOMAIN: dict[str, Any] = {
    "_id": "6a96d1fb745ac3cf4de10e79",
    "description": "HA PBR Test",
    "domains": [{"domain": "pbr-test.example.com", "port_ranges": [], "ports": []}],
    "enabled": True,
    "ip_addresses": [],
    "ip_ranges": [],
    "kill_switch_enabled": True,
    "matching_target": "DOMAIN",
    "network_id": "67678a746c1d8157c66f444e",
    "next_hop": "",
    "regions": [],
    "target_devices": [{"network_id": "67678b326c1d8157c66f4466", "type": "NETWORK"}],
}


def test_policy_based_route_model_parses_live_internet_route() -> None:
    """Test the live INTERNET-target route payload validates cleanly."""
    route = PolicyBasedRoute.model_validate(LIVE_ROUTE_INTERNET)
    assert route.id == "67678b976c1d8157c66f44a2"
    assert route.kill_switch_enabled is True
    assert route.network_id == "67678a746c1d8157c66f444e"
    assert route.next_hop == ""
    assert route.regions == []
    assert route.ip_ranges == []
    assert route.target_devices[0].type == "NETWORK"
    assert route.target_devices[0].network_id == "67678b326c1d8157c66f4466"


def test_policy_based_route_model_parses_live_domain_route() -> None:
    """Test the live DOMAIN-target route payload validates cleanly.

    This is the payload that previously raised
    ``ValidationError: domains.0 Input should be a valid string`` because
    ``domains`` was typed as ``list[str]`` while the controller sends a list
    of domain objects.
    """
    route = PolicyBasedRoute.model_validate(LIVE_ROUTE_DOMAIN)
    assert route.kill_switch_enabled is True
    assert route.domains[0]["domain"] == "pbr-test.example.com"
    assert route.target_devices[0].type == "NETWORK"
    assert route.target_devices[0].network_id == "67678b326c1d8157c66f4466"


async def test_routes_endpoint_list_routes_returns_both_live_routes() -> None:
    """Test list_routes over the real bare-array response returns both routes.

    Before the model fix, the DOMAIN route failed pydantic validation and
    was silently skipped by list_routes' per-item try/except, so this
    returned 1 route instead of 2.
    """
    client: UniFiNetworkClient = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
    )
    client._get = AsyncMock(
        return_value=[LIVE_ROUTE_INTERNET, LIVE_ROUTE_DOMAIN],
    )

    routes: list[PolicyBasedRoute] = await client.routes.list_routes("default")
    assert len(routes) == 2
    assert {r.id for r in routes} == {
        "67678b976c1d8157c66f44a2",
        "6a96d1fb745ac3cf4de10e79",
    }


async def test_routes_endpoint_list_routes() -> None:
    """Test listing policy-based routes."""
    client: UniFiNetworkClient = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
    )
    client._get = AsyncMock(
        return_value=[
            {"_id": "route1", "description": "Route 1", "enabled": True},
            {"_id": "route2", "description": "Route 2", "enabled": False},
        ]
    )

    routes: list[PolicyBasedRoute] = await client.routes.list_routes("default")
    assert len(routes) == 2
    assert routes[0].id == "route1"
    assert routes[0].enabled is True
    assert routes[1].id == "route2"
    assert routes[1].enabled is False
    client._get.assert_awaited_once_with(
        "/proxy/network/v2/api/site/default/trafficroutes"
    )


async def test_routes_endpoint_list_routes_wrapped_and_empty() -> None:
    """Test listing policy-based routes with wrapped dict and empty response."""
    client = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
    )

    # Wrapped dict with data key
    client._get = AsyncMock(
        return_value={"data": [{"_id": "route1", "description": "Route 1"}]}
    )
    routes = await client.routes.list_routes("default")
    assert len(routes) == 1
    assert routes[0].id == "route1"

    # None / empty response
    client._get = AsyncMock(return_value=None)
    routes = await client.routes.list_routes("default")
    assert routes == []


async def test_routes_endpoint_get_route() -> None:
    """Test getting a specific policy-based route."""
    client = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
    )

    # Found via direct GET
    client._get = AsyncMock(
        return_value={"_id": "route1", "description": "Route 1", "enabled": True}
    )
    route = await client.routes.get_route("default", "route1")
    assert route.id == "route1"
    assert route.enabled is True

    # Fallback to searching list_routes when direct GET returns empty
    client._get = AsyncMock(
        side_effect=[
            [],  # direct GET /trafficroutes/route2 returns empty
            [
                {"_id": "route2", "description": "Route 2", "enabled": False}
            ],  # list_routes returns it
        ]
    )
    route2 = await client.routes.get_route("default", "route2")
    assert route2.id == "route2"


async def test_routes_endpoint_get_route_not_found_raises() -> None:
    """Test getting a missing policy-based route raises ValueError."""
    client = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
    )
    client._get = AsyncMock(return_value=[])
    with pytest.raises(ValueError, match="Policy-Based Route missing not found"):
        await client.routes.get_route("default", "missing")


async def test_routes_endpoint_update_route() -> None:
    """Test updating a policy-based route via PUT."""
    client = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
    )
    client._get = AsyncMock(
        return_value=[{"_id": "route1", "description": "Route 1", "enabled": True}]
    )
    client._put = AsyncMock(
        return_value=[{"_id": "route1", "description": "Route 1", "enabled": False}]
    )

    updated = await client.routes.update_route("default", "route1", enabled=False)
    assert updated.id == "route1"
    assert updated.enabled is False

    client._put.assert_awaited_once_with(
        "/proxy/network/v2/api/site/default/trafficroutes/route1",
        json_data={"_id": "route1", "description": "Route 1", "enabled": False},
    )


async def test_routes_endpoint_update_route_not_found_raises() -> None:
    """Test updating a non-existent policy-based route raises ValueError."""
    client = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
    )
    client._get = AsyncMock(return_value=[])

    with pytest.raises(ValueError, match="Policy-Based Route missing not found"):
        await client.routes.update_route("default", "missing", enabled=False)


async def test_routes_endpoint_soft_error_raises() -> None:
    """Test that meta.rc == 'error' envelope raises UniFiResponseError."""
    client = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
    )
    client._get = AsyncMock(
        return_value={"meta": {"rc": "error", "msg": "API error message"}}
    )

    with pytest.raises(UniFiResponseError) as exc_info:
        await client.routes.list_routes("default")
    assert exc_info.value.message == "API error message"
    assert exc_info.value.status_code == 200


def test_vpn_client_model() -> None:
    """Test VpnClient model validation and fields."""
    client: VpnClient = VpnClient.model_validate(
        {
            "_id": "vpn1",
            "name": "Privado VPN",
            "purpose": "vpn-client",
            "vpn_type": "openvpn-client",
            "enabled": True,
            "ip_subnet": "172.21.25.217/32",
            "openvpn_id": 1,
            "remote_host": "syd-012.vpn.privado.io",
        }
    )
    assert client.id == "vpn1"
    assert client.name == "Privado VPN"
    assert client.purpose == "vpn-client"
    assert client.vpn_type == "openvpn-client"
    assert client.enabled is True
    assert client.ip_subnet == "172.21.25.217/32"
    assert client.openvpn_id == 1
    assert client.remote_host == "syd-012.vpn.privado.io"


async def test_vpn_clients_endpoint_list_vpn_clients() -> None:
    """Test listing VPN client configurations."""
    client: UniFiNetworkClient = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
    )
    client._get = AsyncMock(
        return_value={
            "meta": {"rc": "ok"},
            "data": [
                {
                    "_id": "vpn1",
                    "name": "Privado VPN",
                    "purpose": "vpn-client",
                    "vpn_type": "openvpn-client",
                    "enabled": True,
                },
                {
                    "_id": "lan1",
                    "name": "LAN",
                    "purpose": "corporate",
                    "enabled": True,
                },
            ],
        }
    )

    clients: list[VpnClient] = await client.vpn_clients.list_vpn_clients("default")
    assert len(clients) == 1
    assert clients[0].id == "vpn1"
    assert clients[0].name == "Privado VPN"
    assert clients[0].enabled is True
    client._get.assert_awaited_once_with(
        "/proxy/network/api/s/default/rest/networkconf"
    )


async def test_vpn_clients_endpoint_list_vpn_clients_unwrapped_and_empty() -> None:
    """Test listing VPN client configurations with bare list and None responses."""
    client: UniFiNetworkClient = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
    )

    # Bare list
    client._get = AsyncMock(
        return_value=[
            {
                "_id": "vpn1",
                "name": "Privado VPN",
                "purpose": "vpn-client",
                "vpn_type": "openvpn-client",
                "enabled": True,
            }
        ]
    )
    clients: list[VpnClient] = await client.vpn_clients.list_vpn_clients("default")
    assert len(clients) == 1
    assert clients[0].id == "vpn1"

    # None / empty response
    client._get = AsyncMock(return_value=None)
    clients = await client.vpn_clients.list_vpn_clients("default")
    assert clients == []


async def test_vpn_clients_endpoint_list_vpn_clients_error_envelope_raises() -> None:
    """Test listing VPN client configurations when response contains error envelope."""
    client: UniFiNetworkClient = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
    )
    client._get = AsyncMock(
        return_value={
            "meta": {"rc": "error", "msg": "API error"},
            "data": [],
        }
    )
    with pytest.raises(UniFiResponseError) as exc_info:
        await client.vpn_clients.list_vpn_clients("default")
    assert exc_info.value.message == "API error"
    assert exc_info.value.status_code == 200


async def test_vpn_clients_endpoint_get_vpn_client() -> None:
    """Test getting a specific VPN client configuration."""
    client: UniFiNetworkClient = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
    )
    client._get = AsyncMock(
        return_value={
            "meta": {"rc": "ok"},
            "data": [
                {
                    "_id": "vpn1",
                    "name": "Privado VPN",
                    "purpose": "vpn-client",
                    "enabled": True,
                }
            ],
        }
    )

    vpn_client: VpnClient = await client.vpn_clients.get_vpn_client("default", "vpn1")
    assert vpn_client.id == "vpn1"
    assert vpn_client.name == "Privado VPN"


async def test_vpn_clients_endpoint_get_vpn_client_not_found_raises() -> None:
    """Test getting a missing VPN client raises ValueError."""
    client: UniFiNetworkClient = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
    )
    client._get = AsyncMock(return_value={"meta": {"rc": "ok"}, "data": []})
    with pytest.raises(ValueError, match="VPN Client missing not found"):
        await client.vpn_clients.get_vpn_client("default", "missing")


async def test_vpn_clients_endpoint_update_vpn_client() -> None:
    """Test updating a VPN client configuration via PUT."""
    client: UniFiNetworkClient = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
    )
    client._get = AsyncMock(
        return_value={
            "meta": {"rc": "ok"},
            "data": [
                {
                    "_id": "vpn1",
                    "name": "Privado VPN",
                    "purpose": "vpn-client",
                    "enabled": True,
                }
            ],
        }
    )
    client._put = AsyncMock(
        return_value={
            "meta": {"rc": "ok"},
            "data": [
                {
                    "_id": "vpn1",
                    "name": "Privado VPN",
                    "purpose": "vpn-client",
                    "enabled": False,
                }
            ],
        }
    )

    updated: VpnClient = await client.vpn_clients.update_vpn_client(
        "default", "vpn1", enabled=False
    )
    assert updated.id == "vpn1"
    assert updated.enabled is False
    client._put.assert_awaited_once_with(
        "/proxy/network/api/s/default/rest/networkconf/vpn1",
        json_data={
            "_id": "vpn1",
            "name": "Privado VPN",
            "purpose": "vpn-client",
            "enabled": False,
        },
    )


async def test_vpn_clients_endpoint_update_not_found_raises() -> None:
    """Test updating a missing VPN client raises ValueError."""
    client: UniFiNetworkClient = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
    )
    client._get = AsyncMock(return_value={"meta": {"rc": "ok"}, "data": []})

    with pytest.raises(ValueError, match="VPN Client missing not found"):
        await client.vpn_clients.update_vpn_client("default", "missing", enabled=False)


async def test_cameras_get_all_reports_incomplete_when_item_skipped() -> None:
    """Camera get_all should flag a result it silently dropped an item from.

    Skipping the unparseable item keeps every other camera visible, but the
    coordinator would otherwise read the short list as authoritative, treat
    the dropped camera as unadopted and evict it from the device registry.
    """
    client = _protect_client()
    client._get = AsyncMock(
        return_value={
            "data": [
                {"id": "cam-1", "mac": "AABBCCDDEE01"},
                {"id": "cam-2"},  # missing the required mac
            ]
        }
    )

    result = await client.cameras.get_all()

    assert [camera.id for camera in result] == ["cam-1"]
    assert client.cameras.last_result_complete is False


async def test_cameras_get_all_reports_complete_once_items_parse_again() -> None:
    """Camera get_all should clear the incomplete flag on a clean response."""
    client = _protect_client()
    client._get = AsyncMock(return_value={"data": [{"id": "cam-2"}]})
    await client.cameras.get_all()
    assert client.cameras.last_result_complete is False

    client._get = AsyncMock(
        return_value={
            "data": [
                {"id": "cam-1", "mac": "AABBCCDDEE01"},
                {"id": "cam-2", "mac": "AABBCCDDEE02"},
            ]
        }
    )

    result = await client.cameras.get_all()

    assert len(result) == 2
    assert client.cameras.last_result_complete is True


async def test_protect_device_endpoint_get_all_reports_incomplete_when_item_skipped() -> (
    None
):
    """The shared Protect endpoint base should flag incomplete results too."""
    client = _protect_client()
    client._get = AsyncMock(
        return_value={
            "data": [
                {"id": "hub-1", "modelKey": "linkStation"},
                "not-a-hub",
            ]
        }
    )

    result = await client.alarm_hubs.get_all()

    assert [hub.id for hub in result] == ["hub-1"]
    assert client.alarm_hubs.last_result_complete is False


async def test_cameras_get_all_reports_complete_for_response_with_nothing_to_parse() -> (
    None
):
    """Camera get_all should not let an empty response inherit a stale verdict.

    The flag distinguishes "no cameras there" from "every camera failed to
    parse", so it has to describe the call that just ran, not an earlier one.
    """
    client = _protect_client()
    client._get = AsyncMock(return_value={"data": [{"id": "cam-2"}]})
    await client.cameras.get_all()
    assert client.cameras.last_result_complete is False

    client._get = AsyncMock(return_value=None)

    assert await client.cameras.get_all() == []
    assert client.cameras.last_result_complete is True


class _FakeClock:
    """Monotonic clock that only moves when the code under test sleeps."""

    def __init__(self) -> None:
        self.now = 1000.0
        self.sleeps: list[float] = []

    def monotonic(self) -> float:
        return self.now

    async def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


@pytest.fixture
def fake_clock(monkeypatch: pytest.MonkeyPatch) -> _FakeClock:
    """Drive the rate limiter from a fake clock instead of real time."""
    clock = _FakeClock()
    monkeypatch.setattr(api_base.time, "monotonic", clock.monotonic)
    monkeypatch.setattr(api_base.asyncio, "sleep", clock.sleep)
    return clock


def test_protect_client_is_rate_limited_and_network_client_is_not() -> None:
    """Only the Protect client paces itself.

    The local Protect Integration API allows 10 requests per 1-second window
    per API key; the Network Integration API sends no rate-limit headers and
    does not draw from the Protect allowance.
    """
    protect = _protect_client()
    assert protect._rate_limiter is not None
    assert protect._rate_limiter._max_requests == PROTECT_RATE_LIMIT_REQUESTS
    assert protect._rate_limiter._window == pytest.approx(
        PROTECT_RATE_LIMIT_WINDOW + RATE_LIMIT_WINDOW_MARGIN
    )
    assert _network_client()._rate_limiter is None


async def test_rate_limiter_admits_a_full_window_then_waits(
    fake_clock: _FakeClock,
) -> None:
    """The limiter lets `max_requests` through at once and holds the next.

    Regression test: the Protect coordinator used to fire its seven fetches
    within ~100 ms, and together with camera snapshot pulls on the same API
    key that exceeded the 10-per-second limit and 429'd every poll.
    """
    limiter = RequestRateLimiter(max_requests=3, window=1.0)

    for _ in range(3):
        await limiter.acquire()
    assert fake_clock.sleeps == []

    await limiter.acquire()
    assert fake_clock.sleeps == [pytest.approx(1.0)]


async def test_rate_limiter_window_rolls(fake_clock: _FakeClock) -> None:
    """A slot frees up once its request start leaves the rolling window."""
    limiter = RequestRateLimiter(max_requests=2, window=1.0)

    await limiter.acquire()
    fake_clock.now += 0.6
    await limiter.acquire()
    await limiter.acquire()  # must wait for the first start to expire

    assert fake_clock.sleeps == [pytest.approx(0.4)]


async def test_rate_limiter_defer_holds_requests(fake_clock: _FakeClock) -> None:
    """After a 429 every request waits out the server's Retry-After."""
    limiter = RequestRateLimiter(max_requests=10, window=1.0)

    limiter.defer(2)
    await limiter.acquire()

    assert fake_clock.sleeps == [pytest.approx(2.0)]


@pytest.mark.parametrize(
    ("headers", "expected"),
    [
        ({"Retry-After": "1"}, 1),
        ({}, DEFAULT_RATE_LIMIT_RETRY_AFTER),
        ({"Retry-After": "Wed, 21 Oct 2015 07:28:00 GMT"}, 0),
        ({"Retry-After": "invalid"}, DEFAULT_RATE_LIMIT_RETRY_AFTER),
    ],
)
def test_parse_retry_after(headers: dict[str, str], expected: int) -> None:
    """Retry-After parses seconds or HTTP dates; invalid headers fall back to default.

    An HTTP-date Retry-After (allowed by RFC 9110) used to raise ValueError
    out of the response handler instead of a UniFiRateLimitError.
    """
    assert parse_retry_after(headers) == expected


def _rate_limit_error(retry_after: int) -> UniFiRateLimitError:
    return UniFiRateLimitError(
        "Rate limited by API", status_code=429, retry_after=retry_after
    )


def _response_context(
    status: int, headers: dict[str, str], body: Any = None
) -> MagicMock:
    """An `async with session.request(...)` context yielding one response."""
    response = MagicMock()
    response.status = status
    response.headers = headers
    response.text = AsyncMock(
        return_value="Too many requests" if status == 429 else "response body"
    )
    response.json = AsyncMock(return_value=body)
    response.read = AsyncMock(return_value=b"jpeg")
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=response)
    context.__aexit__ = AsyncMock(return_value=None)
    return context


def _recording_session(
    fake_clock: _FakeClock, contexts: list[MagicMock], method: str
) -> tuple[MagicMock, list[float]]:
    """A session whose `method` hands out `contexts` in turn, noting send times."""
    send_times: list[float] = []

    def send(*args: Any, **kwargs: Any) -> MagicMock:
        send_times.append(fake_clock.now)
        return contexts.pop(0)

    session = MagicMock()
    session.closed = False
    setattr(session, method, MagicMock(side_effect=send))
    return session, send_times


async def test_request_retries_once_after_short_retry_after(
    fake_clock: _FakeClock,
) -> None:
    """A 429 with a short Retry-After is waited out and retried once.

    Both attempts go through the limiter, so the retry is only sent once the
    Retry-After has passed.
    """
    client = _protect_client()
    session, send_times = _recording_session(
        fake_clock,
        [
            _response_context(429, {"Retry-After": "1"}),
            _response_context(200, {}, {"ok": True}),
        ],
        "request",
    )
    client._session = session
    start = fake_clock.now

    assert await client._get("/cameras") == {"ok": True}
    assert session.request.call_count == 2
    assert send_times == [start, pytest.approx(start + 1)]


async def test_request_raises_when_retry_also_rate_limited(
    fake_clock: _FakeClock,
) -> None:
    """Only one retry: a second 429 reaches the caller, and defers the client.

    Without the second defer, other queued requests would start against the
    allowance the server has just rejected again.
    """
    client = _protect_client()
    session, send_times = _recording_session(
        fake_clock,
        [
            _response_context(429, {"Retry-After": "1"}),
            _response_context(429, {"Retry-After": "1"}),
        ],
        "request",
    )
    client._session = session
    start = fake_clock.now

    with pytest.raises(UniFiRateLimitError):
        await client._get("/cameras")
    assert session.request.call_count == 2
    assert send_times == [start, pytest.approx(start + 1)]
    assert client._rate_limiter is not None
    assert client._rate_limiter._blocked_until == pytest.approx(start + 2)


async def test_request_does_not_retry_long_retry_after(
    fake_clock: _FakeClock,
) -> None:
    """A long (or defaulted) Retry-After is raised, never slept through."""
    client = _protect_client()
    client._request_once = AsyncMock(  # type: ignore[method-assign]
        side_effect=_rate_limit_error(RATE_LIMIT_MAX_RETRY_AFTER + 1)
    )

    with pytest.raises(UniFiRateLimitError):
        await client._get("/cameras")
    assert client._request_once.await_count == 1
    assert fake_clock.sleeps == []
    # The client still backs off, capped so a long wait cannot freeze it.
    assert client._rate_limiter is not None
    assert client._rate_limiter._blocked_until == pytest.approx(
        fake_clock.now + RATE_LIMIT_MAX_RETRY_AFTER
    )


async def test_unlimited_client_does_not_retry_429() -> None:
    """Clients without a known rate limit keep the old raise-through behavior."""
    client = _network_client()
    client._request_once = AsyncMock(  # type: ignore[method-assign]
        side_effect=_rate_limit_error(1)
    )

    with pytest.raises(UniFiRateLimitError):
        await client._get("/sites")
    assert client._request_once.await_count == 1


async def test_request_once_waits_for_rate_limiter(fake_clock: _FakeClock) -> None:
    """Every HTTP request goes through the limiter before it is sent."""
    client = _protect_client()
    session = MagicMock()
    session.closed = False
    session.request = MagicMock(side_effect=aiohttp.ClientError("boom"))
    client._session = session
    assert client._rate_limiter is not None
    client._rate_limiter.defer(1)

    with pytest.raises(UniFiConnectionError):
        await client._request_once("GET", "/cameras")

    assert fake_clock.sleeps == [pytest.approx(1.0)]
    session.request.assert_called_once()


def _binary_session(status: int, headers: dict[str, str]) -> MagicMock:
    session = MagicMock()
    session.closed = False
    session.get = MagicMock(
        side_effect=lambda *args, **kwargs: _response_context(status, headers)
    )
    return session


async def test_binary_429_is_retried_once(fake_clock: _FakeClock) -> None:
    """A rate-limited snapshot waits out a short Retry-After and is retried."""
    client = _protect_client()
    session, send_times = _recording_session(
        fake_clock,
        [
            _response_context(429, {"Retry-After": "1"}),
            _response_context(200, {}),
        ],
        "get",
    )
    client._session = session
    start = fake_clock.now

    assert await client._get_binary("/cameras/abc/snapshot") == b"jpeg"
    assert session.get.call_count == 2
    assert send_times == [start, pytest.approx(start + 1)]


async def test_binary_429_on_retry_defers_whole_client(
    fake_clock: _FakeClock,
) -> None:
    """A snapshot rate limited twice fails, and makes every request back off.

    Snapshots draw from the same per-key allowance as the JSON calls, so the
    back-off must apply to the whole client, not just the snapshot.
    """
    client = _protect_client()
    client._session = _binary_session(429, {"Retry-After": "1"})
    start = fake_clock.now

    with pytest.raises(UniFiConnectionError):
        await client._get_binary("/cameras/abc/snapshot")

    assert client._session.get.call_count == 2
    assert client._rate_limiter is not None
    assert client._rate_limiter._blocked_until == pytest.approx(start + 2)


async def test_binary_429_without_retry_after_defers_capped(
    fake_clock: _FakeClock,
) -> None:
    """A missing Retry-After is not retried and must not freeze the client.

    It defaults to 60 s, far past the retry cap, so the snapshot fails at
    once and the client backs off only for the capped wait.
    """
    client = _protect_client()
    client._session = _binary_session(429, {})

    with pytest.raises(UniFiConnectionError):
        await client._get_binary("/cameras/abc/snapshot")

    assert client._session.get.call_count == 1
    assert client._rate_limiter is not None
    assert client._rate_limiter._blocked_until == pytest.approx(
        fake_clock.now + RATE_LIMIT_MAX_RETRY_AFTER
    )


async def test_binary_request_is_throttled(fake_clock: _FakeClock) -> None:
    """Snapshot pulls wait for the limiter like every other request."""
    client = _protect_client()
    client._session = _binary_session(200, {})
    assert client._rate_limiter is not None
    client._rate_limiter.defer(1)

    assert await client._get_binary("/cameras/abc/snapshot") == b"jpeg"
    assert fake_clock.sleeps == [pytest.approx(1.0)]


class TestUniFiInnerSpaceClient:
    """Tests for UniFiInnerSpaceClient local/remote paths and endpoints."""

    def test_init_validation_and_paths(self) -> None:
        """Test LOCAL and REMOTE client initialization and path building."""
        with pytest.raises(ValueError, match="base_url is required"):
            UniFiInnerSpaceClient(
                auth=LocalAuth(api_key="k", verify_ssl=False),
                connection_type=ConnectionType.LOCAL,
            )

        with pytest.raises(ValueError, match="console_id is required"):
            UniFiInnerSpaceClient(
                auth=ApiKeyAuth(api_key="k"),
                connection_type=ConnectionType.REMOTE,
            )

        local_client = UniFiInnerSpaceClient(
            auth=LocalAuth(api_key="k", verify_ssl=False),
            base_url="https://192.168.1.1",
            connection_type=ConnectionType.LOCAL,
        )
        assert local_client.connection_type == ConnectionType.LOCAL
        assert local_client.console_id is None
        assert (
            local_client._build_api_path("project")
            == "/proxy/innerspace/integration/v1/project"
        )

        remote_client = UniFiInnerSpaceClient(
            auth=ApiKeyAuth(api_key="k"),
            connection_type=ConnectionType.REMOTE,
            console_id="console-123",
        )
        assert remote_client.connection_type == ConnectionType.REMOTE
        assert remote_client.console_id == "console-123"
        expected_remote = (
            "/v1/connector/consoles/console-123/innerspace/integration/v1/floor_plans"
        )
        assert remote_client._build_api_path("/floor_plans") == expected_remote

    @pytest.mark.asyncio
    async def test_endpoints_and_malformed_handling(self) -> None:
        """Test all 5 InnerSpace endpoints, validate_connection, and malformed data."""
        client = UniFiInnerSpaceClient(
            auth=LocalAuth(api_key="k", verify_ssl=False),
            base_url="https://192.168.1.1",
            connection_type=ConnectionType.LOCAL,
        )

        client._get = AsyncMock(
            return_value={
                "data": {
                    "project": {"id": "proj-1"},
                    "plans": [{"id": "fp-1", "name": "Floor 1", "siteId": "site-1"}],
                    "products": [],
                }
            }
        )
        proj = await client.get_project(mode="2D")
        assert proj.project is not None
        assert proj.project.id == "proj-1"
        assert await client.validate_connection() is True

        # Root-level project fields without 'project' wrapper are also accepted
        client._get = AsyncMock(
            return_value={"id": "proj-root", "title": "Root Project"}
        )
        proj_root = await client.get_project()
        assert proj_root.project is not None
        assert proj_root.project.id == "proj-root"

        client._get = AsyncMock(
            return_value={"floor_plans": [{"id": "fp-1", "name": "Floor 1"}]}
        )
        fps = await client.list_floor_plans(site_id="site-1")
        assert len(fps) == 1
        assert fps[0].id == "fp-1"

        client._get = AsyncMock(
            return_value={
                "access_points": [
                    {"id": "ap-1", "name": "AP 1", "floor_plan_id": "fp-1"}
                ]
            }
        )
        aps = await client.list_access_points()
        assert len(aps) == 1
        assert aps[0].id == "ap-1"

        client._get = AsyncMock(
            return_value={
                "switches": [{"id": "sw-1", "name": "SW 1", "floor_plan_id": "fp-1"}]
            }
        )
        switches = await client.list_switches()
        assert len(switches) == 1
        assert switches[0].id == "sw-1"

        client._get = AsyncMock(
            return_value={"devices": [{"id": "inv-1", "name": "Unplaced AP"}]}
        )
        inventory = await client.list_inventory()
        assert len(inventory) == 1
        assert inventory[0].id == "inv-1"

        # Malformed responses raise UniFiResponseError
        client._get = AsyncMock(return_value="not-a-dict")
        with pytest.raises(UniFiResponseError):
            await client.get_project()
        assert await client.validate_connection() is False

        client._get = AsyncMock(return_value={"unexpected": []})
        with pytest.raises(UniFiResponseError):
            await client.get_project()
        assert await client.validate_connection() is False
        with pytest.raises(UniFiResponseError):
            await client.list_floor_plans()
