"""Tests for port forward and traffic rule API endpoints."""

from __future__ import annotations

import json
from typing import Any, Self

import pytest
from pydantic import ValidationError
from yarl import URL

from custom_components.unifi_insights.api import (
    ApiKeyAuth,
    ConnectionType,
    UniFiAuthenticationError,
    UniFiNotFoundError,
    UniFiResponseError,
)
from custom_components.unifi_insights.api.network.client import UniFiNetworkClient
from custom_components.unifi_insights.api.network.endpoints.port_forwards import (
    PortForwardsEndpoint,
)
from custom_components.unifi_insights.api.network.endpoints.traffic_rules import (
    TrafficRulesEndpoint,
)
from custom_components.unifi_insights.api.network.models.port_forward import PortForward
from custom_components.unifi_insights.api.network.models.traffic_rule import TrafficRule
from tests.fixtures.network_rule_responses import (
    AIOUNIFI_TRAFFIC_RULE_KEYS,
    LIVE_PORT_FORWARD_KEYS,
    port_forward_record,
    traffic_rule_record,
)


class _Response:
    """Minimal aiohttp response replacement for transport tests."""

    def __init__(
        self,
        body: Any = None,
        status: int = 200,
        headers: dict[str, str] | None = None,
        *,
        is_json: bool = True,
    ) -> None:
        self.status = status
        self._body = body
        self.headers = headers or {}
        self.url = URL("https://192.168.1.1")
        self.method = "GET"
        self.history = ()
        self._is_json = is_json

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
        if not self._is_json or self._body is None:
            msg = "No JSON body"
            raise ValueError(msg)
        return self._body


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

    async def close(self) -> None:
        self.closed = True


def _client(session: _Session) -> UniFiNetworkClient:
    return UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-key"),
        base_url="https://192.168.1.1",
        connection_type=ConnectionType.LOCAL,
        session=session,  # type: ignore[arg-type]
    )


def _remote_client(session: _Session) -> UniFiNetworkClient:
    return UniFiNetworkClient(
        auth=ApiKeyAuth(api_key="test-cloud-key"),
        connection_type=ConnectionType.REMOTE,
        console_id="console-1",
        session=session,  # type: ignore[arg-type]
    )


def _assert_request(
    request: dict[str, Any],
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    body: dict[str, Any] | None = None,
) -> None:
    """Pin all four observable parts of a request at the HTTP transport seam."""
    assert (request["method"], request["url"], request["params"], request["json"]) == (
        method,
        f"https://192.168.1.1/proxy/network{path}",
        params,
        body,
    )


def test_port_forward_fixture_matches_live_key_set() -> None:
    """Port forward fixture matches exactly the 14 live keys."""
    record = port_forward_record()
    assert set(record.keys()) == LIVE_PORT_FORWARD_KEYS
    assert len(LIVE_PORT_FORWARD_KEYS) == 14


def test_traffic_rule_fixture_matches_aiounifi_key_set() -> None:
    """Traffic rule fixture matches exactly the aiounifi v96 keys."""
    record = traffic_rule_record()
    assert set(record.keys()) == AIOUNIFI_TRAFFIC_RULE_KEYS
    assert len(AIOUNIFI_TRAFFIC_RULE_KEYS) == 15


async def test_list_port_forwards_local_path_and_models() -> None:
    """List port forwards calls local classic path and parses models."""
    rec = port_forward_record()
    session = _Session([{"meta": {"rc": "ok"}, "data": [rec]}])
    client = _client(session)

    rules = await client.port_forwards.list_port_forwards("default")

    assert len(session.requests) == 1
    _assert_request(session.requests[0], "GET", "/api/s/default/rest/portforward")
    assert len(rules) == 1
    rule = rules[0]
    assert rule.id == "pf-plex"
    assert rule.name == "Plex"
    assert rule.enabled is True
    assert rule.fwd == "192.168.1.50"


async def test_list_port_forwards_remote_connector_path() -> None:
    """List port forwards uses cloud connector path on remote connection."""
    session = _Session([{"meta": {"rc": "ok"}, "data": [port_forward_record()]}])
    client = _remote_client(session)

    rules = await client.port_forwards.list_port_forwards("default")

    assert len(rules) == 1
    assert len(session.requests) == 1
    assert (
        session.requests[0]["url"]
        == "https://api.ui.com/v1/connector/consoles/console-1/network/api/s/default/rest/portforward"
    )


