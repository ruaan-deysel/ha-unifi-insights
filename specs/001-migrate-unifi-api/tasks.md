# Tasks: Migrate to unifi-official-api Library

**Input**: Design documents from `/specs/001-migrate-unifi-api/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Tests ARE REQUIRED per constitution Principle IV. All test tasks included below must be completed before release.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Project type**: Single project (Home Assistant custom integration)
- **Integration path**: `custom_components/unifi_insights/`
- **Tests path**: `tests/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and dependency management

- [x] T001 Add unifi-official-api~=1.0.0 to custom_components/unifi_insights/manifest.json requirements array
- [x] T002 Update requirements.txt to include unifi-official-api~=1.0.0 for development
- [x] T003 [P] Create tests directory structure (tests/conftest.py, tests/fixtures/)
- [x] T004 [P] Create test fixtures for library mocks in tests/fixtures/library_responses.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Create data transformation module in custom_components/unifi_insights/data_transforms.py with transform_network_device() and transform_protect_camera() stubs
- [x] T006 [P] Research unifi-official-api library documentation and complete contracts/library-api.md with verified method signatures
- [x] T007 [P] Update research.md Section 1 with complete library API method mapping matrix (verify all 42+ methods)
- [x] T008 [P] Update research.md Section 4 with exception handling patterns and complete exception mapping matrix
- [x] T009 Verify library WebSocket support and update research.md Section 4 with WebSocket migration decision (Scenario A/B/C)
- [x] T010 Update data-model.md with actual library field names (replace all "?" placeholders with verified library response schemas)
- [x] T011 [P] Implement all transformation functions in data_transforms.py (transform_network_device, transform_protect_camera, transform_protect_light, transform_protect_sensor, transform_protect_chime)
- [x] T012 [P] Create pytest fixtures for mocking UniFiClient in tests/conftest.py with mock_unifi_client fixture
- [x] T013 [P] Write unit tests for data transformation functions in tests/test_data_transforms.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Seamless Existing Functionality (Priority: P1) 🎯 MVP

**Goal**: Migrate all 8 entity platforms to use unifi-official-api while maintaining 100% feature parity

**Independent Test**: Upgrade existing installation and verify all entities maintain state, attributes, and responsiveness exactly as before

**TDD Enforcement (Constitution Principle IV - NON-NEGOTIABLE)**:

- Tests MUST be written BEFORE or ALONGSIDE implementation (Red-Green-Refactor cycle)
- Recommended execution order:
  1. Write test fixtures and mocks (T003-T004, T012 already done in Phase 2)
  2. For each component, write FAILING tests first (T048-T058)
  3. Implement minimum code to make tests pass (T014-T047)
  4. Refactor while keeping tests green
- **Practical approach**: Start test writing (T048-T058) in parallel with or BEFORE implementation (T014-T047)
- Tests may initially fail (expected) - they define success criteria
- Implementation tasks (T014-T047) proceed only when corresponding tests exist

### Core Coordinator Migration for User Story 1

