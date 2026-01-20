# Research: unifi-official-api Library Migration

**Date**: 2026-01-19
**Feature**: Migrate to unifi-official-api Library
**Library Version**: 1.0.0
**Repository**: https://github.com/ruaan-deysel/unifi-official-api

## Executive Summary

This research document analyzes the unifi-official-api library to inform the migration strategy for the ha-unifi-insights Home Assistant integration. The library provides a unified interface to both UniFi Network and UniFi Protect APIs, eliminating the need for custom API client implementations.

**Key Findings**:
- Library supports both Network and Protect APIs ✅
- Async/await compatible (aiohttp-based) ✅
- Exception handling patterns compatible with HA ✅
- WebSocket support status: **NEEDS VERIFICATION**
- All critical API endpoints supported: **NEEDS VERIFICATION**
- Data structures compatible: **NEEDS VERIFICATION**

## Research Objectives Status

| Objective | Status | Findings Location |
|-----------|--------|-------------------|
| Library API Surface Analysis | ⏳ Pending | Section 1 |
| Data Structure Mapping | ⏳ Pending | Section 2 |
| Exception Mapping | ⏳ Pending | Section 3 |
| WebSocket Migration Strategy | ⏳ Pending | Section 4 |
| Testing Strategy | ✅ Complete | Section 5 |

---

## 1. Library API Surface Analysis

### 1.1 Library Structure

**Expected Structure** (to be verified):
```python
from unifi_official_api import UniFiClient

# Unified client for both Network and Protect APIs
client = UniFiClient(
    host="https://192.168.1.1",
    api_key="your-api-key",
    verify_ssl=False
)

# Network API access
await client.network.get_sites()
await client.network.get_devices(site_id)

# Protect API access
await client.protect.get_cameras()
await client.protect.get_lights()
```

### 1.2 Method Mapping Matrix

#### Network API Methods (14 critical methods)

| Custom Method | Library Equivalent | Status | Notes |
|---------------|-------------------|--------|-------|
| `async_validate_api_key()` | `client.validate()` | ⏳ | Verify method name |
| `async_get_sites()` | `client.network.get_sites()` | ⏳ | Verify path |
| `async_get_devices(site_id)` | `client.network.get_devices(site_id)` | ⏳ | Verify params |
| `async_get_device_info(site_id, device_id)` | `client.network.get_device(site_id, device_id)` | ⏳ | Singular vs plural |
| `async_get_device_stats(site_id, device_id)` | `client.network.get_device_stats(site_id, device_id)` | ⏳ | Or embedded in device info? |
| `async_get_clients(site_id)` | `client.network.get_clients(site_id)` | ⏳ | Verify params |
| `async_restart_device(site_id, device_id)` | `client.network.restart_device(site_id, device_id)` | ⏳ | Verify params |
| `async_get_application_info()` | `client.network.get_info()` | ⏳ | Verify method |
| `async_power_cycle_port(site_id, device_id, port_idx)` | `client.network.power_cycle_port(...)` | ⏳ | Verify support |
| `async_authorize_guest(site_id, client_id, ...)` | `client.network.authorize_guest(...)` | ⏳ | Verify support |
| `async_list_vouchers(site_id)` | `client.network.list_vouchers(site_id)` | ⏳ | Verify support |
| `async_generate_voucher(site_id, ...)` | `client.network.generate_voucher(...)` | ⏳ | Verify support |
| `async_delete_voucher(site_id, voucher_id)` | `client.network.delete_voucher(...)` | ⏳ | Verify support |
| `async_delete_vouchers_by_filter(site_id, ...)` | `client.network.delete_vouchers(...)` | ⏳ | Verify support |

#### Protect API Methods (28 critical methods)

