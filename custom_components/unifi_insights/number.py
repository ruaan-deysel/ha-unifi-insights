"""Support for UniFi Protect number entities."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.core import callback
from homeassistant.helpers.entity import EntityCategory

from .const import (
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
from .entity import UnifiProtectEntity, async_call_coordinator_action
from .led_level import led_level_to_percent, percent_to_led_level

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from . import UnifiInsightsConfigEntry
    from .coordinators import UnifiFacadeCoordinator

_LOGGER = logging.getLogger(__name__)

# Number entities are action-based, allow parallel execution
PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: UnifiInsightsConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up number entities for UniFi Protect integration."""
    _ = hass
    coordinator: UnifiFacadeCoordinator = entry.runtime_data.coordinator

    # Skip if Protect API is not available
    if not coordinator.protect_client:
        _LOGGER.debug("Skipping number setup - Protect API not available")
        return

    known_number_keys: set[tuple[str, str]] = set()

    @callback
    def async_discover_numbers() -> None:
        """Discover and add new number entities."""
        if (
            not coordinator.data
            or not isinstance(coordinator.data, dict)
            or "protect" not in coordinator.data
            or not isinstance(coordinator.data["protect"], dict)
        ):
            return

        protect = coordinator.data["protect"]
        entities: list[NumberEntity] = []

        # Add camera microphone volume numbers
        cameras = protect.get("cameras", {})
        if isinstance(cameras, dict):
            for camera_id, camera_data in cameras.items():
                if not isinstance(camera_data, dict):
                    continue
                key = (camera_id, "mic_volume")
                if key in known_number_keys:
                    continue
                known_number_keys.add(key)
                _LOGGER.debug(
                    "Adding microphone volume number for camera %s",
                    camera_data.get("name", camera_id),
                )
                entities.append(
                    UnifiProtectMicrophoneVolumeNumber(
                        coordinator=coordinator,
                        camera_id=camera_id,
                    )
                )

        # Add light brightness level numbers
        lights = protect.get("lights", {})
        if isinstance(lights, dict):
            for light_id, light_data in lights.items():
                if not isinstance(light_data, dict):
                    continue
                key = (light_id, "light_level")
                if key in known_number_keys:
                    continue
                known_number_keys.add(key)
                _LOGGER.debug(
                    "Adding brightness level number for light %s",
                    light_data.get("name", light_id),
                )
                entities.append(
                    UnifiProtectLightLevelNumber(
                        coordinator=coordinator,
                        light_id=light_id,
                    )
                )

        # Add chime volume and repeat times numbers
        chimes = protect.get("chimes", {})
        if isinstance(chimes, dict):
            for chime_id, chime_data in chimes.items():
                if not isinstance(chime_data, dict):
                    continue
                vol_key = (chime_id, "chime_volume")
                if vol_key not in known_number_keys:
                    known_number_keys.add(vol_key)
                    _LOGGER.debug(
                        "Adding volume number for chime %s",
                        chime_data.get("name", chime_id),
                    )
                    entities.append(
                        UnifiProtectChimeVolumeNumber(
                            coordinator=coordinator,
                            chime_id=chime_id,
                        )
                    )

                rep_key = (chime_id, "repeat_times")
                if rep_key not in known_number_keys:
                    known_number_keys.add(rep_key)
                    _LOGGER.debug(
                        "Adding repeat times number for chime %s",
                        chime_data.get("name", chime_id),
                    )
                    entities.append(
                        UnifiProtectChimeRepeatTimesNumber(
                            coordinator=coordinator,
                            chime_id=chime_id,
                        )
                    )

        if entities:
            _LOGGER.info("Adding %d UniFi Protect number entities", len(entities))
            async_add_entities(entities)

    async_discover_numbers()
    entry.async_on_unload(coordinator.async_add_listener(async_discover_numbers))


