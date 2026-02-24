---
applyTo: "custom_components/unifi_insights/coordinator.py, custom_components/unifi_insights/coordinators/**/*.py"
---

# Coordinator Instructions

**Applies to:** Data coordinator implementation files

## Multi-Coordinator Architecture

This integration uses a multi-coordinator pattern:

- **Base Coordinator** (`coordinators/base.py`) — Abstract base with common patterns
- **Config Coordinator** (`coordinators/config.py`) — Site/config data (minimal polling)
- **Device Coordinator** (`coordinators/device.py`) — Network device metrics
- **Protect Coordinator** (`coordinators/protect.py`) — Camera, light, sensor, NVR data (WebSocket + polling)
- **Facade Coordinator** (`coordinators/facade.py`) — Unified view for backward compatibility

## Data Flow

```
API Clients → Config Coordinator → Device Coordinator → Protect Coordinator → Facade → Entities
```

## Error Handling

- Raise `ConfigEntryAuthFailed` for authentication failures (triggers reauth flow)
- Raise `UpdateFailed` for transient failures (HA will retry)
- Use `ConfigEntryNotReady` during setup for temporary issues

```python
async def _async_update_data(self) -> dict[str, Any]:
    try:
        data = await self.api_client.get_data()
    except AuthenticationError as err:
        raise ConfigEntryAuthFailed from err
    except ApiError as err:
        raise UpdateFailed(f"Error fetching data: {err}") from err
    return data
```

## First Refresh

Always use `async_config_entry_first_refresh()` during setup:

```python
coordinator = UnifiInsightsCoordinator(hass, client, entry)
await coordinator.async_config_entry_first_refresh()
```

## Data Schema

Coordinator stores data under keys:
- `sites` — Site configuration data
- `devices` — Network device data
- `clients` — Network client data
- `stats` — Device statistics
- `protect` — Protect data (cameras, lights, sensors, NVRs, viewers, chimes, liveviews, events)

## Stale Device Cleanup

The coordinator cleans stale devices from the HA device registry using previously seen device IDs. When adding new data sources, ensure the cleanup logic accounts for them.

## Polling Interval

- Default: 30 seconds (configurable 10-300s)
- Use exponential backoff on repeated failures
- Protect also uses WebSocket for low-latency event updates

## Best Practices

- Never expose API client directly to entities
- Transform data in coordinator before storing
- Use `data_transforms.py` for API response normalization
- Keep coordinator data schema consistent for entity lookups
