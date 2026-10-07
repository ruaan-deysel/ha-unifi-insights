# Copyright (c) 2026 Ruaan Deysel
"""UniFi Identity (ULP) user models for UniFi Protect API."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

# Privacy note: email, firstName, lastName, and fullName are personal data.
# No entity, coordinator storage or diagnostics output exposes them in this PR.
# If they are ever stored in coordinator data or elsewhere, they must be added
# to the diagnostics redaction set (diagnostics.py).


class UlpUserStatus(StrEnum):
    """Status of a UniFi Identity (ULP) user."""

    ACTIVE = "ACTIVE"
    DEACTIVATED = "DEACTIVATED"


class UlpUser(BaseModel):
    """Model representing a UniFi Identity user with enrolled credentials."""

    id: str
    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")
    full_name: str = Field(alias="fullName")
    email: str = ""
    status: UlpUserStatus | str
    model_key: str = Field(default="ulpUser", alias="modelKey")

    model_config = {"populate_by_name": True, "extra": "allow"}

    @property
    def display_name(self) -> str:
        """Get the display name for the ULP user."""
        return (
            self.full_name or f"{self.first_name} {self.last_name}".strip() or self.id
        )
