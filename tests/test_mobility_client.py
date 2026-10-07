# Copyright 2026 UniFi Insights contributors
"""Tests for the UniFi Mobility API client."""

from __future__ import annotations

import logging
from typing import Any, Self
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.unifi_insights.api.auth import ApiKeyAuth
from custom_components.unifi_insights.api.exceptions import (
    UniFiAuthenticationError,
    UniFiNotFoundError,
    UniFiResponseError,
    UniFiValidationError,
)
from custom_components.unifi_insights.api.mobility import UniFiMobilityClient
from custom_components.unifi_insights.api.mobility.client import (
    _MAX_ITEMS,
    _MAX_PAGES,
    _PAGE_SIZE,
)

_WORKSPACE_ID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
_DEVICE_ID = "550e8400-e29b-41d4-a716-446655440000"


class _Response:
    """Minimal aiohttp response replacement for transport tests."""

    def __init__(self, body: Any = None, status: int = 200) -> None:
        """Store a JSON response body and status."""
        self._body = body
        self.status = status
        self.headers: dict[str, str] = {}

    async def __aenter__(self) -> Self:
        """Enter the async response context."""
        return self

    async def __aexit__(self, *args: object) -> None:
        """Exit the async response context."""

    async def text(self) -> str:
        """Return empty body for 204 No Content or a JSON string."""
        if self.status == 204 or self._body is None:
            return ""
        return "{}"

    async def json(self) -> Any:
        """Return the response body."""
        return self._body


class _Session:
    """Queued response transport recording requests made by the client."""

    closed = False

    def __init__(self, responses: list[Any]) -> None:
        """Initialize queued JSON bodies or prepared responses."""
        self._responses = iter(responses)
        self.requests: list[dict[str, Any]] = []

    def request(self, method: str, url: object, **kwargs: Any) -> _Response:
        """Record a request and return the next configured response."""
        self.requests.append({"method": method, "url": str(url), **kwargs})
        response = next(self._responses)
        return response if isinstance(response, _Response) else _Response(response)


def _client(session: _Session) -> UniFiMobilityClient:
    """Create a Mobility client using a recording transport."""
    return UniFiMobilityClient(ApiKeyAuth("test-key"), session=session)  # type: ignore[arg-type]


def _page(rows: list[dict[str, Any]], **meta: Any) -> dict[str, Any]:
    """Build a paginated Mobility envelope."""
    return {"data": rows, "httpStatusCode": 200, "traceId": "trace", **meta}


async def test_list_workspaces_reads_the_cloud_endpoint() -> None:
    """Workspaces come from the account-wide Mobility endpoint."""
    rows = [{"workspace_id": _WORKSPACE_ID, "workspace_name": "HQ"}]
    session = _Session([_page(rows, total=1, offset=0, limit=0)])

    assert await _client(session).list_workspaces() == rows
    assert session.requests[0]["method"] == "GET"
    assert session.requests[0]["url"] == "https://api.ui.com/v1/mobility/workspaces"
    assert session.requests[0]["headers"]["X-API-Key"] == "test-key"


@pytest.mark.parametrize(
    "body",
    [None, [], {"data": None}, {"data": {"workspace_id": "x"}}, {"data": ["x"]}],
)
async def test_malformed_workspace_envelope_is_an_error(body: Any) -> None:
    """A successful response without a list of records is never treated as empty."""
    session = _Session([body])

    with pytest.raises(UniFiResponseError):
        await _client(session).list_workspaces()


async def test_list_devices_pages_by_offset_until_total() -> None:
    """Device pages are requested by offset until the advertised total is read."""
    first = [{"id": f"device-{index}"} for index in range(_PAGE_SIZE)]
    second = [{"id": "device-last"}]
    session = _Session(
        [
            _page(first, total=_PAGE_SIZE + 1, offset=0, limit=_PAGE_SIZE),
            _page(second, total=_PAGE_SIZE + 1, offset=_PAGE_SIZE, limit=_PAGE_SIZE),
        ]
    )

    devices = await _client(session).list_devices(_WORKSPACE_ID)

    assert devices == [*first, *second]
    assert [request["params"] for request in session.requests] == [
        {"limit": _PAGE_SIZE, "offset": 0},
        {"limit": _PAGE_SIZE, "offset": _PAGE_SIZE},
    ]
    assert session.requests[0]["url"] == (
        f"https://api.ui.com/v1/mobility/workspaces/{_WORKSPACE_ID}/devices"
    )


