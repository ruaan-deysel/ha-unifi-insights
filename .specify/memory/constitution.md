# UniFi Insights Integration Constitution

## Core Principles

### I. Home Assistant First

Every feature must align with Home Assistant's integration quality scale and best practices:

- Follow the [Home Assistant Integration Quality Scale](https://developers.home-assistant.io/docs/integration_quality_scale_index/)
- Adhere to HA entity naming conventions and device classes
- Use config flows for setup (no YAML configuration)
- Implement proper coordinator patterns for data updates
- Support HA's built-in diagnostics and debugging capabilities
- **Non-negotiable**: Must pass `hassfest` validation before any release

### II. API Abstraction Layer

Clean separation between UniFi Network API and Home Assistant entities:

- All UniFi API calls isolated in dedicated client modules
- Entities consume data through coordinator, never call API directly
- API client must be independently testable without HA
- Changes to UniFi API structure don't cascade to entity layer
- Support for both local and cloud UniFi controllers
- Handle API rate limiting and connection resilience gracefully

### III. Test-First Development (NON-NEGOTIABLE)

TDD mandatory for all features and bug fixes:

- **Red**: Write failing test first (unit or integration)
- **Green**: Implement minimal code to pass test
- **Refactor**: Clean up while keeping tests green
- No PR merges without corresponding tests
- Critical paths require both unit and integration tests:
  - Config flow validation
  - API authentication and error handling
  - Coordinator update cycles
  - Entity state updates
  - Service call execution

### IV. User-Centric Design

Every user interaction must be intuitive and helpful:

- Clear, descriptive entity names (no cryptic abbreviations)
- Sensible default update intervals (balance freshness vs. API load)
- Helpful error messages that guide users to solutions
- Config flow includes validation with actionable feedback
- Device grouping follows UniFi site structure
- Services include clear descriptions and examples
- **Golden Rule**: If it requires looking at code to understand, it's not user-centric

### V. Defensive Reliability

Assume everything can and will fail:

- Graceful degradation when UniFi controller unavailable
- Entity availability reflects actual device/API state
- No crashes on malformed API responses
- Retry logic with exponential backoff for transient failures
- Config flow handles network issues without confusing users
- Clear distinction between temporary vs. permanent failures
- **Principle**: Users should never see Python tracebacks in their logs

### VI. Versioning & Release Discipline

Semantic versioning with Home Assistant compatibility:

- **Format**: `YYYY.MM.PATCH` (aligns with HA release calendar)
- **Breaking changes**: Must include migration path in release notes
- **Deprecations**: Warn in logs for 2 releases before removal
- **Changelogs**: User-focused (what changed, why it matters, what to do)
- **Minimum HA version**: Clearly documented, tested, enforced in manifest
- **HACS compliance**: Validate with HACS action before release

### VII. Code Quality & Maintainability

High standards for readability and sustainability:

- Type hints required for all functions and methods
- Docstrings for all public APIs (Google style)
- Ruff + Pylint compliance mandatory (no exceptions without justification)
- Maximum function complexity: 10 (measured by cyclomatic complexity)
- Code coverage minimum: 80% overall, 95% for critical paths
- **Principle**: Code is read 10x more than written; optimize for readers

## Architecture Constraints

### Entity Structure

```
Platform        | Purpose                    | Update Source
----------------|----------------------------|------------------
binary_sensor   | Device online/offline      | Coordinator poll
sensor          | Metrics (CPU, memory, etc) | Coordinator poll
switch          | Device restart control     | Service call + state
```

### Data Flow Pattern

```
UniFi API → API Client → Coordinator → Entities
              ↑              ↑            ↑
         (isolated)    (poll/push)   (consume)
```

### Coordinator Responsibilities

- Single source of truth for UniFi data
- Handles update intervals (default: 30s, configurable: 10s-300s)
- Implements exponential backoff on failures
- Provides async context for all entities
- Manages API session lifecycle

### Configuration Management

- **Config Flow**: All user setup (host, API key, site selection)
- **Options Flow**: Update interval, monitored device filters
- **Storage**: Encrypted credentials via config entries
- **No YAML**: Integration must work without configuration.yaml edits

## Code Quality Standards

### Python Style

- **Formatter**: Ruff (line length: 100)
- **Linter**: Ruff + Pylint (strict mode)
- **Type Checker**: mypy in strict mode (phased adoption)
- **Import Order**: stdlib → third-party → homeassistant → local
- **Naming**:
  - Classes: `PascalCase`
  - Functions/methods: `snake_case`
  - Constants: `UPPER_SNAKE_CASE`
  - Private: `_leading_underscore`

### Documentation Requirements

- **README**: Quick start, features, screenshots, troubleshooting
- **CONTRIBUTING**: Setup, testing, PR guidelines
- **Code comments**: Why, not what (code should explain what)
- **API docs**: All public methods with examples
- **Inline comments**: Only for non-obvious logic or gotchas

### Testing Standards

```python
# Required test structure
tests/
├── __init__.py
├── conftest.py           # Fixtures for HA test harness
├── test_config_flow.py   # Setup and options flows
├── test_coordinator.py   # Data update logic
├── test_api_client.py    # UniFi API interactions (mocked)
├── test_binary_sensor.py # Entity state and attributes
├── test_sensor.py        # Entity state and attributes
└── test_switch.py        # Service calls and state changes
```

### Git Workflow

- **Branch naming**: `feature/description`, `fix/issue-number`, `docs/topic`
- **Commits**: Conventional Commits format
  - `feat:` - New features
  - `fix:` - Bug fixes
  - `docs:` - Documentation only
  - `test:` - Test additions/changes
  - `refactor:` - Code changes without behavior change
  - `chore:` - Maintenance (deps, config, etc)
- **PR requirements**:
  - All CI checks pass (hassfest, pytest, ruff, pylint)
  - Code coverage doesn't decrease
  - Changelog entry added
  - Breaking changes documented

## Development Workflow

### Feature Development Cycle

1. **Issue Creation**: Describe problem/feature with user impact
2. **Design Discussion**: For complex features, outline approach first
3. **Test Writing**: Create failing tests that define success
4. **Implementation**: Code to make tests pass
5. **Integration Testing**: Test against real UniFi controller (dev environment)
6. **Documentation**: Update README, add examples, create troubleshooting entries
7. **PR Submission**: Include testing evidence, screenshots for UI changes
8. **Review**: At least one approval required, all discussions resolved
9. **Merge**: Squash and merge with clean commit message

### Quality Gates

Before merging any PR:

- ✅ All tests pass (100% of the time)
- ✅ Code coverage ≥80% overall
- ✅ No ruff/pylint violations
- ✅ hassfest validation passes
- ✅ Manual testing performed against real UniFi controller
- ✅ Changelog updated with user-facing changes
- ✅ Breaking changes documented in PR and release notes

### Release Process

1. **Version Bump**: Update `manifest.json` version
2. **Changelog**: Consolidate changes since last release
3. **Tag**: Create git tag with version number
4. **GitHub Release**: Auto-creates from tag with changelog
5. **HACS**: Validates and publishes automatically
6. **Monitoring**: Watch for issues in first 48 hours post-release

### Debugging & Support

- **Debug Logging**: Enable via HA logger config
- **Diagnostics**: Implement `async_get_config_entry_diagnostics`
- **Issue Template**: Guide users to provide logs, versions, configuration
- **Common Issues**: Maintain troubleshooting section in README
- **Response Time**: Acknowledge issues within 48 hours (best effort)

## Security Requirements

### Credential Handling

- API keys stored encrypted via HA config entry
- Never log credentials (even in debug mode)
- Support for HA secrets in config (for manual YAML tweaks)
- Secure defaults (verify SSL unless explicitly disabled)

### API Communication

- Default to HTTPS for UniFi controller connections
- Option to disable SSL verification (with warning)
- No credential transmission over unencrypted connections
- Rate limiting to prevent API abuse/DOS

### User Data

- No telemetry or data collection
- All data stays local to user's HA instance
- Device information not shared with third parties
- Privacy-first: only request minimum required permissions

## Governance

### Constitution Authority

- This constitution supersedes all other practices and documentation
- All PRs must demonstrate compliance with these principles
- Violations require justification and approval from maintainer
- Regular reviews (every 6 months) to ensure relevance

### Amendment Process

1. Propose change via GitHub issue with rationale
2. Discussion period (minimum 2 weeks for major changes)
3. Approval required from maintainer
4. Update constitution with version bump
5. Announce in release notes
6. Allow adaptation period before strict enforcement

### Exceptions

- Exceptions to these rules require documented justification
- Security fixes may bypass normal workflow (emergency process)
- Temporary exceptions must have sunset date
- All exceptions tracked in EXCEPTIONS.md

### Conflict Resolution

- Constitution > Home Assistant Guidelines > Personal Preference
- When guidelines conflict, prioritize:
  1. User safety and privacy
  2. Home Assistant compatibility
  3. Code maintainability
  4. Developer convenience

**Version**: 1.0.0 | **Ratified**: 2025-01-15 | **Last Amended**: 2025-01-15
