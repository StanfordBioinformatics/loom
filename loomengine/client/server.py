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

from loomengine.client.common import *


STOCK_SETTINGS_DIR = os.path.join(
    os.path.join(imp.find_module('loomengine')[1], 'client', 'settings'))
STOCK_PLAYBOOK_DIR = os.path.join(
    os.path.join(imp.find_module('loomengine')[1], 'client', 'playbooks'))
STOCK_INVENTORY_DIR = os.path.join(
    os.path.join(imp.find_module('loomengine')[1], 'client', 'inventory'))

LOOM_PLAYBOOK_DIR = 'playbooks'
LOOM_INVENTORY_DIR = 'inventory'

LOOM_ADMIN_FILES_DIR = 'admin-files'
LOOM_ADMIN_SETTINGS_FILE = 'admin-settings.conf'
ADMIN_SETTINGS_SECTION = 'settings'

LOOM_SETTINGS_HOME_TEMP_BACKUP = LOOM_SETTINGS_HOME + '.tmp'

def loom_settings_transaction(function):
    """A decorator to restore settings to original state if an error is raised.
    """

    def transaction(*args, **kwargs):
        # Back up settings
        try:
            # Wipe backup dir if it exists
            shutil.rmtree(LOOM_SETTINGS_HOME_TEMP_BACKUP)
        except OSError:
            pass
        if os.path.exists(LOOM_SETTINGS_HOME):
            previous_settings_exist=True
            shutil.copytree(LOOM_SETTINGS_HOME,
                            LOOM_SETTINGS_HOME_TEMP_BACKUP)
        else:
            previous_settings_exist=False
        try:
            function(*args, **kwargs)
        except (Exception, SystemExit) as e:
            if previous_settings_exist:
                print ("WARNING! An error occurred. Rolling back changes to settings.")
            try:
                shutil.rmtree(LOOM_SETTINGS_HOME)
            except OSError:
                pass # dir doesn't exist
            if previous_settings_exist:
                shutil.move(LOOM_SETTINGS_HOME_TEMP_BACKUP,
                                LOOM_SETTINGS_HOME)
            raise e
        # Success. Deleting backup.
        if previous_settings_exist:
            shutil.rmtree(LOOM_SETTINGS_HOME_TEMP_BACKUP)

    return transaction

