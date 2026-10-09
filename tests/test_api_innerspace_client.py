# Copyright 2026 UniFi Insights contributors
"""Tests for UniFi InnerSpace API client pinning requests against the spec."""

from __future__ import annotations

import json
from typing import Any, Self

import pytest
from yarl import URL

from custom_components.unifi_insights.api.auth import ApiKeyAuth
from custom_components.unifi_insights.api.const import (
    INNERSPACE_API_BASE_URL,
    ConnectionType,
)
from custom_components.unifi_insights.api.exceptions import (
    UniFiAuthenticationError,
    UniFiNotFoundError,
    UniFiResponseError,
    UniFiValidationError,
)
from custom_components.unifi_insights.api.innerspace import UniFiInnerSpaceClient
from custom_components.unifi_insights.api.innerspace.client import (
    is_valid_asset_segment,
)
from custom_components.unifi_insights.api.innerspace.models import (
    InnerSpaceAccessPoint,
    InnerSpaceFloorPlan,
    InnerSpaceInventoryDevice,
    InnerSpaceProject,
    InnerSpaceSwitch,
)


class _Response:
    """Minimal aiohttp response replacement for transport tests."""

    def __init__(
        self,
        body: Any = None,
        status: int = 200,
        headers: dict[str, str] | None = None,
        raw_bytes: bytes = b"",
    ) -> None:
        self.status = status
        self._body = body
        self.headers = headers or {"Content-Type": "application/json"}
        self.content_type = self.headers.get("Content-Type", "application/json")
        self.url = URL("https://192.168.1.1")
        self.method = "GET"
        self.history = ()
        self._raw_bytes = raw_bytes

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *args: object) -> None:
        pass

    async def text(self) -> str:
        if isinstance(self._body, (dict, list)):
            return json.dumps(self._body)
        if self._body is None:
            return ""
        return str(self._body)

    async def json(self) -> Any:
        if self._body is None or isinstance(self._body, str):
            msg = "No JSON body"
            raise ValueError(msg)
        return self._body

    async def read(self) -> bytes:
        return self._raw_bytes


class _Session:
    """Mock session recording requests and returning queued responses."""

    closed = False

    def __init__(
        self, responses: list[_Response | dict[str, Any] | list[Any] | None]
    ) -> None:
        self._responses = iter(
            [r if isinstance(r, _Response) else _Response(r) for r in responses]
        )
        self.requests: list[dict[str, Any]] = []

    def request(self, method: str, url: object, **kwargs: Any) -> _Response:
        self.requests.append({"method": method, "url": str(url), **kwargs})
        return next(self._responses)

    def get(self, url: object, **kwargs: Any) -> _Response:
        self.requests.append({"method": "GET", "url": str(url), **kwargs})
        return next(self._responses)

    async def close(self) -> None:
        self.closed = True


def _client(
    session: _Session,
    *,
    connection_type: ConnectionType = ConnectionType.LOCAL,
    console_id: str | None = None,
) -> UniFiInnerSpaceClient:
    return UniFiInnerSpaceClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url=(
            "https://192.168.1.1"
            if connection_type == ConnectionType.LOCAL
            else INNERSPACE_API_BASE_URL
        ),
        connection_type=connection_type,
        console_id=console_id,
        session=session,  # type: ignore[arg-type]
    )


def _assert_requests(session: _Session, expected: list[tuple[str, Any]]) -> None:
    assert [
        (r["method"], r["url"], r.get("params"), r.get("json"))
        for r in session.requests
    ] == [
        (
            "GET",
            f"https://192.168.1.1/proxy/innerspace/integration/v1/{path}",
            params,
            None,
        )
        for path, params in expected
    ]


