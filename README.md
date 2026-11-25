# PIKOM / Talbotiq registration app

Django 5.2 app for event registration, check-in and campaigns.

## Requirements

- Python 3.12
- MySQL 8 running on `localhost:3306` (database settings in `picom/settings.py`)
- System packages for `mysqlclient` (Ubuntu/Debian: `sudo apt install default-libmysqlclient-dev pkg-config build-essential`)

## Start the project

Run these from the repo root.

```bash
# 1. Create and activate a virtual environment (skip if .venv already exists)
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create the database (once)
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS picom CHARACTER SET utf8mb4;"

# 4. Apply migrations
python manage.py migrate

# 5. Create an admin user (once)
python manage.py createsuperuser

# 6. Run the development server
python manage.py runserver
```

Then open:

- App: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/

## Useful commands

```bash
python manage.py check          # system checks
python manage.py makemigrations # after changing models
python manage.py test user      # run tests
```

## Notes

- `DEBUG = True` and the database/email credentials are set directly in `picom/settings.py`. Do not use these settings in production.
- Uploaded files are stored in `media/`.
