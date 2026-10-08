# Copyright (c) 2026 Ruaan Deysel
"""Tests for the UniFi Carrier Fabric API client and models."""

from __future__ import annotations

import json
import logging
import uuid
from typing import TYPE_CHECKING, Any, Self
from unittest.mock import MagicMock

import pytest

from custom_components.unifi_insights.api.auth import ApiKeyAuth
from custom_components.unifi_insights.api.carrier_fabric import (
    CarrierFabricMeta,
    HostLinkResponse,
    ServicePlan,
    Subscriber,
    UniFiCarrierFabricClient,
)
from custom_components.unifi_insights.api.const import (
    CARRIER_FABRIC_MAX_PAGES,
)
from custom_components.unifi_insights.api.exceptions import (
    UniFiAuthenticationError,
    UniFiNotFoundError,
    UniFiRateLimitError,
    UniFiResponseError,
)

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from custom_components.unifi_insights.api.carrier_fabric.endpoints import (
        SubscribersEndpoint,
    )

VALID_SUB_ID_1 = "11111111-1111-1111-1111-111111111111"
VALID_SUB_ID_2 = "22222222-2222-2222-2222-222222222222"
VALID_PLAN_ID_1 = "33333333-3333-3333-3333-333333333333"


class _Response:
    """Minimal aiohttp response replacement for transport tests."""

    def __init__(
        self,
        body: dict[str, Any] | list[Any] | str,
        status: int = 200,
        headers: dict[str, str] | None = None,
    ) -> None:
        """Store a JSON response body or text."""
        self.status = status
        self._body = body
        self.headers = headers or {}
        self.method = "GET"
        self.url = MagicMock()
        self.url.path = "/v1/carrier"

    async def __aenter__(self) -> Self:
        """Enter the async response context."""
        return self

    async def __aexit__(self, *args: object) -> None:
        """Exit the async response context."""

    async def text(self) -> str:
        """Return string representation of response body."""
        if isinstance(self._body, str):
            return self._body
        return json.dumps(self._body)

    async def json(self) -> Any:
        """Return parsed JSON body."""
        if isinstance(self._body, str):
            return json.loads(self._body)
        return self._body


class _Session:
    """Queued response transport recording requests made by the client."""

    closed = False

    def __init__(self, responses: list[_Response | dict[str, Any] | str]) -> None:
        """Initialize queued responses."""
        self._responses = iter(
            [r if isinstance(r, _Response) else _Response(r) for r in responses]
        )
        self.requests: list[dict[str, Any]] = []

    def request(self, method: str, url: object, **kwargs: Any) -> _Response:
        """Record a request and return next configured response."""
        self.requests.append({"method": method, "url": str(url), **kwargs})
        return next(self._responses)


def _client(session: _Session) -> UniFiCarrierFabricClient:
    """Create a Carrier Fabric client using a recording transport."""
    return UniFiCarrierFabricClient(ApiKeyAuth("test-carrier-key"), session=session)  # type: ignore[arg-type]


async def test_subscribers_multi_page_cursor_pagination() -> None:
    """Subscriber get_all iterates cursor pages until hasMore is false."""
    session = _Session(
        [
            {
                "data": [{"id": VALID_SUB_ID_1, "name": "Alice"}],
                "meta": {"hasMore": True, "nextCursor": "cur-2"},
            },
            {
                "data": [{"id": VALID_SUB_ID_2, "name": "Bob"}],
                "meta": {"hasMore": False, "nextCursor": None},
            },
        ]
    )

    client = _client(session)
    subscribers = await client.subscribers.get_all()

    assert len(subscribers) == 2
    assert subscribers[0].id == VALID_SUB_ID_1
    assert subscribers[0].name == "Alice"
    assert subscribers[1].id == VALID_SUB_ID_2
    assert subscribers[1].name == "Bob"

    assert len(session.requests) == 2
    assert session.requests[0]["params"] == {"limit": 500}
    assert session.requests[1]["params"] == {"limit": 500, "cursor": "cur-2"}
    assert session.requests[0]["headers"]["X-API-Key"] == "test-carrier-key"


async def test_subscribers_single_page_explicit_limit() -> None:
    """Passing an explicit limit fetches only a single page."""
    session = _Session(
        [
            {
                "data": [{"id": VALID_SUB_ID_1}],
                "meta": {"hasMore": True, "nextCursor": "cur-2"},
            }
        ]
    )

    client = _client(session)
    subscribers = await client.subscribers.get_all(limit=1)

    assert len(subscribers) == 1
    assert subscribers[0].id == VALID_SUB_ID_1
    assert len(session.requests) == 1
    assert session.requests[0]["params"] == {"limit": 1}


