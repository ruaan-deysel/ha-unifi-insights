"""Base async client for UniFi APIs."""

from __future__ import annotations

import asyncio
import logging
import math
import re
import time
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from http import HTTPStatus
from types import TracebackType
from typing import TYPE_CHECKING, Any, ClassVar, Self, TypeVar

import aiohttp
from yarl import URL

from .auth import ApiKeyAuth, LocalAuth
from .const import (
    CONTENT_TYPE_JSON,
    DEFAULT_CONNECT_TIMEOUT,
    DEFAULT_RATE_LIMIT_RETRY_AFTER,
    DEFAULT_TIMEOUT,
    HEADER_ACCEPT,
    HEADER_CONTENT_TYPE,
    HEADER_USER_AGENT,
    RATE_LIMIT_MAX_RETRY_AFTER,
    RATE_LIMIT_WINDOW_MARGIN,
    USER_AGENT,
)
from .exceptions import (
    UniFiAuthenticationError,
    UniFiConnectionError,
    UniFiNotFoundError,
    UniFiRateLimitError,
    UniFiResponseError,
    UniFiTimeoutError,
)

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Mapping

_LOGGER = logging.getLogger(__name__)

_T = TypeVar("_T")

_SENSITIVE_KEYS_RE = re.compile(
    r'"(?:password|psk|passphrase|token|apiKey|api_key|secret|credential|'
    r'x-api-key|authorization|code|voucher|fingerprint)"\s*:\s*"[^"]*"',
    re.IGNORECASE,
)


def _redact(text: str) -> str:
    """Replace sensitive JSON field values with a redaction placeholder."""
    return _SENSITIVE_KEYS_RE.sub(
        lambda m: m.group(0).rsplit(":", 1)[0] + ': "**REDACTED**"',
        text,
    )


def _retry_after_seconds(value: str | None) -> int:
    """Parse a Retry-After delay or HTTP date, with a safe fallback."""
    if not value:
        return DEFAULT_RATE_LIMIT_RETRY_AFTER
    try:
        seconds = float(value)
    except ValueError:
        try:
            deadline = parsedate_to_datetime(value)
        except (TypeError, ValueError):
            return DEFAULT_RATE_LIMIT_RETRY_AFTER
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=UTC)
        seconds = (deadline - datetime.now(UTC)).total_seconds()
    if not math.isfinite(seconds):
        return DEFAULT_RATE_LIMIT_RETRY_AFTER
    return max(0, math.ceil(seconds))


def parse_retry_after(headers: Mapping[str, str]) -> int:
    """
    Return a 429 response's Retry-After in seconds.

    Parses integer/fractional seconds or HTTP dates (RFC 9110) and falls back
    to DEFAULT_RATE_LIMIT_RETRY_AFTER when the header is missing or invalid.
    """
    return _retry_after_seconds(headers.get("Retry-After"))


