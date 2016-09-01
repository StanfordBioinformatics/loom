# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

import datetime
import os
import socket
import sys
import tempfile
import warnings

include_models = os.getenv('GRAPH_MODELS_INCLUDE_MODELS')

BASE_DIR = os.path.dirname(__file__)
WEBCLIENT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..', 'webclient'))

def get_secret_key():
    SECRET_FILE = os.path.join(BASE_DIR, 'secret.txt')
    try:
        SECRET_KEY = open(SECRET_FILE).read().strip()
        return SECRET_KEY
    except IOError:
        try:
            import random
            SECRET_KEY = ''.join([random.SystemRandom().choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(50)])
            secret = file(SECRET_FILE, 'w')
            secret.write(SECRET_KEY)
            secret.close()
            return SECRET_KEY
        except IOError:
            Exception('Failed to create file for secret key. Please create file "%s"' \
            ' with a random secret key' % SECRET_FILE)

SECRET_KEY = get_secret_key()

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
    'analysis',
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

ROOT_URLCONF = 'loomserver.urls'

WSGI_APPLICATION = 'loomserver.wsgi.application'

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

def get_sqlite_database_name():
    DATABASE_NAME_FILE = os.path.join(BASE_DIR, 'sqlite_dbname.txt')
    try:
        DATABASE_NAME = open(DATABASE_NAME_FILE).read().strip()
        return DATABASE_NAME
    except IOError:
        try:
            DATABASE_NAME = datetime.datetime.utcnow().strftime("loom-%Y%m%d-%H%M%S")
            f = file(DATABASE_NAME_FILE, 'w')
            f.write(DATABASE_NAME)
            f.close()
            return DATABASE_NAME
        except IOError:
            Exception('Failed to create file for database name. Please create file "%s"' \
                      ' with a name for the Loom database' % DATABASE_NAME_FILE)

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
elif not os.getenv('LOOM_TEST_DATABASE'):
    SQLITE_DATABASE_NAME = get_sqlite_database_name()
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, SQLITE_DATABASE_NAME+'.sqlite3'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'test_loom.sqlite3'),
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

def _get_loom_handler():
    WEBSERVER_LOGFILE = os.getenv('WEBSERVER_LOGFILE', None)
    if WEBSERVER_LOGFILE  is not None:
        if not os.path.exists(os.path.dirname(WEBSERVER_LOGFILE)):
            os.makedirs(os.path.dirname(WEBSERVER_LOGFILE))
        handler = {
            'class': 'logging.FileHandler',
            'filename': WEBSERVER_LOGFILE,
            'formatter': 'default',
            }
    else:
        handler = {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            }
    return handler

def _get_log_level():
    DEFAULT_LOG_LEVEL = 'INFO'
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
        'loom_handler': _get_loom_handler(),
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
        'loom': {
            'handlers': ['loom_handler'],
            'level': LOG_LEVEL,
            },
        },
    }

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_TZ = True

STATIC_URL = '/home/'

STATICFILES_DIRS = [
    WEBCLIENT_ROOT,
]

# Graph Models settings to generate model schema plots
GRAPH_MODELS = {
    'include_models': include_models,
}

# Get settings from the environment and expand paths if needed
WORKER_TYPE = os.getenv('WORKER_TYPE', 'LOCAL')
MASTER_URL_FOR_WORKER = os.getenv('MASTER_URL_FOR_WORKER', 'http://127.0.0.1:8000')
MASTER_URL_FOR_SERVER = os.getenv('MASTER_URL_FOR_SERVER', 'http://127.0.0.1:8000')
FILE_ROOT = os.getenv('FILE_ROOT', tempfile.mkdtemp())
FILE_ROOT_FOR_WORKER = os.getenv('FILE_ROOT_FOR_WORKER')
FILE_SERVER_TYPE = os.getenv('FILE_SERVER_TYPE', 'LOCAL')
LOGS_DIR = os.getenv('LOGS_DIR')

PROJECT_ID = os.getenv('GCE_PROJECT', '')   # Used by loom.common.filehandler.GoogleStorageSource and GoogleStorageDestination
                                            # Retrieved but not used when filehandler is LocalSource and LocalDestination, so need to set a default value
BUCKET_ID = os.getenv('GCE_BUCKET', '')
GCE_PEM_FILE_PATH = os.getenv('GCE_PEM_FILE_PATH')
GCE_INI_PATH = os.getenv('GCE_INI_PATH')
GCE_SSH_KEY_FILE = os.getenv('GCE_SSH_KEY_FILE')
WORKER_VM_IMAGE = os.getenv('WORKER_VM_IMAGE')
WORKER_SKIP_INSTALLS = os.getenv('WORKER_SKIP_INSTALLS')
SERVER_SKIP_INSTALLS = os.getenv('SERVER_SKIP_INSTALLS')
WORKER_LOCATION = os.getenv('WORKER_LOCATION')
WORKER_SCRATCH_DISK_MOUNT_POINT = os.getenv('WORKER_SCRATCH_DISK_MOUNT_POINT')
WORKER_SCRATCH_DISK_TYPE = os.getenv('WORKER_SCRATCH_DISK_TYPE')
WORKER_SCRATCH_DISK_SIZE = os.getenv('WORKER_SCRATCH_DISK_SIZE')
WORKER_BOOT_DISK_TYPE = os.getenv('WORKER_BOOT_DISK_TYPE')
WORKER_BOOT_DISK_SIZE = os.getenv('WORKER_BOOT_DISK_SIZE')
WORKER_NETWORK = os.getenv('WORKER_NETWORK')
WORKER_TAGS = os.getenv('WORKER_TAGS')
DOCKER_TAG = os.getenv('DOCKER_TAG')
DOCKER_FULL_NAME = os.getenv('DOCKER_FULL_NAME')

HASH_FUNCTION = 'md5'

KEEP_DUPLICATE_FILES = True
FORCE_RERUN = True

HARD_STOP_ON_CANCEL = True
HARD_STOP_ON_FAIL = True

DISABLE_AUTO_PUSH = False

# Graph Models settings to generate model schema plots
GRAPH_MODELS = {
    'include_models': include_models,
}

if DEBUG:
    CORS_ORIGIN_ALLOW_ALL = True
else:
    CORS_ORIGIN_WHITELIST = os.getenv('CORS_ORIGIN_WHITELIST', '').split(',')