async def test_list_devices_stops_on_a_short_page_without_total() -> None:
    """A page shorter than the page size is the last one, even without a total."""
    session = _Session([_page([{"id": "only"}])])

    assert await _client(session).list_devices(_WORKSPACE_ID) == [{"id": "only"}]
    assert len(session.requests) == 1


async def test_list_devices_stops_on_an_empty_page() -> None:
    """A full page followed by an empty one ends pagination."""
    full = [{"id": f"device-{index}"} for index in range(_PAGE_SIZE)]
    session = _Session([_page(full), _page([])])

    assert await _client(session).list_devices(_WORKSPACE_ID) == full
    assert len(session.requests) == 2


async def test_list_devices_enforces_the_page_cap() -> None:
    """A server that never stops returning full pages is cut off."""
    full = [{"id": f"device-{index}"} for index in range(_PAGE_SIZE)]
    session = _Session([_page(full)] * (_MAX_PAGES + 1))

    with pytest.raises(UniFiResponseError) as excinfo:
        await _client(session).list_devices(_WORKSPACE_ID)
    assert "page limit" in excinfo.value.message
    assert len(session.requests) == _MAX_PAGES


async def test_list_devices_enforces_the_item_cap() -> None:
    """A page larger than requested cannot grow the result beyond the item cap."""
    oversized = [{"id": f"device-{index}"} for index in range(_MAX_ITEMS + 1)]
    session = _Session([_page(oversized, total=_MAX_ITEMS * 2)])

    with pytest.raises(UniFiResponseError) as excinfo:
        await _client(session).list_devices(_WORKSPACE_ID)
    assert "item limit" in excinfo.value.message


async def test_get_device_returns_the_detail_record() -> None:
    """Device detail is a single record, not a list."""
    detail = {"id": _DEVICE_ID, "client_count": 5}
    session = _Session([{"data": detail, "httpStatusCode": 200, "traceId": "t"}])

    assert await _client(session).get_device(_WORKSPACE_ID, _DEVICE_ID) == detail
    assert session.requests[0]["url"] == (
        "https://api.ui.com/v1/mobility/workspaces/"
        f"{_WORKSPACE_ID}/devices/{_DEVICE_ID}"
    )


@pytest.mark.parametrize("body", [None, [], {"data": None}, {"data": [{}]}])
async def test_malformed_device_detail_is_an_error(body: Any) -> None:
    """A detail response without a record is rejected."""
    with pytest.raises(UniFiResponseError):
        await _client(_Session([body])).get_device(_WORKSPACE_ID, _DEVICE_ID)


@pytest.mark.parametrize("unsafe", ["", "../admins", "a/b", "a?b", "x" * 65, None])
async def test_unsafe_identifiers_are_rejected_before_any_request(
    unsafe: Any,
) -> None:
    """Identifiers are path segments, so anything but a plain id is refused."""
    session = _Session([])
    client = _client(session)

    with pytest.raises(UniFiValidationError):
        await client.list_devices(unsafe)
    with pytest.raises(UniFiValidationError):
        await client.get_device(_WORKSPACE_ID, unsafe)
    assert session.requests == []


@pytest.mark.parametrize(
    ("status", "error"),
    [
        (401, UniFiAuthenticationError),
        (403, UniFiAuthenticationError),
        (404, UniFiNotFoundError),
        (500, UniFiResponseError),
    ],
)
async def test_http_errors_map_to_the_shared_exceptions(
    status: int, error: type[Exception]
) -> None:
    """Mobility uses the vendored client's error mapping."""
    body = {"code": "forbidden", "httpStatusCode": status, "traceId": "t"}
    session = _Session([_Response(body, status=status)])

    with pytest.raises(error):
        await _client(session).get_device(_WORKSPACE_ID, _DEVICE_ID)


