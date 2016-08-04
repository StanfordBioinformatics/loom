import argparse
import ConfigParser
import distutils
import googleapiclient.discovery
import imp
import io
import json
import oauth2client.client
import os
import requests
import subprocess
import sys
import yaml

import loom.client.settings_manager
import loom.common.objecthandler
from loom.client.exceptions import *

LOOM_HOME_SUBDIR = '.loom'
LOOM_SETTINGS_PATH = os.path.join('~', LOOM_HOME_SUBDIR)
SERVER_LOCATION_FILE = os.path.join(LOOM_SETTINGS_PATH, 'server.ini')
SSL_CERT_PATH = os.path.expanduser(os.path.join(LOOM_SETTINGS_PATH, 'ssl.crt'))
SSL_KEY_PATH = os.path.expanduser(os.path.join(LOOM_SETTINGS_PATH, 'ssl.key'))
GCE_INI_PATH = os.path.join(LOOM_SETTINGS_PATH, 'gce.ini')
GCE_JSON_PATH = os.path.join(LOOM_SETTINGS_PATH, 'gce_key.json')
GCE_PY_PATH = os.path.join(imp.find_module('loom')[1], 'common', 'gce.py')
SERVER_PATH = os.path.join(imp.find_module('loom')[1], 'master')

def get_server_type():
    """Checks server.ini for server type."""
    server_location_file = os.path.expanduser(SERVER_LOCATION_FILE)
    if not os.path.exists(server_location_file):
        raise Exception("%s not found. Please run 'loom server set <servertype>' first." % server_location_file)
    config = ConfigParser.SafeConfigParser()
    config.read(server_location_file)
    server_type = config.get('server', 'type')
    return server_type

def get_gcloud_server_name():
    """Reads and returns gcloud server instance name from server.ini."""
    server_location_file = os.path.expanduser(SERVER_LOCATION_FILE)
    if not os.path.exists(server_location_file):
        raise Exception("%s not found. Please run 'loom server set <servertype>' first." % server_location_file)
    config = ConfigParser.SafeConfigParser()
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
    # TODO: add PROTOCOL and EXTERNAL PORT to server.ini since they are required to construct a URL to reach the server
    # Consider how to keep in sync with user-provided settings, default_settings.ini, and _deploy_settings.ini
    # Would remove dependency on SettingsManger from other components
    settings_manager = loom.client.settings_manager.SettingsManager()
    try:
        settings_manager.load_deploy_settings_file()
    except:
        raise Exception("Could not open server deploy settings. Do you need to run \"loom server create\" first?")
    settings = settings_manager.settings
    protocol = settings['PROTOCOL']
    ip = get_server_ip()
    port = settings['EXTERNAL_PORT']
    return '%s://%s:%s' % (protocol, ip, port)

def get_deploy_settings_filename():
    return os.path.expanduser(os.path.join(LOOM_SETTINGS_PATH, get_server_type() + '_deploy_settings.ini'))

def is_server_running():
    try:
        loom.common.objecthandler.disable_insecure_request_warning()
        #response = requests.get(get_server_url() + '/api/status/', cert=(SSL_CERT_PATH, SSL_KEY_PATH)) 
        response = requests.get(get_server_url() + '/api/status/', verify=False) 
    except requests.exceptions.ConnectionError:
        return False

    if response.status_code == 200:
        return True
    else:
        raise Exception("unexpected status code %s from server" % response.status_code)

def get_gcloud_project():
    """Queries gcloud CLI for current project."""
    check_for_gcloud()
    gcloud_output = subprocess.check_output(['gcloud', 'config', 'list'])
    gcloud_output_fp = io.StringIO(unicode(gcloud_output))
    config = ConfigParser.SafeConfigParser()
    try:
        config.readfp(gcloud_output_fp)
        project = str(config.get('core', 'project'))
        return project
    except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
        print 'Could not retrieve project id from gcloud. Please run "gcloud init" or "gcloud config set project <project_id>".'

