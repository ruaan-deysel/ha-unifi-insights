# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2026.6.3] - 2026-06-12

### Fixed

- Fixed UniFi Protect devices removed from the controller never being cleaned up — the Protect coordinator only ever added/merged devices into its data, so the stale-device registry cleanup could never detect a removal; each poll now rebuilds the camera/light/sensor/NVR/chime/viewer/liveview collections from the API response, making the Gold-tier stale-device cleanup actually work
- Fixed missing `@callback` decorator on the WiFi QR code image entity's `_handle_coordinator_update` override (same bug class as the 2026.6.2 coordinator fixes)
- Fixed all coordinators relying on Home Assistant's `current_entry` ContextVar fallback instead of passing `config_entry` explicitly to `DataUpdateCoordinator` — HA flags this pattern for removal (core breaks in 2026.8) and the explicit entry also auto-registers coordinator shutdown on entry unload
- Fixed the facade coordinator's `data` being `None` until an external (private) `_aggregate_data()` call from `__init__.py`; the facade now aggregates sub-coordinator data during its own initialization
- Fixed config entry unloading closing the API clients *before* unloading the platforms — a failed platform unload previously left loaded entities behind with closed clients; clients are now only closed after all platforms unloaded successfully
- Fixed `script/test` being broken: it pinned `homeassistant==2026.4.1` against `pytest-homeassistant-custom-component==0.13.317` (which requires HA 2026.3.1, an unsolvable conflict) and did not install the `segno` manifest requirement; it now installs HA 2026.6.2 with plugin 0.13.338 and `segno`

### Changed

- Service actions are now registered in `async_setup` instead of the first config entry setup, per the Quality Scale `action-setup` rule — actions are validatable even when no entry is loaded, and handlers raise `ServiceValidationError` when no coordinator is available
- Replaced the deprecated `OptionsFlowWithConfigEntry` base class with `OptionsFlow` (the config entry is provided automatically since HA 2024.11)
- Bumped the minimum Home Assistant version to `2026.6.0` in `hacs.json` and the README (HA is now on Python 3.14)
- Added `data_description` helper texts to the reauthentication and reconfigure config flow steps (Quality Scale `config-flow` rule)

### Tests

- Test suite now runs (and passes: 1043 tests, 90.5% coverage) against Home Assistant 2026.6.2 / Python 3.14
- Added a test module for the WiFi QR code image platform (`tests/test_image.py`)
- Updated stale tests that still asserted pre-2026.6.0 behavior (camera snapshot width/height parameters, uppercase tracker unique IDs, the removed global tracked-clients set) and fixed coordinator/config-flow test fixtures that leaked refresh timers and sockets

## [2026.6.2] - 2026-06-06

### Fixed