async def test_validate_connection_lists_workspaces() -> None:
    """Validation succeeds when the key can list Mobility workspaces."""
    session = _Session([_page([])])

    assert await _client(session).validate_connection() is True
    assert session.requests[0]["url"].endswith("/v1/mobility/workspaces")


def test_client_paces_requests_to_the_mobility_rate_limit() -> None:
    """The documented 100 requests per minute per key is enforced client side."""
    client = _client(_Session([]))

    assert client.RATE_LIMIT == (100, 60.0)
    assert client._rate_limiter is not None


async def test_mobility_response_bodies_are_not_logged(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Router inventory, IPs and GPS fixes stay out of transport logs."""
    client = _client(_Session([]))
    response = MagicMock(status=200, method="GET")
    response.url.path = "/v1/mobility/workspaces"
    response.text = AsyncMock(return_value='{"wan_ip":"203.0.113.42"}')
    response.json = AsyncMock(return_value={"data": []})

    with caplog.at_level(
        logging.DEBUG, logger="custom_components.unifi_insights.api.base"
    ):
        await client._handle_response(response)
        response.json.side_effect = ValueError("invalid JSON")
        with pytest.raises(UniFiResponseError):
            await client._handle_response(response)

    assert "203.0.113.42" not in caplog.text
    assert "[Mobility response omitted]" in caplog.text


async def test_list_workspace_admins_reads_the_admins_endpoint() -> None:
    """Workspace admins come from the /admins sub-resource."""
    rows = [
        {
            "name": "Alice Owner",
            "email": "alice@example.com",
            "status": "ACTIVE",
            "is_owner": True,
            "permissions": {"umr": "ALL"},
        }
    ]
    session = _Session([_page(rows, total=1, offset=0, limit=0)])

    assert await _client(session).list_workspace_admins(_WORKSPACE_ID) == rows
    assert session.requests[0]["method"] == "GET"
    assert session.requests[0]["url"] == (
        f"https://api.ui.com/v1/mobility/workspaces/{_WORKSPACE_ID}/admins"
    )
    assert session.requests[0]["headers"]["X-API-Key"] == "test-key"


@pytest.mark.parametrize(
    "body",
    [None, [], {"data": None}, {"data": {"name": "Alice"}}, {"data": ["invalid"]}],
)
async def test_malformed_workspace_admins_envelope_is_an_error(body: Any) -> None:
    """An admins response without a list of records is rejected."""
    session = _Session([body])

    with pytest.raises(UniFiResponseError):
        await _client(session).list_workspace_admins(_WORKSPACE_ID)


@pytest.mark.parametrize("unsafe", ["", "../workspaces", "a/b", "a?b", "x" * 65, None])
async def test_list_workspace_admins_rejects_unsafe_id(unsafe: Any) -> None:
    """Workspace id in list_workspace_admins is checked with _safe_id."""
    session = _Session([])
    with pytest.raises(UniFiValidationError):
        await _client(session).list_workspace_admins(unsafe)
    assert session.requests == []


async def test_list_device_clients_pages_by_offset_until_total() -> None:
    """Device client pages are read by offset until total is reached."""
    first = [{"mac": f"00:11:22:33:44:{index:02x}"} for index in range(_PAGE_SIZE)]
    second = [{"mac": "00:11:22:33:44:ff"}]
    session = _Session(
        [
            _page(first, total=_PAGE_SIZE + 1, offset=0, limit=_PAGE_SIZE),
            _page(second, total=_PAGE_SIZE + 1, offset=_PAGE_SIZE, limit=_PAGE_SIZE),
        ]
    )

    clients = await _client(session).list_device_clients(_WORKSPACE_ID, _DEVICE_ID)

    assert clients == [*first, *second]
    assert [request["params"] for request in session.requests] == [
        {"limit": _PAGE_SIZE, "offset": 0},
        {"limit": _PAGE_SIZE, "offset": _PAGE_SIZE},
    ]
    assert session.requests[0]["url"] == (
        f"https://api.ui.com/v1/mobility/workspaces/{_WORKSPACE_ID}"
        f"/devices/{_DEVICE_ID}/clients"
    )


async def test_list_device_clients_stops_on_a_short_page_without_total() -> None:
    """A page shorter than the page size is the last one, even without a total."""
    session = _Session([_page([{"mac": "AA:BB:CC:DD:EE:FF"}])])

    assert await _client(session).list_device_clients(_WORKSPACE_ID, _DEVICE_ID) == [
        {"mac": "AA:BB:CC:DD:EE:FF"}
    ]
    assert len(session.requests) == 1


async def test_list_device_clients_stops_on_an_empty_page() -> None:
    """A full page followed by an empty one ends pagination."""
    full = [{"mac": f"00:11:22:33:44:{index:02x}"} for index in range(_PAGE_SIZE)]
    session = _Session([_page(full), _page([])])

    assert await _client(session).list_device_clients(_WORKSPACE_ID, _DEVICE_ID) == full
    assert len(session.requests) == 2


async def test_list_device_clients_enforces_the_page_cap() -> None:
    """A server that never stops returning full pages is cut off."""
    full = [{"mac": f"00:11:22:33:44:{index:02x}"} for index in range(_PAGE_SIZE)]
    session = _Session([_page(full)] * (_MAX_PAGES + 1))

    with pytest.raises(UniFiResponseError) as excinfo:
        await _client(session).list_device_clients(_WORKSPACE_ID, _DEVICE_ID)
    assert "page limit" in excinfo.value.message
    assert len(session.requests) == _MAX_PAGES


async def test_list_device_clients_enforces_the_item_cap() -> None:
    """A page larger than requested cannot grow the result beyond the item cap."""
    oversized = [
        {"mac": f"00:11:22:33:44:{index:02x}"} for index in range(_MAX_ITEMS + 1)
    ]
    session = _Session([_page(oversized, total=_MAX_ITEMS * 2)])

    with pytest.raises(UniFiResponseError) as excinfo:
        await _client(session).list_device_clients(_WORKSPACE_ID, _DEVICE_ID)
    assert "item limit" in excinfo.value.message


@pytest.mark.parametrize("unsafe", ["", "../clients", "a/b", "a?b", "x" * 65, None])
async def test_list_device_clients_rejects_unsafe_identifiers(unsafe: Any) -> None:
    """Both workspace and device identifiers are checked before making a request."""
    session = _Session([])
    client = _client(session)

    with pytest.raises(UniFiValidationError):
        await client.list_device_clients(unsafe, _DEVICE_ID)
    with pytest.raises(UniFiValidationError):
        await client.list_device_clients(_WORKSPACE_ID, unsafe)
    assert session.requests == []


async def test_update_device_name_pins_verb_path_and_body() -> None:
    """Renaming a device sends PUT to the device resource with the new name."""
    session = _Session([_Response(status=204)])

    await _client(session).update_device_name(
        _WORKSPACE_ID, _DEVICE_ID, name="Branch Office Router"
    )

    assert len(session.requests) == 1
    assert session.requests[0]["method"] == "PUT"
    assert session.requests[0]["url"] == (
        f"https://api.ui.com/v1/mobility/workspaces/{_WORKSPACE_ID}"
        f"/devices/{_DEVICE_ID}"
    )
    assert session.requests[0]["headers"]["X-API-Key"] == "test-key"
    assert session.requests[0]["json"] == {"name": "Branch Office Router"}


@pytest.mark.parametrize("missing_name", [None, 123, ["name"]])
async def test_update_device_name_validates_required_name(
    missing_name: Any,
) -> None:
    """A missing or non-string device name raises UniFiValidationError."""
    session = _Session([])
    client = _client(session)

    with pytest.raises(UniFiValidationError):
        await client.update_device_name(_WORKSPACE_ID, _DEVICE_ID, name=missing_name)
    assert session.requests == []


@pytest.mark.parametrize("unsafe", ["", "../devices", "a/b", "a?b", "x" * 65, None])
async def test_update_device_name_rejects_unsafe_identifiers(unsafe: Any) -> None:
    """Both workspace and device identifiers are checked before renaming."""
    session = _Session([])
    client = _client(session)

    with pytest.raises(UniFiValidationError):
        await client.update_device_name(unsafe, _DEVICE_ID, name="Valid Name")
    with pytest.raises(UniFiValidationError):
        await client.update_device_name(_WORKSPACE_ID, unsafe, name="Valid Name")
    assert session.requests == []


async def test_update_device_network_pins_verb_path_and_body() -> None:
    """Updating LAN / DHCP settings sends PUT to the /network sub-resource."""
    session = _Session([_Response(status=204)])

    await _client(session).update_device_network(
        _WORKSPACE_ID,
        _DEVICE_ID,
        host_address="192.168.10.1",
        dhcp_mode="dhcp",
        dhcp_range_start="192.168.10.100",
        dhcp_range_stop="192.168.10.200",
        dhcp_lease_time=86400,
    )

    assert len(session.requests) == 1
    assert session.requests[0]["method"] == "PUT"
    assert session.requests[0]["url"] == (
        f"https://api.ui.com/v1/mobility/workspaces/{_WORKSPACE_ID}"
        f"/devices/{_DEVICE_ID}/network"
    )
    assert session.requests[0]["headers"]["X-API-Key"] == "test-key"
    assert session.requests[0]["json"] == {
        "host_address": "192.168.10.1",
        "dhcp_mode": "dhcp",
        "dhcp_range_start": "192.168.10.100",
        "dhcp_range_stop": "192.168.10.200",
        "dhcp_lease_time": 86400,
    }


async def test_update_device_network_accepts_partial_fields() -> None:
    """update_device_network sends non-None fields, preserving lease time 0."""
    session1 = _Session([_Response(status=204)])
    await _client(session1).update_device_network(
        _WORKSPACE_ID, _DEVICE_ID, dhcp_mode="none"
    )
    assert session1.requests[0]["json"] == {"dhcp_mode": "none"}

    session2 = _Session([_Response(status=204)])
    await _client(session2).update_device_network(
        _WORKSPACE_ID, _DEVICE_ID, host_address="192.168.10.1"
    )
    assert session2.requests[0]["json"] == {"host_address": "192.168.10.1"}

    session3 = _Session([_Response(status=204)])
    await _client(session3).update_device_network(
        _WORKSPACE_ID,
        _DEVICE_ID,
        dhcp_mode="dhcp",
        dhcp_lease_time=0,
    )
    assert session3.requests[0]["json"] == {
        "dhcp_mode": "dhcp",
        "dhcp_lease_time": 0,
    }

    session4 = _Session([_Response(status=204)])
    await _client(session4).update_device_network(_WORKSPACE_ID, _DEVICE_ID)
    assert session4.requests[0]["json"] == {}


@pytest.mark.parametrize("unsafe", ["", "../network", "a/b", "a?b", "x" * 65, None])
async def test_update_device_network_rejects_unsafe_identifiers(
    unsafe: Any,
) -> None:
    """Both workspace and device identifiers are checked before network update."""
    session = _Session([])
    client = _client(session)

    with pytest.raises(UniFiValidationError):
        await client.update_device_network(unsafe, _DEVICE_ID, dhcp_mode="none")
    with pytest.raises(UniFiValidationError):
        await client.update_device_network(_WORKSPACE_ID, unsafe, dhcp_mode="none")
    assert session.requests == []


async def test_update_device_wireless_pins_verb_path_and_body() -> None:
    """Updating WiFi settings sends PUT to the /wireless sub-resource."""
    session = _Session([_Response(status=204)])

    await _client(session).update_device_wireless(
        _WORKSPACE_ID,
        _DEVICE_ID,
        ssid="MyNetwork",
        password="securepass123",  # noqa: S106
    )

    assert len(session.requests) == 1
    assert session.requests[0]["method"] == "PUT"
    assert session.requests[0]["url"] == (
        f"https://api.ui.com/v1/mobility/workspaces/{_WORKSPACE_ID}"
        f"/devices/{_DEVICE_ID}/wireless"
    )
    assert session.requests[0]["headers"]["X-API-Key"] == "test-key"
    assert session.requests[0]["json"] == {
        "ssid": "MyNetwork",
        "password": "securepass123",
    }


@pytest.mark.parametrize(
    ("ssid", "password"),
    [
        (None, "pass"),
        ("ssid", None),
        (None, None),
        (123, "pass"),
        ("ssid", 456),
    ],
)
async def test_update_device_wireless_validates_required_fields(
    ssid: Any, password: Any
) -> None:
    """Both ssid and password are required strings."""
    session = _Session([])
    client = _client(session)

    with pytest.raises(UniFiValidationError):
        await client.update_device_wireless(
            _WORKSPACE_ID, _DEVICE_ID, ssid=ssid, password=password
        )
    assert session.requests == []


async def test_update_endpoints_enforce_keyword_only_arguments() -> None:
    """Update endpoints reject positional arguments for update fields."""
    session = _Session([])
    client = _client(session)

    with pytest.raises(TypeError):
        await client.update_device_name(  # type: ignore[misc]
            _WORKSPACE_ID, _DEVICE_ID, "Branch Office Router"
        )
    with pytest.raises(TypeError):
        await client.update_device_network(  # type: ignore[call-arg]
            _WORKSPACE_ID, _DEVICE_ID, "192.168.10.1"
        )
    with pytest.raises(TypeError):
        await client.update_device_wireless(  # type: ignore[misc]
            _WORKSPACE_ID, _DEVICE_ID, "MyNetwork", "test-password"
        )
    assert session.requests == []


@pytest.mark.parametrize("unsafe", ["", "../wireless", "a/b", "a?b", "x" * 65, None])
async def test_update_device_wireless_rejects_unsafe_identifiers(
    unsafe: Any,
) -> None:
    """Both workspace and device identifiers are checked before wireless update."""
    session = _Session([])
    client = _client(session)

    with pytest.raises(UniFiValidationError):
        await client.update_device_wireless(
            unsafe,
            _DEVICE_ID,
            ssid="net",
            password="pass",  # noqa: S106
        )
    with pytest.raises(UniFiValidationError):
        await client.update_device_wireless(
            _WORKSPACE_ID,
            unsafe,
            ssid="net",
            password="pass",  # noqa: S106
        )
    assert session.requests == []


@pytest.mark.parametrize(
    ("status", "error"),
    [
        (401, UniFiAuthenticationError),
        (403, UniFiAuthenticationError),
        (404, UniFiNotFoundError),
        (500, UniFiResponseError),
    ],
)
async def test_put_endpoints_map_http_errors(
    status: int, error: type[Exception]
) -> None:
    """PUT endpoints map HTTP error codes to the shared UniFi exceptions."""
    body = {"code": "upstream_error", "httpStatusCode": status, "traceId": "t"}

    session_name = _Session([_Response(body, status=status)])
    with pytest.raises(error):
        await _client(session_name).update_device_name(
            _WORKSPACE_ID, _DEVICE_ID, name="test"
        )

    session_net = _Session([_Response(body, status=status)])
    with pytest.raises(error):
        await _client(session_net).update_device_network(
            _WORKSPACE_ID, _DEVICE_ID, dhcp_mode="none"
        )

    session_wifi = _Session([_Response(body, status=status)])
    with pytest.raises(error):
        await _client(session_wifi).update_device_wireless(
            _WORKSPACE_ID,
            _DEVICE_ID,
            ssid="test",
            password="password123",  # noqa: S106
        )
