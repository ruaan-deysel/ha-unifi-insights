---
agent: "agent"
tools: ["search/codebase", "edit", "search"]
description: "Add a new entity to an existing UniFi device"
---

# Add Entity to Device

Your goal is to add a new entity to an existing UniFi device (network device or Protect device).

If not provided, ask for:

- Which device type (network device, camera, light, sensor, NVR, etc.)
- Entity platform (sensor, binary_sensor, switch, etc.)
- What data it exposes (field name from API)
- Entity description (name, icon, device class, state class, unit)
- Whether it should be enabled or disabled by default

## Implementation Steps

### 1. Check data availability

Verify the data field exists in the coordinator's data schema. Check `data_transforms.py` and the coordinator to understand what data is available.

### 2. Add entity description

Add a new `EntityDescription` to the appropriate platform file:

```python
UnifiInsightsSensorEntityDescription(
    key="new_metric",
    translation_key="new_metric",
    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    device_class=SensorDeviceClass.TEMPERATURE,
    state_class=SensorStateClass.MEASUREMENT,
    entity_registry_enabled_default=False,  # For diagnostic entities
)
```

### 3. Add data access

Ensure the entity can read its value via `get_field()` or a custom value function.

### 4. Add translations

**File:** `custom_components/unifi_insights/strings.json`

### 5. Add icon (optional)

**File:** `custom_components/unifi_insights/icons.json`

### 6. Extend data transforms (if needed)

If the API field needs normalization, add mapping in `data_transforms.py`.

### 7. Validation

- Run `pre-commit run --all-files`
- Verify the entity appears under the correct device in HA
