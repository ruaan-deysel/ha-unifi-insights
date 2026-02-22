"""Device coordinator for UniFi Insights - handles fast-changing device data."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from unifi_official_api import (
    UniFiAuthenticationError,
    UniFiConnectionError,
    UniFiResponseError,
    UniFiTimeoutError,
)

from custom_components.unifi_insights.const import DOMAIN, SCAN_INTERVAL_DEVICE

from .base import UnifiBaseCoordinator

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from unifi_official_api.network import UniFiNetworkClient
    from unifi_official_api.protect import UniFiProtectClient

    from .config import UnifiConfigCoordinator

_LOGGER = logging.getLogger(__name__)


# --- Legacy PoE port table fetch helper ---
async def _fetch_legacy_port_table(
    hass: Any,
    host: str,
    api_key: str,
    verify_ssl: bool,
    site: str,
    device_mac: str,
) -> dict[str, Any] | None:
    """Fetch legacy controller port_table for a device (includes poe_power per port).

    Uses UniFi OS local path:
      /proxy/network/api/s/<site>/stat/device/<mac>

    Returns the legacy device dict (data[0]) on success, or None on failure.
    """
    base = host.rstrip("/")
    url = f"{base}/proxy/network/api/s/{site}/stat/device/{device_mac}"

    session = async_get_clientsession(hass)
    headers = {
        "X-API-KEY": api_key,
        "Accept": "application/json",
    }

    ssl = None if verify_ssl else False

    async with session.get(url, headers=headers, ssl=ssl) as resp:
        if resp.status >= 400:
            return None
        payload = await resp.json(content_type=None)

    data = payload.get("data") if isinstance(payload, dict) else None
    if not (isinstance(data, list) and data and isinstance(data[0], dict)):
        return None

    return data[0]


class UnifiDeviceCoordinator(UnifiBaseCoordinator):
    """
    Coordinator for fast-changing device data (30 second updates).

    Handles:
    - Device online status
    - Device statistics (CPU, memory, uptime)
    - Client connections
    - Port statistics
    """

    def __init__(
        self,
        hass: HomeAssistant,
        network_client: UniFiNetworkClient,
        protect_client: UniFiProtectClient | None,
        entry: ConfigEntry,
        config_coordinator: UnifiConfigCoordinator,
    ) -> None:
        """Initialize the device coordinator."""
        super().__init__(
            hass=hass,
            network_client=network_client,
            protect_client=protect_client,
            entry=entry,
            name="device",
            update_interval=SCAN_INTERVAL_DEVICE,
        )
        self.config_coordinator = config_coordinator
        # Track previous device IDs for stale device cleanup (Gold requirement)
        self._previous_network_device_ids: set[str] = set()
        self.data: dict[str, Any] = {
            "devices": {},
            "clients": {},
            "stats": {},
            "vouchers": {},
            "last_update": None,
        }

    async def _process_device(
        self, site_id: str, device_dict: dict[str, Any], clients: list[dict[str, Any]]
    ) -> tuple[str, dict[str, Any], dict[str, Any]]:
        """Process a single device and its stats."""
        device_id = device_dict.get("id")
        device_name = device_dict.get("name", device_id)

        try:
            # Get device statistics
            stats_model = await self.network_client.devices.get_statistics(
                site_id, device_id=device_id
            )
            stats = self._model_to_dict(stats_model) if stats_model else {}

            # Legacy port_table (MAC-keyed) provides per-port PoE power and counters
            try:
                host = self.config_entry.data.get("host")
                api_key = self.config_entry.data.get("api_key")
                verify_ssl = bool(self.config_entry.data.get("verify_ssl", False))
                device_mac = (
                    device_dict.get("mac")
                    or device_dict.get("macAddress")
                    or device_dict.get("mac_address")
                )

                legacy_site = site_id
                try:
                    get_site = getattr(self.config_coordinator, "get_site", None)
                    if callable(get_site):
                        site_obj = get_site(site_id)
                        if isinstance(site_obj, dict):
                            legacy_site = (
                                site_obj.get("internalReference")
                                or site_obj.get("internal_reference")
                                or legacy_site
                            )
                except Exception:  # noqa: BLE001
                    pass

                if host and api_key and device_mac:
                    legacy_dev = await _fetch_legacy_port_table(
                        self.hass,
                        host,
                        api_key,
                        verify_ssl,
                        legacy_site,
                        device_mac,
                    )

                    if isinstance(legacy_dev, dict):
                        port_table = legacy_dev.get("port_table")
                        if not isinstance(port_table, list):
                            port_table = []
                        poe_ports: dict[int, float] = {}
                        port_bytes: dict[int, dict[str, int]] = {}
                        any_poe_capable = False

                        for pt in port_table:
                            port_idx = pt.get("port_idx")
                            if not isinstance(port_idx, int):
                                continue

                            # Determine device PoE capability from PoE metadata values
                            poe_enable = pt.get("poe_enable")
                            poe_mode = pt.get("poe_mode")
                            poe_maxw = pt.get("poe_maxw")
                            poe_voltage = pt.get("poe_voltage")
                            poe_current = pt.get("poe_current")
                            poe_good = pt.get("poe_good")

                            def _to_float(v):
                                try:
                                    return float(v)
                                except (TypeError, ValueError):
                                    return None

                            maxw_f = _to_float(poe_maxw)
                            volt_f = _to_float(poe_voltage)
                            curr_f = _to_float(poe_current)

                            # Treat device as PoE-capable if any port reports non-trivial PoE capability values
                            device_poe_hint = False
                            if maxw_f is not None and maxw_f > 0:
                                device_poe_hint = True
                            elif isinstance(poe_mode, str) and poe_mode.lower() not in ("", "off", "disabled", "none"):
                                device_poe_hint = True
                            elif poe_good is True:
                                device_poe_hint = True
                            elif volt_f is not None and volt_f > 0:
                                device_poe_hint = True
                            elif curr_f is not None and curr_f > 0:
                                device_poe_hint = True
                            elif poe_enable in (True, 1, "1", "on", "auto"):
                                device_poe_hint = True

                            if device_poe_hint:
                                any_poe_capable = True

                            # Port is PoE-capable if PoE metadata is present on a PoE-capable device
                            poe_port_declared = any(
                                k in pt
                                for k in (
                                    "poe_enable",
                                    "poe_mode",
                                    "poe_class",
                                    "poe_voltage",
                                    "poe_current",
                                    "poe_good",
                                    "poe_maxw",
                                )
                            )
                            poe_capable = bool(any_poe_capable and poe_port_declared)

                            # Per-port byte counters
                            rx_raw = pt.get("rx_bytes")
                            tx_raw = pt.get("tx_bytes")
                            try:
                                rx_b = int(rx_raw) if rx_raw is not None else None
                            except (TypeError, ValueError):
                                rx_b = None
                            try:
                                tx_b = int(tx_raw) if tx_raw is not None else None
                            except (TypeError, ValueError):
                                tx_b = None

                            if rx_b is not None or tx_b is not None:
                                port_bytes[port_idx] = {
                                    "rx_bytes": rx_b if rx_b is not None else 0,
                                    "tx_bytes": tx_b if tx_b is not None else 0,
                                }

                            # Per-port PoE watts (string in legacy payload)
                            if poe_capable:
                                poe_power_raw = pt.get("poe_power")
                                try:
                                    poe_w = float(poe_power_raw) if poe_power_raw is not None else 0.0
                                except (TypeError, ValueError):
                                    poe_w = 0.0

                                poe_ports[port_idx] = poe_w

                        if port_bytes:
                            stats["port_bytes"] = port_bytes

                        if any_poe_capable:
                            if poe_ports:
                                stats["poe_ports"] = poe_ports

                            # Total PoE power (W): legacy-reported total preferred, else sum of ports
                            total_used = (
                                legacy_dev.get("total_used_power")
                                or legacy_dev.get("total_poe_power")
                                or legacy_dev.get("poe_total_power")
                            )
                            total_w: float | None = None
                            try:
                                if total_used is not None:
                                    total_w = float(total_used)
                            except (TypeError, ValueError):
                                total_w = None

                            if total_w is None and poe_ports:
                                total_w = float(sum(poe_ports.values()))

                            if total_w is not None:
                                stats["poe_total_w"] = total_w
            except Exception as err:  # noqa: BLE001
                _LOGGER.debug(
                    "Legacy PoE wattage fetch failed for %s: %s",
                    device_mac or device_id,
                    err,
                )

            # Add client data to stats
            if stats:
                # Use camelCase uplinkDeviceId as returned by model_dump(by_alias=True)
                stats["clients"] = [
                    c
                    for c in clients
                    if (c.get("uplinkDeviceId") or c.get("uplink_device_id"))
                    == device_id
                ]
                stats["id"] = device_id

            return device_id, device_dict, stats  # noqa: TRY300

        except Exception as err:  # noqa: BLE001
            _LOGGER.debug(
                "Error getting stats for device %s (%s): %s",
                device_name,
                device_id,
                err,
            )
            return device_id, device_dict, {}

    async def _process_site(
        self, site_id: str
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]] | None:
        """Process a single site's devices and clients."""
        try:
            # Get devices and clients in parallel using new API
            devices_task = self.network_client.devices.get_all(site_id)
            clients_task = self.network_client.clients.get_all(site_id)
            devices_models, clients_models = await asyncio.gather(
                devices_task, clients_task
            )

            # Convert model objects to dictionaries
            devices = [self._model_to_dict(d) for d in devices_models]
            clients = [self._model_to_dict(c) for c in clients_models]

            _LOGGER.debug(
                "Device coordinator: Site %s - Found %d devices and %d clients",
                site_id,
                len(devices),
                len(clients),
            )

            # Log sample device keys for debugging data format issues
            if devices:
                sample_device = devices[0]
                _LOGGER.debug(
                    "Device coordinator: Sample device keys for site %s: %s",
                    site_id,
                    list(sample_device.keys()),
                )

            # Process devices in parallel (get stats)
            tasks = [
                self._process_device(site_id, device, clients) for device in devices
            ]
            results = await asyncio.gather(*tasks)

            # Organize results
            devices_dict = {}
            stats_dict = {}
            for device_id, device, stats in results:
                if device_id:
                    devices_dict[device_id] = device
                    stats_dict[device_id] = stats

            clients_dict = {
                client.get("id"): client for client in clients if client.get("id")
            }

            return devices_dict, stats_dict, clients_dict  # noqa: TRY300

        except Exception:
            _LOGGER.exception("Device coordinator: Error processing site %s", site_id)
            return None

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch device data from API."""
        try:
            # Get site IDs from config coordinator
            site_ids = self.config_coordinator.get_site_ids()

            if not site_ids:
                _LOGGER.warning(
                    "Device coordinator: No sites available from config coordinator"
                )
                return self.data

            _LOGGER.debug(
                "Device coordinator: Processing %d sites",
                len(site_ids),
            )

            # Process all sites in parallel
            tasks = [self._process_site(site_id) for site_id in site_ids]
            results = await asyncio.gather(*tasks)

            # Update data structure with results
            for site_id, result in zip(site_ids, results, strict=False):
                if result is not None:
                    devices_dict, stats_dict, clients_dict = result
                    self.data["devices"][site_id] = devices_dict
                    self.data["stats"][site_id] = stats_dict
                    self.data["clients"][site_id] = clients_dict

                    _LOGGER.debug(
                        "Device coordinator: Processed site %s - "
                        "%d devices, %d clients",
                        site_id,
                        len(devices_dict),
                        len(clients_dict),
                    )

            self._available = True
            self.data["last_update"] = datetime.now(tz=UTC)

            # Clean up stale devices (Gold requirement)
            self._cleanup_stale_devices()

            _LOGGER.debug(
                "Device coordinator: Update complete - %d sites processed",
                len(site_ids),
            )

            return self.data  # noqa: TRY300

        except UniFiAuthenticationError as err:
            self._handle_auth_error(err)
        except UniFiConnectionError as err:
            self._handle_connection_error(err)
        except UniFiTimeoutError as err:
            self._handle_timeout_error(err)
        except UniFiResponseError as err:
            self._handle_response_error(err)
        except Exception as err:  # noqa: BLE001
            self._handle_generic_error(err)

        # Should never reach here due to raises above
        return self.data  # pragma: no cover

    def _cleanup_stale_devices(self) -> None:
        """Remove stale network devices from the device registry (Gold requirement)."""
        device_registry = dr.async_get(self.hass)

        # Collect current network device IDs
        current_network_device_ids: set[str] = set()
        for site_id, devices in self.data.get("devices", {}).items():
            for device_id in devices:
                current_network_device_ids.add(f"{site_id}_{device_id}")

        # Find and remove stale network devices
        stale_network_ids = (
            self._previous_network_device_ids - current_network_device_ids
        )
        for device_identifier in stale_network_ids:
            device = device_registry.async_get_device(
                identifiers={(DOMAIN, device_identifier)}
            )
            if device:
                _LOGGER.info(
                    "Device coordinator: Removing stale network device: %s",
                    device_identifier,
                )
                device_registry.async_update_device(
                    device_id=device.id,
                    remove_config_entry_id=self.config_entry.entry_id,
                )

        self._previous_network_device_ids = current_network_device_ids

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

    def get_clients(self, site_id: str) -> dict[str, Any]:
        """Get all clients for a site."""
        return self.data.get("clients", {}).get(site_id, {})
