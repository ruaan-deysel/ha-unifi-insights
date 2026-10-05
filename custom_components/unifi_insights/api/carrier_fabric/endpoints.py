# Copyright 2026 UniFi Insights contributors
"""Endpoints for UniFi Carrier Fabric API."""

from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING, Any

from pydantic import ValidationError

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


def _validate_subscriber_uuid(subscriber_id: str) -> None:
    """Validate that subscriber_id conforms to UUID format."""
    try:
        uuid.UUID(str(subscriber_id))
    except (ValueError, TypeError, AttributeError) as err:
        msg = f"Invalid subscriber ID format (UUID required): {subscriber_id!r}"
        raise ValueError(msg) from err


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
        response = await self._client._get(path)
        if not isinstance(response, dict):
            msg = f"{path} returned unexpected response"
            raise UniFiResponseError(msg, status_code=200)

        data = response.get("data")
        if not isinstance(data, list):
            msg = f"{path} returned malformed data"
            raise UniFiResponseError(msg, status_code=200)

        plans: list[ServicePlan] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            try:
                plans.append(ServicePlan.model_validate(item))
            except ValidationError:
                _LOGGER.debug("Skipping invalid service plan item")
        return plans

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
        response = await self._client._get(path)
        if isinstance(response, dict):
            data = response.get("data", response)
            if isinstance(data, dict):
                return ServicePlan.model_validate(data)
        msg = f"{path} returned unexpected response"
        raise UniFiResponseError(msg, status_code=200)


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

        # Explicit limit or cursor requested: return a single page.
        if limit is not None or cursor is not None:
            params = dict(base_params)
            if limit is not None:
                params["limit"] = limit
            if cursor is not None:
                params["cursor"] = cursor

            response = await self._client._get(path, params=params or None)
            if not isinstance(response, dict):
                msg = f"{path} returned unexpected response"
                raise UniFiResponseError(msg, status_code=200)
            data = response.get("data")
            if not isinstance(data, list):
                msg = f"{path} returned malformed data"
                raise UniFiResponseError(msg, status_code=200)

            seen_ids: set[str] = set()
            single_page_items: list[Subscriber] = []
            for item in data:
                if not isinstance(item, dict):
                    continue
                try:
                    sub = Subscriber.model_validate(item)
                except ValidationError:
                    _LOGGER.debug("Skipping invalid subscriber item")
                    continue
                if sub.id not in seen_ids:
                    seen_ids.add(sub.id)
                    single_page_items.append(sub)
            return single_page_items

        # Cursor pagination loop
        seen_ids = set()
        seen_cursors: set[str] = set()
        subscribers: list[Subscriber] = []
        current_cursor: str | None = None

        for _ in range(CARRIER_FABRIC_MAX_PAGES):
            page_params = dict(base_params)
            page_params["limit"] = CARRIER_FABRIC_MAX_PAGE_SIZE
            if current_cursor is not None:
                page_params["cursor"] = current_cursor

            response = await self._client._get(path, params=page_params)
            if not isinstance(response, dict):
                msg = f"{path} returned unexpected response"
                raise UniFiResponseError(msg, status_code=200)

            data = response.get("data")
            if not isinstance(data, list):
                msg = f"{path} returned malformed data"
                raise UniFiResponseError(msg, status_code=200)

            for item in data:
                if not isinstance(item, dict):
                    continue
                try:
                    sub = Subscriber.model_validate(item)
                except ValidationError:
                    _LOGGER.debug("Skipping invalid subscriber item")
                    continue
                if sub.id not in seen_ids:
                    seen_ids.add(sub.id)
                    subscribers.append(sub)

            meta = response.get("meta")
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
                return subscribers

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
        _validate_subscriber_uuid(subscriber_id)
        path = f"{CARRIER_FABRIC_PATH}/subscribers/{subscriber_id}"
        response = await self._client._get(path)
        if isinstance(response, dict):
            data = response.get("data", response)
            if isinstance(data, dict):
                return Subscriber.model_validate(data)
        msg = f"{path} returned unexpected response"
        raise UniFiResponseError(msg, status_code=200)

    async def suspend(
        self, subscriber_id: str, reason: str | None = None
    ) -> Subscriber:
        """
        Suspend a subscriber.

        Args:
            subscriber_id: The subscriber ID to suspend.
            reason: Optional explanation (max 1024 characters).

        Returns:
            The updated subscriber model.

        Raises:
            ValueError: If the subscriber ID is not a valid UUID.
            UniFiResponseError: If the operation fails or response is invalid.

        """
        _validate_subscriber_uuid(subscriber_id)
        path = f"{CARRIER_FABRIC_PATH}/subscribers/{subscriber_id}/suspend"
        json_data = {"reason": reason} if reason is not None else None
        response = await self._client._post(path, json_data=json_data)
        if isinstance(response, dict):
            data = response.get("data", response)
            if isinstance(data, dict):
                return Subscriber.model_validate(data)
        msg = f"{path} returned unexpected response"
        raise UniFiResponseError(msg, status_code=200)

    async def resume(self, subscriber_id: str) -> Subscriber:
        """
        Resume a suspended subscriber.

        Args:
            subscriber_id: The subscriber ID to resume.

        Returns:
            The updated subscriber model.

        Raises:
            ValueError: If the subscriber ID is not a valid UUID.
            UniFiResponseError: If the operation fails or response is invalid.

        """
        _validate_subscriber_uuid(subscriber_id)
        path = f"{CARRIER_FABRIC_PATH}/subscribers/{subscriber_id}/resume"
        response = await self._client._post(path)
        if isinstance(response, dict):
            data = response.get("data", response)
            if isinstance(data, dict):
                return Subscriber.model_validate(data)
        msg = f"{path} returned unexpected response"
        raise UniFiResponseError(msg, status_code=200)
