#!/usr/bin/env python

import argparse
from datetime import datetime
import imp
import os
import re
import shutil
import subprocess
import sys
import time
import warnings

from ConfigParser import SafeConfigParser
from loom.client.settings_manager import SettingsManager
from loom.client.common import *
from loom.common.version import version
import loom.common.cloud

DAEMON_EXECUTABLE = os.path.abspath(
    os.path.join(
    os.path.dirname(__file__),
    '../master/loomdaemon/loom_daemon.py'
    ))

GCLOUD_SERVER_DEFAULT_NAME = SettingsManager().get_default_setting('gcloud', 'SERVER_NAME')

PLAYBOOKS_PATH = os.path.join(imp.find_module('loom')[1], 'playbooks')
GCLOUD_CREATE_PLAYBOOK = os.path.join(PLAYBOOKS_PATH, 'gcloud_create_server.yml')
GCLOUD_CREATE_SKIP_INSTALLS_PLAYBOOK = os.path.join(PLAYBOOKS_PATH, 'gcloud_create_server_skip_installs.yml')
GCLOUD_START_PLAYBOOK = os.path.join(PLAYBOOKS_PATH, 'gcloud_start_server.yml')
GCLOUD_STOP_PLAYBOOK = os.path.join(PLAYBOOKS_PATH, 'gcloud_stop_server.yml')
GCLOUD_DELETE_PLAYBOOK = os.path.join(PLAYBOOKS_PATH, 'gcloud_delete_server.yml')
GCLOUD_CREATE_BUCKET_PLAYBOOK = os.path.join(PLAYBOOKS_PATH, 'gcloud_create_bucket.yml')
GCLOUD_SETUP_LOOM_USER_PLAYBOOK = os.path.join(PLAYBOOKS_PATH, 'gcloud_setup_loom_user.yml')
NGINX_CONFIG_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), 'nginx.conf'))

def ServerControlsFactory(args):
    """Factory method that checks ~/.loom/server.ini, then instantiates and returns the appropriate class."""

    # Check if we just need the base class (currently, it handles "set" and "status"):
    try:
        return BaseServerControls(args)
    except UnhandledCommandError:
        pass

    server_type = get_server_type()

    # Instantiate the appropriate subclass:
    if server_type == 'local':
        controls = LocalServerControls(args)
    elif server_type == 'gcloud':
        controls = GoogleCloudServerControls(args)
    else:
        raise Exception('Unrecognized server type: %s' % server_type)
    
    return controls

