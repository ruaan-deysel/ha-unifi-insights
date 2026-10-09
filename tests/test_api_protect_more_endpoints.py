# Copyright 2026 UniFi Insights contributors
"""Additional tests for Protect endpoints and models pinned against the spec."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any, Self
from unittest.mock import ANY

import pytest
from pydantic import BaseModel
from yarl import URL

from custom_components.unifi_insights.api.auth import ApiKeyAuth
from custom_components.unifi_insights.api.const import ConnectionType
from custom_components.unifi_insights.api.exceptions import (
    UniFiAuthenticationError,
    UniFiGlobalAlarmManagerError,
    UniFiNotFoundError,
    UniFiResponseError,
)
from custom_components.unifi_insights.api.protect import (
    NVR,
    LightMode,
    Sensor,
    UniFiProtectClient,
)
from custom_components.unifi_insights.api.protect.endpoints._base import (
    ProtectDeviceEndpoint,
)
from custom_components.unifi_insights.api.protect.models import (
    AlarmHub,
    ArmProfile,
    Bridge,
    DoorLock,
    Event,
    Relay,
    Siren,
    Speaker,
    UlpUser,
    Viewport,
)
from custom_components.unifi_insights.api.protect.models.files import (
    ApplicationInfo,
    DeviceFile,
    FileType,
    RTSPSStream,
    TalkbackSession,
)
from custom_components.unifi_insights.api.protect.models.nvr import StorageInfo
from custom_components.unifi_insights.api.protect.models.viewer import (
    Viewer,
    ViewerState,
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
) -> UniFiProtectClient:
    return UniFiProtectClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url=(
            "https://192.168.1.1"
            if connection_type == ConnectionType.LOCAL
            else "https://api.ui.com"
        ),
        connection_type=connection_type,
        console_id=console_id
        or ("console-1" if connection_type == ConnectionType.REMOTE else None),
        session=session,  # type: ignore[arg-type]
    )


def _assert_requests(
    session: _Session, expected: list[tuple[str, str, Any, Any]]
) -> None:
    """Pin every request's verb, full URL, query and body, including retries."""
    assert [
        (r["method"], r["url"], r.get("params"), r.get("json"))
        for r in session.requests
    ] == [
        (
            method,
            f"https://192.168.1.1/proxy/protect/integration/v1/{path}",
            params,
            body,
        )
        for method, path, params, body in expected
    ]


class _DummyModel(BaseModel):
    id: str
    name: str = "dummy"


class _DummyEndpoint(ProtectDeviceEndpoint[_DummyModel]):
    _resource = "dummies"
    _model = _DummyModel


# ===================================================================
# _base.py ProtectDeviceEndpoint tests
# ===================================================================


async def test_protect_device_endpoint_get_all_branches() -> None:
    """Test ProtectDeviceEndpoint get_all edge cases."""
    # 1. response is None
    session = _Session([None])
    client = _client(session)
    ep = _DummyEndpoint(client)
    res = await ep.get_all()
    assert res == []
    assert ep.last_result_complete is True
    _assert_requests(session, [("GET", "dummies", None, None)])

    # 2. data is not a list
    session = _Session([{"data": "not a list"}])
    client = _client(session)
    ep = _DummyEndpoint(client)
    res = await ep.get_all()
    assert res == []
    _assert_requests(session, [("GET", "dummies", None, None)])

    # 3. items with validation errors (and non-dict item)
    session = _Session(
        [
            {
                "data": [
                    {"id": "ok-1", "name": "valid"},
                    {"invalid_missing_id": True},
                    "string-not-dict",
                ]
            }
        ]
    )
    client = _client(session)
    ep = _DummyEndpoint(client)
    res = await ep.get_all(site_id="site-1", expected_unsupported=True)
    assert len(res) == 1
    assert res[0].id == "ok-1"
    assert ep.last_result_complete is False
    _assert_requests(session, [("GET", "dummies", None, None)])

    # 4. REMOTE routes through the console and, like LOCAL, adds no site segment
    session = _Session([{"data": [{"id": "ok-2"}]}])
    ep = _DummyEndpoint(_client(session, connection_type=ConnectionType.REMOTE))
    res = await ep.get_all(site_id="site-1")
    assert [r.id for r in res] == ["ok-2"]
    assert session.requests[0]["url"] == (
        "https://api.ui.com/v1/connector/consoles/console-1"
        "/protect/integration/v1/dummies"
    )


async def test_protect_device_endpoint_get_and_update_branches() -> None:
    """Test ProtectDeviceEndpoint get and update fallback and error branches."""
    session = _Session(
        [
            # Dict payload
            {"data": {"id": "d-1", "name": "dict-first"}},
            # List payload with items
            {"data": [{"id": "d-1", "name": "first"}]},
            # Empty list error
            {"data": []},
            # Non-dict response error
            None,
            # update: data dict
            {"data": {"id": "d-1", "name": "updated"}},
            # update: data not dict -> ValueError
            {"data": "not-a-dict"},
            # update: failure -> ValueError
            None,
        ]
    )
    client = _client(session)
    ep = _DummyEndpoint(client)

    # get with dict
    item0 = await ep.get("d-1")
    assert item0.name == "dict-first"

    # get with list fallback
    item = await ep.get("d-1")
    assert item.id == "d-1"

    # get with empty list
    with pytest.raises(ValueError, match="dummies d-1 not found"):
        await ep.get("d-1")

    # get with non-dict
    with pytest.raises(ValueError, match="dummies d-1 not found"):
        await ep.get("d-1")

    # update success
    up = await ep.update("d-1", name="updated")
    assert up.name == "updated"

    # update with non-dict data
    with pytest.raises(ValueError, match="Failed to update dummies"):
        await ep.update("d-1", name="updated")

    # update failure
    with pytest.raises(ValueError, match="Failed to update dummies"):
        await ep.update("d-1", name="updated")

    _assert_requests(
        session,
        [
            ("GET", "dummies/d-1", None, None),
            ("GET", "dummies/d-1", None, None),
            ("GET", "dummies/d-1", None, None),
            ("GET", "dummies/d-1", None, None),
            ("PATCH", "dummies/d-1", None, {"name": "updated"}),
            ("PATCH", "dummies/d-1", None, {"name": "updated"}),
            ("PATCH", "dummies/d-1", None, {"name": "updated"}),
        ],
    )


# ===================================================================
# alarm_hubs.py tests
# ===================================================================

SAMPLE_HUB = {"id": "hub-1", "mac": "00:11:22:33:44:00", "name": "Alarm Hub 1"}


