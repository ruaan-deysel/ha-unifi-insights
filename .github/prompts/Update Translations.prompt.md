---
agent: "agent"
tools: ["search/codebase", "edit", "search"]
description: "Update translation strings and icons for the UniFi Insights integration"
---

# Update Translations

Your goal is to update translation strings and icon mappings for the UniFi Insights integration following Home Assistant 2026.10+ Gold tier (`entity-translations`, `exception-translations`, `icon-translations`) rules.

If not provided, ask for:

- What needs translating (new entities, service actions, exceptions, config/options flow steps, or repair issues)
- The specific strings or icons to add or modify

## Translation Files

- **`custom_components/unifi_insights/strings.json`** — Primary source of truth for English strings
- **`custom_components/unifi_insights/translations/en.json`** — Must be kept identical to `strings.json`
- **`custom_components/unifi_insights/icons.json`** — Icon translations (including `default`, `state`, and numeric `range` keys)
- **Do NOT edit** non-English files in `custom_components/unifi_insights/translations/<lang>.json` unless explicitly requested.

## Structure (`strings.json` & `translations/en.json`)

```json
{
  "config": {
    "step": {},
    "error": {},
    "abort": {}
  },
  "options": {
    "step": {}
  },
  "entity": {
    "sensor": {},
    "binary_sensor": {},
    "switch": {}
  },
  "services": {},
  "exceptions": {},
  "issues": {}
}
```

## Steps

1. Search recursively for `translation_key` across all Python files under `custom_components/unifi_insights/` (e.g., `rg -n --glob '*.py' 'translation_key' custom_components/unifi_insights/`, covering entities, coordinators, `HomeAssistantError`, `ServiceValidationError`, `ConfigEntryAuthFailed`, and `ir.async_create_issue`) and verify each has a corresponding entry in `strings.json`.
2. Follow Home Assistant style conventions:
   - **Sentence case** — Capitalize only the first word and proper nouns (`UniFi`, `PoE`, `SSID`, `VLAN`, `RTSPS`, `SFP`, `WAN`, `GPON`, `ONU`)
   - **Second person** — Use "you" and "your" for user-facing messages
   - **No trailing periods** in short labels/entity names; include periods in full sentences/descriptions
3. Mirror all changes from `strings.json` to `translations/en.json`.
4. Run `pre-commit run --all-files` to validate JSON syntax and formatting.
