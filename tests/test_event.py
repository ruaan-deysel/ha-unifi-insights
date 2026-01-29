"""Tests for UniFi Insights event platform."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from homeassistant.components.event import EventDeviceClass

from custom_components.unifi_insights.event import (
    EVENT_TYPE_DOORBELL_RING,
    EVENT_TYPE_MOTION,
    EVENT_TYPE_SENSOR_CLOSE,
    EVENT_TYPE_SENSOR_OPEN,
    EVENT_TYPE_SMART_DETECT_ANIMAL,
    EVENT_TYPE_SMART_DETECT_PACKAGE,
    EVENT_TYPE_SMART_DETECT_PERSON,
    EVENT_TYPE_SMART_DETECT_VEHICLE,
    PARALLEL_UPDATES,
    UnifiProtectDoorbellEventEntity,
    UnifiProtectSensorEventEntity,
    UnifiProtectSmartDetectEventEntity,
    _is_doorbell_camera,
    async_setup_entry,
)


class TestParallelUpdates:
    """Test PARALLEL_UPDATES constant."""

    def test_parallel_updates_value(self) -> None:
        """Test that PARALLEL_UPDATES is set correctly."""
        assert PARALLEL_UPDATES == 0


class TestEventTypes:
    """Test event type constants."""

    def test_doorbell_ring_event_type(self) -> None:
        """Test doorbell ring event type."""
        assert EVENT_TYPE_DOORBELL_RING == "ring"

    def test_motion_event_type(self) -> None:
        """Test motion event type."""
        assert EVENT_TYPE_MOTION == "motion"

    def test_smart_detect_event_types(self) -> None:
        """Test smart detect event types."""
        assert EVENT_TYPE_SMART_DETECT_PERSON == "person_detected"
        assert EVENT_TYPE_SMART_DETECT_VEHICLE == "vehicle_detected"
        assert EVENT_TYPE_SMART_DETECT_ANIMAL == "animal_detected"
        assert EVENT_TYPE_SMART_DETECT_PACKAGE == "package_detected"

    def test_sensor_event_types(self) -> None:
        """Test sensor event types."""
        assert EVENT_TYPE_SENSOR_OPEN == "opened"
        assert EVENT_TYPE_SENSOR_CLOSE == "closed"


class TestIsDoorbellCamera:
    """Tests for _is_doorbell_camera helper function."""

    def test_doorbell_in_camera_type(self) -> None:
        """Test detection via _camera_type field."""
        camera_data = {"_camera_type": "doorbell"}
        assert _is_doorbell_camera(camera_data) is True

    def test_doorbell_in_api_type(self) -> None:
        """Test detection via type field."""
        camera_data = {"type": "G4-Doorbell"}
        assert _is_doorbell_camera(camera_data) is True

    def test_doorbell_in_name(self) -> None:
        """Test detection via name field."""
        camera_data = {"name": "Front Doorbell"}
        assert _is_doorbell_camera(camera_data) is True

    def test_not_doorbell(self) -> None:
        """Test non-doorbell camera."""
        camera_data = {"name": "Backyard Camera", "type": "G4-Pro"}
        assert _is_doorbell_camera(camera_data) is False

    def test_empty_data(self) -> None:
        """Test with empty camera data."""
        camera_data = {}
        assert _is_doorbell_camera(camera_data) is False


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
            "clients": {},
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
    async def test_setup_entry_with_doorbell_camera(
        self, hass, mock_coordinator
    ) -> None:
        """Test setup with a doorbell camera."""
        mock_coordinator.data["protect"]["cameras"] = {
            "camera1": {
                "id": "camera1",
                "name": "Front Doorbell",
                "state": "CONNECTED",
                "type": "G4-Doorbell",
                "smartDetectTypes": ["person"],
            }
        }

        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        async_add_entities = MagicMock()

        await async_setup_entry(hass, mock_entry, async_add_entities)

        async_add_entities.assert_called_once()
        entities = async_add_entities.call_args[0][0]
        # Should have doorbell event + smart detect event
        assert len(entities) == 2
        entity_types = [type(e).__name__ for e in entities]
        assert "UnifiProtectDoorbellEventEntity" in entity_types
        assert "UnifiProtectSmartDetectEventEntity" in entity_types

    @pytest.mark.asyncio
    async def test_setup_entry_with_regular_camera(
        self, hass, mock_coordinator
    ) -> None:
        """Test setup with a regular camera."""
        mock_coordinator.data["protect"]["cameras"] = {
            "camera1": {
                "id": "camera1",
                "name": "Backyard Camera",
                "state": "CONNECTED",
                "type": "G4-Pro",
                "smartDetectTypes": ["person", "vehicle"],
            }
        }

        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        async_add_entities = MagicMock()

        await async_setup_entry(hass, mock_entry, async_add_entities)

        async_add_entities.assert_called_once()
        entities = async_add_entities.call_args[0][0]
        # Regular camera only has smart detect event (no doorbell)
        assert len(entities) == 1
        assert isinstance(entities[0], UnifiProtectSmartDetectEventEntity)

    @pytest.mark.asyncio
    async def test_setup_entry_with_sensors(self, hass, mock_coordinator) -> None:
        """Test setup with sensors."""
        mock_coordinator.data["protect"]["sensors"] = {
            "sensor1": {
                "id": "sensor1",
                "name": "Front Door Sensor",
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
        assert isinstance(entities[0], UnifiProtectSensorEventEntity)


class TestUnifiProtectDoorbellEventEntity:
    """Tests for UnifiProtectDoorbellEventEntity."""

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
            "protect": {
                "cameras": {
                    "camera1": {
                        "id": "camera1",
                        "name": "Front Doorbell",
                        "state": "CONNECTED",
                        "type": "G4-Doorbell",
                    }
                },
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "viewers": {},
                "chimes": {},
            },
        }
        return coordinator

    def test_initialization(self, mock_coordinator) -> None:
        """Test entity initialization."""
        entity = UnifiProtectDoorbellEventEntity(
            coordinator=mock_coordinator,
            device_id="camera1",
        )

        assert entity._device_id == "camera1"
        assert entity._attr_device_class == EventDeviceClass.DOORBELL

    def test_unique_id(self, mock_coordinator) -> None:
        """Test unique ID is set correctly."""
        entity = UnifiProtectDoorbellEventEntity(
            coordinator=mock_coordinator,
            device_id="camera1",
        )

        assert "camera1" in entity._attr_unique_id
        assert "doorbell" in entity._attr_unique_id

    def test_event_types(self, mock_coordinator) -> None:
        """Test event types are set correctly."""
        entity = UnifiProtectDoorbellEventEntity(
            coordinator=mock_coordinator,
            device_id="camera1",
        )

        assert EVENT_TYPE_DOORBELL_RING in entity._attr_event_types

    def test_available_when_connected(self, mock_coordinator) -> None:
        """Test availability when camera is connected."""
        entity = UnifiProtectDoorbellEventEntity(
            coordinator=mock_coordinator,
            device_id="camera1",
        )

        assert entity.available is True

    def test_unavailable_when_disconnected(self, mock_coordinator) -> None:
        """Test availability when camera is disconnected."""
        mock_coordinator.data["protect"]["cameras"]["camera1"]["state"] = "DISCONNECTED"

        entity = UnifiProtectDoorbellEventEntity(
            coordinator=mock_coordinator,
            device_id="camera1",
        )

        assert entity.available is False

    def test_device_info(self, mock_coordinator) -> None:
        """Test device info is set correctly."""
        entity = UnifiProtectDoorbellEventEntity(
            coordinator=mock_coordinator,
            device_id="camera1",
        )

        device_info = entity._attr_device_info
        assert device_info is not None
        assert device_info["manufacturer"] == "Ubiquiti Inc."


class TestUnifiProtectSmartDetectEventEntity:
    """Tests for UnifiProtectSmartDetectEventEntity."""

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
            "protect": {
                "cameras": {
                    "camera1": {
                        "id": "camera1",
                        "name": "Backyard Camera",
                        "state": "CONNECTED",
                        "type": "G4-Pro",
                        "smartDetectTypes": ["person", "vehicle", "animal"],
                    }
                },
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "viewers": {},
                "chimes": {},
            },
        }
        return coordinator

    def test_initialization(self, mock_coordinator) -> None:
        """Test entity initialization."""
        entity = UnifiProtectSmartDetectEventEntity(
            coordinator=mock_coordinator,
            device_id="camera1",
        )

        assert entity._device_id == "camera1"
        assert entity._attr_device_class == EventDeviceClass.MOTION

    def test_unique_id(self, mock_coordinator) -> None:
        """Test unique ID is set correctly."""
        entity = UnifiProtectSmartDetectEventEntity(
            coordinator=mock_coordinator,
            device_id="camera1",
        )

        assert "camera1" in entity._attr_unique_id
        assert "smart_detect" in entity._attr_unique_id

    def test_event_types(self, mock_coordinator) -> None:
        """Test event types include all smart detect types."""
        entity = UnifiProtectSmartDetectEventEntity(
            coordinator=mock_coordinator,
            device_id="camera1",
        )

        assert EVENT_TYPE_MOTION in entity._attr_event_types
        assert EVENT_TYPE_SMART_DETECT_PERSON in entity._attr_event_types
        assert EVENT_TYPE_SMART_DETECT_VEHICLE in entity._attr_event_types
        assert EVENT_TYPE_SMART_DETECT_ANIMAL in entity._attr_event_types
        assert EVENT_TYPE_SMART_DETECT_PACKAGE in entity._attr_event_types

    def test_available_when_connected(self, mock_coordinator) -> None:
        """Test availability when camera is connected."""
        entity = UnifiProtectSmartDetectEventEntity(
            coordinator=mock_coordinator,
            device_id="camera1",
        )

        assert entity.available is True

    def test_unavailable_when_disconnected(self, mock_coordinator) -> None:
        """Test availability when camera is disconnected."""
        mock_coordinator.data["protect"]["cameras"]["camera1"]["state"] = "DISCONNECTED"

        entity = UnifiProtectSmartDetectEventEntity(
            coordinator=mock_coordinator,
            device_id="camera1",
        )

        assert entity.available is False

    def test_device_info(self, mock_coordinator) -> None:
        """Test device info is set correctly."""
        entity = UnifiProtectSmartDetectEventEntity(
            coordinator=mock_coordinator,
            device_id="camera1",
        )

        device_info = entity._attr_device_info
        assert device_info is not None
        assert device_info["manufacturer"] == "Ubiquiti Inc."


class TestUnifiProtectSensorEventEntity:
    """Tests for UnifiProtectSensorEventEntity."""

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
            "protect": {
                "cameras": {},
                "lights": {},
                "sensors": {
                    "sensor1": {
                        "id": "sensor1",
                        "name": "Front Door Sensor",
                        "state": "CONNECTED",
                        "type": "UP-Sense",
                        "isOpened": False,
                    }
                },
                "nvrs": {},
                "viewers": {},
                "chimes": {},
            },
        }
        return coordinator

    def test_initialization(self, mock_coordinator) -> None:
        """Test entity initialization."""
        entity = UnifiProtectSensorEventEntity(
            coordinator=mock_coordinator,
            device_id="sensor1",
        )

        assert entity._device_id == "sensor1"

    def test_unique_id(self, mock_coordinator) -> None:
        """Test unique ID is set correctly."""
        entity = UnifiProtectSensorEventEntity(
            coordinator=mock_coordinator,
            device_id="sensor1",
        )

        assert "sensor1" in entity._attr_unique_id
        assert "event" in entity._attr_unique_id

    def test_event_types(self, mock_coordinator) -> None:
        """Test event types include open and close."""
        entity = UnifiProtectSensorEventEntity(
            coordinator=mock_coordinator,
            device_id="sensor1",
        )

        assert EVENT_TYPE_SENSOR_OPEN in entity._attr_event_types
        assert EVENT_TYPE_SENSOR_CLOSE in entity._attr_event_types

    def test_available_when_connected(self, mock_coordinator) -> None:
        """Test availability when sensor is connected."""
        entity = UnifiProtectSensorEventEntity(
            coordinator=mock_coordinator,
            device_id="sensor1",
        )

        assert entity.available is True

    def test_unavailable_when_disconnected(self, mock_coordinator) -> None:
        """Test availability when sensor is disconnected."""
        mock_coordinator.data["protect"]["sensors"]["sensor1"]["state"] = "DISCONNECTED"

        entity = UnifiProtectSensorEventEntity(
            coordinator=mock_coordinator,
            device_id="sensor1",
        )

        assert entity.available is False

    def test_device_info(self, mock_coordinator) -> None:
        """Test device info is set correctly."""
        entity = UnifiProtectSensorEventEntity(
            coordinator=mock_coordinator,
            device_id="sensor1",
        )

        device_info = entity._attr_device_info
        assert device_info is not None
        assert device_info["manufacturer"] == "Ubiquiti Inc."


class TestDoorbellCoordinatorUpdate:
    """Tests for doorbell _handle_coordinator_update method."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Create mock coordinator for doorbell tests."""
        coordinator = MagicMock()
        coordinator.protect_client = MagicMock()
        coordinator.protect_client.base_url = "https://192.168.1.1"
        coordinator.data = {
            "protect": {
                "cameras": {
                    "camera1": {
                        "id": "camera1",
                        "name": "Doorbell",
                        "state": "CONNECTED",
                        "type": "doorbell",
                        "lastRingStart": None,
                        "lastRingEnd": None,
                    }
                },
                "sensors": {},
            }
        }
        return coordinator

    def test_handle_ring_event(self, mock_coordinator) -> None:
        """Test handling of ring event triggers event."""
        entity = UnifiProtectDoorbellEventEntity(
            coordinator=mock_coordinator,
            device_id="camera1",
        )

        # Simulate ring event
        mock_coordinator.data["protect"]["cameras"]["camera1"]["lastRingStart"] = 1234
        mock_coordinator.data["protect"]["cameras"]["camera1"]["lastRingEnd"] = None

        # Patch async_write_ha_state to avoid HA state machine issues
        with patch.object(entity, "async_write_ha_state"):
            entity._handle_coordinator_update()
        assert entity._last_ring_start == 1234

    def test_no_ring_when_ring_ended(self, mock_coordinator) -> None:
        """Test no event when ring has ended."""
        entity = UnifiProtectDoorbellEventEntity(
            coordinator=mock_coordinator,
            device_id="camera1",
        )

        # Ring has ended
        mock_coordinator.data["protect"]["cameras"]["camera1"]["lastRingStart"] = 1234
        mock_coordinator.data["protect"]["cameras"]["camera1"]["lastRingEnd"] = 1235

        # Patch async_write_ha_state to avoid HA state machine issues
        with patch.object(entity, "async_write_ha_state"):
            entity._handle_coordinator_update()
        # _last_ring_start should not be updated since ring_end is not None
        assert entity._last_ring_start is None


