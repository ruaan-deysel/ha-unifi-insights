"""Pydantic models for UniFi Network historical site traffic reports."""

from __future__ import annotations

import math
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

SITE_REPORT_INTERVALS: frozenset[str] = frozenset({"5minutes", "hourly", "daily"})
DEFAULT_SITE_REPORT_ATTRS: tuple[str, ...] = (
    "time",
    "wan-rx_bytes",
    "wan-tx_bytes",
    "wan2-rx_bytes",
    "wan2-tx_bytes",
)


def _coerce_optional_bytes(value: Any) -> float | None:
    """Coerce a report byte counter to a non-negative float or return None."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        numeric = float(value)
        if math.isfinite(numeric) and numeric >= 0:
            return numeric
    return None


class SiteReportBucket(BaseModel):
    """
    One historical site traffic report bucket from ``/stat/report/{interval}.site``.

    The UniFi Network controller returns ``time`` as a millisecond epoch
    timestamp and WAN byte counters as numeric (``int`` or ``float``) values.
    Missing or non-numeric byte fields are treated as ``None`` rather than zero.
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    time: int = Field(description="Bucket timestamp in milliseconds since epoch")
    wan_rx_bytes: float | None = Field(default=None, alias="wan-rx_bytes")
    wan_tx_bytes: float | None = Field(default=None, alias="wan-tx_bytes")
    wan2_rx_bytes: float | None = Field(default=None, alias="wan2-rx_bytes")
    wan2_tx_bytes: float | None = Field(default=None, alias="wan2-tx_bytes")

    @field_validator("time", mode="before")
    @classmethod
    def _validate_time(cls, value: Any) -> int:
        """Validate that the bucket timestamp is a finite integer or float."""
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            msg = "time must be a numeric millisecond timestamp"
            raise ValueError(msg)
        if not math.isfinite(float(value)):
            msg = "time must be finite"
            raise ValueError(msg)
        return int(value)

    @field_validator(
        "wan_rx_bytes",
        "wan_tx_bytes",
        "wan2_rx_bytes",
        "wan2_tx_bytes",
        mode="before",
    )
    @classmethod
    def _validate_optional_bytes(cls, value: Any) -> float | None:
        """Treat missing or non-numeric WAN byte fields as absent (None)."""
        return _coerce_optional_bytes(value)

    @property
    def rx_bytes(self) -> int | None:
        """Return combined download (RX) bytes across present WAN interfaces."""
        present = [
            val for val in (self.wan_rx_bytes, self.wan2_rx_bytes) if val is not None
        ]
        if not present:
            return None
        return round(sum(present))

    @property
    def tx_bytes(self) -> int | None:
        """Return combined upload (TX) bytes across present WAN interfaces."""
        present = [
            val for val in (self.wan_tx_bytes, self.wan2_tx_bytes) if val is not None
        ]
        if not present:
            return None
        return round(sum(present))

    @property
    def total_rx_bytes(self) -> int | None:
        """Alias for combined download (RX) bytes across present WAN interfaces."""
        return self.rx_bytes

    @property
    def total_tx_bytes(self) -> int | None:
        """Alias for combined upload (TX) bytes across present WAN interfaces."""
        return self.tx_bytes