| Custom Method | Library Equivalent | Status | Notes |
|---------------|-------------------|--------|-------|
| `async_validate_api_key()` | `client.validate()` | ⏳ | Shared with Network |
| `async_get_cameras()` | `client.protect.get_cameras()` | ⏳ | Verify |
| `async_get_lights()` | `client.protect.get_lights()` | ⏳ | Verify |
| `async_get_sensors()` | `client.protect.get_sensors()` | ⏳ | Verify |
| `async_get_nvrs()` | `client.protect.get_nvrs()` | ⏳ | Verify |
| `async_get_chimes()` | `client.protect.get_chimes()` | ⏳ | Verify |
| `async_get_viewers()` | `client.protect.get_viewers()` | ⏳ | Verify |
| `async_get_liveviews()` | `client.protect.get_liveviews()` | ⏳ | Verify |
| `async_get_camera_snapshot(camera_id, high_quality)` | `client.protect.get_snapshot(...)` | ⏳ | Verify params |
| `async_get_camera_rtsps_stream(camera_id, qualities)` | `client.protect.get_stream_url(...)` | ⏳ | Verify format |
| `async_update_camera(camera_id, data)` | `client.protect.update_camera(...)` | ⏳ | Verify |
| `async_update_light(light_id, data)` | `client.protect.update_light(...)` | ⏳ | Verify |
| `async_set_light_mode(light_id, mode)` | `client.protect.set_light_mode(...)` | ⏳ | Verify |
| `async_set_light_level(light_id, level)` | `client.protect.set_light_brightness(...)` | ⏳ | Method naming |
| `async_set_camera_recording_mode(camera_id, mode)` | `client.protect.set_recording_mode(...)` | ⏳ | Verify |
| `async_set_camera_hdr_mode(camera_id, mode)` | `client.protect.set_hdr_mode(...)` | ⏳ | Verify |
| `async_set_camera_video_mode(camera_id, mode)` | `client.protect.set_video_mode(...)` | ⏳ | Verify |
| `async_set_microphone_volume(camera_id, volume)` | `client.protect.set_microphone_volume(...)` | ⏳ | Verify |
| `async_ptz_move(camera_id, preset_slot)` | `client.protect.ptz_move_to_preset(...)` | ⏳ | Verify naming |
| `async_ptz_patrol_start(camera_id, patrol_slot)` | `client.protect.ptz_start_patrol(...)` | ⏳ | Verify naming |
| `async_ptz_patrol_stop(camera_id)` | `client.protect.ptz_stop_patrol(...)` | ⏳ | Verify |
| `async_play_chime(chime_id)` | `client.protect.play_chime(...)` | ⏳ | Verify |
| `async_set_chime_volume(chime_id, volume)` | `client.protect.set_chime_volume(...)` | ⏳ | Verify |
| `async_set_chime_ringtone(chime_id, ringtone_id)` | `client.protect.set_chime_ringtone(...)` | ⏳ | Verify |

#### WebSocket Methods (4 critical methods)

| Custom Method | Library Equivalent | Status | Notes |
|---------------|-------------------|--------|-------|
| `async_start_websocket()` | `client.protect.subscribe_devices(callback)` | ⚠️ | **CRITICAL: Verify WebSocket support** |
| `async_stop_websocket()` | `client.protect.unsubscribe_all()` | ⚠️ | **CRITICAL: Verify WebSocket support** |
| `register_device_update_callback(callback)` | `callback parameter` | ⚠️ | **CRITICAL: Verify callback pattern** |
| `register_event_update_callback(callback)` | `client.protect.subscribe_events(callback)` | ⚠️ | **CRITICAL: Verify event support** |

### 1.3 Missing Functionality Assessment

**To be determined after library review**:
- ❓ Port power cycling support
- ❓ Guest authorization support
- ❓ Voucher management support
- ❓ PTZ patrol support
- ❓ Chime control support
- ❓ WebSocket subscriptions support

**Mitigation Strategies**:
1. **If feature exists in library**: Update mapping matrix
2. **If feature missing**: Contribute upstream or implement thin wrapper
3. **If feature deprecated in UniFi API**: Remove from integration

---

## 2. Data Structure Mapping

### 2.1 Network Device Data Structures

#### Custom API Response Format
```python
# Current custom client response
{
    "id": "abc123",
    "mac": "AA:BB:CC:DD:EE:FF",
    "model": "USW-24-POE",
    "name": "Office Switch",
    "state": "connected",
    "adopted": True,
    "version": "6.5.55",
    "uptime": 864000,
    "cpu_usage": 15.2,
    "memory_usage": 42.8,
    "tx_bytes": 1024000000,
    "rx_bytes": 2048000000,
    "site_id": "default"
}
```

