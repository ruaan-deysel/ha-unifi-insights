---
applyTo: "custom_components/unifi_insights/services.yaml"
---

# services.yaml Instructions

**Applies to:** Service action schema definitions

## Naming Convention

- `services.yaml` defines service action schemas for `unifi_insights.<action_name>`
- Action and field names use `snake_case`: `restart_device`, `authorize_guest`

## Schema Structure

```yaml
action_name:
  # Names and descriptions belong in strings.json under "services", not here
  fields:
    parameter_name:
      required: true
      selector:
        text:
    optional_param:
      required: false
      default: "value"
      selector:
        select:
          options:
            - "option1"
            - "option2"
  target:
    entity:
      integration: unifi_insights
      domain: switch
```

## Selectors (HA 2026.8–2026.11+)

Common selectors used in this integration:

- `text:` — Text input (supports `pattern` and `validation_message` in HA 2026.8+)
- `select:` — Dropdown with predefined options (use `translation_key` for translated options)
- `number:` — Numeric input with `min`, `max`, `step`, `unit_of_measurement`
- `boolean:` — Toggle switch
- `entity:` — Entity picker (supports `integration`, `domain`, `device_class`, and `device` filter in HA 2026.8+)
- `device:` — Device picker (supports `integration`, `manufacturer`, `model`)

**CRITICAL (HA 2026.11):** Never use a `device:` filter inside a `target:` selector block (`target:` supports `entity:`, `device:`, and `area:` target selectors, with `integration`, `domain`, `device_class`, or `supported_features` filters where applicable).

## Rules

- Define only schemas and selectors in `services.yaml` — all display names and descriptions belong in `strings.json` and `translations/en.json` under `services`
- Keep `services.yaml` fields in strict sync with `vol.Schema` definitions in `services.py`
- Specify `integration: unifi_insights` on `entity:` and `device:` selectors to scope pickers to this integration
