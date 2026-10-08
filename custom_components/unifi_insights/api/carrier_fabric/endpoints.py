# Copyright (c) 2026 Ruaan Deysel
"""Endpoints for UniFi Carrier Fabric API."""

from __future__ import annotations

import enum
import logging
import uuid
from typing import TYPE_CHECKING, Any, Final

from pydantic import BaseModel, ValidationError

from custom_components.unifi_insights.api.const import (
    CARRIER_FABRIC_MAX_PAGE_SIZE,
    CARRIER_FABRIC_MAX_PAGES,
    CARRIER_FABRIC_PATH,
)
from custom_components.unifi_insights.api.exceptions import UniFiResponseError

from .models import HostLinkResponse, ServicePlan, Subscriber

if TYPE_CHECKING:
    from .client import UniFiCarrierFabricClient

_LOGGER = logging.getLogger(__name__)

# attachSubscriberHost limits hostId to 128 characters.
_HOST_ID_MAX_LENGTH: Final = 128


class _Unset(enum.Enum):
    """Default for update fields, so an omitted field differs from None."""

    TOKEN = enum.auto()


_UNSET: Final = _Unset.TOKEN


def _canonical_uuid(value: str, label: str) -> str:
    """
    Return the canonical text form of a UUID.

    ``uuid.UUID`` also accepts braces, ``urn:uuid:`` and dash-less hex, so only
    the canonical form is ever sent to the API.

    Raises:
        ValueError: If ``value`` is not a UUID.

    """
    try:
        return str(uuid.UUID(str(value)))
    except ValueError as err:
        msg = f"Invalid {label} format (UUID required): {value!r}"
        raise ValueError(msg) from err


def _canonical_subscriber_id(subscriber_id: str) -> str:
    """Return the canonical text form of a subscriber UUID."""
    return _canonical_uuid(subscriber_id, "subscriber ID")


def _checked_host_id(host_id: str) -> str:
    """
    Return ``host_id`` unchanged if it can be a gateway host ID.

    Raises:
        ValueError: If ``host_id`` is not a non-blank string of at most 128
            characters.

    """
    if (
        not isinstance(host_id, str)
        or not host_id.strip()
        or len(host_id) > _HOST_ID_MAX_LENGTH
    ):
        msg = f"Invalid host ID (1-{_HOST_ID_MAX_LENGTH} characters required)"
        raise ValueError(msg)
    return host_id


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


