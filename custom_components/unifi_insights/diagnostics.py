"""Diagnostics support for UniFi Insights."""

from __future__ import annotations

import logging
import re
from collections.abc import Mapping
from datetime import datetime
from typing import TYPE_CHECKING, Any

from homeassistant.components.diagnostics import REDACTED, async_redact_data
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_VERIFY_SSL

from .api import __version__ as api_version
from .const import CONF_CONSOLE_ID, ISP_WAN_NUMBERS, SITE_MANAGER_COLLECTIONS
from .innerspace_transforms import build_innerspace_diagnostics_summary

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from . import UnifiInsightsConfigEntry

_LOGGER = logging.getLogger(__name__)
_MAX_HOST_SITE_COUNTS = 20
_MAX_ISP_SAMPLES = 8
TO_REDACT = {
    # Credentials and secrets
    CONF_API_KEY,
    "token",
    "accessToken",
    "access_token",
    "refreshToken",
    "refresh_token",
    "password",
    "psk",
    "passphrase",
    "qr_code",
    "secret",
    "voucher",
    "fingerprint",
    # Classic-API secrets that ride along with legacy device and WiFi payloads
    "x_passphrase",
    "x_authkey",
    "x_fingerprint",
    "x_iapp_key",
    "x_ssh_hostkey_fingerprint",
    "x_vwirekey",
    # Network identifiers
    CONF_HOST,
    "ip",
    "ipAddress",
    "ip_address",
    "ipAddresses",
    "ip_addresses",
    "host",
    "hostname",
    "wan_ip",
    "wanIp",
    "lan_ip",
    "lanIp",
    "sourceAddress",
    "source_address",
    "destinationAddress",
    "destination_address",
    "domainName",
    "domain_name",
    # WiFi network identity: an SSID names a household and locates it in
    # public wardriving databases, so it is redacted like any other identifier.
    "ssid",
    "essid",
    # Device identifiers
    "serial",
    "serialNumber",
    "hardwareId",
    "hardware_id",
    # HA config entry fields
    "unique_id",
    CONF_CONSOLE_ID,
    CONF_VERIFY_SSL,
    # Common API response id fields that may contain sensitive info
    "id",
    "deviceId",
    "siteId",
    "site_id",
    "floor_plan_id",
    "floorPlanId",
    "matched_device_id",
    "matched_site_id",
    "image_url",
    "imageUrl",
    # Location data
    "latitude",
    "longitude",
    # Smart detections that name a person or their vehicle
    "licensePlate",
    "license_plate",
}

# Labels that name a person rather than a piece of hardware. These are only
# redacted inside the records where they carry personal data - a client is
# usually named after its owner ("Sarah's iPhone"), while the name of a switch,
# a site or a camera is what makes a diagnostics download readable at all.
PERSONAL_NAMES = {
    "name",
    "displayName",
    "display_name",
    "deviceName",
    "device_name",
    "note",
    "userId",
    "user_id",
}

# Client records: everything above, plus the owner-supplied names.
CLIENT_TO_REDACT = TO_REDACT | PERSONAL_NAMES

# WiFi records: the SSID is also carried in the record's "name" field.
WIFI_TO_REDACT = TO_REDACT | {"name"}

# Keys whose value is a MAC address even when it arrives unpunctuated. Values
# are replaced with a per-report placeholder rather than dropped; see
# _anonymize_macs.
MAC_KEYS = frozenset(
    {
        "mac",
        "macAddress",
        "mac_address",
        "macAddresses",
        "mac_addresses",
        "macFilterList",
        "mac_filter_list",
        "bssid",
        "apMac",
        "ap_mac",
        "swMac",
        "sw_mac",
        "uplinkMac",
        "uplink_mac",
        "gatewayMac",
        "gateway_mac",
        "wanMac",
        "wan_mac",
        "lanMac",
        "lan_mac",
    }
)

# A punctuated MAC anywhere in a string, whatever key it arrived under.
_MAC_PATTERN = re.compile(r"\b[0-9A-Fa-f]{2}(?:[:-][0-9A-Fa-f]{2}){5}\b")
# A whole value that is a MAC. Unlike the pattern above this also accepts the
# unpunctuated form, which is only safe to assume when it is the entire value:
# twelve hex characters in the middle of a sentence are not an address.
_MAC_VALUE_PATTERN = re.compile(
    r"[0-9A-Fa-f]{2}(?:[:-][0-9A-Fa-f]{2}){5}|[0-9A-Fa-f]{12}"
)


