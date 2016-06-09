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
    DEFAULT_SETTINGS_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), 'default_settings.ini'))

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
        self.settings = {}
        self.verbose = verbose
        self.require_default_settings = require_default_settings

    def create_deploy_settings(self, server_type=None, user_settings_file=None):
        if server_type == None:
            server_type = get_server_type()
        self.load_settings_from_file(SettingsManager.DEFAULT_SETTINGS_FILE, section=server_type)

        # Override defaults with user-provided settings file
        if not self.require_default_settings:
            if user_settings_file:
                self.load_settings_from_file(user_settings_file, section=server_type)

        #TODO: extract settings from commandline arguments and override self.settings with them
        #TODO: verify required settings are defined and raise error if not

    def create_deploy_settings_file(self, user_settings_file=None):
        self.create_deploy_settings(user_settings_file=user_settings_file)
        self.save_settings_to_file(get_deploy_settings_filename(), section=get_server_type())

    def load_deploy_settings_file(self):
        try:
            self.load_settings_from_file(get_deploy_settings_filename(), section=get_server_type())
        except:
            raise SettingsError("Could not open server deploy settings. You might need to run \"loom server create\" first.")

    def delete_deploy_settings_file(self):
        os.remove(get_deploy_settings_filename())

    def load_settings_from_file(self, settings_file, section):
        """Update current settings dict by reading from a file and section."""
        try:
            config = SafeConfigParser()
            config.optionxform = str                    # preserve uppercase in settings names
            config.read(settings_file)
        except Exception as e: 
            raise SettingsError("Failed to open settings file %s: %s" % (settings_file, e))

        items = dict(config.items(section))
        for item in items:
            if '~' in items[item]:
                items[item] = os.path.expanduser(items[item])
        self.settings.update(items)
        if self.verbose:
            print "Loaded settings from %s." % settings_file

    def save_settings_to_file(self, settings_file, section):
        if not self.settings:
            raise SettingsError("No settings loaded yet.")
        self.make_settings_directory(settings_file)
        config = SafeConfigParser()
        config.optionxform = str                    # preserve uppercase in settings names
        config.add_section(section)
        for key in self.settings:
            config.set(section, key, self.settings[key])
        with open(settings_file, 'w') as fp:
            config.write(fp)

    def make_settings_directory(self, settings_file):
        if os.path.exists(os.path.dirname(settings_file)):
            return
        else:
            try:
                os.makedirs(os.path.dirname(settings_file))
                if self.verbose:
                    print "Created directory %s." % os.path.dirname(settings_file)
            except Exception as e:
                raise SettingsError("Failed to create directory for the settings file %s (%s)" % (os.path.dirname(settings_file), e))

    def delete_saved_settings(self):
        try:
            if self.settings_file is None:
                self.settings_file = SettingsManager.DEFAULT_SETTINGS_FILE
            os.remove(self.settings_file)
            if self.verbose:
                print "Removed settings file %s." % settings_file
            self.remove_dir_if_empty(os.path.dirname(self.settings_file))
        except OSError as e:
            raise SettingsError("No settings file to delete at %s. (%s)" % (self.settings_file, e))

    def remove_dir_if_empty(self, dirpath):
        if os.listdir(dirpath) == []:
            os.rmdir(dirpath)
            if self.verbose:
                print "Removed empty directory %s." % dirpath

    def get_env_settings(self):
        """Return a dict of settings as environment variable-friendly strings."""
        export_settings = {}
        for key in self.settings:
            value = self.settings[key]
            if value is not None:
                if isinstance(value, list): # Expand lists into comma-separated strings, since environment variables must be strings
                    value = ','.join(value)
                elif isinstance(value, str) and '~' in value: # Expand user home directory to absolute path
                    value = os.path.expanduser(value)
                export_settings[key] = value
        return export_settings


class SettingsError(Exception):
    pass
