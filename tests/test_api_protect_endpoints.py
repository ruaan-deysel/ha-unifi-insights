# Copyright 2026
"""Tests for vendored UniFi Protect API client endpoints and plumbing."""

from __future__ import annotations

import json
from typing import Any, NamedTuple
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from custom_components.unifi_insights.api import ApiKeyAuth, ConnectionType
from custom_components.unifi_insights.api.exceptions import (
    UniFiConnectionError,
    UniFiResponseError,
    UniFiTimeoutError,
)
from custom_components.unifi_insights.api.protect import (
    NVR,
    Camera,
    Chime,
    Light,
    LightMode,
    LiveView,
    Sensor,
    UniFiProtectClient,
)
from custom_components.unifi_insights.api.protect.models.files import RTSPSStream
from custom_components.unifi_insights.api.protect.models.viewer import Viewer

SAMPLE_CAMERA: dict[str, Any] = {
    "id": "cam-1",
    "mac": "00:11:22:33:44:01",
    "name": "Camera 1",
}
SAMPLE_CHIME: dict[str, Any] = {
    "id": "chime-1",
    "mac": "00:11:22:33:44:02",
    "name": "Chime 1",
}
SAMPLE_LIGHT: dict[str, Any] = {
    "id": "light-1",
    "mac": "00:11:22:33:44:03",
    "name": "Light 1",
}
SAMPLE_LIVEVIEW: dict[str, Any] = {
    "id": "lv-1",
    "name": "Overview",
}
SAMPLE_NVR: dict[str, Any] = {
    "id": "nvr-1",
    "name": "UNVR",
}
SAMPLE_SENSOR: dict[str, Any] = {
    "id": "sensor-1",
    "mac": "00:11:22:33:44:04",
    "name": "Sensor 1",
}
SAMPLE_VIEWER: dict[str, Any] = {
    "id": "viewer-1",
    "mac": "00:11:22:33:44:05",
    "name": "Viewer 1",
    "state": "CONNECTED",
}
SAMPLE_RTSPS: dict[str, Any] = {
    "high": "rtsps://192.168.1.1:7441/high",
}


class EndpointCase(NamedTuple):
    """Specification of an endpoint call and its expected wire format."""

    name: str
    call_fn: Any
    expected_method: str
    expected_path: str
    expected_params: Any
    expected_body: Any
    resp_payload: Any
    check_fn: Any


def make_client(
    *,
    status: int = 200,
    json_data: Any = None,
    raw_bytes: bytes = b"",
    connection_type: ConnectionType = ConnectionType.LOCAL,
    console_id: str | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[UniFiProtectClient, MagicMock, MagicMock]:
    """Create a UniFiProtectClient with mocked HTTP session."""
    resp = MagicMock()
    resp.status = status
    resp.headers = headers or {"Content-Type": "application/json"}
    resp.text = AsyncMock(
        return_value=json.dumps(json_data) if json_data is not None else ""
    )
    resp.json = AsyncMock(return_value=json_data if json_data is not None else {})
    resp.read = AsyncMock(return_value=raw_bytes)
    resp.history = ()

    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=resp)
    ctx.__aexit__ = AsyncMock(return_value=None)

    session = MagicMock()
    session.closed = False
    session.request = MagicMock(return_value=ctx)
    session.get = MagicMock(return_value=ctx)

    client = UniFiProtectClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url=(
            "https://192.168.1.1"
            if connection_type == ConnectionType.LOCAL
            else "https://api.ui.com"
        ),
        connection_type=connection_type,
        console_id=console_id
        or ("console-1" if connection_type == ConnectionType.REMOTE else None),
        session=session,
    )
    return client, session, resp


