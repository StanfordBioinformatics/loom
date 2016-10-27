# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

import datetime
import os
import random
import socket
import sys
import tempfile
import warnings

BASE_DIR = os.path.dirname(__file__)
WEBPORTAL_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..', 'portal'))


# Get settings from the environment and expand paths if needed
WORKER_TYPE = os.getenv('WORKER_TYPE', 'LOCAL')
MASTER_URL_FOR_WORKER = os.getenv('MASTER_URL_FOR_WORKER', 'http://127.0.0.1:8000')
MASTER_URL_FOR_SERVER = os.getenv('MASTER_URL_FOR_SERVER', 'http://127.0.0.1:8000')
FILE_ROOT = os.getenv('FILE_ROOT', tempfile.mkdtemp())
FILE_ROOT_FOR_WORKER = os.getenv('FILE_ROOT_FOR_WORKER', '~/loomdata')
FILE_SERVER_TYPE = os.getenv('FILE_SERVER_TYPE', 'LOCAL')
LOGS_DIR = os.getenv('LOGS_DIR')
LOOM_SETTINGS_PATH = os.path.expanduser(os.getenv('LOOM_SETTINGS_PATH','~/.loom/'))

PROJECT_ID = os.getenv('GCE_PROJECT', '')   # Used by loom.utils.filemanager.GoogleStorageSource and GoogleStorageDestination
                                            # Retrieved but not used when filemanager is LocalSource and LocalDestination, so need to set a default value
BUCKET_ID = os.getenv('GCE_BUCKET', '')
DOCKER_FULL_NAME = os.getenv('DOCKER_FULL_NAME')
DOCKER_TAG = os.getenv('DOCKER_TAG')
GCE_EMAIL = os.getenv('GCE_EMAIL')
GCE_INI_PATH = os.getenv('GCE_INI_PATH')
GCE_PEM_FILE_PATH = os.getenv('GCE_PEM_FILE_PATH')
GCE_SSH_KEY_FILE = os.getenv('GCE_SSH_KEY_FILE')
SERVER_SKIP_INSTALLS = os.getenv('SERVER_SKIP_INSTALLS')
WORKER_BOOT_DISK_TYPE = os.getenv('WORKER_BOOT_DISK_TYPE')
WORKER_BOOT_DISK_SIZE = os.getenv('WORKER_BOOT_DISK_SIZE')
WORKER_LOCATION = os.getenv('WORKER_LOCATION')
WORKER_NETWORK = os.getenv('WORKER_NETWORK')
WORKER_SCRATCH_DISK_MOUNT_POINT = os.getenv('WORKER_SCRATCH_DISK_MOUNT_POINT')
WORKER_SCRATCH_DISK_TYPE = os.getenv('WORKER_SCRATCH_DISK_TYPE')
WORKER_SCRATCH_DISK_SIZE = os.getenv('WORKER_SCRATCH_DISK_SIZE')
WORKER_SKIP_INSTALLS = os.getenv('WORKER_SKIP_INSTALLS')
WORKER_TAGS = os.getenv('WORKER_TAGS')
WORKER_USES_SERVER_INTERNAL_IP = os.getenv('WORKER_USES_SERVER_INTERNAL_IP')
WORKER_VM_IMAGE = os.getenv('WORKER_VM_IMAGE')

HASH_FUNCTION = 'md5'

KEEP_DUPLICATE_FILES = True
FORCE_RERUN = True

HARD_STOP_ON_CANCEL = True
HARD_STOP_ON_FAIL = True

DISABLE_AUTO_PUSH = False

CORS_ORIGIN_ALLOW_ALL = os.getenv('CORS_ORIGIN_ALLOW_ALL', 'false').upper() == 'TRUE'
CORS_ORIGIN_WHITELIST = os.getenv('CORS_ORIGIN_WHITELIST', '').split(',')


SECRET_KEY = os.getenv('SECRET_KEY',
                       ''.join([random.SystemRandom().choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(50)]))

# TODO
# if os.getenv('LOOM_DEBUG_TRUE'):
DEBUG = True
TEMPLATE_DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1']

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes', #required by polymorphic
    'django_extensions',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'polymorphic',
    'rest_framework',
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

