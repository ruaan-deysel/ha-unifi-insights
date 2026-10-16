---
agent: "agent"
# Tools:
#   - search/codebase, edit, search: standard code exploration and editing
#   - execute/runInTerminal, execute/getTerminalOutput: needed for running
#     validation commands (tests, linters, type checks, reproducible builds)
#
# Terminal tool constraints:
#   Allowed commands: pytest, ruff, mypy, pre-commit, ./script/lint,
#     ./script/mypy, ./script/develop, pip, git (read-only: log, diff, status, show)
#   Allowed command prefixes: python -m pytest, python -m ruff, python -m mypy
#   Working directory: must remain within the workspace root
#   Prohibited operations: rm -rf, mv (destructive), network-modifying commands,
#     git push, git reset --hard, pip install (global)
#   Timeouts: commands should complete within 120 seconds
#   Environment: commands run inside the dev container (sandboxed);
#     verify by checking that $PWD is under /workspaces/
tools:
  [
    "search/codebase",
    "edit",
    "search",
    "execute/runInTerminal",
    "execute/getTerminalOutput",
  ]
description: "Perform a comprehensive quality review of the UniFi Insights integration against HA 2026.10+ standards"
---

# Review Integration

Your goal is to perform a comprehensive quality review of the UniFi Insights integration against Home Assistant 2026.10+ standards and the Integration Quality Scale (Bronze through Platinum).
Treat the official Quality Scale rules as mandatory review criteria:
<https://developers.home-assistant.io/docs/core/integration-quality-scale/rules>

## Review Checklist

### Integration Quality Scale (Bronze → Platinum)

- [ ] **Bronze:** `config-flow`, `test-before-configure`, `unique-config-entry`, `has-entity-name`, `entity-unique-id`, `runtime-data` (`entry.runtime_data`), `action-setup` (services registered in `async_setup`), `config-entry-unloading`
- [ ] **Silver:** `action-exceptions`, `IntegrationOwner`, `log-when-unavailable` (log once on offline/online transitions), `parallel-updates` (`PARALLEL_UPDATES` in all 17 platforms), `reauthentication-flow`, `test-before-setup`
- [ ] **Gold:** `devices` (`DeviceInfo`), `diagnostics` (`async_redact_data` + `_anonymize_macs`), `discovery` / `discovery-update-info` (SSDP), `dynamic-devices` & `stale-devices`, `entity-category`, `entity-disabled-by-default`, `entity-translations`, `exception-translations` (`translation_domain=DOMAIN`, `translation_key` in `strings.json`), `icon-translations` (`icons.json`), `reconfiguration-flow`, `repair-issues`
- [ ] **Platinum:** `async-dependency`, `inject-websession` (`async_get_clientsession(hass)`), `strict-typing` (`mypy` strict + `probatio` schema typing)

### Architecture & HA 2026.8–2026.11+ Core Rules

- [ ] Entities → Coordinator → API Client pattern followed strictly (no layer skipping)
- [ ] Custom base entity class precedes platform entity class in MRO (`class X(UnifiInsightsEntity, SensorEntity):`)
- [ ] `first_not_none()` and `get_field()` used for camelCase/snake_case field resolution without dropping falsy `0`/`False`
- [ ] **Device Registry (HA 2026.8–2026.10):**
  - Single config entry per device (`DeviceEntry.config_entry_id`; no `config_entries`, `config_entries_subentries`, or `primary_config_entry`)
  - `via_device_id` used instead of deprecated `via_device` / `ATTR_VIA_DEVICE`
  - Config-entry-scoped lookups (`async_get_device_by_identifier`, not deprecated `async_get_device`)
  - No dict methods (`.get()`, `.values()`, `.keys()`) called on `dev_reg.devices` or `dev_reg.child_devices`
  - No `default_manufacturer`, `default_model`, or `default_name` in `DeviceInfo`; no reads of removed `DeviceEntry.suggested_area`
- [ ] **Entity Lifecycle (HA 2026.10–2026.11):**
  - `async_prepare_to_add_to_hass` used instead of overriding `add_to_platform_start`
  - Custom entities overriding `async_prepare_to_add_to_hass`, `async_added_to_hass`, or `async_will_remove_from_hass` also implement `@callback def async_entity_id_changed(self, old_entity_id: str) -> None:` calling `super().async_entity_id_changed(old_entity_id)`
  - No access to removed `RestoreStateData.last_states`

### Config Flow & Service Actions

- [ ] Local, Remote, and Carrier Fabric flows validate via `probe.py` and set deterministic `unique_id`
- [ ] Config flow step handlers never raise `ConfigEntryNotReady` or `ConfigEntryAuthFailed` (caught and mapped to `errors["base"]`)
- [ ] No deprecated `FlowHandler.show_advanced_options` or double-reload listener combinations
- [ ] Service helpers (`async_extract_entities`, `extract_entity_ids`, etc.) called without deprecated `hass` argument (HA 2026.10+)
- [ ] `services.yaml` `target:` selectors do not contain the removed `device:` filter (HA 2026.11+)

### Frontend Custom Cards (`frontend/`)

- [ ] Uses `--ha-*` Web Awesome CSS tokens (no deprecated `--mdc-*` or `--switch-*` variables; short button/slider size names `xs`, `s`, `m`, `l`, `xl`)
- [ ] Implements `getGridOptions()` for Sections view layouts
- [ ] Keyboard-accessible interactive controls (`button`, `tabindex`, `aria-label`)
- [ ] Compiled bundles in `custom_components/unifi_insights/frontend/` match `frontend/src/`

### Testing & Translations

- [ ] ≥95% branch coverage per file (`python script/check_coverage_per_file.py coverage.xml --fail-under 95`)
- [ ] `strings.json` and `translations/en.json` are in sync and include `config`, `options`, `entity`, `services`, `exceptions`, and `issues`

## Output

Provide a structured review summary with:

1. **Critical issues** — Must fix before release (with file and line references)
2. **Quality Scale / HA 2026.10+ gaps** — Deprecations or rule violations to address
3. **Suggestions** — Optional maintainability or UX improvements
