---
applyTo: "custom_components/unifi_insights/repairs.py"
---

# Repairs Instructions

**Applies to:** Repair issue creation and repair flow implementation (`repairs.py`)

## Creating Issues (IQS Gold `repair-issues`)

Use `ir.async_create_issue()` with `translation_key` and `translation_placeholders`:

```python
from homeassistant.helpers import issue_registry as ir

ir.async_create_issue(
    hass,
    DOMAIN,
    f"deprecated_option_{entry.entry_id}",
    is_fixable=True,
    is_persistent=False,
    severity=ir.IssueSeverity.WARNING,
    translation_key="deprecated_option",
    translation_placeholders={"entry_title": entry.title},
)
```

## Severity Levels

- **`IssueSeverity.WARNING`** — Non-critical issues (deprecated configuration, degraded optional capability, firmware/permission advisories)
- **`IssueSeverity.ERROR`** — Functional issues requiring user intervention
- **`IssueSeverity.CRITICAL`** — Integration cannot function until resolved

## Repair Flows

Implement `RepairsFlow` subclasses in `repairs.py` and register via `async_create_fix_flow`:

```python
class UnifiInsightsRepairFlow(RepairsFlow):
    """Handler for UniFi Insights repair flows."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> data_entry_flow.FlowResult:
        """Handle the first step of a repair flow."""
```

## Best Practices

- Call `ir.async_delete_issue(hass, DOMAIN, issue_id)` automatically when the underlying condition clears or after the repair flow completes.
- Define all repair titles, descriptions, and step labels under `"issues"` in `strings.json` and `translations/en.json`.
- Do not use repair issues for authentication failures — raise `ConfigEntryAuthFailed` to trigger the standard reauthentication flow instead.
- Test both creation/deletion of repair issues and full repair flow execution in `tests/test_repairs.py`.
