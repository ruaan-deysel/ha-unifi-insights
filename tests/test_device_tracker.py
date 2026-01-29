"""Tests for UniFi Insights device tracker platform."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from homeassistant.components.device_tracker import SourceType

from custom_components.unifi_insights.device_tracker import (
    PARALLEL_UPDATES,
    UnifiClientTracker,
    _get_client_type,
    async_setup_entry,
)


class TestParallelUpdates:
    """Test PARALLEL_UPDATES constant."""

    def test_parallel_updates_value(self) -> None:
        """Test that PARALLEL_UPDATES is set correctly."""
        assert PARALLEL_UPDATES == 0


class TestAsyncSetupEntry:
    """Tests for async_setup_entry function."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Create mock coordinator."""
        coordinator = MagicMock()
        coordinator.protect_client = None
        coordinator.network_client = MagicMock()
        coordinator.network_client.base_url = "https://192.168.1.1"
        coordinator.data = {
            "sites": {"site1": {"id": "site1", "meta": {"name": "Test Site"}}},
            "devices": {"site1": {}},
            "clients": {"site1": {}},
            "protect": {
                "cameras": {},
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "viewers": {},
                "chimes": {},
            },
        }
        return coordinator

    @pytest.mark.asyncio
    async def test_setup_entry_tracking_disabled(self, hass, mock_coordinator) -> None:
        """Test setup when client tracking is disabled (default)."""
        mock_coordinator.data["clients"]["site1"] = {
            "client1": {
                "id": "client1",
                "mac": "AA:BB:CC:DD:EE:FF",
                "name": "Test Client",
                "connected": True,
            }
        }

        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator
        mock_entry.async_on_unload = MagicMock()
        # Tracking disabled by default (options is empty dict)
        mock_entry.options = {}

        # Initialize tracked clients set
        hass.data = {}

        async_add_entities = MagicMock()

        await async_setup_entry(hass, mock_entry, async_add_entities)

        # No entities should be added when tracking is disabled
        async_add_entities.assert_not_called()

    @pytest.mark.asyncio
    async def test_setup_entry_no_clients(self, hass, mock_coordinator) -> None:
        """Test setup when no clients present but tracking is enabled."""
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator
        mock_entry.async_on_unload = MagicMock()
        # Enable WiFi client tracking with new option
        mock_entry.options = {"track_wifi_clients": True}

        # Initialize tracked clients set
        hass.data = {}

        async_add_entities = MagicMock()

        await async_setup_entry(hass, mock_entry, async_add_entities)

        # When no entities, async_add_entities is not called (only called if entities)
        async_add_entities.assert_not_called()

    @pytest.mark.asyncio
    async def test_setup_entry_with_clients(self, hass, mock_coordinator) -> None:
        """Test setup with clients present and tracking enabled (wired client)."""
        mock_coordinator.data["clients"]["site1"] = {
            "client1": {
                "id": "client1",
                "mac": "AA:BB:CC:DD:EE:FF",
                "name": "Test Client",
                "connected": True,
                "ipAddress": "192.168.1.100",
                "hostname": "test-client",
                "type": "WIRED",
            }
        }

        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator
        mock_entry.async_on_unload = MagicMock()
        # Enable wired client tracking with new option
        mock_entry.options = {"track_wired_clients": True}

        # Initialize tracked clients set
        hass.data = {}

        async_add_entities = MagicMock()

        await async_setup_entry(hass, mock_entry, async_add_entities)

        async_add_entities.assert_called_once()
        entities = async_add_entities.call_args[0][0]
        assert len(entities) == 1
        assert isinstance(entities[0], UnifiClientTracker)

    @pytest.mark.asyncio
    async def test_setup_entry_wifi_only_skips_wired(
        self, hass, mock_coordinator
    ) -> None:
        """Test setup with WiFi tracking only skips wired clients."""
        mock_coordinator.data["clients"]["site1"] = {
            "client1": {
                "id": "client1",
                "mac": "AA:BB:CC:DD:EE:FF",
                "name": "Wired Client",
                "connected": True,
                "type": "WIRED",
            },
            "client2": {
                "id": "client2",
                "mac": "11:22:33:44:55:66",
                "name": "WiFi Client",
                "connected": True,
                "type": "WIRELESS",
            },
        }

        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator
        mock_entry.async_on_unload = MagicMock()
        # Enable WiFi only tracking
        mock_entry.options = {"track_wifi_clients": True, "track_wired_clients": False}

        # Initialize tracked clients set
        hass.data = {}

        async_add_entities = MagicMock()

        await async_setup_entry(hass, mock_entry, async_add_entities)

        async_add_entities.assert_called_once()
        entities = async_add_entities.call_args[0][0]
        # Only WiFi client should be tracked
        assert len(entities) == 1
        assert entities[0]._client_id == "client2"

    @pytest.mark.asyncio
    async def test_setup_entry_wired_only_skips_wifi(
        self, hass, mock_coordinator
    ) -> None:
        """Test setup with wired tracking only skips WiFi clients."""
        mock_coordinator.data["clients"]["site1"] = {
            "client1": {
                "id": "client1",
                "mac": "AA:BB:CC:DD:EE:FF",
                "name": "Wired Client",
                "connected": True,
                "type": "WIRED",
            },
            "client2": {
                "id": "client2",
                "mac": "11:22:33:44:55:66",
                "name": "WiFi Client",
                "connected": True,
                "type": "WIRELESS",
            },
        }

        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator
        mock_entry.async_on_unload = MagicMock()
        # Enable wired only tracking
        mock_entry.options = {"track_wifi_clients": False, "track_wired_clients": True}

        # Initialize tracked clients set
        hass.data = {}

        async_add_entities = MagicMock()

        await async_setup_entry(hass, mock_entry, async_add_entities)

        async_add_entities.assert_called_once()
        entities = async_add_entities.call_args[0][0]
        # Only wired client should be tracked
        assert len(entities) == 1
        assert entities[0]._client_id == "client1"

    @pytest.mark.asyncio
    async def test_setup_entry_both_client_types(self, hass, mock_coordinator) -> None:
        """Test setup with both client types tracking enabled."""
        mock_coordinator.data["clients"]["site1"] = {
            "client1": {
                "id": "client1",
                "mac": "AA:BB:CC:DD:EE:FF",
                "name": "Wired Client",
                "connected": True,
                "type": "WIRED",
            },
            "client2": {
                "id": "client2",
                "mac": "11:22:33:44:55:66",
                "name": "WiFi Client",
                "connected": True,
                "type": "WIRELESS",
            },
        }

        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator
        mock_entry.async_on_unload = MagicMock()
        # Enable both tracking options
        mock_entry.options = {"track_wifi_clients": True, "track_wired_clients": True}

        # Initialize tracked clients set
        hass.data = {}

        async_add_entities = MagicMock()

        await async_setup_entry(hass, mock_entry, async_add_entities)

        async_add_entities.assert_called_once()
        entities = async_add_entities.call_args[0][0]
        # Both clients should be tracked
        assert len(entities) == 2

    @pytest.mark.asyncio
    async def test_setup_entry_old_option_migration(
        self, hass, mock_coordinator
    ) -> None:
        """Test setup migrates old track_clients option to new options."""
        mock_coordinator.data["clients"]["site1"] = {
            "client1": {
                "id": "client1",
                "mac": "AA:BB:CC:DD:EE:FF",
                "name": "Wired Client",
                "connected": True,
                "type": "WIRED",
            },
            "client2": {
                "id": "client2",
                "mac": "11:22:33:44:55:66",
                "name": "WiFi Client",
                "connected": True,
                "type": "WIRELESS",
            },
        }

        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator
        mock_entry.async_on_unload = MagicMock()
        # Use old option - should track all clients as fallback
        mock_entry.options = {"track_clients": True}

        # Initialize tracked clients set
        hass.data = {}

        async_add_entities = MagicMock()

        await async_setup_entry(hass, mock_entry, async_add_entities)

        async_add_entities.assert_called_once()
        entities = async_add_entities.call_args[0][0]
        # Both clients should be tracked with old option migration
        assert len(entities) == 2

    @pytest.mark.asyncio
    async def test_setup_entry_multiple_sites(self, hass, mock_coordinator) -> None:
        """Test setup with clients from multiple sites and tracking enabled."""
        mock_coordinator.data["sites"]["site2"] = {
            "id": "site2",
            "meta": {"name": "Site 2"},
        }
        mock_coordinator.data["clients"]["site1"] = {
            "client1": {
                "id": "client1",
                "mac": "AA:BB:CC:DD:EE:FF",
                "name": "Client 1",
                "connected": True,
                "type": "WIRED",
            }
        }
        mock_coordinator.data["clients"]["site2"] = {
            "client2": {
                "id": "client2",
                "mac": "11:22:33:44:55:66",
                "name": "Client 2",
                "connected": False,
                "type": "WIRELESS",
            }
        }

        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator
        mock_entry.async_on_unload = MagicMock()
        # Enable both client tracking options
        mock_entry.options = {"track_wifi_clients": True, "track_wired_clients": True}

        # Initialize tracked clients set
        hass.data = {}

        async_add_entities = MagicMock()

        await async_setup_entry(hass, mock_entry, async_add_entities)

        async_add_entities.assert_called_once()
        entities = async_add_entities.call_args[0][0]
        assert len(entities) == 2

    @pytest.mark.asyncio
    async def test_setup_entry_skips_already_tracked_clients(
        self, hass, mock_coordinator
    ) -> None:
        """Test setup skips clients that are already tracked."""
        mock_coordinator.data["clients"]["site1"] = {
            "client1": {
                "id": "client1",
                "mac": "AA:BB:CC:DD:EE:FF",
                "name": "Already Tracked Client",
                "connected": True,
                "type": "WIRED",
            },
            "client2": {
                "id": "client2",
                "mac": "11:22:33:44:55:66",
                "name": "New Client",
                "connected": True,
                "type": "WIRED",
            },
        }

        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator
        mock_entry.async_on_unload = MagicMock()
        # Enable wired tracking
        mock_entry.options = {"track_wifi_clients": False, "track_wired_clients": True}

        # Pre-populate tracked clients set with client1 as already tracked
        # The code uses coordinator.hass.data, so we need to set it there
        mock_coordinator.hass = hass
        hass.data = {"unifi_insights_tracked_clients": {"site1_client1"}}

        async_add_entities = MagicMock()

        await async_setup_entry(hass, mock_entry, async_add_entities)

        async_add_entities.assert_called_once()
        entities = async_add_entities.call_args[0][0]
        # Only client2 should be added (client1 was already tracked)
        assert len(entities) == 1
        assert entities[0]._client_id == "client2"