async def test_alarm_hubs_endpoints() -> None:
    """Test AlarmHubsEndpoint methods pinning requests against the spec."""
    session = _Session(
        [
            # get_all success
            [SAMPLE_HUB],
            # get_all empty/none
            None,
            # get_all non-list
            {"data": 123},
            # get_all validation error
            [{"missing_id": True}],
            # get via dict
            SAMPLE_HUB,
            # get via list
            {"data": [SAMPLE_HUB]},
            # get failure
            {"data": []},
            # update success
            SAMPLE_HUB,
            # update failure
            None,
            # trigger_output with kwargs
            None,
            # trigger_output without kwargs
            None,
        ]
    )
    client = _client(session)

    # get_all
    hubs = await client.alarm_hubs.get_all(expected_unsupported=True)
    assert len(hubs) == 1
    assert isinstance(hubs[0], AlarmHub)
    assert hubs[0].id == "hub-1"
    assert session.requests[0]["method"] == "GET"
    assert (
        session.requests[0]["url"]
        == "https://192.168.1.1/proxy/protect/integration/v1/alarm-hubs"
    )

    assert await client.alarm_hubs.get_all() == []
    assert await client.alarm_hubs.get_all() == []
    assert await client.alarm_hubs.get_all() == []
    assert client.alarm_hubs.last_result_complete is False

    # get
    hub = await client.alarm_hubs.get("hub-1")
    assert hub.id == "hub-1"
    assert (
        session.requests[4]["url"]
        == "https://192.168.1.1/proxy/protect/integration/v1/alarm-hubs/hub-1"
    )

    hub2 = await client.alarm_hubs.get("hub-1")
    assert hub2.id == "hub-1"

    with pytest.raises(ValueError, match="Alarm hub hub-1 not found"):
        await client.alarm_hubs.get("hub-1")

    # update
    up_hub = await client.alarm_hubs.update("hub-1", name="New Name")
    assert up_hub.id == "hub-1"
    assert session.requests[7]["method"] == "PATCH"
    assert session.requests[7]["json"] == {"name": "New Name"}

    with pytest.raises(ValueError, match="Failed to update alarm hub"):
        await client.alarm_hubs.update("hub-1")

    # trigger_output
    assert (
        await client.alarm_hubs.trigger_output(
            "hub-1", "out-1", enable=True, duration=5000
        )
        is True
    )
    assert session.requests[9]["method"] == "POST"
    assert (
        session.requests[9]["url"]
        == "https://192.168.1.1/proxy/protect/integration/v1/alarm-hubs/hub-1/outputs/out-1/trigger"
    )
    assert session.requests[9]["json"] == {"enable": True, "duration": 5000}

    assert await client.alarm_hubs.trigger_output("hub-1", "out-1") is True
    assert session.requests[10]["json"] is None

    _assert_requests(
        session,
        [
            ("GET", "alarm-hubs", None, None),
            ("GET", "alarm-hubs", None, None),
            ("GET", "alarm-hubs", None, None),
            ("GET", "alarm-hubs", None, None),
            ("GET", "alarm-hubs/hub-1", None, None),
            ("GET", "alarm-hubs/hub-1", None, None),
            ("GET", "alarm-hubs/hub-1", None, None),
            ("PATCH", "alarm-hubs/hub-1", None, {"name": "New Name"}),
            ("PATCH", "alarm-hubs/hub-1", None, {}),
            (
                "POST",
                "alarm-hubs/hub-1/outputs/out-1/trigger",
                None,
                {"enable": True, "duration": 5000},
            ),
            ("POST", "alarm-hubs/hub-1/outputs/out-1/trigger", None, None),
        ],
    )


# ===================================================================
# application.py tests
# ===================================================================

SAMPLE_APP_INFO = {
    "applicationVersion": "5.0.0",
    "version": "5.0.0",
    "build": "1234",
    "anonymousDeviceId": "anon-1",
    "isInstalled": True,
    "isRunning": True,
}
SAMPLE_FILE = {
    "id": "file-1",
    "name": "anim.gif",
    "originalName": "anim.gif",
    "path": "/files/anim.gif",
    "type": "animations",
}


async def test_application_endpoints() -> None:
    """Test ApplicationEndpoint methods pinning requests against the spec."""
    session = _Session(
        [
            # get_info success
            {"data": SAMPLE_APP_INFO},
            # get_info non-dict data failure
            {"data": "not-dict"},
            # get_info failure
            None,
            # get_files success
            {"data": [SAMPLE_FILE]},
            # get_files none
            None,
            # get_files not list
            {"data": "not-a-list"},
            # upload_file non-dict data
            {"data": 123},
            # upload_file failure
            None,
            # trigger_alarm_webhook success
            None,
        ]
    )
    client = _client(session)

    # get_info
    info = await client.application.get_info()
    assert isinstance(info, ApplicationInfo)
    assert info.version == "5.0.0"
    assert session.requests[0]["method"] == "GET"
    assert (
        session.requests[0]["url"]
        == "https://192.168.1.1/proxy/protect/integration/v1/meta/info"
    )

    with pytest.raises(ValueError, match="Failed to get application info"):
        await client.application.get_info()

    with pytest.raises(ValueError, match="Failed to get application info"):
        await client.application.get_info()

    # get_files
    files = await client.application.get_files(FileType.ANIMATIONS)
    assert len(files) == 1
    assert isinstance(files[0], DeviceFile)
    assert files[0].id == "file-1"
    assert session.requests[3]["method"] == "GET"
    assert (
        session.requests[3]["url"]
        == "https://192.168.1.1/proxy/protect/integration/v1/files/animations"
    )

    assert await client.application.get_files() == []
    assert await client.application.get_files() == []

    # upload_file
    with pytest.raises(ValueError, match="Failed to upload file"):
        await client.application.upload_file(b"fake", filename="bad.gif")

    with pytest.raises(ValueError, match="Failed to upload file"):
        await client.application.upload_file(b"fake", filename="bad.gif")

    # trigger_alarm_webhook
    with pytest.raises(ValueError, match="Trigger ID is required"):
        await client.application.trigger_alarm_webhook("")

    assert await client.application.trigger_alarm_webhook("trig-abc") is True
    assert session.requests[8]["method"] == "POST"
    assert (
        session.requests[8]["url"]
        == "https://192.168.1.1/proxy/protect/integration/v1/alarm-manager/webhook/trig-abc"
    )

    _assert_requests(
        session,
        [
            ("GET", "meta/info", None, None),
            ("GET", "meta/info", None, None),
            ("GET", "meta/info", None, None),
            ("GET", "files/animations", None, None),
            ("GET", "files/animations", None, None),
            ("GET", "files/animations", None, None),
            (
                "POST",
                "files/animations",
                None,
                ANY,  # Multipart body is pinned by the strict upload xfail.
            ),
            (
                "POST",
                "files/animations",
                None,
                ANY,  # Multipart body is pinned by the strict upload xfail.
            ),
            ("POST", "alarm-manager/webhook/trig-abc", None, None),
        ],
    )


# ===================================================================
# arm_profiles.py tests
# ===================================================================

SAMPLE_ARM_PROFILE = {
    "id": "prof-1",
    "name": "Home",
}


@pytest.mark.parametrize(
    ("body", "status", "exception"),
    [
        (None, 400, UniFiResponseError),
        ("", 400, UniFiResponseError),
        ("other error", 400, UniFiResponseError),
        ({"k": "v", "sub": [1, True, None, "item"]}, 400, UniFiResponseError),
        ({"error": "GLOBAL_ALARM_MANAGER_ENABLED"}, 400, UniFiGlobalAlarmManagerError),
        (
            "This operation is not available when global alarm manager is enabled",
            400,
            UniFiGlobalAlarmManagerError,
        ),
        ("global alarm manager", 500, UniFiResponseError),
    ],
)
async def test_arm_profiles_alarm_detection(
    body: Any, status: int, exception: type[Exception]
) -> None:
    """Exercise global-alarm detection through public endpoint error mapping."""
    session = _Session([_Response(body, status=status)])
    with pytest.raises(exception):
        await _client(session).arm_profiles.get_all()
    _assert_requests(session, [("GET", "arm-profiles", None, None)])


