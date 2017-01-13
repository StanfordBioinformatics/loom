#!/usr/bin/env python

import argparse
import copy
from datetime import datetime
import errno
import imp
import json
import os
import re
import shutil
import subprocess
import sys
import time
import warnings

import ConfigParser
from StringIO import StringIO

from loomengine.client import settings_manager
from loomengine.client.common import *
from loomengine.utils.version import version
import loomengine.utils.cloud

STOCK_SETTINGS_DIR = os.path.join(
    os.path.dirname(__file__), '..', 'settings')
STOCK_PLAYBOOKS_DIR = os.path.join(
    os.path.dirname(__file__), '..', 'playbooks')

USER_SETTINGS_DIR = os.path.expanduser('~/.loom')
SERVER_FILE = os.path.join(USER_SETTINGS_DIR, 'server.cfg')
SERVER_ADMIN_FILE = os.path.join(USER_SETTINGS_DIR, 'server-admin.cfg')
SERVER_ADMIN_DIR = os.path.join(USER_SETTINGS_DIR, 'server-admin')
COMMON_SETTINGS_DIR = os.path.join(USER_SETTINGS_DIR, 'common-settings')
COMMON_SETTINGS_FILE = 'settings.cfg'

PARSER_SECTION = 'settings' # dummy name because ConfigParser needs sections

#GCLOUD_SERVER_DEFAULT_NAME = settings_manager.get_default_setting('gcloud', 'SERVER_NAME')
#PLAYBOOKS_PATH = os.path.join(imp.find_module('loomengine')[1], 'playbooks')
#LOCAL_START_PLAYBOOK = os.path.join(PLAYBOOKS_PATH, 'local_start_server.yml')
#GCLOUD_CREATE_PLAYBOOK = os.path.join(PLAYBOOKS_PATH, 'gcloud_create_server.yml')
#GCLOUD_START_PLAYBOOK = os.path.join(PLAYBOOKS_PATH, 'gcloud_start_server.yml')
#GCLOUD_STOP_PLAYBOOK = os.path.join(PLAYBOOKS_PATH, 'gcloud_stop_server.yml')
#GCLOUD_DELETE_PLAYBOOK = os.path.join(PLAYBOOKS_PATH, 'gcloud_delete_server.yml')
#GCLOUD_CREATE_BUCKET_PLAYBOOK = os.path.join(PLAYBOOKS_PATH, 'gcloud_create_bucket.yml')
#NGINX_CONFIG_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), 'nginx.conf'))

def get_parser(parser=None):

    if parser is None:
        parser = argparse.ArgumentParser(__file__)

    subparsers = parser.add_subparsers(dest='command')

    create_parser = subparsers.add_parser(
        'create',
        help='Create and start a new loom server')
    create_parser.add_argument('--settings-file', '-s', metavar='SETTINGS_FILE',
                               default='local.yaml')
    create_parser.add_argument('--extra-settings', '-e', action='append',
                               metavar='KEY=VALUE')

    create_parser.add_argument('--verbose', '-v', action='store_true',
                              help='Provide more feedback to console.')

    start_parser = subparsers.add_parser(
        'start',
        help='Restart a server that was stopped')
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
            'create': self.create,
            'delete': self.delete,
            #'start': self.start,
            #'stop': self.stop,

            #'disconnect': self.disconnect
            #'connect': self.connect
        }
        self.run = commands[args.command]

    def _get_args(self):
        parser = get_parser()
        args = parser.parse_args()
        return args

    def status(self):
        print "status"

    def create(self):
        self._verify_not_already_connected()
        settings = self._get_user_settings()
        self._save_common_settings(settings)
        playbook = self._get_required_setting('LOOM_CREATE_SERVER_PLAYBOOK',
                                                            settings)
                                                            
        self._run_playbook(playbook, settings, verbose=self.args.verbose)

    def _save_common_settings(self, settings):
        self._make_dir_if_missing(COMMON_SETTINGS_DIR)
        with open(os.path.join(COMMON_SETTINGS_DIR, COMMON_SETTINGS_FILE), 'w') as f:
            for key, value in sorted(settings.items()):
                f.write('%s=%s\n' % (key, value))
        settings.update({'LOOM_COMMON_SETTINGS_FILE': COMMON_SETTINGS_FILE})
        settings.update({'LOOM_COMMON_SETTINGS_DIR': COMMON_SETTINGS_DIR})

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
                    '-e', 'ansible_python_interpreter="/usr/bin/env python"']

        if verbose:
            cmd_list.append('-vvvv')

        env = copy.copy(os.environ)
        env.update(settings) # Settings override env
        return subprocess.call(cmd_list, env=env)

    # Playbook must:
    #  - create server.cfg and server-admin.cfg
    # 
    #  - provision host
    #  - start Loom

    def _get_required_setting(self, key, settings):
        try:
            return settings[key]
        except KeyError:
            raise SystemExit('ERROR! missing required setting "%s"' % key)

    def _verify_not_already_connected(self):
        """Raise an error if the files "~/.loom/server.cfg" and/or
        "~/.loom/server-admin.cfg" exist.
        """
        if os.path.exists(SERVER_ADMIN_FILE) \
           or os.path.exists(SERVER_ADMIN_DIR) \
           or os.path.exists(SERVER_FILE) \
           or os.path.exists(COMMON_SETTINGS_DIR):
            raise SystemExit('Cannot create new server because there are existing '\
                'server settings in "%s", and we don\'t want to '\
                'overwrite them.' % USER_SETTINGS_DIR)

    def _get_user_settings(self):
        user_settings = self._parse_settings_file(self.args.settings_file)
        user_settings.update(self._parse_extra_settings(self.args.extra_settings))
        return user_settings

    def _parse_settings_file(self, settings_file):
        if not settings_file:
            return {}
        settings_file = self._check_stock_dir_and_get_full_path(settings_file,
                                                                STOCK_SETTINGS_DIR)
        parser = ConfigParser.SafeConfigParser()
        # preserve uppercase in settings names
        parser.optionxform = lambda option: option.upper()
        try:
            with open(settings_file) as stream:
                # Add a section, since ConfigParser requires it
                stream = StringIO("[%s]\n" % PARSER_SECTION + stream.read())
                parser.readfp(stream)
        except IOError:
            raise SystemExit('ERROR! could not open settings file "%s"' % settings_file)
        except ConfigParser.ParsingError as e:
            raise SystemExit('ERROR! could not parse settings file.\n %s' % e.message)
        if parser.sections() != [PARSER_SECTION]:
            raise SystemExit('ERROR! found extra sections in settings file: "%s".'\
                             'Sections are not needed.' % parser.sections())
        return dict(parser.items(PARSER_SECTION))

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
        if not extra_settings:
            return {}
        settings_dict = {}
        for setting in extra_settings:
            (key, value) = setting.split('=', 1)
            settings_dict[key]=value
        return settings_dict

    def delete(self):
        print "delete"
        pass

