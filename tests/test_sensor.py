"""Tests for UniFi Insights sensors."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant

from custom_components.unifi_insights.sensor import (
    NVR_SENSOR_TYPES,
    PARALLEL_UPDATES,
    PORT_SENSOR_TYPES,
    PROTECT_SENSOR_TYPES,
    SENSOR_TYPES,
    UnifiInsightsSensor,
    UnifiPortSensor,
    UnifiProtectNVRSensor,
    UnifiProtectSensor,
    UnifiProtectSensorEntityDescription,
    _bytes_to_gb,
    _calculate_storage_available,
    _calculate_storage_percent,
    _get_client_type,
    _get_storage_bytes,
    _has_storage_info,
    async_setup_entry,
    bytes_to_megabits,
    format_uptime,
)


def _create_mock_model(**kwargs):
    """Create a mock model that properly handles model_dump."""
    mock = MagicMock()
    for key, value in kwargs.items():
        setattr(mock, key, value)
    mock.model_dump = MagicMock(return_value=kwargs)
    return mock


@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator for sensor tests."""
    coordinator = MagicMock()
    coordinator.network_client = MagicMock()
    coordinator.network_client.base_url = "https://192.168.1.1"
    coordinator.protect_client = MagicMock()
    coordinator.protect_client.base_url = "https://192.168.1.1"

    # Setup coordinator data structure
    coordinator.data = {
        "sites": {"site1": {"id": "site1", "meta": {"name": "Default"}}},
        "devices": {
            "site1": {
                "device1": {
                    "id": "device1",
                    "name": "Test Switch",
                    "model": "USW-24",
                    "macAddress": "AA:BB:CC:DD:EE:FF",
                    "ipAddress": "192.168.1.10",
                    "state": "ONLINE",
                    "firmwareVersion": "6.5.55",
                    "interfaces": {
                        "ports": [
                            {
                                "idx": 1,
                                "state": "UP",
                                "speedMbps": 1000,
                                "poe": {"enabled": True, "power": 15.5},
                                "stats": {"txBytes": 1000000, "rxBytes": 2000000},
                            },
                            {
                                "idx": 2,
                                "state": "DOWN",
                                "speedMbps": 0,
                            },
                        ]
                    },
                },
                "device2": {
                    "id": "device2",
                    "name": "Test Gateway",
                    "model": "UDM-Pro",
                    "macAddress": "11:22:33:44:55:66",
                    "ipAddress": "192.168.1.1",
                    "state": "ONLINE",
                    "firmwareVersion": "3.0.0",
                    "features": {"gateway": True, "switching": True},
                    "interfaces": {"ports": []},
                },
            }
        },
        "clients": {"site1": {"client1": {"id": "client1", "name": "Test Client"}}},
        "stats": {
            "site1": {
                "device1": {
                    "id": "device1",
                    "cpuUtilizationPct": 15.5,
                    "memoryUtilizationPct": 30.2,
                    "uptimeSec": 86400,
                    "uplink": {"txRateBps": 1000000, "rxRateBps": 500000},
                    "clients": [
                        {"id": "client1", "type": "WIRED", "uplinkDeviceId": "device1"},
                        {
                            "id": "client2",
                            "type": "WIRELESS",
                            "uplinkDeviceId": "device1",
                        },
                    ],
                },
                "device2": {
                    "id": "device2",
                    "cpuUtilizationPct": 25.0,
                    "memoryUtilizationPct": 45.0,
                    "uptimeSec": 172800,
                    "clients": [],
                },
            }
        },
        "protect": {
            "sensors": {
                "sensor1": {
                    "id": "sensor1",
                    "name": "Kitchen Sensor",
                    "state": "CONNECTED",
                    "stats": {
                        "temperature": {"value": 22.5},
                        "humidity": {"value": 45},
                        "light": {"value": 500},
                    },
                    "batteryStatus": {"percentage": 85, "isLow": False},
                }
            },
            "cameras": {},
            "lights": {},
            "nvrs": {
                "nvr1": {
                    "id": "nvr1",
                    "name": "Test NVR",
                    "state": "CONNECTED",
                    "version": "4.0.0",
                    "storageUsedBytes": 500000000000,  # 500 GB
                    "storageTotalBytes": 1000000000000,  # 1 TB
                }
            },
            "viewers": {},
            "chimes": {},
            "liveviews": {},
            "events": {},
        },
        "last_update": None,
    }
    coordinator.get_site = MagicMock(return_value=coordinator.data["sites"]["site1"])
    coordinator.last_update_success = True
    return coordinator


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.runtime_data = MagicMock()
    return entry


class TestFormatUptime:
    """Tests for format_uptime function."""

    def test_format_uptime_none(self):
        """Test format_uptime with None."""
        assert format_uptime(None) is None

    def test_format_uptime_minutes_only(self):
        """Test format_uptime with just minutes."""
        assert format_uptime(300) == "5m"

    def test_format_uptime_hours_and_minutes(self):
        """Test format_uptime with hours and minutes."""
        assert format_uptime(3660) == "1h 1m"

    def test_format_uptime_days(self):
        """Test format_uptime with days."""
        assert format_uptime(86400) == "1d 0h 0m"

    def test_format_uptime_all_components(self):
        """Test format_uptime with days, hours, and minutes."""
        assert format_uptime(90061) == "1d 1h 1m"

    def test_format_uptime_zero(self):
        """Test format_uptime with zero."""
        assert format_uptime(0) == "0m"


class TestBytesToMegabits:
    """Tests for bytes_to_megabits function."""

    def test_bytes_to_megabits_none(self):
        """Test bytes_to_megabits with None."""
        assert bytes_to_megabits(None) is None

    def test_bytes_to_megabits_zero(self):
        """Test bytes_to_megabits with zero."""
        assert bytes_to_megabits(0) == 0.0

    def test_bytes_to_megabits_calculation(self):
        """Test bytes_to_megabits calculation."""
        # 1,000,000 bytes/sec = 8 Mbps
        assert bytes_to_megabits(1000000) == 8.0

    def test_bytes_to_megabits_rounding(self):
        """Test bytes_to_megabits rounding."""
        # 125000 bytes/sec = 1 Mbps
        assert bytes_to_megabits(125000) == 1.0