async def test_arm_profiles_endpoints() -> None:
    """Test ArmProfilesEndpoint methods pinning requests against the spec."""
    resp_gam_400 = _Response(
        body={"error": "global alarm manager enabled"},
        status=400,
    )
    session = _Session(
        [
            # get_all success
            [SAMPLE_ARM_PROFILE],
            # get_all GAM 400
            resp_gam_400,
            # get_all plain 500 error
            _Response(status=500, body=None),
            # get_all None
            None,
            # get_all non-list
            {"data": 123},
            # get_all validation error
            [{"missing_id": True}],
            # create success
            SAMPLE_ARM_PROFILE,
            # create failure
            None,
            # update success
            SAMPLE_ARM_PROFILE,
            # update failure
            None,
            # delete success
            None,
            # enable success with kwargs
            None,
            # enable GAM 400
            resp_gam_400,
            # disable success without kwargs
            None,
            # disable GAM 400
            resp_gam_400,
            # update_settings success
            None,
        ]
    )
    client = _client(session)

    # get_all
    profiles = await client.arm_profiles.get_all()
    assert len(profiles) == 1
    assert isinstance(profiles[0], ArmProfile)
    assert profiles[0].id == "prof-1"
    assert session.requests[0]["method"] == "GET"
    assert (
        session.requests[0]["url"]
        == "https://192.168.1.1/proxy/protect/integration/v1/arm-profiles"
    )

    with pytest.raises(UniFiGlobalAlarmManagerError):
        await client.arm_profiles.get_all()

    with pytest.raises(UniFiResponseError):
        await client.arm_profiles.get_all()

    assert await client.arm_profiles.get_all() == []
    assert await client.arm_profiles.get_all() == []
    assert await client.arm_profiles.get_all() == []
    assert client.arm_profiles.last_result_complete is False

    # create
    created = await client.arm_profiles.create(
        name="Home",
        automations=[],
        schedules=[],
        recordEverything=False,
        activationDelay=0,
    )
    assert created.id == "prof-1"
    assert session.requests[6]["method"] == "POST"
    assert (
        session.requests[6]["url"]
        == "https://192.168.1.1/proxy/protect/integration/v1/arm-profiles"
    )
    assert session.requests[6]["json"] == {
        "name": "Home",
        "automations": [],
        "schedules": [],
        "recordEverything": False,
        "activationDelay": 0,
    }

    with pytest.raises(ValueError, match="Failed to create arm profile"):
        await client.arm_profiles.create(
            name="Fail",
            automations=[],
            schedules=[],
            recordEverything=False,
            activationDelay=0,
        )

    # update
    up = await client.arm_profiles.update("prof-1", name="Away")
    assert up.id == "prof-1"
    assert session.requests[8]["method"] == "PATCH"
    assert (
        session.requests[8]["url"]
        == "https://192.168.1.1/proxy/protect/integration/v1/arm-profiles/prof-1"
    )
    assert session.requests[8]["json"] == {"name": "Away"}

    with pytest.raises(ValueError, match="Failed to update arm profile"):
        await client.arm_profiles.update("prof-1", name="Fail")

    # delete
    assert await client.arm_profiles.delete("prof-1") is True
    assert session.requests[10]["method"] == "DELETE"
    assert (
        session.requests[10]["url"]
        == "https://192.168.1.1/proxy/protect/integration/v1/arm-profiles/prof-1"
    )

    # enable
    assert await client.arm_profiles.enable() is True
    assert session.requests[11]["method"] == "POST"
    assert (
        session.requests[11]["url"]
        == "https://192.168.1.1/proxy/protect/integration/v1/arm-profiles/enable"
    )
    assert session.requests[11]["json"] is None

    with pytest.raises(UniFiGlobalAlarmManagerError):
        await client.arm_profiles.enable()

    # disable
    assert await client.arm_profiles.disable() is True
    assert session.requests[13]["method"] == "POST"
    assert (
        session.requests[13]["url"]
        == "https://192.168.1.1/proxy/protect/integration/v1/arm-profiles/disable"
    )
    assert session.requests[13]["json"] is None

    with pytest.raises(UniFiGlobalAlarmManagerError):
        await client.arm_profiles.disable()

    # update_settings
    assert await client.arm_profiles.update_settings(armProfileId="prof-1") is True
    assert session.requests[15]["method"] == "PATCH"
    assert (
        session.requests[15]["url"]
        == "https://192.168.1.1/proxy/protect/integration/v1/arm-profiles/settings"
    )
    assert session.requests[15]["json"] == {"armProfileId": "prof-1"}

    _assert_requests(
        session,
        [
            ("GET", "arm-profiles", None, None),
            ("GET", "arm-profiles", None, None),
            ("GET", "arm-profiles", None, None),
            ("GET", "arm-profiles", None, None),
            ("GET", "arm-profiles", None, None),
            ("GET", "arm-profiles", None, None),
            (
                "POST",
                "arm-profiles",
                None,
                {
                    "name": "Home",
                    "automations": [],
                    "schedules": [],
                    "recordEverything": False,
                    "activationDelay": 0,
                },
            ),
            (
                "POST",
                "arm-profiles",
                None,
                {
                    "name": "Fail",
                    "automations": [],
                    "schedules": [],
                    "recordEverything": False,
                    "activationDelay": 0,
                },
            ),
            ("PATCH", "arm-profiles/prof-1", None, {"name": "Away"}),
            ("PATCH", "arm-profiles/prof-1", None, {"name": "Fail"}),
            ("DELETE", "arm-profiles/prof-1", None, None),
            ("POST", "arm-profiles/enable", None, None),
            ("POST", "arm-profiles/enable", None, None),
            ("POST", "arm-profiles/disable", None, None),
            ("POST", "arm-profiles/disable", None, None),
            ("PATCH", "arm-profiles/settings", None, {"armProfileId": "prof-1"}),
        ],
    )


# ===================================================================
# cameras.py tests (skipping recordingMode and privacy/isMicEnabled)
# ===================================================================

SAMPLE_CAMERA = {"id": "cam-1", "mac": "00:11:22:33:44:01", "name": "Camera 1"}
SAMPLE_RTSPS = {"high": "rtsps://192.168.1.1:7441/high"}
SAMPLE_TALKBACK = {
    "url": "wss://192.168.1.1/talkback",
    "codec": "opus",
    "samplingRate": 48000,
    "bitsPerSample": 16,
}