- Fixed missing `@callback` decorator on `UnifiFacadeCoordinator._handle_coordinator_update` — the method is registered as an event-loop listener via `async_add_listener()` on all three sub-coordinators and must be decorated with `@callback` per HA coding standards (closes #59)
- Fixed missing `@callback` decorators on `UnifiProtectCoordinator._handle_device_update` and `_handle_event_update` — these WebSocket callback handlers call `async_update_listeners()` (itself a `@callback`), so they must also be marked as event-loop callbacks
- Fixed misleading "WebSocket callbacks registered" debug log in the Protect coordinator — the message previously fired even when neither WebSocket callback was actually registered (both are guarded by `hasattr` checks that currently return `False`)

### Notes

- The HA warning "Updating state for switch.firewall_policies_default_crowdsec_bouncer_ban_2 took 0.548 seconds" reported in #59 is **not a code bug**. HA's threshold is 0.4 s and the warning fires only once per entity lifetime (`_slow_reported = True`). The entity's properties are all O(1) dict lookups; the 0.548 s was caused by the UDM-SE host running at 100% CPU, starving HA's event loop. The `@callback` changes above are correctness improvements aligned with HA standards that reduce the chance of async-violation warnings from HA's debug checker.

## [2026.6.1] - 2026-06-04

### Added

- Added **Client Control** option (enabled by default) to the integration's options flow — disabling it prevents creation of client allow/block switch entities and client reconnect button entities, eliminating orphaned unavailable entities when clients leave the network (closes #57)

### Fixed

- Fixed deprecation warning "The deprecated alias ScannerEntity was used from unifi_insights" by updating the import to `homeassistant.components.device_tracker.ScannerEntity`; the old path in `config_entry` is removed in HA Core 2027.6 (closes #58)
- Fixed microphone switch always showing as OFF on Protect v7.1.x — the API renamed the field from `micEnabled` to `isMicEnabled`; both names are now read with `isMicEnabled` taking priority, and the PATCH call now correctly sends `isMicEnabled`
- Fixed High FPS mode switch never being created on Protect v7.1.x cameras that support it — the API removed the `hasHighFpsCapability` feature flag in favour of listing `highFps` in `featureFlags.videoModes`; both detection methods are now checked

## [2026.6.0] - 2026-05-30

### Added

- Added per-WiFi-network connected client count sensors (`sensor.<ssid>_connected_clients`) — shows how many clients are currently on each SSID, updated every polling cycle (closes #49)
- Added WiFi QR code image entities (`image.<ssid>_wifi_qr_code`) — phone cameras can scan these directly to join the network; credentials sourced from the classic API (closes #49)
- Added `authorize_guest` and `unauthorize_guest` coordinator methods wired to the official Network Integration API `POST /clients/{id}/actions` endpoint with `AUTHORIZE_GUEST_ACCESS` / `UNAUTHORIZE_GUEST_ACCESS`; the previously stubbed `authorize_guest` service now works

### Fixed

- Fixed client block, unblock, reconnect, and forget actions returning HTTP 404 — the official Network Integration API does not expose these operations; they are now routed through the classic `POST /api/s/{site}/cmd/stamgr` endpoint (`block-sta`, `unblock-sta`, `kick-sta`, `forget-sta`) which is accessible with the same local API key (closes #44)
- Fixed classic API error envelopes (`{"meta":{"rc":"error",...}}` returned with HTTP 200) now raising `UniFiResponseError` instead of silently succeeding in client station-manager commands
- Fixed UniFi Protect cameras returning HTTP 500 (`AJV_PARSE_ERROR`) when HA requested a snapshot — the Protect Integration API rejects `w`/`h` query parameters; removed them from `get_snapshot`; HA scales the returned JPEG internally
- Fixed Protect model parsing silently dropping all cameras/sensors/lights/chimes/viewers when any single device in the response contains an unrecognised field value (e.g. a new enum from Protect 7.1) — each endpoint's `get_all()` now skips and logs the individual malformed item instead of failing the whole list (closes #52)
- Fixed `CameraState` and `ViewerState` (and `CameraType`) enums mapping unknown values to `UNKNOWN` instead of raising a `ValidationError`; Protect 7.1.x new states no longer break camera entities
- Fixed toggling "Track WiFi clients" / "Track wired clients" in the integration options having no effect — the dedup set previously survived config-entry reloads (stored in `hass.data`), so re-enabling tracking added nothing; the set is now local to each setup call, and the entity registry is reconciled on every reload to remove trackers that are no longer wanted and add those that are
- Fixed stale/historical client trackers polluting the integration when tracking was enabled — only currently-connected clients (from the official `/clients` endpoint) become tracker entities; known-but-disconnected devices from the controller history are not imported
- Fixed transient controller connectivity failures (`UniFiConnectionError`, `UniFiTimeoutError`) during device coordinator site processing logging a full ERROR traceback; they are now a concise WARNING

### Changed

- Bumped minimum Home Assistant version to `2026.5.4` in `manifest.json` and `requirements.txt`
- `script/setup/bootstrap` now installs the **latest available** Home Assistant release on every run (`uv pip install --upgrade ".[dev]" homeassistant`) instead of a hard-pinned version, so the dev environment stays current automatically
- WiFi data is now enriched at config-coordinator level: secrets (SSID, passphrase, security) are pulled from the classic `/rest/wlanconf` endpoint (the official API redacts them), and per-SSID client counts are computed from the classic `/stat/sta` endpoint
- `CameraType`, `CameraState`, and `ViewerState` Protect enums now extend a shared `_TolerantStrEnum` base that maps any unrecognised value to `UNKNOWN` instead of raising
- Added `segno==1.6.6` to `manifest.json` requirements for QR code image generation

- Fixed missing `TELEPORT` value in the vendored `ClientType` enum (alongside `VPN`) to prevent client model validation failures when controllers return this connection type

## [2026.5.0] - 2026-05-05

### Fixed

- Fixed port sensor display names showing generic labels like "Data size" and "Power" by restoring missing sensor translation keys in `translations/en.json`
- Fixed per-port sensor naming to use `{port_label}` translation placeholders so each metric has a distinct name (for example, "Port 1 TX", "Port 1 RX", and "Port 1 PoE Power")
- Fixed local/remote config flow handling for UniFi Network Integration API 404 responses by surfacing a clear `api_unsupported` user-facing error instead of an unexpected exception

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

[2026.6.2]: https://github.com/ruaan-deysel/ha-unifi-insights/compare/v2026.6.1...v2026.6.2
[2026.6.1]: https://github.com/ruaan-deysel/ha-unifi-insights/compare/v2026.6.0...v2026.6.1
[2026.6.0]: https://github.com/ruaan-deysel/ha-unifi-insights/compare/v2026.5.0...v2026.6.0
[2026.5.0]: https://github.com/ruaan-deysel/ha-unifi-insights/compare/v2026.4.1...v2026.5.0
[2026.4.1]: https://github.com/ruaan-deysel/ha-unifi-insights/compare/v2026.4.0...v2026.4.1
[2026.4.0]: https://github.com/ruaan-deysel/ha-unifi-insights/compare/v2026.3.2...v2026.4.0
[2026.3.2]: https://github.com/ruaan-deysel/ha-unifi-insights/compare/v2026.3.1...v2026.3.2
[2026.3.1]: https://github.com/ruaan-deysel/ha-unifi-insights/compare/v2026.3.0...v2026.3.1
[2026.3.0]: https://github.com/ruaan-deysel/ha-unifi-insights/compare/v2026.2.0...v2026.3.0
[2026.2.0]: https://github.com/ruaan-deysel/ha-unifi-insights/compare/v2025.06.05...v2026.2.0
[2025.06.05]: https://github.com/ruaan-deysel/ha-unifi-insights/releases/tag/v2025.06.05