# Parametrized table test for request pinning
ENDPOINT_CASES = [
    EndpointCase(
        "application.trigger_alarm_webhook",
        lambda c: c.application.trigger_alarm_webhook("trig-1"),
        "POST",
        "/proxy/protect/integration/v1/alarm-manager/webhook/trig-1",
        None,
        None,
        None,
        lambda r: r is True,
    ),
    EndpointCase(
        "cameras.set_microphone_volume",
        lambda c: c.cameras.set_microphone_volume("cam-1", 75),
        "PATCH",
        "/proxy/protect/integration/v1/cameras/cam-1",
        None,
        {"micVolume": 75},
        SAMPLE_CAMERA,
        lambda r: isinstance(r, Camera) and r.id == "cam-1",
    ),
    EndpointCase(
        "cameras.ptz_goto_preset",
        lambda c: c.cameras.ptz_goto_preset("cam-1", "preset-2"),
        "POST",
        "/proxy/protect/integration/v1/cameras/cam-1/ptz/goto/preset-2",
        None,
        None,
        None,
        lambda r: r is True,
    ),
    EndpointCase(
        "cameras.ptz_patrol_start",
        lambda c: c.cameras.ptz_patrol_start("cam-1", 3),
        "POST",
        "/proxy/protect/integration/v1/cameras/cam-1/ptz/patrol/start/3",
        None,
        None,
        None,
        lambda r: r is True,
    ),
    EndpointCase(
        "cameras.ptz_patrol_stop",
        lambda c: c.cameras.ptz_patrol_stop("cam-1"),
        "POST",
        "/proxy/protect/integration/v1/cameras/cam-1/ptz/patrol/stop",
        None,
        None,
        None,
        lambda r: r is True,
    ),
    EndpointCase(
        "cameras.create_rtsps_stream",
        lambda c: c.cameras.create_rtsps_stream("cam-1"),
        "POST",
        "/proxy/protect/integration/v1/cameras/cam-1/rtsps-stream",
        None,
        {"qualities": ["high"]},
        SAMPLE_RTSPS,
        lambda r: isinstance(r, RTSPSStream) and r.high == SAMPLE_RTSPS["high"],
    ),
    EndpointCase(
        "cameras.set_hdr_mode",
        lambda c: c.cameras.set_hdr_mode("cam-1", "auto"),
        "PATCH",
        "/proxy/protect/integration/v1/cameras/cam-1",
        None,
        {"hdrType": "auto"},
        SAMPLE_CAMERA,
        lambda r: isinstance(r, Camera) and r.id == "cam-1",
    ),
    EndpointCase(
        "chimes.get_all",
        lambda c: c.chimes.get_all(),
        "GET",
        "/proxy/protect/integration/v1/chimes",
        None,
        None,
        [SAMPLE_CHIME],
        lambda r: len(r) == 1 and isinstance(r[0], Chime) and r[0].id == "chime-1",
    ),
    EndpointCase(
        "chimes.update",
        lambda c: c.chimes.update("chime-1", name="Front Door Chime"),
        "PATCH",
        "/proxy/protect/integration/v1/chimes/chime-1",
        None,
        {"name": "Front Door Chime"},
        SAMPLE_CHIME,
        lambda r: isinstance(r, Chime) and r.id == "chime-1",
    ),
    EndpointCase(
        "lights.get_all",
        lambda c: c.lights.get_all(),
        "GET",
        "/proxy/protect/integration/v1/lights",
        None,
        None,
        [SAMPLE_LIGHT],
        lambda r: len(r) == 1 and isinstance(r[0], Light) and r[0].id == "light-1",
    ),
    EndpointCase(
        "liveviews.get_all",
        lambda c: c.liveviews.get_all(),
        "GET",
        "/proxy/protect/integration/v1/liveviews",
        None,
        None,
        [SAMPLE_LIVEVIEW],
        lambda r: len(r) == 1 and isinstance(r[0], LiveView) and r[0].id == "lv-1",
    ),
    EndpointCase(
        "liveviews.create",
        lambda c: c.liveviews.create(name="Yard", layout=4),
        "POST",
        "/proxy/protect/integration/v1/liveviews",
        None,
        {"name": "Yard", "layout": 4},
        SAMPLE_LIVEVIEW,
        lambda r: isinstance(r, LiveView) and r.id == "lv-1",
    ),
    EndpointCase(
        "nvr.get",
        lambda c: c.nvr.get(),
        "GET",
        "/proxy/protect/integration/v1/nvrs",
        None,
        None,
        SAMPLE_NVR,
        lambda r: isinstance(r, NVR) and r.id == "nvr-1",
    ),
    EndpointCase(
        "sensors.get_all",
        lambda c: c.sensors.get_all(),
        "GET",
        "/proxy/protect/integration/v1/sensors",
        None,
        None,
        [SAMPLE_SENSOR],
        lambda r: len(r) == 1 and isinstance(r[0], Sensor) and r[0].id == "sensor-1",
    ),
    EndpointCase(
        "viewers.get_all",
        lambda c: c.viewers.get_all(),
        "GET",
        "/proxy/protect/integration/v1/viewers",
        None,
        None,
        [SAMPLE_VIEWER],
        lambda r: len(r) == 1 and isinstance(r[0], Viewer) and r[0].id == "viewer-1",
    ),
    EndpointCase(
        "viewers.update",
        lambda c: c.viewers.update("viewer-1", name="Kitchen Viewport"),
        "PATCH",
        "/proxy/protect/integration/v1/viewers/viewer-1",
        None,
        {"name": "Kitchen Viewport"},
        SAMPLE_VIEWER,
        lambda r: isinstance(r, Viewer) and r.id == "viewer-1",
    ),
    EndpointCase(
        "cameras.get_all",
        lambda c: c.cameras.get_all(),
        "GET",
        "/proxy/protect/integration/v1/cameras",
        None,
        None,
        [SAMPLE_CAMERA],
        lambda r: len(r) == 1 and isinstance(r[0], Camera) and r[0].id == "cam-1",
    ),
    EndpointCase(
        "cameras.update",
        lambda c: c.cameras.update("cam-1", name="Porch Camera"),
        "PATCH",
        "/proxy/protect/integration/v1/cameras/cam-1",
        None,
        {"name": "Porch Camera"},
        SAMPLE_CAMERA,
        lambda r: isinstance(r, Camera) and r.id == "cam-1",
    ),
    EndpointCase(
        "lights.update",
        lambda c: c.lights.update("light-1", name="Driveway Flood"),
        "PATCH",
        "/proxy/protect/integration/v1/lights/light-1",
        None,
        {"name": "Driveway Flood"},
        SAMPLE_LIGHT,
        lambda r: isinstance(r, Light) and r.id == "light-1",
    ),
    EndpointCase(
        "lights.set_mode",
        lambda c: c.lights.set_mode("light-1", LightMode.MOTION),
        "PATCH",
        "/proxy/protect/integration/v1/lights/light-1",
        None,
        {"lightModeSettings": {"mode": "motion"}},
        SAMPLE_LIGHT,
        lambda r: isinstance(r, Light) and r.id == "light-1",
    ),
]


