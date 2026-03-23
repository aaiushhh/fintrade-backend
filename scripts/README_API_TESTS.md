# API test runner (auto-tests all endpoints)

This backend is FastAPI, so the test runner auto-discovers **all routes** from OpenAPI (`/openapi.json`), executes a few test cases per operation, and writes a report document.

## Prerequisites

- Backend running locally (default): `http://localhost:8000`
- Database seeded (so the default admin exists)
  - Default admin from `docs/api_documentation.md`: `admin@platform.com` / `admin123!`

## Start the backend

From `lms-backend/`:

```bash
uvicorn app.main:app --reload --port 8000
```

## Run the API test suite

From `lms-backend/`:

```bash
python scripts/api_test_runner.py
```

Outputs are written to `test-reports/`:

- `api-test-report-<timestamp>.md` (shareable document)
- `api-test-report-<timestamp>.html` (easy to view in browser)
- `api-test-report-<timestamp>.json` (raw machine-readable results)

## Common options

```bash
python scripts/api_test_runner.py ^
  --base-url http://localhost:8000 ^
  --openapi-url http://localhost:8000/openapi.json ^
  --admin-email admin@platform.com ^
  --admin-password "admin123!" ^
  --concurrency 8 ^
  --timeout 25
```

If you *don’t* want it to register a new student (it registers one by default), run:

```bash
python scripts/api_test_runner.py --no-seed-student
```

## Notes on expectations

- **Auth-required endpoints**: runner does a happy-path request with the appropriate role token (admin/faculty/distributor/student) *and* a negative `no-auth` case expecting `401/403`.
- **JSON-body endpoints**: runner also sends an `invalid-body` case expecting `4xx`.
- Some endpoints depend on existing data (course IDs, exam IDs, lectures). The runner attempts best-effort discovery via list endpoints; if the DB is empty, some “happy” cases may legitimately fail and will be recorded in the report.