class TestGetClientType:
    """Tests for _get_client_type helper function."""

    def test_get_client_type_wired(self):
        """Test _get_client_type returns WIRED for wired clients."""
        assert _get_client_type({"type": "WIRED"}) == "WIRED"
        assert _get_client_type({"type": "wired"}) == "WIRED"

    def test_get_client_type_wireless(self):
        """Test _get_client_type returns WIRELESS for wireless clients."""
        assert _get_client_type({"type": "WIRELESS"}) == "WIRELESS"
        assert _get_client_type({"type": "wireless"}) == "WIRELESS"

    def test_get_client_type_connection_type_fallback(self):
        """Test _get_client_type uses connection_type as fallback."""
        assert _get_client_type({"connection_type": "WIRED"}) == "WIRED"
        assert _get_client_type({"connection_type": "WIRELESS"}) == "WIRELESS"

    def test_get_client_type_unknown_returns_as_is(self):
        """Test _get_client_type returns unknown types as-is (line 73)."""
        # Unknown type should be returned as uppercase
        assert _get_client_type({"type": "UNKNOWN"}) == "UNKNOWN"
        assert _get_client_type({"type": "other"}) == "OTHER"

        # Empty type returns empty string
        assert _get_client_type({"type": ""}) == ""
        assert _get_client_type({}) == ""

        # None type returns empty string (via str(None) -> "NONE")
        assert _get_client_type({"type": None}) == ""


class TestSensorTypes:
    """Tests for sensor type definitions."""

    def test_parallel_updates(self):
        """Test PARALLEL_UPDATES is set to 0."""
        assert PARALLEL_UPDATES == 0

    def test_sensor_types_defined(self):
        """Test that sensor types are defined."""
        assert len(SENSOR_TYPES) > 0

    def test_port_sensor_types_defined(self):
        """Test that port sensor types are defined."""
        assert len(PORT_SENSOR_TYPES) > 0

    def test_protect_sensor_types_defined(self):
        """Test that protect sensor types are defined."""
        assert len(PROTECT_SENSOR_TYPES) > 0


class TestUnifiInsightsSensor:
    """Tests for UnifiInsightsSensor."""

    async def test_sensor_cpu_usage(self, hass: HomeAssistant, mock_coordinator):
        """Test CPU usage sensor."""
        description = next(s for s in SENSOR_TYPES if s.key == "cpu_usage")

        sensor = UnifiInsightsSensor(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
        )

        # Native value should use value_fn
        stats = mock_coordinator.data["stats"]["site1"]["device1"]
        value = description.value_fn(stats)
        assert value == 15.5
        assert sensor.native_value == 15.5

    async def test_sensor_memory_usage(self, hass: HomeAssistant, mock_coordinator):
        """Test memory usage sensor."""
        description = next(s for s in SENSOR_TYPES if s.key == "memory_usage")

        sensor = UnifiInsightsSensor(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
        )

        assert sensor.native_value == 30.2

    async def test_sensor_uptime(self, hass: HomeAssistant, mock_coordinator):
        """Test uptime sensor."""
        description = next(s for s in SENSOR_TYPES if s.key == "uptime")

        sensor = UnifiInsightsSensor(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
        )

        # 86400 seconds = 1 day
        assert sensor.native_value == "1d 0h 0m"

    async def test_sensor_tx_rate(self, hass: HomeAssistant, mock_coordinator):
        """Test TX rate sensor."""
        description = next(s for s in SENSOR_TYPES if s.key == "tx_rate")

        sensor = UnifiInsightsSensor(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
        )

        # 1000000 bytes/sec = 8 Mbps
        assert sensor.native_value == 8.0

    async def test_sensor_firmware_version(self, hass: HomeAssistant, mock_coordinator):
        """Test firmware version sensor."""
        description = next(s for s in SENSOR_TYPES if s.key == "firmware_version")

        sensor = UnifiInsightsSensor(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
        )

        assert sensor.native_value == "6.5.55"

    async def test_sensor_wired_clients(self, hass: HomeAssistant, mock_coordinator):
        """Test wired clients sensor."""
        description = next(s for s in SENSOR_TYPES if s.key == "wired_clients")

        sensor = UnifiInsightsSensor(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
        )

        # One wired client in the test data
        assert sensor.native_value == 1

    async def test_sensor_wireless_clients(self, hass: HomeAssistant, mock_coordinator):
        """Test wireless clients sensor."""
        description = next(s for s in SENSOR_TYPES if s.key == "wireless_clients")

        sensor = UnifiInsightsSensor(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
        )

        # One wireless client in the test data
        assert sensor.native_value == 1

    async def test_sensor_no_stats(self, hass: HomeAssistant, mock_coordinator):
        """Test sensor when no stats are available."""
        description = next(s for s in SENSOR_TYPES if s.key == "cpu_usage")

        # Remove stats for device
        mock_coordinator.data["stats"]["site1"]["device1"] = None

        sensor = UnifiInsightsSensor(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
        )

        assert sensor.native_value is None

    async def test_sensor_unique_id(self, hass: HomeAssistant, mock_coordinator):
        """Test sensor unique ID format."""
        description = next(s for s in SENSOR_TYPES if s.key == "cpu_usage")

        sensor = UnifiInsightsSensor(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
        )

        assert sensor.unique_id == "site1_device1_cpu_usage"


