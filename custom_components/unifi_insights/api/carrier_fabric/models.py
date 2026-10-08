# Copyright (c) 2026 Ruaan Deysel
"""Pydantic models for the UniFi Carrier Fabric API."""

from __future__ import annotations

from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator


class CarrierFabricBaseModel(BaseModel):
    """Base model for Carrier Fabric records."""

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
    )


class Subscriber(CarrierFabricBaseModel):
    """UniFi Carrier Fabric Subscriber model."""

    id: str
    org_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("orgId", "org_id"),
        serialization_alias="orgId",
    )
    subscriber_number: str | None = Field(
        default=None,
        validation_alias=AliasChoices("subscriberNumber", "subscriber_number"),
        serialization_alias="subscriberNumber",
    )
    name: str | None = None
    email: str | None = None
    notes: str | None = None
    service_address: str | None = Field(
        default=None,
        validation_alias=AliasChoices("serviceAddress", "service_address"),
        serialization_alias="serviceAddress",
    )
    plan_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("planId", "plan_id"),
        serialization_alias="planId",
    )
    host_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("hostId", "host_id"),
        serialization_alias="hostId",
    )
    state: str | None = None
    suspended: bool = False
    suspend_reason: str | None = Field(
        default=None,
        validation_alias=AliasChoices("suspendReason", "suspend_reason"),
        serialization_alias="suspendReason",
    )
    suspended_at: str | None = Field(
        default=None,
        validation_alias=AliasChoices("suspendedAt", "suspended_at"),
        serialization_alias="suspendedAt",
    )
    activated_at: str | None = Field(
        default=None,
        validation_alias=AliasChoices("activatedAt", "activated_at"),
        serialization_alias="activatedAt",
    )
    created_at: str | None = Field(
        default=None,
        validation_alias=AliasChoices("createdAt", "created_at"),
        serialization_alias="createdAt",
    )
    updated_at: str | None = Field(
        default=None,
        validation_alias=AliasChoices("updatedAt", "updated_at"),
        serialization_alias="updatedAt",
    )
    metadata: dict[str, Any] | None = None

    @model_validator(mode="before")
    @classmethod
    def _coerce_null_suspended(cls, data: Any) -> Any:
        """Coerce None to False for suspended field."""
        if isinstance(data, dict) and data.get("suspended") is None:
            data = dict(data)
            data["suspended"] = False
        return data


class HostLinkResponse(CarrierFabricBaseModel):
    """Response of attaching or detaching a subscriber's gateway host."""

    subscriber: Subscriber = Field(
        validation_alias=AliasChoices("data", "subscriber"),
        serialization_alias="data",
    )
    # The host linked before the call: None on a fresh attach, the replaced
    # host on a re-link, the removed host on a detach.
    prev_host_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("prevHostId", "prev_host_id"),
        serialization_alias="prevHostId",
    )


class ServicePlan(CarrierFabricBaseModel):
    """UniFi Carrier Fabric Service Plan model."""

    id: str
    org_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("orgId", "org_id"),
        serialization_alias="orgId",
    )
    name: str | None = None
    status: str | None = None
    download_mbps: float | None = Field(
        default=None,
        validation_alias=AliasChoices("downloadMbps", "download_mbps"),
        serialization_alias="downloadMbps",
    )
    upload_mbps: float | None = Field(
        default=None,
        validation_alias=AliasChoices("uploadMbps", "upload_mbps"),
        serialization_alias="uploadMbps",
    )
    archived_at: str | None = Field(
        default=None,
        validation_alias=AliasChoices("archivedAt", "archived_at"),
        serialization_alias="archivedAt",
    )
    created_at: str | None = Field(
        default=None,
        validation_alias=AliasChoices("createdAt", "created_at"),
        serialization_alias="createdAt",
    )
    updated_at: str | None = Field(
        default=None,
        validation_alias=AliasChoices("updatedAt", "updated_at"),
        serialization_alias="updatedAt",
    )
    metadata: dict[str, Any] | None = None


class CarrierFabricMeta(CarrierFabricBaseModel):
    """Pagination metadata in Carrier Fabric list responses."""

    next_cursor: str | None = Field(
        default=None,
        validation_alias=AliasChoices("nextCursor", "next_cursor"),
        serialization_alias="nextCursor",
    )
    limit: int | None = None
    has_more: bool | None = Field(
        default=None,
        validation_alias=AliasChoices("hasMore", "has_more"),
        serialization_alias="hasMore",
    )
