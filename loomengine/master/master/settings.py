# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

import datetime
import json
import os
import random
import socket
import sys
import tempfile
import warnings

def to_boolean(value):
    if value is None:
        return False
    if str(value).upper() == 'FALSE':
        return False
    if str(value).upper() == 'TRUE':
        return True
    raise Exception("Invalid value %s. Expected True or False")

def to_list(value):
    if value is None:
        return []
    value = value.strip(' "\'')
    list = value.lstrip('[').rstrip(']').split(',')
    return [item.strip(' "\'') for item in list]

SETTINGS_DIR = os.path.dirname(__file__)
BASE_DIR = (os.path.join(SETTINGS_DIR, '..'))
sys.path.append(BASE_DIR)

# Security settings
DEBUG = os.getenv('LOOM_DEBUG')
SECRET_KEY = os.getenv(
    'LOOM_MASTER_SECRET_KEY',
    ''.join([random.SystemRandom()\
             .choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)')
             for i in range(50)]))
CORS_ORIGIN_ALLOW_ALL = to_boolean(os.getenv('LOOM_MASTER_CORS_ORIGIN_ALLOW_ALL'))
CORS_ORIGIN_WHITELIST = to_list(os.getenv('LOOM_MASTER_CORS_ORIGIN_WHITELIST'))
ALLOWED_HOSTS = to_list(os.getenv('LOOM_MASTER_ALLOWED_HOSTS', '[]'))

LOG_LEVEL = os.getenv('LOG_LEVEL', 'WARNING').upper()

WORKER_TYPE = os.getenv('WORKER_TYPE', 'LOCAL').upper()
LOOM_STORAGE_TYPE = os.getenv('LOOM_STORAGE_TYPE', 'LOCAL').upper()
LOOM_STORAGE_ROOT = os.getenv('LOOM_STORAGE_ROOT', 'LOCAL').upper()

STATIC_ROOT = os.getenv('LOOM_STATIC_ROOT', '/tmp/static')

MASTER_URL_FOR_WORKER = os.getenv('MASTER_URL_FOR_WORKER', 'http://127.0.0.1:8000')
MASTER_URL_FOR_SERVER = os.getenv('MASTER_URL_FOR_SERVER', 'http://127.0.0.1:8000')
LOOM_STORAGE_ROOT = os.path.expanduser(os.getenv('LOOM_STORAGE_ROOT', '~/loom-data'))
FILE_ROOT_FOR_WORKER = os.path.expanduser(
    os.getenv('FILE_ROOT_FOR_WORKER', LOOM_STORAGE_ROOT))

LOG_DIR = os.path.expanduser(os.getenv('LOG_DIR', '/var/log/loom'))
LOOM_SETTINGS_PATH = os.path.expanduser(os.getenv('LOOM_SETTINGS_PATH','~/.loom/'))

# GCP settings
GCE_EMAIL = os.getenv('GCE_EMAIL')
GCE_PROJECT = os.getenv('GCE_PROJECT', '')
GCE_PEM_FILE_PATH = os.getenv('GCE_PEM_FILE_PATH')
BUCKET_ID = os.getenv('GCE_BUCKET', '')

WORKER_BOOT_DISK_TYPE = os.getenv('WORKER_BOOT_DISK_TYPE')
WORKER_BOOT_DISK_SIZE = os.getenv('WORKER_BOOT_DISK_SIZE')
WORKER_CUSTOM_SUBNET = os.getenv('WORKER_CUSTOM_SUBNET', '')
WORKER_LOCATION = os.getenv('WORKER_LOCATION')
WORKER_NETWORK = os.getenv('WORKER_NETWORK')
WORKER_SCRATCH_DISK_MOUNT_POINT = os.getenv('WORKER_SCRATCH_DISK_MOUNT_POINT')
WORKER_SCRATCH_DISK_TYPE = os.getenv('WORKER_SCRATCH_DISK_TYPE')
WORKER_SCRATCH_DISK_SIZE = os.getenv('WORKER_SCRATCH_DISK_SIZE')
WORKER_SKIP_INSTALLS = os.getenv('WORKER_SKIP_INSTALLS')
WORKER_TAGS = os.getenv('WORKER_TAGS')
WORKER_USES_SERVER_INTERNAL_IP = os.getenv('WORKER_USES_SERVER_INTERNAL_IP')
WORKER_VM_IMAGE = os.getenv('WORKER_VM_IMAGE')

# Database settings
LOOM_MYSQL_PASSWORD = os.getenv('LOOM_MYSQL_PASSWORD')
LOOM_MYSQL_HOST = os.getenv('LOOM_MYSQL_HOST')
LOOM_MYSQL_USER = os.getenv('LOOM_MYSQL_USER')
LOOM_MYSQL_DATABASE = os.getenv('LOOM_MYSQL_DATABASE')
LOOM_MYSQL_PORT = os.getenv('LOOM_MYSQL_PORT', 3306)
LOOM_MYSQL_SSL_CA_CERT_PATH = os.getenv('LOOM_MYSQL_SSL_CA_CERT_PATH')
LOOM_MYSQL_SSL_CLIENT_CERT_PATH = os.getenv('LOOM_MYSQL_SSL_CLIENT_CERT_PATH')
LOOM_MYSQL_SSL_CLIENT_KEY_PATH = os.getenv('LOOM_MYSQL_SSL_CLIENT_KEY_PATH')

