"""Support for UniFi Insights sensors."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import (
    EntityCategory,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    LIGHT_LUX,
    PERCENTAGE,
    UnitOfInformation,
    UnitOfPower,
    UnitOfTemperature,
)

from .const import (
    ATTR_SENSOR_BATTERY,
    ATTR_SENSOR_BATTERY_LOW,
    ATTR_SENSOR_HUMIDITY_VALUE,
    ATTR_SENSOR_ID,
    ATTR_SENSOR_LIGHT_VALUE,
    ATTR_SENSOR_NAME,
    ATTR_SENSOR_TEMPERATURE_VALUE,
    DEVICE_TYPE_SENSOR,
)
from .entity import UnifiInsightsEntity, UnifiProtectEntity, get_field

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from homeassistant.helpers.typing import StateType

    from . import UnifiInsightsConfigEntry
    from .coordinator import UnifiInsightsDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

# Coordinator handles updates centrally (Gold/Platinum requirement)
PARALLEL_UPDATES = 0


@dataclass
class UnifiInsightsSensorEntityDescription(SensorEntityDescription):  # type: ignore[misc]
    """Class describing UniFi Insights sensor entities."""

    value_fn: Callable[[dict[str, Any]], StateType] | None = None


@dataclass
class UnifiProtectSensorEntityDescription(SensorEntityDescription):  # type: ignore[misc]
    """Class describing UniFi Protect sensor entities."""

    value_fn: Callable[[dict[str, Any]], StateType] | None = None
    device_type: str | None = None


def format_uptime(seconds: int | None) -> str | None:
    """Format uptime into days, hours, minutes."""
    if seconds is None:
        return None

    days = seconds // (24 * 3600)
    seconds %= 24 * 3600
    hours = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0 or days > 0:  # Show hours if days present
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m")

    return " ".join(parts)


def get_stats_field(stats: dict, *keys: str, default: Any = None) -> Any:
    """Get a field from stats handling both camelCase and snake_case."""
    return get_field(stats, *keys, default=default)


def bytes_to_megabits(bytes_per_sec: float | None) -> float | None:
    """Convert bytes per second to megabits per second."""
    if bytes_per_sec is None:
        return None
    return round(bytes_per_sec * 8 / 1_000_000, 2)


# Sensor descriptions for UniFi Protect sensors
PROTECT_SENSOR_TYPES: tuple[UnifiProtectSensorEntityDescription, ...] = (
    # Temperature sensor
    UnifiProtectSensorEntityDescription(
        key="temperature",
        translation_key="temperature",
        name="Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda sensor: sensor.get("stats", {})
        .get("temperature", {})
        .get("value"),
        device_type=DEVICE_TYPE_SENSOR,
    ),
    # Humidity sensor
    UnifiProtectSensorEntityDescription(
        key="humidity",
        translation_key="humidity",
        name="Humidity",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda sensor: sensor.get("stats", {})
        .get("humidity", {})
        .get("value"),
        device_type=DEVICE_TYPE_SENSOR,
    ),
    # Light sensor
    UnifiProtectSensorEntityDescription(
        key="light",
        translation_key="light",
        name="Light",
        native_unit_of_measurement=LIGHT_LUX,
        device_class=SensorDeviceClass.ILLUMINANCE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda sensor: sensor.get("stats", {}).get("light", {}).get("value"),
        device_type=DEVICE_TYPE_SENSOR,
    ),
    # Battery sensor
    UnifiProtectSensorEntityDescription(
        key="battery",
        translation_key="battery",
        name="Battery",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda sensor: sensor.get("batteryStatus", {}).get("percentage"),
        device_type=DEVICE_TYPE_SENSOR,
    ),
)

# Sensor descriptions for UniFi Insights sensors
SENSOR_TYPES: tuple[UnifiInsightsSensorEntityDescription, ...] = (
    UnifiInsightsSensorEntityDescription(
        key="cpu_usage",
        translation_key="cpu_usage",
        name="CPU Usage",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.POWER_FACTOR,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:cpu-64-bit",
        value_fn=lambda stats: get_stats_field(
            stats, "cpuUtilizationPct", "cpu_utilization_pct", "cpu_percent", "cpu"
        ),
    ),
    UnifiInsightsSensorEntityDescription(
        key="memory_usage",
        translation_key="memory_usage",
        name="Memory Usage",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.POWER_FACTOR,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:memory",
        value_fn=lambda stats: get_stats_field(
            stats,
            "memoryUtilizationPct",
            "memory_utilization_pct",
            "memory_percent",
            "memory",
        ),
    ),
    UnifiInsightsSensorEntityDescription(
        key="uptime",
        translation_key="uptime",
        name="Uptime",
        device_class=None,
        # Diagnostic - uptime is informational/troubleshooting data
        entity_category=EntityCategory.DIAGNOSTIC,
        # Gold: Disable diagnostic entities by default
        entity_registry_enabled_default=False,
        icon="mdi:clock-start",
        value_fn=lambda stats: format_uptime(
            get_stats_field(
                stats, "uptimeSec", "uptime_sec", "uptime_seconds", "uptime"
            )
        ),
    ),
    UnifiInsightsSensorEntityDescription(
        key="tx_rate",
        translation_key="tx_rate",
        name="TX Rate",
        native_unit_of_measurement="Mbit/s",
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:upload-network",
        value_fn=lambda stats: bytes_to_megabits(
            get_stats_field(stats, "uplink", "uplink_stats", default={}).get(
                "txRateBps"
            )
            or get_stats_field(stats, "uplink", "uplink_stats", default={}).get(
                "tx_rate_bps"
            )
            or get_stats_field(stats, "txRateBps", "tx_rate_bps", "tx_bytes_per_sec")
        ),
    ),
    UnifiInsightsSensorEntityDescription(
        key="rx_rate",
        translation_key="rx_rate",
        name="RX Rate",
        native_unit_of_measurement="Mbit/s",
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:download-network",
        value_fn=lambda stats: bytes_to_megabits(
            get_stats_field(stats, "uplink", "uplink_stats", default={}).get(
                "rxRateBps"
            )
            or get_stats_field(stats, "uplink", "uplink_stats", default={}).get(
                "rx_rate_bps"
            )
            or get_stats_field(stats, "rxRateBps", "rx_rate_bps", "rx_bytes_per_sec")
        ),
    ),
    UnifiInsightsSensorEntityDescription(
        key="firmware_version",
        translation_key="firmware_version",
        name="Firmware Version",
        entity_category=EntityCategory.DIAGNOSTIC,
        # Gold: Disable diagnostic entities by default
        entity_registry_enabled_default=False,
        icon="mdi:text-box-check",
        value_fn=lambda device: get_field(
            device, "firmwareVersion", "firmware_version", "version"
        ),
    ),
    UnifiInsightsSensorEntityDescription(
        key="wired_clients",
        translation_key="wired_clients",
        name="Wired Clients",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:network",
        value_fn=lambda stats: len(
            [
                c
                for c in stats.get("clients", [])
                if (c.get("type") or c.get("connection_type", "")).upper() == "WIRED"
                and (c.get("uplinkDeviceId") or c.get("uplink_device_id"))
                == stats.get("id")
            ]
        ),
    ),
    UnifiInsightsSensorEntityDescription(
        key="wireless_clients",
        translation_key="wireless_clients",
        name="Wireless Clients",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:wifi",
        value_fn=lambda stats: len(
            [
                c
                for c in stats.get("clients", [])
                if (c.get("type") or c.get("connection_type", "")).upper() == "WIRELESS"
                and (c.get("uplinkDeviceId") or c.get("uplink_device_id"))
                == stats.get("id")
            ]
        ),
    ),
)

# Port sensor descriptions for UniFi switches
# These are templates - actual sensors are created dynamically per port
PORT_SENSOR_TYPES: tuple[UnifiInsightsSensorEntityDescription, ...] = (
    # PoE Power Consumption
    UnifiInsightsSensorEntityDescription(
        key="port_poe_power",
        translation_key="port_poe_power",
        name="Port {port_idx} PoE Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=None,  # Changed from DIAGNOSTIC to make visible by default
        icon="mdi:flash",
        value_fn=lambda port: get_field(port, "poe", default={}).get("power")
        or get_field(port, "poe", default={}).get("watts"),
    ),
    # Port Speed
    UnifiInsightsSensorEntityDescription(
        key="port_speed",
        translation_key="port_speed",
        name="Port {port_idx} Speed",
        native_unit_of_measurement="Mbps",
        device_class=None,
        state_class=SensorStateClass.MEASUREMENT,
        # Diagnostic - port speed is configuration/status, not monitored data
        entity_category=EntityCategory.DIAGNOSTIC,
        # Gold: Disable diagnostic entities by default
        entity_registry_enabled_default=False,
        icon="mdi:speedometer",
        value_fn=lambda port: get_field(port, "speedMbps", "speed_mbps", "speed")
        if get_field(port, "state", "status", default="").upper() == "UP"
        else 0,
    ),
    # Port TX Bytes
    UnifiInsightsSensorEntityDescription(
        key="port_tx_bytes",
        translation_key="port_tx_bytes",
        name="Port {port_idx} TX Bytes",
        native_unit_of_measurement=UnitOfInformation.BYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=None,  # Changed from DIAGNOSTIC to make visible by default
        icon="mdi:upload",
        value_fn=lambda port: get_field(port, "stats", default={}).get("txBytes")
        or get_field(port, "stats", default={}).get("tx_bytes", 0),
    ),
    # Port RX Bytes
    UnifiInsightsSensorEntityDescription(
        key="port_rx_bytes",
        translation_key="port_rx_bytes",
        name="Port {port_idx} RX Bytes",
        native_unit_of_measurement=UnitOfInformation.BYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=None,  # Changed from DIAGNOSTIC to make visible by default
        icon="mdi:download",
        value_fn=lambda port: get_field(port, "stats", default={}).get("rxBytes")
        or get_field(port, "stats", default={}).get("rx_bytes", 0),
    ),
)

# WAN sensor descriptions for UniFi gateways
WAN_SENSOR_TYPES: tuple[UnifiInsightsSensorEntityDescription, ...] = (
    # WAN IP Address
    UnifiInsightsSensorEntityDescription(
        key="wan_ip",
        translation_key="wan_ip",
        name="WAN IP Address",
        device_class=None,
        entity_category=EntityCategory.DIAGNOSTIC,
        # Gold: Disable diagnostic entities by default
        entity_registry_enabled_default=False,
        icon="mdi:ip-network",
        value_fn=lambda device: get_field(device, "ipAddress", "ip_address", "ip"),
    ),
    # WAN Uptime
    UnifiInsightsSensorEntityDescription(
        key="wan_uptime",
        translation_key="wan_uptime",
        name="WAN Uptime",
        device_class=None,
        entity_category=EntityCategory.DIAGNOSTIC,
        # Gold: Disable diagnostic entities by default
        entity_registry_enabled_default=False,
        icon="mdi:clock-start",
        value_fn=lambda stats: format_uptime(
            get_stats_field(
                stats, "uptimeSec", "uptime_sec", "uptime_seconds", "uptime"
            )
        ),
    ),
)


async def async_setup_entry(  # noqa: PLR0912
    hass: HomeAssistant,
    config_entry: UnifiInsightsConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors for UniFi Insights integration."""
    _ = hass
    _LOGGER.debug("Setting up UniFi Insights sensors")

    coordinator: UnifiInsightsDataUpdateCoordinator = (
        config_entry.runtime_data.coordinator
    )
    entities = []

    # Add sensors for each device in each site
    for site_id, devices in coordinator.data["devices"].items():
        _LOGGER.debug("Processing site %s with %d devices", site_id, len(devices))
        site_data = coordinator.get_site(site_id)
        site_name = (
            site_data.get("meta", {}).get("name", site_id) if site_data else site_id
        )

        for device_id in devices:
            device_data = (
                coordinator.data.get("devices", {}).get(site_id, {}).get(device_id, {})
            )
            device_name = device_data.get("name", device_id)

            _LOGGER.debug(
                "Creating sensors for device %s (%s) in site %s (%s)",
                device_id,
                device_name,
                site_id,
                site_name,
            )

            for description in SENSOR_TYPES:
                entities.append(  # noqa: PERF401
                    UnifiInsightsSensor(
                        coordinator=coordinator,
                        description=description,
                        site_id=site_id,
                        device_id=device_id,
                    )
                )

            # Add port sensors for switches with port interfaces
            # Handle both camelCase and snake_case for interface keys
            interfaces = get_field(device_data, "interfaces", default={})
            # Ensure interfaces is a dict before accessing ports
            if isinstance(interfaces, dict):
                ports = get_field(interfaces, "ports", default=[])
            else:
                ports = []
            if ports:
                _LOGGER.debug(
                    "Device %s has %d ports, creating port sensors",
                    device_name,
                    len(ports),
                )

                for port in ports:
                    port_idx = get_field(port, "idx", "index", "port_idx")
                    if port_idx is None:
                        continue

                    # Only create sensors for active ports (state = "UP")
                    port_state = get_field(port, "state", "status", default="DOWN")
                    if str(port_state).upper() != "UP":
                        _LOGGER.debug(
                            "Skipping port %d on device %s - port state is %s (not UP)",
                            port_idx,
                            device_name,
                            port_state,
                        )
                        continue

                    # Create PoE power sensor only for PoE-capable ports
                    poe_data = get_field(port, "poe", default={})
                    if poe_data.get("enabled"):
                        poe_desc = PORT_SENSOR_TYPES[0]  # PoE power sensor
                        entities.append(
                            UnifiPortSensor(
                                coordinator=coordinator,
                                description=poe_desc,
                                site_id=site_id,
                                device_id=device_id,
                                port_idx=port_idx,
                            )
                        )

                    # Create speed sensor for all active ports
                    speed_desc = PORT_SENSOR_TYPES[1]  # Port speed sensor
                    entities.append(
                        UnifiPortSensor(
                            coordinator=coordinator,
                            description=speed_desc,
                            site_id=site_id,
                            device_id=device_id,
                            port_idx=port_idx,
                        )
                    )

                    # Create TX/RX bytes sensors for all active ports
                    tx_desc = PORT_SENSOR_TYPES[2]  # TX bytes sensor
                    rx_desc = PORT_SENSOR_TYPES[3]  # RX bytes sensor
                    entities.append(
                        UnifiPortSensor(
                            coordinator=coordinator,
                            description=tx_desc,
                            site_id=site_id,
                            device_id=device_id,
                            port_idx=port_idx,
                        )
                    )
                    entities.append(
                        UnifiPortSensor(
                            coordinator=coordinator,
                            description=rx_desc,
                            site_id=site_id,
                            device_id=device_id,
                            port_idx=port_idx,
                        )
                    )

            # Add WAN sensors for gateway devices
            features = get_field(device_data, "features", default={})
            model = get_field(device_data, "model", default="")
            if (
                "switching" in features or "gateway" in features or "router" in features
            ) and (model.startswith(("UDM", "USG")) or "gateway" in model.lower()):
                _LOGGER.debug(
                    "Device %s is a gateway, creating WAN sensors", device_name
                )

                for description in WAN_SENSOR_TYPES:
                    entities.append(  # noqa: PERF401
                        UnifiInsightsSensor(
                            coordinator=coordinator,
                            description=description,
                            site_id=site_id,
                            device_id=device_id,
                        )
                    )

    # Add UniFi Protect sensors if API is available
    if coordinator.protect_client:
        # Add sensors for UniFi Protect sensors
        for sensor_id, sensor_data in coordinator.data["protect"]["sensors"].items():
            sensor_name = sensor_data.get("name", f"Sensor {sensor_id}")

            _LOGGER.debug(
                "Creating sensors for UniFi Protect sensor %s (%s)",
                sensor_id,
                sensor_name,
            )

            for description in PROTECT_SENSOR_TYPES:
                if description.device_type == DEVICE_TYPE_SENSOR:
                    entities.append(  # noqa: PERF401
                        UnifiProtectSensor(
                            coordinator=coordinator,
                            description=description,
                            device_id=sensor_id,
                        )
                    )

    _LOGGER.info("Adding %d UniFi Insights sensors", len(entities))
    async_add_entities(entities)


