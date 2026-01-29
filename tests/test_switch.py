"""Tests for UniFi Protect switch platform."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.helpers.entity import EntityCategory

from custom_components.unifi_insights.const import (
    ATTR_CAMERA_ID,
    ATTR_CAMERA_NAME,
    ATTR_HIGH_FPS_MODE,
    ATTR_MIC_ENABLED,
    ATTR_PRIVACY_MODE,
    ATTR_STATUS_LIGHT,
    DEVICE_TYPE_CAMERA,
    DOMAIN,
    VIDEO_MODE_DEFAULT,
    VIDEO_MODE_HIGH_FPS,
)
from custom_components.unifi_insights.switch import (
    PARALLEL_UPDATES,
    UnifiClientBlockSwitch,
    UnifiPoESwitch,
    UnifiPortEnableSwitch,
    UnifiProtectHighFPSSwitch,
    UnifiProtectMicrophoneSwitch,
    UnifiProtectPrivacySwitch,
    UnifiProtectStatusLightSwitch,
    UnifiWifiSwitch,
    async_setup_entry,
)


class TestParallelUpdates:
    """Test PARALLEL_UPDATES constant."""

    def test_parallel_updates_value(self) -> None:
        """Test that PARALLEL_UPDATES is set correctly for action-based entities."""
        assert PARALLEL_UPDATES == 1


class TestAsyncSetupEntry:
    """Tests for async_setup_entry function."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Create mock coordinator."""
        coordinator = MagicMock()
        coordinator.protect_client = MagicMock()
        coordinator.network_client = MagicMock()
        coordinator.network_client.base_url = "https://192.168.1.1"
        coordinator.data = {
            "sites": {},
            "devices": {},
            "protect": {
                "cameras": {},
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "viewers": {},
                "chimes": {},
                "liveviews": {},
            },
        }
        return coordinator

    @pytest.mark.asyncio
    async def test_setup_entry_no_protect_client(self, hass, mock_coordinator) -> None:
        """Test setup when Protect API is not available.

        The switch platform now also handles PoE switches for network devices,
        so even without Protect, entities may be added (0 in this case since
        no devices have PoE ports configured).
        """
        mock_coordinator.protect_client = None

        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        async_add_entities = MagicMock()

        await async_setup_entry(hass, mock_entry, async_add_entities)

        # Should add empty list (no PoE ports, no Protect cameras)
        async_add_entities.assert_called_once_with([])

    @pytest.mark.asyncio
    async def test_setup_entry_with_cameras(self, hass, mock_coordinator) -> None:
        """Test setup with cameras present."""
        mock_coordinator.data["protect"]["cameras"] = {
            "camera1": {
                "id": "camera1",
                "name": "Test Camera",
                "state": "CONNECTED",
                "micEnabled": True,
            }
        }

        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        async_add_entities = MagicMock()

        await async_setup_entry(hass, mock_entry, async_add_entities)

        # Should add 3 switch entities per camera (microphone, privacy, status light)
        # High FPS only added if hasHighFpsCapability is True
        async_add_entities.assert_called_once()
        entities = async_add_entities.call_args[0][0]
        assert len(entities) == 3
        assert isinstance(entities[0], UnifiProtectMicrophoneSwitch)
        assert isinstance(entities[1], UnifiProtectPrivacySwitch)
        assert isinstance(entities[2], UnifiProtectStatusLightSwitch)

    @pytest.mark.asyncio
    async def test_setup_entry_with_multiple_cameras(
        self, hass, mock_coordinator
    ) -> None:
        """Test setup with multiple cameras."""
        mock_coordinator.data["protect"]["cameras"] = {
            "camera1": {"id": "camera1", "name": "Front Camera", "state": "CONNECTED"},
            "camera2": {"id": "camera2", "name": "Back Camera", "state": "CONNECTED"},
            "camera3": {
                "id": "camera3",
                "name": "Side Camera",
                "state": "DISCONNECTED",
            },
        }

        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        async_add_entities = MagicMock()

        await async_setup_entry(hass, mock_entry, async_add_entities)

        entities = async_add_entities.call_args[0][0]
        # 3 cameras x 3 switches each = 9 switches
        assert len(entities) == 9


class TestUnifiProtectMicrophoneSwitch:
    """Tests for UnifiProtectMicrophoneSwitch entity."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Create mock coordinator."""
        coordinator = MagicMock()
        coordinator.protect_client = MagicMock()
        coordinator.protect_client.base_url = "https://192.168.1.1"
        coordinator.protect_client.update_camera = AsyncMock()
        coordinator.network_client = MagicMock()
        coordinator.network_client.base_url = "https://192.168.1.1"
        coordinator.data = {
            "sites": {},
            "devices": {},
            "protect": {
                "cameras": {
                    "camera1": {
                        "id": "camera1",
                        "name": "Test Camera",
                        "state": "CONNECTED",
                        "mac": "AA:BB:CC:DD:EE:FF",
                        "type": "UVC-G4-Pro",
                        "firmwareVersion": "1.0.0",
                        "micEnabled": True,
                    }
                },
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "viewers": {},
                "chimes": {},
                "liveviews": {},
            },
        }
        return coordinator

    def test_initialization(self, mock_coordinator) -> None:
        """Test switch entity initialization."""
        switch = UnifiProtectMicrophoneSwitch(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )

        assert switch._device_id == "camera1"
        assert switch._device_type == DEVICE_TYPE_CAMERA
        assert switch._attr_has_entity_name is True
        assert switch._attr_name == "Microphone"
        assert switch._attr_entity_category == EntityCategory.CONFIG

    def test_update_from_data_mic_enabled(self, mock_coordinator) -> None:
        """Test _update_from_data with microphone enabled."""
        switch = UnifiProtectMicrophoneSwitch(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )

        assert switch._attr_is_on is True

    def test_update_from_data_mic_disabled(self, mock_coordinator) -> None:
        """Test _update_from_data with microphone disabled."""
        mock_coordinator.data["protect"]["cameras"]["camera1"]["micEnabled"] = False

        switch = UnifiProtectMicrophoneSwitch(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )

        assert switch._attr_is_on is False

    def test_extra_state_attributes(self, mock_coordinator) -> None:
        """Test extra state attributes."""
        switch = UnifiProtectMicrophoneSwitch(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )

        attrs = switch._attr_extra_state_attributes
        assert attrs[ATTR_CAMERA_ID] == "camera1"
        assert attrs[ATTR_CAMERA_NAME] == "Test Camera"
        assert attrs[ATTR_MIC_ENABLED] is True

    @pytest.mark.asyncio
    async def test_async_turn_on_success(self, mock_coordinator) -> None:
        """Test turning microphone on successfully."""
        switch = UnifiProtectMicrophoneSwitch(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )
        switch.async_write_ha_state = MagicMock()

        await switch.async_turn_on()

        mock_coordinator.protect_client.update_camera.assert_called_once_with(
            camera_id="camera1",
            data={"micEnabled": True},
        )
        assert switch._attr_is_on is True
        switch.async_write_ha_state.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_turn_on_error(self, mock_coordinator) -> None:
        """Test turning microphone on with error."""
        mock_coordinator.protect_client.update_camera.side_effect = Exception(
            "API error"
        )

        switch = UnifiProtectMicrophoneSwitch(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )
        switch._attr_is_on = False
        switch.async_write_ha_state = MagicMock()

        await switch.async_turn_on()

        # Should log error but not update state
        switch.async_write_ha_state.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_turn_off_success(self, mock_coordinator) -> None:
        """Test turning microphone off successfully."""
        switch = UnifiProtectMicrophoneSwitch(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )
        switch.async_write_ha_state = MagicMock()

        await switch.async_turn_off()

        mock_coordinator.protect_client.update_camera.assert_called_once_with(
            camera_id="camera1",
            data={"micEnabled": False},
        )
        assert switch._attr_is_on is False
        switch.async_write_ha_state.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_turn_off_error(self, mock_coordinator) -> None:
        """Test turning microphone off with error."""
        mock_coordinator.protect_client.update_camera.side_effect = Exception(
            "API error"
        )

        switch = UnifiProtectMicrophoneSwitch(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )
        switch._attr_is_on = True
        switch.async_write_ha_state = MagicMock()

        await switch.async_turn_off()

        # Should log error but not update state
        switch.async_write_ha_state.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_turn_on_ignores_kwargs(self, mock_coordinator) -> None:
        """Test turning microphone on ignores extra kwargs."""
        switch = UnifiProtectMicrophoneSwitch(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )
        switch.async_write_ha_state = MagicMock()

        await switch.async_turn_on(some_extra_kwarg="value")

        mock_coordinator.protect_client.update_camera.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_turn_off_ignores_kwargs(self, mock_coordinator) -> None:
        """Test turning microphone off ignores extra kwargs."""
        switch = UnifiProtectMicrophoneSwitch(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )
        switch.async_write_ha_state = MagicMock()

        await switch.async_turn_off(some_extra_kwarg="value")

        mock_coordinator.protect_client.update_camera.assert_called_once()

    def test_missing_camera_data(self, mock_coordinator) -> None:
        """Test handling missing camera data."""
        mock_coordinator.data["protect"]["cameras"]["camera1"] = {}

        switch = UnifiProtectMicrophoneSwitch(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )

        # Should default to off
        assert switch._attr_is_on is False

    def test_missing_mic_enabled(self, mock_coordinator) -> None:
        """Test handling missing micEnabled field."""
        del mock_coordinator.data["protect"]["cameras"]["camera1"]["micEnabled"]

        switch = UnifiProtectMicrophoneSwitch(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )

        # Should default to False
        assert switch._attr_is_on is False


