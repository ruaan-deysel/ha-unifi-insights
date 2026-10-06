# Copyright (c) 2026 Ruaan Deysel
"""Endpoints for UniFi Carrier Fabric API."""

from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ValidationError

from custom_components.unifi_insights.api.const import (
    CARRIER_FABRIC_MAX_PAGE_SIZE,
    CARRIER_FABRIC_MAX_PAGES,
    CARRIER_FABRIC_PATH,
)
from custom_components.unifi_insights.api.exceptions import UniFiResponseError

from .models import ServicePlan, Subscriber

if TYPE_CHECKING:
    from .client import UniFiCarrierFabricClient

_LOGGER = logging.getLogger(__name__)


def _canonical_subscriber_id(subscriber_id: str) -> str:
    """
    Return the canonical text form of a subscriber UUID.

    ``uuid.UUID`` also accepts braces, ``urn:uuid:`` and dash-less hex, so only
    the canonical form is ever placed in a request path.

    Raises:
        ValueError: If ``subscriber_id`` is not a UUID.

    """
    try:
        return str(uuid.UUID(str(subscriber_id)))
    except ValueError as err:
        msg = f"Invalid subscriber ID format (UUID required): {subscriber_id!r}"
        raise ValueError(msg) from err


def _subscriber_path(subscriber_id: str) -> str:
    """Return the request path of one subscriber (validating the id first)."""
    canonical = _canonical_subscriber_id(subscriber_id)
    return f"{CARRIER_FABRIC_PATH}/subscribers/{canonical}"


def _list_envelope(path: str, response: object) -> dict[str, Any]:
    """
    Return a list response, requiring the ``{"data": [...]}`` envelope.

    Raises:
        UniFiResponseError: If the envelope is malformed. A 2xx with a bad shape
            must not look like an empty list: that would publish wrong counts.

    """
    if not isinstance(response, dict):
        msg = f"{path} returned unexpected response"
        raise UniFiResponseError(msg, status_code=200)
    if not isinstance(response.get("data"), list):
        msg = f"{path} returned malformed data"
        raise UniFiResponseError(msg, status_code=200)
    return response


def _object_data(response: object) -> dict[str, Any] | None:
    """Return the record of a single-object response, or None if there is none."""
    if isinstance(response, dict):
        data = response.get("data", response)
        if isinstance(data, dict):
            return data
    return None


def _parse_items[ModelT: BaseModel](
    model: type[ModelT], items: list[Any], label: str
) -> list[ModelT]:
    """Validate list items, skipping malformed ones without logging their content."""
    parsed: list[ModelT] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        try:
            parsed.append(model.model_validate(item))
        except ValidationError:
            _LOGGER.debug("Skipping invalid %s item", label)
    return parsed


class ServicePlansEndpoint:
    """Endpoint for managing Carrier Fabric service plans."""

    def __init__(self, client: UniFiCarrierFabricClient) -> None:
        """Initialize the service plans endpoint."""
        self._client = client

    async def get_all(self) -> list[ServicePlan]:
        """
        List all service plans.

        Returns:
            List of service plans (unpaginated). Malformed items are skipped.

        Raises:
            UniFiResponseError: If the response envelope is invalid.

        """
        path = f"{CARRIER_FABRIC_PATH}/service-plans"
        envelope = _list_envelope(path, await self._client._get(path))
        return _parse_items(ServicePlan, envelope["data"], "service plan")

    async def get(self, plan_id: str) -> ServicePlan:
        """
        Get a specific service plan.

        Args:
            plan_id: The service plan ID.

        Returns:
            The service plan model.

        Raises:
            UniFiNotFoundError: If the service plan is not found.
            UniFiResponseError: If the response envelope is invalid.

        """
        path = f"{CARRIER_FABRIC_PATH}/service-plans/{plan_id}"
        data = _object_data(await self._client._get(path))
        if data is None:
            msg = f"{path} returned unexpected response"
            raise UniFiResponseError(msg, status_code=200)
        return ServicePlan.model_validate(data)


