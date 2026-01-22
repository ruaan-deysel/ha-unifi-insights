# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-01-22

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

## [1.0.0] - 2024-12-22

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
