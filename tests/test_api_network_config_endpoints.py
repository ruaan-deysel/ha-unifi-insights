# Copyright 2026 UniFi Insights contributors
"""Tests for UniFi Network config endpoints pinned against the spec."""

from __future__ import annotations

import json
from typing import Any, Self

import pytest
from yarl import URL

from custom_components.unifi_insights.api import ApiKeyAuth, ConnectionType
from custom_components.unifi_insights.api.exceptions import (
    UniFiNotFoundError,
    UniFiResponseError,
)
from custom_components.unifi_insights.api.network.client import UniFiNetworkClient
from custom_components.unifi_insights.api.network.models.acl import (
    ACLAction,
    ACLDestinationFilter,
    ACLDeviceFilter,
    ACLMetadata,
    ACLRule,
    ACLRuleOrdering,
    ACLRuleType,
    ACLSourceFilter,
)
from custom_components.unifi_insights.api.network.models.acl import (
    MetadataOrigin as ACLMetadataOrigin,
)
from custom_components.unifi_insights.api.network.models.dns import (
    DNSPolicy,
    DNSPolicyMetadata,
    DNSRecordType,
)
from custom_components.unifi_insights.api.network.models.firewall import (
    FirewallAction,
    FirewallActionConfig,
    FirewallPolicyOrdering,
    FirewallProtocol,
    FirewallRule,
    FirewallZone,
    OrderedFirewallPolicyIds,
)
from custom_components.unifi_insights.api.network.models.network import Network
from custom_components.unifi_insights.api.network.models.resources import (
    DeviceTag,
    RADIUSProfile,
    VPNServer,
    VPNTunnel,
    WANInterface,
)
from custom_components.unifi_insights.api.network.models.traffic import (
    Country,
    DPIApplication,
    DPICategory,
    TrafficMatchingList,
    TrafficMatchingType,
    TrafficMetadata,
)
from custom_components.unifi_insights.api.network.models.traffic import (
    MetadataOrigin as TrafficMetadataOrigin,
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


# =============================================================================
# DNS Endpoints (dns.py)
# =============================================================================


async def test_dns_get_all_pins_spec_request_and_branches() -> None:
    """dns.get_all pins endpoint and covers response parsing branches."""
    payload = [
        {
            "id": "dns-1",
            "type": "A_RECORD",
            "enabled": True,
            "domain": "example.com",
            "ipv4Address": "192.168.1.10",
            "ttlSeconds": 300,
        }
    ]
    session = _Session(
        [
            {"data": payload},  # 1. Wrapped list
            payload,  # 2. Raw list with filter query
            None,  # 3. None response
            {"count": 0},  # 4. Non-list data fallback
        ]
    )
    client = _client(session)

    # 1. Wrapped list
    policies = await client.dns.get_all("default", offset=0, limit=25)
    assert len(policies) == 1
    assert isinstance(policies[0], DNSPolicy)
    assert policies[0].id == "dns-1"
    assert policies[0].domain == "example.com"
    req1 = session.requests[0]
    assert req1["method"] == "GET"
    assert (
        req1["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/dns/policies"
    )
    assert req1["params"] == {"offset": 0, "limit": 25}

    # 2. Raw list with filter query
    policies2 = await client.dns.get_all(
        "default", offset=10, limit=50, filter_query="domain.eq('example.com')"
    )
    assert len(policies2) == 1
    req2 = session.requests[1]
    assert req2["params"] == {
        "offset": 10,
        "limit": 50,
        "filter": "domain.eq('example.com')",
    }

    # 3. None response
    assert await client.dns.get_all("default") == []

    # 4. Non-list data fallback
    assert await client.dns.get_all("default") == []


async def test_dns_get_pins_spec_request_and_branches() -> None:
    """dns.get pins endpoint, unwrapped/list responses, and missing error."""
    policy_dict = {
        "id": "dns-1",
        "type": "A_RECORD",
        "enabled": True,
        "domain": "example.com",
    }
    session = _Session(
        [
            {"data": policy_dict},  # 1. Wrapped dict
            {"data": [policy_dict]},  # 2. Wrapped list with item
            {"data": []},  # 3. Empty list -> ValueError
            {"data": 123},  # 4. Non-dict/non-list data -> ValueError
            None,  # 5. None response -> ValueError
        ]
    )
    client = _client(session)

    # 1. Wrapped dict
    p1 = await client.dns.get("default", "dns-1")
    assert p1.id == "dns-1"
    req1 = session.requests[0]
    assert req1["method"] == "GET"
    assert (
        req1["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/dns/policies/dns-1"
    )

    # 2. List response
    p2 = await client.dns.get("default", "dns-1")
    assert p2.id == "dns-1"

    # 3. Empty list
    with pytest.raises(ValueError, match="DNS policy missing not found"):
        await client.dns.get("default", "missing")

    # 4. Invalid structure
    with pytest.raises(ValueError, match="DNS policy invalid not found"):
        await client.dns.get("default", "invalid")
    with pytest.raises(ValueError, match="DNS policy none not found"):
        await client.dns.get("default", "none")


async def test_dns_create_pins_spec_request_and_branches() -> None:
    """dns.create pins request body against spec and covers branches."""
    created_payload = {
        "id": "dns-new",
        "type": "A_RECORD",
        "enabled": True,
        "domain": "test.local",
        "ipv4Address": "192.168.1.50",
        "ttlSeconds": 600,
    }
    session = _Session(
        [
            {"data": created_payload},  # 1. Enum record_type, wrapped response
            created_payload,  # 2. String record_type, raw response, kwargs
            None,  # 3. None response -> ValueError
            {"data": "non-dict"},  # 4. Result not dict -> ValueError
        ]
    )
    client = _client(session)

    # 1. Enum record_type, wrapped response
    res1 = await client.dns.create(
        "default",
        record_type=DNSRecordType.A_RECORD,
        enabled=True,
        domain="test.local",
        ipv4_address="192.168.1.50",
        ttl_seconds=600,
    )
    assert res1.id == "dns-new"
    req1 = session.requests[0]
    assert req1["method"] == "POST"
    assert (
        req1["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/dns/policies"
    )
    assert req1["json"] == {
        "type": "A_RECORD",
        "enabled": True,
        "domain": "test.local",
        "ipv4Address": "192.168.1.50",
        "ttlSeconds": 600,
    }

    # 2. String record_type, raw response, kwargs
    res2 = await client.dns.create(
        "default",
        record_type="MX_RECORD",
        enabled=False,
        domain="example.com",
        mailServerDomain="mail.example.com",
        priority=10,
    )
    assert res2.id == "dns-new"
    req2 = session.requests[1]
    assert req2["json"] == {
        "type": "MX_RECORD",
        "enabled": False,
        "domain": "example.com",
        "mailServerDomain": "mail.example.com",
        "priority": 10,
    }

    # 3. Invalid response
    with pytest.raises(ValueError, match="Failed to create DNS policy"):
        await client.dns.create(
            "default",
            record_type=DNSRecordType.TXT_RECORD,
            domain="example.com",
            text="test",
        )
    with pytest.raises(ValueError, match="Failed to create DNS policy"):
        await client.dns.create(
            "default",
            record_type=DNSRecordType.TXT_RECORD,
            domain="example.com",
            text="test",
        )


async def test_dns_update_pins_spec_request_and_branches() -> None:
    """dns.update pins PUT request and covers branches."""
    updated_payload = {
        "id": "dns-1",
        "type": "AAAA_RECORD",
        "enabled": True,
        "domain": "v6.local",
    }
    session = _Session(
        [
            {"data": updated_payload},  # 1. Enum type and fields
            updated_payload,  # 2. String type and kwargs
            [],  # 3. Invalid response -> ValueError
            {"data": "non-dict"},  # 4. Result not dict -> ValueError
        ]
    )
    client = _client(session)

    # 1. Enum type and fields
    res1 = await client.dns.update(
        "default",
        "dns-1",
        record_type=DNSRecordType.AAAA_RECORD,
        enabled=True,
        domain="v6.local",
        ipv6Address="2001:db8::1",
        ttl_seconds=120,
    )
    assert res1.id == "dns-1"
    req1 = session.requests[0]
    assert req1["method"] == "PUT"
    assert (
        req1["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/dns/policies/dns-1"
    )
    assert req1["json"] == {
        "type": "AAAA_RECORD",
        "enabled": True,
        "domain": "v6.local",
        "ipv6Address": "2001:db8::1",
        "ttlSeconds": 120,
    }

    # 2. String type and kwargs
    res2 = await client.dns.update(
        "default",
        "dns-1",
        record_type="CNAME_RECORD",
        enabled=True,
        domain="alias.example.com",
        targetDomain="example.com",
        ttl_seconds=300,
    )
    assert res2.id == "dns-1"
    req2 = session.requests[1]
    assert req2["json"] == {
        "type": "CNAME_RECORD",
        "enabled": True,
        "domain": "alias.example.com",
        "targetDomain": "example.com",
        "ttlSeconds": 300,
    }

    # 3. Invalid response
    with pytest.raises(ValueError, match="Failed to update DNS policy"):
        await client.dns.update(
            "default",
            "dns-1",
            record_type="TXT_RECORD",
            enabled=True,
            domain="example.com",
            text="test",
        )
    with pytest.raises(ValueError, match="Failed to update DNS policy"):
        await client.dns.update(
            "default",
            "dns-1",
            record_type="TXT_RECORD",
            enabled=True,
            domain="example.com",
            text="test",
        )


async def test_dns_delete_pins_spec_request() -> None:
    """dns.delete pins DELETE request."""
    session = _Session([None])
    client = _client(session)

    assert await client.dns.delete("default", "dns-1") is True
    req = session.requests[0]
    assert req["method"] == "DELETE"
    assert (
        req["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/dns/policies/dns-1"
    )


# =============================================================================
# ACL Endpoints (acl.py)
# =============================================================================


async def test_acl_get_all_pins_spec_request_and_branches() -> None:
    """acl.get_all pins endpoint, limit capping, and fallback branches."""
    rule_payload = {
        "id": "rule-1",
        "type": "IPV4",
        "name": "Block SSH",
        "action": "BLOCK",
        "index": 1,
        "enabled": True,
    }
    session = _Session(
        [
            {"data": [rule_payload]},  # 1. Wrapped list
            [rule_payload],  # 2. Raw list with limit capped at 200 and filter
            None,  # 3. None response
            {"unexpected": True},  # 4. Non-list fallback
        ]
    )
    client = _client(session)

    # 1. Wrapped list
    rules = await client.acl.get_all("default", offset=0, limit=25)
    assert len(rules) == 1
    assert isinstance(rules[0], ACLRule)
    assert rules[0].id == "rule-1"
    req1 = session.requests[0]
    assert req1["method"] == "GET"
    assert (
        req1["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/acl-rules"
    )
    assert req1["params"] == {"offset": 0, "limit": 25}

    # 2. Raw list with limit capped at 200 and filter_str
    rules2 = await client.acl.get_all(
        "default", offset=5, limit=500, filter_str="action.eq('BLOCK')"
    )
    assert len(rules2) == 1
    req2 = session.requests[1]
    assert req2["params"] == {
        "offset": 5,
        "limit": 200,
        "filter": "action.eq('BLOCK')",
    }

    # 3. None response
    assert await client.acl.get_all("default") == []

    # 4. Non-list fallback
    assert await client.acl.get_all("default") == []


async def test_acl_get_pins_spec_request_and_branches() -> None:
    """acl.get pins endpoint, unwrapped/list responses, and missing error."""
    rule_dict = {
        "id": "rule-1",
        "type": "IPV4",
        "name": "Block Telnet",
        "action": "BLOCK",
        "index": 0,
        "enabled": True,
    }
    session = _Session(
        [
            {"data": rule_dict},
            {"data": [rule_dict]},
            {"data": []},
            {"data": 123},
            None,
            {"data": "non-dict"},
        ]
    )
    client = _client(session)

    # 1. Wrapped dict
    r1 = await client.acl.get("default", "rule-1")
    assert r1.id == "rule-1"
    req1 = session.requests[0]
    assert req1["method"] == "GET"
    assert (
        req1["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/acl-rules/rule-1"
    )

    # 2. List response
    r2 = await client.acl.get("default", "rule-1")
    assert r2.id == "rule-1"

    # 3. Empty list
    with pytest.raises(ValueError, match="ACL rule missing not found"):
        await client.acl.get("default", "missing")

    # 4. Non-dict/non-list
    with pytest.raises(ValueError, match="ACL rule invalid not found"):
        await client.acl.get("default", "invalid")
    with pytest.raises(ValueError, match="ACL rule none not found"):
        await client.acl.get("default", "none")


async def test_acl_create_pins_spec_request_and_branches() -> None:
    """acl.create pins POST request against spec and covers branches."""
    created_rule = {
        "id": "rule-created",
        "type": "IPV4",
        "name": "Block Web",
        "action": "BLOCK",
        "index": 2,
        "enabled": True,
        "description": "Block HTTP traffic",
    }
    session = _Session(
        [
            {"data": created_rule},  # 1. With description and kwargs
            created_rule,  # 2. Without description
            None,  # 3. Invalid response
            {"data": "non-dict"},  # 4. Result not dict
        ]
    )
    client = _client(session)

    # 1. With description and kwargs
    res1 = await client.acl.create(
        "default",
        name="Block Web",
        rule_type=ACLRuleType.IPV4,
        action=ACLAction.BLOCK,
        index=2,
        enabled=True,
        description="Block HTTP traffic",
        sourceFilter={"type": "PORTS", "portFilter": [80]},
    )
    assert res1.id == "rule-created"
    req1 = session.requests[0]
    assert req1["method"] == "POST"
    assert (
        req1["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/acl-rules"
    )
    assert req1["json"] == {
        "type": "IPV4",
        "name": "Block Web",
        "action": "BLOCK",
        "index": 2,
        "enabled": True,
        "description": "Block HTTP traffic",
        "sourceFilter": {"type": "PORTS", "portFilter": [80]},
    }

    # 2. Without description
    res2 = await client.acl.create(
        "default",
        name="Allow DNS",
        action=ACLAction.ALLOW,
    )
    assert res2.id == "rule-created"
    req2 = session.requests[1]
    assert req2["json"] == {
        "type": "IPV4",
        "name": "Allow DNS",
        "action": "ALLOW",
        "index": 0,
        "enabled": True,
    }

    # 3. Invalid response
    with pytest.raises(ValueError, match="Failed to create ACL rule"):
        await client.acl.create("default", name="Fail")
    with pytest.raises(ValueError, match="Failed to create ACL rule"):
        await client.acl.create("default", name="Fail")


async def test_acl_update_pins_spec_request_and_branches() -> None:
    """acl.update pins PUT request and covers branches."""
    updated_rule = {
        "id": "rule-1",
        "type": "IPV4",
        "name": "Updated Rule",
        "action": "ALLOW",
        "index": 1,
        "enabled": False,
    }
    session = _Session(
        [
            {"data": updated_rule},
            updated_rule,
            None,
            {"data": "non-dict"},
        ]
    )
    client = _client(session)

    # 1. Wrapped response
    res1 = await client.acl.update(
        "default",
        "rule-1",
        type="IPV4",
        name="Updated Rule",
        action="ALLOW",
        enabled=False,
    )
    assert res1.id == "rule-1"
    req1 = session.requests[0]
    assert req1["method"] == "PUT"
    assert (
        req1["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/acl-rules/rule-1"
    )
    assert req1["json"] == {
        "type": "IPV4",
        "name": "Updated Rule",
        "action": "ALLOW",
        "enabled": False,
    }

    # 2. Raw dict
    res2 = await client.acl.update(
        "default",
        "rule-1",
        type="IPV4",
        name="Updated Rule",
        action="ALLOW",
        enabled=True,
    )
    assert res2.id == "rule-1"

    # 3. Invalid response
    with pytest.raises(ValueError, match="Failed to update ACL rule"):
        await client.acl.update(
            "default",
            "rule-1",
            type="IPV4",
            name="Updated Rule",
            action="ALLOW",
            enabled=True,
        )
    with pytest.raises(ValueError, match="Failed to update ACL rule"):
        await client.acl.update(
            "default",
            "rule-1",
            type="IPV4",
            name="Updated Rule",
            action="ALLOW",
            enabled=True,
        )


async def test_acl_delete_pins_spec_request() -> None:
    """acl.delete pins DELETE request."""
    session = _Session([None])
    client = _client(session)

    assert await client.acl.delete("default", "rule-1") is True
    req = session.requests[0]
    assert req["method"] == "DELETE"
    assert (
        req["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/acl-rules/rule-1"
    )


async def test_acl_ordering_pins_spec_request_and_branches() -> None:
    """acl.get_ordering and update_ordering pin endpoints and cover error branches."""
    ordering_data = {"orderedAclRuleIds": ["r1", "r2", "r3"]}
    session = _Session(
        [
            {"data": ordering_data},  # 1. get_ordering wrapped
            ordering_data,  # 2. get_ordering raw
            None,  # 3. get_ordering failure
            {"data": "non-dict"},  # 3b. get_ordering data not dict
            {"data": ordering_data},  # 4. update_ordering wrapped
            ordering_data,  # 5. update_ordering raw
            None,  # 6. update_ordering failure
            {"data": "non-dict"},  # 6b. update_ordering result not dict
        ]
    )
    client = _client(session)

    # 1. get_ordering wrapped
    ord1 = await client.acl.get_ordering("default")
    assert ord1.ordered_acl_rule_ids == ["r1", "r2", "r3"]
    req1 = session.requests[0]
    assert req1["method"] == "GET"
    assert (
        req1["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/acl-rules/ordering"
    )

    # 2. get_ordering raw
    ord2 = await client.acl.get_ordering("default")
    assert ord2.ordered_acl_rule_ids == ["r1", "r2", "r3"]

    # 3. get_ordering failure
    with pytest.raises(ValueError, match="Failed to get ACL rule ordering"):
        await client.acl.get_ordering("default")
    with pytest.raises(ValueError, match="Failed to get ACL rule ordering"):
        await client.acl.get_ordering("default")

    # 4. update_ordering wrapped
    uord1 = await client.acl.update_ordering(
        "default", ordered_rule_ids=["r3", "r2", "r1"]
    )
    assert uord1.ordered_acl_rule_ids == ["r1", "r2", "r3"]
    req4 = session.requests[4]
    assert req4["method"] == "PUT"
    assert (
        req4["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/acl-rules/ordering"
    )
    assert req4["json"] == {"orderedAclRuleIds": ["r3", "r2", "r1"]}

    # 5. update_ordering raw
    uord2 = await client.acl.update_ordering("default", ordered_rule_ids=["r1"])
    assert uord2.ordered_acl_rule_ids == ["r1", "r2", "r3"]

    # 6. update_ordering failure
    with pytest.raises(ValueError, match="Failed to update ACL rule ordering"):
        await client.acl.update_ordering("default", ordered_rule_ids=[])
    with pytest.raises(ValueError, match="Failed to update ACL rule ordering"):
        await client.acl.update_ordering("default", ordered_rule_ids=[])


# =============================================================================
# Resources Endpoints (resources.py)
# =============================================================================


async def test_resources_get_wan_interfaces_pins_spec_request_and_branches() -> None:
    """resources.get_wan_interfaces pins endpoint and covers branches."""
    wan_payload = {"id": "wan-1", "name": "WAN 1", "status": "CONNECTED"}
    session = _Session(
        [
            {"data": [wan_payload]},  # 1. Wrapped list with params
            [wan_payload],  # 2. Raw list with no params
            None,  # 3. None response
            {"invalid": 1},  # 4. Non-list fallback
        ]
    )
    client = _client(session)

    # 1. Wrapped list with params
    wans = await client.resources.get_wan_interfaces("default", offset=0, limit=10)
    assert len(wans) == 1
    assert isinstance(wans[0], WANInterface)
    assert wans[0].id == "wan-1"
    req1 = session.requests[0]
    assert req1["method"] == "GET"
    assert (
        req1["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/wans"
    )
    assert req1["params"] == {
        "offset": 0,
        "limit": 10,
    }

    # 2. Raw list with no params
    wans2 = await client.resources.get_wan_interfaces("default")
    assert len(wans2) == 1
    req2 = session.requests[1]
    assert req2["params"] is None

    # 3. None response
    assert await client.resources.get_wan_interfaces("default") == []

    # 4. Non-list fallback
    assert await client.resources.get_wan_interfaces("default") == []


async def test_resources_get_vpn_tunnels_pins_spec_request_and_branches() -> None:
    """resources.get_vpn_tunnels pins endpoint and covers branches."""
    tunnel_payload = {"id": "tun-1", "name": "Site A Tunnel", "status": "UP"}
    session = _Session(
        [
            {"data": [tunnel_payload]},
            [tunnel_payload],
            None,
            {"not_list": 1},
        ]
    )
    client = _client(session)

    # 1. Wrapped list with params
    tunnels = await client.resources.get_vpn_tunnels(
        "default", offset=5, limit=20, filter_str="status.eq('UP')"
    )
    assert len(tunnels) == 1
    assert isinstance(tunnels[0], VPNTunnel)
    assert tunnels[0].id == "tun-1"
    req1 = session.requests[0]
    assert req1["method"] == "GET"
    assert (
        req1["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/vpn/site-to-site-tunnels"
    )
    assert req1["params"] == {"offset": 5, "limit": 20, "filter": "status.eq('UP')"}

    # 2. Raw list with no params
    assert len(await client.resources.get_vpn_tunnels("default")) == 1
    assert session.requests[1]["params"] is None

    # 3. None response
    assert await client.resources.get_vpn_tunnels("default") == []

    # 4. Empty list
    assert await client.resources.get_vpn_tunnels("default") == []


async def test_resources_get_vpn_servers_pins_spec_request_and_branches() -> None:
    """resources.get_vpn_servers pins endpoint and covers branches."""
    srv_payload = {"id": "srv-1", "name": "WireGuard Server", "enabled": True}
    session = _Session(
        [
            {"data": [srv_payload]},
            [srv_payload],
            None,
            {"not_a_list": 1},
        ]
    )
    client = _client(session)

    # 1. Wrapped list with params
    servers = await client.resources.get_vpn_servers(
        "default", offset=0, limit=5, filter_str="enabled.eq(true)"
    )
    assert len(servers) == 1
    assert isinstance(servers[0], VPNServer)
    assert servers[0].id == "srv-1"
    req1 = session.requests[0]
    assert req1["method"] == "GET"
    assert (
        req1["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/vpn/servers"
    )
    assert req1["params"] == {
        "offset": 0,
        "limit": 5,
        "filter": "enabled.eq(true)",
    }

    # 2. Raw list with no params
    assert len(await client.resources.get_vpn_servers("default")) == 1
    assert session.requests[1]["params"] is None

    # 3. None response
    assert await client.resources.get_vpn_servers("default") == []

    # 4. Non-list fallback
    assert await client.resources.get_vpn_servers("default") == []


async def test_resources_get_radius_profiles_pins_spec_request_and_branches() -> None:
    """resources.get_radius_profiles pins endpoint and covers branches."""
    rad_payload = {"id": "rad-1", "name": "Default RADIUS", "enabled": True}
    session = _Session(
        [
            {"data": [rad_payload]},
            [rad_payload],
            None,
            123,
        ]
    )
    client = _client(session)

    # 1. Wrapped list with params
    profiles = await client.resources.get_radius_profiles(
        "default", offset=0, limit=10, filter_str="enabled.eq(true)"
    )
    assert len(profiles) == 1
    assert isinstance(profiles[0], RADIUSProfile)
    assert profiles[0].id == "rad-1"
    req1 = session.requests[0]
    assert req1["method"] == "GET"
    assert (
        req1["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/radius/profiles"
    )
    assert req1["params"] == {
        "offset": 0,
        "limit": 10,
        "filter": "enabled.eq(true)",
    }

    # 2. Raw list with no params
    assert len(await client.resources.get_radius_profiles("default")) == 1
    assert session.requests[1]["params"] is None

    # 3. None response
    assert await client.resources.get_radius_profiles("default") == []

    # 4. Non-list fallback
    assert await client.resources.get_radius_profiles("default") == []


async def test_resources_get_device_tags_pins_spec_request_and_branches() -> None:
    """resources.get_device_tags pins endpoint and covers branches."""
    tag_payload = {"id": "tag-1", "name": "Cores"}
    session = _Session(
        [
            {"data": [tag_payload]},
            [tag_payload],
            None,
            {"not": "list"},
        ]
    )
    client = _client(session)

    # 1. Wrapped list with params
    tags = await client.resources.get_device_tags(
        "default", offset=2, limit=15, filter_str="name.eq('Cores')"
    )
    assert len(tags) == 1
    assert isinstance(tags[0], DeviceTag)
    assert tags[0].id == "tag-1"
    req1 = session.requests[0]
    assert req1["method"] == "GET"
    assert (
        req1["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/device-tags"
    )
    assert req1["params"] == {
        "offset": 2,
        "limit": 15,
        "filter": "name.eq('Cores')",
    }

    # 2. Raw list with no params
    assert len(await client.resources.get_device_tags("default")) == 1
    assert session.requests[1]["params"] is None

    # 3. None response
    assert await client.resources.get_device_tags("default") == []

    # 4. Non-list fallback
    assert await client.resources.get_device_tags("default") == []


# =============================================================================
# Networks Endpoints (networks.py)
# =============================================================================


async def test_networks_get_all_pins_spec_request_and_branches() -> None:
    """networks.get_all pins endpoint and covers response parsing branches."""
    net_payload = {"id": "net-1", "name": "Default Network", "vlanId": 1}
    session = _Session(
        [
            {"data": [net_payload]},
            [net_payload],
            None,
            {"total": 1},
        ]
    )
    client = _client(session)

    # 1. Wrapped list with params
    networks = await client.networks.get_all(
        "default", offset=0, limit=20, filter_str="vlanId.eq(1)"
    )
    assert len(networks) == 1
    assert isinstance(networks[0], Network)
    assert networks[0].id == "net-1"
    req1 = session.requests[0]
    assert req1["method"] == "GET"
    assert (
        req1["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/networks"
    )
    assert req1["params"] == {
        "offset": 0,
        "limit": 20,
        "filter": "vlanId.eq(1)",
    }

    # 2. Raw list with no params
    assert len(await client.networks.get_all("default")) == 1
    assert session.requests[1]["params"] is None

    # 3. None response
    assert await client.networks.get_all("default") == []

    # 4. Non-list fallback
    assert await client.networks.get_all("default") == []


async def test_networks_get_pins_spec_request_and_branches() -> None:
    """networks.get pins endpoint, unwrapped/list responses, and missing error."""
    net_dict = {"id": "net-1", "name": "LAN"}
    session = _Session(
        [
            {"data": net_dict},
            {"data": [net_dict]},
            {"data": []},
            {"data": 123},
            None,
            {"data": "non-dict"},
        ]
    )
    client = _client(session)

    # 1. Wrapped dict
    n1 = await client.networks.get("default", "net-1")
    assert n1.id == "net-1"
    req1 = session.requests[0]
    assert req1["method"] == "GET"
    assert (
        req1["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/networks/net-1"
    )

    # 2. List response
    n2 = await client.networks.get("default", "net-1")
    assert n2.id == "net-1"

    # 3. Empty list
    with pytest.raises(ValueError, match="Network missing not found"):
        await client.networks.get("default", "missing")

    # 4. Non-dict/non-list
    with pytest.raises(ValueError, match="Network invalid not found"):
        await client.networks.get("default", "invalid")
    with pytest.raises(ValueError, match="Network none not found"):
        await client.networks.get("default", "none")


@pytest.mark.xfail(
    strict=True,
    reason=(
        "networks.create sends legacy dhcpEnabled; "
        "spec createNetwork requires a management-specific object"
    ),
)
async def test_networks_create_pins_spec_request() -> None:
    """networks.create pins POST request against spec."""
    session = _Session([{"id": "net-1", "name": "LAN"}])
    client = _client(session)

    await client.networks.create(
        "default",
        name="LAN",
        vlan_id=10,
        management="GATEWAY",
        enabled=True,
        ipv4Configuration={
            "hostIpAddress": "192.168.10.1",
            "prefixLength": 24,
            "autoScaleEnabled": False,
        },
        cellularBackupEnabled=False,
        internetAccessEnabled=True,
        isolationEnabled=False,
    )
    req = session.requests[0]
    assert req["method"] == "POST"
    assert (
        req["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/networks"
    )
    assert req["json"] == {
        "name": "LAN",
        "vlanId": 10,
        "management": "GATEWAY",
        "enabled": True,
        "ipv4Configuration": {
            "hostIpAddress": "192.168.10.1",
            "prefixLength": 24,
            "autoScaleEnabled": False,
        },
        "cellularBackupEnabled": False,
        "internetAccessEnabled": True,
        "isolationEnabled": False,
    }


async def test_networks_create_response_parsing_and_branches() -> None:
    """networks.create covers response parsing, optional params, and failure."""
    net_dict = {"id": "net-1", "name": "Guest"}
    session = _Session(
        [
            {"data": net_dict},  # 1. Wrapped response with vlan_id and subnet
            net_dict,  # 2. Raw response with dhcp_enabled=False and kwargs
            None,  # 3. Failure
            {"data": "non-dict"},  # 4. Result not dict
        ]
    )
    client = _client(session)

    # 1. Wrapped response with vlan_id and subnet
    res1 = await client.networks.create(
        "default",
        name="Guest",
        vlan_id=20,
        subnet="192.168.20.0/24",
    )
    assert res1.id == "net-1"
    req1 = session.requests[0]
    assert req1["method"] == "POST"
    assert req1["url"] == (
        "https://192.168.1.1/proxy/network/integration/v1/sites/default/networks"
    )

    # 2. Raw response with dhcp_enabled=False and kwargs
    res2 = await client.networks.create(
        "default",
        name="IoT",
        dhcp_enabled=False,
        management="UNMANAGED",
        enabled=True,
        vlanId=20,
    )
    assert res2.id == "net-1"
    assert session.requests[1]["method"] == "POST"
    assert session.requests[1]["url"] == req1["url"]

    # 3. Failure
    with pytest.raises(ValueError, match="Failed to create network"):
        await client.networks.create("default", name="Fail")
    with pytest.raises(ValueError, match="Failed to create network"):
        await client.networks.create("default", name="Fail")


async def test_networks_update_pins_spec_request_and_branches() -> None:
    """networks.update pins PUT request and covers branches."""
    net_dict = {"id": "net-1", "name": "Updated"}
    session = _Session(
        [
            {"data": net_dict},
            net_dict,
            None,
            {"data": "non-dict"},
        ]
    )
    client = _client(session)

    # 1. Wrapped response
    res1 = await client.networks.update(
        "default",
        "net-1",
        name="Updated",
        vlanId=10,
        management="UNMANAGED",
        enabled=True,
    )
    assert res1.id == "net-1"
    req1 = session.requests[0]
    assert req1["method"] == "PUT"
    assert (
        req1["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/networks/net-1"
    )
    assert req1["json"] == {
        "name": "Updated",
        "vlanId": 10,
        "management": "UNMANAGED",
        "enabled": True,
    }

    # 2. Raw dict
    res2 = await client.networks.update(
        "default",
        "net-1",
        name="Updated",
        vlanId=10,
        management="UNMANAGED",
        enabled=False,
    )
    assert res2.id == "net-1"

    # 3. Failure
    with pytest.raises(ValueError, match="Failed to update network"):
        await client.networks.update(
            "default",
            "net-1",
            name="Updated",
            vlanId=10,
            management="UNMANAGED",
            enabled=True,
        )
    with pytest.raises(ValueError, match="Failed to update network"):
        await client.networks.update(
            "default",
            "net-1",
            name="Updated",
            vlanId=10,
            management="UNMANAGED",
            enabled=True,
        )


async def test_networks_delete_pins_spec_request() -> None:
    """networks.delete pins DELETE request."""
    session = _Session([None])
    client = _client(session)

    assert await client.networks.delete("default", "net-1") is True
    req = session.requests[0]
    assert req["method"] == "DELETE"
    assert (
        req["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/networks/net-1"
    )


async def test_networks_get_references_pins_spec_request_and_branches() -> None:
    """networks.get_references pins GET endpoint and covers dict fallback."""
    ref_data = {"wifiBroadcasts": ["wifi-1"], "firewallPolicies": []}
    session = _Session(
        [
            {"data": ref_data},  # 1. Wrapped dict
            ref_data,  # 2. Raw dict
            None,  # 3. Non-dict fallback
            {"data": "non-dict"},  # 4. Data not dict
        ]
    )
    client = _client(session)

    # 1. Wrapped dict
    r1 = await client.networks.get_references("default", "net-1")
    assert r1 == ref_data
    req1 = session.requests[0]
    assert req1["method"] == "GET"
    assert (
        req1["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/networks/net-1/references"
    )

    # 2. Raw dict
    assert await client.networks.get_references("default", "net-1") == ref_data

    # 3. Non-dict fallback
    assert await client.networks.get_references("default", "net-1") == {}

    # 4. Data not dict fallback
    assert await client.networks.get_references("default", "net-1") == {}


# =============================================================================
# Traffic Matching & DPI Endpoints (traffic.py)
# =============================================================================


async def test_traffic_get_all_lists_pins_spec_request_and_branches() -> None:
    """traffic.get_all_lists pins endpoint, limit capping, and branches."""
    list_payload = {
        "id": "list-1",
        "name": "Block Ports",
        "type": "PORTS",
        "entries": ["80", "443"],
    }
    session = _Session(
        [
            {"data": [list_payload]},
            [list_payload],
            None,
            {"not_list": 1},
        ]
    )
    client = _client(session)

    # 1. Wrapped list with params
    lists = await client.traffic.get_all_lists(
        "default", offset=0, limit=300, filter_str="type.eq('PORTS')"
    )
    assert len(lists) == 1
    assert isinstance(lists[0], TrafficMatchingList)
    assert lists[0].id == "list-1"
    req1 = session.requests[0]
    assert req1["method"] == "GET"
    assert (
        req1["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/traffic-matching-lists"
    )
    assert req1["params"] == {
        "offset": 0,
        "limit": 200,
        "filter": "type.eq('PORTS')",
    }

    # 2. Raw list with no params
    assert len(await client.traffic.get_all_lists("default")) == 1
    assert session.requests[1]["params"] is None

    # 3. None response
    assert await client.traffic.get_all_lists("default") == []

    # 4. Non-list fallback
    assert await client.traffic.get_all_lists("default") == []


async def test_traffic_get_list_pins_spec_request_and_branches() -> None:
    """traffic.get_list pins endpoint, unwrapped/list responses, and missing error."""
    list_dict = {"id": "list-1", "name": "Web", "type": "PORTS"}
    session = _Session(
        [
            {"data": list_dict},
            {"data": [list_dict]},
            {"data": []},
            {"data": 123},
            None,
            {"data": "non-dict"},
        ]
    )
    client = _client(session)

    # 1. Wrapped dict
    l1 = await client.traffic.get_list("default", "list-1")
    assert l1.id == "list-1"
    req1 = session.requests[0]
    assert req1["method"] == "GET"
    assert (
        req1["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/traffic-matching-lists/list-1"
    )

    # 2. List response
    l2 = await client.traffic.get_list("default", "list-1")
    assert l2.id == "list-1"

    # 3. Empty list
    with pytest.raises(ValueError, match="Traffic matching list missing not found"):
        await client.traffic.get_list("default", "missing")

    # 4. Non-dict/non-list
    with pytest.raises(ValueError, match="Traffic matching list invalid not found"):
        await client.traffic.get_list("default", "invalid")
    with pytest.raises(ValueError, match="Traffic matching list none not found"):
        await client.traffic.get_list("default", "none")


@pytest.mark.xfail(
    strict=True,
    reason=(
        "traffic.create_list sends entries; spec createTrafficMatchingList "
        "expects items"
    ),
)
async def test_traffic_create_list_pins_spec_request() -> None:
    """traffic.create_list pins POST request against spec."""
    session = _Session([{"id": "list-1", "name": "port-list", "type": "PORTS"}])
    client = _client(session)

    await client.traffic.create_list(
        "default",
        name="port-list",
        list_type=TrafficMatchingType.PORTS,
        entries=["80"],
    )
    req = session.requests[0]
    assert req["method"] == "POST"
    assert (
        req["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/traffic-matching-lists"
    )
    assert req["json"] == {
        "name": "port-list",
        "type": "PORTS",
        "items": [{"type": "PORT_NUMBER", "value": 80}],
    }


async def test_traffic_create_list_response_parsing_and_branches() -> None:
    """traffic.create_list covers response parsing, description, and failure."""
    list_dict = {
        "id": "list-1",
        "name": "Custom",
        "type": "IPV4_ADDRESSES",
        "entries": ["10.0.0.1"],
    }
    session = _Session(
        [
            {"data": list_dict},  # 1. Wrapped response with description
            list_dict,  # 2. Raw response without description or entries
            None,  # 3. Failure
            {"data": "non-dict"},  # 4. Result not dict
        ]
    )
    client = _client(session)

    # 1. Wrapped response with description
    res1 = await client.traffic.create_list(
        "default",
        name="Custom",
        list_type=TrafficMatchingType.IPV4_ADDRESSES,
        entries=["10.0.0.1"],
        description="Block IP",
    )
    assert res1.id == "list-1"
    req1 = session.requests[0]
    assert req1["method"] == "POST"
    assert req1["url"] == (
        "https://192.168.1.1/proxy/network/integration/v1/sites/default/traffic-matching-lists"
    )

    # 2. Raw response without description or entries
    res2 = await client.traffic.create_list(
        "default",
        name="Empty",
        list_type=TrafficMatchingType.PORTS,
    )
    assert res2.id == "list-1"
    assert session.requests[1]["method"] == "POST"
    assert session.requests[1]["url"] == req1["url"]

    # 3. Failure
    with pytest.raises(ValueError, match="Failed to create traffic matching list"):
        await client.traffic.create_list(
            "default", name="Fail", list_type=TrafficMatchingType.PORTS
        )
    with pytest.raises(ValueError, match="Failed to create traffic matching list"):
        await client.traffic.create_list(
            "default", name="Fail", list_type=TrafficMatchingType.PORTS
        )


async def test_traffic_update_list_pins_spec_request_and_branches() -> None:
    """traffic.update_list pins PUT request and covers branches."""
    list_dict = {"id": "list-1", "name": "Updated", "type": "PORTS"}
    session = _Session(
        [
            {"data": list_dict},
            list_dict,
            None,
            {"data": "non-dict"},
        ]
    )
    client = _client(session)

    # 1. Wrapped response
    res1 = await client.traffic.update_list(
        "default",
        "list-1",
        name="Updated",
        type="PORTS",
        items=[{"type": "PORT_NUMBER", "value": 8080}],
    )
    assert res1.id == "list-1"
    req1 = session.requests[0]
    assert req1["method"] == "PUT"
    assert (
        req1["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/traffic-matching-lists/list-1"
    )
    assert req1["json"] == {
        "name": "Updated",
        "type": "PORTS",
        "items": [{"type": "PORT_NUMBER", "value": 8080}],
    }

    # 2. Raw dict
    res2 = await client.traffic.update_list(
        "default",
        "list-1",
        name="Updated2",
        type="PORTS",
        items=[{"type": "PORT_NUMBER", "value": 8080}],
    )
    assert res2.id == "list-1"

    # 3. Failure
    with pytest.raises(ValueError, match="Failed to update traffic matching list"):
        await client.traffic.update_list(
            "default",
            "list-1",
            name="Updated",
            type="PORTS",
            items=[{"type": "PORT_NUMBER", "value": 8080}],
        )
    with pytest.raises(ValueError, match="Failed to update traffic matching list"):
        await client.traffic.update_list(
            "default",
            "list-1",
            name="Updated",
            type="PORTS",
            items=[{"type": "PORT_NUMBER", "value": 8080}],
        )


async def test_traffic_delete_list_pins_spec_request() -> None:
    """traffic.delete_list pins DELETE request."""
    session = _Session([None])
    client = _client(session)

    assert await client.traffic.delete_list("default", "list-1") is True
    req = session.requests[0]
    assert req["method"] == "DELETE"
    assert (
        req["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/traffic-matching-lists/list-1"
    )


async def test_traffic_get_dpi_categories_pins_spec_request_and_branches() -> None:
    """traffic.get_dpi_categories pins endpoint, limit capping, and branches."""
    # Spec example: id 3, "Network protocols". The spec types id as an integer;
    # the model takes a string, which test_dpi_parses_spec_integer_ids covers.
    cat_payload = {"id": "3", "name": "Network protocols"}
    session = _Session(
        [
            {"data": [cat_payload]},
            [cat_payload],
            None,
            {},
        ]
    )
    client = _client(session)

    # 1. Wrapped list with params
    cats = await client.traffic.get_dpi_categories(
        offset=0, limit=250, filter_str="name.eq('Streaming Media')"
    )
    assert len(cats) == 1
    assert isinstance(cats[0], DPICategory)
    assert cats[0].id == "3"
    req1 = session.requests[0]
    assert req1["method"] == "GET"
    assert (
        req1["url"] == "https://192.168.1.1/proxy/network/integration/v1/dpi/categories"
    )
    assert req1["params"] == {
        "offset": 0,
        "limit": 200,
        "filter": "name.eq('Streaming Media')",
    }

    # 2. Raw list with no params
    assert len(await client.traffic.get_dpi_categories()) == 1
    assert session.requests[1]["params"] is None

    # 3. None response
    assert await client.traffic.get_dpi_categories() == []

    # 4. Non-list fallback
    assert await client.traffic.get_dpi_categories() == []


async def test_traffic_get_dpi_applications_pins_spec_request_and_branches() -> None:
    """traffic.get_dpi_applications pins endpoint, limit capping, and branches."""
    # Spec example: id 786435, "Adobe Express" (id typed as an integer in the spec).
    app_payload = {"id": "786435", "name": "Adobe Express"}
    session = _Session(
        [
            {"data": [app_payload]},
            [app_payload],
            None,
            {"not_list": True},
        ]
    )
    client = _client(session)

    # 1. Wrapped list with params
    apps = await client.traffic.get_dpi_applications(
        offset=5, limit=50, filter_str="categoryId.eq('cat-1')"
    )
    assert len(apps) == 1
    assert isinstance(apps[0], DPIApplication)
    assert apps[0].id == "786435"
    assert apps[0].name == "Adobe Express"
    req1 = session.requests[0]
    assert req1["method"] == "GET"
    assert (
        req1["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/dpi/applications"
    )
    assert req1["params"] == {
        "offset": 5,
        "limit": 50,
        "filter": "categoryId.eq('cat-1')",
    }

    # 2. Raw list with no params
    assert len(await client.traffic.get_dpi_applications()) == 1
    assert session.requests[1]["params"] is None

    # 3. None response
    assert await client.traffic.get_dpi_applications() == []

    # 4. Non-list fallback
    assert await client.traffic.get_dpi_applications() == []


async def test_traffic_get_countries_pins_spec_request_and_branches() -> None:
    """traffic.get_countries pins endpoint, limit capping, and branches."""
    country_payload = {"code": "US", "name": "United States"}
    session = _Session(
        [
            {"data": [country_payload]},
            [country_payload],
            None,
            123,
        ]
    )
    client = _client(session)

    # 1. Wrapped list with params
    countries = await client.traffic.get_countries(
        offset=0, limit=250, filter_str="code.eq('US')"
    )
    assert len(countries) == 1
    assert isinstance(countries[0], Country)
    assert countries[0].code == "US"
    req1 = session.requests[0]
    assert req1["method"] == "GET"
    assert req1["url"] == "https://192.168.1.1/proxy/network/integration/v1/countries"
    assert req1["params"] == {"offset": 0, "limit": 200, "filter": "code.eq('US')"}

    # 2. Raw list with no params
    assert len(await client.traffic.get_countries()) == 1
    assert session.requests[1]["params"] is None

    # 3. None response
    assert await client.traffic.get_countries() == []

    # 4. Non-list fallback
    assert await client.traffic.get_countries() == []


# =============================================================================
# Firewall Endpoints (firewall.py)
# =============================================================================


async def test_firewall_list_zones_pins_spec_request_and_branches() -> None:
    """firewall.list_zones pins endpoint and covers response parsing branches."""
    zone_payload = {
        "id": "zone-1",
        "name": "Internal",
        "siteId": "default",
        "networkIds": ["net-1"],
    }
    session = _Session(
        [
            {"data": [zone_payload]},
            [zone_payload],
            None,
            {"invalid": True},
        ]
    )
    client = _client(session)

    # 1. Wrapped list with params
    zones = await client.firewall.list_zones(
        "default", offset=0, limit=10, filter_str="name.eq('Internal')"
    )
    assert len(zones) == 1
    assert isinstance(zones[0], FirewallZone)
    assert zones[0].id == "zone-1"
    req1 = session.requests[0]
    assert req1["method"] == "GET"
    assert (
        req1["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/firewall/zones"
    )
    assert req1["params"] == {
        "offset": 0,
        "limit": 10,
        "filter": "name.eq('Internal')",
    }

    # 2. Raw list with no params
    assert len(await client.firewall.list_zones("default")) == 1
    assert session.requests[1]["params"] is None

    # 3. None response
    assert await client.firewall.list_zones("default") == []

    # 4. Non-list fallback
    assert await client.firewall.list_zones("default") == []


async def test_firewall_get_zone_pins_spec_request_and_branches() -> None:
    """firewall.get_zone pins endpoint, unwrapped/list responses, and missing error."""
    zone_dict = {"id": "zone-1", "name": "Internal"}
    session = _Session(
        [
            {"data": zone_dict},
            {"data": [zone_dict]},
            {"data": []},
            {"data": 123},
            None,
            {"data": "non-dict"},
        ]
    )
    client = _client(session)

    # 1. Wrapped dict
    z1 = await client.firewall.get_zone("default", "zone-1")
    assert z1.id == "zone-1"
    req1 = session.requests[0]
    assert req1["method"] == "GET"
    assert (
        req1["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/firewall/zones/zone-1"
    )

    # 2. List response
    z2 = await client.firewall.get_zone("default", "zone-1")
    assert z2.id == "zone-1"

    # 3. Empty list
    with pytest.raises(ValueError, match="Firewall zone missing not found"):
        await client.firewall.get_zone("default", "missing")

    # 4. Non-dict/non-list
    with pytest.raises(ValueError, match="Firewall zone invalid not found"):
        await client.firewall.get_zone("default", "invalid")
    with pytest.raises(ValueError, match="Firewall zone none not found"):
        await client.firewall.get_zone("default", "none")


async def test_firewall_create_zone_pins_spec_request_and_branches() -> None:
    """firewall.create_zone pins POST request against spec and covers branches."""
    zone_dict = {
        "id": "zone-new",
        "name": "Guest Zone",
        "networkIds": ["net-1"],
    }
    session = _Session(
        [
            {"data": zone_dict},  # 1. With networkIds kwargs
            zone_dict,  # 2. Empty networkIds
            None,  # 3. Failure
            {"data": "non-dict"},  # 4. Result not dict
        ]
    )
    client = _client(session)

    # 1. With networkIds kwargs matching spec
    res1 = await client.firewall.create_zone(
        "default",
        name="Guest Zone",
        networkIds=["net-1"],
    )
    assert res1.id == "zone-new"
    req1 = session.requests[0]
    assert req1["method"] == "POST"
    assert (
        req1["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/firewall/zones"
    )
    assert req1["json"] == {"name": "Guest Zone", "networkIds": ["net-1"]}

    # 2. Isolated zone with empty networkIds
    res2 = await client.firewall.create_zone(
        "default", name="Isolated Zone", networkIds=[]
    )
    assert res2.id == "zone-new"
    req2 = session.requests[1]
    assert req2["json"] == {"name": "Isolated Zone", "networkIds": []}

    # 3. Failure
    with pytest.raises(ValueError, match="Failed to create firewall zone"):
        await client.firewall.create_zone("default", name="Fail", networkIds=[])
    with pytest.raises(ValueError, match="Failed to create firewall zone"):
        await client.firewall.create_zone("default", name="Fail", networkIds=[])


async def test_firewall_update_zone_pins_spec_request_and_branches() -> None:
    """firewall.update_zone pins PUT request and covers branches."""
    zone_dict = {"id": "zone-1", "name": "Updated Zone"}
    session = _Session(
        [
            {"data": zone_dict},
            zone_dict,
            None,
            {"data": "non-dict"},
        ]
    )
    client = _client(session)

    # 1. Wrapped response
    res1 = await client.firewall.update_zone(
        "default", "zone-1", name="Updated Zone", networkIds=["net-2"]
    )
    assert res1.id == "zone-1"
    req1 = session.requests[0]
    assert req1["method"] == "PUT"
    assert (
        req1["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/firewall/zones/zone-1"
    )
    assert req1["json"] == {"name": "Updated Zone", "networkIds": ["net-2"]}

    # 2. Raw dict
    res2 = await client.firewall.update_zone(
        "default", "zone-1", name="Updated Zone", networkIds=[]
    )
    assert res2.id == "zone-1"

    # 3. Failure
    with pytest.raises(ValueError, match="Failed to update firewall zone"):
        await client.firewall.update_zone(
            "default", "zone-1", name="Updated Zone", networkIds=[]
        )
    with pytest.raises(ValueError, match="Failed to update firewall zone"):
        await client.firewall.update_zone(
            "default", "zone-1", name="Updated Zone", networkIds=[]
        )


async def test_firewall_delete_zone_pins_spec_request() -> None:
    """firewall.delete_zone pins DELETE request."""
    session = _Session([None])
    client = _client(session)

    assert await client.firewall.delete_zone("default", "zone-1") is True
    req = session.requests[0]
    assert req["method"] == "DELETE"
    assert (
        req["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/firewall/zones/zone-1"
    )


async def test_firewall_get_rule_pins_spec_request_and_branches() -> None:
    """firewall.get_rule pins endpoint, unwrapped/list responses, and missing error."""
    rule_dict = {"id": "rule-1", "name": "Drop Rule", "action": "drop"}
    session = _Session(
        [
            {"data": rule_dict},
            {"data": [rule_dict]},
            {"data": []},
            {"data": 123},
            None,
            {"data": "non-dict"},
        ]
    )
    client = _client(session)

    # 1. Wrapped dict
    r1 = await client.firewall.get_rule("default", "rule-1")
    assert r1.id == "rule-1"
    req1 = session.requests[0]
    assert req1["method"] == "GET"
    assert (
        req1["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/firewall/policies/rule-1"
    )

    # 2. List response
    r2 = await client.firewall.get_rule("default", "rule-1")
    assert r2.id == "rule-1"

    # 3. Empty list
    with pytest.raises(ValueError, match="Firewall rule missing not found"):
        await client.firewall.get_rule("default", "missing")

    # 4. Non-dict/non-list
    with pytest.raises(ValueError, match="Firewall rule invalid not found"):
        await client.firewall.get_rule("default", "invalid")
    with pytest.raises(ValueError, match="Firewall rule none not found"):
        await client.firewall.get_rule("default", "none")


@pytest.mark.xfail(
    strict=True,
    reason=(
        "firewall.create_rule sends legacy flat fields (action, protocol, "
        "sourceZoneId, destinationZoneId); spec createFirewallPolicy expects "
        "action object, source/destination zone objects, ipProtocolScope, "
        "enabled and loggingEnabled"
    ),
)
async def test_firewall_create_rule_pins_spec_request() -> None:
    """firewall.create_rule pins POST request against spec."""
    session = _Session([{"id": "rule-1", "name": "block-rule"}])
    client = _client(session)

    await client.firewall.create_rule(
        "default",
        name="block-rule",
        action="drop",
        source_zone_id="zone-1",
        destination_zone_id="zone-2",
    )
    req = session.requests[0]
    assert req["method"] == "POST"
    assert (
        req["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/firewall/policies"
    )
    assert req["json"] == {
        "name": "block-rule",
        "action": {"type": "BLOCK"},
        "source": {"zoneId": "zone-1"},
        "destination": {"zoneId": "zone-2"},
        "ipProtocolScope": {"ipVersion": "IPV4"},
        "enabled": True,
        "loggingEnabled": False,
    }


async def test_firewall_create_rule_response_parsing_and_branches() -> None:
    """firewall.create_rule covers response parsing, parameters, and failure."""
    rule_dict = {"id": "rule-1", "name": "Allow Web", "action": "accept"}
    session = _Session(
        [
            {"data": rule_dict},  # 1. Wrapped response with zones and kwargs
            rule_dict,  # 2. Raw response without zones
            None,  # 3. Failure
            {"data": "non-dict"},  # 4. Result not dict
        ]
    )
    client = _client(session)

    # 1. Wrapped response with zones and kwargs
    res1 = await client.firewall.create_rule(
        "default",
        name="Allow Web",
        action="accept",
        protocol="tcp",
        source_zone_id="z-1",
        destination_zone_id="z-2",
        loggingEnabled=False,
    )
    assert res1.id == "rule-1"
    req1 = session.requests[0]
    assert req1["method"] == "POST"
    assert req1["url"] == (
        "https://192.168.1.1/proxy/network/integration/v1/sites/default/firewall/policies"
    )

    # 2. Raw response without zones
    res2 = await client.firewall.create_rule("default", name="Default Rule")
    assert res2.id == "rule-1"
    assert session.requests[1]["method"] == "POST"
    assert session.requests[1]["url"] == req1["url"]

    # 3. Failure
    with pytest.raises(ValueError, match="Failed to create firewall rule"):
        await client.firewall.create_rule("default", name="Fail")
    with pytest.raises(ValueError, match="Failed to create firewall rule"):
        await client.firewall.create_rule("default", name="Fail")


async def test_firewall_delete_rule_pins_spec_request() -> None:
    """firewall.delete_rule pins DELETE request."""
    session = _Session([None])
    client = _client(session)

    assert await client.firewall.delete_rule("default", "rule-1") is True
    req = session.requests[0]
    assert req["method"] == "DELETE"
    assert (
        req["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/firewall/policies/rule-1"
    )


async def test_firewall_patch_rule_pins_spec_request_and_branches() -> None:
    """firewall.patch_rule pins PATCH request and covers branches."""
    rule_dict = {"id": "rule-1", "name": "Rule 1", "logging": True}
    session = _Session(
        [
            {"data": rule_dict},
            rule_dict,
            None,
            {"data": "non-dict"},
        ]
    )
    client = _client(session)

    # 1. Wrapped response
    res1 = await client.firewall.patch_rule("default", "rule-1", logging_enabled=True)
    assert res1.id == "rule-1"
    req1 = session.requests[0]
    assert req1["method"] == "PATCH"
    assert (
        req1["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/firewall/policies/rule-1"
    )
    assert req1["json"] == {"loggingEnabled": True}

    # 2. Raw dict
    res2 = await client.firewall.patch_rule("default", "rule-1", logging_enabled=False)
    assert res2.id == "rule-1"

    # 3. Failure
    with pytest.raises(ValueError, match="Failed to patch firewall rule"):
        await client.firewall.patch_rule("default", "rule-1", logging_enabled=True)


async def test_firewall_policy_ordering_pins_spec_request_and_branches() -> None:
    """firewall.get_policy_ordering and update_policy_ordering pin requests."""
    ordering_data = {
        "orderedFirewallPolicyIds": {
            "beforeSystemDefined": ["p1"],
            "afterSystemDefined": ["p2"],
        }
    }
    session = _Session(
        [
            {"data": ordering_data},  # 1. get_policy_ordering wrapped
            ordering_data,  # 2. get_policy_ordering raw
            None,  # 3. get_policy_ordering failure
            {"data": ordering_data},  # 4. update_policy_ordering dict
            ordering_data,  # 5. update_policy_ordering model instance
            None,  # 6. update_policy_ordering failure
        ]
    )
    client = _client(session)

    # 1. get_policy_ordering wrapped
    ord1 = await client.firewall.get_policy_ordering(
        "default",
        source_firewall_zone_id="z-src",
        destination_firewall_zone_id="z-dst",
    )
    assert ord1.ordered_firewall_policy_ids.before_system_defined == ["p1"]
    req1 = session.requests[0]
    assert req1["method"] == "GET"
    assert (
        req1["url"]
        == "https://192.168.1.1/proxy/network/integration/v1/sites/default/firewall/policies/ordering"
    )
    assert req1["params"] == {
        "sourceFirewallZoneId": "z-src",
        "destinationFirewallZoneId": "z-dst",
    }

    # 2. get_policy_ordering raw
    ord2 = await client.firewall.get_policy_ordering(
        "default",
        source_firewall_zone_id="z-src",
        destination_firewall_zone_id="z-dst",
    )
    assert ord2.ordered_firewall_policy_ids.after_system_defined == ["p2"]

    # 3. get_policy_ordering failure
    with pytest.raises(ValueError, match="Failed to get firewall policy ordering"):
        await client.firewall.get_policy_ordering(
            "default",
            source_firewall_zone_id="z-src",
            destination_firewall_zone_id="z-dst",
        )

    # 4. update_policy_ordering validation failure (missing beforeSystemDefined)
    with pytest.raises(
        ValueError, match="needs both beforeSystemDefined and afterSystemDefined"
    ):
        await client.firewall.update_policy_ordering(
            "default",
            source_firewall_zone_id="z-src",
            destination_firewall_zone_id="z-dst",
            ordered_firewall_policy_ids={"afterSystemDefined": ["p2"]},
        )

    # 5. update_policy_ordering with complete dict
    uord1 = await client.firewall.update_policy_ordering(
        "default",
        source_firewall_zone_id="z-src",
        destination_firewall_zone_id="z-dst",
        ordered_firewall_policy_ids={
            "beforeSystemDefined": ["p1"],
            "afterSystemDefined": ["p2"],
        },
    )
    assert uord1.ordered_firewall_policy_ids.before_system_defined == ["p1"]
    req4 = session.requests[3]
    assert req4["method"] == "PUT"
    assert req4["params"] == {
        "sourceFirewallZoneId": "z-src",
        "destinationFirewallZoneId": "z-dst",
    }
    assert req4["json"] == {
        "orderedFirewallPolicyIds": {
            "beforeSystemDefined": ["p1"],
            "afterSystemDefined": ["p2"],
        }
    }

    # 6. update_policy_ordering with OrderedFirewallPolicyIds model instance
    model_obj = OrderedFirewallPolicyIds(
        beforeSystemDefined=["p3"], afterSystemDefined=["p4"]
    )
    uord2 = await client.firewall.update_policy_ordering(
        "default",
        source_firewall_zone_id="z-src",
        destination_firewall_zone_id="z-dst",
        ordered_firewall_policy_ids=model_obj,
    )
    assert uord2.ordered_firewall_policy_ids.before_system_defined == ["p1"]
    req5 = session.requests[4]
    assert req5["json"] == {
        "orderedFirewallPolicyIds": {
            "beforeSystemDefined": ["p3"],
            "afterSystemDefined": ["p4"],
        }
    }

    # 7. update_policy_ordering failure
    with pytest.raises(ValueError, match="Failed to update firewall policy ordering"):
        await client.firewall.update_policy_ordering(
            "default",
            source_firewall_zone_id="z-src",
            destination_firewall_zone_id="z-dst",
            ordered_firewall_policy_ids=model_obj,
        )


@pytest.mark.parametrize("payload", [None, [], ["not-a-dict"], 123])
async def test_firewall_patch_rule_invalid_response(payload: Any) -> None:
    """Exercise extraction failures through the public PATCH method."""
    session = _Session([_Response(payload)])
    with pytest.raises(ValueError, match="Failed to patch firewall rule"):
        await _client(session).firewall.patch_rule(
            "default", "rule-1", logging_enabled=True
        )
    assert session.requests[0]["method"] == "PATCH"
    assert session.requests[0]["url"] == (
        "https://192.168.1.1/proxy/network/integration/v1/sites/default/"
        "firewall/policies/rule-1"
    )
    assert session.requests[0]["json"] == {"loggingEnabled": True}


async def test_firewall_patch_rule_list_response() -> None:
    """Exercise list extraction through the public PATCH method."""
    session = _Session(
        [[{"id": "rule-1", "name": "Rule", "action": {"type": "BLOCK"}}]]
    )
    result = await _client(session).firewall.patch_rule(
        "default", "rule-1", logging_enabled=True
    )
    assert result.id == "rule-1"
    assert result.action_type == "BLOCK"


# =============================================================================
# Error Mapping Tests (Shared across endpoints)
# =============================================================================


@pytest.mark.parametrize(
    ("status", "expected_exc"),
    [
        (404, UniFiNotFoundError),
        (500, UniFiResponseError),
    ],
)
async def test_endpoint_error_mapping(
    status: int, expected_exc: type[Exception]
) -> None:
    """Endpoints map HTTP 404/500 errors to UniFi exception types."""
    session = _Session([_Response("Error", status=status)])
    client = _client(session)

    with pytest.raises(expected_exc):
        await client.dns.get("default", "dns-1")

    session2 = _Session([_Response("Error", status=status)])
    client2 = _client(session2)
    with pytest.raises(expected_exc):
        await client2.acl.get("default", "rule-1")

    session3 = _Session([_Response("Error", status=status)])
    client3 = _client(session3)
    with pytest.raises(expected_exc):
        await client3.resources.get_wan_interfaces("default")

    session4 = _Session([_Response("Error", status=status)])
    client4 = _client(session4)
    with pytest.raises(expected_exc):
        await client4.networks.get("default", "net-1")

    session5 = _Session([_Response("Error", status=status)])
    client5 = _client(session5)
    with pytest.raises(expected_exc):
        await client5.traffic.get_list("default", "list-1")

    session6 = _Session([_Response("Error", status=status)])
    client6 = _client(session6)
    with pytest.raises(expected_exc):
        await client6.firewall.get_zone("default", "zone-1")


# =============================================================================
# Model Tests (dns.py, acl.py, traffic.py, firewall.py)
# =============================================================================


def test_models_dns_policy_branches() -> None:
    """DNSPolicy covers is_user_defined and field validation."""
    p_user = DNSPolicy(
        id="dns-1",
        type=DNSRecordType.A_RECORD,
        metadata=DNSPolicyMetadata(origin="USER_DEFINED"),
        ipv4Address="1.1.1.1",
        ttlSeconds=300,
    )
    assert p_user.is_user_defined is True
    assert p_user.ipv4_address == "1.1.1.1"
    assert p_user.ttl_seconds == 300

    p_system = DNSPolicy(
        id="dns-2",
        type="A_RECORD",
        metadata=DNSPolicyMetadata(origin="SYSTEM_DEFINED"),
    )
    assert p_system.is_user_defined is False

    p_none_meta = DNSPolicy(id="dns-3", type="CNAME_RECORD", metadata=None)
    assert p_none_meta.is_user_defined is False

    p_empty_origin = DNSPolicy(
        id="dns-4", type="TXT_RECORD", metadata=DNSPolicyMetadata(origin=None)
    )
    assert p_empty_origin.is_user_defined is False


def test_models_acl_branches() -> None:
    """ACLRule and related models cover is_user_defined, filters, and fields."""
    r_no_meta = ACLRule(
        id="r-1",
        type=ACLRuleType.IPV4,
        name="Rule 1",
        action=ACLAction.BLOCK,
        index=0,
        metadata=None,
    )
    assert r_no_meta.is_user_defined is True

    r_user = ACLRule(
        id="r-2",
        type=ACLRuleType.MAC,
        name="Rule 2",
        action=ACLAction.ALLOW,
        index=1,
        metadata=ACLMetadata(origin=ACLMetadataOrigin.USER_DEFINED),
        enforcingDeviceFilter=ACLDeviceFilter(deviceIds=["dev-1"]),
        sourceFilter=ACLSourceFilter(
            networkIds=["net-1"],
            macAddresses=["aa:bb:cc:dd:ee:ff"],
            ipAddresses=["192.168.1.10"],
            portRanges=["80-443"],
        ),
        destinationFilter=ACLDestinationFilter(
            networkIds=["net-2"],
            macAddresses=["11:22:33:44:55:66"],
            ipAddresses=["10.0.0.1"],
            portRanges=["22"],
        ),
    )
    assert r_user.is_user_defined is True
    assert r_user.enforcing_device_filter.device_ids == ["dev-1"]
    assert r_user.source_filter.port_ranges == ["80-443"]

    r_sys = ACLRule(
        id="r-3",
        type=ACLRuleType.IPV4,
        name="Rule 3",
        action=ACLAction.BLOCK,
        index=2,
        metadata=ACLMetadata(origin=ACLMetadataOrigin.SYSTEM_DEFINED),
    )
    assert r_sys.is_user_defined is False

    ordering = ACLRuleOrdering(orderedAclRuleIds=["r-1", "r-2"])
    assert ordering.ordered_acl_rule_ids == ["r-1", "r-2"]


def test_models_traffic_branches() -> None:
    """TrafficMatchingList and DPI models cover is_user_defined and fields."""
    t_no_meta = TrafficMatchingList(
        id="t-1",
        type=TrafficMatchingType.PORTS,
        name="Ports",
        metadata=None,
    )
    assert t_no_meta.is_user_defined is True

    t_user = TrafficMatchingList(
        id="t-2",
        type=TrafficMatchingType.IPV4_ADDRESSES,
        name="IPs",
        entries=["1.2.3.4"],
        metadata=TrafficMetadata(origin=TrafficMetadataOrigin.USER_DEFINED),
    )
    assert t_user.is_user_defined is True
    assert t_user.entries == ["1.2.3.4"]

    t_sys = TrafficMatchingList(
        id="t-3",
        type=TrafficMatchingType.PORTS,
        name="Domains",
        metadata=TrafficMetadata(origin=TrafficMetadataOrigin.SYSTEM_DEFINED),
    )
    assert t_sys.is_user_defined is False

    # description and categoryId are model fields the spec doesn't have; this only
    # pins that the model still accepts them, not that the API sends them.
    cat = DPICategory(id="3", name="Network protocols", description="Desc")
    assert cat.name == "Network protocols"

    app = DPIApplication(
        id="786435", name="Adobe Express", categoryId="3", description="App Desc"
    )
    assert app.category_id == "3"

    country = Country(code="CA", name="Canada")
    assert country.code == "CA"


def test_models_firewall_branches() -> None:
    """FirewallRule covers action_type property and enums."""
    rule_str = FirewallRule(id="f-1", name="Rule 1", action="drop")
    assert rule_str.action_type == "drop"

    rule_cfg = FirewallRule(
        id="f-2",
        name="Rule 2",
        action=FirewallActionConfig(type="ALLOW", allowReturnTraffic=True),
    )
    assert rule_cfg.action_type == "ALLOW"

    assert FirewallAction.ACCEPT == "accept"
    assert FirewallAction.DENY == "DENY"
    assert FirewallProtocol.TCP == "tcp"
    assert FirewallProtocol.TCP_UDP == "tcp_udp"


async def test_resources_wan_filter_response_parsing() -> None:
    """Cover the filter branch without pinning the unsupported query parameter."""
    session = _Session([{"data": [{"id": "wan-1", "name": "Internet 1"}]}])
    result = await _client(session).resources.get_wan_interfaces(
        "default", offset=0, limit=10, filter_str="name.eq('Internet 1')"
    )
    assert result[0].name == "Internet 1"
    assert session.requests[0]["method"] == "GET"
    assert session.requests[0]["url"] == (
        "https://192.168.1.1/proxy/network/integration/v1/sites/default/wans"
    )


@pytest.mark.xfail(
    strict=True,
    reason=(
        "resources.get_wan_interfaces sends filter; spec getWansOverviewPage "
        "accepts only offset and limit"
    ),
)
async def test_resources_wan_filter_pins_spec_request() -> None:
    """A spec-correct implementation omits the unsupported filter parameter."""
    session = _Session([{"data": [{"id": "wan-1", "name": "Internet 1"}]}])
    result = await _client(session).resources.get_wan_interfaces(
        "default", offset=0, limit=10, filter_str="name.eq('Internet 1')"
    )
    assert result[0].name == "Internet 1"
    assert session.requests[0]["params"] == {"offset": 0, "limit": 10}


# UUIDs and payloads below follow Network v10.6.106 response schemas.
_MODEL_ID = "ffcdb32c-6278-4364-8947-df4f77118df8"
_DEVICE_ID = "dfb21062-8ea0-4dca-b1d8-1eb3da00e58b"
_METADATA = {"origin": "USER_DEFINED"}


@pytest.mark.parametrize(
    ("model", "payload", "fields"),
    [
        (DNSPolicyMetadata, _METADATA, {"origin": "USER_DEFINED"}),
        (
            DNSPolicy,
            {
                "id": _MODEL_ID,
                "type": "A_RECORD",
                "enabled": True,
                "metadata": _METADATA,
                "domain": "example.com",
                "ipv4Address": "192.168.1.10",
                "ttlSeconds": 300,
            },
            {
                "ipv4_address": "192.168.1.10",
                "ttl_seconds": 300,
                "domain": "example.com",
                "is_user_defined": True,
            },
        ),
        (ACLMetadata, _METADATA, {"origin": ACLMetadataOrigin.USER_DEFINED}),
        (
            ACLDeviceFilter,
            {"type": "DEVICES", "deviceIds": [_DEVICE_ID]},
            {"device_ids": [_DEVICE_ID]},
        ),
        (
            ACLSourceFilter,
            {"type": "NETWORKS", "networkIds": [_MODEL_ID], "portFilter": [80]},
            {"network_ids": [_MODEL_ID], "portFilter": [80]},
        ),
        (
            ACLDestinationFilter,
            {"type": "MAC_ADDRESSES", "macAddresses": ["00:11:22:33:44:55"]},
            {"mac_addresses": ["00:11:22:33:44:55"]},
        ),
        (
            ACLRule,
            {
                "id": _MODEL_ID,
                "type": "IPV4",
                "enabled": True,
                "name": "Allow web",
                "action": "ALLOW",
                "index": 2,
                "metadata": _METADATA,
                "enforcingDeviceFilter": {"type": "DEVICES", "deviceIds": [_DEVICE_ID]},
                "sourceFilter": {"type": "NETWORKS", "networkIds": [_MODEL_ID]},
                "destinationFilter": {"type": "PORTS", "portFilter": [80]},
            },
            {
                "enforcing_device_filter.device_ids": [_DEVICE_ID],
                "source_filter.network_ids": [_MODEL_ID],
                "destination_filter.portFilter": [80],
                "is_user_defined": True,
            },
        ),
        (
            ACLRuleOrdering,
            {"orderedAclRuleIds": [_MODEL_ID]},
            {"ordered_acl_rule_ids": [_MODEL_ID]},
        ),
        (TrafficMetadata, _METADATA, {"origin": TrafficMetadataOrigin.USER_DEFINED}),
        (
            TrafficMatchingList,
            {
                "id": _MODEL_ID,
                "type": "PORTS",
                "name": "Web ports",
                "items": [{"type": "PORT_NUMBER", "value": 80}],
            },
            {
                "type": TrafficMatchingType.PORTS,
                "name": "Web ports",
                "items": [{"type": "PORT_NUMBER", "value": 80}],
            },
        ),
        (Country, {"code": "CA", "name": "Canada"}, {"code": "CA", "name": "Canada"}),
        (
            Network,
            {
                "id": _MODEL_ID,
                "name": "LAN",
                "management": "UNMANAGED",
                "enabled": True,
                "default": False,
                "vlanId": 20,
                "metadata": _METADATA,
            },
            {"vlan_id": 20, "enabled": True, "management": "UNMANAGED"},
        ),
        (
            FirewallZone,
            {
                "id": _MODEL_ID,
                "name": "Internal",
                "networkIds": [_DEVICE_ID],
                "metadata": _METADATA,
            },
            {"network_ids": [_DEVICE_ID], "name": "Internal"},
        ),
        (
            FirewallActionConfig,
            {"type": "ALLOW", "allowReturnTraffic": True},
            {"type": "ALLOW", "allow_return_traffic": True},
        ),
        (
            FirewallRule,
            {
                "id": _MODEL_ID,
                "name": "Allow web",
                "enabled": True,
                "index": 0,
                "metadata": _METADATA,
                "action": {"type": "ALLOW", "allowReturnTraffic": True},
                "source": {"zoneId": _MODEL_ID},
                "destination": {"zoneId": _DEVICE_ID},
                "ipProtocolScope": {"ipVersion": "IPV4"},
                "loggingEnabled": True,
            },
            {
                "action_type": "ALLOW",
                "action.allow_return_traffic": True,
                "source": {"zoneId": _MODEL_ID},
                "loggingEnabled": True,
            },
        ),
        (
            OrderedFirewallPolicyIds,
            {"beforeSystemDefined": [_MODEL_ID], "afterSystemDefined": [_DEVICE_ID]},
            {
                "before_system_defined": [_MODEL_ID],
                "after_system_defined": [_DEVICE_ID],
            },
        ),
        (
            FirewallPolicyOrdering,
            {
                "orderedFirewallPolicyIds": {
                    "beforeSystemDefined": [_MODEL_ID],
                    "afterSystemDefined": [_DEVICE_ID],
                }
            },
            {
                "ordered_firewall_policy_ids.before_system_defined": [_MODEL_ID],
                "ordered_firewall_policy_ids.after_system_defined": [_DEVICE_ID],
            },
        ),
        (
            WANInterface,
            {"id": _MODEL_ID, "name": "Internet 1"},
            {"id": _MODEL_ID, "name": "Internet 1"},
        ),
        (
            VPNTunnel,
            {"id": _MODEL_ID, "name": "Branch", "type": "IPSEC", "metadata": _METADATA},
            {"name": "Branch", "type": "IPSEC"},
        ),
        (
            VPNServer,
            {
                "id": _MODEL_ID,
                "name": "Remote",
                "type": "WIREGUARD",
                "enabled": True,
                "metadata": _METADATA,
            },
            {"name": "Remote", "type": "WIREGUARD", "enabled": True},
        ),
        (
            RADIUSProfile,
            {"id": _MODEL_ID, "name": "RADIUS", "metadata": _METADATA},
            {"id": _MODEL_ID, "name": "RADIUS"},
        ),
        (
            DeviceTag,
            {"id": _MODEL_ID, "name": "Core"},
            {"id": _MODEL_ID, "name": "Core"},
        ),
    ],
)
def test_models_parse_spec_shaped_responses(
    model: Any, payload: dict[str, Any], fields: dict[str, Any]
) -> None:
    """Validate complete spec-shaped objects and their supported aliases."""
    parsed = model.model_validate(payload)
    for path, expected in fields.items():
        actual = parsed
        for field in path.split("."):
            actual = getattr(actual, field)
        assert actual == expected


@pytest.mark.parametrize(
    ("model", "payload", "fields"),
    [
        (
            FirewallRule,
            {
                "id": "legacy-rule",
                "name": "Legacy",
                "siteId": "site-1",
                "sourceZoneId": "src",
                "destinationZoneId": "dst",
                "sourceAddress": "10.0.0.1",
                "destinationAddress": "10.0.0.2",
                "sourcePort": "80",
                "destinationPort": "443",
            },
            {
                "site_id": "site-1",
                "source_zone_id": "src",
                "destination_zone_id": "dst",
                "source_address": "10.0.0.1",
                "destination_address": "10.0.0.2",
                "source_port": "80",
                "destination_port": "443",
            },
        ),
        (
            Network,
            {
                "id": "legacy-net",
                "name": "Legacy",
                "siteId": "site-1",
                "vlanId": 20,
                "gatewayIp": "10.0.0.1",
                "dhcpEnabled": False,
                "dhcpStart": "10.0.0.10",
                "dhcpStop": "10.0.0.20",
                "dhcpLeaseTime": 3600,
                "domainName": "example.com",
                "igmpSnooping": True,
                "ipv6Enabled": True,
            },
            {
                "site_id": "site-1",
                "vlan_id": 20,
                "gateway_ip": "10.0.0.1",
                "dhcp_enabled": False,
                "dhcp_start": "10.0.0.10",
                "dhcp_stop": "10.0.0.20",
                "dhcp_lease_time": 3600,
                "domain_name": "example.com",
                "igmp_snooping": True,
                "ipv6_enabled": True,
            },
        ),
        (
            WANInterface,
            {
                "id": "wan",
                "name": "Legacy",
                "ipAddress": "10.0.0.1",
                "isPrimary": True,
                "isConnected": True,
                "uploadSpeed": 100,
                "downloadSpeed": 1000,
            },
            {
                "ip_address": "10.0.0.1",
                "is_primary": True,
                "is_connected": True,
                "upload_speed": 100,
                "download_speed": 1000,
            },
        ),
        (
            VPNTunnel,
            {
                "id": "vpn",
                "localNetwork": "10.0.0.0/24",
                "remoteNetwork": "10.0.1.0/24",
                "remoteIp": "192.0.2.1",
                "ikeVersion": 2,
            },
            {
                "local_network": "10.0.0.0/24",
                "remote_network": "10.0.1.0/24",
                "remote_ip": "192.0.2.1",
                "ike_version": 2,
            },
        ),
        (
            RADIUSProfile,
            {
                "id": "radius",
                "name": "Legacy",
                "authServer": "192.0.2.1",
                "authPort": 1814,
                "acctServer": "192.0.2.2",
                "acctPort": 1815,
            },
            {
                "auth_server": "192.0.2.1",
                "auth_port": 1814,
                "acct_server": "192.0.2.2",
                "acct_port": 1815,
            },
        ),
        (
            DeviceTag,
            {"id": "tag", "name": "Legacy", "deviceCount": 3},
            {"device_count": 3},
        ),
        (
            FirewallZone,
            {"id": "zone", "name": "Legacy", "siteId": "site"},
            {"site_id": "site"},
        ),
        (
            DPIApplication,
            {"id": "786435", "name": "Legacy", "categoryId": "3"},
            {"category_id": "3"},
        ),
        (
            ACLSourceFilter,
            {
                "networkIds": ["net"],
                "macAddresses": ["00:11:22:33:44:55"],
                "ipAddresses": ["192.0.2.1"],
                "portRanges": ["80-443"],
            },
            {
                "network_ids": ["net"],
                "mac_addresses": ["00:11:22:33:44:55"],
                "ip_addresses": ["192.0.2.1"],
                "port_ranges": ["80-443"],
            },
        ),
        (
            ACLDestinationFilter,
            {
                "networkIds": ["net"],
                "macAddresses": ["00:11:22:33:44:55"],
                "ipAddresses": ["192.0.2.1"],
                "portRanges": ["80-443"],
            },
            {
                "network_ids": ["net"],
                "mac_addresses": ["00:11:22:33:44:55"],
                "ip_addresses": ["192.0.2.1"],
                "port_ranges": ["80-443"],
            },
        ),
    ],
)
def test_models_parse_legacy_field_aliases(
    model: Any, payload: dict[str, Any], fields: dict[str, Any]
) -> None:
    """
    Characterization only, not a spec check.

    These aliases aren't in the Network v10.6.106 spec and no integration code
    reads them. The test pins what the models accept today, so dropping an alias
    in a later cleanup is a deliberate change. Delete the matching case when one
    is removed.
    """
    parsed = model.model_validate(payload)
    for field, expected in fields.items():
        assert getattr(parsed, field) == expected


@pytest.mark.parametrize(
    ("method", "identifier", "name"),
    [
        ("get_dpi_categories", 3, "Network protocols"),
        ("get_dpi_applications", 786435, "Adobe Express"),
    ],
)
@pytest.mark.xfail(
    strict=True,
    reason=(
        "DPI models require string IDs; spec DPI category/application IDs are integers"
    ),
)
async def test_dpi_parses_spec_integer_ids(
    method: str, identifier: int, name: str
) -> None:
    """A model fix must accept the spec's numeric identifiers."""
    session = _Session([{"data": [{"id": identifier, "name": name}]}])
    result = await getattr(_client(session).traffic, method)()
    assert result[0].id == identifier
    assert result[0].name == name


async def test_dns_update_a_record_pins_spec_request() -> None:
    """A complete A-record PUT exercises the ipv4Address branch."""
    payload = {
        "id": _MODEL_ID,
        "type": "A_RECORD",
        "enabled": False,
        "metadata": _METADATA,
        "domain": "example.com",
        "ipv4Address": "192.0.2.10",
        "ttlSeconds": 300,
    }
    session = _Session([payload])
    result = await _client(session).dns.update(
        "default",
        _MODEL_ID,
        record_type="A_RECORD",
        enabled=False,
        domain="example.com",
        ipv4_address="192.0.2.10",
        ttl_seconds=300,
    )
    assert result.ipv4_address == "192.0.2.10"
    assert result.ttl_seconds == 300
    assert session.requests[0]["method"] == "PUT"
    assert session.requests[0]["json"] == {
        "type": "A_RECORD",
        "enabled": False,
        "domain": "example.com",
        "ipv4Address": "192.0.2.10",
        "ttlSeconds": 300,
    }


async def test_dns_incomplete_body_passthrough_server_validation() -> None:
    """Deliberately send incomplete bodies: the server owns field validation.

    This is not a valid request example. It exercises omitted optional Python
    arguments and proves server rejection reaches callers as UniFiResponseError.
    """
    session = _Session(
        [_Response({"message": "invalid"}, status=400) for _ in range(2)]
    )
    client = _client(session)
    with pytest.raises(UniFiResponseError):
        await client.dns.create("default", record_type="TXT_RECORD")
    with pytest.raises(UniFiResponseError):
        await client.dns.update("default", _MODEL_ID)
    assert [request["method"] for request in session.requests] == ["POST", "PUT"]
