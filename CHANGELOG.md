# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2026.3.1] - 2026-03-22

### Fixed

- Fixed Unifi Remote Cloud authentication issue.

## [2026.3.0] - 2026-03-15

### Added

- Expanded the vendored UniFi Network API package with typed models and endpoints for firewall policies, DNS policies, traffic matching lists, vouchers, supporting resources, and legacy site and device lookups
- Added a full vendored UniFi Protect client with endpoint coverage for cameras, sensors, lights, chimes, NVRs, viewers, live views, events, application files, RTSPS streams, talkback sessions, and WebSocket subscriptions
- Added enable and disable switches for user-defined UniFi Network firewall rules
- Added network device temperature sensors backed by legacy controller temperature data when available
- Added a new `script/` command suite for bootstrap, linting, testing, spell checking, hassfest validation, Home Assistant startup, config reset, and HACS sync

### Changed

- Vendored the upstream `unifi-official-api` project into `custom_components/unifi_insights/api`
- Switched the integration to use the local vendored API package instead of an external runtime dependency
- Reworked the remote cloud config flow so API keys discover accessible consoles first, then validate the selected console during setup, reauth, and reconfigure
- Updated the development environment and repository tooling for the new `script/` layout, Python 3.14, and Home Assistant 2026.3.1

### Fixed

- Fixed remote cloud setup and reconfiguration flows for API keys that can access multiple UniFi consoles by prompting for console selection instead of relying on manual console ID entry
- Fixed coordinator updates to merge legacy device temperature data without failing refreshes when legacy controller endpoints are unavailable
- Fixed diagnostics and tests to report and validate the vendored API package instead of the removed external dependency
- Fixed vendored WiFi broadcast updates to send full controller-compatible payloads on update
- Added `_attr_translation_key` to 18 Protect and network entity classes for proper HA name localization
- Removed unused SSDP discovery matchers from `manifest.json` (no `async_step_ssdp` handler existed)
- Downgraded auth, connection, and timeout error logging from `exception` to `warning` to reduce log noise on expected failures
- Deduplicated `_get_client_type` helper into `entity.py` as the shared `get_client_type` function
- Added `mac` and `mac_address` to diagnostics redaction set alongside the existing `macAddress` entry
- Fixed `update.py` `latest_version` to return the actual target firmware version instead of a static placeholder string
- Added complete entity translation entries in `strings.json` for switch, select, number, event, and update platforms
- Fixed pre-existing test failures in diagnostics, entity, and update test modules

### Removed

- Removed `unifi-official-api` from manifest and project dependency declarations
- Removed the legacy `scripts/` helpers in favor of the new `script/` tooling layout

### Technical

- Added a `py.typed` marker for the vendored API package and excluded the vendored subtree from first-party Ruff, mypy, and pre-commit checks
- Updated contributor and agent documentation to reference the vendored API package and the new development script workflow

## [2026.2.0] - 2026-01-22

### Changed

- **BREAKING**: Migrated from custom API implementation to `unifi-official-api` library
- Replaced `unifi_network_api.py` and `unifi_protect_api.py` with official library
- Updated coordinator to use library's pydantic models with `model_dump(by_alias=True)` for camelCase compatibility
- Improved data transformation layer for consistent field naming

### Added

#### UniFi Network

- **WiFi Network Switches**: Enable/disable WiFi networks directly from Home Assistant
- **Client Block/Allow Switches**: Block or allow network clients
- **Device Tracker Platform**: Track wireless and wired clients as device_tracker entities
- **Port Enable Switches**: Enable/disable switch ports
- **PoE Switches**: Control PoE on switch ports
- **Update Platform**: Firmware update entities for network devices

#### UniFi Protect

- **Event Platform**: Motion, ring, and smart detection events as event entities
- **Smart Detection Binary Sensors**: Person, vehicle, animal, and package detection
- **Camera Switches**: Microphone, privacy mode, status light, and high FPS mode controls
- **PTZ Controls**: Move to preset and patrol controls via services
- **Chime Services**: Volume, ringtone, and repeat time controls

#### Integration Features

- **Connection Type Selection**: Support for both Local (direct) and Remote (cloud) connections
- **Options Flow**: Configure WiFi and wired client tracking preferences
- **Reauth Flow**: Handle expired API keys gracefully
- **Reconfigure Flow**: Update connection settings without removing the integration
- **Repairs Platform**: Automatic repair suggestions for common issues
- **Diagnostics**: Enhanced diagnostic data for troubleshooting
- **Icons**: Custom icons for all entity types via icons.json

### Fixed

- Fixed `interfaces` field handling for list vs dict format from different API responses
- Fixed NVR storage sensors showing "Unavailable" when API doesn't provide storage data
- Fixed WiFi switch device info to avoid via_device warnings
- Fixed translations for all new entity types
- Fixed client type detection for wired/wireless client counting
- Fixed availability checks for all entity types

### Removed

- Removed custom `unifi_network_api.py` (replaced by `unifi-official-api` library)
- Removed custom `unifi_protect_api.py` (replaced by `unifi-official-api` library)
- Removed unused test files and API test results

### Technical

- Updated to Home Assistant 2026.1.2 compatibility
- 621 tests with 91.62% code coverage
- Full type hints with `py.typed` marker
- Comprehensive linting with ruff/black
- Pre-commit hooks for code quality

## [2025.06.05] - 2025-06-05

### Added

- Initial release of UniFi Insights integration
- Basic sensor support for UniFi Network devices
- CPU, memory, uptime, and throughput sensors
- Device status binary sensors
- Basic camera support for UniFi Protect
- Light control for UniFi Protect lights
- Number entities for camera/light settings
- Select entities for recording modes and video modes

[2.0.0]: https://github.com/ruaan-deysel/ha-unifi-insights/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/ruaan-deysel/ha-unifi-insights/releases/tag/v1.0.0