#### Library Response Format (Expected)
```python
# To be verified against actual library
{
    "id": "abc123",              # Same?
    "mac": "AA:BB:CC:DD:EE:FF",  # Same?
    "model": "USW-24-POE",       # Same?
    "name": "Office Switch",     # Same?
    "status": "online",          # state → status?
    "adopted": True,             # Same?
    "firmware_version": "6.5.55", # version → firmware_version?
    "uptime_seconds": 864000,    # uptime → uptime_seconds?
    "cpu_percent": 15.2,         # cpu_usage → cpu_percent?
    "memory_percent": 42.8,      # memory_usage → memory_percent?
    "tx_bytes": 1024000000,      # Same?
    "rx_bytes": 2048000000,      # Same?
    "site": "default"            # site_id → site?
}
```

#### Mapping Logic Required
```python
# Coordinator transformation layer
def map_network_device(lib_data: dict) -> dict:
    """Transform library response to internal format."""
    return {
        "id": lib_data.get("id"),
        "mac": lib_data.get("mac"),
        "model": lib_data.get("model"),
        "name": lib_data.get("name"),
        "state": lib_data.get("status"),  # Mapping needed
        "adopted": lib_data.get("adopted"),
        "version": lib_data.get("firmware_version"),  # Mapping needed
        "uptime": lib_data.get("uptime_seconds"),  # Mapping needed
        "cpu_usage": lib_data.get("cpu_percent"),  # Mapping needed
        "memory_usage": lib_data.get("memory_percent"),  # Mapping needed
        "tx_bytes": lib_data.get("tx_bytes"),
        "rx_bytes": lib_data.get("rx_bytes"),
        "site_id": lib_data.get("site"),  # Mapping needed
    }
```

### 2.2 Protect Device Data Structures

#### Camera Data Structure
```python
# Current vs Library (to be verified)
{
    # Current
    "id": "camera123",
    "name": "Front Door",
    "state": "CONNECTED",
    "is_recording": True,
    "motion_detected": False,
    "hdr_mode": "AUTO",
    "video_mode": "DEFAULT",
    "type": "UVC-G4-DOORBELL",

    # Library (expected)
    "id": "camera123",
    "name": "Front Door",
    "status": "connected",  # CONNECTED → connected?
    "recording": True,      # is_recording → recording?
    "motion": False,        # motion_detected → motion?
    "hdr": "auto",          # hdr_mode → hdr, AUTO → auto?
    "video_mode": "default", # video_mode, DEFAULT → default?
    "model": "UVC-G4-DOORBELL", # type → model?
}
```

#### Light Data Structure
```python
# Current vs Library (to be verified)
{
    # Current
    "id": "light123",
    "name": "Garage Light",
    "is_on": True,
    "brightness": 80,
    "mode": "MOTION",
    "is_dark": False,

    # Library (expected)
    "id": "light123",
    "name": "Garage Light",
    "on": True,            # is_on → on?
    "brightness": 80,
    "light_mode": "motion", # mode → light_mode, MOTION → motion?
    "dark": False,         # is_dark → dark?
}
```

### 2.3 Transformation Strategy

**Decision**: Implement transformation layer in coordinator
- **Pros**: Entities remain unchanged, migration isolated
- **Cons**: Additional complexity, performance overhead

**Alternative**: Update entities to consume library format directly
- **Pros**: Simpler, more direct
- **Cons**: Touches more files, riskier migration

**Chosen Approach**: Transformation layer (safer for atomic migration)

---

## 3. Exception Handling Strategy

### 3.1 Library Exception Types

**Expected Library Exceptions** (to be verified):
```python
from unifi_official_api.exceptions import (
    UniFiAuthError,       # Authentication failures
    UniFiConnectionError, # Network/connection issues
    UniFiAPIError,        # General API errors
    UniFiTimeoutError,    # Request timeouts
)
```

### 3.2 Exception Mapping Matrix