async def test_subscribers_single_page_explicit_cursor() -> None:
    """Passing an explicit cursor fetches only a single page."""
    session = _Session(
        [
            {
                "data": [{"id": VALID_SUB_ID_1}],
                "meta": {"hasMore": True, "nextCursor": "cur-10"},
            }
        ]
    )

    client = _client(session)
    subscribers = await client.subscribers.get_all(cursor="page-9")

    assert len(subscribers) == 1
    assert subscribers[0].id == VALID_SUB_ID_1
    assert len(session.requests) == 1
    assert session.requests[0]["params"] == {"cursor": "page-9"}


async def test_subscribers_query_filters() -> None:
    """Filter parameters are correctly passed to query params."""
    session = _Session(
        [
            {
                "data": [{"id": VALID_SUB_ID_1}],
            }
        ]
    )

    client = _client(session)
    await client.subscribers.get_all(
        limit=10,
        cursor="cur-x",
        sort="-name",
        plan_id="plan-1",
        suspended=True,
    )

    assert session.requests[0]["params"] == {
        "limit": 10,
        "cursor": "cur-x",
        "sort": "-name",
        "planId": "plan-1",
        "suspended": "true",
    }


async def test_subscribers_repeated_cursor_raises_response_error() -> None:
    """A repeated pagination cursor raises UniFiResponseError."""
    session = _Session(
        [
            {
                "data": [{"id": VALID_SUB_ID_1}],
                "meta": {"hasMore": True, "nextCursor": "loop-token"},
            },
            {
                "data": [{"id": VALID_SUB_ID_2}],
                "meta": {"hasMore": True, "nextCursor": "loop-token"},
            },
        ]
    )

    with pytest.raises(UniFiResponseError) as err:
        await _client(session).subscribers.get_all()

    assert "repeated pagination cursor" in err.value.message


async def test_subscribers_max_pages_cap_raises_response_error() -> None:
    """Exceeding CARRIER_FABRIC_MAX_PAGES raises UniFiResponseError."""
    pages = [
        {
            "data": [{"id": str(uuid.uuid4())}],
            "meta": {"hasMore": True, "nextCursor": f"cur-{i + 1}"},
        }
        for i in range(CARRIER_FABRIC_MAX_PAGES)
    ]
    session = _Session(pages)

    with pytest.raises(UniFiResponseError) as err:
        await _client(session).subscribers.get_all()

    assert f"exceeded maximum pages ({CARRIER_FABRIC_MAX_PAGES})" in err.value.message


async def test_subscribers_deduplicates_by_id() -> None:
    """Subscribers with duplicate IDs across pages are deduplicated."""
    session = _Session(
        [
            {
                "data": [{"id": VALID_SUB_ID_1}, {"id": VALID_SUB_ID_2}],
                "meta": {"hasMore": True, "nextCursor": "cur-2"},
            },
            {
                "data": [
                    {"id": VALID_SUB_ID_2},
                    {"id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"},
                ],
                "meta": {"hasMore": False, "nextCursor": None},
            },
        ]
    )

    subscribers = await _client(session).subscribers.get_all()
    assert [s.id for s in subscribers] == [
        VALID_SUB_ID_1,
        VALID_SUB_ID_2,
        "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
    ]


async def test_subscribers_skips_invalid_items() -> None:
    """Items failing schema validation are skipped without failing the list."""
    session = _Session(
        [
            {
                "data": [
                    {"id": VALID_SUB_ID_1, "name": "Valid 1"},
                    {"name": "missing_id"},
                    [1, 2, 3],
                    {"unexpected": "shape"},
                    12345,
                    {"id": VALID_SUB_ID_2, "name": "Valid 2"},
                ],
                "meta": {"hasMore": False},
            }
        ]
    )

    subscribers = await _client(session).subscribers.get_all()
    assert len(subscribers) == 2
    assert subscribers[0].id == VALID_SUB_ID_1
    assert subscribers[1].id == VALID_SUB_ID_2


async def test_service_plans_get_all_unpaginated() -> None:
    """Service plans endpoint returns unpaginated list of plans."""
    session = _Session(
        [
            {
                "data": [
                    {
                        "id": VALID_PLAN_ID_1,
                        "orgId": "org-1",
                        "name": "Gigabit",
                        "status": "active",
                        "downloadMbps": 1000.0,
                        "uploadMbps": 500.0,
                    },
                    {
                        "id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                        "name": "Standard",
                        "downloadMbps": 100,
                    },
                ]
            }
        ]
    )

    plans = await _client(session).service_plans.get_all()
    assert len(plans) == 2
    assert plans[0].id == VALID_PLAN_ID_1
    assert plans[0].org_id == "org-1"
    assert plans[0].org_id == "org-1"
    assert plans[0].name == "Gigabit"
    assert plans[0].download_mbps == 1000.0
    assert plans[0].download_mbps == 1000.0
    assert plans[0].upload_mbps == 500.0
    assert plans[0].upload_mbps == 500.0
    assert plans[1].id == "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    assert plans[1].download_mbps == 100.0


