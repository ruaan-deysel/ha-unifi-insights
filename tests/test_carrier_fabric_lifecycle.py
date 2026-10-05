# Copyright 2026 UniFi Insights contributors
"""Tests for UniFi Carrier Fabric integration setup, unload, and lifecycle."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.unifi_insights import (
    CarrierFabricData,
    async_remove_config_entry_device,
)
from custom_components.unifi_insights.const import (
    CONF_CARRIER_ORG_ID,
    CONF_CONNECTION_TYPE,
    CONF_TRACK_SUBSCRIBERS,
    CONNECTION_TYPE_CARRIER_FABRIC,
    DOMAIN,
)
from custom_components.unifi_insights.probe import ProbeResult, ProbeStatus

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")


@pytest.fixture
def carrier_entry(hass):
    """Create a mock Carrier Fabric config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="UniFi Carrier Fabric",
        unique_id="carrier_org_test123",
        data={
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_CARRIER_FABRIC,
            CONF_API_KEY: "isp_secret_key",
            CONF_CARRIER_ORG_ID: "org_test123",
        },
    )
    entry.add_to_hass(hass)
    return entry


async def test_carrier_fabric_setup_and_unload_success(hass, carrier_entry):
    """Test full setup, platform forwarding, and unload sequence."""
    mock_client = MagicMock()
    mock_client.close = AsyncMock()
    mock_client.service_plans = MagicMock()
    mock_client.service_plans.get_all = AsyncMock(return_value=[])
    mock_client.subscribers = MagicMock()
    mock_client.subscribers.get_all = AsyncMock(return_value=[])

    with (
        patch(
            "custom_components.unifi_insights.UniFiCarrierFabricClient",
            return_value=mock_client,
        ),
        patch(
            "custom_components.unifi_insights.async_probe_carrier_fabric",
            return_value=ProbeResult(
                status=ProbeStatus.AVAILABLE,
                org_id="org_test123",
            ),
        ),
        patch(
            "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups",
            new_callable=AsyncMock,
        ) as mock_forward,
    ):
        assert await hass.config_entries.async_setup(carrier_entry.entry_id)
        await hass.async_block_till_done()

        assert carrier_entry.state == ConfigEntryState.LOADED
        assert isinstance(carrier_entry.runtime_data, CarrierFabricData)
        assert carrier_entry.runtime_data.client is mock_client

        # Verify only Platform.SENSOR was forwarded
        mock_forward.assert_called_once_with(carrier_entry, [Platform.SENSOR])

        # Test unload
        assert await hass.config_entries.async_unload(carrier_entry.entry_id)
        await hass.async_block_till_done()

        assert carrier_entry.state == ConfigEntryState.NOT_LOADED
        mock_client.close.assert_awaited_once()


async def test_carrier_fabric_setup_probe_auth_failed(hass, carrier_entry):
    """Test setup raises ConfigEntryAuthFailed when probe reports AUTH_FAILED."""
    mock_client = MagicMock()
    mock_client.close = AsyncMock()

    with (
        patch(
            "custom_components.unifi_insights.UniFiCarrierFabricClient",
            return_value=mock_client,
        ),
        patch(
            "custom_components.unifi_insights.async_probe_carrier_fabric",
            return_value=ProbeResult(
                status=ProbeStatus.AUTH_FAILED,
                error=Exception("401 unauthorized"),
            ),
        ),
    ):
        await hass.config_entries.async_setup(carrier_entry.entry_id)
        await hass.async_block_till_done()

        assert carrier_entry.state == ConfigEntryState.SETUP_ERROR


async def test_carrier_fabric_setup_probe_unreachable(hass, carrier_entry):
    """Test setup raises ConfigEntryNotReady when probe reports UNREACHABLE."""
    mock_client = MagicMock()
    mock_client.close = AsyncMock()

    with (
        patch(
            "custom_components.unifi_insights.UniFiCarrierFabricClient",
            return_value=mock_client,
        ),
        patch(
            "custom_components.unifi_insights.async_probe_carrier_fabric",
            return_value=ProbeResult(
                status=ProbeStatus.UNREACHABLE,
                error=Exception("Connection refused"),
            ),
        ),
    ):
        await hass.config_entries.async_setup(carrier_entry.entry_id)
        await hass.async_block_till_done()

        assert carrier_entry.state == ConfigEntryState.SETUP_RETRY


