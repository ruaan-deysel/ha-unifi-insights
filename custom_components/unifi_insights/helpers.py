"""Helper utilities for UniFi Insights."""

from __future__ import annotations

from typing import Any, cast

from homeassistant.helpers import device_registry as dr

from .const import (
    CAMERA_TYPE_DOORBELL,
    CAMERA_TYPE_DOORBELL_MAIN,
    CAMERA_TYPE_DOORBELL_PACKAGE,
    CAMERA_TYPE_DOORBELL_WITH_PACKAGE_DETECTION,
)

# HA 2026.8 added identifier/connection lookups scoped to a config entry, and
# HA 2026.9 deprecated DeviceRegistry.async_get_device (removal in 2027.8).
# Capability is probed on the class rather than the instance so that test
# doubles follow whatever the installed HA actually supports, instead of
# MagicMock's auto-attributes selecting a branch that does not exist at runtime.
_SUPPORTS_BY_IDENTIFIER = hasattr(dr.DeviceRegistry, "async_get_device_by_identifier")
_SUPPORTS_GET_DEVICES = hasattr(dr.DeviceRegistry, "async_get_devices")


def is_doorbell_camera_model(camera_data: dict[str, Any]) -> bool:
    """
    Return whether a cached camera record says, by its model, that it is a doorbell.

    This is the evidence a camera's type gives, as opposed to its name: a
    camera called "Front Door" is not a doorbell because of that.
    """
    camera_type = camera_data.get("_camera_type") or ""
    if camera_type in (
        CAMERA_TYPE_DOORBELL,
        CAMERA_TYPE_DOORBELL_WITH_PACKAGE_DETECTION,
        CAMERA_TYPE_DOORBELL_MAIN,
        CAMERA_TYPE_DOORBELL_PACKAGE,
    ):
        return True

    # The camera type field from the API (handle None safely)
    api_camera_type = (camera_data.get("type") or "").lower()
    return any(
        doorbell_type in api_camera_type
        for doorbell_type in (
            "doorbell",
            "g4-doorbell",
            "ai-doorbell",
            "g4doorbell",
            "aidoorbell",
        )
    )


def async_get_device_entry(
    device_registry: dr.DeviceRegistry,
    identifier: tuple[str, str],
    config_entry_id: str | None = None,
) -> dr.DeviceEntry | None:
    """
    Look up a device entry by identifier, scoped to a config entry when possible.

    Each branch is authoritative: a miss returns None rather than falling
    through to the next lookup. Falling through would call the deprecated
    async_get_device on every miss, which is exactly the common case for the
    stale-device cleanup paths this helper serves.
    """
    # Accessed through Any so this type-checks against both an HA that predates
    # these methods and one that has them; a `type: ignore` would instead turn
    # into an unused-ignore error the moment HA is upgraded.
    registry = cast("Any", device_registry)

    if _SUPPORTS_BY_IDENTIFIER and config_entry_id is not None:
        device: dr.DeviceEntry | None = registry.async_get_device_by_identifier(
            identifier, config_entry_id
        )
        return device

    if _SUPPORTS_GET_DEVICES:
        devices: list[dr.DeviceEntry] = registry.async_get_devices(
            identifiers={identifier}
        )
        return devices[0] if devices else None

    return device_registry.async_get_device(identifiers={identifier})