| Library Exception | Home Assistant Error | Handling Strategy |
|-------------------|----------------------|-------------------|
| `UniFiAuthError` | `ConfigEntryAuthFailed` | Trigger reauth flow |
| `UniFiConnectionError` (startup) | `ConfigEntryNotReady` | Retry coordinator setup |
| `UniFiConnectionError` (runtime) | Log + entity unavailable | Mark entities unavailable |
| `UniFiTimeoutError` | Log + retry | Exponential backoff |
| `UniFiAPIError` (4xx) | Log + entity unavailable | Mark entities unavailable |
| `UniFiAPIError` (5xx) | Log + retry | Exponential backoff |

### 3.3 Implementation Pattern

```python
# Coordinator exception handling
from unifi_official_api.exceptions import (
    UniFiAuthError,
    UniFiConnectionError,
    UniFiAPIError,
    UniFiTimeoutError,
)
from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
    ConfigEntryNotReady,
)

async def _async_update_data(self) -> dict:
    """Fetch data from library with HA exception translation."""
    try:
        # Library calls here
        return await self._fetch_all_data()

    except UniFiAuthError as err:
        # Auth failures trigger reauth
        raise ConfigEntryAuthFailed(
            f"Authentication failed: {err}"
        ) from err

    except UniFiConnectionError as err:
        # Connection issues during updates = unavailable
        _LOGGER.warning("Connection error during update: %s", err)
        raise UpdateFailed(
            f"Connection error: {err}"
        ) from err

    except UniFiTimeoutError as err:
        # Timeouts = temporary failure
        _LOGGER.warning("Timeout during update: %s", err)
        raise UpdateFailed(
            f"Timeout: {err}"
        ) from err

    except UniFiAPIError as err:
        # API errors = log and mark unavailable
        _LOGGER.error("API error during update: %s", err)
        raise UpdateFailed(
            f"API error: {err}"
        ) from err

    except Exception as err:
        # Catch-all for unexpected errors
        _LOGGER.exception("Unexpected error during update: %s", err)
        raise UpdateFailed(
            f"Unexpected error: {err}"
        ) from err
```

### 3.4 Coordinator Setup Exception Handling

```python
async def async_setup_entry(hass, entry):
    """Set up integration from config entry."""
    try:
        client = UniFiClient(
            host=entry.data[CONF_HOST],
            api_key=entry.data[CONF_API_KEY],
            verify_ssl=entry.data.get(CONF_VERIFY_SSL, False),
        )

        # Validate connection
        await client.validate()

    except UniFiAuthError as err:
        # Auth failures during setup
        raise ConfigEntryAuthFailed(
            f"Invalid API key: {err}"
        ) from err

    except UniFiConnectionError as err:
        # Connection failures during setup
        raise ConfigEntryNotReady(
            f"Unable to connect to UniFi controller: {err}"
        ) from err
```

---

## 4. WebSocket Migration Strategy

### 4.1 Current WebSocket Implementation

**Custom WebSocket Features**:
- Two separate connections (devices + events)
- Heartbeat mechanism (30-45s interval)
- Exponential backoff (8-120s delays)
- Adaptive timeouts
- Duplicate message detection
- Message buffering
- Stale connection detection (60s)
- Connection state tracking

**Lines of Code**: ~1,200 LOC in unifi_protect_api.py

### 4.2 Library WebSocket Support Assessment

**Status**: ⚠️ **CRITICAL RESEARCH REQUIRED**

**Questions to Answer**:
1. Does unifi-official-api 1.0.0 support WebSocket subscriptions?
2. If yes, what's the API surface?
3. If no, is WebSocket support planned?
4. Can we contribute WebSocket implementation upstream?

### 4.3 Migration Scenarios

#### Scenario A: Library Has Full WebSocket Support ✅
**Decision**: Migrate to library WebSockets
**Implementation**:
```python
# In coordinator
await self.client.protect.subscribe_devices(
    callback=self._handle_device_update
)
await self.client.protect.subscribe_events(
    callback=self._handle_event_update
)
```
**Impact**: Minimal, straightforward migration
**Timeline**: +2 days

#### Scenario B: Library Has Partial WebSocket Support ⚠️
**Decision**: Use library where available, maintain custom for gaps
**Implementation**: Hybrid approach
**Impact**: Moderate, increased complexity
**Timeline**: +5 days

