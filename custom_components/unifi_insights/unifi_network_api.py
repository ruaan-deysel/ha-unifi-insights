"""UniFi Network API Client."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from aiohttp import ClientError, ClientSession
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .const import DEFAULT_API_HOST, UNIFI_API_HEADERS

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class UnifiInsightsError(Exception):
    """Base class for UniFi Insights errors."""


class UnifiInsightsAuthError(UnifiInsightsError):
    """Authentication error."""


class UnifiInsightsConnectionError(UnifiInsightsError):
    """Connection error."""


class UnifiInsightsBackoff:
    """Class to implement exponential backoff."""

    def __init__(
        self,
        base_delay: float = 1.0,
        max_delay: float = 10.0,
        max_retries: int = 3,
    ) -> None:
        """Initialize backoff."""
        self._base_delay = base_delay
        self._max_delay = max_delay
        self._max_retries = max_retries
        self._tries = 0

    async def execute(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """Execute function with backoff."""
        while True:
            try:
                return await func(*args, **kwargs)
            except Exception as err:  # pylint: disable=broad-except
                self._tries += 1
                if self._tries >= self._max_retries:
                    raise

                delay = min(
                    self._base_delay * (2 ** (self._tries - 1)),
                    self._max_delay,
                )
                _LOGGER.debug(
                    "Retrying %s in %.1f seconds after error: %s",
                    func.__name__,
                    delay,
                    err,
                )
                await asyncio.sleep(delay)


class UnifiInsightsRequestCache:
    """Cache for API requests."""

    def __init__(self, ttl: timedelta = timedelta(minutes=5)) -> None:
        """Initialize cache."""
        self._cache = {}
        self._ttl = ttl

    def get(self, key: str) -> Any | None:
        """Get item from cache."""
        if key not in self._cache:
            return None

        data, timestamp = self._cache[key]
        if datetime.now() - timestamp > self._ttl:
            del self._cache[key]
            return None

        return data

    def set(self, key: str, value: Any) -> None:
        """Set item in cache."""
        self._cache[key] = (value, datetime.now())


class UnifiInsightsClient:
    """UniFi Network API client."""

    def __init__(
        self,
        hass: HomeAssistant,
        api_key: str,
        host: str = DEFAULT_API_HOST,
        session: ClientSession | None = None,
        verify_ssl: bool = False,
    ) -> None:
        """Initialize the UniFi Network API client."""
        _LOGGER.debug("Initializing UniFi Network API client with host: %s", host)
        self._api_key = api_key
        self._host = host
        self._verify_ssl = verify_ssl

        if session:
            self._session = session
        else:
            self._session = async_create_clientsession(
                hass,
                verify_ssl=verify_ssl,
            )

        self._request_lock = asyncio.Lock()
        self._backoff = UnifiInsightsBackoff()
        self._cache = UnifiInsightsRequestCache()
        _LOGGER.info("UniFi Network API client initialized")

    @property
    def host(self) -> str:
        """Return the host address for the UniFi Network system."""
        return self._host

    async def _request(
        self,
        method: str,
        endpoint: str,
        use_cache: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make an API request."""
        cache_key = f"{method}_{endpoint}_{kwargs!s}" if use_cache else None

        if use_cache:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached

        async def _do_request() -> dict[str, Any]:
            async with self._request_lock:
                headers = {
                    **UNIFI_API_HEADERS,
                    "X-API-Key": self._api_key,
                }

                if "headers" in kwargs:
                    headers.update(kwargs.pop("headers"))

                url = f"{self._host}/proxy/network/integration{endpoint}"
                _LOGGER.debug("Making %s request to %s", method, url)

                try:
                    async with self._session.request(
                        method, url, headers=headers, ssl=self._verify_ssl, **kwargs
                    ) as resp:
                        _LOGGER.debug(
                            "Response received from %s - Status: %s",
                            endpoint,
                            resp.status,
                        )

                        # Log raw response for debugging
                        try:
                            raw_data = await resp.text()
                            _LOGGER.debug("Raw response data: %s", raw_data)
                        except Exception as err:
                            _LOGGER.debug("Could not log raw response: %s", err)

                        if resp.status == 401:
                            msg = "Invalid API key"
                            raise UnifiInsightsAuthError(msg)
                        if resp.status == 403:
                            msg = "API key lacks permission"
                            raise UnifiInsightsAuthError(msg)
                        if resp.status == 404:
                            msg = f"Endpoint not found: {endpoint}"
                            raise UnifiInsightsConnectionError(
                                msg
                            )
                        if resp.status >= 500:
                            msg = f"Server error: {resp.status}"
                            raise UnifiInsightsConnectionError(
                                msg
                            )

                        resp.raise_for_status()

                        try:
                            response_data = await resp.json()
                            _LOGGER.debug(
                                "Processed response from %s: %s",
                                endpoint,
                                json.dumps(response_data, indent=2),
                            )

                            if use_cache and cache_key:
                                self._cache.set(cache_key, response_data)

                            return response_data
                        except ValueError as err:
                            _LOGGER.exception("Failed to parse JSON response: %s", err)
                            msg = "Invalid JSON response"
                            raise UnifiInsightsConnectionError(
                                msg
                            ) from err

                except TimeoutError as err:
                    _LOGGER.exception("Request timed out for %s: %s", url, err)
                    msg = f"Timeout connecting to {url}"
                    raise UnifiInsightsConnectionError(
                        msg
                    ) from err
                except ClientError as err:
                    _LOGGER.exception("Connection error for %s: %s", url, err)
                    msg = f"Error connecting to {url}: {err}"
                    raise UnifiInsightsConnectionError(
                        msg
                    ) from err

        return await self._backoff.execute(_do_request)

    async def async_get_sites(self) -> list[dict[str, Any]]:
        """Get all sites."""
        _LOGGER.debug("Fetching all sites")
        try:
            response = await self._request("GET", "/v1/sites", use_cache=True)
            sites = response.get("data", [])

            # Log sites data
            _LOGGER.debug(
                "Sites data structure:\n%s",
                json.dumps(
                    [
                        {
                            "id": site.get("id"),
                            "name": site.get("name"),
                            "description": site.get("description"),
                            "meta": site.get("meta", {}),
                        }
                        for site in sites
                    ],
                    indent=2,
                ),
            )

            _LOGGER.info("Successfully retrieved %d sites", len(sites))
            return sites
        except Exception as err:
            _LOGGER.error("Failed to fetch sites: %s", err, exc_info=True)
            raise

    async def async_get_devices(self, site_id: str) -> list[dict[str, Any]]:
        """Get all devices for a site."""
        _LOGGER.debug("Fetching devices for site %s", site_id)
        try:
            response = await self._request("GET", f"/v1/sites/{site_id}/devices")
            devices = response.get("data", [])

            # Log each device's data structure
            for device in devices:
                _LOGGER.debug(
                    "Device data structure for %s:\n%s",
                    device.get("name", "Unknown"),
                    json.dumps(
                        {
                            "name": device.get("name"),
                            "model": device.get("model"),
                            "mac": device.get("macAddress"),
                            "ip": device.get("ipAddress"),
                            "state": device.get("state"),
                            "features": device.get("features", []),
                            "port_table": device.get("port_table", []),
                            "radio_table": device.get("radio_table", []),
                        },
                        indent=2,
                    ),
                )

            _LOGGER.info(
                "Successfully retrieved %d devices for site %s", len(devices), site_id
            )
            return devices
        except Exception as err:
            _LOGGER.error(
                "Failed to fetch devices for site %s: %s", site_id, err, exc_info=True
            )
            raise

    async def async_get_device_info(
        self, site_id: str, device_id: str
    ) -> dict[str, Any]:
        """Get detailed device information."""
        _LOGGER.debug(
            "Fetching device info for device %s in site %s", device_id, site_id
        )
        try:
            response = await self._request(
                "GET", f"/v1/sites/{site_id}/devices/{device_id}"
            )
            _LOGGER.debug(
                "Device info for %s: %s", device_id, json.dumps(response, indent=2)
            )
            return response
        except Exception as err:
            _LOGGER.exception(
                "Failed to fetch device info for device %s in site %s: %s",
                device_id,
                site_id,
                err,
            )
            raise

    async def async_get_device_stats(
        self, site_id: str, device_id: str
    ) -> dict[str, Any]:
        """Get device statistics."""
        _LOGGER.debug(
            "Fetching statistics for device %s in site %s", device_id, site_id
        )
        try:
            response = await self._request(
                "GET", f"/v1/sites/{site_id}/devices/{device_id}/statistics/latest"
            )

            # Log complete statistics data
            _LOGGER.debug(
                "Complete statistics for device %s: %s",
                device_id,
                json.dumps(response, indent=2),
            )

            return response
        except Exception as err:
            _LOGGER.error(
                "Failed to fetch stats for device %s in site %s: %s",
                device_id,
                site_id,
                err,
                exc_info=True,
            )
            raise

    async def async_get_clients(
        self, site_id: str, offset: int = 0, limit: int = 25
    ) -> list[dict[str, Any]]:
        """Get all clients for a site with pagination."""
        _LOGGER.debug(
            "Fetching clients for site %s (offset: %d, limit: %d)",
            site_id,
            offset,
            limit,
        )
        try:
            response = await self._request(
                "GET",
                f"/v1/sites/{site_id}/clients",
                params={"offset": offset, "limit": limit},
            )
            clients = response.get("data", [])
            total_count = response.get("totalCount", 0)

            # If we have more clients than our current limit, fetch the rest
            if total_count > offset + limit:
                next_offset = offset + limit
                more_clients = await self.async_get_clients(
                    site_id, offset=next_offset, limit=limit
                )
                clients.extend(more_clients)

            _LOGGER.debug("Retrieved %d clients for site %s", len(clients), site_id)
            return clients
        except Exception as err:
            _LOGGER.exception("Failed to fetch clients for site %s: %s", site_id, err)
            raise

    async def async_restart_device(self, site_id: str, device_id: str) -> bool:
        """Restart a device."""
        _LOGGER.debug("Attempting to restart device %s in site %s", device_id, site_id)
        try:
            response = await self._request(
                "POST",
                f"/v1/sites/{site_id}/devices/{device_id}/actions",
                json={"action": "RESTART"},
            )
            success = response.get("status") == "OK"
            if success:
                _LOGGER.info(
                    "Successfully initiated restart for device %s in site %s",
                    device_id,
                    site_id,
                )
            else:
                _LOGGER.error(
                    "Failed to restart device %s in site %s", device_id, site_id
                )
            return success
        except Exception as err:
            _LOGGER.exception(
                "Error restarting device %s in site %s: %s", device_id, site_id, err
            )
            raise

    async def async_validate_api_key(self) -> bool:
        """Validate API key by fetching sites."""
        _LOGGER.debug("Validating API key")
        try:
            await self.async_get_sites()
            _LOGGER.info("API key validation successful")
            return True
        except UnifiInsightsAuthError:
            _LOGGER.exception("API key validation failed")
            return False
        except Exception as err:
            _LOGGER.exception("Unexpected error during API key validation: %s", err)
            return False

    async def async_get_application_info(self) -> dict[str, Any]:
        """Get UniFi Network application information."""
        _LOGGER.debug("Fetching UniFi Network application info")
        try:
            response = await self._request("GET", "/v1/info")
            _LOGGER.debug("Application info: %s", json.dumps(response, indent=2))
            return response
        except Exception as err:
            _LOGGER.exception("Failed to fetch application info: %s", err)
            raise

    async def async_power_cycle_port(
        self, site_id: str, device_id: str, port_idx: int
    ) -> bool:
        """Power cycle a specific port on a device."""
        _LOGGER.debug(
            "Power cycling port %d on device %s in site %s",
            port_idx,
            device_id,
            site_id,
        )
        try:
            await self._request(
                "POST",
                f"/v1/sites/{site_id}/devices/{device_id}/interfaces/ports/{port_idx}/actions",
                json={"action": "POWER_CYCLE"},
            )
            _LOGGER.info(
                "Successfully power cycled port %d on device %s", port_idx, device_id
            )
            return True
        except Exception as err:
            _LOGGER.exception(
                "Failed to power cycle port %d on device %s: %s",
                port_idx,
                device_id,
                err,
            )
            raise

    async def async_authorize_guest(
        self,
        site_id: str,
        client_id: str,
        time_limit_minutes: int | None = None,
        data_usage_limit_mbytes: int | None = None,
        rx_rate_limit_kbps: int | None = None,
        tx_rate_limit_kbps: int | None = None,
    ) -> dict[str, Any]:
        """Authorize guest access for a client."""
        _LOGGER.debug(
            "Authorizing guest access for client %s in site %s", client_id, site_id
        )

        data = {"action": "AUTHORIZE_GUEST_ACCESS"}

        if time_limit_minutes is not None:
            data["timeLimitMinutes"] = time_limit_minutes
        if data_usage_limit_mbytes is not None:
            data["dataUsageLimitMBytes"] = data_usage_limit_mbytes
        if rx_rate_limit_kbps is not None:
            data["rxRateLimitKbps"] = rx_rate_limit_kbps
        if tx_rate_limit_kbps is not None:
            data["txRateLimitKbps"] = tx_rate_limit_kbps

        try:
            response = await self._request(
                "POST", f"/v1/sites/{site_id}/clients/{client_id}/actions", json=data
            )
            _LOGGER.info(
                "Successfully authorized guest access for client %s", client_id
            )
            return response
        except Exception as err:
            _LOGGER.exception(
                "Failed to authorize guest access for client %s: %s", client_id, err
            )
            raise

    async def async_list_vouchers(
        self,
        site_id: str,
        offset: int = 0,
        limit: int = 100,
        filter_expr: str | None = None,
    ) -> list[dict[str, Any]]:
        """List hotspot vouchers for a site."""
        _LOGGER.debug("Listing vouchers for site %s", site_id)

        params = {"offset": offset, "limit": limit}
        if filter_expr:
            params["filter"] = filter_expr

        try:
            response = await self._request(
                "GET", f"/v1/sites/{site_id}/hotspot/vouchers", params=params
            )
            vouchers = response.get("data", [])
            _LOGGER.debug("Retrieved %d vouchers", len(vouchers))
            return vouchers
        except Exception as err:
            _LOGGER.exception("Failed to list vouchers: %s", err)
            raise

    async def async_generate_voucher(
        self,
        site_id: str,
        name: str,
        time_limit_minutes: int,
        count: int = 1,
        authorized_guest_limit: int | None = None,
        data_usage_limit_mbytes: int | None = None,
        rx_rate_limit_kbps: int | None = None,
        tx_rate_limit_kbps: int | None = None,
    ) -> dict[str, Any]:
        """Generate hotspot vouchers."""
        _LOGGER.debug("Generating %d voucher(s) for site %s", count, site_id)

        data = {
            "count": count,
            "name": name,
            "timeLimitMinutes": time_limit_minutes,
        }

        if authorized_guest_limit is not None:
            data["authorizedGuestLimit"] = authorized_guest_limit
        if data_usage_limit_mbytes is not None:
            data["dataUsageLimitMBytes"] = data_usage_limit_mbytes
        if rx_rate_limit_kbps is not None:
            data["rxRateLimitKbps"] = rx_rate_limit_kbps
        if tx_rate_limit_kbps is not None:
            data["txRateLimitKbps"] = tx_rate_limit_kbps

        try:
            response = await self._request(
                "POST", f"/v1/sites/{site_id}/hotspot/vouchers", json=data
            )
            _LOGGER.info("Successfully generated %d voucher(s)", count)
            return response
        except Exception as err:
            _LOGGER.exception("Failed to generate vouchers: %s", err)
            raise

    async def async_delete_voucher(self, site_id: str, voucher_id: str) -> bool:
        """Delete a specific hotspot voucher."""
        _LOGGER.debug("Deleting voucher %s in site %s", voucher_id, site_id)
        try:
            await self._request(
                "DELETE", f"/v1/sites/{site_id}/hotspot/vouchers/{voucher_id}"
            )
            _LOGGER.info("Successfully deleted voucher %s", voucher_id)
            return True
        except Exception as err:
            _LOGGER.exception("Failed to delete voucher %s: %s", voucher_id, err)
            raise

    async def async_delete_vouchers_by_filter(
        self, site_id: str, filter_expr: str
    ) -> int:
        """Delete hotspot vouchers based on filter criteria."""
        _LOGGER.debug(
            "Deleting vouchers in site %s with filter: %s", site_id, filter_expr
        )
        try:
            response = await self._request(
                "DELETE",
                f"/v1/sites/{site_id}/hotspot/vouchers",
                params={"filter": filter_expr},
            )
            deleted_count = response.get("vouchersDeleted", 0)
            _LOGGER.info("Successfully deleted %d voucher(s)", deleted_count)
            return deleted_count
        except Exception as err:
            _LOGGER.exception("Failed to delete vouchers: %s", err)
            raise