async def test_service_plans_skips_invalid_items() -> None:
    """Service plans list skips invalid items."""
    session = _Session(
        [
            {
                "data": [
                    {"id": VALID_PLAN_ID_1},
                    {"name": "missing-id"},
                    "invalid-type",
                    {"id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"},
                ]
            }
        ]
    )

    plans = await _client(session).service_plans.get_all()
    assert len(plans) == 2
    assert [p.id for p in plans] == [
        VALID_PLAN_ID_1,
        "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
    ]


@pytest.mark.parametrize(
    "payload",
    [
        [1, 2, 3],
        {"unexpected": "shape"},
        {"data": "not-a-list"},
        {"data": None},
        {"data": 123},
    ],
)
async def test_unexpected_response_shape_raises_response_error(
    payload: Any,
) -> None:
    """Non-dict and malformed data envelopes raise UniFiResponseError."""
    client = _client(_Session([payload]))
    with pytest.raises(UniFiResponseError):
        await client.subscribers.get_all()

    client2 = _client(_Session([payload]))
    with pytest.raises(UniFiResponseError):
        await client2.subscribers.get_all(limit=1)

    client3 = _client(_Session([payload]))
    with pytest.raises(UniFiResponseError):
        await client3.service_plans.get_all()


async def test_empty_data_envelope_returns_empty_list() -> None:
    """A well-formed {'data': []} returns an empty list without raising."""
    client1 = _client(_Session([{"data": [], "meta": {"hasMore": False}}]))
    assert await client1.subscribers.get_all() == []

    client2 = _client(_Session([{"data": []}]))
    assert await client2.subscribers.get_all(limit=1) == []

    client3 = _client(_Session([{"data": []}]))
    assert await client3.service_plans.get_all() == []


@pytest.mark.parametrize(
    "bad_page_2",
    [
        [1, 2, 3],
        {"unexpected": "shape"},
        {"data": "not-a-list"},
        {"data": [{"id": VALID_SUB_ID_2}], "meta": "not-a-dict"},
        {"data": [{"id": VALID_SUB_ID_2}], "meta": None},
    ],
)
async def test_subscribers_pagination_malformed_envelope_on_subsequent_page_raises(
    bad_page_2: Any,
) -> None:
    """Malformed envelope, data not list, or meta not dict after page 1.

    Should raise UniFiResponseError.
    """
    session = _Session(
        [
            {
                "data": [{"id": VALID_SUB_ID_1}],
                "meta": {"hasMore": True, "nextCursor": "cur-2"},
            },
            bad_page_2,
        ]
    )
    client = _client(session)
    with pytest.raises(UniFiResponseError):
        await client.subscribers.get_all()


@pytest.mark.parametrize(
    "bad_cursor",
    [None, "", 123, []],
)
async def test_subscribers_pagination_has_more_without_cursor_raises(
    bad_cursor: Any,
) -> None:
    """hasMore is True with missing/empty/non-string nextCursor.

    Should raise UniFiResponseError.
    """
    session = _Session(
        [
            {
                "data": [{"id": VALID_SUB_ID_1}],
                "meta": {"hasMore": True, "nextCursor": bad_cursor},
            }
        ]
    )
    client = _client(session)
    with pytest.raises(UniFiResponseError) as err:
        await client.subscribers.get_all()
    assert "hasMore=True but nextCursor is missing" in err.value.message


async def test_subscribers_pagination_has_more_absent_continues_while_next_cursor() -> (
    None
):
    """Pagination continues while nextCursor is string when hasMore omitted."""
    session = _Session(
        [
            {
                "data": [{"id": VALID_SUB_ID_1}],
                "meta": {"nextCursor": "cur-2"},
            },
            {
                "data": [{"id": VALID_SUB_ID_2}],
                "meta": {"nextCursor": None},
            },
        ]
    )
    client = _client(session)
    subs = await client.subscribers.get_all()
    assert len(subs) == 2


@pytest.mark.parametrize("bad_limit", [0, 501, -1, 1000, True, "50"])
async def test_subscribers_limit_bounds_validation(bad_limit: Any) -> None:
    """Limit must be an integer between 1 and 500, failing before HTTP call."""
    session = _Session([])
    client = _client(session)
    with pytest.raises(ValueError, match="limit must be an integer between 1 and 500"):
        await client.subscribers.get_all(limit=bad_limit)
    assert len(session.requests) == 0


