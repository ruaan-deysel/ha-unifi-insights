---
agent: "agent"
tools: ["search/codebase", "edit", "search"]
description: "Add a new service action to the UniFi Insights integration"
---

# Add Service Action

Your goal is to add a new **service action** to the UniFi Insights integration that users can call from automations, scripts, or the UI.

If not provided, ask for:

- Service action name and purpose
- Parameters required (with types and validation)
- What the service action does (API call, state change, etc.)
- Whether it targets a specific device/entity or is integration-wide
- Which API client it uses (network_client, protect_client, or both)

## Implementation Steps

### 1. Define schema in `services.yaml`

**File:** `custom_components/unifi_insights/services.yaml`

```yaml
action_name:
  fields:
    parameter_name:
      required: true
      selector:
        text:
```

### 2. Add handler in `services.py`

**File:** `custom_components/unifi_insights/services.py`

- Use `_get_protect_coordinator` or `_get_first_coordinator` helpers
- Raise `HomeAssistantError` for device/API failures
- Raise `ServiceValidationError` for invalid user input

### 3. Register the service

Add registration in the service setup function within `services.py`.

### 4. Add translations

**File:** `custom_components/unifi_insights/strings.json`

Add under the `services` section:
```json
"action_name": {
  "name": "Action display name",
  "description": "What this action does",
  "fields": {
    "parameter_name": {
      "name": "Parameter display name",
      "description": "What this parameter controls"
    }
  }
}
```

### 5. Validation

- Run `pre-commit run --all-files`
- Verify the service appears in HA Developer Tools → Services
