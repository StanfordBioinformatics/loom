#!/usr/bin/env python

import json
import jsonschema
import os
import re

XPPF_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

class SettingsManager:
    """
    This class manages xppf server settings.
    Default settings may be used, or settings can be saved to the user's home directory.
    Users should interact with this class through ../bin/xppfserver, with these subcommands:
    - savesettings
    - clearsettings
    """

    SETTINGS = None

    SAVED_SETTINGS_FILE = os.path.join(os.getenv('HOME'), '.xppf', 'settings.json')

    DEFAULT_SETTINGS = {
        'WEBSERVER_PIDFILE': '/tmp/xppf_webserver.pid',
        'BIND_IP': '127.0.0.1',
        'BIND_PORT': '8000',
        'PROTOCOL': 'http',
        'SERVER_WSGI_MODULE': 'xppfserver.wsgi',
        'SERVER_PATH': os.path.join(XPPF_ROOT, 'master'),
        'DAEMON_PIDFILE': '/tmp/xppf_daemon.pid',
        'ACCESS_LOGFILE': os.path.join(XPPF_ROOT, 'log', 'xppf_http_access.log'),
        'ERROR_LOGFILE': os.path.join(XPPF_ROOT, 'log', 'xppf_http_error.log'),
        'DJANGO_LOGFILE': os.path.join(XPPF_ROOT, 'log', 'xppf_django.log'),
        'WEBSERVER_LOGFILE': os.path.join(XPPF_ROOT, 'log', 'xppf_webserver.log'),
        'DAEMON_LOGFILE': os.path.join(XPPF_ROOT, 'log', 'xppf_daemon.log'),
        'LOG_LEVEL': 'INFO',
        'RESOURCE_MANAGER': 'LOCAL',

        # Info needed by worker
        'MASTER_URL': 'http://127.0.0.1:8000',
        'LOCAL_FILE_SERVER': 'localhost',
        'FILE_ROOT': '~/working_dir',
    }

    SETTINGS_SCHEMA = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": "object",
        "properties": {
            "BIND_IP": { "type": "string"},
            "BIND_PORT": {"type": "string", "pattern": "^[0-9]+$"},
            "WEBSERVER_PIDFILE": {"type": "string"},
            "PROTOCOL": {"enum": ["http", "https", "HTTP", "HTTPS"]},
            "SERVER_WSGI_MODULE": {"type": "string"},
            "SERVER_PATH": {"type": "string"},
            "DAEMON_PIDFILE": {"type": "string"},
            "ACCESS_LOGFILE": {"type": "string"},
            "ERROR_LOGFILE": {"type": "string"},
            "DJANGO_LOGFILE": {"type": "string"},
            "WEBSERVER_LOGFILE": {"type": "string"},
            "DAEMON_LOGFILE": {"type": "string"},
            "LOG_LEVEL": {"type": "string"},
            "RESOURCE_MANAGER": {"type": "string"},
            'MASTER_URL': {"type": "string"},
            'LOCAL_FILE_SERVER': {"type": "string"},
            'FILE_ROOT': {"type": "string"},
        },
        "additionalProperties": False,
    }

    def __init__(self, settings_file=None, require_default_settings=False, skip_init=False):
        # skip_init is for testing purposes
        if not skip_init:
            self._initialize(settings_file=settings_file, require_default_settings=require_default_settings)

    def _initialize(self, settings_file=None, require_default_settings=None):
        self._validate_input_args(settings_file=settings_file, require_default_settings=require_default_settings)

        if require_default_settings:
            dirty_settings = self._get_default_settings()
        else:
            if settings_file is None:
                settings_file = self.SAVED_SETTINGS_FILE
            try:
                with open(settings_file, 'r') as f:
                    dirty_settings = json.load(f)
            except IOError as e:
                dirty_settings = self._get_default_settings()
            except ValueError:
                raise Exception("Failed to parse the settings file because it is not in valid JSON format.")

        self.SETTINGS = self._clean_settings(dirty_settings)

    def _get_default_settings(self):
        return self.DEFAULT_SETTINGS.copy()

    def _validate_input_args(self, settings_file=None, require_default_settings=False):
        if (settings_file is not None) and require_default_settings:
            raise Exception("You cannot specify a settings file require default settings at the same time.")

    def _clean_settings(self, settings):
        jsonschema.validate(settings, self.SETTINGS_SCHEMA)
        return settings

    def get_server_url(self):
        return "%s://%s:%s" % (
            self.SETTINGS['PROTOCOL'], 
            self.SETTINGS['BIND_IP'], 
            self.SETTINGS['BIND_PORT']
        )

    def get_server_wsgi_module(self):
        return self.SETTINGS['SERVER_WSGI_MODULE']

    def get_bind_ip(self):
        return self.SETTINGS['BIND_IP']

    def get_bind_port(self):
        return self.SETTINGS['BIND_PORT']

    def get_access_logfile(self):
        return self.SETTINGS['ACCESS_LOGFILE']

    def get_error_logfile(self):
        return self.SETTINGS['ERROR_LOGFILE']

    def get_log_level(self):
        return self.SETTINGS['LOG_LEVEL']

    def get_webserver_pidfile(self):
        return self.SETTINGS['WEBSERVER_PIDFILE']

    def get_webserver_pid(self):
        return self._get_pid(self.get_webserver_pidfile())

    def get_daemon_logfile(self):
        return self.SETTINGS['DAEMON_LOGFILE']

    def get_daemon_pidfile(self):
        return self.SETTINGS['DAEMON_PIDFILE']

    def get_daemon_pid(self):
        return self._get_pid(self.get_daemon_pidfile())

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

    def get_server_path(self):
        return self.SETTINGS['SERVER_PATH']

    def save_settings_to_file(self):
        self.make_settings_directory()
        if os.path.exists(self.SAVED_SETTINGS_FILE):
            raise Exception("Settings file already exists. Run 'xppfserver clearsettings' to remove the current settings file before saving new settings.")
        try:
            with open(self.SAVED_SETTINGS_FILE, 'w') as f:
                json.dump(self.SETTINGS, f, sort_keys=True, indent=2, separators=(',', ': '))
        except Exception as e:
            print "Failed to save settings to %s. (%s)." % (self.SAVED_SETTINGS_FILE, e)

    def make_settings_directory(self):
        if os.path.exists(os.path.dirname(self.SAVED_SETTINGS_FILE)):
            return
        else:
            try:
                os.makedirs(os.path.dirname(self.SAVED_SETTINGS_FILE))
            except Exception as e:
                raise Exception("Failed to create directory for the settings file at %s. (%s)" % (os.path.dirname(self.SAVED_SETTINGS_FILE), e))

    def delete_saved_settings(self):
        try:
            os.remove(self.SAVED_SETTINGS_FILE)
            self.remove_dir_if_empty(os.path.dirname(self.SAVED_SETTINGS_FILE))
        except OSError as e:
            raise Exception("No settings file to delete at %s. (%s)" % (self.SAVED_SETTINGS_FILE, e))

    def remove_dir_if_empty(self, dirpath):
        if os.listdir(dirpath) == []:
            os.rmdir(dirpath)

    def get_django_env_settings(self):
        """
        These are settings that will be passed out as environment variables before launching 
        the webserver. This allows master/xppfserver/settings.py to use these settings.
        """
        export_settings = {}
        setting_keys_to_export = [
            'DJANGO_LOGFILE',
            'WEBSERVER_LOGFILE',
            'LOG_LEVEL',
            'RESOURCE_MANAGER',
            'MASTER_URL',
            'LOCAL_FILE_SERVER',
            'FILE_ROOT',
            ]
        for key in setting_keys_to_export:
            value = self.SETTINGS.get(key)
            if value is not None:
                export_settings[key] = value
        return export_settings
