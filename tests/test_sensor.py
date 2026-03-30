"""Tests for UniFi Insights sensors."""

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import PERCENTAGE, UnitOfInformation, UnitOfTemperature

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

from custom_components.unifi_insights.sensor import (
    NVR_SENSOR_TYPES,
    PARALLEL_UPDATES,
    PORT_SENSOR_TYPES,
    PROTECT_SENSOR_TYPES,
    SENSOR_TYPES,
    SFP_SENSOR_TYPES,
    SITE_CLIENT_SENSOR_TYPES,
    UnifiInsightsSensor,
    UnifiPortSensor,
    UnifiProtectNVRSensor,
    UnifiProtectSensor,
    UnifiProtectSensorEntityDescription,
    UnifiSiteClientSensor,
    _bytes_to_gb,
    _calculate_storage_available,
    _calculate_storage_percent,
    _get_client_type,
    _get_port_label,
    _get_storage_bytes,
    _has_protect_stat,
    _has_storage_info,
    _migrate_sensor_units,
    async_setup_entry,
    bytes_to_bits,
    bytes_to_megabits,
    format_uptime,
    get_network_device_temperature,
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
                            {
                                "idx": 25,
                                "state": "UP",
                                "speedMbps": 10000,
                                "media": "SFP+",
                                "name": "SFP+ 1",
                                "is_uplink": True,
                                "sfp_found": True,
                                "sfp_part": "UC-DAC-SFP+",
                                "sfp_vendor": "Ubiquiti Inc.",
                                "sfp_serial": "SN12345",
                                "sfp_compliance": "DAC",
                            },
                            {
                                "idx": 26,
                                "state": "DOWN",
                                "speedMbps": 10000,
                                "media": "SFP+",
                                "name": "SFP+ 2",
                                "sfp_found": False,
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
                    "hasTemperature": True,
                    "generalTemperature": 44.5,
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


class TestBytesToBits:
    """Tests for bytes_to_bits function."""

    def test_bytes_to_bits_none(self):
        """Test bytes_to_bits with None."""
        assert bytes_to_bits(None) is None

    def test_bytes_to_bits_zero(self):
        """Test bytes_to_bits with zero."""
        assert bytes_to_bits(0) == 0

    def test_bytes_to_bits_calculation(self):
        """Test bytes_to_bits calculation."""
        # 1000 bytes/sec = 8000 bits/sec
        assert bytes_to_bits(1000) == 8000

    def test_bytes_to_bits_large_value(self):
        """Test bytes_to_bits with large value."""
        # 1,000,000 bytes/sec = 8,000,000 bits/sec
        assert bytes_to_bits(1000000) == 8000000


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
        """Test TX rate sensor returns bits per second."""
        description = next(s for s in SENSOR_TYPES if s.key == "tx_rate")

        sensor = UnifiInsightsSensor(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
        )

        # 1000000 bytes/sec = 8000000 bits/sec (native unit)
        assert sensor.native_value == 8000000

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

    async def test_sensor_general_temperature(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test network device temperature sensor from device data."""
        description = next(s for s in SENSOR_TYPES if s.key == "general_temperature")

        sensor = UnifiInsightsSensor(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device2",
        )

        assert sensor.native_value == 44.5
        assert sensor.native_unit_of_measurement == UnitOfTemperature.CELSIUS

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


class TestGetPortLabel:
    """Tests for _get_port_label helper."""

    def test_port_label_uses_api_name(self):
        """Test _get_port_label returns the API name when available."""
        port = {"name": "SFP+ 1", "media": "SFP+", "idx": 25}
        assert _get_port_label(port, 25) == "SFP+ 1"

    def test_port_label_sfp_fallback(self):
        """Test _get_port_label returns media-based label for SFP ports without name."""
        port = {"media": "SFP+", "idx": 10}
        assert _get_port_label(port, 10) == "SFP+ 10"

    def test_port_label_regular_port(self):
        """Test _get_port_label returns generic label for regular ports."""
        port = {"media": "GE", "idx": 1}
        assert _get_port_label(port, 1) == "Port 1"

    def test_port_label_no_media(self):
        """Test _get_port_label returns generic label when no media info."""
        port = {"idx": 5}
        assert _get_port_label(port, 5) == "Port 5"

    def test_port_label_ignores_generic_name(self):
        """Test _get_port_label ignores default 'Port N' name and uses media."""
        port = {"name": "Port 25", "media": "SFP+", "idx": 25}
        assert _get_port_label(port, 25) == "SFP+ 25"


class TestSFPPortSensors:
    """Tests for SFP port sensor features."""

    async def test_sfp_sensor_types_defined(self):
        """Test that SFP sensor types are defined."""
        assert len(SFP_SENSOR_TYPES) == 4
        keys = {s.key for s in SFP_SENSOR_TYPES}
        assert keys == {
            "port_sfp_module",
            "port_sfp_vendor",
            "port_sfp_compliance",
            "port_sfp_serial",
        }

    async def test_sfp_module_sensor_value(self, hass: HomeAssistant, mock_coordinator):
        """Test SFP module sensor returns sfp_part."""
        description = next(s for s in SFP_SENSOR_TYPES if s.key == "port_sfp_module")
        sensor = UnifiPortSensor(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
            port_idx=25,
            port_label="SFP+ 1",
        )
        assert sensor.native_value == "UC-DAC-SFP+"

    async def test_sfp_vendor_sensor_value(self, hass: HomeAssistant, mock_coordinator):
        """Test SFP vendor sensor returns sfp_vendor."""
        description = next(s for s in SFP_SENSOR_TYPES if s.key == "port_sfp_vendor")
        sensor = UnifiPortSensor(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
            port_idx=25,
            port_label="SFP+ 1",
        )
        assert sensor.native_value == "Ubiquiti Inc."

    async def test_sfp_compliance_sensor_value(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test SFP compliance sensor returns sfp_compliance."""
        description = next(
            s for s in SFP_SENSOR_TYPES if s.key == "port_sfp_compliance"
        )
        sensor = UnifiPortSensor(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
            port_idx=25,
            port_label="SFP+ 1",
        )
        assert sensor.native_value == "DAC"

    async def test_sfp_serial_sensor_value(self, hass: HomeAssistant, mock_coordinator):
        """Test SFP serial sensor returns sfp_serial."""
        description = next(s for s in SFP_SENSOR_TYPES if s.key == "port_sfp_serial")
        sensor = UnifiPortSensor(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
            port_idx=25,
            port_label="SFP+ 1",
        )
        assert sensor.native_value == "SN12345"

    async def test_sfp_sensor_available_even_when_port_down(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test SFP sensors stay available even when port state is DOWN."""
        description = next(s for s in SFP_SENSOR_TYPES if s.key == "port_sfp_module")
        sensor = UnifiPortSensor(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
            port_idx=26,  # Port 26 is DOWN but has SFP media
        )
        # SFP info sensors stay available regardless of port state
        assert sensor.available is True

    async def test_port_label_in_sensor_name(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test port label is used in sensor name."""
        description = next(s for s in PORT_SENSOR_TYPES if s.key == "port_speed")
        sensor = UnifiPortSensor(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
            port_idx=25,
            port_label="SFP+ 1",
        )
        assert "SFP+ 1" in sensor.name

    async def test_sfp_sensor_name_uses_port_label(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test SFP sensor name includes port label."""
        description = next(s for s in SFP_SENSOR_TYPES if s.key == "port_sfp_module")
        sensor = UnifiPortSensor(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
            port_idx=25,
            port_label="SFP+ 1",
        )
        assert "SFP+ 1" in sensor.name

    async def test_port_extra_state_attributes(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test port sensor extra_state_attributes include port type info."""
        description = next(s for s in PORT_SENSOR_TYPES if s.key == "port_speed")
        sensor = UnifiPortSensor(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
            port_idx=25,
            port_label="SFP+ 1",
        )
        attrs = sensor.extra_state_attributes
        assert attrs is not None
        assert attrs["media_type"] == "SFP+"
        assert attrs["is_uplink"] is True
        assert attrs["port_name"] == "SFP+ 1"
        assert attrs["sfp_module_present"] is True

    async def test_port_extra_state_attributes_regular_port(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test regular port has no extra attributes if no type info."""
        description = next(s for s in PORT_SENSOR_TYPES if s.key == "port_speed")
        sensor = UnifiPortSensor(
            coordinator=mock_coordinator,
            description=description,
            site_id="site1",
            device_id="device1",
            port_idx=1,
        )
        attrs = sensor.extra_state_attributes
        # Regular port without media/is_uplink/etc. has no attributes
        assert attrs is None

    async def test_setup_creates_sfp_sensors(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Test async_setup_entry creates SFP sensors for SFP ports with modules."""
        mock_config_entry.runtime_data.coordinator = mock_coordinator

        added_entities: list = []

        def add_entities(new_entities, **kwargs):
            added_entities.extend(new_entities)

        await async_setup_entry(hass, mock_config_entry, add_entities)

        sfp_sensors = [
            e
            for e in added_entities
            if isinstance(e, UnifiPortSensor)
            and e.entity_description.key.startswith("port_sfp_")
        ]
        # Port 25 has sfp_found=True → 4 SFP sensors
        # Port 26 has sfp_found=False → 0 SFP sensors
        assert len(sfp_sensors) == 4

    async def test_setup_port_labels_passed(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Test async_setup_entry passes port labels to port sensors."""
        mock_config_entry.runtime_data.coordinator = mock_coordinator

        added_entities: list = []

        def add_entities(new_entities, **kwargs):
            added_entities.extend(new_entities)

        await async_setup_entry(hass, mock_config_entry, add_entities)

        # Find a speed sensor for port 25 (SFP+)
        sfp_speed = [
            e
            for e in added_entities
            if isinstance(e, UnifiPortSensor)
            and e.entity_description.key == "port_speed"
            and e._port_idx == 25
        ]
        assert len(sfp_speed) == 1
        assert "SFP+ 1" in sfp_speed[0].name


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

    async def test_setup_entry_creates_network_temperature_sensor(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Test that setup creates network temperature sensors when available."""
        mock_config_entry.runtime_data.coordinator = mock_coordinator

        added_entities: list = []

        def add_entities(new_entities, **kwargs):
            added_entities.extend(new_entities)

        await async_setup_entry(hass, mock_config_entry, add_entities)

        temperature_sensors = [
            entity
            for entity in added_entities
            if isinstance(entity, UnifiInsightsSensor)
            and entity.entity_description.key == "general_temperature"
        ]
        assert len(temperature_sensors) == 1
        assert temperature_sensors[0].native_value == 44.5

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

        # Add port stats using port_bytes key (matches code fallback path)
        mock_coordinator.data["stats"]["site1"]["device1"]["port_bytes"] = {
            "1": {"tx_bytes": 5000000, "rx_bytes": 3000000}
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

        # Add port stats using port_bytes key (matches code fallback path)
        mock_coordinator.data["stats"]["site1"]["device1"]["port_bytes"] = {
            "1": {"tx_bytes": 5000000, "rx_bytes": 3000000}
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

    async def test_setup_entry_stats_fallback_respects_port_state(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Test stats fallback does not create sensors for inactive ports."""
        # Device with switching feature and one UP port, one DOWN port
        mock_coordinator.data["devices"]["site1"]["device1"]["features"] = ["switching"]
        mock_coordinator.data["devices"]["site1"]["device1"]["interfaces"] = {
            "ports": [
                {"idx": 1, "state": "UP", "poe": {"enabled": True}},
                {"idx": 2, "state": "DOWN"},
            ]
        }
        # Stats have poe_ports and port_bytes for BOTH ports (including DOWN)
        mock_coordinator.data["stats"]["site1"]["device1"]["poe_ports"] = {
            1: {"power": 10.0},
            2: {"power": 0.0},
        }
        mock_coordinator.data["stats"]["site1"]["device1"]["port_bytes"] = {
            "1": {"tx_bytes": 5000, "rx_bytes": 3000},
            "2": {"tx_bytes": 0, "rx_bytes": 0},
        }
        mock_config_entry.runtime_data.coordinator = mock_coordinator

        entities = []

        def mock_add_entities(new_entities):
            entities.extend(new_entities)

        await async_setup_entry(hass, mock_config_entry, mock_add_entities)

        port_sensors = [e for e in entities if isinstance(e, UnifiPortSensor)]
        port_indices = {s._port_idx for s in port_sensors}
        # Only port 1 (UP) should have sensors, not port 2 (DOWN)
        assert 1 in port_indices
        assert 2 not in port_indices

    async def test_setup_entry_no_poe_sensor_for_non_poe_device(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Test PoE sensor is NOT created when a non-PoE device is on a PoE port."""
        mock_coordinator.data["devices"]["site1"]["device1"]["interfaces"] = {
            "ports": [
                {
                    "idx": 1,
                    "state": "UP",
                    "speedMbps": 1000,
                    # PoE port enabled but power is 0 (non-PoE device connected)
                    "poe": {"enabled": True, "power": 0.0, "good": False},
                },
                {
                    "idx": 2,
                    "state": "UP",
                    "speedMbps": 1000,
                    # PoE port with a PoE device actually drawing power
                    "poe": {"enabled": True, "power": 8.5, "good": True},
                },
            ]
        }
        mock_config_entry.runtime_data.coordinator = mock_coordinator

        entities = []

        def mock_add_entities(new_entities):
            entities.extend(new_entities)

        await async_setup_entry(hass, mock_config_entry, mock_add_entities)

        poe_sensors = [
            e
            for e in entities
            if isinstance(e, UnifiPortSensor)
            and e.entity_description.key == "port_poe_power"
        ]
        poe_port_indices = {s._port_idx for s in poe_sensors}

        # Port 1 should NOT have PoE sensor (non-PoE device, power=0)
        assert 1 not in poe_port_indices
        # Port 2 should have PoE sensor (PoE device, power=8.5)
        assert 2 in poe_port_indices

    async def test_setup_entry_poe_sensor_created_when_poe_good(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Test PoE sensor IS created when poe_good is True even with 0 power."""
        mock_coordinator.data["devices"]["site1"]["device1"]["interfaces"] = {
            "ports": [
                {
                    "idx": 1,
                    "state": "UP",
                    "speedMbps": 1000,
                    # PoE negotiation succeeded but no current draw (e.g. standby)
                    "poe": {"enabled": True, "power": 0.0, "good": True},
                },
            ]
        }
        mock_config_entry.runtime_data.coordinator = mock_coordinator

        entities = []

        def mock_add_entities(new_entities):
            entities.extend(new_entities)

        await async_setup_entry(hass, mock_config_entry, mock_add_entities)

        poe_sensors = [
            e
            for e in entities
            if isinstance(e, UnifiPortSensor)
            and e.entity_description.key == "port_poe_power"
        ]
        # Sensor should be created because poe_good=True
        assert len(poe_sensors) == 1
        assert poe_sensors[0]._port_idx == 1

    async def test_setup_entry_poe_sensor_only_enabled_no_power(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Test PoE sensor is NOT created when port has only enabled=True."""
        mock_coordinator.data["devices"]["site1"]["device1"]["interfaces"] = {
            "ports": [
                {
                    "idx": 1,
                    "state": "UP",
                    "speedMbps": 1000,
                    # PoE enabled but no power or good flag
                    "poe": {"enabled": True},
                },
            ]
        }
        mock_config_entry.runtime_data.coordinator = mock_coordinator

        entities = []

        def mock_add_entities(new_entities):
            entities.extend(new_entities)

        await async_setup_entry(hass, mock_config_entry, mock_add_entities)

        poe_sensors = [
            e
            for e in entities
            if isinstance(e, UnifiPortSensor)
            and e.entity_description.key == "port_poe_power"
        ]
        # No PoE sensor: enabled=True alone doesn't confirm a PoE device
        assert len(poe_sensors) == 0

    async def test_setup_entry_stats_fallback_skips_zero_poe(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Test stats fallback skips PoE sensors for ports with zero power."""
        mock_coordinator.data["devices"]["site1"]["device1"]["features"] = ["switching"]
        mock_coordinator.data["devices"]["site1"]["device1"]["interfaces"] = {
            "ports": [
                {"idx": 1, "state": "UP"},
                {"idx": 2, "state": "UP"},
            ]
        }
        # Stats: port 1 draws power, port 2 draws zero
        mock_coordinator.data["stats"]["site1"]["device1"]["poe_ports"] = {
            1: 12.5,
            2: 0.0,
        }
        mock_config_entry.runtime_data.coordinator = mock_coordinator

        entities = []

        def mock_add_entities(new_entities):
            entities.extend(new_entities)

        await async_setup_entry(hass, mock_config_entry, mock_add_entities)

        poe_sensors = [
            e
            for e in entities
            if isinstance(e, UnifiPortSensor)
            and e.entity_description.key == "port_poe_power"
        ]
        poe_port_indices = {s._port_idx for s in poe_sensors}

        # Port 1 should have PoE sensor (power > 0)
        assert 1 in poe_port_indices
        # Port 2 should NOT have PoE sensor (power = 0, non-PoE device)
        assert 2 not in poe_port_indices

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

    async def test_setup_entry_uplink_rate_sensors_created_with_uplink_data(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Test uplink rate sensors are created when uplink data exists."""
        # device1 already has uplink stats in default mock data
        mock_config_entry.runtime_data.coordinator = mock_coordinator

        entities = []

        def mock_add_entities(new_entities):
            entities.extend(new_entities)

        await async_setup_entry(hass, mock_config_entry, mock_add_entities)

        rate_sensors = [
            e
            for e in entities
            if isinstance(e, UnifiInsightsSensor)
            and e.entity_description.key in ("tx_rate", "rx_rate")
        ]
        rate_keys = {s.entity_description.key for s in rate_sensors}
        assert "tx_rate" in rate_keys
        assert "rx_rate" in rate_keys

    async def test_setup_entry_uplink_rate_sensors_skipped_without_data(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Test uplink rate sensors are NOT created when no uplink data exists."""
        # Remove uplink data from device1 stats
        mock_coordinator.data["stats"]["site1"]["device1"].pop("uplink", None)
        mock_config_entry.runtime_data.coordinator = mock_coordinator

        entities = []

        def mock_add_entities(new_entities):
            entities.extend(new_entities)

        await async_setup_entry(hass, mock_config_entry, mock_add_entities)

        rate_sensors = [
            e
            for e in entities
            if isinstance(e, UnifiInsightsSensor)
            and e.entity_description.key in ("tx_rate", "rx_rate")
        ]
        # device1 has no uplink stats; device2 never had any
        assert len(rate_sensors) == 0

    async def test_setup_entry_uplink_rate_name_includes_uplink(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Test uplink rate sensors have 'Uplink' in name."""
        mock_config_entry.runtime_data.coordinator = mock_coordinator

        entities = []

        def mock_add_entities(new_entities):
            entities.extend(new_entities)

        await async_setup_entry(hass, mock_config_entry, mock_add_entities)

        tx_sensor = next(
            (
                e
                for e in entities
                if isinstance(e, UnifiInsightsSensor)
                and e.entity_description.key == "tx_rate"
            ),
            None,
        )
        assert tx_sensor is not None
        assert "Uplink" in tx_sensor.entity_description.name


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

    def test_get_network_device_temperature_from_temperatures_list(self):
        """Test fallback temperature extraction from legacy temperatures list."""
        device = {
            "temperatures": [
                {"name": "CPU", "value": 54.0},
                {"name": "Local", "value": 49.5},
            ]
        }

        assert get_network_device_temperature(device) == 49.5


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

        # Add stats data for port using port_bytes key (matches code fallback path)
        mock_coordinator.data["stats"]["site1"]["device1"]["port_bytes"] = {
            "1": {"tx_bytes": 12345}
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


class TestMigrateSensorUnits:
    """Test _migrate_sensor_units for entity registry unit migration."""

    def test_migrate_sets_refresh_flag_for_port_rx_bytes(self, hass, mock_config_entry):
        """Test migration sets refresh_initial_entity_options for port_rx_bytes."""
        mock_entry = MagicMock()
        mock_entry.domain = "sensor"
        mock_entry.unique_id = "aa:bb:cc:dd:ee:ff_port_rx_bytes"
        mock_entry.entity_id = "sensor.device_port_rx_bytes"
        mock_entry.options = {}

        mock_registry = MagicMock()

        with (
            patch(
                "custom_components.unifi_insights.sensor.er.async_get",
                return_value=mock_registry,
            ),
            patch(
                "custom_components.unifi_insights.sensor.er.async_entries_for_config_entry",
                return_value=[mock_entry],
            ),
        ):
            _migrate_sensor_units(hass, mock_config_entry)

        mock_registry.async_update_entity_options.assert_called_once()
        call_args = mock_registry.async_update_entity_options.call_args
        assert call_args[0][0] == "sensor.device_port_rx_bytes"
        assert call_args[0][1] == "sensor.private"
        assert call_args[0][2]["refresh_initial_entity_options"] is True

    def test_migrate_skips_non_sensor_entities(self, hass, mock_config_entry):
        """Test migration skips non-sensor domain entities."""
        mock_entry = MagicMock()
        mock_entry.domain = "binary_sensor"
        mock_entry.unique_id = "aa:bb:cc:dd:ee:ff_port_rx_bytes"
        mock_entry.entity_id = "binary_sensor.something"
        mock_entry.options = {}

        mock_registry = MagicMock()

        with (
            patch(
                "custom_components.unifi_insights.sensor.er.async_get",
                return_value=mock_registry,
            ),
            patch(
                "custom_components.unifi_insights.sensor.er.async_entries_for_config_entry",
                return_value=[mock_entry],
            ),
        ):
            _migrate_sensor_units(hass, mock_config_entry)

        mock_registry.async_update_entity_options.assert_not_called()

    def test_migrate_skips_already_correct_units(self, hass, mock_config_entry):
        """Test migration skips entities whose suggested unit already matches."""
        mock_entry = MagicMock()
        mock_entry.domain = "sensor"
        mock_entry.unique_id = "aa:bb:cc:dd:ee:ff_port_tx_bytes"
        mock_entry.entity_id = "sensor.device_port_tx_bytes"
        mock_entry.options = {
            "sensor.private": {
                "suggested_unit_of_measurement": str(UnitOfInformation.GIGABYTES),
            }
        }

        mock_registry = MagicMock()

        with (
            patch(
                "custom_components.unifi_insights.sensor.er.async_get",
                return_value=mock_registry,
            ),
            patch(
                "custom_components.unifi_insights.sensor.er.async_entries_for_config_entry",
                return_value=[mock_entry],
            ),
        ):
            _migrate_sensor_units(hass, mock_config_entry)

        mock_registry.async_update_entity_options.assert_not_called()

    def test_migrate_skips_unrelated_sensor_keys(self, hass, mock_config_entry):
        """Test migration skips sensors whose key has no suggested unit."""
        mock_entry = MagicMock()
        mock_entry.domain = "sensor"
        mock_entry.unique_id = "aa:bb:cc:dd:ee:ff_cpu_utilization"
        mock_entry.entity_id = "sensor.device_cpu_utilization"
        mock_entry.options = {}

        mock_registry = MagicMock()

        with (
            patch(
                "custom_components.unifi_insights.sensor.er.async_get",
                return_value=mock_registry,
            ),
            patch(
                "custom_components.unifi_insights.sensor.er.async_entries_for_config_entry",
                return_value=[mock_entry],
            ),
        ):
            _migrate_sensor_units(hass, mock_config_entry)

        mock_registry.async_update_entity_options.assert_not_called()

    def test_migrate_handles_uplink_rate_sensors(self, hass, mock_config_entry):
        """Test migration sets refresh flag for uplink rate sensors."""
        mock_entry = MagicMock()
        mock_entry.domain = "sensor"
        mock_entry.unique_id = "aa:bb:cc:dd:ee:ff_tx_rate"
        mock_entry.entity_id = "sensor.device_tx_rate"
        mock_entry.options = {}

        mock_registry = MagicMock()

        with (
            patch(
                "custom_components.unifi_insights.sensor.er.async_get",
                return_value=mock_registry,
            ),
            patch(
                "custom_components.unifi_insights.sensor.er.async_entries_for_config_entry",
                return_value=[mock_entry],
            ),
        ):
            _migrate_sensor_units(hass, mock_config_entry)

        mock_registry.async_update_entity_options.assert_called_once()
        call_args = mock_registry.async_update_entity_options.call_args
        assert call_args[0][2]["refresh_initial_entity_options"] is True


class TestSiteClientSensorTypes:
    """Tests for site-level client sensor descriptions."""

    def test_site_client_sensor_types_defined(self):
        """Test that site client sensor types are defined."""
        assert len(SITE_CLIENT_SENSOR_TYPES) == 3

    def test_sensor_keys(self):
        """Test that sensor keys are correct."""
        keys = {desc.key for desc in SITE_CLIENT_SENSOR_TYPES}
        assert keys == {
            "site_total_clients",
            "site_wired_clients",
            "site_wireless_clients",
        }

    def test_total_clients_value_fn(self):
        """Test value_fn counts all clients."""
        clients = {
            "c1": {"type": "WIRED"},
            "c2": {"type": "WIRELESS"},
            "c3": {"type": "WIRED"},
        }
        desc = next(
            d for d in SITE_CLIENT_SENSOR_TYPES if d.key == "site_total_clients"
        )
        assert desc.value_fn(clients) == 3

    def test_wired_clients_value_fn(self):
        """Test value_fn counts only wired clients."""
        clients = {
            "c1": {"type": "WIRED"},
            "c2": {"type": "WIRELESS"},
            "c3": {"type": "WIRED"},
        }
        desc = next(
            d for d in SITE_CLIENT_SENSOR_TYPES if d.key == "site_wired_clients"
        )
        assert desc.value_fn(clients) == 2

    def test_wireless_clients_value_fn(self):
        """Test value_fn counts only wireless clients."""
        clients = {
            "c1": {"type": "WIRED"},
            "c2": {"type": "WIRELESS"},
            "c3": {"type": "WIRELESS"},
        }
        desc = next(
            d for d in SITE_CLIENT_SENSOR_TYPES if d.key == "site_wireless_clients"
        )
        assert desc.value_fn(clients) == 2

    def test_empty_clients(self):
        """Test value_fn handles empty clients dict."""
        clients: dict = {}
        for desc in SITE_CLIENT_SENSOR_TYPES:
            assert desc.value_fn(clients) == 0


class TestUnifiSiteClientSensor:
    """Tests for the UnifiSiteClientSensor entity class."""

    @pytest.fixture
    def mock_coordinator_with_clients(self, mock_coordinator):
        """Create a coordinator with client data for site-level tests."""
        mock_coordinator.data["clients"] = {
            "site1": {
                "c1": {"id": "c1", "type": "WIRED", "name": "PC"},
                "c2": {"id": "c2", "type": "WIRELESS", "name": "Phone"},
                "c3": {"id": "c3", "type": "WIRED", "name": "Printer"},
            }
        }
        mock_coordinator.last_update_success = True
        return mock_coordinator

    async def test_total_clients_value(
        self, hass: HomeAssistant, mock_coordinator_with_clients
    ):
        """Test total clients sensor returns correct count."""
        desc = next(
            d for d in SITE_CLIENT_SENSOR_TYPES if d.key == "site_total_clients"
        )
        sensor = UnifiSiteClientSensor(
            coordinator=mock_coordinator_with_clients,
            description=desc,
            site_id="site1",
        )
        assert sensor.native_value == 3

    async def test_wired_clients_value(
        self, hass: HomeAssistant, mock_coordinator_with_clients
    ):
        """Test wired clients sensor returns correct count."""
        desc = next(
            d for d in SITE_CLIENT_SENSOR_TYPES if d.key == "site_wired_clients"
        )
        sensor = UnifiSiteClientSensor(
            coordinator=mock_coordinator_with_clients,
            description=desc,
            site_id="site1",
        )
        assert sensor.native_value == 2

    async def test_wireless_clients_value(
        self, hass: HomeAssistant, mock_coordinator_with_clients
    ):
        """Test wireless clients sensor returns correct count."""
        desc = next(
            d for d in SITE_CLIENT_SENSOR_TYPES if d.key == "site_wireless_clients"
        )
        sensor = UnifiSiteClientSensor(
            coordinator=mock_coordinator_with_clients,
            description=desc,
            site_id="site1",
        )
        assert sensor.native_value == 1

    async def test_unique_id(self, hass: HomeAssistant, mock_coordinator_with_clients):
        """Test unique ID format."""
        desc = next(
            d for d in SITE_CLIENT_SENSOR_TYPES if d.key == "site_total_clients"
        )
        sensor = UnifiSiteClientSensor(
            coordinator=mock_coordinator_with_clients,
            description=desc,
            site_id="site1",
        )
        assert sensor.unique_id == "site1_site_total_clients"

    async def test_available(self, hass: HomeAssistant, mock_coordinator_with_clients):
        """Test availability follows coordinator update success."""
        desc = next(
            d for d in SITE_CLIENT_SENSOR_TYPES if d.key == "site_total_clients"
        )
        sensor = UnifiSiteClientSensor(
            coordinator=mock_coordinator_with_clients,
            description=desc,
            site_id="site1",
        )
        assert sensor.available is True

        mock_coordinator_with_clients.last_update_success = False
        assert sensor.available is False

    async def test_device_info_attaches_to_gateway(
        self, hass: HomeAssistant, mock_coordinator_with_clients
    ):
        """Test device info attaches to existing gateway device."""
        desc = next(
            d for d in SITE_CLIENT_SENSOR_TYPES if d.key == "site_total_clients"
        )
        sensor = UnifiSiteClientSensor(
            coordinator=mock_coordinator_with_clients,
            description=desc,
            site_id="site1",
        )
        # device2 is a UDM-Pro gateway, so the sensor should attach to it
        device_info = sensor.device_info
        assert device_info is not None
        idents = device_info.get("identifiers")
        assert idents is not None
        assert ("unifi_insights", "site1_device2") in idents

    async def test_device_info_creates_virtual_site_device(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test virtual site device created when no gateway exists."""
        # Remove the gateway device
        mock_coordinator.data["devices"] = {
            "site1": {
                "device1": {
                    "id": "device1",
                    "name": "Test Switch",
                    "model": "USW-24",
                    "features": ["switching"],
                }
            }
        }
        mock_coordinator.data["clients"] = {
            "site1": {"c1": {"id": "c1", "type": "WIRED"}}
        }
        mock_coordinator.last_update_success = True
        desc = next(
            d for d in SITE_CLIENT_SENSOR_TYPES if d.key == "site_total_clients"
        )
        sensor = UnifiSiteClientSensor(
            coordinator=mock_coordinator,
            description=desc,
            site_id="site1",
        )
        device_info = sensor.device_info
        assert device_info is not None
        idents = device_info.get("identifiers")
        assert ("unifi_insights", "site_site1") in idents

    async def test_native_value_no_clients_data(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test returns 0 when no client data for the site."""
        mock_coordinator.data["clients"] = {}
        mock_coordinator.last_update_success = True
        desc = next(
            d for d in SITE_CLIENT_SENSOR_TYPES if d.key == "site_total_clients"
        )
        sensor = UnifiSiteClientSensor(
            coordinator=mock_coordinator,
            description=desc,
            site_id="site1",
        )
        assert sensor.native_value == 0


class TestAsyncSetupEntrySiteClientSensors:
    """Tests for site-level client sensor creation in async_setup_entry."""

    async def test_setup_entry_creates_site_client_sensors(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test async_setup_entry creates site-level client sensors."""
        mock_coordinator.data["clients"] = {
            "site1": {
                "c1": {"id": "c1", "type": "WIRED"},
                "c2": {"id": "c2", "type": "WIRELESS"},
            }
        }

        config_entry = MagicMock()
        config_entry.runtime_data = MagicMock()
        config_entry.runtime_data.coordinator = mock_coordinator
        config_entry.entry_id = "test_entry"

        entities = []

        def mock_add_entities(new_entities):
            entities.extend(new_entities)

        with (
            patch(
                "custom_components.unifi_insights.sensor.er.async_get",
                return_value=MagicMock(
                    async_entries_for_config_entry=MagicMock(return_value=[])
                ),
            ),
            patch(
                "custom_components.unifi_insights.sensor.er.async_entries_for_config_entry",
                return_value=[],
            ),
        ):
            await async_setup_entry(hass, config_entry, mock_add_entities)

        site_sensors = [e for e in entities if isinstance(e, UnifiSiteClientSensor)]
        assert len(site_sensors) == 3
        keys = {s.entity_description.key for s in site_sensors}
        assert keys == {
            "site_total_clients",
            "site_wired_clients",
            "site_wireless_clients",
        }

    async def test_setup_entry_no_clients_no_site_sensors(
        self, hass: HomeAssistant, mock_coordinator
    ):
        """Test no site sensors when clients data is empty."""
        mock_coordinator.data["clients"] = {}

        config_entry = MagicMock()
        config_entry.runtime_data = MagicMock()
        config_entry.runtime_data.coordinator = mock_coordinator
        config_entry.entry_id = "test_entry"

        entities = []

        def mock_add_entities(new_entities):
            entities.extend(new_entities)

        with (
            patch(
                "custom_components.unifi_insights.sensor.er.async_get",
                return_value=MagicMock(
                    async_entries_for_config_entry=MagicMock(return_value=[])
                ),
            ),
            patch(
                "custom_components.unifi_insights.sensor.er.async_entries_for_config_entry",
                return_value=[],
            ),
        ):
            await async_setup_entry(hass, config_entry, mock_add_entities)

        site_sensors = [e for e in entities if isinstance(e, UnifiSiteClientSensor)]
        assert len(site_sensors) == 0


class TestHasProtectStat:
    """Tests for _has_protect_stat capability check."""

    def test_stat_present_in_stats(self):
        """Test capability returns True when stat exists in stats dict."""
        check = _has_protect_stat("temperature", "temperature")
        data = {"stats": {"temperature": {"value": 22.5}}}
        assert check(data) is True

    def test_stat_missing_from_stats(self):
        """Test capability returns False when stat is absent."""
        check = _has_protect_stat("temperature", "temperature")
        data = {"stats": {}, "temperature": None}
        assert check(data) is False

    def test_stat_none_in_stats(self):
        """Test capability returns False when stat value is None."""
        check = _has_protect_stat("temperature", "temperature")
        data = {"stats": {"temperature": {"value": None}}}
        assert check(data) is False

    def test_flat_field_fallback(self):
        """Test capability uses flat field when stats absent."""
        check = _has_protect_stat("temperature", "temperature")
        data = {"temperature": 22.5}
        assert check(data) is True

    def test_flat_field_none(self):
        """Test capability returns False when flat field is None."""
        check = _has_protect_stat("temperature", "temperature")
        data = {"temperature": None}
        assert check(data) is False

    def test_no_stats_no_flat(self):
        """Test capability returns False when no data at all."""
        check = _has_protect_stat("temperature", "temperature")
        assert check({}) is False

    def test_light_value_flat_key(self):
        """Test light capability with different flat key (lightValue)."""
        check = _has_protect_stat("light", "lightValue")
        data = {"lightValue": 500.0}
        assert check(data) is True

    def test_light_value_none(self):
        """Test light capability when lightValue is None."""
        check = _has_protect_stat("light", "lightValue")
        data = {"lightValue": None}
        assert check(data) is False


class TestProtectSensorCapabilityFiltering:
    """Tests for capability-based filtering of Protect sensor entities."""

    @pytest.fixture
    def mock_coordinator(self):
        """Create a mock coordinator with UP-SENSE and USL-Entry sensors."""
        coordinator = MagicMock()
        coordinator.network_client = MagicMock()
        coordinator.protect_client = MagicMock()
        coordinator.last_update_success = True
        coordinator.data = {
            "sites": {"site1": {"id": "site1", "name": "Default"}},
            "devices": {"site1": {}},
            "clients": {"site1": []},
            "stats": {"site1": {}},
            "network_info": {},
            "vouchers": {},
            "protect": {
                "sensors": {
                    "up_sense_1": {
                        "id": "up_sense_1",
                        "name": "Kitchen Sensor",
                        "model": "UP-SENSE",
                        "state": "CONNECTED",
                        "stats": {
                            "temperature": {"value": 22.5},
                            "humidity": {"value": 45},
                            "light": {"value": 500},
                        },
                        "batteryStatus": {"percentage": 85, "isLow": False},
                    },
                    "usl_entry_1": {
                        "id": "usl_entry_1",
                        "name": "Front Door Sensor",
                        "model": "USL-Entry",
                        "state": "CONNECTED",
                        "mountType": "door",
                        "isOpened": False,
                        "isTamperingDetected": False,
                        "temperature": None,
                        "humidity": None,
                        "lightValue": None,
                        "batteryStatus": {"percentage": 92, "isLow": False},
                    },
                },
                "cameras": {},
                "lights": {},
                "nvrs": {},
                "viewers": {},
                "chimes": {},
                "liveviews": {},
                "events": {},
            },
            "last_update": None,
        }
        coordinator.get_site = MagicMock(
            return_value=coordinator.data["sites"]["site1"]
        )
        return coordinator

    async def test_up_sense_gets_all_sensors(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Test UP-SENSE gets all four sensor types."""
        mock_config_entry.runtime_data.coordinator = mock_coordinator

        added_entities: list = []

        def add_entities(new_entities, **kwargs):
            added_entities.extend(new_entities)

        await async_setup_entry(hass, mock_config_entry, add_entities)

        up_sense_sensors = [
            e
            for e in added_entities
            if isinstance(e, UnifiProtectSensor) and e._device_id == "up_sense_1"
        ]
        sensor_keys = {e.entity_description.key for e in up_sense_sensors}
        assert sensor_keys == {"temperature", "humidity", "light", "battery"}

    async def test_usl_entry_gets_only_battery_sensor(
        self, hass: HomeAssistant, mock_coordinator, mock_config_entry
    ):
        """Test USL-Entry gets only battery sensor."""
        mock_config_entry.runtime_data.coordinator = mock_coordinator

        added_entities: list = []

        def add_entities(new_entities, **kwargs):
            added_entities.extend(new_entities)

        await async_setup_entry(hass, mock_config_entry, add_entities)

        usl_entry_sensors = [
            e
            for e in added_entities
            if isinstance(e, UnifiProtectSensor) and e._device_id == "usl_entry_1"
        ]
        sensor_keys = {e.entity_description.key for e in usl_entry_sensors}
        assert sensor_keys == {"battery"}
        assert "temperature" not in sensor_keys
        assert "humidity" not in sensor_keys
        assert "light" not in sensor_keys
