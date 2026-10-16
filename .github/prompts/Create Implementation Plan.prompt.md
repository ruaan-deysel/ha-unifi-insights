---
agent: "agent"
tools: ["search/codebase", "edit", "search"]
description: "Create a structured implementation plan for a feature or change"
---

# Create Implementation Plan

Your goal is to create a structured implementation plan before starting a complex feature or refactoring, aligned with the repository's Mandatory Development Workflow and Home Assistant 2026.10+ Integration Quality Scale rules.

If not provided, ask for:

- GitHub Issue number (required before writing code)
- Feature description and user story
- Scope (which UniFi applications, coordinators, platforms, or frontend cards are affected)
- Any constraints or backwards-compatibility considerations

## Planning Steps

### 1. Research existing code and specs

- Read relevant integration files and check `const.py`
- Verify API schemas against `https://developer.ui.com/llms.txt` and `https://developer.ui.com/{service}/{version}/openapi.json`
- Check applicable Home Assistant Integration Quality Scale rules (Bronze → Platinum) and HA 2026.8–2026.11 deprecations (`via_device_id`, `DeviceEntry.config_entry_id`, `async_entity_id_changed`, `probatio`)

### 2. Draft plan in `.ai-scratch/`

Write a temporary plan file in `.ai-scratch/` (never committed to git):

```markdown
# Implementation Plan: [Feature Name] (Issue #NNN)

## Goal

[What we are building and why]

## Affected Files

- [ ] `custom_components/unifi_insights/...` — Description of change
- [ ] `tests/test_...` — Unit tests (≥95% branch coverage per file)

## Data Flow & Quality Scale Compliance

- **Data flow:** API Client → Coordinator (`entry.runtime_data`) → Entity / Service / Frontend Card
- **IQS & HA 2026.10+ rules:** (`has-entity-name`, `entity-translations`, `exception-translations`, `icon-translations`, `via_device_id`, `strict-typing`, etc.)

## Implementation Order

1. API models / `data_transforms.py`
2. Coordinator / `probe.py`
3. Entities / Services / Frontend cards
4. `strings.json`, `translations/en.json`, `icons.json`
5. Unit tests (`≥95%` per-file coverage) and `CHANGELOG.md`

## Breaking Changes

[Any impact on entity IDs, unique IDs, config entries, or service schemas]
```

### 3. Review with developer and execute

Present the plan for confirmation, then implement on a dedicated `feat/<issue-id>-...` or `fix/<issue-id>-...` branch.
