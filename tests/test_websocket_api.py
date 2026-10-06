# Copyright (c) 2026 Ruaan Deysel

"""Tests for the topology WebSocket API."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from unittest.mock import Mock, patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry as MockConfigEntryForTest,
)

from custom_components.unifi_insights import CarrierFabricData
from custom_components.unifi_insights.const import (
    CONF_CONNECTION_TYPE,
    CONNECTION_TYPE_CARRIER_FABRIC,
    DOMAIN,
)
from custom_components.unifi_insights.helpers import async_get_device_entry
from custom_components.unifi_insights.topology import build_site_topology
from custom_components.unifi_insights.websocket_api import (
    ERR_ENTRY_NOT_LOADED,
    ws_topology_sources,
    ws_topology_subscribe,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from pytest_homeassistant_custom_component.common import MockConfigEntry

SITE = "site-1"
GW_MAC = "02:00:00:00:00:01"


def _seed(entry: MockConfigEntry) -> dict[str, Any]:
    """
    Add a two-device site with one client beside the mocked setup's data.

    The mocked "default" site is kept (merged, not replaced) so the entity
    listeners that also run on facade updates still find their own data.
    """
    runtime = entry.runtime_data
    runtime.device_coordinator.last_update_success = True
    site = {SITE: {"id": SITE, "name": "Home"}}
    runtime.config_coordinator.data["sites"] = {
        **runtime.config_coordinator.data.get("sites", {}),
        **site,
    }
    data = runtime.coordinator.data
    data["sites"] = {**data.get("sites", {}), **site}
    data["devices"] = {
        **data.get("devices", {}),
        SITE: {
            "uuid-gw": {
                "id": "uuid-gw",
                "name": "Gateway",
                "model": "UDM Pro SE",
                "macAddress": GW_MAC,
                "state": "ONLINE",
                "topology": {"legacy_type": "udm"},
            },
            "uuid-ap": {
                "id": "uuid-ap",
                "name": "AP",
                "model": "U7 Pro XGS",
                "macAddress": "02:00:00:00:00:08",
                "state": "ONLINE",
                "topology": {
                    "legacy_type": "uap",
                    "uplink_mac": GW_MAC,
                    "uplink_type": "wire",
                },
            },
        },
    }
    data["clients"] = {
        **data.get("clients", {}),
        SITE: {
            "cli-1": {
                "id": "cli-1",
                "name": "Phone",
                "type": "WIRELESS",
                "macAddress": "12:00:00:00:00:02",
                "ipAddress": "10.2.0.9",
                "uplinkDeviceId": "uuid-ap",
            }
        },
    }
    return data


async def test_sources_lists_loaded_entries(
    hass: HomeAssistant, init_integration: MockConfigEntry, hass_ws_client
) -> None:
    """Sources returns each loaded entry with its selected sites."""
    _seed(init_integration)
    client = await hass_ws_client(hass)

    await client.send_json({"id": 1, "type": "unifi_insights/topology/sources"})
    msg = await client.receive_json()

    assert msg["success"]
    (source,) = msg["result"]
    assert source["entry_id"] == init_integration.entry_id
    assert source["title"] == init_integration.title
    assert {"id": SITE, "name": "Home"} in source["sites"]


async def test_sources_skips_loaded_entry_without_runtime_data(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """A briefly unloading entry cannot be offered as a topology source."""
    _seed(init_integration)
    connection = Mock()
    unloaded_entry = Mock(runtime_data=None)
    with patch.object(
        hass.config_entries,
        "async_loaded_entries",
        return_value=[unloaded_entry, init_integration],
    ):
        ws_topology_sources(hass, connection, {"id": 1})

    (sources,) = connection.send_result.call_args.args[1:]
    assert [source["entry_id"] for source in sources] == [init_integration.entry_id]


async def test_dashboard_commands_skip_loaded_carrier_fabric_entry(
    hass: HomeAssistant, init_integration: MockConfigEntry, hass_ws_client
) -> None:
    """A loaded Carrier Fabric entry has no topology or Protect data to offer."""
    _seed(init_integration)
    carrier_entry = MockConfigEntryForTest(
        domain=DOMAIN,
        entry_id="carrier_entry",
        unique_id="carrier_org_1",
        data={
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_CARRIER_FABRIC,
            "api_key": "isp_key",
        },
    )
    carrier_entry.add_to_hass(hass)
    carrier_entry.runtime_data = CarrierFabricData(client=Mock(), coordinator=Mock())
    carrier_entry.mock_state(hass, ConfigEntryState.LOADED)
    client = await hass_ws_client(hass)

    for msg_id, msg_type in (
        (1, "unifi_insights/topology/sources"),
        (2, "unifi_insights/protect/sources"),
    ):
        await client.send_json({"id": msg_id, "type": msg_type})
        msg = await client.receive_json()
        assert msg["success"], msg_type
        assert [source["entry_id"] for source in msg["result"]] == [
            init_integration.entry_id
        ], msg_type

    await client.send_json(
        {
            "id": 3,
            "type": "unifi_insights/protect/get",
            "entry_id": carrier_entry.entry_id,
        }
    )
    msg = await client.receive_json()
    assert not msg["success"]
    assert msg["error"]["code"] == ERR_ENTRY_NOT_LOADED


async def test_get_returns_snapshot(
    hass: HomeAssistant, init_integration: MockConfigEntry, hass_ws_client
) -> None:
    """Get returns an allowlisted snapshot with registry ids attached."""
    _seed(init_integration)
    registry_device = dr.async_get(hass).async_get_or_create(
        config_entry_id=init_integration.entry_id,
        identifiers={(DOMAIN, f"{SITE}_uuid-ap")},
    )
    client = await hass_ws_client(hass)

    await client.send_json(
        {
            "id": 1,
            "type": "unifi_insights/topology/get",
            "entry_id": init_integration.entry_id,
            "site_id": SITE,
        }
    )
    msg = await client.receive_json()

    assert msg["success"]
    snapshot = msg["result"]
    assert snapshot["status"] == "ok"
    assert snapshot["site_name"] == "Home"
    assert {edge["source"]: edge["target"] for edge in snapshot["edges"]} == {
        "dev:uuid-ap": "dev:uuid-gw",
        "cli:cli-1": "dev:uuid-ap",
    }
    ap = next(node for node in snapshot["nodes"] if node["id"] == "dev:uuid-ap")
    assert ap["ha_device_id"] == registry_device.id
    assert "10.2.0.9" not in str(snapshot)
    assert GW_MAC not in str(snapshot)


async def test_get_uses_entry_scoped_registry_lookup(
    hass: HomeAssistant, init_integration: MockConfigEntry, hass_ws_client
) -> None:
    """
    Device lookups go through the entry-scoped helper.

    The helper selects the best API available in the installed HA version;
    the snapshot builder must pass the current config entry for scoping.
    """
    _seed(init_integration)
    registry_device = dr.async_get(hass).async_get_or_create(
        config_entry_id=init_integration.entry_id,
        identifiers={(DOMAIN, f"{SITE}_uuid-ap")},
    )
    client = await hass_ws_client(hass)

    with patch(
        "custom_components.unifi_insights.websocket_api.async_get_device_entry",
        wraps=async_get_device_entry,
    ) as lookup:
        await client.send_json(
            {
                "id": 1,
                "type": "unifi_insights/topology/get",
                "entry_id": init_integration.entry_id,
                "site_id": SITE,
            }
        )
        msg = await client.receive_json()

    assert msg["success"]
    assert any(
        call.args[1:] == ((DOMAIN, f"{SITE}_uuid-ap"), init_integration.entry_id)
        for call in lookup.call_args_list
    )
    snapshot = msg["result"]
    ap = next(node for node in snapshot["nodes"] if node["id"] == "dev:uuid-ap")
    assert ap["ha_device_id"] == registry_device.id


async def test_get_non_admin_user_allowed(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    hass_ws_client,
    hass_read_only_access_token: str,
) -> None:
    """Dashboards are used by non-admins, so plain authentication suffices."""
    _seed(init_integration)
    client = await hass_ws_client(hass, hass_read_only_access_token)

    await client.send_json(
        {
            "id": 1,
            "type": "unifi_insights/topology/get",
            "entry_id": init_integration.entry_id,
            "site_id": SITE,
        }
    )
    msg = await client.receive_json()

    assert msg["success"]


async def test_get_max_clients(
    hass: HomeAssistant, init_integration: MockConfigEntry, hass_ws_client
) -> None:
    """max_clients is honoured and validated against the hard cap."""
    _seed(init_integration)
    client = await hass_ws_client(hass)

    await client.send_json(
        {
            "id": 1,
            "type": "unifi_insights/topology/get",
            "entry_id": init_integration.entry_id,
            "site_id": SITE,
            "max_clients": 0,
        }
    )
    msg = await client.receive_json()
    assert msg["result"]["truncation"] == {"clients_total": 1, "clients_included": 0}

    await client.send_json(
        {
            "id": 2,
            "type": "unifi_insights/topology/get",
            "entry_id": init_integration.entry_id,
            "site_id": SITE,
            "max_clients": 501,
        }
    )
    msg = await client.receive_json()
    assert not msg["success"]
    assert msg["error"]["code"] == "invalid_format"


async def test_get_errors(
    hass: HomeAssistant, init_integration: MockConfigEntry, hass_ws_client
) -> None:
    """Unknown entry, foreign domain and unselected site are reported by code."""
    _seed(init_integration)
    client = await hass_ws_client(hass)

    async def _get(msg_id: int, entry_id: str, site_id: str) -> dict:
        await client.send_json(
            {
                "id": msg_id,
                "type": "unifi_insights/topology/get",
                "entry_id": entry_id,
                "site_id": site_id,
            }
        )
        return await client.receive_json()

    missing = await _get(1, "nope", SITE)
    assert missing["error"]["code"] == "entry_not_found"

    other_domain = MockConfigEntryForTest(domain="other_domain")
    other_domain.add_to_hass(hass)
    foreign = await _get(2, other_domain.entry_id, SITE)
    assert foreign["error"]["code"] == "entry_not_found"

    unselected = await _get(3, init_integration.entry_id, "site-9")
    assert unselected["error"]["code"] == "site_not_selected"

    await hass.config_entries.async_unload(init_integration.entry_id)
    await hass.async_block_till_done()
    unloaded = await _get(4, init_integration.entry_id, SITE)
    assert unloaded["error"]["code"] == "entry_not_loaded"


async def _subscribe(client, entry: MockConfigEntry, msg_id: int = 1) -> dict:
    """Subscribe and return the initial snapshot event."""
    await client.send_json(
        {
            "id": msg_id,
            "type": "unifi_insights/topology/subscribe",
            "entry_id": entry.entry_id,
            "site_id": SITE,
        }
    )
    ack = await client.receive_json()
    assert ack["success"], ack
    event = await client.receive_json()
    assert event["type"] == "event"
    return event["event"]


def _rename_ap(data: dict[str, Any], name: str) -> None:
    """Publish a renamed AP the way the coordinator does: a new site dict."""
    devices = data["devices"][SITE]
    data["devices"][SITE] = {**devices, "uuid-ap": {**devices["uuid-ap"], "name": name}}


async def _assert_no_event(client, ping_id: int) -> None:
    """Prove nothing was pushed: the next message is the ping's pong."""
    await client.send_json({"id": ping_id, "type": "ping"})
    msg = await client.receive_json()
    assert msg["type"] == "pong", msg


