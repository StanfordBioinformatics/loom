#!/usr/bin/env python

import argparse
import ConfigParser
import copy
import errno
import os
import shutil
import subprocess

from loomengine.client.common import *


class ServerControls:
    """Class for managing the Loom server.
    """
    def __init__(self, args=None):
        if args is None:
            args=self._get_args()
        self.args = args
        self._set_run_function(args)

    def _set_run_function(self, args):
        # Map user input command to class method
        commands = {
            'status': self.status,
            'start': self.start,
            'delete': self.delete,
            'stop': self.stop,

            #'disconnect': self.disconnect
            #'connect': self.connect
        }
        self.run = commands[args.command]

    def _get_args(self):
        parser = get_parser()
        args = parser.parse_args()
        return args

    def status(self):
        if is_server_running():
            print 'OK. The server is up.'
        else:
            print 'No response from server at %s' % get_server_url()

    def start(self):
        self._verify_not_already_connected()
        settings = self._get_user_settings()
        print 'Starting Loom server named "%s"' % self._get_required_setting(
            'LOOM_SERVER_NAME', settings)
        self._save_common_settings_file(settings)
        playbook = self._get_required_setting('LOOM_START_SERVER_PLAYBOOK',
                                                            settings)
        self._run_playbook(playbook, settings, verbose=self.args.verbose)

    def stop(self):
        settings = parse_settings_file(
            os.path.join(SHARED_SETTINGS_DIR, SHARED_SETTINGS_FILE))
        print 'Stopping Loom server named "%s"' % self._get_required_setting(
            'LOOM_SERVER_NAME', settings)
        playbook = self._get_required_setting('LOOM_STOP_SERVER_PLAYBOOK',
                                              settings)
        self._run_playbook(playbook, settings, verbose=self.args.verbose)

    def delete(self):
        settings = parse_settings_file(
            os.path.join(SHARED_SETTINGS_DIR, SHARED_SETTINGS_FILE))

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
        self._run_playbook(playbook, settings, verbose=self.args.verbose)
        
        shutil.rmtree(SERVER_ADMIN_DIR)
        os.remove(SERVER_FILE)
        
        # TODO delete settings files

    def _save_common_settings_file(self, settings):
        self._make_dir_if_missing(SHARED_SETTINGS_DIR)
        with open(os.path.join(SHARED_SETTINGS_DIR, SHARED_SETTINGS_FILE), 'w') as f:
            for key, value in sorted(settings.items()):
                f.write('%s=%s\n' % (key, value))
        settings.update({'LOOM_SHARED_SETTINGS_FILE': SHARED_SETTINGS_FILE})
        settings.update({'LOOM_SHARED_SETTINGS_DIR': SHARED_SETTINGS_DIR})

    def _make_dir_if_missing(self, path):
        try:
            os.makedirs(path)
        except OSError as e:
            if e.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                msg = 'ERROR! unable to create directory %s' % path
                if self.args.verbose:
                    msg += '\n' +str(e)
                raise SystemExit(msg)

    def _run_playbook(self, playbook, settings, verbose=False):
        playbook = self._check_stock_dir_and_get_full_path(playbook,
                                                           STOCK_PLAYBOOKS_DIR)
        inventory = self._get_required_setting('LOOM_ANSIBLE_INVENTORY', settings)
        cmd_list = ['ansible-playbook',
                    '-i', inventory,
                    playbook,
                    # Without this, ansible uses /usr/bin/python, which
                    # may be missing needed modules
                    '-e', 'ansible_python_interpreter="/usr/bin/env python"',
                    '-e', 'LOOM_SETTINGS_HOME=%s' % LOOM_SETTINGS_HOME,
                    '-e', 'LOOM_SHARED_SETTINGS_DIR=%s' % SHARED_SETTINGS_DIR,
        ]

        if verbose:
            cmd_list.append('-vvvv')

        env = copy.copy(os.environ)
        env.update(settings) # Settings override env
        return subprocess.call(cmd_list, env=env)

    def _get_required_setting(self, key, settings):
        try:
            return settings[key]
        except KeyError:
            raise SystemExit('ERROR! missing required setting "%s"' % key)

    def _verify_not_already_connected(self):
        """Raise an error if the files "~/.loom/server.cfg" and/or
        "~/.loom/server-admin.cfg" exist.
        """
        if os.path.exists(SERVER_ADMIN_DIR) \
           or os.path.exists(SERVER_FILE):
            raise SystemExit('Cannot create new server because there are existing '\
                             'settings in "%s", and we don\'t want to '\
                             'overwrite them.' % LOOM_SETTINGS_HOME)

    def _get_user_settings(self):
        user_settings = {}
        if self.args.settings_file:
            full_path_to_settings_file = self._check_stock_dir_and_get_full_path(
                self.args.settings_file, STOCK_SETTINGS_DIR)
            user_settings.update(parse_settings_file(full_path_to_settings_file))
        if self.args.extra_settings:
            user_settings.update(self._parse_extra_settings(self.args.extra_settings))
        return user_settings

    def _check_stock_dir_and_get_full_path(self, filepath, stock_dir):
        """Some playbooks and settings files are provided with loom.
        If 'filepath' is the name of one of those files, we return the 
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

    start_parser = subparsers.add_parser(
        'start',
        help='Start or create a loom server')
    start_parser.add_argument('--settings-file', '-s', metavar='SETTINGS_FILE',
                               default='local.yaml')
    start_parser.add_argument('--extra-settings', '-e', action='append',
                               metavar='KEY=VALUE')
    start_parser.add_argument('--verbose', '-v', action='store_true',
                              help='Provide more feedback to console.')

    stop_parser = subparsers.add_parser(
        'stop',
        help='Stop execution of a Loom server. (It can be started again.)')
    stop_parser.add_argument('--verbose', '-v', action='store_true',
                             help='Provide more feedback to console.')

    delete_parser = subparsers.add_parser(
        'delete',
        help='Delete the Loom server')
    delete_parser.add_argument('--verbose', '-v', action='store_true',
                               help='Provide more feedback to console.')

    connect_parser = subparsers.add_parser(
        'connect',
        help='Connect to a running Loom server')
    connect_parser.add_argument(
       'Loom Master URL',
        metavar='LOOM_MASTER_URL',
        help='Enter the URL of the Loom server you wish to connect to.')

    disconnect_parser = subparsers.add_parser(
        'disconnect',
        help='Disconnect the client from a Loom server but leave the server running')

    status_parser = subparsers.add_parser(
        'status',
        help='Show the status of the Loom server')

    return parser


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

