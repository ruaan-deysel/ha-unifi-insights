---
applyTo: "custom_components/unifi_insights/repairs.py"
---

# Repairs Instructions

**Applies to:** Repair flow implementation

## Creating Issues

Use `async_create_issue()` with appropriate severity:

```python
from homeassistant.helpers import issue_registry as ir

ir.async_create_issue(
    hass,
    DOMAIN,
    "issue_id",
    is_fixable=True,
    severity=ir.IssueSeverity.WARNING,
    translation_key="issue_translation_key",
)
```

## Severity Levels

- **WARNING** — Non-critical issues (deprecated config, upcoming changes)
- **ERROR** — Functional issues requiring attention
- **CRITICAL** — Integration cannot function properly

## Repair Flows

Implement `RepairsFlow` for guided user fixes:

```python
class UnifiInsightsRepairFlow(RepairsFlow):
    """Handler for UniFi Insights repair flows."""

    async def async_step_init(self, user_input=None):
        """Handle the init step."""
```

## Best Practices

- Delete issues after successful repair
- Use translation keys for all user-facing strings
- Provide clear, actionable descriptions
- Test repair flows with both success and failure paths
