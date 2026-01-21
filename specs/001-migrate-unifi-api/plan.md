# Implementation Plan: Migrate to unifi-official-api Library

**Branch**: `001-migrate-unifi-api` | **Date**: 2026-01-19 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-migrate-unifi-api/spec.md`

## Summary

Migrate the ha-unifi-insights Home Assistant integration from custom UniFi API clients to the official `unifi-official-api` library (version ~=1.0.0). This is an atomic migration that replaces all custom API code (unifi_network_api.py, unifi_protect_api.py) with library calls in a single release while maintaining 100% feature parity across all 8 entity platforms. The migration follows Home Assistant core integration patterns where the coordinator serves as the sole interface to the library, with comprehensive pre-release testing including automated tests, manual validation, and beta user testing.

## Technical Context

**Language/Version**: Python 3.11+ (Home Assistant 2025.9.0+ requirement)
**Primary Dependencies**:

- Home Assistant >= 2025.9.0
- unifi-official-api ~= 1.0.0 (new, to be added)
- aiohttp (HA-provided, async HTTP)
- async_timeout (HA-provided)

**Storage**: N/A (integration uses HA config entries, no direct database access)
**Testing**: pytest with asyncio support, pytest-cov for coverage (80%+ target)
**Target Platform**: Home Assistant OS, Container, Core installations
**Project Type**: Single project (Home Assistant custom integration)
**Performance Goals**:

- Coordinator update cycles <= 30s (maintain current performance)
- No increase in memory footprint
- WebSocket reconnection within 8-120s (exponential backoff)

**Constraints**:

- Must pass hassfest validation
- Zero user-facing breaking changes
- Entity unique IDs must remain unchanged (preserve history)
- Config entries must migrate transparently
- All 8 platforms must maintain feature parity

**Scale/Scope**:

- ~7,900 LOC current integration
- Remove ~2,441 LOC (custom API clients)
- Modify ~450 LOC (coordinator)
- Update all entity platforms for library compatibility
- 8 entity platforms: sensor, binary_sensor, camera, light, switch, select, number, button

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

### ✅ Principle I: Home Assistant First

- **Status**: PASS
- **Evidence**:
  - Integration follows HA coordinator pattern
  - Uses config flows (no YAML)
  - Has diagnostics support
  - Will maintain hassfest compliance post-migration
- **Action**: Verify hassfest passes with unifi-official-api dependency

### ✅ Principle II: External Library Dependency (NON-NEGOTIABLE)

- **Status**: PASS (this is the migration goal)
- **Evidence**:
  - Migration specifically adopts unifi-official-api library
  - Will remove all custom API client code
  - Library pinned as ~=1.0.0 in manifest.json
- **Action**: Core objective of this migration

### ✅ Principle III: API Abstraction Layer

- **Status**: PASS
- **Evidence**:
  - Coordinator already serves as abstraction layer
  - Entities never call API directly (go through coordinator)
  - Migration maintains this pattern with library
- **Action**: Update coordinator to wrap library instead of custom clients

### ✅ Principle IV: Test-First Development (NON-NEGOTIABLE)

- **Status**: PASS - Strict TDD will be enforced
- **Evidence**:
  - pytest.ini configured
  - Coverage target: 80%
  - Tasks structured to write tests BEFORE implementation (Red-Green-Refactor)
  - Test fixtures (T003-T004, T012) precede implementation
  - Test writing for each component happens before or alongside implementation
- **Action**: Follow TDD cycle strictly - write failing tests first, implement to pass, refactor
- **Enforcement**: Tasks.md restructured to ensure test-first approach for all new code

### ✅ Principle V: User-Centric Design

- **Status**: PASS
- **Evidence**:
  - Migration is internal only
  - No user-facing changes
  - Maintains all entity names, IDs, attributes
- **Action**: None (user experience unchanged)

### ✅ Principle VI: Defensive Reliability

- **Status**: PASS
- **Evidence**:
  - Current integration has robust error handling
  - Migration will translate library exceptions to HA errors
  - Graceful degradation patterns maintained
- **Action**: Map library exceptions to ConfigEntryAuthFailed/ConfigEntryNotReady

### ✅ Principle VII: Versioning & Release Discipline

- **Status**: PASS
- **Evidence**:
  - Version format follows YYYY.MM.PATCH
  - Migration requires version bump
  - Comprehensive testing before release
- **Action**: Update manifest.json version, create changelog

### ✅ Principle VIII: Code Quality & Maintainability

- **Status**: PASS
- **Evidence**:
  - Existing code uses type hints
  - Ruff/Pylint configured (ruff==0.13.0)
  - Migration reduces LOC by removing custom clients
- **Action**: Maintain code quality standards during migration

### Gate Status: ✅ **PASS**

All constitution principles satisfied. Principle IV (Test-First Development) compliance ensured through strict TDD task ordering in tasks.md - tests written before implementation for all new code.

## Project Structure

### Documentation (this feature)

```text
specs/001-migrate-unifi-api/
├── plan.md              # This file
├── research.md          # Phase 0: Library API mapping, migration strategy
├── data-model.md        # Phase 1: Entity data mappings (custom API → library)
├── quickstart.md        # Phase 1: Developer migration guide
├── contracts/           # Phase 1: Library API surface documentation
│   └── library-api.md   # unifi-official-api public interface
└── tasks.md             # Phase 2: Task breakdown (created by /speckit.tasks)
```

### Source Code (repository root)

```text
custom_components/unifi_insights/
├── __init__.py                 # Integration entry (174 lines) - Update imports
├── manifest.json               # Add unifi-official-api~=1.0.0 requirement
├── coordinator.py              # Coordinator (452 lines) - Replace API calls with library
├── config_flow.py              # Config flow (118 lines) - Update API validation
├── diagnostics.py              # Diagnostics (42 lines) - Add library version info
├── services.py                 # Services (1236 lines) - Route through library
├── entity.py                   # Base entities (292 lines) - Update device info extraction
├── const.py                    # Constants (299 lines) - May need API constant updates
│
├── sensor.py                   # (784 lines) - Update data extraction
├── binary_sensor.py            # (458 lines) - Update data extraction
├── camera.py                   # (165 lines) - Update snapshot/stream methods
├── light.py                    # (155 lines) - Update control methods
├── switch.py                   # (120 lines) - Update control methods
├── select.py                   # (440 lines) - Update control methods
├── number.py                   # (331 lines) - Update control methods
├── button.py                   # (434 lines) - Update action methods
│
├── unifi_network_api.py        # (601 lines) - DELETE after migration
├── unifi_protect_api.py        # (1840 lines) - DELETE after migration
└── translations/               # No changes needed