@pytest.mark.parametrize(
    "case",
    ENDPOINT_CASES,
    ids=[c.name for c in ENDPOINT_CASES],
)
@pytest.mark.asyncio
async def test_protect_endpoint_request_pinning(case: EndpointCase) -> None:
    """Verify HTTP method, path, params, body, and response parsing."""
    client, session, _ = make_client(json_data=case.resp_payload)
    result = await case.call_fn(client)

    session.request.assert_called_once()
    method_called, url_called = session.request.call_args[0][:2]
    kwargs = session.request.call_args[1]

    assert method_called == case.expected_method
    assert str(url_called).endswith(case.expected_path)
    assert kwargs.get("params") == case.expected_params
    assert kwargs.get("json") == case.expected_body
    assert case.check_fn(result)


@pytest.mark.parametrize(
    "case",
    ENDPOINT_CASES,
    ids=[c.name for c in ENDPOINT_CASES],
)
@pytest.mark.asyncio
async def test_protect_endpoint_error_mapping(case: EndpointCase) -> None:
    """Verify failure HTTP status maps to UniFiResponseError."""
    client, _, _ = make_client(
        status=500,
        json_data={"error": "Internal server error"},
    )
    with pytest.raises(UniFiResponseError):
        await case.call_fn(client)


@pytest.mark.asyncio
async def test_cameras_get_snapshot_request_pinning() -> None:
    """Verify get_snapshot sends binary GET request and returns bytes."""
    fake_png = b"test-image-png-bytes"
    client, session, _ = make_client(raw_bytes=fake_png)

    data = await client.cameras.get_snapshot("cam-1")
    assert data == fake_png

    session.get.assert_called_once()
    url_called = str(session.get.call_args[0][0])
    assert url_called.endswith("/proxy/protect/integration/v1/cameras/cam-1/snapshot")
    assert session.get.call_args[1].get("params") is None


