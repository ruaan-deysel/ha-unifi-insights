---
agent: "agent"
tools: ["search/codebase", "edit", "search"]
description: "Create an Architecture Decision Record for a significant design choice"
---

# Create ADR (Architecture Decision Record)

Your goal is to document a significant architectural or design decision for the UniFi Insights integration.

If not provided, ask for:

- What decision was made
- What alternatives were considered
- Why this option was chosen
- What trade-offs exist

## ADR Template

Write the ADR in `.ai-scratch/` first for review, then move to `docs/development/` if the developer approves.

```markdown
# ADR-NNN: [Decision Title]

**Date:** YYYY-MM-DD
**Status:** Accepted | Proposed | Deprecated | Superseded

## Context

[What is the issue we're facing? What constraints exist?]

## Decision

[What did we decide to do?]

## Alternatives Considered

### Option A: [Name]
- Pros: ...
- Cons: ...

### Option B: [Name]
- Pros: ...
- Cons: ...

## Consequences

### Positive
- ...

### Negative
- ...

### Neutral
- ...
```

## Existing Decisions to Reference

- Multi-coordinator architecture (config/device/protect/facade)
- `unifi-official-api` as sole dependency (no custom HTTP client)
- Calendar versioning (YYYY.MM.PATCH)
- camelCase tolerance via `get_field()`
- WebSocket for Protect, polling for Network
