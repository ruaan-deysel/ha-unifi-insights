# ADR-005: Bundled dashboard cards with versioned WebSocket contracts

**Date:** 2026-10-16 (recorded retroactively; the topology card shipped in 2026.9.8 and the card family grew through 2026.10)
**Status:** Accepted

## Context

A network topology, site health, performance, Protect status, timeline, and internet activity view need more structure than entity states can carry. Users expect them to work after installing the integration from HACS without adding a second repository, and dashboards are shared with non-admin users, so the payload must not expose raw MAC addresses or credentials.

Home Assistant 2026 frontend conventions use Web Awesome `--ha-*` tokens, `getGridOptions()` for sections views, and `hass.formatEntityName()`.

## Decision

- Card sources live in `frontend/src/` (TypeScript + Lit, Vite build, Vitest and Playwright tests). The six bundles are committed to `custom_components/unifi_insights/frontend/` and served by `frontend.py` through `hass.http.async_register_static_paths` with a `?v=<version>-<hash>` content digest, and registered as Lovelace resources after `frontend` and `lovelace` load (`after_dependencies`).
- Data reaches the cards only through `websocket_api.py`: `unifi_insights/topology/{sources,get,subscribe,node_details}` and `unifi_insights/protect/{sources,get,subscribe}`. Commands are available to any authenticated user.
- Payloads are TypedDict contracts with an explicit schema version (`topology_contract.py` and the dashboard snapshot builders). The frontend mirrors the contract in `frontend/src/contract.ts`; a contract change bumps the version on both sides.
- Topology node ids are HMACs of the MAC under a per-entry secret (`topology_keys.py`), so a dashboard user cannot recover addresses and ids stay stable across restarts.
- Snapshot builders (`site_health.py`, `performance.py`, `timeline.py`, `protect_snapshot.py`, `internet_activity_snapshot.py`) are pure functions over coordinator data with no I/O and no Home Assistant imports, so they are unit-tested without a `hass` fixture. [ADR-007](./007-flat-home-assistant-module-layout.md) merges them into one `dashboard_snapshots.py`.

## Alternatives considered

### Option A: Separate HACS frontend repository

- Pros: smaller integration; independent release cadence.
- Cons: two installs for one feature; version skew between card and WebSocket contract; the integration cannot guarantee the card exists.

### Option B: Expose everything as entity attributes

- Pros: no WebSocket API, works with stock cards.
- Cons: a topology graph does not fit attributes; the recorder would store large blobs every 30 s; raw MACs would leak to every dashboard user.

### Option C: Bundled cards with a versioned WebSocket contract (chosen)

- Pros: one install, one version, one contract, privacy-safe payloads.
- Cons: the integration carries a Node toolchain and built artifacts in git.

## Consequences

### Positive

- `npm run build && npm run size` produces reproducible bundles that CI checks; cache busting means upgrades never serve stale cards.
- Builders are testable in isolation and reusable by the `protect/*` and `topology/*` subscriptions.

### Negative

- Built `*.js` files are committed and show up in diffs; `.prettierignore` excludes them from formatting.
- Any backend field rename must be mirrored in `contract.ts`.

### Neutral

- Cards must follow HA 2026 UI conventions (`--ha-*` tokens, `getGridOptions()`, `prefers-reduced-motion`, ARIA, keyboard focus); `frontend/test/a11y.test.ts` enforces the accessibility part.
