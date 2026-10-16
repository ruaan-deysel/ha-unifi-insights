---
applyTo: "custom_components/unifi_insights/strings.json, custom_components/unifi_insights/icons.json, custom_components/unifi_insights/translations/**/*.json"
---

# Translation & Icon Instructions

**Applies to:** `strings.json`, `icons.json`, and `translations/*.json`

## Primary Files

- **`strings.json` & `translations/en.json`:** `strings.json` is the primary source of truth for English strings, and `translations/en.json` must be kept identical to `strings.json` so Home Assistant runtime lookups work in local development and HACS installs.
- **Non-English files (`translations/<lang>.json`):** Managed via localization workflows — never edit non-English translation files manually unless explicitly asked.
- **`icons.json`:** Defines icon translations for entities, state values, and numeric ranges (`icon-translations` Gold rule).

## Structure (`strings.json` / `translations/en.json`)

```json
{
  "config": {
    "step": {
      "user": {
        "title": "Set up UniFi Insights",
        "description": "...",
        "data": {},
        "data_description": {}
      }
    },
    "error": {},
    "abort": {}
  },
  "options": {
    "step": {}
  },
  "entity": {
    "sensor": {
      "translation_key": {
        "name": "Sensor name",
        "state": {}
      }
    }
  },
  "services": {
    "service_name": {
      "name": "Action display name",
      "description": "...",
      "fields": {}
    }
  },
  "exceptions": {
    "exception_key": {
      "message": "User-facing error message with {placeholder}"
    }
  },
  "issues": {
    "issue_key": {
      "title": "Repair issue title",
      "description": "..."
    }
  }
}
```

## Rules (HA 2026.10+ IQS Gold Tier)

- **Sentence case:** Capitalize only the first word and proper nouns (`UniFi`, `PoE`, `SSID`, `VLAN`, `RTSPS`, `SFP`, `WAN`, `GPON`, `ONU`).
- **Clear language:** Write for non-native English speakers using second-person (`you` / `your`).
- **Entity translations (`entity-translations`):** Every entity with a `translation_key` must have a matching entry under `entity.<platform>.<translation_key>`.
- **Exception translations (`exception-translations`):** Every `HomeAssistantError`, `ServiceValidationError`, and `ConfigEntryAuthFailed` raised with a `translation_key` must have a matching entry under `exceptions.<translation_key>.message`.
- **Icon translations (`icon-translations`):** Define entity icons in `icons.json` rather than hardcoding `_attr_icon` on standard entities. Numeric state range icons (`range` key) are supported in HA 2026.9+.
- **Sync check:** Whenever you update `strings.json`, mirror the exact changes to `custom_components/unifi_insights/translations/en.json`.
