---
applyTo: "custom_components/unifi_insights/manifest.json"
---

# Manifest Instructions

**Applies to:** Integration manifest file

## Current Manifest

```json
{
  "domain": "unifi_insights",
  "name": "UniFi Insights",
  "integration_type": "hub",
  "iot_class": "local_polling",
  "dependencies": ["ffmpeg", "stream"],
  "codeowners": ["@ruaan-deysel"]
}
```

## Key Fields

- **domain** — `unifi_insights` (never change)
- **integration_type** — `hub` (gateway to multiple devices)
- **iot_class** — `local_polling` (local network, polling-based with WebSocket for Protect)
- **dependencies** — `ffmpeg` and `stream` required for camera support
- **ssdp** — Discovery matchers for UniFi Dream Machine variants
- **version** — Format: `YYYY.MM.PATCH`

The UniFi API client is vendored in-repo under `custom_components/unifi_insights/api`; do not add `unifi-official-api` back to `requirements`.

## Version Format

This project uses calendar versioning: `YYYY.MM.PATCH`

- Year and month of release
- Patch increments within the same month

## Rules

- Never add unnecessary dependencies
- Do not declare the vendored API package as a manifest requirement
- Update version in manifest when releasing
- SSDP discovery covers Dream Machine, Dream Machine Pro, Dream Machine SE
