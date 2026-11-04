"""Isolated tests: no real mail, CAPTCHA, uploads or production database."""
from .settings import *  # noqa: F403

DEBUG = False
ALLOWED_HOSTS = ["testserver", "localhost"]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
RECAPTCHA_ENABLED = False
SECURE_SSL_REDIRECT = False
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