@pytest.mark.asyncio
async def test_cameras_get_snapshot_high_quality() -> None:
    """Verify high_quality sends highQuality=true query parameter."""
    client, session, _ = make_client(raw_bytes=b"snapshot-hd")

    await client.cameras.get_snapshot("cam-1", high_quality=True)
    assert session.get.call_args[1].get("params") == {"highQuality": "true"}


@pytest.mark.asyncio
async def test_cameras_get_snapshot_error_mapping() -> None:
    """Verify get_snapshot 500 error raises UniFiConnectionError."""
    client, _, _ = make_client(status=500, raw_bytes=b"Camera offline")

    with pytest.raises(UniFiConnectionError, match="Failed to fetch binary data: 500"):
        await client.cameras.get_snapshot("cam-1")


@pytest.mark.asyncio
async def test_remote_client_path_construction() -> None:
    """Verify remote connection builds connector path with console_id."""
    client, session, _ = make_client(
        connection_type=ConnectionType.REMOTE,
        console_id="my-console-42",
        json_data=[SAMPLE_CAMERA],
    )
    await client.cameras.get_all()

    url_called = str(session.request.call_args[0][1])
    expected = "/v1/connector/consoles/my-console-42/protect/integration/v1/cameras"
    assert url_called.endswith(expected)


# Input validation tests
@pytest.mark.asyncio
async def test_application_trigger_alarm_webhook_empty_id() -> None:
    """Empty trigger_id raises ValueError."""
    client, _, _ = make_client()
    with pytest.raises(ValueError, match="Trigger ID is required"):
        await client.application.trigger_alarm_webhook("")


@pytest.mark.parametrize("vol", [0, 101])
@pytest.mark.asyncio
async def test_cameras_set_microphone_volume_out_of_range(vol: int) -> None:
    """Volume outside 1..100 (the spec micVolume range) raises ValueError."""
    client, _, _ = make_client()
    with pytest.raises(ValueError, match="Volume must be between 1 and 100"):
        await client.cameras.set_microphone_volume("cam-1", vol)


@pytest.mark.parametrize("slot", [-1, 5])
@pytest.mark.asyncio
async def test_cameras_ptz_patrol_start_out_of_range(slot: int) -> None:
    """Patrol slot outside 0..4 raises ValueError."""
    client, _, _ = make_client()
    with pytest.raises(ValueError, match="Slot must be between 0 and 4"):
        await client.cameras.ptz_patrol_start("cam-1", slot)


@pytest.mark.asyncio
async def test_cameras_set_hdr_mode_invalid() -> None:
    """Invalid HDR mode raises ValueError."""
    client, _, _ = make_client()
    with pytest.raises(ValueError, match="HDR mode must be 'auto', 'on', or 'off'"):
        await client.cameras.set_hdr_mode("cam-1", "extreme")