def get_parser(parser=None):
    if parser is None:
        parser = argparse.ArgumentParser(__file__)

    parser.add_argument('--test_database', '-t', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--no_daemon', '-n', action='store_true', help=argparse.SUPPRESS)

    subparsers = parser.add_subparsers(dest='command')
    status_parser = subparsers.add_parser('status')

    create_parser = subparsers.add_parser('create')
    create_parser.add_argument('--require_default_settings', '-d', action='store_true', help=argparse.SUPPRESS)
    create_parser.add_argument('--settings', '-s', metavar='SETTINGS_FILE', default=None,
        help="A settings file can be provided to override default settings.")
    create_parser.add_argument('--verbose', '-v', action='store_true', help='Provide more feedback to console.')

    start_parser = subparsers.add_parser('start')
    start_parser.add_argument('--foreground', action='store_true', help='Run webserver in the foreground. Needed to keep Docker container running.')
    start_parser.add_argument('--verbose', '-v', action='store_true', help='Provide more feedback to console.')

    stop_parser = subparsers.add_parser('stop')
    stop_parser.add_argument('--verbose', '-v', action='store_true', help='Provide more feedback to console.')

    restart_parser = subparsers.add_parser('restart')
    restart_parser.add_argument('--foreground', action='store_true', help='Run webserver in the foreground. Needed to keep Docker container running.')
    restart_parser.add_argument('--verbose', '-v', action='store_true', help='Provide more feedback to console.')
    
    delete_parser = subparsers.add_parser('delete')
    delete_parser.add_argument('--verbose', '-v', action='store_true', help='Provide more feedback to console.')

    setserver_parser = subparsers.add_parser('set', help='Tells the client how to find the Loom server. This information is stored in %s.' % SERVER_LOCATION_FILE)
    setserver_parser.add_argument('type', choices=['local', 'gcloud'], help='The type of server the client will manage.')
    setserver_parser.add_argument('--name', help='Not used for local. For gcloud, the instance name of the server to manage. If not provided, defaults to %s.' % GCLOUD_SERVER_DEFAULT_NAME, metavar='GCE_INSTANCE_NAME', default=GCLOUD_SERVER_DEFAULT_NAME)

    return parser


class BaseServerControls:
    """Base class for managing the Loom server. Handles argument parsing, 
    subcommand routing, and implements common base methods such as setting
    the server type and checking the server status.
    """
    def __init__(self, args=None):
        if args is None:
            args=self._get_args()
        self.args = args
        self._set_run_function(args)

    # Defines what commands this class can handle and maps names to functions.
    def _get_command_map(self):
        return {
            'status': self.status,
            'set': self.setserver
        }

    def _set_run_function(self, args):
        # Map user input command to class method
        try:
            self.run = self._get_command_map()[args.command]
        except KeyError:
            raise UnhandledCommandError('Unrecognized command: %s' % args.command)

    def _get_args(self):
        parser = get_parser()
        args = parser.parse_args()
        return args

    def setserver(self):
        '''Set server for the client to manage (currently local or gcloud) and creates Loom settings directory.'''
        server_location_file = os.path.expanduser(SERVER_LOCATION_FILE)
        # Create directory/directories if they don't exist
        ini_dir = os.path.dirname(server_location_file)
        if not os.path.exists(ini_dir):
            print 'Creating Loom settings directory %s...' % ini_dir
            os.makedirs(ini_dir)

        # Write server.ini file
        config = SafeConfigParser()
        config.add_section('server')
        config.set('server', 'type', self.args.type)
        if self.args.type == 'gcloud':
            name = self.args.name
            config.set('server', 'name', name)
        with open(server_location_file, 'w') as configfile:
            print 'Updating %s...' % server_location_file
            config.write(configfile)

        # Copy NGINX config file to same place
        shutil.copy(NGINX_CONFIG_FILE, ini_dir)

    def status(self):
        if is_server_running():
            print 'OK. The server is running.'
        else:
            print 'No response for server at %s. Do you need to run "loom server start"?' % get_server_url()


class LocalServerControls(BaseServerControls):
    """Subclass for managing a server running on localhost."""

    def __init__(self, args=None):
        BaseServerControls.__init__(self, args)
        self.settings_manager = SettingsManager()

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
            if not os.path.exists(get_deploy_settings_filename()):
                self.create()
            self.settings_manager.load_deploy_settings_file()

            if loom.common.cloud.on_gcloud_vm():
                """We're in gcloud and the client is starting the server on the local instance."""
                subprocess.call(['ansible-playbook', GCLOUD_SETUP_LOOM_USER_PLAYBOOK])
                self.settings_manager.add_gcloud_settings_on_server()

            env = os.environ.copy()
            env = self._add_server_to_python_path(env)
            env = self._export_django_settings(env)
            env = self._set_database(env)
            self._create_logdirs()
            self._start_daemon(env)
            print 'Starting Loom server...'
            self._start_webserver(env)
            self._wait_for_server(target_running_state=True)
        print 'Loom server is running.'

    def stop(self):
        # Settings needed to get pidfile names.
        if is_server_running():
            if not os.path.exists(get_deploy_settings_filename()):
                raise Exception('No server deploy settings found. Create them with "loom server create" first.')
            self.settings_manager.load_deploy_settings_file()
            print "Stopping Loom server..."
            self._stop_webserver()
            self._stop_daemon()
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
        for logfile in (self.settings_manager.settings['ACCESS_LOGFILE'],
                        self.settings_manager.settings['ERROR_LOGFILE'],
                        self.settings_manager.settings['DAEMON_LOGFILE'],
                        ):
            logdir = os.path.dirname(os.path.expanduser(logfile))
            if not os.path.exists(logdir):
                os.makedirs(logdir)
        
    def _start_webserver(self, env):
        cmd = "gunicorn %s --bind %s:%s --pid %s --access-logfile %s --error-logfile %s --log-level %s --capture-output" % (
                self.settings_manager.settings['SERVER_WSGI_MODULE'],
                self.settings_manager.settings['BIND_IP'],
                self.settings_manager.settings['BIND_PORT'],
                self.settings_manager.settings['WEBSERVER_PIDFILE'],
                self.settings_manager.settings['ACCESS_LOGFILE'],
                self.settings_manager.settings['ERROR_LOGFILE'],
                self.settings_manager.settings['LOG_LEVEL'],
                )
        if not self.args.foreground:
            cmd = cmd + " --daemon"
        if self.args.verbose:
            print("Starting webserver with command:\n%s\nand environment:\n%s" % (cmd, env))
        process = subprocess.Popen(
            cmd,
            shell=True,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        (stdout, stderr) = process.communicate()
        if not process.returncode == 0:
            raise Exception('Loom webserver failed to start, with return code "%s". \nFailed command is "%s". \n%s \n%s' % (process.returncode, cmd, stdout, stderr))

    def _start_daemon(self, env):
        if self.args.no_daemon == True:
            return
        pidfile = self.settings_manager.settings['DAEMON_PIDFILE']
        logfile = self.settings_manager.settings['DAEMON_LOGFILE']
        loglevel = self.settings_manager.settings['LOG_LEVEL']
        cmd = "%s %s start --pidfile %s --logfile %s --loglevel %s" % (sys.executable, DAEMON_EXECUTABLE, pidfile, logfile, loglevel)
        if self.args.verbose:
            print("Starting loom daemon with command:\n%s\nand environment:\n%s" % (cmd, env))
        process = subprocess.Popen(
            cmd,
            shell=True,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        process.wait()
        (stdout, stderr) = process.communicate()
        if not process.returncode == 0:
            raise Exception('Loom Daemon failed to start, with return code "%s". \nFailed command is "%s". \n%s \n%s' % (process.returncode, cmd, stderr, stdout))

    def _stop_webserver(self):
        pid = self._get_pid(self.settings_manager.settings['WEBSERVER_PIDFILE'])
        if pid is not None:
            subprocess.call(
                "kill %s" % pid,
                shell=True,
                )
        self._cleanup_pidfile(self.settings_manager.settings['WEBSERVER_PIDFILE'])

    def _stop_daemon(self):
        subprocess.call(
            "%s %s --pidfile %s stop" % (sys.executable, DAEMON_EXECUTABLE, self.settings_manager.settings['DAEMON_PIDFILE']),
            shell=True
            )
        self._cleanup_pidfile(self.settings_manager.settings['DAEMON_PIDFILE'])

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
        if self.args.test_database:
            # If test database requested, set LOOM_TEST_DATABASE to true and reset database
            env['LOOM_TEST_DATABASE'] = 'true'
            commands = [
                manage_cmd + ['flush', '--noinput'],
                manage_cmd + ['migrate'],
                ]
            for command in commands:
                stdout = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    env=env).communicate()
        else:
            proc = subprocess.Popen(
                manage_cmd + ['migrate', '-l'],
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
        This allows master/loomserver/settings.py to load them and make them
        available to Django. Passing settings this way only works in local mode
        (the server is on the same machine as the client launching it).
        """
        env.update(self.settings_manager.get_env_settings())
        return env

    def create(self):
        '''Create server deploy settings. Overwrite existing ones.'''
        self.settings_manager.create_deploy_settings_file(self.args.settings)
        print 'Created deploy settings at %s.' % get_deploy_settings_filename()

    def delete(self):
        '''Stops server and deletes deploy settings.'''
        # TODO: Add -f option to continue without asking
        if not os.path.exists(get_deploy_settings_filename()):
            raise Exception('No local server deploy settings found. Create them with "loom server create" first.')
        self.stop()
        self.settings_manager.delete_deploy_settings_file()
        print 'Deleted deploy settings at %s.' % get_deploy_settings_filename()


class GoogleCloudServerControls(BaseServerControls):
    """Subclass for managing a server running in Google Cloud."""
    
    def __init__(self, args=None):
        BaseServerControls.__init__(self, args)
        self.settings_manager = SettingsManager()
        setup_gce_ini_and_json()

    # Defines what commands this class can handle and maps names to functions.
    def _get_command_map(self):
        command_to_method_map = {
            'create': self.create,
            'start': self.start,
            'stop': self.stop,
            'delete': self.delete,
        }
        return command_to_method_map

    def get_ansible_env(self):
        """Load settings needed for Ansible into environment variables, where
        they will be read by the Ansible playbook. Start with everything in
        the deploy settings file, then add other variables that shouldn't be
        in the file (such as absolute paths containing the user home dir).
        """
        self.settings_manager.load_deploy_settings_file()
        env = os.environ.copy()
        env['DEPLOY_SETTINGS_FILENAME'] = get_deploy_settings_filename()
        env['LOOM_HOME_SUBDIR'] = LOOM_HOME_SUBDIR
        env.update(self.settings_manager.get_env_settings())
        return env

    def create(self):
        """Create server deploy settings if they don't exist yet, set up SSH
        keys, create and set up a gcloud instance, copy deploy settings to the
        instance."""
        if hasattr(self.args, 'settings') and self.args.settings != None:
            print 'Creating deploy settings %s using user settings %s...' % (get_deploy_settings_filename(), self.args.settings)
            self.settings_manager.create_deploy_settings_file(user_settings_file=self.args.settings)
        else:
            print 'Creating deploy settings %s using default settings...' % get_deploy_settings_filename()
            self.settings_manager.create_deploy_settings_file()

        setup_gcloud_ssh()
        env = self.get_ansible_env()

        self.run_playbook(GCLOUD_CREATE_BUCKET_PLAYBOOK, env)
        if self.settings_manager.settings['SERVER_SKIP_INSTALLS'] == 'True':
            return self.run_playbook(GCLOUD_CREATE_SKIP_INSTALLS_PLAYBOOK, env)
        else:
            return self.run_playbook(GCLOUD_CREATE_PLAYBOOK, env)
        
    def run_playbook(self, playbook, env):
        if self.settings_manager.settings['CLIENT_USES_SERVER_INTERNAL_IP'] == 'True':
            env['INVENTORY_IP_TYPE'] = 'internal'   # Tell gce.py to use internal IP for ansible_ssh_host
        else:
            env['INVENTORY_IP_TYPE'] = 'external'   
        env['ANSIBLE_HOST_KEY_CHECKING']='False'    # Don't fail due to host ssh key change when creating a new instance with the same IP
        os.chmod(GCE_PY_PATH, 0755)                 # Make sure dynamic inventory is executable
        cmd_list = ['ansible-playbook', '--key-file', self.settings_manager.settings['GCE_SSH_KEY_FILE'], '-i', GCE_PY_PATH, playbook]
        if self.args.verbose:
            cmd_list.append('-vvv')
        return subprocess.call(cmd_list, env=env)

    def build_docker_image(self, build_path, docker_name, docker_tag):
        """Build Docker image using current code. Dockerfile must exist at build_path."""
        subprocess.call(['docker', 'build', build_path, '-t', '%s:%s' % (docker_name, docker_tag)])

    def push_docker_image(self, docker_tag):
        """Use gcloud to push Docker image to registry specified in tag."""
        subprocess.call(['docker', 'push', docker_tag])

    def start(self):
        """Start the gcloud server instance, then start the Loom server."""
        # TODO: Start the gcloud server instance once supported by Ansible
        instance_name = get_gcloud_server_name()
        current_hosts = get_gcloud_hosts()
        if not os.path.exists(get_deploy_settings_filename()):
            print 'Server deploy settings %s not found. Creating it using default settings.' % get_deploy_settings_filename()
        if instance_name not in current_hosts:
            print 'No instance named \"%s\" found in project \"%s\". Creating it using default settings.' % (instance_name, get_gcloud_project())
        if instance_name not in current_hosts or not os.path.exists(get_deploy_settings_filename()):
            returncode = self.create()
            if returncode != 0:
                raise Exception('Error deploying Google Cloud server instance.')

        env = self.get_ansible_env()
        return self.run_playbook(GCLOUD_START_PLAYBOOK, env)

    def stop(self):
        """Stop the Loom server, then stop the gcloud server instance."""
        env = self.get_ansible_env()
        return self.run_playbook(GCLOUD_STOP_PLAYBOOK, env)
        # TODO: Stop the gcloud server instance once supported by Ansible

    def delete(self):
        """Delete the gcloud server instance. Warn and ask for confirmation because this deletes everything on the VM."""
        env = self.get_ansible_env()
        instance_name = get_gcloud_server_name()
        current_hosts = get_gcloud_hosts()
        if instance_name not in current_hosts:
            print 'No instance named \"%s\" found in project \"%s\". It may have been deleted using another method.' % (instance_name, get_gcloud_project())
            if os.path.exists(get_deploy_settings_filename()):
                print 'Deleting %s...' % get_deploy_settings_filename()
                os.remove(get_deploy_settings_filename())
            return
        else:
            confirmation_input = raw_input('WARNING! This will delete the server instance and attached disks. Data will be lost!\n'+ 
                                       'If you are sure you want to continue, please type the name of the server instance:\n> ')
            if confirmation_input != get_gcloud_server_name():
                print 'Input did not match current server name \"%s\".' % instance_name
            else:
                delete_returncode = self.run_playbook(GCLOUD_DELETE_PLAYBOOK, env)
                if delete_returncode == 0:
                    print 'Instance successfully deleted.'
                    if os.path.exists(get_deploy_settings_filename()):
                        print 'Deleting %s...' % get_deploy_settings_filename()
                        os.remove(get_deploy_settings_filename())
                return delete_returncode


class UnhandledCommandError(Exception):
    """Raised when a ServerControls class is given a command that's not in its command map."""
    pass


if __name__=='__main__':
    ServerControls().run()