@pytest.mark.parametrize(
    ("payload", "expected_count"),
    [
        ([port_forward_record()], 1),
        ({"meta": {"rc": "ok"}, "data": [port_forward_record()]}, 1),
        ({"data": port_forward_record()}, 1),
        ({"data": "unexpected"}, 0),
        (None, 0),
        ("not-a-dict", 0),
        ([port_forward_record(), "invalid", 123, None], 1),
    ],
)
async def test_list_port_forwards_response_envelopes(
    payload: Any, expected_count: int
) -> None:
    """List port forwards tolerates various response envelope formats."""
    session = _Session([payload])
    client = _client(session)

    rules = await client.port_forwards.list_port_forwards("default")
    assert len(rules) == expected_count


async def test_list_port_forwards_meta_error_raises() -> None:
    """List port forwards raises UniFiResponseError when meta rc is error."""
    session = _Session([{"meta": {"rc": "error", "msg": "API error"}}])
    client = _client(session)

    with pytest.raises(UniFiResponseError) as exc_info:
        await client.port_forwards.list_port_forwards("default")
    assert exc_info.value.message == "API error"


async def test_list_port_forwards_skips_items_without_string_id() -> None:
    """List port forwards skips items that fail validation due to missing string id."""
    bad_item = {"name": "No ID", "enabled": True}
    session = _Session([[bad_item, port_forward_record()]])
    client = _client(session)

    rules = await client.port_forwards.list_port_forwards("default")
    assert len(rules) == 1
    assert rules[0].id == "pf-plex"


async def test_list_port_forwards_tolerates_unexpected_types_in_undeclared_keys() -> (
    None
):
    """List port forwards tolerates unexpected types in undeclared extra keys."""
    record = port_forward_record(
        dst_port=32400,
        destination_ips=[{"ip": "203.0.113.7"}],
        unseen_controller_key="future_value",
    )
    session = _Session([[record]])
    client = _client(session)

    rules = await client.port_forwards.list_port_forwards("default")
    assert len(rules) == 1
    assert rules[0].unseen_controller_key == "future_value"


async def test_update_port_forward_puts_full_record_with_only_enabled_changed() -> None:
    """Update port forward performs GET then PUT of full record with enabled flipped."""
    original = port_forward_record(enabled=True)
    updated = dict(original)
    updated["enabled"] = False

    session = _Session(
        [
            {"meta": {"rc": "ok"}, "data": [original]},
            {"meta": {"rc": "ok"}, "data": [updated]},
        ]
    )
    client = _client(session)

    result = await client.port_forwards.update_port_forward(
        "default", "pf-plex", enabled=False
    )

    assert len(session.requests) == 2
    _assert_request(session.requests[0], "GET", "/api/s/default/rest/portforward")
    _assert_request(
        session.requests[1],
        "PUT",
        "/api/s/default/rest/portforward/pf-plex",
        body=updated,
    )
    assert set(session.requests[1]["json"].keys()) == LIVE_PORT_FORWARD_KEYS
    assert original["enabled"] is True  # not mutated
    assert result.enabled is False


async def test_update_port_forward_remote_connector_path() -> None:
    """Update port forward uses cloud connector path on remote connection."""
    original = port_forward_record(enabled=True)
    updated = dict(original)
    updated["enabled"] = False

    session = _Session(
        [
            {"meta": {"rc": "ok"}, "data": [original]},
            {"meta": {"rc": "ok"}, "data": [updated]},
        ]
    )
    client = _remote_client(session)

    result = await client.port_forwards.update_port_forward(
        "default", "pf-plex", enabled=False
    )

    assert len(session.requests) == 2
    assert (
        session.requests[0]["url"]
        == "https://api.ui.com/v1/connector/consoles/console-1/network/api/s/default/rest/portforward"
    )
    assert (
        session.requests[1]["url"]
        == "https://api.ui.com/v1/connector/consoles/console-1/network/api/s/default/rest/portforward/pf-plex"
    )
    assert session.requests[1]["json"] == updated
    assert result.enabled is False


async def test_update_port_forward_not_found_raises_and_sends_no_put() -> None:
    """Update port forward raises UniFiNotFoundError if rule not found."""
    session = _Session([{"meta": {"rc": "ok"}, "data": [port_forward_record()]}])
    client = _client(session)

    with pytest.raises(UniFiNotFoundError) as exc_info:
        await client.port_forwards.update_port_forward(
            "default", "pf-missing", enabled=False
        )
    assert "Port forward pf-missing not found" in exc_info.value.args[0]

    assert len(session.requests) == 1