ROOT_URLCONF = 'loomengine.master.urls'

WSGI_APPLICATION = 'loomengine.master.wsgi.application'

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
}

APPEND_SLASH = False

LOOM_MYSQL_PASSWORD = os.getenv('LOOM_MYSQL_PASSWORD')
LOOM_MYSQL_HOST = os.getenv('LOOM_MYSQL_HOST')
LOOM_MYSQL_USER = os.getenv('LOOM_MYSQL_USER')
LOOM_MYSQL_DB_NAME = os.getenv('LOOM_MYSQL_DB_NAME')
LOOM_MYSQL_PORT = os.getenv('LOOM_MYSQL_PORT')
LOOM_MYSQL_SSL_CA_CERT_PATH = os.getenv('LOOM_MYSQL_SSL_CA_CERT_PATH')
LOOM_MYSQL_SSL_CLIENT_CERT_PATH = os.getenv('LOOM_MYSQL_SSL_CLIENT_CERT_PATH')
LOOM_MYSQL_SSL_CLIENT_KEY_PATH = os.getenv('LOOM_MYSQL_SSL_CLIENT_KEY_PATH')



if LOOM_MYSQL_HOST:
    if not LOOM_MYSQL_USER:
        raise Exception(
            "LOOM_MYSQL_HOST is set, but couldn't find LOOM_MYSQL_USER")
    if not LOOM_MYSQL_PASSWORD:
        raise Exception(
            "LOOM_MYSQL_HOST is set, but couldn't find LOOM_MYSQL_PASSWORD")
    if not LOOM_MYSQL_DB_NAME:
        raise Exception(
            "LOOM_MYSQL_HOST is set, but couldn't find LOOM_MYSQL_DB_NAME")
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'HOST': LOOM_MYSQL_HOST,
            'NAME': LOOM_MYSQL_DB_NAME,
            'USER': LOOM_MYSQL_USER,
            'PASSWORD': LOOM_MYSQL_PASSWORD,
        }
    }
    if LOOM_MYSQL_PORT:
        DATABASES['default'].update({
            'PORT': LOOM_MYSQL_PORT
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
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(LOOM_SETTINGS_PATH, 'loom-database.sqlite3')
        }
    }

def _get_django_handler():
    DJANGO_LOGFILE = os.getenv('DJANGO_LOGFILE', None)
    if DJANGO_LOGFILE is not None:
        handler = {
            'class': 'logging.FileHandler',
            'filename': DJANGO_LOGFILE,
            'formatter': 'default',
            }
    else:
        handler = {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            }
    return handler

def _get_loomengine_handler():
    LOOM_MASTER_LOGFILE = os.getenv('LOOM_MASTER_LOGFILE', None)
    if LOOM_MASTER_LOGFILE  is not None:
        if not os.path.exists(os.path.dirname(LOOM_MASTER_LOGFILE)):
            os.makedirs(os.path.dirname(LOOM_MASTER_LOGFILE))
        handler = {
            'class': 'logging.FileHandler',
            'filename': LOOM_MASTER_LOGFILE,
            'formatter': 'default',
            }
    else:
        handler = {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            }
    return handler

def _get_log_level():
    DEFAULT_LOG_LEVEL = 'WARNING'
    LOG_LEVEL = os.getenv('LOG_LEVEL', DEFAULT_LOG_LEVEL)
    return LOG_LEVEL.upper()

LOG_LEVEL = _get_log_level()

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
        'django_request_handler': _get_django_handler(),
        'loomengine_handler': _get_loomengine_handler(),
        },
    'loggers': {
        'django': {
            'handlers': ['django_handler'],
            'level': LOG_LEVEL,
            },
        'django.request': {
            'handlers': ['django_request_handler'],
            'level': LOG_LEVEL,
            },
        'loomengine': {
            'handlers': ['loomengine_handler'],
            'level': LOG_LEVEL,
            },
        },
    }

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_TZ = True

STATIC_URL = '/home/'

STATICFILES_DIRS = [
    WEBPORTAL_ROOT,
]