class UnifiInsightsSensor(UnifiInsightsEntity, SensorEntity):  # type: ignore[misc]
    """Representation of a UniFi Insights Sensor."""

    entity_description: UnifiInsightsSensorEntityDescription

    def __init__(
        self,
        coordinator: UnifiInsightsDataUpdateCoordinator,
        description: UnifiInsightsSensorEntityDescription,
        site_id: str,
        device_id: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, description, site_id, device_id)

        _LOGGER.debug(
            "Initializing %s sensor for device %s in site %s",
            description.key,
            device_id,
            site_id,
        )

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        # Special handling for sensors that come from device data (not stats)
        if self.entity_description.key in ["firmware_version", "wan_ip"]:
            device = (
                self.coordinator.data["devices"]
                .get(self._site_id, {})
                .get(self._device_id)
            )
            if not device:
                _LOGGER.debug(
                    "No device data available for %s sensor (device %s in site %s)",
                    self.entity_description.key,
                    self._device_id,
                    self._site_id,
                )
                return None
            value = self.entity_description.value_fn(device)
        else:
            # For all other sensors, use stats data
            if (
                not self.coordinator.data["stats"]
                .get(self._site_id, {})
                .get(self._device_id)
            ):
                _LOGGER.debug(
                    "No stats available for sensor %s (device %s in site %s)",
                    self.entity_description.key,
                    self._device_id,
                    self._site_id,
                )
                return None

            stats = self.coordinator.data["stats"][self._site_id][self._device_id]
            value = self.entity_description.value_fn(stats)

        _LOGGER.debug(
            "Sensor %s for device %s in site %s updated to %s %s",
            self.entity_description.key,
            self._device_id,
            self._site_id,
            value,
            self.native_unit_of_measurement or "",
        )

        return value

    async def async_update(self) -> None:
        """Update the sensor."""
        await super().async_update()
        _LOGGER.debug(
            "Updated sensor %s for device %s in site %s",
            self.entity_description.key,
            self._device_id,
            self._site_id,
        )


