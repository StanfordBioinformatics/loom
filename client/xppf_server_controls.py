#!/usr/bin/env python

import os
import requests
import subprocess
import sys

from xppf.client import settings_manager

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
        parser.add_argument('--settings', '-s', nargs=1, metavar='SETTINGS_FILE', 
                            help="Settings indicate what server to talk to and how to launch it. Use 'xppfserver savesettings -s SETTINGS_FILE' to save.")
        parser.add_argument('--require_default_settings', '-d', action='store_true', help=argparse.SUPPRESS)
        parser.add_argument('--test_database', '-t', action='store_true', help=argparse.SUPPRESS)
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
        self._verify_server_not_running()
        env = self._add_server_to_python_path(os.environ.copy())
        env = self._set_database(env)
        subprocess.call(
            "gunicorn %s --bind %s:%s --pid %s --daemon" % (
                self.settings_manager.get_server_wsgi_module(), 
                self.settings_manager.get_bind_ip(), 
                self.settings_manager.get_bind_port(), 
                self.settings_manager.get_pid_file(),
                ),
            shell=True, 
            env=env)

    def _verify_server_not_running(self):
        pidfile = self.settings_manager.get_pid_file()
        if os.path.exists(pidfile):
            try:
                with open(pidfile) as f:
                    pid = f.read().strip()
            except:
                pid = 'unknown'
            raise Exception('Server may already be running on pid "%s", as indicated in %s' % (pid, pidfile))


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
        subprocess.call(
            "kill %s" % self.settings_manager.get_pid(),
            shell=True
            )
        if os.path.exists(self.settings_manager.get_pid_file()):
            try:
                os.remove(self.settings_manager.get_pid_file())
            except:
                raise Exception('Failed to delete PID file %s' % self.settings_manager.get_pid_file())

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

if __name__=='__main__':
    XppfServerControls().main()
