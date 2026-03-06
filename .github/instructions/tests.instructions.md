---
applyTo: "tests/**/*.py"
---

# Testing Instructions

**Applies to:** All test files

## Framework

- **pytest** with `pytest-homeassistant-custom-component`
- **pytest-asyncio** for async test support
- **Coverage:** 90% minimum (branch coverage enabled)

## Running Tests

```bash
pytest                       # All tests with coverage
pytest tests/test_sensor.py  # Specific test file
pytest -vvs                  # Verbose output
pytest --no-cov              # Without coverage
```

## Test Structure

Tests mirror the integration structure:

```
tests/
├── conftest.py              # Shared fixtures
├── fixtures/                # Mock data fixtures
├── test_init.py             # Integration setup tests
├── test_config_flow.py      # Config flow tests
├── test_coordinator.py      # Legacy coordinator tests
├── test_coordinators.py     # Multi-coordinator tests
├── test_sensor.py           # Sensor platform tests
├── test_binary_sensor.py    # Binary sensor tests
├── test_switch.py           # Switch tests
├── test_services.py         # Service tests
├── test_entity.py           # Base entity tests
├── test_data_transforms.py  # Data transform tests
└── ...
```

## Fixtures

- Use `conftest.py` for shared fixtures
- Mock API responses, not internal functions
- Use `pytest-homeassistant-custom-component` fixtures for HA setup
- Set up integration through proper config entry flow

```python
@pytest.fixture
async def init_integration(hass, mock_config_entry, mock_api):
    """Set up the integration for testing."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
```

## Best Practices

- Test through the integration's public API (config entries, entities, services)
- Don't access `hass.data` directly in tests
- Mock at the API boundary, not at internal layers
- Test error paths and edge cases
- Use `freeze_time` for time-dependent tests
- Group related tests in classes when it improves readability
