---
applyTo: "config/configuration.yaml, config/**/*.yaml"
---

# Configuration YAML Instructions

**Applies to:** Local Home Assistant configuration files

## YAML Configuration

This integration uses **config flow only** — no YAML configuration for the integration itself.

The `config/` directory contains the local development Home Assistant configuration.

## Local Development Config

- `config/configuration.yaml` — Main HA config for local dev
- Adjust log levels here for debugging:
  ```yaml
  logger:
    default: warning
    logs:
      custom_components.unifi_insights: debug
  ```

## Rules

- NEVER add YAML-based configuration for the integration
- Config flow is the only supported setup method
- The `config/` directory is for local development only
- Don't commit sensitive data in configuration files