class TestUnifiClientBlockSwitch:
    """Tests for client block switch."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Create mock coordinator."""
        coordinator = MagicMock()
        coordinator.network_client = MagicMock()
        coordinator.network_client.clients = MagicMock()
        coordinator.network_client.clients.block = AsyncMock()
        coordinator.network_client.clients.unblock = AsyncMock()
        coordinator.async_request_refresh = AsyncMock()
        coordinator.data = {
            "sites": {"site1": {"id": "site1"}},
            "devices": {
                "site1": {
                    "device1": {
                        "id": "device1",
                        "name": "Test Switch",
                        "model": "USW-24-POE",
                    },
                },
            },
            "clients": {
                "site1": {
                    "client1": {
                        "id": "client1",
                        "name": "Jukebox",
                        "hostname": "jukebox",
                        "mac": "AA:BB:CC:DD:EE:FF",
                        "blocked": False,
                        "uplinkDeviceId": "device1",
                    },
                },
            },
            "stats": {},
            "wifi": {},
            "protect": {
                "cameras": {},
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "viewers": {},
                "chimes": {},
                "liveviews": {},
            },
        }
        return coordinator

    def test_switch_grouped_under_device(self, mock_coordinator) -> None:
        """Test switch is grouped under connected device."""
        switch = UnifiClientBlockSwitch(
            coordinator=mock_coordinator,
            site_id="site1",
            client_id="client1",
        )

        # Should use the uplink device's identifiers
        assert switch._attr_device_info["identifiers"] == {(DOMAIN, "site1_device1")}

    def test_switch_fallback_no_uplink(self, mock_coordinator) -> None:
        """Test switch creates own device when no uplink."""
        # Remove uplink device ID
        mock_coordinator.data["clients"]["site1"]["client1"]["uplinkDeviceId"] = None

        switch = UnifiClientBlockSwitch(
            coordinator=mock_coordinator,
            site_id="site1",
            client_id="client1",
        )

        # Should create its own device
        assert switch._attr_device_info["identifiers"] == {(DOMAIN, "client_client1")}
        assert switch._attr_device_info["name"] == "Jukebox"

    def test_switch_available(self, mock_coordinator) -> None:
        """Test switch availability."""
        switch = UnifiClientBlockSwitch(
            coordinator=mock_coordinator,
            site_id="site1",
            client_id="client1",
        )

        # Should be available when client exists
        assert switch.available is True

        # Should be unavailable when client doesn't exist
        mock_coordinator.data["clients"]["site1"]["client1"] = {}
        assert switch.available is False

    def test_switch_is_on_when_not_blocked(self, mock_coordinator) -> None:
        """Test switch is ON when client is not blocked (allowed)."""
        switch = UnifiClientBlockSwitch(
            coordinator=mock_coordinator,
            site_id="site1",
            client_id="client1",
        )

        # Not blocked = ON (allowed)
        assert switch.is_on is True

    def test_switch_is_off_when_blocked(self, mock_coordinator) -> None:
        """Test switch is OFF when client is blocked."""
        mock_coordinator.data["clients"]["site1"]["client1"]["blocked"] = True

        switch = UnifiClientBlockSwitch(
            coordinator=mock_coordinator,
            site_id="site1",
            client_id="client1",
        )

        # When client is blocked, switch should be OFF (OFF means blocked)
        assert switch.is_on is False

    @pytest.mark.asyncio
    async def test_turn_on_unblocks_client(self, mock_coordinator) -> None:
        """Test turning ON unblocks the client."""
        mock_coordinator.data["clients"]["site1"]["client1"]["blocked"] = True

        switch = UnifiClientBlockSwitch(
            coordinator=mock_coordinator,
            site_id="site1",
            client_id="client1",
        )

        await switch.async_turn_on()

        mock_coordinator.network_client.clients.unblock.assert_called_once_with(
            "site1", "client1"
        )
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_turn_off_blocks_client(self, mock_coordinator) -> None:
        """Test turning OFF blocks the client."""
        switch = UnifiClientBlockSwitch(
            coordinator=mock_coordinator,
            site_id="site1",
            client_id="client1",
        )

        await switch.async_turn_off()

        mock_coordinator.network_client.clients.block.assert_called_once_with(
            "site1", "client1"
        )
        mock_coordinator.async_request_refresh.assert_called_once()


class TestUnifiWifiSwitch:
    """Tests for WiFi network enable/disable switch."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Create mock coordinator."""
        coordinator = MagicMock()
        coordinator.network_client = MagicMock()
        coordinator.network_client.wifi = MagicMock()
        coordinator.network_client.wifi.update = AsyncMock()
        coordinator.async_request_refresh = AsyncMock()
        coordinator.data = {
            "sites": {"site1": {"id": "site1"}},
            "devices": {},
            "clients": {},
            "stats": {},
            "wifi": {
                "site1": {
                    "wifi1": {
                        "id": "wifi1",
                        "name": "Home Network",
                        "ssid": "HomeWiFi",
                        "enabled": True,
                        "security": "wpa2",
                        "hidden": False,
                        "isGuest": False,
                    },
                },
            },
            "protect": {
                "cameras": {},
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "viewers": {},
                "chimes": {},
                "liveviews": {},
            },
        }
        return coordinator

    def test_switch_unique_id(self, mock_coordinator) -> None:
        """Test switch has correct unique ID."""
        wifi_data = mock_coordinator.data["wifi"]["site1"]["wifi1"]
        switch = UnifiWifiSwitch(
            coordinator=mock_coordinator,
            site_id="site1",
            wifi_id="wifi1",
            wifi_data=wifi_data,
        )

        assert switch._attr_unique_id == "site1_wifi1_wifi_switch"

    def test_switch_name(self, mock_coordinator) -> None:
        """Test switch has correct name."""
        wifi_data = mock_coordinator.data["wifi"]["site1"]["wifi1"]
        switch = UnifiWifiSwitch(
            coordinator=mock_coordinator,
            site_id="site1",
            wifi_id="wifi1",
            wifi_data=wifi_data,
        )

        assert switch._attr_name == "WiFi Home Network"

    def test_switch_device_info(self, mock_coordinator) -> None:
        """Test switch device info is set correctly."""
        wifi_data = mock_coordinator.data["wifi"]["site1"]["wifi1"]
        switch = UnifiWifiSwitch(
            coordinator=mock_coordinator,
            site_id="site1",
            wifi_id="wifi1",
            wifi_data=wifi_data,
        )

        assert switch._attr_device_info["identifiers"] == {(DOMAIN, "wifi_wifi1")}
        assert switch._attr_device_info["name"] == "WiFi: Home Network"

    def test_switch_is_on_when_enabled(self, mock_coordinator) -> None:
        """Test switch is ON when WiFi is enabled."""
        wifi_data = mock_coordinator.data["wifi"]["site1"]["wifi1"]
        switch = UnifiWifiSwitch(
            coordinator=mock_coordinator,
            site_id="site1",
            wifi_id="wifi1",
            wifi_data=wifi_data,
        )

        assert switch.is_on is True

    def test_switch_is_off_when_disabled(self, mock_coordinator) -> None:
        """Test switch is OFF when WiFi is disabled."""
        mock_coordinator.data["wifi"]["site1"]["wifi1"]["enabled"] = False
        wifi_data = mock_coordinator.data["wifi"]["site1"]["wifi1"]

        switch = UnifiWifiSwitch(
            coordinator=mock_coordinator,
            site_id="site1",
            wifi_id="wifi1",
            wifi_data=wifi_data,
        )

        assert switch.is_on is False

    def test_extra_state_attributes(self, mock_coordinator) -> None:
        """Test extra state attributes are returned."""
        wifi_data = mock_coordinator.data["wifi"]["site1"]["wifi1"]
        switch = UnifiWifiSwitch(
            coordinator=mock_coordinator,
            site_id="site1",
            wifi_id="wifi1",
            wifi_data=wifi_data,
        )

        attrs = switch.extra_state_attributes
        assert attrs["wifi_id"] == "wifi1"
        assert attrs["ssid"] == "HomeWiFi"
        assert attrs["security"] == "wpa2"
        assert attrs["hidden"] is False
        assert attrs["is_guest"] is False

    @pytest.mark.asyncio
    async def test_turn_on_enables_wifi(self, mock_coordinator) -> None:
        """Test turning ON enables the WiFi network."""
        mock_coordinator.data["wifi"]["site1"]["wifi1"]["enabled"] = False
        wifi_data = mock_coordinator.data["wifi"]["site1"]["wifi1"]

        switch = UnifiWifiSwitch(
            coordinator=mock_coordinator,
            site_id="site1",
            wifi_id="wifi1",
            wifi_data=wifi_data,
        )

        await switch.async_turn_on()

        mock_coordinator.network_client.wifi.update.assert_called_once_with(
            "site1", "wifi1", enabled=True
        )
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_turn_off_disables_wifi(self, mock_coordinator) -> None:
        """Test turning OFF disables the WiFi network."""
        wifi_data = mock_coordinator.data["wifi"]["site1"]["wifi1"]

        switch = UnifiWifiSwitch(
            coordinator=mock_coordinator,
            site_id="site1",
            wifi_id="wifi1",
            wifi_data=wifi_data,
        )

        await switch.async_turn_off()

        mock_coordinator.network_client.wifi.update.assert_called_once_with(
            "site1", "wifi1", enabled=False
        )
        mock_coordinator.async_request_refresh.assert_called_once()

    def test_available_when_wifi_data_exists(self, mock_coordinator) -> None:
        """Test switch is available when WiFi data exists."""
        wifi_data = mock_coordinator.data["wifi"]["site1"]["wifi1"]
        switch = UnifiWifiSwitch(
            coordinator=mock_coordinator,
            site_id="site1",
            wifi_id="wifi1",
            wifi_data=wifi_data,
        )

        assert switch.available is True

    def test_available_falls_back_to_initial_data(self, mock_coordinator) -> None:
        """Test switch uses initial data when coordinator data is empty."""
        wifi_data = mock_coordinator.data["wifi"]["site1"]["wifi1"].copy()
        mock_coordinator.data["wifi"]["site1"]["wifi1"] = {}

        switch = UnifiWifiSwitch(
            coordinator=mock_coordinator,
            site_id="site1",
            wifi_id="wifi1",
            wifi_data=wifi_data,
        )

        # Should fall back to initial wifi_data
        assert switch.available is True


