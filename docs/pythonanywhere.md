# Deploy LinkUp on PythonAnywhere

Use PythonAnywhere's **manual configuration** workflow for an existing Django app, with Python 3.13 and a matching virtualenv. Available Python versions depend on your account's system image; Python 3.13 is available on the `innit` image. Python 3.12 is also supported by this app.

Official guides:
- [Python versions](https://help.pythonanywhere.com/pages/PythonVersions/)
- [Deploy an existing Django project](https://help.pythonanywhere.com/pages/DeployExistingDjangoProject/)
- [Django static files](https://help.pythonanywhere.com/pages/DjangoStaticFiles/)

If updating an existing deployment, back up its database, uploads and .env outside the checkout before pulling this upgrade. The previously tracked .env is removed from Git by this change.

## 1. Get the code and create an environment

After this upgrade is merged, open a Bash console:

```bash
git clone https://github.com/aji2106/linkuappfinal.git
cd ~/linkuappfinal
mkvirtualenv --python=/usr/bin/python3.13 linkup
python -m pip install -r requirements.txt
cp .env.example .env
```

You can also upload the source through PythonAnywhere's Files tab. Do not put an access token into a Git remote URL.

## 2. Configure the app

Generate a new secret:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Edit `~/linkuappfinal/.env` with:

```dotenv
SECRET_KEY=your-new-random-secret
DEBUG=False
ALLOWED_HOSTS=YOUR_USERNAME.pythonanywhere.com
CSRF_TRUSTED_ORIGINS=https://YOUR_USERNAME.pythonanywhere.com
```

Use your actual hostname, including any regional/custom domain. Never use `ALLOWED_HOSTS=*` or turn on debug on the public site. The default production settings use HTTPS redirects and secure session/CSRF cookies.

For an initial low-traffic demo, the default SQLite database is the simplest setup:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
python manage.py check --deploy
```

The deployment check can advise on optional HSTS subdomain/preload settings. These are deliberately off because the app should not impose a policy on unrelated subdomains.

## 3. Create the web app

On the **Web** tab:
1. Add a web app using **Manual configuration**, then select **Python 3.13**.
2. Set the source and working directory to `/home/YOUR_USERNAME/linkuappfinal`.
3. Set the virtualenv to `/home/YOUR_USERNAME/.virtualenvs/linkup`.
4. Open the WSGI configuration file linked on the Web tab and replace its contents with this, using your username:

```python
import os
import sys

project_path = "/home/YOUR_USERNAME/linkuappfinal"
if project_path not in sys.path:
    sys.path.insert(0, project_path)

os.environ["DJANGO_SETTINGS_MODULE"] = "link_up.settings"
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

Django loads the project-root `.env` through python-decouple. The Web tab's WSGI file is separate from the project's `link_up/wsgi.py`.

Do not use `runserver`, the old Heroku Procfile, or `--insecure` to host the app.

## 4. Configure static files and uploads

Add these mappings in the Web tab:

| URL | Directory |
| --- | --- |
| `/static/` | `/home/YOUR_USERNAME/linkuappfinal/staticfiles` |
| `/media/` | `/home/YOUR_USERNAME/linkuappfinal/var/media` |

Create the upload directory if needed:

```bash
mkdir -p ~/linkuappfinal/var/media
```

Bundled default profile images are static assets. User uploads and runtime databases live in `var/`, not the source tree. Do not map the historical repository-wide `media/` directory to a public URL; it contains legacy files unrelated to current uploads.

Reload the web app. Verify the homepage, registration, login, a poll, an event and image uploads. Check the error log on the Web tab if anything fails.

## 5. Configure email and optional spam protection

The default console email backend is for testing; it writes mail to logs and does **not** deliver notifications or password-reset emails. Configure SMTP before relying on those features:

```dotenv
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=your-smtp-provider
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-smtp-user
EMAIL_HOST_PASSWORD=your-new-smtp-password
DEFAULT_FROM_EMAIL=your-verified-sender@example.com
```

Confirm that your PythonAnywhere plan permits access to your email provider. Sender verification and provider credentials must be configured separately.

To enable reCAPTCHA on registration, configure both `GOOGLE_RECAPTCHA_SITE_KEY` and `GOOGLE_RECAPTCHA_SECRET_KEY` for the live domain. With both empty, signup uses Django's normal validation without CAPTCHA. With both configured, failed verification or network errors prevent account creation. Before inviting public signups, decide on spam protection and test it on the live host.

## Existing data and uploads

Do not delete an existing live database. Back up the database and uploads before changing runtimes.

- New installs use a clean `var/linkup.sqlite3`, not the old database committed in Git.
- To reuse an existing SQLite database, set `DATABASE_NAME` to its absolute path and test `migrate` against a backup first.
- The old app uses SQLite. To keep existing data, point DATABASE_NAME at that file rather than starting with the new empty runtime database.
- To preserve uploaded images, copy the existing `profile_pics/` folders into the configured upload directory, preserving filenames. `MEDIA_ROOT` can override that directory if necessary.
- Protect and regularly back up the runtime database and uploads. SQLite suits a small demonstration; reassess storage for a busy multi-user deployment.

## Future updates

```bash
cd ~/linkuappfinal
workon linkup
git pull --ff-only
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py check
```

Then reload the Web app. Replace previously committed credentials at their providers; deleting a file from the latest commit does not remove old secrets from Git history.