async def test_cameras_more_endpoints() -> None:
    """Test CamerasEndpoint methods pinning requests against the spec."""
    fake_jpeg = b"fake-jpeg-bytes"
    resp_snapshot = _Response(
        raw_bytes=fake_jpeg, headers={"Content-Type": "image/jpeg"}
    )

    session = _Session(
        [
            # get via dict
            SAMPLE_CAMERA,
            # get via list
            {"data": [SAMPLE_CAMERA]},
            # get failure
            {"data": []},
            # update failure
            None,
            # get_snapshot high_quality=False
            resp_snapshot,
            # get_snapshot high_quality=True
            resp_snapshot,
            # get_rtsps_stream success
            SAMPLE_RTSPS,
            # get_rtsps_stream failure
            None,
            # delete_rtsps_stream default qualities
            None,
            # delete_rtsps_stream custom qualities
            None,
            # create_talkback_session success
            SAMPLE_TALKBACK,
            # create_talkback_session failure
            None,
            # disable_mic_permanently success
            SAMPLE_CAMERA,
            # disable_mic_permanently failure
            None,
            # set_video_mode (calls update)
            SAMPLE_CAMERA,
        ]
    )
    client = _client(session)

    # get
    cam = await client.cameras.get("cam-1")
    assert cam.id == "cam-1"
    assert session.requests[0]["method"] == "GET"
    assert (
        session.requests[0]["url"]
        == "https://192.168.1.1/proxy/protect/integration/v1/cameras/cam-1"
    )

    cam2 = await client.cameras.get("cam-1")
    assert cam2.id == "cam-1"

    with pytest.raises(ValueError, match="Camera cam-1 not found"):
        await client.cameras.get("cam-1")

    with pytest.raises(ValueError, match="Failed to update camera"):
        await client.cameras.update("cam-1")

    # get_snapshot
    data1 = await client.cameras.get_snapshot("cam-1", high_quality=False)
    assert data1 == fake_jpeg
    assert session.requests[4]["method"] == "GET"
    assert (
        session.requests[4]["url"]
        == "https://192.168.1.1/proxy/protect/integration/v1/cameras/cam-1/snapshot"
    )
    assert session.requests[4]["params"] is None

    data2 = await client.cameras.get_snapshot("cam-1", high_quality=True)
    assert data2 == fake_jpeg
    assert session.requests[5]["params"] == {"highQuality": "true"}

    # get_rtsps_stream
    stream = await client.cameras.get_rtsps_stream("cam-1")
    assert isinstance(stream, RTSPSStream)
    assert stream.high == SAMPLE_RTSPS["high"]
    assert session.requests[6]["method"] == "GET"
    assert (
        session.requests[6]["url"]
        == "https://192.168.1.1/proxy/protect/integration/v1/cameras/cam-1/rtsps-stream"
    )

    with pytest.raises(ValueError, match="RTSPS stream not found"):
        await client.cameras.get_rtsps_stream("cam-1")

    # delete_rtsps_stream
    assert await client.cameras.delete_rtsps_stream("cam-1") is True
    assert session.requests[8]["method"] == "DELETE"
    assert (
        session.requests[8]["url"]
        == "https://192.168.1.1/proxy/protect/integration/v1/cameras/cam-1/rtsps-stream"
    )
    assert session.requests[8]["params"] == {"qualities": ["high"]}

    assert (
        await client.cameras.delete_rtsps_stream("cam-1", qualities=["medium", "low"])
        is True
    )
    assert session.requests[9]["params"] == {"qualities": ["medium", "low"]}

    # create_talkback_session
    tb = await client.cameras.create_talkback_session("cam-1")
    assert isinstance(tb, TalkbackSession)
    assert tb.url == SAMPLE_TALKBACK["url"]
    assert session.requests[10]["method"] == "POST"
    assert (
        session.requests[10]["url"]
        == "https://192.168.1.1/proxy/protect/integration/v1/cameras/cam-1/talkback-session"
    )

    with pytest.raises(ValueError, match="Failed to create talkback session"):
        await client.cameras.create_talkback_session("cam-1")

    # disable_mic_permanently
    dis = await client.cameras.disable_mic_permanently("cam-1")
    assert dis.id == "cam-1"
    assert session.requests[12]["method"] == "POST"
    assert (
        session.requests[12]["url"]
        == "https://192.168.1.1/proxy/protect/integration/v1/cameras/cam-1/disable-mic-permanently"
    )

    with pytest.raises(ValueError, match="Failed to disable microphone"):
        await client.cameras.disable_mic_permanently("cam-1")

    # set_video_mode
    vm = await client.cameras.set_video_mode("cam-1", "highFps")
    assert vm.id == "cam-1"
    assert session.requests[14]["method"] == "PATCH"
    assert session.requests[14]["json"] == {"videoMode": "highFps"}

    _assert_requests(
        session,
        [
            ("GET", "cameras/cam-1", None, None),
            ("GET", "cameras/cam-1", None, None),
            ("GET", "cameras/cam-1", None, None),
            ("PATCH", "cameras/cam-1", None, {}),
            ("GET", "cameras/cam-1/snapshot", None, None),
            ("GET", "cameras/cam-1/snapshot", {"highQuality": "true"}, None),
            ("GET", "cameras/cam-1/rtsps-stream", None, None),
            ("GET", "cameras/cam-1/rtsps-stream", None, None),
            ("DELETE", "cameras/cam-1/rtsps-stream", {"qualities": ["high"]}, None),
            (
                "DELETE",
                "cameras/cam-1/rtsps-stream",
                {"qualities": ["medium", "low"]},
                None,
            ),
            ("POST", "cameras/cam-1/talkback-session", None, None),
            ("POST", "cameras/cam-1/talkback-session", None, None),
            ("POST", "cameras/cam-1/disable-mic-permanently", None, None),
            ("POST", "cameras/cam-1/disable-mic-permanently", None, None),
            ("PATCH", "cameras/cam-1", None, {"videoMode": "highFps"}),
        ],
    )


# ===================================================================
# chimes.py tests and issue #268 strict xfail
# ===================================================================

SAMPLE_CHIME = {
    "id": "chime-1",
    "mac": "00:11:22:33:44:02",
    "name": "Chime 1",
    "ringSettings": [
        {"cameraId": "door-1", "repeatTimes": 1, "ringtoneId": "tone-1", "volume": 50}
    ],
}


async def test_chimes_endpoints() -> None:
    """Test ChimesEndpoint methods pinning requests against the spec."""
    session = _Session(
        [
            # get via dict
            SAMPLE_CHIME,
            # get via list
            {"data": [SAMPLE_CHIME]},
            # get failure
            {"data": []},
            # update failure
            None,
            # set_volume: get chime + patch chime
            SAMPLE_CHIME,
            SAMPLE_CHIME,
            # set_repeat_times: get chime + patch chime
            SAMPLE_CHIME,
            SAMPLE_CHIME,
        ]
    )
    client = _client(session)

    # get
    ch = await client.chimes.get("chime-1")
    assert ch.id == "chime-1"
    assert session.requests[0]["method"] == "GET"
    assert (
        session.requests[0]["url"]
        == "https://192.168.1.1/proxy/protect/integration/v1/chimes/chime-1"
    )

    ch2 = await client.chimes.get("chime-1")
    assert ch2.id == "chime-1"

    with pytest.raises(ValueError, match="Chime chime-1 not found"):
        await client.chimes.get("chime-1")

    with pytest.raises(ValueError, match="Failed to update chime"):
        await client.chimes.update("chime-1")

    # set_volume validations
    with pytest.raises(ValueError, match="Volume must be between 0 and 100"):
        await client.chimes.set_volume("chime-1", -1)
    with pytest.raises(ValueError, match="Volume must be between 0 and 100"):
        await client.chimes.set_volume("chime-1", 101)

    vch = await client.chimes.set_volume("chime-1", 80)
    assert vch.id == "chime-1"
    assert session.requests[5]["method"] == "PATCH"
    assert session.requests[5]["json"] == {
        "ringSettings": [
            {
                "cameraId": "door-1",
                "repeatTimes": 1,
                "ringtoneId": "tone-1",
                "volume": 80,
            }
        ]
    }

    # set_repeat_times validations
    with pytest.raises(ValueError, match="Repeat times must be between 1 and 10"):
        await client.chimes.set_repeat_times("chime-1", 0)
    with pytest.raises(ValueError, match="Repeat times must be between 1 and 10"):
        await client.chimes.set_repeat_times("chime-1", 11)

    rch = await client.chimes.set_repeat_times("chime-1", 3)
    assert rch.id == "chime-1"
    assert session.requests[7]["method"] == "PATCH"
    assert session.requests[7]["json"] == {
        "ringSettings": [
            {
                "cameraId": "door-1",
                "repeatTimes": 3,
                "ringtoneId": "tone-1",
                "volume": 50,
            }
        ]
    }

    _assert_requests(
        session,
        [
            ("GET", "chimes/chime-1", None, None),
            ("GET", "chimes/chime-1", None, None),
            ("GET", "chimes/chime-1", None, None),
            ("PATCH", "chimes/chime-1", None, {}),
            ("GET", "chimes/chime-1", None, None),
            (
                "PATCH",
                "chimes/chime-1",
                None,
                {
                    "ringSettings": [
                        {
                            "cameraId": "door-1",
                            "repeatTimes": 1,
                            "ringtoneId": "tone-1",
                            "volume": 80,
                        }
                    ]
                },
            ),
            ("GET", "chimes/chime-1", None, None),
            (
                "PATCH",
                "chimes/chime-1",
                None,
                {
                    "ringSettings": [
                        {
                            "cameraId": "door-1",
                            "repeatTimes": 3,
                            "ringtoneId": "tone-1",
                            "volume": 50,
                        }
                    ]
                },
            ),
        ],
    )


async def test_chimes_update_ring_settings_errors() -> None:
    """Test _update_ring_settings error branches."""
    chime_no_rings = {"id": "chime-1", "mac": "00:11:22:33:44:02", "name": "Chime"}
    chime_bad_rings = {
        "id": "chime-1",
        "mac": "00:11:22:33:44:02",
        "name": "Chime",
        "ringSettings": [{"cameraId": "door-1"}],
    }

    session = _Session([chime_no_rings, chime_bad_rings])
    client = _client(session)

    with pytest.raises(ValueError, match="has no paired doorbell"):
        await client.chimes.set_volume("chime-1", 50)

    with pytest.raises(ValueError, match="has incomplete ring settings"):
        await client.chimes.set_volume("chime-1", 50)

    _assert_requests(
        session,
        [
            ("GET", "chimes/chime-1", None, None),
            ("GET", "chimes/chime-1", None, None),
        ],
    )


