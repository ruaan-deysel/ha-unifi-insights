# Architectural and design decisions

This document is the index of significant architectural and design decisions for the UniFi Insights integration. Each entry summarizes one decision and links to its full Architecture Decision Record (ADR) in [`adr/`](./adr/).

## Format

Each ADR follows the template from [ADR-001](./adr/001-record-architecture-decisions.md):

- **Date**: when the decision was made or last updated
- **Status**: Proposed, Accepted, Deprecated, or Superseded by ADR-NNN
- **Context**: the problem, and the Home Assistant or UniFi API constraints that apply
- **Decision**: what was decided
- **Alternatives considered**: options with pros and cons
- **Consequences**: positive, negative, and neutral impacts

An accepted ADR is never edited to change its meaning. A new ADR supersedes it instead, so the log shows how long each decision governed the code.

---

## Decision log

| ADR                                                                  | Title                                                      | Status   | Date       |
| -------------------------------------------------------------------- | ---------------------------------------------------------- | -------- | ---------- |
| [001](./adr/001-record-architecture-decisions.md)                    | Record architecture decisions                              | Accepted | 2026-10-16 |
| [002](./adr/002-multi-coordinator-architecture-behind-a-facade.md)   | Multi-coordinator architecture behind a facade             | Accepted | 2026-10-16 |
| [003](./adr/003-vendor-the-unifi-api-client.md)                      | Vendor the UniFi API client inside the integration         | Accepted | 2026-10-16 |
| [004](./adr/004-stable-console-identity-for-unique-ids.md)           | Stable console identity for config entry unique IDs        | Accepted | 2026-10-16 |
| [005](./adr/005-bundled-dashboard-cards-with-versioned-contracts.md) | Bundled dashboard cards with versioned WebSocket contracts | Accepted | 2026-10-16 |
| [006](./adr/006-three-layer-diagnostics-redaction.md)                | Three-layer diagnostics redaction                          | Accepted | 2026-10-16 |
| [007](./adr/007-flat-home-assistant-module-layout.md)                | Flat Home Assistant module layout                          | Proposed | 2026-10-16 |

### Multi-coordinator architecture behind a facade

One `DataUpdateCoordinator` per data domain (Config 5 min, Device 30 s, Protect 30 s plus WebSocket, Access 30 s plus webhook, InnerSpace 5 min, Site Manager 10 min, Mobility 5 min, Carrier Fabric 5 min), aggregated by a push-only facade coordinator that entities and services read from. Keeps expensive configuration polls off the 30 s path and gives every data source its own error and recovery handling. [ADR-002](./adr/002-multi-coordinator-architecture-behind-a-facade.md)

### Vendor the UniFi API client inside the integration

The upstream `unifi-official-api` package is copied into `custom_components/unifi_insights/api/` and held to the same typing and 95% per-file coverage rules as the integration. Contract fixes against the official OpenAPI specs ship with the integration instead of waiting for a PyPI release. [ADR-003](./adr/003-vendor-the-unifi-api-client.md)

### Stable console identity for config entry unique IDs

`unique_id` is the gateway or Cloud Key MAC (falling back to the Protect NVR MAC) for local entries, the cloud `console_id` for remote entries, and `carrier_<org_id>` for Carrier Fabric. One module, `console_identity.py`, answers the question for both the config flow and setup, so the two can never drift. [ADR-004](./adr/004-stable-console-identity-for-unique-ids.md)

### Bundled dashboard cards with versioned WebSocket contracts

The six Lovelace cards are compiled from `frontend/` and served by the integration itself with content-digest cache busting. Cards talk to `websocket_api.py` through versioned TypedDict snapshot contracts, and topology node ids are per-entry HMACs of the MAC. [ADR-005](./adr/005-bundled-dashboard-cards-with-versioned-contracts.md)

### Three-layer diagnostics redaction

Diagnostics pass through `TO_REDACT`, then `CLIENT_TO_REDACT` / `WIFI_TO_REDACT`, then `_anonymize_macs()`. A new field is safe by default because the layers run on the whole payload, not on a hand-picked list of keys. [ADR-006](./adr/006-three-layer-diagnostics-redaction.md)

### Flat Home Assistant module layout (proposed)

Consolidate 57 root modules into 33 by moving every base entity into `entity.py`, every platform entity into its standard platform module, pure helpers into `data_transforms.py`, dashboard builders into `dashboard_snapshots.py`, and topology helpers into `topology.py`. Keep exactly two subpackages: `coordinators/` and the vendored `api/`. Tracked in [#330](https://github.com/tinkerologie/ha-unifi-insights/issues/330). [ADR-007](./adr/007-flat-home-assistant-module-layout.md)

---

## Future considerations

### Facade coordinator

**Status:** kept

`UnifiFacadeCoordinator` exists so entities and services read one `data` mapping. It is the largest coordinator module after Protect and duplicates some lookups that the specialized coordinators already own. Once ADR-007 lands and entities use declarative `EntityDescription` fields, revisit whether entities can subscribe to their owning coordinator directly.

### Repairs

**Status:** not implemented

The `RepairsFlow` scaffold was never wired to `ir.async_create_issue()` and is removed by #330. Add repair issues (with `issues` entries in `strings.json`) when there is a user-fixable condition to surface, for example an expired API key that reauth cannot recover.

### Discovery

**Status:** not implemented

Consoles are added manually through the user step. Zeroconf, DHCP, and SSDP matchers in `manifest.json` are empty; add them (and a `discovery-update-info` path) only if UniFi consoles can be matched reliably without false positives.

### Move the API client back to `unifi-official-api`

**Status:** planned ([tinkerologie/unifi-official-api#41](https://github.com/tinkerologie/unifi-official-api/issues/41), sequenced after #330)

[ADR-003](./adr/003-vendor-the-unifi-api-client.md) vendored the client so spec fixes could ship without a second release train. Since then the two copies have diverged in both directions: about 6,900 differing lines across shared files, plus an Access client and nine Network endpoint families that exist only in the vendored copy, and a cleaner `endpoints/` + `models/` layout that exists only upstream. Home Assistant's `dependency-transparency` rule and development checklist want device communication in a PyPI library published from CI at a tagged release. The plan is to port the vendored tree (the tested, spec-aligned copy) into the upstream repository, remove the `HomeAssistant` dependency in `protect/talkback.py`, release 2.0.0, then switch `manifest.json` to the requirement and delete `api/` (128 files, about 17,000 lines). That change will be recorded as ADR-008 superseding ADR-003. It is sequenced after #330, which already excludes `api/`; nobody should optimize the vendored tree during the consolidation.

---

## Decision review

Review these decisions when:

- UniFi publishes a new major API version (resolve versions from `https://developer.ui.com/llms.txt`)
- Home Assistant Core changes an Integration Quality Scale rule or deprecates a pattern used here
- A module exceeds roughly 2,000 lines or a package gains a third subpackage
- User feedback suggests an architectural problem rather than a bug