def _write_result[ModelT: BaseModel](
    model: type[ModelT], path: str, payload: object, label: str
) -> ModelT | None:
    """
    Parse the body of a successful write without ever failing it.

    Any 2xx means the change was applied, so a body that cannot be read as
    ``model`` returns None. Only the path is logged, never field values.
    """
    try:
        return model.model_validate(payload)
    except ValidationError:
        _LOGGER.debug("%s succeeded without a readable %s body", path, label)
        return None


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
        return self._subscriber_result(path, response)

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
        return self._subscriber_result(path, response)

    async def create(
        self,
        *,
        subscriber_number: str,
        name: str | None = None,
        email: str | None = None,
        notes: str | None = None,
        service_address: str | None = None,
        plan_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Subscriber | None:
        """
        Create a subscriber.

        The API does not deduplicate: every successful call creates a new
        subscriber. A 2xx with an empty body or one that is not a subscriber
        is therefore still success, so the caller is not led to retry. If the
        call raises after the request may have been sent (a timeout, or a
        non-JSON 2xx), look for ``subscriber_number`` in the subscriber list
        before retrying, or the retry may create a duplicate.

        Args:
            subscriber_number: The operator's external reference (1-32
                characters).
            name: Optional display name.
            email: Optional email address.
            notes: Optional free-text notes.
            service_address: Optional free-text service address.
            plan_id: Optional service plan to assign (UUID).
            metadata: Optional free-form key/value metadata.

        Returns:
            The created subscriber, or None if the response carried none.

        Raises:
            ValueError: If ``plan_id`` is not a valid UUID.
            UniFiError: If the API rejects the request (non-2xx).

        """
        path = f"{CARRIER_FABRIC_PATH}/subscribers"
        optional: dict[str, Any] = {
            "name": name,
            "email": email,
            "notes": notes,
            "serviceAddress": service_address,
            "planId": None if plan_id is None else _canonical_uuid(plan_id, "plan ID"),
            "metadata": metadata,
        }
        json_data: dict[str, Any] = {"subscriberNumber": subscriber_number}
        json_data.update({k: v for k, v in optional.items() if v is not None})
        response = await self._client._post(path, json_data=json_data)
        return self._subscriber_result(path, response)

    async def update(
        self,
        subscriber_id: str,
        *,
        subscriber_number: str | _Unset = _UNSET,
        name: str | _Unset | None = _UNSET,
        email: str | _Unset | None = _UNSET,
        notes: str | _Unset | None = _UNSET,
        service_address: str | _Unset | None = _UNSET,
        plan_id: str | _Unset | None = _UNSET,
        metadata: dict[str, Any] | _Unset = _UNSET,
    ) -> Subscriber | None:
        """
        Update a subscriber.

        Only the fields passed are sent, so the others stay unchanged. None
        clears ``name``, ``email``, ``notes``, ``service_address`` or
        ``plan_id``. ``subscriber_number`` cannot be cleared, and
        ``metadata`` replaces the whole document (pass ``{}`` to empty it).

        Args:
            subscriber_id: The subscriber ID to update.
            subscriber_number: New external reference (1-32 characters).
            name: New display name, or None to clear it.
            email: New email address, or None to clear it.
            notes: New notes, or None to clear them.
            service_address: New service address, or None to clear it.
            plan_id: New service plan (UUID), or None to clear it.
            metadata: New metadata document.

        Returns:
            The updated subscriber, or None if the response carried none.

        Raises:
            ValueError: If the subscriber ID or ``plan_id`` is not a valid
                UUID, or no field is passed.
            UniFiError: If the API rejects the request (non-2xx).

        """
        path = _subscriber_path(subscriber_id)
        if plan_id is not None and plan_id is not _UNSET:
            plan_id = _canonical_uuid(plan_id, "plan ID")
        fields: dict[str, Any] = {
            "subscriberNumber": subscriber_number,
            "name": name,
            "email": email,
            "notes": notes,
            "serviceAddress": service_address,
            "planId": plan_id,
            "metadata": metadata,
        }
        json_data = {k: v for k, v in fields.items() if v is not _UNSET}
        if not json_data:
            msg = "No subscriber fields to update"
            raise ValueError(msg)
        response = await self._client._patch(path, json_data=json_data)
        return self._subscriber_result(path, response)

    async def attach_host(
        self, subscriber_id: str, host_id: str
    ) -> HostLinkResponse | None:
        """
        Attach or re-link a subscriber's gateway host.

        A different host replaces the current one (an RMA re-link). This is
        not idempotent: the host that is already linked is rejected with a 409
        whose ``api_error_code`` is ``gateway_already_attached``, and a host
        linked to another subscriber with ``gateway_already_linked``. After a
        timeout, read the subscriber's ``host_id`` instead of retrying.

        Args:
            subscriber_id: The subscriber ID.
            host_id: The gateway host ID (1-128 characters).

        Returns:
            The updated subscriber and the replaced host ID, or None if the
            response carried no readable subscriber.

        Raises:
            ValueError: If the subscriber ID is not a valid UUID, or
                ``host_id`` is blank or longer than 128 characters.
            UniFiError: If the API rejects the request (non-2xx).

        """
        path = f"{_subscriber_path(subscriber_id)}/host"
        json_data = {"hostId": _checked_host_id(host_id)}
        response = await self._client._put(path, json_data=json_data)
        return _write_result(HostLinkResponse, path, response, "host link")

    async def detach_host(self, subscriber_id: str) -> HostLinkResponse | None:
        """
        Detach a subscriber's gateway host.

        This is not idempotent: a subscriber with no host is rejected with a
        409 whose ``api_error_code`` is ``no_attached_host``. After a timeout,
        read the subscriber's ``host_id`` instead of retrying.

        Args:
            subscriber_id: The subscriber ID.

        Returns:
            The updated subscriber and the removed host ID, or None if the
            response carried no readable subscriber.

        Raises:
            ValueError: If the subscriber ID is not a valid UUID.
            UniFiError: If the API rejects the request (non-2xx).

        """
        path = f"{_subscriber_path(subscriber_id)}/host"
        response = await self._client._delete(path)
        return _write_result(HostLinkResponse, path, response, "host link")

    async def assign_plan(self, subscriber_id: str, plan_id: str) -> Subscriber | None:
        """
        Assign a service plan to a subscriber.

        Args:
            subscriber_id: The subscriber ID.
            plan_id: The service plan ID (UUID).

        Returns:
            The updated subscriber, or None if the response carried none.

        Raises:
            ValueError: If the subscriber ID or ``plan_id`` is not a valid UUID.
            UniFiError: If the API rejects the request (non-2xx), for example
                an archived plan (``service_plan_archived``).

        """
        path = f"{_subscriber_path(subscriber_id)}/plan"
        json_data = {"planId": _canonical_uuid(plan_id, "plan ID")}
        response = await self._client._put(path, json_data=json_data)
        return self._subscriber_result(path, response)

    @staticmethod
    def _subscriber_result(path: str, response: object) -> Subscriber | None:
        """Parse the subscriber in a successful write without ever failing it."""
        return _write_result(Subscriber, path, _object_data(response), "subscriber")
