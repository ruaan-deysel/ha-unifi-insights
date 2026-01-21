"""Tests for UniFi Protect number platform."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.components.number import NumberMode
from homeassistant.helpers.entity import EntityCategory

from custom_components.unifi_insights.const import (
    ATTR_CAMERA_ID,
    ATTR_CAMERA_NAME,
    ATTR_CHIME_ID,
    ATTR_CHIME_NAME,
    ATTR_CHIME_REPEAT_TIMES,
    ATTR_CHIME_VOLUME,
    ATTR_LIGHT_ID,
    ATTR_LIGHT_LEVEL,
    ATTR_LIGHT_NAME,
    ATTR_MIC_ENABLED,
    DEVICE_TYPE_CAMERA,
    DEVICE_TYPE_CHIME,
    DEVICE_TYPE_LIGHT,
)
from custom_components.unifi_insights.number import (
    PARALLEL_UPDATES,
    UnifiProtectChimeRepeatTimesNumber,
    UnifiProtectChimeVolumeNumber,
    UnifiProtectLightLevelNumber,
    UnifiProtectMicrophoneVolumeNumber,
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
    async def test_setup_entry_with_cameras(self, hass, mock_coordinator) -> None:
        """Test setup with cameras present."""
        mock_coordinator.data["protect"]["cameras"] = {
            "camera1": {
                "id": "camera1",
                "name": "Test Camera",
                "state": "CONNECTED",
                "micVolume": 50,
            }
        }

        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        async_add_entities = MagicMock()

        await async_setup_entry(hass, mock_entry, async_add_entities)

        async_add_entities.assert_called_once()
        entities = async_add_entities.call_args[0][0]
        assert len(entities) == 1
        assert isinstance(entities[0], UnifiProtectMicrophoneVolumeNumber)

    @pytest.mark.asyncio
    async def test_setup_entry_with_lights(self, hass, mock_coordinator) -> None:
        """Test setup with lights present."""
        mock_coordinator.data["protect"]["lights"] = {
            "light1": {
                "id": "light1",
                "name": "Test Light",
                "state": "CONNECTED",
            }
        }

        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        async_add_entities = MagicMock()

        await async_setup_entry(hass, mock_entry, async_add_entities)

        async_add_entities.assert_called_once()
        entities = async_add_entities.call_args[0][0]
        assert len(entities) == 1
        assert isinstance(entities[0], UnifiProtectLightLevelNumber)

    @pytest.mark.asyncio
    async def test_setup_entry_with_chimes(self, hass, mock_coordinator) -> None:
        """Test setup with chimes present."""
        mock_coordinator.data["protect"]["chimes"] = {
            "chime1": {
                "id": "chime1",
                "name": "Test Chime",
                "state": "CONNECTED",
            }
        }

        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        async_add_entities = MagicMock()

        await async_setup_entry(hass, mock_entry, async_add_entities)

        async_add_entities.assert_called_once()
        entities = async_add_entities.call_args[0][0]
        # Should create both volume and repeat times numbers
        assert len(entities) == 2
        entity_types = {type(e).__name__ for e in entities}
        assert "UnifiProtectChimeVolumeNumber" in entity_types
        assert "UnifiProtectChimeRepeatTimesNumber" in entity_types

    @pytest.mark.asyncio
    async def test_setup_entry_with_all_devices(self, hass, mock_coordinator) -> None:
        """Test setup with all device types."""
        mock_coordinator.data["protect"]["cameras"] = {
            "camera1": {"id": "camera1", "name": "Cam1", "state": "CONNECTED"}
        }
        mock_coordinator.data["protect"]["lights"] = {
            "light1": {"id": "light1", "name": "Light1", "state": "CONNECTED"}
        }
        mock_coordinator.data["protect"]["chimes"] = {
            "chime1": {"id": "chime1", "name": "Chime1", "state": "CONNECTED"}
        }

        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        async_add_entities = MagicMock()

        await async_setup_entry(hass, mock_entry, async_add_entities)

        entities = async_add_entities.call_args[0][0]
        # 1 camera + 1 light + 2 chime (volume + repeat) = 4
        assert len(entities) == 4


class TestUnifiProtectMicrophoneVolumeNumber:
    """Tests for UnifiProtectMicrophoneVolumeNumber entity."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Create mock coordinator."""
        coordinator = MagicMock()
        coordinator.protect_client = MagicMock()
        coordinator.protect_client.base_url = "https://192.168.1.1"
        coordinator.protect_client.set_microphone_volume = AsyncMock()
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
                        "micVolume": 75,
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
        """Test number entity initialization."""
        number = UnifiProtectMicrophoneVolumeNumber(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )

        assert number._device_id == "camera1"
        assert number._device_type == DEVICE_TYPE_CAMERA
        assert number._attr_has_entity_name is True
        assert number._attr_name == "Microphone Volume"
        assert number._attr_entity_category == EntityCategory.CONFIG
        assert number._attr_native_min_value == 0
        assert number._attr_native_max_value == 100
        assert number._attr_native_step == 1
        assert number._attr_mode == NumberMode.SLIDER

    def test_update_from_data(self, mock_coordinator) -> None:
        """Test _update_from_data."""
        number = UnifiProtectMicrophoneVolumeNumber(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )

        assert number._attr_native_value == 75

    def test_extra_state_attributes(self, mock_coordinator) -> None:
        """Test extra state attributes."""
        number = UnifiProtectMicrophoneVolumeNumber(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )

        attrs = number._attr_extra_state_attributes
        assert attrs[ATTR_CAMERA_ID] == "camera1"
        assert attrs[ATTR_CAMERA_NAME] == "Test Camera"
        assert attrs[ATTR_MIC_ENABLED] is True

    @pytest.mark.asyncio
    async def test_async_set_native_value_success(self, mock_coordinator) -> None:
        """Test setting volume successfully."""
        number = UnifiProtectMicrophoneVolumeNumber(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )
        number.async_write_ha_state = MagicMock()

        await number.async_set_native_value(50.0)

        mock_coordinator.protect_client.set_microphone_volume.assert_called_once_with(
            camera_id="camera1",
            volume=50,
        )
        assert number._attr_native_value == 50.0
        number.async_write_ha_state.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_set_native_value_error(self, mock_coordinator) -> None:
        """Test setting volume with error."""
        mock_coordinator.protect_client.set_microphone_volume.side_effect = Exception(
            "API error"
        )

        number = UnifiProtectMicrophoneVolumeNumber(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )
        number.async_write_ha_state = MagicMock()

        await number.async_set_native_value(50.0)

        # Should log error but not update state
        number.async_write_ha_state.assert_not_called()

    def test_missing_mic_volume(self, mock_coordinator) -> None:
        """Test handling missing micVolume field."""
        del mock_coordinator.data["protect"]["cameras"]["camera1"]["micVolume"]

        number = UnifiProtectMicrophoneVolumeNumber(
            coordinator=mock_coordinator,
            camera_id="camera1",
        )

        assert number._attr_native_value == 0