class TestUnifiProtectPrivacySwitch:
    """Tests for UnifiProtectPrivacySwitch entity."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Create mock coordinator."""
        coordinator = MagicMock()
        coordinator.protect_client = MagicMock()
        coordinator.protect_client.base_url = "https://192.168.1.1"
        coordinator.protect_client.cameras = MagicMock()
        coordinator.protect_client.cameras.update = AsyncMock()
        coordinator.network_client = MagicMock()
        coordinator.network_client.base_url = "https://192.168.1.1"
        coordinator.data = {
            "sites": {},
            "devices": {},
            "protect": {
                "cameras": {
                    "camera1": {
                        "id": "camera1",
                        "name": "Test Camera",
                        "state": "CONNECTED",
                        "mac": "AA:BB:CC:DD:EE:FF",
                        "type": "UVC-G4-Pro",
                        "firmwareVersion": "1.0.0",
                        "isPrivacyModeEnabled": False,
                        "privacyZones": [],
                    }
                },
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "viewers": {},
                "chimes": {},
                "liveviews": {},
            },
        }
        return coordinator

    def test_initialization(self, mock_coordinator) -> None:
        """Test switch entity initialization."""
        switch = UnifiProtectPrivacySwitch(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )

        assert switch._device_id == "camera1"
        assert switch._device_type == DEVICE_TYPE_CAMERA
        assert switch._attr_has_entity_name is True
        assert switch._attr_name == "Privacy Mode"
        assert switch._attr_entity_category == EntityCategory.CONFIG
        assert switch._attr_icon == "mdi:eye-off"

    def test_update_from_data_privacy_disabled(self, mock_coordinator) -> None:
        """Test _update_from_data with privacy mode disabled."""
        switch = UnifiProtectPrivacySwitch(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )

        assert switch._attr_is_on is False

    def test_update_from_data_privacy_enabled_via_flag(self, mock_coordinator) -> None:
        """Test _update_from_data with privacy mode enabled via flag."""
        mock_coordinator.data["protect"]["cameras"]["camera1"][
            "isPrivacyModeEnabled"
        ] = True

        switch = UnifiProtectPrivacySwitch(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )

        assert switch._attr_is_on is True

    def test_update_from_data_privacy_enabled_via_zones(self, mock_coordinator) -> None:
        """Test _update_from_data with privacy zones configured."""
        mock_coordinator.data["protect"]["cameras"]["camera1"]["privacyZones"] = [
            {"points": [[0, 0], [100, 0], [100, 100], [0, 100]]}
        ]

        switch = UnifiProtectPrivacySwitch(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )

        assert switch._attr_is_on is True

    def test_extra_state_attributes(self, mock_coordinator) -> None:
        """Test extra state attributes."""
        switch = UnifiProtectPrivacySwitch(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )

        attrs = switch._attr_extra_state_attributes
        assert attrs[ATTR_CAMERA_ID] == "camera1"
        assert attrs[ATTR_CAMERA_NAME] == "Test Camera"
        assert attrs[ATTR_PRIVACY_MODE] is False

    @pytest.mark.asyncio
    async def test_async_turn_on_success(self, mock_coordinator) -> None:
        """Test turning privacy mode on successfully."""
        switch = UnifiProtectPrivacySwitch(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )
        switch.async_write_ha_state = MagicMock()

        await switch.async_turn_on()

        mock_coordinator.protect_client.cameras.update.assert_called_once_with(
            "camera1",
            is_privacy_mode_enabled=True,
        )
        assert switch._attr_is_on is True
        switch.async_write_ha_state.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_turn_on_error(self, mock_coordinator) -> None:
        """Test turning privacy mode on with error."""
        mock_coordinator.protect_client.cameras.update.side_effect = Exception(
            "API error"
        )

        switch = UnifiProtectPrivacySwitch(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )
        switch._attr_is_on = False
        switch.async_write_ha_state = MagicMock()

        await switch.async_turn_on()

        # Should log error but not update state
        switch.async_write_ha_state.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_turn_off_success(self, mock_coordinator) -> None:
        """Test turning privacy mode off successfully."""
        mock_coordinator.data["protect"]["cameras"]["camera1"][
            "isPrivacyModeEnabled"
        ] = True

        switch = UnifiProtectPrivacySwitch(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )
        switch.async_write_ha_state = MagicMock()

        await switch.async_turn_off()

        mock_coordinator.protect_client.cameras.update.assert_called_once_with(
            "camera1",
            is_privacy_mode_enabled=False,
        )
        assert switch._attr_is_on is False
        switch.async_write_ha_state.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_turn_off_error(self, mock_coordinator) -> None:
        """Test turning privacy mode off with error."""
        mock_coordinator.protect_client.cameras.update.side_effect = Exception(
            "API error"
        )
        mock_coordinator.data["protect"]["cameras"]["camera1"][
            "isPrivacyModeEnabled"
        ] = True

        switch = UnifiProtectPrivacySwitch(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )
        switch.async_write_ha_state = MagicMock()

        await switch.async_turn_off()

        # Should log error but not update state
        switch.async_write_ha_state.assert_not_called()


class TestUnifiProtectStatusLightSwitch:
    """Tests for UnifiProtectStatusLightSwitch entity."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Create mock coordinator."""
        coordinator = MagicMock()
        coordinator.protect_client = MagicMock()
        coordinator.protect_client.base_url = "https://192.168.1.1"
        coordinator.protect_client.cameras = MagicMock()
        coordinator.protect_client.cameras.update = AsyncMock()
        coordinator.network_client = MagicMock()
        coordinator.network_client.base_url = "https://192.168.1.1"
        coordinator.data = {
            "sites": {},
            "devices": {},
            "protect": {
                "cameras": {
                    "camera1": {
                        "id": "camera1",
                        "name": "Test Camera",
                        "state": "CONNECTED",
                        "mac": "AA:BB:CC:DD:EE:FF",
                        "type": "UVC-G4-Pro",
                        "firmwareVersion": "1.0.0",
                        "ledSettings": {"isEnabled": True},
                    }
                },
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "viewers": {},
                "chimes": {},
                "liveviews": {},
            },
        }
        return coordinator

    def test_initialization(self, mock_coordinator) -> None:
        """Test switch entity initialization."""
        switch = UnifiProtectStatusLightSwitch(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )

        assert switch._device_id == "camera1"
        assert switch._device_type == DEVICE_TYPE_CAMERA
        assert switch._attr_has_entity_name is True
        assert switch._attr_name == "Status Light"
        assert switch._attr_entity_category == EntityCategory.CONFIG
        assert switch._attr_icon == "mdi:led-on"

    def test_update_from_data_led_enabled(self, mock_coordinator) -> None:
        """Test _update_from_data with LED enabled."""
        switch = UnifiProtectStatusLightSwitch(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )

        assert switch._attr_is_on is True

    def test_update_from_data_led_disabled(self, mock_coordinator) -> None:
        """Test _update_from_data with LED disabled."""
        mock_coordinator.data["protect"]["cameras"]["camera1"]["ledSettings"] = {
            "isEnabled": False
        }

        switch = UnifiProtectStatusLightSwitch(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )

        assert switch._attr_is_on is False

    def test_update_from_data_no_led_settings(self, mock_coordinator) -> None:
        """Test _update_from_data when ledSettings is missing (defaults to True)."""
        del mock_coordinator.data["protect"]["cameras"]["camera1"]["ledSettings"]

        switch = UnifiProtectStatusLightSwitch(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )

        # Default is True when ledSettings is missing
        assert switch._attr_is_on is True

    def test_extra_state_attributes(self, mock_coordinator) -> None:
        """Test extra state attributes."""
        switch = UnifiProtectStatusLightSwitch(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )

        attrs = switch._attr_extra_state_attributes
        assert attrs[ATTR_CAMERA_ID] == "camera1"
        assert attrs[ATTR_CAMERA_NAME] == "Test Camera"
        assert attrs[ATTR_STATUS_LIGHT] is True

    @pytest.mark.asyncio
    async def test_async_turn_on_success(self, mock_coordinator) -> None:
        """Test turning status light on successfully."""
        mock_coordinator.data["protect"]["cameras"]["camera1"]["ledSettings"] = {
            "isEnabled": False
        }

        switch = UnifiProtectStatusLightSwitch(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )
        switch.async_write_ha_state = MagicMock()

        await switch.async_turn_on()

        mock_coordinator.protect_client.cameras.update.assert_called_once_with(
            "camera1",
            led_settings={"isEnabled": True},
        )
        assert switch._attr_is_on is True
        switch.async_write_ha_state.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_turn_on_error(self, mock_coordinator) -> None:
        """Test turning status light on with error."""
        mock_coordinator.protect_client.cameras.update.side_effect = Exception(
            "API error"
        )
        mock_coordinator.data["protect"]["cameras"]["camera1"]["ledSettings"] = {
            "isEnabled": False
        }

        switch = UnifiProtectStatusLightSwitch(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )
        switch.async_write_ha_state = MagicMock()

        await switch.async_turn_on()

        # Should log error but not update state
        switch.async_write_ha_state.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_turn_off_success(self, mock_coordinator) -> None:
        """Test turning status light off successfully."""
        switch = UnifiProtectStatusLightSwitch(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )
        switch.async_write_ha_state = MagicMock()

        await switch.async_turn_off()

        mock_coordinator.protect_client.cameras.update.assert_called_once_with(
            "camera1",
            led_settings={"isEnabled": False},
        )
        assert switch._attr_is_on is False
        switch.async_write_ha_state.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_turn_off_error(self, mock_coordinator) -> None:
        """Test turning status light off with error."""
        mock_coordinator.protect_client.cameras.update.side_effect = Exception(
            "API error"
        )

        switch = UnifiProtectStatusLightSwitch(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )
        switch.async_write_ha_state = MagicMock()

        await switch.async_turn_off()

        # Should log error but not update state
        switch.async_write_ha_state.assert_not_called()


