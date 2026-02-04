import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-default-key-change-me')

DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '127.0.0.1').split(',')

# CSRF Trusted Origins for Vercel
CSRF_TRUSTED_ORIGINS = ['https://*.vercel.app']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'csp',
    'app',
    'users',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'csp.middleware.CSPMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'mitsulist.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'app/templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'mitsulist.wsgi.app'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'mitsulist_db'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASS', 'mitsulist_pass'),
        'HOST': os.getenv('DB_HOST', '127.0.0.1'),
        'PORT': os.getenv('DB_PORT', '5433'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / "app/static"]

# Media files (Uploaded by user)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# =============================================================================
# SECURITY SETTINGS
# =============================================================================

# HTTPS and SSL Settings (Production)
SECURE_SSL_REDIRECT = not DEBUG  # Redirect HTTP to HTTPS in production
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0  # 1 year HSTS
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG

# Secure Cookies (Production)
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# Security Headers
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

# =============================================================================
# CONTENT SECURITY POLICY (CSP)
# =============================================================================

# Django-CSP 4.0+ format
CONTENT_SECURITY_POLICY = {
    'DIRECTIVES': {
        'default-src': ("'self'",),
        'script-src': (
            "'self'",
            'https://cdnjs.cloudflare.com',  # Font Awesome
        ),
        'style-src': (
            "'self'",
            "'unsafe-inline'",  # Required for inline styles in some cases
            'https://fonts.googleapis.com',
            'https://cdnjs.cloudflare.com',
        ),
        'font-src': (
            "'self'",
            'https://fonts.gstatic.com',
            'https://cdnjs.cloudflare.com',
        ),
        'img-src': (
            "'self'",
            'https:',  # Allow images from HTTPS sources (anime posters from API)
            'data:',   # Allow data URIs
        ),
        'connect-src': (
            "'self'",
            'https://api.jikan.moe',  # Jikan API
        ),
        'frame-ancestors': ("'none'",),  # Same as X-Frame-Options: DENY
        'base-uri': ("'self'",),
        'object-src': ("'none'",),
    }
}

# =============================================================================
# RATE LIMITING
# =============================================================================

# Cache backend for rate limiting (uses default cache)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Rate limit settings
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'

# Authentication Redirects
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'