class TestUnifiProtectLightLevelNumber:
    """Tests for UnifiProtectLightLevelNumber entity."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Create mock coordinator."""
        coordinator = MagicMock()
        coordinator.protect_client = MagicMock()
        coordinator.protect_client.base_url = "https://192.168.1.1"
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
                        "lightDeviceSettings": {"ledLevel": 80},
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
        """Test number entity initialization."""
        number = UnifiProtectLightLevelNumber(
            coordinator=mock_coordinator,
            light_id="light1",
        )

        assert number._device_id == "light1"
        assert number._device_type == DEVICE_TYPE_LIGHT
        assert number._attr_has_entity_name is True
        assert number._attr_name == "Brightness Level"
        assert number._attr_entity_category == EntityCategory.CONFIG
        assert number._attr_mode == NumberMode.SLIDER

    def test_update_from_data(self, mock_coordinator) -> None:
        """Test _update_from_data."""
        number = UnifiProtectLightLevelNumber(
            coordinator=mock_coordinator,
            light_id="light1",
        )

        assert number._attr_native_value == 80

    def test_extra_state_attributes(self, mock_coordinator) -> None:
        """Test extra state attributes."""
        number = UnifiProtectLightLevelNumber(
            coordinator=mock_coordinator,
            light_id="light1",
        )

        attrs = number._attr_extra_state_attributes
        assert attrs[ATTR_LIGHT_ID] == "light1"
        assert attrs[ATTR_LIGHT_NAME] == "Test Light"
        assert attrs[ATTR_LIGHT_LEVEL] == 80

    @pytest.mark.asyncio
    async def test_async_set_native_value_success(self, mock_coordinator) -> None:
        """Test setting light level successfully."""
        number = UnifiProtectLightLevelNumber(
            coordinator=mock_coordinator,
            light_id="light1",
        )
        number.async_write_ha_state = MagicMock()

        await number.async_set_native_value(60.0)

        mock_coordinator.protect_client.set_light_brightness.assert_called_once_with(
            light_id="light1",
            level=60,
        )
        assert number._attr_native_value == 60.0
        number.async_write_ha_state.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_set_native_value_error(self, mock_coordinator) -> None:
        """Test setting light level with error."""
        mock_coordinator.protect_client.set_light_brightness.side_effect = Exception(
            "API error"
        )

        number = UnifiProtectLightLevelNumber(
            coordinator=mock_coordinator,
            light_id="light1",
        )
        number.async_write_ha_state = MagicMock()

        await number.async_set_native_value(60.0)

        number.async_write_ha_state.assert_not_called()

    def test_missing_light_device_settings(self, mock_coordinator) -> None:
        """Test handling missing lightDeviceSettings."""
        del mock_coordinator.data["protect"]["lights"]["light1"]["lightDeviceSettings"]

        number = UnifiProtectLightLevelNumber(
            coordinator=mock_coordinator,
            light_id="light1",
        )

        # Default is 100
        assert number._attr_native_value == 100