class TestUnifiPortSensor:
    """Tests for UnifiPortSensor."""

    async def test_port_poe_power(self, hass: HomeAssistant, mock_coordinator):
        """Test PoE power port sensor."""
        description = next(s for s in PORT_SENSOR_TYPES if s.key == "port_poe_power")

        sensor = UnifiPortSensor(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
            port_idx=1,
        )

        assert sensor.native_value == 15.5
        assert "Port 1" in sensor.name

    async def test_port_speed(self, hass: HomeAssistant, mock_coordinator):
        """Test port speed sensor."""
        description = next(s for s in PORT_SENSOR_TYPES if s.key == "port_speed")

        sensor = UnifiPortSensor(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
            port_idx=1,
        )

        assert sensor.native_value == 1000

    async def test_port_sensor_unique_id(self, hass: HomeAssistant, mock_coordinator):
        """Test port sensor unique ID includes port index."""
        description = next(s for s in PORT_SENSOR_TYPES if s.key == "port_speed")

        sensor = UnifiPortSensor(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
            port_idx=1,
        )

        assert sensor.unique_id == "device1_port_speed_1"

    async def test_port_sensor_available_when_port_up(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test port sensor availability when port is UP."""
        description = next(s for s in PORT_SENSOR_TYPES if s.key == "port_speed")

        sensor = UnifiPortSensor(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
            port_idx=1,
        )

        assert sensor.available is True

    async def test_port_sensor_unavailable_when_port_down(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test port sensor availability when port is DOWN."""
        description = next(s for s in PORT_SENSOR_TYPES if s.key == "port_speed")

        sensor = UnifiPortSensor(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
            port_idx=2,  # Port 2 is DOWN in test data
        )

        assert sensor.available is False

    async def test_port_sensor_no_device_data(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test port sensor when device data is removed after initialization."""
        description = next(s for s in PORT_SENSOR_TYPES if s.key == "port_speed")

        # Create sensor with valid data
        sensor = UnifiPortSensor(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
            port_idx=1,
        )

        # Now remove device data to simulate device going offline
        mock_coordinator.data["devices"]["site1"]["device1"] = None

        # Value should be None when device data is missing
        assert sensor.native_value is None


class TestUnifiProtectSensor:
    """Tests for UnifiProtectSensor."""

    async def test_temperature_sensor(self, hass: HomeAssistant, mock_coordinator):
        """Test temperature sensor."""
        description = next(s for s in PROTECT_SENSOR_TYPES if s.key == "temperature")

        sensor = UnifiProtectSensor(
            coordinator=mock_coordinator,
            description=description,
            device_id="sensor1",
        )

        assert sensor.native_value == 22.5
        assert sensor.native_unit_of_measurement == UnitOfTemperature.CELSIUS

    async def test_humidity_sensor(self, hass: HomeAssistant, mock_coordinator):
        """Test humidity sensor."""
        description = next(s for s in PROTECT_SENSOR_TYPES if s.key == "humidity")

        sensor = UnifiProtectSensor(
            coordinator=mock_coordinator,
            description=description,
            device_id="sensor1",
        )

        assert sensor.native_value == 45
        assert sensor.native_unit_of_measurement == PERCENTAGE

    async def test_light_sensor(self, hass: HomeAssistant, mock_coordinator):
        """Test light sensor."""
        description = next(s for s in PROTECT_SENSOR_TYPES if s.key == "light")

        sensor = UnifiProtectSensor(
            coordinator=mock_coordinator,
            description=description,
            device_id="sensor1",
        )

        assert sensor.native_value == 500

    async def test_battery_sensor(self, hass: HomeAssistant, mock_coordinator):
        """Test battery sensor."""
        description = next(s for s in PROTECT_SENSOR_TYPES if s.key == "battery")

        sensor = UnifiProtectSensor(
            coordinator=mock_coordinator,
            description=description,
            device_id="sensor1",
        )

        assert sensor.native_value == 85
        assert sensor.native_unit_of_measurement == PERCENTAGE

    async def test_protect_sensor_no_data(self, hass: HomeAssistant, mock_coordinator):
        """Test protect sensor when data is removed after initialization."""
        description = next(s for s in PROTECT_SENSOR_TYPES if s.key == "temperature")

        # Create sensor with valid data first
        sensor = UnifiProtectSensor(
            coordinator=mock_coordinator,
            description=description,
            device_id="sensor1",
        )

        # Now remove sensor data to simulate device going offline
        mock_coordinator.data["protect"]["sensors"]["sensor1"] = None

        # Value should be None when sensor data is missing
        assert sensor.native_value is None


class TestAsyncSetupEntry:
    """Tests for async_setup_entry."""

    async def test_setup_entry_creates_sensors(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Test that setup entry creates sensors."""
        mock_config_entry.runtime_data.coordinator = mock_coordinator

        added_entities: list = []

        def add_entities(new_entities, **kwargs):
            added_entities.extend(new_entities)

        await async_setup_entry(hass, mock_config_entry, add_entities)

        # Should have created sensors for devices
        assert len(added_entities) > 0

    async def test_setup_entry_creates_port_sensors(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Test that setup entry creates port sensors for active ports."""
        mock_config_entry.runtime_data.coordinator = mock_coordinator

        added_entities: list = []

        def add_entities(new_entities, **kwargs):
            added_entities.extend(new_entities)

        await async_setup_entry(hass, mock_config_entry, add_entities)

        # Check for port sensors (only for port 1 which is UP)
        port_sensors = [e for e in added_entities if isinstance(e, UnifiPortSensor)]
        assert len(port_sensors) > 0

    async def test_setup_entry_creates_protect_sensors(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Test that setup entry creates protect sensors."""
        mock_config_entry.runtime_data.coordinator = mock_coordinator

        added_entities: list = []

        def add_entities(new_entities, **kwargs):
            added_entities.extend(new_entities)

        await async_setup_entry(hass, mock_config_entry, add_entities)

        # Check for protect sensors
        protect_sensors = [
            e for e in added_entities if isinstance(e, UnifiProtectSensor)
        ]
        assert len(protect_sensors) > 0

    async def test_setup_entry_without_protect_client(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Test setup entry without protect client."""
        mock_coordinator.protect_client = None
        mock_config_entry.runtime_data.coordinator = mock_coordinator

        added_entities: list = []

        def add_entities(new_entities, **kwargs):
            added_entities.extend(new_entities)

        await async_setup_entry(hass, mock_config_entry, add_entities)

        # Should still create network sensors
        assert len(added_entities) > 0

        # But no protect sensors
        protect_sensors = [
            e for e in added_entities if isinstance(e, UnifiProtectSensor)
        ]
        assert len(protect_sensors) == 0


class TestUnifiPortSensorEdgeCases:
    """Tests for UnifiPortSensor edge cases."""

    async def test_port_sensor_no_device_data(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test port sensor when device data is missing."""
        description = PORT_SENSOR_TYPES[0]  # PoE power

        sensor = UnifiPortSensor(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
            port_idx=1,
        )

        # Remove device data
        mock_coordinator.data["devices"]["site1"] = {}

        assert sensor.native_value is None

    async def test_port_sensor_no_port_data(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test port sensor when port data is missing."""
        description = PORT_SENSOR_TYPES[0]  # PoE power

        sensor = UnifiPortSensor(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
            port_idx=99,  # Non-existent port
        )

        assert sensor.native_value is None

    async def test_port_sensor_tx_bytes_with_stats(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test port TX bytes sensor with stats data."""
        description = PORT_SENSOR_TYPES[2]  # TX bytes

        # Add port stats
        mock_coordinator.data["stats"]["site1"]["device1"]["ports"] = {
            "1": {"txBytes": 5000000, "rxBytes": 3000000}
        }

        sensor = UnifiPortSensor(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
            port_idx=1,
        )

        value = sensor.native_value
        assert value is not None

    async def test_port_sensor_rx_bytes_with_stats(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test port RX bytes sensor with stats data."""
        description = PORT_SENSOR_TYPES[3]  # RX bytes

        # Add port stats
        mock_coordinator.data["stats"]["site1"]["device1"]["ports"] = {
            "1": {"txBytes": 5000000, "rxBytes": 3000000}
        }

        sensor = UnifiPortSensor(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
            port_idx=1,
        )

        value = sensor.native_value
        assert value is not None

    async def test_port_sensor_available_not_connected(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test port sensor availability when coordinator not connected."""
        description = PORT_SENSOR_TYPES[0]  # PoE power

        sensor = UnifiPortSensor(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
            port_idx=1,
        )

        # Set last_update_success to False
        mock_coordinator.last_update_success = False

        assert sensor.available is False

    async def test_port_sensor_available_devices_not_dict(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test port sensor availability when devices is not a dict."""
        description = PORT_SENSOR_TYPES[0]  # PoE power

        sensor = UnifiPortSensor(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
            port_idx=1,
        )

        # Set devices to non-dict
        mock_coordinator.data["devices"] = "not a dict"

        assert sensor.available is False

    async def test_port_sensor_available_site_devices_not_dict(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test port sensor availability when site devices is not a dict."""
        description = PORT_SENSOR_TYPES[0]  # PoE power

        sensor = UnifiPortSensor(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
            port_idx=1,
        )

        # Set site devices to non-dict
        mock_coordinator.data["devices"]["site1"] = "not a dict"

        assert sensor.available is False

    async def test_port_sensor_available_device_data_not_dict(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test port sensor availability when device data is not a dict."""
        description = PORT_SENSOR_TYPES[0]  # PoE power

        sensor = UnifiPortSensor(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
            port_idx=1,
        )

        # Set device data to non-dict
        mock_coordinator.data["devices"]["site1"]["device1"] = "not a dict"

        assert sensor.available is False

    async def test_port_sensor_available_interfaces_not_dict(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test port sensor availability when interfaces is not a dict."""
        description = PORT_SENSOR_TYPES[0]  # PoE power

        sensor = UnifiPortSensor(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
            port_idx=1,
        )

        # Set interfaces to non-dict
        mock_coordinator.data["devices"]["site1"]["device1"]["interfaces"] = (
            "not a dict"
        )

        assert sensor.available is False

    async def test_port_sensor_available_ports_not_list(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test port sensor availability when ports is not a list."""
        description = PORT_SENSOR_TYPES[0]  # PoE power

        sensor = UnifiPortSensor(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
            port_idx=1,
        )

        # Set ports to non-list
        mock_coordinator.data["devices"]["site1"]["device1"]["interfaces"]["ports"] = (
            "not a list"
        )

        assert sensor.available is False

    async def test_port_sensor_available_port_not_found(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test port sensor availability when port is not found."""
        description = PORT_SENSOR_TYPES[0]  # PoE power

        sensor = UnifiPortSensor(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
            port_idx=99,  # Non-existent port
        )

        assert sensor.available is False

    async def test_port_sensor_available_port_down(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test port sensor availability when port is DOWN."""
        description = PORT_SENSOR_TYPES[0]  # PoE power

        sensor = UnifiPortSensor(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
            port_idx=2,  # Port 2 is DOWN
        )

        assert sensor.available is False

    async def test_port_sensor_available_port_state_not_string(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test port sensor availability when port state is not a string."""
        description = PORT_SENSOR_TYPES[0]  # PoE power

        sensor = UnifiPortSensor(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
            port_idx=1,
        )

        # Set port state to non-string
        mock_coordinator.data["devices"]["site1"]["device1"]["interfaces"]["ports"][0][
            "state"
        ] = 123

        assert sensor.available is False


class TestUnifiProtectSensorAttributes:
    """Tests for UnifiProtectSensor extra state attributes."""

    async def test_temperature_sensor_attributes(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test temperature sensor extra state attributes."""
        description = next(s for s in PROTECT_SENSOR_TYPES if s.key == "temperature")

        sensor = UnifiProtectSensor(
            coordinator=mock_coordinator,
            description=description,
            device_id="sensor1",
        )

        attrs = sensor._attr_extra_state_attributes
        assert attrs["sensor_id"] == "sensor1"
        assert attrs["sensor_name"] == "Kitchen Sensor"
        assert attrs["temperature_value"] == 22.5

    async def test_humidity_sensor_attributes(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test humidity sensor extra state attributes."""
        description = next(s for s in PROTECT_SENSOR_TYPES if s.key == "humidity")

        sensor = UnifiProtectSensor(
            coordinator=mock_coordinator,
            description=description,
            device_id="sensor1",
        )

        attrs = sensor._attr_extra_state_attributes
        assert attrs["sensor_id"] == "sensor1"
        assert attrs["sensor_name"] == "Kitchen Sensor"
        assert attrs["humidity_value"] == 45

    async def test_light_sensor_attributes(self, hass: HomeAssistant, mock_coordinator):
        """Test light sensor extra state attributes."""
        description = next(s for s in PROTECT_SENSOR_TYPES if s.key == "light")

        sensor = UnifiProtectSensor(
            coordinator=mock_coordinator,
            description=description,
            device_id="sensor1",
        )

        attrs = sensor._attr_extra_state_attributes
        assert attrs["sensor_id"] == "sensor1"
        assert attrs["sensor_name"] == "Kitchen Sensor"
        assert attrs["light_value"] == 500

    async def test_battery_sensor_attributes(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test battery sensor extra state attributes."""
        description = next(s for s in PROTECT_SENSOR_TYPES if s.key == "battery")

        sensor = UnifiProtectSensor(
            coordinator=mock_coordinator,
            description=description,
            device_id="sensor1",
        )

        attrs = sensor._attr_extra_state_attributes
        assert attrs["sensor_id"] == "sensor1"
        assert attrs["sensor_name"] == "Kitchen Sensor"
        assert attrs["battery_percentage"] == 85
        assert attrs["battery_low"] is False


class TestHasStorageInfo:
    """Tests for _has_storage_info helper function."""

    def test_has_storage_info_with_direct_camel_case(self):
        """Test _has_storage_info with direct camelCase fields."""
        assert _has_storage_info({"storageUsedBytes": 100}) is True
        assert _has_storage_info({"storageTotalBytes": 100}) is True

    def test_has_storage_info_with_snake_case(self):
        """Test _has_storage_info with snake_case fields."""
        assert _has_storage_info({"storage_used_bytes": 100}) is True
        assert _has_storage_info({"storage_total_bytes": 100}) is True

    def test_has_storage_info_with_nested_used_size(self):
        """Test _has_storage_info with nested storageInfo.usedSize."""
        assert _has_storage_info({"storageInfo": {"usedSize": 100}}) is True

    def test_has_storage_info_with_nested_total_size(self):
        """Test _has_storage_info with nested storageInfo.totalSize."""
        assert _has_storage_info({"storageInfo": {"totalSize": 100}}) is True

    def test_has_storage_info_with_nested_used_size_snake(self):
        """Test _has_storage_info with nested storageInfo.used_size."""
        assert _has_storage_info({"storageInfo": {"used_size": 100}}) is True

    def test_has_storage_info_with_nested_total_size_snake(self):
        """Test _has_storage_info with nested storageInfo.total_size."""
        assert _has_storage_info({"storageInfo": {"total_size": 100}}) is True

    def test_has_storage_info_returns_false_for_empty(self):
        """Test _has_storage_info returns False when no storage info."""
        assert _has_storage_info({}) is False
        assert _has_storage_info({"other_field": 123}) is False

    def test_has_storage_info_with_non_dict_storage_info(self):
        """Test _has_storage_info with non-dict storageInfo."""
        assert _has_storage_info({"storageInfo": "not a dict"}) is False
        assert _has_storage_info({"storageInfo": None}) is False


class TestGetStorageBytes:
    """Tests for _get_storage_bytes helper function."""

    def test_get_storage_bytes_used_direct(self):
        """Test _get_storage_bytes for 'used' with direct fields."""
        assert _get_storage_bytes({"storageUsedBytes": 1000}, "used") == 1000
        assert _get_storage_bytes({"storage_used_bytes": 2000}, "used") == 2000

    def test_get_storage_bytes_total_direct(self):
        """Test _get_storage_bytes for 'total' with direct fields."""
        assert _get_storage_bytes({"storageTotalBytes": 1000}, "total") == 1000
        assert _get_storage_bytes({"storage_total_bytes": 2000}, "total") == 2000

    def test_get_storage_bytes_used_nested(self):
        """Test _get_storage_bytes for 'used' with nested storageInfo."""
        assert _get_storage_bytes({"storageInfo": {"usedSize": 100}}, "used") == 100
        assert _get_storage_bytes({"storageInfo": {"used_size": 200}}, "used") == 200
        data = {"storageInfo": {"usedSpaceBytes": 300}}
        assert _get_storage_bytes(data, "used") == 300
        data = {"storageInfo": {"used_space_bytes": 400}}
        assert _get_storage_bytes(data, "used") == 400

    def test_get_storage_bytes_total_nested(self):
        """Test _get_storage_bytes for 'total' with nested storageInfo."""
        assert _get_storage_bytes({"storageInfo": {"totalSize": 100}}, "total") == 100
        assert _get_storage_bytes({"storageInfo": {"total_size": 200}}, "total") == 200
        data = {"storageInfo": {"totalSpaceBytes": 300}}
        assert _get_storage_bytes(data, "total") == 300
        data = {"storageInfo": {"total_space_bytes": 400}}
        assert _get_storage_bytes(data, "total") == 400

    def test_get_storage_bytes_returns_none_for_invalid_field(self):
        """Test _get_storage_bytes returns None for unknown field."""
        assert _get_storage_bytes({"storageUsedBytes": 100}, "invalid") is None

    def test_get_storage_bytes_with_float_value(self):
        """Test _get_storage_bytes converts float to int."""
        assert _get_storage_bytes({"storageUsedBytes": 100.5}, "used") == 100
        assert _get_storage_bytes({"storageTotalBytes": 200.9}, "total") == 200

    def test_get_storage_bytes_with_non_numeric_value(self):
        """Test _get_storage_bytes returns None for non-numeric."""
        assert _get_storage_bytes({"storageUsedBytes": "not a number"}, "used") is None
        data = {"storageInfo": {"usedSize": "string"}}
        assert _get_storage_bytes(data, "used") is None


class TestNVRStorageHelpers:
    """Tests for NVR storage helper functions."""

    def test_bytes_to_gb(self):
        """Test bytes to GB conversion."""
        # 1 GB
        assert _bytes_to_gb(1073741824) == 1.0
        # 500 GB
        assert _bytes_to_gb(536870912000) == 500.0
        # None input
        assert _bytes_to_gb(None) is None
        # Small value
        assert _bytes_to_gb(1000000) == 0.0

    def test_calculate_storage_percent(self):
        """Test storage percentage calculation."""
        # Test 50% used storage
        nvr_data = {
            "storageUsedBytes": 500000000000,
            "storageTotalBytes": 1000000000000,
        }
        assert _calculate_storage_percent(nvr_data) == 50.0

        # Snake case keys
        nvr_data_snake = {
            "storage_used_bytes": 250000000000,
            "storage_total_bytes": 1000000000000,
        }
        assert _calculate_storage_percent(nvr_data_snake) == 25.0

        # Missing data
        assert _calculate_storage_percent({}) is None
        assert _calculate_storage_percent({"storageUsedBytes": 100}) is None
        assert _calculate_storage_percent({"storageTotalBytes": 100}) is None

        # Zero total (division by zero protection)
        assert (
            _calculate_storage_percent({"storageUsedBytes": 0, "storageTotalBytes": 0})
            is None
        )

    def test_calculate_storage_available(self):
        """Test storage available calculation."""
        # 500 GB available
        nvr_data = {
            "storageUsedBytes": 500000000000,
            "storageTotalBytes": 1000000000000,
        }
        result = _calculate_storage_available(nvr_data)
        assert result is not None
        assert abs(result - 465.66) < 1  # ~465 GB (500 GB in decimal)

        # Snake case keys
        nvr_data_snake = {
            "storage_used_bytes": 250000000000,
            "storage_total_bytes": 1000000000000,
        }
        result = _calculate_storage_available(nvr_data_snake)
        assert result is not None

        # Missing data
        assert _calculate_storage_available({}) is None


class TestNVRSensorTypes:
    """Tests for NVR sensor type definitions."""

    def test_nvr_sensor_types_defined(self):
        """Test that NVR sensor types are properly defined."""
        assert len(NVR_SENSOR_TYPES) == 4

        keys = [s.key for s in NVR_SENSOR_TYPES]
        assert "storage_used" in keys
        assert "storage_total" in keys
        assert "storage_available" in keys
        assert "storage_used_percent" in keys

    def test_nvr_sensor_types_have_device_type(self):
        """Test that all NVR sensor types have device_type set."""
        for sensor_type in NVR_SENSOR_TYPES:
            assert sensor_type.device_type == "nvr"


class TestUnifiProtectNVRSensor:
    """Tests for UnifiProtectNVRSensor class."""

    async def test_storage_used_sensor(self, hass: HomeAssistant, mock_coordinator):
        """Test NVR storage used sensor."""
        description = next(s for s in NVR_SENSOR_TYPES if s.key == "storage_used")

        sensor = UnifiProtectNVRSensor(
            coordinator=mock_coordinator,
            description=description,
            device_id="nvr1",
        )

        # Check native value (500 GB = ~465.66 GB in binary)
        value = sensor.native_value
        assert value is not None
        assert abs(value - 465.66) < 1

    async def test_storage_total_sensor(self, hass: HomeAssistant, mock_coordinator):
        """Test NVR storage total sensor."""
        description = next(s for s in NVR_SENSOR_TYPES if s.key == "storage_total")

        sensor = UnifiProtectNVRSensor(
            coordinator=mock_coordinator,
            description=description,
            device_id="nvr1",
        )

        # Check native value (1 TB = ~931.32 GB in binary)
        value = sensor.native_value
        assert value is not None
        assert abs(value - 931.32) < 1

    async def test_storage_available_sensor(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test NVR storage available sensor."""
        description = next(s for s in NVR_SENSOR_TYPES if s.key == "storage_available")

        sensor = UnifiProtectNVRSensor(
            coordinator=mock_coordinator,
            description=description,
            device_id="nvr1",
        )

        # Check native value (~465.66 GB available)
        value = sensor.native_value
        assert value is not None
        assert abs(value - 465.66) < 1

    async def test_storage_percent_sensor(self, hass: HomeAssistant, mock_coordinator):
        """Test NVR storage percentage sensor."""
        description = next(
            s for s in NVR_SENSOR_TYPES if s.key == "storage_used_percent"
        )

        sensor = UnifiProtectNVRSensor(
            coordinator=mock_coordinator,
            description=description,
            device_id="nvr1",
        )

        # Check native value (50% used)
        value = sensor.native_value
        assert value == 50.0

    async def test_nvr_sensor_no_data(self, hass: HomeAssistant, mock_coordinator):
        """Test NVR sensor with missing data."""
        description = next(s for s in NVR_SENSOR_TYPES if s.key == "storage_used")

        sensor = UnifiProtectNVRSensor(
            coordinator=mock_coordinator,
            description=description,
            device_id="nonexistent_nvr",
        )

        assert sensor.native_value is None

    async def test_nvr_sensor_unique_id(self, hass: HomeAssistant, mock_coordinator):
        """Test NVR sensor unique ID format."""
        description = next(s for s in NVR_SENSOR_TYPES if s.key == "storage_used")

        sensor = UnifiProtectNVRSensor(
            coordinator=mock_coordinator,
            description=description,
            device_id="nvr1",
        )

        assert sensor._attr_unique_id == "unifi_insights_nvr_nvr1_storage_used"

    async def test_nvr_sensor_name(self, hass: HomeAssistant, mock_coordinator):
        """Test NVR sensor name."""
        description = next(s for s in NVR_SENSOR_TYPES if s.key == "storage_used")

        sensor = UnifiProtectNVRSensor(
            coordinator=mock_coordinator,
            description=description,
            device_id="nvr1",
        )

        assert sensor._attr_name == "Storage Used"


class TestUnifiProtectNVRSensorAttributes:
    """Tests for NVR sensor extra state attributes."""

    async def test_nvr_sensor_attributes(self, hass: HomeAssistant, mock_coordinator):
        """Test NVR sensor extra state attributes."""
        description = next(s for s in NVR_SENSOR_TYPES if s.key == "storage_used")

        sensor = UnifiProtectNVRSensor(
            coordinator=mock_coordinator,
            description=description,
            device_id="nvr1",
        )

        attrs = sensor._attr_extra_state_attributes
        assert attrs["nvr_id"] == "nvr1"
        assert attrs["nvr_name"] == "Test NVR"
        assert attrs["nvr_version"] == "4.0.0"
        assert attrs["storage_used"] is not None
        assert attrs["storage_total"] is not None
        assert attrs["storage_available"] is not None
        assert attrs["storage_used_percent"] == 50.0


class TestAsyncSetupEntryWithNVRSensors:
    """Tests for async_setup_entry with NVR sensors."""

    async def test_setup_entry_creates_nvr_sensors(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Test that setup creates NVR sensors."""
        mock_config_entry.runtime_data.coordinator = mock_coordinator

        entities = []

        def mock_add_entities(new_entities):
            entities.extend(new_entities)

        await async_setup_entry(hass, mock_config_entry, mock_add_entities)

        # Should have NVR sensors (4 sensors per NVR)
        nvr_sensors = [e for e in entities if isinstance(e, UnifiProtectNVRSensor)]
        assert len(nvr_sensors) == 4

        # Check sensor keys
        nvr_sensor_keys = [s.entity_description.key for s in nvr_sensors]
        assert "storage_used" in nvr_sensor_keys
        assert "storage_total" in nvr_sensor_keys
        assert "storage_available" in nvr_sensor_keys
        assert "storage_used_percent" in nvr_sensor_keys

    async def test_setup_entry_without_nvrs(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Test setup when there are no NVRs."""
        # Remove NVR data
        mock_coordinator.data["protect"]["nvrs"] = {}
        mock_config_entry.runtime_data.coordinator = mock_coordinator

        entities = []

        def mock_add_entities(new_entities):
            entities.extend(new_entities)

        await async_setup_entry(hass, mock_config_entry, mock_add_entities)

        # Should have no NVR sensors
        nvr_sensors = [e for e in entities if isinstance(e, UnifiProtectNVRSensor)]
        assert len(nvr_sensors) == 0

    async def test_setup_entry_nvr_without_storage_info(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Test setup when NVR has no storage info (covers lines 743, 753)."""
        # Create NVR data without any storage fields
        mock_coordinator.data["protect"]["nvrs"] = {
            "nvr_no_storage": {
                "id": "nvr_no_storage",
                "name": "NVR Without Storage",
                "state": "CONNECTED",
                "version": "4.0.0",
                # No storage fields at all
            }
        }
        mock_config_entry.runtime_data.coordinator = mock_coordinator

        entities = []

        def mock_add_entities(new_entities):
            entities.extend(new_entities)

        await async_setup_entry(hass, mock_config_entry, mock_add_entities)

        # Should have 0 NVR sensors since storage info is not available
        # (all NVR sensor types start with "storage_")
        nvr_sensors = [e for e in entities if isinstance(e, UnifiProtectNVRSensor)]
        assert len(nvr_sensors) == 0


class TestAsyncSetupEntryEdgeCases:
    """Test setup entry edge cases for sensors."""

    async def test_setup_entry_interfaces_not_dict(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Test setup when interfaces is not a dict (e.g., list)."""
        # Set interfaces to a list instead of dict
        mock_coordinator.data["devices"]["site1"]["device1"]["interfaces"] = ["ports"]
        mock_config_entry.runtime_data.coordinator = mock_coordinator

        entities = []

        def mock_add_entities(new_entities):
            entities.extend(new_entities)

        await async_setup_entry(hass, mock_config_entry, mock_add_entities)

        # Should still create device sensors but no port sensors
        port_sensors = [e for e in entities if isinstance(e, UnifiPortSensor)]
        assert len(port_sensors) == 0

    async def test_setup_entry_port_without_idx(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Test setup when port has no idx field."""
        # Add port without idx
        mock_coordinator.data["devices"]["site1"]["device1"]["interfaces"] = {
            "ports": [{"state": "UP", "poe": {"enabled": True}}]  # No idx
        }
        mock_config_entry.runtime_data.coordinator = mock_coordinator

        entities = []

        def mock_add_entities(new_entities):
            entities.extend(new_entities)

        await async_setup_entry(hass, mock_config_entry, mock_add_entities)

        # Should have no port sensors since port has no idx
        port_sensors = [e for e in entities if isinstance(e, UnifiPortSensor)]
        assert len(port_sensors) == 0

    async def test_setup_entry_port_state_down(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Test setup when port state is DOWN."""
        mock_coordinator.data["devices"]["site1"]["device1"]["interfaces"] = {
            "ports": [{"idx": 1, "state": "DOWN", "poe": {"enabled": True}}]
        }
        mock_config_entry.runtime_data.coordinator = mock_coordinator

        entities = []

        def mock_add_entities(new_entities):
            entities.extend(new_entities)

        await async_setup_entry(hass, mock_config_entry, mock_add_entities)

        # Should have no port sensors since port is DOWN
        port_sensors = [e for e in entities if isinstance(e, UnifiPortSensor)]
        assert len(port_sensors) == 0

    async def test_setup_entry_wan_sensors_for_gateway(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Test WAN sensors are created for gateway devices."""
        # Make device a gateway
        mock_coordinator.data["devices"]["site1"]["device1"]["model"] = "UDM-Pro"
        mock_coordinator.data["devices"]["site1"]["device1"]["features"] = ["gateway"]
        mock_config_entry.runtime_data.coordinator = mock_coordinator

        entities = []

        def mock_add_entities(new_entities):
            entities.extend(new_entities)

        await async_setup_entry(hass, mock_config_entry, mock_add_entities)

        # Find WAN sensors
        wan_sensors = [
            e
            for e in entities
            if isinstance(e, UnifiInsightsSensor)
            and e.entity_description.key.startswith("wan_")
        ]
        assert len(wan_sensors) > 0


class TestUnifiInsightsSensorEdgeCases:
    """Test edge cases for UnifiInsightsSensor."""

    async def test_native_value_firmware_version_no_device(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test native_value returns None when device data missing."""
        # Find firmware version description
        fw_desc = next(d for d in SENSOR_TYPES if d.key == "firmware_version")

        sensor = UnifiInsightsSensor(
            coordinator=mock_coordinator,
            description=fw_desc,
            site_id="site1",
            device_id="device1",
        )

        # Remove device data
        mock_coordinator.data["devices"]["site1"] = {}

        assert sensor.native_value is None

    async def test_async_update_calls_super(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test async_update calls parent implementation."""
        cpu_desc = next(d for d in SENSOR_TYPES if d.key == "cpu_usage")
        sensor = UnifiInsightsSensor(
            coordinator=mock_coordinator,
            description=cpu_desc,
            site_id="site1",
            device_id="device1",
        )

        # Mock async_request_refresh to be awaitable
        mock_coordinator.async_request_refresh = AsyncMock()

        # Should not raise
        await sensor.async_update()


class TestUnifiPortSensorNativeValueEdgeCases:
    """Test edge cases for UnifiPortSensor native_value."""

    async def test_native_value_no_device_data(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test native_value returns None when device data is missing."""
        speed_desc = PORT_SENSOR_TYPES[1]
        sensor = UnifiPortSensor(
            coordinator=mock_coordinator,
            description=speed_desc,
            site_id="site1",
            device_id="device1",
            port_idx=1,
        )

        # Remove device data
        mock_coordinator.data["devices"]["site1"] = {}

        assert sensor.native_value is None

    async def test_native_value_no_port_data(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test native_value returns None when port not found."""
        speed_desc = PORT_SENSOR_TYPES[1]
        sensor = UnifiPortSensor(
            coordinator=mock_coordinator,
            description=speed_desc,
            site_id="site1",
            device_id="device1",
            port_idx=99,  # Non-existent port
        )

        assert sensor.native_value is None

    async def test_native_value_tx_bytes_with_stats(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test native_value for TX bytes uses stats."""
        tx_desc = PORT_SENSOR_TYPES[2]  # TX bytes
        sensor = UnifiPortSensor(
            coordinator=mock_coordinator,
            description=tx_desc,
            site_id="site1",
            device_id="device1",
            port_idx=1,
        )

        # Add stats data for port
        mock_coordinator.data["stats"]["site1"]["device1"]["ports"] = {
            "1": {"txBytes": 12345}
        }

        value = sensor.native_value
        # Value should be extracted from value_fn
        assert value is not None or value == 0


class TestUnifiProtectNVRSensorEdgeCases:
    """Test edge cases for UnifiProtectNVRSensor."""

    async def test_available_no_nvr_data(self, hass: HomeAssistant, mock_coordinator):
        """Test available returns False when NVR data missing."""
        storage_desc = next(d for d in NVR_SENSOR_TYPES if d.key == "storage_used")
        sensor = UnifiProtectNVRSensor(
            coordinator=mock_coordinator,
            description=storage_desc,
            device_id="nvr1",
        )

        # Remove NVR data
        mock_coordinator.data["protect"]["nvrs"] = {}

        assert sensor.available is False

    async def test_available_storage_sensor_with_nested_storage_info(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test available for storage sensor with nested storageInfo."""
        storage_desc = next(d for d in NVR_SENSOR_TYPES if d.key == "storage_used")
        sensor = UnifiProtectNVRSensor(
            coordinator=mock_coordinator,
            description=storage_desc,
            device_id="nvr1",
        )

        # Set nested storageInfo
        mock_coordinator.data["protect"]["nvrs"]["nvr1"] = {
            "id": "nvr1",
            "name": "Test NVR",
            "storageInfo": {"usedSize": 100, "totalSize": 1000},
        }

        assert sensor.available is True

    async def test_available_non_storage_sensor(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test available for non-storage NVR sensor."""
        # Create a custom description that's not storage-related
        custom_desc = UnifiProtectSensorEntityDescription(
            key="custom_sensor",
            name="Custom",
            value_fn=lambda x: x.get("customValue"),
            device_type="nvr",
        )

        sensor = UnifiProtectNVRSensor(
            coordinator=mock_coordinator,
            description=custom_desc,
            device_id="nvr1",
        )

        # Has NVR data
        mock_coordinator.data["protect"]["nvrs"]["nvr1"] = {
            "id": "nvr1",
            "name": "Test NVR",
        }

        assert sensor.available is True

    async def test_update_from_data_attributes(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test _update_from_data sets attributes correctly."""
        storage_desc = next(d for d in NVR_SENSOR_TYPES if d.key == "storage_used")
        sensor = UnifiProtectNVRSensor(
            coordinator=mock_coordinator,
            description=storage_desc,
            device_id="nvr1",
        )

        # Set storage data
        mock_coordinator.data["protect"]["nvrs"]["nvr1"] = {
            "id": "nvr1",
            "name": "Test NVR",
            "version": "3.0.0",
            "storageUsedBytes": 500000000000,
            "storageTotalBytes": 1000000000000,
        }

        sensor._update_from_data()

        assert sensor._attr_extra_state_attributes is not None
        assert "nvr_id" in sensor._attr_extra_state_attributes
