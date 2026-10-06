# PIKOM Event Platform

A Django application for managing events and campaigns, registration forms, participants, surveys, QR check-in, and event operations.

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
| `EMAIL_BACKEND` | Django console email backend | Defaults to printing outgoing email to the server terminal. |
| `DEFAULT_FROM_EMAIL` | `webmaster@localhost` | Sender shown for outgoing email. |

The development defaults are not production settings. Before deploying, configure a secure secret, `DEBUG=False`, production hosts, database credentials, and an appropriate email backend. Never deploy with the local fallback secret.

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