# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

import os
import sys

BASE_DIR = os.path.dirname(__file__)

# SECRET_KEY used for sessions, CSFR form verification, and anything else using cryptographic signing.
SECRET_KEY = os.getenv('SECRET_KEY')

RACK_ENV = os.getenv('RACK_ENV', 'production')

if not RACK_ENV in ['test', 'production', 'development']:
    raise Exception('Invalid RACK_ENV setting of "%s".\n '\
                    'Valid values for the env variable RACK_ENV are "production" and "development"' % RACK_ENV)

if RACK_ENV == 'development' or RACK_ENV == 'test':
    DEBUG = True
    TEMPLATE_DEBUG = True
    if SECRET_KEY is None:
        SECRET_KEY = 'l^+hmt%zh$e1j&ca=d3z%0xn6ej_*i!x70fbf^62l3(qou850f'
else:
    # PRODUCTION SETTINGS
    if SECRET_KEY is None:
        raise Exception('In production you must set the SECRET_KEY env variable to a random, secret string.\n'\
                        'In development, you can set RACK_ENV=development to silence this error and turn on debug features.')

ALLOWED_HOSTS = []

INSTALLED_APPS = (
#    'django.contrib.auth',
    'django_extensions',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'immutable',
    'analysis',
    'editor',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
#    'django.contrib.auth.middleware.AuthenticationMiddleware',
#    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'xppfserver.urls'

WSGI_APPLICATION = 'xppfserver.wsgi.application'

if RACK_ENV == 'development':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'development_db.sqlite3'),
        }
    }
elif RACK_ENV == 'test':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'test_db.sqlite3'),
        }
    }
else:
    raise Exception('TODO: create database settings for production environment.')

def _get_django_handler():
    DJANGO_LOGFILE = os.getenv('DJANGO_LOGFILE', None)
    if DJANGO_LOGFILE is not None:
        handler = {
            'class': 'logging.FileHandler',
            'filename': DJANGO_LOGFILE,
            }
    else:
        handler = {
            'class': 'logging.StreamHandler',
            }
    return handler

def _get_xppf_handler():
    XPPF_LOGFILE = os.getenv('XPPF_LOGFILE', None)
    if XPPF_LOGFILE  is not None:
        handler = {
            'class': 'logging.FileHandler',
            'filename': XPPF_LOGFILE,
            }
    else:
        handler = {
            'class': 'logging.StreamHandler',
            }
    return handler

def _get_log_level():
    DEFAULT_LOG_LEVEL = 'INFO'
    LOG_LEVEL = os.getenv('LOG_LEVEL', DEFAULT_LOG_LEVEL)
    return LOG_LEVEL.upper()

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'django_handler': _get_django_handler(),
        'xppf_handler': _get_xppf_handler(),
        },
    'loggers': {
        'django': {
            'handlers': ['django_handler'],
            'level': _get_log_level(),
            },
        'xppf': {
            'handlers': ['xppf_handler'],
            'level': _get_log_level(),
            },
        },
    }

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_TZ = True

STATIC_URL = '/static/'