def setup_gcloud_ssh():
    """Calls gcloud CLI to create SSH keys."""
    check_for_gcloud()
    print 'Configuring SSH keys for gcloud...'
    subprocess.call(['gcloud', 'compute', 'config-ssh', '--quiet'])

def check_for_gcloud():
    """Check if gcloud CLI is installed."""
    if not distutils.spawn.find_executable('gcloud'):
        raise Exception('Google Cloud SDK not found. Please install it from: https://cloud.google.com/sdk/')

def setup_gce_ini_and_json():
    """Creates gce.ini and a service account JSON credential if needed.
    This involves REST calls which should be skipped if possible, both to
    decrease latency and to avoid creating extraneous API keys.
    """
    if is_gce_ini_valid() and is_gce_json_valid():
        return

    check_for_gcloud()

    try:
        credentials = oauth2client.client.GoogleCredentials.get_application_default()
    except oauth2client.client.ApplicationDefaultCredentialsError:
        raise Exception('Could not get credentials from Google Cloud SDK. Please run "gcloud init" first.')

    iam_service = googleapiclient.discovery.build('iam', 'v1', credentials=credentials)
    project = get_gcloud_project()

    request = iam_service.projects().serviceAccounts().list(name='projects/%s' % project)
    response = request.execute()
    service_account_email = None
    for account in response['accounts']:
        if account['displayName'] == 'Compute Engine default service account':
            service_account_email = account['email']
    if not service_account_email:
        raise Exception('Could not retrieve Compute Engine default service account email.')

    if not is_gce_ini_valid():
        print 'Creating or updating %s...' % GCE_INI_PATH
        config = ConfigParser.SafeConfigParser()
        config.add_section('gce')
        config.set('gce', 'gce_project_id', project)
        config.set('gce', 'gce_service_account_email_address', service_account_email)
        config.set('gce', 'gce_service_account_pem_file_path', GCE_JSON_PATH)
        with open(os.path.expanduser(GCE_INI_PATH), 'w') as configfile:
            config.write(configfile)

    if not is_gce_json_valid():
        if os.path.exists(os.path.expanduser(GCE_JSON_PATH)):
            raise Exception('%s doesn\'t match the current gcloud project. Please move it, delete it, or run "gcloud init" to change the current project.' % GCE_JSON_PATH)
        print 'Creating %s...' % GCE_JSON_PATH
        request = iam_service.projects().serviceAccounts().keys().create(name='projects/%s/serviceAccounts/%s' % (project, service_account_email), body={})
        response = request.execute()
        credential_filestring = response['privateKeyData'].decode('base64')
        with open(os.path.expanduser(GCE_JSON_PATH), 'w') as credential_file:
            credential_file.write(credential_filestring)
    
def is_gce_ini_valid():
    """Makes sure that gce.ini exists, and that its project id matches gcloud CLI's."""
    if not os.path.exists(os.path.expanduser(GCE_INI_PATH)):
        return False

    config = ConfigParser.SafeConfigParser()
    config.read(os.path.expanduser(GCE_INI_PATH))
    ini_project = config.get('gce', 'gce_project_id')
    current_project = get_gcloud_project()

    if current_project == ini_project:
        return True
    else:
        return False

def is_gce_json_valid():
    """Makes sure that gce_key.json exists, and that its project id matches gcloud CLI's."""
    if not os.path.exists(os.path.expanduser(GCE_JSON_PATH)):
        return False

    json_project = json.load(open(os.path.expanduser(GCE_JSON_PATH)))['project_id']
    current_project = get_gcloud_project()

    if current_project == json_project:
        return True
    else:
        return False

def is_dev_install():
    """Checks if the client is installed in development mode by looking for a
    Dockerfile in the parent dir of the loom package. This means:
    - we can build a Loom Docker image
    - we have setup.py
    - we have /doc/examples
    - we are probably a Git checkout
    """ 
    dockerfile_path = os.path.join(os.path.dirname(imp.find_module('loom')[1]), 'Dockerfile')
    return os.path.exists(dockerfile_path)

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
