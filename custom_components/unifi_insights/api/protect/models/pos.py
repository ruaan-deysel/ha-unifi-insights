# Copyright (c) 2026 Ruaan Deysel
"""Point of sale (POS) models for UniFi Protect API."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class PosTransactionType(StrEnum):
    """Transaction type for POS transaction."""

    SALE = "sale"
    REFUND = "refund"


class PosLineItem(BaseModel):
    """A purchased line item in a POS transaction."""

    title: str
    quantity: int

    model_config = {"populate_by_name": True, "extra": "forbid"}


class PosLocation(BaseModel):
    """Location or register identifier for a POS transaction."""

    id: str
    name: str | None = None

    model_config = {"populate_by_name": True, "extra": "forbid"}


class PosTransactionRequest(BaseModel):
    """A POS transaction to overlay on camera footage."""

    type: PosTransactionType | str
    external_id: str = Field(alias="externalId")
    amount: float
    currency: str | None = None
    line_items: list[PosLineItem] | None = Field(default=None, alias="lineItems")
    location: PosLocation | None = None
    payment_types: list[str] | None = Field(default=None, alias="paymentTypes")
    timestamp: int | None = None

    model_config = {"populate_by_name": True, "extra": "forbid"}


class PosTransactionResponse(BaseModel):
    """Result of POS transaction ingestion."""

    created: bool
    event_id: str | None = Field(default=None, alias="eventId")

    model_config = {"populate_by_name": True, "extra": "allow"}
