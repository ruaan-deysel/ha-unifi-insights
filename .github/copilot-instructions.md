# Copilot Instructions

- Architecture: Home Assistant custom integration for UniFi Network/Protect using the vendored async clients in [../custom_components/unifi_insights/api](../custom_components/unifi_insights/api); data is centralized across the multi-coordinator system in [../custom_components/unifi_insights/coordinators/](../custom_components/unifi_insights/coordinators/) (`config`, `device`, `protect`, `facade`), with websocket callbacks when Protect is available and stale-device cleanup against the device registry.
- Runtime data: Coordinator stores `data` under `sites`, `devices`, `clients`, `stats`, and `protect` (cameras/lights/sensors/nvrs/viewers/chimes/liveviews/events); lookups go through helpers like `get_site`, `get_device`, `_model_to_dict` to normalize pydantic/camelCase structures.
- Config/auth: [../custom_components/unifi_insights/config_flow.py](../custom_components/unifi_insights/config_flow.py) supports `local` (host + API key, optional verify_ssl) and `remote` (console_id + API key) modes; unique_id uses the API key; reauth/reconfigure mirrors the same validation by fetching sites.
- Entry setup: [../custom_components/unifi_insights/__init__.py](../custom_components/unifi_insights/__init__.py) builds Network client for both modes, Protect client only for local, validates connectivity (fetch sites/cameras), then seeds coordinator and forwards platforms.
- Constants/endpoints: [../custom_components/unifi_insights/const.py](../custom_components/unifi_insights/const.py) centralizes device/service names and UniFi Network/Protect endpoint paths; reuse these instead of hardcoding strings.
- Data transforms: [../custom_components/unifi_insights/data_transforms.py](../custom_components/unifi_insights/data_transforms.py) maps library responses to internal field names (status → connected/disconnected, camelCase → snake_case); extend this when adding new API fields and keep tests updated in [../tests/test_data_transforms.py](../tests/test_data_transforms.py).
- Entity bases: [../custom_components/unifi_insights/entity.py](../custom_components/unifi_insights/entity.py) provides `UnifiInsightsEntity` (network) and `UnifiProtectEntity` (protect) that handle availability, device_info (including MAC connections), and mixed camelCase/snake_case fields via `get_field`; prefer these bases for new entities.
- Entities: Sensors, binary_sensors, cameras, lights, switches build from coordinator data and the above bases (see [../custom_components/unifi_insights/sensor.py](../custom_components/unifi_insights/sensor.py), [../custom_components/unifi_insights/binary_sensor.py](../custom_components/unifi_insights/binary_sensor.py), [../custom_components/unifi_insights/camera.py](../custom_components/unifi_insights/camera.py), [../custom_components/unifi_insights/light.py](../custom_components/unifi_insights/light.py), [../custom_components/unifi_insights/switch.py](../custom_components/unifi_insights/switch.py)). Protect availability is `state == CONNECTED`; network availability uses `is_device_online` helper.
- Sensor patterns: Network sensors expose CPU/memory/uptime/tx/rx, client counts, and per-port metrics (only for ports with state UP). Many diagnostic entities are disabled by default; preserve registry defaults when adding new sensors.
- Binary sensor patterns: Motion/person/vehicle/animal/package detection and ring events rely on coordinator-stored `lastMotion*`, `lastSmartDetectTypes`, `lastRing*`; doorbell detection falls back on `_camera_type`, API type strings, or name heuristics.
- Services: [../custom_components/unifi_insights/services.py](../custom_components/unifi_insights/services.py) registers HA services for refresh, restart_device, Protect controls (recording/hdr/video mode, mic volume, light mode/level, PTZ move/patrol, chime volume/ringtone/repeat, alarm/liveview helpers), and Network actions (authorize_guest, voucher CRUD). Route every action to the owning console with `_get_coordinator_for_network_resource`/`_get_coordinator_for_protect_resource` and raise `HomeAssistantError` with user-facing messages.
- Update flow: Coordinator fetches sites → per-site devices/clients/stats → Protect devices; cleans stale devices from the registry using previously seen IDs. When adding data, ensure the coordinator’s `data` schema remains consistent for entity lookups.
- Testing/linting: `pytest` (configured in [../pyproject.toml](../pyproject.toml) with coverage >=95%, HTML/XML reports) and `./script/lint` (ruff format + check --fix). Type checks via mypy strict settings; ignore_missing_imports is on. Security checks via bandit.
- Dev server: `./script/develop` boots Home Assistant using ./config with `PYTHONPATH` set to custom_components; ensure dependencies are installed via `./script/setup/bootstrap`.
- Conventions: `PARALLEL_UPDATES` set to 0 for coordinator-driven entities, 1 for action-based Protect entities; prefer camelCase tolerance via `get_field`; keep service schemas in sync with `services.yaml`; avoid duplicating API paths or constants.
- Vendored API package: [../custom_components/unifi_insights/api](../custom_components/unifi_insights/api) contains the local copy of the upstream UniFi API client; reuse its client methods (network_client/protect_client) rather than manual HTTP calls.
- UniFi Developer Portal: Consult https://developer.ui.com/ for the latest official UniFi API documentation, endpoint specifications, and developer capabilities.
- Machine-readable API refs: the portal's HTML docs are JavaScript-rendered, so fetching them returns an empty app shell. Use `https://developer.ui.com/llms.txt` (root index of APIs and versions), `https://developer.ui.com/{service}/{version}/llms.txt` (endpoint list), `https://developer.ui.com/{service}/{version}/openapi.json` (schemas), and `https://developer.ui.com/network/v10.4.57/ai-gettingstarted.md` (Network primer for agents).

