#!/usr/bin/env python
import argparse
import ConfigParser
import errno
import imp
import logging
import os
import requests
import shutil
from StringIO import StringIO
import urlparse

from loomengine import write_settings_file, parse_settings_file, to_bool, \
    LoomClientError
from loomengine.deployment import DeploymentManager, COMPONENT_CHOICES, \
    SETTINGS_HOME, SERVER_SETTINGS_FILE, RESOURCE_DIR
import loomengine_utils.version


CONNECTION_SETTINGS_FILE = 'connection-settings.conf'
DEFAULT_SETTINGS_FILE = os.path.join(imp.find_module('loomengine')[1], 'default.conf')
TOKEN_FILE = 'token.txt'


def has_connection_settings():
    return os.path.exists(
        os.path.join(SETTINGS_HOME, CONNECTION_SETTINGS_FILE))


def verify_has_connection_settings():
    if not has_connection_settings():
        raise LoomClientError(
            'ERROR! Not connected to any server. First start a new server '
            'or connect to an existing server.')


def get_server_url():
    connection_settings = parse_settings_file(
        os.path.join(SETTINGS_HOME, CONNECTION_SETTINGS_FILE))
    return connection_settings['server_url']


def is_server_running(url=None):
    if not url:
        url = get_server_url()
    try:
        loomengine_utils.connection.disable_insecure_request_warning()
        response = requests.get(url + '/api/status/', verify=False, timeout=30)
    except requests.exceptions.ConnectionError:
        return False
    if response.status_code == 200:
        return True
    else:
        raise LoomClientError('ERROR! Unexpected status code "%s" from server'
                      % response.status_code)

def verify_server_is_running(url=None):
    if not is_server_running(url=url):
        raise LoomClientError('ERROR! No response from server at %s' % url)


def delete_token():
    token_path = os.path.join(SETTINGS_HOME, TOKEN_FILE)
    if os.path.exists(token_path):
        os.remove(token_path)


def save_token(token):
    delete_token()
    with open(os.path.join(SETTINGS_HOME, TOKEN_FILE), 'w') as f:
        f.write(token)


def get_token():
    token_path = os.path.join(SETTINGS_HOME, TOKEN_FILE)
    if os.path.exists(token_path):
        with open(token_path) as f:
            token = f.read()
    else:
        token = None
    return token


