import collections
import docker
import errno
import jinja2
import logging
import os
import random
import re
import shutil
import time
import uuid

from loomengine import to_bool, to_list, write_settings_file, LoomClientError


SETTINGS_HOME = os.path.expanduser('~/.config/loom')
RESOURCE_DIR = 'resources'
CONFIG_DIR = 'third-party-config'
SERVER_SETTINGS_FILE = 'server-settings.conf'
CONFIG_FILE_TEMPLATE_PATH = os.path.join(
    os.path.dirname(__file__), 'config_templates')


# The jinja2 environment will be used by various components
# to render third-party config files like nginx.conf
def _get_jinja_env():
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(CONFIG_FILE_TEMPLATE_PATH),
        undefined=jinja2.StrictUndefined)
    env.filters['basename'] = lambda path: os.path.basename(path)
    env.filters['dirname'] = lambda path: os.path.dirname(path)
    env.filters['boolean'] = to_bool
    env.filters['list'] = to_list
    return env
JINJA_ENV = _get_jinja_env()


class LoomClientError(Exception):
    pass


class AbstractComponent(object):

    NETWORK_ID = None

    def __init__(self, settings, docker_client):
        self.settings = settings
        self.docker = docker_client

    def write_config_file(self, config_file):
        config_file_path = os.path.join(
            SETTINGS_HOME, CONFIG_DIR, config_file)
        logging.info('Creating config file "%s"' % config_file_path)
        template = JINJA_ENV.get_template(config_file)
        with open(config_file_path,
                  'w') as f:
            f.write(template.render(**self.settings)+'\n')

    def delete_config_file(self, config_file):
        config_file_path = os.path.join(
            SETTINGS_HOME, CONFIG_DIR, config_file)
        logging.info('Deleting config file "%s"' % config_file_path)
        try:
            os.remove(config_file_path)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise
            # else no file to delete. Continue

    def get_setting(self, setting):
        try:
            return self.settings[setting]
        except KeyError:
            raise LoomClientError(
                'ERROR! Missing required setting "%s".' % setting)

    def get_settings_as_environment_variables(self):
        # When settings are passed as environment variables,
        # they should start with "LOOM_" and use uppercase.
        env_settings = {}
        for key, value in self.settings.items():
            if key.upper().startswith('LOOM_'):
                key = key.upper()
            else:
                key = 'LOOM_'+key.upper()
            env_settings[key] = value
        return env_settings

    # component functions are no-op unless overridden
    def preprocess_settings(self):
        pass

    def validate_settings(self):
        pass

    def start(self):
        pass

    def wait(self):
        pass

    def runtime_configuration(self):
        pass

    def stop(self):
        pass

    def delete(self):
        pass

    def run_container(self, image, **kwargs):
        # Run a container, or noop if it already exits
        logging.info('Creating container %s' % kwargs.get('name'))
        try:
            return self.docker.containers.run(image, **kwargs)
        except docker.errors.APIError as e:
            if e.response.status_code == 409:
                logging.info('Container %s already exits. '
                             'Keeping existing container' % kwargs.get('name'))
            else:
                raise

    def wait_for_0_return_code(self, container, command, retries=4, fail_message=None):
        attempt = 0
        while attempt <= retries:
            (retcode, output) = container.exec_run(command)
            if retcode == 0:
                return output
            delay = 2**attempt + random.random()
            attempt += 1
            logging.info('...retry %s of %s in %0.2f seconds' % (
                attempt, retries, delay))
            time.sleep(delay)
        if fail_message is None:
            fail_message = 'Command "%s" failed after %s retries '\
                           'with output "%s"' % (command, retries, output)
        raise LoomClientError(fail_message)

    def wait_for_200_status_code(
            self, container, url, retries=4, fail_message=None):
        attempt = 0
        command = 'curl -I %s' % url
        while attempt < retries:
            (retcode, output) = container.exec_run(command)
            if '200 OK' in output:
                return
            delay = 2**attempt + random.random()
            attempt += 1
            logging.info('...retry %s of %s in %0.2f seconds' % (
                attempt, retries, delay))
            time.sleep(delay)
        if fail_message is None:
            fail_message = 'No 200 status code after %s retries to %s'\
                           % (retries, url)
        raise LoomClientError(fail_message)

    def stop_and_delete_container(self, container_name):
        logging.info('Deleting container "%s"' % container_name)
        try:
            container = self.docker.containers.get(container_name)
            container.stop()
            container.remove()
            logging.info('...done')
        except docker.errors.NotFound:
            # Container already absent. Continue
            logging.info('...not found')

    def delete_volume(self, volume_name):
        logging.info('Deleting volume "%s"' % volume_name)
        try:
            volume = self.docker.volumes.get(volume_name)
            volume.remove()
            logging.info('...done')
        except docker.errors.NotFound:
            # Volume already absent. Continue
            logging.info('...not found')

    def get_network_id(self):
        if not self.NETWORK_ID:
            self.cache_network_id()
        return self.NETWORK_ID

    def cache_network_id(self, network_id=None):
        if network_id:
            self.NETWORK_ID = network_id
        else:
            # Query network id from docker
            network_name = self.get_setting('network_name')
            networks = self.docker.networks.list(network_name)
            if len(networks) == 1:
                self.NETWORK_ID = networks[0].id
            elif len(networks) > 1:
                raise LoomClientError(
                    'Multiple networks found with name "%s". '
                    'Stop or delete the loom server to clean up '
                    'stale resources.' % network_name)
            else:
                raise LoomClientError(
                    'No network found with name "%s". '
                    'Start the "network" component to create it.'
                    % network_name)

    def make_dir_if_missing(self, path):
        logging.info('Creating directory at "%s"' % path)
        try:
            os.makedirs(path)
        except OSError as e:
            if e.errno == errno.EEXIST and os.path.isdir(path):
                pass  # Ok, dir exists
            else:
                raise LoomClientError(
                    'ERROR! Unable to create directory "%s"\n%s'
                    % (path, str(e)))


