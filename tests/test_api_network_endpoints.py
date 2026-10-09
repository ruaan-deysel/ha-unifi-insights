# Copyright 2026 UniFi Insights contributors
"""Tests for UniFi Network endpoint methods pinning requests against the spec."""

from __future__ import annotations

import json
from typing import Any, Self

import pytest
from yarl import URL

from custom_components.unifi_insights.api import ApiKeyAuth, ConnectionType
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
from custom_components.unifi_insights.api.network.models.device import Device
from custom_components.unifi_insights.api.network.models.firewall import FirewallRule
from custom_components.unifi_insights.api.network.models.site import Site
from custom_components.unifi_insights.api.network.models.voucher import Voucher
from custom_components.unifi_insights.api.network.models.wifi import WifiNetwork


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


# -----------------------------------------------------------------------------
# Scope 1: Never run by any test (highest priority)
# -----------------------------------------------------------------------------


async def test_devices_get_statistics_pins_spec_request_and_response() -> None:
    """devices.get_statistics pins device statistics endpoint."""
    session = _Session(
        [
            {"cpuUtilizationPct": 32.5, "loadAverage1Min": 1.25},
            {"data": {"cpuUtilizationPct": 45.0, "memoryUtilizationPct": 60.0}},
            [],
        ]
    )
    client = _client(session)

    # 1. Direct dict response
    res1 = await client.devices.get_statistics("default", "dev-1")
    assert res1 == {"cpuUtilizationPct": 32.5, "loadAverage1Min": 1.25}
    req1 = session.requests[0]
    assert req1["method"] == "GET"
    assert (
        req1["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/devices/dev-1/statistics/latest"
    )
    assert req1["params"] is None
    assert req1["json"] is None

    # 2. Wrapped data response
    res2 = await client.devices.get_statistics("default", "dev-2")
    assert res2 == {"cpuUtilizationPct": 45.0, "memoryUtilizationPct": 60.0}

    # 3. Non-dict fallback
    res3 = await client.devices.get_statistics("default", "dev-3")
    assert res3 == {}


async def test_devices_get_statistics_error_mapping() -> None:
    """devices.get_statistics maps HTTP errors to UniFi exceptions."""
    session = _Session(
        [
            _Response("Not found", status=404),
            _Response("Server error", status=500),
        ]
    )
    client = _client(session)

    with pytest.raises(UniFiNotFoundError):
        await client.devices.get_statistics("default", "missing-dev")

    with pytest.raises(UniFiResponseError):
        await client.devices.get_statistics("default", "err-dev")


async def test_firewall_list_rules_pins_spec_request_and_models() -> None:
    """firewall.list_rules pins firewall policies endpoint."""
    raw_rule = {
        "id": "rule-1",
        "name": "Block Inbound",
        "action": "drop",
        "enabled": True,
        "ipProtocolScope": "all",
        "source": {"zoneId": "zone-wan"},
        "destination": {"zoneId": "zone-lan"},
    }
    session = _Session(
        [
            # Manual pagination request
            {"data": [raw_rule], "totalCount": 1, "count": 1},
        ]
    )
    client = _client(session)

    rules = await client.firewall.list_rules(
        "default", offset=10, limit=5, filter_str="action.eq('drop')"
    )
    assert len(rules) == 1
    assert isinstance(rules[0], FirewallRule)
    assert rules[0].id == "rule-1"
    assert rules[0].name == "Block Inbound"
    assert rules[0].action == "drop"
    assert rules[0].enabled is True

    req = session.requests[0]
    assert req["method"] == "GET"
    assert (
        req["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/firewall/policies"
    )
    assert req["params"] == {"offset": 10, "limit": 5, "filter": "action.eq('drop')"}
    assert req["json"] is None


async def test_firewall_list_rules_auto_pagination() -> None:
    """firewall.list_rules auto-paginates when offset/limit are not specified."""
    rule1 = {"id": "r1", "name": "Rule 1", "action": "accept", "enabled": True}
    rule2 = {"id": "r2", "name": "Rule 2", "action": "drop", "enabled": False}
    session = _Session(
        [
            {"data": [rule1], "totalCount": 201, "count": 200},
            {"data": [rule2], "totalCount": 201, "count": 1},
        ]
    )
    client = _client(session)

    rules = await client.firewall.list_rules("default")
    assert len(rules) == 2
    assert rules[0].id == "r1"
    assert rules[1].id == "r2"

    assert len(session.requests) == 2
    assert session.requests[0]["params"] == {"offset": 0, "limit": 200}
    assert session.requests[1]["params"] == {"offset": 200, "limit": 200}


async def test_firewall_list_rules_error_mapping() -> None:
    """firewall.list_rules maps HTTP 500 to UniFiResponseError."""
    session = _Session([_Response("Server error", status=500)])
    client = _client(session)

    with pytest.raises(UniFiResponseError):
        await client.firewall.list_rules("default")


async def test_firewall_update_rule_pins_spec_request_body_and_strips_read_only() -> (
    None
):
    """firewall.update_rule GETs current policy, strips id/index/metadata, and PUTs."""
    current_rule = {
        "id": "rule-42",
        "index": 10,
        "metadata": {"origin": "USER"},
        "name": "Allow Admin",
        "action": "accept",
        "enabled": True,
        "loggingEnabled": False,
    }
    updated_rule = {
        "id": "rule-42",
        "index": 10,
        "name": "Allow Admin",
        "action": "accept",
        "enabled": False,
        "loggingEnabled": True,
    }
    session = _Session(
        [
            current_rule,
            updated_rule,
        ]
    )
    client = _client(session)

    result = await client.firewall.update_rule(
        "default", "rule-42", enabled=False, loggingEnabled=True
    )
    assert isinstance(result, FirewallRule)
    assert result.id == "rule-42"
    assert result.enabled is False

    # Request 0: GET current policy
    req_get = session.requests[0]
    assert req_get["method"] == "GET"
    assert (
        req_get["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/firewall/policies/rule-42"
    )

    # Request 1: PUT updated policy document (id, index, metadata stripped per spec)
    req_put = session.requests[1]
    assert req_put["method"] == "PUT"
    assert (
        req_put["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/firewall/policies/rule-42"
    )
    expected_put_body = {
        "name": "Allow Admin",
        "action": "accept",
        "enabled": False,
        "loggingEnabled": True,
    }
    assert req_put["json"] == expected_put_body


async def test_firewall_update_rule_not_found_and_error_mapping() -> None:
    """firewall.update_rule raises ValueError when rule not found, maps HTTP errors."""
    session_not_found = _Session([None])
    client_nf = _client(session_not_found)
    with pytest.raises(ValueError, match="Firewall rule missing-42 not found"):
        await client_nf.firewall.update_rule("default", "missing-42", enabled=True)

    session_err = _Session(
        [
            {"id": "rule-1", "name": "Test", "action": "accept", "enabled": True},
            _Response("Internal Error", status=500),
        ]
    )
    client_err = _client(session_err)
    with pytest.raises(UniFiResponseError):
        await client_err.firewall.update_rule("default", "rule-1", enabled=False)


async def test_vouchers_delete_pins_spec_request() -> None:
    """vouchers.delete pins DELETE /sites/{siteId}/hotspot/vouchers/{voucherId}."""
    session = _Session([{"vouchersDeleted": 1}])
    client = _client(session)

    success = await client.vouchers.delete("default", "vouch-99")
    assert success is True

    req = session.requests[0]
    assert req["method"] == "DELETE"
    assert (
        req["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/hotspot/vouchers/vouch-99"
    )
    assert req["params"] is None
    assert req["json"] is None


async def test_vouchers_delete_error_mapping() -> None:
    """vouchers.delete maps HTTP errors to UniFi exceptions."""
    session = _Session(
        [
            _Response("Not found", status=404),
            _Response("Server error", status=500),
        ]
    )
    client = _client(session)

    with pytest.raises(UniFiNotFoundError):
        await client.vouchers.delete("default", "missing-vouch")

    with pytest.raises(UniFiResponseError):
        await client.vouchers.delete("default", "err-vouch")


async def test_wifi_get_all_pins_spec_request_and_models() -> None:
    """wifi.get_all pins GET /sites/{siteId}/wifi/broadcasts with pagination/filter."""
    raw_wifi = {
        "id": "wifi-1",
        "name": "IoT Network",
        "type": "STANDARD",
        "enabled": True,
    }
    session = _Session(
        [
            {"data": [raw_wifi]},
            None,
        ]
    )
    client = _client(session)

    # 1. Valid list response with query parameters
    networks = await client.wifi.get_all(
        "default", offset=2, limit=10, filter_str="enabled.eq(true)"
    )
    assert len(networks) == 1
    assert isinstance(networks[0], WifiNetwork)
    assert networks[0].id == "wifi-1"
    assert networks[0].name == "IoT Network"
    assert networks[0].enabled is True

    req = session.requests[0]
    assert req["method"] == "GET"
    assert (
        req["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/wifi/broadcasts"
    )
    assert req["params"] == {"offset": 2, "limit": 10, "filter": "enabled.eq(true)"}
    assert req["json"] is None

    # 2. None response returns empty list
    empty = await client.wifi.get_all("default")
    assert empty == []


async def test_wifi_get_all_error_mapping() -> None:
    """wifi.get_all maps HTTP 500 to UniFiResponseError."""
    session = _Session([_Response("Server error", status=500)])
    client = _client(session)

    with pytest.raises(UniFiResponseError):
        await client.wifi.get_all("default")


# -----------------------------------------------------------------------------
# Scope 2: Partly covered methods the integration calls
# -----------------------------------------------------------------------------


async def test_clients_get_all_pins_request_and_models() -> None:
    """clients.get_all pins GET /sites/{siteId}/clients manual and auto pagination."""
    c1 = {"id": "c1", "macAddress": "00:11:22:33:44:01"}
    c2 = {"id": "c2", "macAddress": "00:11:22:33:44:02"}
    session = _Session(
        [
            # Manual pagination call
            {"data": [c1]},
            # Auto pagination call (2 pages)
            {"data": [c1], "totalCount": 101, "count": 100},
            {"data": [c2], "totalCount": 101, "count": 1},
        ]
    )
    client = _client(session)

    # Manual pagination
    res_manual = await client.clients.get_all(
        "default", offset=10, limit=20, filter_str="connected.eq(true)"
    )
    assert len(res_manual) == 1
    assert isinstance(res_manual[0], Client)
    assert res_manual[0].id == "c1"
    req_m = session.requests[0]
    assert req_m["method"] == "GET"
    assert (
        req_m["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/clients"
    )
    assert req_m["params"] == {
        "offset": 10,
        "limit": 20,
        "filter": "connected.eq(true)",
    }

    # Auto pagination
    res_auto = await client.clients.get_all("default")
    assert len(res_auto) == 2
    assert res_auto[0].id == "c1"
    assert res_auto[1].id == "c2"


async def test_clients_get_active_legacy_pins_request() -> None:
    """clients.get_active_legacy pins GET /proxy/network/api/s/{site}/stat/sta."""
    session = _Session(
        [
            {"data": [{"mac": "00:11:22:33:44:55", "essid": "Home"}]},
            None,
        ]
    )
    client = _client(session)

    res = await client.clients.get_active_legacy("default")
    assert res == [{"mac": "00:11:22:33:44:55", "essid": "Home"}]
    req = session.requests[0]
    assert req["method"] == "GET"
    assert req["url"] == "https://192.168.1.1/proxy/network/api/s/default/stat/sta"

    empty = await client.clients.get_active_legacy("default")
    assert empty == []


async def test_devices_get_all_pins_request_and_models() -> None:
    """devices.get_all pins GET /sites/{siteId}/devices."""
    raw_dev = {"id": "dev-1", "macAddress": "00:11:22:33:44:01", "name": "Switch 1"}
    session = _Session(
        [
            {"data": [raw_dev, "not-a-dict", {"invalid": "payload"}]},
            None,
        ]
    )
    client = _client(session)

    res = await client.devices.get_all("default", offset=0, limit=10)
    assert len(res) == 1
    assert isinstance(res[0], Device)
    assert res[0].id == "dev-1"
    assert res[0].name == "Switch 1"

    req = session.requests[0]
    assert req["method"] == "GET"
    assert (
        req["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/devices"
    )
    assert req["params"] == {"offset": 0, "limit": 10}

    assert await client.devices.get_all("default") == []


async def test_devices_get_legacy_site_devices_pins_request() -> None:
    """devices.get_legacy_site_devices pins legacy stat/device."""
    session = _Session(
        [
            {"data": [{"mac": "aa:bb:cc:dd:ee:ff"}]},
            {"mac": "11:22:33:44:55:66"},
            [],
        ]
    )
    client = _client(session)

    res1 = await client.devices.get_legacy_site_devices("default")
    assert res1 == [{"mac": "aa:bb:cc:dd:ee:ff"}]
    req1 = session.requests[0]
    assert req1["method"] == "GET"
    assert req1["url"] == "https://192.168.1.1/proxy/network/api/s/default/stat/device"

    res2 = await client.devices.get_legacy_site_devices("default")
    assert res2 == [{"mac": "11:22:33:44:55:66"}]

    res3 = await client.devices.get_legacy_site_devices("default")
    assert res3 == []


async def test_devices_get_port_metrics_comprehensive() -> None:
    """devices.get_port_metrics normalizes PoE, port bytes, and system stats."""
    legacy_payload = {
        "port_table": [
            {
                "port_idx": 1,
                "port_poe": True,
                "poe_power": "14.5",
                "rx_bytes": 1000,
                "tx_bytes": 2000,
            },
            {
                "port_idx": 2,
                "port_poe": False,
                "poe_power": "0.0",
                "rx_bytes": 500,
                "tx_bytes": 600,
            },
        ],
        "total_used_power": "14.5",
        "system-stats": {"cpu": "22.5", "mem": "48.0", "uptime": "86400"},
    }
    session = _Session(
        [
            {"data": [legacy_payload]},
            {"data": []},
        ]
    )
    client = _client(session)

    metrics = await client.devices.get_port_metrics("default", "aa:bb:cc:dd:ee:ff")
    assert metrics.poe_total_w == 14.5
    assert metrics.poe_ports == {1: 14.5}
    assert metrics.port_bytes[1].rx_bytes == 1000
    assert metrics.port_bytes[1].tx_bytes == 2000
    assert metrics.port_bytes[2].rx_bytes == 500
    assert metrics.cpu_utilization_pct == 22.5
    assert metrics.memory_utilization_pct == 48.0
    assert metrics.uptime_sec == 86400

    empty_metrics = await client.devices.get_port_metrics("default", "missing:mac")
    assert empty_metrics.poe_total_w is None
    assert empty_metrics.poe_ports == {}


async def test_devices_set_outlet_state_existing_overrides_and_seeded() -> None:
    """devices.set_outlet_state updates overrides or seeds table."""
    session = _Session([{}, {}])
    client = _client(session)

    # 1. Device with existing outlet_overrides
    current_device_1 = {
        "_id": "dev-obj-1",
        "outlet_overrides": [
            {"index": 1, "relay_state": True},
            {"index": 2, "relay_state": True},
        ],
    }
    ok1 = await client.devices.set_outlet_state(
        "default",
        "dev-mac-1",
        outlet_index=1,
        state=False,
        cycle_enabled=True,
        current_device=current_device_1,
    )
    assert ok1 is True
    req1 = session.requests[0]
    assert req1["method"] == "PUT"
    assert (
        req1["url"]
        == "https://192.168.1.1/proxy/network/api/s/default/rest/device/dev-obj-1"
    )
    assert req1["json"] == {
        "outlet_overrides": [
            {"index": 1, "relay_state": False, "cycle_enabled": True},
            {"index": 2, "relay_state": True},
        ]
    }

    # 2. Device with outlet_table seeding (appending new outlet override)
    current_device_2 = {
        "_id": "dev-obj-2",
        "outlet_table": [
            {"index": 1, "relay_state": True},
        ],
    }
    ok2 = await client.devices.set_outlet_state(
        "default",
        "dev-mac-2",
        outlet_index=3,
        state=False,
        current_device=current_device_2,
    )
    assert ok2 is True
    req2 = session.requests[1]
    assert req2["json"] == {
        "outlet_overrides": [
            {"index": 1, "relay_state": True},
            {"index": 3, "relay_state": False},
        ]
    }


async def test_devices_set_outlet_state_refuses_without_seed() -> None:
    """devices.set_outlet_state raises UniFiValidationError when unseedable."""
    session = _Session([])
    client = _client(session)

    with pytest.raises(UniFiValidationError, match="Refusing to write outlet"):
        await client.devices.set_outlet_state(
            "default",
            "dev-mac-1",
            outlet_index=1,
            state=True,
            current_device={},
        )


async def test_routes_list_routes_pins_request_and_models() -> None:
    """routes.list_routes pins GET /proxy/network/v2/api/site/{site}/trafficroutes."""
    raw_route = {"_id": "rt-1", "description": "WAN Route", "enabled": True}
    session = _Session([{"data": [raw_route, {"_id": "bad", "enabled": "not-a-bool"}]}])
    client = _client(session)

    routes = await client.routes.list_routes("default")
    assert len(routes) == 1
    assert isinstance(routes[0], PolicyBasedRoute)
    assert routes[0].id == "rt-1"
    assert routes[0].description == "WAN Route"

    req = session.requests[0]
    assert req["method"] == "GET"
    assert (
        req["url"]
        == "https://192.168.1.1/proxy/network/v2/api/site/default/trafficroutes"
    )


async def test_routes_update_route_pins_request_and_models() -> None:
    """routes.update_route GETs routes, modifies target, and PUTs back."""
    route_curr = {"_id": "rt-1", "description": "Route 1", "enabled": True}
    route_updated = {"_id": "rt-1", "description": "Route 1", "enabled": False}
    session = _Session(
        [
            {"data": [route_curr]},
            {"data": [route_updated]},
        ]
    )
    client = _client(session)

    updated = await client.routes.update_route("default", "rt-1", enabled=False)
    assert isinstance(updated, PolicyBasedRoute)
    assert updated.id == "rt-1"
    assert updated.enabled is False

    req_put = session.requests[1]
    assert req_put["method"] == "PUT"
    assert (
        req_put["url"]
        == "https://192.168.1.1/proxy/network/v2/api/site/default/trafficroutes/rt-1"
    )
    assert req_put["json"] == {
        "_id": "rt-1",
        "description": "Route 1",
        "enabled": False,
    }


async def test_routes_update_route_not_found_raises() -> None:
    """routes.update_route raises ValueError when target route is missing."""
    session = _Session([{"data": []}])
    client = _client(session)

    with pytest.raises(ValueError, match="Policy-Based Route missing-rt not found"):
        await client.routes.update_route("default", "missing-rt", enabled=True)


async def test_sites_get_all_pins_request_and_models() -> None:
    """sites.get_all pins GET /sites with query params and models."""
    raw_site = {"id": "site-1", "name": "Headquarters"}
    session = _Session(
        [
            {"data": [raw_site, {"id": "bad", "deviceCount": "not-an-int"}]},
            None,
        ]
    )
    client = _client(session)

    sites = await client.sites.get_all(
        offset=0, limit=10, filter_str="name.isNotNull()"
    )
    assert len(sites) == 1
    assert isinstance(sites[0], Site)
    assert sites[0].id == "site-1"
    assert sites[0].name == "Headquarters"

    req = session.requests[0]
    assert req["method"] == "GET"
    assert req["url"] == "https://192.168.1.1/proxy/network/integration/v1/sites"
    assert req["params"] == {"offset": 0, "limit": 10, "filter": "name.isNotNull()"}

    assert await client.sites.get_all() == []


async def test_sites_get_legacy_all_pins_request() -> None:
    """sites.get_legacy_all pins GET /proxy/network/api/self/sites."""
    session = _Session(
        [
            {"data": [{"name": "default", "desc": "Default"}]},
            None,
        ]
    )
    client = _client(session)

    res = await client.sites.get_legacy_all()
    assert res == [{"name": "default", "desc": "Default"}]

    req = session.requests[0]
    assert req["method"] == "GET"
    assert req["url"] == "https://192.168.1.1/proxy/network/api/self/sites"

    assert await client.sites.get_legacy_all() == []


async def test_vouchers_create_pins_spec_request_and_models() -> None:
    """vouchers.create pins POST /sites/{siteId}/hotspot/vouchers with parameters."""
    voucher_data = {"id": "v-1", "code": "12345-67890", "name": "VisitorPass"}
    session = _Session(
        [
            {"data": {"vouchers": [voucher_data]}},
        ]
    )
    client = _client(session)

    res = await client.vouchers.create(
        "default",
        name="VisitorPass",
        time_limit_minutes=480,
        count=2,
        authorized_guest_limit=1,
        data_usage_limit_mbytes=1000,
        rx_rate_limit_kbps=50000,
        tx_rate_limit_kbps=25000,
    )
    assert len(res) == 1
    assert isinstance(res[0], Voucher)
    assert res[0].id == "v-1"
    assert res[0].code == "12345-67890"

    req = session.requests[0]
    assert req["method"] == "POST"
    assert (
        req["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/hotspot/vouchers"
    )
    assert req["json"] == {
        "count": 2,
        "name": "VisitorPass",
        "timeLimitMinutes": 480,
        "authorizedGuestLimit": 1,
        "dataUsageLimitMBytes": 1000,
        "rxRateLimitKbps": 50000,
        "txRateLimitKbps": 25000,
    }


async def test_vouchers_create_minimal_body_has_only_required_and_set_fields() -> None:
    """vouchers.create serializes only required and explicitly set fields."""
    session = _Session(
        [
            {"data": {"vouchers": [{"id": "v-1", "code": "1234567890"}]}},
            {"data": {"vouchers": [{"id": "v-2", "code": "2345678901"}]}},
        ]
    )
    client = _client(session)

    await client.vouchers.create(
        "default",
        name="Home Assistant",
        time_limit_minutes=480,
        count=1,
        authorized_guest_limit=1,
    )
    assert session.requests[0]["json"] == {
        "count": 1,
        "name": "Home Assistant",
        "timeLimitMinutes": 480,
        "authorizedGuestLimit": 1,
    }

    await client.vouchers.create(
        "default",
        name="Home Assistant",
        time_limit_minutes=480,
        count=1,
    )
    assert session.requests[1]["json"] == {
        "count": 1,
        "name": "Home Assistant",
        "timeLimitMinutes": 480,
    }


async def test_vouchers_create_failure_raises() -> None:
    """vouchers.create raises ValueError when creation response is empty."""
    session = _Session([{"data": []}])
    client = _client(session)

    with pytest.raises(ValueError, match="Failed to create vouchers"):
        await client.vouchers.create("default", name="Pass", time_limit_minutes=60)


async def test_vpn_clients_list_vpn_clients_pins_request_and_filters() -> None:
    """vpn_clients.list_vpn_clients pins legacy networkconf."""
    session = _Session(
        [
            {
                "data": [
                    {
                        "_id": "vpn-1",
                        "name": "Work VPN",
                        "purpose": "vpn-client",
                        "enabled": True,
                    },
                    {"_id": "lan-1", "name": "LAN", "purpose": "corporate"},
                    {
                        "_id": "bad-vpn",
                        "purpose": "vpn-client",
                        "enabled": "not-a-bool",
                    },
                ]
            }
        ]
    )
    client = _client(session)

    clients = await client.vpn_clients.list_vpn_clients("default")
    assert len(clients) == 1
    assert isinstance(clients[0], VpnClient)
    assert clients[0].id == "vpn-1"
    assert clients[0].name == "Work VPN"
    assert clients[0].enabled is True

    req = session.requests[0]
    assert req["method"] == "GET"
    assert (
        req["url"] == "https://192.168.1.1/proxy/network/api/s/default/rest/networkconf"
    )


async def test_vpn_clients_update_vpn_client_pins_request_and_fallback() -> None:
    """vpn_clients.update_vpn_client updates VPN client and uses fallback search."""
    session = _Session(
        [
            # Direct hit
            {
                "data": [
                    {
                        "_id": "vpn-1",
                        "name": "VPN 1",
                        "purpose": "vpn-client",
                        "enabled": True,
                    }
                ]
            },
            # PUT response
            {
                "data": [
                    {
                        "_id": "vpn-1",
                        "name": "VPN 1",
                        "purpose": "vpn-client",
                        "enabled": False,
                    }
                ]
            },
            # Direct miss -> fallback list hit
            {"data": []},
            {
                "data": [
                    {
                        "_id": "vpn-2",
                        "name": "VPN 2",
                        "purpose": "vpn-client",
                        "enabled": True,
                    }
                ]
            },
            {
                "data": [
                    {
                        "_id": "vpn-2",
                        "name": "VPN 2",
                        "purpose": "vpn-client",
                        "enabled": False,
                    }
                ]
            },
        ]
    )
    client = _client(session)

    # 1. Direct match
    res1 = await client.vpn_clients.update_vpn_client("default", "vpn-1", enabled=False)
    assert isinstance(res1, VpnClient)
    assert res1.id == "vpn-1"
    assert res1.enabled is False
    assert session.requests[1]["method"] == "PUT"
    assert (
        session.requests[1]["url"]
        == "https://192.168.1.1/proxy/network/api/s/default/rest/networkconf/vpn-1"
    )
    assert session.requests[1]["json"] == {
        "_id": "vpn-1",
        "name": "VPN 1",
        "purpose": "vpn-client",
        "enabled": False,
    }

    # 2. Fallback search match
    res2 = await client.vpn_clients.update_vpn_client("default", "vpn-2", enabled=False)
    assert isinstance(res2, VpnClient)
    assert res2.id == "vpn-2"


async def test_vpn_clients_update_vpn_client_not_found_raises() -> None:
    """vpn_clients.update_vpn_client raises ValueError when not found."""
    session = _Session([{"data": []}, {"data": []}])
    client = _client(session)

    with pytest.raises(ValueError, match="VPN Client missing-vpn not found"):
        await client.vpn_clients.update_vpn_client(
            "default", "missing-vpn", enabled=True
        )


async def test_wifi_get_legacy_configs_pins_request() -> None:
    """wifi.get_legacy_configs pins GET /proxy/network/api/s/{site}/rest/wlanconf."""
    session = _Session(
        [
            {"data": [{"name": "HomeWlan", "x_passphrase": "secret"}]},
            None,
        ]
    )
    client = _client(session)

    configs = await client.wifi.get_legacy_configs("default")
    assert configs == [{"name": "HomeWlan", "x_passphrase": "secret"}]

    req = session.requests[0]
    assert req["method"] == "GET"
    assert req["url"] == "https://192.168.1.1/proxy/network/api/s/default/rest/wlanconf"

    assert await client.wifi.get_legacy_configs("default") == []


async def test_wifi_update_pins_spec_request_and_strips_read_only() -> None:
    """wifi.update GETs current broadcast, strips id/metadata, and PUTs."""
    current_wifi = {
        "id": "wifi-1",
        "metadata": {"origin": "USER"},
        "name": "Home WiFi",
        "type": "STANDARD",
        "enabled": True,
    }
    updated_wifi = {
        "id": "wifi-1",
        "name": "Home WiFi",
        "type": "STANDARD",
        "enabled": False,
    }
    session = _Session(
        [
            current_wifi,
            updated_wifi,
        ]
    )
    client = _client(session)

    res = await client.wifi.update("default", "wifi-1", enabled=False)
    assert isinstance(res, WifiNetwork)
    assert res.id == "wifi-1"
    assert res.enabled is False

    req_put = session.requests[1]
    assert req_put["method"] == "PUT"
    assert (
        req_put["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/wifi/broadcasts/wifi-1"
    )
    assert req_put["json"] == {
        "name": "Home WiFi",
        "type": "STANDARD",
        "enabled": False,
    }


async def test_wifi_update_not_found_raises() -> None:
    """wifi.update raises ValueError when network is not found."""
    session = _Session([None])
    client = _client(session)

    with pytest.raises(ValueError, match="WiFi network missing-wifi not found"):
        await client.wifi.update("default", "missing-wifi", enabled=False)


# =============================================================================
# Scope 2 (Round 2): Branch and edge-case coverage for partially covered methods
# =============================================================================


async def test_clients_get_all_pagination_and_fallback_branches() -> None:
    """clients.get_all covers partial pagination, filter, error, and
    validation branches."""
    c1 = {"id": "c1", "macAddress": "00:11:22:33:44:01"}
    session = _Session(
        [
            # 1. Manual pagination with offset only (limit is None)
            {"data": [c1]},
            # 2. Manual pagination with limit only (offset is None)
            {"data": [c1]},
            # 3. Manual pagination where response is None -> returns []
            None,
            # 4. Manual pagination where data is not a list -> returns []
            {"data": "not-a-list"},
            # 5. Manual pagination where data has non-dict and invalid dict
            # -> logs & returns valid
            {"data": [c1, "not-a-dict", {"bad": "missing-id"}]},
            # 6. Auto-paginate with filter_str (2 pages, terminating
            # when current_offset >= total_count)
            {"data": [c1], "totalCount": 2, "count": 1},
            {"data": [c1], "totalCount": 2, "count": 1},
            # 7. Auto-paginate where response is None -> breaks immediately
            None,
            # 8. Auto-paginate where response is not a dict (e.g. JSON list)
            # -> breaks immediately
            [],
            # 9. Auto-paginate where data is not a list (e.g. integer)
            # -> breaks on count==0
            {"data": 123, "totalCount": 0, "count": 0},
            # 10. Auto-paginate with non-dict and invalid items in data
            {"data": [c1, "non-dict", {"bad": "field"}], "totalCount": 1, "count": 1},
            # 11. Auto-paginate breaks when total_count is None
            {"data": [c1], "count": 1},
            # 12. Auto-paginate breaks when count is not an int
            {"data": [c1], "totalCount": 10, "count": "bad"},
        ]
    )
    client = _client(session)

    # 1. offset only
    res_off = await client.clients.get_all("default", offset=5)
    assert len(res_off) == 1
    req1 = session.requests[0]
    assert req1["method"] == "GET"
    assert (
        req1["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/clients"
    )
    assert req1["params"] == {"offset": 5}

    # 2. limit only
    res_lim = await client.clients.get_all("default", limit=10)
    assert len(res_lim) == 1
    req2 = session.requests[1]
    assert req2["params"] == {"limit": 10}

    # 3. response is None in manual pagination
    assert await client.clients.get_all("default", offset=0, limit=1) == []

    # 4. data not a list in manual pagination
    assert await client.clients.get_all("default", offset=0, limit=1) == []

    # 5. non-dict and invalid items skipped in manual pagination
    res_skip = await client.clients.get_all("default", offset=0, limit=5)
    assert len(res_skip) == 1
    assert res_skip[0].id == "c1"

    # 6. auto-paginate with filter_str
    res_filter = await client.clients.get_all(
        "default", filter_str="connected.eq(true)"
    )
    assert len(res_filter) == 2
    assert session.requests[5]["params"] == {
        "offset": 0,
        "limit": 100,
        "filter": "connected.eq(true)",
    }
    assert session.requests[6]["params"] == {
        "offset": 1,
        "limit": 100,
        "filter": "connected.eq(true)",
    }

    # 7. auto-paginate response is None
    assert await client.clients.get_all("default") == []

    # 8. auto-paginate response not dict
    assert await client.clients.get_all("default") == []

    # 9. auto-paginate data not list
    assert await client.clients.get_all("default") == []

    # 10. auto-paginate non-dict and invalid items in data
    res_auto_skip = await client.clients.get_all("default")
    assert len(res_auto_skip) == 1
    assert res_auto_skip[0].id == "c1"

    # 11. auto-paginate totalCount is None
    res_no_total = await client.clients.get_all("default")
    assert len(res_no_total) == 1

    # 12. auto-paginate count is not an int
    res_bad_count = await client.clients.get_all("default")
    assert len(res_bad_count) == 1


async def test_clients_get_active_legacy_non_list_and_filters() -> None:
    """clients.get_active_legacy handles non-list data and filters out non-dict
    items."""
    session = _Session(
        [
            # 1. Non-list data fallback
            {"data": "not-a-list"},
            # 2. List with non-dict items
            {"data": [{"mac": "00:11:22:33:44:55", "essid": "Home"}, "not-a-dict"]},
        ]
    )
    client = _client(session)

    res1 = await client.clients.get_active_legacy("default")
    assert res1 == []
    req1 = session.requests[0]
    assert req1["method"] == "GET"
    assert req1["url"] == "https://192.168.1.1/proxy/network/api/s/default/stat/sta"

    res2 = await client.clients.get_active_legacy("default")
    assert res2 == [{"mac": "00:11:22:33:44:55", "essid": "Home"}]


async def test_devices_get_all_params_and_fallback_branches() -> None:
    """devices.get_all covers individual query params and non-list data."""
    raw_dev = {"id": "dev-1", "macAddress": "00:11:22:33:44:01"}
    session = _Session(
        [
            # 1. filter_str only
            {"data": [raw_dev]},
            # 2. offset only
            {"data": [raw_dev]},
            # 3. limit only
            {"data": [raw_dev]},
            # 4. non-list data fallback
            {"data": "not-a-list"},
        ]
    )
    client = _client(session)

    # 1. filter_str
    res_f = await client.devices.get_all("default", filter_str="state.eq(ONLINE)")
    assert len(res_f) == 1
    assert session.requests[0]["params"] == {"filter": "state.eq(ONLINE)"}

    # 2. offset only
    res_o = await client.devices.get_all("default", offset=5)
    assert len(res_o) == 1
    assert session.requests[1]["params"] == {"offset": 5}

    # 3. limit only
    res_l = await client.devices.get_all("default", limit=10)
    assert len(res_l) == 1
    assert session.requests[2]["params"] == {"limit": 10}

    # 4. non-list data
    res_non_list = await client.devices.get_all("default")
    assert res_non_list == []


async def test_devices_get_statistics_non_dict_data() -> None:
    """devices.get_statistics returns empty dict when response data is not a dict."""
    session = _Session(
        [
            {"data": "not-a-dict"},
            {"data": [1, 2, 3]},
        ]
    )
    client = _client(session)

    res1 = await client.devices.get_statistics("default", "dev-1")
    assert res1 == {}

    res2 = await client.devices.get_statistics("default", "dev-2")
    assert res2 == {}


async def test_devices_get_legacy_site_devices_non_list_dict() -> None:
    """devices.get_legacy_site_devices handles non-list and non-dict payload data."""
    session = _Session(
        [
            {"data": 123},
            None,
        ]
    )
    client = _client(session)

    res1 = await client.devices.get_legacy_site_devices("default")
    assert res1 == []

    res2 = await client.devices.get_legacy_site_devices("default")
    assert res2 == []


async def test_devices_get_port_metrics_non_dict_and_missing_port_idx() -> None:
    """devices.get_port_metrics skips non-dict ports and ports with
    invalid/missing port_idx."""
    legacy_payload = {
        "port_table": [
            "not-a-dict-port",
            {"name": "missing-idx"},
            {"port_idx": "not-an-int"},
            {
                "port_idx": 1,
                "port_poe": True,
                "poe_power": "5.0",
                "rx_bytes": 100,
                "tx_bytes": 200,
            },
        ],
    }
    session = _Session([{"data": [legacy_payload]}])
    client = _client(session)

    metrics = await client.devices.get_port_metrics("default", "aa:bb:cc:dd:ee:ff")
    assert metrics.poe_ports == {1: 5.0}
    assert metrics.port_bytes[1].rx_bytes == 100
    assert metrics.port_bytes[1].tx_bytes == 200


async def test_devices_set_outlet_state_outlet_idx_and_cycle_enabled() -> None:
    """devices.set_outlet_state handles outlet_idx alias, invalid idx, and
    cycle_enabled on append."""
    session = _Session([{}, {}])
    client = _client(session)

    # 1. Update existing override that uses outlet_idx and has an invalid item
    current_device_1 = {
        "_id": "dev-obj-1",
        "outlet_overrides": [
            {"index": "invalid", "relay_state": True},
            {"outlet_idx": 2, "relay_state": True},
        ],
    }
    ok1 = await client.devices.set_outlet_state(
        "default",
        "dev-mac-1",
        outlet_index=2,
        state=False,
        cycle_enabled=False,
        current_device=current_device_1,
    )
    assert ok1 is True
    assert session.requests[0]["method"] == "PUT"
    assert session.requests[0]["json"] == {
        "outlet_overrides": [
            {"index": "invalid", "relay_state": True},
            {"outlet_idx": 2, "relay_state": False, "cycle_enabled": False},
        ]
    }

    # 2. Append new override when outlet not found, with cycle_enabled=True
    current_device_2 = {
        "_id": "dev-obj-2",
        "outlet_overrides": [
            {"index": 1, "relay_state": True},
        ],
    }
    ok2 = await client.devices.set_outlet_state(
        "default",
        "dev-mac-2",
        outlet_index=4,
        state=True,
        cycle_enabled=True,
        current_device=current_device_2,
    )
    assert ok2 is True
    assert session.requests[1]["json"] == {
        "outlet_overrides": [
            {"index": 1, "relay_state": True},
            {"index": 4, "relay_state": True, "cycle_enabled": True},
        ]
    }


async def test_firewall_list_rules_params_and_fallback_branches() -> None:
    """firewall.list_rules covers single pagination params, filter, and
    non-list responses."""
    raw_rule = {"id": "r-1", "name": "Rule 1", "action": "accept", "enabled": True}
    session = _Session(
        [
            # 1. Manual pagination with offset only
            {"data": [raw_rule]},
            # 2. Manual pagination with limit only
            {"data": [raw_rule]},
            # 3. Manual pagination with offset & limit, no filter
            {"data": [raw_rule]},
            # 4. Manual pagination where response is None -> []
            None,
            # 5. Manual pagination where data is not a list -> []
            {"data": "not-a-list"},
            # 6. Auto-pagination with filter_str
            {"data": [raw_rule], "totalCount": 1, "count": 1},
        ]
    )
    client = _client(session)

    # 1. offset only
    res_o = await client.firewall.list_rules("default", offset=5)
    assert len(res_o) == 1
    assert session.requests[0]["params"] == {"offset": 5}

    # 2. limit only
    res_l = await client.firewall.list_rules("default", limit=10)
    assert len(res_l) == 1
    assert session.requests[1]["params"] == {"limit": 10}

    # 3. offset and limit without filter
    res_ol = await client.firewall.list_rules("default", offset=0, limit=5)
    assert len(res_ol) == 1
    assert session.requests[2]["params"] == {"offset": 0, "limit": 5}

    # 4. None response
    assert await client.firewall.list_rules("default", offset=0, limit=5) == []

    # 5. non-list data
    assert await client.firewall.list_rules("default", offset=0, limit=5) == []

    # 6. auto-pagination with filter_str
    res_f = await client.firewall.list_rules(
        "default", filter_str="action.eq('accept')"
    )
    assert len(res_f) == 1
    assert session.requests[5]["params"] == {
        "offset": 0,
        "limit": 200,
        "filter": "action.eq('accept')",
    }


async def test_routes_update_route_branches_and_fallback() -> None:
    """routes.update_route covers non-matching items, id matching, enabled=None,
    and empty PUT response."""
    session = _Session(
        [
            # 1. GET returns non-matching route followed by matching route by 'id'
            {
                "data": [
                    {"_id": "rt-other", "description": "Other", "enabled": True},
                    {"id": "rt-2", "description": "Route 2", "enabled": True},
                ]
            },
            # PUT response returns empty list -> falls back to current_payload
            {"data": []},
        ]
    )
    client = _client(session)

    res = await client.routes.update_route(
        "default", "rt-2", description="Updated Route"
    )
    assert isinstance(res, PolicyBasedRoute)
    assert res.id == "rt-2"
    assert res.description == "Updated Route"
    assert res.enabled is True

    req_put = session.requests[1]
    assert req_put["method"] == "PUT"
    assert req_put["json"] == {
        "id": "rt-2",
        "description": "Updated Route",
        "enabled": True,
    }


async def test_sites_get_all_params_and_non_list_data() -> None:
    """sites.get_all covers individual pagination params and non-list data."""
    raw_site = {"id": "site-1", "name": "Headquarters"}
    session = _Session(
        [
            # 1. offset only
            {"data": [raw_site]},
            # 2. limit only
            {"data": [raw_site]},
            # 3. non-list data fallback
            {"data": "not-a-list"},
        ]
    )
    client = _client(session)

    res_o = await client.sites.get_all(offset=5)
    assert len(res_o) == 1
    assert session.requests[0]["params"] == {"offset": 5}

    res_l = await client.sites.get_all(limit=10)
    assert len(res_l) == 1
    assert session.requests[1]["params"] == {"limit": 10}

    res_non_list = await client.sites.get_all()
    assert res_non_list == []


async def test_sites_get_legacy_all_dict_and_non_list_fallback() -> None:
    """sites.get_legacy_all handles single dict payload and non-list/non-dict data."""
    session = _Session(
        [
            # 1. Dict payload
            {"data": {"name": "default", "desc": "Default Site"}},
            # 2. Non-list non-dict data
            {"data": 123},
        ]
    )
    client = _client(session)

    res1 = await client.sites.get_legacy_all()
    assert res1 == [{"name": "default", "desc": "Default Site"}]

    res2 = await client.sites.get_legacy_all()
    assert res2 == []


async def test_vouchers_create_single_voucher_and_non_dict_error() -> None:
    """vouchers.create handles single voucher dict result and raises on
    non-dict response."""
    voucher_data = {"id": "v-single", "code": "99999-00000", "name": "SinglePass"}
    session = _Session(
        [
            # 1. Direct single voucher dict result (not wrapped in vouchers list)
            {"data": voucher_data},
            # 2. Non-dict response (e.g. list)
            [],
        ]
    )
    client = _client(session)

    res = await client.vouchers.create(
        "default", name="SinglePass", time_limit_minutes=120
    )
    assert len(res) == 1
    assert isinstance(res[0], Voucher)
    assert res[0].id == "v-single"
    assert res[0].code == "99999-00000"

    with pytest.raises(ValueError, match="Failed to create vouchers"):
        await client.vouchers.create("default", name="FailPass", time_limit_minutes=60)


async def test_vpn_clients_update_vpn_client_branches_and_fallback() -> None:
    """vpn_clients.update_vpn_client covers non-matching items, id matching,
    enabled=None, and empty PUT response."""
    session = _Session(
        [
            # 1. Direct hit with non-matching item first, target matched
            # by 'id', enabled=None, empty PUT response
            {
                "data": [
                    {"_id": "lan-1", "purpose": "corporate"},
                    {
                        "id": "vpn-target",
                        "purpose": "vpn-client",
                        "name": "Target VPN",
                        "enabled": True,
                    },
                ]
            },
            {"data": []},  # empty PUT response -> returns current_payload
            # 2. Fallback search with non-matching item first
            {"data": []},  # direct GET miss
            {
                "data": [
                    {"_id": "lan-2", "purpose": "corporate"},
                    {
                        "_id": "vpn-fb",
                        "purpose": "vpn-client",
                        "name": "FB VPN",
                        "enabled": True,
                    },
                ]
            },
            {
                "data": [
                    {
                        "_id": "vpn-fb",
                        "purpose": "vpn-client",
                        "name": "FB VPN",
                        "enabled": False,
                    },
                ]
            },
        ]
    )
    client = _client(session)

    # 1. Direct hit with enabled=None and empty PUT response
    res1 = await client.vpn_clients.update_vpn_client(
        "default", "vpn-target", name="Target Renamed"
    )
    assert isinstance(res1, VpnClient)
    assert res1.id == "vpn-target"
    assert res1.name == "Target Renamed"
    assert res1.enabled is True
    assert session.requests[1]["method"] == "PUT"
    assert session.requests[1]["json"] == {
        "id": "vpn-target",
        "purpose": "vpn-client",
        "name": "Target Renamed",
        "enabled": True,
    }

    # 2. Fallback search with non-matching item before target
    res2 = await client.vpn_clients.update_vpn_client(
        "default", "vpn-fb", enabled=False
    )
    assert isinstance(res2, VpnClient)
    assert res2.id == "vpn-fb"
    assert res2.enabled is False


async def test_wifi_get_legacy_configs_non_list_and_filter() -> None:
    """wifi.get_legacy_configs handles non-list data and filters out non-dict items."""
    session = _Session(
        [
            {"data": "not-a-list"},
            {"data": [{"name": "HomeWlan", "x_passphrase": "pass"}, "not-a-dict"]},
        ]
    )
    client = _client(session)

    assert await client.wifi.get_legacy_configs("default") == []

    res2 = await client.wifi.get_legacy_configs("default")
    assert res2 == [{"name": "HomeWlan", "x_passphrase": "pass"}]


async def test_wifi_get_all_params_and_non_list_data() -> None:
    """wifi.get_all covers individual query params and non-list data."""
    raw_wifi = {"id": "wifi-1", "name": "IoT", "type": "STANDARD", "enabled": True}
    session = _Session(
        [
            # 1. offset only
            {"data": [raw_wifi]},
            # 2. limit only
            {"data": [raw_wifi]},
            # 3. non-list data
            {"data": "not-a-list"},
        ]
    )
    client = _client(session)

    res_o = await client.wifi.get_all("default", offset=2)
    assert len(res_o) == 1
    assert session.requests[0]["params"] == {"offset": 2}

    res_l = await client.wifi.get_all("default", limit=5)
    assert len(res_l) == 1
    assert session.requests[1]["params"] == {"limit": 5}

    res_non_list = await client.wifi.get_all("default")
    assert res_non_list == []
