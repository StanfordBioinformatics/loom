#!/usr/bin/env python

import argparse
import ConfigParser
import copy
import errno
import glob
import jinja2
import os
import shutil
import subprocess
import urlparse
import warnings

from loomengine import verify_has_connection_settings, \
    has_connection_settings, is_server_running
import loomengine_utils.version
from . import to_bool

STOCK_PLAYBOOK_DIR = os.path.join(
    os.path.join(imp.find_module('loomengine')[1], 'playbooks'))
LOOM_PLAYBOOK_DIR = 'playbooks'
LOOM_RESOURCE_DIR = 'resources'
LOOM_SERVER_SETTINGS_FILE = 'server-settings.conf'

LOOM_SETTINGS_HOME_TEMP_BACKUP = LOOM_SETTINGS_HOME + '.tmp'


class ServerControls(object):
    """Class for managing the Loom server.
    """
    def __init__(self, args=None, silent=False):
        if args is None:
            args = _get_args()
        self.args = args
        self.silent = silent
        self._set_run_function()

    def _print(self, text):
        if not self.silent:
            print text

    def _set_run_function(self):
        # Map user input command to method
        commands = {
            'status': self.status,
            'connect': self.connect,
            'disconnect': self.disconnect,
        }
        self.run = commands[self.args.command]

    def status(self):
        verify_has_connection_settings()
        if is_server_running():
            self._print('OK, the server is up at %s' % get_server_url())
        else:
            raise SystemExit(
                'No response from server at %s' % get_server_url())

    def connect(self):
        server_url = self.args.server_url
        if has_connection_settings():
            raise SystemExit(
                'ERROR! Already connected to "%s".' % get_server_url())

        parsed_url = urlparse.urlparse(server_url)
        if not parsed_url.scheme:
            if is_server_running(url='https://' + server_url):
                server_url = 'https://' + server_url
            elif is_server_running(url='http://' + server_url):
                server_url = 'http://' + server_url
            else:
                raise SystemExit(
                    'ERROR! Loom server not found at "%s".' % server_url)
        elif not is_server_running(url=server_url):
            raise SystemExit(
                'ERROR! Loom server not found at "%s".' % server_url)
        connection_settings = {"LOOM_SERVER_URL": server_url}
        self._save_connection_settings_file(connection_settings)
        self._print('Connected to Loom server at "%s".' % server_url)

    def disconnect(self):
        if not has_connection_settings():
            raise SystemExit(
                'ERROR! No server connection found. Nothing to disconnect.')
        if self._has_server_settings():
            raise SystemExit(
                'ERROR! Server settings found. Disconnecting is not allowed. '
                'If you really want to disconnect without deleting the '
                'server, back up the settings in %s and manually remove them.'
                % os.path.join(LOOM_SETTINGS_HOME))
        settings = parse_settings_file(
            os.path.join(LOOM_SETTINGS_HOME, LOOM_CONNECTION_SETTINGS_FILE))
        server_url = settings.get('LOOM_SERVER_URL')
        os.remove(os.path.join(
            LOOM_SETTINGS_HOME, LOOM_CONNECTION_SETTINGS_FILE))
        delete_token()
        try:
            # remove if empty
            os.rmdir(LOOM_SETTINGS_HOME)
        except OSError:
            pass
        self._print('Disconnected from the Loom server at %s \nTo reconnect, '
                    'use "loom server connect %s"' % (server_url, server_url))

    def _save_connection_settings_file(self, settings):
        if not os.path.exists(LOOM_SETTINGS_HOME):
            os.makedirs(LOOM_SETTINGS_HOME)
        write_settings_file(
            os.path.join(LOOM_SETTINGS_HOME, LOOM_CONNECTION_SETTINGS_FILE),
            settings)

    def _make_dir_if_missing(self, path):
        try:
            os.makedirs(path)
        except OSError as e:
            if e.errno == errno.EEXIST and os.path.isdir(path):
                pass  # Ok, dir exists
            else:
                raise SystemExit('ERROR! Unable to create directory "%s"\n%s'
                                 % (path, str(e)))


def get_parser(parser=None):

    if parser is None:
        parser = argparse.ArgumentParser(__file__)

    subparsers = parser.add_subparsers(dest='command')

    status_parser = subparsers.add_parser(
        'status',
        help='show the status of the Loom server')

    connect_parser = subparsers.add_parser(
        'connect',
        help='connect to a running Loom server')
    connect_parser.add_argument(
        'server_url',
        metavar='LOOM_SERVER_URL',
        help='URL of the Loom server you wish to connect to')

    disconnect_parser = subparsers.add_parser(
        'disconnect',
        help='disconnect the client from a Loom server '
        'but leave the server running')

    return parser


def _get_args():
    parser = get_parser()
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    ServerControls().run()