'''
    def setserver(self):
        """Set server for the client to manage (currently local or gcloud) and creates Loom settings directory."""
        server_location_file = os.path.expanduser(SERVER_LOCATION_FILE)
        # Create directory/directories if they don't exist
        if not os.path.exists(os.path.expanduser(LOOM_SETTINGS_PATH)):
            print 'Creating Loom settings directory %s...' % os.path.expanduser(LOOM_SETTINGS_PATH)
            os.makedirs(os.path.expanduser(LOOM_SETTINGS_PATH))

        # Write server.ini file
        config = SafeConfigParser()
        config.add_section('server')
        config.set('server', 'type', self.args.type)
        if self.args.type == 'gcloud':
            name = self.args.name
            validate_gcloud_instance_name(name)
            config.set('server', 'name', name)
        with open(server_location_file, 'w') as configfile:
            print 'Updating %s...' % server_location_file
            config.write(configfile)

        shutil.copy(NGINX_CONFIG_FILE, os.path.expanduser(LOOM_SETTINGS_PATH))

class LocalServerControls(BaseServerControls):
    """Subclass for managing a server running on localhost."""

    def __init__(self, args=None):
        BaseServerControls.__init__(self, args)

    # Defines what commands this class can handle and maps names to functions.
    def _get_command_map(self):
        command_to_method_map = {
            'create': self.create,
            'start': self.start,
            'restart': self.restart,
            'stop': self.stop,
            'delete': self.delete,
        }
        return command_to_method_map

    def start(self):
        if not is_server_running():
            if not os.path.exists(settings_manager.get_deploy_settings_filename()):
                self.create()
            settings = settings_manager.read_deploy_settings_file()

            if loomengine.utils.cloud.on_gcloud_vm():
                """We're in gcloud and the client is starting the server on the local instance."""
                settings = settings_manager.add_gcloud_settings_on_server(settings)

            env = os.environ.copy()
            env = self._add_server_to_python_path(env)
            env = self._export_django_settings(env)
            env = self._set_database(env)
            self._create_logdirs()
            print 'Starting Loom server...'
            self._start_webserver(env)
            self._wait_for_server(target_running_state=True)
        print 'Loom server is running.'

    def stop(self):
        # Settings needed to get pidfile names.
        if is_server_running():
            if not os.path.exists(settings_manager.get_deploy_settings_filename()):
                raise Exception('No server deploy settings found. Create them with "loom server create" first.')
            settings = settings_manager.read_deploy_settings_file()
            print "Stopping Loom server..."
            self._stop_webserver()
            self._wait_for_server(target_running_state=False)
        print "Loom server is stopped."

    def restart(self):
        self.stop()
        self.start()

    def _wait_for_server(self, target_running_state=True):
        timeout_seconds=5
        poll_interval_seconds=0.1
        start_time = datetime.now()

        while True:
            time_running = datetime.now() - start_time
            if time_running.seconds > timeout_seconds:
                if target_running_state==True:
                    raise Exception("Timeout while waiting for server to %s" % "start" if target_running_state==True else "stop")
            if is_server_running() == target_running_state:
                return
            time.sleep(poll_interval_seconds)

    def _create_logdirs(self):
        settings = settings_manager.read_deploy_settings_file()
        for logfile in (settings['ACCESS_LOGFILE'],
                        settings['ERROR_LOGFILE'],
                        ):
            logdir = os.path.dirname(os.path.expanduser(logfile))
            if not os.path.exists(logdir):
                os.makedirs(logdir)
        
    def _start_webserver(self, env):
        settings = settings_manager.read_deploy_settings_file()
        docker_image = settings.get('LOOM_DOCKER_IMAGE')
        log_dir = os.path.expanduser(settings.get('LOG_DIR'))
        if not docker_image:
            raise Exception('Required setting "LOOM_DOCKER_IMAGE" is missing')
        cmd_list = ['ansible-playbook',
                    LOCAL_START_PLAYBOOK,
                    '--extra-vars',
                    'LOOM_DOCKER_IMAGE=%s LOG_DIR=%s LOOM_ENV_FILE=%s' \
                    % (docker_image,
                       log_dir,
                       settings_manager.get_deploy_settings_filename()
                    )]
        if self.args.verbose:
            cmd_list.append('-vvvv')
            print ' '.join(cmd_list)
            import pprint
            pprint.pprint(env)
        return subprocess.call(cmd_list)

        if self.args.verbose:
            print("Starting webserver with command:\n%s" % cmd_list)
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        (stdout, stderr) = process.communicate()
        if not process.returncode == 0:
            raise Exception('Loom webserver failed to start, with return code "%s". \nFailed command is "%s". \n%s \n%s' % (process.returncode, cmd, stdout, stderr))

    def _stop_webserver(self):
        settings = settings_manager.read_deploy_settings_file()
        pid = self._get_pid(settings['WEBSERVER_PIDFILE'])
        if pid is not None:
            subprocess.call(
                "kill %s" % pid,
                shell=True,
                )
        self._cleanup_pidfile(settings['WEBSERVER_PIDFILE'])

    def _get_pid(self, pidfile):
        if not os.path.exists(pidfile):
            return None
        try:
            with open(pidfile) as f:
                pid = f.read().strip()
                self._validate_pid(pid)
                return pid
        except:
            return None

    def _validate_pid(self, pid):
        if not re.match('^[0-9]*$', pid):
            raise Exception('Invalid pid "%s" found in pidfile %s' % (pid, pidfile))

    def _cleanup_pidfile(self, pidfile):
        if os.path.exists(pidfile):
            try:
                os.remove(pidfile)
            except:
                warnings.warn('Failed to delete PID file %s' % pidfile)

    def _add_server_to_python_path(self, env):
        env.setdefault('PYTHONPATH', '')
        env['PYTHONPATH'] = "%s:%s" % (SERVER_PATH, env['PYTHONPATH'])
        return env

    def _set_database(self, env):
        manage_cmd = [sys.executable, '%s/manage.py' % SERVER_PATH]
        proc = subprocess.Popen(
            manage_cmd + ['showmigrations', '-l'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env)
        output = proc.communicate()
        if proc.returncode != 0 or re.search('Error', output[0]):
            msg = "Loom could not connect to its database. Exiting now. "
            if self.args.verbose:
                msg += output[0]
            raise Exception(msg)
        elif re.search('\[ \]', output[0]):
  	    print("Welcome to Loom!\nInitializing database for first use...")
            proc = subprocess.Popen(
		manage_cmd + ['migrate'],
		stdout=subprocess.PIPE,
		env=env)
            output = proc.communicate()
            if proc.returncode != 0 or re.search('Error', output[0]):
                msg = "Failed to apply database migrations. Exiting now. "
                if self.args.verbose:
                    msg += stdout[0]
                raise Exception(msg)
        return env

    def _export_django_settings(self, env):
        """Update the environment with settings before launching the webserver.
        This allows master/settings.py to load them and make them
        available to Django. Passing settings this way only works in local mode
        (the server is on the same machine as the client launching it).
        """
        deploy_settings = settings_manager.read_deploy_settings_file()
        expanded_deploy_settings = settings_manager.expand_user_dirs(deploy_settings)
        env.update(expanded_deploy_settings)
        return env

    def create(self):
        """Create server deploy settings. Overwrite existing ones."""
        settings_manager.write_deploy_settings_file(self.args.settings)
        print 'Created deploy settings at %s.' % settings_manager.get_deploy_settings_filename()

    def delete(self):
        """Stops server and deletes deploy settings."""
        if not os.path.exists(settings_manager.get_deploy_settings_filename()):
            raise Exception('No local server deploy settings found. Create them with "loom server create" first.')
        self.stop()
        settings_manager.delete_deploy_settings_file()
        print 'Deleted deploy settings at %s.' % settings_manager.get_deploy_settings_filename()


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

class UnhandledCommandError(Exception):
    """Raised when a ServerControls class is given a command that's not in its command map."""
    pass


if __name__=='__main__':
    ServerControls().run()
