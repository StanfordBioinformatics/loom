import ConfigParser
import os
import re
import requests
from StringIO import StringIO

import loomengine_utils.connection
from loomengine.deployment import SETTINGS_HOME


CONNECTION_SETTINGS_FILE = 'connection-settings.conf'
TOKEN_FILE = 'token.txt'


def parse_settings_file(settings_file):
    # dummy section name because ConfigParser needs sections
    PARSER_SECTION = 'settings'
    parser = ConfigParser.SafeConfigParser()
    # Do not transform settings names
    parser.optionxform = str
    try:
        with open(settings_file) as stream:
            # Add a section, since ConfigParser requires it
            stream = StringIO("[%s]\n" % PARSER_SECTION + stream.read())
            parser.readfp(stream)
    except IOError:
        raise SystemExit(
            'ERROR! Could not open file to read settings at "%s".'
            % settings_file)
    except ConfigParser.ParsingError as e:
        raise SystemExit(
            'ERROR! Could not parse settings in file "%s".\n %s'
            % (settings_file, e.message))
    if parser.sections() != [PARSER_SECTION]:
        raise SystemExit(
            'ERROR! Found extra sections in settings file: "%s". '
            'Sections are not needed.' % parser.sections())
    raw_settings = dict(parser.items(PARSER_SECTION))
    settings = {}
    for key, value in raw_settings.items():
        settings[key] = value
    return settings

def write_settings_file(settings_file, settings):
    with open(settings_file, 'w') as f:
        for key, value in sorted(settings.items()):
            f.write('%s=%s\n' % (key, value))

def has_connection_settings():
    return os.path.exists(
        os.path.join(SETTINGS_HOME, CONNECTION_SETTINGS_FILE))

def verify_has_connection_settings():
    if not has_connection_settings():
        raise SystemExit(
            'ERROR! Not connected to any server. First start a new server '
            'or connect to an existing server.')

def get_server_url():
    connection_settings = parse_settings_file(
        os.path.join(SETTINGS_HOME, CONNECTION_SETTINGS_FILE))
    return connection_settings['server_url']

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
            'ERROR! Unexpected status code "%s" from server'
            % response.status_code)

def verify_server_is_running(url=None):
    if not is_server_running(url=url):
        raise SystemExit('ERROR! No response from server at %s' % url)

def delete_token():
    token_path = os.path.join(SETTINGS_HOME, TOKEN_FILE)
    if os.path.exists(token_path):
        os.remove(token_path)

def save_token(token):
    delete_token()
    with open(os.path.join(SETTINGS_HOME, TOKEN_FILE), 'w') as f:
        f.write(token)

def get_token():
    token_path = os.path.join(SETTINGS_HOME, TOKEN_FILE)
    if os.path.exists(token_path):
        with open(token_path) as f:
            token = f.read()
    else:
        token = None
    return token