class TestSmartDetectCoordinatorUpdate:
    """Tests for smart detect _handle_coordinator_update method."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Create mock coordinator for smart detect tests."""
        coordinator = MagicMock()
        coordinator.protect_client = MagicMock()
        coordinator.protect_client.base_url = "https://192.168.1.1"
        coordinator.data = {
            "protect": {
                "cameras": {
                    "camera1": {
                        "id": "camera1",
                        "name": "Front Camera",
                        "state": "CONNECTED",
                        "type": "camera",
                        "lastMotionStart": None,
                        "lastMotionEnd": None,
                        "lastSmartDetectTypes": [],
                    }
                },
                "sensors": {},
            }
        }
        return coordinator

    def test_handle_motion_event(self, mock_coordinator) -> None:
        """Test handling of motion event."""
        entity = UnifiProtectSmartDetectEventEntity(
            coordinator=mock_coordinator,
            device_id="camera1",
        )

        # Simulate motion event
        mock_coordinator.data["protect"]["cameras"]["camera1"]["lastMotionStart"] = 5678
        mock_coordinator.data["protect"]["cameras"]["camera1"]["lastMotionEnd"] = None
        mock_coordinator.data["protect"]["cameras"]["camera1"][
            "lastSmartDetectTypes"
        ] = []

        with patch.object(entity, "async_write_ha_state"):
            entity._handle_coordinator_update()
        assert entity._last_motion_start == 5678

    def test_handle_person_detection(self, mock_coordinator) -> None:
        """Test handling of person detection event."""
        entity = UnifiProtectSmartDetectEventEntity(
            coordinator=mock_coordinator,
            device_id="camera1",
        )

        # Simulate person detection
        mock_coordinator.data["protect"]["cameras"]["camera1"]["lastMotionStart"] = 9999
        mock_coordinator.data["protect"]["cameras"]["camera1"]["lastMotionEnd"] = None
        mock_coordinator.data["protect"]["cameras"]["camera1"][
            "lastSmartDetectTypes"
        ] = ["person"]

        with patch.object(entity, "async_write_ha_state"):
            entity._handle_coordinator_update()
        assert entity._last_motion_start == 9999
        assert "person" in entity._last_smart_detect_types

    def test_no_event_when_motion_ended(self, mock_coordinator) -> None:
        """Test no event when motion has ended."""
        entity = UnifiProtectSmartDetectEventEntity(
            coordinator=mock_coordinator,
            device_id="camera1",
        )

        # Motion has ended
        mock_coordinator.data["protect"]["cameras"]["camera1"]["lastMotionStart"] = 1111
        mock_coordinator.data["protect"]["cameras"]["camera1"]["lastMotionEnd"] = 1112

        with patch.object(entity, "async_write_ha_state"):
            entity._handle_coordinator_update()
        # _last_motion_start should not be updated since motion_end is not None
        assert entity._last_motion_start is None


