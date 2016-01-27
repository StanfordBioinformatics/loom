#!/usr/bin/env python

import argparse
import datetime
import errno
import json
import logging
import os
import requests
import shutil
import socket
import subprocess

from loom.client import settings_manager
from loom.common import md5calc, filehandler


class UploadException(Exception):
    pass

class Upload:

    def __init__(self, args=None):

        # Parse arguments
        if args is None:
            args = self._get_args()
        self.args = args
        self.settings_manager = settings_manager.SettingsManager(
            settings_file=args.settings,
            require_default_settings=args.require_default_settings,
            save_settings=not args.no_save_settings
        )
        self.local_paths = args.files

        # Get relevant settings
        self.master_url = self.settings_manager.get_server_url_for_client()
        self.filehandler = filehandler.FileHandler(self.master_url)

    def _get_args(self):
        parser = self.get_parser()
        return parser.parse_args()

    @classmethod
    def get_parser(cls, parser=None):
        if parser == None:
            parser = argparse.ArgumentParser(__file__)
        parser.add_argument('files', nargs='+', metavar='INPUT_FILE')
        parser.add_argument('--settings', '-s', metavar='SETTINGS_FILE', 
                            help="Settings indicate what server to talk to and how to launch it. Use 'loom config")
        parser.add_argument('--require_default_settings', '-d', action='store_true', help=argparse.SUPPRESS)
        parser.add_argument('--no_save_settings', action='store_true', help=argparse.SUPPRESS)
        return parser

    def run(self):
        for local_path in self.local_paths:
            file_obj = filehandler.create_file_object(local_path)
            destination_location = self.filehandler.get_import_location(local_path, file_object=file_obj)
            self.filehandler.upload(local_path, destination_location)
            filehandler.post_file_object(self.master_url, file_obj)
            filehandler.post_location(self.master_url, destination_location)

if __name__=='__main__':
    response = Upload().run()