@pytest.mark.parametrize("vol", [-1, 101])
@pytest.mark.asyncio
async def test_chimes_set_volume_out_of_range(vol: int) -> None:
    """Chime volume outside 0..100 raises ValueError."""
    client, _, _ = make_client()
    with pytest.raises(ValueError, match="Volume must be between 0 and 100"):
        await client.chimes.set_volume("chime-1", vol)


@pytest.mark.asyncio
async def test_cameras_create_rtsps_stream_custom_qualities() -> None:
    """Custom qualities parameter is sent in request body."""
    client, session, _ = make_client(json_data=SAMPLE_RTSPS)
    await client.cameras.create_rtsps_stream("cam-1", qualities=["medium", "low"])
    assert session.request.call_args[1].get("json") == {"qualities": ["medium", "low"]}


@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_data", [None, {"data": None}])
async def test_cameras_create_rtsps_stream_invalid_response(invalid_data: Any) -> None:
    """Non-dict response raises ValueError."""
    client, _, _ = make_client(json_data=invalid_data)
    with pytest.raises(ValueError, match="Failed to create RTSPS stream"):
        await client.cameras.create_rtsps_stream("cam-1")


@pytest.mark.asyncio
async def test_liveviews_create_with_slots() -> None:
    """Creating liveview with slots includes slots in request payload."""
    client, session, _ = make_client(json_data=SAMPLE_LIVEVIEW)
    slots = [{"cameras": ["cam-1"], "cycleMode": "motion", "cycleInterval": 10}]
    await client.liveviews.create(name="Patio", layout=1, slots=slots)
    assert session.request.call_args[1].get("json") == {
        "name": "Patio",
        "layout": 1,
        "slots": slots,
    }


@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_data", [None, {"data": None}])
async def test_liveviews_create_invalid_response(invalid_data: Any) -> None:
    """Non-dict response raises ValueError."""
    client, _, _ = make_client(json_data=invalid_data)
    with pytest.raises(ValueError, match="Failed to create live view"):
        await client.liveviews.create(name="Patio")


@pytest.mark.asyncio
async def test_nvr_get_list_response() -> None:
    """NVR endpoint accepts list response and returns first element."""
    client, _, _ = make_client(json_data={"data": [SAMPLE_NVR]})
    nvr = await client.nvr.get()
    assert nvr.id == "nvr-1"


@pytest.mark.asyncio
async def test_nvr_get_empty_list_raises() -> None:
    """Empty list response raises ValueError."""
    client, _, _ = make_client(json_data={"data": []})
    with pytest.raises(ValueError, match="NVR not found"):
        await client.nvr.get()


@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_data", [None, {"data": None}])
async def test_chimes_update_invalid_response(invalid_data: Any) -> None:
    """Non-dict response on chime update raises ValueError."""
    client, _, _ = make_client(json_data=invalid_data)
    with pytest.raises(ValueError, match="Failed to update chime"):
        await client.chimes.update("chime-1", name="Chime")


@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_data", [None, {"data": None}])
async def test_cameras_update_invalid_response(invalid_data: Any) -> None:
    """Non-dict response on camera update raises ValueError."""
    client, _, _ = make_client(json_data=invalid_data)
    with pytest.raises(ValueError, match="Failed to update camera"):
        await client.cameras.update("cam-1", name="Camera")


@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_data", [None, {"data": None}])
async def test_lights_update_invalid_response(invalid_data: Any) -> None:
    """Non-dict response on light update raises ValueError."""
    client, _, _ = make_client(json_data=invalid_data)
    with pytest.raises(ValueError, match="Failed to update light"):
        await client.lights.update("light-1", name="Light")


@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_data", [None, {"data": None}])
async def test_viewers_update_invalid_response(invalid_data: Any) -> None:
    """Non-dict response on viewer update raises ValueError."""
    client, _, _ = make_client(json_data=invalid_data)
    with pytest.raises(ValueError, match="Failed to update viewer"):
        await client.viewers.update("viewer-1", name="Viewer")