def test_init_validation() -> None:
    """Test initialization parameter validation."""
    auth = ApiKeyAuth(api_key="test-key")

    # LOCAL without base_url
    with pytest.raises(ValueError, match="base_url is required for LOCAL"):
        UniFiInnerSpaceClient(
            auth=auth,
            base_url=None,  # type: ignore[arg-type]
            connection_type=ConnectionType.LOCAL,
        )

    # REMOTE without console_id
    with pytest.raises(ValueError, match="console_id is required for REMOTE"):
        UniFiInnerSpaceClient(
            auth=auth,
            connection_type=ConnectionType.REMOTE,
            console_id=None,
        )

    # REMOTE with console_id uses default base_url
    remote_client = UniFiInnerSpaceClient(
        auth=auth,
        connection_type=ConnectionType.REMOTE,
        console_id="console-1",
    )
    assert remote_client.connection_type == ConnectionType.REMOTE
    assert remote_client.console_id == "console-1"
    assert str(remote_client.base_url) == INNERSPACE_API_BASE_URL


async def test_remote_connector_path() -> None:
    """A public call sends the full remote connector URL."""
    session = _Session([{"project": {"id": "proj-1", "title": "Office"}}])
    client = _client(
        session, connection_type=ConnectionType.REMOTE, console_id="console-xyz"
    )
    project = await client.get_project()
    assert project.project.id == "proj-1"
    assert len(session.requests) == 1
    assert session.requests[0]["method"] == "GET"
    assert (
        session.requests[0]["url"]
        == INNERSPACE_API_BASE_URL
        + "/v1/connector/consoles/console-xyz/innerspace/integration/v1/project"
    )
    assert session.requests[0]["params"] is None
    assert session.requests[0]["json"] is None


@pytest.mark.parametrize(
    "payload",
    [
        None,
        [{"id": "fp-1", "name": "Ground Floor"}],
        {"floor_plans": [{"id": "fp-1", "name": "Ground Floor"}]},
        {"data": {"floor_plans": [{"id": "fp-1", "name": "Ground Floor"}]}},
        {"data": [{"id": "fp-1", "name": "Ground Floor"}]},
    ],
)
async def test_list_response_envelopes(payload: Any) -> None:
    """Public floor-plan listing accepts supported transport envelopes."""
    session = _Session([payload])
    plans = await _client(session).list_floor_plans()
    assert [plan.id for plan in plans] == ([] if payload is None else ["fp-1"])
    _assert_requests(session, [("floor_plans", None)])


@pytest.mark.parametrize(
    "payload",
    [
        {"data": {"other": []}},
        {"data": 123},
        {"other": []},
        123,
        {"floor_plans": "not-a-list"},
        {"floor_plans": ["string-item"]},
    ],
)
async def test_malformed_list_responses(payload: Any) -> None:
    """Malformed HTTP payloads fail instead of looking like empty lists."""
    session = _Session([payload])
    with pytest.raises(UniFiResponseError) as exc_info:
        await _client(session).list_floor_plans()
    assert exc_info.value.status_code == 200
    assert exc_info.value.message == "/v1/floor_plans returned a malformed response"
    _assert_requests(session, [("floor_plans", None)])


async def test_get_project_success_and_modes() -> None:
    """Test get_project pinning against spec (GET /v1/project)."""
    project_payload = {
        "project": {"id": "proj-1", "title": "Main Office"},
        "plans": [],
    }
    session = _Session(
        [
            project_payload,
            {"data": project_payload},
            {"data": None},
        ]
    )
    client = _client(session)

    # Without mode
    res1 = await client.get_project()
    assert isinstance(res1, InnerSpaceProject)
    assert res1.project.id == "proj-1"
    assert session.requests[0]["method"] == "GET"
    assert (
        session.requests[0]["url"]
        == "https://192.168.1.1/proxy/innerspace/integration/v1/project"
    )
    assert session.requests[0]["params"] is None

    # With mode="3D" and expected_unsupported=True
    res2 = await client.get_project(mode="3D", expected_unsupported=True)
    assert isinstance(res2, InnerSpaceProject)
    assert res2.project.id == "proj-1"
    assert session.requests[1]["params"] == {"mode": "3D"}

    # Data is None -> empty InnerSpaceProject
    res3 = await client.get_project(mode="2D")
    assert isinstance(res3, InnerSpaceProject)
    assert res3.project is None
    assert session.requests[2]["params"] == {"mode": "2D"}

    _assert_requests(
        session,
        [("project", None), ("project", {"mode": "3D"}), ("project", {"mode": "2D"})],
    )