- [x] T014 [US1] Update custom_components/unifi_insights/**init**.py imports (remove custom API imports, add UniFiClient from unifi_official_api)
- [x] T015 [US1] Replace custom client initialization with UniFiClient in custom_components/unifi_insights/**init**.py async_setup_entry()
- [x] T016 [US1] Add library validation call in custom_components/unifi_insights/**init**.py with exception translation (UniFiAuthError → ConfigEntryAuthFailed)
- [x] T017 [US1] Update custom_components/unifi_insights/coordinator.py **init**() to accept single UniFiClient instead of two custom clients
- [x] T018 [US1] Refactor custom_components/unifi_insights/coordinator.py \_async_update_data() Network API section to use client.network.get_sites() and apply transform_network_device()
- [x] T019 [US1] Refactor custom_components/unifi_insights/coordinator.py \_async_update_data() Protect API section to use client.protect.get_cameras() and apply transformation functions
- [x] T020 [US1] Update exception handling in custom_components/unifi_insights/coordinator.py \_async_update_data() to catch library exceptions and translate to UpdateFailed
- [x] T021 [US1] Update custom_components/unifi_insights/config_flow.py async_step_user() to use UniFiClient.validate() for API key validation
- [x] T022 [US1] Update custom_components/unifi_insights/config_flow.py async_step_reauth() to use library exceptions (UniFiAuthError)

### Entity Platform Updates for User Story 1

- [x] T023 [P] [US1] Update custom_components/unifi_insights/entity.py base entity classes to handle transformed data structures
- [x] T024 [P] [US1] Verify custom_components/unifi_insights/sensor.py entities consume transformed data correctly (no changes needed if transformation layer works)
- [x] T025 [P] [US1] Verify custom_components/unifi_insights/binary_sensor.py entities consume transformed data correctly
- [x] T026 [P] [US1] Update custom_components/unifi_insights/camera.py async_camera_image() to use client.protect.get_snapshot()
- [x] T027 [P] [US1] Update custom_components/unifi_insights/camera.py async_stream_source() to use client.protect.get_stream_url()
- [x] T028 [P] [US1] Update custom_components/unifi_insights/light.py async_turn_on/off() to use client.protect.update_light()
- [x] T029 [P] [US1] Update custom_components/unifi_insights/switch.py async_turn_on/off() to use client.protect.update_camera() for microphone control
- [x] T030 [P] [US1] Update custom*components/unifi_insights/select.py async_select_option() to use client.protect.set*\*\_mode() methods
- [x] T031 [P] [US1] Update custom*components/unifi_insights/number.py async_set_native_value() to use client.protect.set*_*volume() and client.protect.set*_\_brightness() methods
- [x] T032 [P] [US1] Update custom_components/unifi_insights/button.py async_press() to use client.network.restart_device() and client.protect.play_chime()

### Services Migration for User Story 1

- [x] T033 [P] [US1] Update custom_components/unifi_insights/services.py async_restart_device() to use client.network.restart_device()
- [x] T034 [P] [US1] Update custom_components/unifi_insights/services.py async_power_cycle_port() to use client.network.power_cycle_port()
- [x] T035 [P] [US1] Update custom_components/unifi_insights/services.py async_authorize_guest() to use client.network.authorize_guest()
- [x] T036 [P] [US1] Update custom_components/unifi_insights/services.py voucher-related services to use client.network.\*\_voucher() methods
- [x] T037 [P] [US1] Update custom*components/unifi_insights/services.py Protect camera services to use client.protect.set*\*\_mode() methods
- [x] T038 [P] [US1] Update custom*components/unifi_insights/services.py PTZ services to use client.protect.ptz*\*() methods
- [x] T039 [P] [US1] Update custom_components/unifi_insights/services.py chime services to use client.protect.\*\_chime() methods

### WebSocket Migration for User Story 1

- [x] T040 [US1] Implement WebSocket migration based on research.md Section 4 decision (Scenario A: migrate to library, Scenario B: hybrid, or Scenario C: maintain custom)
- [x] T041 [US1] Update custom_components/unifi_insights/coordinator.py WebSocket callback handlers (\_handle_device_update, \_handle_event_update) to work with library WebSocket events (if Scenario A)
- [x] T042 [US1] Test WebSocket reconnection and message handling with library (if Scenario A)

### Diagnostics and Cleanup for User Story 1

- [x] T043 [US1] Update custom_components/unifi_insights/diagnostics.py async_get_config_entry_diagnostics() to include library version from unifi_official_api.**version**
- [x] T044 [US1] Add sanitized library connection info (host with redacted credentials) to diagnostics output
- [x] T045 [US1] Remove custom_components/unifi_insights/unifi_network_api.py (601 lines)
- [x] T046 [US1] Remove custom_components/unifi_insights/unifi_protect_api.py (1840 lines)
- [x] T047 [US1] Remove unused imports from all files (search for UnifiInsightsClient, UnifiProtectClient references)

### Tests for User Story 1 (REQUIRED - TDD: Write FIRST)

> **CRITICAL**: Per Constitution Principle IV (NON-NEGOTIABLE), these tests MUST be written BEFORE or ALONGSIDE implementation tasks T014-T047. Follow Red-Green-Refactor: write failing tests first, implement to pass, refactor. Start T048-T058 before or in parallel with T014-T047.

- [x] T048 [P] [US1] Write config flow tests in tests/test_config_flow.py with mocked library (test setup, reauth, validation)
- [x] T049 [P] [US1] Write coordinator tests in tests/test_coordinator.py with mocked library (test \_async_update_data, exception handling, data transformation)
- [~] T050 [P] [US1] Write sensor entity tests in tests/test_sensor.py (test state, attributes, availability)
- [ ] T051 [P] [US1] Write binary sensor entity tests in tests/test_binary_sensor.py
- [ ] T052 [P] [US1] Write camera entity tests in tests/test_camera.py (test snapshot, stream URL generation)
- [ ] T053 [P] [US1] Write light entity tests in tests/test_light.py (test turn_on/off, brightness)
- [ ] T054 [P] [US1] Write switch entity tests in tests/test_switch.py (test microphone toggle)
- [ ] T055 [P] [US1] Write select entity tests in tests/test_select.py (test option selection)
- [ ] T056 [P] [US1] Write number entity tests in tests/test_number.py (test value setting)
- [ ] T057 [P] [US1] Write button entity tests in tests/test_button.py (test press actions)
- [ ] T058 [P] [US1] Write service tests in tests/test_services.py (test all 15+ services)
- [ ] T059 [US1] Run pytest with coverage report and verify >=80% overall coverage
- [ ] T060 [US1] Fix any coverage gaps identified in T059

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently - ALL entities working with library, custom API code removed, tests passing with >=80% coverage

---

## Phase 4: User Story 2 - Improved Reliability and Maintainability (Priority: P2)

**Goal**: Enhance error handling, connection management, and resilience through library's robust implementation

**Independent Test**: Monitor error logs and connection stability over extended periods, simulate network issues and verify graceful degradation

### Error Handling Enhancements for User Story 2

- [ ] T061 [P] [US2] Review and enhance exception translation in custom_components/unifi_insights/coordinator.py for all library exception types (UniFiAuthError, UniFiConnectionError, UniFiTimeoutError, UniFiAPIError)
- [ ] T062 [P] [US2] Add exponential backoff retry logic in coordinator for transient UniFiTimeoutError exceptions
- [ ] T063 [P] [US2] Implement connection state tracking in coordinator to distinguish temporary vs permanent failures
- [ ] T064 [P] [US2] Add comprehensive logging for all library exceptions with context (site_id, device_id, operation)

### Connection Management for User Story 2

- [ ] T065 [P] [US2] Verify library handles API rate limiting transparently (test with rapid requests)
- [ ] T066 [P] [US2] Test integration behavior during network interruptions (disconnect controller, verify entity availability states)
- [ ] T067 [P] [US2] Verify WebSocket reconnection behavior follows library's exponential backoff (if using library WebSockets)
- [ ] T068 [P] [US2] Add health check monitoring in coordinator to detect stale connections

### Documentation for User Story 2

- [ ] T069 [US2] Update README.md to document unifi-official-api library usage and benefits
- [ ] T070 [US2] Add troubleshooting section to README.md with library-specific error patterns
- [ ] T071 [US2] Document library version requirements and upgrade path in README.md

### Tests for User Story 2 (REQUIRED)

- [ ] T072 [P] [US2] Write integration tests for exception handling scenarios in tests/test_error_handling.py (test auth failures, connection errors, timeouts)
- [ ] T073 [P] [US2] Write integration tests for connection resilience in tests/test_connection_resilience.py (test reconnection, rate limiting, network interruptions)
- [ ] T074 [US2] Run extended stability tests (4+ hour run with periodic network disruptions)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - Enhanced error handling verified, connection management robust, stability tests passing

---

## Phase 5: User Story 3 - Standards-Compliant Architecture (Priority: P3)

**Goal**: Ensure codebase follows Home Assistant core integration patterns and best practices

**Independent Test**: Code review against HA integration quality scale, verify coordinator is sole library interface, entities never call library directly

### Architecture Compliance for User Story 3

- [ ] T075 [P] [US3] Audit all entity files to verify ZERO direct library imports (only coordinator access allowed)
- [ ] T076 [P] [US3] Verify coordinator is sole interface to library (grep for "from unifi_official_api import" outside coordinator and **init**)
- [ ] T077 [P] [US3] Review exception handling patterns against HA core integrations (compare with similar integrations)
- [ ] T078 [P] [US3] Verify entity unique IDs follow HA conventions and are preserved from pre-migration

### Code Quality for User Story 3

- [ ] T079 [P] [US3] Run ruff linter on all modified files and fix violations in custom_components/unifi_insights/
- [ ] T080 [P] [US3] Run pylint on all modified files and fix violations (allow only documented exceptions)
- [ ] T081 [P] [US3] Verify type hints on all public methods in coordinator and entities
- [ ] T082 [P] [US3] Add docstrings to all new/modified public methods (Google style)

### Integration Quality Scale Compliance for User Story 3

- [ ] T083 [US3] Run hassfest validation and fix all errors
- [ ] T084 [US3] Verify integration passes all Home Assistant Quality Scale requirements (coordinator pattern, config flow, diagnostics, proper exception handling)
- [ ] T085 [US3] Review code against constitution.md principles and verify compliance (all 8 principles)
- [ ] T086 [US3] Update CLAUDE.md agent context with final implementation notes

### Tests for User Story 3 (REQUIRED)

- [ ] T087 [P] [US3] Write architectural compliance tests in tests/test_architecture.py (test coordinator is sole library interface, entities don't import library)
- [ ] T088 [P] [US3] Write hassfest validation tests (verify manifest.json, validate requirements)
- [ ] T089 [US3] Generate final coverage report and verify >=80% with detailed breakdown by module

**Checkpoint**: All user stories should now be independently functional - Architecture compliant, code quality verified, HA integration standards met

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, documentation, and release preparation

- [ ] T090 [P] Update custom_components/unifi_insights/manifest.json version to YYYY.MM.PATCH format (bump minor version)
- [ ] T091 [P] Create CHANGELOG.md entry documenting migration to library (user-facing: "Improved reliability through official library", dev-facing: "Migrated to unifi-official-api")
- [ ] T092 [P] Update README.md badges and links to reflect library usage
- [ ] T093 [P] Verify SSDP discovery still works for UniFi Dream Machine devices
- [ ] T094 [P] Create upgrade testing guide in specs/001-migrate-unifi-api/test-plan.md
- [ ] T095 [P] Update quickstart.md with final implementation patterns and lessons learned
- [ ] T096 Manual testing against real UniFi controller (all 8 platforms, all services, WebSocket updates)
- [ ] T097 Test fresh installation with library (new config entry setup)
- [ ] T098 Test upgrade from custom client version (verify entity IDs preserved, no reconfiguration needed)
- [ ] T099 Test reauth flow with expired API key (verify library exception translation)
- [ ] T100 Beta testing coordination (recruit beta testers, distribute test version, collect feedback)
- [ ] T101 Address critical issues from beta testing (fix bugs, update documentation)
- [ ] T102 Performance benchmark comparison (pre-migration vs post-migration: memory, CPU, update latency)
- [ ] T103 Final code review and cleanup (remove debug logging, verify no TODO comments, check for unused code)
- [ ] T104 Create release notes with migration highlights, breaking changes (none expected), and upgrade instructions
- [ ] T105 Prepare rollback plan documentation (how to revert to pre-migration version if critical issues discovered)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion (T001-T004) - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational phase completion (T005-T013) - Core migration tasks
  - Can start after Foundational checkpoint reached
- **User Story 2 (Phase 4)**: Depends on User Story 1 completion (T014-T060) - Builds on migrated codebase
  - Can start after US1 checkpoint reached
- **User Story 3 (Phase 5)**: Depends on User Stories 1 & 2 completion (T061-T074) - Final compliance verification
  - Can start after US1 & US2 checkpoints reached
- **Polish (Phase 6)**: Depends on all user stories being complete (T075-T089) - Release preparation

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies on other stories - Can start after Foundational phase
- **User Story 2 (P2)**: Depends on US1 completion - Enhances error handling of migrated code
- **User Story 3 (P3)**: Depends on US1 & US2 completion - Validates final architecture

### Within Each User Story

**User Story 1 Internal Order (TDD-Compliant)**:

1. **Tests (T048-T058)** - Write FIRST or in parallel with implementation (TDD: Red-Green-Refactor)
2. Core Coordinator Migration (T014-T022) - MUST complete with corresponding tests (T048-T049)
3. Entity Platform Updates (T023-T032) - Can run in parallel after coordinator done, with tests (T050-T057)
4. Services Migration (T033-T039) - Can run in parallel with entities, with tests (T058)
5. WebSocket Migration (T040-T042) - Sequential, depends on research decision (includes testing)
6. Diagnostics and Cleanup (T043-T047) - Can run after coordinator stable
7. Coverage Validation (T059-T060) - Final check after all implementation complete

**User Story 2 Internal Order**:

1. Error Handling (T061-T064) - Can run in parallel
2. Connection Management (T065-T068) - Can run in parallel with error handling
3. Documentation (T069-T071) - Can run in parallel with tests
4. Tests (T072-T074) - Can run after error handling and connection management

**User Story 3 Internal Order**:

1. Architecture Compliance (T075-T078) - Can run in parallel
2. Code Quality (T079-T082) - Can run in parallel with architecture audit
3. Integration Quality Scale (T083-T086) - Sequential, depends on code quality passing
4. Tests (T087-T089) - Can run in parallel with quality checks

### Parallel Opportunities

**Phase 1 (Setup)**: All 4 tasks marked [P] can run in parallel

**Phase 2 (Foundational)**:

- T006, T007, T008, T009 can run in parallel (research tasks, different sections)
- T010 waits for T006-T009 (needs library documentation)
- T011, T012, T013 can run in parallel after T010 (different files)

**Phase 3 (User Story 1)**:

- Coordinator migration (T014-T022) MUST be sequential
- After coordinator done, these groups can run in parallel:
  - Entity updates: T023-T032 (10 tasks, different files)
  - Service updates: T033-T039 (7 tasks, different files)
  - Diagnostics: T043-T044 (2 tasks, same file but independent sections)
  - Test writing: T048-T060 (13 tasks, different test files)

**Phase 4 (User Story 2)**:

- T061-T064 can run in parallel (error handling, different aspects)
- T065-T068 can run in parallel (connection management tests)
- T069-T071 can run in parallel (documentation updates)
- T072-T073 can run in parallel (different test files)

**Phase 5 (User Story 3)**:

- T075-T078 can run in parallel (architecture audits, different aspects)
- T079-T082 can run in parallel (code quality tools, different aspects)
- T087-T088 can run in parallel (different test files)

**Phase 6 (Polish)**:

- T090-T095 can run in parallel (different documentation files)
- T096-T105 are mostly sequential (manual testing and release prep)

---

## Parallel Example: User Story 1 Entity Updates

```bash
# After coordinator migration complete (T022), launch entity updates in parallel:

Task: "T023 [P] [US1] Update entity.py base classes"
Task: "T024 [P] [US1] Verify sensor.py entities"
Task: "T025 [P] [US1] Verify binary_sensor.py entities"
Task: "T026 [P] [US1] Update camera.py async_camera_image()"
Task: "T027 [P] [US1] Update camera.py async_stream_source()"
Task: "T028 [P] [US1] Update light.py async_turn_on/off()"
Task: "T029 [P] [US1] Update switch.py async_turn_on/off()"
Task: "T030 [P] [US1] Update select.py async_select_option()"
Task: "T031 [P] [US1] Update number.py async_set_native_value()"
Task: "T032 [P] [US1] Update button.py async_press()"

# All 10 entity platform updates can proceed simultaneously
```

## Parallel Example: User Story 1 Tests

```bash
# Tests can be written in parallel (different files, no dependencies):

Task: "T048 [P] [US1] Write config flow tests in tests/test_config_flow.py"
Task: "T049 [P] [US1] Write coordinator tests in tests/test_coordinator.py"
Task: "T050 [P] [US1] Write sensor entity tests in tests/test_sensor.py"
Task: "T051 [P] [US1] Write binary sensor entity tests in tests/test_binary_sensor.py"
Task: "T052 [P] [US1] Write camera entity tests in tests/test_camera.py"
Task: "T053 [P] [US1] Write light entity tests in tests/test_light.py"
Task: "T054 [P] [US1] Write switch entity tests in tests/test_switch.py"
Task: "T055 [P] [US1] Write select entity tests in tests/test_select.py"
Task: "T056 [P] [US1] Write number entity tests in tests/test_number.py"
Task: "T057 [P] [US1] Write button entity tests in tests/test_button.py"
Task: "T058 [P] [US1] Write service tests in tests/test_services.py"

# All 11 test files can be created simultaneously
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T013) - **CRITICAL CHECKPOINT**
3. Complete Phase 3: User Story 1 (T014-T060)
4. **STOP and VALIDATE**: Run all tests, manual testing, verify zero regressions
5. Deploy/demo if ready (MVP = fully migrated integration with library)

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready (T001-T013)
2. Add User Story 1 → Test independently → Deploy/Demo (T014-T060) ✅ **MVP Release**
3. Add User Story 2 → Test independently → Deploy/Demo (T061-T074) ✅ Enhanced reliability
4. Add User Story 3 → Test independently → Deploy/Demo (T075-T089) ✅ Architecture validated
5. Complete Polish → Final validation → Production release (T090-T105) ✅ **General Release**

### Parallel Team Strategy (TDD-Compliant)

With multiple developers following strict TDD:

1. Team completes Setup + Foundational together (T001-T013)
2. Once Foundational checkpoint reached (after T013):
   - **Developer A**: Write coordinator tests FIRST (T048-T049), then coordinator migration (T014-T022)
   - **Developer C**: Write config flow tests FIRST (T048), support Developer A
3. After coordinator tests defined (T048-T049 written but failing):
   - **Developer A**: Complete coordinator implementation to pass tests (T014-T022)
   - **Developer B**: Write entity tests FIRST (T050-T057), then entity platforms (T023-T032)
   - **Developer C**: Write service tests FIRST (T058), then services migration (T033-T039)
   - **Developer D**: WebSocket migration + diagnostics (T040-T047)
4. After US1 complete:
   - **Developer A**: User Story 2 error handling (T061-T074)
   - **Developer B**: User Story 3 architecture (T075-T089)
5. Final phase: Team collaborates on polish and release (T090-T105)

---

## Notes

- **[P] tasks** = different files, no dependencies on incomplete tasks, can run in parallel
- **[US1], [US2], [US3]** labels map task to specific user story for traceability
- **Each user story is independently completable and testable** (no cross-story dependencies except sequential order for US2 and US3)
- **Coordinator migration (T014-T022) is the critical path** - blocks all other US1 work
- **WebSocket migration decision (T040-T042)** depends on research outcome (Scenario A/B/C)
- **Tests are REQUIRED** (80%+ coverage) before release per constitution
- **Manual testing (T096-T099)** is REQUIRED before beta testing per clarifications
- **Beta testing (T100-T101)** is REQUIRED before general release per clarifications
- Commit after each task or logical group of related tasks
- Stop at any checkpoint to validate story independently
- **Avoid**: Vague tasks, same file conflicts, cross-story dependencies that break independence

---

## Task Summary

- **Total Tasks**: 105 tasks
- **Phase 1 (Setup)**: 4 tasks
- **Phase 2 (Foundational)**: 9 tasks
- **Phase 3 (User Story 1)**: 47 tasks
- **Phase 4 (User Story 2)**: 14 tasks
- **Phase 5 (User Story 3)**: 15 tasks
- **Phase 6 (Polish)**: 16 tasks

### Tasks by Category

- **Research & Documentation**: 8 tasks (T006-T010, T069-T071, T095)
- **Coordinator Migration**: 9 tasks (T014-T022)
- **Entity Platform Updates**: 10 tasks (T023-T032)
- **Services Migration**: 7 tasks (T033-T039)
- **WebSocket Migration**: 3 tasks (T040-T042)
- **Cleanup**: 5 tasks (T043-T047)
- **Test Implementation**: 24 tasks (T048-T060, T072-T074, T087-T089)
- **Error Handling**: 8 tasks (T061-T068)
- **Architecture Compliance**: 11 tasks (T075-T086)
- **Release Preparation**: 16 tasks (T090-T105)

### Parallel Opportunities Identified

- **Phase 2**: 6 parallel tasks (research and test setup)
- **Phase 3 US1**: 30+ parallel tasks (entity updates, services, tests)
- **Phase 4 US2**: 10 parallel tasks (error handling, testing, docs)
- **Phase 5 US3**: 10 parallel tasks (audits, quality checks, tests)
- **Phase 6 Polish**: 6 parallel tasks (documentation updates)

**Total Parallelizable**: ~62 tasks marked with [P] across all phases

---

## Independent Test Criteria

### User Story 1 (P1): Seamless Existing Functionality

**Test**: Upgrade existing installation, verify all entities maintain exact same state/attributes/responsiveness
**Success**: Zero user-facing changes, all 8 platforms working, custom API code removed, tests >=80% coverage

### User Story 2 (P2): Improved Reliability and Maintainability

**Test**: Monitor error logs over 4+ hours with network disruptions, verify graceful error handling
**Success**: No crashes, entity availability reflects connection state, library handles retries transparently

### User Story 3 (P3): Standards-Compliant Architecture

**Test**: Code review against HA integration quality scale, verify coordinator pattern compliance
**Success**: Hassfest passes, coordinator sole library interface, entities never call library, HA patterns followed

---

## Suggested MVP Scope

**Minimum Viable Product = User Story 1 Only (T001-T060)**

This delivers:

- ✅ Complete migration to unifi-official-api library
- ✅ All 8 entity platforms working
- ✅ All services functional
- ✅ Custom API code removed (2,441 LOC cleanup)
- ✅ Tests passing with >=80% coverage
- ✅ Zero user-facing breaking changes

**Rationale**: US1 alone provides the core value (library adoption, code cleanup, HA best practices). US2 and US3 are enhancements that can follow incrementally.

**Recommended Release Strategy**:

1. **Alpha Release**: US1 complete (internal testing)
2. **Beta Release**: US1 + US2 complete (beta testers)
3. **RC Release**: US1 + US2 + US3 complete (final validation)
4. **General Release**: All phases + polish complete (production)

---

**End of Tasks**

**Next Steps**:

1. Execute Phase 1 (Setup) - T001-T004
2. Execute Phase 2 (Foundational) - T005-T013 - **CRITICAL CHECKPOINT**
3. Begin User Story 1 implementation - T014-T060
4. Validate US1 independently before proceeding to US2

**Format Validation**: ✅ All 105 tasks follow required checklist format with checkbox, ID, optional [P]/[Story] labels, and file paths