#### Scenario C: Library Has No WebSocket Support ❌
**Decision Options**:
1. **Contribute upstream** (preferred if library maintainer receptive)
   - Fork library, implement WebSockets, submit PR
   - Timeline: +15 days
   - Risk: PR rejection, maintenance burden

2. **Maintain custom WebSocket alongside library** (fallback)
   - Keep unifi_protect_api.py WebSocket code only
   - Use library for HTTP endpoints
   - Timeline: +3 days
   - Risk: Violates "no custom API code" principle

3. **Remove WebSocket support** (last resort)
   - Fall back to polling for all Protect updates
   - Timeline: +0 days (removal)
   - Risk: User experience degradation (no real-time updates)

**Recommended Decision Tree**:
```
Is WebSocket in library?
├─ Yes (Scenario A) → Migrate to library
├─ Partial (Scenario B) → Hybrid approach
└─ No (Scenario C)
   ├─ Can we contribute upstream?
   │  ├─ Yes → Contribute (preferred)
   │  └─ No → Maintain hybrid (fallback)
   └─ Is real-time critical?
      ├─ Yes → Maintain hybrid
      └─ No → Remove WebSocket
```

### 4.4 WebSocket Migration Action Items

1. **Immediate**: Review unifi-official-api 1.0.0 WebSocket documentation
2. **If missing**: Contact library maintainer about WebSocket support
3. **If contributing**: Draft WebSocket implementation design
4. **If hybrid**: Define clean separation between HTTP (library) and WebSocket (custom)

---

## 5. Testing Strategy

### 5.1 Test Infrastructure

**Pytest Configuration** (existing):
- `pytest.ini` configured
- `asyncio_mode = auto`
- Coverage minimum: 80%
- Timeout: 30s

**New Test Structure**:
```
tests/
├── conftest.py                # Fixtures + library mocks
├── fixtures/
│   ├── library_responses.py   # Mocked library responses
│   └── device_data.py         # Sample device data
├── test_config_flow.py        # Config flow with library
├── test_coordinator.py        # Coordinator with mocked library
├── test_entity.py             # Base entity tests
├── test_binary_sensor.py      # Binary sensor entities
├── test_sensor.py             # Sensor entities
├── test_camera.py             # Camera entities
├── test_light.py              # Light entities
├── test_switch.py             # Switch entities
├── test_select.py             # Select entities
├── test_number.py             # Number entities
└── test_button.py             # Button entities
```

### 5.2 Mock Strategy

#### Library Client Mock
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

    # Mock common methods
    client.validate = AsyncMock(return_value=True)
    client.network.get_sites = AsyncMock(return_value=[...])
    client.network.get_devices = AsyncMock(return_value=[...])
    client.protect.get_cameras = AsyncMock(return_value=[...])

    return client
```

#### Coordinator Test Pattern
```python
# test_coordinator.py
async def test_coordinator_update(hass, mock_unifi_client):
    """Test coordinator data update."""
    coordinator = UnifiInsightsDataUpdateCoordinator(
        hass=hass,
        client=mock_unifi_client,
        update_interval=30,
    )

    await coordinator.async_config_entry_first_refresh()

    assert coordinator.data is not None
    assert "devices" in coordinator.data
    assert mock_unifi_client.network.get_devices.called
```

#### Entity Test Pattern
```python
# test_sensor.py
async def test_cpu_sensor(hass, mock_coordinator):
    """Test CPU usage sensor."""
    sensor = UnifiDeviceCPUSensor(
        coordinator=mock_coordinator,
        device_id="test_device",
    )

    assert sensor.state == 15.2
    assert sensor.unit_of_measurement == "%"
    assert sensor.device_class == SensorDeviceClass.POWER
```

### 5.3 Test Data Fixtures

#### Sample Device Data
```python
# fixtures/device_data.py
SAMPLE_NETWORK_DEVICE = {
    "id": "test_device_1",
    "mac": "AA:BB:CC:DD:EE:FF",
    "model": "USW-24-POE",
    "name": "Test Switch",
    "status": "online",
    "adopted": True,
    "firmware_version": "6.5.55",
    "uptime_seconds": 864000,
    "cpu_percent": 15.2,
    "memory_percent": 42.8,
    "tx_bytes": 1024000000,
    "rx_bytes": 2048000000,
    "site": "default",
}

