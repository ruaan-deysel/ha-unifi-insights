"""Tests for the UniFi Insights diagnostics."""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest
from homeassistant.components.diagnostics.const import REDACTED

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.unifi_insights.api import __version__
from custom_components.unifi_insights.api.network.models.client import Client
from custom_components.unifi_insights.coordinators.config import (
    UnifiConfigCoordinator,
)
from custom_components.unifi_insights.diagnostics import (
    _redact_coordinator_data,
    async_get_config_entry_diagnostics,
)


async def test_diagnostics(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    enable_custom_integrations,
) -> None:
    """Test diagnostics."""
    diagnostics = await async_get_config_entry_diagnostics(hass, init_integration)

    assert diagnostics["library_version"] == __version__
    assert "connection" in diagnostics
    assert "entry" in diagnostics
    assert "data" in diagnostics

    # Check connection info - host is always redacted in diagnostics
    assert diagnostics["connection"]["host"] == "**REDACTED**"
    assert diagnostics["connection"]["network_client_connected"] is True
    assert diagnostics["connection"]["protect_client_connected"] is True

    # Check that actual API key value is redacted (not appearing in output)
    assert "test_api_key" not in str(diagnostics)
    # The key name "api_key" will appear, but the value should be redacted
    assert diagnostics["entry"]["data"]["api_key"] == "**REDACTED**"


async def test_site_manager_diagnostics_exclude_raw_cloud_snapshot(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    enable_custom_integrations,
) -> None:
    """Account-wide Site Manager records never pass through generic redaction."""
    snapshot = {
        "hosts": {
            "secret-host": {
                "id": "secret-host",
                "reportedState": {"hostname": "private.example.test"},
            }
        },
        "sites": {},
        "devices": {},
        "isp_metrics": {},
        "sd_wan_configs": {},
        "collections": {},
        "last_attempt": None,
        "cooldown_until": None,
    }
    runtime = init_integration.runtime_data
    runtime.site_manager_coordinator = SimpleNamespace(data=snapshot)
    runtime.coordinator.data["site_manager"] = snapshot

    diagnostics = await async_get_config_entry_diagnostics(hass, init_integration)

    assert diagnostics["site_manager"]["inventory"]["hosts"] == 1
    assert "site_manager" not in diagnostics["data"]
    assert "secret-host" not in repr(diagnostics)
    assert "private.example.test" not in repr(diagnostics)


async def test_diagnostics_includes_websocket_health(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    enable_custom_integrations,
) -> None:
    """Test diagnostics surface the Protect WebSocket health signal.

    There was previously no way to tell "WS connected and delivering" from
    "connected but silent" from "reconnect-looping" (task 5) - diagnostics
    is the first place an operator would look to distinguish those.
    """
    diagnostics = await async_get_config_entry_diagnostics(hass, init_integration)

    assert "websocket" in diagnostics
    assert diagnostics["websocket"]["connected"] is False
    assert diagnostics["websocket"]["last_message_at"] is None

    # Review finding 1: a single shared connected/last_message_at pair
    # cannot tell "both subscriptions healthy" apart from "devices healthy,
    # events silently hung" - per-subscription detail must reach this
    # diagnostics payload too, not just the coordinator's own property.
    assert diagnostics["websocket"]["devices"] == {
        "connected": False,
        "last_message_at": None,
    }
    assert diagnostics["websocket"]["events"] == {
        "connected": False,
        "last_message_at": None,
    }


