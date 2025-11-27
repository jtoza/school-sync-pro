"""
Django settings for school_app project.

Production-ready configuration for Railway, Render, or local development.
"""

import os
from dotenv import load_dotenv
import dj_database_url

# Load environment variables from .env if present
load_dotenv()

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'unsafe-default-secret')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True') == 'True'

# Allowed hosts
ALLOWED_HOSTS = os.getenv(
    'ALLOWED_HOSTS',
    'localhost,127.0.0.1,edusync-5jgu.onrender.com,school-management-framework.onrender.com,school-sync-pro-production.up.railway.app,192.168.100.12,strengthen-faces-del-newcastle.trycloudflare.com'
).split(',')

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "widget_tweaks",
    "crispy_forms",
    "apps.corecode",
    "apps.students",
    "apps.staffs",
    "apps.finance",
    "apps.result",
    "attendance",
    "crispy_bootstrap4",
    'apps.idcards',
    'apps.sync',
    'student_portfolio',
    'backup_manager',
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.corecode.middleware.SiteWideConfigs",
]

# Security headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False
X_FRAME_OPTIONS = 'SAMEORIGIN'

# Content Security Policy (CSP)
CSP_DEFAULT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", 'https://fonts.googleapis.com')
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'")
CSP_FONT_SRC = ("'self'", 'https://fonts.gstatic.com', 'data:')
CSP_IMG_SRC = ("'self'", 'data:')
CSP_CONNECT_SRC = ("'self'",)

ROOT_URLCONF = "school_app.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.corecode.context_processors.site_defaults",
            ],
        },
    },
]

WSGI_APPLICATION = "school_app.wsgi.application"

# -------------------------------
# DATABASE CONFIGURATION
# -------------------------------
# Use SQLite for local development by default
DEFAULT_LOCAL_DB = f"sqlite:///{os.path.join(BASE_DIR, 'db.sqlite3')}"

# Use DATABASE_URL if provided (Railway or any production host)
DATABASE_URL = os.environ.get("DATABASE_URL", DEFAULT_LOCAL_DB)

# Parse database URL with dj_database_url
DATABASES = {
    "default": dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=600,
        ssl_require=not DEBUG,  # SSL required in production
    )
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",},
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10240

STATIC_URL = "/static/"
STATICFILES_DIRS = (os.path.join(BASE_DIR, "static"),)
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = "/media/"

LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 10800  # 3 hours

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "{levelname} {asctime} {message}", "style": "{"},
    },
    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "when": "W6",
            "interval": 4,
            "backupCount": 3,
            "encoding": "utf8",
            "filename": os.path.join(BASE_DIR, "debug.log"),
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {"handlers": ["file"], "level": "INFO", "propagate": True,},
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Crispy Forms
CRISPY_TEMPLATE_PACK = "bootstrap4"

# CSRF Trusted Origins
CSRF_TRUSTED_ORIGINS = [
    "https://strengthen-faces-del-newcastle.trycloudflare.com",
    "https://school-management-framework.onrender.com",
    "https://edusync-5jgu.onrender.com",
    "https://school-sync-pro-production.up.railway.app",
]

# Backup configuration
BACKUP_CONFIG = {
    'ENABLED': True,
    'BACKUP_DIR': 'backups/',
    'EXPORT_DIR': 'exports/',
    'RETENTION_DAYS': 30,
    'CLOUD_STORAGE': False,
}

# Export formats
EXPORT_FORMATS = ['excel', 'pdf']

# Email defaults
DEFAULT_FROM_EMAIL = 'no-reply@yourschool.com'
BACKUP_EMAIL_TO = ['youraddress@example.com']