# Message broker settings
LOOM_RABBITMQ_PASSWORD = os.getenv('LOOM_RABBITMQ_PASSWORD', 'guest')
LOOM_RABBITMQ_USER = os.getenv('LOOM_RABBITMQ_USER', 'guest')
LOOM_RABBITMQ_VHOST = os.getenv('LOOM_RABBITMQ_VHOST', '/')
LOOM_RABBITMQ_HOST = os.getenv('LOOM_RABBITMQ_HOST', 'rabbitmq')
LOOM_RABBITMQ_PORT = os.getenv('LOOM_RABBITMQ_PORT', '5672')

KEEP_DUPLICATE_FILES = True
FORCE_RERUN = True

# For testing only
TEST_DISABLE_TASK_DELAY = to_boolean(os.getenv('TEST_DISABLE_TASK_DELAY', False))
TEST_NO_AUTO_START_RUNS = to_boolean(os.getenv('TEST_NO_AUTOSTART_RUNS'))
TEST_NO_POSTPROCESS = to_boolean(os.getenv('TEST_NO_POSTPROCESS', False))

# Fixed settings
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_TZ = True
CELERY_ALWAYS_EAGER = True
APPEND_SLASH = True
ROOT_URLCONF = 'master.urls'

# Celery
CELERY_RESULT_BACKEND = 'django-cache'
CELERY_BROKER_URL = 'amqp://%s:%s@%s:%s/%s' \
                    % (LOOM_RABBITMQ_USER, LOOM_RABBITMQ_PASSWORD,
                       LOOM_RABBITMQ_HOST, LOOM_RABBITMQ_PORT,
                       LOOM_RABBITMQ_VHOST)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django_extensions',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'django_celery_results',
    'api',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
#    'django.contrib.auth.middleware.AuthenticationMiddleware',
#    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, "templates")],
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

WSGI_APPLICATION = 'master.wsgi.application'

# Database
if not LOOM_MYSQL_HOST:
    raise Exception(
        "LOOM_MYSQL_HOST is a required setting")
if not LOOM_MYSQL_USER:
    raise Exception(
        "LOOM_MYSQL_USER is a required settings")
if not LOOM_MYSQL_DATABASE:
    raise Exception(
        "LOOM_MYSQL_DATABASE is a required setting")
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': LOOM_MYSQL_HOST,
        'NAME': LOOM_MYSQL_DATABASE,
        'USER': LOOM_MYSQL_USER,
        'PORT': LOOM_MYSQL_PORT,
    }
}
if LOOM_MYSQL_PASSWORD:
    DATABASES['default'].update({
        'PASSWORD': LOOM_MYSQL_PASSWORD
    })
if LOOM_MYSQL_SSL_CA_CERT_PATH \
   or LOOM_MYSQL_SSL_CLIENT_CERT_PATH \
   or LOOM_MYSQL_SSL_CLIENT_KEY_PATH:
    if not (LOOM_MYSQL_SSL_CA_CERT_PATH \
            and LOOM_MYSQL_SSL_CLIENT_CERT_PATH \
            and LOOM_MYSQL_SSL_CLIENT_KEY_PATH):
        raise Exception(
            'One or more required values missing: '\
            'LOOM_MYSQL_SSL_CA_CERT_PATH="%s", '\
            'LOOM_MYSQL_SSL_CLIENT_CERT_PATH="%s", '\
            'LOOM_MYSQL_SSL_CLIENT_KEY_PATH="%s"' % (
                LOOM_MYSQL_SSL_CA_CERT_PATH,
                LOOM_MYSQL_SSL_CLIENT_CERT_PATH,
                LOOM_MYSQL_SSL_CLIENT_KEY_PATH))
    else:
        DATABASES['default'].update({
            'OPTIONS': {
                'ssl': {
                    'ca': LOOM_MYSQL_SSL_CA_CERT_PATH,
                    'cert': LOOM_MYSQL_SSL_CLIENT_CERT_PATH,
                    'key': LOOM_MYSQL_SSL_CLIENT_KEY_PATH
                }
            }
        })

# Logging
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

def _get_django_handler():
    django_logfile = os.path.join(LOG_DIR, 'loom_django.log')
    handler = {
        'class': 'logging.FileHandler',
        'filename': django_logfile,
        'formatter': 'default',
    }
    return handler

def _get_loomengine_handler():
    master_logfile = os.path.join(LOG_DIR, 'loom_master.log')
    handler = {
        'class': 'logging.FileHandler',
        'filename': master_logfile,
        'formatter': 'default',
    }
    return handler

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(levelname)s [%(asctime)s] %(message)s'
            },
        },
    'handlers': {
        'django_handler': _get_django_handler(),
        'loomengine_handler': _get_loomengine_handler(),
        },
    'loggers': {
        'django': {
            'handlers': ['django_handler'],
            'level': LOG_LEVEL,
            },
        'loomengine': {
            'handlers': ['loomengine_handler'],
            'level': LOG_LEVEL,
            },
        'api': { 
            'handlers': ['loomengine_handler'],
            'level': LOG_LEVEL,
            },
        },
    }

STATIC_URL = '/%s/' % os.path.basename(STATIC_ROOT)
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]
