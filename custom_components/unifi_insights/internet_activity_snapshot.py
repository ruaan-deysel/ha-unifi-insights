# Copyright (c) 2026 Ruaan Deysel

"""Internet activity snapshot builder for dashboard cards."""

from __future__ import annotations

from typing import Any

from .dashboard_contract_utils import content_revision
from .topology_contract import site_display_name

WINDOWS = ("1h", "1d", "1w", "1m")


def _resolve_entity_ids(
    registry: Any,
    *,
    site_id: str,
) -> dict[str, str]:
    ids: dict[str, str] = {}
    # Sensor keys implemented by site_internet_activity_sensor.py
    for direction in ("download", "upload"):
        for window in WINDOWS:
            uid = f"{site_id}_internet_{direction}_{window}"
            entity_id = registry.async_get_entity_id("sensor", "unifi_insights", uid)
            if entity_id:
                ids[f"{direction}_{window}"] = entity_id
    return ids


def build_internet_activity_snapshot(
    data: dict[str, Any],
    *,
    entry_id: str,
    site_id: str,
    entity_registry: Any,
) -> dict[str, Any]:
    """Build one site's internet-activity snapshot."""
    activity_by_site = (
        data.get("internet_activity")
        if isinstance(data.get("internet_activity"), dict)
        else {}
    )
    unavailable_sites = data.get("internet_activity_unavailable")
    unavailable_sites = (
        unavailable_sites if isinstance(unavailable_sites, set) else set()
    )

    if site_id in unavailable_sites:
        return build_unavailable_internet_activity(
            entry_id, site_id, "site_unavailable"
        )

    windows_data = activity_by_site.get(site_id)
    if not isinstance(windows_data, dict):
        return build_unavailable_internet_activity(
            entry_id, site_id, "site_unavailable"
        )

    # Gateway WAN health/rates from current site gateway if present.
    devices_by_site = (
        data.get("devices") if isinstance(data.get("devices"), dict) else {}
    )
    stats_by_site = data.get("stats") if isinstance(data.get("stats"), dict) else {}
    devices = devices_by_site.get(site_id)
    stats = stats_by_site.get(site_id)
    devices = devices if isinstance(devices, dict) else {}
    stats = stats if isinstance(stats, dict) else {}

    gateway: dict[str, Any] | None = None
    gateway_id: str | None = None
    for did, device in devices.items():
        if not isinstance(device, dict):
            continue
        model = str(device.get("type", "")).lower()
        legacy = (
            str(device.get("topology", {}).get("legacy_type", "")).lower()
            if isinstance(device.get("topology"), dict)
            else ""
        )
        if "gateway" in model or legacy in {"udm", "ugw", "uxg", "udr", "ucg"}:
            gateway = device
            gateway_id = did
            break

    throughput = None
    wan_links: list[dict[str, Any]] = []
    gateway_online = False
    if gateway_id is not None and gateway is not None:
        metric = (
            stats.get(gateway_id) if isinstance(stats.get(gateway_id), dict) else {}
        )
        tx = metric.get("tx_rate") or metric.get("txRate")
        rx = metric.get("rx_rate") or metric.get("rxRate")
        try:
            tx_bps = int(float(tx) * 8) if tx is not None else None
        except (TypeError, ValueError):
            tx_bps = None
        try:
            rx_bps = int(float(rx) * 8) if rx is not None else None
        except (TypeError, ValueError):
            rx_bps = None
        throughput = {"tx_bps": tx_bps, "rx_bps": rx_bps, "source": "gateway_uplink"}
        gateway_online = str(gateway.get("state", "")).upper() in {
            "ONLINE",
            "CONNECTED",
            "UP",
        }

        wans = gateway.get("wans")
        if isinstance(wans, list):
            for idx, wan in enumerate(wans):
                if not isinstance(wan, dict):
                    continue
                connected = wan.get("connected")
                status = wan.get("status")
                wan_links.append(
                    {
                        "wan_key": str(wan.get("wan_key", f"WAN{idx + 1}")),
                        "connected": bool(connected)
                        if isinstance(connected, bool)
                        else None,
                        "status": str(status) if isinstance(status, str) else None,
                    }
                )

    windows: dict[str, Any] = {}
    for window in WINDOWS:
        totals = windows_data.get(window)
        if not isinstance(totals, dict):
            continue
        rx = totals.get("rx_bytes")
        tx = totals.get("tx_bytes")
        windows[window] = {
            "download_bytes": int(rx) if isinstance(rx, (int, float)) else None,
            "upload_bytes": int(tx) if isinstance(tx, (int, float)) else None,
            "report_interval": window,
            "available": True,
            "series": [],
            "coverage": None,
            "partial": False,
            "peak": None,
        }

    payload: dict[str, Any] = {
        "version": 1,
        "entry_id": entry_id,
        "site_id": site_id,
        "site_name": site_display_name(data, site_id),
        "status": "ok",
        "issues": [],
        "windows": windows,
        "entity_ids": _resolve_entity_ids(
            entity_registry,
            site_id=site_id,
        ),
        "throughput": throughput,
        "wan_health": {
            "gateway_online": gateway_online,
            "links": wan_links,
        },
    }
    payload["revision"] = content_revision(payload)
    return payload


def build_unavailable_internet_activity(
    entry_id: str, site_id: str, code: str
) -> dict[str, Any]:
    """Return an unavailable internet-activity payload."""
    return {
        "version": 1,
        "entry_id": entry_id,
        "site_id": site_id,
        "site_name": site_id,
        "status": "unavailable",
        "issues": [{"code": code, "severity": "error"}],
        "windows": {},
        "entity_ids": {},
        "throughput": None,
        "wan_health": {"gateway_online": False, "links": []},
        "revision": "",
    }
