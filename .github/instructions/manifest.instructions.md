---
applyTo: "custom_components/unifi_insights/manifest.json"
---

# Manifest Instructions

**Applies to:** Integration manifest file

## Current Manifest Structure

```json
{
  "domain": "unifi_insights",
  "name": "UniFi Insights",
  "after_dependencies": ["http", "frontend", "lovelace"],
  "codeowners": ["@ruaan-deysel"],
  "config_flow": true,
  "dependencies": [
    "ffmpeg",
    "media_source",
    "stream",
    "wake_on_lan",
    "webhook",
    "websocket_api"
  ],
  "documentation": "https://github.com/tinkerologie/ha-unifi-insights",
  "integration_type": "hub",
  "iot_class": "local_polling",
  "issue_tracker": "https://github.com/tinkerologie/ha-unifi-insights/issues",
  "requirements": ["segno==1.6.6"],
  "ssdp": [
    { "manufacturer": "Ubiquiti Networks", "modelName": "UniFi Dream Machine" },
    {
      "manufacturer": "Ubiquiti Networks",
      "modelName": "UniFi Dream Machine Pro"
    },
    {
      "manufacturer": "Ubiquiti Networks",
      "modelName": "UniFi Dream Machine SE"
    },
    { "manufacturer": "Ubiquiti Inc.", "modelName": "UniFi Dream Machine" },
    { "manufacturer": "Ubiquiti Inc.", "modelName": "UniFi Dream Machine Pro" },
    { "manufacturer": "Ubiquiti Inc.", "modelName": "UniFi Dream Machine SE" }
  ],
  "version": "YYYY.MM.PATCH"
}
```

## Key Fields

- **domain** — `unifi_insights` (never change)
- **integration_type** — `hub` (gateway to multiple devices and services)
- **iot_class** — `local_polling` (polling with real-time WebSocket updates for Protect)
- **after_dependencies** — `["http", "frontend", "lovelace"]` for custom Lovelace card static path and resource registration (`frontend.py`)
- **dependencies** — `ffmpeg` and `stream` (camera streaming), `media_source` (Protect media browsing), `wake_on_lan` (Wake button magic packet), `webhook` (alarm/event webhooks), `websocket_api` (frontend card WS commands)
- **requirements** — `["segno==1.6.6"]` (QR code generation for guest vouchers). The UniFi API client is vendored under `custom_components/unifi_insights/api`; never re-add `unifi-official-api` to `requirements`
- **ssdp** — Discovery matchers for UniFi Dream Machine variants
- **version** — Calendar versioning: `YYYY.MM.PATCH`

## Rules

- Keep keys sorted (`domain` and `name` first, then alphabetical as required by Hassfest)
- Never add unnecessary runtime dependencies
- Never declare the vendored API package in `requirements`
