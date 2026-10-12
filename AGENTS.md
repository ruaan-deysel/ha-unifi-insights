# AI Agent Instructions

## Mandatory Development Workflow for AI Agents

All AI coding assistants (Claude Code, Gemini, GitHub Copilot, Cursor, Roo, Devin, etc.) MUST strictly adhere to the following workflow when working on this repository:

1. Issue-First Requirement: Never start writing code or creating pull requests without an existing GitHub Issue.
2. Issue Template: Issues must be created using the official Issue Forms (`01-bug-report.yml` for bugs or `02-enhancement-request.yml` for enhancements).
3. CodeRabbit AI Plan: Every issue must have a generated Coding Plan from CodeRabbit AI (`@coderabbitai plan`). AI agents must read and implement strictly according to the approved plan.
4. Branch Discipline: Always create and work on a dedicated branch (`feat/<issue-id>-<description>` or `fix/<issue-id>-<description>`). NEVER commit directly to `main`.
5. Documentation & Changelog: Update `CHANGELOG.md` under `## [Unreleased]` for any user-facing or architectural changes.
6. Local Verification: Run all test, lint, format, and typecheck commands locally before committing. All tests must pass with zero errors and zero warnings.
7. PR Template Completion: Always use `.github/pull_request_template.md`. Complete all fields, link the issue using `Closes #<id>` or `Fixes #<id>` when the PR fully resolves it, or `Part of #<id>` for partial work (only maintainers with write access may write `None`, for housekeeping), and check all Pre-Submission Governance boxes with real terminal output.
8. Draft PR First: ALWAYS open pull requests as DRAFT (`gh pr create --draft`).
9. CI Verification: Wait for CI workflows to run on the draft PR and verify that all status checks pass.
10. Ready for Review: Only mark the PR as ready for review (`gh pr ready`) once all checks pass and all due diligence is verified.
11. Review Clearance: Review and resolve all CodeRabbit AI and GitHub Copilot comments. Ensure Codecov reports show zero errors, zero warnings, and no coverage drop.


This document provides guidance for AI coding agents working on this Home Assistant custom integration project.

## Project Overview

This is **UniFi Insights**, a Home Assistant custom integration that provides monitoring and control of UniFi network infrastructure using the UniFi Network and Protect APIs.

**Integration details:**

- **Domain:** `unifi_insights`
- **Title:** UniFi Insights
- **Class prefix:** `UnifiInsights`
- **Repository:** tinkerologie/ha-unifi-insights

**Key directories:**

- `custom_components/unifi_insights/` — Main integration code
- `custom_components/unifi_insights/coordinators/` — Multi-coordinator system
- `config/` — Home Assistant configuration for local testing
- `tests/` — Unit and integration tests
- `script/` — Development and validation scripts

**Local Home Assistant instance:**

**Use the project's scripts whenever available** (`./script/develop`, `./script/lint`, `./script/setup/bootstrap`). For checks that do not have a wrapper script, use the documented commands (`pre-commit run --all-files`, `mypy`, `pytest`).

**Start Home Assistant:**

```bash
./script/develop
```

**Force restart (when HA is unresponsive or port conflicts):**

```bash
pkill -f "hass --config" || true && ./script/develop
```

**When to restart:** After modifying Python files, `manifest.json`, `services.yaml`, translations, or config flow changes.

**Reading logs:**

- Live: Terminal where `./script/develop` runs
- File: `config/home-assistant.log` (most recent), `config/home-assistant.log.1` (previous)

**Adjusting log levels:**

- Integration logs: `custom_components.unifi_insights: debug` in `config/configuration.yaml`
- Restart HA after changes

**Context-specific instructions:**

If you're using GitHub Copilot, path-specific instructions in `.github/instructions/*.instructions.md` provide additional guidance for specific file types. This document serves as the primary reference for all agents.

**Other agent entry points:**