@pytest.mark.xfail(
    strict=True,
    reason=(
        "chimes.update(ringtone=...) sends top-level 'ringtone'; spec "
        "PATCH /v1/chimes/{id} only allows name, cameraIds, and ringSettings "
        "(issue #268)"
    ),
)
async def test_chime_set_ringtone_spec_mismatch() -> None:
    """Setting chime ringtone via update sends top-level 'ringtone'."""
    ringtone_id = "66d025b301ebc903e80003ea"
    ring_settings = [
        {
            "cameraId": "66d025b301ebc903e80003eb",
            "repeatTimes": 2,
            "volume": 45,
            "ringtoneId": "66d025b301ebc903e80003ec",
        },
        {
            "cameraId": "66d025b301ebc903e80003ed",
            "repeatTimes": 4,
            "volume": 70,
            "ringtoneId": "66d025b301ebc903e80003ee",
        },
    ]
    updated_settings = [{**entry, "ringtoneId": ringtone_id} for entry in ring_settings]
    session = _Session(
        [
            {**SAMPLE_CHIME, "ringSettings": ring_settings},
            {**SAMPLE_CHIME, "ringSettings": updated_settings},
        ]
    )
    chime = await _client(session).chimes.update("chime-1", ringtone=ringtone_id)
    assert chime.id == "chime-1"
    assert chime.model_extra is not None
    assert chime.model_extra["ringSettings"] == updated_settings
    _assert_requests(
        session,
        [
            ("GET", "chimes/chime-1", None, None),
            ("PATCH", "chimes/chime-1", None, {"ringSettings": updated_settings}),
        ],
    )


# ===================================================================
# lights.py tests
# ===================================================================

SAMPLE_LIGHT = {"id": "light-1", "mac": "00:11:22:33:44:03", "name": "Light 1"}


async def test_lights_endpoints() -> None:
    """Test LightsEndpoint methods pinning requests against the spec."""
    session = _Session(
        [
            # get via dict
            SAMPLE_LIGHT,
            # get via list
            {"data": [SAMPLE_LIGHT]},
            # get failure
            {"data": []},
            # update failure
            None,
            # turn_on
            SAMPLE_LIGHT,
            # turn_off
            SAMPLE_LIGHT,
            # set_mode "on" -> "always"
            SAMPLE_LIGHT,
            # set_mode enum
            SAMPLE_LIGHT,
            # set_brightness
            SAMPLE_LIGHT,
        ]
    )
    client = _client(session)

    # get
    l1 = await client.lights.get("light-1")
    assert l1.id == "light-1"
    assert session.requests[0]["method"] == "GET"
    assert (
        session.requests[0]["url"]
        == "https://192.168.1.1/proxy/protect/integration/v1/lights/light-1"
    )

    l2 = await client.lights.get("light-1")
    assert l2.id == "light-1"

    with pytest.raises(ValueError, match="Light light-1 not found"):
        await client.lights.get("light-1")

    with pytest.raises(ValueError, match="Failed to update light"):
        await client.lights.update("light-1")

    # turn_on
    on_l = await client.lights.turn_on("light-1")
    assert on_l.id == "light-1"
    assert session.requests[4]["method"] == "PATCH"
    assert session.requests[4]["json"] == {"lightModeSettings": {"mode": "always"}}

    # turn_off
    off_l = await client.lights.turn_off("light-1")
    assert off_l.id == "light-1"
    assert session.requests[5]["json"] == {"lightModeSettings": {"mode": "off"}}

    # set_mode
    sm_l1 = await client.lights.set_mode("light-1", "on")
    assert sm_l1.id == "light-1"
    assert session.requests[6]["json"] == {"lightModeSettings": {"mode": "always"}}

    sm_l2 = await client.lights.set_mode("light-1", LightMode.MOTION)
    assert sm_l2.id == "light-1"
    assert session.requests[7]["json"] == {"lightModeSettings": {"mode": "motion"}}

    # set_brightness validations
    with pytest.raises(ValueError, match="led_level must be between 1 and 6"):
        await client.lights.set_brightness("light-1", 0)
    with pytest.raises(ValueError, match="led_level must be between 1 and 6"):
        await client.lights.set_brightness("light-1", 7)
    bool_arg = True
    with pytest.raises(ValueError, match="led_level must be between 1 and 6"):
        await client.lights.set_brightness("light-1", bool_arg)  # type: ignore[arg-type]

    br_l = await client.lights.set_brightness("light-1", 4)
    assert br_l.id == "light-1"
    assert session.requests[8]["json"] == {"lightDeviceSettings": {"ledLevel": 4}}

    _assert_requests(
        session,
        [
            ("GET", "lights/light-1", None, None),
            ("GET", "lights/light-1", None, None),
            ("GET", "lights/light-1", None, None),
            ("PATCH", "lights/light-1", None, {}),
            (
                "PATCH",
                "lights/light-1",
                None,
                {"lightModeSettings": {"mode": "always"}},
            ),
            ("PATCH", "lights/light-1", None, {"lightModeSettings": {"mode": "off"}}),
            (
                "PATCH",
                "lights/light-1",
                None,
                {"lightModeSettings": {"mode": "always"}},
            ),
            (
                "PATCH",
                "lights/light-1",
                None,
                {"lightModeSettings": {"mode": "motion"}},
            ),
            ("PATCH", "lights/light-1", None, {"lightDeviceSettings": {"ledLevel": 4}}),
        ],
    )


# ===================================================================
# liveviews.py tests
# ===================================================================

SAMPLE_LIVEVIEW = {
    "id": "lv-1",
    "modelKey": "liveview",
    "name": "Main View",
    "layout": 1,
    "isDefault": False,
    "isGlobal": True,
    "owner": "user-1",
    "slots": [{"cameras": ["cam-1"], "cycleMode": "time", "cycleInterval": 10}],
}


async def test_liveviews_endpoints() -> None:
    """Test LiveViewsEndpoint methods pinning requests against the spec."""
    session = _Session(
        [
            # get_all none
            None,
            # get_all not a list
            {"data": "bad"},
            # get via dict
            SAMPLE_LIVEVIEW,
            # get via list
            {"data": [SAMPLE_LIVEVIEW]},
            # get failure
            {"data": []},
            # create failure
            None,
            # update success
            SAMPLE_LIVEVIEW,
            # update failure
            None,
        ]
    )
    client = _client(session)

    assert await client.liveviews.get_all() == []
    assert await client.liveviews.get_all() == []

    # get
    lv1 = await client.liveviews.get("lv-1")
    assert lv1.id == "lv-1"
    assert session.requests[2]["method"] == "GET"
    assert (
        session.requests[2]["url"]
        == "https://192.168.1.1/proxy/protect/integration/v1/liveviews/lv-1"
    )

    lv2 = await client.liveviews.get("lv-1")
    assert lv2.id == "lv-1"

    with pytest.raises(ValueError, match="LiveView lv-1 not found"):
        await client.liveviews.get("lv-1")

    with pytest.raises(ValueError, match="Failed to create live view"):
        await client.liveviews.create(**{**SAMPLE_LIVEVIEW, "name": "Fail"})

    up_lv = await client.liveviews.update(
        "lv-1", **{**SAMPLE_LIVEVIEW, "name": "New View"}
    )
    assert up_lv.id == "lv-1"
    assert session.requests[6]["method"] == "PATCH"
    assert (
        session.requests[6]["url"]
        == "https://192.168.1.1/proxy/protect/integration/v1/liveviews/lv-1"
    )
    assert session.requests[6]["json"] == {**SAMPLE_LIVEVIEW, "name": "New View"}

    with pytest.raises(ValueError, match="Failed to update live view"):
        await client.liveviews.update("lv-1", **SAMPLE_LIVEVIEW)

    _assert_requests(
        session,
        [
            ("GET", "liveviews", None, None),
            ("GET", "liveviews", None, None),
            ("GET", "liveviews/lv-1", None, None),
            ("GET", "liveviews/lv-1", None, None),
            ("GET", "liveviews/lv-1", None, None),
            ("POST", "liveviews", None, {**SAMPLE_LIVEVIEW, "name": "Fail"}),
            ("PATCH", "liveviews/lv-1", None, {**SAMPLE_LIVEVIEW, "name": "New View"}),
            ("PATCH", "liveviews/lv-1", None, SAMPLE_LIVEVIEW),
        ],
    )