@pytest.mark.asyncio
async def test_lights_set_mode_variants() -> None:
    """Test mode string conversions 'on' -> 'always' and 'off'."""
    client, session, _ = make_client(json_data=SAMPLE_LIGHT)

    await client.lights.set_mode("light-1", "on")
    assert session.request.call_args[1].get("json") == {
        "lightModeSettings": {"mode": "always"}
    }

    await client.lights.set_mode("light-1", "off")
    assert session.request.call_args[1].get("json") == {
        "lightModeSettings": {"mode": "off"}
    }


# Response parsing edge cases: None, non-list, malformed items skipped
@pytest.mark.parametrize(
    ("endpoint_attr", "sample_item"),
    [
        ("chimes", SAMPLE_CHIME),
        ("lights", SAMPLE_LIGHT),
        ("sensors", SAMPLE_SENSOR),
        ("viewers", SAMPLE_VIEWER),
        ("cameras", SAMPLE_CAMERA),
    ],
)
@pytest.mark.asyncio
async def test_listings_handle_none_and_non_list_responses(
    endpoint_attr: str,
    sample_item: dict[str, Any],
) -> None:
    """Endpoints return empty list on None or non-list response."""
    client_none, _, _ = make_client(json_data=None)
    endpoint_none = getattr(client_none, endpoint_attr)
    assert await endpoint_none.get_all() == []

    client_dict, _, _ = make_client(json_data={"not": "a list"})
    endpoint_dict = getattr(client_dict, endpoint_attr)
    assert await endpoint_dict.get_all() == []


@pytest.mark.parametrize(
    ("endpoint_attr", "sample_item"),
    [
        ("chimes", SAMPLE_CHIME),
        ("lights", SAMPLE_LIGHT),
        ("sensors", SAMPLE_SENSOR),
        ("viewers", SAMPLE_VIEWER),
        ("cameras", SAMPLE_CAMERA),
    ],
)
@pytest.mark.asyncio
async def test_listings_skip_malformed_items(
    endpoint_attr: str,
    sample_item: dict[str, Any],
) -> None:
    """Malformed items are skipped and set last_result_complete to False."""
    bad_item = {"id": "broken"}  # Missing required mac
    client, _, _ = make_client(json_data=[sample_item, bad_item])
    endpoint = getattr(client, endpoint_attr)

    items = await endpoint.get_all()
    assert len(items) == 1
    assert endpoint.last_result_complete is False


@pytest.mark.asyncio
async def test_liveviews_get_all_none_and_non_list() -> None:
    """Liveviews get_all returns empty list on None or non-list response."""
    client_none, _, _ = make_client(json_data=None)
    assert await client_none.liveviews.get_all() == []

    client_dict, _, _ = make_client(json_data={"data": "not-a-list"})
    assert await client_dict.liveviews.get_all() == []


# Shared plumbing in api/protect/client.py
def test_protect_client_endpoint_properties() -> None:
    """Verify all Protect endpoint accessor properties."""
    client = UniFiProtectClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
    )
    assert client.connection_type == ConnectionType.LOCAL
    assert client.console_id is None
    assert client.cameras is not None
    assert client.sensors is not None
    assert client.lights is not None
    assert client.chimes is not None
    assert client.nvr is not None
    assert client.liveviews is not None
    assert client.viewers is not None
    assert client.application is not None
    assert client.alarm_hubs is not None
    assert client.arm_profiles is not None
    assert client.bridges is not None
    assert client.fobs is not None
    assert client.relays is not None
    assert client.sirens is not None
    assert client.speakers is not None
    assert client.link_stations is not None
    assert client.pos is not None
    assert client.users is not None
    assert client.ulp_users is not None
    assert client.websocket is not None


