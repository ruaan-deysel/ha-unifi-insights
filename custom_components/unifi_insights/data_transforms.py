"""
Data transformation functions for vendored UniFi API responses.

This module provides transformation functions to convert vendored API
response formats to the internal data structures expected by entities,
maintaining backward compatibility.
"""

from __future__ import annotations

import ipaddress
import math
from typing import Any

from .innerspace_transforms import (
    _normalize_innerspace_mac,
    correlate_innerspace_devices,
    normalize_innerspace_snapshot,
    parse_floor_plan_asset_path,
    transform_innerspace_device,
    transform_innerspace_floor_plan,
    transform_innerspace_project,
)


def map_device_status(lib_status: str | None) -> str:
    """
    Map library device status to internal format.

    Args:
        lib_status: Status from library ("online", "offline", "unknown")

    Returns:
        Internal status format ("connected", "disconnected", "unknown")

    """
    if not lib_status:
        return "unknown"

    status_map = {
        "online": "connected",
        "offline": "disconnected",
        "unknown": "unknown",
    }
    return status_map.get(lib_status.lower(), lib_status)


def transform_network_device(lib_device: dict) -> dict:
    """
    Transform library network device response to internal format.

    Args:
        lib_device: Device data from the vendored UniFi API package

    Returns:
        Transformed device data in internal format

    """
    return {
        "id": lib_device.get("id"),
        "mac": lib_device.get("mac"),
        "model": lib_device.get("model"),
        "name": lib_device.get("name"),
        "state": map_device_status(lib_device.get("status")),
        "adopted": lib_device.get("adopted"),
        "version": lib_device.get("firmware_version"),
        "uptime": lib_device.get("uptime_seconds"),
        "cpu_usage": lib_device.get("cpu_percent"),
        "memory_usage": lib_device.get("memory_percent"),
        "tx_bytes": lib_device.get("tx_bytes"),
        "rx_bytes": lib_device.get("rx_bytes"),
        "site_id": lib_device.get("site"),
    }


def transform_protect_camera(lib_camera: dict) -> dict:
    """
    Transform library Protect camera response to internal format.

    Args:
        lib_camera: Camera data from the vendored UniFi API package

    Returns:
        Transformed camera data in internal format

    """
    return {
        "id": lib_camera.get("id"),
        "name": lib_camera.get("name"),
        "state": lib_camera.get("status", "").upper()
        if lib_camera.get("status")
        else "UNKNOWN",
        "is_recording": lib_camera.get("recording"),
        "motion_detected": lib_camera.get("motion"),
        "type": lib_camera.get("model"),
        "hdr_mode": lib_camera.get("hdr", "").upper()
        if lib_camera.get("hdr")
        else "AUTO",
        "video_mode": lib_camera.get("video_mode", "").upper()
        if lib_camera.get("video_mode")
        else "DEFAULT",
        "is_dark": lib_camera.get("is_dark", False),
        # snapshot_url and rtsps_url generated on-demand via client methods
    }


def transform_protect_light(lib_light: dict) -> dict:
    """
    Transform library Protect light response to internal format.

    Args:
        lib_light: Light data from the vendored UniFi API package

    Returns:
        Transformed light data in internal format

    """
    return {
        "id": lib_light.get("id"),
        "name": lib_light.get("name"),
        "is_on": lib_light.get("on"),
        "brightness": lib_light.get("brightness"),
        "mode": lib_light.get("light_mode", "").upper()
        if lib_light.get("light_mode")
        else "AUTO",
        "is_dark": lib_light.get("dark", False),
    }


def transform_protect_sensor(lib_sensor: dict) -> dict:
    """
    Transform library Protect sensor response to internal format.

    Args:
        lib_sensor: Sensor data from the vendored UniFi API package

    Returns:
        Transformed sensor data in internal format

    """
    return {
        "id": lib_sensor.get("id"),
        "name": lib_sensor.get("name"),
        "temperature": lib_sensor.get("temperature"),
        "humidity": lib_sensor.get("humidity"),
        "light_level": lib_sensor.get("light"),
        "battery_percentage": lib_sensor.get("battery"),
    }


def transform_protect_chime(lib_chime: dict) -> dict:
    """
    Transform library Protect chime response to internal format.

    Args:
        lib_chime: Chime data from the vendored UniFi API package

    Returns:
        Transformed chime data in internal format

    """
    return {
        "id": lib_chime.get("id"),
        "name": lib_chime.get("name"),
        "volume": lib_chime.get("volume"),
        "repeat_times": lib_chime.get("repeat"),
        "ringtone_id": lib_chime.get("ringtone"),
    }


def _is_unspecified_address(value: str) -> bool:
    """Return True for 0.0.0.0 / ::, the placeholder a down link reports."""
    try:
        return ipaddress.ip_address(value).is_unspecified
    except ValueError:
        return False