class ServerControls:
    """Class for managing the Loom server.
    """
    def __init__(self, args=None):
        if args is None:
            args=_get_args()
        self.args = args
        self._set_run_function()

    def _set_run_function(self):
        # Map user input command to class method
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
            print 'OK, the server is up.'
        else:
            print 'No response from server at "%s".' % get_server_url()

    #@loom_settings_transaction
    def start(self):
        settings = self._get_admin_settings()
        # Hard-coded settings that don't come from the user:
        settings.update({
            'LOOM_PLAYBOOK_DIR': LOOM_PLAYBOOK_DIR,
            'LOOM_INVENTORY_DIR': LOOM_INVENTORY_DIR,
            'LOOM_CONNECTION_FILES_DIR': LOOM_CONNECTION_FILES_DIR,
            'LOOM_CONNECTION_SETTINGS_FILE': LOOM_CONNECTION_SETTINGS_FILE,
            'LOOM_ADMIN_FILES_DIR': LOOM_ADMIN_FILES_DIR,
            'LOOM_ADMIN_SETTINGS_FILE': LOOM_ADMIN_SETTINGS_FILE,
        })

        if self._user_provided_settings():
            self._make_dir_if_missing(LOOM_SETTINGS_HOME)
            self._copy_playbooks_to_settings_dir()
            self._copy_inventory_to_settings_dir()

            # These may be later updated by start playbook:
            self._save_admin_settings_file(settings)
            self._copy_admin_files_to_settings_dir()

        print 'Starting Loom server named "%s".' % self._get_required_setting(
            'LOOM_SERVER_NAME', settings)

        playbook = self._get_required_setting(
            'LOOM_START_SERVER_PLAYBOOK', settings)
        retcode = self._run_playbook(playbook, settings, verbose=self.args.verbose)
        if retcode:
            raise SystemExit('ERROR! Playbook to start server failed. There may be '\
                             'active resources such as running docker containers or '\
                             ' VMs that were created by the playbook and not '\
                             'cleaned up.')

    @loom_settings_transaction
    def stop(self):
        if not self._has_admin_settings():
            raise SystemExit('ERROR! No server admin settings found. Nothing to stop.')

        settings = parse_settings_file(
            os.path.join(LOOM_SETTINGS_HOME, LOOM_ADMIN_SETTINGS_FILE))
        print 'Stopping Loom server named "%s".' % self._get_required_setting(
            'LOOM_SERVER_NAME', settings)
        playbook = self._get_required_setting('LOOM_STOP_SERVER_PLAYBOOK',
                                              settings)
        retcode = self._run_playbook(playbook, settings, verbose=self.args.verbose)
        if retcode:
            raise SystemExit('ERROR! Playbook to stop server failed.')

    @loom_settings_transaction
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
                raise SystemExit('ERROR! Loom server not found at "%s".' % server_url)
        elif not is_server_running(url=server_url):
            raise SystemExit('ERROR! Loom server not found at "%s".' % server_url)
        self._copy_connection_files_to_settings_dir()
        connection_settings = { "LOOM_SERVER_URL": server_url }
        self._save_connection_settings_file(connection_settings)
        print 'Connected to Loom server at "%s".' % server_url

    @loom_settings_transaction
    def disconnect(self):
        if not has_connection_settings():
            raise SystemExit(
                'ERROR! No server connection found. Nothing to disconnect.')
        if self._has_admin_settings():
            raise SystemExit(
                'ERROR! Server admin settings found. Disconnecting is not allowed. '\
                'If you really want to disconnect without deleting the server, back '\
                'up the settings in %s and manually remove them.'
                % os.path.join(LOOM_SETTINGS_HOME))
        settings = parse_settings_file(
            os.path.join(LOOM_SETTINGS_HOME, LOOM_CONNECTION_SETTINGS_FILE))
        server_url = settings.get('LOOM_SERVER_URL')
        os.remove(os.path.join(LOOM_SETTINGS_HOME, LOOM_CONNECTION_SETTINGS_FILE))
        if os.path.exists(LOOM_CONNECTION_FILES_DIR):
            shutil.rmtree(LOOM_CONNECTION_FILES_DIR)
        try:
            # remove if empty
            os.rmdir(LOOM_SETTINGS_HOME)
        except OSError:
            pass
        print 'Disconnected from the Loom server at %s \nTo reconnect, '\
            'use "loom server connect %s"' % (server_url, server_url)

    @loom_settings_transaction
    def delete(self):
        if not self._has_admin_settings():
            raise SystemExit(
            'ERROR! No server admin settings found. Nothing to delete.')
        settings = parse_settings_file(
            os.path.join(LOOM_SETTINGS_HOME, LOOM_ADMIN_SETTINGS_FILE))

        server_name =self._get_required_setting('LOOM_SERVER_NAME', settings)
        confirmation_input = raw_input(
            'WARNING! This will delete the Loom server and all its data. '\
            'Data will be lost!\n'\
            'If you are sure you want to continue, please '\
            'type the name of the server:\n> ')

        if confirmation_input != server_name:
            print 'Input did not match current server name \"%s\".' % server_name
            return

        playbook = self._get_required_setting('LOOM_DELETE_SERVER_PLAYBOOK',
                                              settings)
        retcode = self._run_playbook(playbook, settings, verbose=self.args.verbose)

        if retcode:
            raise SystemExit(
                'ERROR! Playbook to delete server failed. '\
                'Skipping deletion of configuration files in "%s".'
                % LOOM_SETTINGS_HOME)

        # Do not attempt remove if value is missing or root
        if not LOOM_SETTINGS_HOME \
           or os.path.abspath(LOOM_SETTINGS_HOME) == os.path.abspath('/'):
            print 'WARNING! LOOM_SETTINGS_HOME is "%s". Refusing to delete.' \
                % LOOM_SETINGS_HOME
        else:
            try:
                if os.path.exists(LOOM_SETTINGS_HOME):
                    shutil.rmtree(LOOM_SETTINGS_HOME)
            except Exception as e:
                print 'WARNING! Failed to remove settings directory %s.\n%s' \
                    % (LOOM_SETTINGS_HOME, str(e))

    def _save_admin_settings_file(self, settings):
        write_settings_file(
            os.path.join(LOOM_SETTINGS_HOME, LOOM_ADMIN_SETTINGS_FILE),
            settings)

    def _save_connection_settings_file(self, settings):
        write_settings_file(
            os.path.join(LOOM_SETTINGS_HOME, LOOM_CONNECTION_SETTINGS_FILE),
            settings)

    def _make_dir_if_missing(self, path):
        try:
            os.makedirs(path)
        except OSError as e:
            if e.errno == errno.EEXIST and os.path.isdir(path):
                pass # Ok, dir exists
            else:
                raise SystemExit('ERROR! Unable to create directory "%s"\n%s'
                                 % (path, str(e)))

    def _copy_playbooks_to_settings_dir(self):
        if self.args.playbook_dir:
            playbook_dir = self.args.playbook_dir
        else:
            playbook_dir = STOCK_PLAYBOOK_DIR
        shutil.copytree(playbook_dir,
                        os.path.join(LOOM_SETTINGS_HOME, LOOM_PLAYBOOK_DIR))

    def _copy_inventory_to_settings_dir(self):
        if self.args.inventory_dir:
            inventory_dir = self.args.inventory_dir
        else:
            inventory_dir = STOCK_INVENTORY_DIR
        shutil.copytree(inventory_dir,
                        os.path.join(LOOM_SETTINGS_HOME, LOOM_INVENTORY_DIR))

    def _copy_admin_files_to_settings_dir(self):
        if self.args.admin_files_dir:
            shutil.copytree(self.args.admin_files_dir,
                            os.path.join(LOOM_SETTINGS_HOME, LOOM_ADMIN_FILES_DIR))
        else:
            # If no files, leave an empty directory
            os.makedirs(
                os.path.join(LOOM_SETTINGS_HOME, LOOM_ADMIN_FILES_DIR))

    def _run_playbook(self, playbook, settings, verbose=False):
        inventory = self._get_required_setting('LOOM_ANSIBLE_INVENTORY', settings)
        if ',' not in inventory:
            inventory = os.path.join(LOOM_SETTINGS_HOME, LOOM_INVENTORY_DIR, inventory)
        cmd_list = ['ansible-playbook',
                    '-i', inventory,
                    os.path.join(LOOM_SETTINGS_HOME, LOOM_PLAYBOOK_DIR, playbook),
                    # Without this, ansible uses /usr/bin/python,
                    # which may be missing needed modules
                    '-e', 'ansible_python_interpreter="/usr/bin/env python"',
        ]
        if 'ANSIBLE_SSH_PRIVATE_KEY_FILE' in settings:
            cmd_list.extend(['--private-key', settings['ANSIBLE_SSH_PRIVATE_KEY_FILE']])
        if verbose:
            cmd_list.append('-vvvv')

        # Add one context-specific setting
        settings.update({ 'LOOM_SETTINGS_HOME': LOOM_SETTINGS_HOME })

        # Add settings to environment, with precedence to environment vars
        settings.update(copy.copy(os.environ))

        return subprocess.call(cmd_list, env=settings)

    def _get_required_setting(self, key, settings):
        try:
            return settings[key]
        except KeyError:
            raise SystemExit('ERROR! Missing required setting "%s".' % key)

    def _user_provided_settings(self):
        # True if user passed settings through commandline arguments
        return self.args.settings_file or self.args.extra_settings

    admin_files_paths = [
        os.path.join(LOOM_SETTINGS_HOME, LOOM_ADMIN_FILES_DIR),
        os.path.join(LOOM_SETTINGS_HOME, LOOM_PLAYBOOK_DIR),
        os.path.join(LOOM_SETTINGS_HOME, LOOM_INVENTORY_DIR),
    ]

    def _has_admin_settings(self):
        admin_settings_path = os.path.join(LOOM_SETTINGS_HOME,
                                           LOOM_ADMIN_SETTINGS_FILE)
        admin_files_paths = [
            os.path.join(LOOM_SETTINGS_HOME, LOOM_ADMIN_FILES_DIR),
            os.path.join(LOOM_SETTINGS_HOME, LOOM_PLAYBOOK_DIR),
            os.path.join(LOOM_SETTINGS_HOME, LOOM_INVENTORY_DIR),
        ]
        has_settings = os.path.exists(admin_settings_path)
        has_files = any(os.path.exists(path) for path in admin_files_paths)
        if has_files and not has_settings:
            raise SystemExit('ERROR! Admin settings are corrupt. No settings file '\
                             'found at "%s", but settings files exist in these '\
                             'directories: [%s]'
                             % (admin_settings_path, ', '.join(admin_files_paths)))
        return has_settings

    def _get_admin_settings(self):
        if self._has_admin_settings():
            if self._user_provided_settings():
                raise SystemExit(
                    'ERROR! Admin settings already exist in "%s". '\
                    'The "--settings-file" and "--extra-settings" '\
                    'flags are not allowed now because new settings '\
                    'and existing settings may conflict.'
                    % os.path.join(LOOM_SETTINGS_HOME, LOOM_ADMIN_SETTINGS_FILE))
            else:
                settings = parse_settings_file(
                    os.path.join(LOOM_SETTINGS_HOME, LOOM_ADMIN_SETTINGS_FILE))
        elif has_connection_settings():
            if self._user_provided_settings():
                raise SystemExit(
                    'ERROR! Connection settings already exist in "%s". '\
                    'The "--settings-file" and "--extra-settings" '\
                    'flags are not allowed now because new settings '\
                    'and existing settings may conflict.'
                    % os.path.join(LOOM_SETTINGS_HOME, LOOM_CONNECTION_SETTINGS_FILE))
            else:
                raise SystemExit(
                    'ERROR! You are already connected to a server. '\
                    'That lets you view or manage workflows, but you do not have '\
                    'the settings needed to manage the server. If you want to '\
                    'start a new server, first disconnect using "loom disconnect".')
        else:
            if self._user_provided_settings():
                settings = self._get_start_settings_from_args()
            else:
                stock_settings_files = ', '.join(stock_settings_files)
                raise SystemExit('ERROR! No settings provided. '\
                                 'Use "--settings-file" to provide your own '\
                                 'custom settings or one of the stock settings '\
                                 'files in "%s": [%s].'
                                 % (STOCK_SETTINGS_DIR,
                                    ', '.join(os.listdir(STOCK_SETTINGS_DIR))))
        self._validate_settings(settings)
        return settings

    def _validate_settings(self, settings):

        # These are always required, independent of what playbooks are used.
        # Additional settings are typically required by the playbooks, but LOOM
        # is blind to those settings.
        REQUIRED_SETTINGS = ['LOOM_SERVER_NAME',
                             'LOOM_START_SERVER_PLAYBOOK',
                             'LOOM_STOP_SERVER_PLAYBOOK',
                             'LOOM_DELETE_SERVER_PLAYBOOK',
                             'LOOM_ANSIBLE_INVENTORY',
        ]
        current_settings = set(settings.keys())
        missing_settings = set(REQUIRED_SETTINGS).difference(current_settings)
        if len(missing_settings) != 0:
            raise SystemExit('ERROR! Missing required settings [%s].'
                             % ', '.join(missing_settings))

    def _get_start_settings_from_args(self):
        settings = {}
        if self.args.settings_file:
            full_path_to_settings_file = self._check_stock_dir_and_get_full_path(
                self.args.settings_file, STOCK_SETTINGS_DIR)
            settings.update(parse_settings_file(full_path_to_settings_file))
        if self.args.extra_settings:
            settings.update(self._parse_extra_settings(self.args.extra_settings))

        # Pick up any LOOM_* settings from the environment, and give precedence to
        # env over settings file. Exclude LOOM_SETTINGS_HOME because it is
        # context-specific.
        for key, value in os.environ.iteritems():
            if key.startswith('LOOM_') and key != 'LOOM_SETTINGS_HOME':
                settings.update({ key: value })

        for key, value in settings.items():
            settings[key] = os.path.expanduser(value)

        return settings

    def _check_stock_dir_and_get_full_path(self, filepath, stock_dir):
        """If 'filepath' is found in stock settings, we return the
        full path to that stock file. Otherwise, we interpret filepath relative
        to the current working directory.
        """
        if os.path.exists(
                os.path.join(stock_dir, filepath)):
            # This matches one of the stock settings files
            return os.path.abspath(os.path.join(stock_dir, filepath))
        elif os.path.exists(
                os.path.join(os.getcwd(), filepath)):
            # File was found relative to current working directory
            return os.path.abspath(os.path.join(os.getcwd(), filepath))
        else:
            # No need to raise exception now for missing file--we'll
            # handle it when we try to read it
            return filepath

    def _copy_connection_files_to_settings_dir(self):
        if self.args.connection_files_dir:
            shutil.copytree(self.args.connection_files_dir,
                            os.path.join(LOOM_SETTINGS_HOME, LOOM_CONNECTION_FILES_DIR))
        else:
            # If no files, leave an empty directory
            os.makedirs(LOOM_CONNECTION_FILES_DIR)

    def _parse_extra_settings(self, extra_settings):
        settings_dict = {}
        for setting in extra_settings:
            (key, value) = setting.split('=', 1)
            settings_dict[key]=value
        return settings_dict


