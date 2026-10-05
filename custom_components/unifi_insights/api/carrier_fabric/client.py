# Copyright 2026 UniFi Insights contributors
"""UniFi Carrier Fabric API client."""

from __future__ import annotations

import json
import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Any, NoReturn

from custom_components.unifi_insights.api.base import BaseUniFiClient, parse_retry_after
from custom_components.unifi_insights.api.const import (
    CARRIER_FABRIC_API_BASE_URL,
    DEFAULT_CONNECT_TIMEOUT,
    DEFAULT_TIMEOUT,
)
from custom_components.unifi_insights.api.exceptions import (
    UniFiAuthenticationError,
    UniFiNotFoundError,
    UniFiRateLimitError,
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

    @staticmethod
    def _raise_auth_error(
        msg: str, status: int, api_error_code: str | None
    ) -> NoReturn:
        """Raise authentication error without triggering linter issues."""
        raise UniFiAuthenticationError(
            msg, status_code=status, api_error_code=api_error_code
        )

    @staticmethod
    def _raise_not_found(
        msg: str, status: int, response_body: str, api_error_code: str | None
    ) -> NoReturn:
        """Raise not found error without triggering linter issues."""
        raise UniFiNotFoundError(
            msg,
            status_code=status,
            response_body=response_body,
            api_error_code=api_error_code,
        )

    @staticmethod
    def _raise_rate_limit(
        msg: str,
        status: int,
        response_body: str,
        headers: Any,
        api_error_code: str | None,
    ) -> NoReturn:
        """Raise rate limit error without triggering linter issues."""
        raise UniFiRateLimitError(
            msg,
            status_code=status,
            response_body=response_body,
            retry_after=parse_retry_after(headers),
            api_error_code=api_error_code,
        )

    @staticmethod
    def _raise_response_error(
        msg: str,
        status: int,
        response_body: str,
        api_error_code: str | None,
    ) -> NoReturn:
        """Raise response error without triggering linter issues."""
        raise UniFiResponseError(
            msg,
            status_code=status,
            response_body=response_body,
            api_error_code=api_error_code,
        )

    async def _handle_response(
        self,
        response: aiohttp.ClientResponse,
        *,
        expected_unsupported: bool = False,
        request_path: str | None = None,
    ) -> dict[str, Any] | list[Any] | None:
        """Handle response with error code extraction and privacy-preserving logging."""
        status = response.status
        if status >= HTTPStatus.BAD_REQUEST:
            response_text = await response.text()
            if _LOGGER.isEnabledFor(logging.DEBUG):
                redacted_body = self._response_log_text(response_text, limit=500)
                _LOGGER.debug("Response status: %s, body: %s", status, redacted_body)

            api_error_code = _extract_api_error_code(response_text)

            if status == HTTPStatus.UNAUTHORIZED:
                msg = "Authentication failed. Check your API key."
                self._raise_auth_error(msg, status, api_error_code)

            if status == HTTPStatus.FORBIDDEN:
                msg = "Access forbidden. Check your API key permissions."
                self._raise_auth_error(msg, status, api_error_code)

            if status == HTTPStatus.NOT_FOUND:
                msg = "Resource not found"
                self._raise_not_found(msg, status, response_text, api_error_code)

            if status == HTTPStatus.TOO_MANY_REQUESTS:
                msg = "Rate limited by API"
                self._raise_rate_limit(
                    msg, status, response_text, response.headers, api_error_code
                )

            msg = f"API error (status {status})"
            self._raise_response_error(msg, status, response_text, api_error_code)

        return await super()._handle_response(
            response,
            expected_unsupported=expected_unsupported,
            request_path=request_path,
        )

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
