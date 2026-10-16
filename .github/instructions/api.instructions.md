---
applyTo: "custom_components/unifi_insights/__init__.py, custom_components/unifi_insights/probe.py, custom_components/unifi_insights/coordinators/**/*.py, custom_components/unifi_insights/api/**/*.py"
---

# API and Coordinator Instructions

**Applies to:** Integration setup, capability probing, coordinators, and vendored API clients

## Architecture (CRITICAL)

**Entities → Coordinator → API Client** — Never skip layers

- **Entities:** Read `coordinator.data` only; never call API clients directly in state properties
- **Coordinators:** Call API clients, normalize data via `data_transforms.py`, handle errors and polling/WebSocket lifecycle
- **API Clients:** Vendored under `custom_components/unifi_insights/api/` (`network`, `protect`, `access`, `innerspace`, `site_manager`, `mobility`, `carrier_fabric`)

## Vendored API Package

This integration vendors the `unifi-official-api` package locally under `custom_components/unifi_insights/api/`. It is not declared as an external PyPI dependency in `manifest.json`.

**Rules:**

- NEVER create ad-hoc `aiohttp` calls outside `custom_components/unifi_insights/api/` — reuse or extend the vendored client modules
- Inject Home Assistant's shared `aiohttp.ClientSession` via `async_get_clientsession(hass, verify_ssl=...)` (Platinum `inject-websession`)
- All client operations must be async (Platinum `async-dependency`)
- Always consult the [UniFi Developer Portal](https://developer.ui.com/) machine-readable specs before adding or modifying API endpoints or models:
  - `https://developer.ui.com/llms.txt` — root index of APIs and versions (as of 2026-10: Network `v10.6.106`, Protect `v7.3.70`, Mobility `v1.0.0`, InnerSpace `v1.3.23`, Site Manager `v1.0.0`, Carrier Fabric `v1.0.0`)
  - `https://developer.ui.com/{service}/{version}/llms.txt` — endpoint list for a service
  - `https://developer.ui.com/{service}/{version}/openapi.json` — authoritative OpenAPI request/response schemas

## Client Setup & Capability Probing

In `__init__.py` and `probe.py`:

- Clients are instantiated with Home Assistant's shared session (`async_get_clientsession`)
- Optional UniFi applications (Protect, Access, InnerSpace, Site Manager, Mobility) are probed gracefully via `probe.py` so consoles running only a subset of applications set up cleanly without failing the config entry

## Data Transforms

- Use `data_transforms.py` (`get_field`, `first_not_none`, model-to-dict helpers) for mapping API responses to internal coordinator dictionaries
- Use `first_not_none()` whenever a valid value can be `0`, `0.0`, `False`, or `""`
- Handle camelCase / snake_case tolerance consistently

## Exception Hierarchy

Map vendored API exceptions (`custom_components/unifi_insights/api/`) to Home Assistant exceptions:

| Vendored API Exception                                                          | Home Assistant Exception                                             | Context                                                     |
| ------------------------------------------------------------------------------- | -------------------------------------------------------------------- | ----------------------------------------------------------- |
| `UniFiAuthenticationError`                                                      | `ConfigEntryAuthFailed`                                              | Setup (`__init__.py`) or Coordinator (`_async_update_data`) |
| `UniFiConnectionError`, `UniFiTimeoutError`                                     | `ConfigEntryNotReady`                                                | Setup (`__init__.py`) when controller is unreachable        |
| `UniFiConnectionError`, `UniFiTimeoutError`, `UniFiResponseError`, `UniFiError` | `UpdateFailed`                                                       | Coordinator refresh (`_async_update_data`)                  |
| `UniFiResponseError`, `UniFiError`                                              | `HomeAssistantError` (with `translation_domain` & `translation_key`) | Service actions (`services.py`) and entity action methods   |
