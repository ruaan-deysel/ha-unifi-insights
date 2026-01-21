# Feature Specification: Migrate to unifi-official-api Library

**Feature Branch**: `001-migrate-unifi-api`
**Created**: 2026-01-19
**Status**: Draft
**Input**: User description: "Migrate the ha-unifi-insights integration to fully use the official python library unifi-official-api 1.0.0, https://github.com/ruaan-deysel/unifi-official-api and remove all other code that we dont need anymore. By using the python library it fully supports home assistant best practises. The migration must also adhere to the same integration code patterns that are using in the ha core for home assistant."

## Clarifications

### Session 2026-01-19

- Q: Migration strategy for transitioning from custom API to library → A: Single atomic migration - Replace all custom API code with library in one release
- Q: Pre-release testing scope for atomic migration → A: Automated + manual - All automated tests pass plus manual validation against real UniFi controller and beta testing with selected users
- Q: Library version compatibility strategy → A: Pin minor version - Allow patch updates with unifi-official-api~=1.0.0 (permits 1.0.x but not 1.1.0)
- Q: Diagnostic information detail for library troubleshooting → A: Standard - Include library version, redacted connection info, and sanitized error messages from library

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Seamless Existing Functionality (Priority: P1)

Users who have already configured the UniFi Insights integration continue to use it without any disruption. All existing entities (sensors, binary sensors, switches, cameras, lights, buttons, selects, numbers) continue to work exactly as before with the same data, attributes, and capabilities.

**Why this priority**: This is the foundation of the migration. Users must not experience any breaking changes or loss of functionality. The migration is internal only - external behavior remains identical.

**Independent Test**: Can be fully tested by upgrading an existing installation and verifying that all entities maintain their state, attributes, and responsiveness exactly as before the migration.

**Acceptance Scenarios**:

1. **Given** an existing installation with configured sites and devices, **When** the integration is upgraded to use unifi-official-api, **Then** all sensors continue to report the same metrics (CPU, memory, uptime, TX/RX rates) with the same update frequency
2. **Given** configured binary sensors showing device online/offline status, **When** the migration is complete, **Then** device status continues to reflect actual device state accurately
3. **Given** configured switches for device restart, **When** a user triggers a device restart after migration, **Then** the device restarts successfully and the switch reflects the correct state
4. **Given** configured cameras, lights, buttons, selects, and numbers, **When** the migration completes, **Then** all platform-specific entities continue to function with their original capabilities

---

### User Story 2 - Improved Reliability and Maintainability (Priority: P2)

Users benefit from improved integration reliability through the use of a well-tested, dedicated library that handles UniFi API communication. The integration becomes more stable with better error handling, connection management, and resilience to API changes.

**Why this priority**: While users won't directly "see" this improvement, it provides long-term value through fewer bugs, faster fixes (handled upstream in the library), and better adherence to Home Assistant best practices.

**Independent Test**: Can be tested by monitoring error logs, connection stability over extended periods, and observing that API-related issues are handled gracefully with appropriate user feedback.

**Acceptance Scenarios**:

1. **Given** intermittent network connectivity to the UniFi controller, **When** connection issues occur, **Then** the integration gracefully handles errors without crashing and provides clear status in entity availability
2. **Given** API rate limiting from the UniFi controller, **When** rapid requests are made, **Then** the library handles backoff and retry logic transparently
3. **Given** future UniFi API changes, **When** the upstream library is updated, **Then** the integration benefits from fixes without requiring integration-specific code changes

---

### User Story 3 - Standards-Compliant Architecture (Priority: P3)

The integration follows Home Assistant core patterns for external library usage, making it easier for contributors to understand, maintain, and extend the codebase. The code structure aligns with official HA integration guidelines.

**Why this priority**: This is primarily for maintainers and contributors. While it doesn't change user-facing functionality, it makes the codebase more sustainable and easier to enhance in the future.

**Independent Test**: Can be tested by reviewing the code structure against Home Assistant integration quality scale and verifying compliance with official patterns (coordinator wraps library, entities never call library directly, proper error handling, etc.).

**Acceptance Scenarios**:

1. **Given** the migrated codebase, **When** reviewed against HA integration patterns, **Then** the coordinator is the sole interface to unifi-official-api
2. **Given** the entity implementations, **When** examined, **Then** all entities consume data through the coordinator without direct library calls
3. **Given** the codebase structure, **When** compared to HA core integrations, **Then** it follows the same architectural patterns for external library usage

---

### Edge Cases