class SettingsComponent(AbstractComponent):

    def preprocess_settings(self):
        if self.settings.get('storage_root'):
            self.settings['storage_root'] = os.path.expanduser(
                self.settings.get('storage_root'))

    def start(self):
        self.make_dir_if_missing(os.path.join(
            SETTINGS_HOME, CONFIG_DIR))
        settings_file_path = os.path.join(SETTINGS_HOME,
                                          SERVER_SETTINGS_FILE)
        logging.info('Creating settings file at "%s"' % settings_file_path)
        write_settings_file(
        os.path.join(SETTINGS_HOME,
                         SERVER_SETTINGS_FILE),
            self.settings)

    def stop(self):
        pass

    def delete(self):
        if not SETTINGS_HOME \
           or os.path.abspath(SETTINGS_HOME) == os.path.abspath('/'):
            logging.warn('WARNING! SETTINGS_HOME is "%s". Refusing to delete.' \
                % SETTINGS_HOME)
        else:
            try:
                logging.info('Deleting settings directory %s' % SETTINGS_HOME)
                if os.path.exists(SETTINGS_HOME):
                    shutil.rmtree(SETTINGS_HOME)
            except Exception as e:
		logging.warn('WARNING! Failed to delete settings directory %s.\n%s' \
                    % (SETTINGS_HOME, str(e)))


class NetworkComponent(AbstractComponent):

    def start(self):
        network_name = self.get_setting('network_name')
        networks = self.docker.networks.list(network_name)
        if len(networks) == 0:
            # Create network if none exists with that name
            logging.info('Creating Docker network "%s"' % network_name)
            network = self.docker.networks.create(network_name)
            self.cache_network_id(network.id)
        elif len(networks) > 1:
            raise LoomClientError(
                'Multiple networks found with name "%s". '
                'Stop or delete the loom server to clean up '
                'stale resources.')
        else:
            # Use existing network
            logging.info('Using existing Docker network "%s"' % network_name)

    def stop(self):
        network_name = self.get_setting('network_name')
        logging.info('Deleting network %s' % network_name)
        for network in self.docker.networks.list(network_name):
            network.remove()

    def delete(self):
        self.stop()