class TestUnifiProtectChimeVolumeNumber:
    """Tests for UnifiProtectChimeVolumeNumber entity."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Create mock coordinator."""
        coordinator = MagicMock()
        coordinator.protect_client = MagicMock()
        coordinator.protect_client.base_url = "https://192.168.1.1"
        coordinator.protect_client.set_chime_volume = AsyncMock()
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
                "chimes": {
                    "chime1": {
                        "id": "chime1",
                        "name": "Test Chime",
                        "state": "CONNECTED",
                        "mac": "AA:BB:CC:DD:EE:FF",
                        "type": "UP-Chime",
                        "firmwareVersion": "1.0.0",
                        "ringSettings": [
                            {"cameraId": "cam1", "volume": 65, "repeatTimes": 2}
                        ],
                    }
                },
                "liveviews": {},
            },
        }
        return coordinator

    def test_initialization(self, mock_coordinator) -> None:
        """Test number entity initialization."""
        number = UnifiProtectChimeVolumeNumber(
            coordinator=mock_coordinator,
            chime_id="chime1",
        )

        assert number._device_id == "chime1"
        assert number._device_type == DEVICE_TYPE_CHIME
        assert number._attr_has_entity_name is True
        assert number._attr_name == "Volume"
        assert number._attr_entity_category == EntityCategory.CONFIG
        assert number._attr_mode == NumberMode.SLIDER
        assert number._attr_icon == "mdi:volume-high"

    def test_update_from_data(self, mock_coordinator) -> None:
        """Test _update_from_data."""
        number = UnifiProtectChimeVolumeNumber(
            coordinator=mock_coordinator,
            chime_id="chime1",
        )

        assert number._attr_native_value == 65

    def test_update_from_data_no_ring_settings(self, mock_coordinator) -> None:
        """Test _update_from_data with no ring settings."""
        mock_coordinator.data["protect"]["chimes"]["chime1"]["ringSettings"] = []

        number = UnifiProtectChimeVolumeNumber(
            coordinator=mock_coordinator,
            chime_id="chime1",
        )

        # Default is 80
        assert number._attr_native_value == 80

    def test_extra_state_attributes(self, mock_coordinator) -> None:
        """Test extra state attributes."""
        number = UnifiProtectChimeVolumeNumber(
            coordinator=mock_coordinator,
            chime_id="chime1",
        )

        attrs = number._attr_extra_state_attributes
        assert attrs[ATTR_CHIME_ID] == "chime1"
        assert attrs[ATTR_CHIME_NAME] == "Test Chime"
        assert attrs[ATTR_CHIME_VOLUME] == 65

    @pytest.mark.asyncio
    async def test_async_set_native_value_success(self, mock_coordinator) -> None:
        """Test setting chime volume successfully."""
        number = UnifiProtectChimeVolumeNumber(
            coordinator=mock_coordinator,
            chime_id="chime1",
        )
        number.async_write_ha_state = MagicMock()

        await number.async_set_native_value(70.0)

        mock_coordinator.protect_client.set_chime_volume.assert_called_once_with(
            chime_id="chime1",
            volume=70,
        )
        assert number._attr_native_value == 70
        number.async_write_ha_state.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_set_native_value_error(self, mock_coordinator) -> None:
        """Test setting chime volume with error."""
        mock_coordinator.protect_client.set_chime_volume.side_effect = Exception(
            "API error"
        )

        number = UnifiProtectChimeVolumeNumber(
            coordinator=mock_coordinator,
            chime_id="chime1",
        )
        number.async_write_ha_state = MagicMock()

        await number.async_set_native_value(70.0)

        number.async_write_ha_state.assert_not_called()


