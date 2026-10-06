# Copyright 2026 UniFi Insights contributors
"""Read-only client for the UniFi Mobility API."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, ClassVar, NoReturn, TypeIs

from custom_components.unifi_insights.api.base import BaseUniFiClient
from custom_components.unifi_insights.api.const import (
    DEFAULT_CONNECT_TIMEOUT,
    DEFAULT_TIMEOUT,
    MOBILITY_RATE_LIMIT_REQUESTS,
    MOBILITY_RATE_LIMIT_WINDOW,
)
from custom_components.unifi_insights.api.exceptions import (
    UniFiResponseError,
    UniFiValidationError,
)

if TYPE_CHECKING:
    import aiohttp

    from custom_components.unifi_insights.api.auth import ApiKeyAuth

_MOBILITY_API_BASE_URL = "https://api.ui.com"
_WORKSPACES_PATH = "/v1/mobility/workspaces"
# The API caps a page at 200 records.
_PAGE_SIZE = 200
_MAX_ITEMS = 5_000
# Full pages stop at the page limit; the item limit also bounds a server that
# returns more records per page than were asked for.
_MAX_PAGES = _MAX_ITEMS // _PAGE_SIZE
# Workspace and device ids are UUIDs. They become path segments, so anything
# that is not a plain id is refused rather than sent.
_ID_PATTERN = re.compile(r"[0-9A-Za-z-]{1,64}")


def is_valid_mobility_id(identifier: Any) -> TypeIs[str]:
    """Return True if a workspace or device id is a plain path segment."""
    return isinstance(identifier, str) and bool(_ID_PATTERN.fullmatch(identifier))


class UniFiMobilityClient(BaseUniFiClient):
    """Async client for the read-only UniFi Mobility endpoints."""

    RATE_LIMIT: ClassVar[tuple[int, float] | None] = (
        MOBILITY_RATE_LIMIT_REQUESTS,
        MOBILITY_RATE_LIMIT_WINDOW,
    )

    def _response_log_text(self, response_text: str, *, limit: int) -> str:
        """Keep router inventory, IP addresses and GPS fixes out of logs."""
        return "[Mobility response omitted]"[:limit] if response_text else "empty"

    def __init__(
        self,
        auth: ApiKeyAuth,
        *,
        session: aiohttp.ClientSession | None = None,
        timeout: int = DEFAULT_TIMEOUT,
        connect_timeout: int = DEFAULT_CONNECT_TIMEOUT,
    ) -> None:
        """Initialize the Mobility API client."""
        super().__init__(
            auth=auth,
            base_url=_MOBILITY_API_BASE_URL,
            session=session,
            timeout=timeout,
            connect_timeout=connect_timeout,
        )

    async def validate_connection(self) -> bool:
        """Validate the key by listing the Mobility workspaces it can read."""
        await self.list_workspaces()
        return True

    async def list_workspaces(self) -> list[dict[str, Any]]:
        """Return every Mobility workspace the API key can access."""
        response = await self._get(_WORKSPACES_PATH)
        return self._extract_list(response, _WORKSPACES_PATH)

    async def list_devices(self, workspace_id: str) -> list[dict[str, Any]]:
        """Return the summary of every device in a workspace."""
        path = f"{_WORKSPACES_PATH}/{self._safe_id(workspace_id)}/devices"
        items: list[dict[str, Any]] = []

        for _ in range(_MAX_PAGES):
            response = await self._get(
                path, params={"limit": _PAGE_SIZE, "offset": len(items)}
            )
            page = self._extract_list(response, path)
            if len(items) + len(page) > _MAX_ITEMS:
                self._raise_response_error(f"{path} exceeded the item limit")
            items.extend(page)

            total = response.get("total") if isinstance(response, dict) else None
            reached_total = (
                isinstance(total, int)
                and not isinstance(total, bool)
                and len(items) >= total
            )
            if reached_total or len(page) < _PAGE_SIZE:
                return items

        return self._raise_response_error(f"{path} exceeded the page limit")

    async def get_device(self, workspace_id: str, device_id: str) -> dict[str, Any]:
        """Return the detail record of one device."""
        path = (
            f"{_WORKSPACES_PATH}/{self._safe_id(workspace_id)}"
            f"/devices/{self._safe_id(device_id)}"
        )
        response = await self._get(path)
        if not isinstance(response, dict) or not isinstance(
            data := response.get("data"), dict
        ):
            self._raise_response_error(f"{path} returned a malformed device")
        return data

    @staticmethod
    def _safe_id(identifier: Any) -> str:
        """Return an id that is safe to use as a URL path segment."""
        if not is_valid_mobility_id(identifier):
            msg = "Invalid Mobility identifier"
            raise UniFiValidationError(msg)
        return identifier

    def _extract_list(
        self,
        response: dict[str, Any] | list[Any] | None,
        path: str,
    ) -> list[dict[str, Any]]:
        """Validate and return a Mobility envelope's list of records."""
        if not isinstance(response, dict):
            self._raise_response_error(f"{path} returned a malformed response envelope")

        data = response.get("data")
        if not isinstance(data, list) or not all(
            isinstance(item, dict) for item in data
        ):
            self._raise_response_error(f"{path} returned malformed data")

        return data

    @staticmethod
    def _raise_response_error(message: str) -> NoReturn:
        """Raise a response error for a successful but malformed payload."""
        raise UniFiResponseError(message, status_code=200)
