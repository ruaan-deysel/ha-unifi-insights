# Copyright 2026 UniFi Insights contributors
"""Carrier Fabric client contracts through the recording HTTP transport."""

from __future__ import annotations

import json
import logging
from typing import Any, Self

import pytest
from yarl import URL

from custom_components.unifi_insights.api.auth import ApiKeyAuth
from custom_components.unifi_insights.api.carrier_fabric.client import (
    UniFiCarrierFabricClient,
)
from custom_components.unifi_insights.api.carrier_fabric.endpoints import (
    ServicePlansEndpoint,
    SubscribersEndpoint,
)
from custom_components.unifi_insights.api.carrier_fabric.models import ServicePlan
from custom_components.unifi_insights.api.exceptions import (
    UniFiAuthenticationError,
    UniFiResponseError,
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


def _client(session: _Session) -> UniFiCarrierFabricClient:
    return UniFiCarrierFabricClient(
        auth=ApiKeyAuth(api_key="test-key"), session=session
    )  # type: ignore[arg-type]


def _assert_request(session: _Session) -> None:
    assert len(session.requests) == 1
    request = session.requests[0]
    assert request["method"] == "GET"
    assert request["url"] == "https://api.ui.com/v1/carrier/service-plans"
    assert request["params"] is None
    assert request["json"] is None


async def test_validate_connection_success() -> None:
    """Connection validation uses spec listServicePlans without filters or body."""
    session = _Session([{"data": []}])
    client = _client(session)
    assert isinstance(client.subscribers, SubscribersEndpoint)
    assert isinstance(client.service_plans, ServicePlansEndpoint)
    assert await client.validate_connection() is True
    _assert_request(session)


async def test_service_plan_response_and_private_logging(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Public requests parse plans and omit response contents from debug logs."""
    session = _Session([{"data": [{"id": "plan-1", "name": "Private plan"}]}])
    client = _client(session)
    with caplog.at_level(
        logging.DEBUG, logger="custom_components.unifi_insights.api.base"
    ):
        plans = await client.service_plans.get_all()
    assert len(plans) == 1
    assert isinstance(plans[0], ServicePlan)
    assert plans[0].id == "plan-1"
    assert plans[0].name == "Private plan"
    assert "Private plan" not in caplog.text
    assert "[Carrier Fabric response omitted]" in caplog.text
    _assert_request(session)


@pytest.mark.parametrize("status", [401, 403])
async def test_validate_connection_auth_failure(status: int) -> None:
    """Authentication failures propagate from the actual HTTP seam."""
    session = _Session([_Response({"code": "UNAUTHORIZED"}, status=status)])
    with pytest.raises(UniFiAuthenticationError) as exc_info:
        await _client(session).validate_connection()
    assert exc_info.value.status_code == status
    assert exc_info.value.api_error_code == "UNAUTHORIZED"
    _assert_request(session)


@pytest.mark.parametrize(
    ("body", "expected_code"),
    [
        (None, None),
        ("", None),
        ("invalid json", None),
        ([1, 2, 3], None),
        (123, None),
        ({"other": 1}, None),
        ({"code": ""}, None),
        ({"code": 123}, None),
        ({"code": "PLAN_NOT_FOUND"}, "PLAN_NOT_FOUND"),
        ({"error": "FORBIDDEN"}, "FORBIDDEN"),
        ({"error": ""}, None),
        ({"error": {"code": "SUBSCRIBER_SUSPENDED"}}, "SUBSCRIBER_SUSPENDED"),
        ({"error": {"code": ""}}, None),
        ({"error": {}}, None),
    ],
)
async def test_response_error_codes(
    body: Any, expected_code: str | None, caplog: pytest.LogCaptureFixture
) -> None:
    """HTTP errors retain machine codes without logging subscriber or plan data."""
    session = _Session([_Response(body, status=400)])
    with (
        caplog.at_level(
            logging.DEBUG, logger="custom_components.unifi_insights.api.base"
        ),
        pytest.raises(UniFiResponseError) as exc_info,
    ):
        await _client(session).service_plans.get_all()
    assert exc_info.value.status_code == 400
    assert exc_info.value.api_error_code == expected_code
    if body is None or body == "":
        assert "body: empty" in caplog.text
    else:
        assert "[Carrier Fabric response omitted]" in caplog.text
    _assert_request(session)


@pytest.mark.parametrize("status", [404, 500])
async def test_transport_error_codes(status: int) -> None:
    """Other HTTP errors retain the Carrier Fabric machine code."""
    session = _Session([_Response({"code": "PLAN_NOT_FOUND"}, status=status)])
    with pytest.raises(UniFiResponseError) as exc_info:
        await _client(session).service_plans.get_all()
    assert exc_info.value.status_code == status
    assert exc_info.value.api_error_code == "PLAN_NOT_FOUND"
    _assert_request(session)
