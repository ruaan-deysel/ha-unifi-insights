"""Tests for UniFi Insights binary sensors."""

from unittest.mock import MagicMock

import pytest
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.core import HomeAssistant

from custom_components.unifi_insights.binary_sensor import (
    BINARY_SENSOR_TYPES,
    UnifiInsightsBinarySensor,
    UnifiProtectBinarySensor,
    _is_doorbell_camera,
    async_setup_entry,
)
from custom_components.unifi_insights.const import (
    CAMERA_TYPE_DOORBELL,
    CAMERA_TYPE_DOORBELL_MAIN,
    DEVICE_TYPE_CAMERA,
    DEVICE_TYPE_SENSOR,
)


class TestIsDoorbellCamera:
    """Tests for _is_doorbell_camera helper function."""

    def test_doorbell_type_metadata(self):
        """Test detection via _camera_type metadata."""
        camera_data = {"_camera_type": CAMERA_TYPE_DOORBELL}
        assert _is_doorbell_camera(camera_data) is True

    def test_doorbell_main_type(self):
        """Test detection via doorbell main type."""
        camera_data = {"_camera_type": CAMERA_TYPE_DOORBELL_MAIN}
        assert _is_doorbell_camera(camera_data) is True

    def test_api_type_doorbell(self):
        """Test detection via API type field."""
        camera_data = {"type": "G4-Doorbell"}
        assert _is_doorbell_camera(camera_data) is True

    def test_api_type_ai_doorbell(self):
        """Test detection via AI doorbell type."""
        camera_data = {"type": "AI-Doorbell-Pro"}
        assert _is_doorbell_camera(camera_data) is True

    def test_name_doorbell(self):
        """Test detection via name."""
        camera_data = {"name": "Front Door Doorbell"}
        assert _is_doorbell_camera(camera_data) is True

    def test_name_front_door(self):
        """Test detection via front door name."""
        camera_data = {"name": "Front Door Camera"}
        assert _is_doorbell_camera(camera_data) is True

    def test_regular_camera(self):
        """Test regular camera is not doorbell."""
        camera_data = {"name": "Garage Camera", "type": "UVC-G4-PRO"}
        assert _is_doorbell_camera(camera_data) is False

    def test_empty_data(self):
        """Test empty data returns False."""
        camera_data = {}
        assert _is_doorbell_camera(camera_data) is False

    def test_none_values(self):
        """Test None values are handled."""
        camera_data = {"name": None, "type": None, "_camera_type": None}
        assert _is_doorbell_camera(camera_data) is False


class TestBinarySensorTypes:
    """Tests for binary sensor type definitions."""

    def test_binary_sensor_types_defined(self):
        """Test that binary sensor types are defined."""
        assert len(BINARY_SENSOR_TYPES) > 0

    def test_device_status_sensor(self):
        """Test device status sensor is defined."""
        device_status = next(
            (s for s in BINARY_SENSOR_TYPES if s.key == "device_status"), None
        )
        assert device_status is not None
        assert device_status.device_class == BinarySensorDeviceClass.CONNECTIVITY

    def test_camera_motion_sensor(self):
        """Test camera motion sensor is defined."""
        motion = next(
            (s for s in BINARY_SENSOR_TYPES if s.key == "camera_motion"), None
        )
        assert motion is not None
        assert motion.device_class == BinarySensorDeviceClass.MOTION
        assert motion.device_type == DEVICE_TYPE_CAMERA

    def test_camera_person_detection(self):
        """Test camera person detection sensor."""
        person = next(
            (s for s in BINARY_SENSOR_TYPES if s.key == "camera_person_detection"),
            None,
        )
        assert person is not None
        assert person.device_class == BinarySensorDeviceClass.MOTION

    def test_sensor_door_sensor(self):
        """Test sensor door sensor is defined."""
        door = next((s for s in BINARY_SENSOR_TYPES if s.key == "sensor_door"), None)
        assert door is not None
        assert door.device_class == BinarySensorDeviceClass.DOOR
        assert door.device_type == DEVICE_TYPE_SENSOR

    def test_sensor_tamper_sensor(self):
        """Test sensor tamper sensor is defined."""
        tamper = next(
            (s for s in BINARY_SENSOR_TYPES if s.key == "sensor_tamper"), None
        )
        assert tamper is not None
        assert tamper.device_class == BinarySensorDeviceClass.TAMPER
        assert tamper.device_type == DEVICE_TYPE_SENSOR

    def test_sensor_leak_sensor(self):
        """Test sensor leak sensor is defined."""
        leak = next((s for s in BINARY_SENSOR_TYPES if s.key == "sensor_leak"), None)
        assert leak is not None
        assert leak.device_class == BinarySensorDeviceClass.MOISTURE
        assert leak.device_type == DEVICE_TYPE_SENSOR


