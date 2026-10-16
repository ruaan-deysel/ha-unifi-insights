---
agent: "agent"
tools: ["search/codebase", "edit", "search"]
description: "Add a new configuration option to the UniFi Insights config or options flow"
---

# Add Config Option

Your goal is to add a new configuration option to the UniFi Insights integration's config flow or options flow following Home Assistant 2026.10+ standards.

If not provided, ask for:

- Option name and purpose
- Data type and selector (`TextSelector`, `BooleanSelector`, `NumberSelector`, `SelectSelector`, `DeviceClassSelector`, `StateClassSelector`, `UnitOfMeasurementSelector`, etc.)
- Default value
- Whether it belongs in initial setup (`local` / `remote` / `carrier_fabric`), `reconfigure`, or `options` flow

## Implementation Steps

### 1. Add constant

**File:** `custom_components/unifi_insights/const.py`

```python
CONF_NEW_OPTION: Final = "new_option"
DEFAULT_NEW_OPTION: Final = "default_value"
```

### 2. Update `config_flow.py`

**File:** `custom_components/unifi_insights/config_flow.py`

- Keep `probatio` typing compatibility (`if TYPE_CHECKING: import probatio as vol`).
- Never use deprecated `FlowHandler.show_advanced_options` (use collapsible flow `section(...)` if grouping advanced settings).
- Do not combine config entry update listeners with `reload_on_update=True` flow helpers (causes double reloads, deprecated in HA 2026.6 / error in HA 2026.12).
- Never raise `ConfigEntryNotReady` or `ConfigEntryAuthFailed` inside config flow steps.

### 3. Add translations

**Files:** `custom_components/unifi_insights/strings.json` and `custom_components/unifi_insights/translations/en.json`

Add under the relevant `config.step.<step_id>` or `options.step.<step_id>` section:

```json
"data": {
  "new_option": "Option label"
},
"data_description": {
  "new_option": "Description of what this option controls."
}
```

### 4. Wire up and test

- Read the option from `entry.options` / `entry.data` in `__init__.py` or the relevant coordinator
- Add 100% branch coverage tests in `tests/test_config_flow.py`
- Run `./script/lint`, `./script/mypy`, and `pytest tests/test_config_flow.py`
