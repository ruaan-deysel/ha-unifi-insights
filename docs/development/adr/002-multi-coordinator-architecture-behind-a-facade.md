# ADR-002: Multi-coordinator architecture behind a facade

**Date:** 2026-10-16 (recorded retroactively; the architecture dates from the 2026.2 to 2026.3 releases)
**Status:** Accepted

## Context

A UniFi console exposes several applications (Network, Protect, Access, InnerSpace, Site Manager, Mobility) with very different data volatility and cost:

- Device and client metrics change every few seconds and are cheap to list.
- Site configuration (WiFi, networks, firewall, ACL, DNS, vouchers, VPN) is expensive to list across many endpoints and changes rarely.
- Protect pushes device and event updates over a WebSocket and only needs a slow REST poll as a safety net.
- Access delivers results through a signed webhook.
- Site Manager and Mobility are cloud APIs with rate limits and are shared by every entry that uses the same cloud key.

The original design used one `UnifiInsightsDataUpdateCoordinator` (`coordinator.py`) that fetched everything on one interval. Home Assistant's `appropriate-polling` rule asks each data source to poll at a rate that fits it, and `log-when-unavailable` expects one log line per outage per data source.

## Decision

Use one `DataUpdateCoordinator` subclass per data domain, all inheriting `UnifiBaseCoordinator` (`coordinators/base.py`) for shared authentication and connection error mapping, and aggregate them behind a push-only `UnifiFacadeCoordinator`:

| Coordinator                           | Interval         | Notes                                             |
| ------------------------------------- | ---------------- | ------------------------------------------------- |
| `UnifiConfigCoordinator`              | 5 min            | Owns legacy site-name mapping for the entry       |
| `UnifiDeviceCoordinator`              | 30 s             | Device and client metrics                         |
| `UnifiProtectCoordinator`             | 30 s + WebSocket | WebSocket is primary; poll is the fallback        |
| `UnifiInsightsAccessCoordinator`      | 30 s + webhook   | Optional, only when an Access token is configured |
| `UnifiInsightsInnerSpaceCoordinator`  | 5 min            | Optional                                          |
| `UnifiInsightsSiteManagerCoordinator` | 10 min           | Shared per cloud key across remote entries        |
| `UnifiInsightsMobilityCoordinator`    | 5 min, 1 h idle  | Only the remote entry that owns the cloud key     |
| `UnifiCarrierFabricCoordinator`       | 5 min            | Standalone `carrier_fabric` entries               |
| `UnifiFacadeCoordinator`              | none             | Subscribes to the others and fans out one update  |

Coordinators live in the `coordinators/` package rather than a single `coordinator.py`. Entities read `coordinator.data` on the facade and never call a client directly. Runtime handles live in `entry.runtime_data` (`UnifiInsightsData`).

## Alternatives considered

### Option A: One coordinator, one interval

- Pros: matches the `common-modules` example; simplest wiring.
- Cons: forces the expensive configuration listing onto the 30 s path or starves metrics; one outage marks every entity unavailable; one log line cannot say which application failed.

### Option B: Per-domain coordinators, entities subscribe directly (no facade)

- Pros: no aggregation layer; each entity has one owner.
- Cons: at the time of the split, every entity and service read a single `coordinator.data` shape; rewriting them all at once was not feasible without breaking `unique_id` and attribute contracts.

### Option C: Per-domain coordinators behind a facade (chosen)

- Pros: correct polling per domain, isolated failure and recovery logging, entities unchanged.
- Cons: an extra aggregation step on every update; the facade can grow into a second data model.

## Consequences

### Positive

- `appropriate-polling` and `log-when-unavailable` hold per application.
- Optional applications (Protect, Access, InnerSpace, Mobility) simply have no coordinator when the probe says they are absent; no entity is created in an unavailable state.

### Negative

- The facade (`coordinators/facade.py`) is 1,600 lines and the Protect coordinator is 3,000 lines; [ADR-007](./007-flat-home-assistant-module-layout.md) splits Protect and [DECISIONS.md](../DECISIONS.md) lists the facade as a future consideration.
- Helper modules without a `DataUpdateCoordinator` accumulated inside `coordinators/`; ADR-007 moves them out.

### Neutral

- `coordinators/` is a deliberate deviation from the single `coordinator.py` in the `common-modules` rule. Home Assistant Core's `unifi` integration uses a `hub/` subpackage for the same reason.