def _strings(value: Any) -> list[str]:
    """Return every string key and value in a nested diagnostics payload."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [s for k, v in value.items() for s in (*_strings(k), *_strings(v))]
    if isinstance(value, (list, tuple, set)):
        return [s for item in value for s in _strings(item)]
    return []


@pytest.mark.parametrize(
    ("passphrase", "escaped"),
    [
        ("simple-password", "simple-password"),
        ('sp;e:c,i"a\\l-pass', 'sp\\;e\\:c\\,i\\"a\\\\l-pass'),
    ],
)
async def test_diagnostics_redacts_wifi_qr_code(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    enable_custom_integrations,
    passphrase: str,
    escaped: str,
) -> None:
    """Test diagnostics does not disclose password-bearing Wi-Fi QR payloads."""
    wifi = {"wifi-1": {"name": "Test WiFi"}}
    UnifiConfigCoordinator._enrich_wifi(
        wifi,
        [
            {
                "name": "Test WiFi",
                "x_passphrase": passphrase,
                "security": "wpa2",
            }
        ],
        [],
    )
    qr_code = wifi["wifi-1"]["qr_code"]
    coordinator = init_integration.runtime_data.coordinator
    coordinator.data["wifi"] = {"site-1": wifi}

    diagnostics = await async_get_config_entry_diagnostics(hass, init_integration)
    diagnostic_wifi = diagnostics["data"]["wifi"]["site-1"]["wifi-1"]

    assert qr_code.startswith("WIFI:T:WPA;S:Test WiFi;P:")
    assert wifi["wifi-1"]["passphrase"] == passphrase
    assert coordinator.data["wifi"]["site-1"]["wifi-1"]["qr_code"] == qr_code
    assert diagnostic_wifi["passphrase"] == REDACTED
    assert diagnostic_wifi["qr_code"] == REDACTED
    assert f"P:{escaped};" in qr_code
    for text in _strings(diagnostics):
        assert passphrase not in text
        assert escaped not in text


CLIENT_PAYLOAD = {
    "id": "client-1",
    "macAddress": "AA:BB:CC:11:22:33",
    "name": "Sarah's iPhone",
    "hostname": "sarahs-iphone",
    "ipAddress": "192.168.1.55",
    "type": "WIRELESS",
    "essid": "Sarah and Tom 5G",
    "bssid": "AA:BB:CC:44:55:66",
    "apMac": "AA:BB:CC:44:55:60",
    "swMac": "AA:BB:CC:77:88:99",
    "deviceName": "Sarah's iPhone 15",
    "osName": "iOS",
    "signal": -52,
    # Client accepts unknown extra fields, so anything the controller starts
    # sending lands in the diagnostics payload untouched by a key list.
    "note": "Sarah - bedroom",
    "gwMac": "AA:BB:CC:AB:CD:EF",
}

PERSONAL_STRINGS = (
    "Sarah's iPhone",
    "sarahs-iphone",
    "Sarah and Tom 5G",
    "Sarah's iPhone 15",
    "Sarah - bedroom",
    "192.168.1.55",
    "AA:BB:CC:11:22:33",
    "AA:BB:CC:44:55:66",
    "AA:BB:CC:44:55:60",
    "AA:BB:CC:77:88:99",
    "AA:BB:CC:AB:CD:EF",
)


def _client_record() -> dict[str, Any]:
    """Return a client record shaped exactly like the coordinator stores one."""
    return Client.model_validate(CLIENT_PAYLOAD).model_dump(by_alias=True)


def _seed_client_data(coordinator: Any) -> dict[str, Any]:
    """Put a synthetic client into every place the coordinator keeps one."""
    record = _client_record()
    coordinator.data["clients"] = {"site-1": {"client-1": record}}
    coordinator.data["stats"] = {
        "site-1": {"device-1": {"id": "device-1", "clients": [record]}}
    }
    return record


async def test_diagnostics_redacts_client_identity(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    enable_custom_integrations,
) -> None:
    """Test diagnostics does not disclose who is on the network.

    Redacting passwords is not enough: a client record names its owner
    ("Sarah's iPhone"), the SSID they connect to, and the MAC addresses of
    both the client and the access point or switch it sits behind.
    """
    coordinator = init_integration.runtime_data.coordinator
    record = _seed_client_data(coordinator)

    diagnostics = await async_get_config_entry_diagnostics(hass, init_integration)
    client = diagnostics["data"]["clients"]["site-1"]["client-1"]

    assert client["name"] == REDACTED
    assert client["hostname"] == REDACTED
    assert client["deviceName"] == REDACTED
    assert client["note"] == REDACTED
    assert client["essid"] == REDACTED
    assert client["ipAddress"] == REDACTED
    for key in ("macAddress", "bssid", "apMac", "swMac", "gwMac"):
        assert client[key].startswith("**REDACTED-MAC-")

    # Non-identifying telemetry is what makes the report useful - keep it.
    assert client["osName"] == "iOS"
    assert client["signal"] == -52
    assert client["type"] == "WIRELESS"

    # The same record is copied into per-device statistics; it has to be
    # redacted there too, not just in the clients collection.
    stats_client = diagnostics["data"]["stats"]["site-1"]["device-1"]["clients"][0]
    assert stats_client["name"] == REDACTED
    assert stats_client["essid"] == REDACTED

    texts = _strings(diagnostics)
    for personal in PERSONAL_STRINGS:
        assert personal not in texts

    # The coordinator's own data is untouched; entities still need it.
    assert record["name"] == "Sarah's iPhone"
    assert coordinator.data["clients"]["site-1"]["client-1"]["apMac"] == (
        "AA:BB:CC:44:55:60"
    )


async def test_diagnostics_keeps_hardware_names_readable(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    enable_custom_integrations,
) -> None:
    """Test device and site names survive redaction.

    A report where every name is **REDACTED** cannot be read: the names of
    switches, access points and sites are what tell an operator which record
    is which, and none of them name a person.
    """
    coordinator = init_integration.runtime_data.coordinator
    coordinator.data["sites"] = {"site-1": {"id": "site-1", "name": "Home"}}
    coordinator.data["devices"] = {
        "site-1": {
            "device-1": {
                "id": "device-1",
                "name": "Garage Switch",
                "model": "USW-24",
                "macAddress": "AA:BB:CC:77:88:99",
            }
        }
    }

    diagnostics = await async_get_config_entry_diagnostics(hass, init_integration)

    assert diagnostics["data"]["sites"]["site-1"]["name"] == "Home"
    device = diagnostics["data"]["devices"]["site-1"]["device-1"]
    assert device["name"] == "Garage Switch"
    assert device["model"] == "USW-24"
    assert device["macAddress"].startswith("**REDACTED-MAC-")


async def test_diagnostics_redacts_wan_link_addresses(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    enable_custom_integrations,
) -> None:
    """Test merged WAN link addresses are redacted but link state is kept."""
    coordinator = init_integration.runtime_data.coordinator
    coordinator.data["devices"] = {
        "site-1": {
            "device-1": {
                "id": "device-1",
                "model": "UCG-Ultra",
                "features": {"gateway": True},
                "wans": [
                    {
                        "key": "wan",
                        "name": "WAN",
                        "status": "online",
                        "ip": "198.51.100.7",
                        "connected": True,
                    }
                ],
            }
        }
    }

    diagnostics = await async_get_config_entry_diagnostics(hass, init_integration)

    device = diagnostics["data"]["devices"]["site-1"]["device-1"]
    wan = device["wans"][0]
    assert wan["ip"] == REDACTED
    assert device["features"] == {"gateway": True}
    assert wan["status"] == "online"
    assert wan["connected"] is True


async def test_diagnostics_mac_placeholders_are_stable_and_distinct(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    enable_custom_integrations,
) -> None:
    """Test MAC placeholders keep a report correlatable without exposing MACs.

    A blanket **REDACTED** would lose which access point a client is on, and
    would collapse the devices the API lists without an id - those are keyed
    by MAC - into a single colliding entry.
    """
    coordinator = init_integration.runtime_data.coordinator
    _seed_client_data(coordinator)
    coordinator.data["devices"] = {
        "site-1": {
            # Devices reported without an id are keyed by MAC (#128).
            "aa:bb:cc:44:55:60": {"name": "Hallway AP", "mac": "AA:BB:CC:44:55:60"},
            # Unpunctuated under a known MAC key is still the same MAC.
            "aa:bb:cc:77:88:99": {"name": "Garage Switch", "mac": "aabbcc778899"},
        }
    }

    diagnostics = await async_get_config_entry_diagnostics(hass, init_integration)
    devices = diagnostics["data"]["devices"]["site-1"]
    client = diagnostics["data"]["clients"]["site-1"]["client-1"]

    # Two MAC-keyed devices stay two entries.
    assert len(devices) == 2
    access_point, switch = devices.values()
    assert access_point["name"] == "Hallway AP"
    assert switch["name"] == "Garage Switch"

    # The client's uplinks still point at the right hardware.
    assert client["apMac"] == access_point["mac"]
    assert client["swMac"] == switch["mac"]
    assert client["apMac"] != client["swMac"]
    assert client["macAddress"] not in (client["apMac"], client["swMac"])

    # Differences in case, separator or punctuation are the same MAC, so the
    # entry keys and the records inside them still agree.
    assert list(devices) == [access_point["mac"], switch["mac"]]


async def test_diagnostics_redacts_wifi_ssid(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    enable_custom_integrations,
) -> None:
    """Test the SSID is redacted wherever the WiFi record carries it."""
    coordinator = init_integration.runtime_data.coordinator
    coordinator.data["wifi"] = {
        "site-1": {
            "wifi-1": {
                "id": "wifi-1",
                "name": "Sarah and Tom 5G",
                "ssid": "Sarah and Tom 5G",
                "enabled": True,
                "security": "wpa2",
                "num_connected_clients": 4,
            }
        }
    }

    diagnostics = await async_get_config_entry_diagnostics(hass, init_integration)
    wifi = diagnostics["data"]["wifi"]["site-1"]["wifi-1"]

    assert wifi["name"] == REDACTED
    assert wifi["ssid"] == REDACTED
    assert wifi["enabled"] is True
    assert wifi["num_connected_clients"] == 4
    assert "Sarah and Tom 5G" not in _strings(diagnostics)


@pytest.mark.parametrize(
    "data",
    [
        None,
        [],
        {"clients": "not-a-mapping", "wifi": None},
        {"stats": {"site-1": None}},
        {"stats": {"site-1": {"device-1": {"uptime": 42}}}},
    ],
)
def test_redact_coordinator_data_tolerates_unexpected_shapes(data: Any) -> None:
    """Test redaction never raises on a snapshot that is not fully populated.

    A diagnostics download must still produce a report when the coordinator
    has not loaded yet, or when a section is missing or shaped unexpectedly.
    """
    assert _redact_coordinator_data(data) == data


async def test_diagnostics_redacts_unpunctuated_macs_anywhere(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    enable_custom_integrations,
) -> None:
    """Test an unpunctuated MAC is redacted under an unknown key or as a key.

    The controller is not consistent about punctuation, and the key list only
    knows the MAC fields that exist today. A bare twelve-hex value is an
    address wherever it turns up, and it is the same address as its punctuated
    form, so both have to reach the same placeholder.
    """
    coordinator = init_integration.runtime_data.coordinator
    coordinator.data["clients"] = {
        "site-1": {
            "client-1": {
                "macAddress": "AA:BB:CC:44:55:60",
                # A field no model declares, holding the unpunctuated form.
                "wiredUplinkMacAddress": "aabbcc445560",
            }
        }
    }
    coordinator.data["devices"] = {
        # Devices reported without an id are keyed by MAC, and nothing
        # guarantees the controller punctuates it.
        "site-1": {"aabbcc445560": {"name": "Hallway AP", "model": "U7-Pro"}}
    }

    diagnostics = await async_get_config_entry_diagnostics(hass, init_integration)
    client = diagnostics["data"]["clients"]["site-1"]["client-1"]
    (device_key,) = diagnostics["data"]["devices"]["site-1"]

    assert client["wiredUplinkMacAddress"].startswith("**REDACTED-MAC-")
    assert device_key.startswith("**REDACTED-MAC-")
    # One address, one placeholder, whichever way it was written.
    assert client["wiredUplinkMacAddress"] == client["macAddress"] == device_key
    assert "aabbcc445560" not in _strings(diagnostics)


async def test_diagnostics_keeps_malformed_mac_values_distinct(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    enable_custom_integrations,
) -> None:
    """Test two unparsable values under MAC keys do not share a placeholder.

    The models accept any string for a MAC field. Canonicalizing by discarding
    everything that is not a hex character would make `not-a-mac` and `aac`
    the same value, which quietly rewrites the client-to-device relationships
    the placeholders exist to preserve.
    """
    coordinator = init_integration.runtime_data.coordinator
    coordinator.data["clients"] = {
        "site-1": {
            "client-1": {"macAddress": "not-a-mac", "apMac": "aac"},
            "client-2": {"macAddress": "aac"},
        }
    }

    diagnostics = await async_get_config_entry_diagnostics(hass, init_integration)
    clients = diagnostics["data"]["clients"]["site-1"]
    first = clients["client-1"]
    second = clients["client-2"]

    assert first["macAddress"] != first["apMac"]
    # The same unparsable value is still the same value.
    assert first["apMac"] == second["macAddress"]
    for value in (first["macAddress"], first["apMac"]):
        assert value.startswith("**REDACTED-MAC-")
    assert "not-a-mac" not in _strings(diagnostics)


async def test_diagnostics_placeholders_topology_uplink_mac(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    enable_custom_integrations,
) -> None:
    """The copied legacy parent MAC is placeholdered like every other MAC."""
    coordinator = init_integration.runtime_data.coordinator
    coordinator.data["devices"] = {
        "site-1": {
            "uuid-child": {
                "name": "Ultra",
                "macAddress": "58:d6:1f:00:00:02",
                "topology": {
                    "legacy_type": "usw",
                    "uplink_mac": "28:70:4e:00:00:01",
                    "uplink_remote_port": 6,
                },
            },
            "uuid-parent": {"name": "Core", "macAddress": "28:70:4e:00:00:01"},
        }
    }

    diagnostics = await async_get_config_entry_diagnostics(hass, init_integration)
    devices = diagnostics["data"]["devices"]["site-1"]
    uplink_mac = devices["uuid-child"]["topology"]["uplink_mac"]

    assert uplink_mac.startswith("**REDACTED-MAC-")
    # Same MAC, same placeholder: the parent link stays traceable.
    assert uplink_mac == devices["uuid-parent"]["macAddress"]
    assert devices["uuid-child"]["topology"]["uplink_remote_port"] == 6
    assert "28:70:4e:00:00:01" not in _strings(diagnostics)


async def test_diagnostics_placeholders_client_links(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    enable_custom_integrations,
) -> None:
    """Client link MACs (keys and values) are placeholdered; VLAN stays."""
    coordinator = init_integration.runtime_data.coordinator
    coordinator.data["client_links"] = {
        "site-1": {
            "8c:ed:e1:00:00:01": {
                "sw_mac": "28:70:4e:00:00:01",
                "sw_port": 14,
                "vlan": 3,
                "network_name": "Cameras",
            }
        }
    }

    diagnostics = await async_get_config_entry_diagnostics(hass, init_integration)
    (link_key,) = diagnostics["data"]["client_links"]["site-1"]
    link = diagnostics["data"]["client_links"]["site-1"][link_key]

    assert link_key.startswith("**REDACTED-MAC-")
    assert link["sw_mac"].startswith("**REDACTED-MAC-")
    assert link["vlan"] == 3
    assert link["network_name"] == "Cameras"
    for raw in ("8c:ed:e1:00:00:01", "28:70:4e:00:00:01"):
        assert raw not in _strings(diagnostics)