def normalize_legacy_wans(legacy_device: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Return per-WAN connection state from a legacy gateway record.

    The gateway's ``wan1..wanN`` blocks describe the physical ports (type
    "ethernet", name "eth8"), not the internet connection, so they cannot
    tell a dropped PPPoE session from a connected one. The controller's own
    per-WAN verdict lives in ``last_wan_status`` ({"WAN": "online"}) and
    ``last_wan_interfaces`` ({"WAN": {"ip": ..., "alive": true}}), keyed by
    the same WAN names the UniFi UI shows. A WAN that is configured but not
    in use does not appear in either.
    """
    statuses = legacy_device.get("last_wan_status")
    interfaces = legacy_device.get("last_wan_interfaces")
    statuses = statuses if isinstance(statuses, dict) else {}
    interfaces = interfaces if isinstance(interfaces, dict) else {}

    wans: list[dict[str, Any]] = []
    for name in dict.fromkeys((*statuses, *interfaces)):
        if not isinstance(name, str) or not name:
            continue
        status = statuses.get(name)
        status = status if isinstance(status, str) else None
        interface = interfaces.get(name)
        interface = interface if isinstance(interface, dict) else {}
        alive = interface.get("alive")
        alive = alive if isinstance(alive, bool) else None
        ip = interface.get("ip")
        has_ip = isinstance(ip, str) and bool(ip) and not _is_unspecified_address(ip)
        wans.append(
            {
                "key": name.lower(),
                "name": name,
                "status": status,
                "alive": alive,
                "ip": ip if has_ip else None,
                # The controller's status is authoritative; "alive" (its
                # reachability probe) only decides when no status is given.
                "connected": (
                    status.lower() == "online" if status is not None else alive is True
                ),
            }
        )
    return wans


# Filesystems that live in RAM or are recreated at boot. They fill and empty
# constantly, so their entities are disabled by default and they never count
# towards "storage nearly full". Matched on the mount path (and the type when a
# console names one): the classic "other" type is NOT a signal, an HDD console
# may report a real array as "other".
_VOLATILE_MOUNT_PREFIXES: tuple[str, ...] = (
    "/" + "tmp",
    "/run",
    "/var/run",
    "/" + "var/tmp",
    "/" + "dev/shm",
)
_VOLATILE_MOUNT_TYPES: frozenset[str] = frozenset({"tmpfs", "ramfs"})


def _clean_text(value: Any) -> str | None:
    """Return a stripped non-empty string, or None."""
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value or None


def _storage_bytes(value: Any) -> int | None:
    """Return a byte count, or None for anything that is not a sane number."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if not math.isfinite(value) or value < 0:
        return None
    return int(value)


def normalize_legacy_storage(legacy_device: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Return the per-mount storage of a legacy (classic) device record.

    Consoles report ``storage`` as a list of ``{mount_point, name, type, size,
    used}`` (sizes in bytes). Entries without a usable ``mount_point`` are
    dropped and a repeated mount point keeps its first entry. Sizes that are
    not finite non-negative numbers become ``None`` so a bad reading reads as
    unknown rather than as 0 or full. ``name`` and ``type`` become ``None``
    when blank. The list is empty when the device reports no storage.
    """
    raw = legacy_device.get("storage")
    if not isinstance(raw, list):
        return []
    mounts: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, dict):
            continue
        mount_point = _clean_text(item.get("mount_point"))
        if mount_point is None or mount_point in seen:
            continue
        seen.add(mount_point)
        mounts.append(
            {
                "mount_point": mount_point,
                "name": _clean_text(item.get("name")),
                "type": _clean_text(item.get("type")),
                "size": _storage_bytes(item.get("size")),
                "used": _storage_bytes(item.get("used")),
            }
        )
    return mounts


def storage_used_percent(mount: dict[str, Any]) -> float | None:
    """
    Return how full a normalised mount is, in percent with one decimal.

    None when either size is unknown or the size is 0. A mount that reports
    more used than its size (a quirk of some filesystems) reads 100.0.
    """
    size = mount.get("size")
    used = mount.get("used")
    if size is None or used is None or size <= 0:
        return None
    return float(min(100.0, round(float(used) / float(size) * 100, 1)))


def is_volatile_storage_mount(mount: dict[str, Any]) -> bool:
    """Return True for RAM-backed or boot-recreated mounts such as ``/tmp``."""
    mount_point = str(mount.get("mount_point") or "").lower()
    if any(
        mount_point == prefix or mount_point.startswith(f"{prefix}/")
        for prefix in _VOLATILE_MOUNT_PREFIXES
    ):
        return True
    return str(mount.get("type") or "").lower() in _VOLATILE_MOUNT_TYPES


__all__ = [
    "_normalize_innerspace_mac",
    "correlate_innerspace_devices",
    "is_volatile_storage_mount",
    "map_device_status",
    "normalize_innerspace_snapshot",
    "normalize_legacy_storage",
    "normalize_legacy_wans",
    "parse_floor_plan_asset_path",
    "storage_used_percent",
    "transform_innerspace_device",
    "transform_innerspace_floor_plan",
    "transform_innerspace_project",
    "transform_network_device",
    "transform_protect_camera",
    "transform_protect_chime",
    "transform_protect_light",
    "transform_protect_sensor",
]