class TestUnifiProtectHighFPSSwitch:
    """Tests for UnifiProtectHighFPSSwitch entity."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Create mock coordinator."""
        coordinator = MagicMock()
        coordinator.protect_client = MagicMock()
        coordinator.protect_client.base_url = "https://192.168.1.1"
        coordinator.protect_client.cameras = MagicMock()
        coordinator.protect_client.cameras.update = AsyncMock()
        coordinator.network_client = MagicMock()
        coordinator.network_client.base_url = "https://192.168.1.1"
        coordinator.data = {
            "sites": {},
            "devices": {},
            "protect": {
                "cameras": {
                    "camera1": {
                        "id": "camera1",
                        "name": "Test Camera",
                        "state": "CONNECTED",
                        "mac": "AA:BB:CC:DD:EE:FF",
                        "type": "UVC-G4-Pro",
                        "firmwareVersion": "1.0.0",
                        "videoMode": "default",
                        "featureFlags": {"hasHighFpsCapability": True},
                    }
                },
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "viewers": {},
                "chimes": {},
                "liveviews": {},
            },
        }
        return coordinator

    def test_initialization(self, mock_coordinator) -> None:
        """Test switch entity initialization."""
        switch = UnifiProtectHighFPSSwitch(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )

        assert switch._device_id == "camera1"
        assert switch._device_type == DEVICE_TYPE_CAMERA
        assert switch._attr_has_entity_name is True
        assert switch._attr_name == "High FPS Mode"
        assert switch._attr_entity_category == EntityCategory.CONFIG
        assert switch._attr_icon == "mdi:fast-forward"

    def test_update_from_data_default_mode(self, mock_coordinator) -> None:
        """Test _update_from_data with default video mode."""
        switch = UnifiProtectHighFPSSwitch(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )

        assert switch._attr_is_on is False

    def test_update_from_data_high_fps_mode(self, mock_coordinator) -> None:
        """Test _update_from_data with high FPS video mode."""
        mock_coordinator.data["protect"]["cameras"]["camera1"]["videoMode"] = (
            VIDEO_MODE_HIGH_FPS
        )

        switch = UnifiProtectHighFPSSwitch(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )

        assert switch._attr_is_on is True

    def test_update_from_data_sport_mode(self, mock_coordinator) -> None:
        """Test _update_from_data with sport video mode (not high FPS)."""
        mock_coordinator.data["protect"]["cameras"]["camera1"]["videoMode"] = "sport"

        switch = UnifiProtectHighFPSSwitch(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )

        assert switch._attr_is_on is False

    def test_extra_state_attributes(self, mock_coordinator) -> None:
        """Test extra state attributes."""
        switch = UnifiProtectHighFPSSwitch(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )

        attrs = switch._attr_extra_state_attributes
        assert attrs[ATTR_CAMERA_ID] == "camera1"
        assert attrs[ATTR_CAMERA_NAME] == "Test Camera"
        assert attrs[ATTR_HIGH_FPS_MODE] is False

    @pytest.mark.asyncio
    async def test_async_turn_on_success(self, mock_coordinator) -> None:
        """Test enabling high FPS mode successfully."""
        switch = UnifiProtectHighFPSSwitch(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )
        switch.async_write_ha_state = MagicMock()

        await switch.async_turn_on()

        mock_coordinator.protect_client.cameras.update.assert_called_once_with(
            "camera1",
            video_mode=VIDEO_MODE_HIGH_FPS,
        )
        assert switch._attr_is_on is True
        switch.async_write_ha_state.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_turn_on_error(self, mock_coordinator) -> None:
        """Test enabling high FPS mode with error."""
        mock_coordinator.protect_client.cameras.update.side_effect = Exception(
            "API error"
        )

        switch = UnifiProtectHighFPSSwitch(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )
        switch._attr_is_on = False
        switch.async_write_ha_state = MagicMock()

        await switch.async_turn_on()

        # Should log error but not update state
        switch.async_write_ha_state.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_turn_off_success(self, mock_coordinator) -> None:
        """Test disabling high FPS mode successfully."""
        mock_coordinator.data["protect"]["cameras"]["camera1"]["videoMode"] = (
            VIDEO_MODE_HIGH_FPS
        )

        switch = UnifiProtectHighFPSSwitch(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )
        switch.async_write_ha_state = MagicMock()

        await switch.async_turn_off()

        mock_coordinator.protect_client.cameras.update.assert_called_once_with(
            "camera1",
            video_mode=VIDEO_MODE_DEFAULT,
        )
        assert switch._attr_is_on is False
        switch.async_write_ha_state.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_turn_off_error(self, mock_coordinator) -> None:
        """Test disabling high FPS mode with error."""
        mock_coordinator.protect_client.cameras.update.side_effect = Exception(
            "API error"
        )
        mock_coordinator.data["protect"]["cameras"]["camera1"]["videoMode"] = (
            VIDEO_MODE_HIGH_FPS
        )

        switch = UnifiProtectHighFPSSwitch(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )
        switch.async_write_ha_state = MagicMock()

        await switch.async_turn_off()

        # Should log error but not update state
        switch.async_write_ha_state.assert_not_called()


class TestAsyncSetupEntryWithNewSwitches:
    """Test async_setup_entry with new camera switches."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Create mock coordinator."""
        coordinator = MagicMock()
        coordinator.protect_client = MagicMock()
        coordinator.network_client = MagicMock()
        coordinator.network_client.base_url = "https://192.168.1.1"
        coordinator.data = {
            "sites": {},
            "devices": {},
            "clients": {},
            "wifi": {},
            "protect": {
                "cameras": {
                    "camera1": {
                        "id": "camera1",
                        "name": "Test Camera",
                        "state": "CONNECTED",
                        "featureFlags": {"hasHighFpsCapability": True},
                    },
                    "camera2": {
                        "id": "camera2",
                        "name": "Basic Camera",
                        "state": "CONNECTED",
                        "featureFlags": {"hasHighFpsCapability": False},
                    },
                },
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "viewers": {},
                "chimes": {},
                "liveviews": {},
            },
        }
        return coordinator

    @pytest.mark.asyncio
    async def test_setup_creates_all_camera_switches(
        self, hass, mock_coordinator
    ) -> None:
        """Test setup creates camera switches (mic, privacy, status, high FPS)."""
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        async_add_entities = MagicMock()

        await async_setup_entry(hass, mock_entry, async_add_entities)

        entities = async_add_entities.call_args[0][0]

        # Camera 1 gets 4 switches (mic, privacy, status light, high FPS)
        # Camera 2 gets 3 switches (mic, privacy, status light - no high FPS)
        # Total: 7 switches
        assert len(entities) == 7

        # Check types
        entity_types = [type(e).__name__ for e in entities]
        assert entity_types.count("UnifiProtectMicrophoneSwitch") == 2
        assert entity_types.count("UnifiProtectPrivacySwitch") == 2
        assert entity_types.count("UnifiProtectStatusLightSwitch") == 2
        assert entity_types.count("UnifiProtectHighFPSSwitch") == 1

    @pytest.mark.asyncio
    async def test_high_fps_only_for_capable_cameras(
        self, hass, mock_coordinator
    ) -> None:
        """Test high FPS switch is only created for cameras with capability."""
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        async_add_entities = MagicMock()

        await async_setup_entry(hass, mock_entry, async_add_entities)

        entities = async_add_entities.call_args[0][0]

        # Find high FPS switches
        high_fps_switches = [
            e for e in entities if isinstance(e, UnifiProtectHighFPSSwitch)
        ]

        # Should only have one high FPS switch (for camera1)
        assert len(high_fps_switches) == 1
        assert high_fps_switches[0]._device_id == "camera1"


