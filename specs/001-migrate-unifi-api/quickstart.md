# Developer Quickstart: unifi-official-api Migration

**Date**: 2026-01-19
**Audience**: Developers implementing the migration
**Purpose**: Quick reference guide for common migration patterns

## Prerequisites

- Python 3.11+
- Home Assistant 2025.9.0+
- unifi-official-api ~=1.0.0
- Access to UniFi controller for testing

---

## 1. Installation & Setup

### Add Library Dependency

**File**: `custom_components/unifi_insights/manifest.json`

```json
{
  "requirements": ["unifi-official-api~=1.0.0"]
}
```

### Install for Development

```bash
cd /path/to/ha-unifi-insights
pip install -e .
pip install unifi-official-api~=1.0.0
```

---

## 2. Import Changes

### Before (Custom API)

```python
from .unifi_network_api import (
    UnifiInsightsClient,
    UnifiInsightsError,
    UnifiInsightsAuthError,
    UnifiInsightsConnectionError,
)
from .unifi_protect_api import (
    UnifiProtectClient,
    UnifiProtectAuthError,
    UnifiProtectConnectionError,
)
```

### After (Library)

```python
from unifi_official_api import UniFiClient
from unifi_official_api.exceptions import (
    UniFiAuthError,
    UniFiConnectionError,
    UniFiAPIError,
    UniFiTimeoutError,
)
```

---

## 3. Client Initialization

### Before (Custom API)

```python
# __init__.py
network_client = UnifiInsightsClient(
    host=entry.data[CONF_HOST],
    api_key=entry.data[CONF_API_KEY],
    session=async_get_clientsession(hass),
)

protect_client = UnifiProtectClient(
    host=entry.data[CONF_HOST],
    api_key=entry.data[CONF_API_KEY],
    session=async_get_clientsession(hass),
)
```

### After (Library)

```python
# __init__.py
client = UniFiClient(
    host=entry.data[CONF_HOST],
    api_key=entry.data[CONF_API_KEY],
    verify_ssl=entry.data.get(CONF_VERIFY_SSL, False),
)

# Validate connection
try:
    await client.validate()
except UniFiAuthError as err:
    raise ConfigEntryAuthFailed(f"Invalid API key: {err}") from err
except UniFiConnectionError as err:
    raise ConfigEntryNotReady(f"Cannot connect: {err}") from err
```

---

## 4. Coordinator Updates

### Before (Custom API)

```python
# coordinator.py
class UnifiInsightsDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, network_client, protect_client):
        self.network_client = network_client
        self.protect_client = protect_client

    async def _async_update_data(self):
        sites = await self.network_client.async_get_sites()
        cameras = await self.protect_client.async_get_cameras()
```

### After (Library)

```python
# coordinator.py
from .data_transforms import (  # New module
    transform_network_device,
    transform_protect_camera,
)

class UnifiInsightsDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, client):
        self.client = client  # Single unified client

    async def _async_update_data(self):
        # Fetch from library
        lib_sites = await self.client.network.get_sites()

        # Transform responses
        sites = [transform_network_site(s) for s in lib_sites]

        lib_cameras = await self.client.protect.get_cameras()
        cameras = {
            c["id"]: transform_protect_camera(c)
            for c in lib_cameras
        }
```

---

## 5. Exception Handling

### Before (Custom API)

```python
try:
    data = await self.network_client.async_get_devices(site_id)
except UnifiInsightsAuthError as err:
    raise ConfigEntryAuthFailed from err
except UnifiInsightsConnectionError as err:
    raise UpdateFailed from err
```

### After (Library)

```python
try:
    data = await self.client.network.get_devices(site_id)
except UniFiAuthError as err:
    raise ConfigEntryAuthFailed(f"Auth failed: {err}") from err
except UniFiConnectionError as err:
    raise UpdateFailed(f"Connection error: {err}") from err
except UniFiTimeoutError as err:
    raise UpdateFailed(f"Timeout: {err}") from err
except UniFiAPIError as err:
    raise UpdateFailed(f"API error: {err}") from err
```

---

## 6. Service Calls

### Before (Custom API)

```python
# services.py
async def async_restart_device(call):
    site_id = call.data["site_id"]
    device_id = call.data["device_id"]

    coordinator = hass.data[DOMAIN][entry.entry_id]
    await coordinator.network_client.async_restart_device(
        site_id, device_id
    )
```

### After (Library)

```python
# services.py
async def async_restart_device(call):
    site_id = call.data["site_id"]
    device_id = call.data["device_id"]

    coordinator = hass.data[DOMAIN][entry.entry_id]
    await coordinator.client.network.restart_device(
        site_id, device_id
    )
```

---

## 7. Entity Data Access

### Before (Custom API)

```python
# sensor.py
class UnifiDeviceCPUSensor(UnifiInsightsEntity, SensorEntity):
    @property
    def native_value(self):
        device = self.coordinator.data["devices"].get(self.device_id)
        return device.get("cpu_usage")  # Custom API field name
```

### After (Library) - With Transformation

```python
# sensor.py
class UnifiDeviceCPUSensor(UnifiInsightsEntity, SensorEntity):
    @property
    def native_value(self):
        device = self.coordinator.data["devices"].get(self.device_id)
        # Still uses "cpu_usage" because coordinator transforms it
        return device.get("cpu_usage")
```

**No entity changes needed** if coordinator handles transformation.

---

## 8. WebSocket Handling

### Before (Custom API)

```python
# coordinator.py
async def async_setup(self):
    await self.protect_client.async_start_websocket()
    self.protect_client.register_device_update_callback(
        self._handle_device_update
    )
```

