import argparse
import ConfigParser
import distutils
import googleapiclient.discovery
import imp
import io
import json
import oauth2client.client
import os
import re
import requests
from StringIO import StringIO
import subprocess
import sys
import time
import yaml

import loomengine_utils.connection

LOOM_SETTINGS_SUBDIR = '.loom'
LOOM_SETTINGS_HOME = os.path.expanduser(os.getenv('LOOM_SETTINGS_HOME', '~/'+LOOM_SETTINGS_SUBDIR))
LOOM_CONNECTION_FILES_DIR = os.path.join(LOOM_SETTINGS_HOME, 'connection-files')
LOOM_CONNECTION_SETTINGS_FILE = 'client-connection-settings.conf'
LOOM_TOKEN_FILE = 'token.txt'

def parse_settings_file(settings_file):
    PARSER_SECTION = 'settings' # dummy name because ConfigParser needs sections
    parser = ConfigParser.SafeConfigParser()
    # preserve uppercase in settings names
    parser.optionxform = lambda option: option.upper()
    try:
        with open(settings_file) as stream:
            # Add a section, since ConfigParser requires it
            stream = StringIO("[%s]\n" % PARSER_SECTION + stream.read())
            parser.readfp(stream)
    except IOError:
        raise SystemExit('ERROR! Could not open file to read settings at "%s".'
                         % settings_file)
    except ConfigParser.ParsingError as e:
        raise SystemExit('ERROR! Could not parse settings in file "%s".\n %s'
                         % (settings_file, e.message))
    if parser.sections() != [PARSER_SECTION]:
        raise SystemExit('ERROR! Found extra sections in settings file: "%s". '\
                         'Sections are not needed.' % parser.sections())
    return dict(parser.items(PARSER_SECTION))

def write_settings_file(settings_file, settings):
    with open(settings_file, 'w') as f:
        for key, value in sorted(settings.items()):
            f.write('%s=%s\n' % (key, value))

def has_connection_settings():
    return os.path.exists(os.path.join(
        LOOM_SETTINGS_HOME, LOOM_CONNECTION_SETTINGS_FILE))

def verify_has_connection_settings():
    if not has_connection_settings():
        raise SystemExit(
            'ERROR! Not connected to any server. First start a new server '\
            'or connect to an existing server.')

def get_server_url():
    connection_settings = parse_settings_file(
        os.path.join(LOOM_SETTINGS_HOME, LOOM_CONNECTION_SETTINGS_FILE))
    return connection_settings.get('LOOM_SERVER_URL')

def is_server_running(url=None):
    if not url:
        url = get_server_url()

    try:
        loomengine_utils.connection.disable_insecure_request_warning()
        response = requests.get(url + '/api/status/', verify=False, timeout=30)
    except requests.exceptions.ConnectionError:
        return False

    if response.status_code == 200:
        return True
    else:
        raise SystemExit(
	    'ERROR! Unexpected status code "%s" from server' % response.status_code)

def verify_server_is_running(url=None):
    if not is_server_running(url=url):
        raise SystemExit('ERROR! No response from server at %s' % url)

SSL_CERT_PATH = os.path.expanduser(os.path.join(LOOM_SETTINGS_HOME, 'ssl.crt'))
SSL_KEY_PATH = os.path.expanduser(os.path.join(LOOM_SETTINGS_HOME, 'ssl.key'))
GCE_INI_PATH = os.path.join(LOOM_SETTINGS_HOME, 'gce.ini')
GCE_JSON_PATH = os.path.join(LOOM_SETTINGS_HOME, 'gce_key.json')
GCE_PY_PATH = os.path.join(imp.find_module('loomengine')[1], 'utils', 'gce.py')
SERVER_PATH = os.path.join(imp.find_module('loomengine')[1], 'master')

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

def validate_gcloud_label(label):
    """Many identifiers in gcloud must conform to RFC 1035."""
    if len(label) > 63 or len(label) < 6:
        raise Exception('Identifier is not 6-63 characters long: %s' % label)
    result = re.match('[a-z]([-a-z0-9]*[a-z0-9])', label)
    if result == None:
        raise Exception('Identifier does not match regular expression [a-z]([-a-z0-9]*[a-z0-9]): %s' % label)

def validate_gcloud_service_account_id(account_id):
    validate_gcloud_label(account_id)

def validate_gcloud_instance_name(name):
    validate_gcloud_label(name)

def get_server_public_ip():
    server_type = get_server_type()
    if server_type == 'local':
        return '127.0.0.1'
    elif server_type == 'gcloud':
        server_instance_name = get_gcloud_server_name()
        return get_gcloud_server_public_ip(server_instance_name)
    else:
        raise Exception("Unknown server type: %s" % server_type)

