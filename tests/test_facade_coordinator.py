# Copyright (c) 2026 Ruaan Deysel
"""Tests for UniFi Insights facade coordinator."""

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.exceptions import HomeAssistantError

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.unifi_insights.coordinators.facade import (
    UnifiFacadeCoordinator,
)


@pytest.fixture
def mock_sub_coordinators() -> tuple[MagicMock, MagicMock, MagicMock, MagicMock]:
    """Create mock sub-coordinators for facade tests."""
    config_coord = MagicMock()
    config_coord.data = {"sites": {"site1": {"name": "Default"}}}
    config_coord.last_update_success = True
    config_coord.last_exception = None
    config_coord.async_refresh = AsyncMock()

    device_coord = MagicMock()
    device_coord.data = {
        "devices": {
            "site1": {
                "dev1": {
                    "id": "dev1",
                    "macAddress": "00:11:22:33:44:55",
                    "name": "Switch 1",
                }
            }
        },
        "clients": {
            "site1": {
                "client1": {
                    "id": "client1",
                    "macAddress": "AA:BB:CC:DD:EE:01",
                    "name": "Phone",
                },
                "client_no_mac": {
                    "id": "client_no_mac",
                    "name": "Ghost Client",
                },
            }
        },
        "stats": {},
    }
    device_coord.last_update_success = True
    device_coord.last_exception = None
    device_coord.async_refresh = AsyncMock()
    device_coord.get_legacy_site_name.return_value = "default"

    protect_coord = MagicMock()
    protect_coord.data = {
        "cameras": {"cam1": {"mac": "66:77:88:99:AA:BB"}},
        "lights": {"light1": {"mac": "11:22:33:44:55:66"}},
        "sensors": {"sens1": {"macAddress": "22:33:44:55:66:77"}},
        "nvrs": {"nvr1": {"mac_address": "33:44:55:66:77:88"}},
        "doorlocks": {"lock1": {"mac": "44:55:66:77:88:99"}},
        "viewports": {"vp1": {"mac": "55:66:77:88:99:00"}},
    }
    protect_coord.last_update_success = True
    protect_coord.last_exception = None
    protect_coord.async_refresh = AsyncMock()

    innerspace_coord = MagicMock()
    innerspace_coord.data = {
        "access_points": {"ap1": {"name": "AP Hall"}},
        "switches": {"sw1": {"name": "Switch Rack"}},
        "inventory": {"inv1": {"name": "Item"}},
    }
    innerspace_coord.last_update_success = True
    innerspace_coord.last_exception = None
    innerspace_coord.async_refresh = AsyncMock()

    return config_coord, device_coord, protect_coord, innerspace_coord


@pytest.fixture
def facade(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_sub_coordinators: tuple[MagicMock, MagicMock, MagicMock, MagicMock],
) -> UnifiFacadeCoordinator:
    """Create a test facade coordinator with mock children."""
    config_coord, device_coord, protect_coord, innerspace_coord = mock_sub_coordinators
    network_client = MagicMock()
    network_client.vouchers.create = AsyncMock()
    network_client.clients.unblock = AsyncMock()
    protect_client = MagicMock()

    return UnifiFacadeCoordinator(
        hass=hass,
        network_client=network_client,
        protect_client=protect_client,
        entry=mock_config_entry,
        config_coordinator=config_coord,
        device_coordinator=device_coord,
        protect_coordinator=protect_coord,
        innerspace_coordinator=innerspace_coord,
    )


class TestFacadeBuildInnerspaceCorrKey:
    """Tests for _build_innerspace_corr_key."""

    def test_build_innerspace_corr_key_full(self) -> None:
        """Test building correlation key with devices and protect data."""
        raw_innerspace = {"raw": 1}
        devices = {
            "site1": {
                "dev1": {"macAddress": "00:11:22:33:44:55"},
                "dev2": {"mac_address": "00:11:22:33:44:66"},
                "dev3": {"mac": "00:11:22:33:44:77"},
                "dev_invalid": "not_a_dict",
            },
            "site2": "not_a_dict",
        }
        protect_data = {
            "cameras": {"cam1": {"mac": "11:22:33:44:55:66"}},
            "lights": {"light1": {"macAddress": "22:33:44:55:66:77"}},
            "sensors": {"sens1": {"mac_address": "33:44:55:66:77:88"}},
            "nvrs": {"nvr1": {"mac": "44:55:66:77:88:99"}},
            "doorlocks": {"lock1": {"mac": "55:66:77:88:99:AA"}},
            "viewports": {"vp1": {"mac": "66:77:88:99:AA:BB"}},
        }
        key = UnifiFacadeCoordinator._build_innerspace_corr_key(
            raw_innerspace, devices, protect_data
        )
        assert isinstance(key, tuple)
        assert len(key) == 3
        assert key[0] == id(raw_innerspace)
        assert ("site1", "dev1", "00:11:22:33:44:55") in key[1]
        assert ("cameras", "cam1", "11:22:33:44:55:66") in key[2]

    def test_build_innerspace_corr_key_non_dict_inputs(self) -> None:
        """Test building correlation key with non-dict devices and protect data."""
        raw_innerspace = {"raw": 2}
        key = UnifiFacadeCoordinator._build_innerspace_corr_key(
            raw_innerspace, "not_dict", None
        )
        assert key == (id(raw_innerspace), (), ())


