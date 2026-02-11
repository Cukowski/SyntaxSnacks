# Testing Plan

## Goals
- Protect core user flows (signup/login, puzzles, challenges, contact).
- Validate admin workflows (user management, messages, imports).
- Prevent regressions when adding features or refactoring.
- Keep tests fast, deterministic, and easy to maintain.

## Scope
Primary areas to test:
- Authentication and session handling
- Challenge CRUD and import
- Contact form and message management
- Admin user tools (toggle active, adjust stats, audit logs)
- Fun cards (add/delete/import)
- API endpoints (fun fact API, CSV exports)
- Puzzle routes and gameplay endpoints

Out of scope for now:
- Full browser-based E2E (can be added later)
- Load testing beyond basic smoke checks

## Methodologies
- Unit tests: pure logic and small helpers.
- Integration tests: Flask routes + DB + templates.
- Functional tests: key user flows through the HTTP layer.
- Regression tests: protect bugs once fixed.
- Security checks: auth guards, access control, rate limiting.
- Light performance checks: ensure critical endpoints stay responsive.

## Test Strategy
- Follow the test pyramid: many unit tests, fewer integration tests, minimal E2E.
- Favor realistic fixtures and minimal mocking for route-level tests.
- Use isolated SQLite databases per test (or per test class) to prevent cross-talk.
- Keep tests independent; no ordering dependencies.

## Test Case Inventory (examples)
Authentication
- Login success/failure; inactive users blocked.
- Session persistence and logout behavior.

Contact
- Form validation (required fields).
- Message creation on submit.
- Rate-limit behavior (429 and retry-after).

Admin: Users
- Toggle active state.
- Adjust stats with bounds checking.
- Audit log creation with correct metadata.

Admin: Messages
- Mark read/unread.
- Soft delete and export filters.

Admin: Challenges
- Edit form persists to DB.
- CSV import preview and confirm flow.
- Invalid rows skipped and reported.

Fun Cards
- Add/delete manually.
- CSV import ignores invalid rows.

API / Data
- Fun fact API returns defaults when empty.
- CSV exports only include expected rows.

Puzzles
- Route access and response codes.
- Basic state transitions (if applicable).

## Quality Assurance Measures
- Code review required for test and feature changes.
- Maintain meaningful coverage on core flows.
- CI gates: run `pytest` on every PR.
- Track regressions with targeted tests and a short incident note.
- Release checklist includes a clean test run.

## Metrics and Exit Criteria
- New features include at least one test at the appropriate level.
- Critical routes have integration coverage.
- No high-severity bugs open at release time.
- Test suite runtime stays within a reasonable budget.