async def test_get_project_malformed() -> None:
    """Test get_project malformed response handling."""
    # Non-dict response
    session1 = _Session([["not a dict"]])
    client1 = _client(session1)
    with pytest.raises(UniFiResponseError):
        await client1.get_project()
    _assert_requests(session1, [("project", None)])

    # Data payload is not a dict
    session2 = _Session([{"data": 123}])
    client2 = _client(session2)
    with pytest.raises(UniFiResponseError):
        await client2.get_project()
    _assert_requests(session2, [("project", None)])

    # Dict payload without known keys
    session3 = _Session([{"unexpected_key": "value"}])
    client3 = _client(session3)
    with pytest.raises(UniFiResponseError):
        await client3.get_project()
    _assert_requests(session3, [("project", None)])


async def test_list_floor_plans() -> None:
    """Test list_floor_plans pinning against spec (GET /v1/floor_plans)."""
    plan_item = {"id": "fp-1", "name": "Ground Floor"}
    session = _Session(
        [
            {"floor_plans": [plan_item]},
            {"floor_plans": []},
        ]
    )
    client = _client(session)

    res1 = await client.list_floor_plans(site_id="default")
    assert len(res1) == 1
    assert isinstance(res1[0], InnerSpaceFloorPlan)
    assert res1[0].id == "fp-1"
    assert session.requests[0]["method"] == "GET"
    assert (
        session.requests[0]["url"]
        == "https://192.168.1.1/proxy/innerspace/integration/v1/floor_plans"
    )
    assert session.requests[0]["params"] == {"siteId": "default"}

    res2 = await client.list_floor_plans()
    assert res2 == []
    assert session.requests[1]["params"] is None

    _assert_requests(
        session, [("floor_plans", {"siteId": "default"}), ("floor_plans", None)]
    )


async def test_list_access_points() -> None:
    """Test list_access_points pinning against spec (GET /v1/access_points)."""
    ap_item = {"id": "ap-1", "name": "Hallway AP"}
    session = _Session(
        [
            {"access_points": [ap_item]},
            {"access_points": []},
        ]
    )
    client = _client(session)

    res1 = await client.list_access_points(site_id="site-1")
    assert len(res1) == 1
    assert isinstance(res1[0], InnerSpaceAccessPoint)
    assert res1[0].id == "ap-1"
    assert session.requests[0]["method"] == "GET"
    assert (
        session.requests[0]["url"]
        == "https://192.168.1.1/proxy/innerspace/integration/v1/access_points"
    )
    assert session.requests[0]["params"] == {"siteId": "site-1"}

    res2 = await client.list_access_points()
    assert res2 == []
    assert session.requests[1]["params"] is None

    _assert_requests(
        session, [("access_points", {"siteId": "site-1"}), ("access_points", None)]
    )


async def test_list_switches() -> None:
    """Test list_switches pinning against spec (GET /v1/switches)."""
    sw_item = {"id": "sw-1", "name": "Main Switch"}
    session = _Session(
        [
            {"switches": [sw_item]},
            {"switches": []},
        ]
    )
    client = _client(session)

    res1 = await client.list_switches(site_id="site-1")
    assert len(res1) == 1
    assert isinstance(res1[0], InnerSpaceSwitch)
    assert res1[0].id == "sw-1"
    assert session.requests[0]["method"] == "GET"
    assert (
        session.requests[0]["url"]
        == "https://192.168.1.1/proxy/innerspace/integration/v1/switches"
    )
    assert session.requests[0]["params"] == {"siteId": "site-1"}

    res2 = await client.list_switches()
    assert res2 == []
    assert session.requests[1]["params"] is None

    _assert_requests(session, [("switches", {"siteId": "site-1"}), ("switches", None)])


