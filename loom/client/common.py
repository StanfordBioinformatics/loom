import argparse
import json
import yaml

from loom.client import settings_manager
from loom.client.exceptions import *

def add_settings_options_to_parser(parser):
    parser.add_argument('--settings', '-s', metavar='SETTINGS_FILE',
                        help='Settings indicate how to launch a server or what running server to connect to. '\
                        'To initialize settings use "loom config".')
    parser.add_argument('--require_default_settings', '-d', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--no_save_settings', action='store_true', help=argparse.SUPPRESS)
    return parser

def get_settings_manager_from_parsed_args(args):
    return settings_manager.SettingsManager(
        settings_file=args.settings,
        require_default_settings=args.require_default_settings,
        save_settings=not args.no_save_settings
    )

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