class SubscribersEndpoint:
    """Endpoint for managing Carrier Fabric subscribers."""

    def __init__(self, client: UniFiCarrierFabricClient) -> None:
        """Initialize the subscribers endpoint."""
        self._client = client

    async def get_all(
        self,
        *,
        limit: int | None = None,
        cursor: str | None = None,
        sort: str | None = None,
        plan_id: str | None = None,
        suspended: bool | None = None,
    ) -> list[Subscriber]:
        """
        List subscribers.

        When either ``limit`` or ``cursor`` is explicitly provided, a single
        page of subscribers is fetched and returned.

        When neither is provided, follows ``meta.nextCursor`` while
        ``meta.hasMore`` is true (or while ``nextCursor`` is a non-empty
        string if ``hasMore`` is omitted) up to ``CARRIER_FABRIC_MAX_PAGES``.
        Deduplicates subscribers by ID across pages and skips items failing
        model validation.

        Args:
            limit: Maximum subscribers to return for single-page fetch.
            cursor: Pagination cursor for single-page fetch.
            sort: Sort criteria (e.g. "name", "-name").
            plan_id: Filter by service plan ID.
            suspended: Filter by suspended state.

        Returns:
            List of valid subscribers, deduped by ID.

        Raises:
            ValueError: If limit is not an int in 1..500.
            UniFiResponseError: If the envelope is malformed, a pagination
                cursor is repeated, or the page count exceeds
                ``CARRIER_FABRIC_MAX_PAGES``.

        """
        if limit is not None and (
            type(limit) is not int or not (1 <= limit <= CARRIER_FABRIC_MAX_PAGE_SIZE)
        ):
            msg = (
                f"limit must be an integer between 1 and "
                f"{CARRIER_FABRIC_MAX_PAGE_SIZE}, got {limit}"
            )
            raise ValueError(msg)

        path = f"{CARRIER_FABRIC_PATH}/subscribers"
        base_params: dict[str, Any] = {}
        if sort is not None:
            base_params["sort"] = sort
        if plan_id is not None:
            base_params["planId"] = plan_id
        if suspended is not None:
            base_params["suspended"] = "true" if suspended else "false"

        # First page wins on duplicate ids, in the order the API returned them.
        subscribers: dict[str, Subscriber] = {}

        # Explicit limit or cursor requested: return a single page.
        if limit is not None or cursor is not None:
            params = dict(base_params)
            if limit is not None:
                params["limit"] = limit
            if cursor is not None:
                params["cursor"] = cursor

            envelope = _list_envelope(
                path, await self._client._get(path, params=params or None)
            )
            for sub in _parse_items(Subscriber, envelope["data"], "subscriber"):
                subscribers.setdefault(sub.id, sub)
            return list(subscribers.values())

        # Cursor pagination loop
        seen_cursors: set[str] = set()
        current_cursor: str | None = None

        for _ in range(CARRIER_FABRIC_MAX_PAGES):
            page_params = dict(base_params)
            page_params["limit"] = CARRIER_FABRIC_MAX_PAGE_SIZE
            if current_cursor is not None:
                page_params["cursor"] = current_cursor

            envelope = _list_envelope(
                path, await self._client._get(path, params=page_params)
            )
            for sub in _parse_items(Subscriber, envelope["data"], "subscriber"):
                subscribers.setdefault(sub.id, sub)

            meta = envelope.get("meta")
            if not isinstance(meta, dict):
                msg = f"{path} returned malformed meta"
                raise UniFiResponseError(msg, status_code=200)

            next_cursor = meta.get("nextCursor")
            has_more = meta.get("hasMore")

            if has_more is True and (
                not next_cursor or not isinstance(next_cursor, str)
            ):
                msg = f"{path} indicated hasMore=True but nextCursor is missing"
                raise UniFiResponseError(msg, status_code=200)

            should_continue = (
                has_more is True
                if has_more is not None
                else bool(next_cursor and isinstance(next_cursor, str))
            )
            if not should_continue or not next_cursor:
                return list(subscribers.values())

            if next_cursor in seen_cursors:
                msg = f"{path} repeated pagination cursor"
                raise UniFiResponseError(msg, status_code=200)

            seen_cursors.add(next_cursor)
            current_cursor = next_cursor

        msg = f"{path} exceeded maximum pages ({CARRIER_FABRIC_MAX_PAGES})"
        raise UniFiResponseError(msg, status_code=200)

    async def get(self, subscriber_id: str) -> Subscriber:
        """
        Get a specific subscriber.

        Args:
            subscriber_id: The subscriber ID.

        Returns:
            The subscriber model.

        Raises:
            ValueError: If the subscriber ID is not a valid UUID.
            UniFiNotFoundError: If the subscriber is not found.
            UniFiResponseError: If the response envelope is invalid.

        """
        path = _subscriber_path(subscriber_id)
        data = _object_data(await self._client._get(path))
        if data is None:
            msg = f"{path} returned unexpected response"
            raise UniFiResponseError(msg, status_code=200)
        return Subscriber.model_validate(data)

    async def suspend(
        self, subscriber_id: str, reason: str | None = None
    ) -> Subscriber | None:
        """
        Suspend a subscriber.

        Any 2xx response means the change was applied, so a response body that
        cannot be read as a subscriber is not an error.

        Args:
            subscriber_id: The subscriber ID to suspend.
            reason: Optional explanation (max 1024 characters).

        Returns:
            The updated subscriber model, or None if the response carried none.

        Raises:
            ValueError: If the subscriber ID is not a valid UUID.
            UniFiError: If the API rejects the request (non-2xx).

        """
        path = f"{_subscriber_path(subscriber_id)}/suspend"
        json_data = {"reason": reason} if reason is not None else None
        response = await self._client._post(path, json_data=json_data)
        return self._write_result(path, response)

    async def resume(self, subscriber_id: str) -> Subscriber | None:
        """
        Resume a suspended subscriber.

        Any 2xx response means the change was applied, so a response body that
        cannot be read as a subscriber is not an error.

        Args:
            subscriber_id: The subscriber ID to resume.

        Returns:
            The updated subscriber model, or None if the response carried none.

        Raises:
            ValueError: If the subscriber ID is not a valid UUID.
            UniFiError: If the API rejects the request (non-2xx).

        """
        path = f"{_subscriber_path(subscriber_id)}/resume"
        response = await self._client._post(path)
        return self._write_result(path, response)

    @staticmethod
    def _write_result(path: str, response: object) -> Subscriber | None:
        """Parse the body of a successful write without ever failing it."""
        try:
            return Subscriber.model_validate(_object_data(response))
        except ValidationError:
            _LOGGER.debug("%s succeeded without a readable subscriber body", path)
            return None
