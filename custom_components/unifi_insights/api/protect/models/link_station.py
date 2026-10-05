"""Link station / alarm-hub models for UniFi Protect API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class LinkStationThreadNetwork(BaseModel):
    """
    Thread mesh status reported by a Thread-capable gateway (Protect 7.3.70+).

    Every field is optional and unconstrained on purpose: the endpoint drops a
    whole device on a ValidationError, so a new firmware enum value (a new
    Thread role, say) must parse rather than make the gateway vanish. The
    spec's enums and ranges are noted per field and enforced in the entities.
    """

    status: str | None = None  # "ready" | "error"
    role: str | None = None  # disabled | detached | child | router | leader
    network_name: str | None = Field(default=None, alias="networkName")
    channel: int | None = None  # 11-26 per spec
    pan_id: str | None = Field(default=None, alias="panId")
    extended_pan_id: str | None = Field(default=None, alias="extendedPanId")
    joined_device_count: int | None = Field(default=None, alias="joinedDeviceCount")
    error_reason: str | None = Field(default=None, alias="errorReason")
    # Epoch milliseconds of the gateway's last refresh of this status.
    last_updated_at: float | None = Field(default=None, alias="lastUpdatedAt")

    model_config = {"populate_by_name": True, "extra": "allow"}


class LinkStationThreadState(BaseModel):
    """Thread state wrapper; ``network`` is null on SKUs without Thread."""

    network: LinkStationThreadNetwork | None = None

    model_config = {"populate_by_name": True, "extra": "allow"}


class LinkStation(BaseModel):
    """
    Model representing a UniFi Protect link station.

    The Protect API returns the same ``linkStation`` schema for both the
    ``/link-stations`` and ``/alarm-hubs`` resources; ``is_alarm_hub``
    distinguishes an alarm hub from a plain link station.
    """

    id: str
    model_key: str | None = Field(default=None, alias="modelKey")
    state: str | None = None
    name: str | None = None
    mac: str | None = None
    is_alarm_hub: bool | None = Field(default=None, alias="isAlarmHub")
    led_settings: dict[str, Any] | None = Field(default=None, alias="ledSettings")
    # The spec types this as epoch milliseconds; the dict form is kept for any
    # payload that was relying on it.
    last_event: int | float | dict[str, Any] | None = Field(
        default=None, alias="lastEvent"
    )
    alarm_hub: dict[str, Any] | None = Field(default=None, alias="alarmHub")
    # Required by the 7.3.70 spec, but a real UP-SuperLink-US on 7.3.70 omits
    # it entirely, so absence has to parse.
    thread_state: LinkStationThreadState | None = Field(
        default=None, alias="threadState"
    )

    model_config = {"populate_by_name": True, "extra": "allow"}

    @property
    def display_name(self) -> str:
        """Get the display name for the link station."""
        return self.name or self.mac or self.id


# Alarm hubs use the same schema as link stations.
AlarmHub = LinkStation