tests/                          # New directory structure
├── conftest.py                 # Fixtures for HA test harness + library mocks
├── test_config_flow.py         # Config flow with library validation
├── test_coordinator.py         # Coordinator with mocked library
├── test_binary_sensor.py       # Entity tests with mocked coordinator
├── test_sensor.py              # Entity tests with mocked coordinator
├── test_camera.py              # Camera entity tests
├── test_light.py               # Light entity tests
├── test_switch.py              # Switch entity tests
├── test_select.py              # Select entity tests
├── test_number.py              # Number entity tests
└── test_button.py              # Button entity tests
```

**Structure Decision**: This is a standard Home Assistant custom component integration (single project). All code lives in `custom_components/unifi_insights/`. Tests will be created in a `tests/` directory at the repository root following HA testing conventions. The migration modifies ~10 files, removes 2 files (custom API clients), and creates ~11 new test files.

## Complexity Tracking

> No constitution violations requiring justification. Migration satisfies all principles with test creation during implementation.

---

# Phase 0: Research & Discovery

## Research Objectives

1. **Library API Surface Analysis**
   - Document unifi-official-api 1.0.0 public API
   - Identify equivalent methods for all custom client calls
   - Determine any missing functionality requiring upstream contributions

2. **Data Structure Mapping**
   - Compare custom API response formats with library responses
   - Identify transformation logic needed in coordinator
   - Document any attribute name changes

3. **Exception Mapping**
   - Catalog library exception types
   - Map to Home Assistant error types (ConfigEntryAuthFailed, ConfigEntryNotReady)
   - Define exception handling strategy

4. **WebSocket Migration Strategy**
   - Determine if library supports WebSocket subscriptions
   - Plan fallback strategy if WebSocket unavailable in library
   - Assess impact on Protect real-time updates

5. **Testing Strategy**
   - Define mock strategy for library
   - Identify test data requirements
   - Plan integration test approach

## Research Tasks

### Task 1: Library API Documentation Review

**Goal**: Understand complete unifi-official-api 1.0.0 interface
**Method**: Review library source code, documentation, examples
**Output**: Comprehensive API reference in `contracts/library-api.md`

### Task 2: Custom API to Library Method Mapping

**Goal**: Create 1:1 mapping of all custom client methods to library equivalents
**Method**: Compare UnifiInsightsClient + UnifiProtectClient methods with library
**Output**: Migration matrix in `research.md`

**Known Custom Methods (Network API - 17 methods):**

- `async_validate_api_key()` → ?
- `async_get_sites()` → ?
- `async_get_devices(site_id)` → ?
- `async_get_device_info(site_id, device_id)` → ?
- `async_get_device_stats(site_id, device_id)` → ?
- `async_get_clients(site_id)` → ?
- `async_restart_device(site_id, device_id)` → ?
- `async_get_application_info()` → ?
- `async_power_cycle_port(site_id, device_id, port_idx)` → ?
- `async_authorize_guest(site_id, client_id, ...)` → ?
- `async_list_vouchers(site_id)` → ?
- `async_generate_voucher(site_id, ...)` → ?
- `async_delete_voucher(site_id, voucher_id)` → ?
- `async_delete_vouchers_by_filter(site_id, ...)` → ?

**Known Custom Methods (Protect API - 24+ methods):**

- `async_validate_api_key()` → ?
- `async_get_cameras()` → ?
- `async_get_lights()` → ?
- `async_get_sensors()` → ?
- `async_get_nvrs()` → ?
- `async_get_chimes()` → ?
- `async_get_viewers()` → ?
- `async_get_liveviews()` → ?
- `async_get_camera_snapshot(camera_id, high_quality)` → ?
- `async_get_camera_rtsps_stream(camera_id, qualities)` → ?
- `async_update_camera(camera_id, data)` → ?
- `async_update_light(light_id, data)` → ?
- `async_set_light_mode(light_id, mode)` → ?
- `async_set_light_level(light_id, level)` → ?
- `async_set_camera_recording_mode(camera_id, mode)` → ?
- `async_set_camera_hdr_mode(camera_id, mode)` → ?
- `async_set_camera_video_mode(camera_id, mode)` → ?
- `async_set_microphone_volume(camera_id, volume)` → ?
- `async_ptz_move(camera_id, preset_slot)` → ?
- `async_ptz_patrol_start(camera_id, patrol_slot)` → ?
- `async_ptz_patrol_stop(camera_id)` → ?
- `async_play_chime(chime_id)` → ?
- `async_set_chime_volume(chime_id, volume)` → ?
- `async_set_chime_ringtone(chime_id, ringtone_id)` → ?
- `async_start_websocket()` → ?
- `async_stop_websocket()` → ?
- `register_device_update_callback(callback)` → ?
- `register_event_update_callback(callback)` → ?

### Task 3: WebSocket Capability Assessment

**Goal**: Determine library WebSocket support and migration strategy
**Method**: Review library WebSocket implementation
**Output**: WebSocket migration plan in `research.md`

**Current Custom WebSocket Features:**

- Two separate WebSocket connections (devices + events)
- Heartbeat mechanism (30-45s interval)
- Exponential backoff with jitter (8-120s delays)
- Adaptive timeout calculation
- Duplicate message detection
- Message buffering during disconnections
- Stale connection detection (60s threshold)
- Connection state tracking (5 states)

**Decision Point**: If library doesn't support WebSockets, determine:

- Can we contribute WebSocket support upstream?
- Should we maintain hybrid approach (library for HTTP, custom for WebSocket)?
- What's the impact on real-time updates?

### Task 4: Exception Handling Strategy

**Goal**: Define exception translation layer
**Method**: Review library exception types, plan mapping
**Output**: Exception handling matrix in `research.md`

**Required Mappings:**

- Library auth exceptions → `ConfigEntryAuthFailed`
- Library connection exceptions → `ConfigEntryNotReady`
- Library API errors → log + entity unavailability
- Library timeout exceptions → retry with backoff

### Task 5: Testing Approach Definition

**Goal**: Plan test implementation strategy
**Method**: Review HA testing patterns, define mock approach
**Output**: Testing strategy section in `research.md`

**Test Categories:**

1. **Unit Tests** - Mock library at coordinator level
2. **Integration Tests** - Test coordinator with mocked library responses
3. **Config Flow Tests** - Test setup/reauth with library validation
4. **Entity Tests** - Test entity state/attributes with mocked coordinator

**Mock Strategy:**

- Create fixtures for library client objects
- Mock async library methods with sample responses
- Use pytest-asyncio for async test support
- Reuse existing device data patterns from custom clients

---

# Phase 1: Design & Contracts

## Phase 1 Outputs

1. **data-model.md** - Entity data structure mappings
2. **contracts/library-api.md** - Library API surface documentation
3. **quickstart.md** - Developer migration quick reference
4. **Updated agent context** - Technology stack additions

## Data Model Design

**File**: `data-model.md`

**Content Structure:**

1. **Coordinator Data Structure** - Current vs. post-migration
2. **Entity Attribute Mappings** - Custom API fields → Library fields
3. **Data Transformation Logic** - Required conversions
4. **WebSocket Event Structures** - If library supports WebSockets

**Key Mappings Required:**

### Network Device Entities

```
Custom API → Library
├── Device Status
│   ├── state: "connected" → ?
│   ├── adopted: true → ?
│   ├── cpu_usage: 15.2 → ?
│   ├── memory_usage: 42.8 → ?
│   ├── uptime: 86400 → ?
│   ├── tx_bytes: 1024000 → ?
│   └── rx_bytes: 2048000 → ?
├── Device Info
│   ├── mac: "AA:BB:CC:DD:EE:FF" → ?
│   ├── model: "USW-24-POE" → ?
│   ├── version: "6.5.55" → ?
│   └── site_id: "default" → ?
└── Device Controls
    ├── restart() → ?
    └── power_cycle_port() → ?
