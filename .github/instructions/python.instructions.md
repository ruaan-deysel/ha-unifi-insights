---
applyTo: "**/*.py"
---

# Python Instructions

**Applies to:** All Python files in this project

## Code Style

- **Python version:** 3.11+ (Home Assistant 2025.9.0+ requirement)
- **Indentation:** 4 spaces
- **Line length:** 88 characters (ruff default)
- **Quotes:** Double quotes
- **Formatter/Linter:** Ruff
- **Type checker:** mypy (strict mode)

## Type Hints

- Add type hints to ALL functions, methods, and variables
- Use modern syntax: `list[str]`, `dict[str, Any]`, `str | None`
- Use `TypeVar` for generic return types
- Custom config entry type:
  ```python
  type UnifiInsightsConfigEntry = ConfigEntry[UnifiInsightsRuntimeData]
  ```

## Imports

**Order (enforced by Ruff/isort):**

1. Standard library (`import asyncio`, `from datetime import timedelta`)
2. Third-party (`from homeassistant.core import HomeAssistant`)
3. Local (`from .const import DOMAIN`)

**Rules:**

- Use absolute imports for HA core (`from homeassistant.core import ...`)
- Use relative imports within the integration (`from .const import ...`)
- Import specific names, not whole modules
- No wildcard imports (`from module import *`)

## Async Patterns

- All external I/O operations must be async
- Use `gather` instead of awaiting in loops
- No blocking calls on event loop
- Use `asyncio.sleep()` instead of `time.sleep()`
- Use `hass.async_add_executor_job()` for blocking operations
- Use `@callback` decorator for event loop safe functions

## Error Handling

- Catch specific exceptions, not bare `except Exception:`
- Keep try blocks minimal — process data outside the try block
- Use `from err` for exception chaining
- Allowed broad exceptions: config flows and background tasks only

## Logging

- Use lazy logging: `_LOGGER.debug("Message with %s", variable)`
- No periods at end of messages
- No integration names/domains (added automatically by HA)
- No sensitive data (keys, tokens, passwords)
- Use debug level for non-user-facing messages

## Documentation

- File headers: Short module docstrings (`"""UniFi Insights sensor platform."""`)
- Method/function docstrings: Required for all public methods
- Explain the "why" not just the "what" in comments

## Linter Overrides

- Use `# noqa: CODE` or `# type: ignore[code]` sparingly
- Only for genuine false positives or unavoidable external library issues
- Always include the specific error code
