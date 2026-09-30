# Copyright (c) 2026 Ruaan Deysel

"""Event timeline snapshot builder for dashboard cards."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from .dashboard_contract_utils import content_revision, utc_iso

TIMELINE_VERSION = 1
DEFAULT_HOURS = 6
DEFAULT_MAX_ITEMS = 10
MAX_ITEMS = 50


KIND_TO_SEVERITY: dict[str, str] = {
    "ring": "warning",
    "person": "warning",
    "package": "warning",
    "motion": "info",
    "vehicle": "info",
    "animal": "info",
    "sensor_opened": "info",
    "sensor_closed": "info",
}


def build_timeline_snapshot(
    data: dict[str, Any],
    *,
    entry_id: str,
    site_id: str,
    categories: list[str] | None = None,
    hours: int = DEFAULT_HOURS,
    max_items: int = DEFAULT_MAX_ITEMS,
) -> dict[str, Any]:
    """Build a compact recent-activity timeline from cached Protect events."""
    categories = categories or ["security"]
    max_items = max(1, min(MAX_ITEMS, max_items))
    hours = max(1, min(24, hours))

    protect = data.get("protect") if isinstance(data.get("protect"), dict) else {}
    events = protect.get("events") if isinstance(protect.get("events"), dict) else {}

    cutoff = datetime.now(tz=UTC) - timedelta(hours=hours)
    items: list[dict[str, Any]] = []
    if "security" in categories:
        for event_type, by_id in events.items():
            if not isinstance(by_id, dict):
                continue
            for event_id, event_data in by_id.items():
                if not isinstance(event_data, dict):
                    continue
                ts = utc_iso(
                    event_data.get("start")
                    or event_data.get("time")
                    or event_data.get("timestamp")
                )
                if ts is None:
                    continue
                try:
                    dt = datetime.fromisoformat(ts)
                except ValueError:
                    continue
                if dt < cutoff:
                    continue

                kind = str(event_type)
                source_name = str(
                    event_data.get("name")
                    or event_data.get("deviceName")
                    or event_data.get("device_id")
                    or "Protect device"
                )
                item = {
                    "id": f"evt:{event_id}",
                    "kind": kind,
                    "category": "security",
                    "severity": KIND_TO_SEVERITY.get(kind, "info"),
                    "timestamp": ts,
                    "time_source": "device",
                    "count": 1,
                    "scope": "entry",
                    "site_id": None,
                    "source": {
                        "id": str(
                            event_data.get("device_id")
                            or event_data.get("id")
                            or event_id
                        ),
                        "name": source_name,
                        "kind": "camera"
                        if kind
                        in {"motion", "ring", "person", "vehicle", "animal", "package"}
                        else "sensor",
                    },
                    "ha_device_id": None,
                    "camera_entity_id": None,
                }
                items.append(item)

    items.sort(key=lambda item: item["timestamp"], reverse=True)
    total = len(items)
    included_items = items[:max_items]
    issues: list[dict[str, str]] = []
    if total > len(included_items):
        issues.append({"code": "events_truncated", "severity": "info"})

    payload: dict[str, Any] = {
        "version": TIMELINE_VERSION,
        "entry_id": entry_id,
        "site_id": site_id,
        "status": "ok",
        "issues": issues,
        "recording_since": included_items[-1]["timestamp"] if included_items else None,
        "total": total,
        "included": len(included_items),
        "items": included_items,
    }
    payload["revision"] = content_revision(payload)
    return payload


def build_unavailable_timeline(
    entry_id: str, site_id: str, code: str
) -> dict[str, Any]:
    """Return unavailable timeline snapshot."""
    return {
        "version": TIMELINE_VERSION,
        "entry_id": entry_id,
        "site_id": site_id,
        "status": "unavailable",
        "issues": [{"code": code, "severity": "error"}],
        "recording_since": None,
        "total": 0,
        "included": 0,
        "items": [],
        "revision": "",
    }
