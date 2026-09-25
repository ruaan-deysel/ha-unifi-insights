"""Pydantic models for the UniFi InnerSpace API."""

from __future__ import annotations

from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator


class InnerSpaceBaseModel(BaseModel):
    """Base model for UniFi InnerSpace records."""

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
    )


class InnerSpaceProjectIdentity(InnerSpaceBaseModel):
    """Project identity metadata from GET /v1/project."""

    id: str
    title: str | None = None
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


class InnerSpacePlan(InnerSpaceBaseModel):
    """Plan metadata nested inside GET /v1/project."""

    id: str
    title: str | None = None
    type: str | None = None
    project_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("projectId", "project_id"),
        serialization_alias="projectId",
    )
    site_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("siteId", "site_id"),
        serialization_alias="siteId",
    )
    ordering: float | int | None = None
    attenuation: float | int | None = None
    location: dict[str, Any] | None = None
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


class InnerSpaceProduct(InnerSpaceBaseModel):
    """Placed product SKU metadata inside GET /v1/project."""

    id: str
    sku: str | None = None
    code: str | None = None
    mac: str | None = None
    plan_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "planId", "plan_id", "floorPlanId", "floor_plan_id"
        ),
        serialization_alias="planId",
    )


class InnerSpaceProject(InnerSpaceBaseModel):
    """Top-level project state from GET /v1/project."""

    project: InnerSpaceProjectIdentity | None = None
    plans: list[InnerSpacePlan] = Field(default_factory=list)
    products: list[InnerSpaceProduct] = Field(default_factory=list)
    wall_types: list[dict[str, Any]] = Field(
        default_factory=list,
        validation_alias=AliasChoices("wallTypes", "wall_types"),
        serialization_alias="wallTypes",
    )
    attenuation_object_types: list[dict[str, Any]] = Field(
        default_factory=list,
        validation_alias=AliasChoices(
            "attenuationObjectTypes",
            "attenuation_object_types",
        ),
        serialization_alias="attenuationObjectTypes",
    )
    shapes: list[dict[str, Any]] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _populate_root_project(cls, data: Any) -> Any:
        """Populate project identity when root-level project fields are returned."""
        if isinstance(data, dict) and "project" not in data:
            root_keys = ("id", "title", "name", "model", "environment")
            if any(k in data for k in root_keys):
                copied = dict(data)
                copied["project"] = {k: data[k] for k in root_keys if k in data}
                return copied
        return data


class InnerSpaceFloorPlan(InnerSpaceBaseModel):
    """Floor plan record from GET /v1/floor_plans."""

    id: str
    name: str
    floor_number: float | int | None = Field(
        default=None,
        validation_alias=AliasChoices("floor_number", "floorNumber"),
    )
    ppm: float | int | None = None
    width: float | int | None = None
    height: float | int | None = None
    origin_x: float | int | None = Field(
        default=None,
        validation_alias=AliasChoices("origin_x", "originX"),
    )
    origin_y: float | int | None = Field(
        default=None,
        validation_alias=AliasChoices("origin_y", "originY"),
    )
    site_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("site_id", "siteId"),
    )


class InnerSpaceAccessPoint(InnerSpaceBaseModel):
    """Placed access point record from GET /v1/access_points."""

    id: str
    name: str
    model: str | None = None
    mac: str | None = None
    serial: str | None = None
    floor_plan_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("floor_plan_id", "floorPlanId"),
    )
    x: float | int | None = None
    y: float | int | None = None
    height: float | int | None = None
    azimuth: float | int | None = None
    mount: str | None = None
    status: str | None = None


class InnerSpaceSwitch(InnerSpaceBaseModel):
    """Placed switch record from GET /v1/switches."""

    id: str
    name: str
    model: str | None = None
    type: str | None = "switch"
    mac: str | None = None
    serial: str | None = None
    floor_plan_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("floor_plan_id", "floorPlanId"),
    )
    x: float | int | None = None
    y: float | int | None = None
    status: str | None = None


class InnerSpaceInventoryDevice(InnerSpaceBaseModel):
    """Unplaced inventory device record from GET /v1/inventory."""

    id: str
    name: str
    model: str | None = None
    type: str | None = None
    mac: str | None = None
    serial: str | None = None
    status: str | None = None
    site_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("site_id", "siteId"),
    )