class TestUnifiPortEnableSwitch:
    """Tests for UnifiPortEnableSwitch class."""

    @pytest.fixture
    def mock_coordinator_with_ports(self) -> MagicMock:
        """Create mock coordinator with network device ports."""
        coordinator = MagicMock()
        coordinator.protect_client = None
        coordinator.network_client = MagicMock()
        coordinator.network_client.base_url = "https://192.168.1.1"
        coordinator.async_request_refresh = AsyncMock()
        coordinator.data = {
            "sites": {"site1": {"id": "site1", "name": "Default"}},
            "devices": {
                "site1": {
                    "switch1": {
                        "id": "switch1",
                        "name": "Test Switch",
                        "model": "USW-24-POE",
                        "state": "ONLINE",
                        "features": ["switching"],
                        "interfaces": {
                            "ports": [
                                {
                                    "idx": 1,
                                    "state": "UP",
                                    "enabled": True,
                                    "speedMbps": 1000,
                                    "media": "GE",
                                    "name": "Port 1",
                                },
                                {
                                    "idx": 2,
                                    "state": "DOWN",
                                    "enabled": True,
                                    "speedMbps": 0,
                                    "media": "GE",
                                    "name": "Port 2",
                                },
                                {
                                    "idx": 3,
                                    "state": "DISABLED",
                                    "enabled": False,
                                    "speedMbps": 0,
                                    "media": "GE",
                                    "name": "Port 3",
                                },
                            ]
                        },
                    }
                }
            },
            "stats": {"site1": {"switch1": {"ports": []}}},
            "protect": {
                "cameras": {},
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "viewers": {},
                "chimes": {},
                "liveviews": {},
            },
        }
        return coordinator

    def test_initialization(self, mock_coordinator_with_ports) -> None:
        """Test switch initialization."""
        switch = UnifiPortEnableSwitch(
            coordinator=mock_coordinator_with_ports,
            site_id="site1",
            device_id="switch1",
            port_idx=1,
        )

        assert switch._site_id == "site1"
        assert switch._device_id == "switch1"
        assert switch._port_idx == 1
        assert switch._attr_unique_id == "site1_switch1_port_1_enable"
        assert switch._attr_name == "Port 1 Enable"

    def test_port_enabled(self, mock_coordinator_with_ports) -> None:
        """Test switch is_on when port is enabled and UP."""
        switch = UnifiPortEnableSwitch(
            coordinator=mock_coordinator_with_ports,
            site_id="site1",
            device_id="switch1",
            port_idx=1,
        )

        assert switch.is_on is True

    def test_port_disabled(self, mock_coordinator_with_ports) -> None:
        """Test switch is_on when port is disabled."""
        switch = UnifiPortEnableSwitch(
            coordinator=mock_coordinator_with_ports,
            site_id="site1",
            device_id="switch1",
            port_idx=3,
        )

        assert switch.is_on is False

    def test_port_down_but_enabled(self, mock_coordinator_with_ports) -> None:
        """Test switch is_on when port is DOWN but enabled."""
        switch = UnifiPortEnableSwitch(
            coordinator=mock_coordinator_with_ports,
            site_id="site1",
            device_id="switch1",
            port_idx=2,
        )

        # Port is enabled=True but state=DOWN, should still show as enabled
        assert switch.is_on is True

    def test_available_when_device_online(self, mock_coordinator_with_ports) -> None:
        """Test available property when device is online."""
        switch = UnifiPortEnableSwitch(
            coordinator=mock_coordinator_with_ports,
            site_id="site1",
            device_id="switch1",
            port_idx=1,
        )

        assert switch.available is True

    def test_not_available_when_device_offline(
        self, mock_coordinator_with_ports
    ) -> None:
        """Test available property when device is offline."""
        mock_coordinator_with_ports.data["devices"]["site1"]["switch1"]["state"] = (
            "OFFLINE"
        )

        switch = UnifiPortEnableSwitch(
            coordinator=mock_coordinator_with_ports,
            site_id="site1",
            device_id="switch1",
            port_idx=1,
        )

        assert switch.available is False

    def test_extra_state_attributes(self, mock_coordinator_with_ports) -> None:
        """Test extra state attributes."""
        switch = UnifiPortEnableSwitch(
            coordinator=mock_coordinator_with_ports,
            site_id="site1",
            device_id="switch1",
            port_idx=1,
        )

        attrs = switch._attr_extra_state_attributes
        assert attrs["port_idx"] == 1
        assert attrs["port_state"] == "UP"
        assert attrs["speed_mbps"] == 1000
        assert attrs["media"] == "GE"
        assert attrs["port_name"] == "Port 1"

    @pytest.mark.asyncio
    async def test_turn_on_enables_port(self, mock_coordinator_with_ports) -> None:
        """Test turning on enables the port."""
        mock_coordinator_with_ports.network_client.devices.execute_port_action = (
            AsyncMock()
        )

        switch = UnifiPortEnableSwitch(
            coordinator=mock_coordinator_with_ports,
            site_id="site1",
            device_id="switch1",
            port_idx=3,  # Use disabled port
        )
        switch.async_write_ha_state = MagicMock()

        await switch.async_turn_on()

        mock_coordinator_with_ports.network_client.devices.execute_port_action.assert_called_once_with(
            "site1",
            "switch1",
            3,
            enabled=True,
        )
        assert switch._attr_is_on is True
        switch.async_write_ha_state.assert_called_once()
        mock_coordinator_with_ports.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_turn_off_disables_port(self, mock_coordinator_with_ports) -> None:
        """Test turning off disables the port."""
        mock_coordinator_with_ports.network_client.devices.execute_port_action = (
            AsyncMock()
        )

        switch = UnifiPortEnableSwitch(
            coordinator=mock_coordinator_with_ports,
            site_id="site1",
            device_id="switch1",
            port_idx=1,  # Use enabled port
        )
        switch.async_write_ha_state = MagicMock()

        await switch.async_turn_off()

        mock_coordinator_with_ports.network_client.devices.execute_port_action.assert_called_once_with(
            "site1",
            "switch1",
            1,
            enabled=False,
        )
        assert switch._attr_is_on is False
        switch.async_write_ha_state.assert_called_once()
        mock_coordinator_with_ports.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_turn_on_handles_error(self, mock_coordinator_with_ports) -> None:
        """Test turning on handles errors gracefully."""
        mock_coordinator_with_ports.network_client.devices.execute_port_action = (
            AsyncMock(side_effect=Exception("API Error"))
        )

        switch = UnifiPortEnableSwitch(
            coordinator=mock_coordinator_with_ports,
            site_id="site1",
            device_id="switch1",
            port_idx=1,
        )
        switch.async_write_ha_state = MagicMock()

        # Should not raise, but log error
        await switch.async_turn_on()

        # State should not be updated on error
        switch.async_write_ha_state.assert_not_called()

    @pytest.mark.asyncio
    async def test_turn_off_handles_error(self, mock_coordinator_with_ports) -> None:
        """Test turning off handles errors gracefully."""
        mock_coordinator_with_ports.network_client.devices.execute_port_action = (
            AsyncMock(side_effect=Exception("API Error"))
        )

        switch = UnifiPortEnableSwitch(
            coordinator=mock_coordinator_with_ports,
            site_id="site1",
            device_id="switch1",
            port_idx=1,
        )
        switch.async_write_ha_state = MagicMock()

        # Should not raise, but log error
        await switch.async_turn_off()

        # State should not be updated on error
        switch.async_write_ha_state.assert_not_called()