async def test_subscribe_pushes_only_on_change(
    hass: HomeAssistant, init_integration: MockConfigEntry, hass_ws_client
) -> None:
    """Initial snapshot, then one push per real change, none for no-ops."""
    data = _seed(init_integration)
    facade = init_integration.runtime_data.coordinator
    # Settle dynamic entity/device discovery for the newly seeded site before
    # measuring: the platforms' own coordinator listeners (e.g. sensor.py's
    # async_discover_sensors) create HA device-registry entries for site-1's
    # devices on their first run after _seed(), which would otherwise look
    # like a spurious content change on the *next* listener call below.
    facade.async_update_listeners()
    await hass.async_block_till_done()
    client = await hass_ws_client(hass)

    initial = await _subscribe(client, init_integration)
    assert initial["status"] == "ok"

    facade.async_update_listeners()
    await _assert_no_event(client, 50)

    # Replace the site dict rather than mutating it in place: that is how the
    # device coordinator publishes each poll, and the subscription only
    # rebuilds when the per-site dict's identity changes.
    _rename_ap(data, "Hallway AP")
    facade.async_update_listeners()
    pushed = await client.receive_json()
    assert pushed["type"] == "event"
    assert pushed["event"]["revision"] != initial["revision"]
    names = {node["id"]: node["name"] for node in pushed["event"]["nodes"]}
    assert names["dev:uuid-ap"] == "Hallway AP"


