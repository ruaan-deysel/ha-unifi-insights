<!--
  Thank you for contributing to UniFi Insights!
  Please fill out this template to help reviewers understand your changes.

  Note for contributors and coding agents:
  Consult https://developer.ui.com/ for the latest official information,
  API references, and capabilities offered to UniFi developers.
-->

## Description

<!-- Provide a clear and concise description of what this pull request does. If this PR adds or updates API endpoints, models, or features, ensure you have checked https://developer.ui.com/ for latest specifications. -->

Closes # <!-- Link any related issues, e.g. Closes #123 -->

## Type of Change

<!-- Mark the appropriate option with an [x] -->

- [ ] 🐛 **Bug fix** (non-breaking change fixing an issue)
- [ ] ✨ **New feature** (non-breaking change adding functionality)
- [ ] 💥 **Breaking change** (fix or feature causing existing functionality/automations to break)
- [ ] ♻️ **Refactoring** (code organization, no functional change)
- [ ] 📝 **Documentation** (documentation updates only)
- [ ] 🧪 **Tests** (adding or improving test coverage)
- [ ] 🔧 **Maintenance / Chore** (dependency updates, tool config, CI)

## Architecture & Home Assistant Quality Scale Checklist

<!-- Mark all items that apply to your changes -->

- [ ] **UniFi Developer Portal**: Checked [developer.ui.com](https://developer.ui.com/) for the latest official UniFi API documentation, endpoints, and schema capabilities to ensure alignment with what UniFi offers to developers.
- [ ] **Data Flow**: Entities read solely from `coordinator.data` (no direct HTTP/network calls in entity properties).
- [ ] **API Encapsulation**: Actions and endpoints route through coordinator methods or vendored API clients (`custom_components/unifi_insights/api/`).
- [ ] **Base Entities**: Inherits from `UnifiInsightsEntity` or `UnifiProtectEntity` with `_attr_has_entity_name = True`.
- [ ] **Parallel Updates**: `PARALLEL_UPDATES = 0` for coordinator/read-only platforms, `1` for action platforms.
- [ ] **Error Handling**: API errors wrapped into user-friendly `HomeAssistantError` or `ServiceValidationError`.
- [ ] **Unique IDs & Device Info**: Unique IDs are deterministic and devices properly attached to `DeviceInfo`.
- [ ] **Translations**: New UI strings added to `strings.json` with appropriate translation keys.

## Validation Checklist

<!-- Run these commands before submitting -->

- [ ] `script/lint` (or `ruff check .` and `ruff format .`) passed with 0 errors.
- [ ] `mypy custom_components/unifi_insights` passed with 0 errors.
- [ ] `bandit -r custom_components/unifi_insights` passed with 0 vulnerabilities.
- [ ] `pytest` passed with ≥ 95% branch coverage (`pytest --cov=custom_components/unifi_insights`) and Codecov coverage targets met.
- [ ] `CHANGELOG.md` updated under `[Unreleased]` with clear user-facing descriptions.
- [ ] Tested on a live local Home Assistant instance (`./script/develop`) without errors in logs.

## Breaking Changes (if applicable)

<!-- If this change breaks backwards compatibility (e.g., changes entity IDs, unique IDs, config entry data, or services), describe the impact and migration path below. -->

- [ ] No breaking changes
- [ ] Breaking change: <!-- Describe breaking change and rationale -->

## Additional Context

<!-- Add any other context, screenshots, or logs about the pull request here. Reference relevant documentation or endpoints from https://developer.ui.com/ where applicable. -->