@pytest.mark.parametrize(
    "put_response",
    [
        {"meta": {"rc": "ok"}, "data": []},
        {},
    ],
)
async def test_update_port_forward_uses_payload_when_put_echo_missing(
    put_response: Any,
) -> None:
    """Update port forward falls back to validated payload when PUT echo is absent."""
    original = port_forward_record(enabled=True)
    session = _Session(
        [
            {"meta": {"rc": "ok"}, "data": [original]},
            put_response,
        ]
    )
    client = _client(session)

    result = await client.port_forwards.update_port_forward(
        "default", "pf-plex", enabled=False
    )
    assert result.id == "pf-plex"
    assert result.enabled is False


async def test_update_port_forward_put_meta_error_raises() -> None:
    """Update port forward raises UniFiResponseError when PUT response is error."""
    original = port_forward_record(enabled=True)
    session = _Session(
        [
            {"meta": {"rc": "ok"}, "data": [original]},
            {"meta": {"rc": "error", "msg": "Write failed"}},
        ]
    )
    client = _client(session)

    with pytest.raises(UniFiResponseError) as exc_info:
        await client.port_forwards.update_port_forward(
            "default", "pf-plex", enabled=False
        )
    assert exc_info.value.message == "Write failed"


async def test_list_traffic_rules_local_v2_path_and_models() -> None:
    """List traffic rules calls local v2 path and parses models."""
    rec = traffic_rule_record()
    session = _Session([[rec]])
    client = _client(session)

    rules = await client.traffic_rules.list_traffic_rules("default")

    assert len(session.requests) == 1
    _assert_request(session.requests[0], "GET", "/v2/api/site/default/trafficrules")
    assert len(rules) == 1
    rule = rules[0]
    assert rule.id == "tr-bedtime"
    assert rule.description == "Bedtime"
    assert rule.enabled is True
    assert rule.action == "BLOCK"


async def test_list_traffic_rules_remote_connector_path() -> None:
    """List traffic rules uses cloud connector v2 path on remote connection."""
    session = _Session([{"meta": {"rc": "ok"}, "data": [traffic_rule_record()]}])
    client = _remote_client(session)

    rules = await client.traffic_rules.list_traffic_rules("default")

    assert len(rules) == 1
    assert len(session.requests) == 1
    assert (
        session.requests[0]["url"]
        == "https://api.ui.com/v1/connector/consoles/console-1/network/v2/api/site/default/trafficrules"
    )


@pytest.mark.parametrize(
    ("payload", "expected_count"),
    [
        ([traffic_rule_record()], 1),
        ({"meta": {"rc": "ok"}, "data": [traffic_rule_record()]}, 1),
        ({"data": traffic_rule_record()}, 1),
        (None, 0),
        ("not-a-dict", 0),
        ({"data": 123}, 0),
        ([traffic_rule_record(), "invalid", 456, None, {"description": "no-id"}], 1),
    ],
)
async def test_list_traffic_rules_response_envelopes(
    payload: Any, expected_count: int
) -> None:
    """List traffic rules tolerates various response envelope formats."""
    session = _Session([payload])
    client = _client(session)

    rules = await client.traffic_rules.list_traffic_rules("default")
    assert len(rules) == expected_count


async def test_list_traffic_rules_meta_error_raises() -> None:
    """List traffic rules raises UniFiResponseError when meta rc is error."""
    session = _Session([{"meta": {"rc": "error", "msg": "API failure"}}])
    client = _client(session)

    with pytest.raises(UniFiResponseError) as exc_info:
        await client.traffic_rules.list_traffic_rules("default")
    assert exc_info.value.message == "API failure"


async def test_update_traffic_rule_puts_full_record_with_only_enabled_changed() -> None:
    """Update traffic rule puts full record to v2 endpoint with only enabled changed."""
    original = traffic_rule_record(enabled=True)
    updated = dict(original)
    updated["enabled"] = False

    session = _Session(
        [
            [original],
            updated,
        ]
    )
    client = _client(session)

    result = await client.traffic_rules.update_traffic_rule(
        "default", "tr-bedtime", enabled=False
    )

    assert len(session.requests) == 2
    _assert_request(session.requests[0], "GET", "/v2/api/site/default/trafficrules")
    _assert_request(
        session.requests[1],
        "PUT",
        "/v2/api/site/default/trafficrules/tr-bedtime",
        body=updated,
    )
    assert set(session.requests[1]["json"].keys()) == AIOUNIFI_TRAFFIC_RULE_KEYS
    # Nested fields are byte/value-identical
    assert session.requests[1]["json"]["schedule"] == original["schedule"]
    assert session.requests[1]["json"]["bandwidth_limit"] == original["bandwidth_limit"]
    assert session.requests[1]["json"]["target_devices"] == original["target_devices"]
    assert original["enabled"] is True
    assert result.enabled is False