class TestSensorCoordinatorUpdate:
    """Tests for sensor _handle_coordinator_update method."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Create mock coordinator for sensor tests."""
        coordinator = MagicMock()
        coordinator.protect_client = MagicMock()
        coordinator.protect_client.base_url = "https://192.168.1.1"
        coordinator.data = {
            "protect": {
                "cameras": {},
                "sensors": {
                    "sensor1": {
                        "id": "sensor1",
                        "name": "Door Sensor",
                        "state": "CONNECTED",
                        "isOpened": False,
                        "openStatusChangedAt": None,
                    }
                },
            }
        }
        return coordinator

    def test_handle_sensor_opened(self, mock_coordinator) -> None:
        """Test handling of sensor opened event."""
        entity = UnifiProtectSensorEventEntity(
            coordinator=mock_coordinator,
            device_id="sensor1",
        )

        # Simulate sensor opened
        mock_coordinator.data["protect"]["sensors"]["sensor1"]["isOpened"] = True
        mock_coordinator.data["protect"]["sensors"]["sensor1"][
            "openStatusChangedAt"
        ] = 2222

        with patch.object(entity, "async_write_ha_state"):
            entity._handle_coordinator_update()
        assert entity._last_open_status_changed_at == 2222
        assert entity._last_is_opened is True

    def test_handle_sensor_closed(self, mock_coordinator) -> None:
        """Test handling of sensor closed event."""
        # Start with sensor opened
        mock_coordinator.data["protect"]["sensors"]["sensor1"]["isOpened"] = True
        mock_coordinator.data["protect"]["sensors"]["sensor1"][
            "openStatusChangedAt"
        ] = 1111

        entity = UnifiProtectSensorEventEntity(
            coordinator=mock_coordinator,
            device_id="sensor1",
        )

        # Record initial state
        with patch.object(entity, "async_write_ha_state"):
            entity._handle_coordinator_update()
        assert entity._last_is_opened is True

        # Now close sensor
        mock_coordinator.data["protect"]["sensors"]["sensor1"]["isOpened"] = False
        mock_coordinator.data["protect"]["sensors"]["sensor1"][
            "openStatusChangedAt"
        ] = 3333

        with patch.object(entity, "async_write_ha_state"):
            entity._handle_coordinator_update()
        assert entity._last_open_status_changed_at == 3333
        assert entity._last_is_opened is False


