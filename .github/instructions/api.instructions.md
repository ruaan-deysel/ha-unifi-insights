---
applyTo: "custom_components/unifi_insights/__init__.py, custom_components/unifi_insights/coordinators/**/*.py"
---

# API and Coordinator Instructions

**Applies to:** Integration setup and coordinator files that interact with the API

## Architecture (CRITICAL)

**Entities → Coordinator → API Client** — Never skip layers

- **Entities:** Read `coordinator.data` only, never call API
- **Coordinator:** Calls API, transforms data, handles errors/timing
- **API Client:** The vendored package in `custom_components/unifi_insights/api` handles communication

## Vendored API package

This integration vendors the upstream `unifi-official-api` project under `custom_components/unifi_insights/api`. It is not declared as a runtime dependency in `manifest.json`.

**Rules:**

- NEVER create a custom HTTP client — reuse or extend the vendored package
- Reuse `network_client` and `protect_client` methods
- Never duplicate API endpoint paths — reference `const.py`

## Client Setup

In `__init__.py`:

- Network client: Created for both local and remote modes
- Protect client: Created for both local and remote modes
- Validates connectivity by fetching sites (Network) and cameras (Protect)

## Session management

- The library manages its own sessions
- Don't create `aiohttp.ClientSession` manually for API calls
- Let the vendored package handle authentication and retries

## Data Transforms

- Use `data_transforms.py` for mapping API responses to internal schema
- Normalize status values (e.g., `online` → `connected`)
- Handle camelCase → snake_case conversion
- Extend transforms when adding new API fields

## Exception Hierarchy

Map library exceptions to HA exceptions:

| Library Exception     | HA Exception            | When                   |
| --------------------- | ----------------------- | ---------------------- |
| `AuthenticationError` | `ConfigEntryAuthFailed` | Bad credentials        |
| `TimeoutError`        | `ConfigEntryNotReady`   | Controller unreachable |
| `ApiError`            | `UpdateFailed`          | Transient API failure  |
| Any API error         | `HomeAssistantError`    | In service calls       |
