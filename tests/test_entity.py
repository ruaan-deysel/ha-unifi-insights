"""Tests for UniFi Insights entity base classes."""

from unittest.mock import MagicMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from homeassistant.helpers.entity import EntityDescription

from custom_components.unifi_insights.const import (
    DEVICE_TYPE_CAMERA,
    DEVICE_TYPE_LIGHT,
    DEVICE_TYPE_SENSOR,
    DOMAIN,
    MANUFACTURER,
)
from custom_components.unifi_insights.entity import (
    UnifiInsightsEntity,
    UnifiProtectEntity,
    get_field,
    is_device_online,
)


class TestGetField:
    """Tests for get_field helper function."""

    def test_get_field_first_key_found(self):
        """Test get_field returns value for first matching key."""
        data = {"key1": "value1", "key2": "value2"}
        assert get_field(data, "key1", "key2") == "value1"

    def test_get_field_second_key_found(self):
        """Test get_field returns value for second key when first missing."""
        data = {"key2": "value2"}
        assert get_field(data, "key1", "key2") == "value2"

    def test_get_field_no_keys_found(self):
        """Test get_field returns default when no keys found."""
        data = {"other": "value"}
        assert get_field(data, "key1", "key2", default="default") == "default"

    def test_get_field_none_value(self):
        """Test get_field returns None value when key exists with None."""
        data = {"key1": None}
        assert get_field(data, "key1", default="default") is None

    def test_get_field_no_default(self):
        """Test get_field returns None when no default specified."""
        data = {"other": "value"}
        assert get_field(data, "key1") is None

    def test_get_field_camelcase_and_snake_case(self):
        """Test get_field handles both camelCase and snake_case."""
        data_camel = {"firmwareVersion": "1.0.0"}
        data_snake = {"firmware_version": "2.0.0"}

        assert get_field(data_camel, "firmwareVersion", "firmware_version") == "1.0.0"
        assert get_field(data_snake, "firmwareVersion", "firmware_version") == "2.0.0"


class TestIsDeviceOnline:
    """Tests for is_device_online helper function."""

    def test_is_device_online_state_online(self):
        """Test device is online with state ONLINE."""
        data = {"state": "ONLINE"}
        assert is_device_online(data) is True

    def test_is_device_online_state_connected(self):
        """Test device is online with state CONNECTED."""
        data = {"state": "CONNECTED"}
        assert is_device_online(data) is True

    def test_is_device_online_state_up(self):
        """Test device is online with state UP."""
        data = {"state": "UP"}
        assert is_device_online(data) is True

    def test_is_device_online_status_online(self):
        """Test device is online with status online."""
        data = {"status": "online"}
        assert is_device_online(data) is True

    def test_is_device_online_state_offline(self):
        """Test device is offline with state OFFLINE."""
        data = {"state": "OFFLINE"}
        assert is_device_online(data) is False

    def test_is_device_online_state_disconnected(self):
        """Test device is offline with state DISCONNECTED."""
        data = {"state": "DISCONNECTED"}
        assert is_device_online(data) is False

    def test_is_device_online_empty(self):
        """Test device is offline with empty data."""
        data = {}
        assert is_device_online(data) is False

    def test_is_device_online_lowercase(self):
        """Test device is online with lowercase status."""
        data = {"state": "online"}
        assert is_device_online(data) is True

    def test_is_device_online_non_string_state(self):
        """Test device is offline when state is not a string (returns False)."""
        # Non-string state values should return False (covers line 48)
        data_int = {"state": 123}
        assert is_device_online(data_int) is False

        data_list = {"state": ["online"]}
        assert is_device_online(data_list) is False

        data_dict = {"state": {"value": "online"}}
        assert is_device_online(data_dict) is False

        data_none = {"state": None}
        assert is_device_online(data_none) is False