class TestEventSetupEmptyCameras:
    """Tests for setup when cameras dict is empty."""

    @pytest.fixture
    def mock_coordinator(self) -> MagicMock:
        """Create mock coordinator with empty cameras."""
        coordinator = MagicMock()
        coordinator.protect_client = MagicMock()
        coordinator.network_client = MagicMock()
        coordinator.network_client.base_url = "https://192.168.1.1"
        coordinator.data = {
            "sites": {},
            "devices": {},
            "clients": {},
            "protect": {
                "cameras": {},  # Empty cameras dict
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "viewers": {},
                "chimes": {},
            },
        }
        return coordinator

    @pytest.mark.asyncio
    async def test_setup_entry_empty_cameras(self, hass, mock_coordinator) -> None:
        """Test setup with empty cameras dict (no iterations)."""
        mock_entry = MagicMock()
        mock_entry.runtime_data = MagicMock()
        mock_entry.runtime_data.coordinator = mock_coordinator

        async_add_entities = MagicMock()

        await async_setup_entry(hass, mock_entry, async_add_entities)

        # Should add empty list since no cameras and no sensors
        async_add_entities.assert_called_once()
        entities = async_add_entities.call_args[0][0]
        assert len(entities) == 0


class TestDoorbellAvailableNoCameraData:
    """Tests for doorbell entity available when camera data is missing."""

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
            "protect": {
                "cameras": {},  # Will be missing the camera
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "viewers": {},
                "chimes": {},
            },
        }
        return coordinator

    def test_available_returns_false_when_camera_missing(
        self, mock_coordinator
    ) -> None:
        """Test available returns False when camera data is missing."""
        # First create entity with camera data present
        mock_coordinator.data["protect"]["cameras"]["camera1"] = {
            "id": "camera1",
            "name": "Front Doorbell",
            "state": "CONNECTED",
            "type": "G4-Doorbell",
        }

        entity = UnifiProtectDoorbellEventEntity(
            coordinator=mock_coordinator,
            device_id="camera1",
        )

        # Now remove the camera from data
        del mock_coordinator.data["protect"]["cameras"]["camera1"]

        # available should return False
        assert entity.available is False


