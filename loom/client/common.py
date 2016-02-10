import argparse
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