class TestUnifiInsightsEntity:
    """Tests for UnifiInsightsEntity base class."""

    @pytest.fixture
    def mock_coordinator(self, hass: HomeAssistant):
        """Create mock coordinator with test data."""
        coordinator = MagicMock()
        coordinator.hass = hass
        coordinator.network_client = MagicMock()
        coordinator.network_client.base_url = "https://192.168.1.1"
        coordinator.data = {
            "sites": {
                "site1": {"id": "site1", "meta": {"name": "Default"}},
            },
            "devices": {
                "site1": {
                    "device1": {
                        "id": "device1",
                        "name": "Test Switch",
                        "model": "USW-24-POE",
                        "firmwareVersion": "6.5.55",
                        "macAddress": "AA:BB:CC:DD:EE:FF",
                        "ipAddress": "192.168.1.10",
                        "state": "ONLINE",
                    },
                    "device2": {
                        "id": "device2",
                        "name": "Test AP",
                        "model": "UAP-AC-PRO",
                        "state": "OFFLINE",
                    },
                },
            },
            "stats": {},
            "clients": {},
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

    async def test_entity_initialization(self, hass: HomeAssistant, mock_coordinator):
        """Test entity initializes correctly."""
        description = EntityDescription(key="test_key", name="Test Sensor")

        entity = UnifiInsightsEntity(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
        )

        assert entity._site_id == "site1"
        assert entity._device_id == "device1"
        assert entity.entity_description == description

    async def test_entity_unique_id(self, hass: HomeAssistant, mock_coordinator):
        """Test entity unique ID format."""
        description = EntityDescription(key="cpu_usage", name="CPU Usage")

        entity = UnifiInsightsEntity(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
        )

        assert entity.unique_id == "site1_device1_cpu_usage"

    async def test_entity_device_info(self, hass: HomeAssistant, mock_coordinator):
        """Test entity device info."""
        description = EntityDescription(key="test", name="Test")

        entity = UnifiInsightsEntity(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
        )

        device_info = entity.device_info
        assert (DOMAIN, "site1_device1") in device_info["identifiers"]
        assert device_info["manufacturer"] == MANUFACTURER
        assert device_info["model"] == "USW-24-POE"
        assert device_info["sw_version"] == "6.5.55"

    async def test_entity_available_online(self, hass: HomeAssistant, mock_coordinator):
        """Test entity is available when device is online."""
        description = EntityDescription(key="test", name="Test")

        entity = UnifiInsightsEntity(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
        )

        assert entity.available is True

    async def test_entity_available_offline(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test entity is unavailable when device is offline."""
        description = EntityDescription(key="test", name="Test")

        entity = UnifiInsightsEntity(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device2",  # This device is OFFLINE
        )

        assert entity.available is False

    async def test_entity_device_data(self, hass: HomeAssistant, mock_coordinator):
        """Test entity device_data property."""
        description = EntityDescription(key="test", name="Test")

        entity = UnifiInsightsEntity(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
        )

        device_data = entity.device_data
        assert device_data["id"] == "device1"
        assert device_data["name"] == "Test Switch"

    async def test_entity_device_stats(self, hass: HomeAssistant, mock_coordinator):
        """Test entity device_stats property."""
        mock_coordinator.data["stats"]["site1"] = {
            "device1": {"cpuUtilizationPct": 25.5},
        }
        description = EntityDescription(key="test", name="Test")

        entity = UnifiInsightsEntity(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
        )

        stats = entity.device_stats
        assert stats["cpuUtilizationPct"] == 25.5

    async def test_entity_mac_connection(self, hass: HomeAssistant, mock_coordinator):
        """Test entity includes MAC address connection."""
        description = EntityDescription(key="test", name="Test")

        entity = UnifiInsightsEntity(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
        )

        device_info = entity.device_info
        assert "connections" in device_info
        connections = device_info["connections"]
        assert (CONNECTION_NETWORK_MAC, "AA:BB:CC:DD:EE:FF") in connections


class TestUnifiProtectEntity:
    """Tests for UnifiProtectEntity base class."""

    @pytest.fixture
    def mock_coordinator(self, hass: HomeAssistant):
        """Create mock coordinator with protect data."""
        coordinator = MagicMock()
        coordinator.hass = hass
        coordinator.network_client = MagicMock()
        coordinator.network_client.base_url = "https://192.168.1.1"
        coordinator.protect_client = MagicMock()
        coordinator.protect_client.base_url = "https://192.168.1.1"
        coordinator.data = {
            "sites": {},
            "devices": {
                "site1": {
                    "device1": {
                        "id": "device1",
                        "name": "UDM Pro",
                        "macAddress": "AA:BB:CC:DD:EE:FF",
                        "model": "UDM-PRO",
                        "firmwareVersion": "2.0.0",
                        "ipAddress": "192.168.1.1",
                        "state": "ONLINE",
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
                        "mac": "AA:BB:CC:DD:EE:FF",
                        "type": "UVC-G4-PRO",
                        "firmwareVersion": "4.50.0",
                    },
                    "camera2": {
                        "id": "camera2",
                        "name": "Backyard",
                        "state": "DISCONNECTED",
                        "type": "UVC-G3-FLEX",
                    },
                },
                "lights": {
                    "light1": {
                        "id": "light1",
                        "name": "Garage Light",
                        "state": "CONNECTED",
                        "type": "UP-FLOODLIGHT",
                    },
                },
                "sensors": {
                    "sensor1": {
                        "id": "sensor1",
                        "name": "Front Door Sensor",
                        "state": "CONNECTED",
                        "type": "UP-SENSE",
                    },
                },
                "nvrs": {},
                "viewers": {},
                "chimes": {},
                "liveviews": {},
            },
        }
        return coordinator

    async def test_protect_entity_initialization(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test protect entity initializes correctly."""
        entity = UnifiProtectEntity(
            coordinator=mock_coordinator,
            device_type=DEVICE_TYPE_CAMERA,
            device_id="camera1",
        )

        assert entity._device_type == DEVICE_TYPE_CAMERA
        assert entity._device_id == "camera1"

    async def test_protect_entity_unique_id(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test protect entity unique ID format."""
        entity = UnifiProtectEntity(
            coordinator=mock_coordinator,
            device_type=DEVICE_TYPE_CAMERA,
            device_id="camera1",
        )

        assert entity.unique_id == f"{DOMAIN}_camera_camera1"

    async def test_protect_entity_unique_id_with_type(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test protect entity unique ID with entity type."""
        entity = UnifiProtectEntity(
            coordinator=mock_coordinator,
            device_type=DEVICE_TYPE_CAMERA,
            device_id="camera1",
            entity_type="motion",
        )

        assert entity.unique_id == f"{DOMAIN}_camera_camera1_motion"

    async def test_protect_entity_available_connected(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test protect entity is available when connected."""
        entity = UnifiProtectEntity(
            coordinator=mock_coordinator,
            device_type=DEVICE_TYPE_CAMERA,
            device_id="camera1",
        )

        assert entity.available is True

    async def test_protect_entity_available_disconnected(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test protect entity is unavailable when disconnected."""
        entity = UnifiProtectEntity(
            coordinator=mock_coordinator,
            device_type=DEVICE_TYPE_CAMERA,
            device_id="camera2",
        )

        assert entity.available is False

    async def test_protect_entity_device_data(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test protect entity device_data property."""
        entity = UnifiProtectEntity(
            coordinator=mock_coordinator,
            device_type=DEVICE_TYPE_CAMERA,
            device_id="camera1",
        )

        device_data = entity.device_data
        assert device_data["id"] == "camera1"
        assert device_data["name"] == "Front Door"

    async def test_protect_entity_device_info(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test protect entity device info."""
        entity = UnifiProtectEntity(
            coordinator=mock_coordinator,
            device_type=DEVICE_TYPE_CAMERA,
            device_id="camera1",
        )

        device_info = entity.device_info
        assert device_info["manufacturer"] == MANUFACTURER

    async def test_protect_entity_light_type(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test protect entity for light type."""
        entity = UnifiProtectEntity(
            coordinator=mock_coordinator,
            device_type=DEVICE_TYPE_LIGHT,
            device_id="light1",
        )

        assert entity._device_type == DEVICE_TYPE_LIGHT
        assert entity.available is True

    async def test_protect_entity_sensor_type(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test protect entity for sensor type."""
        entity = UnifiProtectEntity(
            coordinator=mock_coordinator,
            device_type=DEVICE_TYPE_SENSOR,
            device_id="sensor1",
        )

        assert entity._device_type == DEVICE_TYPE_SENSOR
        assert entity.available is True

    async def test_protect_entity_network_device_matching(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test protect entity matches network device by MAC address."""
        # Camera with MAC that matches a network device
        entity = UnifiProtectEntity(
            coordinator=mock_coordinator,
            device_type=DEVICE_TYPE_CAMERA,
            device_id="camera1",  # Has MAC AA:BB:CC:DD:EE:FF matching device1
        )

        # Should use network device identifiers
        device_info = entity.device_info
        identifiers = device_info.get("identifiers", set())
        # Should match network device site1_device1
        assert (DOMAIN, "site1_device1") in identifiers

    async def test_protect_entity_nvr_network_device_matching(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test protect NVR entity matches network device by MAC (UDM-Pro fix)."""
        # Add NVR with MAC that matches a network device (like UDM-Pro)
        mock_coordinator.data["protect"]["nvrs"]["nvr1"] = {
            "id": "nvr1",
            "name": "UDM-Pro NVR",
            "state": "CONNECTED",
            "mac": "AA:BB:CC:DD:EE:FF",  # Same MAC as device1
        }

        entity = UnifiProtectEntity(
            coordinator=mock_coordinator,
            device_type="nvr",
            device_id="nvr1",
        )

        # Should use network device identifiers - both NVR and network device
        # entities should appear under the same device in HA
        device_info = entity.device_info
        identifiers = device_info.get("identifiers", set())
        # Should match network device site1_device1
        assert (DOMAIN, "site1_device1") in identifiers

    async def test_protect_entity_no_network_match(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test protect entity without matching network device."""
        # Camera2 has no MAC address
        entity = UnifiProtectEntity(
            coordinator=mock_coordinator,
            device_type=DEVICE_TYPE_CAMERA,
            device_id="camera2",
        )

        # Should create its own device entry
        device_info = entity.device_info
        identifiers = device_info.get("identifiers", set())
        assert (DOMAIN, "protect_camera_camera2") in identifiers

    async def test_protect_entity_dual_camera_parent(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test protect entity handles dual-camera parent ID."""
        # Add a camera with _parent_camera_id
        mock_coordinator.data["protect"]["cameras"]["camera_pkg"] = {
            "id": "camera_pkg",
            "name": "Front Door Package Camera",
            "state": "CONNECTED",
            "type": "UVC-G4-DOORBELL",
            "_parent_camera_id": "camera_main",
            "_is_package_camera": True,
        }
        mock_coordinator.data["protect"]["cameras"]["camera_main"] = {
            "id": "camera_main",
            "name": "Front Door Main Camera",
            "state": "CONNECTED",
            "type": "UVC-G4-DOORBELL",
            "mac": "11:22:33:44:55:66",
        }

        entity = UnifiProtectEntity(
            coordinator=mock_coordinator,
            device_type=DEVICE_TYPE_CAMERA,
            device_id="camera_pkg",
        )

        # Should use parent camera ID in device identifiers
        device_info = entity.device_info
        identifiers = device_info.get("identifiers", set())
        # Uses parent ID for grouping
        assert (DOMAIN, "protect_camera_camera_main") in identifiers

    async def test_protect_entity_dual_camera_package_name_stripping(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test protect entity strips Package Camera suffix (line 211)."""
        # Add a package camera with " Package Camera" suffix but NO " Main Camera"
        # This specifically tests the elif branch at line 211
        mock_coordinator.data["protect"]["cameras"]["camera_pkg2"] = {
            "id": "camera_pkg2",
            # Has " Package Camera" but NOT " Main Camera"
            "name": "Garage Package Camera",
            "state": "CONNECTED",
            "type": "UVC-G4-PRO",
            # Has parent so stripping logic runs
            "_parent_camera_id": "camera_garage_main",
            "_is_package_camera": True,
        }
        # Add the parent camera
        mock_coordinator.data["protect"]["cameras"]["camera_garage_main"] = {
            "id": "camera_garage_main",
            "name": "Garage",
            "state": "CONNECTED",
            "type": "UVC-G4-PRO",
        }

        entity = UnifiProtectEntity(
            coordinator=mock_coordinator,
            device_type=DEVICE_TYPE_CAMERA,
            device_id="camera_pkg2",
        )

        # The device name should be stripped of " Package Camera" suffix
        # device_info.name should be "Garage" not "Garage Package Camera"
        device_info = entity.device_info
        assert "Package Camera" not in device_info.get("name", "")

    async def test_protect_entity_dual_camera_main_name_stripping(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test protect entity strips Main Camera suffix (line 209)."""
        # Add a main camera with " Main Camera" suffix AND _parent_camera_id
        # This specifically tests the if branch at line 209 (when the entity
        # itself has " Main Camera" in its name but is referencing a parent)
        mock_coordinator.data["protect"]["cameras"]["camera_main_sub"] = {
            "id": "camera_main_sub",
            "name": "Backyard Main Camera",  # Has " Main Camera"
            "state": "CONNECTED",
            "type": "UVC-G4-PRO",
            "_parent_camera_id": "camera_backyard_parent",  # Has parent ID
        }
        # Add the parent camera
        mock_coordinator.data["protect"]["cameras"]["camera_backyard_parent"] = {
            "id": "camera_backyard_parent",
            "name": "Backyard",
            "state": "CONNECTED",
            "type": "UVC-G4-PRO",
        }

        entity = UnifiProtectEntity(
            coordinator=mock_coordinator,
            device_type=DEVICE_TYPE_CAMERA,
            device_id="camera_main_sub",
        )

        # The device name should be stripped of " Main Camera" suffix
        # device_info.name should be "Backyard" not "Backyard Main Camera"
        device_info = entity.device_info
        assert "Main Camera" not in device_info.get("name", "")
        assert device_info.get("name") == "Backyard"

    async def test_protect_entity_available_non_dict(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test protect entity available with non-dict device data."""
        # Create entity with valid data first
        entity = UnifiProtectEntity(
            coordinator=mock_coordinator,
            device_type=DEVICE_TYPE_CAMERA,
            device_id="camera1",
        )

        # Now set device data to non-dict
        mock_coordinator.data["protect"]["cameras"]["camera1"] = "not a dict"

        assert entity.available is False

    async def test_protect_entity_device_data_non_dict(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test protect entity device_data with non-dict value."""
        # Set device data to non-dict
        mock_coordinator.data["protect"]["cameras"]["camera_test"] = "not a dict"

        # Need to create entity with valid data first
        mock_coordinator.data["protect"]["cameras"]["camera_test"] = {
            "id": "camera_test",
            "name": "Test",
            "state": "CONNECTED",
            "type": "UVC-G4",
        }
        entity = UnifiProtectEntity(
            coordinator=mock_coordinator,
            device_type=DEVICE_TYPE_CAMERA,
            device_id="camera_test",
        )

        # Now change to non-dict
        mock_coordinator.data["protect"]["cameras"]["camera_test"] = "not a dict"

        assert entity.device_data is None

    async def test_protect_entity_suggested_area_camera(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test protect camera entity gets Security suggested area."""
        # Camera without network device match
        mock_coordinator.data["protect"]["cameras"]["camera_new"] = {
            "id": "camera_new",
            "name": "New Camera",
            "state": "CONNECTED",
            "type": "UVC-G4-PRO",
        }

        entity = UnifiProtectEntity(
            coordinator=mock_coordinator,
            device_type=DEVICE_TYPE_CAMERA,
            device_id="camera_new",
        )

        device_info = entity.device_info
        assert device_info.get("suggested_area") == "Security"

    async def test_protect_entity_suggested_area_light(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test protect light entity gets Exterior suggested area."""
        # Light without network device match
        entity = UnifiProtectEntity(
            coordinator=mock_coordinator,
            device_type=DEVICE_TYPE_LIGHT,
            device_id="light1",
        )

        device_info = entity.device_info
        assert device_info.get("suggested_area") == "Exterior"

    async def test_protect_entity_suggested_area_sensor(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test protect sensor entity gets Security suggested area."""
        entity = UnifiProtectEntity(
            coordinator=mock_coordinator,
            device_type=DEVICE_TYPE_SENSOR,
            device_id="sensor1",
        )

        device_info = entity.device_info
        assert device_info.get("suggested_area") == "Security"


class TestUnifiInsightsEntityEdgeCases:
    """Tests for edge cases in UnifiInsightsEntity."""

    @pytest.fixture
    def mock_coordinator_with_ports(self, hass: HomeAssistant):
        """Create mock coordinator with port and radio data."""
        coordinator = MagicMock()
        coordinator.hass = hass
        coordinator.network_client = MagicMock()
        coordinator.network_client.base_url = "https://192.168.1.1"
        coordinator.data = {
            "sites": {"site1": {"id": "site1"}},
            "devices": {
                "site1": {
                    "switch1": {
                        "id": "switch1",
                        "name": "Main Switch",
                        "model": "USW-24-POE",
                        "state": "ONLINE",
                        "port_table": [
                            {"port_idx": 1, "name": "Port 1"},
                            {"port_idx": 2, "name": "Port 2"},
                        ],
                    },
                    "ap1": {
                        "id": "ap1",
                        "name": "Access Point",
                        "model": "UAP-AC-PRO",
                        "state": "ONLINE",
                        "radio_table": [
                            {"name": "ra0", "radio": "ng"},
                            {"name": "rai0", "radio": "na"},
                        ],
                    },
                    "device_minimal": {
                        "id": "device_minimal",
                        "model": "Unknown",
                        "state": "ONLINE",
                    },
                },
            },
            "stats": {},
            "clients": {},
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

    async def test_entity_with_port_table(
        self, hass: HomeAssistant, mock_coordinator_with_ports
    ):
        """Test entity with port_table gets hw_version."""
        description = EntityDescription(key="test", name="Test")

        entity = UnifiInsightsEntity(
            coordinator=mock_coordinator_with_ports,
            description=description,
            site_id="site1",
            device_id="switch1",
        )

        device_info = entity.device_info
        assert "hw_version" in device_info
        assert "2 Ports" in device_info["hw_version"]

    async def test_entity_with_radio_table(
        self, hass: HomeAssistant, mock_coordinator_with_ports
    ):
        """Test entity with radio_table gets hw_version."""
        description = EntityDescription(key="test", name="Test")

        entity = UnifiInsightsEntity(
            coordinator=mock_coordinator_with_ports,
            description=description,
            site_id="site1",
            device_id="ap1",
        )

        device_info = entity.device_info
        assert "hw_version" in device_info
        assert "ra0 (ng)" in device_info["hw_version"]
        assert "rai0 (na)" in device_info["hw_version"]

    async def test_entity_without_name(
        self, hass: HomeAssistant, mock_coordinator_with_ports
    ):
        """Test entity without device name uses fallback."""
        description = EntityDescription(key="test", name="Test")

        entity = UnifiInsightsEntity(
            coordinator=mock_coordinator_with_ports,
            description=description,
            site_id="site1",
            device_id="device_minimal",
        )

        device_info = entity.device_info
        # Should have a name (either from device or fallback)
        assert "name" in device_info

    async def test_entity_device_data_missing(
        self, hass: HomeAssistant, mock_coordinator_with_ports
    ):
        """Test entity device_data when device is missing."""
        description = EntityDescription(key="test", name="Test")

        entity = UnifiInsightsEntity(
            coordinator=mock_coordinator_with_ports,
            description=description,
            site_id="site1",
            device_id="switch1",
        )

        # Remove device from data
        del mock_coordinator_with_ports.data["devices"]["site1"]["switch1"]

        assert entity.device_data is None

    async def test_entity_device_stats_non_dict(
        self, hass: HomeAssistant, mock_coordinator_with_ports
    ):
        """Test entity device_stats returns None for non-dict."""
        description = EntityDescription(key="test", name="Test")

        entity = UnifiInsightsEntity(
            coordinator=mock_coordinator_with_ports,
            description=description,
            site_id="site1",
            device_id="switch1",
        )

        # Set stats to non-dict
        mock_coordinator_with_ports.data["stats"]["site1"] = {"switch1": "not a dict"}

        assert entity.device_stats is None

    async def test_entity_available_missing_device(
        self, hass: HomeAssistant, mock_coordinator_with_ports
    ):
        """Test entity available when device is missing."""
        description = EntityDescription(key="test", name="Test")

        entity = UnifiInsightsEntity(
            coordinator=mock_coordinator_with_ports,
            description=description,
            site_id="site1",
            device_id="switch1",
        )

        # Remove device from data
        del mock_coordinator_with_ports.data["devices"]["site1"]["switch1"]

        assert entity.available is False

    async def test_entity_handle_coordinator_update(
        self, hass: HomeAssistant, mock_coordinator_with_ports
    ):
        """Test entity _handle_coordinator_update."""
        description = EntityDescription(key="test", name="Test")

        entity = UnifiInsightsEntity(
            coordinator=mock_coordinator_with_ports,
            description=description,
            site_id="site1",
            device_id="switch1",
        )

        # Mock async_write_ha_state
        entity.async_write_ha_state = MagicMock()

        # Call update handler
        entity._handle_coordinator_update()

        # Should have called async_write_ha_state
        entity.async_write_ha_state.assert_called()

    async def test_entity_handle_coordinator_update_missing_device(
        self, hass: HomeAssistant, mock_coordinator_with_ports
    ):
        """Test entity _handle_coordinator_update with missing device."""
        description = EntityDescription(key="test", name="Test")

        entity = UnifiInsightsEntity(
            coordinator=mock_coordinator_with_ports,
            description=description,
            site_id="site1",
            device_id="switch1",
        )

        # Mock async_write_ha_state
        entity.async_write_ha_state = MagicMock()

        # Remove device from data
        del mock_coordinator_with_ports.data["devices"]["site1"]["switch1"]

        # Call update handler
        entity._handle_coordinator_update()

        # Should set available to False
        assert entity._attr_available is False
        entity.async_write_ha_state.assert_called()

    async def test_entity_suggested_area_switch(
        self, hass: HomeAssistant, mock_coordinator_with_ports
    ):
        """Test entity with switch model gets Network suggested area."""
        description = EntityDescription(key="test", name="Test")

        entity = UnifiInsightsEntity(
            coordinator=mock_coordinator_with_ports,
            description=description,
            site_id="site1",
            device_id="switch1",
        )

        device_info = entity.device_info
        assert device_info.get("suggested_area") == "Network"

    async def test_entity_suggested_area_ap(
        self, hass: HomeAssistant, mock_coordinator_with_ports
    ):
        """Test entity with AP model gets Network suggested area."""
        description = EntityDescription(key="test", name="Test")

        entity = UnifiInsightsEntity(
            coordinator=mock_coordinator_with_ports,
            description=description,
            site_id="site1",
            device_id="ap1",
        )

        device_info = entity.device_info
        assert device_info.get("suggested_area") == "Network"

    async def test_entity_empty_port_table(
        self, hass: HomeAssistant, mock_coordinator_with_ports
    ):
        """Test entity with empty port_table."""
        # Add device with empty port_table
        mock_coordinator_with_ports.data["devices"]["site1"]["switch_empty"] = {
            "id": "switch_empty",
            "name": "Empty Switch",
            "model": "USW",
            "state": "ONLINE",
            "port_table": [],
        }

        description = EntityDescription(key="test", name="Test")

        entity = UnifiInsightsEntity(
            coordinator=mock_coordinator_with_ports,
            description=description,
            site_id="site1",
            device_id="switch_empty",
        )

        device_info = entity.device_info
        # hw_version should not include ports if empty
        hw_version = device_info.get("hw_version", "")
        assert "Ports" not in hw_version

    async def test_entity_radio_table_non_dict_entry(
        self, hass: HomeAssistant, mock_coordinator_with_ports
    ):
        """Test entity handles non-dict entries in radio_table."""
        # Add device with mixed radio_table
        mock_coordinator_with_ports.data["devices"]["site1"]["ap_mixed"] = {
            "id": "ap_mixed",
            "name": "Mixed AP",
            "model": "UAP",
            "state": "ONLINE",
            "radio_table": [
                {"name": "ra0", "radio": "ng"},
                "not a dict",  # Invalid entry
                None,  # Another invalid entry
            ],
        }

        description = EntityDescription(key="test", name="Test")

        entity = UnifiInsightsEntity(
            coordinator=mock_coordinator_with_ports,
            description=description,
            site_id="site1",
            device_id="ap_mixed",
        )

        device_info = entity.device_info
        hw_version = device_info.get("hw_version", "")
        # Should only include valid radio entry
        assert "ra0 (ng)" in hw_version
