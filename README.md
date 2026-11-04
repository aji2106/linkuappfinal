# LinkUp

LinkUp is a Django app for scheduling events, comparing date/location choices, creating polls and managing a profile.

## Supported runtime

- Python 3.12 or 3.13; Python 3.13 is the PythonAnywhere deployment target.
- Django 5.2 LTS, using the current security patch in the 5.2 series.
- Bootstrap 4-compatible forms and interface. No JavaScript build step is required.

The upgrade keeps the existing model IDs and initial migration. Do not delete migrations or run `makemigrations` just to deploy.

## Run locally

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

On Windows, activate with `.venv\Scripts\Activate.ps1`.

Generate a new application secret, put it in `.env`, and keep `DEBUG=True` for local development:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

New installations use `var/linkup.sqlite3` and `var/media/`. These are ignored by Git. Historical database files and uploaded media from the old project are not loaded automatically.

## Tests and checks

Set a disposable `SECRET_KEY` in your shell, then run:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test --settings=link_up.test_settings
python -m pip check
```

The test settings use an in-memory database, temporary upload folders, local email capture and no real reCAPTCHA calls. They must never be used to host the app.

See [the PythonAnywhere deployment guide](docs/pythonanywhere.md) for production setup, static files, uploads, email and existing-data considerations.

## What changed in the upgrade

- Replaced Django 2.1 and unused legacy dependencies with the Django 5.2 stack.
- Removed the committed environment file and moved deployment settings into environment configuration.
- Replaced removed template tags and fixed a malformed event-choice template.
- Preserved Bootstrap 4 while consolidating jQuery, Bootstrap and Moment assets.
- Fixed signup validation, image defaults, private item visibility, vote validation, cross-poll/event choices, empty results and overnight date durations.
- Close and logout actions now require a CSRF-protected POST.
- Added regression coverage and Python 3.12/3.13 CI configuration.

Credentials previously committed to Git remain in repository history. Replace them at their providers before hosting. This upgrade does not rewrite history or rotate external service credentials.