class RequestRateLimiter:
    """
    Space out requests so a client never exceeds a server-side rate limit.

    Allows at most `max_requests` request starts in any rolling `window`
    seconds. A rolling window is at least as strict as the server's fixed
    one, so staying inside it can never trip a fixed-window limit. Waiters
    are served in arrival order.
    """

    def __init__(self, max_requests: int, window: float) -> None:
        """Initialize the limiter."""
        self._max_requests = max_requests
        self._window = window
        self._starts: list[float] = []
        self._blocked_until = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Wait until another request may start, then record it."""
        async with self._lock:
            while True:
                now = time.monotonic()
                cutoff = now - self._window
                self._starts = [t for t in self._starts if t > cutoff]
                if now < self._blocked_until:
                    wait = self._blocked_until - now
                elif len(self._starts) < self._max_requests:
                    self._starts.append(now)
                    return
                else:
                    wait = self._starts[0] - cutoff
                await asyncio.sleep(wait)

    def defer(self, seconds: float) -> None:
        """Hold every request for `seconds`, e.g. after a server 429."""
        self._blocked_until = max(self._blocked_until, time.monotonic() + seconds)


class BaseUniFiClient(ABC):
    """
    Base async client for UniFi API interactions.

    This class provides common functionality for both Network and Protect APIs.
    """

    # (max requests, window seconds) the server enforces, or None if the
    # API is not rate limited. Subclasses set this; see `_throttle`.
    RATE_LIMIT: ClassVar[tuple[int, float] | None] = None

    def __init__(
        self,
        auth: ApiKeyAuth | LocalAuth,
        base_url: str,
        *,
        session: aiohttp.ClientSession | None = None,
        timeout: int = DEFAULT_TIMEOUT,
        connect_timeout: int = DEFAULT_CONNECT_TIMEOUT,
    ) -> None:
        """
        Initialize the base client.

        Args:
            auth: Authentication configuration.
            base_url: Base URL for the API.
            session: Optional aiohttp session to reuse.
            timeout: Request timeout in seconds.
            connect_timeout: Connection timeout in seconds.

        """
        self._auth = auth
        self._base_url = URL(base_url)
        self._session = session
        self._owns_session = session is None
        self._timeout = aiohttp.ClientTimeout(
            total=timeout,
            connect=connect_timeout,
        )
        self._closed = False
        self._rate_limiter: RequestRateLimiter | None = None
        if self.RATE_LIMIT is not None:
            max_requests, window = self.RATE_LIMIT
            self._rate_limiter = RequestRateLimiter(
                max_requests, window + RATE_LIMIT_WINDOW_MARGIN
            )

    @property
    def base_url(self) -> URL:
        """Return the base URL."""
        return self._base_url

    @property
    def closed(self) -> bool:
        """Return whether the client is closed."""
        return self._closed

    async def _ensure_session(self) -> aiohttp.ClientSession:
        """
        Ensure an aiohttp session exists.

        Returns:
            The aiohttp session.

        """
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(
                ssl=self._get_ssl_context(),
            )
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=self._timeout,
            )
            self._owns_session = True
        return self._session

    def _get_ssl_context(self) -> bool:
        """
        Get SSL context based on auth configuration.

        Returns:
            SSL verification setting.

        """
        if isinstance(self._auth, LocalAuth):
            return self._auth.verify_ssl
        return True

    def _get_headers(self) -> dict[str, str]:
        """
        Get default headers for requests.

        Returns:
            Dictionary of headers.

        """
        headers = {
            HEADER_USER_AGENT: USER_AGENT,
            HEADER_CONTENT_TYPE: CONTENT_TYPE_JSON,
            HEADER_ACCEPT: CONTENT_TYPE_JSON,
        }
        headers.update(self._auth.get_headers())
        return headers

    def _build_url(self, path: str) -> URL:
        """
        Build full URL from path.

        Args:
            path: API path (should start with /).

        Returns:
            Full URL.

        """
        return self._base_url / path.lstrip("/")

    async def _throttle(self) -> None:
        """Wait for the client's rate limiter, if the API has one."""
        if self._rate_limiter is not None:
            await self._rate_limiter.acquire()

    def _defer_after_rate_limit(self, retry_after: float | None) -> None:
        """
        Hold all of this client's requests after the server sent a 429.

        Capped at RATE_LIMIT_MAX_RETRY_AFTER: a missing Retry-After defaults
        to a minute, which must not freeze every request on the client.
        """
        if self._rate_limiter is not None:
            if retry_after is None:
                retry_after = RATE_LIMIT_MAX_RETRY_AFTER
            self._rate_limiter.defer(min(retry_after, RATE_LIMIT_MAX_RETRY_AFTER))

    async def _retry_once_after_rate_limit(
        self,
        send: Callable[[], Awaitable[_T]],
        description: str,
    ) -> _T:
        """
        Run `send`, retrying it once after a short-lived 429.

        Rate-limited APIs are paced by `_throttle`, so a 429 means another
        consumer of the same API key drained the allowance. A rejected
        request was not processed, so retrying it once after the server's
        own Retry-After is safe for every method. Every 429, including one
        on the retry, holds the client's other requests for the (capped)
        Retry-After, so they do not run into the allowance the server has
        just refused. A long or missing Retry-After is raised to the caller
        without a retry.

        Raises:
            UniFiRateLimitError: If still rate limited after the retry, or the
                server asks for a wait longer than RATE_LIMIT_MAX_RETRY_AFTER.

        """
        if self._rate_limiter is None:
            return await send()
        try:
            return await send()
        except UniFiRateLimitError as err:
            retry_after = err.retry_after
            self._defer_after_rate_limit(retry_after)
            if retry_after is None or retry_after > RATE_LIMIT_MAX_RETRY_AFTER:
                raise
            _LOGGER.debug(
                "Rate limited on %s, retrying in %ss", description, retry_after
            )
        try:
            return await send()
        except UniFiRateLimitError as err:
            self._defer_after_rate_limit(err.retry_after)
            raise

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        expected_unsupported: bool = False,
    ) -> dict[str, Any] | list[Any] | None:
        """
        Make an HTTP request, retrying once after a short-lived 429.

        See `_retry_once_after_rate_limit`.

        Raises:
            UniFiRateLimitError: If still rate limited after the retry, or the
                server asks for a wait longer than RATE_LIMIT_MAX_RETRY_AFTER.

        """
        return await self._retry_once_after_rate_limit(
            lambda: self._request_once(
                method,
                path,
                params=params,
                json_data=json_data,
                headers=headers,
                expected_unsupported=expected_unsupported,
            ),
            f"{method} {path}",
        )

    async def _request_once(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        expected_unsupported: bool = False,
    ) -> dict[str, Any] | list[Any] | None:
        """
        Make a single HTTP request to the API.

        Args:
            method: HTTP method.
            path: API path.
            params: Query parameters.
            json_data: JSON body data.
            headers: Additional headers.
            expected_unsupported: Whether a non-JSON 2xx response is an
                expected unsupported-endpoint signal.

        Returns:
            Response data as dict, list, or None.

        Raises:
            UniFiAuthenticationError: If authentication fails.
            UniFiConnectionError: If connection fails.
            UniFiNotFoundError: If resource not found.
            UniFiRateLimitError: If rate limited.
            UniFiResponseError: If API returns an error.
            UniFiTimeoutError: If request times out.

        """
        await self._throttle()
        session = await self._ensure_session()
        url = self._build_url(path)

        request_headers = self._get_headers()
        if headers:
            request_headers.update(headers)

        _LOGGER.debug(
            "Making %s request to %s",
            method,
            url,
        )

        try:
            async with session.request(
                method,
                url,
                params=params,
                json=json_data,
                headers=request_headers,
            ) as response:
                return await self._handle_response(
                    response,
                    expected_unsupported=expected_unsupported,
                    request_path=path,
                )

        except aiohttp.ClientConnectorError as err:
            msg = f"Failed to connect to {url}: {err}"
            raise UniFiConnectionError(msg) from err
        except TimeoutError as err:
            msg = f"Request to {url} timed out"
            raise UniFiTimeoutError(msg) from err
        except aiohttp.ClientError as err:
            msg = f"Request to {url} failed: {err}"
            raise UniFiConnectionError(msg) from err

    def _response_log_text(self, response_text: str, *, limit: int) -> str:
        """Return a bounded, credential-redacted response excerpt for logs."""
        return _redact(response_text)[:limit] if response_text else "empty"

    async def _handle_response(
        self,
        response: aiohttp.ClientResponse,
        *,
        expected_unsupported: bool = False,
        request_path: str | None = None,
    ) -> dict[str, Any] | list[Any] | None:
        """
        Handle API response.

        Args:
            response: The aiohttp response.
            expected_unsupported: Log unredirected non-JSON 2xx responses at
                DEBUG as expected unsupported-endpoint signals.
            request_path: Original request path before any redirect.

        Returns:
            Response data.

        Raises:
            UniFiAuthenticationError: If authentication fails.
            UniFiNotFoundError: If resource not found.
            UniFiRateLimitError: If rate limited.
            UniFiResponseError: If API returns an error.

        """
        status = response.status
        response_text = await response.text()

        if _LOGGER.isEnabledFor(logging.DEBUG):
            redacted_body = self._response_log_text(response_text, limit=500)
            _LOGGER.debug(
                "Response status: %s, body: %s",
                status,
                redacted_body,
            )

        if status == HTTPStatus.UNAUTHORIZED:
            raise UniFiAuthenticationError(
                "Authentication failed. Check your API key.", status_code=status
            )

        if status == HTTPStatus.FORBIDDEN:
            raise UniFiAuthenticationError(
                "Access forbidden. Check your API key permissions.",
                status_code=status,
            )

        if status == HTTPStatus.NOT_FOUND:
            raise UniFiNotFoundError(
                "Resource not found",
                status_code=status,
                response_body=response_text,
            )

        if status == HTTPStatus.TOO_MANY_REQUESTS:
            raise UniFiRateLimitError(
                "Rate limited by API",
                status_code=status,
                response_body=response_text,
                retry_after=parse_retry_after(response.headers),
            )

        if status >= HTTPStatus.BAD_REQUEST:
            message = f"API error (status {status})"
            raise UniFiResponseError(
                message,
                status_code=status,
                response_body=response_text,
            )

        if not response_text:
            return None

        try:
            data: dict[str, Any] | list[Any] = await response.json()
            return data
        except (ValueError, aiohttp.ContentTypeError) as err:
            # A 2xx status with a non-JSON body (e.g. an HTML login page from
            # a proxy/console that considers the request unauthenticated) is
            # not a successful empty response - treating it as one let this
            # go completely unnoticed for 47h in production: no exception
            # ever reached the coordinator, so `last_update_success` stayed
            # True and entities kept serving stale cached data indefinitely
            # instead of surfacing as unavailable and letting the
            # coordinator's normal retry/backoff take over.
            redacted_response = self._response_log_text(response_text, limit=200)
            expected_path = (
                self._build_url(request_path).path
                if request_path is not None
                else response.url.path
            )
            history = getattr(response, "history", ())
            is_unredirected = isinstance(history, (tuple, list)) and len(history) == 0
            if (
                expected_unsupported
                and is_unredirected
                and response.url.path == expected_path
            ):
                _LOGGER.debug(
                    "Expected unsupported-endpoint non-JSON response for %s %s: %s",
                    response.method,
                    response.url.path,
                    redacted_response,
                )
            else:
                # Log the request path: without it this warning names only the
                # body, so a console returning an HTML page on one of several
                # polled endpoints cannot be attributed to the endpoint that
                # actually failed. `url.path` deliberately omits the query
                # string, which can carry credentials.
                _LOGGER.warning(
                    "Response is not JSON for %s %s: %s",
                    response.method,
                    response.url.path,
                    redacted_response,
                )
            msg = f"API returned non-JSON response (status {status})"
            raise UniFiResponseError(
                msg,
                status_code=status,
                response_body=response_text,
            ) from err

    async def _get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        expected_unsupported: bool = False,
    ) -> dict[str, Any] | list[Any] | None:
        """
        Make a GET request.

        Args:
            path: API path.
            params: Query parameters.
            expected_unsupported: Whether a non-JSON 2xx response is an
                expected unsupported-endpoint signal.

        Returns:
            Response data.

        """
        return await self._request(
            "GET",
            path,
            params=params,
            expected_unsupported=expected_unsupported,
        )

    async def _post(
        self,
        path: str,
        *,
        json_data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        expected_unsupported: bool = False,
    ) -> dict[str, Any] | list[Any] | None:
        """
        Make a POST request.

        Args:
            path: API path.
            json_data: JSON body data.
            params: Query parameters.
            expected_unsupported: Whether a non-JSON 2xx response is an
                expected unsupported-endpoint signal.

        Returns:
            Response data.

        """
        return await self._request(
            "POST",
            path,
            json_data=json_data,
            params=params,
            expected_unsupported=expected_unsupported,
        )

    async def _put(
        self,
        path: str,
        *,
        json_data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any] | None:
        """
        Make a PUT request.

        Args:
            path: API path.
            json_data: JSON body data.
            params: Query parameters.

        Returns:
            Response data.

        """
        return await self._request("PUT", path, json_data=json_data, params=params)

    async def _patch(
        self,
        path: str,
        *,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any] | None:
        """
        Make a PATCH request.

        Args:
            path: API path.
            json_data: JSON body data.

        Returns:
            Response data.

        """
        return await self._request("PATCH", path, json_data=json_data)

    async def _delete(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any] | None:
        """
        Make a DELETE request.

        Args:
            path: API path.
            params: Query parameters.

        Returns:
            Response data.

        """
        return await self._request("DELETE", path, params=params)

    @abstractmethod
    async def validate_connection(self) -> bool:
        """
        Validate the connection to the API.

        Returns:
            True if connection is valid.

        """

    async def close(self) -> None:
        """Close the client session."""
        if self._session and self._owns_session and not self._session.closed:
            await self._session.close()
        self._closed = True

    async def __aenter__(self) -> Self:
        """Enter async context manager."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit async context manager."""
        await self.close()