```

### Protect Device Entities

```
Custom API → Library
├── Camera
│   ├── state: "CONNECTED" → ?
│   ├── is_recording: true → ?
│   ├── motion_detected: false → ?
│   ├── snapshot_url → ?
│   ├── rtsps_url → ?
│   ├── hdr_mode: "AUTO" → ?
│   └── video_mode: "DEFAULT" → ?
├── Light
│   ├── is_on: true → ?
│   ├── brightness: 80 → ?
│   ├── mode: "MOTION" → ?
│   └── is_dark: false → ?
├── Sensor
│   ├── temperature: 22.5 → ?
│   ├── humidity: 45 → ?
│   ├── light_level: 750 → ?
│   └── battery_percentage: 85 → ?
└── Chime
    ├── volume: 60 → ?
    ├── repeat_times: 2 → ?
    └── ringtone_id: "DEFAULT" → ?
```

## API Contracts

**File**: `contracts/library-api.md`

**Content**: Complete unifi-official-api 1.0.0 interface documentation including:

- Class structure
- Method signatures
- Parameter types
- Return types
- Exception types
- Usage examples

## Developer Quickstart

**File**: `quickstart.md`

**Content**: Step-by-step migration reference for developers including:

1. **Setup**: Install unifi-official-api library
2. **Import Changes**: Update import statements
3. **Client Initialization**: Library client setup
4. **Method Calls**: Common patterns (before → after)
5. **Exception Handling**: Error handling updates
6. **Testing**: Running tests with mocked library
7. **Debugging**: Common issues and solutions

---

# Phase 2: Implementation Tasks

**Note**: Task generation is handled by `/speckit.tasks` command (not created during `/speckit.plan`).

**Expected Task Categories:**

1. **Setup Tasks** (3-5 tasks)
   - Add library dependency to manifest.json
   - Update requirements.txt
   - Configure test infrastructure

2. **Coordinator Migration** (8-12 tasks)
   - Replace custom client initialization with library
   - Update \_async_update_data() method
   - Migrate WebSocket handling (if supported)
   - Update exception handling
   - Add library diagnostics

3. **Entity Platform Updates** (16-24 tasks, 2-3 per platform)
   - Update data extraction for each platform
   - Verify attribute mappings
   - Test entity state updates

4. **Service Migration** (10-15 tasks)
   - Update each service to call library methods
   - Verify parameter passing
   - Test service execution

5. **Test Implementation** (15-20 tasks)
   - Create test fixtures
   - Write coordinator tests
   - Write config flow tests
   - Write entity tests for each platform

6. **Cleanup** (3-5 tasks)
   - Remove unifi_network_api.py
   - Remove unifi_protect_api.py
   - Remove unused imports
   - Update documentation

7. **Validation** (5-8 tasks)
   - Run hassfest validation
   - Verify code coverage >= 80%
   - Manual testing against real controller
   - Beta user testing coordination

---

# Risk Assessment

## High-Risk Areas

1. **WebSocket Migration**
   - **Risk**: Library may not support WebSocket subscriptions
   - **Impact**: Loss of real-time Protect updates
   - **Mitigation**: Assess early in research phase, contribute upstream if needed

2. **Data Structure Mismatches**
   - **Risk**: Library response formats differ from custom API
   - **Impact**: Entity attributes change, breaking automations
   - **Mitigation**: Comprehensive data-model.md mapping, transformation layer in coordinator

3. **Missing Library Methods**
   - **Risk**: Library doesn't expose all required API endpoints
   - **Impact**: Feature loss (vouchers, PTZ, chimes)
   - **Mitigation**: Identify gaps early, contribute upstream or document workarounds

4. **Test Coverage Gaps**
   - **Risk**: Tests not comprehensive enough to catch regressions
   - **Impact**: Bugs reach production
   - **Mitigation**: Beta testing, manual validation, 80%+ coverage requirement

## Medium-Risk Areas

1. **Performance Regression**
   - **Risk**: Library introduces latency or memory overhead
   - **Impact**: Slower updates, higher resource usage
   - **Mitigation**: Benchmark before/after, profile library calls

2. **Exception Handling Changes**
   - **Risk**: Library exceptions not properly translated
   - **Impact**: Integration crashes or fails to reload
   - **Mitigation**: Comprehensive exception mapping, defensive coding

3. **Config Entry Migration**
   - **Risk**: Existing installations fail to migrate
   - **Impact**: Users forced to reconfigure
   - **Mitigation**: Test upgrade path, preserve config structure

## Low-Risk Areas

1. **Entity ID Preservation**
   - **Risk**: Entity unique IDs change
   - **Impact**: History loss
   - **Mitigation**: IDs based on device MAC/ID (library agnostic)

2. **SSDP Discovery**
   - **Risk**: Discovery breaks with library
   - **Impact**: Auto-discovery fails
   - **Mitigation**: Discovery independent of API client

---

# Success Metrics

## Pre-Release Validation

- ✅ All hassfest checks pass
- ✅ Code coverage >= 80%
- ✅ All automated tests pass
- ✅ Manual testing shows zero regressions
- ✅ Beta testers report no critical issues
- ✅ Custom API client files removed
- ✅ Library version in diagnostics

## Post-Release Monitoring

- Zero increase in error logs (first 48 hours)
- No support tickets related to migration (first week)
- Performance metrics match pre-migration baseline
- Entity histories preserved for existing installations

---

# Timeline Estimate

**Note**: Timelines provided for planning purposes only, not guarantees.

- **Phase 0 (Research)**: 3-5 days
- **Phase 1 (Design)**: 2-3 days
- **Phase 2 (Implementation)**: 10-15 days
- **Testing & Validation**: 5-7 days
- **Beta Testing**: 7-14 days
- **Release Preparation**: 1-2 days

**Total**: 28-46 days (4-7 weeks)

---

**End of Implementation Plan**

Next steps:

1. Execute Phase 0 research (create research.md)
2. Execute Phase 1 design (create data-model.md, contracts/, quickstart.md)
3. Update agent context with unifi-official-api library
4. Proceed to `/speckit.tasks` for task generation
