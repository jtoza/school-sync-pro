"""
Django settings for school_app project.
Optimized for Railway PostgreSQL + Render hosting.
"""

import os
import sys
from dotenv import load_dotenv
import dj_database_url

# Load environment variables
load_dotenv()

# Build paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Security
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-this-in-production')
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Allowed hosts - FIXED
allowed_hosts_str = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,127.0.1.1,.onrender.com')
ALLOWED_HOSTS = [host.strip() for host in allowed_hosts_str.split(',') if host.strip()]
# Ensure common localhost aliases are present
for host in ('127.0.0.1', 'localhost'):
    if host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(host)

# Render external hostname support
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME and RENDER_EXTERNAL_HOSTNAME.strip():
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME.strip())

print(f"🌐 ALLOWED_HOSTS: {ALLOWED_HOSTS}")

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
    'apps.parents',
    'apps.idcards',
    'apps.sync',
    'student_portfolio',
    'backup_manager',
    'apps.homework',
    'chatroom',
    'channels',
    'apps.books',
    'apps.transport',
    'lessonplans.apps.LessonplansConfig',
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

# ============================================
# DATABASE CONFIGURATION - RAILWAY POSTGRESQL
# ============================================
def get_database_config():
    """
    Railway PostgreSQL configuration
    """
    db_url = os.getenv('DATABASE_URL')
    
    if db_url and db_url.strip():
        print(f"🚂 DATABASE_URL found! Connecting to Railway PostgreSQL...")
        
        try:
            # Parse database URL
            db_config = dj_database_url.parse(
                db_url.strip(),
                conn_max_age=600,
                conn_health_checks=True,
                ssl_require=True,
            )
            
            # Ensure PostgreSQL backend
            db_config['ENGINE'] = 'django.db.backends.postgresql'
            
            # Add SSL requirement
            db_config.setdefault('OPTIONS', {})
            db_config['OPTIONS']['sslmode'] = 'require'
            
            # Show connection info (without password)
            safe_url = db_url.replace(db_url.split('@')[0].split(':')[2], '***')
            print(f"✅ Configured for: {safe_url}")
            
            return {'default': db_config}
            
        except Exception as e:
            print(f"❌ Error parsing DATABASE_URL: {e}")
            print("📁 Falling back to SQLite")
    else:
        print("⚠️  DATABASE_URL not found or empty")
    
    # Fallback to SQLite
    print("📁 Using SQLite for local development")
    return {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
        }
    }

DATABASES = get_database_config()

# ============================================
# CSRF CONFIGURATION - FIXED FOR DJANGO 4.0+
# ============================================
csrf_origins_str = os.getenv('CSRF_TRUSTED_ORIGINS', '')
CSRF_TRUSTED_ORIGINS = []

if csrf_origins_str and csrf_origins_str.strip():
    origins = [origin.strip() for origin in csrf_origins_str.split(',') if origin.strip()]
    # Filter out invalid origins (must start with http:// or https://)
    valid_origins = []
    for origin in origins:
        if origin.startswith('http://') or origin.startswith('https://'):
            valid_origins.append(origin)
        else:
            print(f"⚠️  Skipping invalid CSRF origin (must start with http:// or https://): '{origin}'")
    CSRF_TRUSTED_ORIGINS = valid_origins

# Add default Render/Railway origins
CSRF_TRUSTED_ORIGINS.extend([
    "https://*.onrender.com",
    "https://*.railway.app",
])

# Remove duplicates
CSRF_TRUSTED_ORIGINS = list(set(CSRF_TRUSTED_ORIGINS))
print(f"🔒 CSRF Trusted Origins: {CSRF_TRUSTED_ORIGINS}")

# ============================================
# REST OF YOUR SETTINGS...
# ============================================

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

# Static files
STATIC_URL = "/static/"
STATICFILES_DIRS = (os.path.join(BASE_DIR, "static"),)
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Media files
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = "/media/"

# Authentication
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

# Session settings
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 10800

# Security settings for production
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    
    # Render proxy support
    USE_X_FORWARDED_HOST = True
    USE_X_FORWARDED_PORT = True

# Channels configuration (WebSockets)
REDIS_URL = os.getenv('REDIS_URL')
if REDIS_URL and REDIS_URL.strip():
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                "hosts": [REDIS_URL],
            },
        },
    }
else:
    # Local development fallback
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer'
        }
    }

# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', '')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('EMAIL_HOST_USER', 'no-reply@schoolapp.com')

# Payment gateway
LIPANA_PRODUCTION_KEY = os.getenv('LIPANA_PRODUCTION_KEY', '')
LIPANA_SECRET_KEY = os.getenv('LIPANA_SECRET_KEY', '')
LIPANA_ACCESS_TOKEN_URL = "https://lipana.dev/api/v1/auth/token/"
LIPANA_STK_PUSH_URL = "https://lipana.dev/api/v1/mpesa/stk/push/"

# SMS configuration
AFRICASTALKING_USERNAME = os.getenv('AFRICASTALKING_USERNAME', '')
AFRICASTALKING_API_KEY = os.getenv('AFRICASTALKING_API_KEY', '')
AFRICASTALKING_SENDER_ID = os.getenv('AFRICASTALKING_SENDER_ID', '')

# Crispy Forms
CRISPY_TEMPLATE_PACK = "bootstrap4"

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
    },
}

# Data upload limits
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10240

# Remove the database test that causes the warning
print(f"🚀 Django configured. DEBUG={DEBUG}")
