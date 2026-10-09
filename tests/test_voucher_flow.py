# Copyright 2026 UniFi Insights contributors
"""End-to-end flow tests for hotspot vouchers with real coordinators."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.unifi_insights.api.network.models.voucher import Voucher
from homeassistant.const import CONF_API_KEY
from custom_components.unifi_insights.const import DOMAIN
from custom_components.unifi_insights.coordinators.config import (
    UnifiConfigCoordinator,
)
from custom_components.unifi_insights.coordinators.device import (
    UnifiDeviceCoordinator,
)
from custom_components.unifi_insights.coordinators.facade import (
    UnifiFacadeCoordinator,
)
from custom_components.unifi_insights.coordinators.voucher_state import (
    count_active_vouchers,
)


def _create_mock_model(data: dict) -> MagicMock:
    """Create a mock model returning data from model_dump."""
    mock = MagicMock()
    mock.model_dump = MagicMock(return_value=data)
    for k, v in data.items():
        setattr(mock, k, v)
    return mock


@pytest.mark.asyncio
async def test_generate_flow_updates_inventory_and_latest_voucher(
    hass: HomeAssistant,
) -> None:
    """Generating a voucher updates inventory, latest_vouchers and fires listeners."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_API_KEY: "test_api_key"},
        options={},
    )
    network_client = MagicMock()
    network_client.base_url = "https://192.168.1.1"
    network_client.sites = MagicMock()
    network_client.sites.get_all = AsyncMock(
        return_value=[_create_mock_model({"id": "site1", "name": "Default"})]
    )
    network_client.sites.get_legacy_all = AsyncMock(return_value=[])
    network_client.wifi = MagicMock()
    network_client.wifi.get_all = AsyncMock(return_value=[])
    network_client.firewall = MagicMock()
    network_client.firewall.list_rules = AsyncMock(return_value=[])
    network_client.devices = MagicMock()
    network_client.devices.get_all = AsyncMock(return_value=[])
    network_client.clients = MagicMock()
    network_client.clients.get_all = AsyncMock(return_value=[])
    network_client.reports = MagicMock()
    network_client.reports.get_site_report = AsyncMock(return_value=[])

    # Initial state: no vouchers
    created_voucher = Voucher(
        id="v-1",
        code="1234567890",
        name="Home Assistant",
        time_limit_minutes=480,
    )
    updated_voucher_model = _create_mock_model(
        {
            "id": "v-1",
            "code": "1234567890",
            "name": "Home Assistant",
            "timeLimitMinutes": 480,
            "activatedAt": "2026-10-09T12:00:00Z",
            "expiresAt": "2026-10-09T20:00:00Z",
            "expired": False,
            "authorizedGuestCount": 1,
            "authorizedGuestLimit": 2,
        }
    )

    network_client.vouchers = MagicMock()
    network_client.vouchers.create = AsyncMock(return_value=[created_voucher])
    network_client.vouchers.get_all_pages = AsyncMock(
        side_effect=[
            [],  # initial poll
            [updated_voucher_model],  # after create
        ]
    )

    config_coord = UnifiConfigCoordinator(
        hass=hass,
        network_client=network_client,
        protect_client=None,
        entry=entry,
    )
    device_coord = UnifiDeviceCoordinator(
        hass=hass,
        network_client=network_client,
        protect_client=None,
        entry=entry,
        config_coordinator=config_coord,
    )
    facade = UnifiFacadeCoordinator(
        hass=hass,
        network_client=network_client,
        protect_client=None,
        entry=entry,
        config_coordinator=config_coord,
        device_coordinator=device_coord,
        protect_coordinator=None,
    )

    # Initial refresh
    await config_coord.async_refresh()
    await device_coord.async_refresh()
    facade._aggregate_data()

    assert count_active_vouchers(facade.data["vouchers"].get("site1", {})) == 0
    assert facade.data["latest_vouchers"] == {}

    listener = MagicMock()
    facade.async_add_listener(listener)

    # Generate voucher
    result = await facade.async_generate_voucher(
        "site1",
        name="Home Assistant",
        time_limit_minutes=480,
    )
    assert result == [created_voucher]

    # Listener was called
    listener.assert_called()

    # Inventory and latest vouchers are updated
    inventory = facade.data["vouchers"]["site1"]
    assert "v-1" in inventory
    assert inventory["v-1"]["code"] == "1234567890"
    assert inventory["v-1"]["activatedAt"] == "2026-10-09T12:00:00Z"

    latest = facade.data["latest_vouchers"]["site1"]
    assert latest["id"] == "v-1"
    assert latest["code"] == "1234567890"
    assert latest["activatedAt"] == "2026-10-09T12:00:00Z"

    # Active count is 1
    assert count_active_vouchers(inventory) == 1
