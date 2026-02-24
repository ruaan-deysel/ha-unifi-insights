# Copilot Instructions

This is **UniFi Insights** (`unifi_insights`), a Home Assistant custom integration for monitoring and controlling UniFi network infrastructure.

For full instructions, see [`AGENTS.md`](../AGENTS.md). This file provides a compact quick-reference.

## Project Identity

- **Domain:** `unifi_insights`
- **Title:** UniFi Insights
- **Class prefix:** `UnifiInsights`
- **Main code:** `custom_components/unifi_insights/`
- **External dependency:** `unifi-official-api~=1.1.0`

## Validation Commands

```bash
pre-commit run --all-files   # Full validation (ruff, codespell, yamllint, mypy)
scripts/lint                  # Auto-format and fix (ruff format + check)
pytest                        # Tests (90% minimum coverage)
./scripts/develop             # Start local HA instance
```

## Architecture Quick Reference

- **Entry point:** `__init__.py` — Sets up Network + Protect clients, initializes coordinators
- **Multi-coordinator system:** `coordinators/` — Base, Config, Device, Protect, Facade
- **Data flow:** API → Coordinators → Entities (never skip layers)
- **Entity bases:** `entity.py` — `UnifiInsightsEntity` (network), `UnifiProtectEntity` (protect)
- **Field access:** Use `get_field()` for camelCase/snake_case tolerance
- **Config flow:** `config_flow.py` — Local (host + API key) and Remote (console_id + API key) modes
- **Services:** `services.py` — Refresh, device control, Protect controls, Network actions
- **Data transforms:** `data_transforms.py` — API response normalization
- **Constants:** `const.py` — Device/service names, endpoint paths (reuse, don't hardcode)

## Workflow Rules

**Make small, focused changes:**
- One logical feature or fix at a time
- Implement completely even across multiple files
- Suggest committing before moving to next task

**Complete features fully:**
- Entity class + platform registration + translations
- Service definition + implementation + schema
- Config option + flow step + validation

**Research first:**
- Read existing code before modifying
- Check `const.py` for existing constants
- Look for similar patterns in existing platforms

## Code Patterns

**Entity pattern:**
```python
class UnifiInsightsSomeSensor(UnifiInsightsEntity, SensorEntity):
    entity_description = UnifiInsightsSensorEntityDescription(...)

    @property
    def native_value(self) -> StateType:
        return self.get_field(self.coordinator.data, "fieldName")
```

**Error handling:**
- `ConfigEntryNotReady` — Temporary setup issues
- `ConfigEntryAuthFailed` — Authentication problems
- `UpdateFailed` — Coordinator fetch failures
- `HomeAssistantError` — Service call failures
- `ServiceValidationError` — User input errors

**Async patterns:**
- All I/O must be async
- Use `gather` instead of awaiting in loops
- No blocking calls on event loop
- Use `@callback` for event loop safe functions

## Documentation Strategy

- NEVER create random markdown files
- Prefer module docstrings over separate docs
- Use `.ai-scratch/` for temporary planning notes
- Update `strings.json` only when asked

## Session Management

- Suggest commits when switching topics
- Use Conventional Commits format (`feat:`, `fix:`, `chore:`, etc.)
- One feature per commit
- Don't create tests unless explicitly asked