### After (Library) - If Supported

```python
# coordinator.py
async def async_setup(self):
    await self.client.protect.subscribe_devices(
        callback=self._handle_device_update
    )
```

### After (Library) - If NOT Supported

```python
# coordinator.py
# Option 1: Remove WebSocket, rely on polling
# (Simplest, but loses real-time updates)

# Option 2: Maintain custom WebSocket alongside library
# (Hybrid approach, more complex)
from .websocket_manager import ProtectWebSocketManager

self.ws_manager = ProtectWebSocketManager(
    host=self.client.host,
    api_key=self.client.api_key,
)
await self.ws_manager.connect()
```

**See research.md Section 4 for WebSocket migration decision.**

---

## 9. Testing Patterns

### Mock Library Client

```python
# conftest.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from unifi_official_api import UniFiClient

@pytest.fixture
def mock_unifi_client():
    """Mock UniFi library client."""
    client = MagicMock(spec=UniFiClient)
    client.network = AsyncMock()
    client.protect = AsyncMock()
    client.validate = AsyncMock(return_value=True)

    # Mock network methods
    client.network.get_sites = AsyncMock(return_value=[
        {"id": "default", "name": "Default"}
    ])
    client.network.get_devices = AsyncMock(return_value=[
        {"id": "dev1", "mac": "AA:BB:CC:DD:EE:FF"}
    ])

    # Mock protect methods
    client.protect.get_cameras = AsyncMock(return_value=[
        {"id": "cam1", "name": "Front Door"}
    ])

    return client
```

### Test Coordinator

```python
# test_coordinator.py
async def test_coordinator_update(hass, mock_unifi_client):
    """Test coordinator data update with library."""
    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        client=mock_unifi_client,
    )

    await coordinator.async_config_entry_first_refresh()

    assert coordinator.data is not None
    assert "devices" in coordinator.data
    mock_unifi_client.network.get_sites.assert_called_once()
```

---

## 10. Common Pitfalls

### ❌ Don't Do This

```python
# Entities calling library directly
class MySensor(SensorEntity):
    async def async_update(self):
        # BAD: Entity calling library
        data = await self.client.network.get_device(...)
```

### ✅ Do This Instead

```python
# Entities using coordinator data
class MySensor(CoordinatorEntity, SensorEntity):
    @property
    def native_value(self):
        # GOOD: Entity consuming coordinator data
        device = self.coordinator.data["devices"].get(self.device_id)
        return device.get("cpu_usage")
```

### ❌ Don't Do This

```python
# Forgetting to transform library responses
async def _async_update_data(self):
    devices = await self.client.network.get_devices(site_id)
    return devices  # BAD: Raw library format
```

### ✅ Do This Instead

```python
# Transforming library responses
async def _async_update_data(self):
    lib_devices = await self.client.network.get_devices(site_id)
    # GOOD: Transform to internal format
    devices = {
        d["id"]: transform_network_device(d)
        for d in lib_devices
    }
    return devices
```

---

## 11. Debugging Tips

### Enable Debug Logging

```yaml
# configuration.yaml
logger:
  default: info
  logs:
    custom_components.unifi_insights: debug
    unifi_official_api: debug # Library logs
```

### Test Library Directly

```python
# test_library.py - Standalone test
import asyncio
from unifi_official_api import UniFiClient

async def test_library():
    client = UniFiClient(
        host="https://192.168.1.1",
        api_key="your-key",
        verify_ssl=False,
    )

    try:
        await client.validate()
        sites = await client.network.get_sites()
        print(f"Sites: {sites}")

        cameras = await client.protect.get_cameras()
        print(f"Cameras: {cameras}")

    except Exception as err:
        print(f"Error: {err}")

asyncio.run(test_library())
```

### Compare Responses

```python
# Compare custom API vs library responses
custom_device = await old_client.async_get_device(site_id, device_id)
lib_device = await new_client.network.get_device(site_id, device_id)

print("Custom API:", json.dumps(custom_device, indent=2))
print("Library:", json.dumps(lib_device, indent=2))
```

---

## 12. Migration Checklist

- [ ] Library dependency added to manifest.json
- [ ] Imports updated (remove custom API, add library)
- [ ] Client initialization changed to UniFiClient
- [ ] Coordinator updated to use single client
- [ ] Data transformation functions implemented
- [ ] Exception handling updated
- [ ] Services updated to call library methods
- [ ] WebSocket migration completed (if applicable)
- [ ] Tests updated to mock library
- [ ] Manual testing performed
- [ ] Custom API files deleted (unifi_network_api.py, unifi_protect_api.py)
- [ ] hassfest validation passes
- [ ] Code coverage >= 80%

---

## 13. Getting Help

### Resources

- **Library Docs**: https://github.com/ruaan-deysel/unifi-official-api
- **HA Integration Docs**: https://developers.home-assistant.io/
- **Project Plan**: `specs/001-migrate-unifi-api/plan.md`
- **Research Notes**: `specs/001-migrate-unifi-api/research.md`
- **Data Mappings**: `specs/001-migrate-unifi-api/data-model.md`

### Common Issues

| Issue             | Solution                                           |
| ----------------- | -------------------------------------------------- |
| Import errors     | Verify library installed: `pip list \| grep unifi` |
| Auth failures     | Check API key valid, not expired                   |
| Connection errors | Verify host URL, SSL settings                      |
| Missing methods   | Check library version (should be ~=1.0.0)          |
| Test failures     | Update mocks to match library interface            |

---

**Quickstart Status**: ✅ **COMPLETE**
**Last Updated**: 2026-01-19