def get_parser(parser=None):

    if parser is None:
        parser = argparse.ArgumentParser(__file__)

    subparsers = parser.add_subparsers(dest='command')

    status_parser = subparsers.add_parser(
        'status',
        help='Show the status of the Loom server')

    start_parser = subparsers.add_parser(
        'start',
        help='Start or create a loom server')
    start_parser.add_argument('--settings-file', '-s', metavar='SETTINGS_FILE')
    start_parser.add_argument('--extra-settings', '-e', action='append',
                               metavar='KEY=VALUE')
    start_parser.add_argument('--playbook-dir', '-p', metavar='PLAYBOOK_DIR')
    start_parser.add_argument('--inventory-dir', '-i', metavar='INVENTORY_DIR')
    start_parser.add_argument('--admin-files-dir', '-f', metavar='ADMIN_FILES_DIR')
    start_parser.add_argument('--verbose', '-v', action='store_true',
                              help='Provide more feedback to console.')

    stop_parser = subparsers.add_parser(
        'stop',
        help='Stop execution of a Loom server. (It can be started again.)')
    stop_parser.add_argument('--verbose', '-v', action='store_true',
                             help='Provide more feedback to console.')

    connect_parser = subparsers.add_parser(
        'connect',
        help='Connect to a running Loom server')
    connect_parser.add_argument(
        'server_url',
        metavar='LOOM_SERVER_URL',
        help='Enter the URL of the Loom server you wish to connect to.')
    connect_parser.add_argument('--connection-files-dir', '-c',
                              metavar='CONNECTION_FILES_DIR')

    disconnect_parser = subparsers.add_parser(
        'disconnect',
        help='Disconnect the client from a Loom server but leave the server running')

    delete_parser = subparsers.add_parser(
        'delete',
        help='Delete the Loom server')
    delete_parser.add_argument('--verbose', '-v', action='store_true',
                               help='Provide more feedback to console.')

    return parser

def _get_args():
    parser = get_parser()
    args = parser.parse_args()
    return args


if __name__=='__main__':
    ServerControls().run()