# ===================================================================
# nvr.py tests
# ===================================================================

SAMPLE_NVR = {"id": "nvr-1", "name": "UNVR"}


async def test_nvr_endpoint_branches() -> None:
    """Test NVREndpoint get edge cases."""
    session = _Session(
        [
            # get via list
            {"data": [SAMPLE_NVR]},
            # get empty list
            {"data": []},
            # get non-dict
            None,
        ]
    )
    client = _client(session)

    n1 = await client.nvr.get()
    assert n1.id == "nvr-1"

    with pytest.raises(ValueError, match="NVR not found"):
        await client.nvr.get()

    with pytest.raises(ValueError, match="NVR not found"):
        await client.nvr.get()

    _assert_requests(
        session,
        [
            ("GET", "nvrs", None, None),
            ("GET", "nvrs", None, None),
            ("GET", "nvrs", None, None),
        ],
    )


# ===================================================================
# sensors.py tests
# ===================================================================

SAMPLE_SENSOR = {"id": "sensor-1", "mac": "00:11:22:33:44:04", "name": "Sensor 1"}


async def test_sensors_endpoints() -> None:
    """Test SensorsEndpoint methods pinning requests against the spec."""
    session = _Session(
        [
            # get_all none
            None,
            # get_all not list
            {"data": 123},
            # get_all validation error
            [{"missing_id": True}],
            # get via dict
            SAMPLE_SENSOR,
            # get via list
            {"data": [SAMPLE_SENSOR]},
            # get failure
            {"data": []},
            # update failure
            None,
        ]
    )
    client = _client(session)

    assert await client.sensors.get_all() == []
    assert await client.sensors.get_all() == []
    assert await client.sensors.get_all() == []
    assert client.sensors.last_result_complete is False

    # get
    s1 = await client.sensors.get("sensor-1")
    assert s1.id == "sensor-1"
    assert session.requests[3]["method"] == "GET"
    assert (
        session.requests[3]["url"]
        == "https://192.168.1.1/proxy/protect/integration/v1/sensors/sensor-1"
    )

    s2 = await client.sensors.get("sensor-1")
    assert s2.id == "sensor-1"

    with pytest.raises(ValueError, match="Sensor sensor-1 not found"):
        await client.sensors.get("sensor-1")

    with pytest.raises(ValueError, match="Failed to update sensor"):
        await client.sensors.update("sensor-1")

    # set_motion_sensitivity
    with pytest.raises(ValueError, match="Sensitivity must be between 0 and 100"):
        await client.sensors.set_motion_sensitivity("sensor-1", -1)
    with pytest.raises(ValueError, match="Sensitivity must be between 0 and 100"):
        await client.sensors.set_motion_sensitivity("sensor-1", 101)

    _assert_requests(
        session,
        [
            ("GET", "sensors", None, None),
            ("GET", "sensors", None, None),
            ("GET", "sensors", None, None),
            ("GET", "sensors/sensor-1", None, None),
            ("GET", "sensors/sensor-1", None, None),
            ("GET", "sensors/sensor-1", None, None),
            ("PATCH", "sensors/sensor-1", None, {}),
        ],
    )


# ===================================================================
# sirens.py tests
# ===================================================================

SAMPLE_SIREN = {"id": "siren-1", "mac": "00:11:22:33:44:06", "name": "Siren 1"}


async def test_sirens_endpoints() -> None:
    """Test SirensEndpoint methods pinning requests against the spec."""
    session = _Session(
        [
            # play with duration
            None,
            # play without duration
            None,
            # set_volume (calls update)
            SAMPLE_SIREN,
            # stop
            None,
            # test_sound
            None,
        ]
    )
    client = _client(session)

    # play validations
    with pytest.raises(ValueError, match="Siren duration must be one of"):
        await client.sirens.play("siren-1", duration=15)

    assert await client.sirens.play("siren-1", duration=10) is True
    assert session.requests[0]["method"] == "POST"
    assert (
        session.requests[0]["url"]
        == "https://192.168.1.1/proxy/protect/integration/v1/sirens/siren-1/play"
    )
    assert session.requests[0]["json"] == {"duration": 10}

    assert await client.sirens.play("siren-1") is True
    assert session.requests[1]["json"] is None

    # set_volume validations
    with pytest.raises(ValueError, match="Siren volume must be between 1 and 100"):
        await client.sirens.set_volume("siren-1", 0)
    with pytest.raises(ValueError, match="Siren volume must be between 1 and 100"):
        await client.sirens.set_volume("siren-1", 101)

    v_sir = await client.sirens.set_volume("siren-1", 85)
    assert v_sir.id == "siren-1"
    assert session.requests[2]["method"] == "PATCH"
    assert (
        session.requests[2]["url"]
        == "https://192.168.1.1/proxy/protect/integration/v1/sirens/siren-1"
    )
    assert session.requests[2]["json"] == {"volume": 85}

    # stop
    assert await client.sirens.stop("siren-1") is True
    assert session.requests[3]["method"] == "POST"
    assert (
        session.requests[3]["url"]
        == "https://192.168.1.1/proxy/protect/integration/v1/sirens/siren-1/stop"
    )

    # test_sound
    assert await client.sirens.test_sound("siren-1") is True
    assert session.requests[4]["method"] == "POST"
    assert (
        session.requests[4]["url"]
        == "https://192.168.1.1/proxy/protect/integration/v1/sirens/siren-1/test-sound"
    )

    _assert_requests(
        session,
        [
            ("POST", "sirens/siren-1/play", None, {"duration": 10}),
            ("POST", "sirens/siren-1/play", None, None),
            ("PATCH", "sirens/siren-1", None, {"volume": 85}),
            ("POST", "sirens/siren-1/stop", None, None),
            ("POST", "sirens/siren-1/test-sound", None, None),
        ],
    )


# ===================================================================
# ulp_users.py tests
# ===================================================================

SAMPLE_ULP_USER = {
    "id": "ulp-1",
    "fullName": "Jane Doe",
    "status": "ACTIVE",
    "firstName": "Jane",
    "lastName": "Doe",
}


async def test_ulp_users_endpoints() -> None:
    """Test UlpUsersEndpoint methods pinning requests against the spec."""
    session = _Session(
        [
            # get_all success
            [SAMPLE_ULP_USER],
            # get_all none
            None,
            # get_all not list
            {"data": "bad"},
            # get_all validation error
            [{"missing_id": True}],
            # get via dict
            SAMPLE_ULP_USER,
            # get not found
            None,
        ]
    )
    client = _client(session)

    # get_all
    users = await client.ulp_users.get_all(expected_unsupported=True)
    assert len(users) == 1
    assert isinstance(users[0], UlpUser)
    assert users[0].id == "ulp-1"
    assert session.requests[0]["method"] == "GET"
    assert (
        session.requests[0]["url"]
        == "https://192.168.1.1/proxy/protect/integration/v1/ulp-users"
    )

    assert await client.ulp_users.get_all() == []
    assert await client.ulp_users.get_all() == []
    assert await client.ulp_users.get_all() == []
    assert client.ulp_users.last_result_complete is False

    # get validations
    with pytest.raises(ValueError, match="ULP user ID must be a non-empty string"):
        await client.ulp_users.get("")
    with pytest.raises(ValueError, match="ULP user ID must be a non-empty string"):
        await client.ulp_users.get(123)  # type: ignore[arg-type]

    u = await client.ulp_users.get("ulp-1")
    assert u.id == "ulp-1"
    assert session.requests[4]["method"] == "GET"
    assert (
        session.requests[4]["url"]
        == "https://192.168.1.1/proxy/protect/integration/v1/ulp-users/ulp-1"
    )

    with pytest.raises(ValueError, match="ULP user ulp-1 not found"):
        await client.ulp_users.get("ulp-1")

    _assert_requests(
        session,
        [
            ("GET", "ulp-users", None, None),
            ("GET", "ulp-users", None, None),
            ("GET", "ulp-users", None, None),
            ("GET", "ulp-users", None, None),
            ("GET", "ulp-users/ulp-1", None, None),
            ("GET", "ulp-users/ulp-1", None, None),
        ],
    )