class ServerControls(object):
    """Class for managing the Loom server.
    """
    def __init__(self, args=None):
        if args is None:
            args = _get_args()
        self.args = args
        self._set_run_function()

    def _set_run_function(self):
        # Map user input command to method
        commands = {
            'status': self.status,
            'start': self.start,
            'stop': self.stop,
            'connect': self.connect,
            'disconnect': self.disconnect,
            'delete': self.delete,
        }
        self.run = commands[self.args.command]

    def status(self):
        verify_has_connection_settings()
        if is_server_running():
            logging.info('OK, the server is up at %s' % get_server_url())
        else:
            raise LoomClientError(
                'No response from server at %s' % get_server_url())

    def start(self):
        if self._has_server_settings():
            if self._user_provided_settings():
                raise LoomClientError(
                    'ERROR! Server settings already exist in "%s". '
                    'The "--settings-file", "--extra-settings", and '
                    '"--resource-dir" flags are not allowed now because '
                    'new settings and existing settings may conflict.'
                    % os.path.join(
                        SETTINGS_HOME, SERVER_SETTINGS_FILE))
            else:
                settings = parse_settings_file(
                    os.path.join(
                        SETTINGS_HOME, SERVER_SETTINGS_FILE))
                logging.info('Using existing settings.')
        elif has_connection_settings():
            raise LoomClientError(
                'ERROR! You are already connected to a server. '
                'That lets you view or manage workflows, but you do not have '
                'the settings needed to manage the server. If you want to '
                'start a new server, first disconnect using '
                '"loom server disconnect".')
        else:
            # Create new settings from defaults and user input
            user_settings = self._get_server_settings()
            mode = user_settings.get('mode', 'local')
            server_name = user_settings.get('server_name', 'loom')
            settings = self._get_default_settings(mode, server_name)
            settings.update(user_settings)
            self._copy_resources_to_settings_dir()

        deployment_manager = DeploymentManager(
            settings, self.args.component, self.args.skip_component)
        deployment_manager.start()
        self._create_connection_settings(self._construct_server_url(settings))

    def _construct_server_url(self, settings):
        if to_bool(self._get_required_setting('use_https', settings)):
            protocol = 'https'
            port = self._get_required_setting('https_port', settings)
        else:
            protocol = 'http'
            port = self._get_required_setting('http_port', settings)
        hostname = self._get_required_setting('localhost_ip', settings)
        server_url = '%s://%s:%s' % (protocol, hostname, port)
        return server_url
        
    def _create_connection_settings(self, server_url):
        if not os.path.exists(SETTINGS_HOME):
            os.makedirs(SETTINGS_HOME)
        write_settings_file(
            os.path.join(SETTINGS_HOME, CONNECTION_SETTINGS_FILE),
            {"server_url": server_url})

    def stop(self):
        if not self._has_server_settings():
            raise LoomClientError(
                'ERROR! No server settings found. Nothing to stop.')
        settings = parse_settings_file(
            os.path.join(SETTINGS_HOME, SERVER_SETTINGS_FILE))
        logging.info('Stopping Loom server')
        DeploymentManager(settings, self.args.component,
                          self.args.skip_component).stop()

    def connect(self):
        server_url = self.args.server_url
        if has_connection_settings():
            raise LoomClientError(
                'ERROR! Already connected to "%s".' % get_server_url())

        parsed_url = urlparse.urlparse(server_url)
        if not parsed_url.scheme:
            if is_server_running(url='https://' + server_url):
                server_url = 'https://' + server_url
            elif is_server_running(url='http://' + server_url):
                server_url = 'http://' + server_url
            else:
                raise LoomClientError(
                    'ERROR! Loom server not found at "%s".' % server_url)
        elif not is_server_running(url=server_url):
            raise LoomClientError(
                'ERROR! Loom server not found at "%s".' % server_url)
        self._create_connection_settings(server_url)
        logging.info('Connected to Loom server at "%s".' % server_url)

    def disconnect(self):
        if not has_connection_settings():
            raise LoomClientError(
                'ERROR! No server connection found. Nothing to disconnect.')
        if self._has_server_settings():
            raise LoomClientError(
                'ERROR! Server settings found. Disconnecting is not allowed. '
                'If you really want to disconnect without deleting the '
                'server, back up the settings in %s and manually remove them.'
                % os.path.join(SETTINGS_HOME))
        settings = parse_settings_file(
            os.path.join(SETTINGS_HOME, CONNECTION_SETTINGS_FILE))
        server_url = settings.get('server_url')
        os.remove(os.path.join(
            SETTINGS_HOME, CONNECTION_SETTINGS_FILE))
        delete_token()
        try:
            # remove if empty
            os.rmdir(SETTINGS_HOME)
        except OSError:
            pass
        logging.info('Disconnected from the Loom server at %s \nTo reconnect, '
                    'use "loom server connect %s"' % (server_url, server_url))

    def delete(self):
        if not self._has_server_settings():
            raise LoomClientError(
                'ERROR! No server settings found. Nothing to delete.')
        settings = parse_settings_file(
            os.path.join(SETTINGS_HOME, SERVER_SETTINGS_FILE))
        if not self.args.no_confirm:
            confirmation = raw_input(
                'WARNING! This will delete the Loom server, '
                'and all its data will be lost!\n'
                'Are you sure you want to delete the server? '
                '(only "yes" will proceed with deletion)\n> ')
            if confirmation != 'yes':
                logging.info(
                    'Failed to confirm request. No action taken')
                return
        DeploymentManager(settings, self.args.component,
                          self.args.skip_component).delete()

    def _make_dir_if_missing(self, path):
        try:
            os.makedirs(path)
        except OSError as e:
            if e.errno == errno.EEXIST and os.path.isdir(path):
                pass  # Ok, dir exists
            else:
                raise LoomClientError('ERROR! Unable to create directory "%s"\n%s'
                                 % (path, str(e)))

    def _copy_resources_to_settings_dir(self):
        if self.args.resource_dir:
            self._make_dir_if_missing(SETTINGS_HOME)
            shutil.copytree(
                self.args.resource_dir,
                os.path.join(SETTINGS_HOME, RESOURCE_DIR))
        #else:
            # If no files, leave an empty directory
        #    os.makedirs(
        #        os.path.join(SETTINGS_HOME, RESOURCE_DIR))

    def _get_required_setting(self, key, settings):
        try:
            return settings[key.lower()]
        except KeyError:
            raise LoomClientError('ERROR! Missing required setting "%s"' % key)

    def _user_provided_settings(self):
        # True if user passed settings through commandline arguments
        return self.args.settings_file or self.args.extra_settings or \
            self.args.resource_dir

    def _has_server_settings(self):
        return os.path.exists(os.path.join(SETTINGS_HOME,
                                           SERVER_SETTINGS_FILE))

    def _get_server_settings(self):
        if self._has_server_settings():
            if self._user_provided_settings():
                raise LoomClientError(
                    'ERROR! Server settings already exist in "%s". '
                    'The "--settings-file", "--extra-settings", '
                    'and "--resource-dir" '
                    'flags are not allowed now because new settings '
                    'and existing settings may conflict.'
                    % os.path.join(
                        SETTINGS_HOME, SERVER_SETTINGS_FILE))
            else:
                settings = parse_settings_file(
                    os.path.join(
                        SETTINGS_HOME, SERVER_SETTINGS_FILE))
        elif has_connection_settings():
            if self._user_provided_settings():
                raise LoomClientError(
                    'ERROR! Connection settings already exist in "%s". '
                    'The "--settings-file", "--extra-settings", '
                    'and "--resource-dir" '
                    'flags are not allowed now because new settings '
                    'and existing settings may conflict.'
                    % os.path.join(
                        SETTINGS_HOME, CONNECTION_SETTINGS_FILE))
            else:
                raise LoomClientError(
                    'ERROR! You are already connected to a server. '
                    'That lets you view or manage workflows, but you '
                    'do not have the settings needed to manage the server. '
                    'If you want to start a new server, first disconnect '
                    'using "loom server disconnect".')
        else:
            settings = self._get_start_settings_from_args()
        return settings

    def _get_start_settings_from_args(self):
        settings = {}
        if self.args.settings_file:
            for settings_file in self.args.settings_file:
                settings.update(parse_settings_file(settings_file))
        if self.args.extra_settings:
            settings.update(
                self._parse_extra_settings(self.args.extra_settings))

        # Pick up any LOOM_* settings from the environment, and
        # give precedence to env over settings file.
        for key, value in os.environ.iteritems():
            if key.lower().startswith('loom_'):
                key = key.lower().strip('loom_')
                settings.update({key: value})

        for key, value in settings.items():
            settings[key] = os.path.expanduser(value)

        return settings

    def _get_default_settings(self, mode, server_name):
        initial_defaults = {
            'server_name': server_name,
            'mode': mode,
            'version': loomengine_utils.version.version()
        }
        # Use user_settings as defaults. This is used, for example, where
        # SERVER_NAME is used in WORKER_CONTAINER_NAME
        parser = ConfigParser.SafeConfigParser(initial_defaults)
        try:
            parser.read(DEFAULT_SETTINGS_FILE)
            settings = dict(parser.items(mode))
        except ConfigParser.Error as e:
            raise LoomClientError('Error parsing default settings file "%s": %s'
                            % (DEFAULT_SETTINGS_FILE, e))
        return settings

    def _parse_extra_settings(self, extra_settings):
        settings_dict = {}
        for setting in extra_settings:
            if '=' not in setting:
                raise LoomClientError(
                    'Invalid format for extra setting "%s". '
                    'Use "-e key=value" format.' % setting)
            (key, value) = setting.split('=', 1)
            settings_dict[key.lower()] = value
        return settings_dict


