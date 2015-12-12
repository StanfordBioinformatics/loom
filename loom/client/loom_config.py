#!/usr/bin/env python

import os
import requests
import subprocess
import sys

from loom.client import settings_manager

class LoomConfig:
    """
    This class provides methods for configuring the loom installation, specifically the subcommands:
    - local
    - local_gcloud
    - elasticluster
    - elasticluster_frontend (primarily used by elasticluster setup)
    - savesettings
    - clearsettings

    Users should call this through ../bin/loomconfig.
    On first run, settings are saved to the user's home directory in .loom/settings.json.
    By default, this will configure loom for local deployment.
    To switch to elasticluster deployment, run 'loomconfig elasticluster'.
    To switch back to local deployment, run 'loomconfig local'.
    For finer-grained control, .loom/settings.json can be directly edited to set specific values.
    """

    def __init__(self, args=None):
        if args is None:
            args=self._get_args()
        self.args = args
        self._validate_args(args)
        self._set_main_function(args)
        self._set_default_settings(args)
        self.settings_manager = settings_manager.SettingsManager(settings_file=args.settings, require_default_settings=args.require_default_settings, verbose=args.verbose)

    @classmethod
    def _get_parser(cls):
        import argparse
        parser = argparse.ArgumentParser("loomconfig")
        parser.add_argument('command', choices=['local', 'local_gcloud', 'elasticluster', 'elasticluster_frontend', 'savesettings', 'clearsettings'])
        parser.add_argument('--settings', '-s', metavar='SETTINGS_FILE', 
                            help="Settings indicate how to launch the server components, and how the client and worker components can reach them. Use 'loomconfig savesettings -s SETTINGS_FILE' to save.")
        parser.add_argument('--require_default_settings', '-d', action='store_true', help=argparse.SUPPRESS)
        parser.add_argument('--verbose', '-v', action='store_true', help='Provide feedback to the console about changes to settings files.')
        return parser

    def _get_args(self):
        parser = self._get_parser()
        args = parser.parse_args()
        return args

    def _validate_args(self, args):
        if args.command == 'clearsettings' and args.settings is not None:
            raise ArgumentError("The '--settings' flag cannot be used with the 'clearsettings' command")

    def _set_main_function(self, args):
        # Map user input command to class method
        command_to_method_map = {
            'local': self.set_local,
            'local_gcloud': self.set_local_gcloud,
            'elasticluster': self.set_elasticluster,
            'elasticluster_frontend': self.set_elasticluster_frontend,
            'savesettings': self.save_settings,
            'clearsettings': self.clear_settings
        }
        try:
            self.main = command_to_method_map[args.command]
        except KeyError:
            raise ArgumentError('Did not recognize command %s' % args.command)

    def _set_default_settings(self, args):
        if args.require_default_settings == False:
            # If one of the presets is chosen, use default settings (don't bother loading settings.json)
            if args.command in ('local', 'elasticluster', 'elasticluster_frontend', 'clearsettings'):
                args.require_default_settings = True
            else:
                args.require_default_settings = False

    def set_local(self):
        self.settings_manager.set_local()

        # Passing values to Django using environment variables only works if webserver is local to client
        os.environ.update(self.settings_manager.get_django_env_settings()) 

    def set_local_gcloud(self):
        self.settings_manager.set_local_gcloud()

        # Passing values to Django using environment variables only works if webserver is local to client
        os.environ.update(self.settings_manager.get_django_env_settings()) 

    def set_elasticluster_frontend(self):
        self.settings_manager.set_elasticluster_frontend()

        # Passing values to Django using environment variables only works if webserver is local to client
        os.environ.update(self.settings_manager.get_django_env_settings()) 

    def set_elasticluster(self):
        self.settings_manager.set_elasticluster()

    def save_settings(self):
        self.settings_manager.save_settings_to_file()

    def clear_settings(self):
        self.settings_manager.delete_saved_settings()

    class ArgumentError(Exception):
        """Exception for unrecognized or invalid combinations of arguments in this module."""
        pass

if __name__=='__main__':
    LoomConfig().main()
