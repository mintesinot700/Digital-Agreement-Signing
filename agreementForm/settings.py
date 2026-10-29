"""
Django settings for agreementForm project.

Environment-driven configuration:
- Secrets, DEBUG, hosts, database and SMTP all come from environment variables.
- Works out of the box with SQLite for local development.
- Set DATABASE_URL (or the individual POSTGRES_* variables) in production to use PostgreSQL.

See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/
"""
import os
from datetime import timedelta
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


def env(key, default=None):
    """Read an environment variable, treating empty strings as unset."""
    value = os.environ.get(key)
    if value is None or value == '':
        return default
    return value


def env_bool(key, default=False):
    return str(env(key, default)).strip().lower() in ('1', 'true', 'yes', 'on')


def env_list(key, default=''):
    return [item.strip() for item in str(env(key, default)).split(',') if item.strip()]


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env(
    'SECRET_KEY',
    'django-insecure-k6(d%781#!8=j(a&m6g%43by24^)=6-pk4otc)+6w3dow-g!8f'
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env_bool('DEBUG', False)

# Add your local development hosts (comma-separated env var in production)
ALLOWED_HOSTS = env_list(
    'ALLOWED_HOSTS',
    'localhost,127.0.0.1,0.0.0.0,192.168.8.177,10.0.2.2'
)

CSRF_TRUSTED_ORIGINS = env_list(
    'CSRF_TRUSTED_ORIGINS',
    'http://localhost:3000,http://127.0.0.1:3000'
)

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',  # enables refresh-token blacklisting on logout
    'corsheaders',

    # Local apps
    'agreement.apps.AgreementConfig',
    'Accounts',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        *(['rest_framework.renderers.BrowsableAPIRenderer'] if DEBUG else []),
    ],
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=int(env('ACCESS_TOKEN_MINUTES', 60))),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=int(env('REFRESH_TOKEN_DAYS', 7))),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'UPDATE_LAST_LOGIN': True,
}

# Refresh-token cookie configuration (frontend sends an empty POST to
# /api/token/refresh/ and expects the refresh token in this HttpOnly cookie)
REFRESH_COOKIE_NAME = 'refresh_token'
REFRESH_COOKIE_MAX_AGE = int(env('REFRESH_TOKEN_DAYS', 7)) * 24 * 60 * 60
REFRESH_COOKIE_SECURE = env_bool('COOKIE_SECURE', not DEBUG)  # True behind HTTPS
REFRESH_COOKIE_HTTPONLY = True
REFRESH_COOKIE_SAMESITE = env('COOKIE_SAMESITE', 'Lax')  # use 'None' when frontend/API are on different sites over HTTPS

AUTH_USER_MODEL = 'Accounts.UserAccounts'

# Add this line to allow your content to be framed
X_FRAME_OPTIONS = 'SAMEORIGIN'

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# CORS: comma-separated list in production, e.g.
# CORS_ALLOWED_ORIGINS=https://app.example.com,https://admin.example.com
CORS_ALLOWED_ORIGINS = env_list(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:3000,http://127.0.0.1:3000,http://192.168.8.177:3000'
)
CORS_ALLOW_ALL_ORIGINS = env_bool('CORS_ALLOW_ALL_ORIGINS', False)
CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = [
    'content-type',
    'authorization',
    'x-csrftoken',
    'accept',
]

CORS_ALLOW_METHODS = [
    'GET',
    'POST',
    'PUT',
    'DELETE',
    'OPTIONS',
    'PATCH',
]

ROOT_URLCONF = 'agreementForm.urls'

# React production build (served by Django) — used by the SPA catch-all view.
REACT_BUILD_DIR = BASE_DIR / 'agreement' / 'templates' / 'ashewa' / 'my-first-app' / 'build'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [REACT_BUILD_DIR],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'agreementForm.wsgi.application'


# Database
# ---------------------------------------------------------------
# Default: SQLite (zero-config local development).
# Production: set DATABASE_URL=postgres://user:password@host:5432/dbname
# or the individual POSTGRES_* environment variables.
def _databases_from_env():
    from urllib.parse import urlparse

    database_url = env('DATABASE_URL')
    if database_url:
        parsed = urlparse(database_url)
        scheme = (parsed.scheme or '').lower()
        if scheme.startswith('postgres'):
            return {
                'default': {
                    'ENGINE': 'django.db.backends.postgresql',
                    'NAME': parsed.path.lstrip('/'),
                    'USER': parsed.username or '',
                    'PASSWORD': parsed.password or '',
                    'HOST': parsed.hostname or 'localhost',
                    'PORT': str(parsed.port or 5432),
                    'OPTIONS': {'client_encoding': 'utf-8'},
                }
            }
        if scheme in ('sqlite', 'file', 'sqlite3'):
            # Conventions (same as dj-database-url):
            #   sqlite:///relative.db        -> relative to BASE_DIR
            #   sqlite:////absolute/path.db  -> absolute path
            #   file:/absolute/path.db       -> absolute path
            db_path = parsed.path or '/db.sqlite3'
            if scheme == 'file' or db_path.startswith('//'):
                db_path = db_path.lstrip('/') or 'db.sqlite3'
                if not os.path.isabs(db_path):
                    db_path = '/' + db_path
            else:
                db_path = str(BASE_DIR / db_path.lstrip('/'))
            return {
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': db_path,
                }
            }
        # Unknown scheme — fall through to the defaults below.

    if env('POSTGRES_DB') or env('POSTGRES_NAME'):
        return {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': env('POSTGRES_DB', env('POSTGRES_NAME', 'Digital_Agreement_Form')),
                'USER': env('POSTGRES_USER', 'postgres'),
                'PASSWORD': env('POSTGRES_PASSWORD', ''),
                'HOST': env('POSTGRES_HOST', 'localhost'),
                'PORT': env('POSTGRES_PORT', '5432'),
                'OPTIONS': {'client_encoding': 'utf-8'},
            }
        }

    return {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


DATABASES = _databases_from_env()


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = env('TIME_ZONE', 'UTC')

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    str(REACT_BUILD_DIR / 'static'),
]
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Media files settings
MEDIA_URL = '/media/'
MEDIA_ROOT = Path(env('MEDIA_ROOT', str(BASE_DIR / 'media')))

# Maximum upload size (5 MB)
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024


# Email configuration
# ---------------------------------------------------------------
# Development default: console backend (emails printed to the server log).
# Production: set EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
# plus the SMTP_* variables (works with Gmail app passwords, Brevo, Mailgun, etc.)
EMAIL_BACKEND = env(
    'EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend'
)
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', 'Digital Agreement Signing <no-reply@example.com>')
EMAIL_HOST = env('EMAIL_HOST', '')
EMAIL_PORT = int(env('EMAIL_PORT', 587))
EMAIL_HOST_USER = env('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = env_bool('EMAIL_USE_TLS', True)
EMAIL_USE_SSL = env_bool('EMAIL_USE_SSL', False)

# Security hardening (active only when DEBUG=False)
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = env_bool('SECURE_SSL_REDIRECT', False)
    SECURE_HSTS_SECONDS = int(env('SECURE_HSTS_SECONDS', 0))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
