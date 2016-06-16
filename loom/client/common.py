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

LOOM_HOME_SUBDIR = '.loom'
LOOM_SETTINGS_PATH = os.path.join('~', LOOM_HOME_SUBDIR)
SERVER_LOCATION_FILE = os.path.join(LOOM_SETTINGS_PATH, 'server.ini')
GCE_INI_PATH = os.path.join(LOOM_SETTINGS_PATH, 'gce.ini')
GCE_PY_PATH = os.path.join(imp.find_module('loom')[1], 'common', 'gce.py')
SERVER_PATH = os.path.join(imp.find_module('loom')[1], 'master')

def get_server_type():
    """Checks server.ini for server type."""
    server_location_file = os.path.expanduser(SERVER_LOCATION_FILE)
    if not os.path.exists(server_location_file):
        raise Exception("%s not found. Please run 'loom server set <servertype>' first." % server_location_file)
    config = SafeConfigParser()
    config.read(server_location_file)
    server_type = config.get('server', 'type')
    return server_type

def get_gcloud_server_name():
    """Reads and returns gcloud server instance name from server.ini."""
    server_location_file = os.path.expanduser(SERVER_LOCATION_FILE)
    if not os.path.exists(server_location_file):
        raise Exception("%s not found. Please run 'loom server set <servertype>' first." % server_location_file)
    config = SafeConfigParser()
    config.read(server_location_file)
    server_type = config.get('server', 'type')
    if server_type != 'gcloud':
        raise Exception("Tried to get gcloud instance name, but %s is not configured for gcloud." % server_location_file)
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
    inv_hosts = get_gcloud_hosts()
    if name not in inv_hosts:
        raise Exception("%s not found in Ansible dynamic inventory. Current hosts: %s" % (name, inv_hosts.keys()))
    ip = inv_hosts[name]['gce_public_ip'].encode('utf-8')
    return ip

def get_inventory():
    gce_ini_path = os.path.expanduser(GCE_INI_PATH)
    gce_py_path = os.path.expanduser(GCE_PY_PATH)
    env = os.environ.copy()
    env['GCE_INI_PATH'] = gce_ini_path
    if not os.path.exists(gce_ini_path):
        raise Exception("%s not found. Please configure https://github.com/ansible/ansible/blob/devel/contrib/inventory/gce.ini and place it at this location." % GCE_INI_PATH)
    inv = subprocess.check_output([sys.executable, gce_py_path], env=env)
    inv = json.loads(inv)
    return inv

def get_gcloud_hosts():
    inv = get_inventory()
    inv_hosts = inv['_meta']['hostvars']
    return inv_hosts

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
    return os.path.expanduser(os.path.join(LOOM_SETTINGS_PATH, get_server_type() + '_deploy_settings.ini'))

def is_server_running():
    try:
        response = requests.get(get_server_url() + '/api/status/')
        if response.status_code == 200:
            return True
        else:
            raise Exception("unexpected status code %s from server" % response.status_code)
    except requests.exceptions.ConnectionError:
        return False

def parse_as_json_or_yaml(text):
    def read_as_json(json_text):
        try:
            return json.loads(json_text)
        except:
            return None

    # Try as YAML. If that fails due to bad format, try as JSON
    try:
        data = yaml.load(text)
    except yaml.parser.ParserError:
        data = read_as_json(text)
        if data is None:
            raise InvalidFormatError('Text is not valid YAML or JSON format')
    except yaml.scanner.ScannerError as e:
        data = read_as_json(text)
        if data is None:
            raise InvalidFormatError(e.message)
    return data

def read_as_json_or_yaml(file):
    try:
        with open(file) as f:
            text = f.read()
    except IOError:
        raise NoFileError('Could not find or could not read file %s' % file)

    try:
        return parse_as_json_or_yaml(text)
    except InvalidFormatError:
        raise InvalidFormatError('Input file "%s" is not valid YAML or JSON format' % file)