class ElasticsearchComponent(AbstractComponent):

    CONFIG_FILE = 'elasticsearch.yml'

    def start(self):
        self.write_config_file(self.CONFIG_FILE)
        self.run_container(
            self.get_setting('elasticsearch_image'),
            name=self.get_setting('elasticsearch_container'),
            hostname=self.get_setting('elasticsearch_container'),
            volumes={
                os.path.join(
                    SETTINGS_HOME,
                    CONFIG_DIR,
                    self.CONFIG_FILE): {
                        'bind': '/usr/share/elasticsearch/config/%s'
                        % self.CONFIG_FILE,
                        'ro': True},
                self.get_setting('elasticsearch_data_volume'): {
                    'bind': '/usr/share/elasticsearch/data',
                    'ro': False}},
            environment={
                'ES_JAVA_OPTS': self.get_setting('elasticsearch_java_opts'),
                'http.host': '0.0.0.0',
                'transport.host': '127.0.0.1'},
            restart_policy={'Name': 'always'},
            cap_add=['IPC_LOCK'],
            ulimits=[{'Name': 'memlock', 'Soft': -1, 'Hard': -1},
                     {'Name': 'nofile', 'Soft': 65536, 'Hard': 65536}],
            network=self.get_network_id(),
            detach=True)

    def stop(self):
        self.stop_and_delete_container(
            self.get_setting('elasticsearch_container'))
        self.delete_config_file(self.CONFIG_FILE)

    def delete(self):
        self.stop()
        self.delete_volume(
            self.get_setting('elasticsearch_data_volume'))


class KibanaComponent(AbstractComponent):

    CONFIG_FILE = 'kibana.yml'

    def start(self):
        self.write_config_file(self.CONFIG_FILE)
        self.run_container(
            self.get_setting('kibana_image'),
            name=self.get_setting('kibana_container'),
            hostname=self.get_setting('kibana_container'),
            environment = {'ELASTICSEARCH_URL':
                           'http://%s:%s' % (
                               self.get_setting('elasticsearch_host'),
                               self.get_setting('elasticsearch_port'))},
            volumes={
                os.path.join(
                    SETTINGS_HOME,
                    CONFIG_DIR,
                    self.CONFIG_FILE): {
                        'bind': '/usr/share/kibana/config/%s'
                        % self.CONFIG_FILE,
                        'ro': True
                    }},
            network=self.get_network_id(),
            restart_policy={'Name': 'always'},
            detach=True)

    def wait(self):
        logging.info('Waiting for elasticsearch to initialize')
        kibana_container = self.docker.containers.get(
            self.get_setting('kibana_container'))
        url = 'http://%s:%s/.kibana' % (
            self.get_setting('elasticsearch_host'),
            self.get_setting('elasticsearch_port'))
        self.wait_for_200_status_code(kibana_container, url, retries=8)

    def runtime_configuration(self):
        # Set the elasticsearch index pattern for Kibana
        logging.info('Configuring Kibana index in elasticsearch')
        kibana_container = self.docker.containers.get(
            self.get_setting('kibana_container'))
        url = 'http://%s:%s/.kibana/index-pattern/*' % (
            self.get_setting('elasticsearch_host'),
            self.get_setting('elasticsearch_port'))
        payload = '\'{"title" : "*",  "timeFieldName": "@timestamp"}\''
        command = 'curl -w "__%%{http_code}__" -X PUT -H '\
                  '"Content-Type: application/json" -d %s %s' % (
                      payload, url)
        (retcode, output) = kibana_container.exec_run(command)
        if not ('__200__' in output or '__201__' in output):
            raise LoomClientError('ERROR! Failed to set Kibana index pattern')

    def stop(self):
        self.stop_and_delete_container(
            self.get_setting('kibana_container'))
        self.delete_config_file(self.CONFIG_FILE)

    def delete(self):
        self.stop()


class FluentdComponent(AbstractComponent):

    CONFIG_FILE = 'fluent.conf'

    def start(self):
        self.write_config_file(self.CONFIG_FILE)
        self.run_container(
            self.get_setting('fluentd_image'),
            name=self.get_setting('fluentd_container'),
            hostname=self.get_setting('fluentd_container'),
            volumes={
                os.path.join(SETTINGS_HOME, CONFIG_DIR, self.CONFIG_FILE): {
                    'bind': '/fluentd/etc/%s' % self.CONFIG_FILE,
                    'ro': True},
                os.path.join(SETTINGS_HOME, 'log'): {
                    'bind': '/fluentd/log/',
                    'ro': False}},
            ports={self.get_setting('fluentd_port'):
                   self.get_setting('fluentd_port')},
            network=self.get_network_id(),
            restart_policy={'Name': 'always'},
            detach=True)

    def stop(self):
        self.stop_and_delete_container(
            self.get_setting('fluentd_container'))
        self.delete_config_file(self.CONFIG_FILE)

    def delete(self):
        self.stop()
    

