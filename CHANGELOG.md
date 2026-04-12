# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2026.4.1] - 2026-04-12

### Security

- Fixed pip tar extraction symlink vulnerability (CVE-2025-8869) by raising minimum `pip` to `>=25.3` in `requirements.txt`
- Redacted sensitive field values (API keys, passwords, tokens, credentials, PSKs, passphrases, vouchers) from debug log messages and API error bodies in the vendored API base client
- `UniFiResponseError.__str__()` now returns only the exception type and status code (`ExceptionType(status=<code>)`), preventing `message` or raw response body from leaking into logs or error messages
- Expanded `diagnostics.py` redaction set to cover tokens, credentials, network identifiers (IP, hostname, WAN/LAN IPs), device identifiers (MAC, serial), config entry fields, and location data (latitude, longitude)
- Pinned GitHub Actions `actions/checkout` and `actions/stale` to full SHA digests to mitigate supply chain attacks

### Added

- Added `"homeassistant": "2026.4.1"` minimum version requirement to `manifest.json`
- Added Aikido security scan instructions (`.github/instructions/aikido_rules.instructions.md`) to enforce pre-commit and PR security scanning

### Fixed

- Fixed `script/setup/bootstrap` pre-commit hook installation failing when a global `core.hooksPath` is configured (e.g. by the Aikido devcontainer scanner); the local repo value is now overridden to the default `.git/hooks` path before installing
- Fixed incorrect `unique_id` values in test fixtures — both remote and local config entries now use the API key as `unique_id`, matching the actual config flow behavior (`async_set_unique_id(api_key)`)

### Changed

- Replaced `softprops/action-gh-release` in the release workflow with the native `gh release create` CLI command, removing a third-party action dependency
- Log-line string concatenations in `__init__.py` consolidated to single-line strings (cosmetic)

## [2026.4.0] - 2026-04-09

### Added

- Added `.github/dependabot.yml` configuration for `devcontainers`, `github-actions`, and `pip` updates with daily checks, grouped updates, labels, and commit message prefixes

### Changed

- Updated Home Assistant minimum/runtime version to `2026.4.1` across `requirements.txt`, `hacs.json`, `script/setup/bootstrap`, and `script/test`
- Updated dependency automation to allow future Home Assistant version updates (removed Dependabot ignore rule for `homeassistant`)

### Fixed

- Fixed Protect API validation to probe the NVR endpoint when camera discovery returns an empty list, preventing valid "no cameras" setups from being misclassified as Protect API failures (PR #22)

## [2026.3.2] - 2026-03-31

### Added

- Added SFP/SFP+ port differentiation with user-friendly port names (e.g., "SFP+ 1" instead of "Port 25")
- Added SFP module diagnostic sensors: module model, vendor, type (compliance), and serial number
- Added SFP module presence binary sensor for all SFP/SFP+ ports with module detail attributes
- Added port type extra state attributes (media type, uplink status, network, SFP presence) to all port sensors
- Added auto-pagination support for wired client fetching to handle large networks correctly

### Fixed

- Fixed PoE sensor creation failing on non-PoE devices (e.g., UDM Pro) by checking port PoE capability before creating sensors
- Fixed firewall rule switches to properly filter predefined/system rules and group by gateway device
- Fixed port sensor filtering to skip inactive (DOWN) ports
- Fixed `get_port_metrics` endpoint to check PoE capability before requesting PoE data

### Removed

- Removed port enable/disable switches (unreliable with current UniFi API)
- Removed PoE toggle switches (unreliable with current UniFi API)
- Removed port power cycle buttons for PoE ports

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