# ===================================================================
# viewers.py tests
# ===================================================================

SAMPLE_VIEWER = {
    "id": "viewer-1",
    "mac": "00:11:22:33:44:05",
    "name": "Viewer 1",
    "state": "CONNECTED",
}


async def test_viewers_endpoints() -> None:
    """Test ViewersEndpoint methods pinning requests against the spec."""
    session = _Session(
        [
            # get_all none
            None,
            # get_all not list
            {"data": "bad"},
            # get_all validation error
            [{"missing_id": True}],
            # get via dict
            SAMPLE_VIEWER,
            # get via list
            {"data": [SAMPLE_VIEWER]},
            # get failure
            {"data": []},
            # update failure
            None,
            # set_liveview
            SAMPLE_VIEWER,
        ]
    )
    client = _client(session)

    assert await client.viewers.get_all() == []
    assert await client.viewers.get_all() == []
    assert await client.viewers.get_all() == []
    assert client.viewers.last_result_complete is False

    # get
    v1 = await client.viewers.get("viewer-1")
    assert v1.id == "viewer-1"
    assert session.requests[3]["method"] == "GET"
    assert (
        session.requests[3]["url"]
        == "https://192.168.1.1/proxy/protect/integration/v1/viewers/viewer-1"
    )

    v2 = await client.viewers.get("viewer-1")
    assert v2.id == "viewer-1"

    with pytest.raises(ValueError, match="Viewer viewer-1 not found"):
        await client.viewers.get("viewer-1")

    with pytest.raises(ValueError, match="Failed to update viewer"):
        await client.viewers.update("viewer-1")

    # set_liveview
    slv = await client.viewers.set_liveview("viewer-1", "lv-1")
    assert slv.id == "viewer-1"
    assert session.requests[7]["method"] == "PATCH"
    assert (
        session.requests[7]["url"]
        == "https://192.168.1.1/proxy/protect/integration/v1/viewers/viewer-1"
    )
    assert session.requests[7]["json"] == {"liveview": "lv-1"}

    _assert_requests(
        session,
        [
            ("GET", "viewers", None, None),
            ("GET", "viewers", None, None),
            ("GET", "viewers", None, None),
            ("GET", "viewers/viewer-1", None, None),
            ("GET", "viewers/viewer-1", None, None),
            ("GET", "viewers/viewer-1", None, None),
            ("PATCH", "viewers/viewer-1", None, {}),
            ("PATCH", "viewers/viewer-1", None, {"liveview": "lv-1"}),
        ],
    )


# ===================================================================
# Protect models property and validator tests
# ===================================================================


def _sensor_timestamp(value: Any) -> int | None:
    sensor = Sensor.model_validate(
        {**SAMPLE_SENSOR, "openStatusChangedAt": value, "motionDetectedAt": value}
    )
    assert sensor.open_status_changed_at == sensor.motion_detected_at
    return sensor.open_status_changed_at


def test_protect_models_properties() -> None:
    """Test Protect model properties and edge cases."""
    # 1. Bridge display_name
    assert (
        Bridge.model_validate({"id": "b-1", "name": "Bridge 1"}).display_name
        == "Bridge 1"
    )
    assert Bridge.model_validate({"id": "b-1", "mac": "00:11"}).display_name == "00:11"
    assert Bridge.model_validate({"id": "b-1"}).display_name == "b-1"

    # 2. DoorLock display_name
    assert (
        DoorLock.model_validate({"id": "dl-1", "name": "Front Lock"}).display_name
        == "Front Lock"
    )
    assert (
        DoorLock.model_validate({"id": "dl-1", "mac": "00:22"}).display_name == "00:22"
    )
    assert DoorLock.model_validate({"id": "dl-1"}).display_name == "dl-1"

    # 3. Event duration
    e1 = Event.model_validate(
        {
            "id": "ev-1",
            "type": "motion",
            "start": "2026-10-08T10:00:00Z",
            "end": "2026-10-08T10:00:15Z",
        }
    )
    assert e1.duration == 15.0

    e2 = Event.model_validate(
        {"id": "ev-2", "type": "motion", "start": "2026-10-08T10:00:00Z"}
    )
    assert e2.duration is None

    # 4. NVR storage_info usage_percent and display_name
    s0 = StorageInfo(totalSize=0, usedSize=0)
    assert s0.usage_percent == 0.0
    s1 = StorageInfo(totalSize=1000, usedSize=250)
    assert s1.usage_percent == 25.0

    nvr = NVR.model_validate({"id": "n-1", "name": "My UNVR"})
    assert nvr.display_name == "My UNVR"
    nvr_mac = NVR.model_validate({"id": "n-1", "mac": "00:33"})
    assert nvr_mac.display_name == "00:33"
    nvr_id = NVR.model_validate({"id": "n-1"})
    assert nvr_id.display_name == "n-1"

    # 5. Relay display_name
    assert (
        Relay.model_validate({"id": "r-1", "name": "Gate Relay"}).display_name
        == "Gate Relay"
    )
    assert Relay.model_validate({"id": "r-1", "mac": "00:44"}).display_name == "00:44"
    assert Relay.model_validate({"id": "r-1"}).display_name == "r-1"

    # 6. Sensor timestamp validator and display_name
    assert _sensor_timestamp(None) is None
    bool_val = True
    assert _sensor_timestamp(bool_val) is None
    assert _sensor_timestamp(12345) == 12345
    assert _sensor_timestamp(12345.6) == 12345
    now = datetime(2026, 10, 8, 12, 0, 0, tzinfo=UTC)
    assert _sensor_timestamp(now) == int(now.timestamp() * 1000)
    naive = datetime(2026, 10, 8, 12, 0, 0)  # noqa: DTZ001
    assert _sensor_timestamp(naive) == int(now.timestamp() * 1000)
    assert _sensor_timestamp("2026-10-08T12:00:00Z") == int(now.timestamp() * 1000)
    assert _sensor_timestamp("2026-10-08T12:00:00") == int(now.timestamp() * 1000)
    assert _sensor_timestamp("invalid-date") is None
    assert _sensor_timestamp(object()) is None

    assert (
        Sensor.model_validate(
            {"id": "s-1", "mac": "00:55", "name": "Door Sensor"}
        ).display_name
        == "Door Sensor"
    )
    assert Sensor.model_validate({"id": "s-1", "mac": "00:55"}).display_name == "00:55"

    # 7. Siren display_name
    assert (
        Siren.model_validate({"id": "sir-1", "name": "Yard Siren"}).display_name
        == "Yard Siren"
    )
    assert Siren.model_validate({"id": "sir-1", "mac": "00:66"}).display_name == "00:66"
    assert Siren.model_validate({"id": "sir-1"}).display_name == "sir-1"

    # 8. Speaker display_name
    assert (
        Speaker.model_validate({"id": "spk-1", "name": "Horn Speaker"}).display_name
        == "Horn Speaker"
    )
    assert (
        Speaker.model_validate({"id": "spk-1", "mac": "00:77"}).display_name == "00:77"
    )
    assert Speaker.model_validate({"id": "spk-1"}).display_name == "spk-1"

    # 9. Viewer ViewerState _missing_, is_connected, and display_name
    assert ViewerState("NONEXISTENT_STATE") == ViewerState.UNKNOWN

    v_conn = Viewer.model_validate(
        {"id": "v-1", "mac": "00:88", "name": "Desk Viewer", "state": "CONNECTED"}
    )
    assert v_conn.is_connected is True
    assert v_conn.display_name == "Desk Viewer"

    v_disc = Viewer.model_validate(
        {"id": "v-2", "mac": "00:88", "state": "DISCONNECTED"}
    )
    assert v_disc.is_connected is False
    assert v_disc.display_name == "00:88"

    # 10. Viewport display_name
    assert (
        Viewport.model_validate({"id": "vp-1", "name": "Viewport TV"}).display_name
        == "Viewport TV"
    )
    assert (
        Viewport.model_validate({"id": "vp-1", "mac": "00:99"}).display_name == "00:99"
    )
    assert Viewport.model_validate({"id": "vp-1"}).display_name == "vp-1"