- What happens when the unifi-official-api library version on the system is incompatible with the integration requirements (~=1.0.0)?
- What happens if a patch version (e.g., 1.0.5) introduces a regression or breaking change despite semantic versioning?
- How does the system handle cases where the library is not installed or fails to import?
- What happens if the library's API surface changes in a backward-incompatible way in future versions?
- How are deprecated custom API methods that don't exist in the library handled during migration?
- What happens to existing config entries during the migration?
- How are data structure differences between custom API and library API handled?
- What happens if critical issues are discovered after the atomic migration release is deployed to users?
- What happens if beta testers discover issues during pre-release validation?
- How does the system handle diagnostic data collection if the library fails to initialize or import?

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: Integration MUST replace all calls to custom UniFi API clients (UnifiInsightsClient, UnifiProtectClient) with equivalent calls to unifi-official-api library
- **FR-002**: Integration MUST maintain 100% feature parity with current functionality across all platforms (sensor, binary_sensor, button, camera, light, switch, select, number)
- **FR-003**: Integration MUST specify unifi-official-api~=1.0.0 as a dependency in manifest.json requirements array (allows patch updates 1.0.x but prevents breaking changes from 1.1.0+)
- **FR-004**: Coordinator MUST be the sole interface between unifi-official-api library and Home Assistant entities
- **FR-005**: Entities MUST NOT directly import or call unifi-official-api library; all data MUST flow through coordinator
- **FR-006**: Integration MUST remove custom API client files (unifi_network_api.py, unifi_protect_api.py) in the same release as the library integration (atomic migration)
- **FR-007**: Integration MUST handle all library exceptions and translate them to appropriate Home Assistant errors (ConfigEntryAuthFailed, ConfigEntryNotReady, etc.)
- **FR-008**: Integration MUST maintain existing config entry structure so users don't need to reconfigure
- **FR-009**: Integration MUST preserve entity unique IDs, names, and device associations so entity histories are maintained
- **FR-010**: Integration MUST pass hassfest validation with the library dependency properly declared
- **FR-011**: All existing tests MUST be updated to mock unifi-official-api instead of custom API clients
- **FR-012**: Integration MUST maintain the same update intervals and coordinator behavior as current implementation
- **FR-013**: Integration MUST provide diagnostic information through async_get_config_entry_diagnostics including library version, redacted connection info (host with credentials removed), and sanitized error messages from library exceptions
- **FR-014**: All existing services (refresh_data, restart_device, etc.) MUST continue to function through the library
- **FR-015**: Integration MUST maintain SSDP discovery functionality for UniFi Dream Machine devices
- **FR-016**: Integration MUST undergo comprehensive pre-release validation including automated tests, manual testing against real UniFi controller, and beta testing with selected users before general release

### Key Entities

- **UniFi Site**: Represents a UniFi network site/location, contains devices and provides site-level configuration
- **UniFi Device**: Represents a UniFi network device (AP, Switch, Gateway, etc.), includes status, metrics, and control capabilities
- **UniFi Client**: Represents a connected client device, includes connection info and statistics
- **Protect Camera**: Represents a UniFi Protect camera with video/image streaming and control capabilities
- **Device Metrics**: CPU usage, memory usage, uptime, network throughput for monitored devices

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: All existing integration features continue to work identically after migration with zero regression in functionality
- **SC-002**: Integration passes all hassfest validation checks including requirements verification
- **SC-003**: Code coverage remains at or above 80% with all tests passing against the new library implementation
- **SC-004**: Custom API client code (unifi_network_api.py, unifi_protect_api.py) is completely removed from the codebase
- **SC-005**: Integration successfully loads and initializes with unifi-official-api 1.0.x (any patch version) installed
- **SC-006**: Entity update cycles complete within the same time bounds as the previous implementation (no performance regression)
- **SC-007**: Existing user installations upgrade without requiring reconfiguration or losing entity history
- **SC-008**: Integration code structure passes review against Home Assistant core integration patterns
- **SC-009**: All coordinator data processing logic successfully consumes data from unifi-official-api library
- **SC-010**: Error handling and logging provide clear, actionable messages when library-related issues occur
- **SC-011**: Pre-release validation completes successfully with all automated tests passing, manual testing against real UniFi controller showing zero regressions, and beta testers reporting no critical issues
- **SC-012**: Diagnostic information includes library version for troubleshooting and contains no sensitive credentials or API keys

## Assumptions

- The unifi-official-api 1.0.x library provides equivalent or better functionality compared to the custom API clients
- The library's API surface remains backward compatible across patch versions (1.0.0, 1.0.1, 1.0.2, etc.)
- The library handles authentication, session management, and connection pooling appropriately for Home Assistant's async model
- Data structures returned by the library are compatible or easily mappable to existing entity attributes
- The library supports both UniFi Network and UniFi Protect APIs that are currently used by the integration
- Atomic migration approach (single release) is acceptable given thorough pre-release testing and validation
- Existing test fixtures can be adapted to mock the library instead of custom clients
- If critical issues arise post-release, a hotfix or rollback release can be issued quickly
- Library maintainers follow semantic versioning properly, ensuring patch versions (1.0.x) remain backward compatible
- If a problematic patch version is discovered, the integration can be updated to pin a specific safe version
