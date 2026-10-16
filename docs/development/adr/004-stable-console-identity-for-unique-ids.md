# ADR-004: Stable console identity for config entry unique IDs

**Date:** 2026-10-16 (recorded retroactively; consolidated in `console_identity.py` in release 2026.10.2, issue #309)
**Status:** Accepted

## Context

Home Assistant's `unique-config-entry` rule requires each config entry to carry a `unique_id` that identifies the device or service so the same console cannot be added twice. Candidates for a UniFi console are poor:

- The host URL changes with DHCP, DNS, and reverse proxies.
- The API key is a secret and can be rotated.
- The default site id is `default` on every controller.
- Remote (cloud) entries and Carrier Fabric entries have no reachable gateway at all.

Before `console_identity.py` existed, the config flow and `async_setup_entry` derived the identity separately. The flow ignored `is_gateway`, looked only at the first site, and fell back to a host-based id; setup then adopted a MAC the flow could not derive, so `_abort_if_unique_id_configured()` no longer matched and re-adding a console produced a second entry.

Home Assistant 2026.8 made devices belong to exactly one config entry, so device identifiers must also be scoped to the entry that owns them.

## Decision

Resolve the identity once, in one module, for every caller:

| Mode             | `unique_id`                                                                                         |
| ---------------- | --------------------------------------------------------------------------------------------------- |
| `local`          | MAC of the gateway or Cloud Key (`is_gateway`, or a console model token); fallback: Protect NVR MAC |
| `remote`         | Cloud `console_id` from Site Manager                                                                |
| `carrier_fabric` | `carrier_<org_id>`, or `carrier_key_<sha256(api_key)[:16]>` when the organization id is unavailable |

- `console_identity.py` owns `is_console_device()`, `resolve_console_identity()`, and the site-entity identity helpers. The config flow and setup both call it; neither re-implements the logic.
- Logical-site entities carry console-scoped unique IDs and are migrated in place when an older entry is found (`async_restore_site_entity_identities`, `async_rekey_site_entities`).
- Device registry lookups are always entry-scoped (`async_get_device_by_identifier(entry.entry_id, ...)`) and parents use `via_device_id`.

## Alternatives considered

### Option A: Host URL or hostname

- Pros: available before any API call.
- Cons: not stable; the same console behind two hostnames becomes two entries.

### Option B: Hash of the API key

- Pros: unique per credential.
- Cons: rotating a key (a normal reauth) would orphan the entry; keys are secrets and must not become identifiers.

### Option C: Console hardware identity with cloud and organization fallbacks (chosen)

- Pros: survives IP, hostname, and key changes; the same rule serves flow and setup.
- Cons: needs one API round trip during the flow; multi-site controllers must be scanned for the console device.

## Consequences

### Positive

- `unique-config-entry`, `reauthentication-flow`, and `reconfiguration-flow` share one identity check (`_abort_if_unique_id_mismatch()`).
- Replacing a console's IP or key never duplicates entities.

### Negative

- Replacing the physical gateway changes the identity; this is documented as expected behavior.
- The Carrier Fabric key-hash fallback is weaker than an organization id and only exists for keys whose organization cannot be read.

### Neutral

- Any new connection mode must add its rule to `console_identity.py` rather than to the flow.
