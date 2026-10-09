"""Port forwards endpoint for UniFi Network API."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from pydantic import ValidationError

from custom_components.unifi_insights.api.const import ENDPOINT_PORT_FORWARD
from custom_components.unifi_insights.api.exceptions import (
    UniFiNotFoundError,
    UniFiResponseError,
)
from custom_components.unifi_insights.api.network.models.port_forward import PortForward

if TYPE_CHECKING:
    from custom_components.unifi_insights.api.network.client import UniFiNetworkClient

_LOGGER = logging.getLogger(__name__)


class PortForwardsEndpoint:
    """Endpoint for managing port forwarding configurations.

    Targets the classic controller endpoint:
    ``/proxy/network/api/s/{site_name}/rest/portforward``

    This path is not in the official UniFi API (Network 11 returns 404 on v2
    ``/portforwards``). Writes follow the aiounifi ``PortForwardEnableRequest``
    precedent: fetch the full current record, toggle ``enabled``, and PUT the full
    raw object. X-API-Key acceptance for PUT requests through the cloud connector
    is unverified live.
    """

    def __init__(self, client: UniFiNetworkClient) -> None:
        """Initialize the Port Forwards endpoint."""
        self._client = client

    def _extract_items(self, response: Any) -> list[dict[str, Any]]:
        """Extract data items from a legacy response envelope."""
        if response is None:
            return []

        if isinstance(response, dict):
            meta = response.get("meta")
            if isinstance(meta, dict) and meta.get("rc") == "error":
                msg = meta.get("msg", "UniFi Network API error")
                raise UniFiResponseError(
                    msg, status_code=200, response_body=str(response)
                )

            data = response.get("data", response)
            if isinstance(data, list):
                return [item for item in data if isinstance(item, dict)]
            if isinstance(data, dict):
                return [data]
            return []

        if isinstance(response, list):
            return [item for item in response if isinstance(item, dict)]

        return []

    async def list_port_forwards(self, site_name: str) -> list[PortForward]:
        """List all port forwarding rules for a site."""
        path = self._client.build_legacy_api_path(site_name, ENDPOINT_PORT_FORWARD)
        response = await self._client._get(path)
        items = self._extract_items(response)

        rules: list[PortForward] = []
        for item in items:
            try:
                rules.append(PortForward.model_validate(item))
            except ValidationError as err:
                _LOGGER.debug("Skipping invalid port forward item: %s", err)
                continue

        return rules

    async def update_port_forward(
        self, site_name: str, rule_id: str, *, enabled: bool
    ) -> PortForward:
        """Update a port forward configuration (e.g. enable/disable)."""
        list_path = self._client.build_legacy_api_path(site_name, ENDPOINT_PORT_FORWARD)
        items = self._extract_items(await self._client._get(list_path))
        current = next(
            (i for i in items if (i.get("_id") or i.get("id")) == rule_id), None
        )
        if current is None:
            msg = f"Port forward {rule_id} not found"
            raise UniFiNotFoundError(msg, status_code=404)

        payload = dict(current)
        payload["enabled"] = enabled

        put_path = self._client.build_legacy_api_path(
            site_name, f"{ENDPOINT_PORT_FORWARD}/{rule_id}"
        )
        put_items = self._extract_items(
            await self._client._put(put_path, json_data=payload)
        )
        if put_items and (put_items[0].get("_id") or put_items[0].get("id")) == rule_id:
            return PortForward.model_validate(put_items[0])

        return PortForward.model_validate(payload)
