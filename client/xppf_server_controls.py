#!/usr/bin/env python

import os
import requests
import subprocess
import sys

from xppf.client import settings_manager

class XppfServerControls:

    def __init__(self, args=None, skip_initialization=False):
        if not skip_initialization:
            self._initialize(args)

    def _initialize(self, args):
        if args is None:
            args=self._get_args()
        self._validate_args(args)
        self.settings_manager = settings_manager.SettingsManager(settings_file = args.settings)
        self._set_main_function(args)
        self.main()

    def _get_args(self):
        from argparse import ArgumentParser
        parser = ArgumentParser("xppfserver")
        # Any command can take a settings file, which will tell it which server to talk to.
        # If called with no file, it will prompt to ask if local should be set.
        # If no file is specified for start, stop, and status, default will be used.
        # If no default is set when start, stop, and status are called, it asks if you want to run local, and 
        # informs that default can be set with configure.
        parser.add_argument('command', choices=['start', 'stop', 'status', 'savesettings', 'clearsettings'])
        parser.add_argument('--settings', '-s', nargs=1, metavar='SETTINGS_FILE', help="Server settings. Use 'xppfserver savesettings -s SETTINGS_FILE' to save.")
        args = parser.parse_args()
        return args

    def _validate_args(self, args):
        if args.command == 'clearsettings' and args.settings is not None:
            raise Exception("The '--settings' flag cannot be used with the 'clearsettings' command")

    def _set_main_function(self, args):
        # Map command to function
        command_to_function_map = {
            'status': self.status,
            'start': self.start,
            'stop': self.stop,
            'savesettings': self.save_settings,
            'clearsettings': self.clear_settings,
        }
        try:
            self.main = command_to_function_map[args.command]
        except KeyError:
            raise Exception('Did not recognize command %s' % args.command)

    def start(self):
        env = self._add_server_to_python_path(os.environ.copy())
        subprocess.call(
            "gunicorn %s --bind %s:%s --pid %s --daemon" % (
                self.settings_manager.get_server_wsgi_module(), 
                self.settings_manager.get_bind_ip(), 
                self.settings_manager.get_bind_port(), 
                self.settings_manager.get_pid_file(),
                ),
            shell=True, 
            env=env)

    def status(self):
        try:
            response = requests.get(self.settings_manager.get_server_url() + '/status')
            if response.status_code == 200:
                print "server is ok"
            else:
                print "unexpected status code %s from server" % response.status_code
        except requests.exceptions.ConnectionError:
            print "no response from server"

    def stop(self):
        subprocess.call(
            "kill `cat %s`" % self.settings_manager.get_pid_file(),
            shell=True
        )

    def save_settings(self):
        self.settings_manager.save_settings_to_file()

    def clear_settings(self):
        self.settings_manager.delete_saved_settings()

    def _add_server_to_python_path(self, env):
        env.setdefault('PYTHONPATH', '')
        env['PYTHONPATH'] = "%s:%s" % (self.settings_manager.get_server_path(), env['PYTHONPATH'])
        return env


if __name__=='__main__':
    XppfServerControls()
