# unifi-official-api Library API Contract

**Library**: unifi-official-api
**Version**: 1.0.0
**Repository**: https://github.com/ruaan-deysel/unifi-official-api
**Date**: 2026-01-19

## Overview

This document serves as the API contract reference for the unifi-official-api library. It will be populated during Phase 0 research (Task 1) after reviewing the library source code and documentation.

**Status**: ⏳ **PENDING RESEARCH**

---

## Library Installation

```bash
pip install unifi-official-api~=1.0.0
```

**PyPI**: https://pypi.org/project/unifi-official-api/

---

## Client Initialization

### Expected Pattern

```python
from unifi_official_api import UniFiClient

client = UniFiClient(
    host="https://192.168.1.1",
    api_key="your-api-key-here",
    verify_ssl=False,  # Optional, defaults to True
    timeout=30,        # Optional, defaults to 30
)

# Validate connection
await client.validate()
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `host` | str | Yes | None | UniFi controller URL |
| `api_key` | str | Yes | None | API key from controller |
| `verify_ssl` | bool | No | True | Verify SSL certificates |
| `timeout` | int | No | 30 | Request timeout in seconds |

---

## Network API

### Client Access

```python
network = client.network
```

### Methods (To Be Documented)

#### Get Sites
```python
sites = await client.network.get_sites()
# Returns: List[dict]
```

#### Get Devices
```python
devices = await client.network.get_devices(site_id: str)
# Returns: List[dict]
```

#### Get Device Info
```python
device = await client.network.get_device(site_id: str, device_id: str)
# Returns: dict
```

#### Get Device Stats
```python
stats = await client.network.get_device_stats(site_id: str, device_id: str)
# Returns: dict
```

#### Get Clients
```python
clients = await client.network.get_clients(site_id: str)
# Returns: List[dict]
```

#### Restart Device
```python
await client.network.restart_device(site_id: str, device_id: str)
# Returns: None
```

#### Power Cycle Port
```python
await client.network.power_cycle_port(
    site_id: str,
    device_id: str,
    port_idx: int
)
# Returns: None
```

**[Additional Network API methods to be documented during research]**

---

## Protect API

### Client Access

```python
protect = client.protect
```

### Methods (To Be Documented)

#### Get Cameras
```python
cameras = await client.protect.get_cameras()
# Returns: List[dict]
```

#### Get Camera Snapshot
```python
snapshot_bytes = await client.protect.get_snapshot(
    camera_id: str,
    high_quality: bool = False
)
# Returns: bytes
```

#### Get Stream URL
```python
stream_url = await client.protect.get_stream_url(
    camera_id: str,
    quality: str = "high"
)
# Returns: str (RTSPS URL)
```

#### Update Camera
```python
await client.protect.update_camera(
    camera_id: str,
    data: dict
)
# Returns: dict (updated camera)
```

#### Get Lights
```python
lights = await client.protect.get_lights()
# Returns: List[dict]
```

#### Update Light
```python
await client.protect.update_light(
    light_id: str,
    on: bool = None,
    brightness: int = None
)
# Returns: dict (updated light)
```

**[Additional Protect API methods to be documented during research]**

---

## WebSocket API

**Status**: ⚠️ **CRITICAL - REQUIRES RESEARCH**

### Expected Pattern (If Supported)

```python
# Subscribe to device updates
await client.protect.subscribe_devices(
    callback=my_device_callback
)

# Subscribe to events
await client.protect.subscribe_events(
    callback=my_event_callback
)

# Callback signature
async def my_device_callback(event: dict) -> None:
    """Handle device update event."""
    device_id = event["id"]
    # Process update
    pass

# Unsubscribe
await client.protect.unsubscribe_all()
```

### Event Types (If Supported)

- Device updates
- Motion events
- Doorbell rings
- Smart detection events

**[Complete WebSocket documentation during research Task 3]**

---

## Exception Types

### Expected Exceptions

```python
from unifi_official_api.exceptions import (
    UniFiAuthError,        # Authentication failures (401, 403)
    UniFiConnectionError,  # Connection/network issues
    UniFiAPIError,         # General API errors (4xx, 5xx)
    UniFiTimeoutError,     # Request timeouts
)
```

### Exception Hierarchy

```
Exception
└── UniFiError (base)
    ├── UniFiAuthError
    ├── UniFiConnectionError
    ├── UniFiAPIError
    └── UniFiTimeoutError
```

### Exception Details

| Exception | When Raised | Attributes | Recommended Action |
|-----------|-------------|------------|-------------------|
| `UniFiAuthError` | Invalid API key, expired credentials | `message`, `status_code` | Trigger reauth |
| `UniFiConnectionError` | Network unreachable, DNS failure | `message`, `original_error` | Mark unavailable |
| `UniFiAPIError` | API errors (4xx/5xx responses) | `message`, `status_code`, `response` | Log + retry |
| `UniFiTimeoutError` | Request exceeds timeout | `message`, `timeout` | Retry with backoff |

**[Verify and complete during research Task 4]**

---

## Data Structures

### Network Device Schema

```python
{
    "id": "abc123",
    "mac": "AA:BB:CC:DD:EE:FF",
    "model": "USW-24-POE",
    "name": "Office Switch",
    "status": "online",
    "adopted": True,
    "firmware_version": "6.5.55",
    "uptime_seconds": 864000,
    "cpu_percent": 15.2,
    "memory_percent": 42.8,
    "tx_bytes": 1024000000,
    "rx_bytes": 2048000000,
    "site": "default"
}
```

### Protect Camera Schema

```python
{
    "id": "camera123",
    "name": "Front Door",
    "model": "UVC-G4-DOORBELL",
    "status": "connected",
    "recording": True,
    "motion": False,
    "hdr": "auto",
    "video_mode": "default",
    "microphone_volume": 80,
    # ... additional fields
}
```

**[Complete all schemas during research Task 2]**

---

## Usage Examples

### Complete Integration Example

```python
from unifi_official_api import UniFiClient
from unifi_official_api.exceptions import UniFiAuthError, UniFiConnectionError

# Initialize client
client = UniFiClient(
    host="https://192.168.1.1",
    api_key="your-api-key",
    verify_ssl=False,
)

try:
    # Validate connection
    await client.validate()

    # Fetch network data
    sites = await client.network.get_sites()
    for site in sites:
        devices = await client.network.get_devices(site["id"])
        print(f"Site: {site['name']}, Devices: {len(devices)}")

    # Fetch Protect data
    cameras = await client.protect.get_cameras()
    for camera in cameras:
        print(f"Camera: {camera['name']}, Status: {camera['status']}")

    # Control device
    await client.network.restart_device(site_id="default", device_id="device123")

except UniFiAuthError as err:
    print(f"Authentication failed: {err}")

except UniFiConnectionError as err:
    print(f"Connection error: {err}")

finally:
    await client.close()  # If library requires cleanup
```

---

## Research Tasks

- [ ] Document complete Network API surface (all methods, parameters, return types)
- [ ] Document complete Protect API surface (all methods, parameters, return types)
- [ ] Verify WebSocket support and document WebSocket API
- [ ] Document all exception types and when they're raised
- [ ] Document all data structure schemas
- [ ] Add usage examples for common operations
- [ ] Verify async patterns and aiohttp session management
- [ ] Document any rate limiting or retry logic in library
- [ ] Identify library version compatibility requirements
- [ ] Test library with real UniFi controller for validation

---

**Contract Status**: 🟡 **TEMPLATE COMPLETE**
**Research Status**: ⏳ **PENDING**
**Completion Criteria**: All sections filled with verified library information

**Last Updated**: 2026-01-19
