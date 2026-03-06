---
agent: "agent"
tools: ["search/codebase", "edit", "search"]
description: "Create a structured implementation plan for a feature or change"
---

# Create Implementation Plan

Your goal is to create a structured implementation plan before starting a complex feature or change.

If not provided, ask for:

- Feature description and user story
- Scope (which parts of the integration are affected)
- Any constraints or requirements

## Planning Steps

### 1. Research existing code

- Read relevant files to understand current implementation
- Check `const.py` for existing constants and patterns
- Look at similar features for patterns to follow
- Review coordinator data schema for available data

### 2. Create plan in `.ai-scratch/`

Write a temporary plan file (never committed):

```markdown
# Implementation Plan: [Feature Name]

## Goal
[What we're building and why]

## Affected Files
- [ ] `file1.py` — What changes
- [ ] `file2.py` — What changes

## Data Flow
[How data moves through the system]

## Implementation Order
1. [First change — lowest dependency]
2. [Second change — builds on first]
3. [Third change — integrates everything]

## Breaking Changes
[Any impacts on existing users]

## Open Questions
[Things to clarify before starting]
```

### 3. Review with developer

Present the plan and get confirmation before proceeding.

### 4. Execute

Implement changes in the planned order, committing logical units together.