class MySQLComponent(AbstractComponent):

    def preprocess_settings(self):
        # Create a random password if none provided
        if not self.settings.get('mysql_password'):
            self.settings['mysql_password'] = uuid.uuid4()

    def start(self):
        environment={
            'MYSQL_USER': self.get_setting('mysql_user'),
            'MYSQL_PASSWORD': self.get_setting('mysql_password'),
            'MYSQL_DATABASE': self.get_setting('mysql_database'),
            'MYSQL_PORT': self.get_setting('mysql_port')}
        # Unless the user specifies root user and password,
        # use a temporary random password during setup.
        if self.get_setting('mysql_user') != 'root':
            environment.update({'MYSQL_RANDOM_ROOT_PASSWORD': True,
                                'MYSQL_ONETIME_PASSWORD': True})

        mysql_container = self.run_container(
            self.get_setting('mysql_image'),
            name=self.get_setting('mysql_container'),
            hostname=self.get_setting('mysql_host'),
            volumes={
                self.get_setting('mysql_data_volume'): {
                    'bind': '/var/lib/mysql',
                    'ro': False}},
            environment=environment,
            network=self.get_network_id(),
            restart_policy={'Name': 'always'},
            detach=True,
            log_config={
                'type': 'fluentd',
                'config': {
                    'fluentd-address': '%s:%s' % (
                        'localhost',
                        #self.get_setting('fluentd_host'),
                        self.get_setting('fluentd_port')),
                    'fluentd-async-connect': 'true',
                    'tag': 'loom.{{.Name}}.{{.ID}}'
                }})

    def stop(self):
        self.stop_and_delete_container(
            self.get_setting('mysql_container'))

    def delete(self):
        self.stop()
        self.delete_volume(self.get_setting('mysql_data_volume'))


class RabbitMQComponent(AbstractComponent):

    def start(self):
        self.run_container(
            self.get_setting('rabbitmq_image'),
            name=self.get_setting('rabbitmq_container'),
            hostname=self.get_setting('rabbitmq_container'),
            volumes={
                self.get_setting('rabbitmq_data_volume'): {
                    'bind': '/var/lib/rabbitmq',
                    'ro': False}},
            environment={
                'RABBITMQ_USER': self.get_setting('rabbitmq_user'),
                'RABBITMQ_PASSWORD': self.get_setting('rabbitmq_password'),
                'RABBITMQ_HOST': self.get_setting('rabbitmq_host'),
                'RABBITMQ_PORT': self.get_setting('rabbitmq_port'),
                'RABBITMQ_VHOST': self.get_setting('rabbitmq_vhost')},
            network=self.get_network_id(),
            restart_policy={'Name': 'always'},
            detach=True,
            log_config={
                'type': 'fluentd',
                'config': {
                    'fluentd-address': '%s:%s' % (
                        'localhost',
                        #self.get_setting('fluentd_host'),
                        self.get_setting('fluentd_port')),
                    'fluentd-async-connect': 'true',
                    'tag': 'loom.{{.Name}}.{{.ID}}'
                }})

    def stop(self):
        self.stop_and_delete_container(
            self.get_setting('rabbitmq_container'))

    def delete(self):
        self.stop()
        self.delete_volume(self.get_setting('rabbitmq_data_volume'))


class AsyncWorkerComponent(AbstractComponent):

    def start(self):
        environment=self.get_settings_as_environment_variables()
        environment['C_FORCE_ROOT'] = 'true'
        self.run_container(
            self.get_setting('loom_docker_image'),
            name=self.get_setting('async_worker_container'),
            command='/opt/loom/src/bin/run-worker.sh',
            environment=environment,
            volumes={
                SETTINGS_HOME: {
                    'bind': '/root/.config/loom',
                    'ro': True}},
            network=self.get_network_id(),
            restart_policy={'Name': 'always'},
            detach=True,
            log_config={
                'type': 'fluentd',
                'config': {
                    'fluentd-address': '%s:%s' % (
                        'localhost',
                        #self.get_setting('fluentd_host'),
                        self.get_setting('fluentd_port')),
                    'fluentd-async-connect': 'true',
                    'tag': 'loom.{{.Name}}.{{.ID}}'
                }})

    def stop(self):
        self.stop_and_delete_container(
            self.get_setting('async_worker_container'))

    def delete(self):
        self.stop()

    def _create_output_directory(self):
        if self.get_setting('mode').lower() == 'local':
            storage_root = self.get_setting('storage_root')
            self.make_dir_if_missing(os.path.expanduser(storage_root))


