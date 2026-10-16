---
agent: "agent"
tools: ["search/codebase", "edit", "search"]
description: "Add a new entity to an existing UniFi device"
---

# Add Entity to Device

Your goal is to add a new entity to an existing UniFi device (Network, Protect, Access, InnerSpace, Mobility, or Carrier Fabric).

If not provided, ask for:

- Device type (network switch/AP/gateway, camera, light, sensor, NVR, Access door/reader, InnerSpace floor plan, Mobility router, Carrier Fabric OLTs/ONUs)
- Entity platform (`sensor`, `binary_sensor`, `switch`, `number`, `select`, `button`, etc.)
- API field name (verify against `https://developer.ui.com/{service}/{version}/openapi.json` if needed)
- Entity metadata (`translation_key`, `device_class`, `state_class`, unit, `EntityCategory`, `entity_registry_enabled_default`)

## Implementation Steps

### 1. Check data availability

Verify the field exists in the coordinator's data dictionary and `data_transforms.py`. Use `get_field()` and `first_not_none()` so falsy values (`0`, `0.0`, `False`) are preserved.

### 2. Add entity description

Add a frozen `EntityDescription` entry in the target platform file:

```python
UnifiInsightsSensorEntityDescription(
    key="new_metric",
    translation_key="new_metric",
    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    device_class=SensorDeviceClass.TEMPERATURE,
    state_class=SensorStateClass.MEASUREMENT,
    entity_category=EntityCategory.DIAGNOSTIC,
    entity_registry_enabled_default=False,
)
```

### 3. Device Registry & Lifecycle Rules (HA 2026.8–2026.11+)

- Ensure the entity sets `_attr_has_entity_name = True` and a deterministic `_attr_unique_id`.
- If linking a child device to a parent hub or switch, use `via_device_id` (resolved via `dr.async_get_device_id_by_identifier`), never deprecated `via_device`.
- Never use `default_manufacturer`, `default_model`, or `default_name` in `DeviceInfo`.

### 4. Add translations and icons

- **Files:** `custom_components/unifi_insights/strings.json` and `custom_components/unifi_insights/translations/en.json`
- **File:** `custom_components/unifi_insights/icons.json`

### 5. Add tests and validate

- Add unit tests in `tests/test_<platform>.py` covering normal values, `0`/`False` edge cases, and unavailable state
- Run `./script/lint`, `./script/mypy`, and `pytest`