@pytest.mark.parametrize(
    "bad_uuid", ["not-a-uuid", "sub-1", "", "12345", "11111111-1111-1111-1111"]
)
async def test_subscribers_endpoint_uuid_validation(bad_uuid: str) -> None:
    """Every subscriber method validates the UUID before building the path."""
    session = _Session([])
    client = _client(session)

    with pytest.raises(ValueError, match="Invalid subscriber ID format"):
        await client.subscribers.get(bad_uuid)

    with pytest.raises(ValueError, match="Invalid subscriber ID format"):
        await client.subscribers.suspend(bad_uuid)

    with pytest.raises(ValueError, match="Invalid subscriber ID format"):
        await client.subscribers.resume(bad_uuid)

    with pytest.raises(ValueError, match="Invalid subscriber ID format"):
        await client.subscribers.update(bad_uuid, name="New name")

    with pytest.raises(ValueError, match="Invalid subscriber ID format"):
        await client.subscribers.attach_host(bad_uuid, "host-1")

    with pytest.raises(ValueError, match="Invalid subscriber ID format"):
        await client.subscribers.detach_host(bad_uuid)

    with pytest.raises(ValueError, match="Invalid subscriber ID format"):
        await client.subscribers.assign_plan(bad_uuid, VALID_PLAN_ID_1)

    assert len(session.requests) == 0


def test_models_omitted_and_null_fields() -> None:
    """Subscriber and ServicePlan allow optional fields and default suspended."""
    sub = Subscriber.model_validate({"id": VALID_SUB_ID_1})
    assert sub.id == VALID_SUB_ID_1
    assert sub.suspended is False
    assert sub.org_id is None
    assert sub.org_id is None
    assert sub.name is None
    assert sub.email is None
    assert sub.notes is None
    assert sub.plan_id is None
    assert sub.host_id is None
    assert sub.state is None

    # Null suspended explicitly coerced to False
    sub_null = Subscriber.model_validate({"id": VALID_SUB_ID_2, "suspended": None})
    assert sub_null.suspended is False

    # Snake-case field validation works alongside camelCase
    sub_snake = Subscriber.model_validate(
        {
            "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "org_id": "org-3",
            "subscriber_number": "SN3",
        }
    )
    assert sub_snake.org_id == "org-3"
    assert sub_snake.subscriber_number == "SN3"

    plan = ServicePlan.model_validate({"id": VALID_PLAN_ID_1})
    assert plan.id == VALID_PLAN_ID_1
    assert plan.name is None
    assert plan.status is None
    assert plan.download_mbps is None
    assert plan.upload_mbps is None
    assert plan.archived_at is None

    meta = CarrierFabricMeta.model_validate({"nextCursor": "c1", "hasMore": True})
    assert meta.next_cursor == "c1"
    assert meta.has_more is True


def test_models_unknown_state_and_status() -> None:
    """State and status fields are strings, allowing future backend enum additions."""
    sub = Subscriber.model_validate({"id": VALID_SUB_ID_1, "state": "quantum_active"})
    assert sub.state == "quantum_active"

    plan = ServicePlan.model_validate({"id": VALID_PLAN_ID_1, "status": "experimental"})
    assert plan.status == "experimental"


async def test_get_single_subscriber_and_plan() -> None:
    """Fetching individual subscriber and service plan returns models."""
    session = _Session(
        [
            {"data": {"id": VALID_SUB_ID_1, "name": "Single Sub"}},
            {"data": {"id": VALID_PLAN_ID_1, "name": "Single Plan"}},
            {"data": "bad-shape"},
            {"data": "bad-shape"},
        ]
    )

    client = _client(session)
    sub = await client.subscribers.get(VALID_SUB_ID_1)
    assert sub.id == VALID_SUB_ID_1
    assert sub.name == "Single Sub"

    plan = await client.service_plans.get(VALID_PLAN_ID_1)
    assert plan.id == VALID_PLAN_ID_1
    assert plan.name == "Single Plan"

    with pytest.raises(UniFiResponseError):
        await client.subscribers.get(VALID_SUB_ID_1)

    with pytest.raises(UniFiResponseError):
        await client.service_plans.get("plan-bad")


async def test_suspend_with_and_without_reason() -> None:
    """Suspend endpoint sends reason in JSON body only when provided."""
    session = _Session(
        [
            {
                "data": {
                    "id": VALID_SUB_ID_1,
                    "suspended": True,
                    "suspendReason": "nonpayment",
                }
            },
            {"data": {"id": VALID_SUB_ID_2, "suspended": True}},
        ]
    )

    client = _client(session)

    # 1. With reason
    sub1 = await client.subscribers.suspend(VALID_SUB_ID_1, reason="nonpayment")
    assert sub1.suspended is True
    assert sub1.suspend_reason == "nonpayment"
    assert session.requests[0]["method"] == "POST"
    assert (
        session.requests[0]["url"]
        == f"https://api.ui.com/v1/carrier/subscribers/{VALID_SUB_ID_1}/suspend"
    )
    assert session.requests[0]["json"] == {"reason": "nonpayment"}

    # 2. Without reason
    sub2 = await client.subscribers.suspend(VALID_SUB_ID_2)
    assert sub2.suspended is True
    assert session.requests[1]["method"] == "POST"
    assert (
        session.requests[1]["url"]
        == f"https://api.ui.com/v1/carrier/subscribers/{VALID_SUB_ID_2}/suspend"
    )
    assert session.requests[1]["json"] is None


