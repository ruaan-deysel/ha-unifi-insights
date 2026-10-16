# ADR-006: Three-layer diagnostics redaction

**Date:** 2026-10-16 (recorded retroactively)
**Status:** Accepted

## Context

The `diagnostics` Quality Scale rule asks integrations to export a redacted dump of the config entry and runtime data for bug reports. UniFi data is unusually sensitive: API keys and Access tokens, WiFi passphrases, client hostnames and user names, door user records, and MAC addresses that identify households. Users attach diagnostics to public GitHub issues.

A single `TO_REDACT` set is the Home Assistant default (`async_redact_data`), but it only covers fields whose key is known in advance. UniFi responses mix camelCase and snake_case and gain fields with every controller release.

## Decision

Redact in three passes over the whole payload, in this order:

1. **Secrets** (`TO_REDACT`): API keys, tokens, passwords, passphrases, webhook secrets, session cookies, and known identifier keys in both key styles.
2. **Personal data** (`CLIENT_TO_REDACT = TO_REDACT | PERSONAL_NAMES` for clients and Access users; `WIFI_TO_REDACT = TO_REDACT | {"name"}` for WiFi networks): hostnames, user names, SSIDs.
3. **MAC anonymization** (`_anonymize_macs()`): every MAC-shaped string anywhere in the payload is replaced by a stable pseudonym, so relationships (uplinks, port assignments, client-to-AP) survive but the real address does not.

New fields are safe by default because passes 1 and 3 run on the entire structure, not on a hand-maintained path list. Every diagnostics change must keep the three passes; this is called out as `CRITICAL` in `AGENTS.md` and `.github/instructions/diagnostics.instructions.md`.

## Alternatives considered

### Option A: One `TO_REDACT` set

- Pros: the Home Assistant default; simplest.
- Cons: misses MAC values stored under arbitrary keys and personal names under feature-specific keys.

### Option B: Allow-list only the fields needed for support

- Pros: nothing leaks that was not chosen.
- Cons: every new feature needs a diagnostics update, and bug reports for unexpected fields have no data.

### Option C: Three passes over the whole payload (chosen)

- Pros: safe by default, keeps topology relationships, no path list to maintain.
- Cons: MAC detection is heuristic; the pseudonym map must be consistent within one export.

## Consequences

### Positive

- Diagnostics can be attached to public issues without manual editing.
- Tests assert that no raw MAC or secret survives, which also guards new modules.

### Negative

- Pseudonymized MACs cannot be matched against a user's controller by the maintainer without the user's help.

### Neutral

- Per-feature diagnostics tests (`test_access_diagnostics.py`, `test_mobility_diagnostics.py`, `test_carrier_fabric_diagnostics.py`) exist because each feature adds its own personal-data keys.
