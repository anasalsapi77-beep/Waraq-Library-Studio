# Waraq Library Studio 2.0.0 — Verification report

## Environment

- Python: 3.13 (container verification runtime)
- Dependencies: Python standard library only
- Database: temporary SQLite database; no personal/local library data included

## Automated tests

Command:

```bash
python -m unittest discover -s tests -v
```

Result: **28 tests passed**.

Coverage includes:

- salted password hashing and credential verification
- demo account seeding, repair and reset without deleting library records
- catalogue search and field validation
- member creation and account linking
- seven-day due dates, duplicate-loan prevention and three-active-item limit
- member ownership checks on loan returns
- protection of records with lending history
- role-aware navigation and escaped dynamic values
- manager/member login, session rotation and logout
- CSRF rejection and manager-only route protection
- login attempt throttling
- static CSS delivery and `/health`

## Startup and packaging checks

- `python main.py --check`: passed; SQLite `quick_check` returned `ok`.
- Standalone server smoke test: passed; `/health` returned HTTP 200 and JSON status `ok`.
- Fresh ZIP extraction: passed; tests passed from the extracted release directory.
- ZIP archive integrity: passed; no compressed-data errors detected.

## Scope note

This validates local development behavior in the test environment. It does not represent a production security audit or a deployment to a public hosting provider. The included `http.server` runtime is intended for local demonstration and development.
