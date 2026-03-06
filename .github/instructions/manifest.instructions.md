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
  "requirements": ["unifi-official-api~=1.1.0"],
  "dependencies": ["ffmpeg", "stream"],
  "codeowners": ["@ruaan-deysel"]
}
```

## Key Fields

- **domain** — `unifi_insights` (never change)
- **integration_type** — `hub` (gateway to multiple devices)
- **iot_class** — `local_polling` (local network, polling-based with WebSocket for Protect)
- **requirements** — Only `unifi-official-api` (the sole runtime dependency)
- **dependencies** — `ffmpeg` and `stream` required for camera support
- **ssdp** — Discovery matchers for UniFi Dream Machine variants
- **version** — Format: `YYYY.MM.PATCH`

## Version Format

This project uses calendar versioning: `YYYY.MM.PATCH`
- Year and month of release
- Patch increments within the same month

## Rules

- Never add unnecessary dependencies
- Keep requirements pinned with `~=` (compatible release)
- Update version in manifest when releasing
- SSDP discovery covers Dream Machine, Dream Machine Pro, Dream Machine SE
