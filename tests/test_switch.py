"""Tests for UniFi Protect switch platform."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.helpers.entity import EntityCategory

from custom_components.unifi_insights.const import (
    ATTR_CAMERA_ID,
    ATTR_CAMERA_NAME,
    ATTR_MIC_ENABLED,
    DEVICE_TYPE_CAMERA,
)
from custom_components.unifi_insights.switch import (
    PARALLEL_UPDATES,
    UnifiProtectMicrophoneSwitch,
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

        # Should add one switch entity per camera
        async_add_entities.assert_called_once()
        entities = async_add_entities.call_args[0][0]
        assert len(entities) == 1
        assert isinstance(entities[0], UnifiProtectMicrophoneSwitch)

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
        assert len(entities) == 3


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
