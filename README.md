# PIKOM Event Platform

A Django application for managing events and campaigns, registration forms, participants, surveys, QR check-in, and event operations.

For a walkthrough of attendee and organizer workflows, see the
[application guide](APPLICATION_GUIDE.md).

## Requirements

- Python 3.12 recommended (the project has been run with Python 3.12).
- pip and a virtual environment.
- SQLite for local development (included with Python), or a configured MySQL server.
- Some Python dependencies use native system libraries. On Debian/Ubuntu, if installing requirements fails while building `mysqlclient`, `python-magic`, or WeasyPrint dependencies, install the corresponding system development/runtime packages (for example `build-essential`, `pkg-config`, `default-libmysqlclient-dev`, and `libmagic1`) and retry.

## Local Setup

Run commands from the repository root, the directory containing `manage.py`.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py check
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open the app at <http://127.0.0.1:8000/>. Sign in at <http://127.0.0.1:8000/login/>. The Django admin is at <http://127.0.0.1:8000/admin/>.

## Attendee API and Next.js app

The attendee API is served by Django under `/api/`. Public event listing and
registration routes are available without authentication. Attendee routes use
the high-entropy `registration_code` as a bearer token:

```text
GET    /api/events/
GET    /api/events/{event_id}/
POST   /api/events/{event_id}/register/
GET    /api/events/{event_id}/directory/
GET/PATCH /api/me/
GET    /api/me/schedule/
GET    /api/me/check-in/
POST/DELETE /api/jobs/{job_id}/bookmark/
POST/DELETE /api/sessions/{session_id}/registration/
POST/DELETE /api/interview-slots/{slot_id}/booking/
POST/DELETE /api/promotions/{promotion_id}/claim/
```

Send the attendee token as `Authorization: Bearer <registration_code>`. Tokens
are personal credentials; keep them private. Attendee API access does not grant
organizer access. Registration submissions remain pending until approved by an
event organizer. The check-in endpoint is read-only for attendees.

Run the Next.js attendee application separately from Django:

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Set `DJANGO_API_URL` in `frontend/.env.local` to the Django server address. The
Next.js server proxies `/api/` and `/media/` requests to Django. For secure
attendee login links in registration emails, set the Django environment
variable `ATTENDEE_APP_URL` to the deployed Next.js origin, without a trailing
slash. Local registration automatically signs in the browser that submitted
the form.

## Synthetic showcase data

To populate a development database with linked sample events, registrants,
employers, jobs, sessions, maps, interviews, education/training content, and
bookings, follow [the synthetic data instructions](synthetic_data/README.md).
The seed script is repeatable, does not delete data, and refuses to run with
`DJANGO_DEBUG=false`.

If an admin account already exists, use its credentials instead of creating another one. Django does not provide a default username or password. To change an account's password, run `python manage.py changepassword <username>`.

## Database

By default, local development uses SQLite at `db.sqlite3` in the repository root. SQLite has no database username or password; the database is the file itself. Keep this file private if it contains real participant information, and back it up before changing or importing data.

Useful database commands:

```bash
python manage.py showmigrations
python manage.py migrate
python manage.py dbshell
```

`dbshell` opens the SQLite command line when the `sqlite3` CLI is installed. Inside it, use `.tables` to list tables, `.schema register_campaign` to inspect a table, and `.quit` to exit. You can also open `db.sqlite3` with a SQLite viewer such as the SQLite extension for VS Code.

Use Django's ORM through the project shell to inspect application data:

```bash
python manage.py shell
```

For example, at the Python prompt:

```python
from register.models import Campaign, Survey, SurveyUser
Campaign.objects.count()
Survey.objects.count()
SurveyUser.objects.count()
Campaign.objects.values("id", "title")[:10]
```

Exit the shell with `exit()` or Ctrl-D. The `register` application owns the main event and registration data models; check `register/models.py` for the full schema.

### Optional MySQL Configuration

Settings read database configuration from environment variables. Set these in the same terminal before starting Django; the project does not automatically load a `.env` file.

```bash
export DB_ENGINE=django.db.backends.mysql
export DB_NAME=picom
export DB_USER=your_mysql_user
export DB_PASSWORD='your_mysql_password'
export DB_HOST=127.0.0.1
export DB_PORT=3306
```

The MySQL server and database must already exist, and the configured user needs permission to access the database. After configuring it, run `python manage.py migrate`. Do not put real credentials in source control or share them in chat. `mysqlclient` is already listed in `requirements.txt`.

## Configuration

Project settings live in `picom/settings.py`; `manage.py` uses the `picom.settings` module.

