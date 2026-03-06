---
agent: "agent"
tools: ["search/codebase", "edit", "search"]
description: "Add a new entity platform to the UniFi Insights integration"
---

# Add Entity Platform

Your goal is to add a new entity platform (e.g., climate, fan, alarm_control_panel) to the UniFi Insights integration.

If not provided, ask for:

- Platform type (sensor, binary_sensor, switch, etc.)
- What data it represents from the UniFi API
- Whether it's for network devices or Protect devices
- Entity descriptions (name, icon, device class, state class)

## Implementation Steps

### 1. Create platform file

**File:** `custom_components/unifi_insights/<platform>.py`

Follow the pattern from existing platforms (e.g., `sensor.py`):

```python
"""UniFi Insights <platform> platform."""

from homeassistant.components.<platform> import <PlatformEntity>
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import UnifiInsightsConfigEntry
from .entity import UnifiInsightsEntity  # or UnifiProtectEntity

PARALLEL_UPDATES = 0

async def async_setup_entry(
    hass: HomeAssistant,
    entry: UnifiInsightsConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up UniFi Insights <platform> from a config entry."""
```

### 2. Register the platform

**File:** `custom_components/unifi_insights/__init__.py`

Add the platform to the `PLATFORMS` list.

### 3. Add entity descriptions

Define `EntityDescription` dataclasses for each entity in the platform file.

### 4. Add translations

**File:** `custom_components/unifi_insights/strings.json`

Add entity names under the appropriate platform section.

### 5. Add icons (optional)

**File:** `custom_components/unifi_insights/icons.json`

### 6. Validation

- Run `pre-commit run --all-files`
- Run `pytest` to ensure no regressions
- Verify entities appear in HA after adding the integration
