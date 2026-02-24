---
applyTo: "custom_components/unifi_insights/services.py, custom_components/unifi_insights/services.yaml"
---

# Service Action Instructions

**Applies to:** Service definitions and implementations

## Terminology

- **Developer/Code:** "service action" (function names, comments)
- **User-facing:** "action" (UI, translations)
- **Legacy:** `services.yaml`, `hass.services.async_register()`, `ServiceCall` class

## Implementation File

All service actions are implemented in `services.py` (1,166 lines).

## Existing Services

- **Refresh data** — Force coordinator refresh
- **Restart device** — Restart a network device
- **Protect controls** — Recording mode, HDR, video mode, mic volume, light mode/level, PTZ move/patrol, chime settings
- **Network actions** — Authorize guest, voucher CRUD, client block

## Helper Functions

- `_get_protect_coordinator` — Get Protect coordinator from config entry
- `_get_first_coordinator` — Get first available coordinator

## Error Handling

- Raise `HomeAssistantError` with user-facing messages for device/API failures
- Raise `ServiceValidationError` for invalid user input
- Never expose raw API errors to users

## Schema Definition (services.yaml)

```yaml
action_name:
  fields:
    parameter_name:
      required: true
      selector:
        text:
```

## Adding a New Service Action

1. Define schema in `services.yaml`
2. Add handler function in `services.py`
3. Register in the service setup function
4. Add translations in `strings.json` under `services`
5. Update tests if requested