async def test_subscribe_site_vanishes_then_recovers(
    hass: HomeAssistant, init_integration: MockConfigEntry, hass_ws_client
) -> None:
    """A site dropped without a reload is reported once, and the stream recovers."""
    _seed(init_integration)
    runtime = init_integration.runtime_data
    facade = runtime.coordinator
    facade.async_update_listeners()
    await hass.async_block_till_done()
    client = await hass_ws_client(hass)
    initial = await _subscribe(client, init_integration)

    # The site disappears from the selection without an entry reload (deleted
    # on the console, or the Network API went away).
    sites = runtime.config_coordinator.data["sites"]
    runtime.config_coordinator.data["sites"] = {
        site_id: site for site_id, site in sites.items() if site_id != SITE
    }
    facade.async_update_listeners()
    gone = await client.receive_json()
    assert gone["type"] == "event"
    assert gone["event"]["status"] == "unavailable"
    assert gone["event"]["issues"] == [
        {"code": "site_unavailable", "severity": "error"}
    ]
    assert gone["event"]["site_name"] == "Home"
    assert gone["event"]["nodes"] == []

    facade.async_update_listeners()
    await _assert_no_event(client, 60)

    runtime.config_coordinator.data["sites"] = sites
    facade.async_update_listeners()
    back = await client.receive_json()
    assert back["type"] == "event"
    assert back["event"]["status"] == "ok"
    assert back["event"]["revision"] == initial["revision"]