class TestUnifiClientTracker:
    """Tests for UnifiClientTracker entity."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Create mock coordinator."""
        coordinator = MagicMock()
        coordinator.protect_client = None
        coordinator.network_client = MagicMock()
        coordinator.network_client.base_url = "https://192.168.1.1"
        coordinator.last_update_success = True
        coordinator.data = {
            "sites": {"site1": {"id": "site1", "meta": {"name": "Test Site"}}},
            "devices": {"site1": {}},
            "clients": {
                "site1": {
                    "client1": {
                        "id": "client1",
                        "mac": "AA:BB:CC:DD:EE:FF",
                        "name": "Test Client",
                        "connected": True,
                        "ipAddress": "192.168.1.100",
                        "hostname": "test-client",
                        "type": "WIRED",
                    }
                }
            },
            "protect": {
                "cameras": {},
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "viewers": {},
                "chimes": {},
            },
        }
        return coordinator

    def test_initialization(self, mock_coordinator) -> None:
        """Test tracker initialization."""
        tracker = UnifiClientTracker(
            coordinator=mock_coordinator,
            site_id="site1",
            client_id="client1",
        )

        assert tracker._site_id == "site1"
        assert tracker._client_id == "client1"

    def test_unique_id(self, mock_coordinator) -> None:
        """Test unique ID is set correctly."""
        tracker = UnifiClientTracker(
            coordinator=mock_coordinator,
            site_id="site1",
            client_id="client1",
        )

        # Unique ID uses MAC address format
        assert tracker._attr_unique_id is not None
        assert "AA:BB:CC:DD:EE:FF" in tracker._attr_unique_id

    def test_source_type_wired(self, mock_coordinator) -> None:
        """Test source type for wired client."""
        tracker = UnifiClientTracker(
            coordinator=mock_coordinator,
            site_id="site1",
            client_id="client1",
        )

        assert tracker.source_type == SourceType.ROUTER

    def test_source_type_wireless(self, mock_coordinator) -> None:
        """Test source type for wireless client."""
        mock_coordinator.data["clients"]["site1"]["client1"]["type"] = "WIRELESS"

        tracker = UnifiClientTracker(
            coordinator=mock_coordinator,
            site_id="site1",
            client_id="client1",
        )

        assert tracker.source_type == SourceType.ROUTER

    def test_is_connected_online(self, mock_coordinator) -> None:
        """Test is_connected for online client."""
        # Ensure connected field is True
        mock_coordinator.data["clients"]["site1"]["client1"]["connected"] = True

        tracker = UnifiClientTracker(
            coordinator=mock_coordinator,
            site_id="site1",
            client_id="client1",
        )

        assert tracker.is_connected is True

    def test_is_connected_offline(self, mock_coordinator) -> None:
        """Test is_connected for offline client."""
        mock_coordinator.data["clients"]["site1"]["client1"]["connected"] = False

        tracker = UnifiClientTracker(
            coordinator=mock_coordinator,
            site_id="site1",
            client_id="client1",
        )

        assert tracker.is_connected is False

    def test_is_connected_missing_client(self, mock_coordinator) -> None:
        """Test is_connected when client data is missing."""
        tracker = UnifiClientTracker(
            coordinator=mock_coordinator,
            site_id="site1",
            client_id="client1",
        )

        # Remove client data
        mock_coordinator.data["clients"]["site1"] = {}

        assert tracker.is_connected is False

    def test_available(self, mock_coordinator) -> None:
        """Test entity availability based on coordinator update success."""
        tracker = UnifiClientTracker(
            coordinator=mock_coordinator,
            site_id="site1",
            client_id="client1",
        )

        # Default: coordinator last_update_success is True
        assert tracker.available is True

        # Coordinator fails update
        mock_coordinator.last_update_success = False
        assert tracker.available is False

    def test_ip_address(self, mock_coordinator) -> None:
        """Test IP address property."""
        tracker = UnifiClientTracker(
            coordinator=mock_coordinator,
            site_id="site1",
            client_id="client1",
        )

        assert tracker.ip_address == "192.168.1.100"

    def test_mac_address(self, mock_coordinator) -> None:
        """Test MAC address property."""
        tracker = UnifiClientTracker(
            coordinator=mock_coordinator,
            site_id="site1",
            client_id="client1",
        )

        assert tracker.mac_address == "AA:BB:CC:DD:EE:FF"

    def test_hostname(self, mock_coordinator) -> None:
        """Test hostname property."""
        tracker = UnifiClientTracker(
            coordinator=mock_coordinator,
            site_id="site1",
            client_id="client1",
        )

        assert tracker.hostname == "test-client"

    def test_extra_state_attributes(self, mock_coordinator) -> None:
        """Test extra state attributes."""
        mock_coordinator.data["clients"]["site1"]["client1"].update(
            {
                "type": "WIRELESS",
                "uplinkDeviceId": "device123",
                "essid": "TestWiFi",
                "channel": 36,
                "rssi": -45,
            }
        )

        tracker = UnifiClientTracker(
            coordinator=mock_coordinator,
            site_id="site1",
            client_id="client1",
        )

        attrs = tracker.extra_state_attributes
        assert attrs is not None
        assert attrs["connection_type"] == "WIRELESS"

    def test_device_info(self, mock_coordinator) -> None:
        """Test device info is set correctly."""
        tracker = UnifiClientTracker(
            coordinator=mock_coordinator,
            site_id="site1",
            client_id="client1",
        )

        device_info = tracker.device_info
        assert device_info is not None
        assert device_info.get("manufacturer") == "Ubiquiti Inc."


