# GitHub Copilot & Claude Code Instructions

This repository contains `ha-unifi-insights`, a Home Assistant custom component that provides integration with UniFi network devices using the UniFi Insights API.

## Code Review Guidelines

**When reviewing code, do NOT comment on:**
- **Missing imports** - We use static analysis tooling to catch that
- **Code formatting** - We have ruff as a formatting tool that will catch those if needed (unless specifically instructed otherwise in these instructions)

**Git commit practices during review:**
- **Do NOT amend, squash, or rebase commits after review has started** - Reviewers need to see what changed since their last review

## Python Requirements

- **Compatibility**: Python 3.11+ (Home Assistant 2025.9.0+ requirement)
- **Language Features**: Use modern features when possible:
  - Pattern matching
  - Type hints (strict typing required)
  - f-strings (preferred over `%` or `.format()`)
  - Dataclasses
  - Walrus operator

### Strict Typing
- **Comprehensive Type Hints**: Add type hints to all functions, methods, and variables
- **Custom Config Entry Types**: When using runtime_data:
  ```python
  type UnifiInsightsConfigEntry = ConfigEntry[UnifiInsightsRuntimeData]
  ```

## Code Quality Standards

- **Formatting**: Ruff
- **Linting**: Ruff
- **Type Checking**: MyPy (strict mode)
- **Security Scanning**: Bandit
- **Lint/Type/Format Fixes**: Always prefer addressing the underlying issue before disabling a rule or adding `# type: ignore`. Treat suppressions and `noqa` comments as a last resort
- **Testing**: pytest with 90% minimum coverage requirement
- **Language**: American English for all code, comments, and documentation (use sentence case, including titles)

### Writing Style Guidelines
- **Tone**: Friendly and informative
- **Perspective**: Use second-person ("you" and "your") for user-facing messages
- **Inclusivity**: Use objective, non-discriminatory language
- **Clarity**: Write for non-native English speakers
- **Formatting in Messages**:
  - Use backticks for: file paths, filenames, variable names, field entries
  - Use sentence case for titles and messages (capitalize only the first word and proper nouns)
  - Avoid abbreviations when possible

### Documentation Standards
- **File Headers**: Short and concise
  ```python
  """UniFi Insights integration for Home Assistant."""
  ```
- **Method/Function Docstrings**: Required for all
  ```python
  async def async_setup_entry(hass: HomeAssistant, entry: UnifiInsightsConfigEntry) -> bool:
      """Set up UniFi Insights from a config entry."""
  ```
- **Comment Style**:
  - Use clear, descriptive comments
  - Explain the "why" not just the "what"
  - Keep code block lines under 88 characters when possible

## Async Programming

- All external I/O operations must be async
- **Best Practices**:
  - Avoid sleeping in loops
  - Avoid awaiting in loops - use `gather` instead
  - No blocking calls
  - Group executor jobs when possible

### Blocking Operations
- **Use Executor**: For blocking I/O operations
  ```python
  result = await hass.async_add_executor_job(blocking_function, args)
  ```
- **Never Block Event Loop**: Avoid file operations, `time.sleep()`, blocking HTTP calls
- **Replace with Async**: Use `asyncio.sleep()` instead of `time.sleep()`

### Thread Safety
- **@callback Decorator**: For event loop safe functions
  ```python
  @callback
  def async_update_callback(self, event):
      """Safe to run in event loop."""
      self.async_write_ha_state()
  ```
- **Sync APIs from Threads**: Use sync versions when calling from non-event loop threads
- **Registry Changes**: Must be done in event loop thread

### Error Handling
- **Exception Types**: Choose most specific exception available
  - `ServiceValidationError`: User input errors (preferred over `ValueError`)
  - `HomeAssistantError`: Device communication failures
  - `ConfigEntryNotReady`: Temporary setup issues (device offline)
  - `ConfigEntryAuthFailed`: Authentication problems
  - `ConfigEntryError`: Permanent setup issues
- **Try/Catch Best Practices**:
  - Only wrap code that can throw exceptions
  - Keep try blocks minimal - process data after the try/catch
  - **Avoid bare exceptions** except in specific cases:
    - ❌ Generally not allowed: `except:` or `except Exception:`
    - ✅ Allowed in config flows to ensure robustness
    - ✅ Allowed in functions/methods that run in background tasks
  - Good pattern:
    ```python
    try:
        data = await self.api.get_data()  # Can throw
    except ApiException:
        _LOGGER.error("Failed to get data")
        return

    # ✅ Process data outside try block
    processed = data.get("value", 0) * 100
    self._attr_native_value = processed
    ```
- **Setup Failure Patterns**:
  ```python
  try:
      await client.async_connect()
  except (asyncio.TimeoutError, TimeoutException) as ex:
      raise ConfigEntryNotReady(f"Timeout connecting to UniFi controller") from ex
  except AuthenticationError as ex:
      raise ConfigEntryAuthFailed(f"Invalid credentials") from ex
  ```

### Logging
- **Format Guidelines**:
  - No periods at end of messages
  - No integration names/domains (added automatically)
  - No sensitive data (keys, tokens, passwords)