def _mac_placeholder(mac: str, seen: dict[str, str]) -> str:
    """Return a stable placeholder for a MAC address within one report."""
    # Punctuation and case vary by endpoint, so real addresses canonicalize to
    # one key. Anything else keeps its own value as the key: stripping it down
    # to its hex characters would make "not-a-mac" and "aac" collide, and the
    # placeholders are only useful while distinct values stay distinct.
    lowered = mac.lower()
    normalized = (
        re.sub(r"[:-]", "", lowered)
        if _MAC_VALUE_PATTERN.fullmatch(lowered)
        else f"raw:{lowered}"
    )
    placeholder = seen.get(normalized)
    if placeholder is None:
        placeholder = f"**REDACTED-MAC-{len(seen) + 1}**"
        seen[normalized] = placeholder
    return placeholder


def _anonymize_macs(
    value: Any, seen: dict[str, str], *, is_mac_field: bool = False
) -> Any:
    """
    Replace every MAC address with a placeholder that is stable per report.

    Key-based redaction cannot keep up here: the API spells MAC addresses
    `macAddress`, `bssid`, `apMac`, `swMac` and more, and a client record
    accepts unknown extra fields, so any future MAC field would be published
    the moment the controller starts sending it. Every MAC-shaped value is
    therefore rewritten regardless of the key that carried it, punctuated or
    not, whether it appears as a value or as a mapping key.

    The same MAC always maps to the same placeholder, so a report still shows
    which access point or switch port a client sits behind, and devices keyed
    by MAC (those the API lists without an id) cannot collide into one entry.

    Args:
        value: The diagnostics payload, or any part of it.
        seen: Placeholders already handed out, keyed by normalized MAC.
        is_mac_field: Whether the value arrived under a known MAC key, in
            which case it is a MAC even if it is not punctuated like one.

    Returns:
        A copy of the value with MAC addresses replaced.

    """
    if isinstance(value, str):
        if not value or value == REDACTED:
            return value
        if is_mac_field or _MAC_VALUE_PATTERN.fullmatch(value):
            return _mac_placeholder(value, seen)
        return _MAC_PATTERN.sub(
            lambda match: _mac_placeholder(match.group(), seen), value
        )
    if isinstance(value, Mapping):
        return {
            (
                _mac_placeholder(key, seen)
                if isinstance(key, str) and _MAC_VALUE_PATTERN.fullmatch(key)
                else key
            ): _anonymize_macs(
                item, seen, is_mac_field=isinstance(key, str) and key in MAC_KEYS
            )
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [
            _anonymize_macs(item, seen, is_mac_field=is_mac_field) for item in value
        ]
    return value


def _redact_coordinator_data(data: Any) -> Any:
    """
    Redact a coordinator data snapshot.

    Client and WiFi records get the personal-name treatment on top of the
    shared key list; devices, sites and Protect records keep their names so
    the report stays readable.
    """
    redacted = async_redact_data(data, TO_REDACT)
    if not isinstance(data, Mapping) or not isinstance(redacted, dict):
        return redacted

    for section, to_redact in (
        ("clients", CLIENT_TO_REDACT),
        ("wifi", WIFI_TO_REDACT),
    ):
        records = data.get(section)
        if isinstance(records, Mapping):
            redacted[section] = {
                site_id: async_redact_data(site_records, to_redact)
                for site_id, site_records in records.items()
            }

    # Per-device statistics carry a copy of that device's client records.
    stats = redacted.get("stats")
    if isinstance(stats, dict):
        for site_stats in stats.values():
            if not isinstance(site_stats, dict):
                continue
            for device_stats in site_stats.values():
                if isinstance(device_stats, dict) and "clients" in device_stats:
                    device_stats["clients"] = async_redact_data(
                        device_stats["clients"], CLIENT_TO_REDACT
                    )

    return redacted


def _site_manager_summary(
    snapshot: Mapping[str, Any], console_id: str
) -> dict[str, Any]:
    """Build a bounded diagnostic view without cloud identifiers or raw data."""
    hosts = snapshot.get("hosts") or {}
    sites = snapshot.get("sites") or {}
    devices = snapshot.get("devices") or {}
    metrics = snapshot.get("isp_metrics") or {}
    configs = snapshot.get("sd_wan_configs") or {}
    collections = snapshot.get("collections") or {}

    site_counts: dict[str, int] = {}
    for site in sites.values():
        host_id = site.get("hostId") if isinstance(site, Mapping) else None
        if isinstance(host_id, str):
            site_counts[host_id] = site_counts.get(host_id, 0) + 1

    selected_devices = devices.get(console_id) or {}
    selected_device_count = len(selected_devices.get("devices") or [])
    selected_metrics = metrics.get(console_id) or {}
    samples: list[dict[str, Any]] = []
    for item in selected_metrics.values():
        if not isinstance(item, Mapping):
            continue
        metric_time = item.get("metric_time")
        wan = item.get("wan")
        if not isinstance(metric_time, str) or not isinstance(wan, Mapping):
            continue
        try:
            safe_time = datetime.fromisoformat(metric_time).isoformat()
        except ValueError:
            continue
        samples.append(
            {
                "metric_time": safe_time,
                "wan": {
                    key: value
                    for key in ISP_WAN_NUMBERS
                    if isinstance(value := wan.get(key), (int, float))
                    and not isinstance(value, bool)
                },
            }
        )
    samples.sort(key=lambda item: str(item["metric_time"]), reverse=True)

    sd_wan_types: dict[str, int] = {}
    for config in configs.values():
        config_type = config.get("type") if isinstance(config, Mapping) else None
        safe_type = "sdwan-hbsp" if config_type == "sdwan-hbsp" else "other"
        sd_wan_types[safe_type] = sd_wan_types.get(safe_type, 0) + 1

    return {
        "inventory": {
            "hosts": len(hosts),
            "sites": len(sites),
            "device_groups": len(devices),
            "devices": sum(
                len(group.get("devices") or [])
                for group in devices.values()
                if isinstance(group, Mapping)
            ),
            "sd_wan_configs": len(configs),
        },
        "host_site_counts": sorted(site_counts.values(), reverse=True)[
            :_MAX_HOST_SITE_COUNTS
        ],
        "host_site_counts_truncated": len(site_counts) > _MAX_HOST_SITE_COUNTS,
        "selected_host": {
            "found": console_id in hosts,
            "site_count": site_counts.get(console_id, 0),
            "device_count": selected_device_count,
            "isp_samples": samples[:_MAX_ISP_SAMPLES],
            "isp_samples_truncated": len(samples) > _MAX_ISP_SAMPLES,
        },
        "sd_wan_types": sd_wan_types,
        "collections": {
            name: {
                "available": bool(state.get("available")),
                "updated_at": state.get("updated_at"),
                "error": state.get("error"),
            }
            for name in SITE_MANAGER_COLLECTIONS
            if isinstance(state := collections.get(name), Mapping)
        },
        "last_attempt": snapshot.get("last_attempt"),
        "cooldown_until": snapshot.get("cooldown_until"),
    }


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: UnifiInsightsConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    _ = hass
    _LOGGER.debug("Gathering diagnostics data for UniFi Insights")

    data = entry.runtime_data
    coordinator = data.coordinator

    # Get library version
    library_version = api_version

    # Get sanitized connection info
    connection_info = {
        "host": REDACTED,
        "network_client_connected": coordinator.network_client is not None,
        "protect_client_connected": coordinator.protect_client is not None,
        "innerspace_client_connected": (
            getattr(coordinator, "innerspace_client", None) is not None
            or getattr(data, "innerspace_client", None) is not None
        ),
    }

    # WS health signal (task 5): previously no way to tell "connected and
    # delivering" from "connected but silent" from "reconnect-looping" -
    # this is the first place an operator would look for that.
    protect_coordinator = data.protect_coordinator
    websocket_info = (
        protect_coordinator.websocket_health if protect_coordinator else None
    )

    # The Site Manager and InnerSpace snapshots contain identifiers and variable
    # nested fields. Build their summaries separately and exclude raw sections.
    facade_data = dict(coordinator.data)
    facade_data.pop("site_manager", None)
    innerspace_snapshot = facade_data.pop("innerspace", None)
    innerspace_coord = getattr(data, "innerspace_coordinator", None)
    if not isinstance(innerspace_snapshot, Mapping) and innerspace_coord is not None:
        innerspace_snapshot = innerspace_coord.data
    diagnostics_data: dict[str, Any] = {
        "library_version": library_version,
        "connection": connection_info,
        "websocket": websocket_info,
        "entry": async_redact_data(entry.as_dict(), TO_REDACT),
        "data": _redact_coordinator_data(facade_data),
    }
    if isinstance(innerspace_snapshot, Mapping):
        diagnostics_data["innerspace"] = build_innerspace_diagnostics_summary(
            innerspace_snapshot,
            available=bool(getattr(coordinator, "innerspace_available", True)),
            redact_fn=async_redact_data,
            to_redact=TO_REDACT,
        )
    if data.site_manager_coordinator:
        diagnostics_data["site_manager"] = _site_manager_summary(
            data.site_manager_coordinator.data,
            entry.data.get(CONF_CONSOLE_ID, ""),
        )

    # Last pass over the assembled payload: no MAC address leaves this
    # integration, whatever key the controller sent it under.
    anonymized: dict[str, Any] = _anonymize_macs(diagnostics_data, {})

    _LOGGER.debug("Diagnostics data collected successfully")
    return anonymized