class TestGetClientType:
    """Tests for _get_client_type helper function."""

    def test_get_client_type_wired(self) -> None:
        """Test _get_client_type returns WIRED for wired clients."""
        result = _get_client_type({"type": "WIRED"})
        assert result == "WIRED"

    def test_get_client_type_wireless(self) -> None:
        """Test _get_client_type returns WIRELESS for wireless clients."""
        result = _get_client_type({"type": "WIRELESS"})
        assert result == "WIRELESS"

    def test_get_client_type_unknown(self) -> None:
        """Test _get_client_type returns original type for unknown types."""
        result = _get_client_type({"type": "UNKNOWN_TYPE"})
        assert result == "UNKNOWN_TYPE"

    def test_get_client_type_empty_string(self) -> None:
        """Test _get_client_type returns empty string when no type."""
        result = _get_client_type({"type": ""})
        assert result == ""

    def test_get_client_type_connection_type_field(self) -> None:
        """Test _get_client_type uses connection_type field as fallback."""
        result = _get_client_type({"connection_type": "WIRED"})
        assert result == "WIRED"

    def test_get_client_type_no_type_field(self) -> None:
        """Test _get_client_type returns empty string when no type field."""
        result = _get_client_type({})
        assert result == ""


class TestUnifiClientTrackerEdgeCases:
    """Test edge cases for UnifiClientTracker."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Create mock coordinator."""
        coordinator = MagicMock()
        coordinator.protect_client = None
        coordinator.network_client = MagicMock()
        coordinator.network_client.base_url = "https://192.168.1.1"
        coordinator.last_update_success = True
        coordinator.data = {
            "sites": {"site1": {"id": "site1", "meta": {"name": "Test Site"}}},
            "devices": {"site1": {"device1": {"id": "device1", "name": "Device"}}},
            "clients": {
                "site1": {
                    "client1": {
                        "id": "client1",
                        "mac": "AA:BB:CC:DD:EE:FF",
                        "macAddress": "AA:BB:CC:DD:EE:FF",
                        "name": "Test Client",
                        "hostname": "test-client",
                        "connected": True,
                        "type": "WIRELESS",
                    }
                }
            },
            "protect": {
                "cameras": {},
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "viewers": {},
                "chimes": {},
            },
        }
        return coordinator

    def test_source_type_no_client_data(self, mock_coordinator) -> None:
        """Test source_type returns ROUTER when client data is missing."""
        tracker = UnifiClientTracker(
            coordinator=mock_coordinator,
            site_id="site1",
            client_id="client1",
        )

        # Remove client data
        mock_coordinator.data["clients"]["site1"] = {}

        assert tracker.source_type == SourceType.ROUTER

    def test_ip_address_no_client_data(self, mock_coordinator) -> None:
        """Test ip_address returns None when client data is missing."""
        tracker = UnifiClientTracker(
            coordinator=mock_coordinator,
            site_id="site1",
            client_id="client1",
        )

        # Remove client data
        mock_coordinator.data["clients"]["site1"] = {}

        assert tracker.ip_address is None

    def test_mac_address_no_client_data(self, mock_coordinator) -> None:
        """Test mac_address returns None when client data is missing."""
        tracker = UnifiClientTracker(
            coordinator=mock_coordinator,
            site_id="site1",
            client_id="client1",
        )

        # Remove client data
        mock_coordinator.data["clients"]["site1"] = {}

        assert tracker.mac_address is None

    def test_hostname_no_client_data(self, mock_coordinator) -> None:
        """Test hostname returns None when client data is missing."""
        tracker = UnifiClientTracker(
            coordinator=mock_coordinator,
            site_id="site1",
            client_id="client1",
        )

        # Remove client data
        mock_coordinator.data["clients"]["site1"] = {}

        assert tracker.hostname is None

    def test_extra_state_attributes_no_client_data(self, mock_coordinator) -> None:
        """Test extra_state_attributes returns empty dict when missing."""
        tracker = UnifiClientTracker(
            coordinator=mock_coordinator,
            site_id="site1",
            client_id="client1",
        )

        # Remove client data
        mock_coordinator.data["clients"]["site1"] = {}

        assert tracker.extra_state_attributes == {}

    def test_unique_id_without_mac(self, mock_coordinator) -> None:
        """Test unique_id uses client_id when mac is not available."""
        # Create client without mac
        mock_coordinator.data["clients"]["site1"]["client_no_mac"] = {
            "id": "client_no_mac",
            "name": "Client Without MAC",
            "connected": True,
        }

        tracker = UnifiClientTracker(
            coordinator=mock_coordinator,
            site_id="site1",
            client_id="client_no_mac",
        )

        assert tracker._attr_unique_id == "unifi_insights_client_no_mac"

    async def test_async_added_to_hass(self, mock_coordinator, hass) -> None:
        """Test async_added_to_hass registers listener."""
        mock_coordinator.async_add_listener = MagicMock(return_value=MagicMock())

        tracker = UnifiClientTracker(
            coordinator=mock_coordinator,
            site_id="site1",
            client_id="client1",
        )
        tracker.hass = hass

        # Create a mock async_on_remove
        remove_callbacks = []
        tracker.async_on_remove = lambda callback: remove_callbacks.append(callback)

        await tracker.async_added_to_hass()

        # Verify listener was added
        mock_coordinator.async_add_listener.assert_called_once()

    def test_handle_coordinator_update(self, mock_coordinator, hass) -> None:
        """Test _handle_coordinator_update writes state."""
        tracker = UnifiClientTracker(
            coordinator=mock_coordinator,
            site_id="site1",
            client_id="client1",
        )
        tracker.hass = hass

        # Mock async_write_ha_state
        tracker.async_write_ha_state = MagicMock()

        tracker._handle_coordinator_update()

        tracker.async_write_ha_state.assert_called_once()
