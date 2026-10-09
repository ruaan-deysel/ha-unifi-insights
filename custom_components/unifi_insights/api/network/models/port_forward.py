"""Port forward data model for UniFi Network API."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PortForward(BaseModel):
    """Port forward configuration in UniFi Network.

    Keys observed live on Network 11 (2026-10-09):
    _id, destination_ip, destination_ips, dst_port, enabled, fwd, fwd_port, log,
    name, pfwd_interface, proto, site_id, src, src_limiting_enabled.

    Only id, name and enabled are declared; every other key is kept as an extra so a
    type change on the controller cannot make a record fail validation (a skipped
    record would look deleted to the switch orphan prune).
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: str = Field(alias="_id")
    name: str | None = None
    enabled: bool | None = None
