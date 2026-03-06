---
applyTo: "custom_components/unifi_insights/diagnostics.py"
---

# Diagnostics Instructions

**Applies to:** Diagnostic data export

## CRITICAL: Data Redaction

**ALWAYS** use `async_redact_data()` from `homeassistant.helpers.redact` to remove sensitive data before returning diagnostics.

**Must redact:**
- API keys and tokens
- Passwords and secrets
- MAC addresses (if privacy-sensitive)
- Location data
- Personal information

```python
from homeassistant.helpers.redact import async_redact_data

TO_REDACT = {"api_key", "password", "token", "secret"}

async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: UnifiInsightsConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    return async_redact_data(
        {"entry": entry.as_dict(), "data": coordinator.data},
        TO_REDACT,
    )
```

## Structure

Return a dictionary with:
- Config entry data (redacted)
- Coordinator data (redacted)
- Any relevant state information for debugging
