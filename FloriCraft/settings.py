"""
Django settings for FloriCraft project.
"""

from pathlib import Path
import os
from dotenv import load_dotenv
import dj_database_url 


BASE_DIR = Path(__file__).resolve().parent.parent


load_dotenv(BASE_DIR / '.env')


SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = ['api.floricraft.ru', 'localhost', 'backend', '127.0.0.1']

# Posiflora settings
POSIFLORA_URL = os.getenv('POSIFLORA_URL', 'https://floricraft.posiflora.com/api/v1')
POSIFLORA_USER = os.getenv('POSIFLORA_USER')
POSIFLORA_PASSWORD = os.getenv('POSIFLORA_PASSWORD')

# YooKassa settings
YOOKASSA_SHOP_ID = os.getenv('YOOKASSA_SHOP_ID')
YOOKASSA_SECRET_KEY = os.getenv('YOOKASSA_SECRET_KEY')

# SMSC settings
SMSC_LOGIN = os.getenv('SMSC_LOGIN')
SMSC_PASSWORD = os.getenv('SMSC_PASSWORD')
SMSC_DEBUG = os.getenv('SMSC_DEBUG', 'False') == 'True'

# Telegram Bot settings
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'apps.core.apps.CoreConfig',
    'apps.common.apps.CustomAuthConfig',
    'apps.custom_auth.apps.CustomAuthConfig',
    'apps.cart.apps.CartConfig',
    'apps.orders.apps.OrdersConfig',
    'apps.posiflora.apps.PosifloraConfig',
    'apps.telegram.apps.TelegramConfig',
    'corsheaders',
    'drf_spectacular',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ALLOWED_ORIGINS = [
    'https://floricraft.ru',
    'https://www.floricraft.ru',
    'https://admin.floricraft.ru',
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_METHODS = [
    "GET",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
    "OPTIONS",
]

CORS_ALLOW_HEADERS = [
    "authorization",
    "content-type",
    "x-csrftoken",
]

ROOT_URLCONF = 'FloriCraft.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
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

WSGI_APPLICATION = 'FloriCraft.wsgi.application'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'apps.custom_auth.authentication.CookieUserAuthentication',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

DATABASES = {
    'default': dj_database_url.parse(
        os.environ.get('DATABASE_URL'),
        conn_max_age=600,
        ssl_require=False
    )
}

TELEGRAM_BOT_API_URL = os.environ.get('TELEGRAM_BOT_API_URL', 'http://localhost:8000')
TELEGRAM_BOT_API_KEY = os.environ.get('TELEGRAM_BOT_API_KEY', '')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'apps.orders': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'FloriCraft API',
    'DESCRIPTION': 'API для цветочного интернет-магазина FloriCraft с интеграцией Posiflora',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': '/api/',
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
    },
    'TAGS': [
        {'name': 'Posiflora Products', 'description': 'Управление товарами из Posiflora API'},
        {'name': 'Cart', 'description': 'Управление корзиной'},
        {'name': 'Orders', 'description': 'Управление заказами и платежами'},
        {'name': 'Auth', 'description': 'Аутентификация и авторизация'},
    ],
}

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'apps.posiflora.services.products': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