class UnifiPortSensor(UnifiInsightsEntity, SensorEntity):  # type: ignore[misc]
    """Representation of a UniFi Port Sensor."""

    entity_description: UnifiInsightsSensorEntityDescription

    def __init__(
        self,
        coordinator: UnifiInsightsDataUpdateCoordinator,
        description: UnifiInsightsSensorEntityDescription,
        site_id: str,
        device_id: str,
        port_idx: int,
    ) -> None:
        """Initialize the port sensor."""
        super().__init__(coordinator, description, site_id, device_id)
        self._port_idx = port_idx

        # Customize the name to include port number
        port_name = description.name.format(port_idx=port_idx)
        self._attr_name = port_name

        # Create unique ID with port index
        self._attr_unique_id = f"{device_id}_{description.key}_{port_idx}"

        _LOGGER.debug(
            "Initializing %s sensor for port %d on device %s in site %s",
            description.key,
            port_idx,
            device_id,
            site_id,
        )

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        # Get device data to access port information
        device_data = (
            self.coordinator.data.get("devices", {})
            .get(self._site_id, {})
            .get(self._device_id, {})
        )

        if not device_data:
            _LOGGER.debug(
                "No device data available for port sensor %s (device %s in site %s)",
                self.entity_description.key,
                self._device_id,
                self._site_id,
            )
            return None

        # Find the port data
        ports = device_data.get("interfaces", {}).get("ports", [])
        port_data = None
        for port in ports:
            if port.get("idx") == self._port_idx:
                port_data = port
                break

        if not port_data:
            _LOGGER.debug(
                "No port data available for port %d on device %s",
                self._port_idx,
                self._device_id,
            )
            return None

        # Get stats data if needed for TX/RX bytes
        if self.entity_description.key in ["port_tx_bytes", "port_rx_bytes"]:
            stats = (
                self.coordinator.data.get("stats", {})
                .get(self._site_id, {})
                .get(self._device_id, {})
            )
            if stats:
                # Add stats to port data for value_fn
                port_data = {
                    **port_data,
                    "stats": stats.get("ports", {}).get(str(self._port_idx), {}),
                }

        # Use value_fn to extract the value
        value = self.entity_description.value_fn(port_data)

        _LOGGER.debug(
            "Port sensor %s for port %d on device %s updated to %s %s",
            self.entity_description.key,
            self._port_idx,
            self._device_id,
            value,
            self.native_unit_of_measurement or "",
        )

        return value

    @property
    def available(self) -> bool:  # noqa: PLR0911
        """Return if entity is available."""
        # Port sensors are available if the device is available AND the port is UP
        if not self.coordinator.last_update_success:
            return False

        # Get device data
        devices = self.coordinator.data.get("devices", {})
        if not isinstance(devices, dict):
            return False
        site_devices = devices.get(self._site_id, {})
        if not isinstance(site_devices, dict):
            return False
        device_data = site_devices.get(self._device_id, {})
        if not device_data or not isinstance(device_data, dict):
            return False

        # Find the port data
        ports = device_data.get("interfaces", {})
        if not isinstance(ports, dict):
            return False
        port_list = ports.get("ports", [])
        if not isinstance(port_list, list):
            return False

        port_data = None
        for port in port_list:
            if port.get("idx") == self._port_idx:
                port_data = port
                break

        if not port_data:
            return False

        # Port sensor is only available if port state is UP
        port_state = port_data.get("state", "DOWN")
        return isinstance(port_state, str) and port_state == "UP"


