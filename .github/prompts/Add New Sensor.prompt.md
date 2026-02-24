---
agent: "agent"
tools: ["search/codebase", "edit", "search"]
description: "Add a new sensor entity to the UniFi Insights integration"
---

# Add New Sensor

Your goal is to add a new sensor to the UniFi Insights integration.

If not provided, ask for:

- What the sensor measures (CPU temp, bandwidth, client count, etc.)
- Data source (network device field, Protect device field, computed value)
- Unit of measurement
- Device class and state class
- Whether it should be enabled by default or diagnostic-only

## Implementation Steps

### 1. Add entity description

**File:** `custom_components/unifi_insights/sensor.py`

Add to the appropriate description list:

```python
UnifiInsightsSensorEntityDescription(
    key="sensor_key",
    translation_key="sensor_key",
    native_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
    device_class=SensorDeviceClass.DATA_RATE,
    state_class=SensorStateClass.MEASUREMENT,
    suggested_display_precision=2,
    entity_registry_enabled_default=True,
    value_fn=lambda data: data.get("fieldName"),
)
```

### 2. Add to entity creation

Ensure the sensor description is included in the entity creation loop within `async_setup_entry`.

### 3. Check data availability

Verify the data field exists:
- For network devices: Check coordinator data under `devices`
- For Protect devices: Check coordinator data under `protect`
- May need to extend `data_transforms.py` if field needs normalization

### 4. Add translation

**File:** `custom_components/unifi_insights/strings.json`

```json
"entity": {
  "sensor": {
    "sensor_key": {
      "name": "Sensor display name"
    }
  }
}
```

### 5. Add icon

**File:** `custom_components/unifi_insights/icons.json`

```json
"entity": {
  "sensor": {
    "sensor_key": {
      "default": "mdi:icon-name"
    }
  }
}
```

### 6. Patterns to follow

- Network sensors: Per-port metrics only for ports with state UP
- Diagnostic sensors: Set `entity_registry_enabled_default = False`
- Use `get_field()` for camelCase/snake_case field tolerance
- Protect sensors: Inherit from `UnifiProtectEntity`

### 7. Validation

- Run `pre-commit run --all-files`
- Run `pytest tests/test_sensor.py` if tests exist for sensors
