# Copyright 2026 UniFi Insights contributors
"""Tests for UniFi Network endpoint methods and models (strand A2)."""

from __future__ import annotations

import json
from typing import Any, Self

import pytest
from pydantic import ValidationError
from yarl import URL

from custom_components.unifi_insights.api import ApiKeyAuth, ConnectionType
from custom_components.unifi_insights.api.base import _redact
from custom_components.unifi_insights.api.exceptions import (
    UniFiNotFoundError,
    UniFiResponseError,
    UniFiValidationError,
)
from custom_components.unifi_insights.api.network import (
    PolicyBasedRoute,
    UniFiNetworkClient,
    VpnClient,
)
from custom_components.unifi_insights.api.network.models.client import Client
from custom_components.unifi_insights.api.network.models.device import (
    Device,
    parse_outlet_metrics,
)
from custom_components.unifi_insights.api.network.models.lag import LAG, McLagDomain
from custom_components.unifi_insights.api.network.models.report import (
    SiteReportBucket,
)
from custom_components.unifi_insights.api.network.models.site import Site
from custom_components.unifi_insights.api.network.models.stack import SwitchStack
from custom_components.unifi_insights.api.network.models.voucher import (
    Voucher,
    VoucherCreateRequest,
)
from custom_components.unifi_insights.api.network.models.wifi import (
    WifiNetwork,
    WifiSecurity,
)