class TestSmartDetectAvailableNoCameraData:
    """Tests for smart detect entity available when camera data is missing."""

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

    def test_available_returns_false_when_camera_missing(
        self, mock_coordinator
    ) -> None:
        """Test available returns False when camera data is missing."""
        # First create entity with camera data present
        mock_coordinator.data["protect"]["cameras"]["camera1"] = {
            "id": "camera1",
            "name": "Backyard Camera",
            "state": "CONNECTED",
            "type": "G4-Pro",
            "smartDetectTypes": ["person", "vehicle"],
        }

        entity = UnifiProtectSmartDetectEventEntity(
            coordinator=mock_coordinator,
            device_id="camera1",
        )

        # Now remove the camera from data
        del mock_coordinator.data["protect"]["cameras"]["camera1"]

        # available should return False
        assert entity.available is False


class TestSensorAvailableNoSensorData:
    """Tests for sensor entity available when sensor data is missing."""

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

    def test_available_returns_false_when_sensor_missing(
        self, mock_coordinator
    ) -> None:
        """Test available returns False when sensor data is missing."""
        # First create entity with sensor data present
        mock_coordinator.data["protect"]["sensors"]["sensor1"] = {
            "id": "sensor1",
            "name": "Front Door Sensor",
            "state": "CONNECTED",
        }

        entity = UnifiProtectSensorEventEntity(
            coordinator=mock_coordinator,
            device_id="sensor1",
        )

        # Now remove the sensor from data
        del mock_coordinator.data["protect"]["sensors"]["sensor1"]

        # available should return False
        assert entity.available is False


