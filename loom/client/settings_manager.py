#!/usr/bin/env python

import os
import re

from ConfigParser import SafeConfigParser
from loom.client.common import *


class SettingsManager:
    """This class loads settings for the Loom client.
    It should only be called when creating or starting a Loom server. 
    In all other cases, the server should be queried for settings.

    Settings are loaded in the following order, with later ones taking precedence:
    1. the [DEFAULT] section from default_settings.ini
    2. the section from default_settings.ini corresponding to the server type (passed as argument to constructor)
    3. user-provided settings file, if any
    4. user-provided command line arguments, if any

    At this point, required settings must be defined. Otherwise, throw an error.
    """
    DEFAULT_SETTINGS_FILE = 'default_settings.ini'
    DEPLOY_SETTINGS_FILE = os.path.join(os.path.expanduser('~'), '.loom', 'deploy_settings.ini')

    def __init__(self, **kwargs):
        if not self._do_skip_init(**kwargs):
            self._initialize(**kwargs)

    def _do_skip_init(self, **kwargs):
        try:
            skip_init = kwargs.pop('skip_init')
        except KeyError:
            skip_init = False
        return skip_init

    def _initialize(self, require_default_settings=False, verbose=False,  **kwargs):
        self.settings = None
        self.verbose = verbose
        self.require_default_settings = require_default_settings

    def create_deploy_settings(self, section=None, user_settings_file=None):
        if section == None:
            section = get_server_type()
        self.load_settings_from_file(SettingsManager.DEFAULT_SETTINGS_FILE, section)

        # Override defaults with user-provided settings file
        if not self.require_default_settings:
            if user_settings_file:
                self.load_settings_from_file(user_settings_file, section)

        #TODO: extract settings from commandline arguments and override self.settings with them
        #TODO: verify required settings are defined and raise error if not

    def create_deploy_settings_file(self, user_settings_file=None):
        self.create_deploy_settings(user_settings_file=user_settings_file)
        self.save_settings_to_file(SettingsManager.DEPLOY_SETTINGS_FILE, section='deploy')

    def load_deploy_settings_file(self):
        self.load_settings_from_file(SettingsManager.DEPLOY_SETTINGS_FILE, section='deploy')

    def delete_deploy_settings_file(self):
        os.remove(SettingsManager.DEPLOY_SETTINGS_FILE)

    def load_settings_from_file(self, settings_file, section):
        try:
            config = SafeConfigParser(defaults=self.settings)
            config.optionxform = str                    # preserve uppercase in settings names
            config.read(settings_file)
            self.settings = dict(config.items(section))
            if self.verbose:
                print "Loaded settings from %s." % settings_file
        except: 
            raise Exception("Failed to open settings file %s." % settings_file)

    def save_settings_to_file(self, settings_file, section):
        if not self.settings:
            raise Exception("No settings loaded yet.")
        config = SafeConfigParser()
        config.optionxform = str                    # preserve uppercase in settings names
        config.add_section(section)
        for key in self.settings:
            config.set(section, key, self.settings[key])
        with open(settings_file, 'w') as fp:
            config.write(fp)

    def make_settings_directory(self):
        if os.path.exists(os.path.dirname(self.settings_file)):
            return
        else:
            try:
                os.makedirs(os.path.dirname(self.settings_file))
                if self.verbose:
                    print "Created directory %s." % os.path.dirname(self.settings_file)
            except Exception as e:
                raise Exception("Failed to create directory for the settings file %s (%s)" % (os.path.dirname(self.settings_file), e))

    def delete_saved_settings(self):
        try:
            if self.settings_file is None:
                self.settings_file = SettingsManager.DEFAULT_SETTINGS_FILE
            os.remove(self.settings_file)
            if self.verbose:
                print "Removed settings file %s." % settings_file
            self.remove_dir_if_empty(os.path.dirname(self.settings_file))
        except OSError as e:
            raise Exception("No settings file to delete at %s. (%s)" % (self.settings_file, e))

    def remove_dir_if_empty(self, dirpath):
        if os.listdir(dirpath) == []:
            os.rmdir(dirpath)
            if self.verbose:
                print "Removed empty directory %s." % dirpath

    def get_django_env_settings(self):
        """
        These are settings that will be passed out as environment variables before launching 
        the webserver. This allows master/loomserver/settings.py to use these settings.
        Passing settings this way only works if the webserver is on the same machine as the
        client launching it.

        TODO: decide how to pass settings to Django server when client is on a different machine
        """
        export_settings = {}
        setting_keys_to_export = [
            'DJANGO_LOGFILE',
            'WEBSERVER_LOGFILE',
            'LOG_LEVEL',
            'WORKER_TYPE',
            'MASTER_URL_FOR_WORKER',
            'FILE_SERVER_FOR_WORKER',
            'FILE_ROOT_FOR_WORKER',
            'MASTER_URL_FOR_CLIENT',
            'FILE_SERVER_FOR_CLIENT',
            'FILE_SERVER_TYPE',
            'FILE_ROOT',
            'IMPORT_DIR',
            'STEP_RUNS_DIR',
            'BUCKET_ID',
            'PROJECT_ID',
            'ANSIBLE_PEM_FILE',
            'GCE_KEY_FILE',
            'WORKER_VM_IMAGE',
            'WORKER_LOCATION',
            'WORKER_DISK_TYPE',
            'WORKER_DISK_SIZE',
            'WORKER_DISK_MOUNT_POINT',
            'WORKER_NETWORK',
            'WORKER_TAGS',
            ]
        for key in setting_keys_to_export:
            value = self.settings.get(key)
            if value is not None:
                if isinstance(value, list): # Expand arrays into comma-separated strings, since environment variables must be strings
                    value = ','.join(value)
                export_settings[key] = value
        return export_settings