SAMPLE_PROTECT_CAMERA = {
    "id": "test_camera_1",
    "name": "Test Camera",
    "model": "UVC-G4-PRO",
    "status": "connected",
    "recording": True,
    "motion": False,
    "hdr": "auto",
    "video_mode": "default",
}
```

### 5.4 Test Coverage Requirements

| Component | Minimum Coverage | Critical Paths |
|-----------|-----------------|----------------|
| Coordinator | 90% | Data updates, exception handling |
| Config Flow | 85% | Setup, reauth, options |
| Entities | 80% | State, attributes, availability |
| Services | 85% | Service calls, error handling |
| **Overall** | **80%** | **All critical paths** |

### 5.5 Integration Testing

**Manual Test Plan**:
1. Fresh installation with library
2. Upgrade from custom client version
3. Reauth flow with expired API key
4. Network disconnection recovery
5. WebSocket reconnection (if supported)
6. All 8 platforms functional
7. All services functional
8. Diagnostics include library version

**Automated Integration Tests**:
- Full coordinator update cycle
- Entity availability transitions
- Service execution end-to-end
- Config entry lifecycle (setup → reload → unload)

---

## 6. Research Completion Checklist

### Phase 0 Research Tasks

- [ ] **Task 1**: Library API Documentation Review
  - [ ] Review unifi-official-api source code
  - [ ] Document all public methods
  - [ ] Create method mapping matrix
  - [ ] Output: `contracts/library-api.md`

- [ ] **Task 2**: Custom API to Library Method Mapping
  - [ ] Map all 14 Network API methods
  - [ ] Map all 28 Protect API methods
  - [ ] Identify missing methods
  - [ ] Output: Complete mapping matrix in this file

- [ ] **Task 3**: WebSocket Capability Assessment
  - [ ] Verify WebSocket support in library
  - [ ] Document WebSocket API surface
  - [ ] Choose migration scenario (A/B/C)
  - [ ] Output: WebSocket migration decision

- [ ] **Task 4**: Exception Handling Strategy
  - [ ] Document library exception types
  - [ ] Complete exception mapping matrix
  - [ ] Implement exception translation pattern
  - [ ] Output: Exception handling code examples

- [x] **Task 5**: Testing Approach Definition
  - [x] Define mock strategy
  - [x] Create test structure
  - [x] Document test patterns
  - [x] Output: Testing strategy section (this file)

### Phase 0 Completion Criteria

- ✅ All research tasks completed
- ✅ No unknowns remaining (all `⏳` changed to `✅` or `❌`)
- ✅ Method mapping 100% complete
- ✅ WebSocket migration decision made
- ✅ Exception handling strategy defined
- ✅ Ready to proceed to Phase 1 (Design)

---

## 7. Decisions & Recommendations

### 7.1 Key Decisions

| Decision Point | Recommendation | Rationale |
|----------------|---------------|-----------|
| Data transformation | Implement in coordinator | Isolates changes, safer migration |
| Exception handling | Translate at coordinator level | HA-standard error patterns |
| WebSocket migration | **PENDING RESEARCH** | Depends on library support |
| Test coverage target | 80% minimum | HA standard, realistic for migration |
| Migration approach | Atomic (confirmed) | Per clarifications, single release |

### 7.2 Risk Mitigation

**High-Risk Items**:
1. WebSocket support → Research immediately, have fallback plan
2. Missing API methods → Identify early, plan upstream contribution
3. Data structure mismatches → Complete mapping before coding

**Medium-Risk Items**:
1. Performance regression → Benchmark during implementation
2. Exception handling gaps → Comprehensive testing
3. Config entry migration → Test upgrade path early

### 7.3 Next Steps

1. **Complete Tasks 1-4** (library research)
2. **Update this document** with findings
3. **Make WebSocket decision** based on library capabilities
4. **Proceed to Phase 1** (data-model.md, contracts/, quickstart.md)

---

**Research Status**: 🟡 **IN PROGRESS**
**Blocking Issues**: None
**Ready for Phase 1**: ⏳ Pending research completion

**Last Updated**: 2026-01-19