class TestUnifiInsightsBinarySensor:
    """Tests for UnifiInsightsBinarySensor."""

    @pytest.fixture
    def mock_coordinator(self, hass: HomeAssistant):
        """Create mock coordinator."""
        coordinator = MagicMock()
        coordinator.hass = hass
        coordinator.network_client = MagicMock()
        coordinator.network_client.base_url = "https://192.168.1.1"
        coordinator.protect_client = MagicMock()
        coordinator.data = {
            "sites": {"site1": {"id": "site1", "meta": {"name": "Default"}}},
            "devices": {
                "site1": {
                    "device1": {
                        "id": "device1",
                        "name": "Test Switch",
                        "model": "USW-24-POE",
                        "state": "ONLINE",
                        "macAddress": "AA:BB:CC:DD:EE:FF",
                        "ipAddress": "192.168.1.10",
                        "firmwareVersion": "6.5.55",
                    },
                    "device2": {
                        "id": "device2",
                        "name": "UDM Pro",
                        "model": "UDM-PRO",
                        "state": "OFFLINE",
                        "macAddress": "11:22:33:44:55:66",
                        "ipAddress": "192.168.1.1",
                    },
                },
            },
            "stats": {},
            "clients": {},
            "protect": {
                "cameras": {
                    "camera1": {
                        "id": "camera1",
                        "name": "Front Door",
                        "state": "CONNECTED",
                        "smartDetectTypes": ["person", "vehicle"],
                        "lastSmartDetectTypes": [],
                        "lastMotionStart": None,
                        "lastMotionEnd": None,
                        "lastRingStart": None,
                        "lastRingEnd": None,
                    },
                    "camera2": {
                        "id": "camera2",
                        "name": "Doorbell",
                        "state": "CONNECTED",
                        "_camera_type": "doorbell",
                        "smartDetectTypes": ["person", "package"],
                        "lastSmartDetectTypes": ["person"],
                        "lastMotionStart": 1234567890,
                        "lastMotionEnd": None,
                        "lastRingStart": None,
                        "lastRingEnd": None,
                    },
                },
                "lights": {},
                "sensors": {
                    "sensor1": {
                        "id": "sensor1",
                        "name": "Front Door Sensor",
                        "state": "CONNECTED",
                        "isMotionDetected": False,
                        "isOpened": True,
                    },
                },
                "nvrs": {},
                "viewers": {},
                "chimes": {},
                "liveviews": {},
            },
        }
        return coordinator

    async def test_device_status_sensor_online(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test device status sensor when online."""
        description = next(s for s in BINARY_SENSOR_TYPES if s.key == "device_status")

        sensor = UnifiInsightsBinarySensor(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
        )

        assert sensor.is_on is True

    async def test_device_status_sensor_offline(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test device status sensor when offline."""
        description = next(s for s in BINARY_SENSOR_TYPES if s.key == "device_status")

        sensor = UnifiInsightsBinarySensor(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device2",
        )

        assert sensor.is_on is False

    async def test_device_status_no_data(self, hass: HomeAssistant, mock_coordinator):
        """Test device status when data removed."""
        description = next(s for s in BINARY_SENSOR_TYPES if s.key == "device_status")

        sensor = UnifiInsightsBinarySensor(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
        )

        # Remove device data
        mock_coordinator.data["devices"]["site1"]["device1"] = None

        assert sensor.is_on is None


class TestUnifiProtectBinarySensor:
    """Tests for UnifiProtectBinarySensor."""

    @pytest.fixture
    def mock_coordinator(self, hass: HomeAssistant):
        """Create mock coordinator."""
        coordinator = MagicMock()
        coordinator.hass = hass
        coordinator.network_client = MagicMock()
        coordinator.network_client.base_url = "https://192.168.1.1"
        coordinator.protect_client = MagicMock()
        coordinator.protect_client.base_url = "https://192.168.1.1"
        coordinator.data = {
            "sites": {},
            "devices": {},
            "stats": {},
            "clients": {},
            "protect": {
                "cameras": {
                    "camera1": {
                        "id": "camera1",
                        "name": "Front Camera",
                        "state": "CONNECTED",
                        "type": "UVC-G4-PRO",
                        # Supported smart detect types in featureFlags (like real API)
                        "featureFlags": {
                            "smartDetectTypes": ["person", "vehicle"],
                        },
                        "isMotionDetected": False,
                        "isSmartDetected": False,
                        "lastSmartDetectTypes": [],
                        "lastMotionStart": None,
                        "lastMotionEnd": None,
                        "lastRingStart": None,
                        "lastRingEnd": None,
                    },
                    "camera2": {
                        "id": "camera2",
                        "name": "Doorbell",
                        "state": "CONNECTED",
                        "_camera_type": "doorbell",
                        "type": "G4-Doorbell",
                        # Supported smart detect types in featureFlags (like real API)
                        "featureFlags": {
                            "smartDetectTypes": ["person", "package"],
                        },
                        # Active detection state
                        "isMotionDetected": True,
                        "isSmartDetected": True,
                        "lastSmartDetectTypes": ["person"],
                        "lastMotionStart": 1234567890,
                        "lastMotionEnd": None,
                        "lastRingStart": 1234567800,
                        "lastRingEnd": None,
                    },
                },
                "lights": {},
                "sensors": {
                    "sensor1": {
                        "id": "sensor1",
                        "name": "Door Sensor",
                        "state": "CONNECTED",
                        "isMotionDetected": True,
                        "motionDetectedAt": 1234567890,
                        "isOpened": True,
                        "openStatusChangedAt": 1234567800,
                        "isTamperingDetected": True,
                        "tamperingDetectedAt": 1234567850,
                        "isLeakDetected": False,
                        "leakDetectedAt": 0,
                    },
                    "sensor2": {
                        "id": "sensor2",
                        "name": "Water Leak Sensor",
                        "state": "CONNECTED",
                        "isMotionDetected": False,
                        "motionDetectedAt": 0,
                        "isOpened": False,
                        "openStatusChangedAt": 0,
                        "isTamperingDetected": False,
                        "tamperingDetectedAt": 0,
                        "isLeakDetected": True,
                        "leakDetectedAt": 1234567900,
                    },
                },
                "nvrs": {},
                "viewers": {},
                "chimes": {},
                "liveviews": {},
            },
        }
        return coordinator

    async def test_camera_motion_no_motion(self, hass: HomeAssistant, mock_coordinator):
        """Test camera motion sensor when no motion."""
        description = next(s for s in BINARY_SENSOR_TYPES if s.key == "camera_motion")

        sensor = UnifiProtectBinarySensor(
            coordinator=mock_coordinator,
            description=description,
            device_id="camera1",
        )

        assert sensor.is_on is False

    async def test_camera_motion_with_motion(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test camera motion sensor with active motion."""
        description = next(s for s in BINARY_SENSOR_TYPES if s.key == "camera_motion")

        sensor = UnifiProtectBinarySensor(
            coordinator=mock_coordinator,
            description=description,
            device_id="camera2",
        )

        assert sensor.is_on is True

    async def test_camera_person_detection_no_person(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test person detection when no person."""
        description = next(
            s for s in BINARY_SENSOR_TYPES if s.key == "camera_person_detection"
        )

        sensor = UnifiProtectBinarySensor(
            coordinator=mock_coordinator,
            description=description,
            device_id="camera1",
        )

        assert sensor.is_on is False

    async def test_camera_person_detection_with_person(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test person detection with active person detection."""
        description = next(
            s for s in BINARY_SENSOR_TYPES if s.key == "camera_person_detection"
        )

        sensor = UnifiProtectBinarySensor(
            coordinator=mock_coordinator,
            description=description,
            device_id="camera2",
        )

        assert sensor.is_on is True

    async def test_camera_doorbell_ring(self, hass: HomeAssistant, mock_coordinator):
        """Test doorbell ring detection."""
        description = next(
            s for s in BINARY_SENSOR_TYPES if s.key == "camera_doorbell_ring"
        )

        sensor = UnifiProtectBinarySensor(
            coordinator=mock_coordinator,
            description=description,
            device_id="camera2",
        )

        assert sensor.is_on is True

    async def test_sensor_motion_detected(self, hass: HomeAssistant, mock_coordinator):
        """Test sensor motion detection."""
        description = next(s for s in BINARY_SENSOR_TYPES if s.key == "sensor_motion")

        sensor = UnifiProtectBinarySensor(
            coordinator=mock_coordinator,
            description=description,
            device_id="sensor1",
        )

        assert sensor.is_on is True

    async def test_sensor_door_opened(self, hass: HomeAssistant, mock_coordinator):
        """Test sensor door status."""
        description = next(s for s in BINARY_SENSOR_TYPES if s.key == "sensor_door")

        sensor = UnifiProtectBinarySensor(
            coordinator=mock_coordinator,
            description=description,
            device_id="sensor1",
        )

        assert sensor.is_on is True

    async def test_sensor_tamper_detected(self, hass: HomeAssistant, mock_coordinator):
        """Test sensor tamper detection."""
        description = next(s for s in BINARY_SENSOR_TYPES if s.key == "sensor_tamper")

        sensor = UnifiProtectBinarySensor(
            coordinator=mock_coordinator,
            description=description,
            device_id="sensor1",
        )

        assert sensor.is_on is True

    async def test_sensor_tamper_not_detected(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test sensor tamper when not detected."""
        description = next(s for s in BINARY_SENSOR_TYPES if s.key == "sensor_tamper")

        sensor = UnifiProtectBinarySensor(
            coordinator=mock_coordinator,
            description=description,
            device_id="sensor2",
        )

        assert sensor.is_on is False

    async def test_sensor_leak_detected(self, hass: HomeAssistant, mock_coordinator):
        """Test leak sensor detection."""
        description = next(s for s in BINARY_SENSOR_TYPES if s.key == "sensor_leak")

        sensor = UnifiProtectBinarySensor(
            coordinator=mock_coordinator,
            description=description,
            device_id="sensor2",
        )

        assert sensor.is_on is True

    async def test_sensor_leak_not_detected(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test leak sensor when no leak detected."""
        description = next(s for s in BINARY_SENSOR_TYPES if s.key == "sensor_leak")

        sensor = UnifiProtectBinarySensor(
            coordinator=mock_coordinator,
            description=description,
            device_id="sensor1",
        )

        assert sensor.is_on is False

    async def test_protect_sensor_no_data(self, hass: HomeAssistant, mock_coordinator):
        """Test protect sensor when data removed."""
        description = next(s for s in BINARY_SENSOR_TYPES if s.key == "camera_motion")

        sensor = UnifiProtectBinarySensor(
            coordinator=mock_coordinator,
            description=description,
            device_id="camera1",
        )

        # Remove camera data
        mock_coordinator.data["protect"]["cameras"]["camera1"] = None

        assert sensor.is_on is None


class TestAsyncSetupEntry:
    """Tests for async_setup_entry."""

    @pytest.fixture
    def mock_coordinator(self, hass: HomeAssistant):
        """Create mock coordinator."""
        coordinator = MagicMock()
        coordinator.hass = hass
        coordinator.network_client = MagicMock()
        coordinator.network_client.base_url = "https://192.168.1.1"
        coordinator.protect_client = MagicMock()
        coordinator.protect_client.base_url = "https://192.168.1.1"
        coordinator.data = {
            "sites": {"site1": {"id": "site1"}},
            "devices": {
                "site1": {
                    "device1": {
                        "id": "device1",
                        "name": "Test Device",
                        "model": "USW-24-POE",
                        "state": "ONLINE",
                        "macAddress": "AA:BB:CC:DD:EE:FF",
                        "ipAddress": "192.168.1.10",
                        "firmwareVersion": "6.5.55",
                    },
                },
            },
            "stats": {},
            "clients": {},
            "protect": {
                "cameras": {
                    "camera1": {
                        "id": "camera1",
                        "name": "Front Door",
                        "state": "CONNECTED",
                        "type": "UVC-G4-PRO",
                        "smartDetectTypes": ["person"],
                        "lastSmartDetectTypes": [],
                        "lastMotionStart": None,
                        "lastMotionEnd": None,
                    },
                },
                "lights": {},
                "sensors": {
                    "sensor1": {
                        "id": "sensor1",
                        "name": "Door Sensor",
                        "state": "CONNECTED",
                    },
                },
                "nvrs": {},
                "viewers": {},
                "chimes": {},
                "liveviews": {},
            },
        }
        return coordinator

    @pytest.fixture
    def mock_config_entry(self, mock_coordinator):
        """Create mock config entry."""
        entry = MagicMock()
        entry.runtime_data = MagicMock()
        entry.runtime_data.coordinator = mock_coordinator
        return entry

    async def test_setup_entry_creates_sensors(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Test that setup entry creates binary sensors."""
        added_entities: list = []

        def add_entities(new_entities, **kwargs):
            added_entities.extend(new_entities)

        await async_setup_entry(hass, mock_config_entry, add_entities)

        assert len(added_entities) > 0

    async def test_setup_entry_creates_device_sensors(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Test that setup creates device binary sensors."""
        added_entities: list = []

        def add_entities(new_entities, **kwargs):
            added_entities.extend(new_entities)

        await async_setup_entry(hass, mock_config_entry, add_entities)

        device_sensors = [
            e for e in added_entities if isinstance(e, UnifiInsightsBinarySensor)
        ]
        assert len(device_sensors) > 0

    async def test_setup_entry_creates_protect_sensors(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Test that setup creates protect binary sensors."""
        added_entities: list = []

        def add_entities(new_entities, **kwargs):
            added_entities.extend(new_entities)

        await async_setup_entry(hass, mock_config_entry, add_entities)

        protect_sensors = [
            e for e in added_entities if isinstance(e, UnifiProtectBinarySensor)
        ]
        assert len(protect_sensors) > 0

    async def test_setup_entry_without_protect_client(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Test setup without protect client."""
        mock_coordinator.protect_client = None

        added_entities: list = []

        def add_entities(new_entities, **kwargs):
            added_entities.extend(new_entities)

        await async_setup_entry(hass, mock_config_entry, add_entities)

        # Should still create device sensors
        device_sensors = [
            e for e in added_entities if isinstance(e, UnifiInsightsBinarySensor)
        ]
        assert len(device_sensors) > 0

        # But no protect sensors
        protect_sensors = [
            e for e in added_entities if isinstance(e, UnifiProtectBinarySensor)
        ]
        assert len(protect_sensors) == 0