class TestSmartDetectVehicleAnimalPackage:
    """Tests for vehicle, animal, and package detection events."""

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
            "protect": {
                "cameras": {
                    "camera1": {
                        "id": "camera1",
                        "name": "Driveway Camera",
                        "state": "CONNECTED",
                        "type": "G4-Pro",
                        "smartDetectTypes": ["person", "vehicle", "animal", "package"],
                        "lastMotionStart": None,
                        "lastMotionEnd": None,
                        "lastSmartDetectTypes": [],
                    }
                },
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "viewers": {},
                "chimes": {},
            },
        }
        return coordinator

    def test_handle_vehicle_detection(self, mock_coordinator) -> None:
        """Test handling of vehicle detection event."""
        entity = UnifiProtectSmartDetectEventEntity(
            coordinator=mock_coordinator,
            device_id="camera1",
        )

        # Trigger vehicle detection
        mock_coordinator.data["protect"]["cameras"]["camera1"]["lastMotionStart"] = 1234
        mock_coordinator.data["protect"]["cameras"]["camera1"]["lastMotionEnd"] = None
        mock_coordinator.data["protect"]["cameras"]["camera1"][
            "lastSmartDetectTypes"
        ] = ["vehicle"]

        with (
            patch.object(entity, "async_write_ha_state"),
            patch.object(entity, "_trigger_event") as mock_trigger,
        ):
            entity._handle_coordinator_update()
            mock_trigger.assert_called_once_with(
                EVENT_TYPE_SMART_DETECT_VEHICLE,
                {"camera_id": "camera1"},
            )

    def test_handle_animal_detection(self, mock_coordinator) -> None:
        """Test handling of animal detection event."""
        entity = UnifiProtectSmartDetectEventEntity(
            coordinator=mock_coordinator,
            device_id="camera1",
        )

        # Trigger animal detection
        mock_coordinator.data["protect"]["cameras"]["camera1"]["lastMotionStart"] = 2345
        mock_coordinator.data["protect"]["cameras"]["camera1"]["lastMotionEnd"] = None
        mock_coordinator.data["protect"]["cameras"]["camera1"][
            "lastSmartDetectTypes"
        ] = ["animal"]

        with (
            patch.object(entity, "async_write_ha_state"),
            patch.object(entity, "_trigger_event") as mock_trigger,
        ):
            entity._handle_coordinator_update()
            mock_trigger.assert_called_once_with(
                EVENT_TYPE_SMART_DETECT_ANIMAL,
                {"camera_id": "camera1"},
            )

    def test_handle_package_detection(self, mock_coordinator) -> None:
        """Test handling of package detection event."""
        entity = UnifiProtectSmartDetectEventEntity(
            coordinator=mock_coordinator,
            device_id="camera1",
        )

        # Trigger package detection
        mock_coordinator.data["protect"]["cameras"]["camera1"]["lastMotionStart"] = 3456
        mock_coordinator.data["protect"]["cameras"]["camera1"]["lastMotionEnd"] = None
        mock_coordinator.data["protect"]["cameras"]["camera1"][
            "lastSmartDetectTypes"
        ] = ["package"]

        with (
            patch.object(entity, "async_write_ha_state"),
            patch.object(entity, "_trigger_event") as mock_trigger,
        ):
            entity._handle_coordinator_update()
            mock_trigger.assert_called_once_with(
                EVENT_TYPE_SMART_DETECT_PACKAGE,
                {"camera_id": "camera1"},
            )


class TestSensorUpdateNoStatusChange:
    """Tests for sensor update when status hasn't changed."""

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
            "protect": {
                "cameras": {},
                "lights": {},
                "sensors": {
                    "sensor1": {
                        "id": "sensor1",
                        "name": "Front Door Sensor",
                        "state": "CONNECTED",
                        "isOpened": False,
                        "openStatusChangedAt": None,  # No status change timestamp
                    }
                },
                "nvrs": {},
                "viewers": {},
                "chimes": {},
            },
        }
        return coordinator

    def test_no_event_when_status_unchanged_at_is_none(self, mock_coordinator) -> None:
        """Test no event fired when openStatusChangedAt is None."""
        entity = UnifiProtectSensorEventEntity(
            coordinator=mock_coordinator,
            device_id="sensor1",
        )

        with (
            patch.object(entity, "async_write_ha_state"),
            patch.object(entity, "_trigger_event") as mock_trigger,
        ):
            entity._handle_coordinator_update()
            # Should not trigger any event when openStatusChangedAt is None
            mock_trigger.assert_not_called()