def get_server_private_ip():
    server_type = get_server_type()
    if server_type == 'local':
        return '127.0.0.1'
    elif server_type == 'gcloud':
        server_instance_name = get_gcloud_server_name()
        return get_gcloud_server_private_ip(server_instance_name)
    else:
        raise Exception("Unknown server type: %s" % server_type)

def get_gcloud_server_public_ip(name):
    inv_hosts = get_gcloud_hosts()
    if name not in inv_hosts:
        raise Exception("%s not found in Ansible dynamic inventory. Current hosts: %s" % (name, inv_hosts.keys()))
    ip = inv_hosts[name]['gce_public_ip'].encode('utf-8')
    return ip

def get_gcloud_server_private_ip(name):
    inv_hosts = get_gcloud_hosts()
    if name not in inv_hosts:
        raise Exception("%s not found in Ansible dynamic inventory. Current hosts: %s" % (name, inv_hosts.keys()))
    ip = inv_hosts[name]['gce_private_ip'].encode('utf-8')
    return ip

def get_inventory():
    gce_ini_path = os.path.expanduser(GCE_INI_PATH)
    gce_py_path = os.path.expanduser(GCE_PY_PATH)
    env = os.environ.copy()
    env['GCE_INI_PATH'] = gce_ini_path
    if not os.path.exists(gce_ini_path):
        raise Exception("%s not found. Please configure https://github.com/ansible/ansible/blob/devel/contrib/inventory/gce.ini and place it at this location." % GCE_INI_PATH)

    try:
        inv = subprocess.check_output([sys.executable, gce_py_path], env=env)
        inv = json.loads(inv)
        return inv
    except subprocess.CalledProcessError as e:
        print e

def get_gcloud_hosts():
    inv = get_inventory()
    inv_hosts = inv['_meta']['hostvars']
    return inv_hosts

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

def check_for_gcloud():
    """Check if gcloud CLI is installed."""
    if not distutils.spawn.find_executable('gcloud'):
        raise Exception('Google Cloud SDK not found. Please install it from: https://cloud.google.com/sdk/')

def create_gce_ini(email):
    if not is_gce_json_valid():
        raise Exception('Credential %s does not exist or is not valid for the current project. Please run "gcloud init" and ensure that the correct project is selected.' % GCE_JSON_PATH)
    project = get_gcloud_project()
    server_name = get_gcloud_server_name()
    print 'Creating %s...' % GCE_INI_PATH
    config = ConfigParser.SafeConfigParser()
    config.add_section('gce')
    config.set('gce', 'gce_project_id', project)
    config.set('gce', 'gce_service_account_email_address', email)
    config.set('gce', 'gce_service_account_pem_file_path', GCE_JSON_PATH)
    with open(os.path.expanduser(GCE_INI_PATH), 'w') as configfile:
        config.write(configfile)
    delete_libcloud_cached_credential() # Ensures that downstream steps get a new token with updated service account

def create_gce_json(email):
    project = get_gcloud_project()

    print 'Creating %s...' % GCE_JSON_PATH
    create_service_account_key(project, email, GCE_JSON_PATH)

def create_service_account_key(project, email, path):
    """Creates a service account key in the provided project, using the provided
    service account email, and saves it to the provided path.
    """
    iam_service = get_iam_service()
    request = iam_service.projects().serviceAccounts().keys().create(name='projects/%s/serviceAccounts/%s' % (project, email), body={})
    response = request.execute()
    credential_filestring = response['privateKeyData'].decode('base64')
    with open(os.path.expanduser(path), 'w') as credential_file:
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
    dockerfile_path = os.path.join(os.path.dirname(imp.find_module('loomengine')[1]), 'Dockerfile')
    return os.path.exists(dockerfile_path)

def create_service_account(account_id):
    """Creates a service account in the current project using the provided id.
    """
    validate_gcloud_service_account_id(account_id)

    iam_service = get_iam_service()
    project = get_gcloud_project()
    display_name = account_id               # Note: display name is not guaranteed to be unique in project
    request_body =  {"serviceAccount": { "displayName": display_name}, "accountId": account_id}

    request = iam_service.projects().serviceAccounts().create(name='projects/%s' % project, body=request_body)
    response = request.execute()
    return response

def delete_service_account(account_email):
    """Deletes the service account in the current project with the provided email."""
    iam_service = get_iam_service()
    project = get_gcloud_project()

    request = iam_service.projects().serviceAccounts().delete(name='projects/%s/serviceAccounts/%s' % (project, account_email))
    response = request.execute()
    return response

def list_service_accounts():
    """Lists service accounts in the current project."""
    iam_service = get_iam_service()
    project = get_gcloud_project()

    request = iam_service.projects().serviceAccounts().list(name='projects/%s' % project)
    response = request.execute()
    return response['accounts']

