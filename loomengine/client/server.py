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
STOCK_PLAYBOOKS_DIR = os.path.join(
    os.path.join(imp.find_module('loomengine')[1], 'client', 'playbooks'))

LOOM_PLAYBOOKS_DIR = os.path.join(LOOM_SETTINGS_HOME, 'playbooks')

LOOM_ADMIN_FILES_DIR = os.path.join(LOOM_SETTINGS_HOME, 'admin-files')
LOOM_ADMIN_SETTINGS_FILE = 'admin-settings.conf'

LOOM_SETTINGS_HOME_TEMP_BACKUP = LOOM_SETTINGS_HOME + '.tmp'

LOOM_SHARED_FILES_DIR = os.path.join(
    LOOM_SETTINGS_HOME, 'shared-files')
LOOM_SHARED_SETTINGS_FILE = 'shared-settings.conf'

TEMPLATES_DIR = os.path.join(
    os.path.join(imp.find_module('loomengine')[1], 'client', 'templates'))
LOOM_SERVER_SETTINGS_TEMPLATE_PATH = os.path.join(TEMPLATES_DIR, 'server.conf')

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
                print ("WARNING! An error occurred. Rolling back settings.")
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
        verify_has_server_file()
        if is_server_running():
            print 'OK, the server is up.'
        else:
            print 'No response from server at "%s".' % get_server_url()

    @loom_settings_transaction
    def start(self):
        settings = self._get_user_settings_and_arbitrate_their_sources()
        # Just one shared setting that doesn't come from the user:
        settings.update({
            'LOOM_SHARED_SETTINGS_FILE': LOOM_SHARED_SETTINGS_FILE })

        self._make_dir_if_missing(LOOM_SETTINGS_HOME)
        self._make_dir_if_missing(LOOM_SERVER_FILES_DIR)
        self._make_dir_if_missing(LOOM_SHARED_FILES_DIR)
        self._make_dir_if_missing(LOOM_ADMIN_FILES_DIR)
        self._save_shared_settings_file(settings)
        self._copy_playbooks_to_settings_dir()

        settings.update(self._get_context_specific_settings())

        print 'Starting Loom server named "%s".' % self._get_required_setting(
            'LOOM_SERVER_NAME', settings)

        playbook = self._get_required_setting(
            'LOOM_START_SERVER_PLAYBOOK', settings)
        retcode = self._run_playbook(playbook, settings, verbose=self.args.verbose)
        if retcode:
            raise SystemExit('ERROR! Playbook to create server failed.')

    @loom_settings_transaction
    def stop(self):
        if not self._has_admin_files():
            raise SystemExit('ERROR! No server admin settings found. Nothing to stop.')

        settings = parse_settings_file(
            os.path.join(LOOM_SETTINGS_HOME, LOOM_SHARED_SETTINGS_FILE))
        print 'Stopping Loom server named "%s".' % self._get_required_setting(
            'LOOM_SERVER_NAME', settings)
        playbook = self._get_required_setting('LOOM_STOP_SERVER_PLAYBOOK',
                                              settings)
        retcode = self._run_playbook(playbook, settings, verbose=self.args.verbose)
        if retcode:
            raise SystemExit('ERROR! Playbook to stop server failed.')

    @loom_settings_transaction
    def connect(self):
        if has_server_file():
            raise SystemExit(
                'ERROR! Already connected to "%s".' % get_server_url())

        server_url = self.args.server_url
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
        with open(os.path.join(
                LOOM_SETTINGS_HOME,
                LOOM_SERVER_SETTINGS_FILE),
                  'w') as f:
            f.write("LOOM_SERVER_URL: %s" % server_url)
        print 'Connected to Loom server at "%s".' % server_url

    @loom_settings_transaction
    def disconnect(self):
        if not has_server_file():
            raise SystemExit(
                'ERROR! No server connection found. Nothing to disconnect.')
        if self._has_admin_files():
            raise SystemExit(
                'ERROR! Server admin settings found. Disconnecting is not allowed. '\
                'If you really want to disconnect without deleting the server, back '\
                'up the settings in %s and manually remove them.'
                % os.path.join(LOOM_SETTINGS))
        settings = parse_settings_file(os.path.join(LOOM_SETTINGS_HOME, LOOM_SERVER_SETTINGS_FILE))
        server_url = settings.get('LOOM_SERVER_URL')
        os.remove(os.path.join(LOOM_SETTINGS_HOME, LOOM_SERVER_SETTINGS_FILE))
        print 'Disconnected from the Loom server at %s \nTo reconnect, '\
            'use "loom server connect %s"' % (server_url, server_url)

    @loom_settings_transaction
    def delete(self):
        if not self._has_admin_files():
            raise SystemExit(
            'ERROR! No server admin settings found. Nothing to delete.')
        settings = parse_settings_file(
            os.path.join(LOOM_SETTINGS_HOME, LOOM_SHARED_SETTINGS_FILE))

        server_name =self._get_required_setting('LOOM_SERVER_NAME', settings)
        confirmation_input = raw_input(
            'WARNING! This will delete the Loom server and all its data. '\
            'Data will be lost!\n'\
            'If you are sure you want to continue, please '\
            'type the name of the server instance:\n> ')

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

    def _save_shared_settings_file(self, settings):
        with open(os.path.join(
                LOOM_SETTINGS_HOME, LOOM_SHARED_SETTINGS_FILE), 'w') as f:
            for key, value in sorted(settings.items()):
                f.write('%s=%s\n' % (key, value))

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
        shutil.copytree(self.args.playbook_root, LOOM_PLAYBOOKS_DIR)
            
    def _run_playbook(self, playbook, settings, verbose=False):
        inventory = self._get_required_setting('LOOM_ANSIBLE_INVENTORY', settings)
        cmd_list = ['ansible-playbook',
                    '-i', inventory,
                    os.path.join(LOOM_PLAYBOOKS_DIR, playbook),
                    # Without this, ansible uses /usr/bin/python, which
                    # may be missing needed modules
                    '-e', 'ansible_python_interpreter="/usr/bin/env python"',
        ]
        if verbose:
            cmd_list.append('-vvvv')
        env = copy.copy(os.environ)
        env.update(settings) # Settings override env, because env values on local
        # won't be propagated to other environments and we want these settings to
        # be predictabley global.

        return subprocess.call(cmd_list, env=env)

    def _get_required_setting(self, key, settings):
        try:
            return settings[key]
        except KeyError:
            raise SystemExit('ERROR! Missing required setting "%s".' % key)

    def _user_provided_settings(self):
        # True if user passed settings through commandline arguments
        return self.args.settings_file or self.args.extra_settings

    def _has_admin_files(self):
        return os.path.exists(os.path.join(
            LOOM_SETTINGS_HOME, LOOM_ADMIN_SETTINGS_FILE))

    def _get_user_settings_and_arbitrate_their_sources(self):
        settings = {}
        if self._user_provided_settings():
            if self._has_admin_files():
                raise SystemExit(
                    'ERROR! Using the "--settings-file" and "--extra-settings '\
                    'flags is not allowed now because it would conflict '\
                    'with existing admin settings in "%s"'
                    % os.path.join(LOOM_SETTINGS_HOME, LOOM_ADMIN_SETTINGS_FILE))
            else:
                if has_server_file():
                    raise SystemExit(
                        'ERROR! Using the "--settings-file" and "--extra-settings '\
                        'flags is not allowed now because it may conflict '\
                        'with existing server settings in "%s"'
                        % os.path.join(LOOM_SETTINGS_HOME, LOOM_SERVER_SETTINGS_FILE))
                else:
                    settings.update(self._get_start_settings_from_args())
        else:
            if self._has_admin_files():
                settings.update(parse_settings_file(os.path.join(
                    LOOM_SETTINGS_HOME,
                    LOOM_SHARED_SETTINGS_FILE)))
            else:
                if has_server_file():
                    raise SystemExit(
                        'ERROR! You are already connected to a server. '\
                        'That lets you view or manage workflows, but you do not have '\
                        'the settings needed to manage a server. If you want to '\
                        'start a new server, first disconnect using "loom disconnect".'
                        % LOOM_SERVER_SETTINGS_FILE)
                else:
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
        # Additional settings are typically required by he playbooks, but LOOM
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

    def _get_context_specific_settings(self):
        # These are context-dependent and not included in the settings file
        return {
            'LOOM_SETTINGS_HOME': LOOM_SETTINGS_HOME,

            # Config files to be added or read from to these dirs by playbooks:
            'LOOM_SERVER_FILES_DIR': LOOM_SERVER_FILES_DIR,
            'LOOM_ADMIN_FILES_DIR': LOOM_ADMIN_FILES_DIR,
            'LOOM_SHARED_FILES_DIR': LOOM_SHARED_FILES_DIR,
            'LOOM_PLAYBOOKS_DIR': LOOM_PLAYBOOKS_DIR,

            # Files to be created by playbook from template:
            'LOOM_SERVER_SETTINGS_FILE': LOOM_SERVER_SETTINGS_FILE,
            'LOOM_SERVER_SETTINGS_TEMPLATE_PATH': LOOM_SERVER_SETTINGS_TEMPLATE_PATH,
            
            # To be created by playbook:
            'LOOM_ADMIN_SETTINGS_FILE': LOOM_ADMIN_SETTINGS_FILE,

            # LOOM_SHARED_SETTINGS_FILE not needed--values are passed as env variables
        }
        
    def _get_start_settings_from_args(self):
        settings = {}
        if self.args.settings_file:
            full_path_to_settings_file = self._check_stock_dir_and_get_full_path(
                self.args.settings_file, STOCK_SETTINGS_DIR)
            settings.update(parse_settings_file(full_path_to_settings_file))
        if self.args.extra_settings:
            settings.update(self._parse_extra_settings(self.args.extra_settings))
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
    start_parser.add_argument('--playbook-root', '-p', metavar='PLAYBOOK_ROOT',
                              default=STOCK_PLAYBOOKS_DIR)
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


