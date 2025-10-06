"""Data update coordinator for UniFi Insights."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    DEVICE_TYPE_CAMERA,
    DEVICE_TYPE_CHIME,
    DEVICE_TYPE_LIGHT,
    DEVICE_TYPE_NVR,
    DEVICE_TYPE_SENSOR,
    DEVICE_TYPE_VIEWER,
    DOMAIN,
    SCAN_INTERVAL_NORMAL,
)
from .unifi_network_api import (
    UnifiInsightsAuthError,
    UnifiInsightsClient,
    UnifiInsightsConnectionError,
)

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

    from .unifi_protect_api import (
        UnifiProtectClient,
    )

_LOGGER = logging.getLogger(__name__)


class UnifiInsightsDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching UniFi Insights data."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        api: UnifiInsightsClient,
        protect_api: UnifiProtectClient | None = None,
        entry: ConfigEntry = None,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL_NORMAL,
        )
        self.api = api
        self.protect_api = protect_api
        self.config_entry = entry
        self._available = True
        self.data = {
            "sites": {},
            "devices": {},
            "clients": {},
            "stats": {},
            "network_info": {},
            "vouchers": {},
            "protect": {
                "cameras": {},
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "viewers": {},
                "chimes": {},
                "liveviews": {},
                "protect_info": {},
                "events": {},
            },
            "last_update": None,
        }

        # Register WebSocket callbacks if Protect API is available
        if self.protect_api:
            self.protect_api.register_device_update_callback(self._handle_device_update)
            self.protect_api.register_event_update_callback(self._handle_event_update)

    def get_site(self, site_id: str) -> dict[str, Any] | None:
        """Get site data by site ID."""
        return self.data.get("sites", {}).get(site_id)

    def _handle_device_update(
        self, model_key: str, device_data: dict[str, Any]
    ) -> None:
        """Handle device update from WebSocket."""
        device_id = device_data.get("id")
        if not device_id:
            return

        _LOGGER.debug("Handling device update for %s: %s", model_key, device_id)

        if model_key == DEVICE_TYPE_CAMERA:
            self.data["protect"]["cameras"][device_id] = device_data
        elif model_key == DEVICE_TYPE_LIGHT:
            self.data["protect"]["lights"][device_id] = device_data
        elif model_key == DEVICE_TYPE_SENSOR:
            self.data["protect"]["sensors"][device_id] = device_data
        elif model_key == DEVICE_TYPE_NVR:
            self.data["protect"]["nvrs"][device_id] = device_data
        elif model_key == DEVICE_TYPE_VIEWER:
            self.data["protect"]["viewers"][device_id] = device_data
        elif model_key == DEVICE_TYPE_CHIME:
            self.data["protect"]["chimes"][device_id] = device_data

        self.async_update_listeners()

    def _handle_event_update(self, event_type: str, event_data: dict[str, Any]) -> None:
        """Handle event update from WebSocket."""
        event_id = event_data.get("id")
        if not event_id:
            return

        _LOGGER.debug("Handling event update for %s: %s", event_type, event_id)

        # Store event data
        if event_type not in self.data["protect"]["events"]:
            self.data["protect"]["events"][event_type] = {}

        self.data["protect"]["events"][event_type][event_id] = event_data

        # Update device last event time if applicable
        device_id = event_data.get("device")
        if device_id:
            # Check if this is a camera motion event
            if event_type == "motion" and device_id in self.data["protect"]["cameras"]:
                # Store both start and end times for motion events
                self.data["protect"]["cameras"][device_id]["lastMotionStart"] = (
                    event_data.get("start")
                )
                self.data["protect"]["cameras"][device_id]["lastMotionEnd"] = (
                    event_data.get("end")
                )
                # Clear smart detect types for basic motion
                self.data["protect"]["cameras"][device_id]["lastSmartDetectTypes"] = []
                _LOGGER.info(
                    "Motion event for camera %s: start=%s, end=%s",
                    device_id,
                    event_data.get("start"),
                    event_data.get("end"),
                )

            # Check if this is a light motion event
            elif event_type == "motion" and device_id in self.data["protect"]["lights"]:
                self.data["protect"]["lights"][device_id]["lastMotionStart"] = (
                    event_data.get("start")
                )
                self.data["protect"]["lights"][device_id]["lastMotionEnd"] = (
                    event_data.get("end")
                )

            # Check if this is a smart detection event (per API documentation)
            elif (
                event_type == "smartDetectZone"
                and device_id in self.data["protect"]["cameras"]
            ):
                # Extract smart detection types from event data
                smart_detect_types = event_data.get("smartDetectTypes", [])
                event_start = event_data.get("start", 0)
                event_end = event_data.get("end")

                # Update camera with smart detection information
                self.data["protect"]["cameras"][device_id]["lastMotionStart"] = (
                    event_start
                )
                self.data["protect"]["cameras"][device_id]["lastMotionEnd"] = event_end
                self.data["protect"]["cameras"][device_id]["lastSmartDetectTypes"] = (
                    smart_detect_types
                )

                _LOGGER.info(
                    "Smart detection event for camera %s: %s (start=%s, end=%s)",
                    device_id,
                    smart_detect_types,
                    event_start,
                    event_end,
                )

            # Check if this is a doorbell ring event
            elif event_type == "ring" and device_id in self.data["protect"]["cameras"]:
                self.data["protect"]["cameras"][device_id]["lastRingStart"] = (
                    event_data.get("start")
                )
                self.data["protect"]["cameras"][device_id]["lastRingEnd"] = (
                    event_data.get("end")
                )
                _LOGGER.info(
                    "Doorbell ring for camera %s: start=%s, end=%s",
                    device_id,
                    event_data.get("start"),
                    event_data.get("end"),
                )

        self.async_update_listeners()

    def get_device(self, site_id: str, device_id: str) -> dict[str, Any] | None:
        """Get device data by site ID and device ID."""
        return self.data.get("devices", {}).get(site_id, {}).get(device_id)

    def get_device_stats(self, site_id: str, device_id: str) -> dict[str, Any] | None:
        """Get device statistics by site ID and device ID."""
        return self.data.get("stats", {}).get(site_id, {}).get(device_id)

    async def _process_device(
        self, site_id: str, device: dict[str, Any], clients: list[dict[str, Any]]
    ) -> tuple[str, dict[str, Any], dict[str, Any]]:
        """Process a single device and its stats."""
        device_id = device["id"]
        device_name = device.get("name", device_id)

        try:
            # Get device info and stats in parallel
            info_task = self.api.async_get_device_info(site_id, device_id)
            stats_task = self.api.async_get_device_stats(site_id, device_id)
            device_info, stats = await asyncio.gather(info_task, stats_task)

            # Update device info
            device.update(device_info)

            # Add client data and device info to stats
            if stats is not None:
                stats["clients"] = [
                    c for c in clients if c.get("uplinkDeviceId") == device_id
                ]
                stats["id"] = device_id
            else:
                stats = {}

            return device_id, device, stats

        except Exception as err:
            _LOGGER.exception(
                "Error processing device %s (%s): %s", device_name, device_id, err
            )
            return device_id, device, {}

    async def _process_site(
        self, site_id: str
    ) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]] | None:
        """Process a single site's devices and clients."""
        try:
            # Get devices and clients in parallel
            devices_task = self.api.async_get_devices(site_id)
            clients_task = self.api.async_get_clients(site_id)
            devices, clients = await asyncio.gather(devices_task, clients_task)

            # Process devices in parallel
            tasks = [
                self._process_device(site_id, device, clients) for device in devices
            ]
            results = await asyncio.gather(*tasks)

            # Organize results
            devices_dict = {}
            stats_dict = {}
            for device_id, device, stats in results:
                devices_dict[device_id] = device
                stats_dict[device_id] = stats

            clients_dict = {client["id"]: client for client in clients}

            return devices_dict, stats_dict, clients_dict

        except Exception as err:
            _LOGGER.error("Error processing site %s: %s", site_id, err, exc_info=True)
            return None

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API."""
        try:
            # Get all sites first
            sites = await self.api.async_get_sites()
            self.data["sites"] = {site["id"]: site for site in sites}

            # Process all sites in parallel
            tasks = [self._process_site(site_id) for site_id in self.data["sites"]]
            results = await asyncio.gather(*tasks)

            # Update data structure with results
            for site_id, result in zip(self.data["sites"], results, strict=False):
                if result is not None:
                    devices_dict, stats_dict, clients_dict = result
                    self.data["devices"][site_id] = devices_dict
                    self.data["stats"][site_id] = stats_dict
                    self.data["clients"][site_id] = clients_dict

                    _LOGGER.debug(
                        "Successfully processed site %s with %d devices and %d clients",
                        site_id,
                        len(devices_dict),
                        len(clients_dict),
                    )

            # Fetch Unifi Protect data if API is available
            if self.protect_api:
                try:
                    _LOGGER.debug("Fetching Unifi Protect data")

                    # Fetch cameras
                    _LOGGER.debug("Fetching Unifi Protect cameras")
                    cameras = await self.protect_api.async_get_cameras()
                    for camera in cameras:
                        camera_id = camera.get("id")
                        if camera_id:
                            # Extract smartDetectTypes from featureFlags for easier access
                            # (per API documentation, smartDetectTypes is nested in featureFlags)
                            feature_flags = camera.get("featureFlags", {})
                            camera["smartDetectTypes"] = feature_flags.get(
                                "smartDetectTypes", []
                            )

                            # Initialize last detection fields
                            camera["lastSmartDetectTypes"] = []
                            camera["lastMotion"] = 0
                            camera["lastRing"] = 0

                            self.data["protect"]["cameras"][camera_id] = camera

                            _LOGGER.debug(
                                "Camera %s supports smart detection types: %s",
                                camera.get("name", camera_id),
                                camera["smartDetectTypes"],
                            )

                    # Fetch lights
                    _LOGGER.debug("Fetching Unifi Protect lights")
                    lights = await self.protect_api.async_get_lights()
                    for light in lights:
                        light_id = light.get("id")
                        if light_id:
                            self.data["protect"]["lights"][light_id] = light

                    # Fetch sensors
                    _LOGGER.debug("Fetching Unifi Protect sensors")
                    try:
                        sensors = await self.protect_api.async_get_sensors()
                        for sensor in sensors:
                            sensor_id = sensor.get("id")
                            if sensor_id:
                                self.data["protect"]["sensors"][sensor_id] = sensor
                        _LOGGER.debug("Successfully fetched %d sensors", len(sensors))
                    except Exception as err:
                        _LOGGER.warning("Error fetching sensors: %s", err)

                    # Fetch NVRs
                    _LOGGER.debug("Fetching Unifi Protect NVRs")
                    try:
                        nvr = await self.protect_api.async_get_nvrs()
                        # The API returns a single NVR object (dict), not a list
                        if isinstance(nvr, dict):
                            nvr_id = nvr.get("id")
                            if nvr_id:
                                self.data["protect"]["nvrs"][nvr_id] = nvr
                                _LOGGER.debug("Successfully fetched NVR: %s", nvr_id)
                        else:
                            _LOGGER.debug(
                                "Unexpected NVR API response type: %s", type(nvr)
                            )
                    except Exception as err:
                        _LOGGER.debug("Error fetching NVRs: %s", err)

                    # Fetch chimes
                    _LOGGER.debug("Fetching Unifi Protect chimes")
                    try:
                        chimes = await self.protect_api.async_get_chimes()
                        for chime in chimes:
                            chime_id = chime.get("id")
                            if chime_id:
                                self.data["protect"]["chimes"][chime_id] = chime
                        _LOGGER.debug("Successfully fetched %d chimes", len(chimes))
                    except Exception as err:
                        _LOGGER.warning("Error fetching chimes: %s", err)

                    # Fetch viewers
                    _LOGGER.debug("Fetching Unifi Protect viewers")
                    try:
                        viewers = await self.protect_api.async_get_viewers()
                        for viewer in viewers:
                            viewer_id = viewer.get("id")
                            if viewer_id:
                                self.data["protect"]["viewers"][viewer_id] = viewer
                        _LOGGER.debug("Successfully fetched %d viewers", len(viewers))
                    except Exception as err:
                        _LOGGER.warning("Error fetching viewers: %s", err)

                    # Fetch liveviews
                    _LOGGER.debug("Fetching Unifi Protect liveviews")
                    try:
                        liveviews = await self.protect_api.async_get_liveviews()
                        for liveview in liveviews:
                            liveview_id = liveview.get("id")
                            if liveview_id:
                                self.data["protect"]["liveviews"][liveview_id] = (
                                    liveview
                                )
                        _LOGGER.debug(
                            "Successfully fetched %d liveviews", len(liveviews)
                        )
                    except Exception as err:
                        _LOGGER.warning("Error fetching liveviews: %s", err)

                    # Start WebSocket connections if not already started
                    await self.protect_api.async_start_websocket()

                    _LOGGER.debug(
                        "Successfully fetched Unifi Protect data: %d cameras, %d lights, %d sensors, %d NVRs, %d chimes, %d viewers, %d liveviews",
                        len(self.data["protect"]["cameras"]),
                        len(self.data["protect"]["lights"]),
                        len(self.data["protect"]["sensors"]),
                        len(self.data["protect"]["nvrs"]),
                        len(self.data["protect"]["chimes"]),
                        len(self.data["protect"]["viewers"]),
                        len(self.data["protect"]["liveviews"]),
                    )

                except Exception as err:
                    _LOGGER.exception("Error fetching Unifi Protect data: %s", err)

            self._available = True
            self.data["last_update"] = datetime.now()
            return self.data

        except UnifiInsightsAuthError as err:
            self._available = False
            raise ConfigEntryAuthFailed from err
        except UnifiInsightsConnectionError as err:
            self._available = False
            msg = f"Error communicating with API: {err}"
            raise UpdateFailed(msg) from err
        except Exception as err:
            self._available = False
            _LOGGER.error("Unexpected error updating data: %s", err, exc_info=True)
            msg = f"Error updating data: {err}"
            raise UpdateFailed(msg) from err

    @property
    def available(self) -> bool:
        """Return coordinator availability."""
        return self._available