- Use debug level for non-user-facing messages
- **Use Lazy Logging**:
  ```python
  _LOGGER.debug("This is a log message with %s", variable)
  ```

### Unavailability Logging
- **Log Once**: When device/service becomes unavailable (info level)
- **Log Recovery**: When device/service comes back online
- **Implementation Pattern**:
  ```python
  _unavailable_logged: bool = False

  if not self._unavailable_logged:
      _LOGGER.info("The sensor is unavailable: %s", ex)
      self._unavailable_logged = True
  # On recovery:
  if self._unavailable_logged:
      _LOGGER.info("The sensor is back online")
      self._unavailable_logged = False
  ```

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate  # Windows

# Install development dependencies
pip install -e ".[dev]"
```

### Code Quality & Linting
```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Run ruff linting
ruff check .

# Run ruff formatting
ruff format .

# Run MyPy type checking
mypy custom_components/unifi_insights

# Run Bandit security scan
bandit -r custom_components/unifi_insights
```

### Testing
```bash
# Run all tests with coverage
pytest

# Run specific test file
pytest tests/test_sensor.py

# Run tests with verbose output
pytest -vvs

# Run tests without coverage
pytest --no-cov
```

## Project Structure

```
ha-unifi-insights/
├── custom_components/
│   └── unifi_insights/
│       ├── __init__.py          # Integration setup
│       ├── config_flow.py       # Configuration UI
│       ├── const.py             # Constants
│       ├── coordinator.py       # Data update coordinator
│       ├── coordinators/        # Specialized coordinators
│       ├── entity.py            # Base entity classes
│       ├── sensor.py            # Sensor platform
│       ├── binary_sensor.py     # Binary sensor platform
│       ├── switch.py            # Switch platform
│       ├── button.py            # Button platform
│       ├── device_tracker.py    # Device tracker platform
│       ├── camera.py            # Camera platform
│       ├── light.py             # Light platform
│       ├── number.py            # Number platform
│       ├── select.py            # Select platform
│       ├── event.py             # Event platform
│       ├── update.py            # Update platform
│       ├── services.py          # Service definitions
│       ├── diagnostics.py       # Diagnostic data
│       ├── repairs.py           # Repair flows
│       └── data_transforms.py   # Data transformation utilities
├── tests/                       # Test files
└── pyproject.toml              # Project configuration
```

## Common Anti-Patterns & Best Practices

### ❌ **Avoid These Patterns**
```python
# Blocking operations in event loop
data = requests.get(url)  # ❌ Blocks event loop
time.sleep(5)  # ❌ Blocks event loop

# Hardcoded strings in code
self._attr_name = "Temperature Sensor"  # ❌ Not translatable

# Missing error handling
data = await self.api.get_data()  # ❌ No exception handling

# Storing sensitive data in diagnostics
return {"api_key": entry.data[CONF_API_KEY]}  # ❌ Exposes secrets

# Accessing hass.data directly in tests
coordinator = hass.data[DOMAIN][entry.entry_id]  # ❌ Don't access hass.data

# User-configurable polling intervals
vol.Optional("scan_interval", default=60): cv.positive_int  # ❌ Not allowed

# Too much code in try block
try:
    response = await client.get_data()  # Can throw
    # ❌ Data processing should be outside try block
    temperature = response["temperature"] / 10
    self._attr_native_value = temperature
except ClientError:
    _LOGGER.error("Failed to fetch data")

# Bare exceptions in regular code
try:
    value = await sensor.read_value()
except Exception:  # ❌ Too broad - catch specific exceptions
    _LOGGER.error("Failed to read sensor")
```

### ✅ **Use These Patterns Instead**
```python
# Async operations with executor
data = await hass.async_add_executor_job(requests.get, url)
await asyncio.sleep(5)  # ✅ Non-blocking

# Translatable entity names
_attr_translation_key = "temperature_sensor"  # ✅ Translatable

# Proper error handling
try:
    data = await self.api.get_data()
except ApiException as err:
    raise UpdateFailed(f"API error: {err}") from err

# Redacted diagnostics data
return async_redact_data(data, {"api_key", "password"})  # ✅ Safe

# Test through proper integration setup and fixtures
@pytest.fixture
async def init_integration(hass, mock_config_entry, mock_api):
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)  # ✅ Proper setup

# Integration-determined polling intervals
SCAN_INTERVAL = timedelta(minutes=5)  # ✅ Constant in const.py

class UnifiInsightsCoordinator(DataUpdateCoordinator[UnifiInsightsData]):
    def __init__(self, hass: HomeAssistant, client: UnifiClient, config_entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
            config_entry=config_entry,
        )
```

## UniFi-Specific Considerations

- **API Rate Limiting**: Be mindful of UniFi controller API rate limits when setting polling intervals
- **Device Discovery**: Handle dynamic device discovery as UniFi networks can change
- **Connection Resilience**: UniFi controllers may restart or become temporarily unavailable
- **Multiple Sites**: Support for multi-site UniFi deployments where applicable
- **Protect Integration**: Camera entities should handle UniFi Protect separately from network devices