- **Claude Code:** See [`CLAUDE.md`](CLAUDE.md) (pointer to this file)
- **Gemini:** See [`GEMINI.md`](GEMINI.md) (pointer to this file)
- **GitHub Copilot:** See [`.github/copilot-instructions.md`](.github/copilot-instructions.md) (compact version of this file)

## Working With Developers

**For workflow basics (small changes, translations, tests, session management):** See `.github/copilot-instructions.md` for quick-reference guidance.

### When Instructions Conflict With Requests

If a developer requests something that contradicts these instructions:

1. **Clarify the intent** — Ask if they want to deviate from the documented guidelines
2. **Confirm understanding** — Restate what you understood to avoid misinterpretation
3. **Suggest instruction updates** — If this represents a permanent change, offer to update these instructions
4. **Proceed once confirmed** — Follow the developer's explicit direction after clarification

### Maintaining These Instructions

- Refine guidelines based on actual project needs
- Remove outdated rules that no longer apply
- Consolidate redundant sections to prevent bloat

**Propose updates when:**

- You notice repeated deviations from documented patterns
- Instructions become outdated or contradict actual code
- New patterns emerge that should be standardized

### Documentation vs. Instructions

**Three types of content with clear separation:**

1. **Agent Instructions** — How AI should write code (`.github/instructions/`, `AGENTS.md`)
2. **Developer Documentation** — Architecture and design decisions (`docs/`)
3. **User Documentation** — End-user guides (`README.md`)

**AI Planning:** Use `.ai-scratch/` for temporary notes (never committed)

**Rules:**

- NEVER create random markdown files in code directories
- NEVER create documentation in `.github/` unless it's a GitHub-specified file
- ALWAYS ask first before creating permanent documentation
- Prefer module docstrings over separate markdown files

### Session and Context Management

**Commit suggestions:**

When a task completes and the developer moves to a new topic, suggest committing changes. Offer a commit message based on the work done.

