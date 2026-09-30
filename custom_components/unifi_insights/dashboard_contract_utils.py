# Copyright (c) 2026 Ruaan Deysel

"""Shared helpers for dashboard snapshot contracts."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from enum import Enum
from typing import Any

MILLISECONDS_EPOCH_THRESHOLD = 10_000_000_000


def as_dict(value: Any) -> dict[str, Any]:
    """Return value if it is a dict, otherwise an empty dict."""
    return value if isinstance(value, dict) else {}


def enum_str(value: Any, default: str = "") -> str:
    """Return the underlying string value for str or Enum without class prefixes."""
    if isinstance(value, Enum):
        return str(value.value)
    if isinstance(value, str):
        return value
    if value is None:
        return default
    return str(value)


def is_protect_device_connected(device: dict[str, Any]) -> bool:
    """Return True if a Protect device dict represents a connected/online device."""
    state = enum_str(device.get("state") or device.get("status")).strip().upper()
    if state in {"CONNECTED", "ONLINE", "UP"}:
        return True
    if state in {"DISCONNECTED", "OFFLINE", "DOWN"}:
        return False
    is_conn = device.get("isConnected")
    if is_conn is None:
        is_conn = device.get("is_connected")
    return bool(is_conn)


def content_revision(
    payload: dict[str, Any], *, exclude: set[str] | None = None
) -> str:
    """Return a deterministic short revision hash for a payload."""
    body = {k: v for k, v in payload.items() if not exclude or k not in exclude}
    encoded = json.dumps(body, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode()).hexdigest()[:16]


def utc_iso(value: Any) -> str | None:
    """Convert epoch seconds/milliseconds or datetime to UTC ISO-8601."""
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value if value.tzinfo else value.replace(tzinfo=UTC)
        return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")
    if isinstance(value, (int, float)):
        # Protect timestamps are commonly milliseconds.
        ts = value / 1000 if value > MILLISECONDS_EPOCH_THRESHOLD else value
        try:
            dt = datetime.fromtimestamp(ts, tz=UTC)
        except (ValueError, OSError, OverflowError):  # fmt: skip
            return None
        return dt.isoformat().replace("+00:00", "Z")
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            return None
        dt = dt if dt.tzinfo else dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")
    return None