| Variable | Default | Purpose |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | Local development key | Django signing key. Set a private, strong value outside local development. |
| `DJANGO_DEBUG` | `true` | Enables Django debug mode when set to `true`. Turn it off in production. |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated hostnames allowed by Django. |
| `DB_ENGINE` | `django.db.backends.sqlite3` | Django database backend. |
| `DB_NAME` | Repository-root `db.sqlite3` | SQLite path or MySQL database name. |
| `DB_USER`, `DB_PASSWORD` | Empty | MySQL credentials. |
| `DB_HOST`, `DB_PORT` | Empty | MySQL host and port. |
| `EMAIL_BACKEND` | SMTP when `EMAIL_HOST` is set; otherwise console | Selects Django's email backend. |
| `EMAIL_HOST`, `EMAIL_PORT` | Empty, `587` | SMTP server and port. |
| `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | Empty | SMTP credentials. |
| `EMAIL_USE_TLS`, `EMAIL_USE_SSL`, `EMAIL_TIMEOUT` | `true`, `false`, `20` | SMTP connection security and timeout. TLS and SSL cannot both be enabled. |
| `DEFAULT_FROM_EMAIL` | `webmaster@localhost` | Sender shown for outgoing email. |
| `ATTENDEE_APP_URL` | Empty | Deployed Next.js origin used in attendee email links. |
| `DJANGO_SECURE_SSL_REDIRECT` | `false` | Redirects HTTP to HTTPS when enabled. |
| `DJANGO_SESSION_COOKIE_SECURE`, `DJANGO_CSRF_COOKIE_SECURE` | Enabled when debug is off | Restricts cookies to HTTPS. |
| `DJANGO_SECURE_HSTS_SECONDS` | `0` | HSTS duration; enable only after HTTPS is working. |
| `DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS`, `DJANGO_SECURE_HSTS_PRELOAD` | `false` | Optional HSTS scope controls. |
| `DJANGO_BEHIND_HTTPS_PROXY` | `false` | Trusts `X-Forwarded-Proto: https` from a configured proxy. |
| `SHOW_LEGACY_GOLF_TOOLS` | `false` | Shows the retained legacy Golf navigation when explicitly enabled. |

Production mode (`DJANGO_DEBUG=false`) requires explicit `DJANGO_SECRET_KEY` and
`DJANGO_ALLOWED_HOSTS` values. Configure HTTPS redirect, proxy handling, and
HSTS to match the deployment topology. Run `python manage.py collectstatic`
and serve `STATIC_ROOT` (`staticfiles/`) through the web server or a static
file service. `MEDIA_ROOT` (`media/`) contains uploaded assets and needs
persistent storage or an object-storage backend in production. Next.js rewrites
`/api/` and `/media/` to Django, so deploy both behind the intended public
origin. No cross-origin browser API call is needed with this proxy setup.

The development defaults are not production settings. Before deploying,
configure a secure secret, `DEBUG=False`, production hosts, database
credentials, HTTPS, persistent media, static-file serving, and an appropriate
email backend. Never deploy with the local fallback secret.

## Common Commands

```bash
python manage.py runserver                 # Start the local web server
python manage.py check                     # Run Django system checks
python manage.py test                      # Run the Django test suite
python manage.py makemigrations            # Generate migrations after model changes
python manage.py migrate                   # Apply migrations to the configured database
python manage.py showmigrations            # Show migration status
python manage.py createsuperuser           # Create a Django admin account
python manage.py changepassword USERNAME   # Change an account password
python manage.py shell                     # Open an interactive Django/Python shell
python manage.py dbshell                   # Open the configured database command line
```

The repository includes these custom commands:

```bash
python manage.py import_participants --help
python manage.py seed_pikom_survey
python manage.py seed_pikom_gbs_survey
```

The survey seed commands create or update survey questions. Review their source before running against a database with real data. The participant importer supports a `--dry-run`; read [docs/import-participants.md](docs/import-participants.md) before using it.

## Project Map

- `picom/` — Django project settings, URL routing, ASGI, and WSGI entry points.
- `register/` — campaigns/events, registration forms, participants, surveys, registration workflows, and management commands.
- `user/` — login, logout, staff-user management, and password reset.
- `validate/` — attendee validation and check-in pages.
- `templates/` and each app's `templates/` — server-rendered HTML templates.
- `static/` and each app's `static/` — CSS, JavaScript, and other static assets.
- `docs/` — operational and feature guides.
- `PIKOM_IMPLEMENTATION_PLAN.md` — current implementation direction and constraints.
- `PRODUCT_VISION.md` — longer-term product vision.

Useful entry points:

- `/` — campaign/event organizer interface.
- `/login/` — application sign-in.
- `/admin/` — Django's built-in administration site.
- `/registration_forms/` and related paths — registration form management (see `register/urls.py`).

The Django admin is distinct from the organizer interface. A superuser can sign into both, but normal organizer workflows are provided by the application's own pages.

## Existing Guides

- [Import participants from Excel](docs/import-participants.md) — mapping, dry-run, import, and rollback guidance.
- [Automatic label printing](docs/label-printing-setup.md) — check-in station and printer setup.
- [Campaign and registration form manual](docs/user-manual-campaign-and-registration-form.html)

## Troubleshooting

- **`ModuleNotFoundError: No module named 'picom.settings'`** — ensure `picom/settings.py` exists and run commands from the project root.
- **Django says there are unapplied migrations** — run `python manage.py migrate` against the intended database.
- **Admin login fails** — there is no preset password. Create an account with `createsuperuser` or reset one with `changepassword`.
- **SQLite `dbshell` is unavailable** — install the system `sqlite3` command-line program, or use a SQLite viewer. Django's web app can use SQLite without that CLI.
- **A MySQL/native dependency fails to install** — install the operating-system development libraries required by that package, then rerun `pip install -r requirements.txt`.
- **Email does not arrive during local development** — the default backend prints email content in the `runserver` terminal; it does not send email over SMTP.

## Security and Data

Do not commit database files, uploaded media, secrets, or real participant information. The repository's `.gitignore` currently excludes the virtual environment but may need local additions for database/media files. Use a backup before destructive data operations, and test imports with `--dry-run` first.
