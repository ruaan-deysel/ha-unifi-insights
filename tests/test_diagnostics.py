"""Tests for the UniFi Insights diagnostics."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.unifi_insights.diagnostics import (
    async_get_config_entry_diagnostics,
)


async def test_diagnostics(
    hass: HomeAssistant,
    init_integration: ConfigEntry,
) -> None:
    """Test diagnostics."""
    diagnostics = await async_get_config_entry_diagnostics(hass, init_integration)

    assert "library_version" in diagnostics
    assert "connection" in diagnostics
    assert "entry" in diagnostics
    assert "data" in diagnostics

    # Check connection info
    assert diagnostics["connection"]["host"] == "https://192.168.1.1"
    assert diagnostics["connection"]["network_client_connected"] is True
    assert diagnostics["connection"]["protect_client_connected"] is True

    # Check redaction
    assert "api_key" not in str(diagnostics).lower()
    assert "test_api_key" not in str(diagnostics)