async def test_subscribe_skips_rebuild_when_inputs_unchanged(
    hass: HomeAssistant, init_integration: MockConfigEntry, hass_ws_client
) -> None:
    """Facade updates that touch nothing the snapshot reads cost no rebuild."""
    data = _seed(init_integration)
    facade = init_integration.runtime_data.coordinator
    facade.async_update_listeners()
    await hass.async_block_till_done()
    client = await hass_ws_client(hass)
    await _subscribe(client, init_integration)

    with patch(
        "custom_components.unifi_insights.websocket_api.build_site_topology",
        wraps=build_site_topology,
    ) as builder:
        for _ in range(3):
            facade.async_update_listeners()
        await _assert_no_event(client, 70)
        assert builder.call_count == 0

        # A poll that republishes identical content rebuilds once but pushes
        # nothing: the revision still gates what reaches the card.
        data["devices"][SITE] = dict(data["devices"][SITE])
        facade.async_update_listeners()
        await _assert_no_event(client, 71)
        assert builder.call_count == 1

        _rename_ap(data, "Hallway AP")
        facade.async_update_listeners()
        pushed = await client.receive_json()
        assert builder.call_count == 2

    assert pushed["type"] == "event"
    names = {node["id"]: node["name"] for node in pushed["event"]["nodes"]}
    assert names["dev:uuid-ap"] == "Hallway AP"


async def test_subscribe_errors_use_get_codes(
    hass: HomeAssistant, init_integration: MockConfigEntry, hass_ws_client
) -> None:
    """Subscribe rejects the same bad requests as get."""
    _seed(init_integration)
    client = await hass_ws_client(hass)

    await client.send_json(
        {
            "id": 1,
            "type": "unifi_insights/topology/subscribe",
            "entry_id": init_integration.entry_id,
            "site_id": "site-9",
        }
    )
    msg = await client.receive_json()

    assert msg["error"]["code"] == "site_not_selected"


