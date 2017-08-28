import re
import warnings

from . import SettingsValidationError

class BaseSettingsValidator(object):
    """Base class for settings validators
    """

    errors = []

    # To override
    REQUIRED_SETTINGS = ()
    OPTIONAL_SETTINGS = ()

    COMMON_REQUIRED_SETTINGS = (
        'LOOM_DOCKER_IMAGE',
        'LOOM_START_SERVER_PLAYBOOK',
        'LOOM_STOP_SERVER_PLAYBOOK',
        'LOOM_DELETE_SERVER_PLAYBOOK',
        'LOOM_RUN_TASK_PLAYBOOK',
        'LOOM_CLEANUP_TASK_PLAYBOOK',
        'LOOM_STORAGE_TYPE',
        'LOOM_WORKER_TYPE',
        'LOOM_ANSIBLE_INVENTORY',
    )

    COMMON_OPTIONAL_SETTINGS = (
        'LOOM_SERVER_NAME',
        'LOOM_SETTINGS_VALIDATOR',
        'LOOM_DEBUG',
        'LOOM_LOG_LEVEL',
        'LOOM_ANSIBLE_HOST_KEY_CHECKING',
        'ANSIBLE_HOST_KEY_CHECKING', # copy of LOOM_ANSIBLE_HOST_KEY_CHECKING
        'LOOM_DEFAULT_DOCKER_REGISTRY',
        'LOOM_STORAGE_ROOT',
        'LOOM_HTTP_PORT',
        'LOOM_HTTPS_PORT',
        'LOOM_HTTP_PORT_ENABLED',
        'LOOM_HTTPS_PORT_ENABLED',
        'LOOM_HTTP_REDIRECT_TO_HTTPS',
        'LOOM_SSL_CERT_CREATE_NEW',
        'LOOM_SSL_CERT_C',
        'LOOM_SSL_CERT_ST',
        'LOOM_SSL_CERT_L',
        'LOOM_SSL_CERT_O',
        'LOOM_SSL_CERT_KEY_FILE',
        'LOOM_SSL_CERT_FILE',
        'LOOM_MASTER_CONTAINER_NAME_SUFFIX',
        'LOOM_MASTER_INTERNAL_IP',
        'LOOM_MASTER_INTERNAL_PORT',
        'LOOM_MASTER_ALLOWED_HOSTS',
        'LOOM_MASTER_GUNICORN_WORKERS_COUNT',
        'LOOM_MASTER_STATIC_ROOT',
        'LOOM_MASTER_CORS_ORIGIN_ALLOW_ALL',
        'LOOM_MASTER_CORS_ORIGIN_WHITELIST',
        'LOOM_WORKER_CONTAINER_NAME_SUFFIX',
        'LOOM_WORKER_CELERY_CONCURRENCY',
        'LOOM_MYSQL_CREATE_DOCKER_CONTAINER',
        'LOOM_MYSQL_HOST',
        'LOOM_MYSQL_PORT',
        'LOOM_MYSQL_USER',
        'LOOM_MYSQL_DATABASE',
        'LOOM_SCHEDULER_CONTAINER_NAME_SUFFIX',
        'LOOM_RABBITMQ_CONTAINER_NAME_SUFFIX',
        'LOOM_RABBITMQ_IMAGE',
        'LOOM_RABBITMQ_USER',
        'LOOM_RABBITMQ_PASSWORD',
        'LOOM_RABBITMQ_PORT',
        'LOOM_RABBITMQ_VHOST',
        'LOOM_NGINX_CONTAINER_NAME_SUFFIX',
        'LOOM_NGINX_IMAGE',
        'LOOM_NGINX_SERVER_NAME',
        'LOOM_NGINX_WEBPORTAL_ROOT',
        'LOOM_FLUENTD_IMAGE',
        'LOOM_FLUENTD_CONTAINER_NAME_SUFFIX',
        'LOOM_FLUENTD_PORT',
        'LOOM_FLUENTD_OUTPUTS',
        'LOOM_ELASTICSEARCH_CONTAINER_NAME_SUFFIX',
        'LOOM_ELASTICSEARCH_IMAGE',
        'LOOM_ELASTICSEARCH_PORT',
        'LOOM_ELASTICSEARCH_DATA_VOLUME',
        'LOOM_ELASTICSEARCH_JAVA_OPTS',
        'LOOM_KIBANA_CONTAINER_NAME_SUFFIX',
        'LOOM_KIBANA_IMAGE',
        'LOOM_KIBANA_PORT',
        'LOOM_KIBANA_VERSION',
        'LOOM_TASKRUNNER_CONTAINER_NAME_SUFFIX',
        'LOOM_TASKRUNNER_HEARTBEAT_INTERVAL_SECONDS',
        'LOOM_TASKRUNNER_HEARTBEAT_TIMEOUT_SECONDS',
        'LOOM_PRESERVE_ON_FAILURE',
        'LOOM_PRESERVE_ALL',
        'LOOM_MAXIMUM_TASK_RETRIES',
        'LOOM_FLOWER_INTERNAL_PORT',
        'LOOM_FLOWER_CONTAINER_NAME_SUFFIX',
        'LOOM_MYSQL_IMAGE',
        'LOOM_MYSQL_CONTAINER_NAME_SUFFIX',
        'LOOM_MYSQL_RANDOM_ROOT_PASSWORD',
        'LOOM_MYSQL_PASSWORD',
        'LOOM_MYSQL_SSL_CA_CERT_FILE',
        'LOOM_MYSQL_SSL_CLIENT_CERT_FILE',
        'LOOM_MYSQL_SSL_CLIENT_KEY_FILE',
        'LOOM_RABBITMQ_MANAGEMENT_IMAGE',
        'LOOM_EMAIL_HOST',
        'LOOM_EMAIL_PORT',
        'LOOM_EMAIL_HOST_USER',
        'LOOM_EMAIL_HOST_PASSWORD',
        'LOOM_EMAIL_USE_TLS',
        'LOOM_EMAIL_USE_SSL',
        'LOOM_EMAIL_TIMEOUT',
        'LOOM_EMAIL_SSL_KEYFILE',
        'LOOM_EMAIL_SSL_CERTFILE',
        'LOOM_DEFAULT_FROM_EMAIL',
        'LOOM_NOTIFICATION_ADDRESSES',
        'LOOM_GOOGLE_STORAGE_BUCKET',
    )

    def __init__(self, settings):
        self.settings = settings
        self.ALL_SETTINGS = self.REQUIRED_SETTINGS \
                            + self.OPTIONAL_SETTINGS \
                            + self.COMMON_REQUIRED_SETTINGS \
                            + self.COMMON_OPTIONAL_SETTINGS

    def validate_common(self):
        for required_setting in self.REQUIRED_SETTINGS+self.COMMON_REQUIRED_SETTINGS:
            if not required_setting in self.settings.keys():
                self.errors.append('Missing required setting "%s"' % required_setting)

        for setting in self.settings:
            if not setting in self.ALL_SETTINGS:
                warnings.warn('Unrecognized setting "%s" will be ignored' % setting)

        self._validate_ssl_cert_settings()
        self._validate_mysql_settings()
        self._validate_ports()
        self._validate_server_name()

    def raise_if_errors(self):
        if self.errors:
            raise SettingsValidationError(self.errors)

    def _validate_ssl_cert_settings(self):
        if self.to_bool(self.settings.get('LOOM_SSL_CERT_CREATE_NEW')):
            for setting in [
                    'LOOM_SSL_CERT_C',
                    'LOOM_SSL_CERT_ST',
                    'LOOM_SSL_CERT_L',
                    'LOOM_SSL_CERT_O',
	            'LOOM_SSL_CERT_KEY_FILE',
	            'LOOM_SSL_CERT_FILE',
            ]:
                if not setting in self.settings.keys():
                    self.errors.append('Missing setting "%s"' % setting)

    def _validate_ports(self):
        if self.to_bool(self.settings.get('LOOM_HTTP_PORT_ENABLED')):
            if not 'LOOM_HTTP_PORT' in self.settings.keys():
                self.errors.append(
                    'Missing setting LOOM_HTTP_PORT is required when '\
                    'LOOM_HTTP_PORT_ENABLED is True'
                    % setting)
        if self.to_bool(self.settings.get('LOOM_HTTPS_PORT_ENABLED')):
            if not 'LOOM_HTTPS_PORT' in self.settings.keys():
                self.errors.append(
                    'Missing setting LOOM_HTTPS_PORT is required when '\
                    'LOOM_HTTPS_PORT_ENABLED is True'
                    % setting)

    def _validate_mysql_settings(self):
        if self.to_bool(self.settings.get('LOOM_MYSQL_CREATE_DOCKER_CONTAINER')):
            # Then these are required:
            for required_setting in [
                    'LOOM_MYSQL_IMAGE',
                    'LOOM_MYSQL_CONTAINER_NAME_SUFFIX',
                    'LOOM_MYSQL_RANDOM_ROOT_PASSWORD']:
                if not required_setting in self.settings.keys():
                    self.errors.append(
                        'Missing setting "%s" is required when '\
                        'LOOM_MYSQL_CREATE_DOCKER_CONTAINER is True' % required_setting)

    def _validate_server_name(self):
        server_name = self.settings.get('LOOM_SERVER_NAME')
        pattern='^[a-z]([-a-z0-9]*[a-z0-9])?$'
        if not re.match(pattern, server_name):
            self.errors.append(
                'Invalid LOOM_SERVER_NAME "%s". Must start with a letter, '
                'contain only alphanumerics and hyphens, and cannot end with a '
                'hyphen' % server_name)
        if len(server_name) > 63:
            self.errors.append(
                'Invalid LOOM_SERVER_NAME "%s". Cannot exceed 63 letters.'
                % server_name)

    def to_bool(self, value):
        if value and value.upper() in ['TRUE', 'T', 'YES', 'Y']:
            return True
        else:
            return False
