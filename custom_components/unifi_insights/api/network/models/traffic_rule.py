"""Traffic rule data model for UniFi Network API."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class TrafficRule(BaseModel):
    """Traffic rule configuration in UniFi Network.

    Reference shape derived from aiounifi v96 TypedTrafficRule (the Home Assistant core
    unifi dependency); not observed on a live console (0 records on Network 11, 2026-10-09).
    Keys: _id, action, app_category_ids, app_ids, bandwidth_limit, description,
    domains, enabled, ip_addresses, ip_ranges, matching_target, network_ids, regions,
    schedule, target_devices.

    Only id, description and enabled are declared; every other key is kept as an extra so a
    type change on the controller cannot make a record fail validation (a skipped
    record would look deleted to the switch orphan prune).
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: str = Field(alias="_id")
    description: str | None = None
    enabled: bool | None = None
