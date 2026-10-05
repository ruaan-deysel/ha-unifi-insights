"""Exceptions for the UniFi Official API library."""

from __future__ import annotations

from typing import Any


class UniFiError(Exception):
    """Base exception for all UniFi API errors."""

    def __init__(self, message: str, *args: Any) -> None:
        """
        Initialize the exception.

        Args:
            message: The error message.
            *args: Additional arguments.

        """
        super().__init__(message, *args)
        self.message = message


class UniFiAuthenticationError(UniFiError):
    """Raised when authentication fails."""

    def __init__(
        self,
        message: str,
        *args: Any,
        status_code: int | None = None,
        api_error_code: str | None = None,
    ) -> None:
        """
        Initialize the exception.

        Args:
            message: The error message.
            *args: Additional arguments.
            status_code: The HTTP status code (401 or 403) if known.
            api_error_code: Machine-readable API error code if available.

        """
        super().__init__(message, *args)
        self.status_code = status_code
        self.api_error_code = api_error_code


class UniFiConnectionError(UniFiError):
    """Raised when connection to the UniFi API fails."""


class UniFiResponseError(UniFiError):
    """Raised when the API returns an error response."""

    def __init__(
        self,
        message: str,
        status_code: int,
        response_body: str | None = None,
        *,
        api_error_code: str | None = None,
    ) -> None:
        """
        Initialize the exception.

        Args:
            message: The error message.
            status_code: The HTTP status code.
            response_body: The response body if available.
            api_error_code: Machine-readable API error code if available.

        """
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body
        self.api_error_code = api_error_code

    def __str__(self) -> str:
        """Return safe string representation with status only."""
        return f"{self.__class__.__name__}(status={self.status_code})"


class UniFiNotFoundError(UniFiResponseError):
    """Raised when a resource is not found (404)."""


class UniFiRateLimitError(UniFiResponseError):
    """Raised when rate limited by the API (429)."""

    def __init__(
        self,
        message: str,
        status_code: int,
        response_body: str | None = None,
        retry_after: int | None = None,
        *,
        api_error_code: str | None = None,
    ) -> None:
        """
        Initialize the exception.

        Args:
            message: The error message.
            status_code: The HTTP status code.
            response_body: The response body if available.
            retry_after: Seconds to wait before retrying.
            api_error_code: Machine-readable API error code if available.

        """
        super().__init__(
            message,
            status_code,
            response_body,
            api_error_code=api_error_code,
        )
        self.retry_after = retry_after


class UniFiValidationError(UniFiError):
    """Raised when request validation fails."""


class UniFiTimeoutError(UniFiError):
    """Raised when a request times out."""