class _UploadBuffer:
    """Collect the multipart payload through its public asynchronous writer."""

    def __init__(self) -> None:
        self.content = b""

    async def write(self, data: bytes) -> None:
        self.content += data


@pytest.mark.xfail(
    strict=True,
    reason=(
        "application.upload_file sends JSON metadata; spec "
        "POST /v1/files/{fileType} requires multipart/form-data binary"
    ),
)
async def test_upload_file_spec_mismatch() -> None:
    """Binary file contents must reach the spec multipart upload transport."""
    session = _Session([SAMPLE_FILE])
    uploaded = await _client(session).application.upload_file(
        b"fake-gif", filename="test.gif"
    )
    assert isinstance(uploaded, DeviceFile)
    assert uploaded.id == "file-1"
    _assert_requests(session, [("POST", "files/animations", None, None)])
    # The multipart payload must contain the bytes, not only metadata.
    multipart = session.requests[0]["data"]
    payload = multipart() if callable(multipart) else multipart
    buffer = _UploadBuffer()
    await payload.write(buffer)
    assert b"fake-gif" in buffer.content
    assert b'filename="test.gif"' in buffer.content


@pytest.mark.xfail(
    strict=True,
    reason=(
        "sensors.set_motion_sensitivity sends top-level motionSensitivity; "
        "spec PATCH /v1/sensors/{id} expects motionSettings.sensitivity"
    ),
)
async def test_sensor_motion_sensitivity_spec_mismatch() -> None:
    """Motion sensitivity PATCH must nest the value under motionSettings."""
    session = _Session([SAMPLE_SENSOR])
    sensor = await _client(session).sensors.set_motion_sensitivity("sensor-1", 75)
    assert isinstance(sensor, Sensor)
    assert sensor.id == "sensor-1"
    _assert_requests(
        session,
        [("PATCH", "sensors/sensor-1", None, {"motionSettings": {"sensitivity": 75}})],
    )


@pytest.mark.parametrize(
    ("endpoint", "method", "args", "kwargs", "response", "verb", "path"),
    [
        ("alarm_hubs", "get", ("hub-1",), {}, None, "GET", "alarm-hubs/hub-1"),
        ("cameras", "get", ("cam-1",), {}, None, "GET", "cameras/cam-1"),
        ("chimes", "get", ("chime-1",), {}, None, "GET", "chimes/chime-1"),
        ("lights", "get", ("light-1",), {}, None, "GET", "lights/light-1"),
        ("liveviews", "get", ("lv-1",), {}, None, "GET", "liveviews/lv-1"),
        ("sensors", "get", ("sensor-1",), {}, None, "GET", "sensors/sensor-1"),
        ("viewers", "get", ("viewer-1",), {}, None, "GET", "viewers/viewer-1"),
        (
            "alarm_hubs",
            "update",
            ("hub-1",),
            {"name": "New name"},
            {"data": []},
            "PATCH",
            "alarm-hubs/hub-1",
        ),
        (
            "arm_profiles",
            "update",
            ("prof-1",),
            {"name": "Away"},
            {"data": []},
            "PATCH",
            "arm-profiles/prof-1",
        ),
        (
            "liveviews",
            "update",
            ("lv-1",),
            SAMPLE_LIVEVIEW,
            {"data": []},
            "PATCH",
            "liveviews/lv-1",
        ),
        (
            "sensors",
            "update",
            ("sensor-1",),
            {"name": "Door"},
            {"data": []},
            "PATCH",
            "sensors/sensor-1",
        ),
        (
            "arm_profiles",
            "create",
            (),
            {
                "name": "Home",
                "automations": [],
                "schedules": [],
                "recordEverything": False,
                "activationDelay": 0,
            },
            {"data": []},
            "POST",
            "arm-profiles",
        ),
        (
            "cameras",
            "get_rtsps_stream",
            ("cam-1",),
            {},
            {"data": []},
            "GET",
            "cameras/cam-1/rtsps-stream",
        ),
        (
            "cameras",
            "create_talkback_session",
            ("cam-1",),
            {},
            {"data": []},
            "POST",
            "cameras/cam-1/talkback-session",
        ),
        (
            "cameras",
            "disable_mic_permanently",
            ("cam-1",),
            {},
            {"data": []},
            "POST",
            "cameras/cam-1/disable-mic-permanently",
        ),
    ],
)
async def test_missing_and_malformed_object_responses(
    *,
    endpoint: str,
    method: str,
    args: tuple[str, ...],
    kwargs: dict[str, Any],
    response: Any,
    verb: str,
    path: str,
) -> None:
    """Empty objects and malformed envelopes cannot be published as devices."""
    session = _Session([response])
    resource = getattr(_client(session), endpoint)
    with pytest.raises(ValueError, match=r"not found|Failed to"):
        await getattr(resource, method)(*args, **kwargs)
    body = kwargs if verb in {"POST", "PATCH"} and kwargs else None
    _assert_requests(session, [(verb, path, None, body)])


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
async def test_protect_transport_error_mapping(
    status: int, exception: type[Exception]
) -> None:
    """Public device calls preserve the common HTTP exception mapping."""
    session = _Session([_Response({"error": "Request failed"}, status=status)])
    with pytest.raises(exception) as exc_info:
        await _client(session).sensors.get("sensor-1")
    assert exc_info.value.status_code == status
    _assert_requests(session, [("GET", "sensors/sensor-1", None, None)])


@pytest.mark.parametrize("response", [SAMPLE_FILE, {"data": SAMPLE_FILE}])
async def test_upload_file_response_parsing(response: dict[str, Any]) -> None:
    """Parse successful uploads without accepting the off-spec JSON body."""
    session = _Session([response])
    uploaded = await _client(session).application.upload_file(
        b"fake-gif", filename="test.gif"
    )
    assert isinstance(uploaded, DeviceFile)
    assert uploaded.id == "file-1"
    _assert_requests(session, [("POST", "files/animations", None, ANY)])


@pytest.mark.parametrize(
    ("method", "value"),
    [
        ("set_status_led", True),
        ("set_motion_sensitivity", 0),
        ("set_motion_sensitivity", 100),
    ],
)
async def test_sensor_setter_response_parsing(
    *, method: str, value: bool | int
) -> None:
    """Parse setter responses; strict xfails cover the incompatible bodies."""
    session = _Session([{"data": SAMPLE_SENSOR}])
    sensor = await getattr(_client(session).sensors, method)("sensor-1", value)
    assert isinstance(sensor, Sensor)
    assert sensor.id == "sensor-1"
    _assert_requests(session, [("PATCH", "sensors/sensor-1", None, ANY)])


async def test_liveview_delete_response() -> None:
    """Exercise the public delete return path without pinning an off-spec verb."""
    session = _Session([_Response(status=204)])
    assert await _client(session).liveviews.delete("lv-1") is True
    assert len(session.requests) == 1
    request = session.requests[0]
    assert request["url"] == (
        "https://192.168.1.1/proxy/protect/integration/v1/liveviews/lv-1"
    )
    assert request["params"] is None
    assert request["json"] is None