class UnifiProtectSensor(UnifiProtectEntity, SensorEntity):  # type: ignore[misc]
    """Representation of a UniFi Protect Sensor."""

    entity_description: UnifiProtectSensorEntityDescription

    def __init__(
        self,
        coordinator: UnifiInsightsDataUpdateCoordinator,
        description: UnifiProtectSensorEntityDescription,
        device_id: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator, description.device_type, device_id, description.key
        )
        self.entity_description = description

        # Set entity category for battery sensors
        if description.key == "battery":
            self._attr_entity_category = EntityCategory.DIAGNOSTIC

        # Set name
        self._attr_name = description.name

        # Update initial state
        self._update_from_data()

        _LOGGER.debug(
            "Initializing %s sensor for %s device %s",
            description.key,
            description.device_type,
            device_id,
        )

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        device_data = self.coordinator.data["protect"][
            f"{self.entity_description.device_type}s"
        ].get(self._device_id)
        if not device_data:
            return None

        value = self.entity_description.value_fn(device_data)

        _LOGGER.debug(
            "Sensor %s for %s device %s updated to %s %s",
            self.entity_description.key,
            self.entity_description.device_type,
            self._device_id,
            value,
            self.native_unit_of_measurement or "",
        )

        return value

    def _update_from_data(self) -> None:
        """Update entity from data."""
        device_data = self.coordinator.data["protect"][
            f"{self.entity_description.device_type}s"
        ].get(self._device_id, {})

        # Set attributes based on sensor type
        if self.entity_description.key == "temperature":
            self._attr_extra_state_attributes = {
                ATTR_SENSOR_ID: self._device_id,
                ATTR_SENSOR_NAME: device_data.get("name"),
                ATTR_SENSOR_TEMPERATURE_VALUE: device_data.get("stats", {})
                .get("temperature", {})
                .get("value"),
            }
        elif self.entity_description.key == "humidity":
            self._attr_extra_state_attributes = {
                ATTR_SENSOR_ID: self._device_id,
                ATTR_SENSOR_NAME: device_data.get("name"),
                ATTR_SENSOR_HUMIDITY_VALUE: device_data.get("stats", {})
                .get("humidity", {})
                .get("value"),
            }
        elif self.entity_description.key == "light":
            self._attr_extra_state_attributes = {
                ATTR_SENSOR_ID: self._device_id,
                ATTR_SENSOR_NAME: device_data.get("name"),
                ATTR_SENSOR_LIGHT_VALUE: device_data.get("stats", {})
                .get("light", {})
                .get("value"),
            }
        elif self.entity_description.key == "battery":
            self._attr_extra_state_attributes = {
                ATTR_SENSOR_ID: self._device_id,
                ATTR_SENSOR_NAME: device_data.get("name"),
                ATTR_SENSOR_BATTERY: device_data.get("batteryStatus", {}).get(
                    "percentage"
                ),
                ATTR_SENSOR_BATTERY_LOW: device_data.get("batteryStatus", {}).get(
                    "isLow", False
                ),
            }