async def test_update_traffic_rule_remote_connector_path() -> None:
    """Update traffic rule uses cloud connector v2 path on remote connection."""
    original = traffic_rule_record(enabled=True)
    updated = dict(original)
    updated["enabled"] = False

    session = _Session(
        [
            [original],
            updated,
        ]
    )
    client = _remote_client(session)

    result = await client.traffic_rules.update_traffic_rule(
        "default", "tr-bedtime", enabled=False
    )

    assert len(session.requests) == 2
    assert (
        session.requests[0]["url"]
        == "https://api.ui.com/v1/connector/consoles/console-1/network/v2/api/site/default/trafficrules"
    )
    assert (
        session.requests[1]["url"]
        == "https://api.ui.com/v1/connector/consoles/console-1/network/v2/api/site/default/trafficrules/tr-bedtime"
    )
    assert session.requests[1]["json"] == updated
    assert result.enabled is False


async def test_update_traffic_rule_not_found_raises_and_sends_no_put() -> None:
    """Update traffic rule raises UniFiNotFoundError if rule not found."""
    session = _Session([{"meta": {"rc": "ok"}, "data": [traffic_rule_record()]}])
    client = _client(session)

    with pytest.raises(UniFiNotFoundError) as exc_info:
        await client.traffic_rules.update_traffic_rule(
            "default", "tr-missing", enabled=False
        )
    assert "Traffic rule tr-missing not found" in exc_info.value.args[0]

    assert len(session.requests) == 1


@pytest.mark.parametrize(
    "put_response",
    [
        {"meta": {"rc": "ok"}, "data": []},
        {},
    ],
)
async def test_update_traffic_rule_uses_payload_when_put_echo_missing(
    put_response: Any,
) -> None:
    """Update traffic rule falls back to validated payload when PUT echo is absent."""
    original = traffic_rule_record(enabled=True)
    session = _Session(
        [
            {"meta": {"rc": "ok"}, "data": [original]},
            put_response,
        ]
    )
    client = _client(session)

    result = await client.traffic_rules.update_traffic_rule(
        "default", "tr-bedtime", enabled=False
    )
    assert result.id == "tr-bedtime"
    assert result.enabled is False


@pytest.mark.parametrize("endpoint_name", ["port_forwards", "traffic_rules"])
@pytest.mark.parametrize(
    ("status", "body", "expected_exc", "is_json"),
    [
        (401, {"error": "unauthorized"}, UniFiAuthenticationError, True),
        (403, {"error": "forbidden"}, UniFiAuthenticationError, True),
        (404, {"error": "not found"}, UniFiNotFoundError, True),
        (200, "<html>Bad Gateway</html>", UniFiResponseError, False),
    ],
)
async def test_rule_endpoints_map_http_errors(
    endpoint_name: str,
    status: int,
    body: Any,
    expected_exc: type[Exception],
    is_json: bool,  # noqa: FBT001
) -> None:
    """Rule list endpoints map HTTP errors to specific integration exceptions."""
    session = _Session([_Response(body, status=status, is_json=is_json)])
    client = _client(session)

    coro = (
        client.port_forwards.list_port_forwards("default")
        if endpoint_name == "port_forwards"
        else client.traffic_rules.list_traffic_rules("default")
    )
    with pytest.raises(expected_exc) as exc_info:
        await coro

    assert exc_info.value.status_code == status


def test_client_registers_rule_endpoints() -> None:
    """Client exposes port_forwards and traffic_rules endpoint properties."""
    client = _client(_Session([]))
    assert isinstance(client.port_forwards, PortForwardsEndpoint)
    assert isinstance(client.traffic_rules, TrafficRulesEndpoint)


def test_rule_models_require_string_id() -> None:
    """Both models require id and accept id or _id alias."""
    pf1 = PortForward.model_validate({"_id": "pf-1"})
    assert pf1.id == "pf-1"
    pf2 = PortForward.model_validate({"id": "pf-2"})
    assert pf2.id == "pf-2"
    with pytest.raises(ValidationError):
        PortForward.model_validate({})

    tr1 = TrafficRule.model_validate({"_id": "tr-1"})
    assert tr1.id == "tr-1"
    tr2 = TrafficRule.model_validate({"id": "tr-2"})
    assert tr2.id == "tr-2"
    with pytest.raises(ValidationError):
        TrafficRule.model_validate({})