class UnifiProtectMicrophoneVolumeNumber(UnifiProtectEntity, NumberEntity):
    """Representation of a UniFi Protect Camera Microphone Volume Number."""

    _attr_has_entity_name = True
    _attr_translation_key = "mic_volume"
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER

    def __init__(
        self,
        coordinator: UnifiFacadeCoordinator,
        camera_id: str,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(
            coordinator, DEVICE_TYPE_CAMERA, camera_id, "microphone_volume"
        )

        # Set entity category
        self._attr_entity_category = EntityCategory.CONFIG

        # Set initial state
        self._update_from_data()

    def _update_from_data(self) -> None:
        """Update entity from data."""
        camera_data = self.coordinator.data["protect"]["cameras"].get(
            self._device_id, {}
        )

        # Set value
        self._attr_native_value = camera_data.get("micVolume", 0)

        # Set attributes
        self._attr_extra_state_attributes = {
            ATTR_CAMERA_ID: self._device_id,
            ATTR_CAMERA_NAME: camera_data.get("name"),
            ATTR_MIC_ENABLED: camera_data.get("micEnabled", False),
        }

    async def async_set_native_value(self, value: float) -> None:
        """Set the microphone volume."""
        _LOGGER.debug(
            "Setting microphone volume to %s for camera %s", value, self._device_id
        )

        await async_call_coordinator_action(
            self.coordinator,
            "async_set_microphone_volume",
            f"Unable to set microphone volume for camera {self._device_id}",
            self._device_id,
            int(value),
            fallback_factory=lambda: (
                self.coordinator.protect_client.set_microphone_volume(  # type: ignore[union-attr]
                    camera_id=self._device_id,
                    volume=int(value),
                )
            ),
        )
        self._attr_native_value = value
        self.async_write_ha_state()


class UnifiProtectLightLevelNumber(UnifiProtectEntity, NumberEntity):
    """Representation of a UniFi Protect Light Brightness Level Number."""

    _attr_has_entity_name = True
    _attr_translation_key = "brightness_level"
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER

    def __init__(
        self,
        coordinator: UnifiFacadeCoordinator,
        light_id: str,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator, DEVICE_TYPE_LIGHT, light_id, "brightness_level")

        # Set entity category
        self._attr_entity_category = EntityCategory.CONFIG

        # Set initial state
        self._update_from_data()

    def _update_from_data(self) -> None:
        """Update entity from data."""
        light_data = self.coordinator.data["protect"]["lights"].get(self._device_id, {})

        # The slider is a 0-100 percentage; Protect stores a 1-6 ledLevel.
        # lightDeviceSettings can be present but None, as in light.py.
        device_settings = light_data.get("lightDeviceSettings")
        led_level = (
            device_settings.get("ledLevel")
            if isinstance(device_settings, dict)
            else None
        )
        self._attr_native_value = led_level_to_percent(led_level)

        # Set attributes
        self._attr_extra_state_attributes = {
            ATTR_LIGHT_ID: self._device_id,
            ATTR_LIGHT_NAME: light_data.get("name"),
            ATTR_LIGHT_LEVEL: led_level,
        }

    async def async_set_native_value(self, value: float) -> None:
        """Set the light brightness level."""
        led_level = percent_to_led_level(value)
        _LOGGER.debug(
            "Setting light level to %s%% (led_level %s) for light %s",
            value,
            led_level,
            self._device_id,
        )

        await async_call_coordinator_action(
            self.coordinator,
            "async_set_light_brightness",
            f"Unable to set brightness for light {self._device_id}",
            self._device_id,
            led_level,
            fallback_factory=lambda: (
                self.coordinator.protect_client.lights.set_brightness(  # type: ignore[union-attr]
                    self._device_id,
                    led_level,
                )
            ),
        )
        # Show the percentage Protect will report for the level it was given
        self._attr_native_value = led_level_to_percent(led_level)
        self.async_write_ha_state()


class UnifiProtectChimeVolumeNumber(UnifiProtectEntity, NumberEntity):
    """Representation of a UniFi Protect Chime Volume Number."""

    _attr_has_entity_name = True
    _attr_translation_key = "chime_volume"
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER
    _attr_icon = "mdi:volume-high"

    def __init__(
        self,
        coordinator: UnifiFacadeCoordinator,
        chime_id: str,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator, DEVICE_TYPE_CHIME, chime_id, "volume")

        # Set entity category
        self._attr_entity_category = EntityCategory.CONFIG

        # Set initial state
        self._update_from_data()

    def _update_from_data(self) -> None:
        """Update entity from data."""
        chime_data = self.coordinator.data["protect"]["chimes"].get(self._device_id, {})

        # Get ring settings - use the first camera's settings or default to 80
        ring_settings = chime_data.get("ringSettings", [])
        volume = 80  # Default volume

        if ring_settings:
            # Use the first camera's settings
            volume = ring_settings[0].get("volume", 80)

        # Set value
        self._attr_native_value = volume

        # Set attributes
        self._attr_extra_state_attributes = {
            ATTR_CHIME_ID: self._device_id,
            ATTR_CHIME_NAME: chime_data.get("name"),
            ATTR_CHIME_VOLUME: volume,
        }

    async def async_set_native_value(self, value: float) -> None:
        """Set the chime volume level."""
        _LOGGER.debug("Setting chime volume to %s for chime %s", value, self._device_id)

        await async_call_coordinator_action(
            self.coordinator,
            "async_set_chime_volume",
            f"Unable to set volume for chime {self._device_id}",
            self._device_id,
            int(value),
            fallback_factory=lambda: self.coordinator.protect_client.set_chime_volume(  # type: ignore[union-attr]
                chime_id=self._device_id,
                volume=int(value),
            ),
        )
        self._attr_native_value = int(value)
        self.async_write_ha_state()


class UnifiProtectChimeRepeatTimesNumber(UnifiProtectEntity, NumberEntity):
    """Representation of a UniFi Protect Chime Repeat Times Number."""

    _attr_has_entity_name = True
    _attr_translation_key = "repeat_times"
    _attr_native_min_value = 1
    _attr_native_max_value = 10
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:repeat"

    def __init__(
        self,
        coordinator: UnifiFacadeCoordinator,
        chime_id: str,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator, DEVICE_TYPE_CHIME, chime_id, "repeat_times")

        # Set entity category
        self._attr_entity_category = EntityCategory.CONFIG

        # Set initial state
        self._update_from_data()

    def _update_from_data(self) -> None:
        """Update entity from data."""
        chime_data = self.coordinator.data["protect"]["chimes"].get(self._device_id, {})

        # Get ring settings - use the first camera's settings or default to 3
        ring_settings = chime_data.get("ringSettings", [])
        repeat_times = 3  # Default repeat times

        if ring_settings:
            # Use the first camera's settings
            repeat_times = ring_settings[0].get("repeatTimes", 3)

        # Set value
        self._attr_native_value = repeat_times

        # Set attributes
        self._attr_extra_state_attributes = {
            ATTR_CHIME_ID: self._device_id,
            ATTR_CHIME_NAME: chime_data.get("name"),
            ATTR_CHIME_REPEAT_TIMES: repeat_times,
        }

    async def async_set_native_value(self, value: float) -> None:
        """Set the chime repeat times."""
        _LOGGER.debug(
            "Setting chime repeat times to %s for chime %s", value, self._device_id
        )

        await async_call_coordinator_action(
            self.coordinator,
            "async_set_chime_repeat",
            f"Unable to set repeat count for chime {self._device_id}",
            self._device_id,
            int(value),
            fallback_factory=lambda: self.coordinator.protect_client.set_chime_repeat(  # type: ignore[union-attr]
                chime_id=self._device_id,
                repeat_times=int(value),
            ),
        )
        self._attr_native_value = int(value)
        self.async_write_ha_state()
