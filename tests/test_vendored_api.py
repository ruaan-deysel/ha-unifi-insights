"""Tests for the vendored UniFi API package."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from custom_components.unifi_insights.api import ApiKeyAuth, ConnectionType
from custom_components.unifi_insights.api.network import UniFiNetworkClient


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


async def test_get_hosts_remote_without_console_id() -> None:
    """Test remote host discovery works before a console ID is selected."""
    client = UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        connection_type=ConnectionType.REMOTE,
    )
    client._get = AsyncMock(
        return_value={
            "data": [
                {
                    "id": "console-id",
                    "type": "console",
                    "reportedState": {"hostname": "Dream Router 7"},
                }
            ]
        }
    )

    result = await client.get_hosts()

    assert result == [
        {
            "id": "console-id",
            "type": "console",
            "reportedState": {"hostname": "Dream Router 7"},
        }
    ]
    client._get.assert_awaited_once_with("/v1/hosts")


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