def test_protect_client_init_validation() -> None:
    """Verify initializer validation for local and remote connections."""
    with pytest.raises(
        ValueError, match="base_url is required for LOCAL connection type"
    ):
        UniFiProtectClient(
            auth=ApiKeyAuth(api_key="test-key"),
            connection_type=ConnectionType.LOCAL,
            base_url=None,
        )

    with pytest.raises(
        ValueError, match="console_id is required for REMOTE connection type"
    ):
        UniFiProtectClient(
            auth=ApiKeyAuth(api_key="test-key"),
            connection_type=ConnectionType.REMOTE,
            console_id=None,
        )


def test_build_api_path_without_leading_slash() -> None:
    """build_api_path adds leading slash if omitted."""
    client = UniFiProtectClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
    )
    path = client.build_api_path("cameras")
    assert path == "/proxy/protect/integration/v1/cameras"


@pytest.mark.asyncio
async def test_client_get_host_id() -> None:
    """get_host_id fetches NVR info and returns NVR id."""
    client, _, _ = make_client(json_data=SAMPLE_NVR)
    host_id = await client.get_host_id()
    assert host_id == "nvr-1"


@pytest.mark.asyncio
async def test_get_binary_rate_limit_retry_succeeds() -> None:
    """A 429 response is retried once after rate limit deferral."""
    client = UniFiProtectClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
    )

    resp_429 = MagicMock()
    resp_429.status = 429
    resp_429.headers = {"Retry-After": "0"}
    resp_429.text = AsyncMock(return_value="rate limited")

    resp_200 = MagicMock()
    resp_200.status = 200
    resp_200.read = AsyncMock(return_value=b"data-bytes")

    ctx_429 = MagicMock()
    ctx_429.__aenter__ = AsyncMock(return_value=resp_429)
    ctx_429.__aexit__ = AsyncMock(return_value=None)

    ctx_200 = MagicMock()
    ctx_200.__aenter__ = AsyncMock(return_value=resp_200)
    ctx_200.__aexit__ = AsyncMock(return_value=None)

    session = MagicMock()
    session.closed = False
    session.get = MagicMock(side_effect=[ctx_429, ctx_200])
    client._session = session

    result = await client._get_binary("/test")
    assert result == b"data-bytes"
    assert session.get.call_count == 2


@pytest.mark.asyncio
async def test_get_binary_rate_limit_retry_exhausted() -> None:
    """Repeated 429 raises UniFiConnectionError."""
    client = UniFiProtectClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
    )

    resp_429 = MagicMock()
    resp_429.status = 429
    resp_429.headers = {"Retry-After": "0"}
    resp_429.text = AsyncMock(return_value="rate limited")

    ctx_429 = MagicMock()
    ctx_429.__aenter__ = AsyncMock(return_value=resp_429)
    ctx_429.__aexit__ = AsyncMock(return_value=None)

    session = MagicMock()
    session.closed = False
    session.get = MagicMock(side_effect=[ctx_429, ctx_429])
    client._session = session

    with pytest.raises(UniFiConnectionError, match="Failed to fetch binary data: 429"):
        await client._get_binary("/test")


@pytest.mark.parametrize(
    ("exc_to_raise", "expected_exc"),
    [
        (
            aiohttp.ClientConnectorError(MagicMock(), OSError("fail")),
            UniFiConnectionError,
        ),
        (TimeoutError(), UniFiTimeoutError),
        (aiohttp.ClientError("client err"), UniFiConnectionError),
    ],
)
@pytest.mark.asyncio
async def test_get_binary_network_errors(
    exc_to_raise: Exception,
    expected_exc: type[Exception],
) -> None:
    """ClientConnectorError, TimeoutError, ClientError map to library errors."""
    client = UniFiProtectClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
    )

    session = MagicMock()
    session.closed = False
    session.get = MagicMock(side_effect=exc_to_raise)
    client._session = session

    with pytest.raises(expected_exc):
        await client._get_binary("/test")


@pytest.mark.asyncio
async def test_client_validate_connection() -> None:
    """validate_connection makes an API call to verify connectivity."""
    client, _, _ = make_client(json_data=[SAMPLE_CAMERA])
    assert await client.validate_connection() is True