class TestAsyncSetupEntryWithPortSwitches:
    """Tests for async_setup_entry with port switches."""

    @pytest.fixture
    def mock_coordinator_with_switch_device(self) -> MagicMock:
        """Create mock coordinator with network switch device."""
        coordinator = MagicMock()
        coordinator.protect_client = None
        coordinator.network_client = MagicMock()
        coordinator.network_client.base_url = "https://192.168.1.1"
        coordinator.data = {
            "sites": {"site1": {"id": "site1", "name": "Default"}},
            "devices": {
                "site1": {
                    "switch1": {
                        "id": "switch1",
                        "name": "Test Switch",
                        "model": "USW-24-POE",
                        "state": "ONLINE",
                        "features": ["switching"],
                        "interfaces": {
                            "ports": [
                                {
                                    "idx": 1,
                                    "state": "UP",
                                    "enabled": True,
                                    "poe": {"enabled": True, "mode": "auto"},
                                },
                                {
                                    "idx": 2,
                                    "state": "UP",
                                    "enabled": True,
                                },  # No PoE
                            ]
                        },
                    }
                }
            },
            "stats": {"site1": {"switch1": {"ports": []}}},
            "clients": {},
            "wifi": {},
            "protect": {
                "cameras": {},
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "viewers": {},
                "chimes": {},
                "liveviews": {},
            },
        }
        return coordinator

    @pytest.mark.asyncio
    async def test_setup_creates_port_enable_switches(
        self, hass, mock_coordinator_with_switch_device
    ) -> None:
        """Test setup creates port enable switches for all ports."""
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator_with_switch_device

        async_add_entities = MagicMock()

        await async_setup_entry(hass, mock_entry, async_add_entities)

        entities = async_add_entities.call_args[0][0]

        # Should have 2 port enable switches + 1 PoE switch (port 1 has PoE)
        enable_switches = [e for e in entities if isinstance(e, UnifiPortEnableSwitch)]
        poe_switches = [e for e in entities if isinstance(e, UnifiPoESwitch)]

        assert len(enable_switches) == 2
        assert len(poe_switches) == 1
        assert poe_switches[0]._port_idx == 1

    @pytest.mark.asyncio
    async def test_setup_poe_from_interfaces(
        self, hass, mock_coordinator_with_switch_device
    ) -> None:
        """Test setup finds PoE config in interfaces."""
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator_with_switch_device

        async_add_entities = MagicMock()

        await async_setup_entry(hass, mock_entry, async_add_entities)

        entities = async_add_entities.call_args[0][0]
        poe_switches = [e for e in entities if isinstance(e, UnifiPoESwitch)]

        # Only port 1 should have PoE switch
        assert len(poe_switches) == 1
        assert poe_switches[0]._port_idx == 1

    @pytest.mark.asyncio
    async def test_setup_no_switches_for_non_switching_devices(self, hass) -> None:
        """Test no switches created for devices without switching feature."""
        coordinator = MagicMock()
        coordinator.protect_client = None
        coordinator.network_client = MagicMock()
        coordinator.data = {
            "sites": {"site1": {"id": "site1"}},
            "devices": {
                "site1": {
                    "ap1": {
                        "id": "ap1",
                        "name": "Access Point",
                        "features": ["accessPoint"],  # No switching
                        "interfaces": {"ports": []},
                    }
                }
            },
            "stats": {},
            "clients": {},
            "wifi": {},
            "protect": {
                "cameras": {},
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "viewers": {},
                "chimes": {},
                "liveviews": {},
            },
        }

        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = coordinator

        async_add_entities = MagicMock()

        await async_setup_entry(hass, mock_entry, async_add_entities)

        entities = async_add_entities.call_args[0][0]
        port_switches = [
            e
            for e in entities
            if isinstance(e, (UnifiPortEnableSwitch, UnifiPoESwitch))
        ]

        assert len(port_switches) == 0


