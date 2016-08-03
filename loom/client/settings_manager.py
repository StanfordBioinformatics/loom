#!/usr/bin/env python

import json
import os
import re
import uuid

from ConfigParser import SafeConfigParser
from loom.client.common import *
from loom.common.version import version


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

    def __init__(self, require_default_settings=False, verbose=False):
        self.settings = {}
        self.verbose = verbose
        self.require_default_settings = require_default_settings

    def create_deploy_settings(self, server_type=None, user_settings_file=None):
        """ Create deploy settings by loading defaults and overriding with user-provided settings."""
        if server_type == None:
            server_type = get_server_type()
        self.load_settings_from_file(SettingsManager.DEFAULT_SETTINGS_FILE, section=server_type)

        if not self.require_default_settings:
            # Add Google Cloud-specific settings
            if server_type == 'gcloud': 
                self.load_gcloud_settings()
            # Override defaults with user-provided settings file
            if user_settings_file:
                self.load_settings_from_file(user_settings_file, section=server_type)

        self.postprocess_settings()

    def load_gcloud_settings(self):
        """ Load Google Cloud-specific settings."""
        # Add server name from server.ini
        self.settings['SERVER_NAME'] = get_gcloud_server_name()
        self.settings['MASTER_URL_FOR_WORKER'] = '%s://%s:%s' % (self.settings['PROTOCOL'], self.settings['SERVER_NAME'], self.settings['EXTERNAL_PORT'])

        # Add other settings from gce.ini
        gce_config = SafeConfigParser(allow_no_value=True)
        gce_config.read(os.path.expanduser(GCE_INI_PATH))
        self.settings['GCE_INI_PATH'] = GCE_INI_PATH
        self.settings['GCE_EMAIL'] = gce_config.get('gce', 'gce_service_account_email_address')
        self.settings['GCE_PROJECT'] = gce_config.get('gce', 'gce_project_id')
        self.settings['GCE_PEM_FILE_PATH'] = gce_config.get('gce', 'gce_service_account_pem_file_path')
        self.settings['CLIENT_VERSION'] = version()

        # If bucket not provided, default to project id with '-loom' appended
        if self.settings['GCE_BUCKET'] == 'None':
            self.settings['GCE_BUCKET'] = self.settings['GCE_PROJECT'] + '-loom'

    def postprocess_settings(self):
        if get_server_type() == 'gcloud':
            self.settings['DOCKER_FULL_NAME'] = '%s/%s:%s' % (self.settings['DOCKER_REPO'], self.settings['DOCKER_IMAGE'], self.settings['DOCKER_TAG'])
            if self.settings['DOCKER_REGISTRY']:
                self.settings['DOCKER_FULL_NAME'] = '/'.join([self.settings['DOCKER_REGISTRY'], self.settings['DOCKER_FULL_NAME']])

    def create_deploy_settings_file(self, user_settings_file=None):
        self.create_deploy_settings(user_settings_file=user_settings_file)
        self.save_settings_to_file(get_deploy_settings_filename(), section='deploy')

    def load_deploy_settings_file(self):
        try:
            self.load_settings_from_file(get_deploy_settings_filename(), section='deploy')
        except:
            raise SettingsError("Could not open server deploy settings at %s. You might need to run \"loom server create\" first." % get_deploy_settings_filename())

    def delete_deploy_settings_file(self):
        os.remove(get_deploy_settings_filename())

    def load_settings_from_file(self, settings_file, section):
        """Update current settings dict by reading from a file and section."""
        try:
            config = SafeConfigParser(allow_no_value=True)
            config.optionxform = lambda option: option.upper() # preserve uppercase in settings names
            config.read(settings_file)
        except Exception as e: 
            raise SettingsError("Failed to open settings file %s: %s" % (settings_file, e))

        items = dict(config.items(section))
        self.settings.update(items)
        if self.verbose:
            print "Loaded settings from %s." % settings_file

    def save_settings_to_file(self, settings_file, section):
        if not self.settings:
            raise SettingsError("No settings loaded yet.")
        self.make_settings_directory(settings_file)
        config = SafeConfigParser(allow_no_value=True)
        config.optionxform = lambda option: option.upper() # preserve uppercase in settings names
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

    def get_env_settings(self):
        """Return a dict of settings as environment variable-friendly strings."""
        export_settings = {}
        for key in self.settings:
            value = self.settings[key]
            if value is not None:
                if isinstance(value, str) and '~' in value: # Expand user home directory to absolute path
                    value = os.path.expanduser(value)
                export_settings[key] = value
        return export_settings

    def get_default_setting(self, section, option):
        self.load_settings_from_file(SettingsManager.DEFAULT_SETTINGS_FILE, section)
        return self.settings[option]


class SettingsError(Exception):
    pass