**Commit message format:** Follow [Conventional Commits](https://www.conventionalcommits.org/) specification

**Common types:** `feat:`, `fix:`, `chore:`, `refactor:`, `docs:`, `test:`

## Custom Integration Flexibility

**This is a CUSTOM integration, not a Home Assistant Core integration.** While we follow Core patterns for quality and maintainability, we have more flexibility in implementation decisions.

**Vendored API package:**

- The upstream `unifi-official-api` project is vendored locally under `custom_components/unifi_insights/api`
- Reuse its client methods (`network_client`/`protect_client`) rather than manual HTTP calls
- NEVER create a custom API client — extend or reuse the vendored package instead

**Quality Scale requirements (strict):**

As an AI agent, **strictly follow the current Home Assistant Integration Quality Scale rules** for every applicable change:

- Canonical rules: <https://developers.home-assistant.io/docs/core/integration-quality-scale/rules>
- Treat applicable rules as mandatory, not aspirational
- Validate changed behavior against applicable rules before considering work complete
- If a rule is not applicable, call that out briefly in the final summary
- If a request conflicts with a rule, explicitly flag the conflict and ask for direction

**Developer expectation:** Generate production-ready code that meets HA standards and applicable Quality Scale rules.

## Code Style and Quality

**Python:** 4 spaces, 88 char lines, double quotes, full type hints, async for all I/O

**YAML:** 2 spaces, modern HA syntax (no legacy `platform:` style)

**JSON:** 2 spaces, no trailing commas, no comments

**Validation:** Run these before committing:

```bash
# Run all pre-commit hooks (ruff format + check, codespell, yamllint, mypy)
pre-commit run --all-files

# Or individually:
ruff check .          # Linting
ruff format .         # Formatting
mypy custom_components/unifi_insights   # Type checking
pytest                # Tests (95% total coverage enforced locally)
```

**Shortcut scripts:**

```bash
script/lint           # Ruff format + check --fix
```

**For comprehensive standards, see:**

- `.github/instructions/python.instructions.md` — Python patterns, imports, type hints
- `.github/instructions/yaml.instructions.md` — YAML structure and HA-specific patterns
- `.github/instructions/json.instructions.md` — JSON formatting and schema validation

## Project-Specific Rules

### Integration Identifiers

This integration uses the following identifiers consistently:

- **Domain:** `unifi_insights`
- **Title:** UniFi Insights
- **Class prefix:** `UnifiInsights`

**When creating new files:**

- Use the domain `unifi_insights` for all DOMAIN references
- Prefix all integration-specific classes with `UnifiInsights`
- Use "UniFi Insights" as the display title
- Never hardcode different values

### Integration Structure

**Package organization:**

- `coordinators/` — Multi-coordinator system (base, config, device, protect, facade)
- `config_flow.py` — Config flow (local and remote modes)
- `entity.py` — Base entity classes (`UnifiInsightsEntity`, `UnifiProtectEntity`)
- `data_transforms.py` — API response to internal data mapping
- `services.py` — Service action implementations
- `services.yaml` — Service schema definitions
- `const.py` — Constants and endpoint paths
- `diagnostics.py` — Diagnostic data export
- `repairs.py` — Repair flows
- Platform files: `sensor.py`, `binary_sensor.py`, `switch.py`, `button.py`, `device_tracker.py`, `camera.py`, `light.py`, `number.py`, `select.py`, `event.py`, `update.py`

**Do NOT create:**

- `helpers/`, `ha_helpers/`, or similar packages — use existing modules
- `common/`, `shared/`, `lib/` — use existing modules
- New top-level packages without explicit approval

**Key patterns:**

- Entities → Coordinator → API Client (never skip layers)
- Use `EntityDescription` dataclasses for static entity metadata
- Use `get_field()` for mixed camelCase/snake_case field access
- `PARALLEL_UPDATES = 0` for coordinator-driven entities, `1` for action-based Protect entities

**Code organization principles:**

- Keep files focused (200-400 lines per file)
- One class per file for entity implementations where practical
- Split large modules into smaller ones when needed

### Multi-Coordinator Architecture

The integration uses a multi-coordinator pattern:

- **Config Coordinator** (`coordinators/config.py`) — Site and configuration data (minimal polling)
- **Device Coordinator** (`coordinators/device.py`) — Network device metrics
- **Protect Coordinator** (`coordinators/protect.py`) — Camera, light, sensor, NVR data (WebSocket + polling)
- **Facade Coordinator** (`coordinators/facade.py`) — Unified view for backward compatibility
- **Base Coordinator** (`coordinators/base.py`) — Abstract base with common patterns

**Data flow:**

```
UniFi Network API → Network Client ↘
UniFi Protect API → Protect Client → Config Coordinator → Device Coordinator → Protect Coordinator → Facade → Entities
```

### Device Info

All entities should provide consistent device info via the base entity class (manufacturer, model, serial number, configuration URL, firmware version). Use the base classes in `entity.py`.

### Integration Manifest

**Key fields in `manifest.json`:**

- `integration_type: "hub"` — Gateway to multiple devices
- `iot_class: "local_polling"` — Local polling with WebSocket for Protect
- `dependencies: ["ffmpeg", "stream"]` — Required for camera support
- `ssdp` — Discovery matchers for UniFi Dream Machine variants

The API client package is vendored in-repo under `custom_components/unifi_insights/api`; do not re-add `unifi-official-api` to `manifest.json` requirements.

### Config Flow

The integration supports two connection modes:

- **Local** — Host URL + API key (+ optional verify_ssl)
- **Remote** — Console ID + API key

**Unique ID:** Based on API key

**Flows:** User setup, reauth, reconfigure

### Entity Base Classes

Two base classes in `entity.py`:

- **`UnifiInsightsEntity`** — Network devices; availability via `is_device_online` helper
- **`UnifiProtectEntity`** — Protect devices; availability via `state == CONNECTED`

Both handle camelCase/snake_case field mapping via `get_field()`.

## Home Assistant Patterns

**Config flow:**

- Implemented in `config_flow.py`
- Support user setup, reauth, reconfigure
- Always set unique_id for entries
- Validates connectivity by fetching sites

See `.github/instructions/config_flow.instructions.md` for comprehensive patterns.

**Service actions:**

- Defined in `services.yaml` with full descriptions
- Implemented in `services.py`
- Includes: refresh data, restart device, Protect controls (recording/HDR/video mode, mic, light, PTZ, chime), Network actions (authorize guest, voucher CRUD)
- Use `_get_protect_coordinator`/`_get_first_coordinator` helpers
- Raise `HomeAssistantError` with user-facing messages

See `.github/instructions/service_actions.instructions.md` for service patterns.

**Coordinator:**

- Entities → Coordinator → API Client (never skip layers)
- Raise `ConfigEntryAuthFailed` (triggers reauth) or `UpdateFailed` (retry)
- Use `async_config_entry_first_refresh()` for first update

See `.github/instructions/coordinator.instructions.md` for details.

**Entities:**

- Inherit from platform base + `UnifiInsightsEntity` or `UnifiProtectEntity`
- Read from `coordinator.data`, never call API directly
- Use `EntityDescription` for static metadata

See `.github/instructions/entities.instructions.md` for entity patterns.

**Repairs:**

- Implemented in `repairs.py`
- Use `async_create_issue()` with severity levels
- Implement `RepairsFlow` for guided user fixes

See `.github/instructions/repairs.instructions.md` for comprehensive patterns.

**Entity availability:**

- Set `_attr_available = False` when device is unreachable
- Update availability based on coordinator success/failure
- Don't raise exceptions from `@property` methods

**State updates:**

- Use `self.async_write_ha_state()` for immediate updates
- Let coordinator handle periodic updates
- Minimize API calls (batch requests when possible)

**Setup failure handling:**

- `ConfigEntryNotReady` — Device offline/timeout, auto-retry, don't log manually
- `ConfigEntryAuthFailed` — Expired credentials, triggers reauth flow

**Diagnostics:**

- **CRITICAL:** Use `async_redact_data()` to remove sensitive data
- Redact: Passwords, API keys, tokens, location data, personal information

## Validation and Testing

**Before committing, run:**

```bash
pre-commit run --all-files   # Full validation
script/lint                   # Auto-format and fix linting
pytest                        # Run unit tests (95% total coverage enforced locally)
cd frontend && npm ci          # Topology card: install (Node 22)
npm run lint && npm run typecheck && npm test -- --coverage
npm run build                  # Rebuild custom_components/unifi_insights/frontend/topology-card.js — commit it
```

**Generate code that passes these checks on first run.** As an AI agent, you should produce higher quality code than manual development:

- Type hints are trivial for you to generate
- Async patterns are well-known to you
- Import management is automatic for you
- Naming conventions can be applied consistently

Aim for zero validation errors in generated code.

### Error Recovery Strategy

**When validation fails:**

1. **First attempt** — Fix the specific error reported by the tool
2. **Second attempt** — If it fails again, reconsider your approach
3. **Third attempt** — If still failing, ask for clarification rather than looping indefinitely
4. **After 3 failed attempts** — Stop and explain what you tried and why it's not working

**When gathering context:**

- Start with search (1-2 queries maximum)
- Read 3-5 most relevant files based on results
- If still unclear, read 2-3 more specific files
- **After ~10 file reads, you should have enough context** — make a decision or ask for clarification
- Don't fall into infinite research loops

## Testing

**Test structure:**

- `tests/` mirrors `custom_components/unifi_insights/` structure
- Use fixtures for common setup (Home Assistant mock, coordinator, etc.)
- Mock external API calls
- Every module, including the vendored `api/` client, must be ≥95% (branch coverage enabled, checked per file in CI with `python script/check_coverage_per_file.py coverage.xml --fail-under 95`)

Local `pytest` enforces only the 95% total coverage threshold. To check per-file coverage locally, run `pytest --cov-report=xml`, then `python script/check_coverage_per_file.py coverage.xml --fail-under 95`.

**Running tests:**

```bash
pytest                       # All tests with coverage
pytest tests/test_sensor.py  # Specific test file
pytest -vvs                  # Verbose output
pytest --no-cov              # Without coverage
```

**Important:** Add or update tests whenever your change affects behavior that should be covered by applicable Quality Scale rules (for example config flow, coordinator updates, entities, services, or error handling paths). If you intentionally defer test work, state the gap and rationale.

See `.github/instructions/tests.instructions.md` for comprehensive testing patterns.

## Breaking Changes

**Always warn the developer before making changes that:**

- Change entity IDs or unique IDs (users' automations will break)
- Modify config entry data structure (existing installations will fail)
- Change state values or attributes format (dashboards and automations affected)
- Alter service call signatures (user scripts will break)
- Remove or rename config options (users must reconfigure)

**Never do without explicit approval:**

- Removing config options (even if "unused")
- Changing service parameters or return values
- Modifying how data is stored in config entries
- Renaming entities or changing their device classes
- Changing unique_id generation logic

**How to warn:**

> "This change will modify the entity ID format from `sensor.device_name` to `sensor.device_name_sensor`. Existing users' automations and dashboards will break. Should I proceed, or would you prefer a migration path?"

**When breaking changes are necessary:**

- Document the breaking change in commit message (`BREAKING CHANGE:` footer)
- Consider providing migration instructions
- Suggest version bump
- Update CHANGELOG.md

## File Changes

**Scope Management:**

**Single logical feature or fix:**

- Implement completely even if it spans 5-8 files
- Example: New sensor needs entity class + platform init + translations → implement all together

**Multiple independent features:**

- Implement one at a time
- After completing each feature, suggest committing before proceeding to the next

**Large refactoring (>10 files or architectural changes):**

- Propose a plan first before starting implementation
- Get explicit confirmation from developer

**Translation strategy:**

- Use placeholders in code — functionality works without translations
- Update `strings.json` only when asked or at major feature completion
- NEVER update other language files automatically
- Priority: Business logic first, translations later

## UniFi-Specific Considerations

- **UniFi Developer Portal:** Consult [developer.ui.com](https://developer.ui.com/) for official UniFi API documentation, endpoint specifications, and latest developer capabilities
- **Machine-readable API references (use these, not the HTML docs):** the portal's documentation pages are JavaScript-rendered, so a plain HTTP fetch returns an empty app shell — an agent gets HTTP 200 and no API content. These endpoints return real content and are the ones to fetch:
  - `https://developer.ui.com/llms.txt` — root index: which APIs exist and their current versions
  - `https://developer.ui.com/{service}/{version}/llms.txt` — full endpoint list for one service
  - `https://developer.ui.com/{service}/{version}/openapi.json` — request/response schemas
  - `https://developer.ui.com/network/v10.4.57/ai-gettingstarted.md` — agent-oriented onboarding for the Network API
  - Current versions as of 2026-09-16: Network `v10.4.57`, Protect `v7.3.53`, Site Manager `v1.0.0`. Resolve versions from the root index rather than hardcoding them.
- **API Rate Limiting:** Be mindful of UniFi controller API rate limits when setting polling intervals
- **Device Discovery:** Handle dynamic device discovery as UniFi networks can change
- **Connection Resilience:** UniFi controllers may restart or become temporarily unavailable
- **Multiple Sites:** Support for multi-site UniFi deployments where applicable
- **Protect Integration:** Camera entities should handle UniFi Protect separately from network devices
- **camelCase Tolerance:** UniFi API uses camelCase; use `get_field()` for field access
- **Data Transforms:** Extend `data_transforms.py` when adding new API fields

## Tool Parallelization

**Safe to call in parallel:**

- Multiple file read operations (different files)
- File search + file read + content search (independent read-only operations)

**Never call in parallel:**

- Multiple terminal commands (execute sequentially, wait for output)
- Multiple edits on the same file

**Best practices:**

- Batch independent read operations together
- After gathering context in parallel, provide brief progress update before proceeding
- Terminal commands must always be sequential

## Additional Resources

- [UniFi Developer Portal](https://developer.ui.com/) — Official UniFi API documentation and developer resources
- [UniFi API root index (`llms.txt`)](https://developer.ui.com/llms.txt) — machine-readable list of APIs and versions; the HTML pages are JS-rendered and unreadable to agents
- [UniFi Network AI onboarding](https://developer.ui.com/network/v10.4.57/ai-gettingstarted.md) — agent-oriented Network API primer
- [UniFi Protect OpenAPI spec](https://developer.ui.com/protect/v7.3.53/openapi.json) — authoritative sensor/camera schemas
- [Home Assistant Developer Docs](https://developers.home-assistant.io/) — Primary reference
- [Integration Quality Scale Rules](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules)
- [Architecture Docs](https://developers.home-assistant.io/docs/architecture_index)
- [Ruff Rules](https://docs.astral.sh/ruff/rules/) — Linter documentation
- [pytest Documentation](https://docs.pytest.org/) — Testing framework
- See `CONTRIBUTING.md` for contribution guidelines

## Issue and Pull Request Governance

These rules apply to every contributor, including AI coding agents. The full org-wide rules are in
[GOVERNANCE.md](https://github.com/tinkerologie/.github/blob/main/GOVERNANCE.md).

1. **Issue first.** Open an issue with the bug or enhancement template before opening a pull
   request. Keep the title prefix `[Bug]:` or `[Enhancement]:`, followed by a space and the title.
   Automation applies the `bug` or `enhancement` label when it can tell the type, and CodeRabbit
   then posts a Coding Plan on the issue. Implement from that plan. The labeler skips issues labeled
   `question`, `duplicate`, `invalid`, `wontfix`, or `no-type`, and never re-adds a type label that
   a maintainer removed.
2. **Link the issue.** In the PR's **Related Issues** section, write `Closes #<number>` (or `Fixes`
   or `Resolves`) when the PR completely resolves the issue; these keywords close it on merge. Use
   `Part of #<number>` or `Related to #<number>` for partial work. The linked issue must exist; an
   issue in another public repository (`owner/repo#123`) is fine. Only authors with write access or
   higher (maintainers) may write `None`, for housekeeping such as CI,
   documentation, or dependency updates; PR governance rejects `None` from everyone else.
3. **One change at a time.** Contributors without write access can have at most 2 open, non-draft
   pull requests here. GitHub enforces this limit, and draft pull requests do not count toward it.
   Do not open PRs that edit the same files as another open PR, such as `CHANGELOG.md`,
   translations, `README.md`, or generated bundles. Wait for the first to merge, rebase, then
   continue.
4. **Rebase before review.** Rebase on `main` before marking a PR ready for review.
5. **Resolve conflicts first.** When a PR gets the `conflicts` label, rebase on `main`,
   resolve the conflicts (keep every `CHANGELOG.md` entry under `[Unreleased]`), re-run the tests,
   and force-push before doing any other work.
6. **Coverage.** `codecov/patch` must pass: at least 90% of added or changed lines must be
   covered by tests. The gate is the percentage; still, add tests for the uncovered lines the
   Codecov PR comment lists, and explain in the PR description any line you leave uncovered. Do
   not lower coverage targets or add coverage ignore rules to make it pass.
7. **Stale items.** Issues and PRs with no activity for 14 days are labeled `stale` and closed 30
   days later unless there is new activity. These labels are exempt:
   - Issues: `pinned`, `security`, `confirmed`, `work-in-progress`, `priority: critical`, `priority: high`.
   - Pull requests: `pinned`, `security`, `work-in-progress`.