class TestUnifiProtectChimeRepeatTimesNumber:
    """Tests for UnifiProtectChimeRepeatTimesNumber entity."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Create mock coordinator."""
        coordinator = MagicMock()
        coordinator.protect_client = MagicMock()
        coordinator.protect_client.base_url = "https://192.168.1.1"
        coordinator.protect_client.set_chime_repeat = AsyncMock()
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
                "chimes": {
                    "chime1": {
                        "id": "chime1",
                        "name": "Test Chime",
                        "state": "CONNECTED",
                        "mac": "AA:BB:CC:DD:EE:FF",
                        "type": "UP-Chime",
                        "firmwareVersion": "1.0.0",
                        "ringSettings": [
                            {"cameraId": "cam1", "volume": 65, "repeatTimes": 5}
                        ],
                    }
                },
                "liveviews": {},
            },
        }
        return coordinator

    def test_initialization(self, mock_coordinator) -> None:
        """Test number entity initialization."""
        number = UnifiProtectChimeRepeatTimesNumber(
            coordinator=mock_coordinator,
            chime_id="chime1",
        )

        assert number._device_id == "chime1"
        assert number._device_type == DEVICE_TYPE_CHIME
        assert number._attr_has_entity_name is True
        assert number._attr_name == "Repeat Times"
        assert number._attr_entity_category == EntityCategory.CONFIG
        assert number._attr_native_min_value == 1
        assert number._attr_native_max_value == 10
        assert number._attr_native_step == 1
        assert number._attr_mode == NumberMode.BOX
        assert number._attr_icon == "mdi:repeat"

    def test_update_from_data(self, mock_coordinator) -> None:
        """Test _update_from_data."""
        number = UnifiProtectChimeRepeatTimesNumber(
            coordinator=mock_coordinator,
            chime_id="chime1",
        )

        assert number._attr_native_value == 5

    def test_update_from_data_no_ring_settings(self, mock_coordinator) -> None:
        """Test _update_from_data with no ring settings."""
        mock_coordinator.data["protect"]["chimes"]["chime1"]["ringSettings"] = []

        number = UnifiProtectChimeRepeatTimesNumber(
            coordinator=mock_coordinator,
            chime_id="chime1",
        )

        # Default is 3
        assert number._attr_native_value == 3

    def test_extra_state_attributes(self, mock_coordinator) -> None:
        """Test extra state attributes."""
        number = UnifiProtectChimeRepeatTimesNumber(
            coordinator=mock_coordinator,
            chime_id="chime1",
        )

        attrs = number._attr_extra_state_attributes
        assert attrs[ATTR_CHIME_ID] == "chime1"
        assert attrs[ATTR_CHIME_NAME] == "Test Chime"
        assert attrs[ATTR_CHIME_REPEAT_TIMES] == 5

    @pytest.mark.asyncio
    async def test_async_set_native_value_success(self, mock_coordinator) -> None:
        """Test setting repeat times successfully."""
        number = UnifiProtectChimeRepeatTimesNumber(
            coordinator=mock_coordinator,
            chime_id="chime1",
        )
        number.async_write_ha_state = MagicMock()

        await number.async_set_native_value(3.0)

        mock_coordinator.protect_client.set_chime_repeat.assert_called_once_with(
            chime_id="chime1",
            repeat_times=3,
        )
        assert number._attr_native_value == 3
        number.async_write_ha_state.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_set_native_value_error(self, mock_coordinator) -> None:
        """Test setting repeat times with error."""
        mock_coordinator.protect_client.set_chime_repeat.side_effect = Exception(
            "API error"
        )

        number = UnifiProtectChimeRepeatTimesNumber(
            coordinator=mock_coordinator,
            chime_id="chime1",
        )
        number.async_write_ha_state = MagicMock()

        await number.async_set_native_value(3.0)

        number.async_write_ha_state.assert_not_called()
