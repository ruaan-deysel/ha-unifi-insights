# Gemini Instructions

This repository uses a shared AI agent instruction system. **All instructions are in [`AGENTS.md`](AGENTS.md).**

Read `AGENTS.md` completely before starting any work. It contains:

- Project overview and integration identifiers
- Package structure and architectural rules
- Code style, validation commands, and quality expectations
- Home Assistant patterns (config flow, coordinator, entities, services)
- Error recovery strategy and breaking change policy
- Workflow rules (scope management, translations, documentation)

## Quick Reference

- **Domain:** `unifi_insights`
- **Title:** UniFi Insights
- **Class prefix:** `UnifiInsights`
- **Main code:** `custom_components/unifi_insights/`
- **Validate:** `pre-commit run --all-files`
- **Lint:** `scripts/lint` (ruff format + check)
- **Test:** `pytest`
- **Run HA:** `./scripts/develop`

## Path-Specific Instructions

Additional domain-specific guidance is available in `.github/instructions/*.instructions.md`.
These files use `applyTo` globs to indicate which files they cover.
Consult the relevant instruction file when working on specific file types:

- `python.instructions.md` — Python style, async patterns, HA imports
- `entities.instructions.md` — Entity platform patterns, inheritance
- `config_flow.instructions.md` — Config flow, reauth, discovery
- `coordinator.instructions.md` — DataUpdateCoordinator patterns
- `api.instructions.md` — API client, exception hierarchy
- `service_actions.instructions.md` — Service action definitions
- `tests.instructions.md` — Testing patterns and fixtures
- `translations.instructions.md` — Translation file structure
