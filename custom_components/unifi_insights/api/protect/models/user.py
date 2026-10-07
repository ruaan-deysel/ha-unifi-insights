# Copyright (c) 2026 Ruaan Deysel
"""User models for UniFi Protect API."""

from __future__ import annotations

from pydantic import BaseModel, Field

# Privacy note: email, firstName, and lastName are personal data.
# No entity, coordinator storage or diagnostics output exposes them in this PR.
# If they are ever stored in coordinator data or elsewhere, they must be added
# to the diagnostics redaction set (diagnostics.py).


class User(BaseModel):
    """Model representing a UniFi Protect user."""

    id: str
    name: str
    first_name: str | None = Field(default=None, alias="firstName")
    last_name: str | None = Field(default=None, alias="lastName")
    email: str | None = None
    ucore_user_id: str | None = Field(default=None, alias="ucoreUserId")
    model_key: str = Field(default="user", alias="modelKey")

    model_config = {"populate_by_name": True, "extra": "allow"}

    @property
    def display_name(self) -> str:
        """Get the display name for the user."""
        return (
            self.name
            or f"{self.first_name or ''} {self.last_name or ''}".strip()
            or self.id
        )
