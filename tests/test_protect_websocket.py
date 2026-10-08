# Copyright 2026
"""Tests for the vendored UniFi Protect WebSocket client.

This module lives under `custom_components/unifi_insights/api/**`, which is
excluded from the coverage gate (see `[tool.coverage.run].omit` in
pyproject.toml) because it is a vendored package. It still runs live against
production door-lock sensors, so it is tested directly here regardless of the
gate.
"""

from __future__ import annotations

import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from custom_components.unifi_insights.api import ApiKeyAuth, ConnectionType, LocalAuth
from custom_components.unifi_insights.api.protect import UniFiProtectClient
from custom_components.unifi_insights.api.protect.websocket import ProtectWebSocket


def _local_client() -> UniFiProtectClient:
    return UniFiProtectClient(
        auth=LocalAuth(api_key="test-key", verify_ssl=False),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
    )


def _remote_client() -> UniFiProtectClient:
    return UniFiProtectClient(
        auth=ApiKeyAuth(api_key="test-key"),
        connection_type=ConnectionType.REMOTE,
        console_id="console-1",
    )


@pytest.mark.asyncio
async def test_connect_passes_heartbeat_to_ws_connect() -> None:
    """`_connect()` must pass `heartbeat=30` to `session.ws_connect()`.

    Regression test (review finding 1, Major): without a heartbeat, aiohttp
    never pings a half-open connection - if the NVR stops responding
    without ever sending a close/error frame, `async for msg in ws` in
    `subscribe_with_callback` blocks forever and the existing
    reconnect/backoff logic below it never gets a chance to run (an events
    subscription stuck like this while the devices subscription reconnects
    cleanly is exactly the "motion silently stopped working for days"
    scenario `websocket_health` exists to catch). `heartbeat=30` makes
    aiohttp ping every 30s and force-close the connection (surfacing as
    `WSMsgType.CLOSED`/`ERROR`, which `subscribe_with_callback` already
    handles) if no pong comes back, turning a silent hang into a
    bounded-time reconnect.
    """
    client = _local_client()
    ws_socket = ProtectWebSocket(client)

    mock_session = MagicMock()
    mock_session.ws_connect = AsyncMock()
    client._ensure_session = AsyncMock(return_value=mock_session)

    await ws_socket._connect("/proxy/protect/integration/v1/subscribe/devices")

    mock_session.ws_connect.assert_awaited_once()
    _args, kwargs = mock_session.ws_connect.call_args
    assert kwargs.get("heartbeat") == 30


@pytest.mark.asyncio
async def test_connect_acquires_rate_limit_slot_before_handshake() -> None:
    """The WebSocket handshake shares the Protect client's HTTP budget."""
    client = _local_client()
    ws_socket = ProtectWebSocket(client)
    order: list[str] = []

    async def acquire_slot() -> None:
        order.append("acquire")

    async def connect(*_args: object, **_kwargs: object) -> MagicMock:
        order.append("connect")
        return MagicMock()

    session = MagicMock()
    session.ws_connect = AsyncMock(side_effect=connect)
    client._ensure_session = AsyncMock(return_value=session)
    client._throttle = AsyncMock(side_effect=acquire_slot)

    await ws_socket._connect("/proxy/protect/integration/v1/subscribe/events")

    assert order == ["acquire", "connect"]


@pytest.mark.asyncio
@pytest.mark.parametrize("subscription_type", ["devices", "events"])
@pytest.mark.parametrize(
    ("retry_after", "expected_delay"),
    [("2", 2), ("999", 5), (None, 5)],
)
async def test_direct_subscription_429_defers_shared_client(
    subscription_type: str,
    retry_after: str | None,
    expected_delay: int,
) -> None:
    """Both context-manager APIs defer later requests after a rejected handshake."""
    client = _local_client()
    ws_socket = ProtectWebSocket(client)
    headers = {"Retry-After": retry_after} if retry_after is not None else {}
    error = aiohttp.WSServerHandshakeError(MagicMock(), (), status=429, headers=headers)
    session = MagicMock()
    session.ws_connect = AsyncMock(side_effect=error)
    client._ensure_session = AsyncMock(return_value=session)
    client._throttle = AsyncMock()
    client._defer_after_rate_limit = MagicMock()

    subscribe = getattr(ws_socket, f"subscribe_{subscription_type}")
    with pytest.raises(aiohttp.WSServerHandshakeError):
        async with subscribe("nvr1", "default"):
            pytest.fail("A rejected handshake must not open the subscription")

    client._defer_after_rate_limit.assert_called_once_with(expected_delay)


