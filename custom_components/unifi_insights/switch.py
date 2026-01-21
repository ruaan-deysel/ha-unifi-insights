"""Support for UniFi Protect switches."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.entity import EntityCategory

from .const import (
    ATTR_CAMERA_ID,
    ATTR_CAMERA_NAME,
    ATTR_MIC_ENABLED,
    DEVICE_TYPE_CAMERA,
)
from .entity import UnifiProtectEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from . import UnifiInsightsConfigEntry
    from .coordinator import UnifiInsightsDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

# Switch entities are action-based, allow parallel execution
PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: UnifiInsightsConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switches for UniFi integration."""
    _ = hass
    coordinator: UnifiInsightsDataUpdateCoordinator = entry.runtime_data.coordinator
    entities: list[SwitchEntity] = []

    # Add PoE switches for network switch ports
    for site_id, devices in coordinator.data.get("devices", {}).items():
        for device_id, device_data in devices.items():
            # Check if device has switching feature and ports
            features = device_data.get("features", [])
            if "switching" not in features:
                continue

            # Get port configuration from interfaces or stats
            stats = (
                coordinator.data.get("stats", {}).get(site_id, {}).get(device_id, {})
            )
            ports = stats.get("ports", [])

            for port in ports:
                port_idx = port.get("idx") or port.get("portIdx")
                if port_idx is None:
                    continue

                # Check if port supports PoE
                poe_config = port.get("poe", {})
                if not poe_config:
                    continue

                _LOGGER.debug(
                    "Adding PoE switch for port %s on device %s",
                    port_idx,
                    device_data.get("name", device_id),
                )
                entities.append(
                    UnifiPoESwitch(
                        coordinator=coordinator,
                        site_id=site_id,
                        device_id=device_id,
                        port_idx=port_idx,
                    )
                )

    # Add Protect switches if available
    if coordinator.protect_client:
        # Add camera microphone switches
        for camera_id, camera_data in coordinator.data["protect"]["cameras"].items():
            _LOGGER.debug(
                "Adding microphone switch for camera %s",
                camera_data.get("name", camera_id),
            )
            entities.append(
                UnifiProtectMicrophoneSwitch(
                    coordinator=coordinator,
                    camera_id=camera_id,
                )
            )

    _LOGGER.info("Adding %d UniFi switches", len(entities))
    async_add_entities(entities)


