import dateutil.parser
import dateutil.tz
import logging
import sys
import loomengine_utils
import ConfigParser
import os
import requests
from StringIO import StringIO
import loomengine_utils.connection


utils_logger = logging.getLogger(loomengine_utils.__name__)
utils_logger.addHandler(logging.StreamHandler(sys.stdout))
utils_logger.setLevel('INFO')

_DATETIME_FORMAT = '%b %d, %Y %-I:%M:%S %p'
LOOM_SETTINGS_SUBDIR = '.loom'
LOOM_SETTINGS_HOME = os.path.expanduser(
    os.getenv('LOOM_SETTINGS_HOME', '~/'+LOOM_SETTINGS_SUBDIR))
LOOM_CONNECTION_FILES_DIR = os.path.join(
    LOOM_SETTINGS_HOME, 'connection-files')
LOOM_CONNECTION_SETTINGS_FILE = 'client-connection-settings.conf'
LOOM_TOKEN_FILE = 'token.txt'


def _render_time(timestr):
    time_gmt = dateutil.parser.parse(timestr)
    time_local = time_gmt.astimezone(dateutil.tz.tzlocal())
    return format(time_local, _DATETIME_FORMAT)


def to_bool(value):
    if value and value.lower() in ['true', 't', 'yes', 'y']:
        return True
    else:
        return False


def parse_settings_file(settings_file):
    # dummy section name because ConfigParser needs sections
    PARSER_SECTION = 'settings'
    parser = ConfigParser.SafeConfigParser()
    # preserve uppercase in settings names
    parser.optionxform = lambda option: option.upper()
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
            'ERROR! Not connected to any server. First start a new server '
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
            'ERROR! Unexpected status code "%s" from server'
            % response.status_code)


def verify_server_is_running(url=None):
    if not is_server_running(url=url):
        raise SystemExit('ERROR! No response from server at %s' % url)


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