async def test_resume() -> None:
    """Resume endpoint sends POST without JSON body."""
    session = _Session(
        [
            {"data": {"id": VALID_SUB_ID_1, "suspended": False}},
        ]
    )

    client = _client(session)
    sub = await client.subscribers.resume(VALID_SUB_ID_1)
    assert sub.suspended is False
    assert session.requests[0]["method"] == "POST"
    assert (
        session.requests[0]["url"]
        == f"https://api.ui.com/v1/carrier/subscribers/{VALID_SUB_ID_1}/resume"
    )
    assert session.requests[0]["json"] is None


SUBSCRIBERS_URL = "https://api.ui.com/v1/carrier/subscribers"
SUBSCRIBER_URL = f"{SUBSCRIBERS_URL}/{VALID_SUB_ID_1}"


async def test_create_sends_only_the_fields_passed() -> None:
    """Create posts subscriberNumber plus only the optional fields given."""
    session = _Session(
        [
            _Response({"data": {"id": VALID_SUB_ID_1}}, status=201),
            _Response({"data": {"id": VALID_SUB_ID_2}}, status=201),
        ]
    )
    client = _client(session)

    sub = await client.subscribers.create(subscriber_number="ACME-1")
    assert sub is not None
    assert sub.id == VALID_SUB_ID_1
    assert session.requests[0]["method"] == "POST"
    assert session.requests[0]["url"] == SUBSCRIBERS_URL
    assert session.requests[0]["json"] == {"subscriberNumber": "ACME-1"}

    await client.subscribers.create(
        subscriber_number="ACME-2",
        name="Jane Doe",
        email="jane@example.com",
        notes="Gate code 1234",
        service_address="1 Main St",
        plan_id=VALID_PLAN_ID_1.upper(),
        metadata={"crmId": 7},
    )
    assert session.requests[1]["json"] == {
        "subscriberNumber": "ACME-2",
        "name": "Jane Doe",
        "email": "jane@example.com",
        "notes": "Gate code 1234",
        "serviceAddress": "1 Main St",
        "planId": VALID_PLAN_ID_1,
        "metadata": {"crmId": 7},
    }


async def test_update_sends_only_the_fields_passed() -> None:
    """Update patches only the given fields, and None clears a field."""
    session = _Session([{"data": {"id": VALID_SUB_ID_1}}] * 3)
    client = _client(session)

    sub = await client.subscribers.update(VALID_SUB_ID_1, name="New name")
    assert sub is not None
    assert session.requests[0]["method"] == "PATCH"
    assert session.requests[0]["url"] == SUBSCRIBER_URL
    assert session.requests[0]["json"] == {"name": "New name"}

    await client.subscribers.update(
        VALID_SUB_ID_1,
        name=None,
        email=None,
        notes=None,
        service_address=None,
        plan_id=None,
    )
    assert session.requests[1]["json"] == {
        "name": None,
        "email": None,
        "notes": None,
        "serviceAddress": None,
        "planId": None,
    }

    await client.subscribers.update(
        VALID_SUB_ID_1,
        subscriber_number="ACME-9",
        plan_id=VALID_PLAN_ID_1.upper(),
        metadata={},
    )
    assert session.requests[2]["json"] == {
        "subscriberNumber": "ACME-9",
        "planId": VALID_PLAN_ID_1,
        "metadata": {},
    }


async def test_update_without_fields_raises_before_request() -> None:
    """An update with nothing to change is rejected without a request."""
    session = _Session([])

    with pytest.raises(ValueError, match="No subscriber fields to update"):
        await _client(session).subscribers.update(VALID_SUB_ID_1)

    assert session.requests == []


async def test_attach_host() -> None:
    """Attach puts the host ID and returns the subscriber and replaced host."""
    session = _Session(
        [
            {
                "data": {"id": VALID_SUB_ID_1, "hostId": "host-new"},
                "prevHostId": "host-old",
                "traceId": "trace-1",
            }
        ]
    )

    result = await _client(session).subscribers.attach_host(VALID_SUB_ID_1, "host-new")

    assert isinstance(result, HostLinkResponse)
    assert result.subscriber.host_id == "host-new"
    assert result.prev_host_id == "host-old"
    assert session.requests[0]["method"] == "PUT"
    assert session.requests[0]["url"] == f"{SUBSCRIBER_URL}/host"
    assert session.requests[0]["json"] == {"hostId": "host-new"}


