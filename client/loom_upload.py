#!/usr/bin/env python

import datetime
import errno
import json
import logging
import os
import requests
import shutil
import socket
import subprocess

import loom.client.settings_manager
from loom.common import md5calc, filehandler


class LoomUpload:

    def __init__(self, args=None):

        # Parse arguments
        if args is None:
            args=self._get_args()
        self.local_paths = args.files
        settings_manager = loom.client.settings_manager.SettingsManager(settings_file = args.settings, require_default_settings=args.require_default_settings)

        # Get relevant settings
        self.master_url = settings_manager.get_server_url_for_client()
        file_root = settings_manager.get_file_root_for_client()
        import_dir = settings_manager.get_import_dir()
        self.import_path = os.path.join(file_root, import_dir)
        self.filehandler = filehandler.FileHandler(self.master_url, file_root)

    def _get_args(self):
        parser = self.get_parser()
        args = parser.parse_args()
        return args

    @classmethod
    def get_parser(cls):
        import argparse
        parser = argparse.ArgumentParser(description='Register and upload one or more files to loom.')
        parser.add_argument('files', nargs='+')
        parser.add_argument('--settings', '-s', metavar='SETTINGS_FILE', 
                            help="The settings file specifies where and how to upload files. Use loomconfig to create or modify the settings file.")
        parser.add_argument('--require_default_settings', '-d', action='store_true', help=argparse.SUPPRESS)
        return parser

    def run(self):
        for local_path in self.local_paths:
            location = self.filehandler.get_import_destination(local_path)
            self.filehandler.upload(local_path, location)


class LoomUploadError(Exception):
    pass


if __name__=='__main__':
    response = LoomUpload().run()
