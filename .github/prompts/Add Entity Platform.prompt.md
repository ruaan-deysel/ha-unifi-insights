---
agent: "agent"
tools: ["search/codebase", "edit", "search"]
description: "Add a new entity platform to the UniFi Insights integration"
---

# Add Entity Platform

Your goal is to add a new entity platform to the UniFi Insights integration following Home Assistant 2026.10+ and Integration Quality Scale standards.

If not provided, ask for:

- Platform type (`sensor`, `binary_sensor`, `switch`, `lock`, `cover`, `media_player`, `siren`, etc.)
- What data it represents from the UniFi API (Network, Protect, Access, InnerSpace, Mobility, or Carrier Fabric)
- Entity descriptions (translation key, icon, device class, state class, `EntityCategory`, enabled default)

## Implementation Steps

### 1. Create platform file

**File:** `custom_components/unifi_insights/<platform>.py`

Ensure the custom base entity class (`UnifiInsightsEntity`, `UnifiProtectEntity`, `UnifiAccessEntity`, `UnifiInnerSpaceEntity`, or `UnifiCarrierFabricEntity`) comes **before** the Home Assistant platform entity class in the MRO:

```python
"""UniFi Insights <platform> platform."""

from __future__ import annotations

from homeassistant.components.<platform> import <PlatformEntity>
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import CarrierFabricConfigEntry, UnifiInsightsConfigEntry
from .entity import UnifiInsightsEntity

PARALLEL_UPDATES = 0  # Use 1 for action-based platforms

async def async_setup_entry(
    hass: HomeAssistant,
    entry: UnifiInsightsConfigEntry,  # Use CarrierFabricConfigEntry (or union) for Carrier Fabric platforms
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up UniFi Insights <platform> entities from a config entry."""
```

- If overriding `async_prepare_to_add_to_hass`, `async_added_to_hass`, or `async_will_remove_from_hass`, also implement `@callback def async_entity_id_changed(self, old_entity_id: str) -> None:` calling `super().async_entity_id_changed(old_entity_id)` (HA 2026.10/2026.11).

### 2. Register the platform

- **File:** `custom_components/unifi_insights/const.py` — Add `Platform.<PLATFORM>` to `PLATFORMS` (or `CARRIER_FABRIC_PLATFORMS` if applicable).
- **File:** `.github/instructions/entities.instructions.md` — Keep the platform list up to date if adding a permanent platform.

### 3. Add entity descriptions

Define frozen, keyword-only `EntityDescription` dataclasses (`@dataclass(frozen=True, kw_only=True)`) with `translation_key`, `device_class`, `entity_category`, and `entity_registry_enabled_default`.

### 4. Add translations and icons

- **Files:** `custom_components/unifi_insights/strings.json` and `custom_components/unifi_insights/translations/en.json` (keep both in sync)
- **File:** `custom_components/unifi_insights/icons.json`

### 5. Add tests and validate

- Add unit tests in `tests/test_<platform>.py` with ≥95% per-file branch coverage
- Run `./script/lint`, `./script/mypy`, and `pytest --cov-report=xml && python script/check_coverage_per_file.py coverage.xml --fail-under 95`
