# Testing

## Overview
SyntaxSnacks uses `pytest` as the test runner. The current tests are written with
`unittest.TestCase`, and pytest runs them seamlessly. All tests live in `tests/`.

## Setup
1) Create and activate a virtual environment.
2) Install runtime and test dependencies:

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Running tests
- Run the full suite:

```bash
pytest
```

- Run a single file:

```bash
pytest tests/test_admin_users.py
```

- Filter by keyword:

```bash
pytest -k "contact"
```

- Coverage (optional):

```bash
pytest --cov=app --cov-report=term-missing
```

## Test fixtures
Shared fixtures are defined in `tests/conftest.py`:

- `app_context` (autouse): pushes a Flask app context for each test so DB calls work.
- `client`: a Flask test client for request/response tests.
- `db_session`: creates a temporary SQLite database and drops it after the test.

Example usage:

```python
def test_example(client, db_session):
    response = client.get("/")
    assert response.status_code == 200
```

## Current suite (by file)
- `tests/test_app.py`: fun API default vs DB-backed responses.
- `tests/test_contact_form.py`: contact form validation and message creation.
- `tests/test_admin_messages.py`: message read/delete and CSV export filters.
- `tests/test_admin_users.py`: user activation, stats adjustments, and audit logs.
- `tests/test_admin_fun_cards.py`: add/delete/import fun cards.
- `tests/test_challenge_import.py`: CSV preview/import rules and data cleanup.
- `tests/test_edit_challenge.py`: admin edit flow saves to DB.

## Writing new tests
- Put new tests in `tests/` and name files `test_*.py`.
- Prefer deterministic tests with isolated data (use the temp SQLite DB).
- Keep the Arrange/Act/Assert flow clear.
- Avoid network calls or external services.
- If you need extra setup, build helpers or fixtures rather than duplicating code.

## Troubleshooting
- Use `pytest -vv -s` to see detailed output and print statements.
- If you see unexpected 429 responses, reduce repeated login/contact attempts or
  clear/patch rate limit state in the test setup.
