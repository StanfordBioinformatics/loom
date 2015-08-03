#!/usr/bin/env python

import json
import requests

from xppf.client import settings_manager

_OK_RESPONSE_CODE = 200

class XppfFile:

    def __init__(self, args=None):
        if args is None:
            args=self._get_args()
        self.settings_manager = settings_manager.SettingsManager(settings_file = args.settings, require_default_settings=args.require_default_settings)
        self.file = args.pipeline_file

    def _get_args(self):
        parser = self.get_parser()
        args = parser.parse_args()
        return args

    @classmethod
    def get_parser(cls):
        import argparse
        parser = argparse.ArgumentParser('xppffile')
        parser.add_argument('file')
        parser.add_argument('--settings', '-s', metavar='SETTINGS_FILE', 
                            help="Settings indicate what server to talk to and how to launch it. Use 'xppfserver savesettings -s SETTINGS_FILE' to save.")
        parser.add_argument('--require_default_settings', '-d', action='store_true', help=argparse.SUPPRESS)
        return parser

    def run(self):
        response = 'TODO'
        return response

if __name__=='__main__':
    response =  XppfFile().run()
    print response.text