class _Response:
    """Minimal aiohttp response replacement for transport tests."""

    def __init__(
        self,
        body: Any = None,
        status: int = 200,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status = status
        self._body = body
        self.headers = headers or {}
        self.url = URL("https://192.168.1.1")
        self.method = "GET"
        self.history = ()

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


def _wifi_document(name: str) -> dict[str, Any]:
    """Required STANDARD broadcast fields from Network v10.6.106's schema."""
    return {
        "type": "STANDARD",
        "name": name,
        "enabled": True,
        "hideName": False,
        "securityConfiguration": {"type": "OPEN"},
        "channel2gLockedTo6": False,
        "clientIsolationEnabled": False,
        "dtimPeriod2gLockedTo3": False,
        "multicastToUnicastConversionEnabled": False,
        "uapsdEnabled": False,
        "advertiseDeviceName": False,
        "arpProxyEnabled": False,
        "broadcastingFrequenciesGHz": [2.4, 5],
        "bssTransitionEnabled": False,
    }


# =============================================================================
# 1. clients.py
# =============================================================================


async def test_clients_get_pins_spec_request_and_branches() -> None:
    """clients.get pins GET /v1/sites/{siteId}/clients/{clientId}
    and covers branches.
    """
    raw_client = {
        "id": "client-1",
        "macAddress": "00:11:22:33:44:55",
        "ipAddress": "192.168.1.50",
    }
    session = _Session(
        [
            # 1. Wrapped dict
            {"data": raw_client},
            # 2. Direct dict
            raw_client,
            # 3. Wrapped single-item list
            {"data": [raw_client]},
            # 4. Empty list in data -> ValueError
            {"data": []},
            # 5. Non-dict response -> ValueError
            [],
        ]
    )
    client = _client(session)

    # 1. Wrapped dict
    res1 = await client.clients.get("default", "client-1")
    assert isinstance(res1, Client)
    assert res1.id == "client-1"
    assert res1.mac == "00:11:22:33:44:55"
    req1 = session.requests[0]
    assert req1["method"] == "GET"
    assert (
        req1["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/clients/client-1"
    )
    assert req1["params"] is None
    assert req1["json"] is None

    # 2. Direct dict
    res2 = await client.clients.get("default", "client-1")
    assert isinstance(res2, Client)
    assert res2.id == "client-1"

    # 3. Wrapped single-item list
    res3 = await client.clients.get("default", "client-1")
    assert isinstance(res3, Client)
    assert res3.id == "client-1"

    # 4. Empty list in data -> raises ValueError
    with pytest.raises(ValueError, match="Client client-1 not found"):
        await client.clients.get("default", "client-1")

    # 5. Non-dict response -> raises ValueError
    with pytest.raises(ValueError, match="Client client-1 not found"):
        await client.clients.get("default", "client-1")


async def test_clients_get_error_mapping() -> None:
    """clients.get maps HTTP errors to UniFi exceptions."""
    session = _Session(
        [
            _Response("Not found", status=404),
            _Response("Server error", status=500),
        ]
    )
    client = _client(session)

    with pytest.raises(UniFiNotFoundError):
        await client.clients.get("default", "missing-client")

    with pytest.raises(UniFiResponseError):
        await client.clients.get("default", "err-client")


async def test_clients_stamgr_command_envelope_error() -> None:
    """clients._stamgr_command raises UniFiResponseError when meta.rc is error."""
    # Classic endpoint: POST /proxy/network/api/s/{site}/cmd/stamgr (unspecified legacy)
    session = _Session(
        [
            {"meta": {"rc": "error", "msg": "Client not found"}},
        ]
    )
    client = _client(session)

    with pytest.raises(UniFiResponseError) as exc_info:
        await client.clients.block("default", "00:11:22:33:44:55")
    assert "Client not found" in exc_info.value.message

    req = session.requests[0]
    assert req["method"] == "POST"
    assert req["url"] == "https://192.168.1.1/proxy/network/api/s/default/cmd/stamgr"
    assert req["json"] == {"cmd": "block-sta", "mac": "00:11:22:33:44:55"}
    assert req["params"] is None


# =============================================================================
# 2. devices.py
# =============================================================================


async def test_devices_get_pins_spec_request_and_branches() -> None:
    """devices.get pins GET /v1/sites/{siteId}/devices/{deviceId}
    and covers branches.
    """
    raw_device = {
        "id": "dev-1",
        "name": "Switch 1",
        "macAddress": "00:11:22:33:44:55",
    }
    session = _Session(
        [
            # 1. Wrapped dict
            {"data": raw_device},
            # 2. Direct dict
            raw_device,
            # 3. Wrapped single-item list
            {"data": [raw_device]},
            # 4. Empty list in data -> ValueError
            {"data": []},
            # 5. Non-dict response -> ValueError
            [],
        ]
    )
    client = _client(session)

    # 1. Wrapped dict
    res1 = await client.devices.get("default", "dev-1")
    assert isinstance(res1, Device)
    assert res1.id == "dev-1"
    assert res1.name == "Switch 1"
    req1 = session.requests[0]
    assert req1["method"] == "GET"
    assert (
        req1["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/devices/dev-1"
    )
    assert req1["params"] is None
    assert req1["json"] is None

    # 2. Direct dict
    res2 = await client.devices.get("default", "dev-1")
    assert isinstance(res2, Device)
    assert res2.id == "dev-1"

    # 3. Wrapped single-item list
    res3 = await client.devices.get("default", "dev-1")
    assert isinstance(res3, Device)
    assert res3.id == "dev-1"

    # 4. Empty list in data -> raises ValueError
    with pytest.raises(ValueError, match="Device dev-1 not found"):
        await client.devices.get("default", "dev-1")

    # 5. Non-dict response -> raises ValueError
    with pytest.raises(ValueError, match="Device dev-1 not found"):
        await client.devices.get("default", "dev-1")


async def test_devices_get_error_mapping() -> None:
    """devices.get maps HTTP errors to UniFi exceptions."""
    session = _Session(
        [
            _Response("Not found", status=404),
            _Response("Server error", status=500),
        ]
    )
    client = _client(session)

    with pytest.raises(UniFiNotFoundError):
        await client.devices.get("default", "missing-dev")

    with pytest.raises(UniFiResponseError):
        await client.devices.get("default", "err-dev")


async def test_devices_forget_pins_spec_request_and_error_mapping() -> None:
    """devices.forget pins DELETE /v1/sites/{siteId}/devices/{deviceId}."""
    session = _Session(
        [
            {},
            _Response("Not found", status=404),
            _Response("Server error", status=500),
        ]
    )
    client = _client(session)

    assert await client.devices.forget("default", "dev-1") is True
    req = session.requests[0]
    assert req["method"] == "DELETE"
    assert (
        req["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/devices/dev-1"
    )
    assert req["params"] is None
    assert req["json"] is None

    with pytest.raises(UniFiNotFoundError):
        await client.devices.forget("default", "missing-dev")

    with pytest.raises(UniFiResponseError):
        await client.devices.forget("default", "err-dev")


async def test_devices_get_pending_adoption_pins_spec_request_and_branches() -> None:
    """devices.get_pending_adoption pins GET /v1/pending-devices
    and handles pagination/errors.
    """
    raw_pending = {
        "id": "pending-1",
        "name": "AP-Hallway",
        "macAddress": "aa:bb:cc:dd:ee:ff",
    }
    session = _Session(
        [
            # 1. Full params query
            {"data": [raw_pending]},
            # 2. None response
            None,
            # 3. Non-list data
            {"data": "not-a-list"},
            # 4. Data list with non-dict item and invalid device item
            {
                "data": [
                    "non-dict-entry",
                    {"id": "invalid-dev", "uptime": "not-a-number"},
                    raw_pending,
                ]
            },
        ]
    )
    client = _client(session)

    # 1. Full params query
    res1 = await client.devices.get_pending_adoption(
        offset=5, limit=10, filter_str="model.eq(U6-Lite)"
    )
    assert len(res1) == 1
    assert isinstance(res1[0], Device)
    assert res1[0].id == "pending-1"
    req1 = session.requests[0]
    assert req1["method"] == "GET"
    assert (
        req1["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/pending-devices"
    )
    assert req1["params"] == {
        "offset": 5,
        "limit": 10,
        "filter": "model.eq(U6-Lite)",
    }
    assert req1["json"] is None

    # 2. None response
    assert await client.devices.get_pending_adoption() == []

    # 3. Non-list data
    assert await client.devices.get_pending_adoption() == []

    # 4. List with non-dict and invalid items
    res4 = await client.devices.get_pending_adoption()
    assert len(res4) == 1
    assert res4[0].id == "pending-1"


async def test_devices_get_legacy_device_stats_direct_dict() -> None:
    """devices.get_legacy_device_stats handles direct dict data envelope."""
    # Legacy endpoint: GET /proxy/network/api/s/{site}/stat/device/{mac} (unspecified)
    session = _Session(
        [
            {"data": {"cpu": 15.0, "mem": 30.0}},
        ]
    )
    client = _client(session)

    res = await client.devices.get_legacy_device_stats("default", "00:11:22:33:44:55")
    assert res == {"cpu": 15.0, "mem": 30.0}
    req = session.requests[0]
    assert req["method"] == "GET"
    assert (
        req["url"]
        == "https://192.168.1.1/proxy/network/api/s/default/stat/device/00:11:22:33:44:55"
    )
    assert req["params"] is None
    assert req["json"] is None


async def test_devices_get_port_metrics_power_fallbacks() -> None:
    """devices.get_port_metrics covers alternate power and byte keys
    and fallback sum.
    """
    # 1. Device with camelCase portPoe, poePower, rxBytes, txBytes, and totalUsedPower
    dev1 = {
        "port_table": [
            {
                "port_idx": 1,
                "portPoe": True,
                "poePower": "4.5",
                "rxBytes": "1000",
                "txBytes": "2000",
            }
        ],
        "totalUsedPower": "4.5",
    }
    # 2. Device with total_poe_power
    dev2 = {
        "port_table": [],
        "total_poe_power": "12.0",
    }
    # 3. Device with poe_total_power
    dev3 = {
        "port_table": [],
        "poe_total_power": "18.5",
    }
    # 4. Device where total power is None, falls back to sum of poe_ports
    dev4 = {
        "port_table": [
            {"port_idx": 1, "port_poe": True, "poe_power": "5.0"},
            {"port_idx": 2, "port_poe": True, "poe_power": "7.0"},
        ]
    }
    session = _Session(
        [
            {"data": [dev1]},
            {"data": [dev2]},
            {"data": [dev3]},
            {"data": [dev4]},
        ]
    )
    client = _client(session)

    m1 = await client.devices.get_port_metrics("default", "00:11:22:33:44:55")
    assert m1.poe_total_w == 4.5
    assert m1.poe_ports == {1: 4.5}
    assert m1.port_bytes[1].rx_bytes == 1000
    assert m1.port_bytes[1].tx_bytes == 2000

    m2 = await client.devices.get_port_metrics("default", "00:11:22:33:44:55")
    assert m2.poe_total_w == 12.0

    m3 = await client.devices.get_port_metrics("default", "00:11:22:33:44:55")
    assert m3.poe_total_w == 18.5

    m4 = await client.devices.get_port_metrics("default", "00:11:22:33:44:55")
    assert m4.poe_total_w == 12.0

    assert len(session.requests) == 4
    for request in session.requests:
        _assert_request(request, "GET", "/api/s/default/stat/device/00:11:22:33:44:55")


async def test_devices_set_outlet_state_branches() -> None:
    """devices.set_outlet_state covers seeding, missing index, and append override."""
    session = _Session(
        [
            # 1. Seeding from outlet_table and modifying existing outlet
            {},
            # 2. Appending new outlet override with cycle_enabled
            {},
        ]
    )
    client = _client(session)

    # Error case: no outlet_overrides and no outlet_table
    with pytest.raises(UniFiValidationError, match="Refusing to write outlet"):
        await client.devices.set_outlet_state(
            site_name="default",
            device_id="dev-empty",
            outlet_index=1,
            state=True,
            current_device={},
        )

    # 1. Seed from outlet_table with outlet_idx, non-numeric index skipped,
    # cycle_enabled
    device_seed = {
        "_id": "dev-seed",
        "outlet_table": [
            {
                "outlet_idx": "1",
                "relay_state": False,
                "name": "Outlet 1",
                "cycle_enabled": True,
            },
            {"index": "bad-index"},
            "non-dict",
        ],
    }
    assert (
        await client.devices.set_outlet_state(
            site_name="default",
            device_id="dev-seed",
            outlet_index=1,
            state=True,
            cycle_enabled=False,
            current_device=device_seed,
        )
        is True
    )

    req1 = session.requests[0]
    assert req1["method"] == "PUT"
    assert (
        req1["url"]
        == "https://192.168.1.1/proxy/network/api/s/default/rest/device/dev-seed"
    )
    assert req1["json"] == {
        "outlet_overrides": [
            {
                "index": 1,
                "relay_state": True,
                "name": "Outlet 1",
                "cycle_enabled": False,
            }
        ]
    }
    assert req1["params"] is None

    # 2. Existing overrides where target is not found -> appends new override
    device_append = {
        "_id": "dev-append",
        "outlet_overrides": [
            {"outlet_idx": "1", "relay_state": True},
            {"index": "invalid"},
        ],
    }
    assert (
        await client.devices.set_outlet_state(
            site_name="default",
            device_id="dev-append",
            outlet_index=2,
            state=True,
            cycle_enabled=True,
            current_device=device_append,
        )
        is True
    )

    req2 = session.requests[1]
    assert req2["json"] == {
        "outlet_overrides": [
            {"outlet_idx": "1", "relay_state": True},
            {"index": "invalid"},
            {"index": 2, "relay_state": True, "cycle_enabled": True},
        ]
    }
    assert req2["params"] is None


# =============================================================================
# 3. lags.py
# =============================================================================


async def test_lags_get_all_pins_spec_request_and_pagination() -> None:
    """lags.get_all pins GET /v1/sites/{siteId}/switching/lags and tests pagination."""
    lag1 = {"id": "lag-1", "name": "LAG-1"}
    lag2 = {"id": "lag-2", "name": "LAG-2"}
    session = _Session(
        [
            # 1. Single page fetch with offset, limit, filter_str
            {"data": [lag1]},
            # 2. Auto-pagination: page 1 then page 2
            {"data": [lag1], "count": 1, "totalCount": 2},
            {"data": [lag2], "count": 1, "totalCount": 2},
            # 3. Non-dict page stops pagination
            [],
            # 4. totalCount missing stops pagination
            {"data": [lag1]},
            # 5. count == 0 stops pagination
            {"data": [], "count": 0, "totalCount": 10},
        ]
    )
    client = _client(session)

    # 1. Single page fetch
    res1 = await client.lags.get_all(
        "default", offset=5, limit=10, filter_str="name.eq(LAG-1)"
    )
    assert len(res1) == 1
    assert isinstance(res1[0], LAG)
    assert res1[0].id == "lag-1"
    req1 = session.requests[0]
    assert req1["method"] == "GET"
    assert (
        req1["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/switching/lags"
    )
    assert req1["params"] == {
        "offset": 5,
        "limit": 10,
        "filter": "name.eq(LAG-1)",
    }
    assert req1["json"] is None

    # 2. Auto-pagination
    res2 = await client.lags.get_all("default")
    assert len(res2) == 2
    assert res2[0].id == "lag-1"
    assert res2[1].id == "lag-2"
    assert session.requests[1]["params"] == {"offset": 0, "limit": 100}
    assert session.requests[2]["params"] == {"offset": 1, "limit": 100}

    # 3. Non-dict page
    assert await client.lags.get_all("default") == []

    # 4. totalCount missing
    res4 = await client.lags.get_all("default")
    assert len(res4) == 1

    # 5. count == 0
    res5 = await client.lags.get_all("default")
    assert res5 == []


async def test_lags_get_pins_spec_request_and_branches() -> None:
    """lags.get pins GET /v1/sites/{siteId}/switching/lags/{lagId}
    and covers branches.
    """
    raw_lag = {"id": "lag-1", "name": "LAG-1"}
    session = _Session(
        [
            # 1. Wrapped dict
            {"data": raw_lag},
            # 2. Direct dict
            raw_lag,
            # 3. Wrapped list
            {"data": [raw_lag]},
            # 4. Empty list -> ValueError
            {"data": []},
            # 5. Error status mapping
            _Response("Not found", status=404),
            _Response("Server error", status=500),
        ]
    )
    client = _client(session)

    res1 = await client.lags.get("default", "lag-1")
    assert isinstance(res1, LAG)
    assert res1.id == "lag-1"
    req1 = session.requests[0]
    assert req1["method"] == "GET"
    assert (
        req1["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/switching/lags/lag-1"
    )
    assert req1["params"] is None
    assert req1["json"] is None

    res2 = await client.lags.get("default", "lag-1")
    assert res2.id == "lag-1"

    res3 = await client.lags.get("default", "lag-1")
    assert res3.id == "lag-1"

    with pytest.raises(ValueError, match="LAG lag-1 not found"):
        await client.lags.get("default", "lag-1")

    with pytest.raises(UniFiNotFoundError):
        await client.lags.get("default", "missing-lag")

    with pytest.raises(UniFiResponseError):
        await client.lags.get("default", "err-lag")


async def test_lags_mc_lag_domains_pins_spec_requests_and_branches() -> None:
    """lags MC-LAG domain methods pin spec requests and cover branches."""
    raw_mc = {"id": "mc-1", "domainId": 1}
    session = _Session(
        [
            # 1. get_mc_lag_domains single page with offset/limit
            {"data": [raw_mc]},
            # 2. get_mc_lag_domain wrapped dict
            {"data": raw_mc},
            # 3. get_mc_lag_domain wrapped list
            {"data": [raw_mc]},
            # 4. get_mc_lag_domain empty -> ValueError
            {"data": []},
            # 5. Error mapping
            _Response("Not found", status=404),
            _Response("Server error", status=500),
        ]
    )
    client = _client(session)

    # 1. get_mc_lag_domains
    res_list = await client.lags.get_mc_lag_domains("default", offset=0, limit=5)
    assert len(res_list) == 1
    assert isinstance(res_list[0], McLagDomain)
    assert res_list[0].id == "mc-1"
    req1 = session.requests[0]
    assert req1["method"] == "GET"
    assert (
        req1["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/switching/mc-lag-domains"
    )
    assert req1["params"] == {"offset": 0, "limit": 5}
    assert req1["json"] is None

    # 2. get_mc_lag_domain wrapped dict
    res2 = await client.lags.get_mc_lag_domain("default", "mc-1")
    assert isinstance(res2, McLagDomain)
    assert res2.id == "mc-1"
    req2 = session.requests[1]
    assert req2["method"] == "GET"
    assert (
        req2["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/switching/mc-lag-domains/mc-1"
    )
    assert req2["params"] is None
    assert req2["json"] is None

    # 3. get_mc_lag_domain wrapped list
    res3 = await client.lags.get_mc_lag_domain("default", "mc-1")
    assert res3.id == "mc-1"

    # 4. get_mc_lag_domain empty -> ValueError
    with pytest.raises(ValueError, match="MC-LAG domain mc-1 not found"):
        await client.lags.get_mc_lag_domain("default", "mc-1")

    # 5. Error mapping
    with pytest.raises(UniFiNotFoundError):
        await client.lags.get_mc_lag_domain("default", "missing-mc")

    with pytest.raises(UniFiResponseError):
        await client.lags.get_mc_lag_domain("default", "err-mc")


# =============================================================================
# 4. stacks.py
# =============================================================================


async def test_stacks_get_all_pins_spec_request_and_branches() -> None:
    """stacks.get_all pins GET /v1/sites/{siteId}/switching/switch-stacks."""
    raw_stack = {"id": "stack-1", "name": "Stack-1"}
    session = _Session(
        [
            {"data": [raw_stack]},
        ]
    )
    client = _client(session)

    res = await client.stacks.get_all("default", offset=0, limit=10)
    assert len(res) == 1
    assert isinstance(res[0], SwitchStack)
    assert res[0].id == "stack-1"
    req = session.requests[0]
    assert req["method"] == "GET"
    assert (
        req["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/switching/switch-stacks"
    )
    assert req["params"] == {"offset": 0, "limit": 10}
    assert req["json"] is None


async def test_stacks_get_pins_spec_request_and_branches() -> None:
    """stacks.get pins
    GET /v1/sites/{siteId}/switching/switch-stacks/{switchStackId}.
    """
    raw_stack = {"id": "stack-1", "name": "Stack-1"}
    session = _Session(
        [
            # 1. Wrapped dict
            {"data": raw_stack},
            # 2. Direct dict
            raw_stack,
            # 3. Wrapped list
            {"data": [raw_stack]},
            # 4. Empty data -> ValueError
            {"data": []},
            # 5. Error status mapping
            _Response("Not found", status=404),
            _Response("Server error", status=500),
        ]
    )
    client = _client(session)

    res1 = await client.stacks.get("default", "stack-1")
    assert isinstance(res1, SwitchStack)
    assert res1.id == "stack-1"
    req1 = session.requests[0]
    assert req1["method"] == "GET"
    assert (
        req1["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/switching/switch-stacks/stack-1"
    )
    assert req1["params"] is None
    assert req1["json"] is None

    res2 = await client.stacks.get("default", "stack-1")
    assert res2.id == "stack-1"

    res3 = await client.stacks.get("default", "stack-1")
    assert res3.id == "stack-1"

    with pytest.raises(ValueError, match="Switch stack stack-1 not found"):
        await client.stacks.get("default", "stack-1")

    with pytest.raises(UniFiNotFoundError):
        await client.stacks.get("default", "missing-stack")

    with pytest.raises(UniFiResponseError):
        await client.stacks.get("default", "err-stack")


# =============================================================================
# 5. reports.py
# =============================================================================


async def test_reports_get_site_report_pins_request_and_branches() -> None:
    """reports.get_site_report pins POST /stat/report/{interval}.site
    (unspecified) and covers branches.
    """
    raw_bucket = {
        "time": 1600000000000,
        "wan-rx_bytes": 1048576,
        "wan-tx_bytes": 524288,
    }
    session = _Session(
        [
            # 1. Wrapped data response with start_ms/end_ms
            {"data": [raw_bucket]},
            # 2. Bare list response with start/end alias and custom attrs
            [raw_bucket],
            # 3. Envelope error
            {"meta": {"rc": "error", "msg": "Invalid range"}},
            # 4. None response
            None,
            # 5. Non-list data in dict
            {"data": "not-a-list"},
            # 6. Data with invalid item
            {"data": [{"time": "not-numeric"}, raw_bucket]},
        ]
    )
    client = _client(session)

    # 1. Wrapped data response with start_ms/end_ms
    res1 = await client.reports.get_site_report(
        "default",
        "5minutes",
        start_ms=1600000000000,
        end_ms=1600000300000,
    )
    assert len(res1) == 1
    assert isinstance(res1[0], SiteReportBucket)
    assert res1[0].time == 1600000000000
    assert res1[0].wan_rx_bytes == 1048576.0
    req1 = session.requests[0]
    assert req1["method"] == "POST"
    assert (
        req1["url"]
        == "https://192.168.1.1/proxy/network/api/s/default/stat/report/5minutes.site"
    )
    assert req1["json"] == {
        "attrs": [
            "time",
            "wan-rx_bytes",
            "wan-tx_bytes",
            "wan2-rx_bytes",
            "wan2-tx_bytes",
        ],
        "start": 1600000000000,
        "end": 1600000300000,
    }
    assert req1["params"] is None

    # 2. Bare list response with start/end alias and custom attrs
    res2 = await client.reports.get_site_report(
        "default",
        "hourly",
        start=1600000000000,
        end=1600003600000,
        attrs=["time", "wan-rx_bytes"],
    )
    assert len(res2) == 1
    req2 = session.requests[1]
    assert req2["json"] == {
        "attrs": ["time", "wan-rx_bytes"],
        "start": 1600000000000,
        "end": 1600003600000,
    }
    assert req2["params"] is None

    # 3. Envelope error
    with pytest.raises(UniFiResponseError) as exc_info:
        await client.reports.get_site_report(
            "default", "daily", start_ms=1000, end_ms=2000
        )
    assert "Invalid range" in exc_info.value.message

    # 4. None response
    assert (
        await client.reports.get_site_report(
            "default", "daily", start_ms=1000, end_ms=2000
        )
        == []
    )

    # 5. Non-list data in dict
    assert (
        await client.reports.get_site_report(
            "default", "daily", start_ms=1000, end_ms=2000
        )
        == []
    )

    # 6. Data with invalid item skipped
    res6 = await client.reports.get_site_report(
        "default", "daily", start_ms=1000, end_ms=2000
    )
    assert len(res6) == 1
    assert res6[0].time == 1600000000000

    # Validation errors: invalid interval
    with pytest.raises(ValueError, match="Unsupported report interval"):
        await client.reports.get_site_report(
            "default", "weekly", start_ms=1000, end_ms=2000
        )

    # Validation errors: missing start/end
    with pytest.raises(ValueError, match="Both start and end timestamps"):
        await client.reports.get_site_report("default", "5minutes")


# =============================================================================
# 6. routes.py
# =============================================================================


async def test_routes_extract_routes_list_and_get_route_branches() -> None:
    """routes covers envelope errors, single dict response, and get_route failure."""
    session = _Session(
        [
            # 1. list_routes with envelope error
            {"meta": {"rc": "error", "msg": "Route service offline"}},
            # 2. list_routes with single dict data
            {
                "data": {
                    "_id": "rt-single",
                    "description": "Single Route",
                    "enabled": True,
                }
            },
            # 3. list_routes with invalid route item skipped
            {
                "data": [
                    {"_id": "invalid-rt", "enabled": "not-a-bool"},
                    {"_id": "rt-ok"},
                ]
            },
            # 4. get_route direct miss followed by list_routes fallback miss
            # -> ValueError
            {"data": []},
            {"data": [{"_id": "rt-other"}]},
        ]
    )
    client = _client(session)

    # 1. Envelope error
    with pytest.raises(UniFiResponseError) as exc_info:
        await client.routes.list_routes("default")
    assert "Route service offline" in exc_info.value.message

    # 2. Single dict data
    res2 = await client.routes.list_routes("default")
    assert len(res2) == 1
    assert isinstance(res2[0], PolicyBasedRoute)
    assert res2[0].id == "rt-single"

    # 3. Invalid item skipped
    res3 = await client.routes.list_routes("default")
    assert len(res3) == 1
    assert res3[0].id == "rt-ok"

    # 4. get_route not found raises ValueError
    with pytest.raises(ValueError, match="Policy-Based Route rt-missing not found"):
        await client.routes.get_route("default", "rt-missing")

    for request, path in zip(
        session.requests,
        [
            "/v2/api/site/default/trafficroutes",
            "/v2/api/site/default/trafficroutes",
            "/v2/api/site/default/trafficroutes",
            "/v2/api/site/default/trafficroutes/rt-missing",
            "/v2/api/site/default/trafficroutes",
        ],
        strict=True,
    ):
        _assert_request(request, "GET", path)


# =============================================================================
# 7. vouchers.py
# =============================================================================


async def test_vouchers_get_all_pins_spec_request_and_branches() -> None:
    """vouchers.get_all pins GET /v1/sites/{siteId}/hotspot/vouchers
    and covers branches.
    """
    raw_voucher = {"id": "v-1", "code": "12345-67890"}
    session = _Session(
        [
            # 1. Query params with offset, limit, filter_str
            {"data": [raw_voucher]},
            # 2. Limit capped at 1000
            {"data": [raw_voucher]},
            # 3. None response
            None,
            # 4. Non-list data
            {"data": "not-a-list"},
        ]
    )
    client = _client(session)

    res1 = await client.vouchers.get_all(
        "default", offset=10, limit=50, filter_str="expired.eq(false)"
    )
    assert len(res1) == 1
    assert isinstance(res1[0], Voucher)
    assert res1[0].id == "v-1"
    req1 = session.requests[0]
    assert req1["method"] == "GET"
    assert (
        req1["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/hotspot/vouchers"
    )
    assert req1["params"] == {
        "offset": 10,
        "limit": 50,
        "filter": "expired.eq(false)",
    }
    assert req1["json"] is None

    # 2. Limit capped at 1000
    await client.vouchers.get_all("default", limit=2000)
    assert session.requests[1]["params"] == {"offset": 0, "limit": 1000}

    # 3. None response
    assert await client.vouchers.get_all("default") == []

    # 4. Non-list data
    assert await client.vouchers.get_all("default") == []


async def test_vouchers_get_pins_spec_request_and_branches() -> None:
    """vouchers.get pins GET /v1/sites/{siteId}/hotspot/vouchers/{voucherId}
    and covers branches.
    """
    raw_voucher = {"id": "v-1", "code": "12345-67890"}
    session = _Session(
        [
            # 1. Wrapped dict
            {"data": raw_voucher},
            # 2. Direct dict
            raw_voucher,
            # 3. Wrapped list
            {"data": [raw_voucher]},
            # 4. Empty data -> ValueError
            {"data": []},
            # 5. Error status mapping
            _Response("Not found", status=404),
            _Response("Server error", status=500),
        ]
    )
    client = _client(session)

    res1 = await client.vouchers.get("default", "v-1")
    assert isinstance(res1, Voucher)
    assert res1.id == "v-1"
    req1 = session.requests[0]
    assert req1["method"] == "GET"
    assert (
        req1["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/hotspot/vouchers/v-1"
    )
    assert req1["params"] is None
    assert req1["json"] is None

    res2 = await client.vouchers.get("default", "v-1")
    assert res2.id == "v-1"

    res3 = await client.vouchers.get("default", "v-1")
    assert res3.id == "v-1"

    with pytest.raises(ValueError, match="Voucher v-1 not found"):
        await client.vouchers.get("default", "v-1")

    with pytest.raises(UniFiNotFoundError):
        await client.vouchers.get("default", "missing-v")

    with pytest.raises(UniFiResponseError):
        await client.vouchers.get("default", "err-v")


async def test_vouchers_delete_methods_pin_spec_requests_and_branches() -> None:
    """vouchers delete methods pin spec requests and cover branches."""
    session = _Session(
        [
            # 1. delete single
            {},
            # 2. delete error mapping
            _Response("Not found", status=404),
            # 3. delete_by_filter dict response
            {"vouchersDeleted": 7},
            # 4. delete_by_filter non-dict response
            [],
            # 5. delete_multiple (2 calls)
            {},
            {},
        ]
    )
    client = _client(session)

    # 1. delete
    assert await client.vouchers.delete("default", "v-1") is True
    req1 = session.requests[0]
    assert req1["method"] == "DELETE"
    assert (
        req1["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/hotspot/vouchers/v-1"
    )
    assert req1["params"] is None
    assert req1["json"] is None

    # 2. delete error mapping
    with pytest.raises(UniFiNotFoundError):
        await client.vouchers.delete("default", "missing-v")

    # 3. delete_by_filter
    del_count = await client.vouchers.delete_by_filter("default", "expired.eq(true)")
    assert del_count == 7
    req3 = session.requests[2]
    assert req3["method"] == "DELETE"
    assert (
        req3["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/hotspot/vouchers"
    )
    assert req3["params"] == {"filter": "expired.eq(true)"}
    assert req3["json"] is None

    # 4. delete_by_filter non-dict response
    assert await client.vouchers.delete_by_filter("default", "expired.eq(true)") == 0

    # 5. delete_multiple
    assert await client.vouchers.delete_multiple("default", ["v-1", "v-2"]) is True
    assert len(session.requests) == 6

    for request, voucher_id in zip(session.requests[4:], ["v-1", "v-2"], strict=True):
        _assert_request(
            request,
            "DELETE",
            f"/integration/v1/sites/default/hotspot/vouchers/{voucher_id}",
        )


async def test_vouchers_get_all_pages_walks_total_count_and_pins_spec_requests() -> (
    None
):
    """get_all_pages walks pages using totalCount and pins spec requests."""
    page1_items = [{"id": f"v-{i}", "code": f"12345{i:05d}"} for i in range(1000)]
    page2_items = [{"id": "v-1000", "code": "1234501000"}]
    session = _Session(
        [
            {"data": page1_items, "totalCount": 1001},
            {"data": page2_items, "totalCount": 1001},
        ]
    )
    client = _client(session)

    vouchers = await client.vouchers.get_all_pages("default")
    assert len(vouchers) == 1001
    assert all(isinstance(v, Voucher) for v in vouchers)
    assert len(session.requests) == 2

    assert (
        session.requests[0]["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/hotspot/vouchers"
    )
    assert session.requests[0]["params"] == {"offset": 0, "limit": 1000}
    assert (
        session.requests[1]["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/hotspot/vouchers"
    )
    assert session.requests[1]["params"] == {"offset": 1000, "limit": 1000}


async def test_vouchers_get_all_pages_no_total_count_stops_on_short_page() -> None:
    """get_all_pages stops when returned page is shorter than page size."""
    raw_voucher = {"id": "v-1", "code": "1234567890"}
    session = _Session(
        [
            {"data": [raw_voucher]},
        ]
    )
    client = _client(session)

    vouchers = await client.vouchers.get_all_pages("default")
    assert len(vouchers) == 1
    assert isinstance(vouchers[0], Voucher)
    assert len(session.requests) == 1
    assert session.requests[0]["params"] == {"offset": 0, "limit": 1000}


async def test_vouchers_get_all_pages_without_total_count_continues_on_full_page() -> (
    None
):
    """get_all_pages continues when page is full and totalCount is absent."""
    page1_items = [{"id": f"v-{i}", "code": f"12345{i:05d}"} for i in range(1000)]
    session = _Session(
        [
            {"data": page1_items},
            {"data": []},
        ]
    )
    client = _client(session)

    vouchers = await client.vouchers.get_all_pages("default")
    assert len(vouchers) == 1000
    assert len(session.requests) == 2
    assert session.requests[0]["params"] == {"offset": 0, "limit": 1000}
    assert session.requests[1]["params"] == {"offset": 1000, "limit": 1000}


async def test_vouchers_get_all_pages_empty_and_malformed_responses() -> None:
    """get_all_pages handles None, non-list, empty, and bare list responses."""
    raw_voucher = {"id": "v-1", "code": "1234567890"}

    # None
    session_none = _Session([None])
    client_none = _client(session_none)
    assert await client_none.vouchers.get_all_pages("default") == []

    # Non-list data
    session_str = _Session([{"data": "x"}])
    client_str = _client(session_str)
    assert await client_str.vouchers.get_all_pages("default") == []

    # Empty list with totalCount 0
    session_empty = _Session([{"data": [], "totalCount": 0}])
    client_empty = _client(session_empty)
    assert await client_empty.vouchers.get_all_pages("default") == []

    # Bare list
    session_bare = _Session([[raw_voucher]])
    client_bare = _client(session_bare)
    vouchers = await client_bare.vouchers.get_all_pages("default")
    assert len(vouchers) == 1
    assert isinstance(vouchers[0], Voucher)


async def test_vouchers_get_all_pages_deduplicates_by_voucher_id() -> None:
    """get_all_pages deduplicates vouchers across pages by voucher ID."""
    v1 = {"id": "v-1", "code": "1111111111", "name": "V1", "timeLimitMinutes": 60}
    v2 = {"id": "v-2", "code": "2222222222", "name": "V2", "timeLimitMinutes": 60}
    v3 = {"id": "v-3", "code": "3333333333", "name": "V3", "timeLimitMinutes": 60}
    session = _Session(
        [
            {"data": [v1, v2], "totalCount": 3},
            {"data": [v2, v3], "totalCount": 3},
        ]
    )
    client = _client(session)
    vouchers = await client.vouchers.get_all_pages("default")
    assert len(vouchers) == 3
    assert [v.id for v in vouchers] == ["v-1", "v-2", "v-3"]


async def test_vouchers_get_all_pages_no_progress_raises_incomplete_error() -> None:
    """get_all_pages raises credential-free error when a page makes no progress."""
    v1 = {"id": "v-1", "code": "1111111111", "name": "V1", "timeLimitMinutes": 60}
    session = _Session(
        [
            {"data": [v1], "totalCount": 2},
            {"data": [v1], "totalCount": 2},
        ]
    )
    client = _client(session)
    with pytest.raises(RuntimeError, match="no progress"):
        await client.vouchers.get_all_pages("default")


async def test_vouchers_get_all_pages_unsupported_html_is_debug_only_and_redirect_warns(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Expected 200 HTML logs at DEBUG only; unexpected redirect still logs WARNING."""
    path = "/proxy/network/integration/v1/sites/default/hotspot/vouchers"

    # 1. Expected unsupported response (unredirected path)
    resp_unsupported = _Response("<!doctype html><html>login</html>", status=200)
    resp_unsupported.url = URL(f"https://192.168.1.1{path}")
    session1 = _Session([resp_unsupported])
    client1 = _client(session1)

    with caplog.at_level("DEBUG"), pytest.raises(UniFiResponseError):
        await client1.vouchers.get_all_pages("default")

    assert not any(
        record.levelno >= 30 and "Response is not JSON" in record.getMessage()
        for record in caplog.records
    )
    assert any(
        "Expected unsupported-endpoint non-JSON response" in record.getMessage()
        for record in caplog.records
    )

    # 2. Redirected response logs WARNING
    caplog.clear()
    resp_redirected = _Response("<!doctype html><html>login</html>", status=200)
    resp_redirected.url = URL("https://192.168.1.1/manage/account/login")
    session2 = _Session([resp_redirected])
    client2 = _client(session2)

    with caplog.at_level("DEBUG"), pytest.raises(UniFiResponseError):
        await client2.vouchers.get_all_pages("default")

    assert any(
        record.levelno >= 30 and "Response is not JSON" in record.getMessage()
        for record in caplog.records
    )


async def test_vouchers_get_all_pages_stops_at_page_cap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """get_all_pages stops at page cap and raises incomplete listing error."""
    page1_items = [{"id": f"v-{i}", "code": f"12345{i:05d}"} for i in range(1000)]
    page2_items = [
        {"id": f"v-{1000 + i}", "code": f"12345{1000 + i:05d}"} for i in range(1000)
    ]
    monkeypatch.setattr(
        "custom_components.unifi_insights.api.network.endpoints.vouchers.VOUCHER_MAX_PAGES",
        2,
    )
    session = _Session(
        [
            {"data": page1_items, "totalCount": 99999},
            {"data": page2_items, "totalCount": 99999},
        ]
    )
    client = _client(session)

    with pytest.raises(RuntimeError, match="reached page limit"):
        await client.vouchers.get_all_pages("default")

    assert len(session.requests) == 2


async def test_vouchers_get_all_pages_propagates_http_errors() -> None:
    """get_all_pages propagates HTTP errors from _get."""
    session = _Session([_Response("Not found", status=404)])
    client = _client(session)

    with pytest.raises(UniFiNotFoundError):
        await client.vouchers.get_all_pages("default")


@pytest.mark.parametrize("retry_consistent", [True, False])
async def test_vouchers_get_all_pages_retries_incomplete_inventory_once(
    *,
    retry_consistent: bool,
) -> None:
    """Only the retry's distinct inventory can satisfy a changed totalCount."""
    stale = [{"id": f"stale-{i}", "code": "1234567890"} for i in range(3)]
    fresh = [{"id": f"fresh-{i}", "code": "1234567890"} for i in range(4)]
    incomplete = [
        {"data": stale[:2], "totalCount": 4},
        {"data": stale[1:], "totalCount": 4},
    ]
    retry = (
        [
            {"data": fresh[:2], "totalCount": 4},
            {"data": fresh[2:], "totalCount": 4},
        ]
        if retry_consistent
        else incomplete
    )
    session = _Session(incomplete + retry)
    client = _client(session)
    if retry_consistent:
        result = await client.vouchers.get_all_pages("default")
        assert [voucher.id for voucher in result] == [item["id"] for item in fresh]
    else:
        with pytest.raises(RuntimeError, match="distinct inventory"):
            await client.vouchers.get_all_pages("default")
    assert [request["params"]["offset"] for request in session.requests] == [0, 2, 0, 2]


async def test_vouchers_get_all_pages_retry_preserves_page_cap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A completeness retry still fails when its own page budget is exhausted."""
    monkeypatch.setattr(
        "custom_components.unifi_insights.api.network.endpoints.vouchers.VOUCHER_MAX_PAGES",
        2,
    )
    items = [{"id": f"v-{i}", "code": "1234567890"} for i in range(4)]
    session = _Session(
        [
            {"data": items[:2], "totalCount": 4},
            {"data": items[1:3], "totalCount": 4},
            {"data": items[:2], "totalCount": 10},
            {"data": items[2:], "totalCount": 10},
        ]
    )
    with pytest.raises(RuntimeError, match="reached page limit"):
        await _client(session).vouchers.get_all_pages("default")
    assert [request["params"]["offset"] for request in session.requests] == [0, 2, 0, 2]


@pytest.mark.parametrize(
    "operation",
    [
        "get_all_pages",
        "get_all",
        "get",
        "create",
        "delete",
        "delete_by_filter",
        "delete_multiple",
    ],
)
@pytest.mark.parametrize("non_json", [False, True])
async def test_voucher_endpoints_omit_response_bodies(
    caplog: pytest.LogCaptureFixture,
    operation: str,
    *,
    non_json: bool,
) -> None:
    """Every voucher entry point suppresses JSON and non-JSON response bodies."""
    body = (
        "<html>1234567890 Café</html>"
        if non_json
        else {"id": "v1", "code": "1234567890", "name": "Café"}
    )
    response = _Response(body)
    # A login redirect must exercise the non-JSON WARNING, even for list/get.
    response.url = URL("https://192.168.1.1/login")
    client = _client(_Session([response]))
    endpoint = getattr(client.vouchers, operation)
    args: list[Any] = ["default"]
    kwargs: dict[str, Any] = {}
    if operation in {"get", "delete"}:
        args.append("v1")
    elif operation == "delete_by_filter":
        args.append("expired.eq(true)")
    elif operation == "delete_multiple":
        args.append(["v1"])
    elif operation == "create":
        kwargs = {"name": "Home Assistant", "time_limit_minutes": 480}
    with caplog.at_level("DEBUG"):
        if non_json:
            with pytest.raises(UniFiResponseError):
                await endpoint(*args, **kwargs)
        else:
            await endpoint(*args, **kwargs)
    assert "1234567890" not in caplog.text
    assert "Caf" not in caplog.text
    assert (
        f"<body omitted, {len((await response.text()).encode())} bytes>" in caplog.text
    )
    if non_json:
        assert any(
            record.levelname == "WARNING" and "body omitted" in record.getMessage()
            for record in caplog.records
        )


async def test_non_voucher_transport_logs_redacted_body_by_default(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Other endpoints retain body logging and recursive credential redaction."""
    body = {"data": {"name": "safe-name", "token": [1234567890]}}
    client = _client(_Session([body]))
    with caplog.at_level("DEBUG"):
        assert await client._get("/sites/default") == body
    assert (
        json.dumps({"data": {"name": "safe-name", "token": "**REDACTED**"}})
        in caplog.text
    )
    assert "1234567890" not in caplog.text
    assert "body omitted" not in caplog.text


# =============================================================================
# 8. vpn_clients.py
# =============================================================================


async def test_vpn_clients_extract_networkconf_and_get_vpn_client_branches() -> None:
    """vpn_clients covers envelope error, single dict, and get_vpn_client failure."""
    session = _Session(
        [
            # 1. list_vpn_clients with envelope error
            {"meta": {"rc": "error", "msg": "Networkconf error"}},
            # 2. list_site_to_site_vpns with single dict
            {
                "data": {
                    "_id": "vpn-single",
                    "purpose": "site-vpn",
                    "name": "Branch Tunnel",
                }
            },
            # 3. get_vpn_client miss on direct GET and miss on list_vpn_clients fallback
            {"data": []},
            {"data": [{"_id": "vpn-other", "purpose": "vpn-client"}]},
        ]
    )
    client = _client(session)

    # 1. Envelope error
    with pytest.raises(UniFiResponseError) as exc_info:
        await client.vpn_clients.list_vpn_clients("default")
    assert "Networkconf error" in exc_info.value.message

    # 2. Single dict in list_site_to_site_vpns
    res2 = await client.vpn_clients.list_site_to_site_vpns("default")
    assert len(res2) == 1
    assert res2[0]["id"] == "vpn-single"

    # 3. get_vpn_client not found raises ValueError
    with pytest.raises(ValueError, match="VPN Client vpn-missing not found"):
        await client.vpn_clients.get_vpn_client("default", "vpn-missing")

    # 4. get_vpn_client fallback hit in list_vpn_clients with bare list response
    session_hit = _Session(
        [
            {"data": []},
            [{"_id": "vpn-found", "name": "Found VPN", "purpose": "vpn-client"}],
        ]
    )
    client_hit = _client(session_hit)
    res_hit = await client_hit.vpn_clients.get_vpn_client("default", "vpn-found")
    assert isinstance(res_hit, VpnClient)
    assert res_hit.id == "vpn-found"
    assert res_hit.name == "Found VPN"

    for request, path in zip(
        session.requests,
        [
            "/api/s/default/rest/networkconf",
            "/api/s/default/rest/networkconf",
            "/api/s/default/rest/networkconf/vpn-missing",
            "/api/s/default/rest/networkconf",
        ],
        strict=True,
    ):
        _assert_request(request, "GET", path)
    for request, path in zip(
        session_hit.requests,
        [
            "/api/s/default/rest/networkconf/vpn-found",
            "/api/s/default/rest/networkconf",
        ],
        strict=True,
    ):
        _assert_request(request, "GET", path)


# =============================================================================
# 9. wifi.py
# =============================================================================


async def test_wifi_extract_payload_branches() -> None:
    """wifi._extract_wifi_payload covers None and non-dict list items."""
    session = _Session(
        [
            # 1. get returning None -> ValueError
            None,
            # 2. get returning list with non-dict -> ValueError
            {"data": ["not-a-dict"]},
        ]
    )
    client = _client(session)

    with pytest.raises(ValueError, match="WiFi network wifi-1 not found"):
        await client.wifi.get("default", "wifi-1")

    with pytest.raises(ValueError, match="WiFi network wifi-2 not found"):
        await client.wifi.get("default", "wifi-2")

    for request, wifi_id in zip(session.requests, ["wifi-1", "wifi-2"], strict=True):
        _assert_request(
            request, "GET", f"/integration/v1/sites/default/wifi/broadcasts/{wifi_id}"
        )


async def test_wifi_create_response_branches() -> None:
    """Parse successful create responses and reject malformed responses."""
    raw_wifi = {
        "id": "wifi-created",
        "name": "Guest Net",
        "ssid": "Guest-SSID",
        "security": "wpa2",
        "enabled": True,
    }
    session = _Session(
        [
            # 1. Successful creation
            {"data": raw_wifi},
            # 2. Non-dict response -> ValueError
            [],
        ]
    )
    client = _client(session)

    # 1. Successful creation
    res = await client.wifi.create(
        "default",
        name="Guest Net",
        ssid="Guest-SSID",
        passphrase="guestpass",  # noqa: S106
        security=WifiSecurity.WPA2,
        network_id="net-1",
        hidden=True,
    )
    assert isinstance(res, WifiNetwork)
    assert res.id == "wifi-created"
    assert res.name == "Guest Net"
    req = session.requests[0]
    assert req["method"] == "POST"
    assert (
        req["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/wifi/broadcasts"
    )

    # 2. Non-dict response -> ValueError
    with pytest.raises(ValueError, match="Failed to create WiFi network"):
        await client.wifi.create("default", name="Fail", ssid="Fail-SSID")


async def test_wifi_update_pins_spec_request_and_branches() -> None:
    """wifi.update pins PUT /v1/sites/{siteId}/wifi/broadcasts/{wifiBroadcastId}."""
    current_wifi = {**_wifi_document("Old Name"), "id": "wifi-1", "metadata": {}}
    updated_wifi = {**_wifi_document("New Name"), "id": "wifi-1"}
    session = _Session(
        [
            # 1. Update with response payload
            {"data": current_wifi},
            {"data": updated_wifi},
            # 2. Update when current_payload is missing -> ValueError
            None,
            # 3. Update when PUT returns empty/None response -> fallback to sent payload
            {"data": current_wifi},
            None,
        ]
    )
    client = _client(session)

    # 1. Update with response payload
    res1 = await client.wifi.update("default", "wifi-1", name="New Name")
    assert isinstance(res1, WifiNetwork)
    assert res1.name == "New Name"
    req_put1 = session.requests[1]
    assert req_put1["method"] == "PUT"
    assert (
        req_put1["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/wifi/broadcasts/wifi-1"
    )
    assert req_put1["json"] == _wifi_document("New Name")

    # 2. Update when current payload is missing -> ValueError
    with pytest.raises(ValueError, match="WiFi network wifi-1 not found"):
        await client.wifi.update("default", "wifi-1", name="New Name")

    # 3. Update when PUT returns empty response
    res3 = await client.wifi.update("default", "wifi-1", name="New Name")
    assert isinstance(res3, WifiNetwork)
    assert res3.id == "wifi-1"
    assert res3.name == "New Name"

    for index in [0, 2, 3]:
        _assert_request(
            session.requests[index],
            "GET",
            "/integration/v1/sites/default/wifi/broadcasts/wifi-1",
        )
    _assert_request(
        session.requests[4],
        "PUT",
        "/integration/v1/sites/default/wifi/broadcasts/wifi-1",
        body=_wifi_document("New Name"),
    )


async def test_wifi_delete_pins_spec_request_and_error_mapping() -> None:
    """wifi.delete pins DELETE /v1/sites/{siteId}/wifi/broadcasts/{wifiBroadcastId}."""
    session = _Session(
        [
            {},
            _Response("Not found", status=404),
            _Response("Server error", status=500),
        ]
    )
    client = _client(session)

    assert await client.wifi.delete("default", "wifi-1") is True
    req = session.requests[0]
    assert req["method"] == "DELETE"
    assert (
        req["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/wifi/broadcasts/wifi-1"
    )
    assert req["params"] is None
    assert req["json"] is None

    with pytest.raises(UniFiNotFoundError):
        await client.wifi.delete("default", "missing-wifi")

    with pytest.raises(UniFiResponseError):
        await client.wifi.delete("default", "err-wifi")


# =============================================================================
# 10. Models
# =============================================================================


def test_device_model_outlet_table_alternate_keys() -> None:
    """Device model covers alternate outlet table key names and branches."""
    legacy_dev = {
        "outlet_table": [
            # non-dict entry (skipped)
            "string-entry",
            # non-numeric index (skipped)
            {"index": "not-an-int"},
            # relayState, cycleEnabled, outletCaps
            {
                "outlet_idx": "1",
                "relayState": True,
                "cycleEnabled": True,
                "outletCaps": 3,
            },
            # state, caps
            {
                "outletIdx": "2",
                "state": True,
                "caps": 1,
            },
            # missing relay_state -> False
            {
                "index": 3,
            },
        ],
    }
    metrics = parse_outlet_metrics(legacy_dev)
    assert len(metrics.outlets) == 3
    assert metrics.outlets[0].index == 1
    assert metrics.outlets[0].relay_state is True
    assert metrics.outlets[0].cycle_enabled is True
    assert metrics.outlets[0].outlet_caps == 3

    assert metrics.outlets[1].index == 2
    assert metrics.outlets[1].relay_state is True
    assert metrics.outlets[1].outlet_caps == 1

    assert metrics.outlets[2].index == 3
    assert metrics.outlets[2].relay_state is False


def test_report_model_validators_and_properties() -> None:
    """SiteReportBucket model covers byte coercion, time validator, and properties."""
    # Exercise byte coercion through the public model validators.
    for value, expected in [
        (None, None),
        (True, None),
        (False, None),
        ("100", None),
        (-5, None),
        (float("nan"), None),
        (float("inf"), None),
        (100, 100.0),
        (250.5, 250.5),
    ]:
        bucket = SiteReportBucket.model_validate({"time": 1000, "wan-rx_bytes": value})
        assert bucket.wan_rx_bytes == expected

    # time validator branches
    with pytest.raises(
        ValidationError, match="time must be a numeric millisecond timestamp"
    ):
        SiteReportBucket.model_validate({"time": True})

    with pytest.raises(
        ValidationError, match="time must be a numeric millisecond timestamp"
    ):
        SiteReportBucket.model_validate({"time": "not-a-number"})

    with pytest.raises(ValidationError, match="time must be finite"):
        SiteReportBucket.model_validate({"time": float("inf")})

    # properties when byte fields are absent
    b_empty = SiteReportBucket.model_validate({"time": 1000})
    assert b_empty.rx_bytes is None
    assert b_empty.tx_bytes is None
    assert b_empty.total_rx_bytes is None
    assert b_empty.total_tx_bytes is None

    # properties when byte fields are present
    b_full = SiteReportBucket.model_validate(
        {
            "time": 1000.0,
            "wan-rx_bytes": 1000,
            "wan2-rx_bytes": 2000,
            "wan-tx_bytes": 300,
            "wan2-tx_bytes": 700,
        }
    )
    assert b_full.time == 1000
    assert b_full.rx_bytes == 3000
    assert b_full.tx_bytes == 1000
    assert b_full.total_rx_bytes == 3000
    assert b_full.total_tx_bytes == 1000


def test_site_model_fallbacks_and_properties() -> None:
    """Site model covers populate_fallbacks branches and display_name."""
    # 1. Both id and name provided
    s1 = Site.model_validate({"id": "s-1", "name": "Site 1"})
    assert s1.id == "s-1"
    assert s1.name == "Site 1"
    assert s1.display_name == "Site 1"

    # 2. id provided, name missing -> name falls back to id
    s2 = Site.model_validate({"id": "s-2"})
    assert s2.id == "s-2"
    assert s2.name == "s-2"
    assert s2.display_name == "s-2"

    # 3. name provided, id missing -> id falls back to name
    s3 = Site.model_validate({"name": "Site 3"})
    assert s3.id == "Site 3"
    assert s3.name == "Site 3"

    # 4. internalReference provided, id and name missing -> both fall back
    # to internalReference
    s4 = Site.model_validate({"internalReference": "site-ref"})
    assert s4.id == "site-ref"
    assert s4.name == "site-ref"
    assert s4.display_name == "site-ref"

    # 5. Empty dictionary -> falls back to default / Default
    s5 = Site.model_validate({})
    assert s5.id == "default"
    assert s5.name == "default"


def test_voucher_model_is_active_and_create_request() -> None:
    """Voucher and VoucherCreateRequest models cover is_active and validations."""
    # 1. expired is True -> is_active is False
    v1 = Voucher.model_validate({"id": "v-1", "code": "1111", "expired": True})
    assert v1.is_active is False

    # 2. guest limit reached -> is_active is False
    v2 = Voucher.model_validate(
        {
            "id": "v-2",
            "code": "2222",
            "expired": False,
            "authorizedGuestLimit": 2,
            "authorizedGuestCount": 2,
        }
    )
    assert v2.is_active is False

    # 3. guest limit not reached -> is_active is True
    v3 = Voucher.model_validate(
        {
            "id": "v-3",
            "code": "3333",
            "expired": False,
            "authorizedGuestLimit": 2,
            "authorizedGuestCount": 1,
        }
    )
    assert v3.is_active is True

    # 4. guest limit is None -> is_active is True
    v4 = Voucher.model_validate({"id": "v-4", "code": "4444", "expired": False})
    assert v4.is_active is True

    # VoucherCreateRequest valid
    req = VoucherCreateRequest.model_validate(
        {
            "name": "VPass",
            "count": 5,
            "authorizedGuestLimit": 1,
            "timeLimitMinutes": 60,
            "dataUsageLimitMBytes": 500,
            "rxRateLimitKbps": 10000,
            "txRateLimitKbps": 5000,
        }
    )
    assert req.count == 5
    assert req.time_limit_minutes == 60

    # VoucherCreateRequest invalid count
    with pytest.raises(ValidationError):
        VoucherCreateRequest.model_validate({"count": 0})


async def test_clients_guest_authorization_and_stamgr_actions() -> None:
    """clients covers guest authorization, classic actions, and envelope parsing."""
    session = _Session(
        [
            # authorize_guest
            {},
            # unauthorize_guest
            {},
            # unblock
            {"meta": {"rc": "ok"}},
            # reconnect
            {},
            # forget
            {},
            # execute_action unblock
            {},
            # execute_action reconnect
            {},
            # execute_action forget
            {},
        ]
    )
    client = _client(session)

    # 1. authorize_guest pins POST /v1/sites/{siteId}/clients/{clientId}/actions
    assert await client.clients.authorize_guest("default", "client-1") is True
    req1 = session.requests[0]
    assert req1["method"] == "POST"
    assert (
        req1["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/clients/client-1/actions"
    )
    assert req1["json"] == {"action": "AUTHORIZE_GUEST_ACCESS"}
    assert req1["params"] is None

    # 2. unauthorize_guest pins POST /v1/sites/{siteId}/clients/{clientId}/actions
    assert await client.clients.unauthorize_guest("default", "client-1") is True
    req2 = session.requests[1]
    assert req2["method"] == "POST"
    assert (
        req2["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/clients/client-1/actions"
    )
    assert req2["json"] == {"action": "UNAUTHORIZE_GUEST_ACCESS"}
    assert req2["params"] is None

    # 3. unblock
    assert await client.clients.unblock("default", "00:11:22:33:44:55") is True

    # 4. reconnect
    assert await client.clients.reconnect("default", "00:11:22:33:44:55") is True

    # 5. forget
    assert await client.clients.forget("default", "00:11:22:33:44:55") is True

    # 6. execute_action valid actions
    assert (
        await client.clients.execute_action("default", "00:11:22:33:44:55", "unblock")
        is True
    )
    assert (
        await client.clients.execute_action("default", "00:11:22:33:44:55", "reconnect")
        is True
    )
    assert (
        await client.clients.execute_action("default", "00:11:22:33:44:55", "forget")
        is True
    )

    # execute_action invalid action raises ValueError
    with pytest.raises(ValueError, match="Action must be one of"):
        await client.clients.execute_action(
            "default", "00:11:22:33:44:55", "invalid-action"
        )

    for request, command in zip(
        session.requests[2:],
        [
            "unblock-sta",
            "kick-sta",
            "forget-sta",
            "unblock-sta",
            "kick-sta",
            "forget-sta",
        ],
        strict=True,
    ):
        _assert_request(
            request,
            "POST",
            "/api/s/default/cmd/stamgr",
            body={"cmd": command, "mac": "00:11:22:33:44:55"},
        )


async def test_lags_get_all_pagination_branches_and_parse_items() -> None:
    """lags covers offset-only, limit-only, filter pagination, and non-integer count."""
    raw_lag = {"id": "lag-1", "name": "LAG-1"}
    session = _Session(
        [
            # 1. offset only
            {"data": [raw_lag]},
            # 2. limit only
            {"data": [raw_lag]},
            # 3. filter_str in auto-pagination
            {"data": [raw_lag], "count": 1, "totalCount": 1},
            # 4. count is non-integer
            {"data": [raw_lag], "count": "not-an-int", "totalCount": 10},
            # 5. _parse_items with None response
            None,
            # 6. _parse_items with non-list data
            {"data": 123},
        ]
    )
    client = _client(session)

    # 1. offset only
    res_o = await client.lags.get_all("default", offset=5)
    assert len(res_o) == 1
    assert session.requests[0]["params"] == {"offset": 5}

    # 2. limit only
    res_l = await client.lags.get_all("default", limit=10)
    assert len(res_l) == 1
    assert session.requests[1]["params"] == {"limit": 10}

    # 3. filter_str in auto-pagination
    res_f = await client.lags.get_all("default", filter_str="name.eq(LAG-1)")
    assert len(res_f) == 1
    assert session.requests[2]["params"] == {
        "offset": 0,
        "limit": 100,
        "filter": "name.eq(LAG-1)",
    }

    # 4. count is non-integer -> stops pagination
    res_bad_count = await client.lags.get_all("default")
    assert len(res_bad_count) == 1

    # 5. None response
    assert await client.lags.get_all("default", offset=0, limit=5) == []

    # 6. Non-list data
    assert await client.lags.get_all("default", offset=0, limit=5) == []


async def test_vpn_clients_list_vpn_connections_and_extract_items() -> None:
    """vpn_clients covers list_vpn_connections and error/dict branches."""
    session = _Session(
        [
            # 1. list_vpn_connections success
            {
                "connections": [
                    {"network_id": "net-1", "type": "openvpn", "status": "connected"},
                    "non-dict",
                    {"network_id": 123},  # non-string network_id skipped
                ]
            },
            # 2. list_vpn_connections non-list connections
            {"connections": "not-a-list"},
            # 3. list_vpn_connections None response
            None,
            # 4. _extract_networkconf_list with error meta but missing msg
            {"meta": {"rc": "error"}},
            # 5. _extract_networkconf_list with non-list/non-dict data
            {"data": 123},
            # 6. _extract_networkconf_list with None response
            None,
        ]
    )
    client = _client(session)

    # 1. list_vpn_connections success
    conns = await client.vpn_clients.list_vpn_connections("default")
    assert len(conns) == 1
    assert conns[0] == {"network_id": "net-1", "type": "openvpn", "status": "connected"}
    req1 = session.requests[0]
    assert req1["method"] == "GET"
    assert (
        req1["url"]
        == "https://192.168.1.1/proxy/network/v2/api/site/default/vpn/connections"
    )
    assert req1["params"] is None
    assert req1["json"] is None

    # 2. non-list connections raises UniFiResponseError
    with pytest.raises(UniFiResponseError):
        await client.vpn_clients.list_vpn_connections("default")

    # 3. None response raises UniFiResponseError
    with pytest.raises(UniFiResponseError):
        await client.vpn_clients.list_vpn_connections("default")

    # 4. error meta with default msg
    with pytest.raises(UniFiResponseError) as exc_info:
        await client.vpn_clients.list_vpn_clients("default")
    assert "UniFi Network API error" in exc_info.value.message

    # 5. non-list/non-dict data -> []
    assert await client.vpn_clients.list_vpn_clients("default") == []

    # 6. None response -> []
    assert await client.vpn_clients.list_vpn_clients("default") == []


async def test_wifi_payload_extraction_and_create_defaults() -> None:
    """wifi covers list-of-dict get payload and create with default None args."""
    raw_wifi = {
        "id": "w-open",
        "name": "Open Net",
        "ssid": "Open-SSID",
        "security": "open",
        "enabled": True,
    }
    session = _Session(
        [
            # 1. get where data is a list of dicts
            {"data": [raw_wifi]},
            # 2. create with open security (passphrase and network_id are None)
            {"data": raw_wifi},
        ]
    )
    client = _client(session)

    res1 = await client.wifi.get("default", "w-open")
    assert res1.id == "w-open"

    res2 = await client.wifi.create(
        "default",
        name="Open Net",
        ssid="Open-SSID",
        security=WifiSecurity.OPEN,
    )
    assert res2.id == "w-open"
    req2 = session.requests[1]
    assert req2["method"] == "POST"
    assert req2["url"] == (
        "https://192.168.1.1/proxy/network/integration/v1/sites/default/wifi/broadcasts"
    )
    assert req2["params"] is None

    _assert_request(
        session.requests[0],
        "GET",
        "/integration/v1/sites/default/wifi/broadcasts/w-open",
    )


@pytest.mark.parametrize("security", [WifiSecurity.OPEN, WifiSecurity.WPA2])
@pytest.mark.xfail(
    strict=True,
    reason=(
        "wifi.create sends flat ssid/security/hidden/passphrase/networkId; "
        "POST /v1/sites/{siteId}/wifi/broadcasts expects type/hideName, "
        "nested securityConfiguration/network and required broadcast flags"
    ),
)
async def test_wifi_create_body_matches_spec(security: WifiSecurity) -> None:
    """Creation must send a valid STANDARD broadcast document, without flat fields."""
    expected = _wifi_document("Guest Net")
    expected["hideName"] = True
    network_id = "12345678-1234-4234-8234-123456789abc"
    expected["network"] = {"type": "SPECIFIC", "networkId": network_id}
    passphrase = None
    if security == WifiSecurity.WPA2:
        passphrase = "guestpass"  # noqa: S105
        expected["securityConfiguration"] = {
            "type": "WPA2_PERSONAL",
            "passphrase": passphrase,
        }
    session = _Session([{**expected, "id": "wifi-created"}])
    result = await _client(session).wifi.create(
        "default",
        name="Guest Net",
        ssid="Guest Net",
        security=security,
        hidden=True,
        passphrase=passphrase,
        network_id=network_id,
    )
    assert result.id == "wifi-created"
    _assert_request(
        session.requests[0],
        "POST",
        "/integration/v1/sites/default/wifi/broadcasts",
        body=expected,
    )


@pytest.mark.parametrize("payload", [{"data": 123}, [], 123])
async def test_routes_list_malformed_payloads(payload: Any) -> None:
    """Reject scalar envelopes and bare non-dictionaries through list_routes."""
    session = _Session([payload])
    assert await _client(session).routes.list_routes("default") == []
    _assert_request(session.requests[0], "GET", "/v2/api/site/default/trafficroutes")


@pytest.mark.parametrize(
    "value", [9876543210, True, None, [9876543210], {"raw": 9876543210}]
)
def test_response_redaction_handles_all_credential_value_types(value: object) -> None:
    """All existing case-insensitive credential keys redact recursively."""
    keys = (
        "password",
        "psk",
        "passphrase",
        "token",
        "apiKey",
        "api_key",
        "secret",
        "credential",
        "x-api-key",
        "authorization",
        "code",
        "voucher",
        "fingerprint",
    )
    payload = {"safe": 123, "nested": [{key.upper(): value for key in keys}]}
    redacted = json.loads(_redact(json.dumps(payload)))
    assert redacted == {
        "safe": 123,
        "nested": [{key.upper(): "**REDACTED**" for key in keys}],
    }


def test_response_redaction_preserves_non_json_fallback_and_log_bound() -> None:
    """Non-JSON regex fallback and post-redaction truncation retain behavior."""
    client = _client(_Session([]))
    text = 'prefix {"code": "synthetic-code", "safe": "ok"} suffix'
    assert _redact(text) == 'prefix {"code": "**REDACTED**", "safe": "ok"} suffix'
    assert client._response_log_text("", limit=10) == "empty"
    payload = json.dumps({"code": 9876543210, "safe": "x" * 600})
    excerpt = client._response_log_text(payload, limit=500)
    assert len(excerpt) == 500
    assert "9876543210" not in excerpt
    assert "**REDACTED**" in excerpt
