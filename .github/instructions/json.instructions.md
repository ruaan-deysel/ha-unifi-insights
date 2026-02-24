---
applyTo: "**/*.json"
---

# JSON Instructions

**Applies to:** All JSON files

## Formatting

- 2-space indentation
- No trailing commas
- No comments (JSON does not support comments)
- UTF-8 encoding
- Final newline

## Key Files

- `manifest.json` — Integration metadata (domain, version, requirements, etc.)
- `strings.json` — Translatable UI strings
- `icons.json` — Custom entity icons (MDI icon references)
- `hacs.json` — HACS store metadata

## Validation

- `manifest.json` is validated by hassfest
- `strings.json` structure must match HA translation schema
- `icons.json` must reference valid MDI icon names
