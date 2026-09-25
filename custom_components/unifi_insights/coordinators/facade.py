"""Facade coordinator providing backward-compatible unified data view."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

    from custom_components.unifi_insights.api.innerspace import UniFiInnerSpaceClient
    from custom_components.unifi_insights.api.network import UniFiNetworkClient
    from custom_components.unifi_insights.api.protect import UniFiProtectClient

    from .config import UnifiConfigCoordinator
    from .device import UnifiDeviceCoordinator
    from .innerspace import UnifiInsightsInnerSpaceCoordinator
    from .protect import UnifiProtectCoordinator
    from .site_manager import UnifiInsightsSiteManagerCoordinator

from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from custom_components.unifi_insights.const import CONF_CONSOLE_ID, DOMAIN
from custom_components.unifi_insights.data_transforms import (
    correlate_innerspace_devices,
    normalize_innerspace_snapshot,
)

_LOGGER = logging.getLogger(__name__)


class UnifiFacadeCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """
    Facade coordinator providing unified data view for backward compatibility.

    This coordinator aggregates data from the specialized coordinators
    (config, device, protect) and presents a unified interface that matches
    the original single-coordinator structure. This allows existing entity
    classes to work without modifications.

    Data structure (matches original coordinator):
    - sites: from config_coordinator
    - devices: from device_coordinator
    - clients: from device_coordinator
    - stats: from device_coordinator
    - wifi: from config_coordinator
    - protect: from protect_coordinator (cameras, lights, sensors, etc.)
    - innerspace: from innerspace_coordinator (floor_plans, access_points,
      switches, inventory)
    - last_update: combined from all coordinators
    """

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        network_client: UniFiNetworkClient,
        protect_client: UniFiProtectClient | None,
        entry: ConfigEntry,
        config_coordinator: UnifiConfigCoordinator,
        device_coordinator: UnifiDeviceCoordinator,
        protect_coordinator: UnifiProtectCoordinator | None,
        *,
        innerspace_client: UniFiInnerSpaceClient | None = None,
        innerspace_coordinator: UnifiInsightsInnerSpaceCoordinator | None = None,
        site_manager_coordinator: UnifiInsightsSiteManagerCoordinator | None = None,
    ) -> None:
        """Initialize the facade coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN}_facade",
            # Facade doesn't poll - it aggregates from other coordinators
            update_interval=None,
        )
        self.network_client = network_client
        self.protect_client = protect_client
        self.innerspace_client = innerspace_client
        self._config_coordinator = config_coordinator
        self._device_coordinator = device_coordinator
        self._protect_coordinator = protect_coordinator
        self._innerspace_coordinator = innerspace_coordinator
        self._site_manager_coordinator = site_manager_coordinator
        self._site_manager_host_id = entry.data.get(CONF_CONSOLE_ID)

        # Remove-callbacks returned by async_add_listener() below, released
        # in async_shutdown() so this facade's forwarding listener doesn't
        # outlive it on the sub-coordinators (see _setup_listeners).
        self._sub_coordinator_unsubs: list[Callable[[], None]] = []
        self._innerspace_corr_key: tuple[Any, ...] | None = None
        self._cached_innerspace_data: dict[str, Any] | None = None

        # Register listeners to update when any coordinator updates
        self._setup_listeners()

        # Aggregate the sub-coordinators' current data immediately so that
        # self.data is never None for entities created right after init.
        self._aggregate_data()

    def _setup_listeners(self) -> None:
        """Set up listeners to aggregate data when coordinators update."""
        # async_add_listener() returns a remove-callback; it must be kept
        # and invoked on shutdown (see async_shutdown) or this facade's
        # listener registration outlives the facade itself - each
        # config-entry reload builds a fresh facade + fresh sub-coordinators,
        # but without releasing this, the outgoing facade stays reachable
        # (and un-collectable) via the very listener slot it never freed.
        self._sub_coordinator_unsubs.append(
            self._device_coordinator.async_add_listener(self._handle_coordinator_update)
        )
        self._sub_coordinator_unsubs.append(
            self._config_coordinator.async_add_listener(self._handle_coordinator_update)
        )
        if self._protect_coordinator:
            self._sub_coordinator_unsubs.append(
                self._protect_coordinator.async_add_listener(
                    self._handle_coordinator_update
                )
            )
        if self._innerspace_coordinator:
            self._sub_coordinator_unsubs.append(
                self._innerspace_coordinator.async_add_listener(
                    self._handle_coordinator_update
                )
            )
        if self._site_manager_coordinator:
            self._sub_coordinator_unsubs.append(
                self._site_manager_coordinator.async_add_listener(
                    self._handle_coordinator_update
                )
            )

    async def async_shutdown(self) -> None:
        """
        Shut down the facade and release its listeners on the sub-coordinators.

        ``DataUpdateCoordinator.__init__`` auto-registers
        ``config_entry.async_on_unload(self.async_shutdown)`` for every
        coordinator constructed with a ``config_entry`` (all four of ours
        qualify), so this already runs automatically on config-entry
        unload/reload - no extra wiring is needed in
        ``__init__.py::async_unload_entry``. That auto-registration is also
        why a leaked facade doesn't keep the sub-coordinators *polling*:
        each sub-coordinator's own auto-registered ``async_shutdown()``
        cancels its scheduled refresh and sets ``_shutdown_requested``,
        which ``_async_refresh()`` checks before it would ever fetch or
        reschedule. What that auto-registration does *not* do is undo the
        side effect *this* facade caused on *other* objects: the base
        ``async_shutdown()`` never touches ``_listeners``, so the
        remove-callbacks from ``_setup_listeners`` must be released here
        explicitly, or the sub-coordinators keep a dead reference back to
        this facade indefinitely.
        """
        for unsub in self._sub_coordinator_unsubs:
            unsub()
        self._sub_coordinator_unsubs.clear()
        await super().async_shutdown()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle update from any coordinator by refreshing aggregated data."""
        self._aggregate_data()
        self.async_update_listeners()

    @staticmethod
    def _build_innerspace_corr_key(
        raw_innerspace: dict[str, Any],
        devices: Any,
        protect_data: Any,
    ) -> tuple[Any, ...]:
        """Build a lightweight cache key for InnerSpace MAC correlation."""
        net_pairs: list[tuple[str, str, Any]] = []
        if isinstance(devices, dict):
            for site_id, site_devs in sorted(devices.items()):
                if isinstance(site_devs, dict):
                    for dev_id, dev in sorted(site_devs.items()):
                        if isinstance(dev, dict):
                            net_pairs.append(
                                (
                                    str(site_id),
                                    str(dev_id),
                                    dev.get("macAddress")
                                    or dev.get("mac_address")
                                    or dev.get("mac"),
                                )
                            )
        prot_pairs: list[tuple[str, str, Any]] = []
        if isinstance(protect_data, dict):
            for col_name in (
                "cameras",
                "lights",
                "sensors",
                "nvrs",
                "viewers",
                "chimes",
                "doorlocks",
                "viewports",
            ):
                col = protect_data.get(col_name)
                if isinstance(col, dict):
                    for dev_id, dev in sorted(col.items()):
                        if isinstance(dev, dict):
                            prot_pairs.append(
                                (
                                    col_name,
                                    str(dev_id),
                                    dev.get("mac")
                                    or dev.get("macAddress")
                                    or dev.get("mac_address"),
                                )
                            )
        return (id(raw_innerspace), tuple(net_pairs), tuple(prot_pairs))

    def _aggregate_data(self) -> None:
        """Aggregate data from all coordinators into unified structure."""
        devices = self._device_coordinator.data.get("devices", {})
        protect_data = (
            self._protect_coordinator.data
            if self._protect_coordinator
            else {
                "cameras": {},
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "viewers": {},
                "chimes": {},
                "doorlocks": {},
                "viewports": {},
                "liveviews": {},
                "protect_info": {},
                "events": {},
            }
        )
        if self._innerspace_coordinator and self._innerspace_coordinator.data:
            raw_innerspace = self._innerspace_coordinator.data
            corr_key = self._build_innerspace_corr_key(
                raw_innerspace, devices, protect_data
            )
            if (
                self._cached_innerspace_data is not None
                and self._innerspace_corr_key == corr_key
            ):
                innerspace_data = self._cached_innerspace_data
            else:
                devices_map: dict[str, dict[str, Any]] = {}
                access_points_map = {
                    str(rec_id): dict(rec)
                    for rec_id, rec in raw_innerspace.get("access_points", {}).items()
                    if isinstance(rec, dict)
                }
                switches_map = {
                    str(rec_id): dict(rec)
                    for rec_id, rec in raw_innerspace.get("switches", {}).items()
                    if isinstance(rec, dict)
                }
                inventory_map = {
                    str(rec_id): dict(rec)
                    for rec_id, rec in raw_innerspace.get("inventory", {}).items()
                    if isinstance(rec, dict)
                }
                for section_map in (access_points_map, switches_map, inventory_map):
                    devices_map.update(section_map)
                innerspace_data = {
                    "project": raw_innerspace.get("project"),
                    "floor_plans": dict(raw_innerspace.get("floor_plans", {})),
                    "access_points": access_points_map,
                    "switches": switches_map,
                    "inventory": inventory_map,
                    "placed_devices": {**access_points_map, **switches_map},
                    "devices": devices_map,
                    "last_update": raw_innerspace.get("last_update"),
                }
                innerspace_data["correlations"] = correlate_innerspace_devices(
                    innerspace_data,
                    network_devices=devices if isinstance(devices, dict) else None,
                    protect_devices=protect_data
                    if isinstance(protect_data, dict)
                    else None,
                )
                self._innerspace_corr_key = corr_key
                self._cached_innerspace_data = innerspace_data
        else:
            self._innerspace_corr_key = None
            self._cached_innerspace_data = None
            innerspace_data = {**normalize_innerspace_snapshot(), "last_update": None}

        self.data = {
            # From config coordinator
            "sites": self._config_coordinator.data.get("sites", {}),
            "wifi": self._config_coordinator.data.get("wifi", {}),
            "firewall_rules": self._config_coordinator.data.get("firewall_rules", {}),
            "policy_based_routes": self._config_coordinator.data.get(
                "policy_based_routes", {}
            ),
            "vpn_clients": self._config_coordinator.data.get("vpn_clients", {}),
            "site_vpns": self._config_coordinator.data.get("site_vpns", {}),
            "network_info": self._config_coordinator.data.get("network_info", {}),
            "client_links": self._config_coordinator.data.get("client_links", {}),
            # From device coordinator
            "devices": devices,
            "clients": self._device_coordinator.data.get("clients", {}),
            "stats": self._device_coordinator.data.get("stats", {}),
            "vouchers": self._device_coordinator.data.get("vouchers", {}),
            "vpn_connections": self._device_coordinator.data.get("vpn_connections", {}),
            # From protect coordinator
            "protect": protect_data,
            # From innerspace coordinator
            "innerspace": innerspace_data,
            # Combined timestamp
            "last_update": datetime.now(tz=UTC),
        }
        if self._site_manager_coordinator:
            account_data = self._site_manager_coordinator.data
            self.data["site_manager"] = {
                **account_data,
                "selected_host_id": (
                    self._site_manager_host_id
                    if self._site_manager_host_id in account_data["hosts"]
                    else None
                ),
            }

    def get_site(self, site_id: str) -> dict[str, Any] | None:
        """Get site data by site ID (delegates to config coordinator)."""
        return self._config_coordinator.get_site(site_id)

    def get_device(self, site_id: str, device_id: str) -> dict[str, Any] | None:
        """Get device data by site ID and device ID."""
        devices = self.data.get("devices", {}).get(site_id, {})
        result = devices.get(device_id)
        return result if isinstance(result, dict) else None

    def get_device_stats(self, site_id: str, device_id: str) -> dict[str, Any] | None:
        """Get device statistics by site ID and device ID."""
        stats = self.data.get("stats", {}).get(site_id, {})
        result = stats.get(device_id)
        return result if isinstance(result, dict) else None

    @property
    def available(self) -> bool:
        """Return combined availability from all sub-coordinators."""
        return (
            self.device_available
            and self.config_available
            and self.protect_available
            and self.innerspace_available
        )

    @property
    def device_available(self) -> bool:
        """Return True if the device coordinator is available."""
        return self._device_coordinator.last_update_success

    @property
    def config_available(self) -> bool:
        """Return True if the config coordinator is available."""
        return self._config_coordinator.last_update_success

    def wifi_available(self, site_id: str) -> bool:
        """Return True if a site's WiFi networks were fetched on the last refresh."""
        return self._config_coordinator.wifi_available(site_id)

    def firewall_available(self, site_id: str) -> bool:
        """Return True if a site's firewall rules were fetched on the last refresh."""
        return self._config_coordinator.firewall_available(site_id)

    @property
    def protect_available(self) -> bool:
        """Return True if the protect coordinator is available or not configured."""
        if self._protect_coordinator is None:
            return True
        return self._protect_coordinator.last_update_success

    @property
    def innerspace_available(self) -> bool:
        """Return True if the InnerSpace coordinator is available or not configured."""
        if self._innerspace_coordinator is None:
            return True
        return self._innerspace_coordinator.last_update_success

    async def _async_update_data(self) -> dict[str, Any]:
        """
        Update aggregated data.

        The facade doesn't fetch data itself - it aggregates from coordinators.
        This method is called periodically and ensures data is fresh.
        """
        self._aggregate_data()
        return self.data

    async def async_request_refresh(self) -> None:
        """
        Force a genuine refresh of all underlying coordinators and notify listeners.

        Entity action handlers (see switch.py) call this right after a
        mutating API call and expect the coordinator to reflect the change
        by the time the await returns. Two deliberate departures from the
        obvious implementation make that true:

        1. Each sub-coordinator's own ``async_refresh()`` is used instead
           of its ``async_request_refresh()``. The latter goes through
           that coordinator's ``Debouncer`` - fine for coalescing
           coordinator-internal refresh triggers, but wrong here: when a
           debounce cooldown from unrelated recent activity is already
           armed, ``async_request_refresh()`` returns immediately without
           fetching anything, so aggregating right after it would silently
           serve stale data. ``async_refresh()`` always performs (and
           awaits) a real fetch. The trade-off is that this path no longer
           benefits from that debounce - acceptable because it only runs
           once per explicit, user-triggered action, not on a hot loop.
        2. The three refreshes run concurrently via ``asyncio.gather``
           rather than sequentially - three real HTTP round trips awaited
           one after another would make every action handler noticeably
           slower for no benefit, since the coordinators are independent.

        Each sub-coordinator's own refresh already calls
        ``async_update_listeners()`` when its data changes, which cascades
        into this facade's ``_handle_coordinator_update`` via the listener
        chain from ``_setup_listeners`` - re-aggregating and notifying
        this facade's listeners already in the common case. The explicit
        ``_aggregate_data()`` + ``async_update_listeners()`` below is kept
        anyway so a caller of this method is *always* notified even in the
        edge case where none of the three sub-refreshes produced a change
        (so that cascade stays silent) - the base
        ``DataUpdateCoordinator.async_request_refresh()`` this replaces
        never called ``async_update_listeners()`` at all, which was the
        second half of the original defect.
        """
        await self._async_refresh_children()

    async def _async_refresh_children(
        self,
        *,
        include_protect: bool = True,
        include_innerspace: bool = False,
    ) -> list[str]:
        """
        Refresh the sub-coordinators concurrently and report what failed.

        ``DataUpdateCoordinator.async_refresh()`` does not raise: it records
        the problem as ``last_update_success = False`` plus ``last_exception``
        and returns normally. A caller that only awaits it therefore cannot
        tell a successful refresh from a failed one, so both that recorded
        state and any exception that escaped ``gather`` are collected here and
        returned as human-readable strings, newest data aggregated either way.
        """
        targets: list[tuple[str, DataUpdateCoordinator[Any]]] = [
            ("config", self._config_coordinator),
            ("devices", self._device_coordinator),
        ]
        if include_protect and self._protect_coordinator:
            targets.append(("protect", self._protect_coordinator))
        if include_innerspace and self._innerspace_coordinator:
            targets.append(("innerspace", self._innerspace_coordinator))

        results = await asyncio.gather(
            *(coordinator.async_refresh() for _, coordinator in targets),
            return_exceptions=True,
        )

        failures: list[str] = []
        for (name, coordinator), result in zip(targets, results, strict=True):
            if isinstance(result, BaseException):
                # CancelledError is a BaseException and means this task is
                # being torn down, not that the console misbehaved.
                if isinstance(result, asyncio.CancelledError):
                    raise result
                failures.append(f"{name} coordinator: {result}")
            elif not coordinator.last_update_success:
                error = coordinator.last_exception
                failures.append(
                    f"{name} coordinator: {error}" if error else f"{name} coordinator"
                )

        # Aggregate the updated data and notify this facade's own listeners.
        self._aggregate_data()
        self.async_update_listeners()
        return failures

    async def async_refresh_or_raise(self, *, include_protect: bool = True) -> None:
        """Refresh the sub-coordinators, raising if any of them failed."""
        failures = await self._async_refresh_children(include_protect=include_protect)
        if failures:
            joined = ", ".join(failures)
            msg = f"Error refreshing UniFi Insights data: {joined}"
            raise HomeAssistantError(msg)

    def _require_protect_client(self) -> UniFiProtectClient:
        """Return the Protect client or raise a user-facing error."""
        if self.protect_client is None:
            msg = "Protect is not available for this config"
            raise HomeAssistantError(msg)
        return self.protect_client

    async def _async_execute_api_action[ActionResult](
        self,
        error_message: str,
        action: Callable[..., Awaitable[ActionResult]],
        *args: Any,
        **kwargs: Any,
    ) -> ActionResult:
        """Execute an API action and convert failures to Home Assistant errors."""
        try:
            return await action(*args, **kwargs)
        except HomeAssistantError:
            raise
        except Exception as err:
            _LOGGER.exception("%s", error_message)
            raise HomeAssistantError(error_message) from err

    async def async_restart_device(self, site_id: str, device_id: str) -> bool:
        """Restart a network device."""
        return await self._async_execute_api_action(
            f"Unable to restart device {device_id}",
            self.network_client.devices.restart,
            site_id,
            device_id,
        )

    async def async_set_outlet_state(
        self,
        site_id: str,
        device_id: str,
        outlet_index: int,
        state: bool,
        cycle_enabled: bool | None = None,
    ) -> bool:
        """Set outlet relay state and/or cycle_enabled on a PDU device."""
        site_name = self._device_coordinator.get_legacy_site_name(site_id) or "default"
        device_data = self.get_device(site_id, device_id) or {}
        target_id = device_data.get("_id") or device_id

        return await self._async_execute_api_action(
            f"Unable to set outlet {outlet_index} state on device {device_id}",
            self.network_client.devices.set_outlet_state,
            site_name,
            target_id,
            outlet_index,
            state,
            cycle_enabled=cycle_enabled,
            current_device=device_data,
        )

    async def async_set_firewall_rule_enabled(
        self,
        site_id: str,
        rule_id: str,
        *,
        enabled: bool,
    ) -> None:
        """Enable or disable a firewall rule."""
        await self._async_execute_api_action(
            f"Unable to update firewall rule {rule_id}",
            self.network_client.firewall.update_rule,
            site_id,
            rule_id,
            enabled=enabled,
        )

    def resolve_legacy_site_name(self, site_id: str) -> str:
        """
        Resolve the classic site name for a facade (integration API) site id.

        Falls back to ``"default"`` (the standard single-site name) when the
        legacy site mapping has not resolved yet.
        """
        return self._device_coordinator.get_legacy_site_name(site_id) or "default"

    async def async_set_policy_based_route_enabled(
        self,
        site_id: str,
        route_id: str,
        *,
        enabled: bool,
    ) -> None:
        """Enable or disable a policy-based route (traffic route)."""
        site_name = self.resolve_legacy_site_name(site_id)
        await self._async_execute_api_action(
            f"Unable to update policy-based route {route_id}",
            self.network_client.routes.update_route,
            site_name,
            route_id,
            enabled=enabled,
        )

    async def async_set_vpn_client_enabled(
        self,
        site_id: str,
        client_id: str,
        *,
        enabled: bool,
    ) -> None:
        """Enable or disable a VPN client configuration."""
        site_name = self.resolve_legacy_site_name(site_id)
        await self._async_execute_api_action(
            f"Unable to update VPN client {client_id}",
            self.network_client.vpn_clients.update_vpn_client,
            site_name,
            client_id,
            enabled=enabled,
        )

    async def async_update_camera(self, camera_id: str, **kwargs: Any) -> None:
        """Update a camera via the Protect cameras endpoint."""
        protect_client = self._require_protect_client()
        await self._async_execute_api_action(
            f"Unable to update camera {camera_id}",
            protect_client.cameras.update,
            camera_id,
            **kwargs,
        )

    async def async_update_camera_settings(
        self,
        camera_id: str,
        **kwargs: Any,
    ) -> None:
        """Update camera settings (alias for async_update_camera)."""
        await self.async_update_camera(camera_id, **kwargs)

    def _resolve_client_action_target(
        self, site_id: str, client_id: str
    ) -> tuple[str, str]:
        """
        Resolve the classic site name and client MAC for a client action.

        The official Integration API has no block/unblock/reconnect/forget
        operations, so these are issued against the classic ``cmd/stamgr``
        endpoint, which is scoped by the classic site name and identifies the
        client by MAC address rather than the integration client UUID.
        """
        clients = self.data.get("clients", {}).get(site_id, {})
        client_data = clients.get(client_id, {}) if isinstance(clients, dict) else {}
        mac = (
            client_data.get("macAddress")
            or client_data.get("mac_address")
            or client_data.get("mac")
        )
        if not mac:
            msg = f"Unable to determine MAC address for client {client_id}"
            raise HomeAssistantError(msg)

        # Fall back to "default" (the standard single-site name) when the
        # legacy site mapping has not been resolved yet.
        site_name = self._device_coordinator.get_legacy_site_name(site_id) or "default"
        return site_name, mac

    async def async_unblock_client(self, site_id: str, client_id: str) -> None:
        """Unblock a network client."""
        site_name, mac = self._resolve_client_action_target(site_id, client_id)
        await self._async_execute_api_action(
            f"Unable to unblock client {client_id}",
            self.network_client.clients.unblock,
            site_name,
            mac,
        )

    async def async_block_client(self, site_id: str, client_id: str) -> None:
        """Block a network client."""
        site_name, mac = self._resolve_client_action_target(site_id, client_id)
        await self._async_execute_api_action(
            f"Unable to block client {client_id}",
            self.network_client.clients.block,
            site_name,
            mac,
        )

    async def async_reconnect_client(self, site_id: str, client_id: str) -> None:
        """Reconnect a network client."""
        site_name, mac = self._resolve_client_action_target(site_id, client_id)
        await self._async_execute_api_action(
            f"Unable to reconnect client {client_id}",
            self.network_client.clients.reconnect,
            site_name,
            mac,
        )

    async def async_forget_client(self, site_id: str, client_id: str) -> None:
        """Forget/remove a network client."""
        site_name, mac = self._resolve_client_action_target(site_id, client_id)
        await self._async_execute_api_action(
            f"Unable to forget client {client_id}",
            self.network_client.clients.forget,
            site_name,
            mac,
        )

    async def async_authorize_guest(self, site_id: str, client_id: str) -> None:
        """Authorize guest access for a network client."""
        await self._async_execute_api_action(
            f"Unable to authorize guest client {client_id}",
            self.network_client.clients.authorize_guest,
            site_id,
            client_id,
        )

    async def async_unauthorize_guest(self, site_id: str, client_id: str) -> None:
        """Remove guest authorization for a network client."""
        await self._async_execute_api_action(
            f"Unable to unauthorize guest client {client_id}",
            self.network_client.clients.unauthorize_guest,
            site_id,
            client_id,
        )

    async def async_update_wifi_network(
        self,
        site_id: str,
        wifi_id: str,
        *,
        enabled: bool,
    ) -> None:
        """Enable or disable a WiFi network."""
        await self._async_execute_api_action(
            f"Unable to update WiFi network {wifi_id}",
            self.network_client.wifi.update,
            site_id,
            wifi_id,
            enabled=enabled,
        )

    async def async_play_chime(self, chime_id: str) -> None:
        """Play a chime sound."""
        protect_client = self._require_protect_client()
        await self._async_execute_api_action(
            f"Unable to play chime {chime_id}",
            protect_client.chimes.play,
            chime_id,
        )

    async def async_start_ptz_patrol(self, camera_id: str, slot: int) -> None:
        """Start PTZ patrol for a camera."""
        protect_client = self._require_protect_client()
        await self._async_execute_api_action(
            f"Unable to start PTZ patrol for camera {camera_id}",
            protect_client.cameras.ptz_patrol_start,
            camera_id,
            slot,
        )

    async def async_stop_ptz_patrol(self, camera_id: str) -> None:
        """Stop PTZ patrol for a camera."""
        protect_client = self._require_protect_client()
        await self._async_execute_api_action(
            f"Unable to stop PTZ patrol for camera {camera_id}",
            protect_client.cameras.ptz_patrol_stop,
            camera_id,
        )

    async def async_set_hdr_mode(self, camera_id: str, mode: str) -> None:
        """Set HDR mode for a camera."""
        protect_client = self._require_protect_client()
        await self._async_execute_api_action(
            f"Unable to set HDR mode for camera {camera_id}",
            protect_client.cameras.set_hdr_mode,
            camera_id,
            mode,
        )

    async def async_set_video_mode(self, camera_id: str, mode: str) -> None:
        """Set video mode for a camera."""
        protect_client = self._require_protect_client()
        await self._async_execute_api_action(
            f"Unable to set video mode for camera {camera_id}",
            protect_client.cameras.set_video_mode,
            camera_id,
            mode,
        )

    async def async_set_recording_mode(self, camera_id: str, mode: str) -> None:
        """Set recording mode for a camera."""
        protect_client = self._require_protect_client()
        await self._async_execute_api_action(
            f"Unable to set recording mode for camera {camera_id}",
            protect_client.cameras.update,
            camera_id,
            recordingMode=mode,
        )

    async def async_set_chime_ringtone(self, chime_id: str, ringtone_id: str) -> None:
        """Set ringtone for a chime."""
        protect_client = self._require_protect_client()
        await self._async_execute_api_action(
            f"Unable to set ringtone for chime {chime_id}",
            protect_client.chimes.update,
            chime_id,
            ringtone=ringtone_id,
        )

    async def async_move_ptz_to_preset(self, camera_id: str, preset: int) -> None:
        """Move a PTZ camera to a preset."""
        protect_client = self._require_protect_client()
        await self._async_execute_api_action(
            f"Unable to move camera {camera_id} to PTZ preset {preset}",
            protect_client.cameras.ptz_goto_preset,
            camera_id,
            str(preset),
        )

    async def async_update_viewer(self, viewer_id: str, **kwargs: Any) -> None:
        """Update viewer settings."""
        protect_client = self._require_protect_client()
        await self._async_execute_api_action(
            f"Unable to update viewer {viewer_id}",
            protect_client.viewers.update,
            viewer_id,
            **kwargs,
        )

    async def async_set_microphone_volume(self, camera_id: str, volume: int) -> None:
        """Set microphone volume for a camera."""
        protect_client = self._require_protect_client()
        await self._async_execute_api_action(
            f"Unable to set microphone volume for camera {camera_id}",
            protect_client.cameras.set_microphone_volume,
            camera_id,
            volume,
        )

    async def async_set_light_brightness(self, light_id: str, level: int) -> None:
        """Set light brightness for a Protect light."""
        protect_client = self._require_protect_client()
        await self._async_execute_api_action(
            f"Unable to set brightness for light {light_id}",
            protect_client.lights.set_brightness,
            light_id,
            level,
        )

    async def async_set_light_mode(self, light_id: str, mode: str) -> None:
        """Set mode for a Protect light."""
        protect_client = self._require_protect_client()
        await self._async_execute_api_action(
            f"Unable to set mode for light {light_id}",
            protect_client.lights.update,
            light_id,
            lightMode=mode,
        )

    async def async_set_chime_volume(self, chime_id: str, volume: int) -> None:
        """Set volume for a chime."""
        protect_client = self._require_protect_client()
        await self._async_execute_api_action(
            f"Unable to set volume for chime {chime_id}",
            protect_client.chimes.set_volume,
            chime_id,
            volume,
        )

    async def async_set_chime_repeat(
        self,
        chime_id: str,
        repeat_times: int,
    ) -> None:
        """Set repeat count for a chime."""
        protect_client = self._require_protect_client()
        await self._async_execute_api_action(
            f"Unable to set repeat count for chime {chime_id}",
            protect_client.chimes.update,
            chime_id,
            repeatTimes=repeat_times,
        )

    async def async_generate_voucher(
        self,
        site_id: str,
        *,
        count: int = 1,
        time_limit_minutes: int | None = None,
        tx_rate_limit_kbps: int | None = None,
        rx_rate_limit_kbps: int | None = None,
        data_usage_limit_mbytes: int | None = None,
        name: str | None = None,
    ) -> None:
        """Generate voucher(s) for a site."""
        kwargs: dict[str, Any] = {"count": count}
        if time_limit_minutes is not None:
            kwargs["time_limit_minutes"] = time_limit_minutes
        if tx_rate_limit_kbps is not None:
            kwargs["tx_rate_limit_kbps"] = tx_rate_limit_kbps
        if rx_rate_limit_kbps is not None:
            kwargs["rx_rate_limit_kbps"] = rx_rate_limit_kbps
        if data_usage_limit_mbytes is not None:
            kwargs["data_usage_limit_mbytes"] = data_usage_limit_mbytes
        if name is not None:
            kwargs["name"] = name
        await self._async_execute_api_action(
            f"Unable to generate voucher in site {site_id}",
            self.network_client.vouchers.create,
            site_id,
            **kwargs,
        )

    async def async_delete_voucher(self, site_id: str, voucher_id: str) -> None:
        """Delete a voucher."""
        await self._async_execute_api_action(
            f"Unable to delete voucher {voucher_id}",
            self.network_client.vouchers.delete,
            site_id,
            voucher_id,
        )

    async def async_trigger_alarm(self, alarm_id: str) -> None:
        """Trigger an alarm."""
        protect_client = self._require_protect_client()
        await self._async_execute_api_action(
            f"Unable to trigger alarm {alarm_id}",
            protect_client.application.trigger_alarm_webhook,
            alarm_id,
        )

    async def async_create_liveview(
        self,
        *,
        name: str,
        layout: int,
        is_default: bool = False,
    ) -> None:
        """Create a liveview."""
        protect_client = self._require_protect_client()
        await self._async_execute_api_action(
            f"Unable to create liveview {name}",
            protect_client.liveviews.create,
            name=name,
            layout=layout,
            isDefault=is_default,
        )
