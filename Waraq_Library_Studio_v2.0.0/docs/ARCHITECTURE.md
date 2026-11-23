# Waraq architecture

Waraq is a small layered application built with Python's standard library.

## Layers

- **Presentation** — `static/` contains the design system and the small browser-side interactions. `waraq/views.py` renders RTL HTML and escapes dynamic values.
- **HTTP adapter** — `waraq/web.py` maps URLs to application operations, validates form/CSRF input, manages sessions and enforces manager/member permissions.
- **Application services** — `waraq/library.py` applies catalogue, member and lending rules. `waraq/security.py` handles authentication, password changes and sample-account recovery.
- **Persistence** — `waraq/storage.py` owns the SQLite connection lifecycle, schema, indexes, seed data and health checks.
- **Configuration** — `waraq/config.py` centralizes runtime paths and environment variables.

## Request flow

1. The browser requests a page or submits a form.
2. `LibraryHandler` loads the signed-in session context and checks CSRF on POST requests.
3. The HTTP layer verifies the user's role before calling a service.
4. The service performs validation and executes a transaction through the SQLite connection context manager.
5. `views.py` renders escaped HTML, or the health route returns JSON.

## Data integrity

- Foreign keys are enabled on each connection.
- A partial unique index prevents more than one active loan for the same item.
- Borrow requests use `BEGIN IMMEDIATE` to serialize availability and member-limit checks.
- A member may hold at most three active items.
- A loan is due seven calendar days after borrowing.
- Items with lending history cannot be deleted, preserving the audit trail.

## Security boundaries

- Passwords are stored as salted PBKDF2-HMAC-SHA256 hashes.
- Session IDs rotate after successful authentication.
- Session cookies are HttpOnly and SameSite=Lax; `WARAQ_COOKIE_SECURE=1` adds Secure behind HTTPS.
- State-changing forms require a per-session CSRF token.
- Manager-only pages and actions are checked server-side.
- Login failures are throttled per client IP and username.
- Dynamic text is HTML-escaped before rendering.

The built-in HTTP server and in-memory sessions are appropriate for a local project/demo. They are not a substitute for a production server, persistent session backend, HTTPS termination and deployment hardening.