## Pull Request Code Review Guidelines

When reviewing pull requests for this repository, act as a strict Home Assistant Integration Quality Scale reviewer and senior engineer. Prioritize correctness, architectural layering, error handling, security, and test coverage over superficial comments.

### 1. Architectural & Home Assistant Quality Scale Rules
- **Strict Layering Integrity:** Entities must NEVER make direct network or API client calls; they must read state exclusively from `coordinator.data`. Actions/services must route through coordinator or facade methods.
- **Entity Inheritance:** Network entities must inherit from `UnifiInsightsEntity`; Protect entities must inherit from `UnifiProtectEntity`. Do not create unapproved entity bases or helper packages (`helpers/`, `shared/`, etc.).
- **UniFi API Data Tolerance:** UniFi API payloads use camelCase; ensure entity getters and transformations safely use `get_field()` or the pre-transformed keys from `data_transforms.py`. Flag unsafe direct dictionary index lookups (`dict["someKey"]`) that could raise `KeyError`.
- **Availability Contract:** Availability must use `is_device_online` for network entities and `state == CONNECTED` for Protect entities. Never raise exceptions in `@property` getters.
- **Concurrency:** `PARALLEL_UPDATES` must be `0` for coordinator-driven entities and `1` for action-based Protect entities.
- **Exceptions & Errors:** Integration setup failures must raise `ConfigEntryNotReady` (temporary) or `ConfigEntryAuthFailed` (bad credentials). Service calls must raise `HomeAssistantError` with actionable, user-friendly messages.
- **Diagnostics Redaction:** Ensure any changes touching diagnostics export use `async_redact_data` to redact sensitive values (passwords, tokens, API keys, client MAC/IP addresses where applicable, and user identifiers).

### 2. Breaking Changes Detection
Flag any PR as needing closer human inspection before approval if it introduces:
- Changes to `unique_id` generation, entity IDs, or device identifier tuples (breaks automations).
- Modifications to config entry storage structure or options flow schemas without explicit backward-compatible migration logic.
- Renaming or removing service action fields or return schemas.

### 3. Vendored API & Spec Alignment
- External network requests must go through the vendored client (`custom_components/unifi_insights/api`). Flag any raw `aiohttp`, `requests`, or custom HTTP clients.
- Verify new API routes and payloads against official UniFi OpenAPI definitions (`developer.ui.com`).

### 4. Testing & Coverage Requirements
- Every new entity, coordinator branch, service action, or API client method must have tests in `tests/`.
- Ensure tests maintain the project's minimum 95% branch coverage requirement.
- Flag any test attempting real network I/O; all external interactions must be mocked.
- For frontend pull requests (`frontend/src/**`), ensure TypeScript types are sound and tests pass.
