"""Sites endpoint for UniFi Network API."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from pydantic import ValidationError

from ..models import Site

if TYPE_CHECKING:
    from ..client import UniFiNetworkClient

_LOGGER = logging.getLogger(__name__)


class SitesEndpoint:
    """Endpoint for managing UniFi sites."""

    def __init__(self, client: UniFiNetworkClient) -> None:
        """
        Initialize the sites endpoint.

        Args:
            client: The UniFi Network client.

        """
        self._client = client

    async def get_all(
        self,
        *,
        offset: int | None = None,
        limit: int | None = None,
        filter_str: str | None = None,
        expected_unsupported: bool = False,
    ) -> list[Site]:
        """
        List all sites.

        Args:
            offset: Number of sites to skip (pagination).
            limit: Maximum number of sites to return.
            filter_str: Filter string for site properties.
            expected_unsupported: Whether a non-JSON 2xx response is an
                expected unsupported-endpoint signal - a console without the
                Network application. Only lowers the log level of an
                unredirected response; the call still raises.

        Returns:
            List of sites.

        """
        params: dict[str, Any] = {}
        if offset is not None:
            params["offset"] = offset
        if limit is not None:
            params["limit"] = limit
        if filter_str:
            params["filter"] = filter_str

        path = self._client.build_api_path("/sites")
        response = await self._client._get(
            path,
            params=params if params else None,
            expected_unsupported=expected_unsupported,
        )

        if response is None:
            return []

        data = (
            response.get("data", response) if isinstance(response, dict) else response
        )
        if isinstance(data, list):
            sites: list[Site] = []
            for item in data:
                try:
                    sites.append(Site.model_validate(item))
                except ValidationError as err:
                    _LOGGER.warning(
                        "Skipping site that failed to parse (id=%s): %s",
                        item.get("id") or item.get("internalReference")
                        if isinstance(item, dict)
                        else "?",
                        err,
                    )
            return sites
        return []

    async def get_legacy_all(self) -> list[dict[str, Any]]:
        """
        List all sites from the legacy Network API.

        Returns:
            Raw legacy site dictionaries from ``/self/sites``.

        """
        path = self._client.build_legacy_global_api_path("/self/sites")
        response = await self._client._get(path)

        if response is None:
            return []

        data = (
            response.get("data", response) if isinstance(response, dict) else response
        )
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        if isinstance(data, dict):
            return [data]
        return []