def find_service_account_email(account_id=None):
    """Looks for a service account email in the current project using the
    provided account id. If none provided, defaults to current instance name.
    Matches the specified ID to the email username (before the @). If more than
    one match, raise an error since we don't know which email is the right one. 
    """
    if account_id == None:
        account_id = get_gcloud_server_name()
    accounts = list_service_accounts()
    emails = []
    for account in accounts:
        email = account['email']
        if email.split('@')[0] == account_id:
            emails.append(email)
    if len(emails) == 1:
        return emails[0]
    elif len(emails) > 1:
        raise Exception('More than one service account email matches account ID: %s' % account_id)
    elif len(emails) < 1:
        return None

def get_serviceaccount_policy(email=None):
    """Gets the IAM policy for the provided service account email in the current
    project. If no email provided, defaults to account for the current instance.
    """
    if email == None:
        email = find_service_account_email()

    iam_service = get_iam_service()
    project = get_gcloud_project()
    request = iam_service.projects().serviceAccounts().getIamPolicy(resource='projects/%s/serviceAccounts/%s' % (project, email))
    response = request.execute()
    return response

def get_project_policy(project=None):
    """Gets the IAM policy for the specified project. If none specified,
    defaults to current project.
    """
    if project == None:
        project = get_gcloud_project()

    crm_service = get_crm_service()
    request = crm_service.projects().getIamPolicy(resource='%s' % project, body={})
    response = request.execute()
    return response

def set_project_policy(policy, project=None):
    """Sets the IAM policy for the specified project. If no project specified,
    defaults to current project.
    """
    if project == None:
        project = get_gcloud_project()

    crm_service = get_crm_service()
    request = crm_service.projects().setIamPolicy(resource='%s' % project, body=policy)
    response = request.execute()
    return response

def grant_roles(roles, email=None):
    """Grants the specified roles to the specified service account in the current 
    project. If no email provided, defaults to account for the current instance.
    """
    if email == None:
        email = find_service_account_email()

    project = get_gcloud_project()

    # Set policy on service account

    # iam_service = get_iam_service()

    # bindings = []
    # for role in roles:
    #     bindings.append({"role": role, "members": ["serviceAccount:%s" % email]})

    # request_body = {"policy": {"bindings": bindings}}
    # request = iam_service.projects().serviceAccounts().setIamPolicy(resource='projects/%s/serviceAccounts/%s' % (project, email), body=request_body)
    # response = request.execute()

    # Set policy on project
    policy = get_project_policy(project)
    jsonfilename = os.path.expanduser(os.path.join(LOOM_SETTINGS_HOME, 'policy-%s.json' % time.strftime("%Y%m%d-%H%M%S")))
    with open(jsonfilename, 'w') as jsonfile:
        json.dump(policy, jsonfile)
    print 'Current project policy saved to %s' % jsonfilename
    added_roles = []
    for binding in policy['bindings']:
        if binding['role'] in roles:
            binding['members'].append('serviceAccount:%s' % email)
            added_roles.append(binding['role']) # mark as added
    # if any specified roles not added, create and add new binding
    for role in roles:
        if role not in added_roles:
            policy['bindings'].append({"role":role, "members": ["serviceAccount:%s" % email]})
    set_project_policy({"policy": policy}, project)
    
def get_iam_service():
    try:
        credentials = oauth2client.client.GoogleCredentials.get_application_default()
    except oauth2client.client.ApplicationDefaultCredentialsError:
        raise Exception('Could not get credentials from Google Cloud SDK. Please run "gcloud init" first.')

    iam_service = googleapiclient.discovery.build('iam', 'v1', credentials=credentials)
    return iam_service

def get_crm_service():
    try:
        credentials = oauth2client.client.GoogleCredentials.get_application_default()
    except oauth2client.client.ApplicationDefaultCredentialsError:
        raise Exception('Could not get credentials from Google Cloud SDK. Please run "gcloud init" first.')

    crm_service = googleapiclient.discovery.build('cloudresourcemanager', 'v1', credentials=credentials)
    return crm_service

def delete_libcloud_cached_credential():
    project = get_gcloud_project()
    credential = os.path.expanduser('~/.google_libcloud_auth.%s' % project)
    if os.path.exists(credential):
        print 'Deleting %s...' % credential
        os.remove(credential)

def delete_token():
    token_path = os.path.join(LOOM_SETTINGS_HOME, LOOM_TOKEN_FILE)
    if os.path.exists(token_path):
        os.remove(token_path)

def save_token(token):
    delete_token()
    with open(os.path.join(LOOM_SETTINGS_HOME, LOOM_TOKEN_FILE), 'w') as f:
        f.write(token)

def get_token():
    token_path = os.path.join(LOOM_SETTINGS_HOME, LOOM_TOKEN_FILE)
    if os.path.exists(token_path):
        with open(token_path) as f:
            token = f.read()
    else:
        token = None
    return token
