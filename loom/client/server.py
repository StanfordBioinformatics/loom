#!/usr/bin/env python

import argparse
import imp
import os
import re
import subprocess
import sys
import warnings

from ConfigParser import SafeConfigParser
from loom.client.settings_manager import SettingsManager
from loom.client.common import *
from  loom.common.version import version

DAEMON_EXECUTABLE = os.path.abspath(
    os.path.join(
    os.path.dirname(__file__),
    '../master/loomdaemon/loom_daemon.py'
    ))
GCLOUD_DEPLOY_PLAYBOOK = os.path.abspath(os.path.join(os.path.dirname(__file__), 'gcloud_deploy_playbook.yml'))

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
    parser.add_argument('--fg_webserver', action='store_true', help=argparse.SUPPRESS) # Run webserver in the foreground. Needed to keep Docker container running.
    parser.add_argument('--require_default_settings', '-d', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--verbose', '-v', action='store_true', help='Provide more feedback to console.')

    subparsers = parser.add_subparsers(dest='command')
    start_parser = subparsers.add_parser('start')
    stop_parser = subparsers.add_parser('stop')
    status_parser = subparsers.add_parser('status')

    create_parser = subparsers.add_parser('create')
    create_parser.add_argument('--settings', '-s', metavar='SETTINGS_FILE', default=None,
        help="A settings file can be provided on server creation to override default settings and provide required settings instead of prompting.")
    create_parser.add_argument('--require_default_settings', '-d', action='store_true', help=argparse.SUPPRESS)

    delete_parser = subparsers.add_parser('delete')

    setserver_parser = subparsers.add_parser('set', help='Tells the client how to find the Loom server. This information is stored in %s.' % SERVER_LOCATION_FILE)
    setserver_parser.add_argument('type', choices=['local', 'gcloud'], help='The type of server the client will manage.')
    setserver_parser.add_argument('--name', help='Not used for local. For gcloud, the instance name of the server to manage. If not provided, defaults to %s.' % SERVER_DEFAULT_NAME, metavar='GCE_INSTANCE_NAME', default=SERVER_DEFAULT_NAME)

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
        '''Set server for the client to manage (currently local or gcloud).'''
        # Create directory/directories if they don't exist
        ini_dir = os.path.dirname(SERVER_LOCATION_FILE)
        if not os.path.exists(ini_dir):
            os.makedirs(ini_dir)

        # Write server.ini file
        config = SafeConfigParser()
        config.add_section('server')
        config.set('server', 'type', self.args.type)
        if self.args.type == 'gcloud':
            name = self.args.name
            config.set('server', 'name', name)
        with open(SERVER_LOCATION_FILE, 'w') as configfile:
            config.write(configfile)

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
            'stop': self.stop,
            'delete': self.delete,
        }
        return command_to_method_map

    def start(self):
        if not os.path.exists(get_deploy_settings_filename()):
            self.create()
        self.settings_manager.load_deploy_settings_file()
        env = os.environ.copy()
        env = self._add_server_to_python_path(env)
        env = self._set_database(env)
        env = self._export_django_settings(env)
        self._create_logdirs()
        self._start_daemon(env)
        self._start_webserver(env)

    def _create_logdirs(self):
        for logfile in (self.settings_manager.settings['ACCESS_LOGFILE'],
                        self.settings_manager.settings['ERROR_LOGFILE'],
                        self.settings_manager.settings['DAEMON_LOGFILE'],
                        ):
            logdir = os.path.dirname(logfile)
            if not os.path.exists(logdir):
                os.makedirs(logdir)
        
    def _start_webserver(self, env):
        cmd = "gunicorn %s --bind %s:%s --pid %s --access-logfile %s --error-logfile %s --log-level %s" % (
                self.settings_manager.settings['SERVER_WSGI_MODULE'],
                self.settings_manager.settings['BIND_IP'],
                self.settings_manager.settings['BIND_PORT'],
                self.settings_manager.settings['WEBSERVER_PIDFILE'],
                self.settings_manager.settings['ACCESS_LOGFILE'],
                self.settings_manager.settings['ERROR_LOGFILE'],
                self.settings_manager.settings['LOG_LEVEL'],
                )
        if not self.args.fg_webserver:
            cmd = cmd + " --daemon"
        if self.args.verbose:
            print("Starting webserver with command:\n%s\nand environment:\n%s" % (cmd, env))
        process = subprocess.Popen(
            cmd,
            shell=True,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        process.wait()
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

    def stop(self):
        # Settings needed to get pidfile names.
        if not os.path.exists(get_deploy_settings_filename()):
            raise Exception('No server deploy settings found. Create them with "loom server create" first.')
        self.settings_manager.load_deploy_settings_file()
        self._stop_webserver()
        self._stop_daemon()

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
            # If test database requested, set LOOM_TEST_DATABSE to true and reset database
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
            stdout = subprocess.Popen(
                manage_cmd + ['migrate', '-l'],
                stdout=subprocess.PIPE,
                env=env).communicate()
            if re.search('\[ \]', stdout[0]):
  	        print("The Loom database needs to be initialized or updated. Proceeding...")
		try:
	            stdout = subprocess.Popen(
		        manage_cmd + ['migrate'],
		        stdout=subprocess.PIPE,
		        env=env).communicate()
                except:
                    raise Exception("Failed to apply database migrations. Exiting now.")
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
        '''Create server deploy settings if they don't exist yet.'''
        # TODO: Add -f option to overwrite existing settings
        if os.path.exists(get_deploy_settings_filename()):
            raise Exception('Local server deploy settings already exist. Please delete them with "loom server delete" first.')
        self.settings_manager.create_deploy_settings_file(self.args.settings)
        print 'Created deploy settings at %s.' % get_deploy_settings_filename()

    def delete(self):
        '''Stops server and deletes deploy settings.'''
        # TODO: Ask for confirmation before continuing; add -f option to continue without asking
        this.stop()
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
        """Create server deploy settings if they don't exist yet, create and
        set up a gcloud instance, copy deploy settings to the instance."""
        # TODO: Add -f option to overwrite existing settings
        if os.path.exists(get_deploy_settings_filename()):
            raise Exception('Google Cloud server deploy settings already exist. Please delete them with "loom server delete" first.')
        self.settings_manager.create_deploy_settings_file(self.args.settings)
        print 'Created deploy settings at %s.' % get_deploy_settings_filename()

        # Load settings into environment, where they will be read by the Ansible playbook.
        gce_config = SafeConfigParser()
        gce_config.read(GCE_INI_PATH)
        
        env = os.environ.copy()
        env['GCE_INI_PATH'] = GCE_INI_PATH
        env['GCE_EMAIL'] = gce_config.get('gce', 'gce_service_account_email_address')
        env['GCE_PROJECT'] = gce_config.get('gce', 'gce_project_id')
        env['GCE_PEM_FILE_PATH'] = gce_config.get('gce', 'gce_service_account_pem_file_path')
        env['CLIENT_VERSION'] = version()
        server_tags = self.settings_manager.settings['SERVER_TAGS'].strip()
        if len(server_tags) == 0:
            env['SERVER_TAGS'] = ''
        else:
            env['SERVER_TAGS'] = 'tags=%s' % server_tags
        env.update(self.settings_manager.get_env_settings())

        self.run_playbook(GCLOUD_DEPLOY_PLAYBOOK, env)
        
    def run_playbook(self, playbook, env):
        subprocess.call(['ansible-playbook', '--key-file', self.settings_manager.settings['GCE_KEY_FILE'], '-i', GCE_PY_PATH, playbook, '-vvv'], env=env)

    def start(self):
        """Start the gcloud server instance if it's stopped, then start the Loom server."""
        pass
    def stop(self):
        """Stop the Loom server, then stop the gcloud server instance."""
        pass
    def delete(self):
        """Stop the Loom server, then delete the gcloud server instance. Warn and ask for confirmation because this deletes everything on the VM."""
        pass


class UnhandledCommandError(Exception):
    """Raised when a ServerControls class is given a command that's not in its command map."""
    pass


if __name__=='__main__':
    ServerControls().run()
