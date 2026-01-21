# Data Model: unifi-official-api Migration

**Date**: 2026-01-19
**Feature**: Migrate to unifi-official-api Library
**Purpose**: Document entity data mappings between custom API and library responses

## Overview

This document defines the data structure transformations required to migrate from custom UniFi API clients to the unifi-official-api library while maintaining 100% entity attribute compatibility.

**Transformation Strategy**: Implement mapping layer in coordinator to isolate changes from entity platforms.

---

## Coordinator Data Structure

### Current Structure (Custom API)

```python
{
    "sites": {                      # Network sites
        "site_id": {...}
    },
    "devices": {                    # Network devices
        "device_id": {...}
    },
    "clients": {                    # Connected clients
        "client_id": {...}
    },
    "stats": {                      # Device statistics
        "device_id": {...}
    },
    "network_info": {...},          # Application info
    "vouchers": {...},              # Guest vouchers
    "protect": {                    # Protect subsystem
        "cameras": {
            "camera_id": {...}
        },
        "lights": {
            "light_id": {...}
        },
        "sensors": {
            "sensor_id": {...}
        },
        "nvrs": {...},
        "viewers": {...},
        "chimes": {...},
        "liveviews": {...},
        "protect_info": {...},
        "events": {...}
    },
    "last_update": datetime
}
```

### Post-Migration Structure (With Library)

**No changes to structure** - coordinator maintains same dictionary format. Library responses are transformed on ingest.

---

## Network Device Mappings

### Device Status Fields

| Current Field  | Library Field      | Transform  | Notes                   |
| -------------- | ------------------ | ---------- | ----------------------- |
| `id`           | `id`               | None       | Direct mapping          |
| `mac`          | `mac`              | None       | Direct mapping          |
| `model`        | `model`            | None       | Direct mapping          |
| `name`         | `name`             | None       | Direct mapping          |
| `state`        | `status`           | Map values | "connected" ↔ "online" |
| `adopted`      | `adopted`          | None       | Direct mapping          |
| `version`      | `firmware_version` | None       | Key name change only    |
| `uptime`       | `uptime_seconds`   | None       | Key name change only    |
| `cpu_usage`    | `cpu_percent`      | None       | Key name change only    |
| `memory_usage` | `memory_percent`   | None       | Key name change only    |
| `tx_bytes`     | `tx_bytes`         | None       | Direct mapping          |
| `rx_bytes`     | `rx_bytes`         | None       | Direct mapping          |
| `site_id`      | `site`             | None       | Key name change only    |

### Transformation Function

```python
def transform_network_device(lib_device: dict) -> dict:
    """Transform library device response to internal format."""
    return {
        "id": lib_device.get("id"),
        "mac": lib_device.get("mac"),
        "model": lib_device.get("model"),
        "name": lib_device.get("name"),
        "state": map_device_status(lib_device.get("status")),
        "adopted": lib_device.get("adopted"),
        "version": lib_device.get("firmware_version"),
        "uptime": lib_device.get("uptime_seconds"),
        "cpu_usage": lib_device.get("cpu_percent"),
        "memory_usage": lib_device.get("memory_percent"),
        "tx_bytes": lib_device.get("tx_bytes"),
        "rx_bytes": lib_device.get("rx_bytes"),
        "site_id": lib_device.get("site"),
    }

def map_device_status(lib_status: str) -> str:
    """Map library status to internal format."""
    status_map = {
        "online": "connected",
        "offline": "disconnected",
        "unknown": "unknown",
    }
    return status_map.get(lib_status, lib_status)
```

---

## Protect Device Mappings

### Camera Fields

