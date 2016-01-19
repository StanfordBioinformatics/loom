#!/usr/bin/env python

import argparse
import os
import requests
import subprocess
import sys

from loom.client import settings_manager

DAEMON_EXECUTABLE = os.path.abspath(
    os.path.join(
    os.path.dirname(__file__),
    '../master/loomdaemon/loom_daemon.py'
    ))

class ServerControls:
    """
    This class provides methods for managing the loom server, specifically the commands:
    - start
    - stop
    - status

    Users should call this through ../bin/loomserver to ensure the environment is configured.
    """

    def __init__(self, args=None):
        if args is None:
            args=self._get_args()
        self.args = args
        self.settings_manager = settings_manager.SettingsManager(settings_file=args.settings, require_default_settings=args.require_default_settings)
        self._set_run_function(args)

    @classmethod
    def get_parser(cls, parser=None):
        if parser == None:
            parser = argparse.ArgumentParser(__file__)
        parser.add_argument('command', choices=['start', 'stop', 'status'])
        parser.add_argument('--settings', '-s', metavar='SETTINGS_FILE',
                            help="Settings files indicate which server to talk to and how the server can be reached. Defaults to ~/.loom/settings.json (created on first run if not found). Use loom config to choose from available presets, or edit the file directly.")
        parser.add_argument('--test_database', '-t', action='store_true', help=argparse.SUPPRESS)
        parser.add_argument('--no_daemon', '-n', action='store_true', help=argparse.SUPPRESS)
        parser.add_argument('--fg_webserver', action='store_true', help='Run webserver in the foreground. Needed to keep Docker container running.')
        parser.add_argument('--require_default_settings', '-d', action='store_true', help=argparse.SUPPRESS)
        parser.add_argument('--verbose', '-v', action='store_true', help='Provide more feedback to console.')
        return parser

    def _get_args(self):
        parser = self.get_parser()
        args = parser.parse_args()
        return args

    def _set_run_function(self, args):
        # Map user input command to class method
        command_to_method_map = {
            'status': self.status,
            'start': self.start,
            'stop': self.stop
        }
        try:
            self.run = command_to_method_map[args.command]
        except KeyError:
            raise Exception('Did not recognize command %s' % args.command)

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

    def status(self):
        try:
            response = requests.get(self.settings_manager.get_server_url_for_client() + '/api/status')
            if response.status_code == 200:
                print "server is up"
            else:
                print "unexpected status code %s from server" % response.status_code
            return response
        except requests.exceptions.ConnectionError:
            print "no response from server"

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
        # If test database requested, set RACK_ENV to test and reset database
        if self.args.test_database:
            env['RACK_ENV'] = 'test'
            manage_cmd = '%s/manage.py' % self.settings_manager.get_server_path()
            commands = [
                '%s flush --noinput' % manage_cmd,
                '%s migrate' % manage_cmd,
                ]
            for command in commands:
                stdout = subprocess.Popen(
                    command,
                    shell=True, 
                    stdout=subprocess.PIPE,
                    env=env).communicate()
        return env

    def _export_django_settings(self, env):
        env.update(self.settings_manager.get_django_env_settings())
        return env

if __name__=='__main__':
    ServerControls().run()
