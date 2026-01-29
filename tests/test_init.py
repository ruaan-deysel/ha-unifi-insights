"""Tests for the UniFi Insights integration initialization."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from unifi_official_api import (
    UniFiAuthenticationError,
    UniFiConnectionError,
    UniFiTimeoutError,
)

from custom_components.unifi_insights import UnifiInsightsData


async def test_setup_entry_success(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_network_client,
    mock_protect_client,
    mock_local_auth,
    enable_custom_integrations,
) -> None:
    """Test successful setup of config entry."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state == ConfigEntryState.LOADED


async def test_setup_entry_auth_failed(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_network_client,
    mock_local_auth,
    enable_custom_integrations,
) -> None:
    """Test setup fails with authentication error."""
    mock_network_client.sites.get_all.side_effect = UniFiAuthenticationError(
        "Invalid API key"
    )

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state == ConfigEntryState.SETUP_ERROR


async def test_setup_entry_connection_error(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_network_client,
    mock_local_auth,
    enable_custom_integrations,
) -> None:
    """Test setup fails with connection error."""
    mock_network_client.sites.get_all.side_effect = UniFiConnectionError(
        "Cannot connect"
    )

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state == ConfigEntryState.SETUP_RETRY


async def test_setup_entry_timeout_error(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_network_client,
    mock_local_auth,
    enable_custom_integrations,
) -> None:
    """Test setup fails with timeout error."""
    mock_network_client.sites.get_all.side_effect = UniFiTimeoutError(
        "Connection timeout"
    )

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state == ConfigEntryState.SETUP_RETRY


async def test_setup_entry_protect_unavailable(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_network_client,
    mock_protect_client,
    mock_local_auth,
    enable_custom_integrations,
) -> None:
    """Test setup succeeds even if Protect is unavailable."""
    mock_protect_client.cameras.get_all.side_effect = Exception("Protect unavailable")

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state == ConfigEntryState.LOADED


async def test_unload_entry(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    enable_custom_integrations,
) -> None:
    """Test successful unload of a config entry."""
    assert await hass.config_entries.async_unload(init_integration.entry_id)
    await hass.async_block_till_done()

    assert init_integration.state == ConfigEntryState.NOT_LOADED


async def test_reload_entry(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    enable_custom_integrations,
) -> None:
    """Test successful reload of a config entry."""
    await hass.config_entries.async_reload(init_integration.entry_id)
    await hass.async_block_till_done()

    assert init_integration.state == ConfigEntryState.LOADED


async def test_reload_entry_via_options_update(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    enable_custom_integrations,
) -> None:
    """Test reload triggered by options update (update listener)."""
    # Update options to trigger the update listener (async_reload_entry)
    hass.config_entries.async_update_entry(
        init_integration,
        options={"track_wifi_clients": True},
    )
    await hass.async_block_till_done()

    # Entry should be reloaded and in loaded state
    assert init_integration.state == ConfigEntryState.LOADED


async def test_setup_entry_no_sites_found(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_network_client,
    mock_local_auth,
    enable_custom_integrations,
) -> None:
    """Test setup fails when no sites are found."""
    # Return empty list - no sites found
    mock_network_client.sites.get_all.return_value = []

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Should fail with auth failed (no sites means bad API key)
    assert mock_config_entry.state == ConfigEntryState.SETUP_ERROR


async def test_setup_entry_remote_connection(
    hass: HomeAssistant,
    mock_network_client,
    mock_local_auth,
    enable_custom_integrations,
) -> None:
    """Test setup with remote connection type skips Protect."""
    # Create remote config entry
    remote_entry = MockConfigEntry(
        domain="unifi_insights",
        data={
            "connection_type": "remote",
            "console_id": "test_console",
            "api_key": "test_api_key",
        },
        entry_id="remote_entry",
    )

    remote_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(remote_entry.entry_id)
    await hass.async_block_till_done()

    assert remote_entry.state == ConfigEntryState.LOADED


async def test_unload_entry_with_websocket_task(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    enable_custom_integrations,
) -> None:
    """Test unload entry cancels websocket task."""

    # Add a mock websocket task to the protect coordinator
    runtime_data = init_integration.runtime_data
    if runtime_data.protect_coordinator:
        mock_task = MagicMock()
        mock_task.cancel = MagicMock()
        runtime_data.protect_coordinator.websocket_task = mock_task

    assert await hass.config_entries.async_unload(init_integration.entry_id)
    await hass.async_block_till_done()

    assert init_integration.state == ConfigEntryState.NOT_LOADED


async def test_unload_entry_protect_close_error(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    enable_custom_integrations,
) -> None:
    """Test unload entry handles protect client close error gracefully."""
    # Make protect client close raise an error
    runtime_data = init_integration.runtime_data
    if runtime_data.protect_client:
        runtime_data.protect_client.close = AsyncMock(
            side_effect=Exception("Close error")
        )

    # Should still unload successfully
    assert await hass.config_entries.async_unload(init_integration.entry_id)
    await hass.async_block_till_done()

    assert init_integration.state == ConfigEntryState.NOT_LOADED


async def test_unload_entry_network_close_error(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    enable_custom_integrations,
) -> None:
    """Test unload entry handles network client close error gracefully."""
    # Make network client close raise an error
    runtime_data = init_integration.runtime_data
    runtime_data.network_client.close = AsyncMock(side_effect=Exception("Close error"))

    # Should still unload successfully
    assert await hass.config_entries.async_unload(init_integration.entry_id)
    await hass.async_block_till_done()

    assert init_integration.state == ConfigEntryState.NOT_LOADED


async def test_unifi_insights_data_coordinator_not_initialized(
    hass: HomeAssistant,
) -> None:
    """Test UnifiInsightsData raises error when facade coordinator not initialized."""
    # Create data object with None facade coordinator
    data = UnifiInsightsData(
        config_coordinator=MagicMock(),
        device_coordinator=MagicMock(),
        protect_coordinator=None,
        network_client=MagicMock(),
        protect_client=None,
        _facade_coordinator=None,
    )

    # Accessing coordinator property should raise RuntimeError
    with pytest.raises(RuntimeError, match="Facade coordinator not initialized"):
        _ = data.coordinator