async def test_unsubscribe_stops_pushes(
    hass: HomeAssistant, init_integration: MockConfigEntry, hass_ws_client
) -> None:
    """After unsubscribe_events, changes are no longer pushed."""
    data = _seed(init_integration)
    facade = init_integration.runtime_data.coordinator
    client = await hass_ws_client(hass)
    await _subscribe(client, init_integration, msg_id=7)

    await client.send_json({"id": 8, "type": "unsubscribe_events", "subscription": 7})
    assert (await client.receive_json())["success"]

    _rename_ap(data, "Changed")
    facade.async_update_listeners()
    await _assert_no_event(client, 9)


async def test_subscription_cleanup_callbacks_are_idempotent(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Overlapping unsubscribe and unload callbacks leave one clean listener."""
    _seed(init_integration)
    connection = Mock()
    connection.subscriptions = {}
    ws_topology_subscribe(
        hass,
        connection,
        {
            "id": 7,
            "entry_id": init_integration.entry_id,
            "site_id": SITE,
            "max_clients": 500,
        },
    )
    watchers = hass.data[f"{DOMAIN}_topology_unload_watchers"]
    (unload_callback,) = watchers[init_integration.entry_id]
    unsubscribe = connection.subscriptions[7]

    unsubscribe()
    unsubscribe()
    unload_callback()

    assert not watchers[init_integration.entry_id]
    assert connection.send_message.call_count == 1


async def test_subscribe_entry_unload_sends_final_snapshot(
    hass: HomeAssistant, init_integration: MockConfigEntry, hass_ws_client
) -> None:
    """Unloading the entry pushes an unavailable snapshot and ends the stream."""
    _seed(init_integration)
    client = await hass_ws_client(hass)
    await _subscribe(client, init_integration)

    await hass.config_entries.async_unload(init_integration.entry_id)
    await hass.async_block_till_done()

    final = await client.receive_json()
    assert final["type"] == "event"
    assert final["event"]["status"] == "unavailable"
    assert final["event"]["issues"] == [{"code": "entry_unloaded", "severity": "error"}]
    assert final["event"]["site_name"] == "Home"


async def test_subscribe_after_reload_gets_unload_snapshot(
    hass: HomeAssistant, init_integration: MockConfigEntry, hass_ws_client
) -> None:
    """A subscription made after a reload still hears the next unload."""
    _seed(init_integration)
    client = await hass_ws_client(hass)
    await _subscribe(client, init_integration, msg_id=1)

    assert await hass.config_entries.async_reload(init_integration.entry_id)
    await hass.async_block_till_done()
    first_final = await client.receive_json()
    assert first_final["id"] == 1
    assert first_final["event"]["issues"] == [
        {"code": "entry_unloaded", "severity": "error"}
    ]

    _seed(init_integration)
    await _subscribe(client, init_integration, msg_id=2)

    assert await hass.config_entries.async_unload(init_integration.entry_id)
    await hass.async_block_till_done()
    # The ping is answered after anything the unload pushed, so a missing
    # final snapshot shows up as the pong arriving first instead of a hang.
    await client.send_json({"id": 3, "type": "ping"})
    final = await client.receive_json()
    assert final["type"] == "event", final
    assert final["id"] == 2
    assert final["event"]["status"] == "unavailable"
    assert final["event"]["issues"] == [{"code": "entry_unloaded", "severity": "error"}]
    assert (await client.receive_json())["type"] == "pong"


async def test_subscribe_unload_then_close_is_safe(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    hass_ws_client,
    caplog,
) -> None:
    """Unload followed by connection close never removes the listener twice."""
    _seed(init_integration)
    client = await hass_ws_client(hass)
    await _subscribe(client, init_integration)

    await hass.config_entries.async_unload(init_integration.entry_id)
    await hass.async_block_till_done()
    await client.receive_json()  # final unavailable snapshot

    # A second remove_listener() raises KeyError, but ActiveConnection's close
    # handler catches every unsubscribe error and only logs it - so the proof
    # that nothing ran twice is the absence of an ERROR record, not a raise.
    with caplog.at_level(logging.ERROR):
        await client.close()
        await hass.async_block_till_done()

    errors = [rec for rec in caplog.records if rec.levelno >= logging.ERROR]
    assert not errors, [rec.getMessage() for rec in errors]


async def test_subscribe_close_then_unload_is_safe(
    hass: HomeAssistant, init_integration: MockConfigEntry, hass_ws_client
) -> None:
    """Connection close followed by unload never removes the listener twice."""
    _seed(init_integration)
    client = await hass_ws_client(hass)
    await _subscribe(client, init_integration)

    await client.close()
    await hass.async_block_till_done()
    assert await hass.config_entries.async_unload(init_integration.entry_id)
    await hass.async_block_till_done()

    assert init_integration.state is ConfigEntryState.NOT_LOADED


async def test_subscribe_cycles_share_one_unload_hook(
    hass: HomeAssistant, init_integration: MockConfigEntry, hass_ws_client
) -> None:
    """Repeated subscribe/unsubscribe adds at most one unload hook per entry."""
    _seed(init_integration)
    client = await hass_ws_client(hass)
    # _on_unload is private, but async_on_unload returns no remover, so the
    # hook list itself is the only place a per-subscription leak would show.
    hooks_before = len(init_integration._on_unload or [])

    for cycle in range(3):
        sub_id = 10 + cycle * 2
        await _subscribe(client, init_integration, msg_id=sub_id)
        await client.send_json(
            {"id": sub_id + 1, "type": "unsubscribe_events", "subscription": sub_id}
        )
        assert (await client.receive_json())["success"]

    assert len(init_integration._on_unload or []) <= hooks_before + 1
    watchers = hass.data[f"{DOMAIN}_topology_unload_watchers"]
    assert not watchers[init_integration.entry_id]


async def test_subscribe_builder_error_does_not_break_listeners(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    hass_ws_client,
    caplog,
) -> None:
    """
    A builder bug gets the guard's own per-site log line.

    Home Assistant already isolates listener failures, so "other listeners
    still run" holds with or without the guard; what the guard adds is a
    message naming the feature and site instead of HA's generic one.
    """
    _seed(init_integration)
    facade = init_integration.runtime_data.coordinator
    client = await hass_ws_client(hass)
    await _subscribe(client, init_integration)

    calls: list[str] = []
    facade.async_add_listener(lambda: calls.append("entity"))
    _rename_ap(init_integration.runtime_data.coordinator.data, "Changed")
    with (
        caplog.at_level(logging.ERROR),
        patch(
            "custom_components.unifi_insights.websocket_api.build_site_topology",
            side_effect=RuntimeError("boom"),
        ),
    ):
        facade.async_update_listeners()

    assert calls == ["entity"]
    assert f"Failed to rebuild the topology snapshot for {SITE}" in caplog.text
    assert "Unexpected error updating listener" not in caplog.text


async def test_timeline_subscribe_pushes_on_in_place_protect_event_update(
    hass: HomeAssistant, init_integration: MockConfigEntry, hass_ws_client
) -> None:
    """Timeline stream updates when Protect events mutate in place."""
    data = _seed(init_integration)
    facade = init_integration.runtime_data.coordinator
    data["protect"] = {"events": {"motion": {}}}
    client = await hass_ws_client(hass)

    await client.send_json(
        {
            "id": 501,
            "type": "unifi_insights/timeline/subscribe",
            "entry_id": init_integration.entry_id,
            "site_id": SITE,
            "max_items": 10,
            "hours": 24,
            "categories": ["security"],
        }
    )
    assert (await client.receive_json())["success"]
    initial = await client.receive_json()
    assert initial["type"] == "event"
    assert initial["event"]["included"] == 0

    data["protect"]["events"]["motion"]["evt-1"] = {
        "id": "evt-1",
        "device_id": "uuid-ap",
        "name": "AP",
        "timestamp": 4_102_444_800_000,
    }
    facade.async_update_listeners()

    update = await client.receive_json()
    assert update["type"] == "event"
    assert update["event"]["included"] == 1


async def test_site_health_get_returns_snapshot(
    hass: HomeAssistant, init_integration: MockConfigEntry, hass_ws_client
) -> None:
    """Site health get returns a snapshot for a selected site."""
    _seed(init_integration)
    client = await hass_ws_client(hass)

    await client.send_json(
        {
            "id": 90,
            "type": "unifi_insights/site_health/get",
            "entry_id": init_integration.entry_id,
            "site_id": SITE,
        }
    )
    msg = await client.receive_json()

    assert msg["success"]
    assert msg["result"]["site_id"] == SITE
    assert msg["result"]["status"] in {"ok", "partial"}
    assert "health" in msg["result"]


async def test_internet_activity_get_returns_snapshot(
    hass: HomeAssistant, init_integration: MockConfigEntry, hass_ws_client
) -> None:
    """Internet activity get returns configured window totals."""
    _seed(init_integration)
    data = init_integration.runtime_data.coordinator.data
    data["internet_activity"] = {
        SITE: {
            "1h": {"rx_bytes": 1000, "tx_bytes": 500},
            "1d": {"rx_bytes": 2000, "tx_bytes": 1000},
        }
    }
    data["internet_activity_unavailable"] = set()
    client = await hass_ws_client(hass)

    await client.send_json(
        {
            "id": 91,
            "type": "unifi_insights/internet_activity/get",
            "entry_id": init_integration.entry_id,
            "site_id": SITE,
        }
    )
    msg = await client.receive_json()

    assert msg["success"]
    assert msg["result"]["windows"]["1h"]["download_bytes"] == 1000
    assert msg["result"]["windows"]["1h"]["upload_bytes"] == 500


async def test_performance_get_returns_snapshot(
    hass: HomeAssistant, init_integration: MockConfigEntry, hass_ws_client
) -> None:
    """Performance get returns device performance rows."""
    _seed(init_integration)
    stats = init_integration.runtime_data.coordinator.data.setdefault("stats", {})
    stats[SITE] = {
        "uuid-gw": {
            "cpuUtilizationPct": 10,
            "memoryUtilizationPct": 20,
            "tx_rate": 100,
            "rx_rate": 50,
        }
    }
    client = await hass_ws_client(hass)

    await client.send_json(
        {
            "id": 92,
            "type": "unifi_insights/performance/get",
            "entry_id": init_integration.entry_id,
            "site_id": SITE,
        }
    )
    msg = await client.receive_json()

    assert msg["success"]
    assert isinstance(msg["result"].get("devices"), list)
    assert any(device["id"] == f"{SITE}:uuid-gw" for device in msg["result"]["devices"])


async def test_timeline_get_returns_snapshot(
    hass: HomeAssistant, init_integration: MockConfigEntry, hass_ws_client
) -> None:
    """Timeline get returns recent events in security category."""
    _seed(init_integration)
    data = init_integration.runtime_data.coordinator.data
    data.setdefault("protect", {}).setdefault("events", {}).setdefault("motion", {})[
        "evt-1"
    ] = {
        "id": "evt-1",
        "device_id": "uuid-ap",
        "name": "AP",
        "timestamp": int(datetime.now(tz=UTC).timestamp() * 1000),
    }
    client = await hass_ws_client(hass)

    await client.send_json(
        {
            "id": 93,
            "type": "unifi_insights/timeline/get",
            "entry_id": init_integration.entry_id,
            "site_id": SITE,
            "hours": 24,
            "max_items": 10,
            "categories": ["security"],
        }
    )
    msg = await client.receive_json()

    assert msg["success"]
    assert msg["result"]["status"] == "ok"
    assert isinstance(msg["result"].get("items"), list)
    assert any(item["id"] == "evt:evt-1" for item in msg["result"]["items"])


async def test_protect_sources_and_get_and_subscribe(
    hass: HomeAssistant, init_integration: MockConfigEntry, hass_ws_client
) -> None:
    """Protect sources, get, and subscribe return snapshots and stream updates."""
    data = _seed(init_integration)
    facade = init_integration.runtime_data.coordinator
    data["protect"] = {
        "cameras": {},
        "chimes": {},
        "nvrs": {"nvr-1": {"storage": {"healthy": True, "used": 40.0}}},
    }
    client = await hass_ws_client(hass)

    await client.send_json({"id": 94, "type": "unifi_insights/protect/sources"})
    sources_msg = await client.receive_json()
    assert sources_msg["success"]
    assert any(
        source["entry_id"] == init_integration.entry_id
        for source in sources_msg["result"]
    )

    await client.send_json(
        {
            "id": 95,
            "type": "unifi_insights/protect/get",
            "entry_id": init_integration.entry_id,
        }
    )
    get_msg = await client.receive_json()
    assert get_msg["success"]
    assert get_msg["result"]["status"] == "ok"

    await client.send_json(
        {
            "id": 96,
            "type": "unifi_insights/protect/subscribe",
            "entry_id": init_integration.entry_id,
        }
    )
    assert (await client.receive_json())["success"]
    initial = await client.receive_json()
    assert initial["type"] == "event"
    assert initial["event"]["status"] == "ok"

    data["protect"]["nvrs"]["nvr-1"]["storage"]["healthy"] = False
    facade.async_update_listeners()
    updated = await client.receive_json()
    assert updated["type"] == "event"
    assert updated["event"]["status"] == "degraded"

    await hass.config_entries.async_unload(init_integration.entry_id)
    await hass.async_block_till_done()
    unloaded_evt = await client.receive_json()
    assert unloaded_evt["type"] == "event"
    assert unloaded_evt["event"]["status"] == "unavailable"


async def test_dashboard_site_subscriptions_and_errors(
    hass: HomeAssistant, init_integration: MockConfigEntry, hass_ws_client, caplog
) -> None:
    """Cover get/subscribe error codes, updates, and unload for site dashboard streams."""
    data = _seed(init_integration)
    facade = init_integration.runtime_data.coordinator
    data["internet_activity"] = {
        SITE: {"1h": {"rx_bytes": 1000, "tx_bytes": 500}},
    }
    data["internet_activity_unavailable"] = set()
    data["stats"] = {SITE: {"uuid-gw": {"cpuUtilizationPct": 12}}}
    facade.async_update_listeners()
    await hass.async_block_till_done()
    client = await hass_ws_client(hass)

    for idx, cmd in enumerate(
        (
            "unifi_insights/site_health/get",
            "unifi_insights/internet_activity/get",
            "unifi_insights/performance/get",
            "unifi_insights/timeline/get",
        ),
        start=200,
    ):
        await client.send_json(
            {"id": idx, "type": cmd, "entry_id": "missing", "site_id": SITE}
        )
        err = await client.receive_json()
        assert err["error"]["code"] == "entry_not_found"

    await client.send_json(
        {"id": 210, "type": "unifi_insights/protect/get", "entry_id": "missing"}
    )
    assert (await client.receive_json())["error"]["code"] == "entry_not_found"

    await client.send_json(
        {
            "id": 211,
            "type": "unifi_insights/protect/subscribe",
            "entry_id": "missing",
        }
    )
    assert (await client.receive_json())["error"]["code"] == "entry_not_found"

    await client.send_json(
        {
            "id": 212,
            "type": "unifi_insights/site_health/subscribe",
            "entry_id": "missing",
            "site_id": SITE,
        }
    )
    assert (await client.receive_json())["error"]["code"] == "entry_not_found"

    for idx, cmd in enumerate(
        (
            "unifi_insights/site_health/subscribe",
            "unifi_insights/internet_activity/subscribe",
            "unifi_insights/performance/subscribe",
        ),
        start=220,
    ):
        await client.send_json(
            {
                "id": idx,
                "type": cmd,
                "entry_id": init_integration.entry_id,
                "site_id": SITE,
            }
        )
        assert (await client.receive_json())["success"]
        initial = await client.receive_json()
        assert initial["type"] == "event"

    # Trigger rebuild error logging isolation
    _rename_ap(data, "AP-Renamed")
    with (
        caplog.at_level(logging.ERROR),
        patch(
            "custom_components.unifi_insights.websocket_api.build_site_health_snapshot",
            side_effect=RuntimeError("boom"),
        ),
    ):
        facade.async_update_listeners()
    assert "Failed to rebuild site_health snapshot" in caplog.text

    # Drain performance update from _rename_ap
    perf_evt = await client.receive_json()
    assert perf_evt["type"] == "event"

    await hass.config_entries.async_unload(init_integration.entry_id)
    await hass.async_block_till_done()
