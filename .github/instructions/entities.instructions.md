---
applyTo: "custom_components/unifi_insights/sensor.py, custom_components/unifi_insights/binary_sensor.py, custom_components/unifi_insights/switch.py, custom_components/unifi_insights/button.py, custom_components/unifi_insights/device_tracker.py, custom_components/unifi_insights/camera.py, custom_components/unifi_insights/light.py, custom_components/unifi_insights/number.py, custom_components/unifi_insights/select.py, custom_components/unifi_insights/event.py, custom_components/unifi_insights/update.py, custom_components/unifi_insights/entity.py"
---

# Entity Instructions

**Applies to:** Entity platform files and base entity classes

## Base Entity Classes

Two base classes in `entity.py`:

- **`UnifiInsightsEntity`** — For network devices. Availability via `is_device_online` helper.
- **`UnifiProtectEntity`** — For Protect devices. Availability via `state == CONNECTED`.

Both handle camelCase/snake_case field mapping via `get_field()`.

## MRO (Method Resolution Order)

**CRITICAL:** Platform base class MUST come first:

```python
# Correct
class MySwitch(UnifiInsightsEntity, SwitchEntity): ...

# Wrong - will cause MRO errors
class MySwitch(SwitchEntity, UnifiInsightsEntity): ...
```

## EntityDescription Pattern

Use dataclasses for static entity metadata:

```python
@dataclass(frozen=True, kw_only=True)
class UnifiInsightsSensorEntityDescription(SensorEntityDescription):
    """Describe a UniFi Insights sensor."""
    value_fn: Callable[[dict[str, Any]], StateType] | None = None
```

## Platform Setup

Every platform file must implement:

```python
async def async_setup_entry(
    hass: HomeAssistant,
    entry: UnifiInsightsConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up UniFi Insights sensors from a config entry."""
```

## Data Access

- ALWAYS read from `coordinator.data` — never call API directly
- Use `get_field()` for field access (handles camelCase tolerance)
- Set `PARALLEL_UPDATES = 0` for coordinator-driven entities
- Set `PARALLEL_UPDATES = 1` for action-based Protect entities

## Availability

- Network entities: Use `is_device_online` helper
- Protect entities: Check `state == CONNECTED`
- Don't raise exceptions from `@property` methods
- Return `None` for unavailable state values

## Entity Naming

- Use `translation_key` for translatable names (not hardcoded strings)
- Use `has_entity_name = True` for proper entity naming
- Disabled-by-default for diagnostic entities: `entity_registry_enabled_default = False`

## Existing Platforms

| Platform | Purpose | Key patterns |
|----------|---------|-------------|
| `sensor.py` | CPU, memory, uptime, TX/RX, port stats | Per-port metrics only for ports with state UP |
| `binary_sensor.py` | Online/offline, motion, smart detection | Uses `lastMotion*`, `lastSmartDetectTypes` |
| `switch.py` | Port enable/disable, PoE, WiFi, client block | Action-based with API calls |
| `button.py` | Device restart, port power cycle | Fire-and-forget actions |
| `select.py` | Recording mode, HDR, video mode, light mode | Protect-specific selections |
| `number.py` | Volume, light level controls | Numeric Protect controls |
| `event.py` | Motion, ring, smart detection events | Event-driven from coordinator |
| `device_tracker.py` | Client presence tracking | Based on client data |
| `update.py` | Firmware update entities | Based on device firmware info |
| `camera.py` | Live view, snapshots, RTSPS | Protect camera streams |
| `light.py` | Protect light brightness/mode | Protect light control |