async def test_attach_host_accepts_a_128_character_host_id() -> None:
    """The spec allows a host ID of up to 128 characters."""
    session = _Session([{"data": {"id": VALID_SUB_ID_1}}])

    await _client(session).subscribers.attach_host(VALID_SUB_ID_1, "h" * 128)

    assert session.requests[0]["json"] == {"hostId": "h" * 128}


@pytest.mark.parametrize("bad_host_id", ["", "   ", "h" * 129, None, 123])
async def test_attach_host_rejects_invalid_host_id(bad_host_id: Any) -> None:
    """A blank, too long or non-string host ID never reaches the API."""
    session = _Session([])

    with pytest.raises(ValueError, match="Invalid host ID"):
        await _client(session).subscribers.attach_host(VALID_SUB_ID_1, bad_host_id)

    assert session.requests == []


async def test_detach_host() -> None:
    """Detach deletes the host link without a body and returns the removed host."""
    session = _Session(
        [{"data": {"id": VALID_SUB_ID_1, "hostId": None}, "prevHostId": "host-old"}]
    )

    result = await _client(session).subscribers.detach_host(VALID_SUB_ID_1)

    assert result is not None
    assert result.subscriber.host_id is None
    assert result.prev_host_id == "host-old"
    assert session.requests[0]["method"] == "DELETE"
    assert session.requests[0]["url"] == f"{SUBSCRIBER_URL}/host"
    assert session.requests[0]["json"] is None


async def test_assign_plan() -> None:
    """Assign plan puts the canonical plan UUID."""
    session = _Session([{"data": {"id": VALID_SUB_ID_1, "planId": VALID_PLAN_ID_1}}])

    sub = await _client(session).subscribers.assign_plan(
        VALID_SUB_ID_1, VALID_PLAN_ID_1.upper()
    )

    assert sub is not None
    assert sub.plan_id == VALID_PLAN_ID_1
    assert session.requests[0]["method"] == "PUT"
    assert session.requests[0]["url"] == f"{SUBSCRIBER_URL}/plan"
    assert session.requests[0]["json"] == {"planId": VALID_PLAN_ID_1}


@pytest.mark.parametrize(
    "call",
    [
        lambda subscribers: subscribers.create(
            subscriber_number="ACME-1", plan_id="plan-1"
        ),
        lambda subscribers: subscribers.update(VALID_SUB_ID_1, plan_id="plan-1"),
        lambda subscribers: subscribers.assign_plan(VALID_SUB_ID_1, "plan-1"),
    ],
    ids=["create", "update", "assign_plan"],
)
async def test_invalid_plan_id_raises_before_request(
    call: Callable[[SubscribersEndpoint], Awaitable[object]],
) -> None:
    """A plan ID that is not a UUID never reaches the API."""
    session = _Session([])

    with pytest.raises(ValueError, match="Invalid plan ID format"):
        await call(_client(session).subscribers)

    assert session.requests == []


@pytest.mark.parametrize(
    "call",
    [
        lambda subscribers: subscribers.create(
            subscriber_number="ACME-1", plan_id=uuid.UUID(VALID_PLAN_ID_1)
        ),
        lambda subscribers: subscribers.update(
            VALID_SUB_ID_1, plan_id=uuid.UUID(VALID_PLAN_ID_1)
        ),
        lambda subscribers: subscribers.assign_plan(
            VALID_SUB_ID_1, uuid.UUID(VALID_PLAN_ID_1)
        ),
    ],
    ids=["create", "update", "assign_plan"],
)
async def test_plan_id_uuid_object_is_sent_as_text(
    call: Callable[[SubscribersEndpoint], Awaitable[object]],
) -> None:
    """A uuid.UUID plan ID is sent as its canonical text, never as an object."""
    session = _Session([{"data": {"id": VALID_SUB_ID_1}}])

    await call(_client(session).subscribers)

    assert session.requests[0]["json"]["planId"] == VALID_PLAN_ID_1


async def test_create_with_non_json_success_body_raises() -> None:
    """A non-JSON 2xx still raises, so create's docstring warns before a retry."""
    session = _Session([_Response("<html>login</html>", status=201)])

    with pytest.raises(UniFiResponseError) as err:
        await _client(session).subscribers.create(subscriber_number="ACME-1")

    assert err.value.status_code == 201
    assert len(session.requests) == 1


