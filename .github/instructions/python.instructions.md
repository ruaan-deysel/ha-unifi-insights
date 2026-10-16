---
applyTo: "**/*.py"
---

# Python Instructions

**Applies to:** All Python files in this project

## Code Style

- **Python version:** 3.14.2+ (`py314`, Home Assistant 2026.10+ requirement)
- **Indentation:** 4 spaces
- **Line length:** 88 characters (ruff default)
- **Quotes:** Double quotes
- **Formatter/Linter:** Ruff (`./script/lint`)
- **Type checker:** mypy in strict mode (`./script/mypy` or `mypy custom_components/unifi_insights`)

## Type Hints

- Add type hints to ALL functions, methods, and variables (Platinum `strict-typing`)
- Use modern syntax: `list[str]`, `dict[str, Any]`, `str | None`
- Typed `ConfigEntry.runtime_data` aliases in `custom_components/unifi_insights/__init__.py`:
  ```python
  UnifiInsightsConfigEntry: TypeAlias = ConfigEntry[UnifiInsightsData]
  CarrierFabricConfigEntry: TypeAlias = ConfigEntry[CarrierFabricData]
  ```
- For Voluptuous schemas in config/options flows and services, use `probatio` under `TYPE_CHECKING` (HA 2026.5+):

  ```python
  from typing import TYPE_CHECKING

  if TYPE_CHECKING:
      import probatio as vol  # type: ignore[import-not-found]
  else:
      import voluptuous as vol
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

- All external I/O operations must be async (Platinum `async-dependency`)
- Inject Home Assistant's shared session via `async_get_clientsession(hass, verify_ssl=...)` (Platinum `inject-websession`)
- Use `asyncio.gather()` instead of awaiting in sequential loops where independent
- Never make blocking calls on the event loop (`time.sleep`, sync file/network I/O)
- Use `hass.async_add_executor_job()` for unavoidable CPU-bound or sync operations
- Decorate synchronous event-loop-safe callbacks with `@callback`

## Error Handling

- Catch specific exceptions, not bare `except Exception:`
- Keep `try` blocks minimal — process data outside the `try` block
- Use `from err` for exception chaining
- Pass `translation_domain=DOMAIN`, `translation_key="..."`, and `translation_placeholders={...}` when raising `HomeAssistantError` or `ServiceValidationError` (Gold `exception-translations`)
- Allowed broad exceptions: config flows (`errors["base"] = "unknown"`) and background tasks only

## Logging

- Use lazy logging: `_LOGGER.debug("Message with %s", variable)`
- No periods at end of messages
- No integration names/domains (added automatically by HA)
- Never log sensitive data (API keys, tokens, passwords, raw credentials)
- Log once at `INFO`/`WARNING` when a device/service transitions to unavailable and once when it recovers (Silver `log-when-unavailable`); do not spam logs on every failed poll

## Documentation

- File headers: Short module docstrings (`"""UniFi Insights sensor platform."""`)
- Method/function docstrings: Required for all public methods
- Explain the "why" not just the "what" in comments

## Linter Overrides

- Use `# noqa: CODE` or `# type: ignore[code]` sparingly
- Only for genuine false positives or unavoidable external library issues
- Always include the specific error code
