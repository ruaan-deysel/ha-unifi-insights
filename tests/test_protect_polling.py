"""Tests for Protect-only console polling and warning suppression."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.unifi_insights.api.exceptions import (
    UniFiResponseError,
)
from custom_components.unifi_insights.coordinators.config import (
    UnifiConfigCoordinator,
)


class TestProtectOnlyPollingBehavior:
    """Test Protect-only consoles avoid repeating Network site polling."""

    @pytest.mark.asyncio
    async def test_config_coordinator_skips_sites_when_network_unavailable(self):
        """Test config coordinator skips sites.get_all when network unavailable."""
        hass = MagicMock()
        network_client = MagicMock()
        protect_client = MagicMock()
        entry = MagicMock()
        entry.entry_id = "test_protect_entry"

        coordinator = UnifiConfigCoordinator(
            hass=hass,
            network_client=network_client,
            protect_client=protect_client,
            entry=entry,
            network_available=False,
        )
        assert coordinator._network_available is False

        data = await coordinator._async_update_data()
        assert data["sites"] == {}
        network_client.sites.get_all.assert_not_called()

    @pytest.mark.asyncio
    async def test_config_coordinator_marks_network_unavailable_on_non_json(self):
        """Test sites.get_all non-JSON error marks network unavailable."""
        hass = MagicMock()
        network_client = MagicMock()
        protect_client = MagicMock()
        entry = MagicMock()
        entry.entry_id = "test_protect_entry"

        coordinator = UnifiConfigCoordinator(
            hass=hass,
            network_client=network_client,
            protect_client=protect_client,
            entry=entry,
            network_available=True,
        )
        network_client.sites.get_all = AsyncMock(
            side_effect=UniFiResponseError("Response is not JSON", status_code=200)
        )

        data = await coordinator._async_update_data()
        assert coordinator._network_available is False
        assert data["sites"] == {}
