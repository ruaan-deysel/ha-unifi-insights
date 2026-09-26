"""Historical site traffic report endpoint for UniFi Network API."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from custom_components.unifi_insights.api.exceptions import UniFiResponseError
from custom_components.unifi_insights.api.network.models.report import (
    DEFAULT_SITE_REPORT_ATTRS,
    SITE_REPORT_INTERVALS,
    SiteReportBucket,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from custom_components.unifi_insights.api.network.client import UniFiNetworkClient

_LOGGER = logging.getLogger(__name__)


class ReportsEndpoint:
    """
    Endpoint for querying historical site traffic statistics.

    Targets the unverified classic controller report endpoint documented by the
    UniFi community (Art of WiFi controller API reference / UniFi Network web
    UI traffic activity charts):
    ``POST /proxy/network/api/s/{site}/stat/report/{interval}.site``
    """

    def __init__(self, client: UniFiNetworkClient) -> None:
        """Initialize the Reports endpoint."""
        self._client = client

    @staticmethod
    def _extract_buckets_list(response: Any) -> list[dict[str, Any]]:
        """
        Extract report bucket dictionaries from a controller response.

        Accepts either a bare list or a ``{"meta": ..., "data": [...]}``
        envelope, raising ``UniFiResponseError`` when ``meta.rc == "error"``.
        """
        if response is None:
            return []

        if isinstance(response, dict):
            meta = response.get("meta")
            if isinstance(meta, dict) and meta.get("rc") == "error":
                msg = str(meta.get("msg", "UniFi Network API error"))
                raise UniFiResponseError(
                    msg,
                    status_code=200,
                    response_body=str(response),
                )

            data = response.get("data")
            if isinstance(data, list):
                return [item for item in data if isinstance(item, dict)]
            return []

        if isinstance(response, list):
            return [item for item in response if isinstance(item, dict)]

        return []

    async def get_site_report(
        self,
        site_name: str,
        interval: str,
        *,
        start_ms: int | None = None,
        end_ms: int | None = None,
        start: int | None = None,
        end: int | None = None,
        attrs: Sequence[str] | None = None,
        expected_unsupported: bool = True,
    ) -> list[SiteReportBucket]:
        """
        Fetch historical site traffic report buckets for a time window.

        Uses the community-documented classic controller endpoint
        ``POST /proxy/network/api/s/{site}/stat/report/{interval}.site`` with
        millisecond ``start`` and ``end`` timestamps and requested ``attrs``.
        This endpoint is not part of the official integration OpenAPI schema
        and should be treated as optional/unverified by callers.

        Args:
            site_name: The classic UniFi site name (e.g. ``"default"``).
            interval: Report bucket interval (``"5minutes"``, ``"hourly"``,
                or ``"daily"``).
            start_ms: Start timestamp in milliseconds since epoch.
            end_ms: End timestamp in milliseconds since epoch.
            start: Alias for ``start_ms``.
            end: Alias for ``end_ms``.
            attrs: Optional attribute list (defaults to WAN RX/TX byte fields).
            expected_unsupported: Whether a non-JSON 2xx response is an
                expected unsupported-endpoint signal.

        Returns:
            List of validated ``SiteReportBucket`` instances.

        Raises:
            ValueError: If ``interval`` is unsupported or timestamps are missing.
            UniFiResponseError: If the controller returns ``meta.rc == "error"``.

        """
        if interval not in SITE_REPORT_INTERVALS:
            msg = (
                f"Unsupported report interval {interval!r}; "
                f"expected one of {sorted(SITE_REPORT_INTERVALS)}"
            )
            raise ValueError(msg)

        resolved_start = start_ms if start_ms is not None else start
        resolved_end = end_ms if end_ms is not None else end
        if resolved_start is None or resolved_end is None:
            msg = "Both start and end timestamps (in milliseconds) are required"
            raise ValueError(msg)

        path = self._client.build_legacy_api_path(
            site_name,
            f"/stat/report/{interval}.site",
        )
        payload: dict[str, Any] = {
            "attrs": list(attrs)
            if attrs is not None
            else list(DEFAULT_SITE_REPORT_ATTRS),
            "start": int(resolved_start),
            "end": int(resolved_end),
        }
        response = await self._client._post(
            path,
            json_data=payload,
            expected_unsupported=expected_unsupported,
        )
        raw_items = self._extract_buckets_list(response)

        buckets: list[SiteReportBucket] = []
        for item in raw_items:
            try:
                buckets.append(SiteReportBucket.model_validate(item))
            except Exception as err:
                _LOGGER.debug("Skipping invalid site report bucket: %s", err)
                continue

        return buckets