def test_subscribe_path_local_uses_integration_api() -> None:
    """LOCAL WS subscribe path must match the client's own REST convention.

    Regression test: the WS path used to be hardcoded to a cloud-only
    `/ea/hosts/{host_id}/sites/{site_id}/subscribe/...` scheme that does not
    exist on a local console, which made the WebSocket silently non-functional
    for LOCAL (including Protect-only) consoles.
    """
    client = _local_client()

    assert (
        client.websocket._subscribe_path("devices")
        == "/proxy/protect/integration/v1/subscribe/devices"
    )
    assert (
        client.websocket._subscribe_path("events")
        == "/proxy/protect/integration/v1/subscribe/events"
    )


def test_subscribe_path_remote_uses_connector_routing() -> None:
    """REMOTE WS subscribe path must route through the connector like REST calls."""
    client = _remote_client()

    assert client.websocket._subscribe_path("devices") == (
        "/v1/connector/consoles/console-1/protect/integration/v1/subscribe/devices"
    )


def _make_ws(messages: list[aiohttp.WSMessage]) -> MagicMock:
    """Build a fake aiohttp WebSocket that yields the given messages then ends."""
    ws = MagicMock()
    ws.closed = False

    async def _aiter():
        for msg in messages:
            yield msg

    ws.__aiter__ = lambda self=ws: _aiter()
    ws.close = AsyncMock(side_effect=lambda: setattr(ws, "closed", True))
    return ws


@pytest.mark.asyncio
async def test_subscribe_with_callback_dispatches_messages() -> None:
    """A single successful connection delivers decoded JSON messages."""
    client = _local_client()
    ws_socket = ProtectWebSocket(client)

    text_msg = MagicMock(type=aiohttp.WSMsgType.TEXT, data='{"modelKey": "sensor"}')
    close_msg = MagicMock(type=aiohttp.WSMsgType.CLOSED)
    fake_ws = _make_ws([text_msg, close_msg])

    ws_socket._connect = AsyncMock(return_value=fake_ws)
    received: list[dict] = []

    await ws_socket.subscribe_with_callback(
        "nvr1", "default", "devices", received.append, reconnect=False
    )

    assert received == [{"modelKey": "sensor"}]
    fake_ws.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_subscribe_with_callback_invalid_subscription_type() -> None:
    """Only 'devices'/'events' are valid subscription types."""
    client = _local_client()
    ws_socket = ProtectWebSocket(client)

    with pytest.raises(ValueError, match=r"devices.*events"):
        await ws_socket.subscribe_with_callback(
            "nvr1", "default", "bogus", lambda _msg: None
        )


