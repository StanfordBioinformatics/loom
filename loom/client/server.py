#!/usr/bin/env python

import argparse
import os
import re
import requests
import subprocess
import sys
import warnings

from abc import ABCMeta, abstractmethod
from ConfigParser import SafeConfigParser
from loom.client import settings_manager

DAEMON_EXECUTABLE = os.path.abspath(
    os.path.join(
    os.path.dirname(__file__),
    '../master/loomdaemon/loom_daemon.py'
    ))

SERVER_LOCATION_FILE = os.path.join(os.getenv('HOME'), '.loom', 'server.ini')

def is_server_running(master_url):
    try:
        response = requests.get(master_url + '/api/status/')
        if response.status_code == 200:
            return True
        else:
            raise Exception("unexpected status code %s from server" % response.status_code)
    except requests.exceptions.ConnectionError:
        return False

def ServerControls(args):
    """Factory method that checks ~/.loom/server.ini, then instantiates and returns the appropriate concrete subclass."""

    # Check server type
    config = SafeConfigParser()
    config.read(SERVER_LOCATION_FILE)
    server_type = config.get('server', 'type')

    # Instantiate concrete subclass
    if server_type == 'local':
        controls = LocalServerControls(args)
    elif server_type == 'gcloud':
        controls = GcloudServerControls(args)
    else:
        raise Exception('Unrecognized server type: %s' % server_type)
    
    return controls

class BaseServerControls:
    """Abstract base class for managing the Loom server. Defines common methods such as argument parsing and setting server type."""
    
    __metaclass__ = ABCMeta

    def __init__(self, args=None):
        if args is None:
            args=self._get_args()
        self.args = args
        self.settings_manager = settings_manager.SettingsManager(require_default_settings=args.require_default_settings)

        # Set run function
        self._set_run_function(args)

    def _set_run_function(self, args):
        # Map user input command to class method
        command_to_method_map = {
            'status': self.status,
            'start': self.start,
            'stop': self.stop,
            'create': self.create,
            'delete': self.delete,
            'set': self.setserver
        }
        try:
            self.run = command_to_method_map[args.command]
        except KeyError:
            raise Exception('Unrecognized command: %s' % args.command)

    @classmethod
    def get_parser(cls, parser=None):
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
        create_parser.add_argument('--settings', '-s', metavar='SETTINGS_FILE',
            help="A settings file can be provided on server creation to override default settings and provide required settings instead of prompting.")
        create_parser.add_argument('--require_default_settings', '-d', action='store_true', help=argparse.SUPPRESS)

        delete_parser = subparsers.add_parser('delete')

        setserver_parser = subparsers.add_parser('set')
        setserver_parser.add_argument('type', choices=['local', 'gcloud'], help='The type of server the client will manage.')
        setserver_parser.add_argument('--name', help='The instance name of the server to manage.')

        return parser

    def _get_args(self):
        parser = self.get_parser()
        args = parser.parse_args()
        return args

    def setserver(self):
        '''Set server for the client to manage (currently local or gcloud).'''
        config = SafeConfigParser()
        config.add_section('server')
        config.set('server', 'type', self.args.type)
        if self.args.type == 'gcloud':
            if self.args.name:
                name = self.args.name
            else:
                name = 'loom-master'
            config.set('server', 'name', name)
        with open(SERVER_LOCATION_FILE, 'w') as configfile:
            config.write(configfile)

    def status(self):
        url = self.get_server_url()
        if is_server_running(url):
            print 'OK. The server is running.'
        else:
            print 'No response for server at %s. Do you need to run "loom server start"?' % url

    # Required overrides
    @abstractmethod
    def create(self):
        pass
    @abstractmethod
    def delete(self):
        pass
    @abstractmethod
    def start(self):
        pass
    @abstractmethod
    def stop(self):
        pass
    @abstractmethod
    def get_server_url(self):
        pass


class LocalServerControls(BaseServerControls):

    def start(self):
        env = os.environ.copy()
        env = self._add_server_to_python_path(env)
        env = self._set_database(env)
        env = self._export_django_settings(env)
        self._create_logdirs()
        self._start_daemon(env)
        self._start_webserver(env)

    def _create_logdirs(self):
        for logfile in (self.settings_manager.get_access_logfile(),
                        self.settings_manager.get_error_logfile(),
                        self.settings_manager.get_daemon_logfile()):
            logdir = os.path.dirname(logfile)
            if not os.path.exists(logdir):
                os.makedirs(logdir)
        
    def _start_webserver(self, env):
        cmd = "gunicorn %s --bind %s:%s --pid %s --access-logfile %s --error-logfile %s --log-level %s" % (
                self.settings_manager.get_server_wsgi_module(), 
                self.settings_manager.get_bind_ip(), 
                self.settings_manager.get_bind_port(), 
                self.settings_manager.get_webserver_pidfile(),
                self.settings_manager.get_access_logfile(),
                self.settings_manager.get_error_logfile(),
                self.settings_manager.get_log_level(),
                )
        if not self.args.fg_webserver:
            cmd = cmd + " --daemon"
        if self.args.verbose:
            print("Starting webserver with command:\n%s" % cmd)
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
        pidfile = self.settings_manager.get_daemon_pidfile()
        logfile = self.settings_manager.get_daemon_logfile()
        loglevel = self.settings_manager.get_log_level()
        cmd = "%s %s start --pidfile %s --logfile %s --loglevel %s" % (sys.executable, DAEMON_EXECUTABLE, pidfile, logfile, loglevel)
        if self.args.verbose:
            print("Starting loom daemon with command:\n%s" % cmd)
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
        self._stop_webserver()
        self._stop_daemon()

    def _stop_webserver(self):
        pid = self.settings_manager.get_webserver_pid()
        if pid is not None:
            subprocess.call(
                "kill %s" % pid,
                shell=True,
                )
        self._cleanup_pidfile(self.settings_manager.get_webserver_pidfile())

    def _stop_daemon(self):
        subprocess.call(
            "%s %s --pidfile %s stop" % (sys.executable, DAEMON_EXECUTABLE, self.settings_manager.get_daemon_pidfile()),
            shell=True
            )
        self._cleanup_pidfile(self.settings_manager.get_daemon_pidfile())

    def _cleanup_pidfile(self, pidfile):
        if os.path.exists(pidfile):
            try:
                os.remove(pidfile)
            except:
                warnings.warn('Failed to delete PID file %s' % pidfile)

    def _add_server_to_python_path(self, env):
        env.setdefault('PYTHONPATH', '')
        env['PYTHONPATH'] = "%s:%s" % (self.settings_manager.get_server_path(), env['PYTHONPATH'])
        return env

    def _set_database(self, env):
        manage_cmd = [sys.executable, '%s/manage.py' % self.settings_manager.get_server_path()]
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
        env.update(self.settings_manager.get_django_env_settings())
        return env

    def create(self):
        '''Create server if it doesn't exist yet.'''
        print self.args

    def delete(self):
        '''Delete server and its settings.'''
        print self.args

    def get_server_url(self):
        return 'http://127.0.0.1:8000'


class GcloudServerControls(BaseServerControls):

    def create(self):
        pass
    def delete(self):
        pass
    def start(self):
        pass
    def stop(self):
        pass
    def get_server_url(self):
        pass


if __name__=='__main__':
    ServerControls().run()
