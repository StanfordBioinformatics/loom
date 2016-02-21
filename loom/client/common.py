import argparse
import json
import yaml

from loom.client import settings_manager

def add_settings_options_to_parser(parser):
    parser.add_argument('--settings', '-s', metavar='SETTINGS_FILE',
                        help='Settings indicate how to launch a server or what running server to connect to. '\
                        'To initialize settings use "loom config".')
    parser.add_argument('--require_default_settings', '-d', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--no_save_settings', action='store_true', help=argparse.SUPPRESS)
    return parser

def get_settings_manager(args):
    return settings_manager.SettingsManager(
        settings_file=args.settings,
        require_default_settings=args.require_default_settings,
        save_settings=not args.no_save_settings
    )

def _read_as_json(file):
    try:
        with open(file) as f:
            return json.load(f)
    except:
        return None

def read_as_json_or_yaml(file):
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
