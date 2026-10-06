# Copyright (c) 2026 Ruaan Deysel
"""UniFi Carrier Fabric API client."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from custom_components.unifi_insights.api.base import BaseUniFiClient
from custom_components.unifi_insights.api.const import (
    CARRIER_FABRIC_API_BASE_URL,
    DEFAULT_CONNECT_TIMEOUT,
    DEFAULT_TIMEOUT,
)
from custom_components.unifi_insights.api.exceptions import (
    UniFiAuthenticationError,
    UniFiResponseError,
)

from .endpoints import ServicePlansEndpoint, SubscribersEndpoint

if TYPE_CHECKING:
    import aiohttp

    from custom_components.unifi_insights.api.auth import ApiKeyAuth

_LOGGER = logging.getLogger(__name__)


def _extract_api_error_code(response_text: str | None) -> str | None:
    """Extract machine-readable error code from Carrier Fabric response body."""
    if not response_text:
        return None
    try:
        data = json.loads(response_text)
    except (ValueError, TypeError):
        return None

    if isinstance(data, dict):
        error = data.get("error")
        if isinstance(error, dict):
            code = error.get("code")
            if isinstance(code, str) and code:
                return code
        elif isinstance(error, str) and error:
            return error
        code = data.get("code")
        if isinstance(code, str) and code:
            return code
    return None


class UniFiCarrierFabricClient(BaseUniFiClient):
    """
    Async client for the UniFi Carrier Fabric API.

    Uses cloud API key authentication (`X-API-Key`) to communicate with
    https://api.ui.com/v1/carrier.
    """

    def __init__(
        self,
        auth: ApiKeyAuth,
        *,
        base_url: str = CARRIER_FABRIC_API_BASE_URL,
        session: aiohttp.ClientSession | None = None,
        timeout: int = DEFAULT_TIMEOUT,
        connect_timeout: int = DEFAULT_CONNECT_TIMEOUT,
    ) -> None:
        """Initialize the UniFi Carrier Fabric client."""
        super().__init__(
            auth=auth,
            base_url=base_url,
            session=session,
            timeout=timeout,
            connect_timeout=connect_timeout,
        )
        self._subscribers = SubscribersEndpoint(self)
        self._service_plans = ServicePlansEndpoint(self)

    @property
    def subscribers(self) -> SubscribersEndpoint:
        """Access subscriber management endpoints."""
        return self._subscribers

    @property
    def service_plans(self) -> ServicePlansEndpoint:
        """Access service plan endpoints."""
        return self._service_plans

    def _response_log_text(self, response_text: str, *, limit: int) -> str:
        """Keep subscriber and plan data out of transport logs."""
        return "[Carrier Fabric response omitted]"[:limit] if response_text else "empty"

    async def _handle_response(
        self,
        response: aiohttp.ClientResponse,
        *,
        expected_unsupported: bool = False,
        request_path: str | None = None,
    ) -> dict[str, Any] | list[Any] | None:
        """Handle response with error code extraction and privacy-preserving logging."""
        try:
            return await super()._handle_response(
                response,
                expected_unsupported=expected_unsupported,
                request_path=request_path,
            )
        except (UniFiAuthenticationError, UniFiResponseError) as err:
            response_text = getattr(err, "response_body", None)
            if response_text is None:
                response_text = await response.text()
            err.api_error_code = _extract_api_error_code(response_text)
            raise

    async def validate_connection(self) -> bool:
        """
        Validate connection by listing service plans.

        Returns:
            True if connection is valid.

        Raises:
            UniFiAuthenticationError: If authentication fails.
            UniFiConnectionError: If connection fails.

        """
        await self._service_plans.get_all()
        return True
