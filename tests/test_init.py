"""Tests for the UniFi Insights integration initialization."""

import pytest
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from unifi_official_api import (
    UniFiAuthenticationError,
    UniFiConnectionError,
    UniFiTimeoutError,
)

from custom_components.unifi_insights import (
    async_reload_entry,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.unifi_insights.const import DOMAIN


async def test_setup_entry_success(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_network_client,
    mock_protect_client,
    mock_local_auth,
) -> None:
    """Test successful setup of config entry."""
    assert await async_setup_entry(hass, mock_config_entry)
    await hass.async_block_till_done()

    assert mock_config_entry.state == ConfigEntryState.LOADED
    assert DOMAIN in hass.data
    assert mock_config_entry.entry_id in hass.data[DOMAIN]


async def test_setup_entry_auth_failed(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_network_client,
    mock_local_auth,
) -> None:
    """Test setup fails with authentication error."""
    mock_network_client.validate_connection.side_effect = UniFiAuthenticationError(
        "Invalid API key"
    )

    with pytest.raises(ConfigEntryAuthFailed):
        await async_setup_entry(hass, mock_config_entry)


async def test_setup_entry_connection_error(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_network_client,
    mock_local_auth,
) -> None:
    """Test setup fails with connection error."""
    mock_network_client.validate_connection.side_effect = UniFiConnectionError(
        "Cannot connect"
    )

    with pytest.raises(ConfigEntryNotReady):
        await async_setup_entry(hass, mock_config_entry)


async def test_setup_entry_timeout_error(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_network_client,
    mock_local_auth,
) -> None:
    """Test setup fails with timeout error."""
    mock_network_client.validate_connection.side_effect = UniFiTimeoutError(
        "Connection timeout"
    )

    with pytest.raises(ConfigEntryNotReady):
        await async_setup_entry(hass, mock_config_entry)


async def test_setup_entry_protect_unavailable(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_network_client,
    mock_protect_client,
    mock_local_auth,
) -> None:
    """Test setup succeeds even if Protect is unavailable."""
    mock_protect_client.validate_connection.return_value = False

    assert await async_setup_entry(hass, mock_config_entry)
    await hass.async_block_till_done()

    assert mock_config_entry.state == ConfigEntryState.LOADED


async def test_unload_entry(
    hass: HomeAssistant,
    init_integration: ConfigEntry,
) -> None:
    """Test successful unload of a config entry."""
    assert await async_unload_entry(hass, init_integration)
    await hass.async_block_till_done()

    assert init_integration.state == ConfigEntryState.NOT_LOADED
    assert init_integration.entry_id not in hass.data.get(DOMAIN, {})


async def test_reload_entry(
    hass: HomeAssistant,
    init_integration: ConfigEntry,
) -> None:
    """Test successful reload of a config entry."""
    await async_reload_entry(hass, init_integration)
    await hass.async_block_till_done()

    assert init_integration.state == ConfigEntryState.LOADED
    assert DOMAIN in hass.data
    assert init_integration.entry_id in hass.data[DOMAIN]