@pytest.mark.asyncio
async def test_subscribe_with_callback_drops_invalid_json(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Non-JSON text frames are dropped without invoking the callback."""
    client = _local_client()
    ws_socket = ProtectWebSocket(client)

    bad_msg = MagicMock(type=aiohttp.WSMsgType.TEXT, data="not-json")
    close_msg = MagicMock(type=aiohttp.WSMsgType.CLOSED)
    fake_ws = _make_ws([bad_msg, close_msg])
    ws_socket._connect = AsyncMock(return_value=fake_ws)

    callback = MagicMock()
    with caplog.at_level(logging.DEBUG):
        await ws_socket.subscribe_with_callback(
            "nvr1", "default", "devices", callback, reconnect=False
        )

    callback.assert_not_called()


@pytest.mark.asyncio
async def test_subscribe_with_callback_reconnects_after_client_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A connection error is logged at WARNING and triggers a reconnect."""
    client = _local_client()
    ws_socket = ProtectWebSocket(client)

    close_msg = MagicMock(type=aiohttp.WSMsgType.CLOSED)
    good_ws = _make_ws([close_msg])

    connect_calls = 0

    async def _connect(_path: str):
        nonlocal connect_calls
        connect_calls += 1
        if connect_calls == 1:
            msg = "handshake failed"
            raise aiohttp.ClientConnectionError(msg)
        # Second attempt succeeds, then subscribe_with_callback stops because
        # reconnect=False keeps _running True only for one more loop; force
        # stop from within the second connection.
        ws_socket.stop()
        return good_ws

    ws_socket._connect = _connect

    with caplog.at_level(logging.WARNING):
        await ws_socket.subscribe_with_callback(
            "nvr1",
            "default",
            "devices",
            lambda _msg: None,
            reconnect=True,
            reconnect_delay=0,
        )

    assert connect_calls == 2
    assert "connection error" in caplog.text.lower()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("retry_after", "expected_delay"),
    [("2", 2), ("999", 5), (None, 5)],
)
async def test_handshake_429_defers_requests_before_reconnect(
    retry_after: str | None,
    expected_delay: int,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A rejected handshake delays the shared client and its next attempt."""
    client = _local_client()
    ws_socket = ProtectWebSocket(client)
    headers = {"Retry-After": retry_after} if retry_after is not None else {}
    error = aiohttp.WSServerHandshakeError(MagicMock(), (), status=429, headers=headers)
    good_ws = _make_ws([MagicMock(type=aiohttp.WSMsgType.CLOSED)])
    calls = 0

    async def connect(*_args: object, **_kwargs: object) -> MagicMock:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise error
        ws_socket.stop()
        return good_ws

    session = MagicMock()
    session.ws_connect = AsyncMock(side_effect=connect)
    client._ensure_session = AsyncMock(return_value=session)
    client._throttle = AsyncMock()
    client._defer_after_rate_limit = MagicMock()

    with (
        caplog.at_level(logging.DEBUG),
        patch(
            "custom_components.unifi_insights.api.protect.websocket.asyncio.sleep",
            new_callable=AsyncMock,
        ) as sleep,
    ):
        await ws_socket.subscribe_with_callback(
            "nvr1",
            "default",
            "events",
            lambda _msg: None,
            reconnect_delay=0,
        )

    assert calls == 2
    client._defer_after_rate_limit.assert_called_once_with(expected_delay)
    sleep.assert_awaited_once_with(expected_delay)
    assert "requests deferred" in caplog.text
    assert not any(r.levelno == logging.WARNING for r in caplog.records)


@pytest.mark.asyncio
async def test_subscribe_with_callback_propagates_cancellation() -> None:
    """Cancellation must propagate, not be swallowed into a reconnect loop.

    Regression test: the previous implementation caught
    `asyncio.CancelledError` alongside `aiohttp.ClientError` and fell through
    to the reconnect-sleep branch, so `task.cancel()` from the integration's
    unload path never actually stopped the background WebSocket loop.
    """
    client = _local_client()
    ws_socket = ProtectWebSocket(client)

    async def _connect(_path: str):
        raise asyncio.CancelledError

    ws_socket._connect = _connect

    with pytest.raises(asyncio.CancelledError):
        await ws_socket.subscribe_with_callback(
            "nvr1", "default", "devices", lambda _msg: None
        )


def test_stop_sets_running_false() -> None:
    """stop() flips the running flag so the reconnect loop exits."""
    client = _local_client()
    ws_socket = ProtectWebSocket(client)
    ws_socket._running = True

    ws_socket.stop()

    assert ws_socket._running is False


@pytest.mark.asyncio
async def test_subscribe_with_callback_reports_connect_then_disconnect() -> None:
    """`on_connection_state_change` fires True after connect, False on exit.

    The coordinator's WS health signal and its "reconcile on WS reconnect"
    safety net (see coordinators/protect.py) both depend on knowing exactly
    when a subscription connects/disconnects - this method is the only place
    that actually knows.
    """
    client = _local_client()
    ws_socket = ProtectWebSocket(client)

    close_msg = MagicMock(type=aiohttp.WSMsgType.CLOSED)
    fake_ws = _make_ws([close_msg])
    ws_socket._connect = AsyncMock(return_value=fake_ws)

    states: list[bool] = []

    await ws_socket.subscribe_with_callback(
        "nvr1",
        "default",
        "devices",
        lambda _msg: None,
        reconnect=False,
        on_connection_state_change=states.append,
    )

    assert states == [True, False]


@pytest.mark.asyncio
async def test_subscribe_with_callback_reports_disconnect_before_reconnect() -> None:
    """A connection error reports False (never connected) before the retry,
    then True/False again around the successful reconnection.
    """
    client = _local_client()
    ws_socket = ProtectWebSocket(client)

    close_msg = MagicMock(type=aiohttp.WSMsgType.CLOSED)
    good_ws = _make_ws([close_msg])

    connect_calls = 0

    async def _connect(_path: str):
        nonlocal connect_calls
        connect_calls += 1
        if connect_calls == 1:
            msg = "handshake failed"
            raise aiohttp.ClientConnectionError(msg)
        ws_socket.stop()
        return good_ws

    ws_socket._connect = _connect
    states: list[bool] = []

    await ws_socket.subscribe_with_callback(
        "nvr1",
        "default",
        "devices",
        lambda _msg: None,
        reconnect=True,
        reconnect_delay=0,
        on_connection_state_change=states.append,
    )

    assert states == [False, True, False]


@pytest.mark.asyncio
async def test_subscribe_with_callback_without_state_callback_still_works() -> None:
    """`on_connection_state_change` is optional and defaults to a no-op."""
    client = _local_client()
    ws_socket = ProtectWebSocket(client)

    close_msg = MagicMock(type=aiohttp.WSMsgType.CLOSED)
    fake_ws = _make_ws([close_msg])
    ws_socket._connect = AsyncMock(return_value=fake_ws)

    # Must not raise even though no callback was supplied.
    await ws_socket.subscribe_with_callback(
        "nvr1", "default", "devices", lambda _msg: None, reconnect=False
    )


@pytest.mark.asyncio
async def test_connect_non_429_handshake_error_raises() -> None:
    """A non-429 WSServerHandshakeError raises without deferring rate limit."""
    client = _local_client()
    ws_socket = ProtectWebSocket(client)
    session = MagicMock()
    session.closed = False
    handshake_err = aiohttp.WSServerHandshakeError(
        MagicMock(), MagicMock(), status=500, message="Internal Server Error"
    )
    session.ws_connect = AsyncMock(side_effect=handshake_err)
    client._ensure_session = AsyncMock(return_value=session)
    client._defer_after_rate_limit = MagicMock()

    with pytest.raises(aiohttp.WSServerHandshakeError):
        await ws_socket._connect("/test")

    client._defer_after_rate_limit.assert_not_called()


@pytest.mark.asyncio
async def test_subscribe_with_callback_logs_state_callback_exception(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """An exception in on_connection_state_change is logged and does not abort."""
    client = _local_client()
    ws_socket = ProtectWebSocket(client)

    close_msg = MagicMock(type=aiohttp.WSMsgType.CLOSED)
    fake_ws = _make_ws([close_msg])
    ws_socket._connect = AsyncMock(return_value=fake_ws)

    states: list[object] = []

    def bad_callback(state: object) -> None:
        states.append(state)
        err_msg = "boom"
        raise RuntimeError(err_msg)

    with caplog.at_level(logging.ERROR):
        await ws_socket.subscribe_with_callback(
            "nvr1",
            "default",
            "devices",
            lambda _msg: None,
            reconnect=False,
            on_connection_state_change=bad_callback,
        )

    assert "on_connection_state_change callback raised" in caplog.text
    assert states == [True, False]


@pytest.mark.asyncio
async def test_subscribe_with_callback_reconnects_after_non_429_handshake_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A non-429 WSServerHandshakeError in the reconnect loop logs a warning."""
    client = _local_client()
    ws_socket = ProtectWebSocket(client)

    close_msg = MagicMock(type=aiohttp.WSMsgType.CLOSED)
    good_ws = _make_ws([close_msg])

    connect_calls = 0

    async def _connect(_path: str):
        nonlocal connect_calls
        connect_calls += 1
        if connect_calls == 1:
            raise aiohttp.WSServerHandshakeError(
                MagicMock(), MagicMock(), status=500, message="Server error"
            )
        ws_socket.stop()
        return good_ws

    ws_socket._connect = _connect

    with caplog.at_level(logging.WARNING):
        await ws_socket.subscribe_with_callback(
            "nvr1",
            "default",
            "devices",
            lambda _msg: None,
            reconnect=True,
            reconnect_delay=0,
        )

    assert connect_calls == 2
    assert "connection error subscribing to devices" in caplog.text


@pytest.mark.asyncio
async def test_subscribe_with_callback_handles_error_ws_message() -> None:
    """An ERROR WSMsgType breaks out of the message loop and finishes."""
    client = _local_client()
    ws_socket = ProtectWebSocket(client)

    err_msg = MagicMock(type=aiohttp.WSMsgType.ERROR)
    later_msg = MagicMock(type=aiohttp.WSMsgType.TEXT, data='{"event": "after-error"}')
    fake_ws = _make_ws([err_msg, later_msg])
    ws_socket._connect = AsyncMock(return_value=fake_ws)

    received: list[object] = []
    await ws_socket.subscribe_with_callback(
        "nvr1", "default", "devices", received.append, reconnect=False
    )

    assert received == []
    fake_ws.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_subscribe_with_callback_stops_when_not_running() -> None:
    """Setting running=False during iteration terminates the message loop."""
    client = _local_client()
    ws_socket = ProtectWebSocket(client)

    def _on_msg(_msg: dict) -> None:
        ws_socket.stop()

    msg1 = MagicMock(type=aiohttp.WSMsgType.TEXT, data='{"event": "1"}')
    msg2 = MagicMock(type=aiohttp.WSMsgType.TEXT, data='{"event": "2"}')
    fake_ws = _make_ws([msg1, msg2])
    ws_socket._connect = AsyncMock(return_value=fake_ws)

    received = []
    await ws_socket.subscribe_with_callback(
        "nvr1",
        "default",
        "devices",
        lambda m: (received.append(m), _on_msg(m)),
        reconnect=False,
    )

    assert len(received) == 1