class TestFacadeInnerSpaceCaching:
    """Tests for InnerSpace data aggregation caching."""

    def test_aggregate_data_innerspace_cache_hit(
        self, facade: UnifiFacadeCoordinator
    ) -> None:
        """Test that repeated _aggregate_data calls reuse cached innerspace data."""
        facade._aggregate_data()
        assert facade._cached_innerspace_data is not None
        cached_before = facade._cached_innerspace_data

        facade._aggregate_data()
        assert facade.data["innerspace"] is cached_before


class TestFacadeAsyncRefreshChildren:
    """Tests for _async_refresh_children."""

    async def test_refresh_children_includes_innerspace(
        self, facade: UnifiFacadeCoordinator, mock_sub_coordinators
    ) -> None:
        """Test _async_refresh_children with include_innerspace=True."""
        _, _, _, innerspace_coord = mock_sub_coordinators
        failures = await facade._async_refresh_children(
            include_protect=True, include_innerspace=True
        )
        assert failures == []
        innerspace_coord.async_refresh.assert_awaited_once()


class TestFacadeClientTargetResolution:
    """Tests for _resolve_client_action_target."""

    def test_resolve_client_action_target_success(
        self, facade: UnifiFacadeCoordinator
    ) -> None:
        """Test resolving valid client target."""
        facade._device_coordinator.get_legacy_site_name.return_value = "legacy-site"
        facade._aggregate_data()
        site_name, mac = facade._resolve_client_action_target("site1", "client1")
        assert site_name == "legacy-site"
        assert mac == "AA:BB:CC:DD:EE:01"

    def test_resolve_client_action_target_missing_mac(
        self, facade: UnifiFacadeCoordinator
    ) -> None:
        """Test resolving client without MAC raises HomeAssistantError."""
        facade._aggregate_data()
        with pytest.raises(
            HomeAssistantError,
            match="Unable to determine MAC address for client client_no_mac",
        ):
            facade._resolve_client_action_target("site1", "client_no_mac")

    def test_resolve_client_action_target_missing_client(
        self, facade: UnifiFacadeCoordinator
    ) -> None:
        """Test resolving non-existent client raises HomeAssistantError."""
        facade._aggregate_data()
        with pytest.raises(
            HomeAssistantError,
            match="Unable to determine MAC address for client unknown_client",
        ):
            facade._resolve_client_action_target("site1", "unknown_client")


class TestFacadeGenerateVoucher:
    """Tests for async_generate_voucher."""

    async def test_generate_voucher_with_rate_limits(
        self, facade: UnifiFacadeCoordinator
    ) -> None:
        """Test async_generate_voucher with rate limits and usage limits."""
        await facade.async_generate_voucher(
            site_id="site1",
            name="VIP Guest",
            time_limit_minutes=120,
            count=2,
            tx_rate_limit_kbps=1000,
            rx_rate_limit_kbps=2000,
            data_usage_limit_mbytes=500,
        )
        facade.network_client.vouchers.create.assert_awaited_once_with(
            "site1",
            name="VIP Guest",
            time_limit_minutes=120,
            count=2,
            tx_rate_limit_kbps=1000,
            rx_rate_limit_kbps=2000,
            data_usage_limit_mbytes=500,
        )

    async def test_generate_voucher_without_limits(
        self, facade: UnifiFacadeCoordinator
    ) -> None:
        """Test async_generate_voucher without optional limits."""
        await facade.async_generate_voucher(
            site_id="site1",
            name="Standard Guest",
            time_limit_minutes=60,
            count=1,
        )
        facade.network_client.vouchers.create.assert_awaited_once_with(
            "site1",
            name="Standard Guest",
            time_limit_minutes=60,
            count=1,
        )
