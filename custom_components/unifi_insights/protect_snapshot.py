# Copyright (c) 2026 Ruaan Deysel

"""Protect status snapshot builder for dashboard cards."""

from __future__ import annotations

from typing import Any

from .dashboard_contract_utils import content_revision, utc_iso

LOW_BATTERY_PCT = 20
NEARLY_FULL_PCT = 90


def _site_from_mac(data: dict[str, Any], mac: str | None) -> str | None:
    if not mac:
        return None
    devices_by_site = (
        data.get("devices") if isinstance(data.get("devices"), dict) else {}
    )
    for site_id, devices in devices_by_site.items():
        if not isinstance(devices, dict):
            continue
        for device in devices.values():
            if isinstance(device, dict) and device.get("macAddress") == mac:
                return str(site_id)
    return None


def _is_doorbell_camera(camera_data: dict[str, Any]) -> bool:
    """Check if a camera record represents a doorbell."""
    camera_type = str(camera_data.get("_camera_type") or "").lower()
    if "doorbell" in camera_type:
        return True

    api_type = str(camera_data.get("type") or "").lower()
    if "doorbell" in api_type:
        return True

    name = str(camera_data.get("name") or "").lower()
    return "doorbell" in name


def _camera_entity_id(registry: Any, camera_id: str) -> str | None:
    unique_id = f"unifi_insights_camera_{camera_id}"
    return registry.async_get_entity_id("camera", "unifi_insights", unique_id)


def build_protect_snapshot(
    data: dict[str, Any],
    *,
    entry_id: str,
    entry_title: str,
    entity_registry: Any,
    ha_device_ids: dict[str, str],
    protect_available: bool,
) -> dict[str, Any]:
    """Build a protect status snapshot for cameras/doorbells/chimes."""
    protect = data.get("protect") if isinstance(data.get("protect"), dict) else {}
    cameras = protect.get("cameras") if isinstance(protect.get("cameras"), dict) else {}
    chimes = protect.get("chimes") if isinstance(protect.get("chimes"), dict) else {}
    nvrs = protect.get("nvrs") if isinstance(protect.get("nvrs"), dict) else {}

    if not protect:
        return build_no_protect_snapshot(entry_id, entry_title)

    devices: list[dict[str, Any]] = []
    warnings: list[str] = []

    for camera_id, camera in cameras.items():
        if not isinstance(camera, dict):
            continue
        model = str(camera.get("type") or "camera")
        is_doorbell = _is_doorbell_camera(camera)
        kind = "doorbell" if is_doorbell else "camera"
        connected = str(camera.get("state", "")).upper() == "CONNECTED"
        device_warnings: list[str] = []
        if not connected:
            device_warnings.append("offline")

        battery_pct = camera.get("batteryPercentage")
        battery_low = camera.get("batteryLow")
        battery_value = (
            int(battery_pct) if isinstance(battery_pct, (int, float)) else None
        )
        low_battery = bool(battery_low) or (
            battery_value is not None and battery_value <= LOW_BATTERY_PCT
        )
        if low_battery:
            device_warnings.append("low_battery")

        smart_types = camera.get("lastSmartDetectTypes")
        event_type = (
            smart_types[0] if isinstance(smart_types, list) and smart_types else None
        )
        last_event = utc_iso(
            camera.get("lastSmartDetect")
            or camera.get("lastMotionStart")
            or camera.get("lastRingStart")
        )

        payload = {
            "id": str(camera_id),
            "kind": kind,
            "name": str(camera.get("name") or camera_id),
            "model": model,
            "connected": connected,
            "last_seen_at": utc_iso(camera.get("lastSeen")),
            "site_id": _site_from_mac(data, camera.get("mac")),
            "ha_device_id": ha_device_ids.get(str(camera_id))
            or ha_device_ids.get(f"protect_camera_{camera_id}"),
            "camera_entity_id": _camera_entity_id(entity_registry, str(camera_id)),
            "warnings": device_warnings,
            "motion_active": bool(
                camera.get("isMotionDetected") or camera.get("isMotionDetectedByPir")
            ),
            "is_recording": bool(
                camera.get("isRecording")
                or camera.get("recordingSettings", {}).get("mode")
                not in {None, "never"}
            ),
            "recording_mode": (
                camera.get("recordingSettings", {}).get("mode")
                if isinstance(camera.get("recordingSettings"), dict)
                else None
            ),
            "last_event_at": last_event,
            "last_event_type": event_type,
            "last_ring_at": (
                utc_iso(camera.get("lastRingStart")) if is_doorbell else None
            ),
        }
        if battery_value is not None or battery_low is not None:
            payload["battery"] = {"percentage": battery_value, "low": low_battery}

        devices.append(payload)

    for chime_id, chime in chimes.items():
        if not isinstance(chime, dict):
            continue
        connected = str(chime.get("state", "")).upper() == "CONNECTED"
        chime_warnings = ["offline"] if not connected else []
        payload = {
            "id": str(chime_id),
            "kind": "chime",
            "name": str(chime.get("name") or chime_id),
            "model": str(chime.get("type") or "chime"),
            "connected": connected,
            "last_seen_at": utc_iso(chime.get("lastSeen")),
            "site_id": None,
            "ha_device_id": ha_device_ids.get(str(chime_id))
            or ha_device_ids.get(f"protect_chime_{chime_id}"),
            "camera_entity_id": None,
            "warnings": chime_warnings,
            "last_ring_at": None,
        }
        devices.append(payload)

    storage_unhealthy = False
    storage_nearly_full = False
    for nvr in nvrs.values():
        if not isinstance(nvr, dict):
            continue
        storage = nvr.get("storage")
        if not isinstance(storage, dict):
            continue
        healthy = storage.get("healthy")
        if healthy is False:
            storage_unhealthy = True
        used_pct = storage.get("used")
        try:
            used = float(used_pct)
        except TypeError, ValueError:
            used = None
        if used is not None and used >= NEARLY_FULL_PCT:
            storage_nearly_full = True

    if storage_unhealthy:
        warnings.append("storage_unhealthy")
    if storage_nearly_full:
        warnings.append("storage_nearly_full")

    stale = not protect_available
    status = (
        "degraded"
        if (warnings or any(d.get("warnings") for d in devices) or stale)
        else "ok"
    )

    payload: dict[str, Any] = {
        "schema_version": 1,
        "entry_id": entry_id,
        "entry_title": entry_title,
        "status": "unavailable" if not devices and stale else status,
        "warnings": warnings,
        "devices": devices,
        "issues": (
            [{"code": "protect_unavailable", "severity": "warning"}] if stale else []
        ),
    }
    payload["revision"] = content_revision(payload)
    return payload


def build_no_protect_snapshot(entry_id: str, entry_title: str) -> dict[str, Any]:
    """Return snapshot for entries that do not have Protect configured."""
    return {
        "schema_version": 1,
        "entry_id": entry_id,
        "entry_title": entry_title,
        "status": "no_protect",
        "warnings": [],
        "issues": [],
        "devices": [],
        "revision": "",
    }


def build_unavailable_protect_snapshot(
    entry_id: str, entry_title: str, code: str
) -> dict[str, Any]:
    """Return unavailable protect snapshot."""
    return {
        "schema_version": 1,
        "entry_id": entry_id,
        "entry_title": entry_title,
        "status": "unavailable",
        "warnings": [],
        "issues": [{"code": code, "severity": "error"}],
        "devices": [],
        "revision": "",
    }
