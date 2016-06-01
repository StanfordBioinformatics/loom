#!/usr/bin/env python

import os
import re

from ConfigParser import SafeConfigParser

import loom.client.common

DEFAULT_SETTINGS_FILE = 'default_settings.ini'

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

    def __init__(self, **kwargs):
        if not self._do_skip_init(**kwargs):
            self._initialize(**kwargs)

    def _do_skip_init(self, **kwargs):
        try:
            skip_init = kwargs.pop('skip_init')
        except KeyError:
            skip_init = False
        return skip_init

    def _initialize(self, settings_file=DEFAULT_SETTINGS_FILE, require_default_settings=False, verbose=False,  **kwargs):
        self.verbose = verbose
        server_type = loom.client.common.get_server_type()

        default_config = SafeConfigParser()
        default_config.optionxform = str                # preserve uppercase in settings names
        default_config.read(DEFAULT_SETTINGS_FILE)
        self.settings = dict(default_config.items(server_type))

        if not require_default_settings:
            if self.settings is not None:
                self.load_settings_from_file(settings_file, server_type)

        #TODO: extract settings from commandline arguments and override self.settings with them

    def load_settings_from_file(self, settings_file, server_type):
        try:
            config = SafeConfigParser(defaults=self.settings)
            config.optionxform = str                    # preserve uppercase in settings names
            config.read(settings_file)
            self.settings = dict(config.items(server_type))
            if self.verbose:
                print "Loaded settings from %s." % settings_file
        except: 
            raise Exception("Failed to open settings file %s." % settings_file)

    #TODO: move this to common.py
    def _update_elasticluster_frontend_ip(self):
        """Update settings with the elasticluster frontend IP, and also write to presets."""
        frontend_ip = self._get_elasticluster_frontend_ip()
        self.settings['FILE_SERVER_FOR_CLIENT'] = frontend_ip
        self.settings['MASTER_URL_FOR_CLIENT'] = "http://%s:8000" % frontend_ip
        
        current_preset_key = self.presets['CURRENT_PRESET']
        self.presets[current_preset_key] = self.settings

    @staticmethod
    def _get_elasticluster_frontend_ip():
        """Gets external IP of frontend node from Ansible inventory file.

        Preconditions:
        - Inventory file is in default location ($HOME/.elasticluster/storage)
        - User only has one cluster running through elasticluster (TODO: support multiple clusters by taking cluster name as input)
        - LOOM webserver and fileserver are on frontend001
        """
        inventory_search_path = os.path.join(os.getenv('HOME'), '.elasticluster', 'storage', 'ansible-inventory.*')
        import glob
        inventory_files = glob.glob(inventory_search_path)

        if len(inventory_files) > 1:
            raise Exception("More than one running cluster found, don't know which to target!")
        if len(inventory_files) < 1:
            raise Exception("Ansible inventory file not found in default location %s" % inventory_search_path)
        
        inventory_file = inventory_files[0]
        
        with open(inventory_file) as f:
            for line in f:
                match = re.match(r"frontend001 ansible_ssh_host=([\d.]+)", line) # matches IP address of frontend node
                if match:
                    ip = match.group(1) 
                    return ip
            raise Exception("No entry for frontend001 found in Ansible inventory file %s" % inventory_file)

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