'''
class GoogleCloudServerControls(BaseServerControls):
    """Subclass for managing a server running in Google Cloud."""
    
    def __init__(self, args=None):
        BaseServerControls.__init__(self, args)

    # Defines what commands this class can handle and maps names to functions.
    def _get_command_map(self):
        command_to_method_map = {
            'create': self.create,
            'start': self.start,
            'stop': self.stop,
            'delete': self.delete,
        }
        return command_to_method_map

    def create(self):
        """Create a service account for the server (can use custom
        service account instead), create gce.ini, create JSON credential, create
        server deploy settings, set up SSH keys, create and set up a gcloud
        instance, and copy deploy settings to the instance.
        """
        default_settings = settings_manager.get_default_settings()
        default_plus_user_settings = settings_manager.add_user_settings(default_settings, self.args.settings)

        if not settings_manager.has_custom_service_account(default_plus_user_settings):
            # Default behavior: create a service account based on server name, grant roles, create JSON credential, write to ini.
            server_name = get_gcloud_server_name()
            print 'Creating service account for instance %s...' % server_name 
            try:
                create_service_account(server_name)
            except googleapiclient.errors.HttpError as e:
                print 'Warning: %s' % e._get_reason()
            email = find_service_account_email(server_name)
            if email != None:
                print 'Service account %s created.' % email
            roles = json.loads(default_plus_user_settings['SERVICE_ACCOUNT_ROLES'])
            print 'Granting "%s" roles to service account %s:' % (roles, email)
            grant_roles(roles, email)
            create_gce_json(email)
            create_gce_ini(email)
        else:
            # Pre-existing service account specified: copy and validate JSON credential, and write to ini.
            if self.args.key:
                print 'Copying %s to %s...' % (self.args.key, GCE_JSON_PATH)
                shutil.copyfile(self.args.key, os.path.expanduser(GCE_JSON_PATH))
            create_gce_ini(default_plus_user_settings['CUSTOM_SERVICE_ACCOUNT_EMAIL'])

        settings_manager.write_deploy_settings_file(self.args.settings)

        env = settings_manager.get_ansible_env()
        self.run_playbook(GCLOUD_CREATE_BUCKET_PLAYBOOK, env)
        return self.run_playbook(GCLOUD_CREATE_PLAYBOOK, env)
        
    def run_playbook(self, playbook, env):
        settings = settings_manager.read_deploy_settings_file()

        if settings['CLIENT_USES_SERVER_INTERNAL_IP'] == 'True':
            env['INVENTORY_IP_TYPE'] = 'internal'   # Tell gce.py to use internal IP for ansible_ssh_host
        else:
            env['INVENTORY_IP_TYPE'] = 'external'   
        env['ANSIBLE_HOST_KEY_CHECKING']='False'    # Don't fail due to host ssh key change when creating a new instance with the same IP
        os.chmod(GCE_PY_PATH, 0755)                 # Make sure dynamic inventory is executable
        cmd_list = ['ansible-playbook', '--key-file', settings['GCE_SSH_KEY_FILE'], '-i', GCE_PY_PATH, playbook]
        if self.args.verbose:
            cmd_list.append('-vvvv')
            print ' '.join(cmd_list)
            import pprint
            pprint.pprint(env)
        return subprocess.call(cmd_list, env=env)

    def start(self):
        """Start the gcloud server instance, then start the Loom server."""
        # TODO: Start the gcloud server instance once supported by Ansible
        instance_name = get_gcloud_server_name()
        current_hosts = get_gcloud_hosts()
        if not os.path.exists(settings_manager.get_deploy_settings_filename()):
            print 'Server deploy settings %s not found. Creating it using default settings.' % settings_manager.get_deploy_settings_filename()
        if instance_name not in current_hosts:
            print 'No instance named \"%s\" found in project \"%s\". Creating it using default settings.' % (instance_name, get_gcloud_project())
        if instance_name not in current_hosts or not os.path.exists(settings_manager.get_deploy_settings_filename()):
            returncode = self.create()
            if returncode != 0:
                raise Exception('Error deploying Google Cloud server instance.')

        env = settings_manager.get_ansible_env()
        return self.run_playbook(GCLOUD_START_PLAYBOOK, env)

    def stop(self):
        """Stop the Loom server, then stop the gcloud server instance."""
        env = settings_manager.get_ansible_env()
        return self.run_playbook(GCLOUD_STOP_PLAYBOOK, env)
        # TODO: Stop the gcloud server instance once supported by Ansible

    def delete(self):
        """Delete the gcloud server instance. Warn and ask for confirmation because this deletes everything on the VM."""
        settings = settings_manager.read_deploy_settings_file()
        try:
            instance_name = get_gcloud_server_name()
            current_hosts = get_gcloud_hosts()
            confirmation_input = raw_input('WARNING! This will delete the server\'s instance, attached disks, and service account. Data will be lost!\n'+ 
                                           'If you are sure you want to continue, please type the name of the server instance:\n> ')
            if confirmation_input != get_gcloud_server_name():
                print 'Input did not match current server name \"%s\".' % instance_name
                return

            if instance_name not in current_hosts:
                print 'No instance named \"%s\" found in project \"%s\". It may have been deleted using another method.' % (instance_name, get_gcloud_project())
            else:
                env = settings_manager.get_ansible_env()
                delete_returncode = self.run_playbook(GCLOUD_DELETE_PLAYBOOK, env)
                if delete_returncode == 0:
                    print 'Instance successfully deleted.'
        except Exception as e:
            print e

        try:
            email = find_service_account_email(instance_name)
            custom_email = settings['CUSTOM_SERVICE_ACCOUNT_EMAIL']
            if email and custom_email == 'None':
                print 'Deleting service account %s...' % email
                delete_service_account(email)
                json_key = os.path.expanduser(GCE_JSON_PATH)
                if os.path.exists(json_key):
                    print 'Deleting %s...' % json_key
                    os.remove(json_key)
        except Exception as e:
            print e

        cleanup_files = [settings_manager.get_deploy_settings_filename(), GCE_INI_PATH, SERVER_LOCATION_FILE]
        for path in cleanup_files:
            path = os.path.expanduser(path)
            if os.path.exists(path):
                print 'Deleting %s...' % path
                os.remove(path)

        delete_libcloud_cached_credential()

'''