| Current Field     | Library Field | Transform | Notes                                     |
| ----------------- | ------------- | --------- | ----------------------------------------- |
| `id`              | `id`          | None      | Direct mapping                            |
| `name`            | `name`        | None      | Direct mapping                            |
| `state`           | `status`      | Uppercase | "CONNECTED" ↔ "connected"                |
| `is_recording`    | `recording`   | None      | Key name change                           |
| `motion_detected` | `motion`      | None      | Key name change                           |
| `type`            | `model`       | None      | Key name change                           |
| `hdr_mode`        | `hdr`         | Uppercase | "AUTO" ↔ "auto"                          |
| `video_mode`      | `video_mode`  | Uppercase | "DEFAULT" ↔ "default"                    |
| `snapshot_url`    | Method call   | Generate  | `await client.protect.get_snapshot(id)`   |
| `rtsps_url`       | Method call   | Generate  | `await client.protect.get_stream_url(id)` |

### Transformation Function

```python
def transform_protect_camera(lib_camera: dict) -> dict:
    """Transform library camera response to internal format."""
    return {
        "id": lib_camera.get("id"),
        "name": lib_camera.get("name"),
        "state": lib_camera.get("status", "").upper(),
        "is_recording": lib_camera.get("recording"),
        "motion_detected": lib_camera.get("motion"),
        "type": lib_camera.get("model"),
        "hdr_mode": lib_camera.get("hdr", "").upper(),
        "video_mode": lib_camera.get("video_mode", "").upper(),
        # snapshot_url and rtsps_url generated on-demand
    }
```

### Light Fields

| Current Field | Library Field | Transform | Notes                |
| ------------- | ------------- | --------- | -------------------- |
| `id`          | `id`          | None      | Direct mapping       |
| `name`        | `name`        | None      | Direct mapping       |
| `is_on`       | `on`          | None      | Key name change      |
| `brightness`  | `brightness`  | None      | Direct mapping       |
| `mode`        | `light_mode`  | Uppercase | "MOTION" ↔ "motion" |
| `is_dark`     | `dark`        | None      | Key name change      |

### Transformation Function

```python
def transform_protect_light(lib_light: dict) -> dict:
    """Transform library light response to internal format."""
    return {
        "id": lib_light.get("id"),
        "name": lib_light.get("name"),
        "is_on": lib_light.get("on"),
        "brightness": lib_light.get("brightness"),
        "mode": lib_light.get("light_mode", "").upper(),
        "is_dark": lib_light.get("dark"),
    }
```

### Sensor Fields

| Current Field        | Library Field | Transform | Notes           |
| -------------------- | ------------- | --------- | --------------- |
| `id`                 | `id`          | None      | Direct mapping  |
| `name`               | `name`        | None      | Direct mapping  |
| `temperature`        | `temperature` | None      | Direct mapping  |
| `humidity`           | `humidity`    | None      | Direct mapping  |
| `light_level`        | `light`       | None      | Key name change |
| `battery_percentage` | `battery`     | None      | Key name change |

### Chime Fields

| Current Field  | Library Field | Transform | Notes           |
| -------------- | ------------- | --------- | --------------- |
| `id`           | `id`          | None      | Direct mapping  |
| `name`         | `name`        | None      | Direct mapping  |
| `volume`       | `volume`      | None      | Direct mapping  |
| `repeat_times` | `repeat`      | None      | Key name change |
| `ringtone_id`  | `ringtone`    | None      | Key name change |

---

## WebSocket Event Mappings

**Status**: ⏳ Pending library WebSocket research

**If library supports WebSockets**, event structures will need mapping:

### Device Update Events

```python
# Current custom format
{
    "type": "device_update",
    "device_id": "camera123",
    "data": {...}  # Full device object
}

# Library format (expected)
{
    "event": "device.updated",
    "id": "camera123",
    "changes": {...}  # Delta only?
}
```

### Motion Events

```python
# Current custom format
{
    "type": "motion_detected",
    "camera_id": "camera123",
    "timestamp": "2026-01-19T10:00:00Z"
}

# Library format (expected)
{
    "event": "motion.detected",
    "device_id": "camera123",
    "timestamp": 1705658400
}
```

**Action**: Complete this section after WebSocket research (Task 3 in research.md)