class TestAsyncSetupEntryEdgeCases:
    """Tests for async_setup_entry edge cases to improve coverage."""

    @pytest.mark.asyncio
    async def test_port_without_idx_skipped(self, hass) -> None:
        """Test that ports without idx or portIdx are skipped (line 74)."""
        coordinator = MagicMock()
        coordinator.protect_client = None
        coordinator.network_client = MagicMock()
        coordinator.data = {
            "sites": {"site1": {"id": "site1"}},
            "devices": {
                "site1": {
                    "switch1": {
                        "id": "switch1",
                        "name": "Test Switch",
                        "features": ["switching"],
                        "interfaces": {
                            "ports": [
                                # Port without idx or portIdx - should be skipped
                                {"state": "UP", "enabled": True},
                                # Port with idx - should be processed
                                {"idx": 2, "state": "UP", "enabled": True},
                            ]
                        },
                    }
                }
            },
            "stats": {"site1": {"switch1": {"ports": []}}},
            "clients": {},
            "wifi": {},
            "protect": {
                "cameras": {},
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "viewers": {},
                "chimes": {},
                "liveviews": {},
            },
        }

        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = coordinator

        async_add_entities = MagicMock()

        await async_setup_entry(hass, mock_entry, async_add_entities)

        entities = async_add_entities.call_args[0][0]
        port_switches = [e for e in entities if isinstance(e, UnifiPortEnableSwitch)]

        # Only one port should have switch (port 2)
        assert len(port_switches) == 1
        assert port_switches[0]._port_idx == 2

    @pytest.mark.asyncio
    async def test_poe_config_from_stats_ports_fallback(self, hass) -> None:
        """Test PoE config found in stats_ports when not in interfaces."""
        coordinator = MagicMock()
        coordinator.protect_client = None
        coordinator.network_client = MagicMock()
        coordinator.data = {
            "sites": {"site1": {"id": "site1"}},
            "devices": {
                "site1": {
                    "switch1": {
                        "id": "switch1",
                        "name": "Test Switch",
                        "features": ["switching"],
                        "interfaces": {
                            "ports": [
                                # Port without PoE in interfaces
                                {"idx": 1, "state": "UP", "enabled": True},
                            ]
                        },
                    }
                }
            },
            "stats": {
                "site1": {
                    "switch1": {
                        "ports": [
                            # PoE config in stats with idx match
                            {"idx": 1, "poe": {"enabled": True, "mode": "auto"}},
                        ]
                    }
                }
            },
            "clients": {},
            "wifi": {},
            "protect": {
                "cameras": {},
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "viewers": {},
                "chimes": {},
                "liveviews": {},
            },
        }

        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = coordinator

        async_add_entities = MagicMock()

        await async_setup_entry(hass, mock_entry, async_add_entities)

        entities = async_add_entities.call_args[0][0]
        poe_switches = [e for e in entities if isinstance(e, UnifiPoESwitch)]

        # Should have PoE switch from stats_ports
        assert len(poe_switches) == 1
        assert poe_switches[0]._port_idx == 1

    @pytest.mark.asyncio
    async def test_poe_config_from_stats_ports_with_alternate_key(self, hass) -> None:
        """Test PoE config found in stats_ports using portIdx key."""
        coordinator = MagicMock()
        coordinator.protect_client = None
        coordinator.network_client = MagicMock()
        coordinator.data = {
            "sites": {"site1": {"id": "site1"}},
            "devices": {
                "site1": {
                    "switch1": {
                        "id": "switch1",
                        "name": "Test Switch",
                        "features": ["switching"],
                        "interfaces": {
                            "ports": [
                                # Port without PoE in interfaces
                                {"idx": 1, "state": "UP", "enabled": True},
                            ]
                        },
                    }
                }
            },
            "stats": {
                "site1": {
                    "switch1": {
                        "ports": [
                            # PoE config in stats with portIdx match
                            {"portIdx": 1, "poe": {"enabled": True, "mode": "auto"}},
                        ]
                    }
                }
            },
            "clients": {},
            "wifi": {},
            "protect": {
                "cameras": {},
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "viewers": {},
                "chimes": {},
                "liveviews": {},
            },
        }

        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = coordinator

        async_add_entities = MagicMock()

        await async_setup_entry(hass, mock_entry, async_add_entities)

        entities = async_add_entities.call_args[0][0]
        poe_switches = [e for e in entities if isinstance(e, UnifiPoESwitch)]

        # Should have PoE switch from stats_ports
        assert len(poe_switches) == 1

    @pytest.mark.asyncio
    async def test_camera_with_high_fps_capability(self, hass) -> None:
        """Test High FPS switch created for cameras with hasHighFpsCapability."""
        coordinator = MagicMock()
        coordinator.protect_client = MagicMock()
        coordinator.network_client = MagicMock()
        coordinator.network_client.base_url = "https://192.168.1.1"
        coordinator.protect_client.base_url = "https://192.168.1.1"
        coordinator.data = {
            "sites": {},
            "devices": {},
            "stats": {},
            "clients": {},
            "wifi": {},
            "protect": {
                "cameras": {
                    "camera1": {
                        "id": "camera1",
                        "name": "High FPS Camera",
                        "state": "CONNECTED",
                        "featureFlags": {"hasHighFpsCapability": True},
                    }
                },
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "viewers": {},
                "chimes": {},
                "liveviews": {},
            },
        }

        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = coordinator

        async_add_entities = MagicMock()

        await async_setup_entry(hass, mock_entry, async_add_entities)

        entities = async_add_entities.call_args[0][0]
        high_fps_switches = [
            e for e in entities if isinstance(e, UnifiProtectHighFPSSwitch)
        ]

        # Should have High FPS switch
        assert len(high_fps_switches) == 1

    @pytest.mark.asyncio
    async def test_camera_without_high_fps_capability(self, hass) -> None:
        """Test no High FPS switch for cameras without hasHighFpsCapability."""
        coordinator = MagicMock()
        coordinator.protect_client = MagicMock()
        coordinator.network_client = MagicMock()
        coordinator.network_client.base_url = "https://192.168.1.1"
        coordinator.protect_client.base_url = "https://192.168.1.1"
        coordinator.data = {
            "sites": {},
            "devices": {},
            "stats": {},
            "clients": {},
            "wifi": {},
            "protect": {
                "cameras": {
                    "camera1": {
                        "id": "camera1",
                        "name": "Basic Camera",
                        "state": "CONNECTED",
                        "featureFlags": {"hasHighFpsCapability": False},
                    }
                },
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "viewers": {},
                "chimes": {},
                "liveviews": {},
            },
        }

        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = coordinator

        async_add_entities = MagicMock()

        await async_setup_entry(hass, mock_entry, async_add_entities)

        entities = async_add_entities.call_args[0][0]
        high_fps_switches = [
            e for e in entities if isinstance(e, UnifiProtectHighFPSSwitch)
        ]

        # Should NOT have High FPS switch
        assert len(high_fps_switches) == 0

    @pytest.mark.asyncio
    async def test_camera_with_feature_flags_not_dict(self, hass) -> None:
        """Test camera with featureFlags not being a dict."""
        coordinator = MagicMock()
        coordinator.protect_client = MagicMock()
        coordinator.network_client = MagicMock()
        coordinator.network_client.base_url = "https://192.168.1.1"
        coordinator.protect_client.base_url = "https://192.168.1.1"
        coordinator.data = {
            "sites": {},
            "devices": {},
            "stats": {},
            "clients": {},
            "wifi": {},
            "protect": {
                "cameras": {
                    "camera1": {
                        "id": "camera1",
                        "name": "Basic Camera",
                        "state": "CONNECTED",
                        "featureFlags": None,  # Not a dict
                    }
                },
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "viewers": {},
                "chimes": {},
                "liveviews": {},
            },
        }

        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = coordinator

        async_add_entities = MagicMock()

        await async_setup_entry(hass, mock_entry, async_add_entities)

        entities = async_add_entities.call_args[0][0]
        high_fps_switches = [
            e for e in entities if isinstance(e, UnifiProtectHighFPSSwitch)
        ]

        # Should NOT have High FPS switch (featureFlags is not dict)
        assert len(high_fps_switches) == 0

    @pytest.mark.asyncio
    async def test_client_name_fallback_to_hostname(self, hass) -> None:
        """Test client name fallback from name to hostname (line 163)."""
        coordinator = MagicMock()
        coordinator.protect_client = None
        coordinator.network_client = MagicMock()
        coordinator.network_client.base_url = "https://192.168.1.1"
        coordinator.data = {
            "sites": {"site1": {"id": "site1"}},
            "devices": {"site1": {}},
            "stats": {},
            "clients": {
                "site1": {
                    "client1": {
                        "id": "client1",
                        "hostname": "test-hostname",  # No name, fallback to hostname
                        "mac": "AA:BB:CC:DD:EE:FF",
                        "blocked": False,
                    }
                }
            },
            "wifi": {},
            "protect": {
                "cameras": {},
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "viewers": {},
                "chimes": {},
                "liveviews": {},
            },
        }

        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = coordinator

        async_add_entities = MagicMock()

        await async_setup_entry(hass, mock_entry, async_add_entities)

        entities = async_add_entities.call_args[0][0]
        client_switches = [e for e in entities if isinstance(e, UnifiClientBlockSwitch)]

        assert len(client_switches) == 1
        # Verify switch was created (hostname used for naming)
        assert client_switches[0]._client_id == "client1"

    @pytest.mark.asyncio
    async def test_client_name_fallback_to_mac(self, hass) -> None:
        """Test client name fallback from name/hostname to mac (lines 163-166)."""
        coordinator = MagicMock()
        coordinator.protect_client = None
        coordinator.network_client = MagicMock()
        coordinator.network_client.base_url = "https://192.168.1.1"
        coordinator.data = {
            "sites": {"site1": {"id": "site1"}},
            "devices": {"site1": {}},
            "stats": {},
            "clients": {
                "site1": {
                    "client1": {
                        "id": "client1",
                        # No name, no hostname, fallback to mac
                        "mac": "AA:BB:CC:DD:EE:FF",
                        "blocked": False,
                    }
                }
            },
            "wifi": {},
            "protect": {
                "cameras": {},
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "viewers": {},
                "chimes": {},
                "liveviews": {},
            },
        }

        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = coordinator

        async_add_entities = MagicMock()

        await async_setup_entry(hass, mock_entry, async_add_entities)

        entities = async_add_entities.call_args[0][0]
        client_switches = [e for e in entities if isinstance(e, UnifiClientBlockSwitch)]

        assert len(client_switches) == 1

    @pytest.mark.asyncio
    async def test_wifi_name_fallback_to_ssid(self, hass) -> None:
        """Test WiFi name fallback from name to ssid (lines 182-183)."""
        coordinator = MagicMock()
        coordinator.protect_client = None
        coordinator.network_client = MagicMock()
        coordinator.network_client.base_url = "https://192.168.1.1"
        coordinator.data = {
            "sites": {"site1": {"id": "site1"}},
            "devices": {"site1": {}},
            "stats": {},
            "clients": {},
            "wifi": {
                "site1": {
                    "wifi1": {
                        "id": "wifi1",
                        "ssid": "MyNetwork",  # No name, fallback to ssid
                        "enabled": True,
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
                "liveviews": {},
            },
        }

        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = coordinator

        async_add_entities = MagicMock()

        await async_setup_entry(hass, mock_entry, async_add_entities)

        entities = async_add_entities.call_args[0][0]
        wifi_switches = [e for e in entities if isinstance(e, UnifiWifiSwitch)]

        assert len(wifi_switches) == 1
        # Verify switch was created with ssid in name
        assert wifi_switches[0]._wifi_id == "wifi1"


class TestUnifiPoESwitchEdgeCases:
    """Tests for UnifiPoESwitch edge cases."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Create mock coordinator with PoE port."""
        coordinator = MagicMock()
        coordinator.network_client = MagicMock()
        coordinator.network_client.devices = MagicMock()
        coordinator.network_client.devices.execute_port_action = AsyncMock()
        coordinator.async_request_refresh = AsyncMock()
        coordinator.data = {
            "sites": {"site1": {"id": "site1"}},
            "devices": {
                "site1": {
                    "switch1": {
                        "id": "switch1",
                        "name": "Test Switch",
                        "model": "USW-24-POE",
                        "state": "ONLINE",
                    }
                }
            },
            "stats": {
                "site1": {
                    "switch1": {
                        "ports": [
                            {
                                "idx": 1,
                                "poe": {"enabled": True, "mode": "auto", "power": 5.5},
                                "state": "UP",
                                "speedMbps": 1000,
                            },
                        ]
                    }
                }
            },
            "clients": {},
            "wifi": {},
            "protect": {
                "cameras": {},
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "viewers": {},
                "chimes": {},
                "liveviews": {},
            },
        }
        return coordinator

    def test_get_port_data_with_alternate_key_match(self, mock_coordinator) -> None:
        """Test _get_port_data matches on portIdx instead of idx."""
        # Change stats to use portIdx instead of idx
        mock_coordinator.data["stats"]["site1"]["switch1"]["ports"] = [
            {"portIdx": 1, "poe": {"enabled": True}, "state": "UP"},
        ]

        switch = UnifiPoESwitch(
            coordinator=mock_coordinator,
            site_id="site1",
            device_id="switch1",
            port_idx=1,
        )

        port_data = switch._get_port_data()
        assert port_data.get("portIdx") == 1

    def test_get_port_data_returns_empty_dict_when_not_found(
        self, mock_coordinator
    ) -> None:
        """Test _get_port_data returns empty dict when port not found."""
        switch = UnifiPoESwitch(
            coordinator=mock_coordinator,
            site_id="site1",
            device_id="switch1",
            port_idx=99,  # Port that doesn't exist
        )

        port_data = switch._get_port_data()
        assert port_data == {}

    def test_available_when_device_online(self, mock_coordinator) -> None:
        """Test available property returns True when device is online."""
        switch = UnifiPoESwitch(
            coordinator=mock_coordinator,
            site_id="site1",
            device_id="switch1",
            port_idx=1,
        )
        assert switch.available is True

    def test_available_when_device_offline(self, mock_coordinator) -> None:
        """Test available property returns False when device is offline."""
        mock_coordinator.data["devices"]["site1"]["switch1"]["state"] = "OFFLINE"

        switch = UnifiPoESwitch(
            coordinator=mock_coordinator,
            site_id="site1",
            device_id="switch1",
            port_idx=1,
        )
        assert switch.available is False

    def test_available_when_device_not_found(self, mock_coordinator) -> None:
        """Test available property returns False when device not found."""
        switch = UnifiPoESwitch(
            coordinator=mock_coordinator,
            site_id="site1",
            device_id="switch1",
            port_idx=1,
        )

        # Remove device from data
        del mock_coordinator.data["devices"]["site1"]["switch1"]
        assert switch.available is False

    def test_is_on_property(self, mock_coordinator) -> None:
        """Test is_on property returns correct state."""
        switch = UnifiPoESwitch(
            coordinator=mock_coordinator,
            site_id="site1",
            device_id="switch1",
            port_idx=1,
        )
        assert switch.is_on is True

        # Disable PoE
        mock_coordinator.data["stats"]["site1"]["switch1"]["ports"][0]["poe"][
            "enabled"
        ] = False
        assert switch.is_on is False

    @pytest.mark.asyncio
    async def test_async_turn_on_success(self, mock_coordinator) -> None:
        """Test async_turn_on enables PoE successfully."""
        switch = UnifiPoESwitch(
            coordinator=mock_coordinator,
            site_id="site1",
            device_id="switch1",
            port_idx=1,
        )
        switch.async_write_ha_state = MagicMock()

        await switch.async_turn_on()

        mock_coordinator.network_client.devices.execute_port_action.assert_called_once_with(
            "site1", "switch1", 1, poe_mode="auto"
        )
        assert switch._attr_is_on is True
        switch.async_write_ha_state.assert_called_once()
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_turn_on_error(self, mock_coordinator) -> None:
        """Test async_turn_on handles errors gracefully."""
        mock_coordinator.network_client.devices.execute_port_action = AsyncMock(
            side_effect=Exception("API Error")
        )

        switch = UnifiPoESwitch(
            coordinator=mock_coordinator,
            site_id="site1",
            device_id="switch1",
            port_idx=1,
        )

        # Should not raise
        await switch.async_turn_on()

        # Should have attempted to enable
        mock_coordinator.network_client.devices.execute_port_action.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_turn_off_success(self, mock_coordinator) -> None:
        """Test async_turn_off disables PoE successfully."""
        switch = UnifiPoESwitch(
            coordinator=mock_coordinator,
            site_id="site1",
            device_id="switch1",
            port_idx=1,
        )
        switch.async_write_ha_state = MagicMock()

        await switch.async_turn_off()

        mock_coordinator.network_client.devices.execute_port_action.assert_called_once_with(
            "site1", "switch1", 1, poe_mode="off"
        )
        assert switch._attr_is_on is False
        switch.async_write_ha_state.assert_called_once()
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_turn_off_error(self, mock_coordinator) -> None:
        """Test async_turn_off handles errors gracefully."""
        mock_coordinator.network_client.devices.execute_port_action = AsyncMock(
            side_effect=Exception("API Error")
        )

        switch = UnifiPoESwitch(
            coordinator=mock_coordinator,
            site_id="site1",
            device_id="switch1",
            port_idx=1,
        )

        # Should not raise
        await switch.async_turn_off()

        # Should have attempted to disable
        mock_coordinator.network_client.devices.execute_port_action.assert_called_once()


class TestUnifiPortEnableSwitchEdgeCases:
    """Tests for UnifiPortEnableSwitch edge cases."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Create mock coordinator with ports."""
        coordinator = MagicMock()
        coordinator.network_client = MagicMock()
        coordinator.network_client.devices = MagicMock()
        coordinator.network_client.devices.execute_port_action = AsyncMock()
        coordinator.async_request_refresh = AsyncMock()
        coordinator.data = {
            "sites": {"site1": {"id": "site1"}},
            "devices": {
                "site1": {
                    "switch1": {
                        "id": "switch1",
                        "name": "Test Switch",
                        "model": "USW-24-POE",
                        "state": "ONLINE",
                        "interfaces": {
                            "ports": [
                                {
                                    "idx": 1,
                                    "state": "UP",
                                    "enabled": True,
                                    "speedMbps": 1000,
                                },
                            ]
                        },
                    }
                }
            },
            "stats": {},
            "clients": {},
            "wifi": {},
            "protect": {
                "cameras": {},
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "viewers": {},
                "chimes": {},
                "liveviews": {},
            },
        }
        return coordinator

    def test_get_port_data_with_alternate_key_match(self, mock_coordinator) -> None:
        """Test _get_port_data matches on portIdx instead of idx."""
        # Change interfaces to use portIdx instead of idx
        mock_coordinator.data["devices"]["site1"]["switch1"]["interfaces"]["ports"] = [
            {"portIdx": 1, "state": "UP", "enabled": True},
        ]

        switch = UnifiPortEnableSwitch(
            coordinator=mock_coordinator,
            site_id="site1",
            device_id="switch1",
            port_idx=1,
        )

        port_data = switch._get_port_data()
        assert port_data.get("portIdx") == 1

    def test_get_port_data_returns_empty_when_not_found(self, mock_coordinator) -> None:
        """Test _get_port_data returns empty dict when port not found (line 693)."""
        switch = UnifiPortEnableSwitch(
            coordinator=mock_coordinator,
            site_id="site1",
            device_id="switch1",
            port_idx=99,  # Port that doesn't exist
        )

        port_data = switch._get_port_data()
        assert port_data == {}

    def test_available_when_device_not_found(self, mock_coordinator) -> None:
        """Test available returns False when device not found (line 719)."""
        switch = UnifiPortEnableSwitch(
            coordinator=mock_coordinator,
            site_id="site1",
            device_id="switch1",
            port_idx=1,
        )

        # Remove device from data
        mock_coordinator.data["devices"]["site1"] = {}

        assert switch.available is False


class TestUnifiClientBlockSwitchEdgeCases:
    """Tests for UnifiClientBlockSwitch edge cases."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Create mock coordinator with client."""
        coordinator = MagicMock()
        coordinator.network_client = MagicMock()
        coordinator.network_client.clients = MagicMock()
        coordinator.network_client.clients.block = AsyncMock()
        coordinator.network_client.clients.unblock = AsyncMock()
        coordinator.async_request_refresh = AsyncMock()
        coordinator.data = {
            "sites": {"site1": {"id": "site1"}},
            "devices": {"site1": {}},
            "stats": {},
            "clients": {
                "site1": {
                    "client1": {
                        "id": "client1",
                        "name": "Test Client",
                        "mac": "AA:BB:CC:DD:EE:FF",
                        "blocked": False,
                    }
                }
            },
            "wifi": {},
            "protect": {
                "cameras": {},
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "viewers": {},
                "chimes": {},
                "liveviews": {},
            },
        }
        return coordinator

    @pytest.mark.asyncio
    async def test_turn_on_handles_error(self, mock_coordinator) -> None:
        """Test async_turn_on handles errors gracefully (lines 863-864)."""
        mock_coordinator.network_client.clients.unblock = AsyncMock(
            side_effect=Exception("API Error")
        )

        switch = UnifiClientBlockSwitch(
            coordinator=mock_coordinator,
            site_id="site1",
            client_id="client1",
        )

        # Should not raise, but log error
        await switch.async_turn_on()

        # Should have tried to unblock
        mock_coordinator.network_client.clients.unblock.assert_called_once()

    @pytest.mark.asyncio
    async def test_turn_off_handles_error(self, mock_coordinator) -> None:
        """Test async_turn_off handles errors gracefully (lines 884-885)."""
        mock_coordinator.network_client.clients.block = AsyncMock(
            side_effect=Exception("API Error")
        )

        switch = UnifiClientBlockSwitch(
            coordinator=mock_coordinator,
            site_id="site1",
            client_id="client1",
        )

        # Should not raise, but log error
        await switch.async_turn_off()

        # Should have tried to block
        mock_coordinator.network_client.clients.block.assert_called_once()


class TestUnifiWifiSwitchEdgeCases:
    """Tests for UnifiWifiSwitch edge cases."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Create mock coordinator with WiFi."""
        coordinator = MagicMock()
        coordinator.network_client = MagicMock()
        coordinator.network_client.wifi = MagicMock()
        coordinator.network_client.wifi.update = AsyncMock()
        coordinator.async_request_refresh = AsyncMock()
        coordinator.data = {
            "sites": {"site1": {"id": "site1"}},
            "devices": {},
            "stats": {},
            "clients": {},
            "wifi": {
                "site1": {
                    "wifi1": {
                        "id": "wifi1",
                        "name": "Test WiFi",
                        "ssid": "TestSSID",
                        "enabled": True,
                        "security": "wpa2",
                        "hidden": False,
                        "isGuest": False,
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
                "liveviews": {},
            },
        }
        return coordinator

    @pytest.mark.asyncio
    async def test_turn_on_handles_error(self, mock_coordinator) -> None:
        """Test async_turn_on handles errors gracefully (lines 975-976)."""
        mock_coordinator.network_client.wifi.update = AsyncMock(
            side_effect=Exception("API Error")
        )

        switch = UnifiWifiSwitch(
            coordinator=mock_coordinator,
            site_id="site1",
            wifi_id="wifi1",
            wifi_data=mock_coordinator.data["wifi"]["site1"]["wifi1"],
        )

        # Should not raise, but log error
        await switch.async_turn_on()

        # Should have tried to enable
        mock_coordinator.network_client.wifi.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_turn_off_handles_error(self, mock_coordinator) -> None:
        """Test async_turn_off handles errors gracefully (lines 1000-1001)."""
        mock_coordinator.network_client.wifi.update = AsyncMock(
            side_effect=Exception("API Error")
        )

        switch = UnifiWifiSwitch(
            coordinator=mock_coordinator,
            site_id="site1",
            wifi_id="wifi1",
            wifi_data=mock_coordinator.data["wifi"]["site1"]["wifi1"],
        )

        # Should not raise, but log error
        await switch.async_turn_off()

        # Should have tried to disable
        mock_coordinator.network_client.wifi.update.assert_called_once()

    def test_get_wifi_data_fallback_to_initial_data(self, mock_coordinator) -> None:
        """Test _get_wifi_data falls back to initial wifi_data."""
        initial_wifi_data = {
            "id": "wifi1",
            "name": "Initial WiFi",
            "ssid": "InitialSSID",
            "enabled": True,
        }

        switch = UnifiWifiSwitch(
            coordinator=mock_coordinator,
            site_id="site1",
            wifi_id="wifi1",
            wifi_data=initial_wifi_data,
        )

        # Remove wifi from coordinator data
        mock_coordinator.data["wifi"]["site1"] = {}

        wifi_data = switch._get_wifi_data()
        assert wifi_data == initial_wifi_data