@pytest.mark.parametrize(
    ("call", "status", "code"),
    [
        (
            lambda subscribers: subscribers.attach_host(VALID_SUB_ID_1, "host-1"),
            409,
            "gateway_already_attached",
        ),
        (
            lambda subscribers: subscribers.detach_host(VALID_SUB_ID_1),
            409,
            "no_attached_host",
        ),
        (
            lambda subscribers: subscribers.assign_plan(
                VALID_SUB_ID_1, VALID_PLAN_ID_1
            ),
            400,
            "service_plan_archived",
        ),
        (
            lambda subscribers: subscribers.create(subscriber_number="ACME-1"),
            400,
            "validation_failed",
        ),
    ],
    ids=["attach_host", "detach_host", "assign_plan", "create"],
)
async def test_write_errors_carry_the_api_error_code(
    call: Callable[[SubscribersEndpoint], Awaitable[object]],
    status: int,
    code: str,
) -> None:
    """A rejected write raises with the API's error code, like suspend and resume."""
    session = _Session(
        [_Response({"error": {"code": code}, "traceId": "trace-1"}, status=status)]
    )

    with pytest.raises(UniFiResponseError) as err:
        await call(_client(session).subscribers)

    assert err.value.status_code == status
    assert err.value.api_error_code == code
    assert len(session.requests) == 1


