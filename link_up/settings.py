"""Django configuration for local development and PythonAnywhere WSGI hosting."""
from pathlib import Path

from decouple import Csv, config
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = config("SECRET_KEY")
if SECRET_KEY == "replace-with-a-new-random-secret-key":
    raise ImproperlyConfigured("Generate a new SECRET_KEY before running LinkUp.")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1,[::1]", cast=Csv())
CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", default="", cast=Csv())

INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    "crispy_forms", "crispy_bootstrap4", "linkup.apps.LinkupConfig",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware", "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "link_up.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "linkup" / "templates"], "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.debug", "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth", "django.contrib.messages.context_processors.messages",
        "linkup.context_processors.recaptcha",
    ]},
}]
WSGI_APPLICATION = "link_up.wsgi.application"
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Start new installs with a clean database, not the historical demo database in Git.
DATA_DIR = BASE_DIR / "var"
DATA_DIR.mkdir(exist_ok=True)
DATABASES = {"default": {
    "ENGINE": "django.db.backends.sqlite3",
    "NAME": config("DATABASE_NAME", default="") or DATA_DIR / "linkup.sqlite3",
    "OPTIONS": {"timeout": 20},
}}
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LANGUAGE_CODE = "en-gb"
TIME_ZONE = "Europe/London"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_ROOT = Path(config("MEDIA_ROOT", default=str(DATA_DIR / "media")))
MEDIA_URL = "/media/"
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap4"
CRISPY_TEMPLATE_PACK = "bootstrap4"

GOOGLE_RECAPTCHA_SITE_KEY = config("GOOGLE_RECAPTCHA_SITE_KEY", default="")
GOOGLE_RECAPTCHA_SECRET_KEY = config("GOOGLE_RECAPTCHA_SECRET_KEY", default="")
if bool(GOOGLE_RECAPTCHA_SITE_KEY) != bool(GOOGLE_RECAPTCHA_SECRET_KEY):
    raise ImproperlyConfigured("Configure both reCAPTCHA keys, or leave both empty.")
RECAPTCHA_ENABLED = bool(GOOGLE_RECAPTCHA_SITE_KEY)

EMAIL_BACKEND = config("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = config("EMAIL_HOST", default="")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="webmaster@localhost")
EMAIL_TIMEOUT = 10
LOGIN_REDIRECT_URL = "profile"
LOGIN_URL = "login"

# PythonAnywhere terminates TLS at its trusted front-end proxy.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=not DEBUG, cast=bool)
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", default=3600 if not DEBUG else 0, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
X_FRAME_OPTIONS = "DENY"
