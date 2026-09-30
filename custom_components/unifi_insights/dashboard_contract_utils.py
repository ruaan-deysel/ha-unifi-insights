# Copyright (c) 2026 Ruaan Deysel

"""Shared helpers for dashboard snapshot contracts."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

MILLISECONDS_EPOCH_THRESHOLD = 10_000_000_000


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
        except (ValueError, OSError):
            return None
        return dt.isoformat().replace("+00:00", "Z")
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        if text.endswith("Z"):
            return text
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            return None
        dt = dt if dt.tzinfo else dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")
    return None
