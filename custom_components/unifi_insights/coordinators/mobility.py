# Copyright 2026 UniFi Insights contributors
"""Optional UniFi Mobility polling for the entry that owns a cloud API key."""

from __future__ import annotations

import logging
import math
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.const import CONF_API_KEY
from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from custom_components.unifi_insights.api import (
    ApiKeyAuth,
    UniFiAuthenticationError,
    UniFiError,
    UniFiRateLimitError,
    UniFiResponseError,
)
from custom_components.unifi_insights.api.mobility import (
    UniFiMobilityClient,
    is_valid_mobility_id,
)
from custom_components.unifi_insights.const import (
    CONF_CONNECTION_TYPE,
    CONNECTION_TYPE_REMOTE,
    DOMAIN,
    SCAN_INTERVAL_MOBILITY,
    SCAN_INTERVAL_MOBILITY_IDLE,
)

if TYPE_CHECKING:
    from aiohttp import ClientSession
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)
# Polling uses at most half of the key's 100 requests per minute on average,
# leaving the rest for anything else that uses the same key.
_REQUESTS_PER_MINUTE_BUDGET = 50
ACCESS_UNKNOWN = "unknown"
ACCESS_GRANTED = "granted"
ACCESS_DENIED = "denied"


def _empty_snapshot(access: str = ACCESS_UNKNOWN) -> dict[str, Any]:
    """Return a snapshot without workspaces or devices."""
    return {"access": access, "workspaces": {}, "devices": {}, "updated_at": None}


class UnifiInsightsMobilityCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Poll Mobility workspaces and routers for one config entry."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: UniFiMobilityClient,
    ) -> None:
        """Initialize the coordinator for the entry that owns the API key."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN}_mobility",
            update_interval=SCAN_INTERVAL_MOBILITY,
        )
        self.client = client
        self.data = _empty_snapshot()
        self.last_error_type: str | None = None

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch Mobility data, keeping the last snapshot when a poll fails."""
        try:
            snapshot = await self._async_fetch()
        except UniFiError as err:
            self.last_error_type = type(err).__name__
            msg = f"Error fetching UniFi Mobility data ({type(err).__name__})"
            raise UpdateFailed(msg) from err
        self.last_error_type = None
        return snapshot

    async def _async_fetch(self) -> dict[str, Any]:
        """Read workspaces, then each active workspace's routers and their detail."""
        now = datetime.now(UTC).isoformat()
        try:
            workspace_rows = await self.client.list_workspaces()
        except UniFiAuthenticationError as err:
            # Most cloud keys have no Mobility scope. That is not a broken
            # entry, so it never starts reauth; it is only re-checked hourly.
            if self.data.get("access") != ACCESS_DENIED:
                _LOGGER.info(
                    "UniFi Mobility is not available to this API key (status %s), "
                    "checking again in an hour",
                    err.status_code,
                )
            self.update_interval = SCAN_INTERVAL_MOBILITY_IDLE
            return {**_empty_snapshot(ACCESS_DENIED), "updated_at": now}

        if self.data.get("access") == ACCESS_DENIED:
            _LOGGER.info("UniFi Mobility is available to this API key again")

        workspaces: dict[str, dict[str, Any]] = {}
        devices: dict[str, dict[str, Any]] = {}
        requests = 1
        for row in workspace_rows:
            workspace_id = row.get("workspace_id")
            if not is_valid_mobility_id(workspace_id):
                continue
            workspace: dict[str, Any] = {
                "name": str(row.get("workspace_name") or ""),
                "status": row.get("status"),
                "is_owner": row.get("is_owner") is True,
                "device_ids": [],
            }
            workspaces[workspace_id] = workspace
            # Pending, declined and inactive memberships cannot be read.
            if workspace["status"] != "ACTIVE":
                continue

            requests += 1
            try:
                summaries = await self.client.list_devices(workspace_id)
            except UniFiAuthenticationError:
                _LOGGER.debug("Skipping a Mobility workspace this key cannot read")
                continue

            for summary in summaries:
                device_id = summary.get("id")
                if not is_valid_mobility_id(device_id) or device_id in devices:
                    continue
                requests += 1
                workspace["device_ids"].append(device_id)
                devices[device_id] = await self._async_device(
                    workspace_id, device_id, summary
                )

        self.update_interval = (
            max(
                SCAN_INTERVAL_MOBILITY,
                timedelta(minutes=math.ceil(requests / _REQUESTS_PER_MINUTE_BUDGET)),
            )
            if devices
            else SCAN_INTERVAL_MOBILITY_IDLE
        )
        return {
            "access": ACCESS_GRANTED,
            "workspaces": workspaces,
            "devices": devices,
            "updated_at": now,
        }

    async def _async_device(
        self, workspace_id: str, device_id: str, summary: dict[str, Any]
    ) -> dict[str, Any]:
        """Return a router's detail, or its summary if the detail is unavailable."""
        try:
            detail = await self.client.get_device(workspace_id, device_id)
        except UniFiRateLimitError:
            raise
        except UniFiResponseError as err:
            # A router removed between the two calls answers 404; an upstream
            # error for one router should not hide every other router.
            _LOGGER.debug(
                "Mobility device detail unavailable (status %s)", err.status_code
            )
            return {**summary, "workspace_id": workspace_id, "detail_available": False}
        return {
            **summary,
            **detail,
            "id": device_id,
            "workspace_id": workspace_id,
            "detail_available": True,
        }


def is_mobility_owner(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Return True if this entry polls Mobility for its API key.

    Mobility is account-wide, so remote entries sharing a key would create the
    same entities. The oldest enabled remote entry with the key owns them.
    """
    if entry.data.get(CONF_CONNECTION_TYPE) != CONNECTION_TYPE_REMOTE:
        return False
    api_key = entry.data.get(CONF_API_KEY)
    candidates = [
        candidate.entry_id
        for candidate in hass.config_entries.async_entries(
            DOMAIN, include_ignore=False, include_disabled=False
        )
        if candidate.data.get(CONF_CONNECTION_TYPE) == CONNECTION_TYPE_REMOTE
        and candidate.data.get(CONF_API_KEY) == api_key
    ]
    return bool(candidates) and min(candidates) == entry.entry_id


@callback
def async_setup_mobility(
    hass: HomeAssistant, entry: ConfigEntry, session: ClientSession
) -> UnifiInsightsMobilityCoordinator | None:
    """Start Mobility polling if this entry owns its API key's Mobility data."""
    if not is_mobility_owner(hass, entry):
        _LOGGER.debug("UniFi Mobility is polled by another entry with this API key")
        return None

    client = UniFiMobilityClient(
        auth=ApiKeyAuth(api_key=entry.data[CONF_API_KEY]), session=session, timeout=30
    )
    entry.async_on_unload(client.close)
    coordinator = UnifiInsightsMobilityCoordinator(hass, entry, client)
    # A background task keeps optional cloud requests from holding up
    # Home Assistant startup.
    entry.async_create_background_task(
        hass, coordinator.async_refresh(), name=f"{DOMAIN}_mobility_initial_refresh"
    )
    return coordinator
