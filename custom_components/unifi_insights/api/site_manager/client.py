# Copyright 2026 UniFi Insights contributors
"""Client for the UniFi Site Manager API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, NoReturn

from custom_components.unifi_insights.api.base import BaseUniFiClient
from custom_components.unifi_insights.api.const import (
    DEFAULT_CONNECT_TIMEOUT,
    DEFAULT_TIMEOUT,
)
from custom_components.unifi_insights.api.exceptions import UniFiResponseError

if TYPE_CHECKING:
    from datetime import datetime

    import aiohttp

    from custom_components.unifi_insights.api.auth import ApiKeyAuth

_SITE_MANAGER_API_BASE_URL = "https://api.ui.com"
_MAX_PAGES = 100
_MAX_ITEMS = 10_000


class UniFiSiteManagerClient(BaseUniFiClient):
    """Async client for the UniFi Site Manager API."""

    def _response_log_text(self, response_text: str, *, limit: int) -> str:
        """Keep account-wide inventory and metadata out of transport logs."""
        return "[Site Manager response omitted]"[:limit] if response_text else "empty"

    def __init__(
        self,
        auth: ApiKeyAuth,
        *,
        session: aiohttp.ClientSession | None = None,
        timeout: int = DEFAULT_TIMEOUT,
        connect_timeout: int = DEFAULT_CONNECT_TIMEOUT,
    ) -> None:
        """Initialize the Site Manager API client."""
        super().__init__(
            auth=auth,
            base_url=_SITE_MANAGER_API_BASE_URL,
            session=session,
            timeout=timeout,
            connect_timeout=connect_timeout,
        )

    async def validate_connection(self) -> bool:
        """Validate credentials by listing accessible hosts."""
        await self.list_hosts()
        return True

    async def list_hosts(self) -> list[dict[str, Any]]:
        """Return all accessible UniFi hosts."""
        return await self._list_paginated("/v1/hosts")

    async def get_host(self, host_id: str) -> dict[str, Any]:
        """Return detailed information for a specific host."""
        path = f"/v1/hosts/{host_id}"
        data = await self._get(path)
        return self._extract_object(data, path)

    async def list_sites(self) -> list[dict[str, Any]]:
        """Return all accessible UniFi sites."""
        return await self._list_paginated("/v1/sites")

    async def list_devices(
        self, host_ids: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """Return devices grouped by host, merged across every result page."""
        params: dict[str, Any] | None = None
        if host_ids:
            params = {"hostIds[]": host_ids}

        pages = await self._list_paginated("/v1/devices", params=params)
        groups: dict[str, dict[str, Any]] = {}
        anonymous_groups: list[dict[str, Any]] = []

        for group in pages:
            devices = group.get("devices")
            if devices is None:
                devices = []
            if not isinstance(devices, list) or not all(
                isinstance(device, dict) for device in devices
            ):
                self._raise_response_error("/v1/devices returned malformed devices")
            host_id = group.get("hostId")
            if not isinstance(host_id, str) or not host_id:
                anonymous_groups.append({**group, "devices": devices})
                continue

            existing = groups.get(host_id)
            if existing is None:
                groups[host_id] = {**group, "devices": list(devices)}
                continue

            existing.update(
                {key: value for key, value in group.items() if key != "devices"}
            )
            existing_devices = existing["devices"]
            existing_devices.extend(devices)

        return [*groups.values(), *anonymous_groups]

    async def get_isp_metrics(
        self,
        begin_timestamp: datetime | None = None,
        end_timestamp: datetime | None = None,
        *,
        metric_type: Literal["5m", "1h"] = "5m",
        duration: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return ISP metrics for the supplied time range or duration."""
        params: dict[str, Any] = {}
        if begin_timestamp is not None:
            params["beginTimestamp"] = self._format_timestamp(begin_timestamp)
        if end_timestamp is not None:
            params["endTimestamp"] = self._format_timestamp(end_timestamp)
        if duration is not None:
            params["duration"] = duration

        path = f"/v1/isp-metrics/{metric_type}"
        data = await self._get(path, params=params or None)
        return self._extract_data(data, path)

    async def query_isp_metrics(
        self,
        metric_type: Literal["5m", "1h"],
        sites: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Query ISP metrics for specific sites and time ranges."""
        path = f"/v1/isp-metrics/{metric_type}/query"
        data = await self._post(path, json_data={"sites": sites})
        return self._extract_object(data, path)

    async def list_sd_wan_configs(self) -> list[dict[str, Any]]:
        """Return all SD-WAN configurations."""
        data = await self._get("/v1/sd-wan-configs")
        return self._extract_data(data, "/v1/sd-wan-configs")

    async def get_sd_wan_config(self, config_id: str) -> dict[str, Any]:
        """Return detailed information for a specific SD-WAN configuration."""
        path = f"/v1/sd-wan-configs/{config_id}"
        data = await self._get(path)
        return self._extract_object(data, path)

    async def get_sd_wan_config_status(self, config_id: str) -> dict[str, Any]:
        """Return deployment and connection status for an SD-WAN config."""
        path = f"/v1/sd-wan-configs/{config_id}/status"
        data = await self._get(path)
        return self._extract_object(data, path)

    async def _list_paginated(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Return all pages from a Site Manager list endpoint."""
        items: list[dict[str, Any]] = []
        next_token: str | None = None
        seen_tokens: set[str] = set()

        for _ in range(_MAX_PAGES):
            page_params = dict(params or {})
            if next_token is not None:
                page_params["nextToken"] = next_token

            response = await self._get(path, params=page_params or None)
            page = self._extract_data(response, path)
            if len(items) + len(page) > _MAX_ITEMS:
                self._raise_response_error(f"{path} exceeded the item limit")
            items.extend(page)

            token = self._extract_next_token(response, path)
            if token is None:
                return items
            if not page:
                self._raise_response_error(
                    f"{path} returned an empty page with nextToken"
                )
            if token in seen_tokens:
                self._raise_response_error(f"{path} repeated nextToken")
            seen_tokens.add(token)
            next_token = token

        msg = f"{path} exceeded the page limit"
        raise UniFiResponseError(msg, status_code=200)

    @staticmethod
    def _format_timestamp(timestamp: datetime) -> str:
        """Format an aware datetime as an RFC3339 timestamp."""
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            msg = "Timestamps must include a UTC offset"
            raise ValueError(msg)

        return timestamp.isoformat().replace("+00:00", "Z")

    def _extract_data(
        self,
        response: dict[str, Any] | list[Any] | None,
        path: str,
    ) -> list[dict[str, Any]]:
        """Validate and return a Site Manager response envelope's data list."""
        if not isinstance(response, dict):
            self._raise_response_error(f"{path} returned a malformed response envelope")

        data = response.get("data")
        if not isinstance(data, list) or not all(
            isinstance(item, dict) for item in data
        ):
            self._raise_response_error(f"{path} returned malformed data")

        return data

    def _extract_object(
        self,
        response: dict[str, Any] | list[Any] | None,
        path: str,
    ) -> dict[str, Any]:
        """Validate and return a Site Manager response envelope's data object."""
        if not isinstance(response, dict):
            self._raise_response_error(f"{path} returned a malformed response envelope")

        data = response.get("data")
        if not isinstance(data, dict):
            self._raise_response_error(f"{path} returned malformed data")

        return data

    def _extract_next_token(
        self,
        response: dict[str, Any] | list[Any] | None,
        path: str,
    ) -> str | None:
        """Validate and return an optional pagination token."""
        if not isinstance(response, dict):
            self._raise_response_error(f"{path} returned a malformed response envelope")

        token = response.get("nextToken")
        if token is None:
            return None
        if not isinstance(token, str) or not token:
            self._raise_response_error(f"{path} returned an invalid nextToken")
        return token

    @staticmethod
    def _raise_response_error(message: str) -> NoReturn:
        """Raise a response error for a successful but malformed payload."""
        raise UniFiResponseError(message, status_code=200)