def get_parser(parser=None):

    if parser is None:
        parser = argparse.ArgumentParser(__file__)

    subparsers = parser.add_subparsers(dest='command')

    status_parser = subparsers.add_parser(
        'status',
        help='show the status of the Loom server')

    start_parser = subparsers.add_parser(
        'start',
        help='start a loom server')
    start_parser.add_argument('-m', '--mode', default='local', metavar='MODE',
                              choices=['local', 'gce'])
    start_parser.add_argument('-s', '--settings-file', action='append',
                              metavar='SETTINGS_FILE')
    start_parser.add_argument('-e', '--extra-settings', action='append',
                              metavar='KEY=VALUE')
    start_parser.add_argument('-r', '--resource-dir', metavar='RESOURCE_DIR')
    start_parser.add_argument(
        '-c', '--component', metavar='COMPONENT', action='append',
        choices=COMPONENT_CHOICES,
        help='individual server components to install (default "all")')
    start_parser.add_argument(
        '-k', '--skip-component', metavar='SKIPPED_COMPONENT', action='append',
        choices=COMPONENT_CHOICES,
        help='individual server components to skip (default "none")')
    start_parser.add_argument('-v', '--verbose', action='store_true',
                              help='provide more feedback to console')

    stop_parser = subparsers.add_parser(
        'stop',
        help='stop execution of a Loom server. (It can be started again.)')
    stop_parser.add_argument(
        '-c', '--component', metavar='COMPONENT', action='append',
        choices=COMPONENT_CHOICES,
        help='individual server components to stop (default "all")')
    stop_parser.add_argument(
        '-k', '--skip-component', metavar='SKIPPED_COMPONENT', action='append',
        choices=COMPONENT_CHOICES,
        help='individual server components to stop (default "none")')
    stop_parser.add_argument('-v', '--verbose', action='store_true',
                             help='provide more feedback to console')

    connect_parser = subparsers.add_parser(
        'connect',
        help='connect to a running Loom server')
    connect_parser.add_argument(
        'server_url',
        metavar='SERVER_URL',
        help='URL of the Loom server you wish to connect to')

    disconnect_parser = subparsers.add_parser(
        'disconnect',
        help='disconnect the client from a Loom server '
        'but leave the server running')

    delete_parser = subparsers.add_parser(
        'delete',
        help='delete the Loom server')
    delete_parser.add_argument(
        '-c', '--component', metavar='COMPONENT', action='append',
        choices=COMPONENT_CHOICES,
        help='individual server components to delete (default "all")')
    delete_parser.add_argument(
        '-k', '--skip-component', metavar='SKIPPED_COMPONENT', action='append',
        choices=COMPONENT_CHOICES,
        help='individual server components to delete (default "none")')
    delete_parser.add_argument(
        '-n', '--no-confirm', action='store_true',
        help='no confirmation prompt when deleting the server')
    delete_parser.add_argument('-v', '--verbose', action='store_true',
                               help='provide more feedback to console')
    return parser


def _get_args():
    parser = get_parser()
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    ServerControls().run()
