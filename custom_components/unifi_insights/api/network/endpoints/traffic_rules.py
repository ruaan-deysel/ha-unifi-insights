"""Traffic rules endpoint for UniFi Network API."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from pydantic import ValidationError

from custom_components.unifi_insights.api.const import ENDPOINT_TRAFFIC_RULES
from custom_components.unifi_insights.api.exceptions import (
    UniFiNotFoundError,
    UniFiResponseError,
)
from custom_components.unifi_insights.api.network.models.traffic_rule import TrafficRule

if TYPE_CHECKING:
    from custom_components.unifi_insights.api.network.client import UniFiNetworkClient

_LOGGER = logging.getLogger(__name__)


class TrafficRulesEndpoint:
    """Endpoint for managing traffic rule configurations.

    Targets the legacy v2 controller endpoint:
    ``/proxy/network/v2/api/site/{site_name}/trafficrules``

    Writes follow the aiounifi ``TrafficRuleEnableRequest`` precedent: fetch the
    full current record, toggle ``enabled``, and PUT the full raw object to
    ``trafficrules/{rule_id}``.
    """

    def __init__(self, client: UniFiNetworkClient) -> None:
        """Initialize the Traffic Rules endpoint."""
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

    async def list_traffic_rules(self, site_name: str) -> list[TrafficRule]:
        """List all traffic rules for a site."""
        path = self._client.build_legacy_v2_api_path(site_name, ENDPOINT_TRAFFIC_RULES)
        response = await self._client._get(path)
        items = self._extract_items(response)

        rules: list[TrafficRule] = []
        for item in items:
            try:
                rules.append(TrafficRule.model_validate(item))
            except ValidationError as err:
                _LOGGER.debug("Skipping invalid traffic rule item: %s", err)
                continue

        return rules

    async def update_traffic_rule(
        self, site_name: str, rule_id: str, *, enabled: bool
    ) -> TrafficRule:
        """Update a traffic rule configuration (e.g. enable/disable)."""
        list_path = self._client.build_legacy_v2_api_path(
            site_name, ENDPOINT_TRAFFIC_RULES
        )
        items = self._extract_items(await self._client._get(list_path))
        current = next(
            (i for i in items if (i.get("_id") or i.get("id")) == rule_id), None
        )
        if current is None:
            msg = f"Traffic rule {rule_id} not found"
            raise UniFiNotFoundError(msg, status_code=404)

        payload = dict(current)
        payload["enabled"] = enabled

        put_path = self._client.build_legacy_v2_api_path(
            site_name, f"{ENDPOINT_TRAFFIC_RULES}/{rule_id}"
        )
        put_items = self._extract_items(
            await self._client._put(put_path, json_data=payload)
        )
        if put_items and (put_items[0].get("_id") or put_items[0].get("id")) == rule_id:
            return TrafficRule.model_validate(put_items[0])

        return TrafficRule.model_validate(payload)
