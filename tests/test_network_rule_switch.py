"""Tests for port forward and traffic rule switches."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.const import EntityCategory
from homeassistant.exceptions import HomeAssistantError

from custom_components.unifi_insights.api.exceptions import UniFiConnectionError
from custom_components.unifi_insights.const import DOMAIN
from custom_components.unifi_insights.network_rule_switch import (
    NETWORK_RULE_SWITCH_TYPES,
    PORT_FORWARD_SWITCH,
    TRAFFIC_RULE_SWITCH,
    UnifiInsightsNetworkRuleSwitch,
    UnifiInsightsNetworkRuleSwitchEntityDescription,
    discover_network_rule_switches,
)
from custom_components.unifi_insights.switch import async_setup_entry
from tests.fixtures.network_rule_responses import (
    port_forward_record,
    traffic_rule_record,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


@pytest.fixture
def mock_coordinator() -> MagicMock:
    """Create mock coordinator with port forward and traffic rule data."""
    coordinator = MagicMock()
    coordinator.protect_client = None
    coordinator.network_client = MagicMock()
    coordinator.network_client.base_url = "https://192.168.1.1"
    coordinator.port_forwards_available = MagicMock(return_value=True)
    coordinator.traffic_rules_available = MagicMock(return_value=True)
    coordinator.data = {
        "sites": {"site1": {"id": "site1", "name": "Default"}},
        "devices": {},
        "clients": {},
        "stats": {},
        "wifi": {},
        "firewall_rules": {},
        "policy_based_routes": {},
        "vpn_clients": {},
        "port_forwards": {
            "site1": {
                "pf1": port_forward_record(_id="pf1", name="Plex"),
            }
        },
        "traffic_rules": {
            "site1": {
                "tr1": traffic_rule_record(_id="tr1", description="Bedtime"),
            }
        },
        "protect": {
            "cameras": {},
            "lights": {},
            "sensors": {},
            "nvrs": {},
            "viewers": {},
            "chimes": {},
            "liveviews": {},
        },
    }
    return coordinator


@pytest.mark.asyncio
async def test_setup_entry_adds_port_forward_and_traffic_rule_switches(
    hass: HomeAssistant, mock_coordinator: MagicMock
) -> None:
    """Platform setup adds both port forward and traffic rule switches."""
    mock_entry = MagicMock()
    mock_entry.options = {}
    mock_entry.entry_id = "test_entry_id"
    mock_entry.runtime_data = MagicMock()
    mock_entry.runtime_data.coordinator = mock_coordinator

    async_add_entities = MagicMock()
    await async_setup_entry(hass, mock_entry, async_add_entities)

    entities = async_add_entities.call_args[0][0]
    rule_switches = [
        entity
        for entity in entities
        if isinstance(entity, UnifiInsightsNetworkRuleSwitch)
    ]
    assert len(rule_switches) == 2
    assert {e._rule_id for e in rule_switches} == {"pf1", "tr1"}


def test_discovery_skips_malformed_sites_records_and_non_bool_enabled(
    mock_coordinator: MagicMock,
) -> None:
    """Non-dict collections, non-dict records, and non-bool enabled are skipped."""
    mock_coordinator.data["port_forwards"] = {
        "site_not_dict": "not-a-dict",
        "site1": {
            "rule_not_dict": "not-a-dict",
            "rule_no_enabled": {"name": "No enabled"},
            "rule_str_enabled": {"name": "Str enabled", "enabled": "true"},
            "rule_int_enabled": {"name": "Int enabled", "enabled": 1},
            "rule_none_enabled": {"name": "None enabled", "enabled": None},
            "valid_rule": {"name": "Valid", "enabled": True},
        },
    }
    known_keys: set[tuple[Any, ...]] = set()
    entities = discover_network_rule_switches(mock_coordinator, known_keys)
    pf_entities = [e for e in entities if e.entity_description.key == "port_forward"]
    assert len(pf_entities) == 1
    assert pf_entities[0]._rule_id == "valid_rule"


@pytest.mark.asyncio
async def test_discovery_adds_new_rule_on_listener_tick_without_duplicates(
    hass: HomeAssistant, mock_coordinator: MagicMock
) -> None:
    """Coordinator update listener adds new entities without duplicates."""
    mock_entry = MagicMock()
    mock_entry.options = {}
    mock_entry.entry_id = "test_entry_id"
    mock_entry.runtime_data = MagicMock()
    mock_entry.runtime_data.coordinator = mock_coordinator

    async_add_entities = MagicMock()
    await async_setup_entry(hass, mock_entry, async_add_entities)

    first_added = async_add_entities.call_args[0][0]
    first_rules = [
        e for e in first_added if isinstance(e, UnifiInsightsNetworkRuleSwitch)
    ]
    assert len(first_rules) == 2

    listener = mock_coordinator.async_add_listener.call_args[0][0]

    call_count = async_add_entities.call_count
    listener()
    assert async_add_entities.call_count == call_count

    mock_coordinator.data["port_forwards"]["site1"]["pf2"] = {
        "_id": "pf2",
        "name": "SSH",
        "enabled": False,
    }
    listener()
    assert async_add_entities.call_count == call_count + 1
    new_added = async_add_entities.call_args[0][0]
    assert len(new_added) == 1
    assert new_added[0]._rule_id == "pf2"


@pytest.mark.parametrize(
    ("desc", "rule_id", "rule_name"),
    [
        (PORT_FORWARD_SWITCH, "pf1", " Plex "),
        (TRAFFIC_RULE_SWITCH, "tr1", " Bedtime "),
    ],
)
def test_unique_id_and_named_translation(
    mock_coordinator: MagicMock,
    desc: UnifiInsightsNetworkRuleSwitchEntityDescription,
    rule_id: str,
    rule_name: str,
) -> None:
    """Named rule populates unique_id, translation_key and trimmed rule_name."""
    mock_coordinator.data[desc.data_key] = {
        "site1": {rule_id: {desc.name_field: rule_name, "enabled": True}}
    }
    switch = UnifiInsightsNetworkRuleSwitch(mock_coordinator, desc, "site1", rule_id)
    assert switch.unique_id == f"site1_{rule_id}_{desc.unique_id_suffix}"
    assert switch.translation_key == desc.translation_key
    assert switch.translation_placeholders == {"rule_name": rule_name.strip()}


@pytest.mark.parametrize("desc", [PORT_FORWARD_SWITCH, TRAFFIC_RULE_SWITCH])
@pytest.mark.parametrize("name_val", [None, "", "   "])
def test_unnamed_rule_uses_rule_id_placeholder(
    mock_coordinator: MagicMock,
    desc: UnifiInsightsNetworkRuleSwitchEntityDescription,
    name_val: str | None,
) -> None:
    """Unnamed rule falls back to unnamed translation and rule_id placeholder."""
    mock_coordinator.data[desc.data_key] = {
        "site1": {"r1": {desc.name_field: name_val, "enabled": True}}
    }
    switch = UnifiInsightsNetworkRuleSwitch(mock_coordinator, desc, "site1", "r1")
    assert switch.translation_key == desc.unnamed_translation_key
    assert switch.translation_placeholders == {"rule_id": "r1"}


def test_device_info_uses_site_gateway(mock_coordinator: MagicMock) -> None:
    """Switch attaches to site gateway device when present."""
    mock_coordinator.data["devices"] = {
        "site1": {"gw1": {"model": "UDM-Pro", "name": "Gateway"}}
    }
    switch = UnifiInsightsNetworkRuleSwitch(
        mock_coordinator, PORT_FORWARD_SWITCH, "site1", "pf1"
    )
    assert switch.device_info is not None
    assert (DOMAIN, "site1_gw1") in switch.device_info["identifiers"]


def test_device_info_falls_back_to_site_device(mock_coordinator: MagicMock) -> None:
    """Switch falls back to site device grouping when no gateway is found."""
    mock_coordinator.data["devices"] = {"site1": {}}
    switch = UnifiInsightsNetworkRuleSwitch(
        mock_coordinator, PORT_FORWARD_SWITCH, "site1", "pf1"
    )
    assert switch.device_info is not None
    assert (DOMAIN, "site_site1") in switch.device_info["identifiers"]


@pytest.mark.parametrize(
    ("section_avail", "rule_data", "expected"),
    [
        (True, {"enabled": True}, True),
        (True, {"enabled": False}, True),
        (False, {"enabled": True}, False),
        (False, {"enabled": False}, False),
        (True, {"enabled": None}, False),
        (True, {"enabled": "true"}, False),
        (True, {"enabled": 1}, False),
        (True, {}, False),
        (True, None, False),
    ],
)
def test_available_requires_section_rule_and_bool_enabled(
    mock_coordinator: MagicMock,
    section_avail: bool,  # noqa: FBT001
    rule_data: dict[str, Any] | None,
    expected: bool,  # noqa: FBT001
) -> None:
    """Switch availability requires section, rule, and bool enabled."""
    mock_coordinator.port_forwards_available = MagicMock(return_value=section_avail)
    if rule_data is None:
        mock_coordinator.data["port_forwards"] = {"site1": {}}
    else:
        mock_coordinator.data["port_forwards"] = {"site1": {"pf1": rule_data}}
    switch = UnifiInsightsNetworkRuleSwitch(
        mock_coordinator, PORT_FORWARD_SWITCH, "site1", "pf1"
    )
    assert switch.available is expected


@pytest.mark.parametrize(("enabled", "expected"), [(True, True), (False, False)])
def test_is_on_follows_enabled(
    mock_coordinator: MagicMock,
    enabled: bool,  # noqa: FBT001
    expected: bool,  # noqa: FBT001
) -> None:
    """is_on follows enabled bool state."""
    mock_coordinator.data["port_forwards"]["site1"]["pf1"]["enabled"] = enabled
    switch = UnifiInsightsNetworkRuleSwitch(
        mock_coordinator, PORT_FORWARD_SWITCH, "site1", "pf1"
    )
    assert switch.is_on is expected


def test_port_forward_attributes_exclude_addresses(
    mock_coordinator: MagicMock,
) -> None:
    """Port forward extra state attributes contain metadata but no IP addresses."""
    mock_coordinator.data["port_forwards"]["site1"]["pf1"] = port_forward_record(
        _id="pf1",
        name="Plex",
        enabled=True,
        src_limiting_enabled=True,
        fwd="192.168.1.50",
        src="198.51.100.0/24",
        destination_ip="203.0.113.7",
        destination_ips=["203.0.113.8"],
    )
    switch = UnifiInsightsNetworkRuleSwitch(
        mock_coordinator, PORT_FORWARD_SWITCH, "site1", "pf1"
    )
    attrs = switch.extra_state_attributes
    expected_keys = {
        "rule_id",
        "protocol",
        "external_port",
        "forward_port",
        "interface",
        "logging",
        "source_limiting_enabled",
    }
    assert set(attrs.keys()) == expected_keys
    assert "192.168.1.50" not in attrs.values()
    assert "203.0.113.7" not in attrs.values()
    assert "203.0.113.8" not in attrs.values()
    assert "198.51.100.0/24" not in attrs.values()


def test_traffic_rule_attributes(mock_coordinator: MagicMock) -> None:
    """Traffic rule extra state attributes contain action and matching target."""
    switch = UnifiInsightsNetworkRuleSwitch(
        mock_coordinator, TRAFFIC_RULE_SWITCH, "site1", "tr1"
    )
    attrs = switch.extra_state_attributes
    assert attrs == {
        "rule_id": "tr1",
        "action": "BLOCK",
        "matching_target": "INTERNET",
    }


@pytest.mark.parametrize(
    ("desc", "rule_id", "method_name"),
    [
        (PORT_FORWARD_SWITCH, "pf1", "async_set_port_forward_enabled"),
        (TRAFFIC_RULE_SWITCH, "tr1", "async_set_traffic_rule_enabled"),
    ],
)
@pytest.mark.parametrize("turn_on", [True, False])
@pytest.mark.asyncio
async def test_turn_on_off_calls_facade_then_refreshes(
    mock_coordinator: MagicMock,
    desc: UnifiInsightsNetworkRuleSwitchEntityDescription,
    rule_id: str,
    method_name: str,
    turn_on: bool,  # noqa: FBT001
) -> None:
    """turn_on / turn_off invokes facade method, updates local state and refreshes."""
    setattr(mock_coordinator, method_name, AsyncMock())
    mock_coordinator.async_request_refresh = AsyncMock()

    mock_coordinator.data[desc.data_key]["site1"][rule_id]["enabled"] = not turn_on

    switch = UnifiInsightsNetworkRuleSwitch(mock_coordinator, desc, "site1", rule_id)
    switch.async_write_ha_state = MagicMock()

    if turn_on:
        await switch.async_turn_on()
    else:
        await switch.async_turn_off()

    handler = getattr(mock_coordinator, method_name)
    handler.assert_awaited_once_with("site1", rule_id, enabled=turn_on)
    assert mock_coordinator.data[desc.data_key]["site1"][rule_id]["enabled"] is turn_on
    switch.async_write_ha_state.assert_called_once()
    mock_coordinator.async_request_refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_turn_on_failure_raises_and_keeps_state(
    mock_coordinator: MagicMock,
) -> None:
    """Facade failure raises HomeAssistantError without state change or refresh."""
    err_msg = "Connection failed"
    mock_coordinator.async_set_port_forward_enabled = AsyncMock(
        side_effect=UniFiConnectionError(err_msg)
    )
    mock_coordinator.async_request_refresh = AsyncMock()

    mock_coordinator.data["port_forwards"]["site1"]["pf1"]["enabled"] = False
    switch = UnifiInsightsNetworkRuleSwitch(
        mock_coordinator, PORT_FORWARD_SWITCH, "site1", "pf1"
    )

    with pytest.raises(HomeAssistantError, match="Unable to update port forward Plex"):
        await switch.async_turn_on()

    assert mock_coordinator.data["port_forwards"]["site1"]["pf1"]["enabled"] is False
    mock_coordinator.async_request_refresh.assert_not_called()


@pytest.mark.asyncio
async def test_missing_facade_action_raises_without_fallback() -> None:
    """Coordinator missing action method raises HomeAssistantError without fallback."""

    class FakeCoordinator:
        data: ClassVar[dict[str, Any]] = {
            "port_forwards": {"site1": {"pf1": {"enabled": False}}}
        }

        def port_forwards_available(self, site_id: str) -> bool:
            return True

    coord = FakeCoordinator()
    switch = UnifiInsightsNetworkRuleSwitch(
        coord,
        PORT_FORWARD_SWITCH,
        "site1",
        "pf1",  # type: ignore[arg-type]
    )
    with pytest.raises(HomeAssistantError, match="Unable to update port forward pf1"):
        await switch.async_turn_on()


def test_entity_category_is_config_and_has_entity_name(
    mock_coordinator: MagicMock,
) -> None:
    """Switches have EntityCategory.CONFIG and _attr_has_entity_name True."""
    for desc in NETWORK_RULE_SWITCH_TYPES:
        rule_id = "pf1" if desc.key == "port_forward" else "tr1"
        switch = UnifiInsightsNetworkRuleSwitch(
            mock_coordinator, desc, "site1", rule_id
        )
        assert switch.entity_category == EntityCategory.CONFIG
        assert switch.has_entity_name is True


def test_discover_is_noop_when_sections_missing(mock_coordinator: MagicMock) -> None:
    """discover_network_rule_switches returns empty list when sections are missing."""
    mock_coordinator.data = {}
    known_keys: set[tuple[Any, ...]] = set()
    assert discover_network_rule_switches(mock_coordinator, known_keys) == []
    assert known_keys == set()

    mock_coordinator.data = None
    assert discover_network_rule_switches(mock_coordinator, known_keys) == []


def test_get_rule_data_guards_against_non_dict_data(
    mock_coordinator: MagicMock,
) -> None:
    """_get_rule_data returns {} when any coordinator data level is not a dict."""
    switch = UnifiInsightsNetworkRuleSwitch(
        mock_coordinator, PORT_FORWARD_SWITCH, "site1", "pf1"
    )
    mock_coordinator.data = "not-a-dict"
    assert switch._get_rule_data() == {}

    mock_coordinator.data = {"port_forwards": "not-a-dict"}
    assert switch._get_rule_data() == {}

    mock_coordinator.data = {"port_forwards": {"site1": "not-a-dict"}}
    assert switch._get_rule_data() == {}


def test_update_local_state_guards_against_non_dict_data(
    mock_coordinator: MagicMock,
) -> None:
    """_update_local_state handles non-dict data and missing rule cleanly."""
    switch = UnifiInsightsNetworkRuleSwitch(
        mock_coordinator, PORT_FORWARD_SWITCH, "site1", "pf1"
    )
    mock_coordinator.data = "not-a-dict"
    switch._update_local_state(enabled=True)

    mock_coordinator.data = {"port_forwards": "not-a-dict"}
    switch._update_local_state(enabled=True)

    mock_coordinator.data = {"port_forwards": {"site1": {}}}
    switch._update_local_state(enabled=True)
    assert switch._get_rule_data() == {}
