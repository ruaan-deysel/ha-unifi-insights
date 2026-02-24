---
applyTo: "custom_components/unifi_insights/services.yaml"
---

# services.yaml Instructions

**Applies to:** Service action schema definitions

## Naming Convention

- `services.yaml` is a legacy filename — HA now calls these "service actions"
- Action names use snake_case: `restart_device`, `authorize_guest`
- Full format: `unifi_insights.action_name`

## Schema Structure

```yaml
action_name:
  # Names and descriptions go in strings.json, not here
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
      domain: sensor
```

## Selectors

Common selectors used in this integration:

- `text:` — Free text input
- `select:` — Dropdown with predefined options
- `number:` — Numeric input with min/max/step
- `boolean:` — On/off toggle
- `entity:` — Entity picker
- `device:` — Device picker

## Rules

- Define only the schema here, not names/descriptions
- Names and descriptions go in `strings.json` under `services`
- Keep schemas in sync with `services.py` implementations
- Use appropriate selectors for each parameter type