async def test_list_inventory() -> None:
    """Test list_inventory pinning against spec (GET /v1/inventory)."""
    inv_item = {"id": "inv-1", "name": "Spare Switch"}
    session = _Session(
        [
            {"devices": [inv_item]},
            {"devices": []},
        ]
    )
    client = _client(session)

    res1 = await client.list_inventory(site_id="site-1")
    assert len(res1) == 1
    assert isinstance(res1[0], InnerSpaceInventoryDevice)
    assert res1[0].id == "inv-1"
    assert session.requests[0]["method"] == "GET"
    assert (
        session.requests[0]["url"]
        == "https://192.168.1.1/proxy/innerspace/integration/v1/inventory"
    )
    assert session.requests[0]["params"] == {"siteId": "site-1"}

    res2 = await client.list_inventory()
    assert res2 == []
    assert session.requests[1]["params"] is None

    _assert_requests(
        session, [("inventory", {"siteId": "site-1"}), ("inventory", None)]
    )


async def test_download_floor_plan_image() -> None:
    """Test download_floor_plan_image pinning against spec.

    Path: GET /v1/assets/{planId}/{filename}
    """
    fake_png = b"dummy-png-data"
    resp = _Response(
        raw_bytes=fake_png,
        headers={"Content-Type": "image/png"},
    )
    session = _Session([resp])
    client = _client(session)

    # Valid call
    data, content_type = await client.download_floor_plan_image("plan-123", "map.png")
    assert data == fake_png
    assert content_type == "image/png"
    assert session.requests[0]["method"] == "GET"
    assert (
        session.requests[0]["url"]
        == "https://192.168.1.1/proxy/innerspace/integration/v1/assets/plan-123/map.png"
    )

    # Validation errors
    with pytest.raises(UniFiValidationError, match="Invalid floor plan ID"):
        await client.download_floor_plan_image("../escape", "map.png")

    with pytest.raises(UniFiValidationError, match="Invalid asset filename"):
        await client.download_floor_plan_image("plan-123", "../escape.png")

    _assert_requests(session, [("assets/plan-123/map.png", None)])


async def test_validate_connection() -> None:
    """Test validate_connection success and error handling."""
    session = _Session(
        [
            {"project": {"id": "proj-1", "title": "Office"}},
            _Response(status=500, body=None),
        ]
    )
    client = _client(session)

    # Success
    assert await client.validate_connection() is True

    # Error
    assert await client.validate_connection() is False

    _assert_requests(session, [("project", None), ("project", None)])


def test_is_valid_asset_segment() -> None:
    """Test asset segment validation branches."""
    assert is_valid_asset_segment("valid-name") is True
    assert is_valid_asset_segment("") is False
    assert is_valid_asset_segment("   ") is False
    assert is_valid_asset_segment("a" * 300) is False
    assert is_valid_asset_segment(".") is False
    assert is_valid_asset_segment("..") is False
    assert is_valid_asset_segment("path/slash") is False
    assert is_valid_asset_segment(r"path\backslash") is False
    assert is_valid_asset_segment("null" + chr(0) + "byte") is False


@pytest.mark.parametrize(
    ("status", "exception"),
    [
        (400, UniFiResponseError),
        (401, UniFiAuthenticationError),
        (403, UniFiAuthenticationError),
        (404, UniFiNotFoundError),
        (500, UniFiResponseError),
    ],
)
async def test_transport_error_mapping(status: int, exception: type[Exception]) -> None:
    """List endpoints propagate errors instead of returning empty inventories."""
    session = _Session([_Response({"error": "Request failed"}, status=status)])
    with pytest.raises(exception) as exc_info:
        await _client(session).list_floor_plans()
    assert exc_info.value.status_code == status
    _assert_requests(session, [("floor_plans", None)])
