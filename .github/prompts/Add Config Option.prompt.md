---
agent: "agent"
tools: ["search/codebase", "edit", "search"]
description: "Add a new configuration option to the UniFi Insights config flow"
---

# Add Config Option

Your goal is to add a new configuration option to the UniFi Insights integration's config or options flow.

If not provided, ask for:

- Option name and purpose
- Data type (string, boolean, number, select)
- Default value
- Whether it belongs in initial setup or options flow
- Validation requirements

## Implementation Steps

### 1. Add constant

**File:** `custom_components/unifi_insights/const.py`

```python
CONF_NEW_OPTION = "new_option"
DEFAULT_NEW_OPTION = "default_value"
```

### 2. Update config flow

**File:** `custom_components/unifi_insights/config_flow.py`

Add the field to the appropriate step's schema and handle the value.

### 3. Add translations

**File:** `custom_components/unifi_insights/strings.json`

Add under the appropriate `config.step` section:
```json
"data": {
  "new_option": "Option label"
},
"data_description": {
  "new_option": "Description of what this option controls"
}
```

### 4. Use the option

Update the integration setup or coordinator to read and use the new option from `entry.data` or `entry.options`.

### 5. Validation

- Run `pre-commit run --all-files`
- Test the flow in HA UI
- Verify reconfigure flow includes the option if applicable