class AsyncSchedulerComponent(AbstractComponent):

    def start(self):
        environment = self.get_settings_as_environment_variables()
        environment['C_FORCE_ROOT'] = 'true'
        self.run_container(
            self.get_setting('loom_docker_image'),
            name=self.get_setting('scheduler_container'),
            hostname=self.get_setting('scheduler_container'),
            command='/opt/loom/src/bin/run-scheduler.sh',
            environment=environment,
            volumes={
                SETTINGS_HOME: {
                    'bind': '/root/.config/loom',
                    'ro': True}},
            network=self.get_network_id(),
            restart_policy={'Name': 'always'},
            detach=True,
            log_config={
                'type': 'fluentd',
                'config': {
                    'fluentd-address': '%s:%s' % (
                        'localhost',
                        #self.get_setting('fluentd_host'),
                        self.get_setting('fluentd_port')),
                    'fluentd-async-connect': 'true',
                    'tag': 'loom.{{.Name}}.{{.ID}}'
                }})

    def stop(self):
        self.stop_and_delete_container(
            self.get_setting('scheduler_container'))

    def delete(self):
        self.stop()


class LoomComponent(AbstractComponent):

    CONTAINER_SETTINGS_HOME = '/root/.config/loom'

    def start(self):
        self.run_container(
            self.get_setting('loom_docker_image'),
            name=self.get_setting('loom_container'),
            command='/opt/loom/src/bin/run-server.sh',
            environment=self.get_settings_as_environment_variables(),
            volumes={
                self.get_setting('portal_data_volume'): {
                    'bind': self.get_setting('portal_root'),
                    'ro': False},
                self.get_setting('static_data_volume'): {
                    'bind': self.get_setting('static_root'),
                    'ro': False},
                SETTINGS_HOME: {
                    'bind': self.CONTAINER_SETTINGS_HOME,
                    'ro': True}},
            network=self.get_network_id(),
            restart_policy={'Name': 'always'},
            detach=True,
            log_config={
                'type': 'fluentd',
                'config': {
                    'fluentd-address': '%s:%s' % (
                        'localhost',
                        #self.get_setting('fluentd_host'),
                        self.get_setting('fluentd_port')),
                    'fluentd-async-connect': 'true',
                    'tag': 'loom.{{.Name}}.{{.ID}}'
                }})

    def runtime_configuration(self):
        self._apply_migrations()

    def _apply_migrations(self):
        apply_migrations = self.get_setting('apply_database_migrations')
        loom_container = self.docker.containers.get(
            self.get_setting('loom_container'))
        logging.info('Waiting for database to be available to Loom')
        output = self.wait_for_0_return_code(
            loom_container, 'loom-manage showmigrations',
            fail_message='Loom failed to connect to the database.')
        # Typical output:
        # api
        #  [X] 0001_initial
        # auth
        #  [X] 0001_initial
        #  [ ] 0002_alter_permission_name_max_length
        # ...
        pending_migrations = len(re.findall('\[ \]', output))
        completed_migrations = len(re.findall('\[X\]', output))
        total_migrations = pending_migrations + completed_migrations
        if total_migrations == 0:
            raise LoomClientError('No migrations found')
        if pending_migrations == 0:
            # nothing to do
            return
        if pending_migrations > 0:
            logging.info('Found %s migrations pending' % pending_migrations)
            if apply_migrations:
                logging.info('Applying migrations')
                loom_container.exec_run('loom-manage migrate')
            else:
                logging.warn('WARNING! Skipping migrations because ' \
                             '"apply_database_migrations" setting is false')

    def stop(self):
        self.stop_and_delete_container(
            self.get_setting('loom_container'))
        self.delete_volume(self.get_setting('portal_data_volume'))
        self.delete_volume(self.get_setting('static_data_volume'))

    def delete(self):
        self.stop()