async def test_carrier_fabric_setup_first_refresh_failure_closes_client(
    hass, carrier_entry
):
    """Test client is closed when coordinator first refresh fails during setup."""
    mock_client = MagicMock()
    mock_client.close = AsyncMock()
    mock_client.service_plans = MagicMock()
    mock_client.service_plans.get_all = AsyncMock(
        side_effect=Exception("Failed to load plans")
    )
    mock_client.subscribers = MagicMock()
    mock_client.subscribers.get_all = AsyncMock(return_value=[])

    with (
        patch(
            "custom_components.unifi_insights.UniFiCarrierFabricClient",
            return_value=mock_client,
        ),
        patch(
            "custom_components.unifi_insights.async_probe_carrier_fabric",
            return_value=ProbeResult(
                status=ProbeStatus.AVAILABLE,
                org_id="org_test123",
            ),
        ),
    ):
        await hass.config_entries.async_setup(carrier_entry.entry_id)
        await hass.async_block_till_done()

        assert carrier_entry.state == ConfigEntryState.SETUP_RETRY
        mock_client.close.assert_awaited()


async def test_carrier_fabric_options_update_listener(hass, carrier_entry):
    """Test updating options triggers reload of entry."""
    mock_client = MagicMock()
    mock_client.close = AsyncMock()
    mock_client.service_plans = MagicMock()
    mock_client.service_plans.get_all = AsyncMock(return_value=[])
    mock_client.subscribers = MagicMock()
    mock_client.subscribers.get_all = AsyncMock(return_value=[])

    with (
        patch(
            "custom_components.unifi_insights.UniFiCarrierFabricClient",
            return_value=mock_client,
        ),
        patch(
            "custom_components.unifi_insights.async_probe_carrier_fabric",
            return_value=ProbeResult(
                status=ProbeStatus.AVAILABLE,
                org_id="org_test123",
            ),
        ),
        patch(
            "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups",
            new_callable=AsyncMock,
        ),
    ):
        assert await hass.config_entries.async_setup(carrier_entry.entry_id)
        await hass.async_block_till_done()

        with patch.object(
            hass.config_entries, "async_reload", new_callable=AsyncMock
        ) as mock_reload:
            hass.config_entries.async_update_entry(
                carrier_entry,
                options={CONF_TRACK_SUBSCRIBERS: True},
            )
            await hass.async_block_till_done()
            mock_reload.assert_called_once_with(carrier_entry.entry_id)


async def test_carrier_fabric_device_removal(hass, carrier_entry):
    """Test device removal rules for Carrier Fabric."""
    mock_coordinator = MagicMock()
    mock_coordinator.data = {
        "subscribers": {
            "sub_active_1": {"id": "sub_active_1", "name": "Active 1"},
        }
    }
    mock_client = MagicMock()
    mock_client.close = AsyncMock()

    carrier_entry.runtime_data = CarrierFabricData(
        client=mock_client,
        coordinator=mock_coordinator,
    )

    # 1. Organization device (refuse removal)
    dev_reg = dr.async_get(hass)
    org_device = dev_reg.async_get_or_create(
        config_entry_id=carrier_entry.entry_id,
        identifiers={(DOMAIN, carrier_entry.unique_id)},
    )
    assert not await async_remove_config_entry_device(hass, carrier_entry, org_device)

    # 2. Subscriber device still in coordinator data (refuse removal)
    active_sub_device = dev_reg.async_get_or_create(
        config_entry_id=carrier_entry.entry_id,
        identifiers={(DOMAIN, "carrier_subscriber_sub_active_1")},
    )
    assert not await async_remove_config_entry_device(
        hass, carrier_entry, active_sub_device
    )

    # 3. Subscriber device no longer in coordinator data (allow removal)
    stale_sub_device = dev_reg.async_get_or_create(
        config_entry_id=carrier_entry.entry_id,
        identifiers={(DOMAIN, "carrier_subscriber_sub_removed_2")},
    )
    assert await async_remove_config_entry_device(hass, carrier_entry, stale_sub_device)

    # 4. Unknown device identifier format (refuse removal)
    other_device = dev_reg.async_get_or_create(
        config_entry_id=carrier_entry.entry_id,
        identifiers={(DOMAIN, "some_unknown_device_id")},
    )
    assert not await async_remove_config_entry_device(hass, carrier_entry, other_device)