class UnifiProtectMicrophoneSwitch(UnifiProtectEntity, SwitchEntity):  # type: ignore[misc]
    """Representation of a UniFi Protect Camera Microphone Switch."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: UnifiInsightsDataUpdateCoordinator,
        camera_id: str,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, DEVICE_TYPE_CAMERA, camera_id, "microphone")

        # Set entity category
        self._attr_entity_category = EntityCategory.CONFIG

        # Set name
        self._attr_name = "Microphone"

        # Set initial state
        self._update_from_data()

    def _update_from_data(self) -> None:
        """Update entity from data."""
        camera_data = self.coordinator.data["protect"]["cameras"].get(
            self._device_id, {}
        )

        # Set state
        self._attr_is_on = camera_data.get("micEnabled", False)

        # Set attributes
        self._attr_extra_state_attributes = {
            ATTR_CAMERA_ID: self._device_id,
            ATTR_CAMERA_NAME: camera_data.get("name"),
            ATTR_MIC_ENABLED: self._attr_is_on,
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the microphone on."""
        _ = kwargs
        _LOGGER.debug("Turning on microphone for camera %s", self._device_id)

        try:
            await self.coordinator.protect_client.update_camera(
                camera_id=self._device_id,
                data={"micEnabled": True},
            )
            self._attr_is_on = True
            self.async_write_ha_state()
        except Exception:
            _LOGGER.exception("Error turning on microphone")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the microphone off."""
        _ = kwargs
        _LOGGER.debug("Turning off microphone for camera %s", self._device_id)

        try:
            await self.coordinator.protect_client.update_camera(
                camera_id=self._device_id,
                data={"micEnabled": False},
            )
            self._attr_is_on = False
            self.async_write_ha_state()
        except Exception:
            _LOGGER.exception("Error turning off microphone")


class UnifiPoESwitch(SwitchEntity):  # type: ignore[misc]
    """Representation of a UniFi PoE Port Switch."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:ethernet"

    def __init__(
        self,
        coordinator: UnifiInsightsDataUpdateCoordinator,
        site_id: str,
        device_id: str,
        port_idx: int,
    ) -> None:
        """Initialize the switch."""
        self.coordinator = coordinator
        self._site_id = site_id
        self._device_id = device_id
        self._port_idx = port_idx

        # Get device info for naming
        device_data = self._get_device_data()
        device_name = device_data.get("name", device_id)

        self._attr_unique_id = f"{site_id}_{device_id}_port_{port_idx}_poe"
        self._attr_name = f"Port {port_idx} PoE"
        self._attr_entity_category = EntityCategory.CONFIG

        # Device info
        self._attr_device_info = {
            "identifiers": {("unifi_insights", device_id)},
            "name": device_name,
            "manufacturer": "Ubiquiti",
            "model": device_data.get("model", "UniFi Switch"),
            "via_device": ("unifi_insights", site_id),
        }

        # Set initial state
        self._update_from_data()

    def _get_device_data(self) -> dict[str, Any]:
        """Get device data from coordinator."""
        result: dict[str, Any] = (
            self.coordinator.data.get("devices", {})
            .get(self._site_id, {})
            .get(self._device_id, {})
        )
        return result

    def _get_port_data(self) -> dict[str, Any]:
        """Get port data from coordinator."""
        stats = (
            self.coordinator.data.get("stats", {})
            .get(self._site_id, {})
            .get(self._device_id, {})
        )
        ports = stats.get("ports", [])
        for port in ports:
            if (
                port.get("idx") == self._port_idx
                or port.get("portIdx") == self._port_idx
            ):
                result: dict[str, Any] = port
                return result
        return {}

    def _update_from_data(self) -> None:
        """Update entity from data."""
        port_data = self._get_port_data()
        poe_config = port_data.get("poe", {})

        # PoE is on if enabled
        self._attr_is_on = poe_config.get("enabled", False)

        # Set extra attributes
        self._attr_extra_state_attributes = {
            "port_idx": self._port_idx,
            "poe_mode": poe_config.get("mode"),
            "poe_power": poe_config.get("power"),
            "port_state": port_data.get("state"),
            "speed_mbps": port_data.get("speedMbps"),
        }

    @property
    def available(self) -> bool:
        """Return if the switch is available."""
        device_data = self._get_device_data()
        if not device_data:
            return False
        state = device_data.get("state")
        return bool(state == "ONLINE")

    @property
    def is_on(self) -> bool:
        """Return true if PoE is enabled."""
        self._update_from_data()
        return bool(self._attr_is_on)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable PoE on the port."""
        _ = kwargs
        _LOGGER.debug(
            "Enabling PoE on port %s of device %s", self._port_idx, self._device_id
        )

        try:
            await self.coordinator.network_client.devices.execute_port_action(
                self._site_id,
                self._device_id,
                self._port_idx,
                poe_mode="auto",  # Enable PoE with auto mode
            )
            self._attr_is_on = True
            self.async_write_ha_state()
            # Request coordinator refresh
            await self.coordinator.async_request_refresh()
        except Exception:
            _LOGGER.exception("Error enabling PoE on port %s", self._port_idx)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable PoE on the port."""
        _ = kwargs
        _LOGGER.debug(
            "Disabling PoE on port %s of device %s", self._port_idx, self._device_id
        )

        try:
            await self.coordinator.network_client.devices.execute_port_action(
                self._site_id,
                self._device_id,
                self._port_idx,
                poe_mode="off",  # Disable PoE
            )
            self._attr_is_on = False
            self.async_write_ha_state()
            # Request coordinator refresh
            await self.coordinator.async_request_refresh()
        except Exception:
            _LOGGER.exception("Error disabling PoE on port %s", self._port_idx)