---

## Coordinator Integration

### Data Update Flow

```python
class UnifiInsightsDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator with library integration."""

    async def _async_update_data(self) -> dict:
        """Fetch data from library and transform."""
        data = {
            "sites": {},
            "devices": {},
            "clients": {},
            "stats": {},
            "network_info": {},
            "vouchers": {},
            "protect": {
                "cameras": {},
                "lights": {},
                "sensors": {},
                "nvrs": {},
                "viewers": {},
                "chimes": {},
                "liveviews": {},
                "protect_info": {},
                "events": {},
            },
            "last_update": None,
        }

        # Fetch from library
        sites = await self.client.network.get_sites()
        for site in sites:
            site_id = site["id"]
            data["sites"][site_id] = site

            # Fetch devices for site
            lib_devices = await self.client.network.get_devices(site_id)
            for lib_device in lib_devices:
                # Transform and store
                device = transform_network_device(lib_device)
                data["devices"][device["id"]] = device

        # Fetch Protect devices
        lib_cameras = await self.client.protect.get_cameras()
        for lib_camera in lib_cameras:
            camera = transform_protect_camera(lib_camera)
            data["protect"]["cameras"][camera["id"]] = camera

        # ... similar for lights, sensors, etc.

        data["last_update"] = utcnow()
        return data
```

---

## Entity Attribute Preservation

### Critical Requirement

**All entity unique IDs MUST remain unchanged** to preserve history.

### Unique ID Patterns

| Entity Type    | Unique ID Format                  | Source Field       |
| -------------- | --------------------------------- | ------------------ |
| Network Device | `{domain}_{mac}_{attribute}`      | Device MAC address |
| Protect Camera | `protect_camera_{id}_{attribute}` | Camera ID          |
| Protect Light  | `protect_light_{id}`              | Light ID           |
| Protect Sensor | `protect_sensor_{id}_{attribute}` | Sensor ID          |
| Protect Chime  | `protect_chime_{id}`              | Chime ID           |

**These patterns are library-agnostic** - they depend only on device identifiers, not API structure.

---

## Transformation Testing Strategy

### Unit Tests for Transformations

```python
def test_transform_network_device():
    """Test network device transformation."""
    lib_data = {
        "id": "test123",
        "mac": "AA:BB:CC:DD:EE:FF",
        "status": "online",
        "firmware_version": "6.5.55",
        "cpu_percent": 15.2,
    }

    result = transform_network_device(lib_data)

    assert result["id"] == "test123"
    assert result["mac"] == "AA:BB:CC:DD:EE:FF"
    assert result["state"] == "connected"  # Mapped
    assert result["version"] == "6.5.55"   # Renamed
    assert result["cpu_usage"] == 15.2     # Renamed

def test_transform_protect_camera():
    """Test Protect camera transformation."""
    lib_data = {
        "id": "cam123",
        "name": "Front Door",
        "status": "connected",
        "recording": True,
        "hdr": "auto",
    }

    result = transform_protect_camera(lib_data)

    assert result["id"] == "cam123"
    assert result["state"] == "CONNECTED"  # Uppercased
    assert result["is_recording"] == True  # Renamed
    assert result["hdr_mode"] == "AUTO"    # Uppercased
```

---

## Data Model Completion Checklist

- [ ] Network device transformation function complete
- [ ] Protect camera transformation function complete
- [ ] Protect light transformation function complete
- [ ] Protect sensor transformation function complete
- [ ] Protect chime transformation function complete
- [ ] WebSocket event transformation (if applicable)
- [ ] Unit tests for all transformations
- [ ] Coordinator integration updated
- [ ] Entity unique ID preservation verified

---

**Data Model Status**: 🟡 **TEMPLATE COMPLETE**
**Implementation Status**: ⏳ Awaiting library research completion
**Ready for Implementation**: ✅ Structure defined, pending library field verification

**Last Updated**: 2026-01-19
