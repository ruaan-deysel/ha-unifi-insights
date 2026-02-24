---
applyTo: "custom_components/unifi_insights/strings.json, custom_components/unifi_insights/translations/**/*.json"
---

# Translation Instructions

**Applies to:** Translation and string files

## Primary File

`strings.json` is the source of truth for all translatable strings. Home Assistant uses this to generate language-specific files.

## Structure

```json
{
  "config": {
    "step": {
      "user": {
        "title": "Set up UniFi Insights",
        "description": "...",
        "data": { ... },
        "data_description": { ... }
      }
    },
    "error": { ... },
    "abort": { ... }
  },
  "entity": {
    "sensor": {
      "translation_key": {
        "name": "Sensor name"
      }
    }
  },
  "services": {
    "service_name": {
      "name": "Service display name",
      "description": "...",
      "fields": { ... }
    }
  }
}
```

## Rules

- Use sentence case for all strings (capitalize first word and proper nouns only)
- Use backticks for technical terms in descriptions
- Write for non-native English speakers (clear, simple language)
- Use second-person ("you" and "your") for user-facing messages
- NEVER update language files in `translations/` manually — only edit `strings.json`
- Keep `strings.json` as the single source; HA generates translation files

## Adding New Strings

1. Add to appropriate section in `strings.json`
2. Use `translation_key` in entity code to reference
3. Test that strings render correctly in the HA UI
