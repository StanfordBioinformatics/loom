import argparse
import imp
import json
import os
import requests
import subprocess
import sys
import yaml

from ConfigParser import SafeConfigParser

import loom.client.settings_manager
from loom.client.exceptions import *

SERVER_LOCATION_FILE = os.path.join(os.path.expanduser('~'), '.loom', 'server.ini')
DEPLOY_SETTINGS_LOCATION = os.path.join(os.path.expanduser('~'), '.loom')
GCE_INI_PATH = os.path.join(os.path.expanduser('~'), '.loom', 'gce.ini')
GCE_PY_PATH = os.path.join(imp.find_module('loom')[1], 'common', 'gce.py')
SERVER_PATH = os.path.join(imp.find_module('loom')[1], 'master')
SERVER_DEFAULT_NAME = 'loom-master'

def get_server_type():
    """Checks server.ini for server type."""
    if not os.path.exists(SERVER_LOCATION_FILE):
        raise Exception("%s not found. Please run 'loom server set <servertype>' first." % SERVER_LOCATION_FILE)
    config = SafeConfigParser()
    config.read(SERVER_LOCATION_FILE)
    server_type = config.get('server', 'type')
    return server_type

def get_gcloud_server_name():
    """Reads and returns gcloud server instance name from server.ini."""
    if not os.path.exists(SERVER_LOCATION_FILE):
        raise Exception("%s not found. Please run 'loom server set <servertype>' first." % SERVER_LOCATION_FILE)
    config = SafeConfigParser()
    config.read(SERVER_LOCATION_FILE)
    server_type = config.get('server', 'type')
    if server_type != 'gcloud':
        raise Exception("Tried to get gcloud instance name, but %s is not configured for gcloud." % SERVER_LOCATION_FILE)
    server_name = config.get('server', 'name')
    return server_name

def get_server_ip():
    server_type = get_server_type()
    if server_type == 'local':
        return '127.0.0.1'
    elif server_type == 'gcloud':
        server_instance_name = get_gcloud_server_name()
        return get_gcloud_server_ip(server_instance_name)
    else:
        raise Exception("Unknown server type: %s" % server_type)

def get_gcloud_server_ip(name):
    if not os.path.exists(GCE_INI_PATH):
        raise Exception("%s not found. Please configure https://github.com/ansible/ansible/blob/devel/contrib/inventory/gce.ini and place it at this location." % GCE_INI_PATH)
    os.environ['GCE_INI_PATH'] = GCE_INI_PATH 
    inv = subprocess.check_output([sys.executable, GCE_PY_PATH])
    inv = json.loads(inv)
    inv_hosts = inv['_meta']['hostvars']
    if name not in inv_hosts:
        raise Exception("%s not found in Ansible dynamic inventory. Current hosts: %s" % (name, inv_hosts.keys()))
    ip = inv_hosts[name]['gce_public_ip'].encode('utf-8')
    return ip

def get_server_url():
    # TODO: add protocol and bind_port to server.ini since they are required to construct a URL to reach the server
    # Think about how to keep in sync with user-provided settings, default_settings.ini, and _deploy_settings.ini
    # Would remove dependency on SettingsManger from other components
    settings_manager = loom.client.settings_manager.SettingsManager()
    try:
        settings_manager.load_deploy_settings_file()
    except:
        raise Exception("Could not open server deploy settings. Do you need to run \"loom server create\" first?")
    settings = settings_manager.settings
    protocol = settings['PROTOCOL']
    ip = get_server_ip()
    port = settings['BIND_PORT']
    return '%s://%s:%s' % (protocol, ip, port)

def get_deploy_settings_filename():
    return os.path.join(DEPLOY_SETTINGS_LOCATION, get_server_type() + '_deploy_settings.ini')

def is_server_running():
    try:
        response = requests.get(get_server_url() + '/api/status/')
        if response.status_code == 200:
            return True
        else:
            raise Exception("unexpected status code %s from server" % response.status_code)
    except requests.exceptions.ConnectionError:
        return False

def read_as_json_or_yaml(file):
    
    def _read_as_json(file):
        try:
            with open(file) as f:
                return json.load(f)
        except:
            return None
    
    # Try as YAML. If that fails due to bad format, try as JSON
    try:
        with open(file) as f:
            data = yaml.load(f)
    except IOError:
        raise NoFileError('Could not find or could not read file %s' % file)
    except yaml.parser.ParserError:
        data = _read_as_json(file)
        if data is None:
            raise InvalidFormatError('Input file "%s" is not valid YAML or JSON format' % file)
    except yaml.scanner.ScannerError as e:
        data = _read_as_json(file)
        if data is None:
            raise InvalidFormatError(e.message)
    return data
