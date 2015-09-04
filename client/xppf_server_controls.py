#!/usr/bin/env python

import os
import requests
import subprocess
import sys

from xppf.client import settings_manager

DAEMON_EXECUTABLE = os.path.abspath(
    os.path.join(
    os.path.dirname(__file__),
    '../master/xppfdaemon/xppf_daemon.py'
    ))

class XppfServerControls:
    """
    This class provides methods for managing the xppf server, specifically the commands:
    - start
    - stop
    - status
    - savesettings
    - clearsettings

    Users should call this through ../bin/xppfserver to ensure the environment is configured.
    """

    def __init__(self, args=None):
        if args is None:
            args=self._get_args()
        self.args = args
        self._validate_args(args)
        self.settings_manager = settings_manager.SettingsManager(settings_file=args.settings, require_default_settings=args.require_default_settings)
        self._set_main_function(args)

    @classmethod
    def _get_parser(cls):
        import argparse
        parser = argparse.ArgumentParser("xppfserver")
        parser.add_argument('command', choices=['start', 'stop', 'status', 'savesettings', 'clearsettings'])
        parser.add_argument('--settings', '-s', metavar='SETTINGS_FILE', 
                            help="Settings indicate what server to talk to and how to launch it. Use 'xppfserver savesettings -s SETTINGS_FILE' to save.")
        parser.add_argument('--require_default_settings', '-d', action='store_true', help=argparse.SUPPRESS)
        parser.add_argument('--test_database', '-t', action='store_true', help=argparse.SUPPRESS)
        parser.add_argument('--no_daemon', '-n', action='store_true', help=argparse.SUPPRESS)
        parser.add_argument('--fg_webserver', action='store_true', help='Run webserver in the foreground. Needed to keep Docker container running.')
        return parser

    def _get_args(self):
        parser = self._get_parser()
        args = parser.parse_args()
        return args

    def _validate_args(self, args):
        if args.command == 'clearsettings' and args.settings is not None:
            raise Exception("The '--settings' flag cannot be used with the 'clearsettings' command")

    def _set_main_function(self, args):
        # Map user input command to class method
        command_to_method_map = {
            'status': self.status,
            'start': self.start,
            'stop': self.stop,
            'savesettings': self.save_settings,
            'clearsettings': self.clear_settings,
        }
        try:
            self.main = command_to_method_map[args.command]
        except KeyError:
            raise Exception('Did not recognize command %s' % args.command)

    def start(self):
        env = os.environ.copy()
        env = self._add_server_to_python_path(env)
        env = self._set_database(env)
        env = self._export_django_settings(env)
        self._start_daemon(env)
        self._start_webserver(env)

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
        process = subprocess.Popen(
            cmd,
            shell=True,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        process.wait()
        (stdout, stderr) = process.communicate()
        if not process.returncode == 0:
            raise Exception('XPPF Webserver failed to start, with return code "%s". \nFailed command is "%s". \n%s \n%s' % (process.returncode, cmd, stdout, stderr))

    def _start_daemon(self, env):
        if self.args.no_daemon == True:
            return
        pidfile = self.settings_manager.get_daemon_pidfile()
        logfile = self.settings_manager.get_daemon_logfile()
        loglevel = self.settings_manager.get_log_level()
        cmd = "%s start --pidfile %s --logfile %s --loglevel %s" % (DAEMON_EXECUTABLE, pidfile, logfile, loglevel)
        process = subprocess.Popen(
            cmd,
            shell=True,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        process.wait()
        (stdout, stderr) = process.communicate()
        if not process.returncode == 0:
            raise Exception('XPPF Daemon failed to start, with return code "%s". \nFailed command is "%s". \n%s \n%s' % (process.returncode, cmd, stderr, stdout))

    def status(self):
        try:
            response = requests.get(self.settings_manager.get_server_url() + '/api/status')
            if response.status_code == 200:
                print "server is ok"
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
            "%s --pidfile %s stop" % (DAEMON_EXECUTABLE, self.settings_manager.get_daemon_pidfile()),
            shell=True
            )
        self._cleanup_pidfile(self.settings_manager.get_daemon_pidfile())

    def _cleanup_pidfile(self, pidfile):
        if os.path.exists(pidfile):
            try:
                os.remove(pidfile)
            except:
                warnings.warn('Failed to delete PID file %s' % pidfile)

    def save_settings(self):
        self.settings_manager.save_settings_to_file()

    def clear_settings(self):
        self.settings_manager.delete_saved_settings()

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
    XppfServerControls().main()
