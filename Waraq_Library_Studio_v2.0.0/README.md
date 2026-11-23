# وَرَق | WARAQ Library Studio

**An Arabic-first library management experience for books, student projects, members and lending.**

وَرَق تطبيق ويب محلي لإدارة مكتبة صغيرة أو مكتبة جامعية. يجمع بين واجهة تحريرية سينمائية خفيفة، ولوحة تحكم عملية، ونظام إعارة يحفظ البيانات في SQLite.

## What is included

- RTL Arabic-first responsive interface for desktop, tablet and mobile.
- Editorial visual system: warm ivory, forest green, sage, copper and muted gold.
- Separate manager and member workspaces.
- Dashboard statistics and recent lending activity.
- Searchable catalogue for books and student projects.
- Filters by type, specialization, availability and project year.
- Manager tools to add books/projects and create member accounts.
- Member borrowing, return tracking, history and due-date visibility.
- Seven-day loan period and a three-item active-loan limit per member.
- Password change, salted PBKDF2-HMAC-SHA256 password storage, CSRF protection, session rotation, role checks and login throttling.
- SQLite persistence with foreign keys, indexes and WAL mode.
- Health endpoint and automated unit/HTTP tests.
- No third-party Python dependencies.

## Requirements

- Python 3.10 or newer.
- A modern browser.
- No `pip install` step is needed. The application uses Python's standard library only.

## Run on Windows

1. Download and extract the ZIP archive.
2. Open the extracted folder that contains `main.py`.
3. Double-click `run.bat`, or open PowerShell in that exact folder and run:

   ```powershell
   python main.py
   ```

4. Open <http://127.0.0.1:8000>.
5. Keep the terminal open while using the app. Press `Ctrl + C` in the terminal to stop it.

PowerShell tip: In File Explorer, open the project folder, click its address bar, type `powershell`, then press Enter. This opens the terminal in the correct folder.

## Run on macOS / Linux

```bash
python3 main.py
```

Then open <http://127.0.0.1:8000>.

## Demo accounts

A fresh local database is seeded with the following sample users:

| Role | Username | Password |
|---|---|---|
| Manager | `admin` | `admin123` |
| Member | `saif_101` | `saif123` |
| Member | `rida_102` | `rida123` |
| Member | `aws_103` | `aws123` |

The login page provides a helper to fill sample credentials. It does not submit the form automatically.

### Repair sample logins

When the local sample credentials have been changed or a linked sample member login is missing, run this command from the folder containing `main.py`:

```powershell
python main.py --reset-demo-accounts
```

It resets only the built-in sample accounts. It does **not** delete catalogue records, members or lending history. Start the server afterward with `python main.py`.

To hide sample credentials in a local evaluation or hosted environment:

```powershell
$env:WARAQ_DEMO_MODE = "0"
python main.py
```

Do not use sample passwords for real accounts. Change the manager password from **Account settings** before any shared demonstration.

## Data and backup

The SQLite file is created automatically at `data/library.db` on first run. It is intentionally excluded from Git commits.

To back up your local library, stop the application and copy `data/library.db` to a safe location. To move your data to another extracted copy of Waraq, place that file in the new project's `data` folder before starting the server.

## Useful routes

| Route | Purpose |
|---|---|
| `/` | Public introduction |
| `/login` | Sign in |
| `/dashboard` | Role-aware dashboard |
| `/catalog` | Search and browse catalogue |
| `/members` | Manager-only member management |
| `/loans` | Active, overdue and returned loans |
| `/account` | Change password |
| `/health` | JSON database health check |

## Project structure

```text
Waraq_Library_Studio/
├── main.py                       # CLI entry point
├── run.bat / run.ps1 / run.sh    # launch helpers
├── waraq/
│   ├── config.py                 # paths and environment settings
│   ├── storage.py                # SQLite connection, schema and seed data
│   ├── security.py               # password hashing and authentication
│   ├── library.py                # catalogue, members and lending rules
│   ├── web.py                    # HTTP routing, sessions and access control
│   └── views.py                  # escaped HTML rendering
├── static/
│   ├── css/styles.css            # responsive cinematic design system
│   ├── js/app.js                 # small client-side interactions
│   └── img/favicon.svg           # application icon
├── data/                         # local SQLite file; ignored by Git
├── tests/                        # service, rendering and HTTP flow tests
├── docs/
│   ├── ARCHITECTURE.md           # architecture and request flow
│   ├── SETUP_WINDOWS.md          # Windows launch guide
│   └── TEST_REPORT.md            # release verification report
├── CHANGELOG.md                  # release notes
└── .github/workflows/tests.yml   # CI test matrix
```

## Tests

Run from the project folder:

```powershell
python -m unittest discover -s tests -v
```

The test suite checks password hashing, demo account repair, search and validation, borrowing and return rules, the three-item limit, role permissions, CSRF rejection, session rotation, logout, static assets and the health endpoint.

## Configuration

Defaults are intentionally local-only:

- Host: `127.0.0.1`
- Port: `8000`
- Database: `data/library.db`

PowerShell example:

```powershell
$env:HOST = "127.0.0.1"
$env:PORT = "8000"
python main.py
```

The database path can be overridden with `LIBRARY_DB`. `WARAQ_COOKIE_SECURE=1` enables the Secure cookie flag when serving through HTTPS.

## GitHub and deployment

This repository is ready to publish as source code. The Python/SQLite backend **cannot run on GitHub Pages**; it needs a Python-capable host with persistent storage. The included development server is intended for local use and academic demonstration, not production hosting. A public deployment should use a production WSGI/ASGI server, HTTPS, persistent secret/session management, database backups, controlled account provisioning and a deployment-specific security review. Disable demo credentials before any public deployment.

---

وَرَق — مساحةٌ للقراءة والتعلّم.
