"""Tests for UniFi Protect light platform."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.components.light import ATTR_BRIGHTNESS, ColorMode

from custom_components.unifi_insights.const import (
    ATTR_LIGHT_DARK,
    ATTR_LIGHT_ID,
    ATTR_LIGHT_LEVEL,
    ATTR_LIGHT_MODE,
    ATTR_LIGHT_MOTION,
    ATTR_LIGHT_NAME,
    ATTR_LIGHT_STATE,
    DEVICE_TYPE_LIGHT,
    LIGHT_MODE_ALWAYS,
    LIGHT_MODE_OFF,
)
from custom_components.unifi_insights.light import (
    PARALLEL_UPDATES,
    UnifiProtectLight,
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
        """Test setup when Protect API is not available."""
        mock_coordinator.protect_client = None

        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        async_add_entities = MagicMock()

        await async_setup_entry(hass, mock_entry, async_add_entities)

        # Should not add any entities when Protect is not available
        async_add_entities.assert_not_called()

    @pytest.mark.asyncio
    async def test_setup_entry_with_lights(self, hass, mock_coordinator) -> None:
        """Test setup with lights present."""
        mock_coordinator.data["protect"]["lights"] = {
            "light1": {
                "id": "light1",
                "name": "Test Light",
                "state": "CONNECTED",
                "lightModeSettings": {"mode": "motion"},
                "lightDeviceSettings": {"ledLevel": 75},
            }
        }

        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        async_add_entities = MagicMock()

        await async_setup_entry(hass, mock_entry, async_add_entities)

        # Should add one light entity
        async_add_entities.assert_called_once()
        entities = async_add_entities.call_args[0][0]
        assert len(entities) == 1
        assert isinstance(entities[0], UnifiProtectLight)

    @pytest.mark.asyncio
    async def test_setup_entry_with_multiple_lights(
        self, hass, mock_coordinator
    ) -> None:
        """Test setup with multiple lights."""
        mock_coordinator.data["protect"]["lights"] = {
            "light1": {"id": "light1", "name": "Front Light", "state": "CONNECTED"},
            "light2": {"id": "light2", "name": "Back Light", "state": "CONNECTED"},
            "light3": {"id": "light3", "name": "Side Light", "state": "DISCONNECTED"},
        }

        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        async_add_entities = MagicMock()

        await async_setup_entry(hass, mock_entry, async_add_entities)

        entities = async_add_entities.call_args[0][0]
        assert len(entities) == 3


class TestUnifiProtectLight:
    """Tests for UnifiProtectLight entity."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Create mock coordinator."""
        coordinator = MagicMock()
        coordinator.protect_client = MagicMock()
        coordinator.protect_client.base_url = "https://192.168.1.1"
        coordinator.protect_client.set_light_mode = AsyncMock()
        coordinator.protect_client.set_light_brightness = AsyncMock()
        coordinator.network_client = MagicMock()
        coordinator.network_client.base_url = "https://192.168.1.1"
        coordinator.data = {
            "sites": {},
            "devices": {},
            "protect": {
                "cameras": {},
                "lights": {
                    "light1": {
                        "id": "light1",
                        "name": "Test Light",
                        "state": "CONNECTED",
                        "mac": "AA:BB:CC:DD:EE:FF",
                        "type": "UP-Floodlight",
                        "firmwareVersion": "1.0.0",
                        "lightModeSettings": {"mode": "motion"},
                        "lightDeviceSettings": {"ledLevel": 75},
                        "lastMotion": 1234567890,
                        "isDark": True,
                    }
                },
                "sensors": {},
                "nvrs": {},
                "viewers": {},
                "chimes": {},
                "liveviews": {},
            },
        }
        return coordinator

    def test_initialization(self, mock_coordinator) -> None:
        """Test light entity initialization."""
        light = UnifiProtectLight(
            coordinator=mock_coordinator,
            light_id="light1",
        )

        assert light._device_id == "light1"
        assert light._device_type == DEVICE_TYPE_LIGHT
        assert light._attr_has_entity_name is True
        assert light._attr_name is None
        assert light._attr_color_mode == ColorMode.BRIGHTNESS
        assert ColorMode.BRIGHTNESS in light._attr_supported_color_modes
        assert light._attr_entity_category is None

    def test_update_from_data_connected(self, mock_coordinator) -> None:
        """Test _update_from_data with connected light."""
        light = UnifiProtectLight(
            coordinator=mock_coordinator,
            light_id="light1",
        )

        assert light._attr_available is True
        assert light._attr_is_on is True  # mode is "motion", not OFF
        assert light._attr_brightness == int(75 * 255 / 100)  # 191

    def test_update_from_data_off_mode(self, mock_coordinator) -> None:
        """Test _update_from_data with light in OFF mode."""
        mock_coordinator.data["protect"]["lights"]["light1"]["lightModeSettings"] = {
            "mode": LIGHT_MODE_OFF
        }

        light = UnifiProtectLight(
            coordinator=mock_coordinator,
            light_id="light1",
        )

        assert light._attr_is_on is False

    def test_update_from_data_always_on_mode(self, mock_coordinator) -> None:
        """Test _update_from_data with light in always-on mode."""
        mock_coordinator.data["protect"]["lights"]["light1"]["lightModeSettings"] = {
            "mode": LIGHT_MODE_ALWAYS
        }

        light = UnifiProtectLight(
            coordinator=mock_coordinator,
            light_id="light1",
        )

        assert light._attr_is_on is True

    def test_update_from_data_disconnected(self, mock_coordinator) -> None:
        """Test _update_from_data with disconnected light."""
        mock_coordinator.data["protect"]["lights"]["light1"]["state"] = "DISCONNECTED"

        light = UnifiProtectLight(
            coordinator=mock_coordinator,
            light_id="light1",
        )

        assert light._attr_available is False

    def test_extra_state_attributes(self, mock_coordinator) -> None:
        """Test extra state attributes."""
        light = UnifiProtectLight(
            coordinator=mock_coordinator,
            light_id="light1",
        )

        attrs = light._attr_extra_state_attributes
        assert attrs[ATTR_LIGHT_ID] == "light1"
        assert attrs[ATTR_LIGHT_NAME] == "Test Light"
        assert attrs[ATTR_LIGHT_STATE] == "CONNECTED"
        assert attrs[ATTR_LIGHT_MODE] == "motion"
        assert attrs[ATTR_LIGHT_LEVEL] == 75
        assert attrs[ATTR_LIGHT_MOTION] == 1234567890
        assert attrs[ATTR_LIGHT_DARK] is True

    def test_brightness_calculation(self, mock_coordinator) -> None:
        """Test brightness value calculation from LED level."""
        # Test 100% brightness
        mock_coordinator.data["protect"]["lights"]["light1"]["lightDeviceSettings"][
            "ledLevel"
        ] = 100
        light = UnifiProtectLight(
            coordinator=mock_coordinator,
            light_id="light1",
        )
        assert light._attr_brightness == 255

        # Test 0% brightness
        mock_coordinator.data["protect"]["lights"]["light1"]["lightDeviceSettings"][
            "ledLevel"
        ] = 0
        light._update_from_data()
        assert light._attr_brightness == 0

        # Test 50% brightness
        mock_coordinator.data["protect"]["lights"]["light1"]["lightDeviceSettings"][
            "ledLevel"
        ] = 50
        light._update_from_data()
        assert light._attr_brightness == 127

    def test_default_led_level(self, mock_coordinator) -> None:
        """Test default LED level when not provided."""
        mock_coordinator.data["protect"]["lights"]["light1"]["lightDeviceSettings"] = {}

        light = UnifiProtectLight(
            coordinator=mock_coordinator,
            light_id="light1",
        )

        # Default is 100 when not provided
        assert light._attr_brightness == 255

    @pytest.mark.asyncio
    async def test_async_turn_on(self, mock_coordinator) -> None:
        """Test turning light on."""
        light = UnifiProtectLight(
            coordinator=mock_coordinator,
            light_id="light1",
        )
        light.async_write_ha_state = MagicMock()

        await light.async_turn_on()

        mock_coordinator.protect_client.set_light_mode.assert_called_once_with(
            light_id="light1",
            mode=LIGHT_MODE_ALWAYS,
        )
        assert light._attr_is_on is True
        light.async_write_ha_state.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_turn_on_with_brightness(self, mock_coordinator) -> None:
        """Test turning light on with specific brightness."""
        light = UnifiProtectLight(
            coordinator=mock_coordinator,
            light_id="light1",
        )
        light.async_write_ha_state = MagicMock()

        await light.async_turn_on(**{ATTR_BRIGHTNESS: 128})

        # Should set brightness first
        mock_coordinator.protect_client.set_light_brightness.assert_called_once_with(
            light_id="light1",
            level=50,  # 128 * 100 / 255 = 50
        )
        # Then set mode
        mock_coordinator.protect_client.set_light_mode.assert_called_once_with(
            light_id="light1",
            mode=LIGHT_MODE_ALWAYS,
        )

    @pytest.mark.asyncio
    async def test_async_turn_on_with_full_brightness(self, mock_coordinator) -> None:
        """Test turning light on with full brightness."""
        light = UnifiProtectLight(
            coordinator=mock_coordinator,
            light_id="light1",
        )
        light.async_write_ha_state = MagicMock()

        await light.async_turn_on(**{ATTR_BRIGHTNESS: 255})

        mock_coordinator.protect_client.set_light_brightness.assert_called_once_with(
            light_id="light1",
            level=100,
        )

    @pytest.mark.asyncio
    async def test_async_turn_off(self, mock_coordinator) -> None:
        """Test turning light off."""
        light = UnifiProtectLight(
            coordinator=mock_coordinator,
            light_id="light1",
        )
        light.async_write_ha_state = MagicMock()

        await light.async_turn_off()

        mock_coordinator.protect_client.set_light_mode.assert_called_once_with(
            light_id="light1",
            mode=LIGHT_MODE_OFF,
        )
        assert light._attr_is_on is False
        light.async_write_ha_state.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_turn_off_with_kwargs(self, mock_coordinator) -> None:
        """Test turning light off ignores extra kwargs."""
        light = UnifiProtectLight(
            coordinator=mock_coordinator,
            light_id="light1",
        )
        light.async_write_ha_state = MagicMock()

        await light.async_turn_off(some_extra_kwarg="value")

        mock_coordinator.protect_client.set_light_mode.assert_called_once()

    def test_missing_light_data(self, mock_coordinator) -> None:
        """Test handling missing light data."""
        mock_coordinator.data["protect"]["lights"]["light1"] = {}

        light = UnifiProtectLight(
            coordinator=mock_coordinator,
            light_id="light1",
        )

        # Should use defaults
        assert light._attr_available is False
        assert light._attr_is_on is False
        assert light._attr_brightness == 255  # default 100%

    def test_missing_mode_settings(self, mock_coordinator) -> None:
        """Test handling missing mode settings."""
        del mock_coordinator.data["protect"]["lights"]["light1"]["lightModeSettings"]

        light = UnifiProtectLight(
            coordinator=mock_coordinator,
            light_id="light1",
        )

        # Should default to OFF mode
        assert light._attr_is_on is False
