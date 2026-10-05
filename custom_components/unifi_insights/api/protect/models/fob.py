"""Fob models for UniFi Protect API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class FobKeypadSettings(BaseModel):
    """
    Keypad settings of a fob with a PIN keypad (Protect 7.3.70+).

    Read-only in the public API: ``PATCH /v1/fobs/{id}`` accepts ``name`` only.
    Fields are optional and unconstrained so an out-of-range value cannot make
    the endpoint drop the fob.
    """

    beep_enabled: bool | None = Field(default=None, alias="beepEnabled")
    beep_volume: int | None = Field(default=None, alias="beepVolume")  # 0-100

    model_config = {"populate_by_name": True, "extra": "allow"}


class FobArmControlSettings(BaseModel):
    """Which external arm profiles a fob arms and disarms (Protect 7.3.70+)."""

    enabled: bool | None = None
    arm_profile_id: str | None = Field(default=None, alias="armProfileId")
    night_profile_id: str | None = Field(default=None, alias="nightProfileId")

    model_config = {"populate_by_name": True, "extra": "allow"}


class Fob(BaseModel):
    """Model representing a UniFi Protect key fob."""

    id: str
    model_key: str | None = Field(default=None, alias="modelKey")
    state: str | None = None
    name: str | None = None
    mac: str | None = None
    away_state: str | None = Field(default=None, alias="awayState")
    # The spec types this as a string enum ("securityActions"/"positionHint");
    # the container forms are kept for any payload that was relying on them.
    button_labels: str | dict[str, Any] | list[Any] | None = Field(
        default=None, alias="buttonLabels"
    )
    feature_flags: dict[str, Any] | None = Field(default=None, alias="featureFlags")
    wireless_connection_state: dict[str, Any] | None = Field(
        default=None, alias="wirelessConnectionState"
    )
    keypad_settings: FobKeypadSettings | None = Field(
        default=None, alias="keypadSettings"
    )
    arm_control_settings: FobArmControlSettings | None = Field(
        default=None, alias="armControlSettings"
    )

    model_config = {"populate_by_name": True, "extra": "allow"}

    @property
    def display_name(self) -> str:
        """Get the display name for the fob."""
        return self.name or self.mac or self.id