class NginxComponent(AbstractComponent):

    CONFIG_FILE = 'nginx.conf'

    def start(self):
        self.write_config_file(self.CONFIG_FILE)
        ports = {}
        http_port = self.settings.get('http_port')
        if http_port:
            ports[http_port] = http_port
        if to_bool(self.get_setting('use_https')):
            https_port = self.settings.get('https_port')
            ports[https_port] = https_port
        self.make_dir_if_missing(os.path.join(
            SETTINGS_HOME, RESOURCE_DIR))
        self.run_container(
            self.get_setting('nginx_image'),
            name=self.get_setting('nginx_container'),
            hostname=self.get_setting('nginx_container'),
            volumes={
                os.path.join(
                    SETTINGS_HOME,
                    CONFIG_DIR,
                    self.CONFIG_FILE): {
                        'bind': '/etc/nginx/conf.d/default.conf',
                        'ro': True},
                os.path.join(
                    SETTINGS_HOME,
                    RESOURCE_DIR): {
                        'bind': os.path.join(
                            '/root/.config/loom',
                            RESOURCE_DIR),
                        'ro': True}},
            volumes_from=self.get_setting('loom_container'),
            network=self.get_network_id(),
            ports=ports,
            restart_policy={'Name': 'always'},
            detach=True,
            log_config={
                'type': 'fluentd',
                'config': {
                    'fluentd-address': '%s:%s' % (
                        'localhost',
                        #self.get_setting('fluentd_host'),
                        self.get_setting('fluentd_port')),
                    'fluentd-async-connect': 'true',
                    'tag': 'loom.{{.Name}}.{{.ID}}'
                }})

    def stop(self):
        self.stop_and_delete_container(
            self.get_setting('nginx_container'))
        self.delete_config_file(self.CONFIG_FILE)

    def delete(self):
        self.stop()


# In the order in which components will be started.
# Stop and delete are done in reverse order.
COMPONENTS = collections.OrderedDict([
    ('settings', SettingsComponent),
    ('network', NetworkComponent),
    ('elasticsearch', ElasticsearchComponent),
    ('kibana', KibanaComponent),
    ('fluentd', FluentdComponent),
    ('mysql', MySQLComponent),
    ('rabbitmq', RabbitMQComponent),
    ('async-worker', AsyncWorkerComponent),
    ('async-scheduler', AsyncSchedulerComponent),
    ('loom', LoomComponent),
    ('nginx', NginxComponent)])
COMPONENT_CHOICES = [key for key in COMPONENTS.keys()] + ['none', 'all']


class DeploymentManager(object):

    def __init__(self, settings, component_names,
                 skip_components):
        self.settings = settings
        self.docker = docker.from_env()
        self.components = self._get_components(
            component_names, skip_components)

    def start(self):
        logging.info('Starting Loom server components %s'
                     % ', '.join(self.components.keys()))

        for component in self.components.values():
            component.preprocess_settings()

        for component in self.components.values():
            component.validate_settings()

        for component in self.components.values():
            component.start()

        for component in self.components.values():
            component.wait()

        for component in self.components.values():
            component.runtime_configuration()

    def stop(self):
        logging.info('Stopping Loom server components %s'
                     % ', '.join(self.components.keys()))
        for component in self.components.values()[::-1]:
            component.stop()

    def delete(self):
        logging.info('Deleting Loom server components %s'
                     % ', '.join(self.components.keys()))
        for component in self.components.values()[::-1]:
            component.delete()

    def _get_components(self, component_names, skip_components):
        if component_names:
            for component in component_names:
                assert component in COMPONENT_CHOICES, \
                    'unrecognized component "%s"' % component
        if skip_components:
            for component in skip_components:
                assert component in COMPONENT_CHOICES, \
                    'unrecognized component "%s"' % component
        # component_names and skip_components are mutually exclusive,
        # but non-conflicting args like (component_names='all',
        # skip_components='none') are allowed.
        component_names = self._translate_components_none_or_all(component_names)
        skip_components = self._translate_components_none_or_all(skip_components)
        assert not (component_names and skip_components), 'components and '\
            'skip_components are mutually exclusive'
        if skip_components:
            component_names = filter(lambda c: c not in skip_components,
                                     COMPONENTS.keys())
        if not component_names:
            component_names = [k for k in COMPONENTS.keys()]
        # Go in component order and build list of component classes
        components = collections.OrderedDict()
        for name, Component in COMPONENTS.items():
            if name in component_names:
                components[name] = Component(self.settings, self.docker)
        return components

    def _translate_components_none_or_all(self, components):
        if components and len(components) > 1:
            assert not 'all' in components, \
                '"all" is mutually exclusive with all other components'
            assert not 'none' in components, \
                '"none" is mutually exclusive with all other components'
        if components and 'none' in components:
            return []
        elif components and 'all' in components:
            return [key for key in COMPONENTS.keys()]
        else:
            return components
