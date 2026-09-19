"""Helper utilities for UniFi Insights."""

from __future__ import annotations

from typing import Any, cast

from homeassistant.helpers import device_registry as dr

# HA 2026.8 added identifier/connection lookups scoped to a config entry, and
# HA 2026.9 deprecated DeviceRegistry.async_get_device (removal in 2027.8).
# Capability is probed on the class rather than the instance so that test
# doubles follow whatever the installed HA actually supports, instead of
# MagicMock's auto-attributes selecting a branch that does not exist at runtime.
_SUPPORTS_BY_IDENTIFIER = hasattr(dr.DeviceRegistry, "async_get_device_by_identifier")
_SUPPORTS_GET_DEVICES = hasattr(dr.DeviceRegistry, "async_get_devices")


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