async def test_create_does_not_log_subscriber_fields(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Request and response field values stay out of the logs."""
    session = _Session(
        [_Response({"data": {"suspended": True, "name": "Jane Doe"}}, status=201)]
    )

    with caplog.at_level(logging.DEBUG):
        await _client(session).subscribers.create(
            subscriber_number="ACME-1", name="Jane Doe", email="jane@example.com"
        )

    assert "Jane Doe" not in caplog.text
    assert "jane@example.com" not in caplog.text
    assert "ACME-1" not in caplog.text


def test_host_link_response_model() -> None:
    """HostLinkResponse reads the spec envelope and keeps unknown keys."""
    result = HostLinkResponse.model_validate(
        {"data": {"id": VALID_SUB_ID_1}, "prevHostId": None, "traceId": "trace-1"}
    )

    assert result.subscriber.id == VALID_SUB_ID_1
    assert result.prev_host_id is None
    assert result.model_extra == {"traceId": "trace-1"}
    assert result.model_dump(by_alias=True, exclude_none=True)["data"] == {
        "id": VALID_SUB_ID_1,
        "suspended": False,
    }


_WRITES: dict[str, Callable[[SubscribersEndpoint], Awaitable[object]]] = {
    "suspend": lambda subscribers: subscribers.suspend(VALID_SUB_ID_1),
    "resume": lambda subscribers: subscribers.resume(VALID_SUB_ID_1),
    "create": lambda subscribers: subscribers.create(subscriber_number="ACME-1"),
    "update": lambda subscribers: subscribers.update(VALID_SUB_ID_1, name="New"),
    "attach_host": lambda subscribers: subscribers.attach_host(
        VALID_SUB_ID_1, "host-1"
    ),
    "detach_host": lambda subscribers: subscribers.detach_host(VALID_SUB_ID_1),
    "assign_plan": lambda subscribers: subscribers.assign_plan(
        VALID_SUB_ID_1, VALID_PLAN_ID_1
    ),
}


@pytest.mark.parametrize("action", list(_WRITES))
@pytest.mark.parametrize(
    "body",
    [
        {},
        {"data": []},
        {"data": "unexpected"},
        {"data": {"suspended": True}},  # no id: not a valid Subscriber
        {"unrelated": 1},
        [1, 2],
        "",
    ],
)
async def test_write_with_unreadable_success_body_returns_none(
    action: str, body: Any, caplog: pytest.LogCaptureFixture
) -> None:
    """A 2xx means the write was applied: a bad body is not a failure."""
    session = _Session([_Response(body)])
    client = _client(session)

    with caplog.at_level(logging.DEBUG):
        result = await _WRITES[action](client.subscribers)

    assert result is None
    assert len(session.requests) == 1
    label = "host link" if action.endswith("_host") else "subscriber"
    assert f"succeeded without a readable {label} body" in caplog.text


@pytest.mark.parametrize("action", list(_WRITES))
async def test_write_with_error_status_still_raises(action: str) -> None:
    """Only a 2xx is success: a rejected write must still raise."""
    session = _Session([_Response({"error": {"code": "internal_error"}}, status=500)])
    client = _client(session)

    with pytest.raises(UniFiResponseError):
        await _WRITES[action](client.subscribers)


@pytest.mark.parametrize(
    "spelling",
    [
        "{11111111-1111-1111-1111-111111111111}",
        "urn:uuid:11111111-1111-1111-1111-111111111111",
        "11111111111111111111111111111111",
        "11111111-1111-1111-1111-111111111111".upper(),
    ],
)
async def test_subscriber_paths_use_the_canonical_uuid(spelling: str) -> None:
    """Non-canonical UUID spellings never reach the request path."""
    session = _Session([{"data": {"id": VALID_SUB_ID_1}}] * 7)
    client = _client(session)

    await client.subscribers.get(spelling)
    await client.subscribers.suspend(spelling)
    await client.subscribers.resume(spelling)
    await client.subscribers.update(spelling, name="New name")
    await client.subscribers.attach_host(spelling, "host-1")
    await client.subscribers.detach_host(spelling)
    await client.subscribers.assign_plan(spelling, VALID_PLAN_ID_1)

    base = f"https://api.ui.com/v1/carrier/subscribers/{VALID_SUB_ID_1}"
    assert [r["url"] for r in session.requests] == [
        base,
        f"{base}/suspend",
        f"{base}/resume",
        base,
        f"{base}/host",
        f"{base}/host",
        f"{base}/plan",
    ]


async def test_error_code_extraction_403_insufficient_scope() -> None:
    """403 insufficient_scope sets api_error_code on UniFiAuthenticationError."""
    session = _Session(
        [
            _Response(
                {
                    "error": {
                        "code": "insufficient_scope",
                        "message": "Missing required scope",
                    },
                    "traceId": "trace-403",
                },
                status=403,
            )
        ]
    )

    with pytest.raises(UniFiAuthenticationError) as err:
        await _client(session).service_plans.get_all()

    assert err.value.status_code == 403
    assert err.value.api_error_code == "insufficient_scope"


async def test_error_code_extraction_503_write_conflict_retryable() -> None:
    """503 write_conflict_retryable sets api_error_code on UniFiResponseError."""
    session = _Session(
        [
            _Response(
                {
                    "error": {
                        "code": "write_conflict_retryable",
                        "message": "Write collision occurred",
                    },
                    "traceId": "trace-503",
                },
                status=503,
            )
        ]
    )

    with pytest.raises(UniFiResponseError) as err:
        await _client(session).subscribers.suspend(VALID_SUB_ID_1)

    assert err.value.status_code == 503
    assert err.value.api_error_code == "write_conflict_retryable"


async def test_error_code_extraction_404_subscriber_not_found() -> None:
    """404 subscriber_not_found sets api_error_code on UniFiNotFoundError."""
    session = _Session(
        [
            _Response(
                {
                    "error": {
                        "code": "subscriber_not_found",
                        "message": "Subscriber does not exist",
                    }
                },
                status=404,
            )
        ]
    )

    with pytest.raises(UniFiNotFoundError) as err:
        await _client(session).subscribers.get(VALID_SUB_ID_1)

    assert err.value.status_code == 404
    assert err.value.api_error_code == "subscriber_not_found"


async def test_error_code_extraction_429_rate_limit() -> None:
    """429 response extracts rate limit error code and retry after."""
    session = _Session(
        [
            _Response(
                {"error": {"code": "too_many_requests"}},
                status=429,
                headers={"Retry-After": "10"},
            )
        ]
    )

    with pytest.raises(UniFiRateLimitError) as err:
        await _client(session).service_plans.get_all()

    assert err.value.status_code == 429
    assert err.value.api_error_code == "too_many_requests"
    assert err.value.retry_after == 10


async def test_carrier_fabric_response_bodies_not_logged(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Subscriber and plan response bodies stay private in transport logs."""
    client = _client(_Session([]))
    assert (
        client._response_log_text('{"name": "Secret"}', limit=500)
        == "[Carrier Fabric response omitted]"
    )
    assert client._response_log_text("", limit=500) == "empty"

    response = MagicMock(status=500, method="GET")
    response.url.path = "/v1/carrier/subscribers"
    response.headers = {}
    response.text = pytest.importorskip("unittest.mock").AsyncMock(
        return_value='{"name": "Secret Customer"}'
    )

    with (
        caplog.at_level(
            logging.DEBUG,
            logger="custom_components.unifi_insights.api",
        ),
        pytest.raises(UniFiResponseError),
    ):
        await client._handle_response(response)

    assert "Secret Customer" not in caplog.text
    assert "[Carrier Fabric response omitted]" in caplog.text


async def test_body_still_readable_after_base_class() -> None:
    """Verify response body is readable after base class raises auth error."""
    client = _client(_Session([]))
    response = MagicMock(status=401, method="GET")
    response.url.path = "/v1/carrier/service-plans"
    response.headers = {}
    response.text = pytest.importorskip("unittest.mock").AsyncMock(
        return_value=json.dumps({"error": {"code": "invalid_credentials"}})
    )

    with pytest.raises(UniFiAuthenticationError) as err:
        await client._handle_response(response)

    assert err.value.status_code == 401
    assert err.value.api_error_code == "invalid_credentials"
    assert response.text.call_count >= 2


async def test_validate_connection() -> None:
    """validate_connection verifies credentials via service plans."""
    session = _Session([{"data": [{"id": VALID_PLAN_ID_1}]}])
    client = _client(session)
    assert await client.validate_connection() is True
    assert session.requests[0]["url"] == "https://api.ui.com/v1/carrier/service-plans"
